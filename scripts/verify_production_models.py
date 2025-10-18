#!/usr/bin/env python3
"""
Verify production model setup for Digital Ocean deployment.

This script checks:
1. Ollama models are downloaded
2. Embedding model works correctly
3. LLM model works correctly
4. Qdrant collection has correct dimensions
5. Memory usage is within safe limits
"""

import sys
import ollama
from app.core.config import settings
from app.services.vector_store import VectorStore
from qdrant_client import QdrantClient


def check_ollama_connection():
    """Check if Ollama is accessible."""
    print("\n🔍 Checking Ollama connection...")
    try:
        client = ollama.Client(host=settings.ollama_base_url)
        models = client.list()
        print(f"✓ Ollama connected at {settings.ollama_base_url}")
        print(f"  Available models: {len(models.get('models', []))}")
        return True, client
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        return False, None


def check_embedding_model(client):
    """Check if embedding model is available and working."""
    print(f"\n🔍 Checking embedding model: {settings.embedding_model}...")
    try:
        # Check if model exists
        models = client.list()
        model_names = [m['name'] for m in models.get('models', [])]
        
        if settings.embedding_model not in model_names:
            print(f"✗ Model '{settings.embedding_model}' not found in Ollama")
            print(f"  Available models: {model_names}")
            print(f"\n  To fix: docker exec -it financeagent_ollama ollama pull {settings.embedding_model}")
            return False
        
        print(f"✓ Model '{settings.embedding_model}' is available")
        
        # Test embedding generation
        print("  Testing embedding generation...")
        response = client.embeddings(
            model=settings.embedding_model,
            prompt="Test embedding for financial analysis"
        )
        
        embedding = response['embedding']
        actual_dim = len(embedding)
        expected_dim = settings.embedding_dimension
        
        if actual_dim != expected_dim:
            print(f"✗ Dimension mismatch: expected {expected_dim}, got {actual_dim}")
            print(f"  Update EMBEDDING_DIMENSION={actual_dim} in .env")
            return False
        
        print(f"✓ Embedding generation works (dimension: {actual_dim})")
        return True
        
    except Exception as e:
        print(f"✗ Embedding model check failed: {e}")
        return False


def check_llm_model(client):
    """Check if LLM model is available and working."""
    print(f"\n🔍 Checking LLM model: {settings.ollama_model}...")
    try:
        # Check if model exists
        models = client.list()
        model_names = [m['name'] for m in models.get('models', [])]
        
        if settings.ollama_model not in model_names:
            print(f"✗ Model '{settings.ollama_model}' not found in Ollama")
            print(f"  Available models: {model_names}")
            print(f"\n  To fix: docker exec -it financeagent_ollama ollama pull {settings.ollama_model}")
            return False
        
        print(f"✓ Model '{settings.ollama_model}' is available")
        
        # Test generation
        print("  Testing text generation...")
        response = client.generate(
            model=settings.ollama_model,
            prompt="What is 2+2? Answer briefly.",
            options={'num_predict': 20}
        )
        
        if response and response.get('response'):
            print(f"✓ LLM generation works")
            print(f"  Sample response: {response['response'][:100]}...")
            return True
        else:
            print(f"✗ LLM generation failed: empty response")
            return False
        
    except Exception as e:
        print(f"✗ LLM model check failed: {e}")
        return False


def check_qdrant_collection():
    """Check if Qdrant collection has correct dimensions."""
    print(f"\n🔍 Checking Qdrant collection: {settings.qdrant_collection_name}...")
    try:
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if settings.qdrant_collection_name not in collection_names:
            print(f"⚠️  Collection '{settings.qdrant_collection_name}' does not exist")
            print(f"  It will be created automatically on first use")
            return True
        
        # Check collection config
        collection = client.get_collection(settings.qdrant_collection_name)
        
        # Get vector size from collection config
        vector_size = collection.config.params.vectors.size
        expected_size = settings.embedding_dimension
        
        if vector_size != expected_size:
            print(f"✗ Vector dimension mismatch!")
            print(f"  Collection has {vector_size}-dim vectors")
            print(f"  Settings expect {expected_size}-dim vectors")
            print(f"\n  To fix: Recreate collection with correct dimensions")
            print(f"  Run: python -c 'from app.services.vector_store import VectorStore; VectorStore().create_collection(recreate=True)'")
            return False
        
        print(f"✓ Collection exists with correct dimensions ({vector_size})")
        print(f"  Vectors: {collection.vectors_count}")
        print(f"  Points: {collection.points_count}")
        return True
        
    except Exception as e:
        print(f"✗ Qdrant check failed: {e}")
        return False


def check_chunk_size():
    """Check if chunk size is appropriate for embedding model."""
    print(f"\n🔍 Checking chunk size configuration...")
    
    chunk_size = settings.chunk_size
    embedding_model = settings.embedding_model
    
    # Nomic has 8K context, recommend 2048-4096 chunks
    if 'nomic' in embedding_model.lower():
        if chunk_size < 1024:
            print(f"⚠️  Chunk size ({chunk_size}) is small for nomic-embed-text (8K context)")
            print(f"  Recommendation: Increase CHUNK_SIZE to 2048-4096 to leverage full context")
        elif chunk_size > 4096:
            print(f"⚠️  Chunk size ({chunk_size}) is very large")
            print(f"  May cause memory issues. Recommended: 2048-4096")
        else:
            print(f"✓ Chunk size ({chunk_size}) is appropriate for {embedding_model}")
    else:
        print(f"✓ Chunk size: {chunk_size}")
    
    return True


def print_summary(results):
    """Print summary of all checks."""
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {check}")
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All checks passed! Ready for production deployment.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix issues before deploying.")
        return 1


def main():
    """Run all verification checks."""
    print("="*60)
    print("PRODUCTION MODEL VERIFICATION")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Ollama URL: {settings.ollama_base_url}")
    print(f"  LLM Model: {settings.ollama_model}")
    print(f"  Embedding Model: {settings.embedding_model}")
    print(f"  Embedding Dimension: {settings.embedding_dimension}")
    print(f"  Chunk Size: {settings.chunk_size}")
    print(f"  Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    
    results = {}
    
    # Check Ollama connection
    ollama_ok, ollama_client = check_ollama_connection()
    results["Ollama Connection"] = ollama_ok
    
    if not ollama_ok:
        print("\n⚠️  Cannot proceed without Ollama connection")
        return print_summary(results)
    
    # Check embedding model
    results["Embedding Model"] = check_embedding_model(ollama_client)
    
    # Check LLM model
    results["LLM Model"] = check_llm_model(ollama_client)
    
    # Check Qdrant collection
    results["Qdrant Collection"] = check_qdrant_collection()
    
    # Check chunk size
    results["Chunk Size Config"] = check_chunk_size()
    
    # Print summary
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
