"""
Document ingestion service with async wrappers for existing functionality.
"""

import asyncio
from functools import wraps
import logging
import time

from openai import OpenAI
import weaviate

from rag.ingest import embed_chunks, ensure_schema
from rag.utils import chunk_text

from ..exceptions import (
    DatabaseError,
    ExternalServiceError,
    InternalProcessingError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def make_async(func):  # type: ignore
    """Convert synchronous function to async."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):  # type: ignore
        loop = asyncio.get_event_loop()
        try:
            # Create partial function with kwargs if needed
            if kwargs:
                from functools import partial

                partial_func = partial(func, *args, **kwargs)
                return await loop.run_in_executor(None, partial_func)
            else:
                return await loop.run_in_executor(None, func, *args)
        except Exception as e:
            logger.error(f"Error in async wrapper for {func.__name__}: {e}")
            raise

    return async_wrapper


# Create async versions of existing functions
chunk_text_async = make_async(chunk_text)
embed_chunks_async = make_async(embed_chunks)
ensure_schema_async = make_async(ensure_schema)


class IngestionService:
    """Service for handling document ingestion operations."""

    def __init__(self, weaviate_client: weaviate.WeaviateClient, openai_client: OpenAI):
        self.weaviate_client = weaviate_client
        self.openai_client = openai_client

    async def ingest_text(
        self,
        text: str,
        source: str,
        collection_name: str,
        embed_model: str,
        chunk_tokens: int,
        chunk_overlap: int,
    ) -> dict:
        """
        Ingest text content into the vector database.

        Args:
            text: Text content to ingest
            source: Source identifier
            collection_name: Target collection name
            embed_model: Embedding model to use
            chunk_tokens: Target tokens per chunk
            chunk_overlap: Overlap between chunks

        Returns:
            Dictionary with ingestion results
        """
        start_time = time.time()

        try:
            # Validate input
            if not text.strip():
                raise ValidationError("Text content cannot be empty")

            if len(text) > 1024 * 1024:  # 1MB limit
                raise ValidationError("Text content too large (max 1MB)")

            logger.info(
                f"Starting text ingestion - Source: {source}, Length: {len(text)} chars"
            )

            # Step 1: Chunk the text
            try:
                chunks = await chunk_text_async(
                    text=text,
                    model=embed_model,
                    chunk_tokens=chunk_tokens,
                    overlap_tokens=chunk_overlap,
                )
                logger.info(f"Created {len(chunks)} text chunks")
            except Exception as e:
                raise InternalProcessingError(f"Text chunking failed: {e!s}")

            # Step 2: Generate embeddings
            try:
                vectors = await embed_chunks_async(
                    client=self.openai_client, model=embed_model, chunks=chunks
                )
                logger.info(f"Generated embeddings for {len(vectors)} chunks")
            except Exception as e:
                if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                    raise ExternalServiceError(
                        "OpenAI", "API key authentication failed"
                    )
                elif "rate_limit" in str(e).lower():
                    raise ExternalServiceError("OpenAI", "Rate limit exceeded")
                else:
                    raise ExternalServiceError(
                        "OpenAI", f"Embedding generation failed: {e!s}"
                    )

            # Step 3: Ensure collection exists
            try:
                collection = await ensure_schema_async(
                    client=self.weaviate_client, collection_name=collection_name
                )
                logger.info(f"Collection '{collection_name}' ready for ingestion")
            except Exception as e:
                raise DatabaseError(f"Collection setup failed: {e!s}")

            # Step 4: Store chunks with vectors
            try:
                await self._store_chunks(collection, chunks, vectors, source)
                logger.info(
                    f"Successfully stored {len(chunks)} chunks in collection '{collection_name}'"
                )
            except Exception as e:
                raise DatabaseError(f"Storage operation failed: {e!s}")

            processing_time = time.time() - start_time

            return {
                "success": True,
                "message": f"Successfully ingested {len(chunks)} chunks",
                "chunks_created": len(chunks),
                "collection": collection_name,
                "source": source,
                "processing_time": round(processing_time, 2),
            }

        except (
            ValidationError,
            ExternalServiceError,
            DatabaseError,
            InternalProcessingError,
        ):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text ingestion: {e}", exc_info=True)
            raise InternalProcessingError(f"Unexpected ingestion error: {e!s}")

    async def _store_chunks(
        self, collection, chunks: list[str], vectors: list[list[float]], source: str
    ) -> None:
        """Store chunks with their vectors in the collection."""

        def _batch_insert() -> None:
            """Synchronous batch insertion."""
            try:
                with collection.batch.dynamic() as batch:
                    for i, (chunk, vector) in enumerate(
                        zip(chunks, vectors, strict=True)
                    ):
                        batch.add_object(
                            properties={
                                "text": chunk,
                                "source": source,
                                "chunk_id": str(i),
                            },
                            vector=vector,
                        )

                # Check for failed objects
                if (
                    hasattr(collection.batch, "failed_objects")
                    and collection.batch.failed_objects
                ):
                    failed_count = len(collection.batch.failed_objects)
                    raise Exception(f"Failed to insert {failed_count} objects")

            except Exception as batch_error:
                logger.warning(
                    f"Batch insertion failed: {batch_error}, trying individual insertion"
                )

                # Fallback to individual insertion
                for i, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                    try:
                        collection.data.insert(
                            properties={
                                "text": chunk,
                                "source": source,
                                "chunk_id": str(i),
                            },
                            vector=vector,
                        )
                    except Exception as individual_error:
                        logger.error(f"Failed to insert chunk {i}: {individual_error}")
                        raise Exception(f"Individual insertion failed for chunk {i}")

        # Run the batch insertion in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _batch_insert)
