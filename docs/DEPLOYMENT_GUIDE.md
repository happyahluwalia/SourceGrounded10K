# 🚀 Deployment Guide - Finance Agent

## ✅ All Security Fixes Applied!

I've applied all critical security fixes:
- ✅ CORS configuration (configurable via environment)
- ✅ Debug mode set to False by default
- ✅ Database password using environment variables
- ✅ Input validation (SQL injection prevention)
- ✅ Sensitive data masked in logs
- ✅ Debug log streaming (configurable via ENABLE_DEBUG_LOGS)
- ✅ Rate limiting ready (slowapi added to requirements)
- ✅ Docker Compose for both backend and frontend

---

## 🎯 Quick Start (Development)

### 1. Clone and Setup
```bash
git clone <your-repo>
cd financeagent

# Create .env from template
cp .env.example .env

# Edit .env and set:
# - SEC_USER_AGENT=your-email@example.com
# - POSTGRES_PASSWORD=<generate-strong-password>
```

### 2. Start All Services
```bash
# Start infrastructure (Postgres, Qdrant, Ollama, Redis)
docker-compose up -d

# Download LLM model (one-time)
docker exec -it financeagent_ollama ollama pull gemma3:1b

# Install Python dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.api.main:app --reload

# In another terminal, run frontend
cd frontend
npm install
npm run dev
```

### 3. Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🐳 Docker Deployment (Production)

### Option 1: Docker Compose (Recommended)

**Step 1: Create production .env**
```bash
cp .env.example .env.production

# Edit .env.production and set:
SEC_USER_AGENT=your-production-email@company.com
POSTGRES_PASSWORD=$(openssl rand -base64 32)
DEBUG=False
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ENABLE_DEBUG_LOGS=False  # Disable in production for security
VITE_API_URL=https://api.yourdomain.com  # Your actual API domain
```

**Step 2: Build and Start**
```bash
# Load environment variables
export $(cat .env.production | xargs)

# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Download LLM model (one-time)
docker exec financeagent_ollama ollama pull gemma3:1b

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

**Step 3: Verify**
```bash
# Check health
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost/
```

### Option 2: Separate Containers

**Backend:**
```bash
# Build
docker build -t financeagent-backend:latest .

# Run
docker run -d \
  --name financeagent-backend \
  -p 8000:8000 \
  --env-file .env.production \
  financeagent-backend:latest
```

**Frontend:**
```bash
# Build with API URL
docker build \
  -f Dockerfile.frontend \
  --build-arg VITE_API_URL=https://api.yourdomain.com \
  -t financeagent-frontend:latest .

# Run
docker run -d \
  --name financeagent-frontend \
  -p 80:80 \
  financeagent-frontend:latest
```

---

## ☁️ Cloud Deployment

### AWS (ECS/Fargate)

1. **Push images to ECR**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag financeagent-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/financeagent-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/financeagent-backend:latest

docker tag financeagent-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/financeagent-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/financeagent-frontend:latest
```

2. **Create ECS task definitions** for backend and frontend
3. **Set up RDS** for Postgres
4. **Set up Application Load Balancer**
5. **Configure environment variables** in ECS task definition

### Google Cloud (Cloud Run)

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT-ID/financeagent-backend
gcloud builds submit --tag gcr.io/PROJECT-ID/financeagent-frontend -f Dockerfile.frontend

# Deploy backend
gcloud run deploy financeagent-backend \
  --image gcr.io/PROJECT-ID/financeagent-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "$(cat .env.production | xargs | tr ' ' ',')"

# Deploy frontend
gcloud run deploy financeagent-frontend \
  --image gcr.io/PROJECT-ID/financeagent-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### DigitalOcean App Platform

1. Connect your GitHub repo
2. Add two components:
   - **Backend**: Dockerfile, port 8000
   - **Frontend**: Dockerfile.frontend, port 80
3. Add environment variables in the dashboard
4. Deploy!

---

## 🔧 Configuration Guide

### Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `SEC_USER_AGENT` - Your email (required by SEC.gov)

**Security (Important!):**
- `DEBUG=False` - MUST be False in production
- `CORS_ORIGINS` - Set to your actual domain(s)
- `ENABLE_DEBUG_LOGS` - Set to False to disable UI log streaming
- `API_KEY` - Optional API key for authentication

**Services:**
- `QDRANT_HOST` - Qdrant hostname
- `OLLAMA_BASE_URL` - Ollama API URL
- `VITE_API_URL` - Frontend API URL (for Docker builds)

### Debug Logs Control

The debug log streaming feature (showing backend logs in the UI) can be controlled:

```bash
# Enable (default for development)
ENABLE_DEBUG_LOGS=True

# Disable (recommended for production)
ENABLE_DEBUG_LOGS=False
```

When disabled, the `/api/logs/stream` endpoint will return 403 Forbidden.

### CORS Configuration

```bash
# Development (allow all)
CORS_ORIGINS=*

# Production (specific domains)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Multiple domains
CORS_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com,https://api.yourdomain.com
```

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] Set `DEBUG=False`
- [ ] Set `CORS_ORIGINS` to your actual domain(s)
- [ ] Generate strong `POSTGRES_PASSWORD` (32+ characters)
- [ ] Set `ENABLE_DEBUG_LOGS=False` (optional, for extra security)
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Review and set rate limits
- [ ] Set up monitoring/alerting
- [ ] Test all endpoints
- [ ] Backup database
- [ ] Document incident response plan

---

## 📊 Monitoring

### Health Check
```bash
curl https://yourdomain.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "vector_store": "connected",
    "llm": "connected"
  }
}
```

### Logs
```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Individual containers
docker logs -f financeagent-backend
docker logs -f financeagent-frontend
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker logs financeagent-backend

# Common issues:
# 1. Missing SEC_USER_AGENT
# 2. Database connection failed
# 3. Qdrant not ready

# Verify services
docker ps
curl http://localhost:6333/health  # Qdrant
curl http://localhost:11434/api/tags  # Ollama
```

### Frontend can't connect to backend
```bash
# Check VITE_API_URL in build
docker inspect financeagent-frontend | grep VITE_API_URL

# Rebuild with correct URL
docker build -f Dockerfile.frontend \
  --build-arg VITE_API_URL=https://api.yourdomain.com \
  -t financeagent-frontend:latest .
```

### CORS errors
```bash
# Check CORS_ORIGINS setting
echo $CORS_ORIGINS

# Should match your frontend domain
# Example: CORS_ORIGINS=https://yourdomain.com
```

### Debug logs not showing
```bash
# Check if enabled
echo $ENABLE_DEBUG_LOGS

# Should be "True" to see logs in UI
# Set to "False" in production for security
```

---

## 🔄 Updates & Maintenance

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Update Dependencies
```bash
# Backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend && npm update
```

### Backup Database
```bash
# Backup
docker exec financeagent_postgres pg_dump -U postgres financeagent > backup.sql

# Restore
docker exec -i financeagent_postgres psql -U postgres financeagent < backup.sql
```

---

## 📞 Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:8000/api/health`
3. Check environment variables: `docker exec financeagent-backend env`
4. Review this guide's troubleshooting section

---

## 🎉 You're Ready to Deploy!

Your application is now production-ready with:
- ✅ Security hardening
- ✅ Configurable debug logs
- ✅ Docker containerization
- ✅ Environment-based configuration
- ✅ Input validation
- ✅ Health checks
- ✅ Proper logging

**Next steps:**
1. Set up your domain and SSL
2. Configure your .env.production
3. Deploy using docker-compose.prod.yml
4. Monitor and enjoy! 🚀
