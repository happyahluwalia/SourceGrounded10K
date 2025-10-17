"""
Set up Qdrant collection and upload existing chunks.

This script:
1. Creates Qdrant collection
2. Fetches all chunks from Postgres
3. Generates embeddings
4. Uploads to Qdrant
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_store import VectorStore
from app.services.storage import DatabaseStorage
from app.services.sec_parser import SECFilingParser
from app.services.chunker import FinancialDocumentChunker
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Set up vector database with existing chunks."""
    
    # Initialize services
    vector_store = VectorStore(
        host="localhost",
        port=6333,
        collection_name="financial_filings"
    )
    
    db_storage = DatabaseStorage()  # No arguments needed
    
    # Step 1: Create collection (or recreate if exists)
    logger.info("Creating Qdrant collection...")
    vector_store.create_collection(recreate=False)  # Set True to wipe and start fresh
    
    # Step 2: Fetch all chunks from Postgres
    logger.info("Fetching chunks from Postgres...")
    
    try:
        # Get all processed filings
        from app.models.database import SECFiling, Chunk
        
        session = db_storage._get_session()
        
        filings = session.query(SECFiling).filter(
            SECFiling.processed == True
        ).all()
        
        all_chunks = []
        for filing in filings:
            chunks = session.query(Chunk).filter(
                Chunk.filing_id == filing.id
            ).all()
            
            for chunk in chunks:
                all_chunks.append({
                    "id": chunk.id,
                    "filing_id": chunk.filing_id,
                    "ticker": filing.ticker,
                    "filing_type": filing.filing_type,
                    "report_date": filing.report_date.isoformat(),
                    "section": chunk.section,
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    "text": chunk.text,
                })
        
        logger.info(f"Found {len(all_chunks)} chunks from {len(filings)} filings")
        
        # Step 3: Upload to Qdrant (with embeddings)
        # Note: add_chunks() handles deduplication automatically
        if all_chunks:
            vector_store.add_chunks(all_chunks, batch_size=100)
        else:
            logger.warning("No chunks found to upload")
        
        logger.info("✓ Vector database setup complete!")
    
    finally:
        # Always close database connection
        db_storage.close()


if __name__ == "__main__":
    main()