#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Resetting Weaviate database..."

# Stop Weaviate containers
echo "📥 Stopping Weaviate..."
docker compose -f docker-compose.weaviate.yml down

# Remove the data volume to completely reset the database
echo "🗑️  Removing Weaviate data volume..."
docker volume rm local-weaviate-rag_weaviate-data 2>/dev/null || true

# Start Weaviate again (will create a fresh volume)
echo "🚀 Starting fresh Weaviate instance..."
docker compose -f docker-compose.weaviate.yml up -d

# Load .env if present for port info
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi

echo "✅ Weaviate has been reset and is starting on http://localhost:${WEAVIATE_PORT:-8080}"
echo "   All previous data has been permanently deleted."