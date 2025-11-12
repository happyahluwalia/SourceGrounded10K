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

## Architectural Learnings

### Multi-Company Comparison: Data Structure > Complex Architecture

**Date**: November 4, 2025

#### The Initial Plan (Rejected)

When planning multi-company comparative analysis (e.g., "Compare Apple vs Microsoft revenue growth"), the initial design proposed:

```
Orchestrator Agent
  ├─ Parallel RAG Agent (AAPL)
  ├─ Parallel RAG Agent (MSFT)
  ├─ Parallel RAG Agent (GOOGL)
  └─ Synthesis Agent (aggregates results)
```

**Complexity**:
- New orchestrator agent for parallel execution
- Separate RAG agent instances per company
- Complex result aggregation layer
- State management across parallel agents
- **Estimated timeline**: 5-6 weeks

#### The Reality Check

Testing the existing system with "Compare Microsoft and Apple" produced "fairly decent" results, revealing:

1. ✅ **Existing planner already generates per-company tasks**:
   ```json
   {
     "intent": "compare_data",
     "tasks": [
       {"ticker": "AAPL", "search_query": "revenue growth"},
       {"ticker": "MSFT", "search_query": "revenue growth"}
     ]
   }
   ```

2. ✅ **Existing executor already fetches data per company**:
   ```python
   for task in tasks:
       chunks = vector_store.search(ticker=task['ticker'], ...)
   ```

3. ❌ **But the data structure was wrong**:
   ```python
   # Current (problematic)
   all_chunks = []  # Pools all companies together
   for task in tasks:
       chunks = search(...)
       all_chunks.extend(chunks)  # Loses company association
   
   unique = dedupe(all_chunks)[:5]  # Only 5 total chunks!
   # Result: 4 AAPL chunks, 1 MSFT chunk → unbalanced comparison
   ```

#### The Simple Fix

**Change one data structure**: Return `dict` instead of `list`

```python
# Improved (correct)
results_by_company = {}  # Maintain company separation
for task in tasks:
    ticker = task['ticker']
    chunks = search(ticker=ticker, ...)
    results_by_company[ticker] = chunks[:5]  # 5 per company

# Result: {"AAPL": [5 chunks], "MSFT": [5 chunks]}
# Total: 10 chunks (equal representation) ✅
```

**Impact**:
- ✅ Equal data retrieval for all companies (5 chunks each)
- ✅ No missing data ("Apple's MD&A not found" → fixed)
- ✅ Better comparison quality (balanced context)
- ✅ **Timeline**: 1-2 days (not 5-6 weeks)

#### Key Lessons

1. **Test before redesigning**: The existing architecture was 90% there. Testing revealed a simple data structure issue, not an architectural gap.

2. **Data structures matter more than agents**: Changing from `list` to `dict` solved the multi-company problem without adding complexity.

3. **Simplicity wins**: 
   - Complex solution: New orchestrator + parallel agents + aggregation layer
   - Simple solution: Change return type from `list` to `dict`
   - **Result**: Same functionality, 95% less code

4. **Incremental > Rebuild**: Improving existing code beats rebuilding from scratch:
   - Reuses tested components
   - Maintains backward compatibility  
   - Ships faster (days vs weeks)
   - Lower risk of regressions

5. **Deterministic > LLM where possible**:
   - Formatting comparison tables: Python function (0.1s) > LLM generation (2-3s)
   - Caching embeddings: Hash lookup (0.01s) > Re-embedding (0.5s)
   - Parsing structured output: JSON schema > Prompt engineering

#### Performance Improvements from This Learning

| Metric | Before | After | Method |
|--------|--------|-------|--------|
| **Data per company** | Unequal (4+1) | Equal (5+5) | Dict structure |
| **Missing data** | Common | Rare | Balanced retrieval |
| **Embedding calls** | 10+ per query | 1 per query | Caching |
| **Synthesis time** | 42.8s | ~15-20s | Smaller context |
| **Total time** | 58s | 20-25s | Combined fixes |
| **Code complexity** | +500 lines | +50 lines | Simple fix |

#### When to Use Complex Architecture

The parallel agent architecture **would** be justified if:
- ❌ Comparing 10+ companies simultaneously (not current requirement)
- ❌ Different data sources per company (all use same SEC EDGAR)
- ❌ Complex inter-company dependencies (not needed for comparison)
- ❌ Real-time streaming from multiple sources (not current requirement)

**Current requirement**: Compare 2-3 companies from same data source → Simple data structure suffices.

#### References

- Initial design: `docs/v2.1/COMPARATIVE_ANALYSIS_HIGH_LEVEL_DESIGN.md`
- Decision rationale: `docs/v2.1/COMPARATIVE_ANALYSIS_FEATURE_DECISION.md`
- Code changes: `app/tools/filing_qa_tool.py` (execute_plan function)

---

### Prompt Engineering: Natural Text In → Structured Data Out

**Date**: November 4, 2025

#### The Question

When building the RAG pipeline, we faced a design choice for how to format context sent to the LLM:

**Option A: Plain Text Context**
```
Context for AAPL:
================================================================================

[Document 1]
Company: AAPL
Filing: 10-K (2024-09-28)
Section: Item 7
Relevance Score: 0.95

Apple Inc. reported total net sales of $391.0 billion...
----------
```

**Option B: JSON Context**
```json
{
  "companies": {
    "AAPL": {
      "documents": [
        {
          "filing": "10-K",
          "date": "2024-09-28",
          "section": "Item 7",
          "score": 0.95,
          "text": "Apple Inc. reported..."
        }
      ]
    }
  }
}
```

#### The Analysis

**JSON Context Drawbacks**:
1. **Token overhead**: 20-30% more tokens for JSON syntax
   - Plain text: `"Company: AAPL"` = 3 tokens
   - JSON: `"company": "AAPL",` = 5 tokens
   - For 25 documents: ~2,000 wasted tokens on syntax!

2. **Less natural for LLMs**: Models are trained primarily on natural language, not JSON
   - LLMs excel at understanding narrative context
   - JSON parsing adds cognitive overhead for the model

3. **Context window pressure**: With limited context (4K-8K tokens), every token counts

**Plain Text Advantages**:
1. **Token efficiency**: 20-30% fewer tokens = more actual content
2. **Natural comprehension**: Closer to training data distribution
3. **Human readability**: Easier to debug prompts in logs

#### The Solution: Hybrid Approach

**Input (Context)**: Plain text ✅
- More token-efficient
- More natural for LLM comprehension
- Easier to read in logs

**Output (Answer)**: JSON ✅
- Structured for frontend parsing
- Enables programmatic formatting
- Better for UI rendering

```python
# Context sent to LLM (plain text)
context = """
Context for AAPL:
[Document 1]
Company: AAPL
Filing: 10-K (2024-09-28)
Section: Item 7
Apple Inc. reported...
"""

# Response from LLM (JSON)
response = {
  "answer": "According to Apple's 10-K Item 7...",
  "companies": {
    "AAPL": {
      "metrics": {"revenue": "$391.0B"},
      "key_findings": [...]
    }
  },
  "confidence": "high"
}
```

#### Key Lessons

**Rule of Thumb**: Natural text in → Structured data out (when needed). Don't over-structure your prompts.

1. **LLMs are trained on narrative text**: They comprehend natural language better than JSON
2. **Token efficiency matters**: 20-30% savings compounds across millions of queries
3. **Structure where it adds value**: Output needs structure for parsing, input doesn't
4. **Readability for debugging**: Plain text prompts are easier to inspect in logs

#### When JSON Context WOULD Make Sense

JSON context would be justified if:
- ❌ You need complex cross-referencing (not our use case)
- ❌ Documents are very short (token overhead negligible)
- ❌ Using function calling / tool use (requires structured input)
- ✅ **Using a model with native JSON mode** (some models optimize for this)

**Current requirement**: Comprehension of narrative financial documents → Plain text suffices.

#### Performance Impact

| Metric | Plain Text | JSON | Savings |
|--------|-----------|------|----------|
| **Tokens per query** | ~8,000 | ~10,000 | 2,000 (20%) |
| **Context window usage** | 50% | 62% | 12% more headroom |
| **LLM comprehension** | Native | Requires parsing | Better quality |
| **Debug readability** | High | Low | Easier troubleshooting |

#### Implementation

- **Context building**: `app/tools/rag_search_service.py` (build_context method)
- **Prompt template**: `app/prompts/synthesizer.txt` (requires JSON output)
- **Response parsing**: `app/tools/filing_qa_tool.py` (synthesize_answer function)

---

### UI Rendering: Structured Data → Deterministic Formatting

**Date**: November 4, 2025

#### The Problem

When building the UI for displaying LLM answers, we faced a choice:

**Option A: LLM Formats Output (Markdown/HTML)**
- Ask LLM to output formatted text with bold, tables, hyperlinks
- Example: `"**Apple**: Revenue was **$391.0B** ([source](#1))"`

**Option B: LLM Outputs Structured Data, Code Formats**
- LLM outputs semantic sections (paragraph, table, comparison)
- Backend functions convert to UI components
- Frontend renders components

#### Why Option A Fails

**LLMs are unreliable at formatting**:
1. **Inconsistency**: Sometimes bold works (`**text**`), sometimes it doesn't
2. **Token waste**: Formatting syntax adds 10-15% overhead
3. **Hard to maintain**: Changing UI requires re-prompting LLM
4. **Limited control**: Can't A/B test layouts or add interactivity
5. **Debugging nightmare**: Malformed markdown/HTML breaks UI

**Example of LLM formatting failures**:
```markdown
# Sometimes LLM does this:
**Apple** revenue: $391.0B

# Other times:
Apple revenue: **$391.0B

# Or even:
Apple revenue: $391.0B (bold)
```

#### The Solution: Separation of Concerns

**Architecture**:
```
LLM (Synthesizer)
    ↓
  Structured JSON (semantic intent)
    ↓
Backend Formatter (deterministic)
    ↓
  UI Components (React)
    ↓
  Rich UI (tables, charts, hyperlinks)
```

**LLM Output (Structured)**:
```json
{
  "answer": {
    "sections": [
      {
        "type": "paragraph",
        "content": "Apple's revenue was $391.0B in 2024.",
        "citations": [0, 1]
      },
      {
        "type": "table",
        "content": "Revenue comparison",
        "data": {
          "headers": ["Company", "Revenue", "Growth"],
          "rows": [
            ["AAPL", "$391.0B", "2%"],
            ["MSFT", "$245.1B", "16%"]
          ]
        },
        "citations": [0, 2]
      }
    ]
  }
}
```

**Backend Formatter** (`app/tools/filing_qa_tool.py`):
```python
def format_answer_for_ui(synthesis_result: dict, sources: list) -> dict:
    """
    Convert structured LLM output to UI-ready format.
    LLM provides semantic data, code handles presentation.
    """
    formatted_sections = []
    for section in synthesis_result["answer"]["sections"]:
        if section["type"] == "table":
            formatted_sections.append({
                "component": "Table",
                "props": {
                    "headers": section["data"]["headers"],
                    "rows": section["data"]["rows"],
                    "citations": build_citations(section["citations"], sources)
                }
            })
        elif section["type"] == "paragraph":
            formatted_sections.append({
                "component": "Paragraph",
                "props": {
                    "text": section["content"],
                    "citations": build_citations(section["citations"], sources)
                }
            })
    return {"sections": formatted_sections}
```

**Frontend Renderer** (React):
```tsx
function AnswerRenderer({ sections }) {
  return (
    <div className="answer">
      {sections.map((section, idx) => {
        switch (section.component) {
          case 'Table':
            return <ComparisonTable key={idx} {...section.props} />;
          case 'Paragraph':
            return <AnswerParagraph key={idx} {...section.props} />;
        }
      })}
    </div>
  );
}
```

#### Key Benefits

| Aspect | LLM Formatting | Structured Data + Code |
|--------|----------------|------------------------|
| **Consistency** | Unreliable | 100% consistent |
| **Token efficiency** | -10-15% overhead | No formatting tokens |
| **Maintainability** | Change prompts | Change code |
| **Flexibility** | Limited | Easy A/B testing |
| **Interactivity** | Static text | Charts, tooltips, etc. |
| **Debugging** | Hard (malformed markup) | Easy (structured data) |

#### Implementation Details

**Section Types Supported**:
- `paragraph`: Standard text with inline citations
- `table`: Comparison tables with headers and rows
- `key_findings`: Bullet-point style findings
- `comparison_summary`: Summary of differences

**Citation System**:
- LLM uses 0-based indices: `"citations": [0, 1, 2]`
- Backend converts to hyperlinks: `{"id": 0, "text": "10-K Item 7", "url": "#source-0"}`
- Frontend renders as clickable links with hover previews

**Metrics Format**:
```json
{
  "metrics": {
    "revenue": {
      "value": 391.0,  // Number for calculations
      "unit": "billion",
      "formatted": "$391.0B"  // String for display
    }
  }
}
```

#### Future Enhancements

With this architecture, we can easily add:
1. **Charts**: Bar charts, line graphs from structured metrics
2. **Interactive tables**: Sorting, filtering, highlighting
3. **Tooltips**: Hover over citations for preview
4. **Animations**: Smooth transitions between sections
5. **Export**: PDF, CSV from structured data

All without changing the LLM or prompts!

#### Key Lessons

**Rule of Thumb**: LLMs should focus on semantic data extraction, not presentation.

1. **Separation of concerns**: LLM = analysis, Code = formatting
2. **Deterministic > LLM**: Use code for anything that needs consistency
3. **Future-proof**: Easy to add new UI features without re-prompting
4. **Token efficiency**: No formatting syntax in LLM output
5. **Testability**: Can unit test formatters independently

#### References

- **Synthesizer prompt**: `app/prompts/synthesizer.txt` (defines JSON schema)
- **Formatter functions**: `app/tools/filing_qa_tool.py` (format_answer_for_ui)
- **LLM output examples**: See prompt file for single/comparison query examples

---

### Infrastructure Optimization: Docker vs Native Ollama

**Date**: November 10, 2024

#### The Problem: "Slow" Inference

During local development on Mac, LLM inference was extremely slow:
- **Total query time**: 90+ seconds
- **3 LLM calls**: Supervisor (32.79s) + Planner (57.66s) + Synthesizer (unknown)
- **Symptom**: `ollama ps` showed `PROCESSOR: 100% CPU` instead of GPU

**Initial assumption**: Model was too large or prompts were inefficient.

#### The Root Cause: Infrastructure Bottleneck

**Docker on macOS doesn't support GPU passthrough**:
- Docker containers on Mac run in a Linux VM
- Apple's Metal GPU framework is not accessible to Docker
- Ollama falls back to CPU-only inference
- Result: 5-10x slower than GPU-accelerated inference

#### The Solution: Platform-Specific Deployment

**Local Development (Mac)**:
```bash
# Run Ollama natively (not in Docker)
brew install ollama
ollama serve

# Ollama automatically uses Metal for GPU acceleration
# Update app to use localhost:11434
```

**Production (Linux Server)**:
```yaml
# docker-compose.prod.yml already configured correctly
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

#### Performance Impact

| Environment | GPU Access | Inference Speed | Notes |
|-------------|-----------|-----------------|-------|
| **Docker on Mac** | ❌ CPU-only | 90+ seconds | Docker VM blocks Metal |
| **Native Mac** | ✅ Metal GPU | 10-15 seconds | 5-10x faster |
| **Docker on Linux** | ✅ NVIDIA GPU | 8-12 seconds | With NVIDIA Container Toolkit |

**Verification Commands**:
```bash
# Check if GPU is being used
ollama ps
# Look for "PROCESSOR: 100% GPU" (good) vs "100% CPU" (bad)

# On Linux servers
nvidia-smi  # Check GPU utilization
```

#### Key Lessons

1. **Infrastructure bottlenecks masquerade as algorithm problems**: What seemed like a model performance issue was actually a deployment configuration problem.

2. **Platform-specific optimizations matter**: 
   - Mac: Native Ollama with Metal
   - Linux: Docker with NVIDIA Container Toolkit
   - Windows: Native Ollama or WSL2 with GPU passthrough

3. **Test infrastructure assumptions early**: Don't optimize prompts or models before verifying GPU acceleration is working.

4. **Production vs Development**: Production Linux servers with NVIDIA GPUs work correctly in Docker. Mac development requires native Ollama.

5. **Monitoring is critical**: `ollama ps` immediately reveals CPU vs GPU usage. Check this first when debugging performance.

#### References

- Ollama documentation: https://ollama.ai/
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
- Apple Metal: https://developer.apple.com/metal/

---

### Multi-Agent Token Economics

**Date**: November 10, 2024

#### The Research: Multi-Agent Systems Use 15x More Tokens

According to [Anthropic's multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system):
- **Simple chat**: ~100 tokens per interaction
- **Single agent**: ~400 tokens (4x chat)
- **Multi-agent system**: ~1,500 tokens (15x chat)

**Why?** Each agent processes full context, multiplying token usage.

#### Our System: 3-Agent Pipeline

**Architecture**:
```
User Query (21 tokens)
    ↓
Supervisor Agent (decides which tool to use)
    ↓ System prompt: 208 tokens, Output: 0 tokens
Planner Agent (creates structured retrieval plan)
    ↓ System prompt: 1,284 tokens, Output: 62 tokens
Deterministic Execution (vector search, no LLM)
    ↓
Synthesizer Agent (generates final answer)
    ↓ System prompt: ~500 tokens, Output: ~600 tokens
Final Answer
```

#### Measured Token Usage

**Example Query**: "What is Apple's revenue?"

| Stage | System Tokens | Human Tokens | Output Tokens | Total | Latency |
|-------|--------------|--------------|---------------|-------|----------|
| **Supervisor** | 208 | 6 | 0 | 214 | 32.79s |
| **Planner** | 1,284 | 15 | 62 | 1,361 | 57.66s |
| **Synthesizer** | ~500 | ~50 | ~600 | ~1,150 | ~15s |
| **TOTAL** | 1,992 | 71 | 662 | **2,725** | **~105s** |

**Key Insights**:
1. **System prompts dominate**: 1,992 tokens (73%) vs user queries 71 tokens (3%)
2. **Planner is heaviest**: 1,284 system tokens (47% of all input)
3. **15x multiplier confirmed**: 2,725 total vs ~180 for simple chat
4. **System prompts are 28x larger than user queries**

#### Design Trade-offs

**Why 3 Agents?**

1. **Supervisor**: Tool delegation and routing
   - Could be deterministic (pattern matching)
   - LLM provides flexibility for future tools
   - **Cost**: 214 tokens

2. **Planner**: Structured retrieval plan
   - Converts natural language → search queries
   - Handles multi-company comparisons
   - **Cost**: 1,361 tokens (heaviest)

3. **Synthesizer**: Answer generation
   - Reads 10+ document chunks (~10,000 words)
   - Generates grounded, cited answers
   - **Cost**: ~1,150 tokens

**Alternative: Single LLM Call**
- Pros: ~180 tokens (15x less)
- Cons: No structured planning, worse accuracy, no tool delegation

**Our Choice**: Trade tokens for reasoning quality and accuracy.

#### Optimization Opportunities

**High Impact**:
1. **Reduce Planner system prompt** (1,284 → 800 tokens)
   - Remove redundant examples
   - Simplify instructions
   - **Savings**: 484 tokens (18%)

2. **Cache system prompts** (already implemented)
   - System prompts don't change per query
   - Only user query changes
   - **Savings**: Reduced compute, not tokens

3. **Deterministic Supervisor** (future)
   - Replace LLM with pattern matching
   - Only one tool currently exists
   - **Savings**: 214 tokens (8%)

**Low Impact**:
1. Compress user queries (21 tokens is already minimal)
2. Reduce Synthesizer output (quality trade-off)

#### Token Cost Analysis

**Local Ollama**: $0 (free)

**If using OpenAI GPT-4**:
- Input: 2,063 tokens × $0.03/1K = $0.062
- Output: 662 tokens × $0.06/1K = $0.040
- **Total per query**: $0.102
- **1,000 queries/day**: $102/day = $3,060/month

**Why local LLMs matter**: Zero marginal cost for unlimited queries.

#### Key Lessons

1. **Multi-agent systems are token-expensive**: 15x multiplier is real. Budget accordingly.

2. **System prompts are the optimization target**: 73% of tokens. User queries are already minimal.

3. **Measure before optimizing**: Token profiling revealed Planner as the bottleneck (47% of input tokens).

4. **Trade-offs are intentional**: We chose accuracy over token efficiency. Single LLM would be 15x cheaper but less accurate.

5. **Local LLMs enable experimentation**: Zero cost means we can afford multi-agent architectures.

#### Implementation

**Token Profiling System**:
- `app/utils/token_metrics.py`: Token counting with tiktoken
- Tracks system vs human tokens separately
- Logs per-stage breakdown and optimization insights
- Real-time logging + end-of-query summary

**Example Output**:
```
📊 TOKEN USAGE & PERFORMANCE ANALYSIS
📈 OVERALL TOTALS:
  Total Input Tokens:
    - System: 1,492
    - Human: 21
    - Total: 1,513
  Total Output Tokens: 62
  Grand Total Tokens: 1,575
  Total Latency: 90.45s

🔍 PER-STAGE BREAKDOWN:
  1. SUPERVISOR (llama3.2:3b)
     Input:  System=208, Human=6, Total=214
     Output: 0
     Time:   32.79s
  
  2. PLANNER (llama3.2:3b)
     Input:  System=1,284, Human=15, Total=1,299
     Output: 62
     Time:   57.66s

💡 OPTIMIZATION INSIGHTS:
  ⚠️  Slowest stage: planner (57.66s)
  📊 Most token-heavy: planner (1,361 tokens)
  ⚙️  System prompts are larger than user queries - consider optimization
```

#### References

- Anthropic Multi-Agent Research: https://www.anthropic.com/engineering/multi-agent-research-system
- Token profiling implementation: `app/utils/token_metrics.py`
- Prompt files: `app/prompts/supervisor.txt`, `planner.txt`, `synthesizer.txt`

---

## Future Enhancements

- **Streaming responses**: Token-by-token generation ✅ *Implemented*
- **Multi-document analysis**: Compare multiple companies ✅ *Implemented via data structure fix*
- **Token optimization**: Reduce Planner system prompt by 40%
- **Time-series queries**: Track metrics over quarters
- **Advanced filters**: Industry, market cap, geography
- **Hybrid search**: Combine semantic + keyword search
- **Distributed deployment**: Kubernetes orchestration