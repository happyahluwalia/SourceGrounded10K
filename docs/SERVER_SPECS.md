# RTX 3060 GPU Server Specifications

## Server Details

Your production GPU server has the following specifications:

| Component | Specification | Details |
|-----------|--------------|---------|
| **GPU** | RTX 3060 | 12GB VRAM, 12.0 TFLOPS |
| **CUDA** | 12.4 | Latest CUDA support |
| **VRAM** | 12.0 GB | 0.6 GB used / 12.0 GB total |
| **Memory Bandwidth** | 318.5 GB/s | High-speed memory access |
| **CPU** | AMD EPYC 7402 24-Core | 12/48 cores allocated |
| **RAM** | 32.2 GB | Plenty for all services |
| **Storage** | 75 GB NVMe | 1884.4 MB/s read/write speed |
| **Motherboard** | MZ31-AR0-00 | PCIe 3.0/16x (11.9 GB/s) |
| **Network** | 100 ports | 77.9 Mbps down / 349.3 Mbps up |
| **DLPerf** | 318.5 DLP/$/hr | Deep learning performance metric |

## Recommended Configuration

Based on your 12GB VRAM, the optimal configuration is:

```bash
# LLM Model (uses ~9GB VRAM)
OLLAMA_MODEL=llama3.1:8b-instruct-q8_0

# Embedding Model
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768

# Expected Performance
LLM_SPEED=40-80 tokens/sec
FIRST_QUERY=40-70 seconds (includes SEC filing fetch)
CACHED_QUERY=2-5 seconds
CONCURRENT_USERS=15-25
```

## Deployment

### Quick Start

```bash
# SSH into your server
ssh user@your-server-ip

# Clone repository
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# Run universal GPU deployment script
./scripts/gpu_deploy.sh
```

The script will:
1. Auto-detect your RTX 3060 (12GB VRAM)
2. Select optimal model: `llama3.1:8b-instruct-q8_0`
3. Configure all services
4. Pull Docker images and models
5. Initialize databases
6. Verify deployment

**Time**: 15-20 minutes (mostly downloading models)

### What Gets Deployed

All services run as Docker containers:

| Service | Image | Purpose |
|---------|-------|---------|
| **Backend** | Custom (FastAPI) | API server, RAG pipeline |
| **Frontend** | Custom (React + Nginx) | Web UI |
| **Ollama** | `ollama/ollama:latest` | LLM inference (GPU) |
| **Qdrant** | `qdrant/qdrant:latest` | Vector database |
| **PostgreSQL** | `postgres:15-alpine` | Relational database |

### Resource Usage

Expected resource consumption:

```
GPU VRAM:     9-10 GB / 12 GB (safe buffer)
System RAM:   8-12 GB / 32 GB
Disk Space:   20-25 GB / 75 GB
CPU Usage:    20-40% average
Network:      Minimal (only during SEC fetches)
```

## Automated Deployment

### GitHub Actions

Push to `main` branch triggers automated deployment:

```bash
git add .
git commit -m "Update application"
git push origin main
```

GitHub Actions will:
1. Build Docker images for backend and frontend
2. Push images to GitHub Container Registry
3. SSH into your RTX 3060 server
4. Pull latest images
5. Restart services with zero downtime

### Manual Deployment

If you need to deploy manually:

```bash
# SSH into server
ssh user@your-server-ip
cd financeagent

# Pull latest code
git pull origin main

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Monitoring

### GPU Monitoring

```bash
# Real-time GPU stats
watch -n 1 nvidia-smi

# Detailed monitoring dashboard
./scripts/gpu_monitor.sh
```

### Service Health

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Health endpoints
curl http://localhost:8000/api/health
curl http://localhost:11434/api/tags
curl http://localhost:6333/health
```

## Performance Expectations

With your RTX 3060 (12GB VRAM):

| Metric | Performance |
|--------|-------------|
| **LLM Inference** | 40-80 tokens/sec |
| **First Query** | 40-70 seconds (includes SEC filing fetch) |
| **Cached Queries** | 2-5 seconds |
| **Embedding Generation** | 15-25 seconds (500 chunks) |
| **Concurrent Users** | 15-25 users |
| **VRAM Usage** | 9-10GB / 12GB |
| **GPU Utilization** | 60-90% during inference |

**Comparison to CPU-only**: 10-20x faster! 🚀

## Troubleshooting

### GPU Not Working

```bash
# Check GPU
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Restart Ollama
docker-compose -f docker-compose.prod.yml restart ollama
```

### Out of Memory

```bash
# Switch to smaller model (uses 6GB instead of 9GB)
# Edit .env:
OLLAMA_MODEL=llama3.1:8b-instruct

# Restart
docker-compose -f docker-compose.prod.yml restart ollama backend
```

### Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Rebuild
docker-compose -f docker-compose.prod.yml up -d --build
```

## Security

- [ ] Change default passwords in `.env`
- [ ] Set `SEC_USER_AGENT` with your real email
- [ ] Configure firewall: `sudo ufw enable`
- [ ] Set up SSL/TLS with Let's Encrypt
- [ ] Restrict CORS origins to your domain
- [ ] Enable rate limiting in production
- [ ] Set up automated backups

## Additional Resources

- **Full GPU Guide**: [GPU_DEPLOYMENT.md](GPU_DEPLOYMENT.md)
- **General Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Main README**: [../README.md](../README.md)

---

**Your RTX 3060 server is perfect for this application!** The universal `gpu_deploy.sh` script handles everything automatically.
