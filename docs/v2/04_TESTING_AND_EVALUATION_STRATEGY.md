# Testing and Evaluation Strategy for Multi-Agent Finance Agent

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Test Types and Hierarchy](#test-types-and-hierarchy)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Agent Evaluation](#agent-evaluation)
7. [Performance Testing](#performance-testing)
8. [Evaluation Metrics](#evaluation-metrics)

---

## Testing Philosophy

### Anthropic's Insights on Agent Testing

Based on Anthropic's multi-agent research system:

**Key Finding**: Traditional testing assumes fixed paths (input X → path Y → output Z), but multi-agent systems don't work this way. Even with identical inputs, agents may take different valid paths.

**Solution**: Focus on **outcome evaluation** rather than **process validation**.

### Testing Pyramid for Agents

```
         /\
        /  \  E2E Tests (10%)
       /____\  - Real LLMs, full system
      /      \ - Complex queries, edge cases
     /________\ Integration Tests (30%)
    /          \ - Multiple agents + real services
   /____________\ - Mocked LLMs possible
  /              \
 /________________\ Unit Tests (60%)
/                  \ - Individual agents/tools
--------------------  - Fast, isolated, deterministic
```

---

## Test Types and Hierarchy

### 1. Unit Tests (60% of test suite)

**Purpose**: Test individual components in isolation

**What to Test**:
- Individual agent functions
- Tool functions
- State transformers
- Utility functions
- Validators

**Characteristics**:
- Fast (< 1 second each)
- Deterministic
- Use mocked LLMs (FakeLLM)
- No external dependencies

### 2. Integration Tests (30% of test suite)

**Purpose**: Test interactions between components

**What to Test**:
- Multiple agents working together
- Agent + database interactions
- Agent + vector store interactions
- Graph execution with subgraphs

**Characteristics**:
- Medium speed (1-10 seconds)
- May use real services (DB, Qdrant)
- Can mock LLMs or use smaller models
- Tests coordination logic

### 3. End-to-End Tests (10% of test suite)

**Purpose**: Test complete user journeys

**What to Test**:
- Full query processing pipeline
- Real LLM responses
- Complete graph execution
- Production-like scenarios

**Characteristics**:
- Slow (10-60 seconds)
- Uses real LLMs
- All services running
- Tests actual user experience

---

## Unit Testing

### Test Structure

```python
# tests/unit/test_rag_agent.py

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain.llms.fake import FakeListLLM
from datetime import datetime

from app.agents.rag_agent import rag_agent
from app.schemas.state import FinanceAgentState


class TestRAGAgent:
    """Test suite for RAG Agent."""
    
    @pytest.fixture
    def base_state(self):
        """Fixture providing standard test state."""
        return FinanceAgentState(
            query="What was Apple's Q4 2024 revenue?",
            user_id="test_user",
            session_id="test_123",
            companies_mentioned=["AAPL"],
            query_type="simple",
            retrieval_results={},
            execution_log=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_qdrant(self):
        """Fixture providing mocked Qdrant client."""
        mock = Mock()
        mock.search = AsyncMock(return_value=[
            Mock(
                score=0.95,
                payload={
                    "text": "Apple Inc. reported net sales of $119.6B for Q4 2024",
                    "filing_type": "10-Q",
                    "section": "Item 1",
                    "page": 3,
                    "filing_date": "2024-11-01"
                }
            ),
            Mock(
                score=0.89,
                payload={
                    "text": "Products revenue was $96.5B, up from $89.5B YoY",
                    "filing_type": "10-Q",
                    "section": "Item 1",
                    "page": 3,
                    "filing_date": "2024-11-01"
                }
            )
        ])
        return mock
    
    @pytest.fixture
    def fake_llm(self):
        """Fixture providing deterministic fake LLM."""
        responses = [
            """Based on the SEC filings, Apple's Q4 2024 revenue was $119.6B.
            
            This represents strong growth from the previous year."""
        ]
        return FakeListLLM(responses=responses)
    
    # SUCCESS TESTS
    
    @pytest.mark.asyncio
    async def test_rag_agent_retrieves_data_successfully(
        self, base_state, mock_qdrant, fake_llm
    ):
        """Test: RAG agent successfully retrieves and processes data."""
        # Arrange
        expected_ticker = "AAPL"
        
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        assert result_state["retrieval_results"][expected_ticker] is not None
        assert "error" not in result_state or result_state["error"] is None
        assert len(result_state["execution_log"]) > 0
        assert "RAG search completed" in result_state["execution_log"][-1]
        
        # Verify Qdrant was called correctly
        mock_qdrant.search.assert_called_once()
        call_args = mock_qdrant.search.call_args
        assert call_args.kwargs["collection_name"] == "sec_filings"
    
    @pytest.mark.asyncio
    async def test_rag_agent_adds_metadata_to_results(
        self, base_state, mock_qdrant, fake_llm
    ):
        """Test: RAG agent includes comprehensive metadata."""
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        result = result_state["retrieval_results"]["AAPL"]
        assert "chunks" in result
        assert "metadata" in result
        assert "timestamp" in result["metadata"]
        assert "source" in result["metadata"]
        assert result["metadata"]["source"] == "qdrant"
    
    # FAILURE TESTS
    
    @pytest.mark.asyncio
    async def test_rag_agent_handles_qdrant_timeout(
        self, base_state, fake_llm
    ):
        """Test: RAG agent handles Qdrant timeout gracefully."""
        # Arrange
        mock_qdrant = Mock()
        mock_qdrant.search = AsyncMock(side_effect=TimeoutError("Qdrant timeout"))
        
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        assert result_state["error"] is not None
        assert "timeout" in result_state["error"].lower()
        assert "RAG agent failed" in result_state["execution_log"][-1]
        # Should not crash, should return state with error
        assert isinstance(result_state, dict)
    
    @pytest.mark.asyncio
    async def test_rag_agent_handles_empty_results(
        self, base_state, fake_llm
    ):
        """Test: RAG agent handles empty search results."""
        # Arrange
        mock_qdrant = Mock()
        mock_qdrant.search = AsyncMock(return_value=[])  # No results
        
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        assert "No data found" in result_state["execution_log"][-1]
        # Should provide helpful message to user
        assert result_state["retrieval_results"]["AAPL"]["chunks"] == []
    
    @pytest.mark.asyncio
    async def test_rag_agent_validates_ticker_format(
        self, base_state, mock_qdrant, fake_llm
    ):
        """Test: RAG agent validates ticker symbols."""
        # Arrange
        base_state["companies_mentioned"] = ["INVALID!!TICKER"]
        
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        assert result_state["error"] is not None
        assert "invalid ticker" in result_state["error"].lower()
    
    # EDGE CASES
    
    @pytest.mark.asyncio
    async def test_rag_agent_handles_multiple_companies(
        self, base_state, fake_llm
    ):
        """Test: RAG agent can handle multiple companies."""
        # Arrange
        base_state["companies_mentioned"] = ["AAPL", "MSFT", "GOOGL"]
        
        mock_qdrant = Mock()
        mock_qdrant.search = AsyncMock(return_value=[
            Mock(score=0.9, payload={"text": "Data for company", "filing_type": "10-Q"})
        ])
        
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        # Should call search once per company
        assert mock_qdrant.search.call_count == 3
        # Should have results for all companies
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            assert ticker in result_state["retrieval_results"]
    
    @pytest.mark.asyncio
    async def test_rag_agent_respects_date_filters(
        self, base_state, mock_qdrant, fake_llm
    ):
        """Test: RAG agent applies date range filters."""
        # Arrange
        base_state["time_period"] = {
            "start": "2024-01-01",
            "end": "2024-12-31"
        }
        
        # Act
        with patch('app.agents.rag_agent.get_qdrant_client', return_value=mock_qdrant):
            with patch('app.agents.rag_agent.get_llm', return_value=fake_llm):
                result_state = await rag_agent(base_state)
        
        # Assert
        call_args = mock_qdrant.search.call_args
        filters = call_args.kwargs.get("query_filter")
        # Verify date filters were applied
        assert filters is not None
        # (Implementation-specific assertion)


class TestLeadAgent:
    """Test suite for Lead Agent."""
    
    @pytest.mark.asyncio
    async def test_lead_agent_categorizes_simple_query(self):
        """Test: Lead agent correctly identifies simple query."""
        state = FinanceAgentState(
            query="What was Apple's revenue in Q4 2024?",
            user_id="test",
            session_id="test",
            companies_mentioned=[],
            execution_log=[]
        )
        
        result = await lead_agent(state)
        
        assert result["query_type"] == "simple"
        assert len(result["companies_mentioned"]) == 1
        assert "AAPL" in result["companies_mentioned"]
        assert "research_plan" in result
    
    @pytest.mark.asyncio
    async def test_lead_agent_plans_complex_query(self):
        """Test: Lead agent creates appropriate plan for complex query."""
        state = FinanceAgentState(
            query="Compare Apple and Microsoft revenue growth trends over the last 3 years and explain market factors",
            user_id="test",
            session_id="test",
            companies_mentioned=[],
            execution_log=[]
        )
        
        result = await lead_agent(state)
        
        assert result["query_type"] == "complex"
        assert len(result["companies_mentioned"]) >= 2
        assert result["requires_web_search"] is True
        assert len(result["research_plan"]["subtasks"]) >= 3


class TestTools:
    """Test suite for Tools."""
    
    def test_sec_search_tool_validates_inputs(self):
        """Test: SEC search tool validates ticker format."""
        from app.tools.sec_search import search_sec_filings
        
        # Invalid ticker
        result = search_sec_filings(
            ticker="INVALID$$$",
            filing_types=["10-K"],
            query="revenue"
        )
        
        assert result["success"] is False
        assert "invalid ticker" in result["error"].lower()
    
    def test_financial_calculator_handles_missing_data(self):
        """Test: Calculator tool handles missing required data."""
        from app.tools.calculator import calculate_financial_metric
        
        result = calculate_financial_metric(
            metric_name="revenue_growth",
            data={"current_revenue": 100}  # Missing previous_revenue
        )
        
        assert result["success"] is False
        assert "missing" in result["error"].lower()
```

---

## Integration Testing

### Testing Multiple Agents Together

```python
# tests/integration/test_agent_coordination.py

import pytest
from app.graphs.finance_graph import build_finance_agent_graph
from app.schemas.state import FinanceAgentState


@pytest.mark.integration
class TestAgentCoordination:
    """Integration tests for multi-agent coordination."""
    
    @pytest.fixture
    def real_services(self):
        """Fixture providing real service connections."""
        # These run against test databases/services
        return {
            "qdrant": get_test_qdrant_client(),
            "postgres": get_test_db_session(),
            "redis": get_test_redis_client()
        }
    
    @pytest.mark.asyncio
    async def test_lead_agent_spawns_rag_agents(self, real_services):
        """Test: Lead agent correctly spawns RAG workers."""
        # Arrange
        graph = build_finance_agent_graph()
        initial_state = {
            "query": "Compare Apple and Microsoft Q4 2024 revenues",
            "user_id": "integration_test",
            "session_id": "test_123"
        }
        
        # Act
        result = await graph.ainvoke(initial_state)
        
        # Assert
        assert "AAPL" in result["retrieval_results"]
        assert "MSFT" in result["retrieval_results"]
        assert len(result["execution_log"]) > 2  # Multiple agents ran
        # Check that agents ran in expected order
        assert "lead_agent" in result["execution_log"][0]
        assert any("rag_agent" in log for log in result["execution_log"])
    
    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self, real_services):
        """Test: Parallel agent execution is faster."""
        import time
        
        # Arrange
        graph_parallel = build_finance_agent_graph(parallel=True)
        graph_sequential = build_finance_agent_graph(parallel=False)
        
        query = {
            "query": "Get financial data for Apple, Microsoft, and Google",
            "user_id": "perf_test",
            "session_id": "test_perf"
        }
        
        # Act
        start = time.time()
        await graph_parallel.ainvoke(query)
        parallel_time = time.time() - start
        
        start = time.time()
        await graph_sequential.ainvoke(query)
        sequential_time = time.time() - start
        
        # Assert
        # Parallel should be at least 30% faster for 3 companies
        assert parallel_time < sequential_time * 0.7
    
    @pytest.mark.asyncio
    async def test_error_in_one_agent_doesnt_crash_system(self, real_services):
        """Test: System handles partial failures gracefully."""
        # Arrange
        graph = build_finance_agent_graph()
        
        # Simulate Qdrant failure for one ticker
        with patch('app.services.qdrant_service.search') as mock_search:
            mock_search.side_effect = [
                [{"text": "AAPL data"}],  # Success for AAPL
                Exception("Connection failed"),  # Failure for MSFT
            ]
            
            # Act
            result = await graph.ainvoke({
                "query": "Compare Apple and Microsoft",
                "user_id": "test",
                "session_id": "test_err"
            })
        
        # Assert
        assert "AAPL" in result["retrieval_results"]
        assert result["retrieval_results"]["AAPL"]["success"] is True
        # MSFT should have error but system didn't crash
        assert "MSFT" in result["retrieval_results"]
        assert result["retrieval_results"]["MSFT"]["success"] is False
        # Final answer should mention partial results
        assert "partial" in result["final_answer"].lower() or "available" in result["final_answer"].lower()
```

---

## End-to-End Testing

### Real User Scenarios

```python
# tests/e2e/test_user_journeys.py

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.e2e
class TestUserJourneys:
    """End-to-end tests simulating real user interactions."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for API testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_simple_query_flow(self, client):
        """
        User Journey: Simple SEC filing query
        
        Steps:
        1. User asks about Apple's revenue
        2. System retrieves from SEC filings
        3. Returns answer with citations
        """
        # Act
        response = await client.post(
            "/api/v2/query-multi-agent",
            json={
                "query": "What was Apple's total revenue in Q4 2024?",
                "user_id": "e2e_user_1"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should have clear answer
        assert "answer" in data
        assert "119" in data["answer"] or "billion" in data["answer"].lower()
        
        # Should have citations
        assert "citations" in data
        assert len(data["citations"]) > 0
        assert any("10-Q" in cite or "10-K" in cite for cite in data["citations"])
        
        # Should complete in reasonable time
        assert data.get("execution_time_seconds", 999) < 30
    
    @pytest.mark.asyncio
    async def test_comparison_query_flow(self, client):
        """
        User Journey: Company comparison
        
        Steps:
        1. User asks to compare two companies
        2. System retrieves both companies' data
        3. Performs analysis
        4. Returns comprehensive comparison
        """
        response = await client.post(
            "/api/v2/query-multi-agent",
            json={
                "query": "Compare Apple and Microsoft Q4 2024 revenues. Which grew faster?",
                "user_id": "e2e_user_2"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should mention both companies
        assert "Apple" in data["answer"] or "AAPL" in data["answer"]
        assert "Microsoft" in data["answer"] or "MSFT" in data["answer"]
        
        # Should perform comparison
        assert "higher" in data["answer"].lower() or "faster" in data["answer"].lower() or "grew" in data["answer"].lower()
        
        # Should have citations for both companies
        apple_citations = [c for c in data["citations"] if "AAPL" in c or "Apple" in c]
        msft_citations = [c for c in data["citations"] if "MSFT" in c or "Microsoft" in c]
        assert len(apple_citations) > 0
        assert len(msft_citations) > 0
    
    @pytest.mark.asyncio
    async def test_complex_analysis_query_flow(self, client):
        """
        User Journey: Complex analysis with web context
        
        Steps:
        1. User asks complex question requiring multiple sources
        2. System searches SEC filings
        3. System searches web for context
        4. Performs analysis
        5. Returns comprehensive report
        """
        response = await client.post(
            "/api/v2/query-multi-agent",
            json={
                "query": "Analyze Apple's iPhone revenue trend over the last 3 quarters and explain why based on market conditions",
                "user_id": "e2e_user_3"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have used multiple agents
        assert data.get("agents_used", [])
        assert "rag_agent" in data["agents_used"]
        assert "web_search_agent" in data["agents_used"]
        assert "analysis_agent" in data["agents_used"]
        
        # Should show trend
        assert "trend" in data["answer"].lower() or "quarter" in data["answer"].lower()
        
        # Should explain with context
        assert len(data["answer"]) > 500  # Substantial analysis
        
        # Should have both SEC and web sources
        sec_citations = [c for c in data["citations"] if "10-" in c]
        web_citations = [c for c in data["citations"] if "http" in c]
        assert len(sec_citations) > 0
        assert len(web_citations) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_query_handling(self, client):
        """Test: System handles invalid queries gracefully."""
        response = await client.post(
            "/api/v2/query-multi-agent",
            json={
                "query": "asdfkjas dflkjasdflk",  # Gibberish
                "user_id": "e2e_user_4"
            }
        )
        
        # Should not crash
        assert response.status_code == 200
        data = response.json()
        
        # Should provide helpful message
        assert "could not understand" in data["answer"].lower() or "unclear" in data["answer"].lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test: API enforces rate limits."""
        # Make rapid requests
        for i in range(15):  # Assuming limit is 10/min
            response = await client.post(
                "/api/v2/query-multi-agent",
                json={
                    "query": f"Test query {i}",
                    "user_id": "rate_limit_test"
                }
            )
            
            if i < 10:
                assert response.status_code == 200
            else:
                assert response.status_code == 429  # Too Many Requests
```

---

## Agent Evaluation

### LLM-as-Judge Evaluation

```python
# tests/evaluation/test_agent_quality.py

import pytest
from app.evaluation.llm_judge import evaluate_response
from app.schemas.evaluation import EvaluationCriteria


class TestAgentQuality:
    """Evaluation tests using LLM-as-judge."""
    
    @pytest.mark.evaluation
    async def test_factual_accuracy(self):
        """Evaluate: Are agent responses factually accurate?"""
        # Arrange
        test_cases = [
            {
                "query": "What was Apple's Q4 2024 revenue?",
                "response": "Apple reported revenues of $119.6B in Q4 2024.",
                "ground_truth": "119.6 billion",
                "sources": ["AAPL 10-Q 2024-11-01"]
            },
            # Add more test cases...
        ]
        
        results = []
        for case in test_cases:
            # Act
            evaluation = await evaluate_response(
                query=case["query"],
                response=case["response"],
                ground_truth=case["ground_truth"],
                sources=case["sources"],
                criteria=EvaluationCriteria.FACTUAL_ACCURACY
            )
            
            results.append(evaluation)
        
        # Assert
        avg_score = sum(r["score"] for r in results) / len(results)
        assert avg_score >= 0.9, f"Factual accuracy too low: {avg_score}"
    
    @pytest.mark.evaluation
    async def test_citation_accuracy(self):
        """Evaluate: Are citations correct and complete?"""
        test_cases = [
            {
                "response": "Apple's revenue was $119.6B[1].",
                "citations": ["[1] Apple Inc. 10-Q (2024-11-01), p.3"],
                "source_documents": [
                    {"text": "Net sales: $119.6B", "filing": "10-Q", "date": "2024-11-01"}
                ]
            },
        ]
        
        for case in test_cases:
            evaluation = await evaluate_response(
                response=case["response"],
                citations=case["citations"],
                source_documents=case["source_documents"],
                criteria=EvaluationCriteria.CITATION_ACCURACY
            )
            
            assert evaluation["score"] >= 0.9
            assert evaluation["all_claims_cited"]
            assert evaluation["citations_match_sources"]
    
    @pytest.mark.evaluation
    async def test_completeness(self):
        """Evaluate: Does response address all aspects of query?"""
        test_case = {
            "query": "Compare Apple and Microsoft Q4 2024 revenues and margins",
            "response": "Apple had revenue of $119.6B with 29.1% margin. Microsoft had $62.0B revenue with 41.5% margin. Microsoft's margin is higher.",
            "aspects_required": ["apple_revenue", "msft_revenue", "apple_margin", "msft_margin", "comparison"]
        }
        
        evaluation = await evaluate_response(
            query=test_case["query"],
            response=test_case["response"],
            aspects_required=test_case["aspects_required"],
            criteria=EvaluationCriteria.COMPLETENESS
        )
        
        assert evaluation["score"] >= 0.8
        assert evaluation["covered_aspects"] == test_case["aspects_required"]
```

### Evaluation Rubric

```python
# app/evaluation/rubric.py

from typing import Dict, Any
from pydantic import BaseModel


class EvaluationRubric(BaseModel):
    """Rubric for evaluating agent responses."""
    
    factual_accuracy: float  # 0.0-1.0
    citation_accuracy: float
    completeness: float
    source_quality: float
    tool_efficiency: float
    response_quality: float  # Overall
    
    def overall_score(self) -> float:
        """Calculate weighted overall score."""
        weights = {
            "factual_accuracy": 0.30,
            "citation_accuracy": 0.20,
            "completeness": 0.20,
            "source_quality": 0.15,
            "tool_efficiency": 0.10,
            "response_quality": 0.05
        }
        
        score = sum(
            getattr(self, criterion) * weight
            for criterion, weight in weights.items()
        )
        
        return round(score, 3)
    
    def pass_fail(self, threshold: float = 0.8) -> bool:
        """Determine if response passes quality threshold."""
        return self.overall_score() >= threshold


async def evaluate_with_llm(
    query: str,
    response: str,
    citations: List[str],
    sources: List[Dict],
    execution_log: List[str]
) -> EvaluationRubric:
    """
    Use LLM to evaluate response quality.
    
    This is the "LLM-as-judge" pattern from Anthropic's best practices.
    """
    evaluation_prompt = f"""
You are an expert evaluator for financial research AI systems.

USER QUERY: {query}

AGENT RESPONSE: {response}

CITATIONS: {citations}

SOURCE DOCUMENTS: {sources}

EXECUTION LOG: {execution_log}

Evaluate the response on these criteria (score 0.0-1.0):

1. FACTUAL ACCURACY (weight: 30%)
   - Do the claims match the source documents?
   - Are numbers/dates correct?
   - Is there any misinformation?
   Score: [0.0-1.0]
   Reasoning: [Brief explanation]

2. CITATION ACCURACY (weight: 20%)
   - Is every factual claim cited?
   - Do citations point to correct sources?
   - Are citations formatted properly?
   Score: [0.0-1.0]
   Reasoning: [Brief explanation]

3. COMPLETENESS (weight: 20%)
   - Does response fully answer the question?
   - Are all requested aspects covered?
   - Is any important information missing?
   Score: [0.0-1.0]
   Reasoning: [Brief explanation]

4. SOURCE QUALITY (weight: 15%)
   - Are sources authoritative (official SEC vs forums)?
   - Are sources recent enough?
   - Are there enough sources for claims?
   Score: [0.0-1.0]
   Reasoning: [Brief explanation]

5. TOOL EFFICIENCY (weight: 10%)
   - Did agent use appropriate tools?
   - Were there unnecessary tool calls?
   - Was execution efficient?
   Score: [0.0-1.0]
   Reasoning: [Brief explanation]

6. RESPONSE QUALITY (weight: 5%)
   - Is response clear and well-structured?
   - Is it appropriately concise/detailed?
   - Is language professional?
   Score: [0.0-1.0]
   Reasoning: [Brief explanation]

Provide scores as JSON:
{{
  "factual_accuracy": 0.X,
  "citation_accuracy": 0.X,
  "completeness": 0.X,
  "source_quality": 0.X,
  "tool_efficiency": 0.X,
  "response_quality": 0.X,
  "reasoning": {{
    "factual_accuracy": "...",
    "citation_accuracy": "...",
    ...
  }}
}}
"""
    
    # Call LLM for evaluation
    llm_response = await llm.ainvoke(evaluation_prompt)
    scores = parse_json(llm_response)
    
    return EvaluationRubric(**scores)
```

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py

import pytest
import asyncio
from statistics import mean, stdev


@pytest.mark.performance
class TestPerformance:
    """Performance and load tests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test: System handles concurrent requests."""
        # Arrange
        num_concurrent = 10
        queries = [
            {"query": f"Test query {i}", "user_id": f"perf_user_{i}"}
            for i in range(num_concurrent)
        ]
        
        # Act
        start = time.time()
        tasks = [query_multi_agent(q) for q in queries]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        
        # Assert
        assert all(r["success"] for r in results)
        # Should handle all requests in reasonable time
        assert total_time < 60  # 10 requests in < 60 seconds
        
        # Average time per request should be reasonable
        avg_time = total_time / num_concurrent
        assert avg_time < 10
    
    @pytest.mark.asyncio
    async def test_latency_distribution(self):
        """Test: Measure latency distribution."""
        # Arrange
        num_requests = 50
        latencies = []
        
        # Act
        for i in range(num_requests):
            start = time.time()
            result = await query_multi_agent({"query": f"Test {i}", "user_id": f"latency_test_{i}"})
            latency = time.time() - start
            latencies.append(latency)
        
        # Assert
        avg_latency = mean(latencies)
        std_latency = stdev(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        p99_latency = sorted(latencies)[int(0.99 * len(latencies))]
        
        print(f"""
        Latency Statistics:
        Average: {avg_latency:.2f}s
        Std Dev: {std_latency:.2f}s
        P95: {p95_latency:.2f}s
        P99: {p99_latency:.2f}s
        """)
        
        # Performance targets
        assert avg_latency < 15, "Average latency too high"
        assert p95_latency < 30, "P95 latency too high"
        assert p99_latency < 45, "P99 latency too high"
    
    @pytest.mark.asyncio
    async def test_token_usage_tracking(self):
        """Test: Track token usage for cost monitoring."""
        queries = [
            "Simple query",
            "Medium complexity comparison",
            "Complex analysis with multiple companies and context"
        ]
        
        results = []
        for query in queries:
            result = await query_multi_agent({"query": query, "user_id": "token_test"})
            results.append({
                "query": query,
                "tokens": result.get("token_usage", {}),
                "cost_estimate": calculate_cost(result.get("token_usage", {}))
            })
        
        # Log for monitoring
        for r in results:
            print(f"Query: {r['query']}")
            print(f"Tokens: {r['tokens']}")
            print(f"Cost: ${r['cost_estimate']:.4f}")
        
        # Assert costs are reasonable
        assert all(r["cost_estimate"] < 1.0 for r in results), "Query too expensive"
```

---

## Evaluation Metrics Dashboard

### Key Metrics to Track

```python
# app/monitoring/metrics.py

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class AgentMetrics:
    """Metrics for monitoring agent performance."""
    
    # Latency
    avg_latency_seconds: float
    p95_latency_seconds: float
    p99_latency_seconds: float
    
    # Success Rate
    total_queries: int
    successful_queries: int
    failed_queries: int
    partial_results: int
    
    def success_rate(self) -> float:
        return self.successful_queries / self.total_queries if self.total_queries > 0 else 0.0
    
    # Token Usage
    avg_tokens_per_query: float
    total_tokens: int
    
    # Cost
    total_cost_usd: float
    avg_cost_per_query: float
    
    # Quality (from evaluations)
    avg_factual_accuracy: float
    avg_citation_accuracy: float
    avg_completeness: float
    
    # Tool Usage
    tool_call_distribution: Dict[str, int]
    avg_tool_calls_per_query: float
    
    # Agent Usage
    agent_usage_distribution: Dict[str, int]
    
    def to_dashboard_dict(self) -> Dict:
        """Format metrics for dashboard display."""
        return {
            "performance": {
                "avg_latency": f"{self.avg_latency_seconds:.2f}s",
                "p95_latency": f"{self.p95_latency_seconds:.2f}s",
                "success_rate": f"{self.success_rate():.1%}"
            },
            "cost": {
                "total": f"${self.total_cost_usd:.2f}",
                "per_query": f"${self.avg_cost_per_query:.4f}"
            },
            "quality": {
                "factual_accuracy": f"{self.avg_factual_accuracy:.1%}",
                "citation_accuracy": f"{self.avg_citation_accuracy:.1%}",
                "completeness": f"{self.avg_completeness:.1%}"
            },
            "usage": {
                "total_queries": self.total_queries,
                "tool_calls": self.tool_call_distribution,
                "agent_usage": self.agent_usage_distribution
            }
        }
```

### Sample Evaluation Report

```
AGENT EVALUATION REPORT
=====================
Date: 2025-01-15
Evaluation Period: Last 7 days
Total Queries Evaluated: 500

OVERALL SCORES
--------------
✓ Factual Accuracy:    94.2% (target: >90%)
✓ Citation Accuracy:   91.8% (target: >90%)
✓ Completeness:        88.5% (target: >85%)
✓ Source Quality:      92.1% (target: >90%)
⚠ Tool Efficiency:     78.3% (target: >80%)
✓ Response Quality:    90.7% (target: >85%)

OVERALL PASS RATE: 89.2% (target: >85%)

PERFORMANCE METRICS
-------------------
Latency:
  Average: 12.4s
  P95:     24.8s  
  P99:     38.2s

Success Rate: 96.4%
Failed Queries: 3.6%

TOKEN USAGE
-----------
Total Tokens: 2.4M
Avg per Query: 4,800 tokens
Cost: $144.50 ($0.29/query)

BY QUERY COMPLEXITY
-------------------
Simple:  5,200 tokens avg, $0.15/query
Medium:  8,100 tokens avg, $0.42/query
Complex: 22,300 tokens avg, $1.24/query

RECOMMENDATIONS
---------------
1. Improve tool efficiency (currently 78.3%)
   - Reduce redundant web searches
   - Better caching of embedding lookups
   
2. Monitor complex query costs
   - Average $1.24/query may be high
   - Consider using smaller models for subtasks

3. Investigate failed queries (3.6%)
   - Most failures: Qdrant timeouts
   - Action: Increase timeout, add retry logic
```

---

## Testing Best Practices Summary

1. **Start with Unit Tests**: Test components in isolation first
2. **Mock External Dependencies**: Use FakeLLM, Mock services in unit tests
3. **Test Both Paths**: Success and failure scenarios
4. **Use Real LLMs for E2E**: Integration tests can mock, but E2E should be real
5. **Measure Everything**: Latency, tokens, costs, success rates
6. **Use LLM-as-Judge**: For quality evaluation at scale
7. **Track Trends**: Monitor metrics over time, not just point-in-time
8. **Test Edge Cases**: Empty results, timeouts, invalid inputs
9. **Performance Test Early**: Don't wait until production
10. **Automate Evaluation**: Run eval suite on every major change

---

## Continuous Evaluation Pipeline

```yaml
# .github/workflows/evaluation.yml

name: Agent Evaluation Pipeline

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/unit -v
  
  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
      qdrant:
        image: qdrant/qdrant:latest
    steps:
      - name: Run integration tests
        run: pytest tests/integration -v
  
  evaluation:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run LLM evaluation
        run: pytest tests/evaluation -v --create-report
      - name: Upload evaluation report
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-report
          path: reports/evaluation_report.html
```

---

## Resources

- [Anthropic Evaluation Guide](https://docs.anthropic.com/en/docs/build-with-claude/evaluation)
- [LangSmith Evaluation](https://docs.smith.langchain.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Load Testing with Locust](https://locust.io/)
