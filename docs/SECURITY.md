# Security Guide

## Quick Security Checklist

Before deploying to production, apply these critical security fixes:

### 1. CORS Configuration (Critical)

**File:** `app/core/config.py`
```python
class Settings(BaseSettings):
    # Change from wildcard to specific origins
    cors_origins: str = "https://yourdomain.com,https://www.yourdomain.com"
```

**File:** `app/api/main.py`
```python
# Use environment variable instead of wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),  # Not ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Debug Mode (Critical)

**File:** `app/core/config.py`
```python
# Disable debug in production
debug: bool = False  # Not True
```

**File:** `.env`
```bash
DEBUG=False
```

### 3. Database Passwords (Critical)

**File:** `docker-compose.prod.yml`
```yaml
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # From environment
```

**File:** `.env`
```bash
# Use strong, random passwords
POSTGRES_PASSWORD=<generate-strong-password>
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/financeagent
```

### 4. API Key Authentication (Recommended)

**File:** `app/core/config.py`
```python
class Settings(BaseSettings):
    api_key: str = ""  # Set in production
```

**File:** `app/api/main.py`
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Apply to endpoints
@app.post("/api/query", dependencies=[Depends(verify_api_key)])
async def query_endpoint(...):
    ...
```

### 5. Rate Limiting (Recommended)

Already implemented via SlowAPI:
```python
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

Adjust based on your needs.

---

## Environment Variables Security

### Never Commit Secrets

**Add to `.gitignore`:**
```
.env
.env.local
.env.production
*.pem
*.key
```

### Use Environment Variables

**Development (`.env`):**
```bash
DEBUG=True
POSTGRES_PASSWORD=dev_password
CORS_ORIGINS=http://localhost:3000
```

**Production (`.env.production`):**
```bash
DEBUG=False
POSTGRES_PASSWORD=<strong-random-password>
CORS_ORIGINS=https://yourdomain.com
API_KEY=<strong-random-api-key>
SEC_USER_AGENT=your-email@company.com
```

### Generate Strong Passwords

```bash
# Generate random password
openssl rand -base64 32

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## SSL/TLS Configuration

### Certbot (Let's Encrypt)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already set up by certbot)
certbot renew --dry-run
```

### Nginx SSL Configuration

**File:** `/etc/nginx/sites-available/financeagent`
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Firewall Configuration

### UFW (Ubuntu)

```bash
# Enable UFW
ufw enable

# Allow SSH (change port if using non-standard)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Deny all other incoming
ufw default deny incoming
ufw default allow outgoing

# Check status
ufw status verbose
```

### Fail2Ban (SSH Protection)

```bash
# Install
apt install fail2ban

# Configure
cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

# Restart
systemctl restart fail2ban
systemctl enable fail2ban

# Check status
fail2ban-client status sshd
```

---

## Docker Security

### Run as Non-Root User

**File:** `Dockerfile`
```dockerfile
# Create non-root user
RUN useradd -m -u 1000 appuser

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Limit Container Resources

**File:** `docker-compose.prod.yml`
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Use Secrets for Sensitive Data

```yaml
services:
  backend:
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt
```

---

## Database Security

### PostgreSQL Hardening

**File:** `docker-compose.prod.yml`
```yaml
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
    -c ssl_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
```

### Connection Encryption

```python
# Use SSL for database connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Backup Encryption

```bash
# Encrypt backups
pg_dump financeagent | gpg --encrypt --recipient your@email.com > backup.sql.gpg

# Decrypt
gpg --decrypt backup.sql.gpg | psql financeagent
```

---

## Application Security

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    ticker: str = Field(..., regex=r'^[A-Z]{1,5}$')
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove potentially dangerous characters
        return v.strip()
```

### SQL Injection Prevention

```python
# Use SQLAlchemy ORM (parameterized queries)
# NEVER use string concatenation
result = db.query(Company).filter(Company.ticker == ticker).first()

# NOT THIS:
# query = f"SELECT * FROM companies WHERE ticker = '{ticker}'"
```

### XSS Prevention

```python
# FastAPI automatically escapes output
# For extra safety, use bleach library
import bleach

def sanitize_html(text: str) -> str:
    return bleach.clean(text, tags=[], strip=True)
```

---

## Monitoring & Logging

### Security Logging

```python
import logging

security_logger = logging.getLogger("security")

# Log authentication attempts
security_logger.warning(f"Failed API key attempt from {request.client.host}")

# Log suspicious activity
security_logger.error(f"SQL injection attempt detected: {query}")
```

### Log Rotation

```bash
# Configure logrotate
cat > /etc/logrotate.d/financeagent <<EOF
/var/log/financeagent/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
    postrotate
        docker compose restart backend
    endscript
}
EOF
```

### Intrusion Detection

```bash
# Install AIDE
apt install aide

# Initialize database
aideinit

# Check for changes
aide --check
```

---

## Secrets Management

### Using Docker Secrets

```bash
# Create secrets
echo "my-db-password" | docker secret create db_password -
echo "my-api-key" | docker secret create api_key -

# Use in compose file
services:
  backend:
    secrets:
      - db_password
      - api_key
```

### Using HashiCorp Vault

```bash
# Install Vault
apt install vault

# Start Vault server
vault server -dev

# Store secrets
vault kv put secret/financeagent \
  db_password="xxx" \
  api_key="yyy"

# Retrieve in application
vault kv get -field=db_password secret/financeagent
```

---

## Compliance

### GDPR Considerations

- Log user consent for data processing
- Implement data deletion endpoints
- Encrypt personal data at rest
- Provide data export functionality

### SOC 2 Considerations

- Implement audit logging
- Regular security assessments
- Access control policies
- Incident response plan

---

## Security Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Disable debug mode
- [ ] Set up firewall (UFW)
- [ ] Install Fail2Ban
- [ ] Enable automatic security updates
- [ ] Implement API key authentication
- [ ] Configure rate limiting
- [ ] Set up log rotation
- [ ] Create backup strategy
- [ ] Test disaster recovery
- [ ] Document security procedures
- [ ] Set up monitoring/alerts
- [ ] Review and update dependencies
- [ ] Conduct security audit
- [ ] Create incident response plan

---

## Reporting Security Issues

If you discover a security vulnerability, please email: security@yourdomain.com

**Do NOT** open a public GitHub issue for security vulnerabilities.

---

**Security is an ongoing process, not a one-time task. Stay vigilant! 🔒**
