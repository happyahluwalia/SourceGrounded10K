"""
Configuration management using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "FinanceAgent"
    debug: bool = False  # Changed to False for production
    log_level: str = "INFO"
    
    # Security
    cors_origins: str = "*"  # Comma-separated list, use "*" for development
    api_key: str = ""  # Optional API key for authentication
    enable_debug_logs: bool = True  # Control debug log streaming to UI
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 100
    
    # Database
    database_url: str
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "financial_documents"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"  # Production: 8B params for Quadro P4000
    
    # Embeddings
    embedding_model: str = "nomic-embed-text"  # Production: 768-dim, 8K context
    embedding_dimension: int = 768  # Changed from 384 to match nomic model
    
    # Chunking
    # Context window math for phi3 (4K tokens):
    # - 5 chunks × 1024 chars/chunk = 5,120 chars
    # - 5,120 chars ÷ 4 chars/token ≈ 1,280 tokens (31% of context)
    # - Prompt overhead: ~200 tokens
    # - Answer: 500 tokens
    # - Total: ~1,980 tokens (48% utilization, leaves 2K buffer)
    chunk_size: int = 1024  # Balanced for phi3's 4K context
    chunk_overlap: int = 150  # ~15% of 1024
    
    # RAG Settings
    top_k: int = 5  # Number of chunks to retrieve from Qdrant
    score_threshold: float = 0.5  # Minimum similarity score (0-1)
    max_tokens: int = 500  # Maximum tokens in LLM response
    
    # Batch Processing
    embedding_batch_size: int = 32  # Batch size for embedding generation
    qdrant_upload_batch_size: int = 100  # Batch size for Qdrant uploads
    
    # SEC
    sec_user_agent: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Create settings instance (cached).
    
    Using lru_cache ensures we only load settings once.
    """
    return Settings()


# For easy import
settings = get_settings()