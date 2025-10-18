# Production Deployment Guide - Digital Ocean 8GB Droplet

## Model Configuration

### Selected Models

#### Embeddings: `nomic-embed-text-v1.5`
- **Dimensions**: 768 (vs BGE's 1024 = 25% memory savings)
- **Context Window**: 8K tokens (vs BGE's 512 = 16x larger)
- **Memory**: ~31MB for 10K vectors (vs ~41MB for BGE)
- **Why**: Better for long financial documents, native Ollama support

#### LLM: `phi3:mini-instruct`
- **Parameters**: 3.8B
- **Memory**: ~3GB (model + inference)
- **Why**: Stable on 8GB RAM with ~3.5GB buffer for other services
- **Alternative**: `llama3.1:8b-instruct` (higher quality, riskier - only if needed)

### Memory Budget (8GB Droplet)

```
Component               Memory
─────────────────────────────────
System/OS               ~500MB
PostgreSQL              ~300MB
Qdrant (10K vectors)    ~500MB
Redis                   ~100MB
Nginx                    ~50MB
─────────────────────────────────
Subtotal               ~1.45GB

Available for Ollama   ~6.5GB
─────────────────────────────────
Phi-3 (recommended)     ~3GB ✅
Llama 3.1 (optional)    ~6GB ⚠️
```

## Deployment Steps

### 1. Pull Models in Ollama Container

```bash
# SSH into your Digital Ocean droplet
ssh root@your-droplet-ip

# Pull the embedding model
docker exec -it financeagent_ollama ollama pull nomic-embed-text

# Pull the LLM (start with phi3)
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct

# Optional: Pull Llama 3.1 if you need more reasoning power
# docker exec -it financeagent_ollama ollama pull llama3.1:8b-instruct

# Verify models are downloaded
docker exec -it financeagent_ollama ollama list
```

### 2. Update Environment Variables

Create/update your `.env` file on the droplet:

```bash
# .env file

# Database
DATABASE_URL=postgresql://postgres:your_secure_password@postgres:5432/financeagent

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=financial_documents

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=phi3:mini-instruct

# Embeddings
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768

# Chunking (leverage nomic's 8K context)
CHUNK_SIZE=2048
CHUNK_OVERLAP=300

# SEC API
SEC_USER_AGENT=YourName your.email@example.com

# Security
CORS_ORIGINS=https://yourdomain.com
API_KEY=your_secure_api_key_here

# Postgres
POSTGRES_DB=financeagent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
```

### 3. Recreate Qdrant Collection

**IMPORTANT**: The embedding dimension changed from 1024 → 768, so you must recreate the Qdrant collection.

```bash
# Option A: Delete and recreate via Python script
docker exec -it financeagent_app python -c "
from app.services.vector_store import VectorStore
vs = VectorStore()
vs.create_collection(recreate=True)
print('✓ Collection recreated with 768-dim vectors')
"

# Option B: Delete via Qdrant API
curl -X DELETE http://localhost:6333/collections/financial_documents

# Then restart your app to auto-create the collection
docker-compose restart app
```

### 4. Reprocess Existing Filings (if any)

If you have existing filings in PostgreSQL, you need to regenerate embeddings:

```bash
# Mark all filings as needing re-embedding
docker exec -it financeagent_postgres psql -U postgres -d financeagent -c "
UPDATE sec_filings SET embeddings_generated = false;
"

# Reprocess filings using your script
docker exec -it financeagent_app python scripts/reprocess_embeddings.py
```

### 5. Deploy Application

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f app
docker-compose logs -f ollama

# Verify health
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

### 6. Monitor Performance

```bash
# Watch memory usage
docker stats

# Check Ollama model loading
docker exec -it financeagent_ollama ollama ps

# Monitor application logs
docker-compose logs -f app | grep -E "(Embedding|LLM|Memory)"
```

## Performance Expectations

### Embedding Generation
- **Old (BGE)**: ~30 seconds for 500 chunks
- **New (Nomic)**: ~40-50 seconds for 500 chunks (sequential API calls)
- **Note**: Slightly slower but worth it for 8K context window

### LLM Inference
- **Old (Gemma 1B)**: ~2-3 seconds per query
- **New (Phi-3)**: ~3-5 seconds per query (better quality, slightly slower)

### Memory Usage
- **Idle**: ~2.5GB total
- **Under Load**: ~4-5GB total (safe buffer remaining)

## Troubleshooting

### Out of Memory Errors

```bash
# Check memory usage
free -h
docker stats

# If Ollama OOM:
# 1. Restart Ollama container
docker-compose restart ollama

# 2. Consider switching to smaller model
# Update .env: OLLAMA_MODEL=phi3:mini-instruct
```

### Slow Embedding Generation

```bash
# Check if model is loaded
docker exec -it financeagent_ollama ollama ps

# Preload model to avoid cold start
docker exec -it financeagent_ollama ollama run nomic-embed-text "test"
```

### Wrong Vector Dimensions Error

```bash
# Error: "Vector dimension mismatch: expected 1024, got 768"
# Solution: Recreate Qdrant collection (see Step 3)

docker exec -it financeagent_app python -c "
from app.services.vector_store import VectorStore
vs = VectorStore()
vs.create_collection(recreate=True)
"
```

## Upgrade Path to Llama 3.1 (Optional)

If you need better reasoning and are willing to risk memory pressure:

```bash
# 1. Pull model
docker exec -it financeagent_ollama ollama pull llama3.1:8b-instruct

# 2. Update .env
# OLLAMA_MODEL=llama3.1:8b-instruct

# 3. Restart app
docker-compose restart app

# 4. Monitor memory closely
watch -n 1 free -h
```

**Warning**: Llama 3.1 8B leaves only ~500MB buffer. Monitor for OOM kills.

## Rollback Plan

If production issues occur:

```bash
# 1. Revert to old models
docker exec -it financeagent_ollama ollama pull gemma:1b

# 2. Update .env
# OLLAMA_MODEL=gemma:1b
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# EMBEDDING_DIMENSION=384
# CHUNK_SIZE=512
# CHUNK_OVERLAP=75

# 3. Recreate Qdrant collection for 384-dim
# 4. Restart services
docker-compose restart
```

## Production Checklist

- [ ] Models pulled in Ollama container
- [ ] `.env` file updated with new settings
- [ ] Qdrant collection recreated (768-dim)
- [ ] Existing filings re-embedded (if any)
- [ ] Application deployed and healthy
- [ ] Memory usage monitored (<6GB total)
- [ ] Test queries returning good results
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured

## Cost Optimization

### If Memory is Tight

1. **Reduce Qdrant memory**:
   - Set `QDRANT__STORAGE__OPTIMIZERS__MEMMAP_THRESHOLD=20000` in docker-compose.yml
   - Uses disk instead of RAM for large collections

2. **Limit concurrent requests**:
   - Set `workers=1` in uvicorn (app already single-worker)
   - Add rate limiting (already configured)

3. **Use smaller LLM**:
   - Stick with `phi3:mini-instruct` (don't upgrade to Llama 3.1)

### If Need More Performance

1. **Upgrade to 16GB Droplet** ($24/mo → $48/mo):
   - Run Llama 3.1 8B safely
   - Increase uvicorn workers to 2-4
   - Better concurrent request handling

2. **Separate Ollama to dedicated instance**:
   - App + DB on 4GB droplet
   - Ollama on 8GB droplet
   - Better isolation and scaling

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Monitor memory: `docker stats`
3. Review this guide's troubleshooting section
4. Check Ollama docs: https://ollama.ai/library
