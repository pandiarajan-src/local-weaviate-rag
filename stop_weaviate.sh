#!/bin/bash

# Stop Weaviate Docker container
echo "Stopping Weaviate container..."

# Check if container is running
if [ "$(docker ps -q -f name=weaviate)" ]; then
    echo "Stopping Weaviate container..."
    docker stop weaviate
    echo "Weaviate container stopped"
else
    echo "Weaviate container is not running"
fi

# Optional: Remove the container (uncomment if you want to remove it)
# echo "Removing Weaviate container..."
# docker rm weaviate
# echo "Weaviate container removed"

# Optional: Remove the volume (uncomment if you want to remove all data)
# echo "Removing Weaviate data volume..."
# docker volume rm weaviate_data
# echo "Weaviate data volume removed"

echo "Done"