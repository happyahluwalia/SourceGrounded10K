"""
Database models using SQLAlchemy ORM.
"""
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
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

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
    filings = relationship("SECFiling", back_populates="company")
    news = relationship("NewsArticle", back_populates="company")


class SECFiling(Base):
    """SEC filings (10-K, 10-Q, etc.)."""
    __tablename__ = "sec_filings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("companies.ticker"))
    filing_type = Column(String(10))  # 10-K, 10-Q, 8-K
    filing_date = Column(DateTime)
    document_url = Column(Text)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="filings")


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
    company = relationship("Company", back_populates="news")


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


if __name__ == "__main__":
    init_db()