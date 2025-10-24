#!/bin/bash
# Universal GPU Deployment Script
# Auto-detects GPU and configures optimal settings for Finance Agent

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================================================="
echo "  Finance Agent - GPU Deployment"
echo "=========================================================================="
echo ""

# ============================================================================
# STEP 1: Detect GPU
# ============================================================================
log_info "Detecting GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    log_error "nvidia-smi not found. GPU drivers may not be installed."
    log_info "Install NVIDIA drivers first, then run this script again."
    exit 1
fi

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
GPU_VRAM_GB=$((GPU_VRAM / 1024))

log_success "Detected: $GPU_NAME with ${GPU_VRAM_GB}GB VRAM"
echo ""

# ============================================================================
# STEP 2: Auto-select model based on VRAM
# ============================================================================
log_info "Selecting optimal model for ${GPU_VRAM_GB}GB VRAM..."

if [ $GPU_VRAM_GB -ge 24 ]; then
    RECOMMENDED_MODEL="llama3.1:8b-instruct-q8_0"
    log_info "VRAM: ${GPU_VRAM_GB}GB - Can run 8B (Q8) or even 70B models"
    log_info "Recommended: $RECOMMENDED_MODEL (highest quality 8B)"
elif [ $GPU_VRAM_GB -ge 12 ]; then
    RECOMMENDED_MODEL="llama3.1:8b-instruct-q8_0"
    log_info "VRAM: ${GPU_VRAM_GB}GB - Perfect for 8B Q8 model"
    log_info "Recommended: $RECOMMENDED_MODEL"
elif [ $GPU_VRAM_GB -ge 8 ]; then
    RECOMMENDED_MODEL="llama3.1:8b-instruct"
    log_info "VRAM: ${GPU_VRAM_GB}GB - Using 8B Q4 model"
    log_info "Recommended: $RECOMMENDED_MODEL"
else
    log_error "VRAM: ${GPU_VRAM_GB}GB - Insufficient for LLM inference (need 8GB+)"
    exit 1
fi
echo ""

# ============================================================================
# STEP 3: Setup environment
# ============================================================================
log_info "Setting up environment..."

if [ ! -f ".env" ]; then
    if [ -f ".env.production.example" ]; then
        cp .env.production.example .env
        
        # Auto-configure model
        sed -i.bak "s|^OLLAMA_MODEL=.*|OLLAMA_MODEL=$RECOMMENDED_MODEL|" .env
        rm -f .env.bak
        
        # Generate secure passwords
        POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
        API_KEY=$(openssl rand -base64 32)
        
        sed -i.bak "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" .env
        sed -i.bak "s|API_KEY=.*|API_KEY=$API_KEY|" .env
        rm -f .env.bak
        
        log_success "Created .env with auto-configured settings"
        log_warning "IMPORTANT: Edit .env and set SEC_USER_AGENT with your email"
        echo ""
        read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit manually..."
        ${EDITOR:-nano} .env
    else
        log_error ".env.production.example not found"
        exit 1
    fi
else
    log_info ".env already exists, skipping..."
fi
echo ""

# ============================================================================
# STEP 4: Verify Docker GPU access
# ============================================================================
log_info "Verifying Docker GPU access..."

if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker first."
    log_info "Run: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

if docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
    log_success "Docker can access GPU"
else
    log_error "Docker cannot access GPU. Install nvidia-docker2"
    log_info "Run: sudo apt-get install -y nvidia-docker2 && sudo systemctl restart docker"
    exit 1
fi
echo ""

# ============================================================================
# STEP 5: Start services
# ============================================================================
log_info "Starting Docker services..."

if [ ! -f "docker-compose.prod.yml" ]; then
    log_error "docker-compose.prod.yml not found. Are you in the project root?"
    exit 1
fi

docker-compose -f docker-compose.prod.yml up -d

log_info "Waiting for services to initialize (30 seconds)..."
sleep 30
log_success "Services started"
echo ""

# ============================================================================
# STEP 6: Pull AI models
# ============================================================================
log_info "Pulling Ollama models (this takes 5-10 minutes)..."
log_info "Model: $RECOMMENDED_MODEL"

docker exec financeagent_ollama ollama pull $RECOMMENDED_MODEL &
PID1=$!

log_info "Model: nomic-embed-text"
docker exec financeagent_ollama ollama pull nomic-embed-text &
PID2=$!

wait $PID1
log_success "LLM model downloaded: $RECOMMENDED_MODEL"

wait $PID2
log_success "Embedding model downloaded: nomic-embed-text"
echo ""

# ============================================================================
# STEP 7: Initialize database
# ============================================================================
log_info "Initializing database..."

docker exec financeagent_backend python -c "
from app.models.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✓ Database initialized')
" 2>/dev/null && log_success "Database initialized" || log_warning "Database may already be initialized"
echo ""

# ============================================================================
# STEP 8: Verify deployment
# ============================================================================
log_info "Verifying deployment..."
sleep 10

# Health checks
BACKEND_OK=false
OLLAMA_OK=false
QDRANT_OK=false
POSTGRES_OK=false

if curl -s http://localhost:8000/api/health | grep -q "healthy" 2>/dev/null; then
    log_success "✓ Backend: http://localhost:8000"
    BACKEND_OK=true
else
    log_warning "✗ Backend: Not responding yet"
fi

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_success "✓ Ollama: http://localhost:11434"
    OLLAMA_OK=true
else
    log_warning "✗ Ollama: Not responding yet"
fi

if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    log_success "✓ Qdrant: http://localhost:6333"
    QDRANT_OK=true
else
    log_warning "✗ Qdrant: Not responding yet"
fi

if docker exec financeagent_postgres pg_isready -U postgres > /dev/null 2>&1; then
    log_success "✓ PostgreSQL: Running"
    POSTGRES_OK=true
else
    log_warning "✗ PostgreSQL: Not responding"
fi

echo ""
log_info "GPU Status:"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader

echo ""
echo "=========================================================================="
if [ "$BACKEND_OK" = true ] && [ "$OLLAMA_OK" = true ] && [ "$QDRANT_OK" = true ] && [ "$POSTGRES_OK" = true ]; then
    log_success "🚀 DEPLOYMENT COMPLETE! 🚀"
else
    log_warning "⚠️  DEPLOYMENT STARTED - Some services still initializing"
    echo ""
    echo "Wait 1-2 minutes and check:"
    echo "  docker-compose -f docker-compose.prod.yml ps"
    echo "  docker-compose -f docker-compose.prod.yml logs -f backend"
fi
echo "=========================================================================="
echo ""

# ============================================================================
# Configuration Summary
# ============================================================================
echo "📊 Configuration Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  GPU:              $GPU_NAME (${GPU_VRAM_GB}GB VRAM)"
echo "  LLM Model:        $RECOMMENDED_MODEL"
echo "  Embedding Model:  nomic-embed-text"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# Access Information
# ============================================================================
echo "🌐 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend:         http://localhost"
echo "  Backend API:      http://localhost:8000"
echo "  API Docs:         http://localhost:8000/docs"
echo "  Ollama:           http://localhost:11434"
echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# Test Commands
# ============================================================================
echo "🧪 Test Your Deployment:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "# Test query (first query takes ~60s to fetch SEC filing)"
echo "curl -X POST http://localhost:8000/api/query \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"What were Apple'\''s revenues?\", \"ticker\": \"AAPL\"}'"
echo ""
echo "# Monitor GPU"
echo "watch -n 1 nvidia-smi"
echo ""
echo "# View logs"
echo "docker-compose -f docker-compose.prod.yml logs -f backend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_success "🎉 All done! Your Finance Agent is ready to use! 🎉"
echo ""
