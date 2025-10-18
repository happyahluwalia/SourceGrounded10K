#!/bin/bash
# Initialize database and vector store

set -e

echo "🗄️  Initializing Finance Agent databases..."

# Check if services are running
echo "Checking services..."

# Check Postgres
if ! docker exec financeagent_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running"
    echo "   Start with: docker compose up -d postgres"
    exit 1
fi
echo "✅ PostgreSQL is ready"

# Check Qdrant
if ! curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "❌ Qdrant is not running"
    echo "   Start with: docker compose up -d qdrant"
    exit 1
fi
echo "✅ Qdrant is ready"

# Create database tables
echo "📊 Creating database tables..."
python -c "
from app.models.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"

# Initialize Qdrant collection
echo "🔍 Creating Qdrant collection..."
python -c "
from app.services.vector_store import VectorStore
vs = VectorStore()
vs.create_collection()
print('✅ Qdrant collection created')
"

echo ""
echo "🎉 Database initialization complete!"
echo ""
echo "Next steps:"
echo "1. Process a company: python scripts/process_company.py AAPL"
echo "2. Or start the API and let it auto-fetch: uvicorn app.api.main:app --reload"
