# Configuration Guide

## Overview

All configuration is centralized in `app/core/config.py` and can be overridden via environment variables in `.env`.

---

## Configuration Parameters

### LLM Settings

```python
# Model selection
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini-instruct

# Context window: 4K tokens
# Memory: ~3GB
```

**Options:**
- `phi3:mini-instruct` - **Recommended** (3.8B params, stable)
- `llama3.1:8b-instruct` - Higher quality, risky on 8GB RAM
- `gemma:1b` - Development only

---

### Embedding Settings

```python
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768
```

**Why nomic-embed-text-v1.5?**
- 768 dimensions (25% less memory than BGE)
- 8K context window (handles long financial docs)
- Native Ollama support

---

### Chunking Strategy

```python
CHUNK_SIZE=1024
CHUNK_OVERLAP=150
```

**Context Window Math (Phi-3 4K tokens):**
```
5 chunks × 1024 chars = 5,120 chars ≈ 1,280 tokens
Prompt overhead: ~200 tokens
Answer: 500 tokens
─────────────────────────────────────────
Total: ~1,980 tokens (leaves 2K buffer)
```

**Why 1024?**
- Balances context vs. LLM capacity
- Financial sections stay coherent
- Leaves room for prompt + answer

**Alternatives:**
- `512` - Development/testing (faster)
- `768` - Conservative production
- `1536` - If using Llama 3.1 8B (8K context)

---

### RAG Settings

```python
TOP_K=5                    # Number of chunks to retrieve
SCORE_THRESHOLD=0.5        # Minimum similarity (0-1)
MAX_TOKENS=500             # Maximum answer length
```

**Tuning Guide:**

| Parameter | Lower | Higher | Effect |
|-----------|-------|--------|--------|
| `TOP_K` | 3 | 7 | More context, slower |
| `SCORE_THRESHOLD` | 0.3 | 0.7 | Stricter relevance |
| `MAX_TOKENS` | 300 | 800 | Longer answers |

---

### Batch Processing

```python
EMBEDDING_BATCH_SIZE=32           # Embedding generation
QDRANT_UPLOAD_BATCH_SIZE=100      # Vector uploads
```

**Performance Impact:**
- Higher = faster but more memory
- Lower = slower but safer

---

## Environment Variables

### Required

```bash
# SEC API (REQUIRED - SEC will block without this)
SEC_USER_AGENT=FirstName LastName your.email@example.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Optional (with defaults)

```bash
# Application
APP_NAME=FinanceAgent
DEBUG=false
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=*
API_KEY=

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=financial_documents

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## Configuration Profiles

### Development

```bash
# .env.development
OLLAMA_MODEL=gemma:1b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=75
TOP_K=5
SCORE_THRESHOLD=0.5
DEBUG=true
LOG_LEVEL=DEBUG
```

**Characteristics:**
- Fast iteration
- Lower memory
- Good enough quality

---

### Production (8GB Droplet)

```bash
# .env.production
OLLAMA_MODEL=phi3:mini-instruct
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768
CHUNK_SIZE=1024
CHUNK_OVERLAP=150
TOP_K=5
SCORE_THRESHOLD=0.5
MAX_TOKENS=500
DEBUG=false
LOG_LEVEL=INFO
```

**Characteristics:**
- Stable on 8GB RAM
- High quality
- Production-ready

---

### Production (16GB Droplet)

```bash
# .env.production-16gb
OLLAMA_MODEL=llama3.1:8b-instruct
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768
CHUNK_SIZE=1536
CHUNK_OVERLAP=230
TOP_K=5
SCORE_THRESHOLD=0.5
MAX_TOKENS=800
DEBUG=false
LOG_LEVEL=INFO
```

**Characteristics:**
- Maximum quality
- More context
- Requires monitoring

---

## Hardcoded Values Removed

All previously hardcoded values are now configurable:

### Before (Hardcoded)
```python
# vector_store.py
def embed_texts(self, texts, batch_size=32):  # ❌ Hardcoded
def add_chunks(self, chunks, batch_size=100):  # ❌ Hardcoded
def search(self, query, limit=5):  # ❌ Hardcoded

# rag_chain.py
def __init__(self, model_name="gemma3:1b"):  # ❌ Hardcoded
def retrieve(self, top_k=5, score_threshold=0.7):  # ❌ Hardcoded
def generate(self, max_tokens=500):  # ❌ Hardcoded
```

### After (Configurable)
```python
# All values now use settings with optional overrides
def embed_texts(self, texts, batch_size=None):
    batch_size = batch_size or settings.embedding_batch_size

def search(self, query, limit=None):
    limit = limit or settings.top_k

def retrieve(self, top_k=None, score_threshold=None):
    top_k = top_k or settings.top_k
    score_threshold = score_threshold or settings.score_threshold
```

---

## Verification

After changing configuration:

```bash
# 1. Restart services
docker-compose restart

# 2. Run verification
docker exec -it financeagent_app python scripts/verify_production_models.py

# 3. Check logs
docker-compose logs -f app | grep -E "(config|settings|model)"
```

---

## Troubleshooting

### Out of Memory

**Symptoms:**
- Ollama container crashes
- `docker stats` shows >7GB usage

**Solutions:**
1. Reduce `CHUNK_SIZE` to 768
2. Reduce `TOP_K` to 3
3. Switch to smaller model (`phi3` instead of `llama3.1`)
4. Upgrade to 16GB droplet

---

### Poor Answer Quality

**Symptoms:**
- Answers are vague or incorrect
- Missing relevant information

**Solutions:**
1. Increase `TOP_K` to 7
2. Lower `SCORE_THRESHOLD` to 0.3
3. Increase `CHUNK_SIZE` to 1536
4. Upgrade to `llama3.1:8b-instruct`

---

### Slow Performance

**Symptoms:**
- Queries take >10 seconds
- Embedding generation is slow

**Solutions:**
1. Reduce `TOP_K` to 3
2. Reduce `CHUNK_SIZE` to 768
3. Increase `EMBEDDING_BATCH_SIZE` to 64
4. Use development model (`gemma:1b`)

---

### Dimension Mismatch

**Symptoms:**
```
Error: Vector dimension mismatch: expected 768, got 1024
```

**Solution:**
```bash
# Delete and recreate Qdrant collection
curl -X DELETE http://localhost:6333/collections/financial_documents
docker-compose restart app
```

---

## Best Practices

### 1. **Use Environment Variables**
Never hardcode in Python files:
```bash
# ✅ Good
OLLAMA_MODEL=phi3:mini-instruct

# ❌ Bad
model_name = "phi3:mini-instruct"  # in code
```

### 2. **Test Configuration Changes**
```bash
# Always verify after changes
python scripts/verify_production_models.py
```

### 3. **Monitor Memory**
```bash
# Keep an eye on usage
watch -n 5 docker stats
```

### 4. **Document Custom Settings**
```bash
# Add comments in .env
CHUNK_SIZE=1536  # Increased for better context
```

### 5. **Version Control**
```bash
# Track configuration changes
git add .env.production.example
git commit -m "Update production config for phi3"
```

---

## Configuration Checklist

Before deployment:

- [ ] All required env vars set (`SEC_USER_AGENT`, `DATABASE_URL`)
- [ ] Model names match pulled models
- [ ] Embedding dimension matches model
- [ ] Chunk size appropriate for LLM context
- [ ] `TOP_K × CHUNK_SIZE` fits in context window
- [ ] Qdrant collection recreated if dimension changed
- [ ] Verification script passes
- [ ] Test query works

---

## References

- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Model Selection Analysis](MODEL_SELECTION_ANALYSIS.md)
- [Quick Deploy Reference](QUICK_DEPLOY_REFERENCE.md)
