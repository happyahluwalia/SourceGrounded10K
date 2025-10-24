# Finance Agent 🤖📊

An AI-powered financial research assistant that analyzes SEC filings using Retrieval-Augmented Generation (RAG). Ask natural language questions about any company's financial data and get accurate, source-cited answers.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.119+-green.svg)
![React](https://img.shields.io/badge/React-18.3+-blue.svg)

## ✨ Features

- **🔍 Semantic Search**: Ask questions in natural language about company financials
- **📄 SEC Filing Analysis**: Automatically fetches and processes 10-K, 10-Q filings
- **🎯 Source Citations**: Every answer includes the exact document chunks used
- **💬 Modern Chat UI**: ChatGPT-like interface with message history
- **🐛 Debug Panel**: Toggle-able view showing RAG pipeline logs in real-time
- **⚡ Fast Processing**: First query ~30s (includes fetching), subsequent queries ~2s
- **🔄 Auto-Caching**: Smart caching prevents duplicate SEC API calls

## 🎥 Demo

```bash
# Ask a question
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were Apple'\''s revenues last year?",
    "ticker": "AAPL"
  }'

# Response includes answer + sources with similarity scores
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- 8GB+ RAM recommended

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# Run quick start script
chmod +x scripts/quick_start.sh
./scripts/quick_start.sh
```

This will:
1. Start all Docker services (Postgres, Qdrant, Ollama)
2. Initialize databases
3. Download the LLM model
4. Verify all services are healthy

### Manual Setup

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your SEC_USER_AGENT email

# 2. Start services
docker compose up -d

# 3. Initialize databases
python -c "from app.models.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 4. Download Ollama models
# Development (lightweight)
docker exec -it financeagent_ollama ollama pull gemma3:1b

# Production (recommended for deployment)
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct
docker exec -it financeagent_ollama ollama pull nomic-embed-text

# 5. Start backend
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (in new terminal)
cd frontend
npm install
npm run dev
```

### Access the Application

- **Frontend UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 📖 Usage

### Web UI

1. Open http://localhost:3000
2. Enter a ticker symbol (e.g., AAPL, TSLA, GOOG)
3. Ask a question about the company
4. Toggle "Debug Logs" to see the RAG pipeline in action

### CLI

```bash
# Ask a question
python cli/client.py ask "What were the revenues?" --ticker AAPL

# List available companies
python cli/client.py list-companies

# Process a new company
python cli/client.py process MSFT --filing-type 10-K
```

### API

```python
import requests

response = requests.post('http://localhost:8000/api/query', json={
    'query': 'What were the total revenues?',
    'ticker': 'AAPL',
    'filing_type': '10-K'
})

print(response.json()['answer'])
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  Chat UI + Debug Panel + Source Citations               │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RAG Pipeline                                     │   │
│  │  1. Query → Embedding                             │   │
│  │  2. Vector Search (Qdrant)                        │   │
│  │  3. Retrieve Top-K Chunks                         │   │
│  │  4. LLM Generation (Ollama)                       │   │
│  │  5. Return Answer + Sources                       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────┬──────────────────┬──────────────────┬─────────┘
          │                  │                  │
    ┌─────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
    │ Postgres  │      │  Qdrant  │      │  Ollama  │
    │ (Metadata)│      │ (Vectors)│      │  (LLM)   │
    └───────────┘      └──────────┘      └──────────┘
```

### Tech Stack

**Backend:**
- FastAPI - Modern async Python web framework
- Qdrant - Vector database for semantic search
- PostgreSQL - Relational database for metadata
- Ollama - Local LLM inference
  - **Development**: gemma3:1b (lightweight testing)
  - **Production**: phi3:mini-instruct (3.8B params, stable on 8GB RAM)
- Embeddings:
  - **Development**: BGE-large-en-v1.5 (1024-dim)
  - **Production**: nomic-embed-text-v1.5 (768-dim, 8K context)

**Frontend:**
- React 18 - UI framework
- Vite - Build tool
- TailwindCSS - Styling
- Lucide React - Icons

**Infrastructure:**
- Docker Compose - Local development
- GitHub Actions - CI/CD
- Nginx - Reverse proxy (production)

## 🌐 Deployment

Deploy to cloud platforms with one command:

### Digital Ocean (8GB Droplet)

**Production-ready configuration included!**

See detailed guide: [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)

Quick reference: [docs/QUICK_DEPLOY_REFERENCE.md](docs/QUICK_DEPLOY_REFERENCE.md)

```bash
# Pull production models
docker exec -it financeagent_ollama ollama pull nomic-embed-text
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct

# Deploy
doctl apps create --spec app.yaml
```

### Railway

```bash
railway up
```

### Render

```bash
# Connect your GitHub repo in Render dashboard
# Blueprint will auto-deploy from render.yaml
```

### Self-Hosted

```bash
docker compose -f docker-compose.prod.yml up -d
```

See deployment guides:
- **[SERVER_SETUP_GUIDE.md](docs/SERVER_SETUP_GUIDE.md)** - Complete server setup (Docker, Nginx, SSL, security)
- **[SERVER_SPECS.md](docs/SERVER_SPECS.md)** - GPU server specifications and deployment
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - General deployment guide (Digital Ocean, Railway, Render)
- [GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md) - Automated CI/CD deployment
- [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) - Full production guide
- [QUICK_DEPLOY_REFERENCE.md](docs/QUICK_DEPLOY_REFERENCE.md) - Quick reference commands
- [MODEL_SELECTION_ANALYSIS.md](docs/MODEL_SELECTION_ANALYSIS.md) - Model selection rationale

## 📊 Performance

**Development (gemma3:1b, BGE embeddings):**
- **First query** (new company): 30-60s (includes SEC fetch + processing)
- **Subsequent queries**: 1-3s (cached in vector DB)
- **Embedding generation**: ~30s for 500 chunks
- **Vector search**: <100ms
- **LLM generation**: 1-2s

**Production (phi3:mini-instruct, nomic embeddings):**
- **First query**: 40-80s (higher quality processing)
- **Subsequent queries**: 3-5s (better reasoning)
- **Embedding generation**: ~40-50s for 500 chunks
- **Vector search**: <100ms
- **LLM generation**: 3-5s (higher quality answers)

## 🔧 Configuration

Key environment variables:

```bash
# Required
SEC_USER_AGENT=your-email@example.com  # SEC API compliance

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/financeagent
QDRANT_HOST=localhost
QDRANT_PORT=6333

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini-instruct  # Production (gemma3:1b for dev)

# Embeddings
EMBEDDING_MODEL=nomic-embed-text-v1.5  # Production
EMBEDDING_DIMENSION=768

# RAG Settings
CHUNK_SIZE=2048  # Increased for production (512 for dev)
CHUNK_OVERLAP=300
TOP_K=5
SCORE_THRESHOLD=0.5
```

## 🧪 Testing

```bash
# Run tests
pytest

# Check service health
curl http://localhost:8000/api/health

# Verify signatures
python verify_signatures.py
```

## 📝 Project Status

**Current Status**: Day 5 - Production-Ready MVP ✅

**Completed:**
- ✅ SEC filing fetching and parsing
- ✅ Document chunking and embedding
- ✅ Vector storage (Qdrant)
- ✅ RAG pipeline with LLM
- ✅ FastAPI REST API
- ✅ CLI interface
- ✅ Modern React chat UI
- ✅ Debug panel with logs
- ✅ Docker deployment
- ✅ Cloud deployment configs

**Next Steps:**
- [ ] WebSocket support for real-time logs
- [ ] Multi-company comparative analysis
- [ ] Streaming responses
- [ ] Authentication & rate limiting
- [ ] Advanced analytics dashboard

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- SEC EDGAR for public financial data
- Qdrant for vector search
- Ollama for local LLM inference
- FastAPI for the excellent web framework

## 📧 Contact

Questions? Open an issue or reach out on Twitter [@yourusername](https://twitter.com/yourusername)

---

**Built with ❤️ for financial transparency and AI-powered research**