
# Comprehensive Study Guide: FinanceAgent Project

Based on the docs folder and implementation, here's an exhaustive list of concepts, technologies, and decisions you need to study to understand everything about this project.

---

## 📚 **PART 1: CORE CONCEPTS & ARCHITECTURE**

### **1.1 Multi-Agent Systems**
- [ ] **LangGraph Framework**
  - StateGraph vs MessageGraph
  - Nodes, edges, conditional edges
  - START and END constants
  - Graph compilation and execution
  - State management patterns
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/01_FRAMEWORK_COMPARISON_AND_RECOMMENDATION.md`

- [ ] **Agent Design Patterns**
  - Orchestrator-Worker pattern
  - Supervisor-Agent architecture
  - Single responsibility principle for agents
  - Tool-calling agents vs reasoning agents
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/02_MULTI_AGENT_ARCHITECTURE_DESIGN.md`

- [ ] **Framework Comparison**
  - LangGraph vs CrewAI vs AutoGen
  - Why LangGraph was chosen
  - Production readiness criteria
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/01_FRAMEWORK_COMPARISON_AND_RECOMMENDATION.md`

### **1.2 RAG (Retrieval-Augmented Generation)**
- [ ] **RAG Pipeline Stages**
  - Query embedding
  - Vector search (cosine similarity)
  - Context building
  - LLM generation
  - Citation extraction
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/rag_search_service.py`

- [ ] **Why RAG over Fine-Tuning**
  - Dynamic data updates (quarterly SEC filings)
  - Transparency (source citations)
  - Cost efficiency
  - Flexibility
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:342-365`

---

## 📚 **PART 2: CHECKPOINTING & SESSION MANAGEMENT**

### **2.1 LangGraph Checkpointing**
- [ ] **AsyncPostgresSaver**
  - Async context manager protocol
  - Manual lifecycle management (`__aenter__`, `__aexit__`)
  - Idempotent setup (table creation)
  - Singleton pattern for connection pooling
  - **Implementation**: `@/Users/harpreet/financeagent/app/agents/supervisor.py:49-119`
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/08_CHECKPOINT_AND_SESSION_MANAGEMENT.md`

- [ ] **Database Schema**
  - `checkpoints` table structure
  - `checkpoint_writes` table
  - `checkpoint_blobs` table
  - `checkpoint_migrations` table
  - Thread ID format: `{user_id}_{session_id}`
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/08_CHECKPOINT_AND_SESSION_MANAGEMENT.md:725-753`

- [ ] **Issues Encountered**
  - "async context manager protocol" error (sync vs async)
  - "connection is closed" error (context manager lifecycle)
  - Race conditions in frontend (session loading)
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/08_CHECKPOINT_AND_SESSION_MANAGEMENT.md:267-387`

### **2.2 Session Management**
- [ ] **Frontend localStorage**
  - Session ID persistence
  - Race condition prevention
  - New conversation handling
  - **Implementation**: `@/Users/harpreet/financeagent/docs/v2/08_CHECKPOINT_AND_SESSION_MANAGEMENT.md:445-524`

- [ ] **Backend Thread Management**
  - Thread ID generation
  - RunnableConfig usage
  - Session continuity
  - **Implementation**: `@/Users/harpreet/financeagent/app/agents/supervisor.py:230-307`

---

## 📚 **PART 3: CONTEXT WINDOW MANAGEMENT**

### **3.1 Token-Based Trimming**
- [ ] **The Problem**
  - Unbounded conversation growth with checkpointing
  - Context window overflow (8,192 tokens for llama3.1:8b)
  - Variable message sizes (tool responses: 5,000-10,000 tokens)
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:367-532`

- [ ] **Solution Options Compared**
  - Sliding window (message count) - REJECTED
  - Token-based trimming - CHOSEN
  - Conversation summarization - TOO COMPLEX
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/00_START_HERE_ROADMAP.md:3-110`

- [ ] **Implementation**
  - LangChain's `trim_messages` utility
  - Token counter function
  - Max token budget (6,000 tokens)
  - Strategy: "last" (keep most recent)
  - **Implementation**: `@/Users/harpreet/financeagent/app/agents/supervisor.py:153-178`

### **3.2 10 Benefits of Token Management**
- [ ] **Performance Benefits**
  - Inference speed: 3-4x faster (O(n²) attention complexity)
  - Memory efficiency: 75% less VRAM
  - Predictable latency (consistent 4s vs 3-25s)
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:535-845`

- [ ] **Cost & Scalability**
  - 76% cost reduction (for paid APIs)
  - 2.5x more concurrent users
  - Better token budget allocation
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:666-712`

- [ ] **Quality Benefits**
  - Reduced hallucination risk
  - Fair resource allocation
  - Model compatibility
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:635-781`

---

## 📚 **PART 4: STRUCTURED OUTPUTS**

### **4.1 Pydantic Schemas**
- [ ] **Schema Definition**
  - `SynthesizerOutput` model
  - `PlannerOutput` model
  - Nested models (Answer, Section, CompanyData, Comparison)
  - **Implementation**: `@/Users/harpreet/financeagent/app/schemas/synthesizer_output.py`

- [ ] **Ollama Structured Outputs**
  - `format` parameter with JSON schema
  - Constrained generation (grammar-based sampling)
  - Token-level constraints
  - Mathematical guarantee of valid JSON
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/rag_search_service.py:222-230`

- [ ] **Benefits**
  - 10% → 0% malformed JSON errors
  - 15% token reduction (removed formatting instructions)
  - Type safety with Pydantic
  - **Docs**: `@/Users/harpreet/financeagent/docs/PRESENTATION_OUTLINE.md:872-957`

### **4.2 Prompt Engineering Decision**
- [ ] **Natural Text In → JSON Out**
  - Context as natural text (not JSON)
  - Output as structured JSON
  - 20-30% token savings
  - LLMs comprehend narrative better
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:977-1024`

---

## 📚 **PART 5: MULTI-COMPANY COMPARISON**

### **5.1 The Simple Fix**
- [ ] **Data Structure Change**
  - Problem: `list` pooled all companies together
  - Solution: `dict` maintains per-company separation
  - Result: Equal retrieval (5 chunks per company)
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:442-518`
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:848-975`

- [ ] **Key Learning**
  - Data structures > Complex architecture
  - Test before redesigning
  - 1-2 days vs 5-6 weeks
  - 95% less code than parallel agent approach
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2.1/COMPARATIVE_ANALYSIS_FEATURE_DECISION.md`

### **5.2 Hallucination Filtering**
- [ ] **Post-Processing**
  - Filter companies not in original context
  - Remove comparison data for single company
  - Validate against retrieved tickers
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:837-854`

---

## 📚 **PART 6: MODEL SELECTION & BENCHMARKING**

### **6.1 Model Performance Analysis**
- [ ] **Benchmark Results**
  - llama3.1:8b: 30.2s, 72.5% accuracy (WINNER)
  - qwen2.5:72b: 692.9s, 50.8% accuracy (23x slower, worse!)
  - qwen2.5:32b: 197.9s, 51.7% accuracy
  - Mixtral:8x7b: FAILED (0/10 queries)
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/11_MODEL_PERFORMANCE_ANALYSIS.md`

- [ ] **Key Findings**
  - Size ≠ Performance (larger models worse)
  - Speed matters (only llama3.1 meets UX threshold <30s)
  - Consistency > Occasional speed
  - Mixed models don't work
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/11_MODEL_PERFORMANCE_ANALYSIS.md:299-382`

### **6.2 Embedding Models**
- [ ] **nomic-embed-text-v1.5**
  - 768 dimensions (vs 1024 for BGE)
  - 8,192 token context window (vs 512 for BGE)
  - Native Ollama integration
  - 25% less memory than BGE-large
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:76-94`

---

## 📚 **PART 7: DETERMINISTIC vs LLM DECISIONS**

### **7.1 Deterministic Planning**
- [ ] **Why Deterministic?**
  - 40% faster than LLM routing
  - 100% reliable (no hallucinations)
  - Easier to debug
  - Lower cost (no LLM call)
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:180-281`

- [ ] **When to Use LLM**
  - Complex reasoning required
  - Natural language understanding needed
  - Synthesis and generation
  - **Pattern**: Planner (deterministic) → Executor (deterministic) → Synthesizer (LLM)

### **7.2 3-Stage Pipeline**
- [ ] **Stage 1: Planner (LLM)**
  - Query intent classification
  - Ticker extraction
  - Task generation
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:283-377`

- [ ] **Stage 2: Executor (Deterministic)**
  - Vector search
  - Data preparation
  - Chunk retrieval
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:442-518`

- [ ] **Stage 3: Synthesizer (LLM)**
  - Answer generation
  - Structured output
  - Citation formatting
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:524-777`

---

## 📚 **PART 8: VECTOR DATABASE & EMBEDDINGS**

### **8.1 Qdrant Vector Store**
- [ ] **Configuration**
  - 768-dimensional vectors
  - Cosine similarity search
  - Metadata filtering (ticker, filing_type, section)
  - Score threshold (default: 0.5)
  - **Implementation**: `@/Users/harpreet/financeagent/app/services/vector_store.py`

- [ ] **Why Qdrant?**
  - Performance optimized for similarity search
  - Rich metadata filtering
  - Scalability (millions of vectors)
  - Docker-friendly
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:355-360`

### **8.2 Dual Storage Strategy**
- [ ] **PostgreSQL + Qdrant**
  - PostgreSQL: Metadata, full text, analytics
  - Qdrant: Vector search, semantic retrieval
  - Both store text (resilience, no cross-DB lookups)
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:43-68`

---

## 📚 **PART 9: CHUNKING STRATEGY**

### **9.1 Document Chunking**
- [ ] **Configuration**
  - Chunk size: 2,048 characters (production)
  - Overlap: 300 characters
  - RecursiveCharacterTextSplitter
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:113-132`

- [ ] **Split Hierarchy**
  - Paragraph breaks (`\n\n`)
  - Line breaks (`\n`)
  - Sentence ends (`. `)
  - Word boundaries (` `)
  - Characters (last resort)

- [ ] **Why 2,048 characters?**
  - Leverages 25% of nomic's 8K context
  - Preserves financial tables intact
  - Reduces total chunks (better coherence)
  - Memory safe (~512 tokens per chunk)

---

## 📚 **PART 10: PARSING & DATA PREPARATION**

### **10.1 SEC Filing Processing**
- [ ] **Pipeline Stages**
  - Download from SEC EDGAR
  - HTML parsing (BeautifulSoup4)
  - Section extraction
  - Table preservation
  - Chunking
  - Embedding generation
  - Storage (PostgreSQL + Qdrant)
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/data_prep_service.py`

- [ ] **Idempotency**
  - Check if filing exists before processing
  - Avoid duplicate downloads
  - Safe to call repeatedly
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/data_prep_service.py:199-248`

---

## 📚 **PART 11: INFERENCE OPTIMIZATION**

### **11.1 Infrastructure Bottlenecks**
- [ ] **Docker GPU Passthrough**
  - macOS: No GPU support (CPU-only)
  - Linux: NVIDIA GPU support
  - Native Ollama on Mac: Metal GPU (6x faster)
  - **Docs**: `@/Users/harpreet/financeagent/docs/PRESENTATION_OUTLINE.md:624-677`

### **11.2 vLLM Migration (Planned)**
- [ ] **Why vLLM?**
  - PagedAttention (efficient KV cache management)
  - Continuous batching (2-3x throughput)
  - Prefix caching
  - OpenAI-compatible API
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2.2/Inference_Improvement.md:19-104`

- [ ] **LMCache Integration (Planned)**
  - RAG-optimized caching
  - 3-5x TTFT reduction
  - CPU offloading for KV cache
  - Non-prefix caching
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2.2/Inference_Improvement.md:106-191`

### **11.3 Key Concepts**
- [ ] **PagedAttention Algorithm**
  - Treats KV cache like OS virtual memory
  - Paging mechanism
  - Efficient memory management
  - **Paper**: https://arxiv.org/abs/2309.06180

- [ ] **Continuous Batching**
  - Dynamic request batching
  - Add/remove requests on-the-fly
  - Higher GPU utilization
  - Lower latency

- [ ] **KV Cache Bottleneck**
  - Memory constraint in LLMs
  - 70B model: ~1GB per 1K tokens
  - Cache hierarchy: GPU → CPU → Disk

---

## 📚 **PART 12: STREAMING & REAL-TIME UPDATES**

### **12.1 Server-Sent Events (SSE)**
- [ ] **Implementation**
  - Real-time log streaming
  - Progress tracking (planning → fetching → synthesis)
  - Token streaming
  - Source availability notifications
  - **Implementation**: `@/Users/harpreet/financeagent/app/agents/supervisor.py:309-547`

- [ ] **Event Types**
  - `step_start`: New stage beginning
  - `tool_start`: Tool execution started
  - `tool_end`: Tool execution completed
  - `token`: Individual token (for text streaming)
  - `complete_structured`: Full structured response
  - `sources_ready`: Citations available
  - `error`: Error occurred

---

## 📚 **PART 13: TESTING & EVALUATION**

### **13.1 Playwright Testing**
- [ ] **End-to-End Testing**
  - Browser automation
  - Real Chromium browser
  - Structured DOM snapshots
  - Integration testing (LLM → Backend → Frontend → UI)
  - **Docs**: `@/Users/harpreet/financeagent/docs/PLAYWRIGHT_TESTING_GUIDE.md`

- [ ] **Benefits**
  - 2-minute verification vs 5-minute manual testing
  - Catches integration bugs unit tests miss
  - Regression testing (just re-run)
  - **Docs**: `@/Users/harpreet/financeagent/docs/PRESENTATION_OUTLINE.md:774-846`

### **13.2 Evaluation Strategy**
- [ ] **LLM-as-Judge**
  - Factual accuracy scoring
  - Citation quality
  - Completeness assessment
  - **Docs**: `@/Users/harpreet/financeagent/docs/v2/04_TESTING_AND_EVALUATION_STRATEGY.md`

- [ ] **Metrics**
  - Success rate (10/10 queries)
  - Accuracy score (keyword matching)
  - Response time (P50, P95, P99)
  - Token usage

---

## 📚 **PART 14: MONITORING & OBSERVABILITY**

### **14.1 Logging**
- [ ] **Structured Logging**
  - JSON format
  - Context: user_id, session_id, agent_name, step
  - Token usage tracking
  - Latency measurement
  - **Implementation**: Throughout codebase

- [ ] **Token Metrics**
  - Per-stage tracking (supervisor, planner, synthesizer)
  - Total tokens per query (~2,725 tokens)
  - Cost estimation
  - **Implementation**: `@/Users/harpreet/financeagent/app/utils/token_metrics.py`

### **14.2 Metrics to Track**
- [ ] **Performance**
  - Average response time
  - Trimming frequency
  - Max tokens seen
  - P95 latency

- [ ] **Quality**
  - Accuracy rate
  - Hallucination detection
  - Citation completeness

- [ ] **Cost**
  - Tokens per query
  - API costs (if using paid LLMs)
  - GPU utilization

---

## 📚 **PART 15: DEPLOYMENT & INFRASTRUCTURE**

### **15.1 Docker Compose**
- [ ] **Services**
  - PostgreSQL (metadata + checkpoints)
  - Qdrant (vector search)
  - Ollama (LLM inference)
  - Redis (caching)
  - Backend (FastAPI)
  - Frontend (React + Nginx)
  - **Config**: `docker-compose.prod.yml`

### **15.2 Production Considerations**
- [ ] **Scaling**
  - Horizontal scaling (multiple uvicorn workers)
  - GPU server for Ollama
  - Managed databases (RDS, Qdrant Cloud)
  - **Docs**: `@/Users/harpreet/financeagent/docs/DEPLOYMENT.md`

- [ ] **Security**
  - API key authentication
  - Rate limiting
  - CORS configuration
  - Environment variable secrets
  - **Docs**: `@/Users/harpreet/financeagent/docs/SECURITY.md`

---

## 📚 **PART 16: PROMPT ENGINEERING**

### **16.1 Prompt Organization**
- [ ] **Separation of Concerns**
  - Prompts in separate files (`prompts/` directory)
  - Never hardcode in Python
  - Version control alongside code
  - **Pattern**: `Path(__file__).parent.parent / "prompts" / "supervisor.txt"`

### **16.2 Prompt Techniques**
- [ ] **Few-Shot Examples**
  - Concrete examples in planner prompt
  - 60% reduction in malformed queries
  - **Implementation**: Planner prompt file

- [ ] **Structured Instructions**
  - Clear output format
  - Negative examples (what NOT to do)
  - XML tags for parsing
  - Citation requirements

---

## 📚 **PART 17: ERROR HANDLING & RESILIENCE**

### **17.1 Graceful Degradation**
- [ ] **Missing Data Handling**
  - Explain what's missing
  - Suggest alternatives
  - Partial results better than nothing
  - **Implementation**: Throughout tools

- [ ] **Retry Logic**
  - Exponential backoff
  - Circuit breakers
  - Timeout handling
  - **Pattern**: Wrap tool calls in try-except

### **17.2 JSON Parsing Recovery**
- [ ] **Malformed JSON Handling**
  - Attempt repair (add closing braces)
  - Extract content fields with regex
  - Fallback to readable text
  - **Implementation**: `@/Users/harpreet/financeagent/app/tools/filing_qa_tool.py:608-777`

---

## 📚 **PART 18: CONFIGURATION MANAGEMENT**

### **18.1 Environment Variables**
- [ ] **Required Settings**
  - `DATABASE_URL`: PostgreSQL connection
  - `SEC_USER_AGENT`: Email for SEC API
  - `OLLAMA_BASE_URL`: LLM endpoint
  - **Config**: `@/Users/harpreet/financeagent/app/core/config.py`

- [ ] **Model Configuration**
  - `SUPERVISOR_MODEL`: llama3.1:8b
  - `PLANNER_MODEL`: llama3.1:8b
  - `SYNTHESIZER_MODEL`: llama3.1:8b
  - `EMBEDDING_MODEL`: nomic-embed-text-v1.5

- [ ] **RAG Settings**
  - `CHUNK_SIZE`: 2048
  - `CHUNK_OVERLAP`: 300
  - `TOP_K`: 5
  - `SCORE_THRESHOLD`: 0.5
  - `MAX_CONVERSATION_TOKENS`: 6000

---

## 📚 **PART 19: LLM PROVIDER ABSTRACTION**

### **19.1 LLM Factory Pattern**
- [ ] **Dual Provider Support**
  - Ollama (local)
  - vLLM (production)
  - OpenAI-compatible API
  - **Implementation**: `@/Users/harpreet/financeagent/app/utils/llm_factory.py`

- [ ] **Configuration**
  - `LLM_PROVIDER`: "ollama" or "vllm"
  - Automatic endpoint switching
  - Structured output support (Ollama only)

---

## 📚 **PART 20: KEY LEARNINGS & DECISIONS**

### **20.1 Architecture Decisions**
- [ ] **Simplicity Wins**
  - Data structure change > Complex architecture
  - Deterministic > LLM where possible
  - Test before redesigning
  - **Docs**: `@/Users/harpreet/financeagent/docs/Architecture.md:848-975`

- [ ] **Performance Optimization**
  - Infrastructure first (GPU access)
  - Token management (O(n²) complexity)
  - Caching strategies
  - **Docs**: Multiple locations

### **20.2 Production Lessons**
- [ ] **Data Safety**
  - Never recommend destructive commands
  - Always provide backup steps
  - Warn about consequences
  - **Docs**: `@/Users/harpreet/financeagent/docs/DATA_SAFETY_RULES.md`

- [ ] **Incremental Development**
  - Ship fast, iterate
  - 90% solution > 100% delayed
  - User feedback drives features

---

## 🎯 **STUDY PRIORITY MATRIX**

### **Critical (Must Know for Interviews)**
1. ✅ Multi-agent architecture (LangGraph)
2. ✅ RAG pipeline (embedding → search → generation)
3. ✅ Checkpointing (AsyncPostgresSaver)
4. ✅ Context window management (token trimming)
5. ✅ Structured outputs (Pydantic + Ollama)
6. ✅ Model benchmarking results
7. ✅ Data structure decisions (dict vs list)

### **Important (Deep Understanding)**
8. ✅ Deterministic vs LLM decisions
9. ✅ Prompt engineering patterns
10. ✅ Vector databases (Qdrant)
11. ✅ Chunking strategies
12. ✅ Error handling & resilience
13. ✅ Streaming (SSE)
14. ✅ Session management

### **Good to Know (Production Skills)**
15. ✅ Docker deployment
16. ✅ Monitoring & observability
17. ✅ Testing strategies (Playwright)
18. ✅ Security considerations
19. ✅ Infrastructure optimization (GPU)
20. ✅ vLLM & LMCache (future)

---

## 📖 **RECOMMENDED READING ORDER**

1. **Start Here**: `@/Users/harpreet/financeagent/docs/v2/00_START_HERE_ROADMAP.md`
2. **Architecture**: `@/Users/harpreet/financeagent/docs/Architecture.md`
3. **Framework Choice**: `@/Users/harpreet/financeagent/docs/v2/01_FRAMEWORK_COMPARISON_AND_RECOMMENDATION.md`
4. **Checkpointing**: `@/Users/harpreet/financeagent/docs/v2/08_CHECKPOINT_AND_SESSION_MANAGEMENT.md`
5. **Model Analysis**: `@/Users/harpreet/financeagent/docs/v2/11_MODEL_PERFORMANCE_ANALYSIS.md`
6. **Comparison Feature**: `@/Users/harpreet/financeagent/docs/v2.1/COMPARATIVE_ANALYSIS_FEATURE_DECISION.md`
7. **Inference Optimization**: `@/Users/harpreet/financeagent/docs/v2.2/Inference_Improvement.md`
8. **Presentation**: `@/Users/harpreet/financeagent/docs/PRESENTATION_OUTLINE.md`

---

## 🔗 **EXTERNAL RESOURCES TO STUDY**

### **Papers**
- vLLM: https://arxiv.org/abs/2309.06180
- CacheBlend: https://dl.acm.org/doi/10.1145/3689031.3696098
- Attention is All You Need: https://arxiv.org/abs/1706.03762

### **Documentation**
- LangGraph: https://langchain-ai.github.io/langgraph/
- Anthropic Multi-Agent: https://www.anthropic.com/engineering/multi-agent-research-system
- Ollama: https://ollama.ai/
- Qdrant: https://qdrant.tech/documentation/

### **Blogs**
- vLLM Blog: https://blog.vllm.ai/
- LangChain Blog: https://blog.langchain.com/

---

This study guide covers **every major concept, decision, and implementation detail** in your financeagent project. Use it as a checklist to systematically understand each component!