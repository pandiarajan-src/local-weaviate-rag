# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready RAG (Retrieval-Augmented Generation) system using Weaviate vector database, OpenAI embeddings, and GPT-4o for intelligent document Q&A. The system provides both CLI tools and a REST API built with FastAPI.

## Quick Start Commands

### Development Setup
```bash
# Install dependencies
uv sync

# Install development tools (linters, type checkers)
uv sync --extra dev
# or
make install-dev
```

### Weaviate Database Management
```bash
# Start Weaviate (Docker required)
./start_weaviate.sh

# Stop Weaviate (data persists)
./stop_weaviate.sh

# Reset Weaviate (⚠️ deletes all data)
./reset_weaviate.sh

# Check Weaviate status
docker compose -f docker-compose.weaviate.yml ps
```

### CLI Usage
```bash
# Ingest documents
uv run python -m rag.ingest <file_or_text> --source "Source Name"
uv run python -m rag.ingest README.md --source "Documentation"

# Query documents
uv run python -m rag.query "Your question here"
```

### FastAPI Server (Development - Local)
```bash
# Start API server locally (starts Weaviate automatically if needed)
./start_api.sh
# or
make start-api

# Stop API server
make stop-api

# Access API documentation at http://localhost:${API_PORT:-8001}/docs
```

### Docker Deployment (Production)
```bash
# Build Docker images
make docker-build

# Start all services (Weaviate + API) in Docker
make docker-up

# View logs
make docker-logs
make docker-logs-api        # API logs only
make docker-logs-weaviate   # Weaviate logs only

# Stop all services
make docker-down

# Restart services
make docker-restart

# Rebuild after code changes
make docker-rebuild

# Clean up (⚠️ deletes all data)
make docker-clean

# Check status
make docker-status
```

### Testing
```bash
# Run core functionality tests
make test
# or
uv run python tests/test_functionality.py

# Test FastAPI endpoints
make test-api
# or
uv run python test_api.py
```

### Code Quality
```bash
# Run all linters with auto-fix
make lint-fix
# or
./lint.sh --fix

# Check code quality (no fixes)
make lint
# or
./lint.sh

# Run specific linters
./lint.sh --ruff-only --fix    # Python linting + formatting
./lint.sh --mypy-only          # Type checking
./lint.sh --shellcheck-only    # Shell script checking
```

## System Architecture

### Core Components

**1. RAG Pipeline (`rag/` directory)**
- `rag/utils.py` - Core utilities: tokenization, text chunking, Weaviate client factory, retry logic
- `rag/ingest.py` - Document ingestion: text splitting, embedding generation, Weaviate storage
- `rag/query.py` - Query engine: hybrid search (BM25 + vector), context assembly, GPT-4o integration

**2. FastAPI Service (`api/` directory)**
- `api/main.py` - App initialization, middleware, exception handlers
- `api/routers/` - REST endpoints (system, ingest, query, collections)
- `api/services/` - Business logic (ingestion, query, background tasks)
- `api/dependencies/` - Dependency injection (clients, config)
- `api/models/` - Pydantic request/response models
- `api/exceptions.py` - Custom exception hierarchy

**3. Configuration**
- `.env` - Environment variables (not in git, copy from `.env.example`)
- All config loaded via `rag.utils.env()` or `api.dependencies.config.Settings`
- API port configured via `API_PORT` env var (default: 8001)

**4. Docker Infrastructure**
- `Dockerfile` - Multi-stage build for production API container
- `docker-compose.yml` - Production orchestration (Weaviate + API)
- `docker-compose.weaviate.yml` - Development (Weaviate only, API runs locally)
- `.dockerignore` - Optimizes Docker build context

### Data Flow

**Ingestion:**
```
Document → Text Chunking (sentence-aware, token-based) → OpenAI Embeddings → Weaviate Storage
```

**Query:**
```
Question → Embedding → Hybrid Search (BM25 + Vector) → Context Assembly → GPT-4o → Answer
```

### Key Design Patterns

1. **Text Chunking**: Token-aware splitting with sentence boundary preservation and configurable overlap (`rag/utils.py:chunk_text()`)
2. **Hybrid Search**: Combines BM25 keyword search with vector similarity (controlled by `HYBRID_ALPHA`)
3. **Retry Logic**: Exponential backoff for external API calls (`rag/utils.py:backoff_retry()`)
4. **Error Handling**: Custom exception hierarchy in FastAPI with correlation IDs for tracing

## Important Implementation Details

### Configuration Management

**Two parallel config systems:**
1. CLI tools use `rag.utils.env()` - simple environment variable getter with validation
2. FastAPI uses `pydantic-settings` - type-safe settings with `api.dependencies.config.Settings`

Both load from the same `.env` file but validate independently.

### Weaviate Client Management

**CLI tools**: Create client per operation via `rag.utils.get_weaviate_client()`
```python
client = get_weaviate_client()
client.connect()
# ... operations ...
client.close()
```

**FastAPI**: Singleton client pattern in `api.dependencies.clients.get_weaviate_client()` with proper lifecycle management and async wrappers.

**Docker deployment**: API connects to Weaviate using service name `weaviate` instead of `localhost` (configured via `WEAVIATE_HOST` env var in docker-compose.yml).

### Async/Sync Integration

The core RAG logic in `rag/` is synchronous. FastAPI wraps these in async functions:
```python
async def async_operation():
    # Run sync code in thread pool to avoid blocking
    result = await asyncio.to_thread(sync_operation, args)
```

### Port Configuration

The API server port is configured via `API_PORT` environment variable:
- Default: 8001 (to avoid conflicts with common 8000)
- Used in: `start_api.sh`, `api/main.py`, `Makefile`, all documentation
- Update `.env` to change: `API_PORT=8001`

## Development Workflow

### Adding New Features

1. **Core RAG functionality**: Add to `rag/` modules (keep synchronous)
2. **API endpoints**: Add router in `api/routers/`, service logic in `api/services/`
3. **Type hints required**: All functions must have complete type annotations
4. **Error handling**: Use custom exceptions from `api/exceptions.py` for API, log errors in CLI

### Code Quality Standards

**Linting tools configured:**
- Ruff (replaces flake8, isort, pyupgrade) - primary linter with auto-fix
- Black - code formatting (88 char line length)
- mypy - static type checking (strict mode, but `rag/` and `api/` modules have `ignore_errors=true`)
- shellcheck - shell script validation

**Before committing:**
1. `make lint-fix` - auto-fix all issues
2. `make test` - ensure tests pass
3. `make lint` - verify all linters pass

### Testing Strategy

**Functional tests** (`tests/test_functionality.py`):
- End-to-end RAG pipeline testing
- Ingestion and query validation
- Error handling verification

**API tests** (`test_api.py`):
- REST endpoint testing
- Request/response validation
- Error response checking

Run before making changes: `make test && make test-api`

## Common Patterns

### Ingestion Pattern
```python
from rag.ingest import ingest_text
from rag.utils import get_weaviate_client

client = get_weaviate_client()
client.connect()
try:
    ingest_text(
        client=client,
        text="content",
        source="source_name",
        collection="Documents"
    )
finally:
    client.close()
```

### Query Pattern
```python
from rag.query import query_rag
from rag.utils import get_weaviate_client

client = get_weaviate_client()
client.connect()
try:
    result = query_rag(
        client=client,
        query="question",
        collection="Documents",
        top_k=5,
        hybrid_alpha=0.5
    )
finally:
    client.close()
```

### FastAPI Dependency Pattern
```python
from fastapi import Depends
from api.dependencies.clients import get_weaviate_client
from api.dependencies.config import get_config

@router.post("/endpoint")
async def endpoint(
    client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    config: Settings = Depends(get_config)
):
    # Use client and config
    pass
```

## Key Configuration Parameters

**Chunking:**
- `CHUNK_TOKENS=400` - Target tokens per chunk (200-300=focused, 400-500=balanced, 600-800=contextual)
- `CHUNK_OVERLAP=60` - Overlap tokens between chunks (maintains context continuity)

**Search:**
- `HYBRID_ALPHA=0.5` - Search balance (0.0=keyword BM25, 1.0=semantic vector, 0.5=balanced)
- `TOP_K=5` - Number of chunks to retrieve
- `MAX_CONTEXT_CHUNKS=6` - Max chunks sent to LLM (controls token usage/cost)

**Models:**
- `OPENAI_EMBED_MODEL=text-embedding-3-small` - Embedding model (1536 dimensions)
- `OPENAI_COMPLETIONS_MODEL=gpt-4o` - Chat model for answers

## Troubleshooting Guide

**"Connection refused" errors:**
- Check Weaviate: `docker compose -f docker-compose.weaviate.yml ps`
- Start if needed: `./start_weaviate.sh`

**Port conflicts:**
- API port in use: Change `API_PORT` in `.env`, restart with `make stop-api && make start-api`
- Weaviate port 8080 in use: Change `WEAVIATE_PORT` in `.env`, restart Weaviate

**Missing API keys:**
- Verify `.env` exists: `cat .env | grep -E 'OPENAI_API_KEY|WEAVIATE_API_KEY'`
- Copy from template if missing: `cp .env.example .env`

**Type checking errors:**
- Note: `mypy` has `ignore_errors=true` for `rag.*` and `api.*` modules in `pyproject.toml`
- This is intentional to allow gradual type hint improvements
- Still use type hints for documentation and IDE support

## Security Considerations

- `.env` file contains secrets - never commit to git (in `.gitignore`)
- `WEAVIATE_API_KEY` must be strong (min 16 chars) - change from default
- Use `WEAVIATE_SCHEME=https` in production
- FastAPI CORS is open (`allow_origins=["*"]`) - configure for production
- File upload limits: `MAX_FILE_SIZE=50MB`, `MAX_TEXT_SIZE=1MB` (configurable)

## API Endpoint Reference

**System:**
- `GET /api/v1/health` - Health check with dependency status

**Ingestion:**
- `POST /api/v1/ingest/text` - Ingest text directly
- `POST /api/v1/ingest/file` - Upload file for background processing
- `GET /api/v1/ingest/status/{job_id}` - Check background job status

**Query:**
- `POST /api/v1/query` - Query documents with optional parameters

**Collections:**
- `GET /api/v1/collections` - List collections with stats
- `GET /api/v1/collections/{name}/stats` - Collection details
- `DELETE /api/v1/collections/{name}` - Delete collection

Full API documentation available at `/docs` when server is running.

## Docker Deployment Guide

### Architecture

**Two deployment modes:**

1. **Development** - Weaviate in Docker, API runs locally on host
   - Uses: `docker-compose.weaviate.yml`
   - Start: `./start_api.sh` or `make start-api`
   - API connects to Weaviate at `localhost:8080`

2. **Production** - Both Weaviate and API in Docker containers
   - Uses: `docker-compose.yml`
   - Start: `make docker-up`
   - API connects to Weaviate at `weaviate:8080` (internal Docker network)

### Production Deployment Steps

**1. Build the Docker images:**
```bash
make docker-build
```
This creates a production-optimized image using multi-stage build (no dev dependencies).

**2. Configure environment:**
Ensure `.env` file has production settings:
```bash
# Use HTTPS in production
WEAVIATE_SCHEME=https

# Strong API keys
WEAVIATE_API_KEY=<strong-random-key-min-16-chars>
OPENAI_API_KEY=<your-openai-key>

# Ports (defaults work fine)
WEAVIATE_PORT=8080
API_PORT=8001
```

**3. Start services:**
```bash
make docker-up
```
This starts both Weaviate and API containers with:
- Shared Docker network (`rag-network`)
- Persistent volume for Weaviate data
- Health checks for both services
- Proper service dependencies (API waits for Weaviate)

**4. Verify deployment:**
```bash
# Check container status
make docker-status

# View logs
make docker-logs

# Test health endpoint
curl http://localhost:8001/api/v1/health
```

### Docker Commands Reference

```bash
# Build/rebuild
make docker-build          # Build images from scratch
make docker-rebuild        # Down → Build → Up (after code changes)

# Lifecycle
make docker-up            # Start all services
make docker-down          # Stop and remove containers
make docker-restart       # Restart services
make docker-clean         # Stop and remove volumes (deletes data)

# Monitoring
make docker-logs          # All logs (follow mode)
make docker-logs-api      # API logs only
make docker-logs-weaviate # Weaviate logs only
make docker-status        # Container status

# Direct Docker Compose (if needed)
docker compose ps                    # List containers
docker compose exec api bash         # Shell into API container
docker compose exec weaviate bash    # Shell into Weaviate container
```

### Key Docker Configuration

**Dockerfile features:**
- Multi-stage build (reduces image size)
- Non-root user (`appuser`) for security
- Health check endpoint integration
- Optimized layer caching

**docker-compose.yml features:**
- Service dependencies with health checks
- Shared network for internal communication
- Environment variable injection from `.env`
- Persistent volume for Weaviate data
- Port mapping to host

**Networking:**
- Development: API on host → Weaviate at `localhost:8080`
- Production: API container → Weaviate at `weaviate:8080` (internal DNS)

### Production Best Practices

1. **Environment variables**: Never commit `.env`, always use `.env.example` as template
2. **HTTPS**: Set `WEAVIATE_SCHEME=https` in production
3. **API Keys**: Use strong, unique keys (min 16 chars)
4. **Monitoring**: Set up log aggregation (e.g., ELK stack, CloudWatch)
5. **Scaling**: Use orchestrator like Kubernetes or Docker Swarm for multi-instance deployment
6. **Backups**: Regular backups of Weaviate volume (`weaviate-data`)

### Troubleshooting Docker Deployment

**Container won't start:**
```bash
# Check logs
make docker-logs-api

# Verify env vars loaded
docker compose config

# Check health
docker compose ps
```

**API can't connect to Weaviate:**
- In Docker, use `WEAVIATE_HOST=weaviate` (service name, not localhost)
- Verify both containers on same network: `docker network inspect local-weaviate-rag_rag-network`

**Port conflicts:**
- Change ports in `.env`: `WEAVIATE_PORT=8081`, `API_PORT=8002`
- Restart: `make docker-restart`

**Need to reset data:**
```bash
make docker-clean  # Removes volumes (⚠️ deletes all data)
make docker-up     # Start fresh
```
