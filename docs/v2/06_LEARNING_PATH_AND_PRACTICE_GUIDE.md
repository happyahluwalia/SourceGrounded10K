# Finance Agent v2.0: Learning Path & Practice Guide

## Overview

This guide provides a structured 8-week learning path to build Finance Agent v2.0 while mastering multi-agent systems for interview preparation. Each week includes:
- **Learning objectives** with clear outcomes
- **Hands-on coding challenges** with starter code
- **Evaluation criteria** using Anthropic's patterns
- **Decision logging exercises** from Day 1
- **Interview prep questions** aligned with OpenAI/Anthropic
- **Self-assessment rubrics** to track progress

---

## Week 1: Foundation & Single Agent (Days 1-7)

### Learning Objectives
- Understand LangGraph StateGraph fundamentals
- Master state management and checkpointing
- Build decision logging infrastructure
- Wrap existing RAG as LangGraph node

### Day 1-2: Setup & LangGraph Basics

**Study Materials:**
1. Complete [LangGraph Quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/) (2 hours)
2. Read state management patterns in Architecture doc (1 hour)
3. Watch LangGraph Academy Module 1 (1 hour)

**Coding Challenge 1: Hello World Graph**
```python
# Challenge: Build simplest possible graph
# File: app/graphs/hello_graph.py

from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class HelloState(TypedDict):
    message: str
    count: int

def hello_node(state: HelloState) -> HelloState:
    # TODO: Implement
    # 1. Increment count
    # 2. Append "Hello" to message
    # 3. Return updated state
    pass

# TODO: Build graph
# 1. Create StateGraph(HelloState)
# 2. Add hello_node
# 3. Add edges START -> hello_node -> END
# 4. Compile and test
```

**Evaluation Criteria:**
- [ ] Graph compiles without errors
- [ ] State updates correctly
- [ ] Can invoke graph and get result
- [ ] Code has type hints

**Decision Log Entry Template:**
```markdown
## Decision: [Title]
**Date:** YYYY-MM-DD
**Context:** What problem are you solving?
**Options Considered:**
1. Option A - Pros/Cons
2. Option B - Pros/Cons
**Decision:** Chose Option X
**Reasoning:** Why this option?
**Trade-offs:** What did you sacrifice?
**Learning:** What did you learn?
```

**Interview Prep Question:**
> "Explain the difference between StateGraph and MessageGraph in LangGraph. When would you use each?"

**Self-Assessment Rubric (1-5):**
- [ ] Can explain what a StateGraph is (1=no idea, 5=teach others)
- [ ] Can build a simple graph from scratch (1=need help, 5=easy)
- [ ] Understand state immutability (1=confused, 5=clear)

---

### Day 3-4: Observability with LangSmith

**Goal:** Set up production-grade observability without building custom infrastructure.

**Key Insight:** LangGraph + LangSmith provide built-in tracing, state history, and debugging. Don't reinvent the wheel!

---

**Coding Challenge 2: Enable LangSmith Tracing**

**Step 1: Setup (5 minutes)**
```bash
# Install LangSmith
pip install langsmith

# Get free API key from https://smith.langchain.com
# Add to .env
echo "LANGCHAIN_TRACING_V2=true" >> .env
echo "LANGCHAIN_API_KEY=your_key_here" >> .env
```

**Step 2: Enable in Your App (2 minutes)**
```python
# File: app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...
    
    # LangSmith Observability
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "finance-agent-v2"  # Optional: organize traces
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 3: Test Tracing (15 minutes)**
```python
# File: tests/test_tracing.py

import os
from typing import Literal
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END

# Ensure tracing is enabled
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Define a simple tool
@tool
def get_company_info(ticker: str) -> str:
    """Get basic company information."""
    return f"Company {ticker} is a technology company."

# Setup LLM with tools
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
tools = [get_company_info]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# Define agent nodes
def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not."""
    return {
        "messages": [
            llm_with_tools.invoke(
                [SystemMessage(content="You are a helpful financial assistant.")]
                + state["messages"]
            )
        ]
    }

def tool_node(state: MessagesState):
    """Execute tool calls."""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
        )
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Route to tool node or end based on LLM decision."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END

# Build the agent graph
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# Run test query - will automatically trace to LangSmith!
messages = [HumanMessage(content="Tell me about Apple (AAPL)")]
result = agent.invoke({"messages": messages})

print("Check LangSmith UI for trace: https://smith.langchain.com")
print(f"\nResult: {result['messages'][-1].content}")
```

**Step 4: Add Simple Logging (30 minutes)**
```python
# File: app/utils/agent_logger.py

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def log_agent_decision(
    agent_name: str,
    decision_point: str,
    chosen_option: str,
    reasoning: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log agent decisions for debugging and analysis.
    
    This complements LangSmith tracing with custom decision points.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "decision_point": decision_point,
        "chosen_option": chosen_option,
        "reasoning": reasoning,
        "metadata": metadata or {}
    }
    
    logger.info(
        f"DECISION | {agent_name} | {decision_point} | {chosen_option}",
        extra=log_entry
    )
    
    return log_entry


def log_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Any,
    duration_ms: float
) -> None:
    """Log tool execution for monitoring."""
    logger.info(
        f"TOOL | {tool_name} | {duration_ms}ms",
        extra={
            "tool": tool_name,
            "arguments": arguments,
            "duration_ms": duration_ms,
            "success": result is not None
        }
    )
```

**Step 5: Build Your Orchestrator Agent (30 minutes)**
```python
# File: app/agents/orchestrator.py

from typing import Literal
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from app.tools.data_prep_tool import ensure_filing_available
from app.tools.rag_search_tool import search_sec_filings
from app.utils.agent_logger import log_agent_decision
from app.core.config import settings

# Setup LLM with tools
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=settings.ANTHROPIC_API_KEY
)

tools = [ensure_filing_available, search_sec_filings]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# Define orchestrator nodes
def llm_call(state: MessagesState):
    """Orchestrator LLM decides which tools to call."""
    system_prompt = """You are a financial research assistant.
    
    When users ask about company financials:
    1. Extract the company ticker from the query
    2. Use ensure_filing_available() to ensure data is ready
    3. Use search_sec_filings() to find the answer
    4. Provide clear, accurate answers with sources
    
    Be helpful and thorough."""
    
    return {
        "messages": [
            llm_with_tools.invoke(
                [SystemMessage(content=system_prompt)] + state["messages"]
            )
        ]
    }

def tool_node(state: MessagesState):
    """Execute tool calls made by the orchestrator."""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        
        # Log the tool call
        log_agent_decision(
            agent_name="orchestrator",
            decision_point="tool_selection",
            chosen_option=tool_call["name"],
            reasoning="LLM decided to call this tool",
            metadata={"args": tool_call["args"]}
        )
        
        # Execute tool
        observation = tool.invoke(tool_call["args"])
        result.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
        )
    
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Route to tool execution or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END

# Build the orchestrator graph
orchestrator_builder = StateGraph(MessagesState)
orchestrator_builder.add_node("llm_call", llm_call)
orchestrator_builder.add_node("tool_node", tool_node)
orchestrator_builder.add_edge(START, "llm_call")
orchestrator_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
orchestrator_builder.add_edge("tool_node", "llm_call")

# Compile the orchestrator (automatically traces to LangSmith!)
orchestrator = orchestrator_builder.compile()

# Usage example
async def answer_query(query: str) -> dict:
    """Answer a natural language financial query."""
    messages = [HumanMessage(content=query)]
    result = await orchestrator.ainvoke({"messages": messages})
    
    return {
        "query": query,
        "answer": result["messages"][-1].content,
        "messages": result["messages"]
    }
```

---

**What You Get Out-of-the-Box:**

✅ **LangSmith Tracing:**
- Full execution tree visualization
- Token usage per step
- Latency per node
- Input/output for each step
- Error tracking
- Cost monitoring

✅ **LangGraph State History:**
- Every state snapshot
- Time-travel debugging
- Execution order
- Which node ran when

✅ **Message History:**
- Agent reasoning (AI messages)
- Tool calls with arguments
- Tool results
- Full conversation flow

---

**Evaluation Criteria:**
- [ ] LangSmith tracing enabled and working
- [ ] Can view traces in LangSmith UI
- [ ] Custom logging added for key decisions
- [ ] Logs are structured and searchable
- [ ] Can debug agent execution using traces

**Decision Log Entry:**
```markdown
## Decision: Observability Strategy
**Options Considered:**
1. Build custom decision tree infrastructure - Full control but time-consuming
2. Use LangSmith + simple logging - Fast, production-ready, less control
3. Use only Python logging - Simple but limited visibility
**Decision:** LangSmith + simple logging
**Reasoning:** 
- LangSmith provides 90% of what we need out-of-the-box
- Free tier is generous for learning/MVP
- Production-grade without building infrastructure
- Can add custom decision tree later if needed (Week 5-6)
**Trade-offs:** 
- Slight vendor lock-in (but can export traces)
- Less customization than building our own
- Worth it for speed and reliability
```

**Interview Prep:**
> "How do you implement observability for multi-agent systems?"

**Expected Answer:**
- Use LangSmith for automatic tracing of agent execution
- LangGraph checkpointing for state persistence and time-travel debugging
- Structured logging for custom decision points
- Monitor: token usage, latency, tool calls, error rates
- Can export traces for custom analysis if needed
- Don't build custom infrastructure when production tools exist

---

**📚 Learning Exercise for Later (Week 5-6):**

Once you're comfortable with LangSmith, you can build a custom decision tree visualization as an advanced exercise. This helps you understand what's happening under the hood and gives you a great interview talking point. See "Week 5: Advanced Observability" for the custom decision tree implementation.

---

### Day 5-7: Wrap Existing RAG as LangGraph Node

**Coding Challenge 3: RAG Agent Node**
```python
# File: app/agents/rag_agent.py

from typing import TypedDict, List, Dict, Any, Annotated
from operator import add
import structlog
from datetime import datetime

from app.services.rag_chain import RAGChain  # Your existing RAG
from app.schemas.decision_tree import DecisionTreeBuilder, ReasoningStep

logger = structlog.get_logger()

class FinanceAgentState(TypedDict):
    # Input
    query: str
    user_id: str
    session_id: str
    ticker: str
    
    # Results
    retrieval_results: Dict[str, Any]
    
    # Observability
    execution_log: Annotated[List[str], add]
    reasoning_steps: Annotated[List[ReasoningStep], add]
    decision_tree: DecisionTreeBuilder
    
    # Metadata
    start_time: datetime
    token_count: int

async def rag_agent_node(
    state: FinanceAgentState
) -> FinanceAgentState:
    """
    Wraps existing RAG system as LangGraph node with full observability.
    
    TODO:
    1. Log reasoning step: "Starting RAG search for {ticker}"
    2. Call existing RAG system
    3. Log decision: "Retrieved X chunks with avg score Y"
    4. Update state with results
    5. Track token usage
    6. Return updated state
    """
    log = logger.bind(
        agent="rag_agent",
        session_id=state["session_id"],
        ticker=state["ticker"]
    )
    
    # TODO: Add reasoning step
    reasoning_step = ReasoningStep(
        step_id=str(uuid4()),
        agent_name="rag_agent",
        timestamp=datetime.now(),
        thought="",  # TODO: Fill in
        action="",   # TODO: Fill in
        observation="",  # TODO: Fill in
        next_thought=""  # TODO: Fill in
    )
    
    try:
        # TODO: Call your existing RAG
        rag = RAGChain()
        result = await rag.query(
            query=state["query"],
            ticker=state["ticker"]
        )
        
        # TODO: Log decision
        decision_id = state["decision_tree"].add_decision(
            agent_name="rag_agent",
            decision_point="",  # TODO: Fill in
            options_considered=[],  # TODO: Fill in
            chosen_option="",  # TODO: Fill in
            reasoning="",  # TODO: Fill in
            confidence=0.0  # TODO: Calculate
        )
        
        # Update state
        state["retrieval_results"] = result
        state["reasoning_steps"].append(reasoning_step)
        state["execution_log"].append(f"RAG completed: {len(result['chunks'])} chunks")
        
        log.info("rag_agent_success", chunks=len(result['chunks']))
        
    except Exception as e:
        log.error("rag_agent_failed", error=str(e))
        state["execution_log"].append(f"RAG failed: {e}")
    
    return state
```

**Evaluation Criteria (Anthropic Pattern):**

**Outcome Evaluation:**
- [ ] Returns valid results for known queries
- [ ] Handles errors gracefully (no crashes)
- [ ] State updates correctly

**Process Evaluation:**
- [ ] Logs all decisions with reasoning
- [ ] Captures thinking process
- [ ] Reasonable tool usage (not excessive)

**LLM-as-Judge Rubric:**
```python
# File: tests/evals/rag_agent_eval.py

EVAL_PROMPT = """
Evaluate the RAG agent's performance:

Query: {query}
Agent Output: {output}
Expected Behavior: Retrieve relevant SEC filing chunks

Score each criterion 0.0-1.0:

1. **Factual Accuracy**: Do results match query intent?
2. **Source Quality**: Are chunks from correct filings?
3. **Completeness**: Are all relevant aspects covered?
4. **Efficiency**: Reasonable number of chunks retrieved?
5. **Error Handling**: Graceful degradation if issues?

Output JSON:
{{
  "factual_accuracy": 0.0-1.0,
  "source_quality": 0.0-1.0,
  "completeness": 0.0-1.0,
  "efficiency": 0.0-1.0,
  "error_handling": 0.0-1.0,
  "overall_pass": true/false,
  "reasoning": "Brief explanation"
}}
"""
```

**Decision Log Entry:**
```markdown
## Decision: State Schema Design
**Options:**
1. Minimal state (query, results only)
2. Rich state (query, results, logs, decisions, reasoning)
**Decision:** Rich state with observability fields
**Reasoning:** Need full visibility for learning and debugging
**Trade-offs:** More complex state management, but essential for interviews
```

**Interview Prep:**
> "Walk me through how you would migrate an existing RAG system to a multi-agent architecture without breaking production."

**Week 1 Self-Assessment:**
- [ ] Built working LangGraph with 1 node (5/5 = production ready)
- [ ] Decision logging infrastructure in place (5/5 = captures everything)
- [ ] Can explain state management to interviewer (5/5 = confident)
- [ ] Wrapped existing RAG with full observability (5/5 = complete)

**Week 1 Deliverable:**
- Working graph: `START -> rag_agent -> END`
- Decision tree captures all agent decisions
- Reasoning steps logged
- 3+ decision log entries
- Can demo to interviewer

---

## Week 2: Observability & Streaming (Days 8-14)

### Learning Objectives
- Implement real-time thinking stream to UI
- Add PostgreSQL checkpointing
- Build evaluation framework with LLM-as-judge
- Master async streaming patterns

### Day 8-10: Streaming Thinking Process

**Coding Challenge 4: SSE Streaming Endpoint**
```python
# File: app/api/v2/streaming.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json

router = APIRouter()

@router.get("/stream/{session_id}")
async def stream_agent_thinking(session_id: str) -> StreamingResponse:
    """
    Stream agent's thinking process via Server-Sent Events.
    
    TODO:
    1. Connect to graph execution
    2. Stream reasoning steps as they happen
    3. Stream decision nodes
    4. Handle client disconnection
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        # TODO: Implement
        # Yield events in SSE format:
        # data: {"type": "thought", "content": "...", "agent": "rag_agent"}
        pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Frontend Challenge:**
```jsx
// File: frontend/src/components/ThinkingPanel.jsx

export function ThinkingPanel({ sessionId }) {
  const [thoughts, setThoughts] = useState([]);
  
  useEffect(() => {
    // TODO: Connect to SSE endpoint
    // TODO: Update thoughts state as events arrive
    // TODO: Auto-scroll to latest
    // TODO: Cleanup on unmount
  }, [sessionId]);
  
  return (
    <div className="thinking-panel">
      {thoughts.map(t => (
        <ThoughtBubble 
          key={t.id}
          agent={t.agent}
          content={t.content}
          timestamp={t.timestamp}
        />
      ))}
    </div>
  );
}
```

**Evaluation:**
- [ ] Thoughts stream in real-time (< 100ms latency)
- [ ] UI updates smoothly without flicker
- [ ] Handles disconnection gracefully
- [ ] Shows which agent is thinking

**Decision Log:**
```markdown
## Decision: SSE vs WebSocket for Streaming
**Options:**
1. WebSocket - Bidirectional, more complex
2. SSE - Unidirectional, simpler, auto-reconnect
**Decision:** SSE
**Reasoning:** Only need server→client, SSE has built-in reconnection
**Trade-offs:** Can't send client→server, but don't need that
```

**Interview Prep:**
> \"How would you implement real-time streaming of agent thoughts to a web UI? What are the trade-offs between WebSocket and SSE?\"

---

### Day 11-12: Checkpointing & Time Travel

**Coding Challenge 5: PostgreSQL Checkpointer**
```python
# File: app/graphs/checkpointed_graph.py

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph

async def build_checkpointed_graph():
    \"\"\"
    Build graph with PostgreSQL checkpointing for state persistence.
    
    TODO:
    1. Create PostgresSaver from DATABASE_URL
    2. Compile graph with checkpointer
    3. Test state persistence across runs
    4. Implement time-travel debugging
    \"\"\"
    
    checkpointer = PostgresSaver.from_conn_string(
        # TODO: Get from settings
    )
    
    graph = StateGraph(FinanceAgentState)
    # TODO: Add nodes
    
    app = graph.compile(checkpointer=checkpointer)
    
    return app

# Time-travel debugging
async def replay_execution(session_id: str):
    \"\"\"
    Replay agent execution step-by-step for debugging.
    
    TODO:
    1. Get all checkpoints for session
    2. Display state at each step
    3. Allow jumping to any point
    \"\"\"
    config = {\"configurable\": {\"thread_id\": session_id}}
    
    for checkpoint in app.get_state_history(config):
        print(f\"Step: {checkpoint.values['current_step']}\")
        print(f\"State: {checkpoint.values}\")
```

---

#### **Production Checkpointing Best Practices**

**Critical for interviews and production deployment!**

##### 1. Use Persistent Storage
```python
# ❌ Never in production
from langgraph.checkpoint.memory import InMemorySaver

# ✅ Production-ready
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
```

##### 2. Thread Management
```python
# Unique, namespaced thread IDs
thread_id = f"{user_id}_{session_id}_{timestamp}"

# Include metadata for queries/cleanup
config = {
    "configurable": {
        "thread_id": thread_id,
        "user_id": user_id,  # For queries/cleanup
    }
}
```

##### 3. Control State Size
```python
from langchain_core.messages import trim_messages

def chatbot(state: State):
    # Keep last N messages only
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,  # Or message count
        strategy="last"
    )
    return {"messages": llm.invoke(trimmed)}
```

##### 4. Implement Cleanup
```python
# File: app/services/checkpoint_cleanup.py

async def cleanup_old_threads(days=30):
    """
    Delete old checkpoints periodically.
    Run as scheduled job (cron/celery).
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    checkpointer.delete_threads(older_than=cutoff_date)
```

##### 5. Handle Errors Gracefully
```python
try:
    state = graph.get_state(config)
    if state is None:
        # Thread doesn't exist - start fresh
        state = initialize_new_state()
except Exception as e:
    logger.error(f"Failed to load checkpoint: {e}")
    state = initialize_new_state()
```

##### 6. Security
```python
import uuid

# ✅ Use UUIDs for unpredictable IDs
thread_id = f"{user_id}_{uuid.uuid4()}"

# ✅ Validate thread ownership before loading
async def validate_thread_access(thread_id: str, user_id: str) -> bool:
    """Ensure user owns this thread."""
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    return state.values.get("user_id") == user_id

# ❌ Don't expose thread IDs in URLs/logs
# Bad: /api/chat?thread=user123_session456
# Good: /api/chat?session=<opaque_token>
```

##### 7. Monitor Size
```python
# File: app/utils/checkpoint_monitoring.py

async def monitor_checkpoint_size(config: dict):
    """Track checkpoint sizes and alert on bloat."""
    state = graph.get_state(config)
    size = len(str(state.values))
    
    if size > 100_000:  # 100KB threshold
        logger.warning(f"Large checkpoint: {size} bytes", 
                      thread_id=config["configurable"]["thread_id"])
        # Trigger summarization or cleanup
        await summarize_old_messages(state)
```

##### 8. Separate Concerns
```python
# Different thread types for different purposes
support_thread = f"support_{ticket_id}"
chat_thread = f"chat_{user_id}_{date}"
workflow_thread = f"workflow_{job_id}"

# Use prefixes for easy querying
def get_user_threads(user_id: str):
    return checkpointer.list_threads(prefix=f"chat_{user_id}_")
```

#### **Production Checklist**
- [ ] PostgreSQL/SQLite checkpointer (not InMemory)
- [ ] Unique thread IDs with user context
- [ ] Message trimming (keep last 20-50 messages)
- [ ] Automated cleanup job (delete >30 days)
- [ ] Thread ownership validation
- [ ] Size monitoring and alerts
- [ ] Backup strategy for checkpoint DB
- [ ] Error handling for missing/corrupt checkpoints

**Key Principle:** Treat checkpoints like any other database - validate, monitor, clean up, and secure. 🎯

---

**Evaluation:**
- [ ] State persists across server restarts
- [ ] Can resume execution from any checkpoint
- [ ] Time-travel debugging works
- [ ] No data loss on crashes
- [ ] Thread IDs are secure (UUIDs)
- [ ] Cleanup job implemented
- [ ] Size monitoring in place

**Decision Log Entry:**
```markdown
## Decision: Checkpoint Storage Strategy
**Options:**
1. InMemorySaver - Fast but loses data on restart
2. SQLite - Simple file-based persistence
3. PostgreSQL - Production-grade, already in stack
**Decision:** PostgreSQL
**Reasoning:** Already using Postgres, need durability, supports concurrent access
**Trade-offs:** Slightly more complex setup, but worth it for production
**Security:** Using UUIDs in thread IDs, validating ownership before loading
```

**Interview Prep:**
> \"Explain how checkpointing works in LangGraph. Why is it important for production systems? What are the security and performance considerations?\"

**Expected Answer Points:**
- State persistence across restarts
- Time-travel debugging capability
- Must use persistent storage (Postgres/SQLite)
- Security: validate thread ownership, use UUIDs
- Performance: trim messages, monitor size, cleanup old threads
- Production concerns: backup strategy, error handling

---

### Day 13-14: LLM-as-Judge Evaluation

**Coding Challenge 6: Evaluation Framework**
```python
# File: tests/evals/eval_framework.py

from typing import List, Dict
import asyncio
from anthropic import Anthropic

class AgentEvaluator:
    \"\"\"
    Evaluates agent performance using LLM-as-judge pattern.
    \"\"\"
    
    def __init__(self, test_cases: List[Dict]):
        self.test_cases = test_cases
        self.client = Anthropic()
    
    async def evaluate_agent(self, agent_output: Dict) -> Dict:
        \"\"\"
        Use Claude to evaluate agent output.
        
        TODO:
        1. Build evaluation prompt
        2. Call Claude with output and rubric
        3. Parse scores from response
        4. Return structured evaluation
        \"\"\"
        
        eval_prompt = f\"\"\"
        Evaluate this agent's performance:
        
        Query: {agent_output['query']}
        Agent Answer: {agent_output['answer']}
        Sources Used: {agent_output['sources']}
        
        Rubric (score 0.0-1.0 each):
        1. Factual Accuracy: Claims match sources?
        2. Citation Accuracy: Citations correct?
        3. Completeness: All aspects covered?
        4. Source Quality: Used authoritative sources?
        5. Tool Efficiency: Reasonable tool usage?
        
        Output JSON with scores and reasoning.
        \"\"\"
        
        # TODO: Call Claude
        # TODO: Parse response
        # TODO: Return scores
        pass
    
    async def run_eval_suite(self) -> Dict:
        \"\"\"
        Run all test cases and aggregate results.
        
        TODO:
        1. Run agent on each test case
        2. Evaluate each output
        3. Calculate aggregate metrics
        4. Identify failure patterns
        \"\"\"
        results = []
        
        for test_case in self.test_cases:
            # TODO: Run agent
            # TODO: Evaluate
            # TODO: Store result
            pass
        
        return {
            \"total_tests\": len(self.test_cases),
            \"passed\": sum(1 for r in results if r['overall_pass']),
            \"avg_scores\": {},  # TODO: Calculate
            \"failures\": []  # TODO: List failed cases
        }

# Test cases
TEST_CASES = [
    {
        \"query\": \"What was Apple's revenue in Q4 2024?\",
        \"expected_answer_contains\": [\"$119.6\", \"billion\", \"Q4 2024\"],
        \"expected_sources\": [\"10-K\", \"10-Q\"],
        \"complexity\": \"simple\"
    },
    {
        \"query\": \"Compare Apple and Microsoft Q4 revenues\",
        \"expected_answer_contains\": [\"Apple\", \"Microsoft\", \"comparison\"],
        \"expected_sources\": [\"10-K\", \"10-Q\"],
        \"complexity\": \"medium\"
    },
    # TODO: Add 18 more test cases
]
```

**Evaluation Criteria:**
- [ ] LLM-as-judge scores align with human judgment (>80% agreement)
- [ ] Eval suite runs in < 5 minutes
- [ ] Identifies failure patterns clearly
- [ ] Tracks metrics over time

**Decision Log:**
```markdown
## Decision: Evaluation Strategy
**Options:**
1. Manual testing only - Doesn't scale
2. Rule-based evals - Brittle, misses nuance
3. LLM-as-judge - Scalable, catches nuance
**Decision:** LLM-as-judge with 20 test cases
**Reasoning:** Anthropic's research shows this works well
**Trade-offs:** Costs money, but worth it for quality
```

**Week 2 Deliverable:**
- Thinking stream visible in UI
- Checkpointing working
- 20 test cases with LLM-as-judge
- Eval suite passing >80%
- 3+ decision log entries

---

## Week 3-4: Multi-Agent Orchestration (Days 15-28)

### Learning Objectives
- Build lead agent (orchestrator)
- Implement parallel worker execution
- Add web search agent
- Master conditional routing

### Day 15-17: Lead Agent

**Coding Challenge 7: Orchestrator Agent**
```python
# File: app/agents/lead_agent.py

async def lead_agent_node(state: FinanceAgentState) -> FinanceAgentState:
    \"\"\"
    Lead agent analyzes query and creates research plan.
    
    TODO:
    1. Analyze query complexity
    2. Identify companies mentioned
    3. Determine which agents to spawn
    4. Create research plan
    5. Log decision with reasoning
    \"\"\"
    
    # Load prompt
    prompt = load_prompt(\"lead_agent\")
    
    # TODO: Call LLM to analyze query
    analysis = await llm.ainvoke(prompt.format(
        query=state[\"query\"],
        available_agents=[\"rag_agent\", \"web_search_agent\", \"analysis_agent\"]
    ))
    
    # TODO: Parse analysis
    # TODO: Create research plan
    # TODO: Log decision
    
    state[\"query_complexity\"] = analysis[\"complexity\"]
    state[\"research_plan\"] = analysis[\"plan\"]
    state[\"agents_to_spawn\"] = analysis[\"agents_needed\"]
    
    return state

def route_to_workers(state: FinanceAgentState) -> List[str]:
    \"\"\"
    Route to appropriate worker agents based on research plan.
    
    TODO:
    1. Read research_plan from state
    2. Return list of agent names to execute
    3. Log routing decision
    \"\"\"
    plan = state[\"research_plan\"]
    
    # TODO: Implement routing logic
    # Simple query -> [\"rag_agent\"]
    # Medium query -> [\"rag_agent\", \"web_search_agent\"]
    # Complex query -> all agents
    
    pass
```

**Evaluation:**
- [ ] Correctly classifies query complexity (>90% accuracy)
- [ ] Spawns appropriate agents (not too many, not too few)
- [ ] Explains reasoning clearly
- [ ] Handles edge cases (ambiguous queries)

**Interview Prep:**
> \"Design an orchestrator agent that can dynamically route queries to specialized workers. How do you prevent it from spawning too many agents?\"

---

### Day 18-21: Parallel Execution

**Coding Challenge 8: Parallel RAG Agents**
```python
# File: app/graphs/parallel_graph.py

def build_parallel_graph():
    \"\"\"
    Build graph with parallel worker execution.
    
    TODO:
    1. Lead agent decides which companies to query
    2. Spawn RAG agent for each company in parallel
    3. Collect results
    4. Synthesize in lead agent
    \"\"\"
    
    graph = StateGraph(FinanceAgentState)
    
    graph.add_node(\"lead\", lead_agent_node)
    
    # Dynamic parallel execution
    graph.add_node(\"rag_apple\", lambda s: rag_agent_node({**s, \"ticker\": \"AAPL\"}))
    graph.add_node(\"rag_msft\", lambda s: rag_agent_node({**s, \"ticker\": \"MSFT\"}))
    
    graph.add_node(\"synthesis\", synthesis_agent_node)
    
    # TODO: Add conditional edges
    # TODO: Parallel execution of RAG agents
    # TODO: Converge to synthesis
    
    return graph.compile(checkpointer=checkpointer)
```

**Performance Test:**
```python
# Measure parallel vs sequential
import time

async def test_parallel_performance():
    # Sequential
    start = time.time()
    result1 = await rag_agent(state, \"AAPL\")
    result2 = await rag_agent(state, \"MSFT\")
    sequential_time = time.time() - start
    
    # Parallel
    start = time.time()
    results = await asyncio.gather(
        rag_agent(state, \"AAPL\"),
        rag_agent(state, \"MSFT\")
    )
    parallel_time = time.time() - start
    
    speedup = sequential_time / parallel_time
    print(f\"Speedup: {speedup}x\")
    
    # TODO: Assert speedup > 1.5x
```

**Evaluation:**
- [ ] Parallel execution faster than sequential (>1.5x speedup)
- [ ] No race conditions in state updates
- [ ] All agents complete successfully
- [ ] Results merged correctly

**Decision Log:**
```markdown
## Decision: Parallel vs Sequential Execution
**Context:** Comparing 2 companies requires 2 RAG queries
**Options:**
1. Sequential - Simple, slower
2. Parallel - Complex, faster
**Decision:** Parallel with asyncio.gather
**Reasoning:** 2x speedup worth the complexity
**Trade-offs:** More complex error handling
**Measurement:** Achieved 1.8x speedup in tests
```

---

### Day 22-24: Web Search Agent

**Coding Challenge 9: Web Search Integration**
```python
# File: app/agents/web_search_agent.py
# File: app/tools/web_search.py

from langchain.tools import tool

@tool
async def search_financial_news(
    query: str,
    companies: List[str],
    time_period: str = \"1m\"
) -> Dict[str, Any]:
    \"\"\"
    Search web for recent financial news.
    
    Use Tavily API for structured results.
    
    TODO:
    1. Construct search queries
    2. Call Tavily API
    3. Filter for authoritative sources
    4. Return structured results
    \"\"\"
    pass

async def web_search_agent_node(state: FinanceAgentState) -> FinanceAgentState:
    \"\"\"
    Search web for recent context.
    
    TODO:
    1. Generate 3-5 search queries
    2. Execute searches in parallel
    3. Filter and rank results
    4. Log decisions
    \"\"\"
    pass
```

**Evaluation:**
- [ ] Returns relevant, recent articles
- [ ] Filters out SEO spam
- [ ] Prefers authoritative sources
- [ ] Handles API failures gracefully

**Week 3-4 Deliverable:**
- Lead agent + 2 workers (RAG, web search)
- Parallel execution working
- Comparison queries working
- 5+ decision log entries
- Can explain orchestrator pattern to interviewer

---

## Week 5-6: Advanced Agents & Tools (Days 29-42)

### Learning Objectives
- Add analysis agent for calculations
- Build citation agent
- Implement synthesis agent
- Master tool calling patterns

### Coding Challenges:
- Challenge 10: Financial calculator tool
- Challenge 11: Analysis agent with code execution
- Challenge 12: Citation agent
- Challenge 13: Synthesis agent

**Evaluation Focus:**
- Tool selection accuracy
- Calculation correctness
- Citation accuracy
- Synthesis quality

**Week 5-6 Deliverable:**
- 5 agents working together
- Complex queries handled end-to-end
- All citations accurate
- Eval suite passing >85%

---

## Week 7-8: Production & Interview Prep (Days 43-56)

### Learning Objectives
- Production hardening
- Cost optimization
- Interview preparation
- Demo creation

### Activities:
- Error handling for all failure modes
- Cost tracking and optimization
- Load testing
- Create demo video
- Practice interview questions
- Write blog post about learnings

### Final Deliverable:
- Production-ready Finance Agent v2.0
- 20+ decision log entries
- Eval suite passing >90%
- 5-minute demo video
- Interview question answers documented
- Blog post published

---

## Evaluation Rubrics

### Agent Quality Rubric (Anthropic Pattern)

**Outcome Metrics:**
- Factual Accuracy: 0.0-1.0
- Citation Accuracy: 0.0-1.0
- Completeness: 0.0-1.0
- Source Quality: 0.0-1.0

**Process Metrics:**
- Tool Efficiency: 0.0-1.0 (not too many, not too few)
- Decision Quality: 0.0-1.0 (reasonable choices)
- Error Handling: 0.0-1.0 (graceful degradation)

**Pass Threshold:** All metrics > 0.7, overall > 0.8

### Interview Readiness Rubric

**Technical Knowledge (1-5):**
- [ ] Can explain multi-agent architecture (5 = teach others)
- [ ] Can discuss LangGraph internals (5 = contribute to library)
- [ ] Can compare frameworks (5 = make informed recommendations)

**System Design (1-5):**
- [ ] Can design agent systems (5 = production-ready designs)
- [ ] Can discuss trade-offs (5 = quantify with data)
- [ ] Can optimize for cost/quality (5 = proven strategies)

**Production Experience (1-5):**
- [ ] Can discuss failures (5 = learned from real incidents)
- [ ] Can explain monitoring (5 = built observability systems)
- [ ] Can discuss scaling (5 = scaled to production load)

**Target:** All metrics ≥ 4 for interview readiness

---

## Interview Question Bank

### Week 1-2 Questions:
1. Explain StateGraph vs MessageGraph
2. Why is state immutability important?
3. How does checkpointing work?
4. Design a decision logging system

### Week 3-4 Questions:
1. Orchestrator-worker vs peer-to-peer patterns?
2. When to use parallel vs sequential execution?
3. How to prevent agent coordination failures?
4. Design a routing system for dynamic agent selection

### Week 5-6 Questions:
1. How do you evaluate agent quality?
2. LLM-as-judge vs rule-based evaluation?
3. Tool calling best practices?
4. How to handle tool failures?

### Week 7-8 Questions:
1. Production challenges in multi-agent systems?
2. Cost optimization strategies?
3. How to debug emergent behaviors?
4. Scaling multi-agent systems?

---

## Success Metrics

**By Week 4:**
- [ ] Working multi-agent system (3+ agents)
- [ ] Decision log with 10+ entries
- [ ] Can explain architecture on whiteboard
- [ ] Eval suite passing >80%

**By Week 8:**
- [ ] Production-ready system
- [ ] Decision log with 20+ entries
- [ ] Demo video recorded
- [ ] Eval suite passing >90%
- [ ] Ready for interviews

---

**Remember:** Focus on learning deeply, not just building quickly. Every decision is a learning opportunity. Document your reasoning. The goal is interview readiness AND a production system.