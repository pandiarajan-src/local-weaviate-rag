"""
Response models for API endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    """Response model for text ingestion."""

    success: bool = Field(..., description="Whether ingestion was successful")
    message: str = Field(..., description="Result message")
    chunks_created: int = Field(..., description="Number of text chunks created")
    collection: str = Field(..., description="Target collection name")
    source: str = Field(..., description="Source identifier")
    processing_time: float = Field(..., description="Processing time in seconds")


class FileIngestResponse(BaseModel):
    """Response model for file ingestion (background job)."""

    job_id: str = Field(..., description="Background job identifier")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., description="File size in bytes")


class RetrievedChunk(BaseModel):
    """Model for a retrieved text chunk."""

    text: str = Field(..., description="Chunk text content")
    source: str = Field(..., description="Source document identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    score: float = Field(..., description="Relevance score")
    metadata: dict[str, Any] | None = Field(
        None, description="Additional chunk metadata"
    )


class QueryResponse(BaseModel):
    """Response model for document querying."""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    retrieved_chunks: list[RetrievedChunk] = Field(
        ..., description="Retrieved relevant chunks"
    )
    processing_time: float = Field(..., description="Total processing time in seconds")
    model_used: str = Field(..., description="LLM model used for generation")
    chunk_count: int = Field(..., description="Number of chunks used for context")
    collection: str = Field(..., description="Collection searched")
    search_params: dict[str, Any] = Field(..., description="Search parameters used")


class CollectionStatsResponse(BaseModel):
    """Response model for collection statistics."""

    name: str = Field(..., description="Collection name")
    document_count: int = Field(..., description="Number of source documents")
    chunk_count: int = Field(..., description="Total number of text chunks")
    total_tokens: int | None = Field(None, description="Approximate total tokens")
    storage_size: str | None = Field(None, description="Human-readable storage size")
    created_at: str | None = Field(None, description="Collection creation timestamp")
    last_updated: str | None = Field(None, description="Last update timestamp")


class CollectionListResponse(BaseModel):
    """Response model for listing collections."""

    collections: list[CollectionStatsResponse] = Field(
        ..., description="List of collections"
    )
    total_count: int = Field(..., description="Total number of collections")


class DeleteCollectionResponse(BaseModel):
    """Response model for collection deletion."""

    success: bool = Field(..., description="Whether deletion was successful")
    collection: str = Field(..., description="Deleted collection name")
    documents_removed: int = Field(..., description="Number of documents removed")
    message: str = Field(..., description="Operation result message")
