"""
FastAPI application main entry point.
"""

from contextlib import asynccontextmanager
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .exceptions import RAGAPIError
from .routers import collections, ingest, query, system

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting FastAPI RAG service...")
    yield
    logger.info("Shutting down FastAPI RAG service...")


# Create FastAPI app
app = FastAPI(
    title="Local Weaviate RAG API",
    description="REST API for document ingestion and intelligent querying using RAG",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for correlation ID and logging
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):  # type: ignore
    """Add correlation ID to each request for tracing."""
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    # Log request
    logger.info(
        f"Request started - {request.method} {request.url.path} [{correlation_id}]"
    )

    response = await call_next(request)

    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id

    # Log response
    logger.info(
        f"Request completed - {request.method} {request.url.path} "
        f"[{correlation_id}] - Status: {response.status_code}"
    )

    return response


# Global exception handlers
@app.exception_handler(RAGAPIError)
async def rag_exception_handler(request: Request, exc: RAGAPIError) -> JSONResponse:
    """Handle custom RAG API exceptions."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.error(f"RAG API Error - {exc.error_code}: {exc.message} [{correlation_id}]")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "correlation_id": correlation_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.error(f"Unexpected error: {exc!s} [{correlation_id}]", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
        },
    )


# Include routers
app.include_router(system.router, prefix="/api/v1", tags=["system"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingestion"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(collections.router, prefix="/api/v1", tags=["collections"])


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint with basic API information."""
    return {
        "name": "Local Weaviate RAG API",
        "version": "0.1.0",
        "description": "REST API for document ingestion and intelligent querying",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
