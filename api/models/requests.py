"""
Request models for API endpoints.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IngestTextRequest(BaseModel):
    """Request model for text ingestion."""

    text: str = Field(..., min_length=1, description="Text content to ingest")
    source: str = Field("", description="Source identifier for the text")
    collection: str = Field(
        "Documents", description="Collection name to store the text"
    )
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        if len(v) > 1024 * 1024:  # 1MB limit for direct text
            raise ValueError("Text content too large (max 1MB)")
        return v.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        return v.strip() if v else ""

    @field_validator("collection")
    @classmethod
    def validate_collection(cls, v: str) -> str:
        # Basic validation for collection names
        v = v.strip()
        if not v:
            return "Documents"
        # Collection name must start with uppercase letter for Weaviate
        return v[0].upper() + v[1:] if v else "Documents"


class QueryRequest(BaseModel):
    """Request model for document querying."""

    query: str = Field(..., min_length=1, description="Search query")
    collection: str | list[str] | None = Field(
        None,
        description="Collection name(s) to search. Can be a single string, list of strings, or None to search all collections",
    )
    options: Optional["QueryOptions"] = Field(
        None, description="Query configuration options"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        return v.strip()

    @field_validator("collection")
    @classmethod
    def validate_collection(cls, v: str | list[str] | None) -> str | list[str] | None:
        if v is None:
            return None

        # Handle single string
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            # Ensure proper capitalization
            return v[0].upper() + v[1:] if v else None

        # Handle list of strings
        # v must be a list at this point since we've checked for None and str
        validated_list = []
        for collection_name in v:
            if collection_name and isinstance(collection_name, str):
                collection_name = collection_name.strip()
                if collection_name:
                    # Ensure proper capitalization
                    validated_list.append(
                        collection_name[0].upper() + collection_name[1:]
                    )
        return validated_list if validated_list else None


class QueryOptions(BaseModel):
    """Query configuration options."""

    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    hybrid_alpha: float = Field(
        0.5, ge=0.0, le=1.0, description="Hybrid search balance (0=keyword, 1=vector)"
    )
    max_context_chunks: int = Field(
        6, ge=1, le=10, description="Maximum chunks to include in LLM context"
    )
    temperature: float = Field(
        0.2, ge=0.0, le=2.0, description="LLM temperature for response generation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "top_k": 5,
                "hybrid_alpha": 0.5,
                "max_context_chunks": 6,
                "temperature": 0.2,
            }
        }
    )


# Update forward reference
QueryRequest.model_rebuild()
