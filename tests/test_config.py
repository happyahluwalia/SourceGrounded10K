from app.core.config import settings

print("=== Configuration Test ===")
print(f"App Name: {settings.app_name}")
print(f"Database: {settings.database_url}")
print(f"Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
print(f"Redis: {settings.redis_host}:{settings.redis_port}")
print(f"Ollama: {settings.ollama_base_url}")
print(f"Embedding Model: {settings.embedding_model}")
print(f"SEC User Agent: {settings.sec_user_agent}")
print("\n✅ Configuration loaded successfully!")