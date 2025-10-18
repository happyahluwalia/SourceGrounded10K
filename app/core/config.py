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
    ollama_model: str = "gemma3:1b"
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
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