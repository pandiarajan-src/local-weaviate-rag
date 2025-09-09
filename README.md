# Local Weaviate RAG System

A complete, production-ready Retrieval-Augmented Generation (RAG) system using Weaviate vector database, OpenAI embeddings, and GPT-4 Turbo. Designed for local deployment with focus on performance, security, and ease of use.

## 🚀 Features

- **Local Weaviate deployment** with Docker containers
- **Smart text chunking** with token-aware splitting and overlap
- **Hybrid search** combining vector similarity and keyword matching
- **OpenAI integration** with text-embedding-3-small and GPT-4 Turbo
- **Comprehensive error handling** and logging
- **Security-focused** environment variable configuration
- **Performance optimized** batch processing and connection management
- **Easy-to-use CLI tools** for embedding and querying

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.8 or higher
- OpenAI API key
- Git

## 🛠️ Quick Setup

### 1. Clone and Setup

```bash
git clone <repository-url>
cd local-weaviate-rag
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required configuration in `.env`:**
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Weaviate Configuration (defaults work for local setup)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_TIMEOUT=60

# Model Configuration
EMBEDDING_MODEL=text-embedding-3-small
GPT_MODEL=gpt-4-turbo-preview
MAX_TOKENS=4096
TEMPERATURE=0.1

# Text Processing Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_PER_QUERY=5

# Weaviate Collection Configuration
COLLECTION_NAME=DocumentChunks
VECTOR_DIMENSION=1536
```

### 4. Start Weaviate

```bash
# Start Weaviate container
./start_weaviate.sh
```

Wait for the message: "Weaviate is ready and accessible at http://localhost:8080"

## 📚 Usage

### Embedding Text

#### From Command Line Text:
```bash
python embed_text.py "Your text content here to be embedded and stored."
```

#### From File:
```bash
python embed_text.py --file path/to/your/document.txt
```

#### With Custom Source Name:
```bash
python embed_text.py --file document.txt --source "Technical Documentation"
```

#### Verbose Mode:
```bash
python embed_text.py "Content here" --verbose
```

### Querying the RAG System

#### Basic Query:
```bash
python query_rag.py "What is machine learning?"
```

#### Advanced Query with Options:
```bash
python query_rag.py --query "Explain neural networks" --max-results 3 --verbose
```

#### Adjust Search Parameters:
```bash
# More keyword-focused search (alpha=0.3)
python query_rag.py "specific term" --alpha 0.3

# More semantic search (alpha=0.9)
python query_rag.py "conceptual question" --alpha 0.9
```

## 🔧 Advanced Configuration

### Text Chunking Parameters

- **CHUNK_SIZE**: Maximum tokens per chunk (default: 1000)
- **CHUNK_OVERLAP**: Overlap tokens between chunks (default: 200)

### Search Parameters

- **MAX_CHUNKS_PER_QUERY**: Maximum context chunks for responses (default: 5)
- **Alpha**: Hybrid search weight (0.0=keyword, 1.0=vector, default: 0.7)

### Model Parameters

- **TEMPERATURE**: Response creativity (0.0=deterministic, 1.0=creative, default: 0.1)
- **MAX_TOKENS**: Maximum response length (default: 4096)

## 🐳 Container Management

### Start Weaviate:
```bash
./start_weaviate.sh
```

### Stop Weaviate:
```bash
./stop_weaviate.sh
```

### Check Weaviate Status:
```bash
curl http://localhost:8080/v1/meta
```

### View Container Logs:
```bash
docker logs weaviate
```

## 📊 Monitoring and Logs

### Application Logs:
- `embed_text.log` - Embedding operations log
- `query_rag.log` - Query operations log

### View Logs:
```bash
tail -f embed_text.log
tail -f query_rag.log
```

## 🔍 Troubleshooting

### Common Issues:

#### 1. Weaviate Connection Failed
```bash
# Check if container is running
docker ps | grep weaviate

# Restart Weaviate
./stop_weaviate.sh
./start_weaviate.sh
```

#### 2. OpenAI API Errors
```bash
# Verify API key in .env
grep OPENAI_API_KEY .env

# Check API quota: https://platform.openai.com/usage
```

#### 3. Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version
```

#### 4. Permission Errors
```bash
# Make scripts executable
chmod +x start_weaviate.sh stop_weaviate.sh
```

### Debug Mode:
```bash
# Enable verbose logging
python embed_text.py "text" --verbose
python query_rag.py "query" --verbose
```

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit `.env` file
2. **API Keys**: Use restricted OpenAI API keys
3. **Network**: Run Weaviate on localhost only
4. **Input Validation**: All inputs are validated and sanitized
5. **Error Handling**: Sensitive information not exposed in errors

## ⚡ Performance Optimization

### For Large Documents:
```bash
# Adjust chunk size for longer documents
export CHUNK_SIZE=1500
export CHUNK_OVERLAP=300
```

### For Better Search Results:
```bash
# Increase context chunks
export MAX_CHUNKS_PER_QUERY=7
```

### For Faster Responses:
```bash
# Reduce max tokens
export MAX_TOKENS=2048
```

## 📁 Project Structure

```
local-weaviate-rag/
├── embed_text.py          # Text embedding and storage
├── query_rag.py           # RAG querying system
├── start_weaviate.sh      # Start Weaviate container
├── stop_weaviate.sh       # Stop Weaviate container
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🚀 Getting Started Workflow

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   pip install -r requirements.txt
   ```

2. **Start Services**:
   ```bash
   ./start_weaviate.sh
   ```

3. **Add Content**:
   ```bash
   python embed_text.py --file your_document.txt
   ```

4. **Query Content**:
   ```bash
   python query_rag.py "Your question about the content"
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Open an issue on GitHub

---

**Happy RAG-ing! 🚀**