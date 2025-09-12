"""
Common Pydantic models shared across the API.
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    correlation_id: str = Field(..., description="Request correlation ID for tracing")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Response timestamp")
    dependencies: dict[str, str] = Field(..., description="Dependency service statuses")


class JobStatus(BaseModel):
    """Background job status model."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(
        ..., description="Job status (queued, processing, completed, failed)"
    )
    progress: int | None = Field(None, description="Progress percentage (0-100)")
    message: str | None = Field(None, description="Status message or error details")
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class CollectionInfo(BaseModel):
    """Collection information model."""

    name: str = Field(..., description="Collection name")
    document_count: int = Field(..., description="Number of documents in collection")
    chunk_count: int = Field(..., description="Number of text chunks in collection")
    created_at: str | None = Field(None, description="Collection creation timestamp")
    size_bytes: int | None = Field(
        None, description="Approximate storage size in bytes"
    )
