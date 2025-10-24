# 🚀 Finance Agent Deployment Checklist

This document ensures a smooth, error-free deployment every time.

## ✅ Pre-Deployment Checklist

### 1. Server Requirements
- [ ] Ubuntu 22.04 LTS
- [ ] NVIDIA GPU with 8GB+ VRAM
- [ ] NVIDIA drivers installed (`nvidia-smi` works)
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Git installed

### 2. Domain Setup (if using custom domain)
- [ ] Domain registered (e.g., 10kiq.com)
- [ ] Cloudflare account created
- [ ] Domain added to Cloudflare
- [ ] Cloudflare Tunnel created
- [ ] DNS records configured (CNAME to tunnel)

### 3. Server Access
- [ ] SSH access configured
- [ ] Non-root user created (e.g., `deployer`)
- [ ] User added to `docker` and `sudo` groups

---

## 📋 Deployment Steps

### Step 1: Initial Server Provisioning (One-Time)

```bash
# SSH as root
ssh root@YOUR_SERVER_IP

# Clone repository
git clone https://YOUR_PAT@github.com/yourusername/financeagent.git
cd financeagent

# Run provisioning script (installs Docker, NVIDIA runtime, Nginx, etc.)
./scripts/provision_server.sh

# Switch to deployer user
su - deployer
cd financeagent
```

**What this does:**
- ✅ Installs Docker & Docker Compose
- ✅ Installs NVIDIA Docker Toolkit
- ✅ Configures Docker daemon for GPU access
- ✅ Installs Nginx
- ✅ Configures firewall (UFW)
- ✅ Sets up Fail2Ban
- ✅ Creates deployer user

---

### Step 2: Configure Environment

```bash
# The gpu_deploy.sh script will:
# 1. Copy .env.production.example to .env
# 2. Auto-configure GPU settings
# 3. Generate secure passwords
# 4. Prompt you to set SEC_USER_AGENT

# Just make sure to set your email in SEC_USER_AGENT when prompted
```

**Environment variables auto-configured:**
- ✅ `DOMAIN` - Your domain (e.g., 10kiq.com)
- ✅ `VITE_API_URL` - Frontend API URL (/api)
- ✅ `OLLAMA_MODEL` - Based on GPU VRAM
- ✅ `POSTGRES_PASSWORD` - Random secure password
- ✅ `DATABASE_URL` - With generated password
- ✅ `API_KEY` - Random secure key
- ✅ `CORS_ORIGINS` - Your domain + localhost

**You only need to set:**
- ⚠️ `SEC_USER_AGENT` - Your name and email (required by SEC)

---

### Step 3: Deploy Application

```bash
# Run the deployment script
./scripts/gpu_deploy.sh
```

**What this does automatically:**
1. ✅ Detects GPU (Quadro P4000, RTX 3060, etc.)
2. ✅ Selects optimal AI model based on VRAM
3. ✅ Creates/updates `.env` file
4. ✅ Verifies Docker GPU access
5. ✅ Starts all Docker containers:
   - PostgreSQL database
   - Qdrant vector database
   - Ollama LLM service (with GPU)
   - Backend API
   - Frontend React app
6. ✅ Downloads AI models (~5-10 minutes):
   - LLM model (llama3.1:8b-instruct)
   - Embedding model (nomic-embed-text)
7. ✅ Initializes database tables
8. ✅ Creates Qdrant vector collection
9. ✅ Configures Nginx reverse proxy
10. ✅ Verifies all services are healthy

**Total time:** ~15-20 minutes (mostly downloading models)

---

### Step 4: Configure Cloudflare Tunnel (if using)

```bash
# Already done if you followed the domain setup
# Just verify tunnel is running:
sudo systemctl status cloudflared

# If not running:
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

---

## 🔍 Verification

### Check All Services

```bash
# View all containers
docker-compose -f docker-compose.prod.yml ps

# Should show:
# - financeagent-postgres-1   (healthy)
# - financeagent-qdrant-1     (running)
# - financeagent-ollama-1     (running)
# - financeagent-backend-1    (healthy)
# - financeagent-frontend-1   (running)
```

### Test Locally

```bash
# Test frontend
curl http://localhost:3000

# Test backend
curl http://localhost:8000/api/health

# Test Ollama
curl http://localhost:11434/api/tags

# Test Qdrant
curl http://localhost:6333/health
```

### Test Publicly

Visit your domain:
- **Frontend:** https://10kiq.com
- **API Docs:** https://10kiq.com/docs
- **Health Check:** https://10kiq.com/health

### Test AI Query

```bash
curl -X POST https://10kiq.com/api/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What were Apple'\''s revenues?", "ticker": "AAPL"}'
```

**Note:** First query takes ~60 seconds (fetches SEC filing)

---

## 🐛 Common Issues & Fixes

### Issue 1: GPU Not Accessible

**Error:** `Docker cannot access GPU`

**Fix:**
```bash
# Configure Docker daemon
sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
EOF

sudo systemctl restart docker
```

### Issue 2: Database Tables Missing

**Error:** `relation "sec_filings" does not exist`

**Fix:**
```bash
# Initialize database
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.models.database import Base, engine
Base.metadata.create_all(bind=engine)
"

# Initialize Qdrant
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.services.vector_store import VectorStore
vs = VectorStore()
vs.create_collection()
"
```

### Issue 3: Mixed Content Error (HTTP/HTTPS)

**Error:** `Blocked loading mixed active content`

**Fix:** Already fixed in docker-compose.prod.yml
- Frontend uses `VITE_API_URL=/api` (relative path)
- Nginx proxies `/api` to backend

### Issue 4: Nginx Not Running

**Error:** `nginx.service is not active`

**Fix:**
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Issue 5: Port Conflicts

**Error:** `port is already allocated`

**Fix:**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :80

# Stop conflicting service or change port in docker-compose.prod.yml
```

---

## 🔄 Redeployment (Updates)

### For Code Changes

```bash
cd ~/financeagent
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### For Configuration Changes

```bash
# Edit .env
nano .env

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### For Model Changes

```bash
# Change model in .env
nano .env  # Update OLLAMA_MODEL

# Pull new model
docker exec financeagent-ollama-1 ollama pull llama3.1:8b-instruct-q8_0

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f ollama

# Nginx
sudo journalctl -u nginx -f

# Cloudflared
sudo journalctl -u cloudflared -f
```

### Monitor GPU

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Or
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv -l 1
```

### Check Disk Space

```bash
# Docker volumes can grow large
df -h
docker system df

# Clean up if needed
docker system prune -a --volumes
```

---

## 🎯 Success Criteria

Deployment is successful when:

- ✅ All containers are running/healthy
- ✅ Frontend loads at https://yourdomain.com
- ✅ Backend health check returns `{"status": "healthy"}`
- ✅ GPU is detected and utilized
- ✅ AI query returns a response (may take 60s first time)
- ✅ No errors in logs
- ✅ Database tables exist
- ✅ Qdrant collection exists

---

## 📝 Post-Deployment

### Security Hardening

1. **Enable UFW firewall:**
   ```bash
   sudo ufw enable
   ```

2. **Change SSH port** (optional but recommended)

3. **Set up monitoring** (optional):
   - Uptime monitoring (UptimeRobot, etc.)
   - Log aggregation (Papertrail, etc.)
   - Error tracking (Sentry, etc.)

### Backup Strategy

1. **Database backups:**
   ```bash
   docker exec financeagent-postgres-1 pg_dump -U postgres financeagent > backup.sql
   ```

2. **Volume backups:**
   ```bash
   docker run --rm -v financeagent_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz /data
   ```

---

## 🆘 Support

If you encounter issues not covered here:

1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify all environment variables are set correctly
3. Ensure GPU drivers are up to date
4. Check Docker and Docker Compose versions
5. Review GitHub Issues

---

**Last Updated:** 2025-10-24
**Tested On:** Ubuntu 22.04 LTS with NVIDIA Quadro P4000 (8GB)
