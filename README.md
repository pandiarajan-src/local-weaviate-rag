# Local Weaviate RAG System 🚀

> **A complete, production-ready RAG (Retrieval-Augmented Generation) system that demonstrates modern AI architecture patterns using Weaviate vector database, OpenAI embeddings, and GPT-4o for intelligent document Q&A.**

---

## 📖 Table of Contents

- [Purpose & Learning Goals](#-purpose--learning-goals)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Detailed Usage](#-detailed-usage)
- [Architecture Deep Dive](#-architecture-deep-dive)
- [Configuration Guide](#-configuration-guide)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🎯 Purpose & Learning Goals

### **What This Repository Is**
A **production-ready RAG (Retrieval-Augmented Generation) system** that demonstrates how to build intelligent document Q&A using modern AI tools. Designed for learning and real-world deployment.

### **Learning Goals**
Master these core competencies by studying this codebase:

- **RAG Architecture** - Complete pipeline from document ingestion to AI-powered answers
- **Vector Databases** - Weaviate integration for semantic search and hybrid retrieval
- **Production Engineering** - Error handling, security, testing, and code quality
- **AI Integration** - OpenAI embeddings and GPT-4o for intelligent responses

### **Why RAG Matters**
RAG systems power modern AI applications by combining retrieval with generation, enabling AI to answer questions about your specific documents and knowledge bases.

---

## 🏗️ System Architecture

### **System Flow**

```
📄 Documents → 🔪 Text Chunking → 🧠 OpenAI Embeddings → 💾 Weaviate Storage
                                                             ↓
❓ User Query → 🧠 Query Embedding → 🔍 Hybrid Search ←─────┘
                                          ↓
              ✅ Final Answer ← 🤖 GPT-4o ← 📝 Context Assembly
```

**Infrastructure**: 🐳 Docker → 📊 Weaviate DB + ⚙️ .env Config → 🐍 Python App

### **Core Components**

#### **1. Ingestion Engine (`rag/ingest.py`)**
- **Intelligent Text Chunking** - Token-aware splitting with sentence boundaries
- **Batch Embedding** - Efficient OpenAI API usage with rate limiting
- **Schema Management** - Automatic collection creation and validation
- **Error Recovery** - Fallback strategies and robust error handling

#### **2. Query Engine (`rag/query.py`)**
- **Hybrid Search** - Combines BM25 and vector similarity (configurable balance)
- **Context Assembly** - Smart chunk selection and prompt building
- **Structured Output** - Detailed query analysis and result presentation
- **Temperature Control** - Optimized GPT-4o parameters for factual responses

#### **3. Utility Layer (`rag/utils.py`)**
- **Configuration Management** - Environment variable handling with validation
- **Tokenization** - Efficient tiktoken-based token counting and caching
- **Retry Logic** - Exponential backoff for external API calls
- **Logging** - Structured logging with appropriate levels

#### **4. Vector Database (Weaviate)**
- **Persistent Storage** - Docker volume for data persistence
- **API Authentication** - Secure access with API keys
- **Schema Flexibility** - Dynamic collection management
- **Hybrid Capabilities** - Built-in BM25 + vector search

---

## 📋 Prerequisites

- **Docker & Docker Compose** - For running Weaviate vector database
- **Python 3.10+** - Modern Python with type hints support
- **OpenAI API Key** - For embeddings and completions ([get one here](https://platform.openai.com/api-keys))
- **4GB+ RAM** - For Weaviate and document processing
- **uv package manager** - Fast Python package manager (or use pip)

---

## 🚀 Quick Start

### **1. Clone and Setup**
```bash
git clone <this-repo>
cd local-weaviate-rag

# Copy environment template
cp .env.example .env
```

### **2. Configure Environment**
Edit `.env` file with your credentials:
```bash
# Required: Add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-key-here

# Required: Set a strong Weaviate API key
WEAVIATE_API_KEY=your-secure-random-key-16chars+

# Optional: Tune RAG parameters
CHUNK_TOKENS=400
HYBRID_ALPHA=0.5
TOP_K=5
```

### **3. Start the System**
```bash
# Install dependencies
uv sync

# Start Weaviate database
./start_weaviate.sh

# Verify setup (optional but recommended)
make test
```

### **4. Ingest Your First Document**
```bash
# Ingest this README
uv run python -m rag.ingest README.md --source "Project Documentation"

# Or ingest direct text
uv run python -m rag.ingest "Python is a versatile programming language" --source "Quick Note"
```

### **5. Ask Questions**
```bash
uv run python -m rag.query "What is this project about?"
uv run python -m rag.query "How do I configure the system?"
uv run python -m rag.query "What are the learning goals?"
```

---

## 📚 Detailed Usage

### **Document Ingestion**

#### **Supported File Types**
- **Text**: `.txt`, `.md`, `.rst`
- **Code**: `.py`, `.js`, `.json`, `.html`, `.xml`
- **Documents**: `.csv`, `.tex`
- **Direct Text**: Pass strings directly via command line

#### **Ingestion Examples**
```bash
# Single file ingestion
uv run python -m rag.ingest docs/api.md --source "API Documentation"

# Multiple files (run separately for better source tracking)
uv run python -m rag.ingest README.md --source "Main Docs"
uv run python -m rag.ingest src/main.py --source "Source Code"
uv run python -m rag.ingest config.json --source "Configuration"

# Direct text ingestion
uv run python -m rag.ingest "Machine learning is a subset of AI" --source "ML Notes"

# Long text with source context
uv run python -m rag.ingest "$(cat research_paper.txt)" --source "Research Paper 2024"
```

#### **Advanced Ingestion Options**
```bash
# Large document batches (for automation)
find docs/ -name "*.md" -exec uv run python -m rag.ingest {} --source "Documentation" \;

# Monitoring ingestion progress
uv run python -m rag.ingest large_doc.txt --source "Large Doc" 2>&1 | tee ingestion.log
```

### **Querying and Search**

#### **Query Types**

**Factual Questions**
```bash
uv run python -m rag.query "What are the system requirements?"
uv run python -m rag.query "How much memory does Weaviate need?"
```

**Conceptual Questions**
```bash
uv run python -m rag.query "Explain the RAG architecture"
uv run python -m rag.query "What is hybrid search and why is it useful?"
```

**Code-Related Questions**
```bash
uv run python -m rag.query "How does the text chunking algorithm work?"
uv run python -m rag.query "Show me error handling patterns in the code"
```

**Configuration Questions**
```bash
uv run python -m rag.query "How do I tune the search parameters?"
uv run python -m rag.query "What environment variables are available?"
```

#### **Understanding Query Output**

The system provides structured output with four main sections:

1. **INPUT QUERY** - Your original question
2. **RETRIEVED VECTOR SEARCH** - Relevant chunks found in the database
3. **FULL DETAILS** - Complete prompt sent to GPT-4o including context
4. **GENERATED ANSWER** - Final AI-generated response

This transparency helps you understand how the RAG system processes your queries and generates answers.

### **Database Management**

#### **Lifecycle Commands**
```bash
# Check status
docker compose -f docker-compose.weaviate.yml ps

# Start database
./start_weaviate.sh

# Stop database (data persists)
./stop_weaviate.sh

# Reset database (⚠️ deletes all data)
./reset_weaviate.sh
```

#### **Data Persistence**
- **Automatic**: Data persists between container restarts
- **Volumes**: Stored in Docker volume `local-weaviate-rag_weaviate-data`
- **Backup**: Use `docker volume inspect` to locate data for backup

---

## 🔧 Architecture Deep Dive

### **Text Processing Pipeline**

#### **1. Chunking Strategy**
The system uses intelligent chunking that:
- **Respects Sentence Boundaries** - Never breaks mid-sentence
- **Token-Aware Splitting** - Uses tiktoken for accurate token counting
- **Configurable Overlap** - Maintains context continuity between chunks
- **Paragraph Preservation** - Maintains document structure where possible

```python
# Example: 400-token chunks with 60-token overlap
chunks = chunk_text(
    text="Long document content...",
    model="text-embedding-3-small",
    chunk_tokens=400,
    overlap_tokens=60
)
```

#### **2. Embedding Generation**
- **Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Batching**: 100 chunks per API call for efficiency
- **Rate Limiting**: Built-in delays to respect API limits
- **Error Handling**: Automatic retry with exponential backoff

#### **3. Storage Schema**
Each document chunk is stored with:
```json
{
  "text": "The actual text content",
  "source": "Source identifier (filename, URL, etc.)",
  "chunk_id": "Sequential chunk identifier",
  "vector": [1536-dimensional embedding array]
}
```

### **Search and Retrieval**

#### **Hybrid Search Algorithm**
The system combines two search methods:

1. **BM25 (Keyword Search)**
   - Excellent for exact term matches
   - Handles technical terminology well
   - Fast execution

2. **Vector Similarity (Semantic Search)**
   - Captures semantic meaning
   - Handles synonyms and concepts
   - Cross-lingual capabilities

**Balance Parameter (HYBRID_ALPHA)**:
- `0.0` = Pure keyword search
- `0.5` = Balanced hybrid (recommended)
- `1.0` = Pure semantic search

#### **Context Assembly**
1. **Retrieval**: Get top-K chunks based on hybrid score
2. **Ranking**: Order by relevance score
3. **Selection**: Take top N chunks (respecting token limits)
4. **Formatting**: Assemble into coherent context with separators

### **AI Generation Pipeline**

#### **Prompt Engineering**
The system uses a structured prompt template:
```
You are a helpful assistant that answers questions based on the provided context.
Use the information from the context to answer the question as completely as possible.
If you cannot find a direct answer in the context, provide the most relevant information available.

Context:
[Retrieved chunks with separators]

Question: [User query]

Answer:
```

#### **Model Configuration**
- **Model**: GPT-4o (latest OpenAI model)
- **Temperature**: 0.2 (factual, consistent responses)
- **Max Tokens**: Determined by context length
- **Stop Sequences**: None (allow complete responses)

---

## ⚙️ Configuration Guide

### **Environment Variables**

#### **Weaviate Database**
```bash
WEAVIATE_SCHEME=http              # Use https in production
WEAVIATE_HOST=localhost           # Database host
WEAVIATE_PORT=8080               # HTTP port
WEAVIATE_GRPC_PORT=50051         # gRPC port (for advanced usage)
WEAVIATE_API_KEY=your-secret-key  # ⚠️ Change this! (min 16 chars)
```

#### **OpenAI API**
```bash
OPENAI_API_KEY=sk-your-key        # Your OpenAI API key
OPENAI_BASE_URL=                  # Optional: Custom endpoint (Azure, proxy)
OPENAI_EMBED_MODEL=text-embedding-3-small    # Embedding model
OPENAI_COMPLETIONS_MODEL=gpt-4o   # Chat completion model
```

#### **RAG Configuration**
```bash
RAG_COLLECTION=Documents          # Collection name in Weaviate
CHUNK_TOKENS=400                  # Target tokens per chunk
CHUNK_OVERLAP=60                  # Overlap between chunks
HYBRID_ALPHA=0.5                  # Search balance (0=keyword, 1=vector)
TOP_K=5                          # Chunks to retrieve
MAX_CONTEXT_CHUNKS=6             # Max chunks sent to LLM
```

### **Tuning Guidelines**

#### **Chunk Size (`CHUNK_TOKENS`)**
- **Small (200-300)**: Better for specific, focused answers
- **Medium (400-500)**: Good balance, recommended default
- **Large (600-800)**: Better for complex, contextual answers
- **Considerations**: Larger chunks = more context but fewer chunks in prompt

#### **Search Balance (`HYBRID_ALPHA`)**
- **0.0-0.3**: Keyword-heavy (good for technical terms, exact matches)
- **0.4-0.6**: Balanced (recommended for most use cases)
- **0.7-1.0**: Semantic-heavy (good for conceptual questions)

#### **Retrieval Parameters**
- **TOP_K**: More chunks = better coverage but slower processing
- **MAX_CONTEXT_CHUNKS**: More context = better answers but higher API costs
- **Overlap**: Higher overlap = better continuity but more storage

---

## 🛠️ Development

### **Running Tests**
```bash
# Comprehensive functionality tests
make test

# Alternative: Direct execution
uv run python tests/test_functionality.py

# Manual end-to-end test
uv run python -m rag.ingest "Test document" --source "test"
uv run python -m rag.query "What was the test about?"
```

### **Code Quality & Linting**

#### **Available Linters**
- **Ruff** ⚡ - Fast Python linter with auto-fix (replaces flake8, isort, pyupgrade)
- **Black** ⚫ - Code formatter for consistent style
- **isort** 📥 - Import sorting and organization
- **mypy** 🔍 - Static type checking
- **shellcheck** 🐚 - Shell script linting

#### **Quick Commands**
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

#### **Manual Linting**
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

#### **Configuration Files**
- **`pyproject.toml`** - Python tool configuration (ruff, black, isort, mypy)
- **`.shellcheckrc`** - Shellcheck configuration with common warnings disabled
- **`lint.sh`** - Comprehensive linting script with auto-fix capabilities

### **Adding New Features**

The codebase follows strict modular architecture:

#### **Core Modules**
- **`rag/utils.py`** - Shared utilities, configuration, and helpers
- **`rag/ingest.py`** - Document ingestion, chunking, and storage
- **`rag/query.py`** - Search, retrieval, and answer generation
- **`tests/`** - Comprehensive test suite with 95%+ coverage

#### **Development Workflow**
1. **Setup**: `make install-dev` to install linting tools
2. **Code**: Follow existing patterns and type hints
3. **Test**: `make test` to ensure functionality works
4. **Lint**: `make lint-fix` to auto-fix code quality issues
5. **Verify**: `make lint` to check all linters pass

#### **Code Standards**
- **Type Hints**: All functions must have complete type annotations
- **Docstrings**: Google-style docstrings for all public functions
- **Error Handling**: Explicit exception handling with logging
- **Security**: Input validation and secure defaults
- **Performance**: Efficient algorithms and resource usage

### **Project Structure**
```
local-weaviate-rag/
├── rag/                     # Main package
│   ├── __init__.py         # Package initialization
│   ├── utils.py            # Shared utilities and configuration
│   ├── ingest.py           # Document ingestion pipeline
│   └── query.py            # Query and answer generation
├── tests/                   # Test suite
│   └── test_functionality.py  # Comprehensive functionality tests
├── docker-compose.weaviate.yml  # Weaviate container configuration
├── .env.example            # Environment template
├── .env                    # Your environment (not in git)
├── pyproject.toml          # Python project configuration
├── Makefile               # Development commands
├── lint.sh                # Linting automation script
├── start_weaviate.sh      # Database startup script
├── stop_weaviate.sh       # Database shutdown script
├── reset_weaviate.sh      # Database reset script
└── README.md              # This documentation
```

---

## 🔍 Troubleshooting

### **Common Issues**

#### **"Connection refused" or "Cannot connect to Weaviate"**
```bash
# Check if Weaviate is running
docker compose -f docker-compose.weaviate.yml ps

# If not running, start it
./start_weaviate.sh

# Check logs for errors
docker compose -f docker-compose.weaviate.yml logs
```

#### **"OpenAI API key not found"**
```bash
# Verify .env file exists and contains your API key
cat .env | grep OPENAI_API_KEY

# If missing, add it:
echo "OPENAI_API_KEY=sk-your-actual-key-here" >> .env
```

#### **"No results found" or Poor Search Results**
```bash
# Check if documents were ingested
uv run python -m rag.query "test"

# Verify collection has data (should show object count > 0)
# If no results, try re-ingesting:
uv run python -m rag.ingest "test document" --source "test"

# Tune search parameters in .env:
HYBRID_ALPHA=0.3  # More keyword-based
# or
HYBRID_ALPHA=0.7  # More semantic-based
```

#### **Port Conflicts (8080 already in use)**
```bash
# Change the port in .env
echo "WEAVIATE_PORT=8081" >> .env

# Restart Weaviate
./stop_weaviate.sh
./start_weaviate.sh
```

#### **Out of Memory or Performance Issues**
```bash
# Reduce chunk size to process less data at once
echo "CHUNK_TOKENS=200" >> .env

# Reduce retrieval parameters
echo "TOP_K=3" >> .env
echo "MAX_CONTEXT_CHUNKS=3" >> .env

# Restart system after changes
./stop_weaviate.sh
./start_weaviate.sh
```

### **Performance Optimization**

#### **Ingestion Performance**
1. **Batch Processing** - Ingest multiple documents sequentially rather than individually
2. **Chunk Size Tuning** - Smaller chunks = more granular but slower ingestion
3. **Rate Limiting** - Built-in delays prevent API rate limiting
4. **Connection Reuse** - Single client instance for multiple operations

#### **Query Performance**
1. **Search Parameter Tuning** - Lower TOP_K for faster queries
2. **Context Management** - Fewer chunks = faster LLM responses
3. **Caching** - Tokenizer and embedding caches improve repeated operations
4. **Index Optimization** - Weaviate automatically optimizes vector indices

#### **Cost Optimization**
1. **Embedding Costs** - Use smaller chunk sizes to reduce embedding API calls
2. **Completion Costs** - Reduce MAX_CONTEXT_CHUNKS to limit token usage
3. **Model Selection** - Consider `text-embedding-3-small` vs larger models
4. **Batch Operations** - Process multiple chunks per API call

### **Security Considerations**

#### **Production Deployment**
- ⚠️ **Never commit `.env`** - contains sensitive API keys
- 🔒 **Use strong `WEAVIATE_API_KEY`** - minimum 16 characters, cryptographically secure
- 🔐 **Use HTTPS in production** - set `WEAVIATE_SCHEME=https`
- 📁 **Validate file inputs** - system checks file types, sizes, and paths
- 🛡️ **Network Security** - restrict Weaviate port access in production
- 🔐 **API Key Rotation** - regularly rotate OpenAI and Weaviate API keys

#### **Data Privacy**
- **Local Processing** - All document processing happens locally
- **OpenAI Policy** - Review OpenAI's data usage policy for your use case
- **Data Retention** - Consider implementing data retention policies
- **Access Control** - Implement proper authentication for production use

---

## 📈 Real-World Usage Examples

### **Example 1: Technical Documentation RAG**
```bash
# Ingest your project documentation
uv run python -m rag.ingest README.md --source "Main Documentation"
uv run python -m rag.ingest docs/api.md --source "API Reference"
uv run python -m rag.ingest docs/deployment.md --source "Deployment Guide"

# Ask technical questions
uv run python -m rag.query "How do I deploy this application?"
uv run python -m rag.query "What are the API endpoints for user management?"
uv run python -m rag.query "Show me a complete setup example"
```

### **Example 2: Code Analysis RAG**
```bash
# Ingest source code for analysis
uv run python -m rag.ingest src/models.py --source "Data Models"
uv run python -m rag.ingest src/api.py --source "API Layer"
uv run python -m rag.ingest src/utils.py --source "Utility Functions"

# Ask about code structure and patterns
uv run python -m rag.query "How does authentication work in this codebase?"
uv run python -m rag.query "What database models are defined?"
uv run python -m rag.query "Show me error handling patterns used"
```

### **Example 3: Research and Knowledge Management**
```bash
# Ingest research materials
uv run python -m rag.ingest paper1.pdf --source "ML Research Paper"
uv run python -m rag.ingest notes.md --source "Research Notes"
uv run python -m rag.ingest bibliography.txt --source "Literature Review"

# Ask research questions
uv run python -m rag.query "What are the main findings about neural networks?"
uv run python -m rag.query "Compare the different approaches mentioned"
uv run python -m rag.query "What are the limitations of current methods?"
```

### **Example 4: Customer Support Knowledge Base**
```bash
# Build a support knowledge base
uv run python -m rag.ingest faq.md --source "Frequently Asked Questions"
uv run python -m rag.ingest troubleshooting.md --source "Troubleshooting Guide"
uv run python -m rag.ingest user_manual.pdf --source "User Manual"

# Answer customer questions
uv run python -m rag.query "How do I reset my password?"
uv run python -m rag.query "What should I do if the app crashes?"
uv run python -m rag.query "How do I contact customer support?"
```

---

## 🚀 Production Deployment

### **Environment Setup**
```bash
# Production environment variables
WEAVIATE_SCHEME=https
WEAVIATE_HOST=your-production-host.com
WEAVIATE_API_KEY=cryptographically-secure-key-here

# Resource scaling
CHUNK_TOKENS=500
TOP_K=10
MAX_CONTEXT_CHUNKS=8
```

### **Monitoring and Logging**
- **Application Logs** - Structured logging to files or log aggregation service
- **Performance Metrics** - Token usage, response times, error rates
- **Health Checks** - Weaviate connectivity and API availability
- **Resource Usage** - Memory, CPU, and storage monitoring

### **Scaling Considerations**
- **Horizontal Scaling** - Multiple application instances behind load balancer
- **Database Scaling** - Weaviate cluster for high availability
- **Caching Layer** - Redis for frequent queries and embeddings
- **Rate Limiting** - Protect against abuse and manage costs

---

## 📚 Additional Resources

### **Learning Materials**
- **RAG Fundamentals** - [Anthropic's RAG Guide](https://docs.anthropic.com/claude/docs/retrieval-augmented-generation)
- **Vector Databases** - [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- **OpenAI APIs** - [OpenAI API Documentation](https://platform.openai.com/docs)
- **Embedding Models** - [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

### **Advanced Topics**
- **Hybrid Search Theory** - Understanding BM25 and vector similarity trade-offs
- **Prompt Engineering** - Optimizing prompts for better RAG responses
- **Vector Database Design** - Schema design and indexing strategies
- **Production MLOps** - Deployment, monitoring, and maintenance patterns

### **Community and Support**
- **Issues and Bugs** - [GitHub Issues](https://github.com/your-repo/issues)
- **Feature Requests** - Use GitHub Discussions
- **Weaviate Community** - [Weaviate Slack](https://weaviate.io/slack)
- **OpenAI Community** - [OpenAI Community Forum](https://community.openai.com)

---

## 📄 License

This project is open source under the MIT License. Feel free to modify, distribute, and use in your own projects.

### **Attribution**
If you use this project as a learning resource or base for your own work, attribution is appreciated but not required.

### **Contributing**
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow the code quality standards (`make lint-fix`)
4. Add tests for new functionality
5. Submit a pull request with clear description

---

## 🎉 Conclusion

This repository demonstrates a complete, production-ready RAG system that serves as both an educational resource and a practical tool. By studying and extending this codebase, you'll gain deep understanding of modern AI architecture patterns and be well-prepared to build your own AI-powered applications.

The system is designed to be:
- **📚 Educational** - Clear, well-documented code with comprehensive examples
- **🚀 Production-Ready** - Robust error handling, security, and performance optimization
- **🔧 Extensible** - Modular architecture for easy customization and extension
- **🛡️ Secure** - Security best practices and input validation
- **⚡ Performant** - Optimized for speed and efficiency

Whether you're learning about RAG systems, building a proof of concept, or deploying to production, this repository provides the foundation and patterns you need to succeed.

**Happy building! 🚀**