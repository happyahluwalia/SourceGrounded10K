#!/bin/bash
# Setup script for Ollama model

set -e

echo "🚀 Setting up Ollama for Finance Agent..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama is not running. Please start Ollama first."
    echo "   Docker: docker compose up -d ollama"
    echo "   Local: ollama serve"
    exit 1
fi

echo "✅ Ollama is running"

# Pull the model
echo "📥 Pulling gemma3:1b model (this may take a few minutes)..."
ollama pull gemma3:1b

echo "✅ Model downloaded successfully"

# Test the model
echo "🧪 Testing model..."
response=$(ollama run gemma3:1b "Say hello" --verbose=false 2>/dev/null || echo "")

if [ -n "$response" ]; then
    echo "✅ Model is working!"
    echo "   Response: $response"
else
    echo "⚠️  Model pulled but test failed. This might be normal."
fi

echo ""
echo "🎉 Ollama setup complete!"
echo ""
echo "Available models:"
ollama list

echo ""
echo "Next steps:"
echo "1. Start the backend: uvicorn app.api.main:app --reload"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Open http://localhost:3000"
