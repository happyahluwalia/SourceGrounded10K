# Ollama Setup Guide (Docker)

## Quick Start

### 1. Start Ollama Container

```bash
# Start Ollama (and all other services)
docker compose up -d

# Or start just Ollama
docker compose up -d ollama

# Check if it's running
docker ps | grep ollama
```

### 2. Download a Model

Once the container is running, download a model:

```bash
# Download gemma3:1b (recommended - small and fast)
docker exec -it financeagent_ollama ollama pull gemma3:1b

# Or download other models:
docker exec -it financeagent_ollama ollama pull llama3.2:1b    # Llama 3.2 1B
docker exec -it financeagent_ollama ollama pull phi3:mini      # Microsoft Phi-3
docker exec -it financeagent_ollama ollama pull mistral:7b     # Mistral 7B (larger, better quality)
```

### 3. Verify Model is Downloaded

```bash
# List all downloaded models
docker exec -it financeagent_ollama ollama list

# Expected output:
# NAME              ID              SIZE      MODIFIED
# gemma3:1b         abc123def       1.2 GB    2 minutes ago
```

### 4. Test the Model

```bash
# Test with a simple prompt
docker exec -it financeagent_ollama ollama run gemma3:1b "Hello, how are you?"

# You should see a response from the model
```

---

## Model Recommendations

### For Development (Fast):
- **gemma3:1b** (1.2 GB) - Google's Gemma, very fast
- **llama3.2:1b** (1.3 GB) - Meta's Llama, good quality
- **phi3:mini** (2.3 GB) - Microsoft's Phi-3, excellent reasoning

### For Production (Better Quality):
- **mistral:7b** (4.1 GB) - Great balance of speed and quality
- **llama3.1:8b** (4.7 GB) - Meta's latest, very capable
- **gemma2:9b** (5.4 GB) - Google's Gemma 2, excellent quality

### For Best Results (Requires More RAM):
- **llama3.1:70b** (40 GB) - State-of-the-art, needs powerful hardware
- **mixtral:8x7b** (26 GB) - Mixture of experts, very capable

---

## Common Commands

### Download a Model
```bash
docker exec -it financeagent_ollama ollama pull <model-name>
```

### List Downloaded Models
```bash
docker exec -it financeagent_ollama ollama list
```

### Delete a Model
```bash
docker exec -it financeagent_ollama ollama rm <model-name>
```

### Check Model Info
```bash
docker exec -it financeagent_ollama ollama show <model-name>
```

### Interactive Chat (for testing)
```bash
docker exec -it financeagent_ollama ollama run gemma3:1b
# Type your messages, press Ctrl+D to exit
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs financeagent_ollama

# Restart container
docker compose restart ollama
```

### Model Download Fails
```bash
# Check internet connection
curl -I https://ollama.ai

# Check disk space
docker system df

# Try pulling again
docker exec -it financeagent_ollama ollama pull gemma3:1b
```

### Out of Memory
```bash
# Check container memory
docker stats financeagent_ollama

# Use a smaller model
docker exec -it financeagent_ollama ollama pull gemma3:1b  # Only 1.2 GB
```

---

## Changing the Model in Your App

After downloading a different model, update your `.env` file:

```bash
# Edit .env
LLM_MODEL=mistral:7b  # Change to your preferred model
```

Or set it in your environment:
```bash
export LLM_MODEL=mistral:7b
```

Then restart your backend:
```bash
uvicorn app.api.main:app --reload
```

---

## Storage Location

Models are stored in a Docker volume:
```bash
# View volume info
docker volume inspect financeagent_ollama_data

# Models persist across container restarts
# To completely remove models, delete the volume:
docker volume rm financeagent_ollama_data
```

---

## Performance Tips

1. **Start with small models** (1-3B parameters) for development
2. **Use larger models** (7B+) for production if you have the resources
3. **Models are cached** - first run is slow, subsequent runs are fast
4. **GPU acceleration** - If you have an NVIDIA GPU, Ollama will use it automatically
5. **Apple Silicon** - Ollama uses Metal acceleration on M1/M2/M3 Macs

---

## Next Steps

1. ✅ Start Ollama: `docker compose up -d ollama`
2. ✅ Download model: `docker exec -it financeagent_ollama ollama pull gemma3:1b`
3. ✅ Verify: `docker exec -it financeagent_ollama ollama list`
4. ✅ Run quick start: `./scripts/quick_start.sh`
5. ✅ Start backend: `uvicorn app.api.main:app --reload`
6. ✅ Start frontend: `cd frontend && npm run dev`

---

**You're all set! 🚀**
