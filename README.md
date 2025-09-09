# Local Weaviate RAG System

A complete Retrieval-Augmented Generation (RAG) system using local Weaviate vector database, OpenAI's text-embedding-3-small for embeddings, and GPT-4.1 for inference.

## Features

- 🚀 Local Weaviate instance running in Docker
- 📄 Document chunking and embedding with OpenAI text-embedding-3-small
- 🔍 Hybrid search (vector + keyword) for optimal retrieval
- 🤖 Response generation using GPT-4.1
- 💬 Interactive query interface
- 🛠️ Easy setup and management scripts

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.8+
- OpenAI API key

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd local-weaviate-rag

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Test your setup
python test_setup.py
```

### 3. Start Weaviate

```bash
# Start local Weaviate instance
./start_weaviate.sh
```

### 4. Ingest Documents

```bash
# Setup Weaviate schema
python ingest_documents.py --setup-schema

# Ingest a text file
python ingest_documents.py --file path/to/your/document.txt

# Or ingest text directly
python ingest_documents.py --text "Your text content here" --source "manual_input"
```

### 5. Query the System

```bash
# Interactive mode (recommended)
python query_rag.py --interactive

# Single query
python query_rag.py --query "Your question here"

# Query with options
python query_rag.py --query "Your question" --search-type hybrid --limit 10 --verbose
```

### 6. Stop Weaviate

```bash
# Stop Weaviate when done
./stop_weaviate.sh
```

## Detailed Usage

### Starting and Stopping Weaviate

The system includes convenient scripts to manage the local Weaviate instance:

```bash
# Start Weaviate
./start_weaviate.sh
# ✓ Starts Docker container
# ✓ Waits for Weaviate to be ready
# ✓ Provides status confirmation

# Stop Weaviate
./stop_weaviate.sh
# ✓ Stops container gracefully
# ✓ Preserves data in Docker volume
```

### Document Ingestion

The `ingest_documents.py` script handles document processing:

#### Basic Usage

```bash
# Setup schema (run once)
python ingest_documents.py --setup-schema

# Ingest a file
python ingest_documents.py --file document.txt

# Ingest text directly
python ingest_documents.py --text "Content to ingest" --source "my_source"
```

#### Features

- **Smart Chunking**: Automatically chunks documents using token-based splitting
- **Overlap Support**: Configurable chunk overlap to maintain context
- **OpenAI Embeddings**: Uses text-embedding-3-small for high-quality embeddings
- **Metadata Preservation**: Tracks source, chunk positions, and token counts
- **Batch Processing**: Efficient batch uploads to Weaviate

### Querying the System

The `query_rag.py` script provides powerful querying capabilities:

#### Interactive Mode (Recommended)

```bash
python query_rag.py --interactive
```

Features:
- Continuous querying session
- Real-time responses
- Detailed result display
- Easy exit commands

#### Single Query Mode

```bash
# Basic query
python query_rag.py --query "What is machine learning?"

# Advanced options
python query_rag.py \
  --query "Explain neural networks" \
  --search-type hybrid \
  --limit 10 \
  --verbose \
  --output results.json
```

#### Search Types

- **Hybrid Search** (default): Combines vector similarity and keyword matching
- **Vector Search**: Pure semantic similarity search

### Configuration

Edit `.env` file to customize settings:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional customization
WEAVIATE_URL=http://localhost:8080
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4-turbo-preview
```

## System Architecture

```
User Query
    ↓
Query Processing (query_rag.py)
    ↓
Embedding Generation (OpenAI)
    ↓
Hybrid Search (Weaviate)
    ↓
Context Retrieval
    ↓
Response Generation (GPT-4.1)
    ↓
Final Answer
```

## Files Structure

```
local-weaviate-rag/
├── docker-compose.yml          # Weaviate Docker setup
├── start_weaviate.sh          # Start Weaviate script
├── stop_weaviate.sh           # Stop Weaviate script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── config.py                 # Configuration management
├── ingest_documents.py       # Document ingestion system
├── query_rag.py             # Query processing system
├── test_setup.py            # Setup validation script
└── README.md                # This file
```

## Error Handling

### Common Issues

1. **Docker not running**
   ```bash
   Error: Docker is not running. Please start Docker first.
   ```
   Solution: Start Docker Desktop or Docker service

2. **Missing OpenAI API key**
   ```bash
   Error: OPENAI_API_KEY is required. Please set it in .env file
   ```
   Solution: Add your API key to `.env` file

3. **Weaviate not responding**
   ```bash
   Error: Weaviate failed to start within 60 seconds
   ```
   Solution: Check Docker logs with `docker-compose logs weaviate`

4. **No documents found**
   ```bash
   I couldn't find any relevant documents to answer your question.
   ```
   Solution: Ingest documents first using `ingest_documents.py`

### Debugging

```bash
# Check Weaviate status
curl http://localhost:8080/v1/meta

# View Docker logs
docker-compose logs weaviate

# Check ingested documents count
# (Access Weaviate console at http://localhost:8080)
```

## Performance Tips

1. **Chunking**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` for your documents
2. **Search Results**: Use `--limit` to control context document count
3. **Search Type**: Use vector search for semantic queries, hybrid for mixed
4. **Batch Size**: Large documents are processed in batches automatically

## Examples

### Example 1: Technical Documentation

```bash
# Ingest API documentation
python ingest_documents.py --file api_docs.txt --source "API_Documentation"

# Query about specific endpoints
python query_rag.py --query "How do I authenticate with the API?"
```

### Example 2: Research Papers

```bash
# Ingest research paper
python ingest_documents.py --file research_paper.txt --source "ML_Research_2024"

# Ask research questions
python query_rag.py --query "What are the key findings about neural networks?" --verbose
```

### Example 3: Company Knowledge Base

```bash
# Ingest multiple documents
python ingest_documents.py --file policies.txt --source "HR_Policies"
python ingest_documents.py --file procedures.txt --source "IT_Procedures"

# Interactive querying
python query_rag.py --interactive
```

## Advanced Usage

### Custom System Prompts

Modify the `generate_response` method in `query_rag.py` to customize the AI behavior.

### Metadata Filtering

Extend the search methods in `WeaviateSearcher` to filter by source or other metadata.

### Multiple Collections

Modify `Config.COLLECTION_NAME` to use different collections for different document types.

## Troubleshooting

If you encounter issues:

1. Check all prerequisites are installed
2. Verify Docker is running and accessible
3. Ensure OpenAI API key is valid and has credits
4. Check Weaviate is responding at http://localhost:8080
5. Verify documents are ingested before querying

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the repository for license details.