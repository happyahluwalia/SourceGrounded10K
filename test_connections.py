"""
Test all service connections.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from qdrant_client import QdrantClient
import redis
import requests

try:
    import pytest
except ImportError:
    pytest = None


def test_postgres_connection():
    """Test PostgreSQL connection."""
    
    from app.models.database import engine
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("✅ Postgres connection successful")


def test_qdrant_connection():
    """Test Qdrant connection."""
    from app.core.config import settings
    
    client = QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port
    )
    
    # Check if service is ready
    collections = client.get_collections()
    assert collections is not None
    print(f"✅ Qdrant connection successful (collections: {len(collections.collections)})")


def test_redis_connection():
    """Test Redis connection."""
    from app.core.config import settings
    
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db
    )
    
    # Test set/get
    r.set("test_key", "test_value")
    assert r.get("test_key").decode() == "test_value"
    r.delete("test_key")
    print("✅ Redis connection successful")


def test_ollama_connection():
    """Test Ollama connection."""
    from app.core.config import settings
    
    response = requests.get(f"{settings.ollama_base_url}/api/tags")
    assert response.status_code == 200
    
    models = response.json().get("models", [])
    model_names = [m["name"] for m in models]
    
    print(f"✅ Ollama connection successful")
    print(f"   Available models: {model_names}")


if __name__ == "__main__":
    """Run all tests manually."""
    print("\n=== Testing Service Connections ===\n")
    
    try:
        test_postgres_connection()
    except Exception as e:
        print(f"❌ Postgres failed: {e}")
    
    try:
        test_qdrant_connection()
    except Exception as e:
        print(f"❌ Qdrant failed: {e}")
    
    try:
        test_redis_connection()
    except Exception as e:
        print(f"❌ Redis failed: {e}")
    
    try:
        test_ollama_connection()
    except Exception as e:
        print(f"❌ Ollama failed: {e}")
    
    print("\n=== All Tests Complete ===\n")