# Quick Production Deployment Reference

## TL;DR - Copy/Paste Commands

### 1. Pull Models (on Digital Ocean droplet)

```bash
# Pull embedding model
docker exec -it financeagent_ollama ollama pull nomic-embed-text

# Pull LLM (recommended)
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct

# Verify
docker exec -it financeagent_ollama ollama list
```

### 2. Environment Variables (.env)

```bash
# Core settings
OLLAMA_MODEL=phi3:mini-instruct
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768
CHUNK_SIZE=2048
CHUNK_OVERLAP=300

# Connection strings (update for production)
DATABASE_URL=postgresql://postgres:your_password@postgres:5432/financeagent
OLLAMA_BASE_URL=http://ollama:11434
QDRANT_HOST=qdrant
REDIS_HOST=redis
```

### 3. Recreate Qdrant Collection (REQUIRED)

```bash
# Delete old collection
curl -X DELETE http://localhost:6333/collections/financial_documents

# Restart app to auto-create with 768-dim
docker-compose restart app
```

### 4. Deploy

```bash
git pull origin main
docker-compose build
docker-compose up -d
docker-compose logs -f app
```

### 5. Verify Setup

```bash
# Run verification script (checks everything automatically)
docker exec -it financeagent_app python scripts/verify_production_models.py

# What it checks:
# ✓ Ollama connection
# ✓ Embedding model available and working
# ✓ LLM model available and working
# ✓ Qdrant collection dimensions match
# ✓ Chunk size configuration

# Check health endpoint
curl http://localhost:8000/health
```

## Model Comparison

| Model | Params | RAM | Speed | Quality | Recommendation |
|-------|--------|-----|-------|---------|----------------|
| **phi3:mini-instruct** | 3.8B | ~3GB | Fast | Good | ✅ **Start here** |
| llama3.1:8b-instruct | 8B | ~6GB | Medium | Better | ⚠️ Only if needed |
| gemma:1b (old) | 1B | ~1.5GB | Very Fast | Basic | ❌ Too basic |

## Embedding Comparison

| Model | Dimensions | Context | RAM (10K vecs) | Recommendation |
|-------|------------|---------|----------------|----------------|
| **nomic-embed-text-v1.5** | 768 | 8K | ~31MB | ✅ **Use this** |
| BGE-large-en-v1.5 (old) | 1024 | 512 | ~41MB | ❌ Smaller context |
| all-MiniLM-L6-v2 (old) | 384 | 256 | ~15MB | ❌ Too small |

## Memory Budget (8GB Droplet)

```
Total RAM: 8GB
─────────────────────
System:     0.5GB
Postgres:   0.3GB
Qdrant:     0.5GB
Redis:      0.1GB
Nginx:      0.05GB
─────────────────────
Used:       1.45GB
Available:  6.55GB

Phi-3:      3GB ✅ (3.5GB buffer)
Llama 3.1:  6GB ⚠️ (0.5GB buffer)
```

## Troubleshooting One-Liners

```bash
# Model not found
docker exec -it financeagent_ollama ollama pull <model-name>

# Dimension mismatch
curl -X DELETE http://localhost:6333/collections/financial_documents
docker-compose restart app

# Out of memory
docker-compose restart ollama
# Then switch to phi3 in .env

# Check memory
docker stats
free -h

# View logs
docker-compose logs -f app | grep -E "(ERROR|Embedding|LLM)"
```

## Performance Expectations

### Embedding Generation
- **500 chunks**: ~40-50 seconds
- **1000 chunks**: ~80-100 seconds

### LLM Queries
- **Simple query**: 3-5 seconds
- **Complex query**: 5-10 seconds

### Memory Usage
- **Idle**: 2.5GB
- **Processing**: 4-5GB
- **Peak**: <6GB (safe)

## Rollback (if needed)

```bash
# Revert to old models
docker exec -it financeagent_ollama ollama pull gemma:1b

# Update .env
OLLAMA_MODEL=gemma:1b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=75

# Recreate collection
curl -X DELETE http://localhost:6333/collections/financial_documents
docker-compose restart
```

## Pre-Deployment Checklist

- [ ] Models pulled: `ollama list` shows nomic-embed-text and phi3
- [ ] .env updated with new settings
- [ ] Qdrant collection deleted (dimension change)
- [ ] Code deployed: `git pull && docker-compose build`
- [ ] Services started: `docker-compose up -d`
- [ ] Verification passed: `python scripts/verify_production_models.py`
- [ ] Health check: `curl http://localhost:8000/health`
- [ ] Test query works
- [ ] Memory usage <6GB: `docker stats`

## When to Upgrade to Llama 3.1

Upgrade if you need:
- Better reasoning on complex queries
- More accurate financial analysis
- Willing to monitor memory closely

Don't upgrade if:
- Phi-3 quality is sufficient
- Want maximum stability
- Running other services on same droplet
