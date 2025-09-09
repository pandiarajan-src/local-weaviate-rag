#!/bin/bash

echo "Starting Weaviate local instance..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start Weaviate using Docker Compose
docker compose up -d

# Wait for Weaviate to be ready
echo "Waiting for Weaviate to be ready..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:8080/v1/meta > /dev/null 2>&1; then
        echo "✓ Weaviate is ready and running on http://localhost:8080"
        echo "✓ You can check the status at: http://localhost:8080/v1/meta"
        exit 0
    fi
    
    echo "Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

echo "Error: Weaviate failed to start within $timeout seconds"
echo "Check the logs with: docker compose logs weaviate"
exit 1