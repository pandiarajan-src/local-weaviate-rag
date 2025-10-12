# Multi-stage build for production-ready FastAPI application
FROM python:3.10-slim as builder

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies in a virtual environment
RUN uv sync --no-dev


# Production stage
FROM python:3.10-slim

# Install uv in production stage as well
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY rag/ ./rag/
COPY api/ ./api/
COPY pyproject.toml ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/api/v1/health')" || exit 1

# Expose API port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
