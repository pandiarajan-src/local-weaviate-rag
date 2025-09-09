#!/bin/bash
# 
# Complete RAG System Demo Script
# This script demonstrates the full workflow of the local Weaviate RAG system
#

echo "🚀 Local Weaviate RAG System Demo"
echo "================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Please create .env file from .env.example and add your OPENAI_API_KEY"
    echo "   cp .env.example .env"
    echo "   # Edit .env and add your OpenAI API key"
    exit 1
fi

# Create sample document
echo "📝 Creating sample document..."
mkdir -p /tmp/demo_docs
cat > /tmp/demo_docs/ai_overview.txt << 'EOF'
Artificial Intelligence Overview

Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that can think and learn like humans. AI systems can perform tasks that typically require human intelligence, such as visual perception, speech recognition, decision-making, and language translation.

Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms and statistical models to analyze data, identify patterns, and make predictions or decisions.

Deep Learning is a specialized area of machine learning that uses artificial neural networks with multiple layers to model and understand complex patterns in data. Deep learning has revolutionized fields like computer vision, natural language processing, and speech recognition.

Natural Language Processing (NLP) is the branch of AI that helps computers understand, interpret, and manipulate human language. NLP combines computational linguistics with statistical, machine learning, and deep learning models to enable computers to process human language in a valuable way.

Computer Vision is a field of AI that trains computers to interpret and understand the visual world. Using digital images from cameras and videos and deep learning models, machines can accurately identify and classify objects and react to what they "see."

The applications of AI are vast and growing, including autonomous vehicles, medical diagnosis, fraud detection, recommendation systems, chatbots, and many more areas that are transforming how we live and work.
EOF

echo "✅ Sample document created at /tmp/demo_docs/ai_overview.txt"

# Test setup
echo ""
echo "🧪 Testing system setup..."
python test_setup.py

if [ $? -ne 0 ]; then
    echo "❌ Setup test failed. Please fix the issues before proceeding."
    exit 1
fi

echo ""
echo "🐳 Starting Weaviate..."
./start_weaviate.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to start Weaviate"
    exit 1
fi

echo ""
echo "📊 Setting up Weaviate schema..."
python ingest_documents.py --setup-schema

if [ $? -ne 0 ]; then
    echo "❌ Failed to setup schema"
    ./stop_weaviate.sh
    exit 1
fi

echo ""
echo "📄 Ingesting sample document..."
python ingest_documents.py --file /tmp/demo_docs/ai_overview.txt --source "AI_Overview_Demo"

if [ $? -ne 0 ]; then
    echo "❌ Failed to ingest document"
    ./stop_weaviate.sh
    exit 1
fi

echo ""
echo "🎉 Demo setup complete!"
echo ""
echo "Now you can query the system. Here are some example queries to try:"
echo ""
echo "🔍 Example queries:"
echo "  • What is machine learning?"
echo "  • How does deep learning work?"
echo "  • What are the applications of AI?"
echo "  • Explain natural language processing"
echo ""
echo "💬 Start interactive mode:"
echo "  python query_rag.py --interactive"
echo ""
echo "📝 Or run a single query:"
echo "  python query_rag.py --query \"What is machine learning?\" --verbose"
echo ""
echo "🛑 When done, stop Weaviate:"
echo "  ./stop_weaviate.sh"
echo ""
echo "Happy querying! 🤖"