
# 10kiq.com Production Deployment Documentation

## Architecture Overview

**Domain:** 10kiq.com  
**Tunnel ID:** ab3e757b-66ec-4d1f-b514-724e0fd5f267  
**Server:** VAST AI GPU Instance (171.248.248.17)

### Service Stack
- **Frontend:** React (port 3000) → https://10kiq.com
- **Backend:** FastAPI (port 8000) → https://api.10kiq.com
- **Database:** PostgreSQL (port 5432)
- **Vector Store:** Qdrant (port 6333)
- **LLM:** Ollama (port 11434)
- **Tunnel:** Cloudflare Tunnel

---

## 1. Cloudflare Tunnel Configuration

### DNS Records (Cloudflare Dashboard)
```
Type: CNAME
Name: @
Target: ab3e757b-66ec-4d1f-b514-724e0fd5f267.cfargotunnel.com
Proxy: ON (orange cloud)

Type: CNAME
Name: www
Target: ab3e757b-66ec-4d1f-b514-724e0fd5f267.cfargotunnel.com
Proxy: ON (orange cloud)

Type: CNAME
Name: api
Target: ab3e757b-66ec-4d1f-b514-724e0fd5f267.cfargotunnel.com
Proxy: ON (orange cloud)
```

### Tunnel Configuration
**Location:** `/root/.cloudflared/config.yml`

```yaml
tunnel: ab3e757b-66ec-4d1f-b514-724e0fd5f267
credentials-file: /root/.cloudflared/ab3e757b-66ec-4d1f-b514-724e0fd5f267.json

ingress:
  - hostname: 10kiq.com
    service: http://localhost:3000
  
  - hostname: www.10kiq.com
    service: http://localhost:3000
  
  - hostname: api.10kiq.com
    service: http://localhost:8000
  
  - service: http_status:404
```

### Cloudflare Tunnel Commands
```bash
# Start/Stop/Restart (via supervisor)
supervisorctl start cloudflared
supervisorctl stop cloudflared
supervisorctl restart cloudflared

# Check status
supervisorctl status cloudflared

# View logs
tail -f /var/log/cloudflared.log

# Test tunnel manually (for debugging)
cloudflared tunnel --config ~/.cloudflared/config.yml run 10kiq_new_vastai

# Check tunnel info
cloudflared tunnel info 10kiq_new_vastai
```

---

## 2. PostgreSQL Database

### Configuration
- **Host:** localhost
- **Port:** 5432
- **Database:** financeagent
- **User:** financeuser
- **Password:** (stored in `/home/financeapp/SourceGrounded10K/.env`)

### PostgreSQL Commands
```bash
# Start/Stop service
service postgresql start
service postgresql stop
service postgresql restart
service postgresql status

# Connect to database
sudo -u postgres psql

# Connect to financeagent database
sudo -u postgres psql -d financeagent

# List databases
sudo -u postgres psql -c "\l"

# Check if database exists
sudo -u postgres psql -c "\l" | grep financeagent

# Backup database
sudo -u postgres pg_dump financeagent > /backup/financeagent_$(date +%Y%m%d).sql

# Restore database
sudo -u postgres psql financeagent < /backup/financeagent_20260104.sql
```

---

## 3. Qdrant Vector Store

### Configuration
- **Host:** localhost
- **Port:** 6333
- **Storage:** /var/lib/qdrant
- **Config:** /etc/qdrant/config.yaml

### Qdrant Commands
```bash
# Start Qdrant
nohup /opt/qdrant --config-path /etc/qdrant/config.yaml > /var/log/qdrant.log 2>&1 &

# Stop Qdrant
pkill qdrant

# Check if running
ps aux | grep qdrant

# View logs
tail -f /var/log/qdrant.log

# Check health
curl http://localhost:6333/

# List collections
curl http://localhost:6333/collections

# Delete a collection (careful!)
curl -X DELETE http://localhost:6333/collections/financial_filings
```

### Qdrant Config File
**Location:** `/etc/qdrant/config.yaml`
```yaml
storage:
  storage_path: /var/lib/qdrant

service:
  http_port: 6333
  grpc_port: 6334

log_level: INFO
```

---

## 4. Ollama LLM Service

### Configuration
- **Host:** localhost
- **Port:** 11434
- **Models:** llama3.1, nomic-embed-text

### Ollama Commands
```bash
# Check if running
ps aux | grep ollama
curl http://localhost:11434/api/tags

# List models
ollama list

# Pull a model
ollama pull llama3.1
ollama pull nomic-embed-text

# Remove a model
ollama rm model-name

# Run a model interactively (testing)
ollama run llama3.1

# Check model info
ollama show llama3.1
```

---

## 5. Backend (FastAPI)

### Configuration
- **Port:** 8000
- **Project Path:** /home/financeapp/SourceGrounded10K
- **Virtual Env:** /home/financeapp/SourceGrounded10K/venv
- **Config File:** /home/financeapp/SourceGrounded10K/.env

### Backend Commands
```bash
# Start/Stop/Restart (via supervisor)
supervisorctl start backend
supervisorctl stop backend
supervisorctl restart backend

# Check status
supervisorctl status backend

# View logs
tail -f /var/log/backend.log

# View real-time logs
tail -f /var/log/backend.log | grep -E "INFO|ERROR|WARNING"

# Test backend locally
curl http://localhost:8000/api/health

# Test backend via domain
curl https://api.10kiq.com/api/health

# Manual start (for debugging)
su - financeapp
cd ~/SourceGrounded10K
source venv/bin/activate
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Backend Environment Variables
**Location:** `/home/financeapp/SourceGrounded10K/.env`

Key settings:
```bash
DATABASE_URL=postgresql://financeuser:PASSWORD@localhost:5432/financeagent
QDRANT_HOST=localhost
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
CORS_ORIGINS=https://10kiq.com,https://www.10kiq.com,https://api.10kiq.com
DEBUG=False
ENABLE_DEBUG_LOGS=True
```

### Update Backend Configuration
```bash
# As financeapp user
su - financeapp
cd ~/SourceGrounded10K
nano .env

# After changes, restart backend
exit
supervisorctl restart backend
```

---

## 6. Frontend (React)

### Configuration
- **Port:** 3000
- **Project Path:** /home/financeapp/SourceGrounded10K/frontend
- **Build Output:** /home/financeapp/SourceGrounded10K/frontend/dist

### Frontend Commands
```bash
# Start/Stop/Restart (via supervisor)
supervisorctl start frontend
supervisorctl stop frontend
supervisorctl restart frontend

# Check status
supervisorctl status frontend

# View logs
tail -f /var/log/frontend.log

# Test frontend locally
curl http://localhost:3000

# Rebuild frontend (after code changes)
su - financeapp
cd ~/SourceGrounded10K/frontend
npm run build
exit
supervisorctl restart frontend
```

### Frontend Environment Variables
**Location:** `/home/financeapp/SourceGrounded10K/frontend/.env`

```bash
VITE_API_URL=https://api.10kiq.com
```

### Rebuild Frontend
```bash
# As financeapp user
su - financeapp
cd ~/SourceGrounded10K/frontend

# Update .env if needed
nano .env

# Rebuild
npm run build

# Exit and restart
exit
supervisorctl restart frontend
```

---

## 7. Supervisor Service Management

### All Services Overview
```bash
# Check all services
supervisorctl status

# Start all services
supervisorctl start all

# Stop all services
supervisorctl stop all

# Restart all services
supervisorctl restart all

# Reload supervisor config (after changes)
supervisorctl reread
supervisorctl update
```

### Supervisor Config Locations
```
/etc/supervisor/conf.d/docker.conf
/etc/supervisor/conf.d/cloudflared.conf
/etc/supervisor/conf.d/backend.conf
/etc/supervisor/conf.d/frontend.conf
```

### View Supervisor Logs
```bash
tail -f /var/log/supervisor/supervisord.log
```

---

## 8. Complete Service Startup Sequence

### After Server Reboot
```bash
# 1. Start Docker daemon
dockerd --iptables=false --ip-masq=false --bridge=none > /var/log/docker.log 2>&1 &

# 2. Start PostgreSQL
service postgresql start

# 3. Start Qdrant
nohup /opt/qdrant --config-path /etc/qdrant/config.yaml > /var/log/qdrant.log 2>&1 &

# 4. Ollama should already be running (VAST AI managed)
# Verify: curl http://localhost:11434/api/tags

# 5. Start all supervisor services
supervisorctl start all

# 6. Verify everything is running
supervisorctl status
```

**Note:** Supervisor is configured to auto-start most services, but PostgreSQL and Qdrant need manual start after reboot.

---

## 9. Health Check Commands

```bash
# Quick health check script
cat > /root/health-check.sh << 'EOF'
#!/bin/bash
echo "=== Service Health Check ==="
echo ""
echo "PostgreSQL:"
service postgresql status | head -1
echo ""
echo "Qdrant:"
curl -s http://localhost:6333/ > /dev/null && echo "✓ Running" || echo "✗ Not running"
echo ""
echo "Ollama:"
curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Running" || echo "✗ Not running"
echo ""
echo "Backend:"
curl -s http://localhost:8000/api/health > /dev/null && echo "✓ Running" || echo "✗ Not running"
echo ""
echo "Frontend:"
curl -s http://localhost:3000 > /dev/null && echo "✓ Running" || echo "✗ Not running"
echo ""
echo "Cloudflare Tunnel:"
supervisorctl status cloudflared | grep RUNNING > /dev/null && echo "✓ Running" || echo "✗ Not running"
echo ""
echo "=== Public URLs ==="
echo "Frontend: https://10kiq.com"
echo "Backend: https://api.10kiq.com/api/health"
EOF

chmod +x /root/health-check.sh

# Run health check
/root/health-check.sh
```

---

## 10. Troubleshooting

### Backend not responding
```bash
# Check logs
tail -100 /var/log/backend.log

# Check if port is in use
sudo lsof -i :8000

# Restart backend
supervisorctl restart backend
```

### Frontend not loading
```bash
# Check logs
tail -100 /var/log/frontend.log

# Verify build exists
ls -la /home/financeapp/SourceGrounded10K/frontend/dist/

# Restart frontend
supervisorctl restart frontend
```

### Cloudflare Tunnel disconnected
```bash
# Check logs
tail -100 /var/log/cloudflared.log

# Restart tunnel
supervisorctl restart cloudflared

# Verify tunnel is connected
supervisorctl status cloudflared
```

### Database connection errors
```bash
# Check PostgreSQL is running
service postgresql status

# Test connection
sudo -u postgres psql -c "SELECT 1"

# Restart PostgreSQL
service postgresql restart
```

---

## 11. Backup and Maintenance

### Database Backup
```bash
# Create backup directory
mkdir -p /backup

# Backup database
sudo -u postgres pg_dump financeagent > /backup/financeagent_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup (add to crontab)
crontab -e
# Add: 0 2 * * * sudo -u postgres pg_dump financeagent > /backup/financeagent_$(date +\%Y\%m\%d).sql
```

### Qdrant Backup
```bash
# Qdrant data is in /var/lib/qdrant
tar -czf /backup/qdrant_$(date +%Y%m%d).tar.gz /var/lib/qdrant
```

### Update Application Code
```bash
# As financeapp user
su - financeapp
cd ~/SourceGrounded10K

# Pull latest code
git pull

# Update backend dependencies
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend
cd frontend
npm install
npm run build

# Exit and restart services
exit
supervisorctl restart backend
supervisorctl restart frontend
```

---

**Documentation complete!** All service management commands are now documented.