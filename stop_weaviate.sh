#!/bin/bash

echo "Stopping Weaviate local instance..."

# Stop and remove containers
docker-compose down

# Check if containers are stopped
if [ $? -eq 0 ]; then
    echo "✓ Weaviate has been stopped successfully"
    echo "Note: Data is preserved in Docker volume 'weaviate_data'"
    echo "To completely remove data, run: docker-compose down -v"
else
    echo "Error: Failed to stop Weaviate"
    exit 1
fi