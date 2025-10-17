## Day 1

- [x] Initialize project with core config, database models and Docker services
- [x] Test connections to all services
- [x] Initialize project with core config, database models and Docker services

# 🎯 Day 2 Complete Plan

Great! Let's map out today's full journey so you know where we're headed.

---

## 📋 **Day 2 Overview: SEC Data Pipeline**

**Goal:** Fetch, parse, chunk, and store SEC filings in our database

**Total estimated time:** 6-8 hours

---

## 🗺️ **Complete Roadmap for Today**

```
┌─────────────────────────────────────────────────┐
│  Today's Pipeline (What We're Building)         │
├─────────────────────────────────────────────────┤
│                                                 │
│  Input: Ticker (e.g., "AAPL")                   │
│     ↓                                           │
│  [1] SECClient.ticker_to_cik()         ✅ DONE  │
│     ↓                                           │
│  [2] SECClient.get_company_filings()            │
│     ↓ (returns list of 10-K, 10-Q, etc.)        │
│  [3] SECClient.download_filing()                │
│     ↓ (downloads HTML to disk)                  │
│  [4] SECParser.parse_filing()                   │
│     ↓ (extracts sections, tables)               │
│  [5] DocumentChunker.chunk_sections()           │
│     ↓ (creates RAG-ready chunks)                │
│  [6] Store in Postgres                          │
│     ↓                                           │
│  Output: Structured data ready for RAG          │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## ⏱️ **Detailed Schedule**

### **Block 3: Fetch Company Filings List (45 min)** ← WE ARE HERE

**What we'll build:**
- Method to get all filings for a company
- Filter by filing type (10-K, 10-Q)
- Return metadata (date, accession number, document name)

**What you'll learn:**
- Working with SEC's submissions API
- Filtering and sorting financial data
- Handling API response structures

**Deliverable:** Function that returns: "Here are Apple's last 5 10-K filings"

---

### **Block 4: Download Filing Documents (45 min)**

**What we'll build:**
- Method to download HTML filing to disk
- Proper file organization (by ticker/year)
- Error handling for failed downloads

**What you'll learn:**
- File system organization
- Download strategies (stream vs load all)
- Path management

**Deliverable:** Downloaded HTML files organized in `data/filings/AAPL/2024-10K.html`

---

### **BREAK (15 min)** ☕

---

### **Block 5: Parse Filing Structure (1.5 hours)**

**What we'll build:**
- Extract sections (Item 1, Item 1A, Item 7, etc.)
- Extract tables separately
- Clean up HTML artifacts

**What you'll learn:**
- BeautifulSoup navigation
- Pattern matching for financial documents
- Handling messy real-world HTML

**Deliverable:** Structured dict: `{"Item 1": "text...", "Item 1A": "text...", tables: [...]}`

---

### **Block 6: Chunking Strategy (1 hour)**

**What we'll build:**
- Section-aware chunker
- Metadata preservation (which section, which filing)
- Table handling (keep whole vs split)

**What you'll learn:**
- Why naive chunking fails for financial docs
- Overlap strategies
- Metadata importance for RAG

**Deliverable:** List of chunks with metadata ready for embedding

---

### **BREAK (15 min)** ☕

---

### **Block 7: Database Storage (1 hour)**

**What we'll build:**
- Save filing metadata to Postgres
- Store chunks (we'll add vectors tomorrow)
- Query functions to retrieve

**What you'll learn:**
- SQLAlchemy relationships
- Bulk insert strategies
- Database design for RAG

**Deliverable:** Filings and chunks in database, queryable

---

### **Block 8: End-to-End Pipeline Test (45 min)**

**What we'll build:**
- Single command: "Process AAPL's latest 10-K"
- Runs entire pipeline
- Verification queries

**What you'll learn:**
- Orchestrating multiple steps
- Error handling at pipeline level
- Data validation

**Deliverable:** `python scripts/process_company.py AAPL` works end-to-end

---

### **Block 9: Documentation & Learnings (30 min)**

**What we'll do:**
- Review what we built
- Document key decisions
- Extract tweet-worthy insights
- Commit to git

**Deliverable:** 
- Clean git history
- Learning log
- 1-2 tweet drafts

---

## 📊 **Success Criteria for Today**

By end of day, you should be able to:

```bash
# Run this command:
python scripts/process_company.py AAPL --filing-type 10-K --limit 1

# And see:
✅ Fetched AAPL company info (CIK: 320193)
✅ Found 1 10-K filing
✅ Downloaded: aapl-20240928.htm
✅ Parsed 15 sections
✅ Extracted 42 tables
✅ Created 234 chunks
✅ Stored in database

# Then query it:
python -c "
from app.models.database import SessionLocal, SECFiling
db = SessionLocal()
filing = db.query(SECFiling).filter_by(ticker='AAPL').first()
print(f'Filing: {filing.filing_type} from {filing.filing_date}')
print(f'Processed: {filing.processed}')
"

# Output:
Filing: 10-K from 2024-09-28
Processed: True
```

---

## 🎓 **What You'll Learn Today (Big Picture)**

### **Technical Skills:**
1. HTTP API integration (rate limiting, sessions, headers)
2. HTML parsing with BeautifulSoup
3. File system management
4. Database operations (inserts, relationships)
5. Error handling strategies
6. Pipeline orchestration

### **Domain Knowledge:**
1. SEC filing structure (Items, sections)
2. Financial document characteristics
3. Why chunking strategies matter for finance

### **Engineering Practices:**
1. Incremental development (test each piece)
2. Separation of concerns (client, parser, chunker)
3. Documentation as you go
4. Making measurable tradeoff decisions

---

## 📝 **Learnings We'll Track for Tweets**

As we build, I'll note these decision points:

1. **Why sec-edgar-downloader over custom downloader?**
2. **Section-aware chunking vs naive splitting** (we'll measure quality)
3. **How to preserve tables in RAG** (practical example)
4. **Rate limiting implementation** (why it matters)
5. **Metadata design for citations** (show the importance)

---

## 🎯 **Next Steps (Right Now)**

Let's continue with **Block 3: Fetch Company Filings List**

We'll add this method to `SECClient`:
- `get_company_filings(ticker, filing_type, limit)`

This will return a list like:
```python
[
  {
    "accessionNumber": "0000320193-24-000123",
    "filingDate": "2024-11-01",
    "reportDate": "2024-09-28",
    "form": "10-K",
    "primaryDocument": "aapl-20240928.htm",
    "documentUrl": "https://www.sec.gov/Archives/edgar/..."
  },
  ...
]
```

---
## 📝 **Day 2 Summary for Documentation**

### **What We Built:**
Completed Features:
- SEC EDGAR API client with rate limiting
- Document downloading with caching
- HTML parsing (18 sections, proper normalization)
- Structure-aware chunking (540 chunks per 10-K)
- Database storage with UUID primary keys
- End-to-end pipeline script
- Query utility for database inspection

Pipeline Performance:
- Process 10-K: ~30 seconds
- Chunk generation: 540 chunks @ 500 chars avg
- Database insert: 540 chunks in <1 second (bulk)

Command Usage:
  python scripts/process_company.py AAPL --filing-type 10-K --limit 1
  python scripts/query_filings.py --ticker AAPL

Ready for Day 3: Embeddings + Vector Search

## Day 3 Store in Qdrant Vector DB
### Storage Design Clarification
**Text storage:** Chunk text is stored in BOTH Postgres and Qdrant
- **Postgres:** Full text in `chunks.text` column (for SQL queries, display, backup)
- **Qdrant:** Full text in payload (for immediate access after vector search)
- **Rationale:** Resilience, no cross-DB lookups, flexibility for SQL search later
- **Cost:** ~2MB duplication per filing (acceptable)



## Summary Note for Future
```
TODO: Filing-Level Smart Caching
Location: scripts/process_company.py

Current: Always fetch from SEC, deduplicate at chunk level
Desired: Check Postgres+Qdrant first, skip if exists

Implementation:
1. Add embeddings_generated flag to SECFiling model
2. Create FilingChecker service (check_filing_exists)
3. Update process_company.py to check before fetching
4. Mark filings as embedded after Qdrant upload

Benefits:
- No duplicate SEC API calls
- No duplicate embedding generation
- Instant responses for cached filings
- 66%+ cost savings for repeated queries

Priority: Medium (Week 2-3)
Blockers: None (can implement anytime)