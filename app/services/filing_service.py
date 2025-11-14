"""
Filing Service - Orchestrates the Complete SEC Filing Processing Pipeline

This module provides the high-level orchestration layer that coordinates all
services required to fetch, process, and store SEC filings. It acts as the
"conductor" that manages the entire data pipeline from raw SEC filings to
searchable vector embeddings.

Architecture Overview:
--------------------
The FilingService coordinates 5 main services:
1. SECClient: Downloads filings from SEC EDGAR
2. SECFilingParser: Extracts structured data from HTML
3. FinancialDocumentChunker: Splits documents into searchable chunks
4. DatabaseStorage: Stores metadata and chunks in Postgres
5. VectorStore: Generates embeddings and stores in Qdrant

Pipeline Flow:
-------------
1. Check Existence: Query Postgres to see if filing already processed
2. Fetch from SEC: Download HTML filing from EDGAR if missing
3. Parse HTML: Extract sections, tables, and metadata
4. Chunk Document: Split into ~500 char chunks for semantic search
5. Store Metadata: Save filing + chunks to Postgres
6. Generate Embeddings: Convert text to 1024-dim vectors using BGE model
7. Store Vectors: Upload embeddings to Qdrant for similarity search

Key Features:
------------
- **Idempotency**: Checks if filing exists before reprocessing
- **Lazy Loading**: Automatically fetches missing filings on-demand
- **Atomic Operations**: Uses database transactions for consistency
- **Error Handling**: Graceful failure with detailed error messages
- **Status Tracking**: Monitors processing state (ready, pending, error)

Usage Example:
-------------
```python
from app.services.filing_service import FilingService
from app.services.storage import DatabaseStorage
from app.services.vector_store import VectorStore

# Initialize services
db_storage = DatabaseStorage()
vector_store = VectorStore()
filing_service = FilingService(db_storage, vector_store)

# Process a filing (fetches if missing)
result = filing_service.get_or_process_filing("AAPL", "10-K")

if result['status'] == 'success':
    print(f"Processed {result['chunks_created']} chunks")
```

Database Schema:
---------------
The service interacts with 3 main tables:
- companies: Company metadata (ticker, name, CIK)
- sec_filings: Filing metadata (type, dates, status)
- chunks: Text chunks with section info

Vector Store:
------------
Embeddings are stored in Qdrant with metadata:
- ticker: Company ticker for filtering
- filing_type: 10-K, 10-Q, etc.
- section: Item 1, Item 7, etc.
- report_date: Fiscal period end date
- text: Actual chunk content

Status States:
-------------
- "ready": Filing processed, embeddings generated, ready for search
- "embeddings_pending": Filing parsed but embeddings not yet generated
- "processing": Currently being processed
- "error": Processing failed

Performance Considerations:
--------------------------
- Embedding generation: ~30 seconds for 500 chunks (BGE-large model)
- Qdrant upload: ~2 seconds for 500 chunks (batched)
- Total pipeline: ~1-2 minutes per filing
- Deduplication: Skips already-processed filings automatically

Error Scenarios:
---------------
1. Filing not found on SEC: Returns error status
2. Parse failure: Logs error, returns error status
3. Database error: Transaction rolled back, error returned
4. Qdrant unavailable: Postgres updated but embeddings_generated=False

See Also:
--------
- sec_client.py: SEC EDGAR API client
- sec_parser.py: HTML parsing logic
- chunker.py: Document chunking strategy
- storage.py: Postgres operations
- vector_store.py: Qdrant operations
"""

from typing import Optional, Dict, List
from datetime import datetime, date
import logging

from sqlalchemy.orm import Session
from app.models.database import Company, SECFiling, Chunk
from app.services.sec_client import SECClient
from app.services.sec_parser import SECFilingParser
from app.services.chunker import FinancialDocumentChunker
from app.services.storage import DatabaseStorage
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class FilingService:
    """
    Orchestrates the complete SEC filing processing pipeline.
    
    This is the main service that coordinates all other services to fetch,
    process, and store SEC filings. It provides a high-level API for:
    
    1. **Checking** if filings exist in the local database
    2. **Fetching** filings from SEC EDGAR when needed
    3. **Processing** filings through the full pipeline
    4. **Lazy loading** filings on-demand for Q&A
    
    The service ensures idempotency - it won't reprocess filings that
    already exist unless explicitly requested. This makes it safe to call
    repeatedly without wasting resources.
    
    Thread Safety:
        This service is NOT thread-safe. Create separate instances for
        concurrent processing or use a task queue (e.g., Celery).
    
    Attributes:
        db_storage (DatabaseStorage): Handles Postgres operations
        vector_store (VectorStore): Handles Qdrant operations
        sec_client (SECClient): Fetches filings from SEC EDGAR
        parser (SECFilingParser): Parses HTML filings
        chunker (FinancialDocumentChunker): Chunks documents for search
    
    Example:
        >>> # Initialize service
        >>> service = FilingService(db_storage, vector_store)
        >>> 
        >>> # Process a filing
        >>> result = service.process_filing("AAPL", "10-K")
        >>> if result['status'] == 'success':
        >>>     print(f"Created {result['chunks_created']} chunks")
        >>> 
        >>> # Check if filing exists
        >>> info = service.check_filing_exists("AAPL", "10-K")
        >>> if info:
        >>>     print(f"Status: {info['status']}")
    """
    
    def __init__(
        self,
        db_storage: DatabaseStorage,
        vector_store: VectorStore,
        sec_client: Optional[SECClient] = None,
    ):
        """
        Initialize the filing service with required dependencies.
        
        This constructor sets up all the services needed for the complete
        filing processing pipeline. If no SEC client is provided, a default
        one will be created automatically.
        
        Args:
            db_storage (DatabaseStorage): Service for Postgres operations.
                Must be initialized with valid database connection.
            vector_store (VectorStore): Service for Qdrant operations.
                Must be connected to a running Qdrant instance.
            sec_client (Optional[SECClient]): Client for SEC EDGAR API.
                If None, creates a default client with standard rate limiting.
        
        Raises:
            ConnectionError: If database or Qdrant connection fails
        
        Example:
            >>> from app.services.storage import DatabaseStorage
            >>> from app.services.vector_store import VectorStore
            >>> 
            >>> db = DatabaseStorage()
            >>> vs = VectorStore()
            >>> service = FilingService(db, vs)
        """
        self.db_storage = db_storage
        self.vector_store = vector_store
        self.sec_client = sec_client or SECClient()
        # Parser is created per-filing (requires filepath)
        self.chunker = FinancialDocumentChunker()
    
    def check_filing_exists(
        self,
        ticker: str,
        filing_type: str = "10-K",
        year: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Check if a filing exists in the local database.
        
        This method queries Postgres to determine if a filing has already
        been processed and stored. It returns detailed status information
        including whether embeddings have been generated.
        
        The method always returns the most recent filing matching the criteria.
        If a year is specified, it returns the most recent filing from that year.
        
        Args:
            ticker (str): Company ticker symbol (e.g., "AAPL", "MSFT").
                Case-insensitive - will be converted to uppercase.
            filing_type (str, optional): Type of SEC filing. Defaults to "10-K".
                Common types: "10-K" (annual), "10-Q" (quarterly), "8-K" (current).
            year (Optional[int], optional): Fiscal year to filter by.
                If None, returns most recent filing regardless of year.
                If specified, returns most recent filing from that year.
        
        Returns:
            Optional[Dict]: Filing information dictionary if found, None otherwise.
                Dictionary contains:
                - filing_id (str): UUID of the filing
                - ticker (str): Company ticker
                - filing_type (str): Type of filing
                - report_date (str): Fiscal period end date (ISO format)
                - filing_date (str): Date filed with SEC (ISO format)
                - num_chunks (int): Number of text chunks created
                - processed (bool): Whether parsing completed
                - embeddings_generated (bool): Whether vectors created
                - status (str): Overall status ("ready", "embeddings_pending", "processing")
                - created_at (str): When record was created (ISO format)
        
        Status Values:
            - "ready": Fully processed and searchable
            - "embeddings_pending": Parsed but embeddings not yet generated
            - "processing": Currently being processed
        
        Example:
            >>> service = FilingService(db, vs)
            >>> 
            >>> # Check for most recent 10-K
            >>> info = service.check_filing_exists("AAPL", "10-K")
            >>> if info:
            >>>     print(f"Status: {info['status']}")
            >>>     print(f"Chunks: {info['num_chunks']}")
            >>> else:
            >>>     print("Filing not found")
            >>> 
            >>> # Check for specific year
            >>> info = service.check_filing_exists("AAPL", "10-K", year=2023)
            >>> if info and info['status'] == 'ready':
            >>>     print("2023 10-K is ready for search")
        
        Note:
            This method only checks the database, it does NOT fetch from SEC.
            Use get_or_process_filing() for automatic fetching.
        """
        with self.db_storage.get_session() as session:
            query = session.query(SECFiling).join(Company).filter(
                Company.ticker == ticker.upper(),
                SECFiling.filing_type == filing_type
            )
            
            # Filter by year if specified
            if year:
                query = query.filter(
                    SECFiling.report_date >= date(year, 1, 1),
                    SECFiling.report_date <= date(year, 12, 31)
                )
            
            # Get most recent filing
            filing = query.order_by(SECFiling.report_date.desc()).first()
            
            if not filing:
                return None
            
            # Determine status
            if filing.processed and filing.embeddings_generated:
                status = "ready"
            elif filing.processed:
                status = "embeddings_pending"
            else:
                status = "processing"
            
            return {
                "filing_id": str(filing.id),
                "ticker": filing.ticker,
                "filing_type": filing.filing_type,
                "report_date": filing.report_date.isoformat(),
                "filing_date": filing.filing_date.isoformat() if filing.filing_date else None,
                "num_chunks": filing.num_chunks,
                "processed": filing.processed,
                "embeddings_generated": filing.embeddings_generated,
                "status": status,
                "created_at": filing.created_at.isoformat(),
            }
    
    def process_filing(
        self,
        ticker: str,
        filing_type: str = "10-K",
        force_reprocess: bool = False
    ) -> Dict:
        """
        Execute the complete filing processing pipeline.
        
        This is the main workhorse method that orchestrates the entire pipeline:
        1. Check if filing already exists (skip if found, unless force_reprocess=True)
        2. Ensure company record exists in database
        3. Fetch filing from SEC EDGAR
        4. Download HTML document
        5. Parse HTML to extract sections and tables
        6. Chunk document into ~500 character pieces
        7. Store filing metadata and chunks in Postgres
        8. Generate 1024-dim embeddings using BGE-large model
        9. Upload embeddings to Qdrant vector database
        10. Mark filing as complete
        
        The entire process typically takes 1-2 minutes per filing.
        All operations are logged for debugging and monitoring.
        
        Args:
            ticker (str): Company ticker symbol (e.g., "AAPL").
                Case-insensitive, will be normalized to uppercase.
            filing_type (str, optional): Type of SEC filing. Defaults to "10-K".
                Supported types: "10-K", "10-Q", "8-K", "DEF 14A", etc.
            force_reprocess (bool, optional): Force reprocessing even if exists.
                Defaults to False. Set to True to update existing filings.
        
        Returns:
            Dict: Result dictionary with status and details.
                Success response:
                {
                    "status": "success",
                    "message": "Successfully processed AAPL 10-K",
                    "filing": {
                        "filing_id": "uuid-string",
                        "ticker": "AAPL",
                        "filing_type": "10-K",
                        "report_date": "2024-09-28",
                        "num_chunks": 569
                    },
                    "chunks_created": 569,
                    "embeddings_generated": 569
                }
                
                Already exists response:
                {
                    "status": "already_exists",
                    "message": "Filing for AAPL 10-K already processed",
                    "filing": {...}  # Full filing info
                }
                
                Error response:
                {
                    "status": "error",
                    "message": "Error description"
                }
        
        Raises:
            No exceptions are raised - all errors are caught and returned
            in the result dict with status="error".
        
        Example:
            >>> service = FilingService(db, vs)
            >>> 
            >>> # Process a new filing
            >>> result = service.process_filing("AAPL", "10-K")
            >>> if result['status'] == 'success':
            >>>     print(f"Created {result['chunks_created']} chunks")
            >>> elif result['status'] == 'already_exists':
            >>>     print("Filing already processed")
            >>> else:
            >>>     print(f"Error: {result['message']}")
            >>> 
            >>> # Force reprocess an existing filing
            >>> result = service.process_filing("AAPL", "10-K", force_reprocess=True)
        
        Performance:
            - SEC download: 2-5 seconds
            - HTML parsing: 1-2 seconds
            - Chunking: <1 second
            - Postgres storage: 1-2 seconds
            - Embedding generation: 20-40 seconds (depends on chunk count)
            - Qdrant upload: 1-3 seconds
            - Total: 30-60 seconds typical
        
        Error Handling:
            - SEC API errors: Returns error status with message
            - Parse errors: Logged and returned as error
            - Database errors: Transaction rolled back, error returned
            - Qdrant errors: Postgres marked as embeddings_generated=False
        
        Note:
            This method is idempotent by default. Calling it multiple times
            with the same ticker will not reprocess unless force_reprocess=True.
        """
        ticker = ticker.upper()
        
        logger.info(f"Processing {ticker} {filing_type}...")
        
        # Step 1: Check if already exists
        if not force_reprocess:
            existing = self.check_filing_exists(ticker, filing_type)
            if existing and existing['status'] == 'ready':
                logger.info(f"Filing already exists and is ready: {ticker} {filing_type}")
                return {
                    "status": "already_exists",
                    "message": f"Filing for {ticker} {filing_type} already processed",
                    "filing": existing
                }
        
        try:
            # Step 2: Ensure company exists
            with self.db_storage.get_session() as session:
                company = session.query(Company).filter(
                    Company.ticker == ticker
                ).first()
                
                if not company:
                    # Create company entry (we'll get details from filing)
                    company = Company(ticker=ticker, name=ticker)
                    session.add(company)
                    session.commit()
                    logger.info(f"Created company entry: {ticker}")
            
            # Step 3: Fetch filing from SEC
            logger.info(f"Fetching {ticker} {filing_type} from SEC EDGAR...")
            filings = self.sec_client.get_company_filings(
                ticker=ticker,
                filing_types=[filing_type],  # Pass as list
                limit=1
            )
            
            if not filings:
                return {
                    "status": "error",
                    "message": f"No {filing_type} filings found for {ticker}"
                }
            
            filing_meta_raw = filings[0]
            
            # Convert camelCase keys to snake_case for consistency
            from datetime import datetime
            filing_meta = {
                'report_date': datetime.strptime(filing_meta_raw['reportDate'], '%Y-%m-%d').date(),
                'filing_date': datetime.strptime(filing_meta_raw['filingDate'], '%Y-%m-%d').date() if filing_meta_raw.get('filingDate') else None,
                'accession_number': filing_meta_raw['accessionNumber'],
                'document_url': filing_meta_raw['documentURL'],
            }
            
            # Step 4: Download HTML
            logger.info("Downloading filing document...")
            html_path = self.sec_client.download_filing(filing_meta_raw)
            
            # Step 5: Parse HTML
            logger.info("Parsing document...")
            parser = SECFilingParser(html_path)
            
            # Extract sections and tables
            sections = parser.extract_sections()
            tables = parser.extract_tables()
            
            # Combine into parsed document structure
            parsed_doc = {
                'sections': sections,
                'tables': tables
            }
            
            # Step 6: Chunk document
            logger.info("Chunking document...")
            chunks = self.chunker.chunk_filing(
                sections=parsed_doc['sections'],
                tables=parsed_doc['tables'],
                filing_metadata={
                    'ticker': ticker,
                    'filing_type': filing_type,
                    'report_date': filing_meta['report_date'],
                    'filing_date': filing_meta.get('filing_date'),
                    'accession_number': filing_meta['accession_number']
                }
            )
            
            # Step 7: Store in Postgres
            logger.info("Storing in Postgres...")
            filing = self.db_storage.save_filing_with_chunks(
                filing_metadata={
                    'ticker': ticker,
                    'form': filing_type,  # Note: method expects 'form' not 'filing_type'
                    'filing_date': filing_meta.get('filing_date'),
                    'report_date': filing_meta['report_date'],
                    'document_url': filing_meta.get('document_url'),
                    'document_path': html_path,
                    'accession_number': filing_meta['accession_number']
                },
                chunks_data=chunks
            )
            filing_id = filing.id
            
            # Step 8: Generate embeddings and store in Qdrant
            logger.info("Generating embeddings...")
            
            # Get chunks from database with all metadata
            with self.db_storage.get_session() as session:
                db_chunks = session.query(Chunk).filter(
                    Chunk.filing_id == filing_id
                ).all()
                
                # Format for vector store
                # Note: We don't include document_url here to avoid data duplication
                # It will be fetched from PostgreSQL when needed (see enrich_chunks_with_document_url)
                chunks_for_embedding = []
                for chunk in db_chunks:
                    chunk_text = getattr(chunk, 'text', None) or getattr(chunk, 'content', '')
                    chunks_for_embedding.append({
                        "id": chunk.id,
                        "filing_id": chunk.filing_id,
                        "ticker": ticker,
                        "filing_type": filing_type,
                        "report_date": filing_meta['report_date'].isoformat(),
                        "section": chunk.section,
                        "chunk_index": chunk.chunk_index,
                        "chunk_type": chunk.chunk_type or "text",
                        "text": chunk_text,
                    })
                
                # Upload to Qdrant
                self.vector_store.add_chunks(chunks_for_embedding, batch_size=100)
                
                # Mark as complete
                filing = session.query(SECFiling).filter(
                    SECFiling.id == filing_id
                ).first()
                if filing:
                    filing.embeddings_generated = True
                    session.commit()
            
            logger.info(f"✓ Successfully processed {ticker} {filing_type}")
            
            # Return success
            return {
                "status": "success",
                "message": f"Successfully processed {ticker} {filing_type}",
                "filing": {
                    "filing_id": str(filing_id),
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "report_date": filing_meta['report_date'].isoformat(),
                    "num_chunks": len(chunks),
                },
                "chunks_created": len(chunks),
                "embeddings_generated": len(chunks_for_embedding)
            }
        
        except Exception as e:
            logger.error(f"Error processing filing: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error processing filing: {str(e)}"
            }
    
    def get_or_process_filing(
        self,
        ticker: str,
        filing_type: str = "10-K"
    ) -> Dict:
        """
        Get filing from database or fetch and process it if missing.
        
        This is the recommended method for "lazy loading" filings. It provides
        a simple interface that automatically handles the complexity of checking
        existence and fetching when needed.
        
        This method is commonly used by:
        - Q&A endpoints: Ensure filing exists before answering questions
        - Batch processors: Process multiple filings with automatic deduplication
        - Background jobs: Populate database with filings on-demand
        
        Behavior:
        1. Check if filing exists and is ready (status="ready")
        2. If yes: Return immediately with existing filing info
        3. If no: Fetch from SEC and process through full pipeline
        
        Args:
            ticker (str): Company ticker symbol (e.g., "AAPL", "MSFT").
                Case-insensitive, normalized to uppercase internally.
            filing_type (str, optional): Type of SEC filing. Defaults to "10-K".
                Common types: "10-K" (annual), "10-Q" (quarterly).
        
        Returns:
            Dict: Result dictionary with status and filing information.
                If filing exists:
                {
                    "status": "exists",
                    "message": "Filing already available",
                    "filing": {
                        "filing_id": "uuid",
                        "ticker": "AAPL",
                        "filing_type": "10-K",
                        "report_date": "2024-09-28",
                        "num_chunks": 569,
                        "status": "ready",
                        ...
                    }
                }
                
                If filing processed:
                {
                    "status": "success",
                    "message": "Successfully processed AAPL 10-K",
                    "filing": {...},
                    "chunks_created": 569,
                    "embeddings_generated": 569
                }
                
                If error:
                {
                    "status": "error",
                    "message": "Error description"
                }
        
        Example:
            >>> service = FilingService(db, vs)
            >>> 
            >>> # Simple usage - handles everything automatically
            >>> result = service.get_or_process_filing("AAPL", "10-K")
            >>> 
            >>> if result['status'] in ['exists', 'success']:
            >>>     filing_id = result['filing']['filing_id']
            >>>     print(f"Filing ready: {filing_id}")
            >>> else:
            >>>     print(f"Error: {result['message']}")
            >>> 
            >>> # Use in Q&A endpoint
            >>> @app.post("/qa")
            >>> def answer_question(ticker: str, question: str):
            >>>     # Ensure filing exists
            >>>     result = service.get_or_process_filing(ticker)
            >>>     if result['status'] not in ['exists', 'success']:
            >>>         return {"error": result['message']}
            >>>     
            >>>     # Now safe to query
            >>>     answer = rag_chain.answer(question, ticker=ticker)
            >>>     return answer
        
        Performance:
            - If exists: <100ms (database query only)
            - If missing: 30-60 seconds (full pipeline)
        
        Thread Safety:
            Not thread-safe. If multiple threads call this simultaneously
            for the same ticker, both may attempt to process. Use a
            distributed lock or task queue for concurrent access.
        
        Note:
            This method will NOT reprocess existing filings. If you need
            to update an existing filing, use process_filing() with
            force_reprocess=True.
        """
        # Step 1: Check if filing already exists and is ready
        existing = self.check_filing_exists(ticker, filing_type)
        
        if existing and existing['status'] == 'ready':
            # Filing exists and is fully processed - return immediately
            logger.info(f"Filing found locally: {ticker} {filing_type}")
            return {
                "status": "exists",
                "message": f"Filing already available",
                "filing": existing
            }
        
        # Step 2: Filing doesn't exist or is incomplete - process it
        logger.info(f"Filing not found locally, fetching from SEC: {ticker} {filing_type}")
        return self.process_filing(ticker, filing_type)