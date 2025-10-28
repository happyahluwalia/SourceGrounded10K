# Features & Implementation Details

## Real-Time Log Streaming

### Overview

Finance Agent includes **real-time log streaming** from backend to frontend using Server-Sent Events (SSE). The debug panel shows actual backend logs as queries are processed, providing full transparency into the RAG pipeline.

### How It Works

**Backend (FastAPI):**
- Custom logging handler captures all application logs
- Broadcasts logs to multiple subscribers via thread-safe queues
- SSE endpoint `/api/logs/stream` streams logs to connected clients
- Keepalive pings every 30 seconds prevent connection timeout
- Auto-cleanup removes disconnected clients

**Frontend (React):**
- EventSource connects to `/api/logs/stream` when debug panel opens
- Receives logs in real-time with auto-reconnect on errors
- Color-coded display by log level (INFO, ERROR, WARNING, DEBUG)
- Auto-scrolls to latest logs
- Disconnects when panel closes

### What You'll See

When processing a query, the debug panel shows:

```
14:18:57  [INFO]  app.api.main              Query request: AAPL - What were revenues?
14:18:57  [INFO]  filing_service            Filing not found locally, fetching...
14:18:58  [INFO]  filing_service            Fetching AAPL 10-K from SEC EDGAR...
14:19:00  [INFO]  filing_service            Parsing document...
14:19:00  [INFO]  filing_service            Chunking document...
14:19:00  [INFO]  vector_store              Checking 1180 chunks for duplicates...
14:19:00  [INFO]  vector_store              Adding 1180 new chunks to Qdrant...
14:19:00  [INFO]  vector_store              Embedding 1180 texts...
14:19:52  [INFO]  vector_store              Uploaded batch 1/12
14:19:52  [INFO]  vector_store              Uploaded batch 2/12
14:19:53  [INFO]  vector_store              ✓ Successfully added 1180 new chunks
14:19:53  [INFO]  rag_chain                 Processing query...
14:19:53  [INFO]  rag_chain                 Retrieving chunks for query...
14:19:53  [INFO]  rag_chain                 Retrieved 5 chunks, 5 above threshold 0.5
14:19:53  [INFO]  rag_chain                 Generating answer with phi3:mini-instruct...
14:20:13  [INFO]  rag_chain                 Generated answer (487 chars)
14:20:13  [INFO]  rag_chain                 Completed in 19.64s using 5 sources
```

### Log Format

Each log entry contains:
```json
{
  "timestamp": "2025-10-18T14:18:57.888000",
  "level": "INFO",
  "logger": "app.services.filing_service",
  "message": "Filing not found locally, fetching from SEC: AAPL 10-K"
}
```

### Benefits

1. **Transparency**: Users see exactly what's happening
2. **Debugging**: Easy to identify bottlenecks
3. **Learning**: Understand RAG pipeline step-by-step
4. **Trust**: See the data sources being used
5. **Performance**: Identify slow operations

### Technical Details

**Why SSE Instead of WebSocket?**
- Simpler: One-way communication (server → client)
- Auto-reconnect: Built into EventSource API
- HTTP/2 friendly: Works well with proxies
- Perfect for logs: We only need server → client streaming

**Performance:**
- Minimal overhead: Logs broadcast without blocking
- Memory efficient: Queue size limited to 100 entries per subscriber
- Auto-cleanup: Dead subscribers automatically removed
- Keepalive: Prevents connection timeout

### Implementation Files

- `app/services/log_streamer.py` - Log streaming service
- `app/api/main.py` - SSE endpoint `/api/logs/stream`
- `frontend/src/App.jsx` - EventSource connection
- `frontend/src/components/DebugPanel.jsx` - Log display

---

## Source Citations

### Overview

Every answer includes citations showing which document chunks were used, with relevance scores and metadata.

### Citation Format

```json
{
  "sources": [
    {
      "ticker": "AAPL",
      "filing_type": "10-K",
      "report_date": "2024-09-30",
      "section": "Item 7 - Management Discussion",
      "score": 0.87,
      "text": "Total net sales increased 6% or $19.0 billion..."
    }
  ]
}
```

### Display

- Expandable source cards in UI
- Relevance score (0-1) with color coding
- Document metadata (company, filing, date, section)
- Text preview (first 200 characters)
- Full text on expand

---

## Chat Interface

### Features

- **Message History**: Persistent conversation within session
- **Ticker Context**: Set ticker once, ask multiple questions
- **Markdown Support**: Formatted answers with lists, tables, bold
- **Copy to Clipboard**: One-click copy of answers
- **Loading States**: Animated loading indicators
- **Error Handling**: Clear error messages with retry options

### UI Components

- **Header**: Branding, debug toggle, settings
- **Sidebar**: Ticker selection, filing type filter
- **Chat Area**: Message bubbles (user/assistant)
- **Input Box**: Multi-line text input with submit button
- **Debug Panel**: Collapsible log viewer

---

## Filtering & Search

### Available Filters

**Company:**
- Ticker symbol (e.g., AAPL, MSFT, GOOG)
- Auto-complete from processed companies

**Filing Type:**
- 10-K (Annual Report)
- 10-Q (Quarterly Report)
- 8-K (Current Report)

**Section:**
- Item 1 - Business
- Item 7 - Management Discussion & Analysis
- Item 8 - Financial Statements
- Risk Factors
- Notes to Financial Statements

**Date Range:**
- Latest filing only
- Specific fiscal year
- Date range (from/to)

### Search Quality

**Semantic Search:**
- Cosine similarity on 768-dim embeddings
- Configurable score threshold (default: 0.3)
- Top-K retrieval (default: 5 chunks)

**Metadata Filtering:**
- Pre-filter before vector search
- Reduces search space
- Improves relevance

---

## Performance Monitoring

### Metrics Tracked

**Query Performance:**
- Total processing time
- Embedding generation time
- Vector search time
- LLM generation time
- Number of sources retrieved

**System Health:**
- Database connection status
- Qdrant availability
- Ollama model status
- Memory usage
- Disk space

### Health Endpoint

```bash
GET /api/health

Response:
{
  "status": "healthy",
  "database": "connected",
  "qdrant": "connected",
  "ollama": "ready",
  "models": {
    "embedding": "nomic-embed-text",
    "llm": "phi3:mini-instruct"
  }
}
```

---

## Rate Limiting

### Configuration

```python
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

### Implementation

- SlowAPI library for rate limiting
- Per-IP tracking
- Redis-backed counters
- Custom error messages

### Response Headers

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1634567890
```

---

## Caching Strategy

### What's Cached

**Redis Cache:**
- API responses (5 minute TTL)
- Company metadata (1 hour TTL)
- Filing lists (1 hour TTL)

**Database Cache:**
- Processed filings (permanent)
- Generated embeddings (permanent)
- Chunk metadata (permanent)

### Cache Invalidation

- Manual: DELETE endpoint to clear cache
- Automatic: TTL expiration
- Selective: Clear specific ticker/filing

---

## API Documentation

### Interactive Docs

**Swagger UI:**
- Available at `/docs`
- Try endpoints directly
- View request/response schemas
- Authentication testing

**ReDoc:**
- Available at `/redoc`
- Clean, readable documentation
- Code examples
- Schema browser

### Key Endpoints

**POST /api/query**
```json
{
  "query": "What were Apple's revenues?",
  "ticker": "AAPL",
  "filing_type": "10-K",
  "top_k": 5,
  "score_threshold": 0.3
}
```

**POST /api/companies/{ticker}/process**
```json
{
  "filing_type": "10-K",
  "force_refresh": false
}
```

**GET /api/companies**
```json
{
  "skip": 0,
  "limit": 20
}
```

---

## Error Handling

### Error Types

**User Errors (4xx):**
- 400: Invalid request (missing ticker, bad parameters)
- 404: Company/filing not found
- 429: Rate limit exceeded

**Server Errors (5xx):**
- 500: Internal server error
- 502: Ollama/Qdrant unavailable
- 503: Service temporarily unavailable

### Error Response Format

```json
{
  "error": "Company not found",
  "detail": "No filings found for ticker: INVALID",
  "timestamp": "2025-10-27T19:00:00",
  "request_id": "abc123"
}
```

### User-Friendly Messages

- Clear error descriptions
- Actionable suggestions
- Retry mechanisms
- Fallback options

---

## Future Enhancements

### Planned Features

- [ ] **Streaming responses**: Token-by-token LLM generation
- [ ] **Multi-company analysis**: Compare multiple companies
- [ ] **Time-series queries**: Track metrics over quarters
- [ ] **Advanced filters**: Industry, market cap, geography
- [ ] **Export functionality**: Download answers as PDF/CSV
- [ ] **User accounts**: Save chat history, preferences
- [ ] **Webhooks**: Notify on new filings
- [ ] **Analytics dashboard**: Usage statistics, popular queries

### Under Consideration

- WebSocket support for bidirectional communication
- Voice input/output
- Mobile app
- Browser extension
- Slack/Teams integration
- API key management
- Team collaboration features

---

**Built with ❤️ for transparency and user experience**
