import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# test_storage.py

from app.services.sec_parser import SECFilingParser
from app.services.chunker import FinancialDocumentChunker
from app.services.storage import DatabaseStorage, convert_date_strings
from datetime import datetime

print("="*60)
print("TEST: Database Storage")
print("="*60)

# 1. Parse a filing (reuse what we already have)
filepath = "data/filings/AAPL/2024-10-K-2024-09-28.html"
parser = SECFilingParser(filepath)

print("\n1. Parsing filing...")
sections = parser.extract_sections()
tables = parser.extract_tables()
print(f"   ✅ Parsed {len(sections)} sections, {len(tables)} tables")

# 2. Chunk the filing
print("\n2. Chunking filing...")
filing_metadata = {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "filing_date": "2024-11-01",
    "report_date": "2024-09-28",
    "form": "10-K",
    "document_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
    "document_path": filepath
}

chunker = FinancialDocumentChunker(chunk_size=512, chunk_overlap=75)
chunks = chunker.chunk_filing(sections, tables, filing_metadata)
print(f"   ✅ Created {len(chunks)} chunks")

# 3. Save to database
print("\n3. Saving to database...")
storage = DatabaseStorage()

try:
    # Convert date strings to date objects
    filing_metadata_db = convert_date_strings(filing_metadata)
    
    # Save filing with chunks
    filing = storage.save_filing_with_chunks(filing_metadata_db, chunks)
    
    print(f"\n✅ Storage successful!")
    print(f"   Filing ID: {filing.id}")
    print(f"   Chunks saved: {filing.num_chunks}")
    print(f"   Processed: {filing.processed}")
    
except Exception as e:
    print(f"\n❌ Storage failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    storage.close()

# 4. Verify in database
print("\n4. Verifying data...")
storage = DatabaseStorage()

try:
    # Get filing stats
    stats = storage.get_filing_stats("AAPL")
    print(f"   Total filings for AAPL: {len(stats)}")
    
    for stat in stats:
        print(f"\n   Filing: {stat['filing_type']} ({stat['report_date']})")
        print(f"     ID: {stat['id']}")
        print(f"     Chunks: {stat['num_chunks']}")
        print(f"     Processed: {stat['processed']}")
    
    # Get chunks for first filing
    if stats:
        filing_id = stats[0]['id']
        chunks_db = storage.get_chunks_for_filing(filing_id)
        print(f"\n   Chunks in database: {len(chunks_db)}")
        
        # Show sample chunk
        if chunks_db:
            sample = chunks_db[0]
            print(f"\n   Sample chunk:")
            print(f"     ID: {sample.id}")
            print(f"     Section: {sample.section}")
            print(f"     Type: {sample.chunk_type}")
            print(f"     Size: {sample.char_count} chars")
    
finally:
    storage.close()

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)