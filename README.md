# Local Weaviate RAG (OpenAI Embeddings + GPT-4o)

A minimal, secure, and fast local RAG (Retrieval-Augmented Generation) system that lets you chat with your documents using AI.

## Features
- 🐳 **Weaviate vector database** in Docker with API-key authentication and persistent storage
- 🧠 **OpenAI embeddings** (`text-embedding-3-small`) for semantic search
- 🔍 **Hybrid search** combining BM25 keyword search + vector similarity
- 🤖 **GPT-4o** for intelligent question answering from your documents
- ⚙️ **Simple configuration** via `.env` file
- 🔒 **Security-focused** with proper input validation and error handling

## Prerequisites
- Docker & Docker Compose
- Python 3.10+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Quick Start

### 1. Setup
```bash
# Clone and enter directory
git clone <this-repo> && cd local-weaviate-rag

# Copy and configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY and WEAVIATE_API_KEY
```

### 2. Start Weaviate Database
```bash
./start_weaviate.sh
# Wait ~10 seconds for Weaviate to fully start
```

### 3. Install Dependencies
```bash
# Using uv (recommended)
uv sync
```

### 4. Test Core Functionality (Optional)
```bash
# Run tests to verify everything is working
uv run python test_functionality.py
```

### 5. Ingest Your First Document
```bash
# Ingest a text file
uv run python -m rag.ingest README.md --source "Project Documentation"

# OR ingest raw text directly
uv run python -m rag.ingest "Python is a programming language" --source "Quick Note"
```

### 6. Ask Questions
```bash
uv run python -m rag.query "What is this project about?"
uv run python -m rag.query "How do I install the dependencies?"
```

## Detailed Usage Examples

### Document Ingestion

#### Ingest Different File Types
```bash
# Markdown files
uv run python -m rag.ingest docs/api.md --source "API Documentation"

# Python code
uv run python -m rag.ingest src/main.py --source "Source Code"

# Text files
uv run python -m rag.ingest notes.txt --source "Meeting Notes"

# JSON configuration
uv run python -m rag.ingest config.json --source "Configuration"

# Multiple files (run separately)
uv run python -m rag.ingest doc1.md --source "Documentation"
uv run python -m rag.ingest doc2.md --source "Documentation"  
uv run python -m rag.ingest code.py --source "Source Code"
```

#### Ingest Raw Text
```bash
# Short text snippets
uv run python -m rag.ingest "The API endpoint is /users/{id}" --source "API Notes"

# Longer text (use quotes)
uv run python -m rag.ingest "This is a long document about machine learning concepts..." --source "ML Guide"
```

### Querying Examples

#### Basic Questions
```bash
# Simple factual questions
uv run python -m rag.query "What is the main purpose of this project?"
uv run python -m rag.query "How do I configure the database?"
uv run python -m rag.query "What are the prerequisites?"

# Technical questions
uv run python -m rag.query "What Python version is required?"
uv run python -m rag.query "Which ports does Weaviate use?"
uv run python -m rag.query "How do I reset the database?"
```

#### Advanced Queries
```bash
# Comparative questions
uv run python -m rag.query "What's the difference between BM25 and vector search?"

# Step-by-step questions  
uv run python -m rag.query "Show me the complete setup process"

# Code-related questions
uv run python -m rag.query "How does the chunking algorithm work?"
uv run python -m rag.query "What error handling is implemented?"
```

## Database Management

### Reset Database (Clear All Data)
```bash
# ⚠️ WARNING: This permanently deletes all ingested documents
./reset_weaviate.sh
```

### Stop/Start Database
```bash
# Stop Weaviate
./stop_weaviate.sh

# Start Weaviate  
./start_weaviate.sh
```

### Check Database Status
```bash
# Check if Weaviate is running
docker compose -f docker-compose.weaviate.yml ps

# View logs
docker compose -f docker-compose.weaviate.yml logs -f
```

## Configuration Guide

### Environment Variables (`.env`)

```bash
# Weaviate Database
WEAVIATE_SCHEME=http              # Use https in production
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your-secret-key  # Change this!

# OpenAI API
OPENAI_API_KEY=sk-your-key        # Your OpenAI API key
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_COMPLETIONS_MODEL=gpt-4o

# RAG Configuration
RAG_COLLECTION=Documents          # Collection name
CHUNK_TOKENS=400                  # Text chunk size
CHUNK_OVERLAP=60                  # Overlap between chunks
HYBRID_ALPHA=0.5                  # 0=keyword only, 1=vector only
TOP_K=5                          # Results to retrieve
MAX_CONTEXT_CHUNKS=6             # Max chunks sent to GPT
```

### Tuning Parameters

#### Chunk Size (`CHUNK_TOKENS`)
- **Small (200-300)**: Better for precise, specific answers
- **Medium (400-500)**: Balanced, good default
- **Large (600-800)**: Better for complex, contextual answers

#### Search Balance (`HYBRID_ALPHA`)
- **0.0**: Pure keyword search (BM25) - good for exact term matches
- **0.5**: Balanced hybrid search - recommended default
- **1.0**: Pure vector search - good for semantic similarity

#### Retrieval (`TOP_K`, `MAX_CONTEXT_CHUNKS`)
- **TOP_K**: More results = better coverage, but slower
- **MAX_CONTEXT_CHUNKS**: More context = better answers, but higher cost

## Real-World Workflow Examples

### Example 1: Documentation RAG
```bash
# 1. Ingest your project docs
uv run python -m rag.ingest README.md --source "Main Documentation"
uv run python -m rag.ingest docs/api.md --source "API Reference"  
uv run python -m rag.ingest docs/tutorial.md --source "Tutorial"

# 2. Ask questions
uv run python -m rag.query "How do I authenticate with the API?"
uv run python -m rag.query "Show me a complete example"
```

### Example 2: Code Analysis RAG  
```bash
# 1. Ingest source code
uv run python -m rag.ingest src/models.py --source "Models"
uv run python -m rag.ingest src/api.py --source "API Layer"
uv run python -m rag.ingest src/utils.py --source "Utilities"

# 2. Ask about the code
uv run python -m rag.query "How does the authentication work?"
uv run python -m rag.query "What models are defined?"
uv run python -m rag.query "Find the error handling patterns"
```

### Example 3: Research RAG
```bash
# 1. Ingest research papers/notes
uv run python -m rag.ingest paper1.txt --source "ML Research"
uv run python -m rag.ingest notes.md --source "Research Notes" 
uv run python -m rag.ingest summary.txt --source "Literature Review"

# 2. Research questions
uv run python -m rag.query "What are the main findings about neural networks?"
uv run python -m rag.query "Compare the different approaches mentioned"
```

## Troubleshooting

### Common Issues

#### "Connection refused" or "Cannot connect to Weaviate"
```bash
# Check if Weaviate is running
docker compose -f docker-compose.weaviate.yml ps

# If not running, start it
./start_weaviate.sh

# Check logs for errors
docker compose -f docker-compose.weaviate.yml logs
```

#### "OpenAI API key not found"
```bash
# Make sure .env file exists and contains your API key
cat .env | grep OPENAI_API_KEY

# If missing, add it:
echo "OPENAI_API_KEY=sk-your-actual-key-here" >> .env
```

#### "No results found"
```bash
# Check if documents were ingested
uv run python -m rag.query "test"

# If no results, try ingesting again
uv run python -m rag.ingest "test document" --source "test"
```

#### Port conflicts (8080 already in use)
```bash
# Change the port in .env
echo "WEAVIATE_PORT=8081" >> .env

# Restart Weaviate
./stop_weaviate.sh
./start_weaviate.sh
```

### Performance Tips

1. **Batch ingestion**: Ingest multiple documents before querying
2. **Optimize chunk size**: Experiment with `CHUNK_TOKENS` for your use case  
3. **Tune search**: Adjust `HYBRID_ALPHA` based on your query patterns
4. **Monitor costs**: Check OpenAI usage, especially with large documents

### Security Notes

- ⚠️ **Never commit `.env`** - it contains your API keys
- 🔒 **Use strong `WEAVIATE_API_KEY`** - at least 16 characters
- 🔐 **Use HTTPS in production** - set `WEAVIATE_SCHEME=https`
- 📁 **Validate file inputs** - the system checks file types and sizes

## Development

### Running Tests
```bash
# Run comprehensive functionality tests
uv run python tests/test_functionality.py

# Or use the Makefile
make test

# Run basic end-to-end test (requires OpenAI API key and Weaviate)
uv run python -m rag.ingest "This is a test document" --source "test"
uv run python -m rag.query "What is this about?"
```

### Code Quality & Linting

This project includes comprehensive linting and code quality tools:

#### Available Linters
- **Ruff** - Fast Python linter with auto-fix (replaces flake8, isort, pyupgrade)
- **Black** - Code formatter for consistent style
- **isort** - Import sorting and organization
- **mypy** - Static type checking
- **shellcheck** - Shell script linting

#### Quick Commands
```bash
# Install development dependencies
make install-dev

# Run all linters with auto-fix
make lint-fix

# Check code quality without fixing
make lint

# Format code only
make format

# Clean up temporary files
make clean
```

#### Manual Linting
```bash
# Run all linters with auto-fix
./lint.sh --fix

# Run specific linters
./lint.sh --ruff-only --fix    # Fast Python linting + formatting
./lint.sh --mypy-only          # Type checking
./lint.sh --shellcheck-only    # Shell script checking

# Check without fixing
./lint.sh                     # All linters (check mode)
./lint.sh --quiet             # Minimal output
```

#### Configuration Files
- `pyproject.toml` - Python tool configuration (ruff, black, isort, mypy)
- `.shellcheckrc` - Shellcheck configuration with common warnings disabled
- `lint.sh` - Comprehensive linting script with auto-fix capabilities

### Adding New Features
The codebase is modular and follows strict code quality standards:
- `rag/utils.py` - Shared utilities and configuration
- `rag/ingest.py` - Document ingestion and chunking  
- `rag/query.py` - Search and answer generation
- `tests/` - Comprehensive test suite

**Before submitting changes:**
1. Run `make lint-fix` to auto-fix issues
2. Run `make test` to ensure functionality works
3. Check that all linters pass with `make lint`

## License

This project is open source. Feel free to modify and distribute.

