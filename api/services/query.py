"""
Query service with async wrappers for search and answer generation.
"""

import asyncio
import logging
import time
from typing import Any

from openai import OpenAI
import weaviate
from weaviate.collections import Collection

from rag.query import build_prompt, hybrid_search

from ..exceptions import (
    DatabaseError,
    ExternalServiceError,
    InternalProcessingError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling document querying and answer generation."""

    def __init__(self, weaviate_client: weaviate.WeaviateClient, openai_client: OpenAI):
        self.weaviate_client = weaviate_client
        self.openai_client = openai_client

    async def process_query(
        self,
        query: str,
        collection_name: str,
        embed_model: str,
        completions_model: str,
        top_k: int,
        hybrid_alpha: float,
        max_context_chunks: int,
        temperature: float,
    ) -> dict[str, Any]:
        """
        Process a query and generate an answer using RAG.

        Args:
            query: User query
            collection_name: Collection to search
            embed_model: Embedding model for query vectorization
            completions_model: Model for answer generation
            top_k: Number of chunks to retrieve
            hybrid_alpha: Hybrid search balance
            max_context_chunks: Max chunks for context
            temperature: LLM temperature

        Returns:
            Dictionary with query results and generated answer
        """
        start_time = time.time()

        try:
            # Validate input
            if not query.strip():
                raise ValidationError("Query cannot be empty")

            logger.info(f"Processing query: {query[:100]}...")

            # Step 1: Get collection
            try:
                collection = self.weaviate_client.collections.get(collection_name)
            except Exception:
                raise NotFoundError("Collection", collection_name)

            # Step 2: Create query embedding
            try:
                query_vector = await self._create_query_embedding(query, embed_model)
                logger.info("Created query embedding")
            except Exception as e:
                if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                    raise ExternalServiceError(
                        "OpenAI", "API key authentication failed"
                    )
                else:
                    raise ExternalServiceError(
                        "OpenAI", f"Query embedding failed: {e!s}"
                    )

            # Step 3: Perform hybrid search
            try:
                search_results = await self._perform_search(
                    collection, query, query_vector, hybrid_alpha, top_k
                )
                logger.info(f"Found {len(search_results)} search results")
            except Exception as e:
                raise DatabaseError(f"Search operation failed: {e!s}")

            if not search_results:
                return {
                    "query": query,
                    "answer": "No relevant documents found for your query.",
                    "retrieved_chunks": [],
                    "processing_time": round(time.time() - start_time, 2),
                    "model_used": completions_model,
                    "chunk_count": 0,
                    "collection": collection_name,
                    "search_params": {
                        "top_k": top_k,
                        "hybrid_alpha": hybrid_alpha,
                        "max_context_chunks": max_context_chunks,
                    },
                }

            # Step 4: Prepare context and generate answer
            try:
                contexts = []
                retrieved_chunks = []

                # Limit to max_context_chunks
                for obj in search_results[:max_context_chunks]:
                    props = obj.properties
                    text = props.get("text", "")
                    contexts.append(text)

                    # Extract score if available
                    score = 0.0
                    if hasattr(obj, "metadata") and obj.metadata:
                        distance = getattr(obj.metadata, "distance", None)
                        if distance is not None:
                            # Convert distance to similarity score (inverse)
                            score = max(0.0, 1.0 - distance)

                    retrieved_chunks.append(
                        {
                            "text": text,
                            "source": props.get("source", ""),
                            "chunk_id": props.get("chunk_id", ""),
                            "score": round(score, 4),
                        }
                    )

                # Generate answer
                answer = await self._generate_answer(
                    query, contexts, completions_model, temperature
                )
                logger.info("Generated answer successfully")

            except Exception as e:
                raise InternalProcessingError(f"Answer generation failed: {e!s}")

            processing_time = time.time() - start_time

            return {
                "query": query,
                "answer": answer,
                "retrieved_chunks": retrieved_chunks,
                "processing_time": round(processing_time, 2),
                "model_used": completions_model,
                "chunk_count": len(retrieved_chunks),
                "collection": collection_name,
                "search_params": {
                    "top_k": top_k,
                    "hybrid_alpha": hybrid_alpha,
                    "max_context_chunks": max_context_chunks,
                    "temperature": temperature,
                },
            }

        except (
            ValidationError,
            NotFoundError,
            ExternalServiceError,
            DatabaseError,
            InternalProcessingError,
        ):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during query processing: {e}", exc_info=True
            )
            raise InternalProcessingError(f"Unexpected query error: {e!s}")

    async def _create_query_embedding(
        self, query: str, embed_model: str
    ) -> list[float]:
        """Create embedding for the query."""

        def _embed() -> list[float]:
            response = self.openai_client.embeddings.create(
                model=embed_model, input=[query]
            )
            return response.data[0].embedding

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _embed)

    async def _perform_search(
        self,
        collection: Collection,
        query: str,
        query_vector: list[float],
        alpha: float,
        limit: int,
    ):  # type: ignore
        """Perform hybrid search."""

        def _search():  # type: ignore
            return hybrid_search(collection, query, query_vector, alpha, limit)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _search)
        return result.objects if result else []

    async def _generate_answer(
        self, query: str, contexts: list[str], model: str, temperature: float
    ) -> str:
        """Generate answer using LLM."""

        def _generate() -> str:
            prompt = build_prompt(query, contexts)

            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )

            return response.choices[0].message.content

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _generate)
