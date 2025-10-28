# Finance Agent Architecture

Comprehensive technical architecture and design decisions for the Finance Agent RAG system.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (React + Vite)                 │
│  • Chat UI with message history                          │
│  • Real-time log streaming panel                         │
│  • Source citations display                              │
│  • TailwindCSS + Lucide icons                            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Python 3.11+)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RAG Pipeline                                     │   │
│  │  1. Query → Embedding (nomic-embed-text)         │   │
│  │  2. Vector Search (Qdrant, cosine similarity)    │   │
│  │  3. Retrieve Top-K Chunks (default: 5)           │   │
│  │  4. Build Context Prompt                         │   │
│  │  5. LLM Generation (Ollama/Phi-3)                │   │
│  │  6. Return Answer + Citations                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  Services:                                                │
│  • SEC Filing Downloader (sec-edgar-downloader)          │
│  • Document Parser (BeautifulSoup4)                      │
│  • Text Chunker (LangChain RecursiveCharacterTextSplitter)│
│  • Vector Store Manager                                   │
│  • RAG Chain Orchestrator                                │
└─────────┬──────────────────┬──────────────────┬─────────┘
          │                  │                  │
    ┌─────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
    │ PostgreSQL│      │  Qdrant  │      │  Ollama  │
    │ (Metadata)│      │ (Vectors)│      │  (LLM)   │
    │  + Redis  │      │ 768-dim  │      │  Phi-3   │
    └───────────┘      └──────────┘      └──────────┘
```

## Storage Architecture

### Dual-Database Strategy

**PostgreSQL (Primary metadata + text storage):**
- Companies table (ticker, name, CIK)
- Filings table (filing_type, report_date, accession_number)
- Chunks table with FULL TEXT (for SQL-based search fallback)
- Use for: Analytics, SQL queries, display, reporting

**Qdrant (Vector search engine):**
- 768-dimensional embeddings (nomic-embed-text-v1.5)
- Payload includes: text, metadata (ticker, section, filing_type, date)
- Use for: Semantic search, similarity retrieval, RAG pipeline

**Why both have text:**
- **Resilience**: Either DB can fail independently
- **Performance**: No cross-DB lookups during queries
- **Flexibility**: SQL text search possible as fallback
- **Analytics**: PostgreSQL for business intelligence

**Sync strategy:**
- Insert to both in same transaction flow
- UUID links records across systems
- Atomic operations ensure consistency

**Redis (Caching layer):**
- API response caching
- Rate limiting counters
- Session management
- Reduces load on primary databases

## Model Selection & Configuration

### Embedding Model: nomic-embed-text-v1.5

**Specifications:**
- **Dimensions**: 768 (vs 1024 for BGE-large)
- **Context Window**: 8,192 tokens (vs 512 for BGE)
- **Integration**: Native Ollama API
- **Memory**: 25% less than BGE-large

**Why Nomic?**
- **Long document support**: Financial filings often exceed 512 tokens
- **Better accuracy**: 8K context captures full tables and sections
- **Simpler deployment**: No separate sentence-transformers dependency
- **Production-ready**: Optimized for retrieval tasks

**Performance:**
- 500 chunks: ~40-50 seconds
- Trade-off: 33% slower than batched BGE, but better quality

### LLM Model: phi3:mini-instruct

**Specifications:**
- **Parameters**: 3.8 billion
- **Memory**: ~3GB (model + inference)
- **Quality**: Significantly better than 1B models
- **Stability**: Microsoft production-grade

**Why Phi-3?**
- **Memory safety**: 3.5GB buffer on 8GB servers
- **Quality upgrade**: 3.8B >> 1B parameters
- **Fast inference**: 3-5 seconds per query
- **Proven stability**: No OOM issues in production

**Alternatives:**
- **Development**: gemma3:1b (faster, lower quality)
- **High-end**: llama3.1:8b (better quality, risky on 8GB RAM)

### Chunking Strategy

**Configuration:**
- **Chunk Size**: 2,048 characters (up from 512)
- **Overlap**: 300 characters (up from 150)
- **Splitter**: LangChain RecursiveCharacterTextSplitter

**Split Hierarchy:**
1. Paragraph breaks (`\n\n`)
2. Line breaks (`\n`)
3. Sentence ends (`. `)
4. Word boundaries (` `)
5. Characters (last resort)

**Why 2,048 characters?**
- Leverages 25% of Nomic's 8K context window
- Preserves financial tables and sections intact
- Reduces total chunks → better semantic coherence
- Memory safe: ~512 tokens per chunk

## RAG Pipeline Details

### Step 1: Query Processing
```python
# User query → embedding
query_vector = ollama.embeddings(
    model="nomic-embed-text",
    prompt=user_query
)
```

### Step 2: Vector Search
```python
# Cosine similarity search in Qdrant
results = qdrant.search(
    collection="financial_filings",
    query_vector=query_vector,
    limit=TOP_K,  # default: 5
    score_threshold=0.3,  # minimum similarity
    filter={"ticker": "AAPL"}  # optional filters
)
```

### Step 3: Context Building
```
[Document 1]
Company: AAPL
Filing: 10-K (2024-09-30)
Section: Item 7 - Management Discussion
Relevance Score: 0.87
<chunk_text>
----------
[Document 2]
...
```

### Step 4: LLM Prompting
```python
prompt = f"""
You are a financial analyst assistant.

{context}

Instructions:
1. Answer using ONLY the context above
2. Cite sources (e.g., "According to Document 1...")
3. Be specific with numbers and dates
4. Acknowledge if information is insufficient

Question: {user_query}

Answer:
"""
```

### Step 5: Generation
```python
response = ollama.generate(
    model="phi3:mini-instruct",
    prompt=prompt,
    options={
        "temperature": 0.1,  # Low for factual answers
        "num_predict": 500   # Max tokens
    }
)
```

## API Design

### Core Endpoints

**POST /api/query**
- Main RAG endpoint
- Accepts: query, ticker, filing_type, filters
- Returns: answer, sources, metadata, processing_time

**POST /api/companies/{ticker}/process**
- Download and process SEC filings
- Async job with progress tracking

**GET /api/companies**
- List all processed companies
- Pagination support

**GET /api/health**
- Service health check
- Verifies: DB connections, Ollama, Qdrant

### Real-Time Log Streaming

**Implementation:**
- Server-Sent Events (SSE) for log streaming
- Structured JSON logs with timestamps
- Log levels: INFO, WARNING, ERROR
- Client-side debug panel toggles visibility

**Log Flow:**
```
[INFO] Query request: AAPL - What were revenues?
[INFO] Embedding query...
[INFO] Searching Qdrant...
[INFO] Retrieved 5 chunks, 5 above threshold
[INFO] Building context...
[INFO] Generating answer with phi3:mini-instruct...
[INFO] Generated answer (245 chars)
[INFO] Completed in 4.2s using 5 sources
```

## Performance Characteristics

### Latency Breakdown

**First Query (new company):**
- SEC filing download: 10-15s
- Document parsing: 3-5s
- Chunking: 1-2s
- Embedding generation: 40-50s (500 chunks)
- Vector storage: 1-2s
- **Total**: 55-75 seconds

**Subsequent Queries:**
- Query embedding: 0.5s
- Vector search: 0.1s
- Context building: 0.1s
- LLM generation: 3-5s
- **Total**: 3.7-5.7 seconds

### Memory Budget (8GB Server)

```
Component               Memory    Notes
────────────────────────────────────────────────────────
System/OS               500 MB    Base Ubuntu overhead
PostgreSQL              300 MB    Small database
Qdrant (10K vectors)    500 MB    768-dim embeddings
Redis                   100 MB    Cache + sessions
Nginx                    50 MB    Reverse proxy
────────────────────────────────────────────────────────
Infrastructure Total   1.45 GB

Available for Ollama   6.55 GB
────────────────────────────────────────────────────────
Phi-3 Mini:            3.0 GB    ✅ Safe (3.5GB buffer)
```

## Deployment Architecture

### Docker Compose Services

1. **postgres**: PostgreSQL 16-alpine
2. **qdrant**: Qdrant latest
3. **ollama**: Ollama with GPU support (optional)
4. **redis**: Redis 7-alpine
5. **backend**: FastAPI application
6. **frontend**: React SPA (Nginx)

### Production Considerations

**Scaling:**
- Backend: Horizontal scaling (multiple uvicorn workers)
- Frontend: CDN distribution
- Ollama: Dedicated GPU server for high traffic
- Databases: Managed services (RDS, Qdrant Cloud)

**Monitoring:**
- Prometheus metrics
- Grafana dashboards
- Log aggregation (Loki)
- GPU utilization tracking

**Security:**
- API key authentication
- Rate limiting (10/min, 100/hr)
- CORS configuration
- Environment variable secrets
- SSL/TLS termination

## Technology Stack Summary

**Backend:**
- FastAPI 0.119+ (async Python web framework)
- SQLAlchemy 2.0+ (ORM)
- Alembic (database migrations)
- Pydantic (data validation)
- Ollama 0.6.0 (LLM client)

**Databases:**
- PostgreSQL 16 (metadata)
- Qdrant 1.7+ (vector search)
- Redis 7 (caching)

**AI/ML:**
- Ollama (LLM inference)
- nomic-embed-text-v1.5 (embeddings)
- phi3:mini-instruct (generation)
- LangChain text splitters

**Frontend:**
- React 18.3+
- Vite (build tool)
- TailwindCSS (styling)
- Lucide React (icons)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- GitHub Actions (CI/CD)

## Design Decisions

### Why RAG over Fine-Tuning?
- **Dynamic data**: SEC filings update quarterly
- **Transparency**: Source citations build trust
- **Cost**: No expensive training required
- **Flexibility**: Easy to update knowledge base

### Why Local LLM (Ollama) vs API?
- **Cost**: No per-token API fees
- **Privacy**: Financial data stays on-premise
- **Latency**: No external API calls
- **Control**: Full model customization

### Why Qdrant vs Alternatives?
- **Performance**: Optimized for similarity search
- **Filtering**: Rich metadata filtering
- **Scalability**: Handles millions of vectors
- **Docker-friendly**: Easy local development

### Why Dual Storage (Postgres + Qdrant)?
- **Separation of concerns**: Relational vs vector data
- **Resilience**: Independent failure modes
- **Optimization**: Each DB optimized for its use case
- **Analytics**: SQL for business intelligence

## Future Enhancements

- **Streaming responses**: Token-by-token generation
- **Multi-document analysis**: Compare multiple companies
- **Time-series queries**: Track metrics over quarters
- **Advanced filters**: Industry, market cap, geography
- **Hybrid search**: Combine semantic + keyword search
- **GPU optimization**: CUDA acceleration for embeddings
- **Distributed deployment**: Kubernetes orchestration