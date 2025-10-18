#!/bin/bash
# Ollama initialization script
# Automatically pulls required models on container startup

set -e

echo "🚀 Starting Ollama initialization..."

# Wait for Ollama service to be ready
echo "⏳ Waiting for Ollama service..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done
echo "✓ Ollama service is ready"

# Pull embedding model
echo "📥 Pulling embedding model: ${EMBEDDING_MODEL:-nomic-embed-text}..."
ollama pull "${EMBEDDING_MODEL:-nomic-embed-text}" || echo "⚠️  Failed to pull embedding model"

# Pull LLM model
echo "📥 Pulling LLM model: ${LLM_MODEL:-phi3:mini-instruct}..."
ollama pull "${LLM_MODEL:-phi3:mini-instruct}" || echo "⚠️  Failed to pull LLM model"

echo "✅ Ollama initialization complete!"
echo "📋 Available models:"
ollama list
