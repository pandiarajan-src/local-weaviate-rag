#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting Local Weaviate RAG API Server..."

# Load .env if present
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi

# Set default API port if not set
API_PORT=${API_PORT:-8001}

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
echo "🌐 Starting FastAPI server on http://localhost:${API_PORT}"
echo "📖 API Documentation: http://localhost:${API_PORT}/docs"
echo "🔍 Health Check: http://localhost:${API_PORT}/api/v1/health"
echo ""
echo "Press Ctrl+C to stop the server"

uv run uvicorn api.main:app --host 0.0.0.0 --port "${API_PORT}" --reload
