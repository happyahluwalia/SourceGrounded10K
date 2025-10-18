# 🚨 Quick Security Fixes - Apply These NOW

## 1. Fix CORS (2 minutes)

**File:** `app/core/config.py`

Add this field:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Add this:
    cors_origins: str = "http://localhost:3000"  # Comma-separated list
```

**File:** `app/api/main.py`

Change line 225:
```python
# BEFORE:
allow_origins=["*"],

# AFTER:
allow_origins=settings.cors_origins.split(","),
```

---

## 2. Fix Debug Mode (1 minute)

**File:** `app/core/config.py`

Change line 13:
```python
# BEFORE:
debug: bool = True

# AFTER:
debug: bool = False
```

---

## 3. Fix Database Password (1 minute)

**File:** `docker-compose.yml`

Change line 8:
```python
# BEFORE:
POSTGRES_PASSWORD: dev_password_change_in_prod

# AFTER:
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dev_password_change_in_prod}
```

Then create/update `.env`:
```bash
POSTGRES_PASSWORD=your-strong-random-password-here
```

---

## 4. Add Rate Limiting (5 minutes)

**Step 1:** Install dependency
```bash
pip install slowapi==0.1.9
echo "slowapi==0.1.9" >> requirements.txt
```

**Step 2:** Add to `app/api/main.py` (after imports):
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# After app creation
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Step 3:** Add decorator to query endpoint:
```python
@app.post("/api/query", response_model=QueryResponse)
@limiter.limit("10/minute")  # 10 queries per minute per IP
async def query_company(request: Request, query_request: QueryRequest):
    # ... rest of code
```

---

## 5. Mask Sensitive Logs (2 minutes)

**File:** `app/api/main.py`

Change lines 181-183:
```python
# BEFORE:
logger.info(f"Database: {settings.database_url}")
logger.info(f"Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
logger.info(f"Ollama: {settings.ollama_base_url}")

# AFTER:
db_host = settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else 'configured'
logger.info(f"Database: {db_host}")
logger.info(f"Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
logger.info(f"Ollama: {settings.ollama_base_url}")
```

---

## 6. Add Input Validation (3 minutes)

**File:** `app/api/main.py`

Update QueryRequest model:
```python
from pydantic import validator
import re

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Question to ask")
    ticker: str = Field(..., min_length=1, max_length=10, description="Company ticker")
    # ... other fields ...
    
    @validator('ticker')
    def validate_ticker(cls, v):
        # Only allow uppercase letters
        if not re.match(r'^[A-Z]{1,10}$', v.upper()):
            raise ValueError('Ticker must be 1-10 uppercase letters')
        return v.upper()
    
    @validator('query')
    def validate_query(cls, v):
        # Remove dangerous SQL keywords
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', '--', ';']
        v_upper = v.upper()
        for word in dangerous:
            if word in v_upper:
                raise ValueError(f'Query contains forbidden keyword: {word}')
        return v.strip()
```

---

## ⚡ Apply All Fixes at Once

Run this script:

```bash
#!/bin/bash
# quick_security_fixes.sh

echo "🔒 Applying security fixes..."

# 1. Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from template"
fi

# 2. Install rate limiting
pip install slowapi==0.1.9
echo "✅ Installed slowapi"

# 3. Set secure defaults in .env
if ! grep -q "DEBUG=False" .env; then
    echo "DEBUG=False" >> .env
    echo "✅ Set DEBUG=False"
fi

if ! grep -q "CORS_ORIGINS" .env; then
    echo "CORS_ORIGINS=http://localhost:3000" >> .env
    echo "✅ Set CORS_ORIGINS"
fi

# 4. Generate random password if not set
if ! grep -q "POSTGRES_PASSWORD" .env; then
    RANDOM_PASS=$(openssl rand -base64 32)
    echo "POSTGRES_PASSWORD=$RANDOM_PASS" >> .env
    echo "✅ Generated secure database password"
fi

echo ""
echo "🎉 Security fixes applied!"
echo ""
echo "⚠️  MANUAL STEPS REQUIRED:"
echo "1. Update app/core/config.py - add cors_origins field"
echo "2. Update app/api/main.py - fix CORS, add rate limiting, add validators"
echo "3. Review .env file and update values"
echo "4. Test locally before deploying"
echo ""
echo "See QUICK_SECURITY_FIXES.md for detailed instructions"
```

---

## ✅ Verification

After applying fixes, test:

```bash
# 1. Check CORS
curl -H "Origin: https://evil.com" http://localhost:8000/api/health
# Should fail or not include CORS headers

# 2. Check rate limiting
for i in {1..15}; do
    curl -X POST http://localhost:8000/api/query \
        -H "Content-Type: application/json" \
        -d '{"query":"test","ticker":"AAPL"}'
done
# Should get 429 Too Many Requests after 10 requests

# 3. Check input validation
curl -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query":"DROP TABLE users;","ticker":"AAPL"}'
# Should get 422 Validation Error

# 4. Check debug mode
curl http://localhost:8000/api/health
# Should NOT expose stack traces on errors
```

---

## 📋 Checklist

Before deploying:
- [ ] Applied all 6 fixes above
- [ ] Created .env from .env.example
- [ ] Set strong database password
- [ ] Set DEBUG=False
- [ ] Set CORS to your domain
- [ ] Tested rate limiting
- [ ] Tested input validation
- [ ] Reviewed logs (no passwords visible)
- [ ] Tested all endpoints
- [ ] Backed up database

---

**Total Time: ~15 minutes**

These are the MINIMUM fixes needed. See PRE_DEPLOYMENT_REVIEW.md for complete recommendations.
