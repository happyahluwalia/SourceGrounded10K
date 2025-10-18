# Quick Start Guide

Get Finance Agent running in under 5 minutes!

## 🚀 Fastest Path (Recommended)

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# 2. Set up environment
cp .env.example .env
echo "SEC_USER_AGENT=your-email@example.com" >> .env

# 3. Run the quick start script
chmod +x scripts/quick_start.sh
./scripts/quick_start.sh

# 4. Start the frontend (in a new terminal)
cd frontend
npm install
npm run dev
```

**That's it!** Open http://localhost:3000 and start asking questions.

---

## 📋 What Just Happened?

The quick start script:
1. ✅ Started Docker containers (Postgres, Qdrant, Ollama)
2. ✅ Created database tables
3. ✅ Initialized Qdrant vector collection
4. ✅ Downloaded the gemma3:1b LLM model
5. ✅ Verified all services are healthy

---

## 🎯 Try It Out

### Example 1: Ask About Apple

```
Ticker: AAPL
Question: What were Apple's revenues last year?
```

The system will:
1. Fetch Apple's latest 10-K filing from SEC (~10s)
2. Parse and chunk the document (~5s)
3. Generate embeddings and store in Qdrant (~15s)
4. Answer your question (~2s)

**Total first query: ~30s**

### Example 2: Follow-up Question

```
Ticker: AAPL
Question: What are the main risk factors?
```

**Subsequent queries: ~2s** (already cached!)

### Example 3: Different Company

```
Ticker: TSLA
Question: Who is the CFO?
```

---

## 🐛 Debug Panel

Click the **"Debug Logs"** button in the UI to see:

```
11:47:50 [INFO] Query request: AAPL - What were Apple's revenues...
11:47:50 [INFO] Checking if filing exists locally: AAPL 10-K
11:47:50 [INFO] Embedding 1 texts...
11:47:50 [INFO] HTTP Request: POST http://localhost:6333/collections/financial_filings/points/search
11:47:50 [INFO] Retrieved 5 chunks, 5 above threshold 0.5
11:47:50 [INFO] Generating answer with gemma3:1b...
11:47:52 [INFO] HTTP Request: POST http://127.0.0.1:11434/api/generate
11:47:52 [INFO] Generated answer (135 chars)
11:47:52 [INFO] Completed in 1.83s using 5 sources
```

This shows exactly how the RAG pipeline works!

---

## 🔧 Troubleshooting

### Services Not Starting?

```bash
# Check Docker is running
docker ps

# View logs
docker compose logs -f

# Restart services
docker compose restart
```

### Ollama Model Not Found?

```bash
# Pull the model manually
docker exec -it financeagent_ollama ollama pull gemma3:1b

# Verify it's downloaded
docker exec -it financeagent_ollama ollama list
```

### Frontend Won't Start?

```bash
# Make sure you're in the frontend directory
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database Connection Error?

```bash
# Check Postgres is running
docker exec financeagent_postgres pg_isready -U postgres

# Recreate tables
python -c "from app.models.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

---

## 📊 Service URLs

Once running, access:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Chat UI |
| **API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Qdrant** | http://localhost:6333/dashboard | Vector DB UI |
| **Postgres** | localhost:5432 | Database |
| **Ollama** | http://localhost:11434 | LLM Service |

---

## 🎓 Next Steps

### 1. Process More Companies

```bash
# Via CLI
python cli/client.py process MSFT --filing-type 10-K
python cli/client.py process GOOG --filing-type 10-K

# Via API
curl -X POST http://localhost:8000/api/companies/TSLA/process \
  -H "Content-Type: application/json" \
  -d '{"filing_type": "10-K"}'
```

### 2. Explore the API

Visit http://localhost:8000/docs to see all available endpoints:
- `POST /api/query` - Ask questions
- `GET /api/companies` - List companies
- `GET /api/companies/{ticker}/filings` - Get filings
- `GET /api/health` - Check service health

### 3. Customize Settings

Edit `.env` to change:
- `CHUNK_SIZE` - Size of document chunks (default: 512)
- `TOP_K` - Number of chunks to retrieve (default: 5)
- `SCORE_THRESHOLD` - Minimum similarity score (default: 0.5)
- `LLM_MODEL` - LLM model to use (default: gemma3:1b)

### 4. Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for guides on deploying to:
- Digital Ocean
- Railway
- Render
- Self-hosted VPS

---

## 💡 Tips

1. **First query is slow**: The system fetches and processes the filing. Subsequent queries are fast!
2. **Use specific tickers**: Make sure to use valid stock tickers (AAPL, TSLA, MSFT, etc.)
3. **Ask specific questions**: More specific questions get better answers
4. **Check sources**: Click "View sources" to see the exact document chunks used
5. **Toggle debug logs**: See exactly how the RAG pipeline works

---

## 🆘 Need Help?

- Check the [main README](README.md) for detailed documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guides
- Open an issue on GitHub
- Check Docker logs: `docker compose logs -f`

---

**Happy analyzing! 📊🚀**
