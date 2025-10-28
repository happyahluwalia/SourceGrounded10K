# Deployment Guide

Complete guide for deploying Finance Agent to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deploy (GPU Server)](#quick-deploy-gpu-server)
- [Digital Ocean Droplet](#digital-ocean-droplet)
- [Cloud Platforms](#cloud-platforms)
- [Docker Compose (Self-Hosted)](#docker-compose-self-hosted)
- [Configuration](#configuration)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

**Required:**
- SEC User Agent email (SEC API compliance)
- Server with 8GB+ RAM (16GB recommended for Llama 3.1)
- Docker & Docker Compose
- Domain name (optional, for SSL)

**For GPU deployment:**
- NVIDIA GPU with 8GB+ VRAM
- CUDA 11.0+
- nvidia-docker2

---

## Quick Deploy (GPU Server)

### Automated Setup

```bash
# 1. SSH into server
ssh user@your-server-ip

# 2. Download and run provisioning script
wget https://raw.githubusercontent.com/yourusername/financeagent/main/scripts/provision_server.sh
chmod +x provision_server.sh
./provision_server.sh

# 3. Log out and back in (for docker group)
exit
ssh user@your-server-ip

# 4. Clone and deploy
git clone https://github.com/yourusername/financeagent.git
cd financeagent
./scripts/gpu_deploy.sh
```

**Provisioning includes:**
- Docker + Docker Compose + nvidia-docker2
- Nginx + SSL (Certbot)
- UFW firewall + Fail2Ban
- Security patches + auto-updates
- System optimizations

**Time:** ~15-20 minutes

---

## Digital Ocean Droplet

### Server Specs

| Tier | RAM | vCPU | Cost/mo | Use Case |
|------|-----|------|---------|----------|
| Basic | 4GB | 2 | $24 | Development only |
| **Recommended** | **8GB** | **4** | **$48** | **Production (Phi-3)** |
| High-end | 16GB | 8 | $96 | Production (Llama 3.1) |

### Step-by-Step Setup

#### 1. Create Droplet

```bash
# Via doctl CLI
doctl compute droplet create financeagent \
  --image ubuntu-22-04-x64 \
  --size s-4vcpu-8gb \
  --region nyc1 \
  --ssh-keys YOUR_SSH_KEY_ID

# Or use Digital Ocean web console
```

#### 2. Initial Server Setup

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# (Optional) Install nvidia-docker for GPU
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  tee /etc/apt/sources.list.d/nvidia-docker.list
apt update && apt install -y nvidia-docker2
systemctl restart docker
```

#### 3. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# Copy and configure environment
cp .env.production.example .env
nano .env  # Edit with your values

# Start services
docker compose -f docker-compose.prod.yml up -d

# Pull Ollama models
docker exec -it financeagent_ollama ollama pull nomic-embed-text
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct

# Verify deployment
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8000/api/health
```

#### 4. Setup Nginx & SSL

```bash
# Install Nginx
apt install nginx certbot python3-certbot-nginx -y

# Copy Nginx config
cp nginx.conf /etc/nginx/sites-available/financeagent
ln -s /etc/nginx/sites-available/financeagent /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Update domain in config
nano /etc/nginx/sites-available/financeagent
# Replace yourdomain.com with your actual domain

# Test and reload
nginx -t
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 5. Setup Firewall

```bash
# Configure UFW
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Install Fail2Ban (SSH protection)
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

---

## Cloud Platforms

### Railway

**Pros:** Simple, auto-scaling, managed databases  
**Cons:** More expensive, no GPU support

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Cost:** ~$20-30/month (without Ollama, use OpenAI API instead)

### Render

**Pros:** Free tier available, auto-deploy from GitHub  
**Cons:** Limited resources, no GPU

```bash
# Deploy via render.yaml (included in repo)
# 1. Connect GitHub repo in Render dashboard
# 2. Render auto-detects render.yaml
# 3. Add environment variables
# 4. Deploy
```

**Cost:** Free tier (limited), $7+/month for production

### Google Cloud / AWS / Azure

See cloud-specific guides in `docs/cloud/` directory.

---

## Docker Compose (Self-Hosted)

### Development

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Production

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d

# With GPU support
docker compose -f docker-compose.prod.yml --profile gpu up -d

# View resource usage
docker stats
```

---

## Configuration

### Environment Variables

**Required:**
```bash
SEC_USER_AGENT=your-email@example.com
DATABASE_URL=postgresql://user:pass@postgres:5432/financeagent
QDRANT_HOST=qdrant
OLLAMA_BASE_URL=http://ollama:11434
```

**Model Configuration:**
```bash
# Embeddings
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_DIMENSION=768

# LLM (choose one)
OLLAMA_MODEL=phi3:mini-instruct      # Recommended (8GB RAM)
# OLLAMA_MODEL=llama3.1:8b-instruct  # Better quality (16GB RAM)
# OLLAMA_MODEL=gemma3:1b             # Development only
```

**RAG Settings:**
```bash
CHUNK_SIZE=2048
CHUNK_OVERLAP=300
TOP_K=5
SCORE_THRESHOLD=0.3
MAX_TOKENS=500
```

**Security:**
```bash
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
API_KEY=your-secret-api-key
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

### Model Selection Guide

| Model | RAM | VRAM | Quality | Speed | Use Case |
|-------|-----|------|---------|-------|----------|
| gemma3:1b | 2GB | - | Basic | Fast | Development |
| **phi3:mini** | **3GB** | - | **Good** | **Medium** | **Production (8GB)** |
| llama3.1:8b | 6GB | - | Better | Slow | Production (16GB) |
| llama3.1:8b | - | 8GB | Better | Fast | GPU server |

### Memory Budget (8GB Server)

```
Component               Memory    Notes
────────────────────────────────────────────────────────
System/OS               500 MB    Base Ubuntu
PostgreSQL              300 MB    Metadata storage
Qdrant (10K vectors)    500 MB    768-dim embeddings
Redis                   100 MB    Caching
Nginx                    50 MB    Reverse proxy
────────────────────────────────────────────────────────
Infrastructure Total   1.45 GB

Available for Ollama   6.55 GB
────────────────────────────────────────────────────────
Phi-3 Mini:            3.0 GB    ✅ Safe (3.5GB buffer)
Llama 3.1:             6.0 GB    ⚠️ Risky (0.5GB buffer)
```

---

## Post-Deployment

### Verification Checklist

```bash
# 1. Check all services are running
docker compose ps

# 2. Verify health endpoint
curl http://localhost:8000/api/health

# 3. Check Ollama models
docker exec -it financeagent_ollama ollama list

# 4. Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "ticker": "AAPL"}'

# 5. Check logs for errors
docker compose logs --tail=100

# 6. Monitor memory usage
docker stats --no-stream
```

### Monitoring

**Docker Stats:**
```bash
# Real-time resource monitoring
docker stats

# Expected memory usage:
# - ollama: 3-6GB (depending on model)
# - postgres: 200-400MB
# - qdrant: 300-600MB
# - backend: 100-300MB
```

**Logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

**Health Checks:**
```bash
# API health
curl http://localhost:8000/api/health

# Qdrant health
curl http://localhost:6333/health

# PostgreSQL
docker exec financeagent_postgres pg_isready -U postgres
```

### Backup Strategy

**Database Backup:**
```bash
# PostgreSQL
docker exec financeagent_postgres pg_dump -U postgres financeagent > backup.sql

# Restore
docker exec -i financeagent_postgres psql -U postgres financeagent < backup.sql
```

**Qdrant Backup:**
```bash
# Create snapshot
curl -X POST http://localhost:6333/collections/financial_filings/snapshots

# Download snapshot
curl http://localhost:6333/collections/financial_filings/snapshots/snapshot_name \
  -o qdrant_backup.snapshot
```

**Ollama Models:**
```bash
# Models persist in Docker volume
docker volume inspect financeagent_ollama_data

# Backup volume
docker run --rm -v financeagent_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_models.tar.gz /data
```

### Auto-Updates

**Setup automatic security updates:**
```bash
# Install unattended-upgrades
apt install unattended-upgrades -y

# Configure
dpkg-reconfigure --priority=low unattended-upgrades
```

**Docker image updates:**
```bash
# Pull latest images
docker compose pull

# Recreate containers
docker compose up -d --force-recreate
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
docker compose logs

# Restart services
docker compose restart

# Full restart
docker compose down && docker compose up -d
```

#### Out of Memory

```bash
# Check memory usage
docker stats

# Solutions:
# 1. Switch to smaller model
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct
# Update .env: OLLAMA_MODEL=phi3:mini-instruct
docker compose restart backend

# 2. Increase swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

#### Ollama Model Not Found

```bash
# List models
docker exec -it financeagent_ollama ollama list

# Pull missing model
docker exec -it financeagent_ollama ollama pull nomic-embed-text
docker exec -it financeagent_ollama ollama pull phi3:mini-instruct

# Verify
docker exec -it financeagent_ollama ollama list
```

#### Qdrant Collection Error

```bash
# Delete and recreate collection
curl -X DELETE http://localhost:6333/collections/financial_filings

# Restart backend (will recreate collection)
docker compose restart backend
```

#### SSL Certificate Issues

```bash
# Renew certificate
certbot renew

# Test renewal
certbot renew --dry-run

# Force renewal
certbot renew --force-renewal
```

#### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Performance Optimization

**Increase uvicorn workers:**
```yaml
# docker-compose.prod.yml
command: uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**PostgreSQL tuning:**
```bash
# Edit postgresql.conf
docker exec -it financeagent_postgres bash
nano /var/lib/postgresql/data/postgresql.conf

# Increase connections and memory
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
```

**Qdrant optimization:**
```bash
# Increase HNSW parameters for better search quality
# (at the cost of memory)
curl -X PATCH http://localhost:6333/collections/financial_filings \
  -H "Content-Type: application/json" \
  -d '{
    "hnsw_config": {
      "m": 32,
      "ef_construct": 200
    }
  }'
```

### Getting Help

- **Logs**: Always check `docker compose logs` first
- **Health endpoint**: `curl http://localhost:8000/api/health`
- **GitHub Issues**: Open an issue with logs and configuration
- **Documentation**: See other guides in `docs/` directory

---

## Next Steps

- **[CONFIGURATION.md](CONFIGURATION.md)** - Detailed configuration options
- **[SECURITY.md](SECURITY.md)** - Security hardening guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture details
- **[QUICKSTART.md](QUICKSTART.md)** - Local development setup

---

**Deployment complete! 🚀**
