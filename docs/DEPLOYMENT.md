# Deployment Guide

This guide covers deploying the Finance Agent application to various cloud platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Digital Ocean Deployment](#digital-ocean-deployment)
- [Railway Deployment](#railway-deployment)
- [Render Deployment](#render-deployment)
- [Docker Compose (Self-Hosted)](#docker-compose-self-hosted)
- [Environment Variables](#environment-variables)

---

## Prerequisites

Before deploying, ensure you have:

1. **SEC User Agent Email**: Required for SEC API compliance
2. **Domain name** (optional but recommended)
3. **Cloud platform account** (Digital Ocean, Railway, or Render)
4. **Docker** installed (for local testing)

---

## Digital Ocean Deployment

### Option 1: App Platform (Easiest)

Digital Ocean App Platform is the simplest way to deploy with automatic scaling and managed databases.

#### Steps:

1. **Create a new App**
   ```bash
   # Install doctl CLI
   brew install doctl  # macOS
   
   # Authenticate
   doctl auth init
   ```

2. **Create `app.yaml` configuration** (already included in repo)

3. **Deploy via CLI**
   ```bash
   doctl apps create --spec app.yaml
   ```

4. **Or deploy via Web UI**
   - Go to Digital Ocean Console → Apps → Create App
   - Connect your GitHub repository
   - Select the `main` branch
   - Digital Ocean will auto-detect the Dockerfile
   - Add environment variables (see below)
   - Deploy!

#### Estimated Cost:
- Basic tier: $12/month (backend + frontend)
- Managed Postgres: $15/month
- Total: ~$27/month

### Option 2: Droplet (More Control)

For more control and potentially lower costs, use a Droplet.

1. **Create a Droplet**
   - Choose Ubuntu 22.04 LTS
   - Minimum: 4GB RAM, 2 vCPUs ($24/month)
   - Recommended: 8GB RAM, 4 vCPUs ($48/month) for Ollama

2. **SSH into Droplet**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

4. **Install Docker Compose**
   ```bash
   apt-get update
   apt-get install docker-compose-plugin
   ```

5. **Clone your repository**
   ```bash
   git clone https://github.com/yourusername/financeagent.git
   cd financeagent
   ```

6. **Set up environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your values
   ```

7. **Deploy with Docker Compose**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

8. **Set up Nginx reverse proxy** (optional, for HTTPS)
   ```bash
   apt-get install nginx certbot python3-certbot-nginx
   
   # Configure nginx
   nano /etc/nginx/sites-available/financeagent
   
   # Enable site
   ln -s /etc/nginx/sites-available/financeagent /etc/nginx/sites-enabled/
   
   # Get SSL certificate
   certbot --nginx -d yourdomain.com
   ```

9. **Pull Ollama model**
   ```bash
   docker exec -it financeagent_ollama ollama pull gemma3:1b
   ```

---

## Railway Deployment

Railway offers simple deployment with automatic HTTPS and environment management.

### Steps:

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Initialize project**
   ```bash
   cd financeagent
   railway init
   ```

3. **Create services**
   ```bash
   # Create Postgres database
   railway add --database postgres
   
   # Deploy backend
   railway up
   ```

4. **Add environment variables**
   ```bash
   railway variables set SEC_USER_AGENT="your-email@example.com"
   railway variables set QDRANT_HOST="qdrant"
   railway variables set OLLAMA_BASE_URL="http://ollama:11434"
   ```

5. **Deploy frontend separately**
   - Create a new service in Railway dashboard
   - Connect to your repo
   - Set root directory to `frontend`
   - Railway will auto-detect Vite and build

#### Estimated Cost:
- Hobby plan: $5/month (includes $5 credit)
- Additional usage: ~$10-20/month
- Total: ~$15-25/month

**Note**: Railway may not support GPU for Ollama. Consider using a smaller model or external LLM API.

---

## Render Deployment

Render provides free tiers for testing and easy scaling for production.

### Steps:

1. **Create a Render account** at https://render.com

2. **Deploy Backend**
   - New → Web Service
   - Connect your GitHub repo
   - Name: `financeagent-backend`
   - Environment: Docker
   - Dockerfile path: `Dockerfile`
   - Add environment variables

3. **Deploy Frontend**
   - New → Static Site
   - Connect your GitHub repo
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/dist`

4. **Create Postgres Database**
   - New → PostgreSQL
   - Copy the internal database URL
   - Add to backend environment variables

5. **Deploy Qdrant** (use external service)
   - Sign up at https://cloud.qdrant.io
   - Create a cluster
   - Get API key and URL
   - Add to backend environment variables

6. **Configure Ollama** (use external API)
   - Option 1: Use OpenAI API instead
   - Option 2: Deploy Ollama on separate GPU server
   - Option 3: Use Render's GPU instances (beta)

#### Estimated Cost:
- Free tier: $0/month (limited resources)
- Starter: $7/month (backend) + $7/month (Postgres)
- Total: ~$14/month (without Ollama GPU)

---

## Docker Compose (Self-Hosted)

For self-hosting on your own server or VPS.

### Quick Start:

```bash
# Clone repository
git clone https://github.com/yourusername/financeagent.git
cd financeagent

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env

# Build and start all services
docker compose -f docker-compose.prod.yml up -d

# Pull Ollama model
docker exec -it financeagent_ollama ollama pull gemma3:1b

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Access the application
# Frontend: http://localhost
# API: http://localhost/api
# API Docs: http://localhost/api/docs
```

### System Requirements:

- **Minimum**: 8GB RAM, 4 CPU cores, 50GB storage
- **Recommended**: 16GB RAM, 8 CPU cores, 100GB storage
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for Ollama)

### Updating:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Clean up old images
docker system prune -a
```

---

## Environment Variables

### Required Variables:

```bash
# SEC API Compliance (REQUIRED)
SEC_USER_AGENT=your-email@example.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
POSTGRES_USER=financeuser
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=financeagent

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# LLM Service
OLLAMA_BASE_URL=http://ollama:11434
```

### Optional Variables:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=*

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSION=1024

# LLM Configuration
LLM_MODEL=gemma3:1b
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500

# RAG Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=0.15
TOP_K=5
SCORE_THRESHOLD=0.5

# Logging
LOG_LEVEL=INFO
```

---

## Post-Deployment Checklist

- [ ] Verify all services are healthy: `curl http://your-domain/api/health`
- [ ] Test a query: `curl -X POST http://your-domain/api/query -d '{"query":"test","ticker":"AAPL"}'`
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure backups for Postgres and Qdrant
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS for your domain
- [ ] Add rate limiting
- [ ] Set up authentication (if needed)
- [ ] Monitor costs and resource usage

---

## Troubleshooting

### Ollama not responding

```bash
# Check if model is downloaded
docker exec -it financeagent_ollama ollama list

# Pull model manually
docker exec -it financeagent_ollama ollama pull gemma3:1b

# Check logs
docker logs financeagent_ollama
```

### Database connection errors

```bash
# Check Postgres is running
docker ps | grep postgres

# Test connection
docker exec -it financeagent_postgres psql -U postgres -d financeagent

# Check logs
docker logs financeagent_postgres
```

### Qdrant connection errors

```bash
# Check Qdrant is running
curl http://localhost:6333/health

# View collections
curl http://localhost:6333/collections

# Check logs
docker logs financeagent_qdrant
```

### Frontend not loading

```bash
# Check nginx logs
docker logs financeagent_frontend

# Verify build
docker exec -it financeagent_frontend ls /usr/share/nginx/html

# Test API proxy
curl http://localhost/api/health
```

---

## Cost Comparison

| Platform | Monthly Cost | Pros | Cons |
|----------|-------------|------|------|
| **Digital Ocean Droplet** | $24-48 | Full control, GPU support | Manual setup |
| **Digital Ocean App Platform** | $27+ | Managed, auto-scaling | Limited GPU |
| **Railway** | $15-25 | Easy setup, auto-deploy | No GPU on hobby plan |
| **Render** | $14+ (free tier available) | Free tier, easy setup | GPU in beta |
| **Self-Hosted** | $0 (hardware cost) | Full control, no limits | Maintenance required |

---

## Production Recommendations

1. **Use managed databases** for Postgres (easier backups, scaling)
2. **Deploy Qdrant separately** on Qdrant Cloud for better performance
3. **Use external LLM API** (OpenAI, Anthropic) instead of Ollama for production
4. **Set up monitoring** with Sentry, DataDog, or Prometheus
5. **Enable HTTPS** with Let's Encrypt or cloud provider SSL
6. **Add authentication** for production use
7. **Implement rate limiting** to prevent abuse
8. **Set up CI/CD** with GitHub Actions
9. **Configure backups** for all data stores
10. **Use CDN** for frontend assets (Cloudflare, etc.)

---

## Next Steps

After deployment:

1. Process initial companies: `POST /api/companies/{ticker}/process`
2. Test queries via UI or API
3. Monitor logs and performance
4. Set up alerts for errors
5. Plan for scaling based on usage

For questions or issues, check the main README or open an issue on GitHub.
