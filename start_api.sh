#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting Local Weaviate RAG API Server..."

# Load .env if present
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi

# Check if Weaviate is running
echo "🔍 Checking Weaviate status..."
if ! docker compose -f docker-compose.weaviate.yml ps | grep -q "Up"; then
    echo "⚠️  Weaviate is not running. Starting Weaviate first..."
    ./start_weaviate.sh
    echo "⏳ Waiting for Weaviate to be ready..."
    sleep 10
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Start the API server
echo "🌐 Starting FastAPI server on http://localhost:8001"
echo "📖 API Documentation: http://localhost:8001/docs"
echo "🔍 Health Check: http://localhost:8001/api/v1/health"
echo ""
echo "Press Ctrl+C to stop the server"

uv run uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload