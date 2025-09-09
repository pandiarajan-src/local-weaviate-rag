#!/bin/bash

# Demo script for the local Weaviate RAG system
# This script demonstrates the complete workflow

echo "🚀 Local Weaviate RAG System Demo"
echo "=================================="
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your OPENAI_API_KEY"
    echo "   Then run this demo again."
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  Please set your OPENAI_API_KEY in the .env file"
    echo "   Edit .env and replace 'your_openai_api_key_here' with your actual API key"
    exit 1
fi

echo "✅ Environment configured"
echo

# Start Weaviate
echo "🐳 Starting Weaviate container..."
./start_weaviate.sh
echo

if [ $? -ne 0 ]; then
    echo "❌ Failed to start Weaviate. Please check Docker installation."
    exit 1
fi

# Wait a moment for Weaviate to be fully ready
echo "⏱️  Waiting for Weaviate to be fully ready..."
sleep 5

# Sample content to embed
SAMPLE_TEXT="Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience. Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data. Neural networks are computing systems inspired by biological neural networks and are used to estimate functions that depend on a large number of generally unknown inputs."

echo "📚 Embedding sample content about machine learning..."
python embed_text.py "$SAMPLE_TEXT" --source "ML Demo Content" --verbose
echo

if [ $? -ne 0 ]; then
    echo "❌ Failed to embed text. Please check your OpenAI API key."
    exit 1
fi

echo "✅ Content embedded successfully!"
echo

# Sample queries
QUERIES=(
    "What is machine learning?"
    "Explain deep learning"
    "How do neural networks work?"
)

echo "🔍 Running sample queries..."
echo

for query in "${QUERIES[@]}"; do
    echo "Query: $query"
    echo "----------------------------------------"
    python query_rag.py "$query"
    echo
    echo "========================================"
    echo
done

echo "🎉 Demo completed successfully!"
echo
echo "Next steps:"
echo "• Add your own content: python embed_text.py --file your_document.txt"
echo "• Ask your own questions: python query_rag.py 'Your question'"
echo "• Stop Weaviate when done: ./stop_weaviate.sh"