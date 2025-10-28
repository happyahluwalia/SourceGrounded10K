# Production Deployment and Operations Guide

## Table of Contents
1. [Deployment Architecture](#deployment-architecture)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Container Configuration](#container-configuration)
4. [Scaling Strategies](#scaling-strategies)
5. [Monitoring and Observability](#monitoring-and-observability)
6. [Cost Optimization](#cost-optimization)
7. [Operational Runbook](#operational-runbook)

---

## Deployment Architecture

### Self-Hosted Production Architecture

```
┌─────────────────── Internet ──────────────────┐
│                                                │
│                                                │
▼                                                │
┌─────────────────┐                             │
│  Load Balancer  │                             │
│   (nginx/Caddy) │                             │
└────────┬────────┘                             │
         │                                       │
         ├──────────┬──────────┬─────────┐      │
         │          │          │         │      │
         ▼          ▼          ▼         ▼      │
┌──────────┐  ┌──────────┐  ┌──────────┐      │
│ FastAPI  │  │ FastAPI  │  │ FastAPI  │      │
│ Instance │  │ Instance │  │ Instance │      │
│    #1    │  │    #2    │  │    #3    │      │
└────┬─────┘  └────┬─────┘  └────┬─────┘      │
     │             │             │              │
     └─────────────┴─────────────┘              │
                   │                            │
     ┌─────────────┴─────────────┐              │
     │                           │              │
     ▼                           ▼              │
┌──────────────┐          ┌──────────────┐     │
│  PostgreSQL  │          │   Qdrant     │     │
│  (Primary +  │          │ Vector Store │     │
│   Replicas)  │          └──────────────┘     │
└──────────────┘                               │
     │                                          │
     ▼                                          │
┌──────────────┐          ┌──────────────┐     │
│    Redis     │          │    Ollama    │     │
│   (Cluster)  │          │  (GPU Nodes) │     │
└──────────────┘          └──────────────┘     │
                                                │
┌─────────────── Monitoring Stack ─────────────┤
│                                                │
│  Prometheus + Grafana + Loki + AlertManager   │
│                                                │
└────────────────────────────────────────────────┘
```

### Component Responsibilities

**Load Balancer** (nginx/Caddy):
- SSL/TLS termination
- Request routing
- Rate limiting (first layer)
- Health checking
- Static content serving

**FastAPI Instances**:
- Handle HTTP requests
- Run LangGraph workflows
- Manage agent orchestration
- Session management
- Second-layer rate limiting

**PostgreSQL**:
- Application data
- LangGraph checkpoints
- User sessions
- Audit logs

**Qdrant**:
- Vector embeddings storage
- Semantic search
- Metadata filtering

**Ollama**:
- Local LLM inference
- GPU-accelerated
- Model management

**Redis**:
- Response caching
- Session storage
- Rate limit counters
- Distributed locks

**Monitoring Stack**:
- Prometheus: Metrics collection
- Grafana: Visualization
- Loki: Log aggregation
- AlertManager: Alert routing

---

## Infrastructure Setup

### Hardware Requirements

#### Minimum (Development/Small Scale)
```yaml
API Servers (3x):
  CPU: 4 cores
  RAM: 8GB
  Storage: 50GB SSD

PostgreSQL:
  CPU: 4 cores
  RAM: 16GB
  Storage: 500GB SSD

Qdrant:
  CPU: 4 cores
  RAM: 16GB
  Storage: 200GB SSD

Ollama (with GPU):
  CPU: 8 cores
  RAM: 32GB
  GPU: NVIDIA T4 or better (16GB VRAM)
  Storage: 100GB SSD

Redis:
  CPU: 2 cores
  RAM: 4GB
  Storage: 20GB SSD

Monitoring:
  CPU: 4 cores
  RAM: 8GB
  Storage: 100GB SSD

Total: ~40 cores, ~92GB RAM, ~970GB storage, 1x GPU
```

#### Production (Medium Scale, 100 req/min)
```yaml
API Servers (5x):
  CPU: 8 cores
  RAM: 16GB
  Storage: 100GB SSD

PostgreSQL:
  Primary: 8 cores, 32GB RAM, 1TB SSD
  Replica: 8 cores, 32GB RAM, 1TB SSD

Qdrant (cluster):
  3 nodes: 8 cores, 32GB RAM, 500GB SSD each

Ollama (GPU cluster):
  3 nodes: 16 cores, 64GB RAM, 2x NVIDIA A100 (40GB), 200GB SSD

Redis (cluster):
  3 nodes: 4 cores, 16GB RAM, 50GB SSD

Monitoring:
  CPU: 8 cores
  RAM: 16GB
  Storage: 500GB SSD

Total: ~148 cores, ~480GB RAM, ~5.5TB storage, 6x A100 GPUs
```

### Cloud Provider Options

#### Self-Hosted on AWS
```yaml
API Servers:
  Instance Type: c6i.2xlarge
  Count: 3-5
  Cost: ~$0.34/hr × 5 = $1.70/hr = $1,224/month

Database:
  RDS PostgreSQL db.r6i.2xlarge
  Multi-AZ
  Cost: ~$1.40/hr = $1,008/month

Vector DB:
  EC2 r6i.2xlarge
  Count: 3
  Cost: ~$0.50/hr × 3 = $1.50/hr = $1,080/month

GPU Inference:
  EC2 g5.4xlarge (NVIDIA A10G)
  Count: 2
  Cost: ~$1.50/hr × 2 = $3.00/hr = $2,160/month

Redis:
  ElastiCache r6g.large
  Cost: ~$0.18/hr = $130/month

Load Balancer:
  ALB
  Cost: ~$20/month + data transfer

Monitoring:
  EC2 t3.large
  Cost: ~$0.08/hr = $58/month

Total: ~$5,680/month (before data transfer)
```

#### Self-Hosted on GCP
```yaml
Similar configuration:
  Compute Engine + Cloud SQL + Memorystore
  
Estimated: ~$5,200/month
```

#### Bare Metal/On-Premise
```yaml
Initial Hardware Cost: ~$50,000-80,000
Monthly Operating Cost: ~$500-1,000 (power, cooling, maintenance)
Break-even: ~12-18 months

Best for:
- Long-term deployments
- High data privacy requirements
- Predictable workloads
```

---

## Container Configuration

### Docker Compose (Development)

```yaml
# docker-compose.yml

version: '3.8'

services:
  # API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/financeagent
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - qdrant
      - redis
      - ollama
    volumes:
      - ./app:/app/app
      - ./prompts:/app/prompts
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=financeagent
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=2GB
      -c effective_cache_size=6GB
      -c work_mem=16MB
      -c maintenance_work_mem=512MB

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

  # Ollama LLM Service
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 16G
    environment:
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_MAX_LOADED_MODELS=2

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: >
      redis-server
      --appendonly yes
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G

  # Monitoring: Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'

  # Monitoring: Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/datasources:/etc/grafana/provisioning/datasources:ro
    depends_on:
      - prometheus

volumes:
  postgres_data:
  qdrant_data:
  ollama_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

### Dockerfile (Multi-stage Build)

```dockerfile
# Dockerfile

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY prompts/ ./prompts/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

# Expose port
EXPOSE 8000
```

### nginx Configuration

```nginx
# nginx.conf

events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_status 429;

    # Upstream API servers
    upstream api_backend {
        least_conn;  # Load balancing method
        server api:8000 max_fails=3 fail_timeout=30s;
        server api:8001 max_fails=3 fail_timeout=30s;
        server api:8002 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name finance-agent.example.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name finance-agent.example.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts (important for long-running agent queries)
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            
            # Buffering
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # Health check endpoint (no rate limit)
        location /health {
            proxy_pass http://api_backend/health;
            access_log off;
        }

        # Static files (if any)
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

---

## Scaling Strategies

### Horizontal Scaling

#### API Servers
```bash
# Scale API service
docker compose up -d --scale api=5

# Or in Kubernetes
kubectl scale deployment finance-agent-api --replicas=5
```

**Considerations**:
- Stateless design (all state in DB/Redis)
- Session affinity not required
- Load balancer distributes evenly
- Easy to scale up/down

#### Database (Read Replicas)
```yaml
# PostgreSQL with read replicas
services:
  postgres-primary:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=master
  
  postgres-replica-1:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_HOST=postgres-primary
  
  postgres-replica-2:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_HOST=postgres-primary
```

**Usage**:
```python
# Read from replicas for queries
read_db = get_replica_connection()
results = read_db.query("SELECT...")

# Write to primary
write_db = get_primary_connection()
write_db.execute("INSERT...")
```

#### Qdrant (Sharding)
```yaml
# Qdrant cluster with sharding
qdrant-node-1:
  environment:
    - QDRANT__CLUSTER__ENABLED=true
    - QDRANT__CLUSTER__NODE_ID=1

qdrant-node-2:
  environment:
    - QDRANT__CLUSTER__ENABLED=true
    - QDRANT__CLUSTER__NODE_ID=2

qdrant-node-3:
  environment:
    - QDRANT__CLUSTER__ENABLED=true
    - QDRANT__CLUSTER__NODE_ID=3
```

### Vertical Scaling

**When to Scale Vertically**:
- Single database instance hitting limits
- Ollama inference needs more GPU memory
- Redis needs more memory for cache

**Example: Increase Resources**:
```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '8'    # Was 4
          memory: 16G  # Was 8G
```

### Auto-Scaling Rules

```yaml
# Example Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: finance-agent-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: finance-agent-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

---

## Monitoring and Observability

### Prometheus Metrics

```python
# app/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Agent metrics
agent_execution_duration = Histogram(
    'agent_execution_duration_seconds',
    'Time spent in agent execution',
    ['agent_name', 'query_type']
)

agent_token_usage = Histogram(
    'agent_token_usage',
    'Tokens used per agent execution',
    ['agent_name', 'model']
)

agent_errors_total = Counter(
    'agent_errors_total',
    'Total agent execution errors',
    ['agent_name', 'error_type']
)

# System metrics
active_queries = Gauge(
    'active_queries',
    'Number of currently active queries'
)

# Tool metrics
tool_calls_total = Counter(
    'tool_calls_total',
    'Total tool invocations',
    ['tool_name', 'success']
)

tool_duration = Histogram(
    'tool_duration_seconds',
    'Tool execution time',
    ['tool_name']
)

# Quality metrics
response_quality_score = Histogram(
    'response_quality_score',
    'LLM-as-judge quality scores',
    ['metric_type']
)


# Usage in code
@app.post("/api/v2/query-multi-agent")
async def query_endpoint(query: QueryRequest):
    start_time = time.time()
    active_queries.inc()
    
    try:
        result = await execute_query(query)
        
        # Record metrics
        http_requests_total.labels(
            method="POST",
            endpoint="/query-multi-agent",
            status="200"
        ).inc()
        
        duration = time.time() - start_time
        agent_execution_duration.labels(
            agent_name="lead_agent",
            query_type=result["query_type"]
        ).observe(duration)
        
        agent_token_usage.labels(
            agent_name="lead_agent",
            model="llama3.1"
        ).observe(result["token_usage"]["total"])
        
        return result
        
    except Exception as e:
        agent_errors_total.labels(
            agent_name="lead_agent",
            error_type=type(e).__name__
        ).inc()
        raise
        
    finally:
        active_queries.dec()
```

### Grafana Dashboards

#### Dashboard 1: System Overview
```json
{
  "dashboard": {
    "title": "Finance Agent - System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          "rate(http_requests_total[5m])"
        ]
      },
      {
        "title": "Success Rate",
        "targets": [
          "sum(rate(http_requests_total{status='200'}[5m])) / sum(rate(http_requests_total[5m]))"
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          "histogram_quantile(0.95, rate(agent_execution_duration_seconds_bucket[5m]))"
        ]
      },
      {
        "title": "Active Queries",
        "targets": [
          "active_queries"
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          "rate(agent_errors_total[5m])"
        ]
      }
    ]
  }
}
```

#### Dashboard 2: Cost and Token Usage
```json
{
  "dashboard": {
    "title": "Finance Agent - Cost Monitoring",
    "panels": [
      {
        "title": "Tokens per Minute",
        "targets": [
          "rate(agent_token_usage_sum[1m])"
        ]
      },
      {
        "title": "Estimated Cost per Hour",
        "targets": [
          "rate(agent_token_usage_sum[1h]) * 0.00002"  # $0.02 per 1K tokens
        ]
      },
      {
        "title": "Token Distribution by Model",
        "targets": [
          "sum(rate(agent_token_usage_sum[5m])) by (model)"
        ]
      },
      {
        "title": "Average Tokens per Query",
        "targets": [
          "rate(agent_token_usage_sum[5m]) / rate(http_requests_total[5m])"
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
# prometheus/alerts.yml

groups:
  - name: finance_agent_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (sum(rate(agent_errors_total[5m])) / sum(rate(http_requests_total[5m]))) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(agent_execution_duration_seconds_bucket[5m])) > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency is high"
          description: "P95 latency is {{ $value }}s"
      
      # Service down
      - alert: ServiceDown
        expr: up{job="finance-agent-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.instance }} has been down for >2 minutes"
      
      # High cost
      - alert: HighTokenUsage
        expr: |
          rate(agent_token_usage_sum[1h]) > 1000000
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Token usage is high"
          description: "Using {{ $value }} tokens/hour (~${{ $value | humanize }} * 0.00002)"
      
      # Database connection issues
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          pg_stat_database_numbackends / pg_settings_max_connections > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool near limit"
          description: "{{ $value | humanizePercentage }} of connections in use"
      
      # Qdrant issues
      - alert: QdrantHighLatency
        expr: |
          qdrant_search_duration_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Qdrant search latency high"
          description: "Average search time is {{ $value }}s"
```

### Logging Strategy

```python
# app/logging_config.py

import logging
import structlog
from pythonjsonlogger import jsonlogger


def configure_logging():
    """Configure structured logging."""
    
    # JSON formatter for structured logs
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={
            'asctime': 'timestamp',
            'name': 'logger',
            'levelname': 'level'
        }
    )
    logHandler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(logHandler)
    root_logger.setLevel(logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Usage in application
logger = structlog.get_logger()

logger.info(
    "agent_execution_started",
    agent="lead_agent",
    user_id=user_id,
    session_id=session_id,
    query_type="complex"
)

logger.error(
    "tool_execution_failed",
    tool="sec_search",
    error=str(error),
    ticker="AAPL",
    retry_count=3
)
```

---

## Cost Optimization

### Token Usage Optimization

```python
# app/optimization/token_optimizer.py

class TokenOptimizer:
    """Strategies to reduce token usage and costs."""
    
    @staticmethod
    async def use_cached_embeddings(text: str) -> List[float]:
        """Cache embeddings to avoid regenerating."""
        cache_key = f"embedding:{hash(text)}"
        
        # Check Redis cache
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Generate and cache
        embedding = await generate_embedding(text)
        await redis_client.setex(
            cache_key,
            3600 * 24,  # 24 hour TTL
            json.dumps(embedding)
        )
        return embedding
    
    @staticmethod
    async def use_smaller_model_for_simple_tasks(
        task_complexity: str
    ) -> str:
        """Choose model based on task complexity."""
        model_mapping = {
            "simple": "phi3:mini",          # Cheap, fast
            "medium": "llama3.1:8b",       # Balanced
            "complex": "llama3.1:70b"      # Expensive, best quality
        }
        return model_mapping.get(task_complexity, "llama3.1:8b")
    
    @staticmethod
    async def compress_context_window(
        chunks: List[str],
        max_tokens: int = 4000
    ) -> List[str]:
        """Compress context to fit token budget."""
        # Use extractive summarization for long contexts
        if estimate_tokens(chunks) > max_tokens:
            # Keep most relevant chunks
            ranked_chunks = rank_by_relevance(chunks)
            selected = []
            token_count = 0
            
            for chunk in ranked_chunks:
                chunk_tokens = estimate_tokens([chunk])
                if token_count + chunk_tokens <= max_tokens:
                    selected.append(chunk)
                    token_count += chunk_tokens
                else:
                    break
            
            return selected
        return chunks
    
    @staticmethod
    async def batch_similar_queries(
        queries: List[str],
        time_window_seconds: int = 5
    ) -> List[List[str]]:
        """Batch similar queries to share context."""
        # Group queries by similarity
        batches = []
        for query in queries:
            added = False
            for batch in batches:
                if is_similar(query, batch[0], threshold=0.8):
                    batch.append(query)
                    added = True
                    break
            if not added:
                batches.append([query])
        
        return batches


# Usage
async def execute_query_optimized(query: QueryRequest):
    # Choose appropriate model
    complexity = analyze_query_complexity(query.query)
    model = await TokenOptimizer.use_smaller_model_for_simple_tasks(complexity)
    
    # Use cached embeddings
    embedding = await TokenOptimizer.use_cached_embeddings(query.query)
    
    # Compress retrieved context
    chunks = await retrieve_chunks(embedding)
    compressed = await TokenOptimizer.compress_context_window(chunks)
    
    # Execute with optimized settings
    result = await execute_agent(query, model=model, context=compressed)
    
    return result
```

### Infrastructure Cost Optimization

```python
# app/optimization/infra_optimizer.py

class InfrastructureOptimizer:
    """Optimize infrastructure costs."""
    
    @staticmethod
    async def use_spot_instances_for_batch_work():
        """Use cheaper spot instances for non-critical work."""
        # AWS Spot instances can be 70-90% cheaper
        # Use for:
        # - Batch embedding generation
        # - Offline evaluation
        # - Model fine-tuning
        pass
    
    @staticmethod
    async def scale_down_during_low_traffic():
        """Reduce resources during off-peak hours."""
        current_hour = datetime.now().hour
        
        # Off-peak hours (midnight-6am)
        if 0 <= current_hour < 6:
            return {
                "api_replicas": 2,      # Down from 5
                "ollama_replicas": 1,   # Down from 3
                "cache_size_gb": 2      # Down from 8
            }
        # Peak hours
        else:
            return {
                "api_replicas": 5,
                "ollama_replicas": 3,
                "cache_size_gb": 8
            }
    
    @staticmethod
    async def use_cold_storage_for_old_data():
        """Move old data to cheaper storage."""
        # Move SEC filings older than 2 years to S3 Glacier
        # Cost: $0.004/GB vs $0.023/GB for S3 Standard
        cutoff_date = datetime.now() - timedelta(days=365*2)
        
        old_filings = db.query(Filing).filter(
            Filing.date < cutoff_date
        ).all()
        
        for filing in old_filings:
            # Archive to cold storage
            await archive_to_glacier(filing)
            # Remove from hot storage
            await remove_from_qdrant(filing.id)
```

---

## Operational Runbook

### Common Issues and Solutions

#### Issue 1: High Latency

**Symptoms**:
- P95 latency > 30 seconds
- User complaints about slow responses

**Diagnosis**:
```bash
# Check which component is slow
kubectl logs -f deployment/finance-agent-api | grep "duration"

# Check Qdrant performance
curl http://qdrant:6333/metrics | grep search_duration

# Check Ollama queue
curl http://ollama:11434/api/ps
```

**Solutions**:
1. Scale up API replicas: `kubectl scale deployment/api --replicas=10`
2. Add Ollama GPU nodes if inference is bottleneck
3. Increase Qdrant cache size
4. Enable response caching for common queries

#### Issue 2: Out of Memory (OOM)

**Symptoms**:
- Pods/containers restarting
- OOMKilled errors in logs

**Diagnosis**:
```bash
# Check memory usage
kubectl top pods
docker stats

# Check which service
kubectl describe pod <pod-name>
```

**Solutions**:
1. Increase memory limits in deployment
2. Reduce batch sizes in agent processing
3. Implement memory-efficient chunking strategy
4. Add memory limits to prevent runaway processes

#### Issue 3: Database Connection Pool Exhausted

**Symptoms**:
- "Too many connections" errors
- Queries hanging

**Diagnosis**:
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

**Solutions**:
1. Increase max_connections in PostgreSQL
2. Implement connection pooling (PgBouncer)
3. Fix long-running queries
4. Add query timeouts

#### Issue 4: Ollama Model Loading Slow

**Symptoms**:
- First query after restart very slow
- "Model loading" messages in logs

**Solutions**:
1. Pre-load models on startup:
```bash
# In Ollama startup script
ollama pull llama3.1:8b
ollama pull llama3.1:70b
```

2. Keep models in memory:
```yaml
environment:
  - OLLAMA_KEEP_ALIVE=24h  # Don't unload models
  - OLLAMA_MAX_LOADED_MODELS=3
```

#### Issue 5: Qdrant Search Timeouts

**Symptoms**:
- Queries failing with timeout errors
- Qdrant CPU/memory maxed out

**Solutions**:
1. Add Qdrant indexes:
```python
client.create_payload_index(
    collection_name="sec_filings",
    field_name="ticker",
    field_schema="keyword"
)
```

2. Use HNSW parameters tuning:
```python
from qdrant_client.models import HnswConfigDiff

client.update_collection(
    collection_name="sec_filings",
    hnsw_config=HnswConfigDiff(
        m=16,  # Default is 16
        ef_construct=200  # Increase for better quality
    )
)
```

3. Implement query result caching

### Deployment Checklist

**Pre-Deployment**:
- [ ] All tests passing (unit, integration, E2E)
- [ ] Performance tests completed
- [ ] Security scan completed
- [ ] Database migrations tested
- [ ] Backup strategy verified
- [ ] Rollback plan documented
- [ ] Monitoring dashboards updated
- [ ] Alert rules configured
- [ ] Load testing completed
- [ ] Documentation updated

**During Deployment**:
- [ ] Blue-green deployment or canary release
- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] Logs flowing to centralized system
- [ ] No errors in error tracking
- [ ] Database migrations applied successfully
- [ ] Cache warmed up

**Post-Deployment**:
- [ ] Monitor error rates for 1 hour
- [ ] Check latency metrics
- [ ] Verify token usage within budget
- [ ] Test critical user flows
- [ ] Review logs for anomalies
- [ ] Confirm alerting working
- [ ] Update runbook if needed

### Backup and Disaster Recovery

```bash
# PostgreSQL Backup (Daily)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres -U user financeagent | gzip > /backups/postgres_${DATE}.sql.gz

# Keep last 30 days
find /backups -name "postgres_*.sql.gz" -mtime +30 -delete

# Qdrant Backup (Weekly)
curl -X POST "http://qdrant:6333/collections/sec_filings/snapshots"
# Download snapshot
curl "http://qdrant:6333/collections/sec_filings/snapshots/{snapshot_name}" > /backups/qdrant_${DATE}.snapshot

# Redis Backup (Daily via AOF/RDB)
redis-cli BGSAVE
cp /data/dump.rdb /backups/redis_${DATE}.rdb

# Upload to S3
aws s3 sync /backups s3://finance-agent-backups/
```

---

## Summary

### Quick Reference

**Deployment Sizes**:
- **Development**: 1 server, no GPU, $50/month
- **Small Production**: 3-5 servers, 1 GPU, $2,000/month
- **Medium Production**: 10+ servers, 3 GPUs, $5,000/month
- **Large Production**: 20+ servers, 6+ GPUs, $10,000+/month

**Key Metrics to Monitor**:
1. Request rate and success rate
2. P95/P99 latency
3. Token usage and cost
4. Error rate by agent/tool
5. Database connection pool usage
6. GPU utilization
7. Cache hit rate

**Cost Optimization Priorities**:
1. Use local models (Ollama) for most tasks
2. Cache embeddings and common queries
3. Choose smaller models for simple tasks
4. Implement query result caching
5. Scale down during off-peak hours

**Production Readiness Checklist**:
- [x] Comprehensive test coverage
- [x] Monitoring and alerting configured
- [x] Backup and recovery procedures
- [x] Security hardening
- [x] Performance optimization
- [x] Documentation complete
- [x] Runbook for common issues
- [x] On-call rotation defined

---

## Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Qdrant Optimization](https://qdrant.tech/documentation/guides/optimization/)
