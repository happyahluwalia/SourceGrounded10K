"""
    End to end pipeline for processing SEC Filings.

    Usage:
        python scripts/process_company.py AAPL --filing_type 10-K --limit 1
        python scripts/process_company.py MSFT --filing_type 10-Q --limit 3

"""

# Standard library imports
import argparse  # Command-line argument parsing
import sys
from pathlib import Path 
from datetime import datetime 

# Add parent directory to path so we can import app modules
# This allows running the script from anywhere
sys.path.insert(0,str(Path(__file__).parent.parent))

# Import our custom services for the pipeline
from app.services.sec_client import SECClient  # Fetch and download from SEC
from app.services.sec_parser import SECFilingParser  # Parse HTML filings
from app.services.chunker import FinancialDocumentChunker  # Split into chunks
from app.services.storage import DatabaseStorage, convert_date_strings  # Save to Postgres

def process_company(
    ticker:str,
    filing_type: str = "10-K",
    limit: int =1,
    chunk_size: int=512,
    chunk_overlap: int=75
):
    """
        Process SEC filings for a company end-to-end.

        Pipeline:
            1. Fetch filings metadata from SEC EDGAR
            2. Download HTML documents
            3. Parse sections and tables
            4. Chunk documents
            5. Save to database

        Args:
            ticker: Stock ticker 
            filing_type: Form type to process
            limit: Maximum number of filings to process
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap betwen chunks

    """

    # Print header
    print("="*70)
    print(f"PROCESSING: {ticker} - {filing_type} (limit: {limit})")
    print("="*70)
    
    # Initialize all services needed for the pipeline
    sec_client = SECClient()  # Handles SEC API calls and downloads
    chunker = FinancialDocumentChunker(
        chunk_size=chunk_size,  # Target size for each chunk
        chunk_overlap=chunk_overlap  # Overlap to preserve context
    )
    storage = DatabaseStorage()  # Handles Postgres operations

    try:
        # ===================================================================
        # STEP 1: Fetch filing metadata from SEC EDGAR API
        # ===================================================================
        print(f" \n{'='*70}")
        print(f"STEP 1: Fetching {filing_type} filings for {ticker}")
        print("="*70)

        # Query SEC API for recent filings of specified type
        filings = sec_client.get_company_filings(
            ticker=ticker,
            filing_types=[filing_type],  # e.g., ["10-K"] or ["10-Q"]
            limit=limit  # How many recent filings to fetch
        )

        # Handle case where no filings found
        if not filings:
            print(f"❌ No {filing_type} filings found for {ticker}")
            return
        
        # Display what we found
        print(f"✅ Found {len(filings)} filing(s)")
        for i, filing in enumerate(filings, 1):
            print(f"   {i}. {filing['form']} - {filing['filingDate']} (Report: {filing['reportDate']})")
        
        # ===================================================================
        # Process each filing through the pipeline
        # ===================================================================
        total_chunks = 0  # Track total chunks across all filings

        for idx, filings in enumerate(filings, 1):
            # Print filing header
            print(f"\n{'='*70}")
            print(f"PROCESSING FILING {idx}/{len(filings)}")
            print("="*70)
            print(f"Form: {filing['form']}")
            print(f"Filing Date: {filing['filingDate']}")
            print(f"Report Date: {filing['reportDate']}")
            print(f"Document: {filing['primaryDocument']}")
            
            # ---------------------------------------------------------------
            # STEP 2: Download HTML document from SEC
            # ---------------------------------------------------------------
            print(f"\n{'─'*70}")
            print(f"STEP 2: Downloading filing")
            print("─"*70)

            # Download to local filesystem (or use cached version if exists)
            filepath = sec_client.download_filing(filing)
            print(f"✅ Saved to: {filepath}")
            
            # ---------------------------------------------------------------
            # STEP 3: Parse HTML to extract sections and tables
            # ---------------------------------------------------------------
            print(f"\n{'─'*70}")
            print(f"STEP 3: Parsing filing")
            print("─"*70)
            
            # Initialize parser with the downloaded HTML file
            parser = SECFilingParser(filepath)
            # Extract structured content
            sections = parser.extract_sections()  # Dict: {section_name: text}
            tables = parser.extract_tables()  # List of table dicts

            print(f"✅ Extracted {len(sections)} sections")
            print(f"✅ Extracted {len(tables)} tables")
            
            # Show preview of what sections were found
            print(f"\n   Sections found:")
            for section_name in list(sections.keys())[:5]:  # Show first 5
                print(f"     • {section_name}")
            if len(sections) > 5:
                print(f"     ... and {len(sections) - 5} more")
            
            # ---------------------------------------------------------------
            # STEP 4: Chunk document for vector storage
            # ---------------------------------------------------------------
            print(f"\n{'─'*70}")
            print(f"STEP 4: Chunking document")
            print("─"*70)
            
            # Prepare metadata to attach to each chunk
            filing_metadata = {
                "ticker": filing["ticker"],
                "form": filing["form"],
                "filing_date": filing["filingDate"],
                "report_date": filing["reportDate"],
                "document_url": filing["documentURL"],
                "document_path": filepath
            }
            
            # Chunk sections and tables with metadata
            # Each chunk will have: text, section, chunk_index, metadata, etc.
            chunks = chunker.chunk_filing(sections, tables, filing_metadata)
            
            print(f"✅ Created {len(chunks)} chunks")
            
            # Display statistics about the chunks created
            stats = chunker.get_chunk_stats(chunks)
            print(f"\n   Chunk statistics:")
            print(f"     Section chunks: {stats['section_chunks']}")
            print(f"     Table chunks: {stats['table_chunks']}")
            print(f"     Avg section size: {stats['avg_section_size']:.0f} chars")
            if stats['table_chunks'] > 0:
                print(f"     Avg table size: {stats['avg_table_size']:.0f} chars")
            print(f"     Total characters: {stats['total_chars']:,}")
            
            # ---------------------------------------------------------------
            # STEP 5: Save to PostgreSQL database
            # ---------------------------------------------------------------
            print(f"\n{'─'*70}")
            print(f"STEP 5: Saving to database")
            print("─"*70)
            
            # Convert date strings to Python date objects (required by SQLAlchemy)
            filing_metadata_db = convert_date_strings(filing_metadata)
            
            # Save filing and all chunks in a single transaction
            # This will:
            # - Upsert company record
            # - Delete existing filing if duplicate (same ticker+type+date)
            # - Insert new filing record
            # - Generate UUIDs for chunks
            # - Bulk insert chunk metadata
            saved_filing = storage.save_filing_with_chunks(filing_metadata_db, chunks)
            
            print(f"✅ Saved to database")
            print(f"   Filing ID: {saved_filing.id}")
            print(f"   Chunks stored: {saved_filing.num_chunks}")
            
            # Accumulate total chunks processed
            total_chunks += len(chunks)
        
        # ===================================================================
        # Final summary of processing
        # ===================================================================
        print(f"\n{'='*70}")
        print(f"PROCESSING COMPLETE")
        print("="*70)
        print(f"✅ Processed {len(filings)} filing(s)")
        print(f"✅ Generated {total_chunks} total chunks")
        print(f"✅ All data saved to database")
        
        # ===================================================================
        # Show current state of database for this company
        # ===================================================================
        print(f"\n{'─'*70}")
        print(f"DATABASE SUMMARY")
        print("─"*70)

        # Query database for all filings of this company
        filing_stats = storage.get_filing_stats(ticker)
        print(f"Total filings for {ticker}: {len(filing_stats)}")
        
        # Display each filing's status
        for stat in filing_stats:
            print(f"\n  {stat['filing_type']} - {stat['report_date']}")
            print(f"    Filing ID: {stat['id']}")
            print(f"    Chunks: {stat['num_chunks']}")
            print(f"    Processed: {'✅' if stat['processed'] else '⏳'}")
        
    except Exception as e:
        # Handle any errors that occur during processing
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()  # Show full stack trace for debugging
        sys.exit(1)  # Exit with error code
    
    finally:
        # Always close database connection, even if error occurred
        storage.close()
    
    # Success message
    print(f"\n{'='*70}")
    print("DONE! 🎉")
    print("="*70)

def main():
    """
    Parse command-line arguments and run the pipeline.
    
    This is the entry point when script is run from command line.
    """

    # Set up argument parser with examples in help text
    parser = argparse.ArgumentParser(
        description = "Process SEC filings for a company",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserve formatting in epilog
        epilog="""  # Examples shown in --help
        Examples:
                # Process Apple's most recent 10-K
                python scripts/process_company.py AAPL --filing-type 10-K --limit 1
                
                # Process Microsoft's 3 most recent 10-Q filings
                python scripts/process_company.py MSFT --filing-type 10-Q --limit 3
                
                # Process with custom chunk size
                python scripts/process_company.py TSLA --filing-type 10-K --chunk-size 1024
            """
        )

    # Required positional argument
    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker (e.g., AAPL, MSFT, TSLA)"
    )
    
    # Optional arguments with defaults
    parser.add_argument(
        "--filing-type",
        type=str,
        default="10-K",
        help="Filing type to process (default: 10-K)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum number of filings to process (default: 1)"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Target chunk size in characters (default: 512)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=75,
        help="Chunk overlap in characters (default: 75, ~15% of chunk_size)"
    )
    
    # Parse command-line arguments
    args = parser.parse_args()

    # Run the pipeline with parsed arguments
    process_company(
        ticker = args.ticker.upper(),  # Normalize to uppercase
        filing_type=args.filing_type,
        limit=args.limit,
        chunk_size = args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )

# Entry point when script is run directly
if __name__ == "__main__":
    main()

