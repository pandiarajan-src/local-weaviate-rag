#!/bin/bash

# Start Weaviate Docker container
echo "Starting Weaviate container..."

# Check if container already exists
if [ "$(docker ps -q -f name=weaviate)" ]; then
    echo "Weaviate container is already running"
    exit 0
fi

# Check if container exists but is stopped
if [ "$(docker ps -aq -f status=exited -f name=weaviate)" ]; then
    echo "Starting existing Weaviate container..."
    docker start weaviate
else
    echo "Creating and starting new Weaviate container..."
    docker run -d \
        --name weaviate \
        -p 8080:8080 \
        -p 50051:50051 \
        -e QUERY_DEFAULTS_LIMIT=25 \
        -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
        -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
        -e DEFAULT_VECTORIZER_MODULE='none' \
        -e ENABLE_MODULES='text2vec-openai,generative-openai' \
        -e CLUSTER_HOSTNAME='node1' \
        -v weaviate_data:/var/lib/weaviate \
        semitechnologies/weaviate:1.22.4
fi

# Wait for Weaviate to be ready
echo "Waiting for Weaviate to be ready..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:8080/v1/meta > /dev/null 2>&1; then
        echo "Weaviate is ready and accessible at http://localhost:8080"
        exit 0
    fi
    echo "Waiting... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

echo "Timeout: Weaviate did not start within $timeout seconds"
echo "Check logs with: docker logs weaviate"
exit 1