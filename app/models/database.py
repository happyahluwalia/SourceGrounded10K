# app/models/database.py

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    JSON,
    Date,
    UniqueConstraint,
    Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

from app.core.config import settings

# Create engine
engine = create_engine(settings.database_url)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Company(Base):
    """Company information."""
    __tablename__ = "companies"
    
    ticker = Column(String(10), primary_key=True)
    name = Column(Text)
    sector = Column(String(100))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    filings = relationship("SECFiling", back_populates="company", cascade="all, delete-orphan")


class SECFiling(Base):
    """SEC filings (10-K, 10-Q, etc.)."""
    __tablename__ = "sec_filings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("companies.ticker", ondelete="CASCADE"))
    filing_type = Column(String(10))  # 10-K, 10-Q, 8-K
    filing_date = Column(Date)
    report_date = Column(Date)
    document_url = Column(Text)
    document_path = Column(Text)  # Local file path
    processed = Column(Boolean, default=False)
    num_chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="filings")
    chunks = relationship("Chunk", back_populates="filing", cascade="all, delete-orphan")
    
    # Prevent duplicate filings
    __table_args__ = (
        UniqueConstraint('ticker', 'filing_type', 'report_date', name='uix_ticker_type_date'),
    )


class Chunk(Base):
    """
    Text chunks from SEC filings.
    
    Stores metadata only - full text lives in Qdrant.
    UUID primary key matches Qdrant document ID.
    """
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filing_id = Column(Integer, ForeignKey("sec_filings.id", ondelete="CASCADE"), nullable=False)
    
    # Store chunk text
    text = Column(Text, nullable=False) 

    # Content metadata
    section = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    total_chunks_in_section = Column(Integer)
    chunk_type = Column(String(20), nullable=False)  # 'section' or 'table'
    
    # Size info
    char_count = Column(Integer, nullable=False)
    token_count_estimate = Column(Integer)
    
    # Table-specific (nullable for non-table chunks)
    table_rows = Column(Integer)
    table_cols = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    filing = relationship("SECFiling", back_populates="chunks")
    
    # Indexes
    __table_args__ = (
        Index('idx_chunks_filing_id', 'filing_id'),
        Index('idx_chunks_section', 'section'),
        Index('idx_chunks_filing_section', 'filing_id', 'section'),
    )


class NewsArticle(Base):
    """News articles related to companies."""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("companies.ticker"))
    title = Column(Text)
    url = Column(Text)
    published_at = Column(DateTime)
    sentiment = Column(Float)  # -1 to 1
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")


class Query(Base):
    """User queries for evaluation."""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10))
    question = Column(Text)
    answer = Column(Text)
    retrieved_chunks = Column(JSON)
    faithfulness_score = Column(Float)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables)."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")


def drop_all():
    """Drop all tables (for testing)."""
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped!")


if __name__ == "__main__":
    init_db()