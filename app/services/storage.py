# app/services/storage.py
# Database storage layer for SEC filings and chunks

# SQLAlchemy imports for database operations
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
# Type hints for better code clarity
from typing import List, Dict, Optional
from datetime import datetime, date
from contextlib import contextmanager
# UUID for generating unique chunk identifiers (shared with Qdrant)
import uuid

# Import database models and session factory
from app.models.database import SessionLocal, Company, SECFiling, Chunk


class DatabaseStorage:
    """
    Manages persistent storage of SEC filings and chunks.
    
    Responsibilities:
    - Save filing metadata to Postgres
    - Save chunk metadata to Postgres (text lives in Qdrant)
    - Handle duplicates (delete and replace)
    - Maintain referential integrity
    """
    
    def __init__(self):
        # Lazy session initialization - only create when needed
        self.session: Optional[Session] = None
    
    def _get_session(self) -> Session:
        """Get or create session."""
        # Lazy initialization pattern - create session on first use
        if self.session is None:
            self.session = SessionLocal()
        return self.session
    
    @contextmanager
    def get_session(self):
        """
        Get a database session as a context manager.
        
        This allows using the session with 'with' statement:
            with db_storage.get_session() as session:
                # use session
                pass
        
        The session is automatically closed after the block.
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database session."""
        # Clean up database connection - important to avoid connection leaks
        if self.session:
            self.session.close()
            self.session = None
    
    def upsert_company(self, ticker: str, name: str = None, sector: str = None) -> Company:
        """
        Create or update company record.
        
        Args:
            ticker: Stock ticker
            name: Company name (optional)
            sector: Business sector (optional)
            
        Returns:
            Company object
        """
        session = self._get_session()
        
        # Check if company already exists in database
        company = session.query(Company).filter_by(ticker=ticker).first()
        
        if company:
            # Update existing company with new information (if provided)
            if name:
                company.name = name
            if sector:
                company.sector = sector
            company.last_updated = datetime.utcnow()
        else:
            # Create new company record
            company = Company(
                ticker=ticker,
                name=name,
                sector=sector
            )
            session.add(company)
        
        # Commit changes to database
        session.commit()
        return company
    
    def get_filing(
        self, 
        ticker: str, 
        filing_type: str, 
        report_date: date
    ) -> Optional[SECFiling]:
        """
        Get existing filing by unique identifiers.
        
        Args:
            ticker: Stock ticker
            filing_type: Form type (10-K, 10-Q)
            report_date: Report date
            
        Returns:
            SECFiling if exists, None otherwise
        """
        session = self._get_session()
        
        # Query by unique constraint (ticker + filing_type + report_date)
        # This combination uniquely identifies a filing
        return session.query(SECFiling).filter_by(
            ticker=ticker,
            filing_type=filing_type,
            report_date=report_date
        ).first()
    
    def delete_filing(self, filing_id: int):
        """
        Delete filing and all associated chunks (cascade).
        
        Args:
            filing_id: Filing ID to delete
        """
        session = self._get_session()
        
        # Find the filing to delete
        filing = session.query(SECFiling).filter_by(id=filing_id).first()
        if filing:
            # Log deletion (includes chunk count for visibility)
            print(f"   Deleting existing filing (ID: {filing_id}) and {filing.num_chunks} chunks...")
            # Delete filing - chunks are automatically deleted via cascade relationship
            session.delete(filing)
            session.commit()
    
    def save_filing_with_chunks(
        self,
        filing_metadata: Dict,
        chunks_data: List[Dict]
    ) -> SECFiling:
        """
        Save filing and chunks in a single transaction.
        
        This is the main method for persisting processed filings.
        
        Flow:
        1. Upsert company
        2. Check for existing filing (delete if exists)
        3. Insert filing
        4. Generate UUIDs for chunks
        5. Bulk insert chunks
        6. Update filing stats
        
        Args:
            filing_metadata: Dict with filing info
            chunks_data: List of chunk dicts
            
        Returns:
            Created SECFiling object
            
        Raises:
            Exception if transaction fails (with rollback)
        """
        session = self._get_session()
        
        try:
            # 1. Upsert company (ensure company record exists)
            print(f"\n1. Upserting company: {filing_metadata['ticker']}")
            company = self.upsert_company(
                ticker=filing_metadata['ticker'],
                name=filing_metadata.get('company_name')
            )
            
            # 2. Check for existing filing (handle duplicates)
            print(f"2. Checking for existing filing...")
            existing = self.get_filing(
                ticker=filing_metadata['ticker'],
                filing_type=filing_metadata['form'],
                report_date=filing_metadata['report_date']
            )
            
            # If filing already exists, delete it (will be replaced with new version)
            if existing:
                self.delete_filing(existing.id)
            
            # 3. Insert filing record
            print(f"3. Creating filing record...")
            filing = SECFiling(
                ticker=filing_metadata['ticker'],
                filing_type=filing_metadata['form'],
                filing_date=filing_metadata['filing_date'],
                report_date=filing_metadata['report_date'],
                document_url=filing_metadata.get('document_url'),
                document_path=filing_metadata.get('document_path'),
                processed=False  # Will set to True after chunks are saved
            )
            session.add(filing)
            # Flush to get filing.id without committing transaction
            # This allows us to use filing.id for foreign keys in chunks
            session.flush()
            
            print(f"   Filing ID: {filing.id}")
            
            # 4. Generate UUIDs and create chunk objects
            print(f"4. Preparing {len(chunks_data)} chunks...")
            chunk_objects = []
            
            for chunk_data in chunks_data:
                # Generate UUID - this will be the primary key in both Postgres and Qdrant
                # Using the same ID ensures we can link metadata (Postgres) to vectors (Qdrant)
                chunk_id = uuid.uuid4()
                
                # Store UUID back in chunk_data so it can be used when saving to Qdrant
                chunk_data['id'] = chunk_id
                
                # Create Chunk ORM object with metadata
                # Note: actual text content is NOT stored here (goes to Qdrant)
                chunk = Chunk(
                    id=chunk_id,  # UUID primary key
                    filing_id=filing.id,  # Foreign key to filing
                    text=chunk_data['text'],
                    section=chunk_data['section'],  # Section name for filtering
                    chunk_index=chunk_data['chunk_index'],  # Position within section
                    total_chunks_in_section=chunk_data.get('total_chunks_in_section'),
                    chunk_type=chunk_data['chunk_type'],  # 'section' or 'table'
                    char_count=chunk_data['char_count'],  # Size metrics
                    token_count_estimate=chunk_data.get('token_count_estimate'),
                    table_rows=chunk_data.get('table_rows'),  # Table-specific metadata
                    table_cols=chunk_data.get('table_cols')
                )
                chunk_objects.append(chunk)
            
            # 5. Bulk insert chunks (more efficient than individual inserts)
            print(f"5. Bulk inserting {len(chunk_objects)} chunks...")
            # bulk_save_objects is faster than adding one-by-one for large datasets
            session.bulk_save_objects(chunk_objects)
            
            # 6. Update filing statistics
            filing.num_chunks = len(chunk_objects)
            filing.processed = True  # Mark as successfully processed
            
            # Commit entire transaction (filing + all chunks)
            # If this fails, everything rolls back (atomicity)
            print(f"6. Committing transaction...")
            session.commit()
            
            print(f"✅ Successfully saved filing with {len(chunk_objects)} chunks")
            
            return filing
            
        except Exception as e:
            # If anything fails, rollback entire transaction
            # This ensures we don't have partial data (filing without chunks, etc.)
            print(f"❌ Error saving filing: {e}")
            session.rollback()
            raise  # Re-raise exception for caller to handle
    
    def get_chunks_for_filing(self, filing_id: int) -> List[Chunk]:
        """Get all chunks for a filing."""
        session = self._get_session()
        # Return all chunks associated with this filing
        return session.query(Chunk).filter_by(filing_id=filing_id).all()
    
    def get_chunks_by_section(self, filing_id: int, section: str) -> List[Chunk]:
        """Get chunks for a specific section."""
        session = self._get_session()
        # Filter chunks by both filing and section name
        # Useful for retrieving specific parts of a filing (e.g., only Risk Factors)
        return session.query(Chunk).filter_by(
            filing_id=filing_id,
            section=section
        ).all()
    
    def get_filing_stats(self, ticker: str) -> List[Dict]:
        """
        Get statistics for all filings of a company.
        
        Returns:
            List of dicts with filing info and chunk counts
        """
        session = self._get_session()
        
        # Get all filings for this company
        filings = session.query(SECFiling).filter_by(ticker=ticker).all()
        
        # Convert ORM objects to dictionaries for easier consumption
        stats = []
        for filing in filings:
            stats.append({
                'id': filing.id,
                'filing_type': filing.filing_type,  # 10-K, 10-Q, etc.
                'filing_date': filing.filing_date,  # When filed with SEC
                'report_date': filing.report_date,  # Fiscal period end date
                'num_chunks': filing.num_chunks,  # How many chunks created
                'processed': filing.processed  # Whether processing completed
            })
        
        return stats


def convert_date_strings(metadata: Dict) -> Dict:
    """
    Convert date strings to date objects for database storage.
    
    Args:
        metadata: Dict with string dates
        
    Returns:
        Dict with date objects
    """
    from datetime import datetime
    
    # Create a copy to avoid mutating original dict
    result = metadata.copy()
    
    # Convert date strings to Python date objects
    # SQLAlchemy Date columns require date objects, not strings
    date_fields = ['filing_date', 'report_date']
    for field in date_fields:
        if field in result and isinstance(result[field], str):
            # Parse "YYYY-MM-DD" format (ISO 8601)
            # .date() extracts just the date part (no time)
            result[field] = datetime.strptime(result[field], '%Y-%m-%d').date()
    
    return result