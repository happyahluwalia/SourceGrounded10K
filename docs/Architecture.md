## Storage Architecture

**Postgres (Primary metadata + text storage):**
- Companies, filings metadata
- Chunks table with FULL TEXT
- Use for: Analytics, SQL queries, display

**Qdrant (Vector search):**
- Embeddings (vectors)
- Payload includes: text, metadata
- Use for: Semantic search, retrieval

**Why both have text:**
- Resilience (either DB can fail)
- Performance (no cross-DB lookups)
- Flexibility (SQL text search possible)

**Sync strategy:**
- Insert to both in same transaction flow
- UUID links records across systems