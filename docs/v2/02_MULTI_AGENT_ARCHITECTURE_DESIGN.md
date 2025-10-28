# Finance Agent v2.0: Multi-Agent Architecture Design

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Agent Design](#agent-design)
4. [State Management](#state-management)
5. [Tool Design](#tool-design)
6. [Integration with Existing System](#integration-with-existing-system)
7. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### Current State (Finance Agent v1.0)
```
Single-Agent RAG System
┌─────────────────────────────────────────┐
│          User Query                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│     Query Embedding (nomic-embed-text)   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│   Qdrant Similarity Search (top 5)       │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│   LLM Generation (Llama 3.1/phi3:mini)   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Response with Citations          │
└──────────────────────────────────────────┘
```

**Limitations**:
- ❌ Can't compare across multiple companies
- ❌ No web context for recent events
- ❌ Limited reasoning on complex financial questions
- ❌ No research planning or task decomposition
- ❌ Sequential processing only

---

### Target State (Finance Agent v2.0)
```
Multi-Agent Orchestrator System
┌─────────────────────────────────────────────────────────┐
│                 User Complex Query                       │
│  "Compare Apple and Microsoft Q4 revenues and explain    │
│   the difference in context of recent market trends"     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Lead Finance Agent                          │
│  • Analyzes query complexity                             │
│  • Creates research plan                                 │
│  • Spawns specialized subagents                          │
│  • Synthesizes final response                            │
└─────┬──────────┬──────────┬──────────┬─────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│ SEC RAG │ │Financial│ │  Web    │ │Citation  │
│ Agent   │ │Analysis │ │ Search  │ │  Agent   │
│         │ │ Agent   │ │ Agent   │ │          │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘
     │           │           │           │
     └───────────┴───────────┴───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Comprehensive Answer with Citations              │
└─────────────────────────────────────────────────────────┘
```

**Capabilities**:
- ✅ Parallel information gathering
- ✅ Complex reasoning and planning
- ✅ Multi-source synthesis
- ✅ Web context integration
- ✅ Advanced financial calculations
- ✅ Intelligent task decomposition

---

## Architecture Patterns

### Pattern 1: Orchestrator-Worker (Recommended)

**Description**: Single lead agent coordinates specialized worker agents

**Use When**:
- Query complexity varies (simple to complex)
- Need dynamic task allocation
- Want centralized coordination

**Flow**:
```
User → Lead Agent → [Worker 1, Worker 2, Worker 3] → Lead Agent → User
```

**Pros**:
- Flexible adaptation to query complexity
- Clear responsibility separation
- Easy to add new worker types

**Cons**:
- Lead agent is bottleneck
- Synchronous coordination overhead

### Pattern 2: Hierarchical Multi-Agent

**Description**: Tree structure with managers and specialists

**Use When**:
- Very complex queries with sub-tasks
- Need multiple coordination layers
- Building research reports

**Flow**:
```
Chief Agent
├── Research Manager
│   ├── SEC Agent
│   └── News Agent
└── Analysis Manager
    ├── Calculation Agent
    └── Comparison Agent
```

**Pros**:
- Handles extreme complexity
- Modular and scalable

**Cons**:
- Higher latency
- More token usage
- Complex debugging

### Pattern 3: Pipeline (Sequential)

**Description**: Linear sequence of specialized agents

**Use When**:
- Clear sequential steps
- Each step depends on previous
- Workflow is predictable

**Flow**:
```
Retrieval → Validation → Analysis → Citation → Response
```

**Pros**:
- Simple to understand
- Predictable execution
- Easy debugging

**Cons**:
- No parallelization
- Slower for complex queries
- Rigid workflow

### Pattern 4: Peer-to-Peer Collaboration

**Description**: Agents communicate directly without central coordinator

**Use When**:
- Need emergent problem-solving
- Agents have equal authority
- Complex deliberation required

**Flow**:
```
Agent A ↔ Agent B
   ↕         ↕
Agent C ↔ Agent D
```

**Pros**:
- Flexible problem-solving
- No single point of failure

**Cons**:
- Hard to control
- Can be non-deterministic
- Difficult to debug

---

## Recommended Architecture for Finance Agent v2.0

### **Hybrid: Orchestrator-Worker + Pipeline**

```python
"""
Primary pattern: Orchestrator-Worker for query handling
Secondary pattern: Pipeline within each worker for internal workflow
"""

graph = StateGraph(FinanceAgentState)

# Orchestrator layer
graph.add_node("lead_agent", lead_finance_agent)

# Worker layer (parallel execution possible)
graph.add_node("sec_rag_agent", sec_retrieval_agent)
graph.add_node("web_search_agent", web_search_agent)
graph.add_node("financial_analysis_agent", analysis_agent)

# Post-processing layer (pipeline)
graph.add_node("citation_agent", citation_agent)
graph.add_node("quality_check", quality_checker)

# Workflow edges
graph.add_edge(START, "lead_agent")
graph.add_conditional_edges(
    "lead_agent",
    route_to_workers,
    ["sec_rag_agent", "web_search_agent", "financial_analysis_agent"]
)
# Workers report back to lead agent
for worker in ["sec_rag_agent", "web_search_agent", "financial_analysis_agent"]:
    graph.add_edge(worker, "citation_agent")

graph.add_edge("citation_agent", "quality_check")
graph.add_conditional_edges(
    "quality_check",
    needs_more_research,
    {
        "continue": "lead_agent",  # Loop back if needed
        "finish": END
    }
)
```

---

## Agent Design

### 1. Lead Finance Agent (Orchestrator)

**Role**: Coordinates the entire research process

**Responsibilities**:
1. Query analysis and understanding
2. Research plan creation
3. Worker agent spawning and coordination
4. Result synthesis
5. Quality assessment

**Model Choice**: Claude Sonnet 4.5 or Llama 3.1 70B
- Needs strong reasoning for planning
- Must handle long context for synthesis

**Prompt Structure**:
```python
LEAD_AGENT_PROMPT = """You are the Lead Financial Research Agent.

Your responsibilities:
1. Analyze the user's query to determine:
   - What companies are mentioned?
   - What time periods are relevant?
   - What financial metrics are needed?
   - What level of detail is required?
   - Is external context (news, market trends) needed?

2. Create a research plan:
   - Decompose into subtasks
   - Assign subtasks to specialist agents
   - Determine if tasks can run in parallel
   - Set success criteria for each subtask

3. Coordinate workers:
   - Spawn SEC RAG agents for each company
   - Trigger web search if recent context needed
   - Request financial calculations if comparisons needed
   - Ensure no redundant work across agents

4. Synthesize results:
   - Combine findings from all workers
   - Resolve any conflicts in data
   - Create coherent narrative
   - Ensure all claims are cited

Query Complexity Guidelines:
- Simple (single company, single metric): 1 agent, direct RAG
- Medium (comparison, multiple metrics): 2-3 agents, parallel RAG
- Complex (analysis, trends, context): 5+ agents, full orchestration

Current query: {query}

Available tools:
- spawn_sec_rag_agent: Retrieves SEC filing data
- spawn_web_search_agent: Searches web for context
- spawn_analysis_agent: Performs calculations and comparisons
- add_citation: Adds source attribution

Begin by analyzing the query and creating your research plan.
"""
```

**State It Manages**:
```python
class LeadAgentState(TypedDict):
    query: str
    query_type: Literal["simple", "medium", "complex"]
    research_plan: Dict[str, Any]
    worker_results: Dict[str, Any]
    synthesis: str
    quality_score: float
```

---

### 2. SEC RAG Agent (Worker)

**Role**: Retrieves and processes SEC filing data

**Responsibilities**:
1. Search your existing Qdrant vector DB
2. Filter by ticker, filing type, date range
3. Extract relevant sections
4. Return structured data with metadata

**Model Choice**: Llama 3.1 8B (local) or phi3:mini
- Retrieval is well-defined task
- Can use smaller model for cost efficiency
- Ollama handles local inference

**Prompt Structure**:
```python
SEC_RAG_AGENT_PROMPT = """You are a specialized SEC Filing Retrieval Agent.

Task: {task_description}

Your responsibilities:
1. Search the SEC filings database for: {target_company}
2. Focus on filing types: {filing_types}  # e.g., ["10-K", "10-Q"]
3. Look in sections: {sections}  # e.g., ["Item 8", "Management Discussion"]
4. Date range: {date_range}

Search strategy:
- Start with broad semantic search
- Filter by metadata (ticker, filing_type, date)
- Retrieve top 10 chunks initially
- Re-rank by relevance to specific question
- Return top 5 with confidence scores

Output format:
{{
  "company": str,
  "filing_type": str,
  "filing_date": str,
  "chunks": [
    {{
      "text": str,
      "section": str,
      "page": int,
      "relevance_score": float,
      "source_url": str
    }}
  ],
  "summary": str
}}

Current available chunks in database: {available_count}

Begin search now.
"""
```

**Integration with Existing RAG**:
```python
async def sec_rag_agent(state: AgentState) -> AgentState:
    """
    Wraps your existing RAG system as a LangGraph node
    """
    task = state["task"]
    
    # Use your existing code
    embeddings = generate_embeddings(task["query"])
    results = qdrant_client.search(
        collection_name="sec_filings",
        query_vector=embeddings,
        limit=10,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="ticker",
                    match=models.MatchValue(value=task["ticker"])
                ),
                models.FieldCondition(
                    key="filing_type",
                    match=models.MatchAny(any=task["filing_types"])
                )
            ]
        )
    )
    
    # Format for agent consumption
    state["retrieval_results"][task["ticker"]] = {
        "chunks": [r.payload for r in results],
        "metadata": {"source": "qdrant", "timestamp": datetime.now()}
    }
    
    return state
```

---

### 3. Web Search Agent (Worker)

**Role**: Provides recent context beyond SEC filings

**Responsibilities**:
1. Search web for company news, market trends
2. Find analyst reports and earnings calls
3. Gather competitor information
4. Validate with authoritative sources

**Model Choice**: Claude Haiku or Llama 3.1 8B
- Fast inference for parallel searches
- Good enough for search query generation

**Tools**:
- Tavily API (recommended for structured results)
- SerpAPI (backup option)
- Custom web scraper for specific sites

**Prompt Structure**:
```python
WEB_SEARCH_AGENT_PROMPT = """You are a Web Research Agent specializing in financial information.

Task: {task_description}

Research objectives:
- Companies: {companies}
- Topics: {topics}  # e.g., ["revenue trends", "market competition"]
- Time period: {time_period}  # "last 6 months", "Q4 2024", etc.

Search strategy:
1. Construct 2-3 word search queries (not full questions)
2. Start broad: "{company} Q4 2024 revenue"
3. Then narrow: "{company} revenue growth factors"
4. Use multiple searches in parallel (3-5 queries)
5. Prefer authoritative sources:
   - Company investor relations
   - Major financial news (WSJ, Bloomberg, FT)
   - SEC announcements
   - Analyst reports (if accessible)

Avoid:
- SEO spam sites
- Unverified forums
- Clickbait headlines
- Outdated information (check dates!)

Output format:
{{
  "findings": [
    {{
      "title": str,
      "source": str,
      "url": str,
      "publish_date": str,
      "key_points": List[str],
      "relevance_score": float
    }}
  ],
  "summary": str,
  "confidence": float
}}

Execute 3-5 parallel searches now.
"""
```

---

### 4. Financial Analysis Agent (Worker)

**Role**: Performs calculations, comparisons, trend analysis

**Responsibilities**:
1. Extract numbers from retrieved documents
2. Calculate financial ratios and metrics
3. Perform comparative analysis
4. Identify trends and anomalies

**Model Choice**: Claude Sonnet 4 or GPT-4
- Needs strong reasoning for math
- Should validate calculations
- Can generate Python code for complex math

**Tools**:
- Python code execution (sandboxed)
- Financial formula library
- Data validation functions

**Prompt Structure**:
```python
ANALYSIS_AGENT_PROMPT = """You are a Financial Analysis Agent with strong quantitative skills.

Task: {task_description}

Available data:
- Company A: {company_a_data}
- Company B: {company_b_data}
- Market context: {market_context}

Analysis requirements:
- Metrics to calculate: {required_metrics}  # ["revenue_growth", "margin_comparison", etc.]
- Comparison type: {comparison_type}  # "year-over-year", "company vs company", etc.

Methodology:
1. Extract all relevant numbers from source documents
2. Validate data quality (check for inconsistencies)
3. Perform calculations using Python (show your work)
4. Interpret results in business context
5. Flag any limitations or assumptions

Tools available:
- execute_python: Run Python code for calculations
- validate_financial_data: Check data consistency
- fetch_historical_data: Get prior period comparisons

Output format:
{{
  "calculations": [
    {{
      "metric": str,
      "formula": str,
      "result": float,
      "unit": str,
      "code": str  # Python code used
    }}
  ],
  "insights": List[str],
  "limitations": List[str],
  "confidence": float
}}

Begin analysis.
"""
```

---

### 5. Citation Agent (Post-Processor)

**Role**: Adds proper source attribution to final answer

**Responsibilities**:
1. Track all sources used in research
2. Match claims to specific sources
3. Format citations consistently
4. Generate bibliography

**Model Choice**: Claude Haiku (fast, accurate)

**Prompt Structure**:
```python
CITATION_AGENT_PROMPT = """You are a Citation Agent ensuring all claims are properly attributed.

Task: Add citations to the following answer

Answer to cite: {answer}

Available sources:
{sources}  # List of all sources with IDs

Citation rules:
1. Every factual claim needs a citation
2. Use superscript numbers: [1], [2], etc.
3. Multiple sources for one claim: [1,2]
4. Direct quotes must be in "quotes" with citation
5. General knowledge doesn't need citation

Citation format:
[1] {Company} {FilingType} ({Date}), {Section}, p.{Page}
[2] {Publisher}, "{ArticleTitle}", {URL}, {Date}

Example output:
"Apple reported revenues of $119.6B in Q1 2024[1], while Microsoft reported $62.0B[2]. 
This represents 12% growth for Apple[1] compared to 18% for Microsoft[2]."

Bibliography:
[1] Apple Inc. 10-Q (2024-01-01), Item 1, p.3
[2] Microsoft Corp. 10-Q (2024-01-01), Item 1, p.5

Now add citations to the answer.
"""
```

---

## State Management

### Global State Schema
```python
from typing import TypedDict, List, Dict, Any, Literal, Annotated
from operator import add
from datetime import datetime

class FinanceAgentState(TypedDict):
    """
    Global state shared across all agents in the graph
    """
    # Input
    query: str
    user_id: str
    session_id: str
    
    # Query Analysis
    query_type: Literal["simple", "medium", "complex"]
    companies_mentioned: List[str]
    metrics_requested: List[str]
    time_period: Dict[str, Any]
    requires_web_search: bool
    
    # Research Plan
    research_plan: Dict[str, Any]
    subtasks: List[Dict[str, Any]]
    
    # Agent Results (accumulated)
    retrieval_results: Annotated[Dict[str, Any], add]  # Merges results
    web_search_results: Annotated[List[Dict], add]
    analysis_results: Annotated[Dict[str, Any], add]
    
    # Intermediate Processing
    extracted_data: Dict[str, Any]
    calculations: List[Dict[str, Any]]
    
    # Quality Control
    validation_status: Dict[str, bool]
    confidence_scores: Dict[str, float]
    
    # Final Output
    synthesis: str
    citations: List[str]
    final_answer: str
    
    # Metadata
    execution_log: Annotated[List[str], add]
    token_usage: Dict[str, int]
    latency: Dict[str, float]
```

### State Management Patterns

#### 1. Reducer Pattern (for accumulation)
```python
from operator import add

# This accumulates results from multiple agents
retrieval_results: Annotated[Dict[str, Any], add]

# Usage in agent:
def agent(state):
    state["retrieval_results"]["apple"] = {...}
    return state  # Merges with existing results
```

#### 2. Conditional Updates
```python
def update_if_confident(state):
    if state["confidence_scores"]["retrieval"] > 0.8:
        state["validated"] = True
    return state
```

#### 3. State Snapshots (Checkpointing)
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Your existing PostgreSQL
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/financeagent"
)

# Automatic checkpointing after each node
app = graph.compile(checkpointer=checkpointer)

# Resume from any point
config = {"configurable": {"thread_id": "query_12345"}}
result = app.invoke(input_state, config=config)

# Time-travel for debugging
for state in app.get_state_history(config):
    print(f"Step: {state.values}")
```

---

## Tool Design

### Tool Requirements (Anthropic Best Practices)

1. **Clear Purpose**: Each tool does ONE thing well
2. **Good Descriptions**: Agent understands when to use it
3. **Consistent Interface**: Predictable inputs/outputs
4. **Error Handling**: Graceful failures with helpful messages
5. **Testing**: Tool works reliably before agent uses it

### Core Tools for Finance Agent

#### 1. SEC RAG Tool
```python
from langchain.tools import tool
from typing import List, Dict

@tool
def search_sec_filings(
    ticker: str,
    filing_type: List[str],
    query: str,
    date_range: Dict[str, str] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Search SEC filings for a specific company.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        filing_type: Types of filings to search (e.g., ["10-K", "10-Q"])
        query: Natural language query about company
        date_range: Optional {"start": "2024-01-01", "end": "2024-12-31"}
        limit: Maximum number of results to return
    
    Returns:
        {
            "results": [
                {
                    "text": str,
                    "metadata": {...},
                    "score": float
                }
            ],
            "total_found": int
        }
    
    Use this tool when you need information from SEC filings like:
    - Financial statements (balance sheet, income statement, cash flow)
    - Management discussion (MD&A)
    - Risk factors
    - Business description
    
    Do NOT use for:
    - Real-time stock prices (use market_data tool)
    - News and market sentiment (use web_search tool)
    - General company information (use web_search tool)
    """
    # Your existing Qdrant logic here
    pass
```

#### 2. Web Search Tool
```python
@tool
def search_financial_news(
    query: str,
    companies: List[str] = None,
    max_results: int = 5,
    time_period: str = "1m"  # 1month, 3m, 6m, 1y
) -> Dict[str, Any]:
    """
    Search the web for recent financial news and analysis.
    
    Args:
        query: Search query (keep it 2-4 words)
        companies: Optional list of company tickers to focus on
        max_results: Number of results to return (max 10)
        time_period: How far back to search ("1m", "3m", "6m", "1y")
    
    Returns:
        {
            "results": [
                {
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "published": str,
                    "source": str
                }
            ]
        }
    
    Use this tool when you need:
    - Recent company news or announcements
    - Market trends and analyst opinions
    - Competitor information
    - Industry context
    
    Search strategy:
    - Start broad: "Apple Q4 revenue"
    - Then narrow: "Apple iPhone sales decline"
    - Use 3-5 parallel searches for comprehensive coverage
    
    Do NOT use for:
    - Historical financial data (use SEC tool)
    - Precise calculations (use analysis tool)
    """
    # Implementation with Tavily/SerpAPI
    pass
```

#### 3. Financial Calculation Tool
```python
@tool
def calculate_financial_metric(
    metric_name: str,
    data: Dict[str, float],
    period_type: str = "quarterly"
) -> Dict[str, Any]:
    """
    Calculate financial metrics and ratios.
    
    Args:
        metric_name: Name of metric (see supported_metrics below)
        data: Dictionary of financial data points
        period_type: "quarterly", "annual", "ttm" (trailing twelve months)
    
    Supported metrics:
        - revenue_growth: ((current - previous) / previous) * 100
        - operating_margin: (operating_income / revenue) * 100
        - net_margin: (net_income / revenue) * 100
        - roe: (net_income / shareholder_equity) * 100
        - roa: (net_income / total_assets) * 100
        - debt_to_equity: total_debt / shareholder_equity
        - current_ratio: current_assets / current_liabilities
        - eps_growth: ((current_eps - previous_eps) / previous_eps) * 100
    
    Returns:
        {
            "metric": str,
            "value": float,
            "unit": str,  # "%", "ratio", "$", etc.
            "formula": str,
            "inputs_used": Dict[str, float]
        }
    
    Example:
        calculate_financial_metric(
            "revenue_growth",
            {
                "current_revenue": 119.6e9,
                "previous_revenue": 106.8e9
            },
            "quarterly"
        )
    """
    # Implementation with validated formulas
    pass
```

#### 4. Code Execution Tool (Advanced)
```python
@tool
def execute_financial_analysis_code(
    code: str,
    data_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Python code for complex financial analysis.
    
    Args:
        code: Python code to execute (string)
        data_context: Variables to inject into execution context
    
    Returns:
        {
            "result": Any,
            "stdout": str,
            "stderr": str,
            "execution_time": float
        }
    
    Security:
        - Executes in sandboxed environment
        - Limited imports (pandas, numpy, scipy only)
        - 30 second timeout
        - No file system access
    
    Use when:
        - Complex multi-step calculations needed
        - Statistical analysis required
        - Custom metric computation
    
    Example:
        code = '''
        import pandas as pd
        df = pd.DataFrame(revenue_data)
        growth_rate = df["revenue"].pct_change()
        result = {
            "average_growth": growth_rate.mean(),
            "volatility": growth_rate.std()
        }
        '''
    """
    # Sandboxed execution implementation
    pass
```

---

## Integration with Existing System

### Phase 1: Minimal Disruption (Week 1-2)

**Goal**: Add LangGraph alongside existing RAG without breaking anything

**Changes**:
```
Current:
POST /query → single_agent_rag() → response

New (parallel):
POST /query-multi-agent → langgraph_handler() → response
POST /query → single_agent_rag() → response (unchanged)
```

**Implementation**:
```python
# app/api/v2/endpoints.py

from langgraph.graph import StateGraph, END
from app.agents.lead_agent import lead_agent
from app.agents.rag_agent import rag_agent

# New endpoint for multi-agent
@router.post("/query-multi-agent")
async def query_multi_agent(
    query: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    # Build graph
    graph = StateGraph(FinanceAgentState)
    graph.add_node("lead", lead_agent)
    graph.add_node("rag", rag_agent_wrapper)  # Wraps your existing RAG
    graph.add_edge("lead", "rag")
    graph.add_edge("rag", END)
    
    app = graph.compile()
    
    # Execute
    result = await app.ainvoke({
        "query": query,
        "user_id": user_id,
        "session_id": str(uuid.uuid4())
    })
    
    return {
        "answer": result["final_answer"],
        "citations": result["citations"],
        "execution_log": result["execution_log"]
    }

# Wrapper to reuse existing RAG
def rag_agent_wrapper(state: FinanceAgentState) -> FinanceAgentState:
    """
    Wraps your existing RAG system as a LangGraph node
    """
    from app.services.rag_service import query_rag  # Your existing function
    
    result = query_rag(
        query=state["query"],
        ticker=state.get("companies_mentioned", [""])[0],
        top_k=5
    )
    
    state["retrieval_results"] = result
    return state
```

### Phase 2: Parallel Agents (Week 3-4)

**Goal**: Add parallel execution for multiple companies

**Changes**:
- Lead agent spawns multiple RAG agents
- Each RAG agent queries for different company
- Results combined in synthesis step

**Graph**:
```python
def build_parallel_graph():
    graph = StateGraph(FinanceAgentState)
    
    graph.add_node("lead", lead_agent)
    
    # Dynamically add RAG nodes based on companies
    def route_to_rag_agents(state):
        companies = state["companies_mentioned"]
        return [f"rag_{company}" for company in companies]
    
    # Add a RAG node for each company
    for company in ["apple", "microsoft", "google"]:  # Example
        graph.add_node(
            f"rag_{company}",
            lambda state, c=company: rag_agent(state, c)
        )
    
    # Lead agent decides which companies to query
    graph.add_conditional_edges(
        "lead",
        route_to_rag_agents,
        # Dynamic routing based on companies mentioned
    )
    
    # All RAG agents converge to synthesis
    graph.add_node("synthesis", synthesis_agent)
    for company in ["apple", "microsoft", "google"]:
        graph.add_edge(f"rag_{company}", "synthesis")
    
    graph.add_edge("synthesis", END)
    
    return graph.compile()
```

### Phase 3: Full Multi-Agent (Week 5-6)

**Goal**: Add web search, analysis, citation agents

**Architecture**:
```
Lead Agent
├── SEC RAG Agents (parallel)
│   ├── Apple RAG
│   ├── Microsoft RAG
│   └── Google RAG
├── Web Search Agents (parallel)
│   ├── Apple News
│   ├── Microsoft News
│   └── Market Trends
├── Analysis Agent
│   └── Compares all data
└── Citation Agent
    └── Adds sources
```

### Phase 4: Production Hardening (Week 7-8)

**Goals**:
- Add comprehensive error handling
- Implement retry logic
- Add observability and monitoring
- Optimize performance
- Deploy to production

**Error Handling**:
```python
from langgraph.prebuilt import ToolNode

def handle_tool_error(state: FinanceAgentState) -> FinanceAgentState:
    """
    Called when tool execution fails
    """
    error = state.get("error")
    state["execution_log"].append(f"Tool error: {error}")
    
    # Retry logic
    if state.get("retry_count", 0) < 3:
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state  # Retry
    else:
        # Fallback: use cached data or return partial results
        state["final_answer"] = "Partial results available due to errors"
        return state

graph.add_conditional_edges(
    "rag_agent",
    lambda state: "error" if state.get("error") else "success",
    {
        "error": handle_tool_error,
        "success": "next_step"
    }
)
```

---

## Deployment Architecture

### Development Environment
```
Docker Compose Services:
├── fastapi (your existing backend + LangGraph server)
├── postgres (existing + checkpointing tables)
├── qdrant (existing vector DB)
├── ollama (existing local LLMs)
├── redis (existing cache + session management)
└── langgraph-studio (new - for debugging)
```

### Production Environment (Self-Hosted)
```
Kubernetes/Docker Swarm:
├── API Gateway (nginx/traefik)
├── Finance Agent Service (replicas: 3)
│   ├── FastAPI
│   ├── LangGraph runtime
│   └── Connection to shared resources
├── Postgres (StatefulSet)
│   ├── Application data
│   └── LangGraph checkpoints
├── Qdrant (StatefulSet)
│   └── Vector embeddings
├── Ollama (StatefulSet with GPU)
│   └── Local model inference
├── Redis (StatefulSet)
│   └── Caching + sessions
└── Monitoring Stack
    ├── Prometheus (metrics)
    ├── Grafana (dashboards)
    └── Loki (logs)
```

### Scaling Considerations

**Stateless Components** (can scale horizontally):
- FastAPI servers
- LangGraph execution workers
- Ollama inference (with load balancer)

**Stateful Components** (scale vertically or use replication):
- PostgreSQL (read replicas for checkpoints)
- Qdrant (sharding for large datasets)
- Redis (clustering for high availability)

**Resource Allocation**:
```yaml
# Example Kubernetes resources
fastapi-langgraph:
  replicas: 3
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"

ollama-gpu:
  replicas: 2
  resources:
    requests:
      memory: "16Gi"
      nvidia.com/gpu: 1
    limits:
      memory: "32Gi"
      nvidia.com/gpu: 1
```

---

## Next Steps

1. **Read**: Cursor IDE Rules document for coding guidelines
2. **Study**: LangGraph quickstart and tutorials
3. **Build**: Start with Phase 1 (minimal disruption)
4. **Test**: Use evaluation framework (separate document)
5. **Deploy**: Follow deployment guide (separate document)

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Orchestrator-Worker pattern | Balances flexibility and control |
| PostgreSQL for checkpointing | Reuse existing infrastructure |
| Hybrid local+API models | Cost optimization + quality |
| Parallel agent execution | Faster query resolution |
| Tool-first design | Better maintainability |
| Gradual migration | Minimize risk |

---

## Resources

- [LangGraph Multi-Agent Docs](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Exa Production Case Study](https://blog.langchain.com/exa/)
