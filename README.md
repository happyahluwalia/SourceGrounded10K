# FinanceAgent

We’re building an AI-driven Financial Research Agent that continuously reads and analyzes public company filings, earnings reports, and real-time news to deliver actionable investment insights.

It combines Retrieval-Augmented Generation (RAG) for deep comprehension of financial documents with autonomous agents that track market signals, summarize sentiment, and reason about potential impacts.

The system uses LangGraph for orchestration, Qdrant + Postgres for context memory, and multi-provider LLMs for reasoning and advice generation.

In essence, it’s a personalized AI analyst that thinks like a research team — monitoring, reasoning, and advising before the market moves.

# Tech Stack

## Final Architecture Blueprint

### Backend:

- FastAPI (API + LangGraph execution)
- LangGraph (agent orchestration)
- Qdrant (vector search)
- Postgres (structured data)
- Redis (cache, message bus)
- APScheduler (background tasks)
- HF Transformers + PEFT (LoRA)

### Frontend:

- Start with Streamlit
- Transition to Reflex (Pythonic web UI)
- Eventual React/Next.js optional

### Runtime:

- Ollama locally, OpenAI/Anthropic remotely
- Containerized with Docker

### CI/CD:

- CI/CD via GitHub Actions

### The migration path that matters:

- Week 2: All local (Docker Compose)
- Week 3: Add cloud LLM providers  
- Week 4: Migrate to LangGraph
- Week 5: Add managed vector DB
- Week 6: Professional frontend (if needed)