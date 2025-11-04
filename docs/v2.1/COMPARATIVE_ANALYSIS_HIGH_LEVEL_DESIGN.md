# High-Level Design: Multi-Company Comparative Analysis

**Version**: 1.0  
**Date**: November 4, 2025  
**Status**: Design Phase  
**Implementation Timeline**: 5-6 weeks

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [API Design](#api-design)
6. [State Management](#state-management)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Open Questions](#open-questions)

---

## System Overview

### Goal
Enable users to compare 2-3 companies simultaneously using natural language queries, with AI-synthesized insights backed by SEC filing citations.

### Example Queries
```
1. "Compare AAPL vs MSFT revenue growth over the last 3 years"
2. "Which company has better operating margins: GOOGL or META?"
3. "Compare Tesla, Ford, and GM's R&D spending and explain differences"
4. "How do Apple and Microsoft's risk factors differ?"
```

### Expected Output
```markdown
## Revenue Growth Comparison: AAPL vs MSFT

### Summary
Apple's revenue grew 12% YoY while Microsoft grew 18% YoY in Q4 2024.

### Key Findings

**Apple (AAPL)**
- Total Revenue: $119.6B (Q4 2024)
- Growth Rate: +12% YoY
- Primary Driver: iPhone sales increased 15% [1]
- Headwind: Mac sales declined 8% [1]

**Microsoft (MSFT)**
- Total Revenue: $62.0B (Q4 2024)
- Growth Rate: +18% YoY
- Primary Driver: Azure cloud revenue up 30% [2]
- Strength: Commercial cloud margins improved to 71% [2]

### Why the Difference?
Microsoft's higher growth is driven by enterprise cloud adoption, 
while Apple faces market saturation in consumer hardware. Microsoft's 
MD&A highlights strategic shift to AI-powered cloud services [2], 
whereas Apple's 10-K notes increasing competition in smartphone 
market [1].

### Sources
[1] Apple Inc. 10-K (2024-09-30), Item 7 - MD&A, p.23
[2] Microsoft Corp. 10-K (2024-06-30), Item 7 - MD&A, p.31
```

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
│  "Compare AAPL vs MSFT revenue growth"                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Parser Agent                              │
│  • Extract company tickers: [AAPL, MSFT]                    │
│  • Identify comparison type: revenue_growth                  │
│  • Determine time period: recent quarters                    │
│  • Generate sub-queries for each company                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator Agent                              │
│  • Spawns parallel RAG agents (one per company)             │
│  • Manages execution flow                                    │
│  • Aggregates results                                        │
│  • Handles errors and retries                                │
└─────┬───────────────────────────┬───────────────────────────┘
      │                           │
      ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│  RAG Agent       │      │  RAG Agent       │
│  (AAPL)          │      │  (MSFT)          │
│                  │      │                  │
│ 1. Query Qdrant  │      │ 1. Query Qdrant  │
│ 2. Get top-5     │      │ 2. Get top-5     │
│ 3. Extract data  │      │ 3. Extract data  │
│ 4. Return result │      │ 4. Return result │
└────────┬─────────┘      └─────────┬────────┘
         │                          │
         └──────────┬───────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Aggregation Layer                          │
│  • Combines results from all RAG agents                      │
│  • Normalizes data formats                                   │
│  • Identifies missing data                                   │
│  • Creates structured comparison object                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Synthesis Agent                                 │
│  • Analyzes aggregated data                                  │
│  • Identifies key differences                                │
│  • Explains WHY differences exist                            │
│  • Generates narrative with citations                        │
│  • Formats output (markdown + tables)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Response Formatter                              │
│  • Adds comparison tables                                    │
│  • Formats citations                                         │
│  • Generates summary section                                 │
│  • Returns to user                                           │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Agent Pattern: Orchestrator-Worker

**Why This Pattern?**
- Central coordinator (Orchestrator) manages complexity
- Workers (RAG agents) operate independently in parallel
- Clear separation of concerns
- Easy to add more companies (scale workers)
- Synthesis happens after all data collected

**Alternative Considered: Pipeline Pattern**
- Sequential: Query → RAG1 → RAG2 → Synthesis
- **Rejected**: Too slow, no parallelization benefit

---

## Component Design

### 1. Query Parser Agent

**Responsibility**: Understand user intent and extract structured information

**Input**:
```python
{
    "query": "Compare AAPL vs MSFT revenue growth",
    "user_id": "user_123",
    "session_id": "session_456"
}
```

**Output**:
```python
{
    "companies": ["AAPL", "MSFT"],
    "comparison_type": "revenue_growth",
    "metrics": ["revenue", "growth_rate"],
    "time_period": "recent",  # or specific: "Q4_2024"
    "sections_needed": ["Item 7", "Item 8"],
    "sub_queries": [
        "What was AAPL's revenue in recent quarters?",
        "What was MSFT's revenue in recent quarters?"
    ]
}
```

**Implementation**:
- Use LLM (Claude or GPT-4) for query understanding
- Structured output with Pydantic validation
- Fallback to simple regex if LLM fails

**Prompt Template**:
```python
QUERY_PARSER_PROMPT = """
You are a financial query parser. Extract structured information.

User Query: {query}

Extract:
1. Company tickers (e.g., AAPL, MSFT)
2. What they want to compare (revenue, margins, R&D, etc.)
3. Time period (if specified)
4. Output as JSON

Example:
Query: "Compare Apple and Microsoft revenues"
Output: {
    "companies": ["AAPL", "MSFT"],
    "comparison_type": "revenue",
    "metrics": ["total_revenue"],
    "time_period": "recent"
}

Now parse: {query}
"""
```

### 2. Orchestrator Agent

**Responsibility**: Coordinate parallel RAG queries and manage state

**Key Functions**:
```python
class OrchestratorAgent:
    async def orchestrate(self, parsed_query: Dict) -> Dict:
        """
        Main orchestration logic
        """
        # 1. Spawn parallel RAG agents
        tasks = [
            self.spawn_rag_agent(ticker, parsed_query)
            for ticker in parsed_query["companies"]
        ]
        
        # 2. Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. Handle errors
        results = self.handle_errors(results)
        
        # 4. Aggregate
        aggregated = self.aggregate_results(results)
        
        # 5. Synthesize
        synthesis = await self.synthesize(aggregated)
        
        return synthesis
```

**State Management**:
- Uses LangGraph StateGraph
- Checkpointing enabled for debugging
- Stores intermediate results

### 3. RAG Agent (Worker)

**Responsibility**: Query vector DB for specific company and extract relevant data

**Input**:
```python
{
    "ticker": "AAPL",
    "query": "What was AAPL's revenue in recent quarters?",
    "sections": ["Item 7", "Item 8"],
    "top_k": 5
}
```

**Output**:
```python
{
    "ticker": "AAPL",
    "chunks": [
        {
            "text": "Total net sales increased 6% or $19.0B...",
            "metadata": {
                "filing_type": "10-K",
                "report_date": "2024-09-30",
                "section": "Item 7",
                "page": 23
            },
            "score": 0.87
        },
        # ... more chunks
    ],
    "extracted_metrics": {
        "revenue": 119.6e9,
        "growth_rate": 0.12,
        "currency": "USD"
    },
    "status": "success"
}
```

**Implementation**:
- Reuses existing RAG pipeline
- Adds structured data extraction
- Returns both raw chunks and extracted metrics

### 4. Data Aggregation Layer

**Responsibility**: Combine results from multiple RAG agents into unified structure

**Input**: List of RAG agent outputs

**Output**:
```python
{
    "companies": {
        "AAPL": {
            "metrics": {"revenue": 119.6e9, "growth": 0.12},
            "chunks": [...],
            "status": "success"
        },
        "MSFT": {
            "metrics": {"revenue": 62.0e9, "growth": 0.18},
            "chunks": [...],
            "status": "success"
        }
    },
    "missing_data": [],
    "comparison_ready": true
}
```

**Key Logic**:
- Normalize data formats (handle different units, currencies)
- Identify missing data gracefully
- Create comparison matrix
- Flag inconsistencies

### 5. Synthesis Agent

**Responsibility**: Generate comparative narrative that explains differences

**This is the CORE VALUE of the feature**

**Input**: Aggregated data from all companies

**Output**: Markdown-formatted comparison with:
- Summary section
- Side-by-side metrics
- Explanation of differences
- Context from SEC filings
- Full citations

**Prompt Template**:
```python
SYNTHESIS_PROMPT = """
You are a financial analyst comparing companies.

Data:
{aggregated_data}

Task:
1. Create a comparison summary
2. Present key metrics side-by-side
3. Explain WHY differences exist (use SEC filing context)
4. Cite all sources

Format:
## [Metric] Comparison: [Company1] vs [Company2]

### Summary
[2-3 sentence overview]

### Key Findings
**[Company1]**
- Metric: Value
- Context from filings [citation]

**[Company2]**
- Metric: Value
- Context from filings [citation]

### Why the Difference?
[Explain using MD&A, risk factors, business description]

### Sources
[Numbered citations]
"""
```

**Key Requirements**:
- Every claim must be cited
- Explain *why*, not just *what*
- Use context from SEC filings (MD&A, risk factors)
- Handle missing data gracefully
- Generate comparison tables

---

## Data Flow

### Sequence Diagram

```
User          API         QueryParser   Orchestrator   RAG(AAPL)   RAG(MSFT)   Synthesis
 │              │              │              │              │            │           │
 │─Compare──────>│              │              │              │            │           │
 │              │─Parse────────>│              │              │            │           │
 │              │<─Parsed───────│              │              │            │           │
 │              │─Orchestrate──────────────────>│              │            │           │
 │              │              │              │─Query─────────>│            │           │
 │              │              │              │─Query──────────────────────>│           │
 │              │              │              │<─Results──────│            │           │
 │              │              │              │<─Results───────────────────│           │
 │              │              │              │─Aggregate─────────────────────────────>│
 │              │              │              │<─Synthesis─────────────────────────────│
 │<─Response────│<─────────────────────────────│              │            │           │
```

### State Transitions

```
[INIT] → [PARSING] → [ORCHESTRATING] → [QUERYING] → [AGGREGATING] → [SYNTHESIZING] → [COMPLETE]
                                           ↓
                                        [ERROR] → [RETRY] → [QUERYING]
                                           ↓
                                        [PARTIAL_SUCCESS] → [SYNTHESIZING]
```

---

## API Design

### New Endpoint: POST /api/compare

**Request**:
```json
{
  "query": "Compare AAPL vs MSFT revenue growth",
  "companies": ["AAPL", "MSFT"],  // Optional: override auto-detection
  "filing_type": "10-K",            // Optional: default to latest
  "time_period": "recent",          // Optional: "recent", "Q4_2024", etc.
  "options": {
    "include_tables": true,
    "max_companies": 3,
    "top_k_per_company": 5
  }
}
```

**Response**:
```json
{
  "comparison": {
    "summary": "Apple grew 12% vs Microsoft's 18%...",
    "companies": {
      "AAPL": {
        "metrics": {"revenue": 119.6e9, "growth": 0.12},
        "sources": [...]  
      },
      "MSFT": {
        "metrics": {"revenue": 62.0e9, "growth": 0.18},
        "sources": [...]
      }
    },
    "synthesis": "<markdown formatted comparison>",
    "table": {
      "headers": ["Metric", "AAPL", "MSFT"],
      "rows": [
        ["Revenue", "$119.6B", "$62.0B"],
        ["Growth", "12%", "18%"]
      ]
    },
    "citations": [
      {"id": 1, "company": "AAPL", "filing": "10-K", "date": "2024-09-30"},
      {"id": 2, "company": "MSFT", "filing": "10-K", "date": "2024-06-30"}
    ]
  },
  "metadata": {
    "processing_time": 8.3,
    "companies_processed": 2,
    "total_chunks_used": 10,
    "status": "success"
  }
}
```

**Error Response**:
```json
{
  "error": "partial_failure",
  "message": "Could not retrieve data for TSLA",
  "details": {
    "successful": ["AAPL", "MSFT"],
    "failed": ["TSLA"],
    "reason": "No filings found in database"
  },
  "partial_result": {
    "comparison": "<comparison of AAPL vs MSFT only>"
  }
}
```

---

## State Management

### LangGraph State Schema

```python
from typing import TypedDict, List, Dict, Any, Annotated
from operator import add

class ComparisonState(TypedDict):
    """Global state for comparison workflow"""
    
    # Input
    query: str
    user_id: str
    session_id: str
    
    # Parsed query
    companies: List[str]
    comparison_type: str
    metrics: List[str]
    time_period: str
    
    # RAG results (accumulated from parallel agents)
    rag_results: Annotated[Dict[str, Any], add]
    
    # Aggregated data
    aggregated_data: Dict[str, Any]
    comparison_matrix: Dict[str, Any]
    
    # Synthesis
    synthesis: str
    formatted_output: str
    
    # Metadata
    execution_log: Annotated[List[str], add]
    errors: Annotated[List[Dict], add]
    processing_time: float
    
    # Status
    status: str  # "parsing", "querying", "synthesizing", "complete", "error"
```

### State Updates

```python
# Query Parser updates
state["companies"] = ["AAPL", "MSFT"]
state["comparison_type"] = "revenue_growth"

# RAG agents accumulate results
state["rag_results"]["AAPL"] = {...}
state["rag_results"]["MSFT"] = {...}

# Synthesis agent adds final output
state["synthesis"] = "<markdown comparison>"
```

---

## Error Handling

### Error Scenarios

1. **Company Not in Database**
   - **Handling**: Return partial results for available companies
   - **Message**: "TSLA not found. Showing comparison of AAPL vs MSFT only."

2. **No Comparable Data**
   - **Handling**: Explain what's missing
   - **Message**: "AAPL has revenue data but MSFT's latest 10-K doesn't include segment breakdown."

3. **Query Too Vague**
   - **Handling**: Ask for clarification
   - **Message**: "Did you mean revenue growth or profit margins? Please clarify."

4. **Too Many Companies**
   - **Handling**: Limit to 3, suggest narrowing
   - **Message**: "Comparing 5 companies at once. Showing top 3 by market cap. Refine your query?"

5. **Timeout**
   - **Handling**: Return cached results if available
   - **Message**: "Query taking longer than expected. Here are preliminary results..."

### Graceful Degradation

```python
if rag_results["AAPL"]["status"] == "success" and rag_results["MSFT"]["status"] == "error":
    # Partial success
    return {
        "comparison": "Partial comparison available",
        "note": "Could not retrieve MSFT data. Showing AAPL only.",
        "suggestion": "Try again or check if MSFT filings are processed."
    }
```

---

## Performance Considerations

### Target Metrics
- **2-company comparison**: < 10 seconds
- **3-company comparison**: < 15 seconds
- **Success rate**: > 95%

### Optimization Strategies

1. **Parallel Execution**
   ```python
   # Run RAG queries in parallel
   results = await asyncio.gather(
       rag_agent("AAPL"),
       rag_agent("MSFT"),
       rag_agent("GOOGL")
   )
   ```

2. **Caching**
   - Cache parsed queries (5 min TTL)
   - Cache RAG results per company (1 hour TTL)
   - Cache embeddings (permanent)

3. **Vector Search Optimization**
   - Use Qdrant's filtering before vector search
   - Reduce top_k to 5 (from 10)
   - Pre-filter by filing type and date

4. **LLM Optimization**
   - Use smaller model for query parsing (Haiku)
   - Use larger model only for synthesis (Sonnet)
   - Stream synthesis output for perceived speed

### Bottleneck Analysis

```
Typical 2-company comparison breakdown:
- Query parsing: 0.5s
- Parallel RAG queries: 3-5s (2x in parallel)
- Data aggregation: 0.2s
- Synthesis: 3-4s
- Formatting: 0.1s
─────────────────────────
Total: 7-10s ✅
```

---

## Testing Strategy

### Unit Tests

```python
def test_query_parser():
    """Test query parsing extracts correct companies"""
    query = "Compare Apple and Microsoft revenues"
    result = query_parser.parse(query)
    assert result["companies"] == ["AAPL", "MSFT"]
    assert result["comparison_type"] == "revenue"

def test_rag_agent_single_company():
    """Test RAG agent returns valid results"""
    result = rag_agent.query("AAPL", "revenue")
    assert result["status"] == "success"
    assert len(result["chunks"]) > 0
    assert "revenue" in result["extracted_metrics"]

def test_aggregation_handles_missing_data():
    """Test aggregation gracefully handles missing company"""
    results = {
        "AAPL": {"status": "success", "metrics": {...}},
        "TSLA": {"status": "error", "error": "not_found"}
    }
    aggregated = aggregator.aggregate(results)
    assert aggregated["comparison_ready"] == True
    assert "TSLA" in aggregated["missing_data"]
```

### Integration Tests

```python
async def test_end_to_end_comparison():
    """Test full comparison workflow"""
    query = "Compare AAPL vs MSFT revenue growth"
    result = await comparison_api.compare(query)
    
    assert result["metadata"]["status"] == "success"
    assert len(result["comparison"]["companies"]) == 2
    assert "AAPL" in result["comparison"]["companies"]
    assert "MSFT" in result["comparison"]["companies"]
    assert len(result["comparison"]["citations"]) > 0
    assert result["metadata"]["processing_time"] < 10.0
```

### Test Cases

| Test Case | Expected Behavior |
|-----------|------------------|
| 2 companies, both in DB | Full comparison with citations |
| 3 companies, all in DB | Full comparison, < 15s |
| 1 company not in DB | Partial comparison with note |
| Vague query | Ask for clarification |
| Conflicting data | Explain discrepancy |
| No comparable sections | Graceful message |

---

## Open Questions

### For Discussion

1. **Comparison Tables**
   - Q: Should we generate visual tables or just markdown?
   - Options: 
     - A) Markdown tables (simple, fast)
     - B) Structured JSON for frontend rendering (flexible)
   - **Decision Needed**: Week 1

2. **Time Period Handling**
   - Q: How do we handle companies with different fiscal year ends?
   - Example: AAPL (Sep 30) vs MSFT (Jun 30)
   - Options:
     - A) Compare most recent quarters regardless of alignment
     - B) Align by calendar quarters
     - C) Explain the mismatch in output
   - **Decision Needed**: Week 2

3. **Synthesis Model Choice**
   - Q: Which LLM for synthesis?
   - Options:
     - A) Claude Sonnet (best quality, $$$)
     - B) GPT-4 (good quality, $$)
     - C) Llama 3.1 70B local (free, slower)
   - **Decision Needed**: Week 3 (after quality testing)

4. **Missing Data Strategy**
   - Q: What if one company has revenue but not margins?
   - Options:
     - A) Compare only available metrics
     - B) Fetch additional filings
     - C) Use external data sources
   - **Decision Needed**: Week 2

5. **Caching Strategy**
   - Q: How long to cache comparison results?
   - Considerations: SEC filings update quarterly
   - Options:
     - A) Cache for 1 week
     - B) Cache until next filing
     - C) No caching (always fresh)
   - **Decision Needed**: Week 4

---

## Next Steps

### Week 1-2: Parallel RAG Queries
1. Implement query parser
2. Build orchestrator agent
3. Modify existing RAG agent for parallel execution
4. Test with 2 companies
5. **Deliverable**: Parallel queries working, returning raw results

### Week 3-4: Synthesis Agent
1. Design synthesis prompt
2. Implement data aggregation layer
3. Build synthesis agent
4. Test comparison quality
5. **Deliverable**: End-to-end comparison with basic synthesis

### Week 5-6: Polish & Testing
1. Add comparison tables
2. Improve error handling
3. Performance optimization
4. Comprehensive testing
5. Documentation
6. **Deliverable**: Production-ready feature

---

## Success Criteria Review

- [ ] Sub-10-second response for 2-company comparison
- [ ] Accurate source citations (100% of claims cited)
- [ ] Handles 80% of comparative queries without errors
- [ ] Graceful degradation when data missing
- [ ] Can explain architecture decisions in interview
- [ ] Code is maintainable and well-documented

---

**Next Document**: [Low-Level Design: Component Implementation Details](./COMPARATIVE_ANALYSIS_LOW_LEVEL_DESIGN.md) (to be created after design review)