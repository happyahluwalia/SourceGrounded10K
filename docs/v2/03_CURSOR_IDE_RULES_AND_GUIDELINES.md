# Cursor IDE Rules for Multi-Agent Finance Agent Development

## How to Use This Document

Add these rules to your Cursor IDE:
1. Create `.cursorrules` file in your project root
2. Copy relevant sections from this document
3. Cursor will use these rules for AI-assisted coding

---

## Core Development Principles

### 1. Agent Design Principles

```
AGENT DESIGN RULES:
- Each agent should have a single, clear responsibility
- Agents communicate only through shared state (no side effects)
- Always include type hints for agent functions
- Agent prompts should be stored in separate files (prompts/ directory)
- Never hardcode prompts in Python code
- Each agent should be testable in isolation
- Use async/await for all agent operations
- Log every agent decision and action

Example agent structure:
```python
async def research_agent(
    state: ResearchAgentState,
    config: RunnableConfig
) -> ResearchAgentState:
    """
    Brief description of agent's purpose.
    
    Responsibility: [Single clear task]
    Input: [What it needs from state]
    Output: [What it adds to state]
    """
    # Load prompt from file
    prompt = load_prompt("research_agent")
    
    # Execute with error handling
    try:
        result = await llm.ainvoke(prompt.format(**state))
        state["research_results"] = result
        state["execution_log"].append(f"Research completed: {len(result)} items")
    except Exception as e:
        state["error"] = str(e)
        state["execution_log"].append(f"Research failed: {e}")
    
    return state
```
```

### 2. State Management Rules

```
STATE MANAGEMENT RULES:
- Always use TypedDict for state schemas
- Use Annotated with reducer functions for accumulated fields
- Never mutate state in place (return new state)
- Include metadata fields: timestamp, execution_log, errors
- Keep state flat when possible (avoid deep nesting)
- Always provide default values in state schema
- Document what each state field represents

Example state schema:
```python
from typing import TypedDict, List, Dict, Any, Annotated, Literal
from operator import add
from datetime import datetime

class AgentState(TypedDict):
    # Required fields
    query: str
    user_id: str
    session_id: str
    
    # Accumulated fields (merge across agents)
    retrieval_results: Annotated[Dict[str, Any], add]
    execution_log: Annotated[List[str], add]
    
    # Simple fields (last write wins)
    current_step: str
    confidence: float
    
    # Optional fields
    error: str | None
    retry_count: int
    
    # Metadata
    created_at: datetime
    updated_at: datetime
```
```

### 3. Error Handling and Resilience

```
ERROR HANDLING RULES:
- Wrap all tool calls in try-except blocks
- Implement exponential backoff for retries
- Log errors with full context (state, input, stack trace)
- Provide graceful degradation (partial results better than nothing)
- Never let exceptions crash the entire graph
- Use error states to trigger retry or fallback logic
- Always inform user when partial results returned

Example error handling:
```python
async def resilient_tool_call(
    tool: Callable,
    args: Dict[str, Any],
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Execute tool with retry logic and error recovery.
    """
    for attempt in range(max_retries):
        try:
            result = await tool(**args)
            return {"success": True, "data": result, "error": None}
        except RateLimitError as e:
            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
            if attempt == max_retries - 1:
                return {"success": False, "data": None, "error": str(e)}
        except Exception as e:
            logger.error(f"Tool call failed: {e}", exc_info=True)
            return {"success": False, "data": None, "error": str(e)}
```
```

### 4. LangGraph Specific Rules

```
LANGGRAPH RULES:
- Always use StateGraph, not MessageGraph
- Compile graph with checkpointer for production
- Use conditional edges for dynamic routing
- Test graphs with simple inputs before complex ones
- Visualize graphs using mermaid diagrams in docs
- Name nodes with clear, descriptive names
- Use START and END constants, never strings
- Always provide RunnableConfig for thread management

Example graph construction:
```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

def build_finance_agent_graph() -> StateGraph:
    """
    Constructs the multi-agent finance research graph.
    
    Flow:
        START → lead_agent → [rag_agent, web_agent] → synthesis → END
    """
    graph = StateGraph(FinanceAgentState)
    
    # Add nodes
    graph.add_node("lead_agent", lead_agent_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("web_agent", web_search_node)
    graph.add_node("synthesis", synthesis_node)
    
    # Define workflow
    graph.add_edge(START, "lead_agent")
    
    # Conditional routing based on lead agent's decision
    graph.add_conditional_edges(
        "lead_agent",
        route_to_workers,  # Function that returns node names
        ["rag_agent", "web_agent", "synthesis"]
    )
    
    # Workers converge to synthesis
    graph.add_edge("rag_agent", "synthesis")
    graph.add_edge("web_agent", "synthesis")
    graph.add_edge("synthesis", END)
    
    # Compile with PostgreSQL checkpointing
    checkpointer = PostgresSaver.from_conn_string(
        os.getenv("DATABASE_URL")
    )
    
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=[]  # Add nodes for human-in-the-loop
    )
```
```

### 5. Prompt Engineering Rules

```
PROMPT ENGINEERING RULES:
- Store prompts in separate .txt or .md files in prompts/ directory
- Use Jinja2 templates for dynamic prompt generation
- Include clear instructions, examples, and output format
- Specify what the agent should NOT do (negative examples)
- Use XML tags for structured output parsing
- Test prompts independently before integrating
- Version control prompts alongside code
- Document what each prompt template variable expects

Prompt file structure:
```
prompts/
├── lead_agent_prompt.txt
├── rag_agent_prompt.txt
├── web_search_prompt.txt
├── analysis_prompt.txt
└── citation_prompt.txt
```

Example prompt template (prompts/lead_agent_prompt.txt):
```
You are the Lead Financial Research Agent coordinating a team of specialists.

USER QUERY: {{ query }}

AVAILABLE COMPANIES: {{ companies | join(", ") }}
DATE RANGE: {{ date_range.start }} to {{ date_range.end }}

YOUR RESPONSIBILITIES:
1. Analyze query complexity
2. Create research plan
3. Delegate to specialist agents
4. Synthesize final response

QUERY COMPLEXITY GUIDE:
- Simple: Single company, single metric → Use 1 RAG agent
- Medium: Comparison, 2-3 companies → Use 2-3 RAG agents in parallel
- Complex: Analysis with context → Use all agents (RAG + web + analysis)

CURRENT QUERY ANALYSIS:
- Companies mentioned: {{ companies }}
- Metrics requested: {{ metrics }}
- Time sensitivity: {{ "high" if requires_recent_data else "low" }}

RESEARCH PLAN (output as JSON):
{
  "complexity": "simple|medium|complex",
  "agents_needed": ["rag_apple", "web_search", "analysis"],
  "parallel_execution": true|false,
  "estimated_tokens": 5000,
  "reasoning": "Why this plan is appropriate"
}

Create your research plan now.
```
```

### 6. Tool Development Rules

```
TOOL DEVELOPMENT RULES:
- Use @tool decorator from langchain.tools
- Provide comprehensive docstrings (used by LLM to decide tool usage)
- Include type hints for all parameters
- Return structured data (Dict), not strings
- Handle errors internally (don't let exceptions escape)
- Add usage examples in docstring
- Specify when to use vs when NOT to use
- Test tools independently before agent integration

Example tool:
```python
from langchain.tools import tool
from typing import List, Dict, Any

@tool
def search_sec_filings(
    ticker: str,
    filing_types: List[str],
    query: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Search SEC filings for a specific company using semantic search.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
        filing_types: Types of filings (e.g., ["10-K", "10-Q", "8-K"])
        query: Natural language question about the company
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        limit: Maximum number of chunks to return (1-20)
    
    Returns:
        {
            "success": bool,
            "results": [
                {
                    "text": str,
                    "metadata": {
                        "filing_type": str,
                        "filing_date": str,
                        "section": str,
                        "page": int
                    },
                    "relevance_score": float,
                    "source_url": str
                }
            ],
            "total_found": int,
            "error": str | None
        }
    
    Use this tool when:
    - Need financial data from official SEC filings
    - Looking for specific sections (Item 1, Item 7, Item 8, etc.)
    - Need historical financial statements
    
    Do NOT use when:
    - Need real-time stock prices (use market_data tool)
    - Need recent news (use web_search tool)
    - Query is about general company info not in filings
    
    Examples:
        # Find Apple's revenue from latest 10-K
        search_sec_filings(
            ticker="AAPL",
            filing_types=["10-K"],
            query="total net sales revenue"
        )
        
        # Find risk factors from recent 10-Q
        search_sec_filings(
            ticker="MSFT",
            filing_types=["10-Q"],
            query="risk factors",
            start_date="2024-01-01"
        )
    """
    try:
        # Validate inputs
        if not ticker or len(ticker) > 10:
            return {
                "success": False,
                "results": [],
                "total_found": 0,
                "error": "Invalid ticker symbol"
            }
        
        # Your existing Qdrant search logic here
        results = query_qdrant_with_filters(...)
        
        return {
            "success": True,
            "results": results,
            "total_found": len(results),
            "error": None
        }
        
    except Exception as e:
        logger.error(f"SEC search failed: {e}", exc_info=True)
        return {
            "success": False,
            "results": [],
            "total_found": 0,
            "error": str(e)
        }
```
```

### 7. Testing Rules

```
TESTING RULES:
- Write tests for each agent independently
- Mock LLM calls in unit tests (use FakeLLM)
- Test both success and failure paths
- Test state transitions explicitly
- Use pytest fixtures for common state setups
- Test with real LLM in integration tests
- Measure token usage in tests
- Test graph execution end-to-end

Example test structure:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from langchain.llms.fake import FakeListLLM

from app.agents.rag_agent import rag_agent
from app.schemas.state import FinanceAgentState

@pytest.fixture
def mock_state():
    """Fixture providing test state."""
    return FinanceAgentState(
        query="What was Apple's revenue in Q4 2024?",
        user_id="test_user",
        session_id="test_session",
        companies_mentioned=["AAPL"],
        retrieval_results={},
        execution_log=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def fake_llm():
    """Fixture providing fake LLM with predetermined responses."""
    responses = [
        "Based on the SEC filings, Apple's Q4 2024 revenue was $119.6B",
    ]
    return FakeListLLM(responses=responses)

@pytest.mark.asyncio
async def test_rag_agent_success(mock_state, fake_llm):
    """Test RAG agent successfully retrieves and processes data."""
    # Arrange
    mock_qdrant = Mock()
    mock_qdrant.search = AsyncMock(return_value=[
        {"text": "Revenue: $119.6B", "score": 0.95}
    ])
    
    # Act
    result_state = await rag_agent(mock_state, fake_llm, mock_qdrant)
    
    # Assert
    assert result_state["retrieval_results"]["AAPL"] is not None
    assert len(result_state["execution_log"]) > 0
    assert "error" not in result_state or result_state["error"] is None

@pytest.mark.asyncio
async def test_rag_agent_handles_qdrant_failure(mock_state):
    """Test RAG agent gracefully handles Qdrant failures."""
    # Arrange
    mock_qdrant = Mock()
    mock_qdrant.search = AsyncMock(side_effect=Exception("Qdrant unavailable"))
    
    # Act
    result_state = await rag_agent(mock_state, Mock(), mock_qdrant)
    
    # Assert
    assert result_state["error"] is not None
    assert "Qdrant unavailable" in result_state["error"]
    assert "RAG agent failed" in result_state["execution_log"][-1]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_graph_execution(real_llm):
    """Integration test with real LLM and database."""
    graph = build_finance_agent_graph()
    
    result = await graph.ainvoke({
        "query": "Compare Apple and Microsoft Q4 2024 revenues",
        "user_id": "integration_test",
        "session_id": "test_session_123"
    })
    
    assert result["final_answer"] is not None
    assert len(result["citations"]) > 0
    assert "Apple" in result["final_answer"]
    assert "Microsoft" in result["final_answer"]
```
```

### 8. Logging and Observability Rules

```
LOGGING RULES:
- Use structured logging (JSON format)
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include context: user_id, session_id, agent_name, step
- Log token usage for cost tracking
- Log latency for each agent and tool call
- Never log sensitive user data (PII)
- Use correlation IDs to trace requests across agents
- Log to stdout for containerized environments

Example logging setup:
```python
import logging
import structlog
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in agent
async def rag_agent(state: FinanceAgentState) -> FinanceAgentState:
    log = logger.bind(
        agent="rag_agent",
        user_id=state["user_id"],
        session_id=state["session_id"],
        ticker=state.get("companies_mentioned", ["unknown"])[0]
    )
    
    start_time = datetime.now()
    
    log.info("rag_agent_started", query=state["query"])
    
    try:
        result = await execute_rag_search(state)
        
        latency = (datetime.now() - start_time).total_seconds()
        log.info(
            "rag_agent_completed",
            latency_seconds=latency,
            results_count=len(result),
            tokens_used=result.get("token_count", 0)
        )
        
        state["retrieval_results"] = result
        return state
        
    except Exception as e:
        log.error(
            "rag_agent_failed",
            error=str(e),
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        state["error"] = str(e)
        return state
```
```

### DECISION LOGGING RULES:
- Log every agent decision with options considered
- Capture reasoning for each choice
- Track confidence scores
- Build decision tree structure for UI visualization
- Stream thinking process in real-time

### 9. Performance Optimization Rules

```
PERFORMANCE RULES:
- Use async/await for all I/O operations
- Implement parallel execution where possible (multiple agents)
- Cache expensive operations (embeddings, LLM calls for identical inputs)
- Use connection pooling for databases
- Implement request batching for vector DB queries
- Monitor and optimize token usage
- Use smaller models for simple tasks (Llama 3.1 8B vs 70B)
- Implement timeouts for all external calls

Example parallel execution:
```python
import asyncio

async def execute_parallel_rag(
    state: FinanceAgentState
) -> FinanceAgentState:
    """
    Execute RAG queries for multiple companies in parallel.
    """
    companies = state["companies_mentioned"]
    
    # Create tasks for parallel execution
    tasks = [
        search_company_data(company, state["query"])
        for company in companies
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results and exceptions
    for company, result in zip(companies, results):
        if isinstance(result, Exception):
            logger.error(f"RAG failed for {company}: {result}")
            state["retrieval_results"][company] = {
                "error": str(result),
                "success": False
            }
        else:
            state["retrieval_results"][company] = result
    
    return state

# Caching expensive operations
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding_cached(text: str) -> List[float]:
    """Cache embeddings to avoid recomputation."""
    return generate_embedding(text)
```
```

### 10. Code Organization Rules

```
CODE ORGANIZATION RULES:
- Follow this directory structure:
  
  finance_agent/
  ├── agents/
  │   ├── __init__.py
  │   ├── lead_agent.py
  │   ├── rag_agent.py
  │   ├── web_search_agent.py
  │   ├── analysis_agent.py
  │   └── citation_agent.py
  ├── graphs/
  │   ├── __init__.py
  │   ├── finance_graph.py
  │   └── graph_builder.py
  ├── tools/
  │   ├── __init__.py
  │   ├── sec_search.py
  │   ├── web_search.py
  │   ├── calculator.py
  │   └── code_executor.py
  ├── prompts/
  │   ├── lead_agent_prompt.txt
  │   ├── rag_agent_prompt.txt
  │   └── ...
  ├── schemas/
  │   ├── __init__.py
  │   ├── state.py
  │   └── models.py
  ├── services/
  │   ├── __init__.py
  │   ├── qdrant_service.py
  │   ├── ollama_service.py
  │   └── cache_service.py
  ├── utils/
  │   ├── __init__.py
  │   ├── logging.py
  │   ├── metrics.py
  │   └── validators.py
  └── tests/
      ├── unit/
      ├── integration/
      └── fixtures/

- One agent per file
- One tool per file
- Keep prompts separate from code
- Use dependency injection for services
- Follow PEP 8 style guide
- Use type hints everywhere
- Maximum function length: 50 lines
```

---

## Configuration Management

```
CONFIGURATION RULES:
- Use environment variables for all secrets
- Use .env files for local development (never commit)
- Use pydantic BaseSettings for config validation
- Separate config for dev/staging/prod
- Never hardcode URLs, API keys, or model names

Example config:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 5
    
    # Vector DB
    qdrant_url: str
    qdrant_api_key: str | None = None
    collection_name: str = "sec_filings"
    
    # LLM
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.1:8b"
    lead_agent_model: str = "llama3.1:70b"
    
    # API Keys (optional, for non-local models)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    
    # Agent Settings
    max_agent_iterations: int = 10
    agent_timeout_seconds: int = 300
    enable_parallel_execution: bool = True
    
    # Performance
    redis_url: str
    cache_ttl_seconds: int = 3600
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Usage
settings = Settings()
```
```

---
## EVALUATION RULES:
- Start with 20 test queries representing real usage
- Use LLM-as-judge for grading (factual accuracy, citations, completeness)
- Human testing for edge cases and emergent behaviors
- Track: success rate, tool efficiency, source quality, latency
- Test both outcomes AND process (did agent follow reasonable path?)
---

---

## Documentation Rules

```
DOCUMENTATION RULES:
- Every agent needs a docstring explaining its purpose
- Every tool needs usage examples in docstring
- Document state transitions in graph builder
- Keep a CHANGELOG.md for agent behavior changes
- Document prompt template variables
- Add inline comments for complex logic only
- Use type hints as self-documenting code
- Maintain architecture diagrams in docs/

Example documentation:
```python
def route_to_workers(state: FinanceAgentState) -> List[str]:
    """
    Routes lead agent's plan to appropriate worker agents.
    
    Routing Logic:
    - Simple queries (1 company, 1 metric): ["rag_agent"]
    - Medium queries (2-3 companies, comparison): ["rag_agent", "web_agent"]
    - Complex queries (analysis, trends): ["rag_agent", "web_agent", "analysis_agent"]
    
    State Requirements:
        - state["query_type"]: Literal["simple", "medium", "complex"]
        - state["companies_mentioned"]: List[str]
        - state["requires_web_search"]: bool
    
    Returns:
        List of agent node names to execute
    
    Examples:
        >>> state = {"query_type": "simple", "companies_mentioned": ["AAPL"]}
        >>> route_to_workers(state)
        ["rag_agent"]
        
        >>> state = {"query_type": "complex", "requires_web_search": True}
        >>> route_to_workers(state)
        ["rag_agent", "web_agent", "analysis_agent"]
    """
    complexity = state["query_type"]
    
    if complexity == "simple":
        return ["rag_agent"]
    elif complexity == "medium":
        nodes = ["rag_agent"]
        if state.get("requires_web_search"):
            nodes.append("web_agent")
        return nodes
    else:  # complex
        return ["rag_agent", "web_agent", "analysis_agent"]
```
```

---

## Security Rules

```
SECURITY RULES:
- Never log API keys or tokens
- Validate all user inputs (SQL injection, XSS prevention)
- Use parameterized queries for database
- Sanitize file paths in file operations
- Implement rate limiting on API endpoints
- Use HTTPS for all external calls
- Implement authentication for multi-agent API
- Sandbox code execution (if using code execution tool)
- Rotate API keys regularly
- Use secrets management service (Vault, AWS Secrets Manager)

Example input validation:
```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    tickers: List[str] = Field(default_factory=list, max_items=10)
    
    @validator('tickers')
    def validate_tickers(cls, v):
        """Validate ticker symbols."""
        for ticker in v:
            if not ticker.isalnum() or len(ticker) > 10:
                raise ValueError(f"Invalid ticker: {ticker}")
        return [t.upper() for t in v]
    
    @validator('query')
    def sanitize_query(cls, v):
        """Remove potentially harmful characters."""
        # Remove SQL injection attempts
        dangerous = ["';", "--", "/*", "*/", "xp_", "sp_"]
        for pattern in dangerous:
            if pattern in v.lower():
                raise ValueError("Query contains disallowed patterns")
        return v
```
```

---

## Deployment and Operations Rules

```
DEPLOYMENT RULES:
- Use Docker for all services
- Pin all dependency versions in requirements.txt
- Use multi-stage Docker builds for smaller images
- Implement health check endpoints
- Use environment-based configuration
- Implement graceful shutdown
- Use process managers (gunicorn, uvicorn workers)
- Implement circuit breakers for external services

Example Docker setup:
```dockerfile
# Multi-stage build for Finance Agent
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Example health check endpoint:
```python
from fastapi import FastAPI
from app.services.qdrant_service import check_qdrant_health
from app.services.ollama_service import check_ollama_health

@app.get("/health")
async def health_check():
    """
    Comprehensive health check for all services.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check Qdrant
    try:
        await check_qdrant_health()
        health_status["services"]["qdrant"] = "healthy"
    except Exception as e:
        health_status["services"]["qdrant"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ollama
    try:
        await check_ollama_health()
        health_status["services"]["ollama"] = "healthy"
    except Exception as e:
        health_status["services"]["ollama"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Database
    try:
        await check_database_health()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```
```

---

## Quick Reference: Common Patterns

### Pattern 1: Adding a New Agent
```python
# 1. Define agent function in agents/new_agent.py
async def new_agent(state: FinanceAgentState) -> FinanceAgentState:
    """Agent that does X."""
    # Load prompt
    # Execute logic
    # Update state
    return state

# 2. Add to graph in graphs/finance_graph.py
graph.add_node("new_agent", new_agent)
graph.add_edge("previous_node", "new_agent")

# 3. Create prompt in prompts/new_agent_prompt.txt

# 4. Write tests in tests/unit/test_new_agent.py
```

### Pattern 2: Adding a New Tool
```python
# 1. Create tool in tools/new_tool.py
@tool
def new_tool(param: str) -> Dict[str, Any]:
    """Tool that does Y."""
    # Implementation
    return {"success": True, "data": result}

# 2. Register tool in tools/__init__.py
from .new_tool import new_tool

__all__ = ["new_tool", ...]

# 3. Add to agent's available tools
agent_tools = [existing_tool, new_tool]

# 4. Test tool independently
```

### Pattern 3: Modifying State Schema
```python
# 1. Update state in schemas/state.py
class FinanceAgentState(TypedDict):
    # ... existing fields
    new_field: NewType  # Add new field

# 2. Update all agents that use state
# 3. Update tests
# 4. Document the new field
# 5. Handle migration for existing checkpoints
```

---

## Common Pitfalls to Avoid

1. **Don't** hardcode prompts in Python code → Use template files
2. **Don't** use synchronous calls in async functions → Use async/await
3. **Don't** mutate state objects → Return new state
4. **Don't** catch exceptions without logging → Always log errors
5. **Don't** skip type hints → They prevent bugs
6. **Don't** create circular dependencies between agents → Use state for communication
7. **Don't** forget to test with real LLMs → Unit tests with mocks aren't enough
8. **Don't** skip error handling in tools → Tools should never crash agents
9. **Don't** log sensitive data → PII, API keys, user queries (be careful)
10. **Don't** ignore performance metrics → Monitor token usage and latency

---

## Development Workflow

1. **Design**: Document agent responsibility and interface
2. **Prompt**: Write and test prompt template independently
3. **Implement**: Code agent function with error handling
4. **Test Unit**: Test with mocked LLM and dependencies
5. **Test Integration**: Test with real LLM and services
6. **Add to Graph**: Integrate into graph with proper edges
7. **Test E2E**: Test full graph execution
8. **Document**: Update docs and add examples
9. **Deploy**: Build Docker image and deploy
10. **Monitor**: Watch logs and metrics

---

## Resources and Learning

- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- Anthropic Multi-Agent Guide: https://www.anthropic.com/engineering/multi-agent-research-system
- FastAPI Best Practices: https://fastapi.tiangolo.com/
- Python Async Programming: https://docs.python.org/3/library/asyncio.html
- Structured Logging: https://www.structlog.org/

---

## Final Checklist Before Committing Code

- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Tests pass (pytest)
- [ ] Code formatted (black, isort)
- [ ] No sensitive data in code
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Documentation updated
- [ ] Prompts in separate files
- [ ] Performance considered (async where needed)
