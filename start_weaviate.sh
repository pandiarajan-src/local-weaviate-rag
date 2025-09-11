#!/usr/bin/env bash
set -euo pipefail

# Load .env if present (for WEAVIATE_PORT/WEAVIATE_API_KEY etc.)
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi

docker compose -f docker-compose.weaviate.yml up -d
echo "Weaviate is starting on http://localhost:${WEAVIATE_PORT:-8080}"
