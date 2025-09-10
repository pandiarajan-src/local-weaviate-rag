#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.weaviate.yml down
echo "Weaviate has been stopped.
"
