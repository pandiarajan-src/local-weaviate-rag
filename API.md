# FastAPI RAG Service Documentation

## Overview

The FastAPI RAG service provides REST API endpoints for document ingestion and intelligent querying using the local Weaviate RAG system. It offers the same functionality as the CLI tools but through a web-accessible interface.

## Quick Start

### 1. Start the Service
```bash
# Start Weaviate and API server
make start-api

# Or manually
./start_api.sh
```

### 2. Access the API
- **API Server**: http://localhost:${API_PORT:-8001}
- **Interactive Docs**: http://localhost:${API_PORT:-8001}/docs
- **Health Check**: http://localhost:${API_PORT:-8001}/api/v1/health

**Note**: The API port is configured via the `API_PORT` environment variable in `.env` (default: 8001)

### 3. Test the API
```bash
make test-api
```

## API Endpoints

### System Endpoints

#### Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-01T12:00:00",
  "dependencies": {
    "weaviate": "healthy",
    "openai": "healthy"
  }
}
```

### Ingestion Endpoints

#### Ingest Text
```http
POST /api/v1/ingest/text
Content-Type: application/json

{
  "text": "Your document content here...",
  "source": "Document Name",
  "metadata": {"category": "docs"}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully ingested 3 chunks",
  "chunks_created": 3,
  "collection": "Documents",
  "source": "Document Name",
  "processing_time": 2.35
}
```

#### Ingest File
```http
POST /api/v1/ingest/file
Content-Type: multipart/form-data

file: [uploaded file]
source: "Document Name"
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "File upload received and queued for processing",
  "filename": "document.pdf",
  "file_size": 1024000
}
```

#### Check Job Status
```http
GET /api/v1/ingest/status/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "message": "Successfully ingested 15 chunks from document.pdf",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:01:30"
}
```

### Query Endpoints

#### Query Documents
```http
POST /api/v1/query
Content-Type: application/json

{
  "query": "What is the main topic of the documents?",
  "collection": "Documents",
  "options": {
    "top_k": 5,
    "hybrid_alpha": 0.5,
    "max_context_chunks": 6,
    "temperature": 0.2
  }
}
```

**Response:**
```json
{
  "query": "What is the main topic of the documents?",
  "answer": "Based on the retrieved documents, the main topic appears to be...",
  "retrieved_chunks": [
    {
      "text": "Relevant text chunk...",
      "source": "Document Name",
      "chunk_id": "0",
      "score": 0.95
    }
  ],
  "processing_time": 1.23,
  "model_used": "gpt-4o",
  "chunk_count": 3,
  "collection": "Documents",
  "search_params": {
    "top_k": 5,
    "hybrid_alpha": 0.5,
    "max_context_chunks": 6,
    "temperature": 0.2
  }
}
```

### Collection Management

#### List Collections
```http
GET /api/v1/collections
```

**Response:**
```json
{
  "collections": [
    {
      "name": "Documents",
      "document_count": 25,
      "chunk_count": 150,
      "storage_size": "2.5MB",
      "created_at": null,
      "last_updated": null
    }
  ],
  "total_count": 1
}
```

#### Get Collection Stats
```http
GET /api/v1/collections/{collection_name}/stats
```

#### Delete Collection
```http
DELETE /api/v1/collections/{collection_name}
```

## Error Handling

All endpoints return structured error responses:

```json
{
  "error": "validation_error",
  "message": "Text content cannot be empty",
  "correlation_id": "uuid-for-tracing"
}
```

### Error Types
- `validation_error` (400) - Invalid request data
- `not_found` (404) - Resource not found
- `file_processing_error` (422) - File upload/processing issues
- `external_service_error` (502) - OpenAI/Weaviate service issues
- `database_error` (500) - Weaviate database issues
- `internal_server_error` (500) - Unexpected server errors

## Configuration

The API uses the same `.env` configuration as the CLI tools:

```bash
# Required
OPENAI_API_KEY=sk-your-key
WEAVIATE_API_KEY=your-key

# Optional API-specific settings
MAX_FILE_SIZE=52428800  # 50MB
MAX_TEXT_SIZE=1048576   # 1MB
```

## Development

### Start Development Server
```bash
make start-api
# Server starts with auto-reload enabled
```

### Run Tests
```bash
# Test API endpoints
make test-api

# Test core functionality
make test
```

### Stop Server
```bash
make stop-api
```

## Integration Examples

### Python Client
```python
import os
import requests

# Ingest text
response = requests.post(f"http://localhost:{os.getenv('API_PORT', '8001')}/api/v1/ingest/text", json={
    "text": "Your document content...",
    "source": "My Document"
})

# Query
response = requests.post(f"http://localhost:{os.getenv('API_PORT', '8001')}/api/v1/query", json={
    "query": "What is this about?"
})
```

### cURL Examples
```bash
# Health check
curl http://localhost:${API_PORT:-8001}/api/v1/health

# Ingest text
curl -X POST http://localhost:${API_PORT:-8001}/api/v1/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample text", "source": "Test"}'

# Query
curl -X POST http://localhost:${API_PORT:-8001}/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this about?"}'
```

### JavaScript/Frontend
```javascript
// Ingest text
const response = await fetch('/api/v1/ingest/text', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    text: 'Document content...',
    source: 'Frontend Upload'
  })
});

// Query
const queryResponse = await fetch('/api/v1/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: 'What is the main topic?'
  })
});
```

## Production Deployment

For production deployment, consider:

1. **Security**: Add authentication, rate limiting, CORS configuration
2. **Scaling**: Use gunicorn/uvicorn workers, load balancer
3. **Monitoring**: Add logging, metrics, health checks
4. **Storage**: Replace in-memory job storage with Redis/database
5. **File Storage**: Use cloud storage for file uploads

Example production command:
```bash
uvicorn api.main:app --host 0.0.0.0 --port ${API_PORT:-8001} --workers 4
```