#!/bin/bash
# Quick start script for Finance Agent

set -e

echo "🚀 Finance Agent Quick Start"
echo "=============================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your SEC_USER_AGENT email"
    echo "   Then run this script again"
    exit 1
fi

# Check if SEC_USER_AGENT is set
if ! grep -q "SEC_USER_AGENT=.*@.*" .env; then
    echo "⚠️  SEC_USER_AGENT not configured in .env"
    echo "   Please add your email for SEC API compliance"
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Start services
echo "🐳 Starting Docker services..."
docker compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check services
echo "🔍 Checking service health..."

# Check Postgres
until docker exec financeagent_postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL ready"

# Check Qdrant
until curl -s http://localhost:6333/health > /dev/null 2>&1; do
    echo "   Waiting for Qdrant..."
    sleep 2
done
echo "✅ Qdrant ready"

# Check Ollama (optional - skip if not running after 10 seconds)
echo "Checking for Ollama..."
OLLAMA_WAIT=0
MAX_OLLAMA_WAIT=5
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $OLLAMA_WAIT -ge $MAX_OLLAMA_WAIT ]; then
        echo "⚠️  Ollama not detected (this is optional)"
        echo "   You can use external LLM API or start Ollama later"
        break
    fi
    echo "   Waiting for Ollama... ($OLLAMA_WAIT/$MAX_OLLAMA_WAIT)"
    sleep 2
    OLLAMA_WAIT=$((OLLAMA_WAIT + 1))
done

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama ready"
fi

# Initialize databases
echo ""
echo "📊 Initializing databases..."
bash scripts/init_db.sh

# Setup Ollama model (if Ollama container exists)
echo ""
if docker ps --format '{{.Names}}' | grep -q 'financeagent_ollama'; then
    echo "🤖 Setting up Ollama model..."
    docker exec financeagent_ollama ollama pull gemma3:1b
else
    echo "⚠️  Ollama container not found. Start it with: docker compose up -d ollama"
    echo "   Or use external LLM API (OpenAI, etc.)"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📍 Services running at:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Qdrant: http://localhost:6333/dashboard"
echo ""
echo "🧪 Test the API:"
echo "   curl http://localhost:8000/api/health"
echo ""
echo "📦 Process a company:"
echo "   python scripts/process_company.py AAPL"
echo ""
echo "🌐 Start the frontend:"
echo "   cd frontend && npm install && npm run dev"
echo ""
echo "📖 View logs:"
echo "   docker compose logs -f"