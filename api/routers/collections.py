"""
Collection management endpoints.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends
import weaviate

from ..dependencies import get_config, get_weaviate_client
from ..exceptions import DatabaseError, NotFoundError
from ..models import (
    CollectionListResponse,
    CollectionStatsResponse,
    DeleteCollectionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/collections", response_model=CollectionListResponse)
async def list_collections(
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    config=Depends(get_config),
):
    """
    List all collections with basic statistics.
    """

    def _get_collections():
        try:
            collections = []

            # Get all collections from Weaviate
            for collection_name in weaviate_client.collections.list_all():
                try:
                    collection = weaviate_client.collections.get(collection_name)

                    # Get basic stats
                    objects = collection.query.fetch_objects(limit=0)  # Just get count
                    document_count = len(objects.objects) if objects else 0

                    # Count unique sources (approximate document count)
                    sources = set()
                    if objects and objects.objects:
                        for obj in objects.objects[:1000]:  # Sample first 1000
                            if hasattr(obj, "properties") and obj.properties:
                                source = obj.properties.get("source", "")
                                if source:
                                    sources.add(source)

                    collections.append(
                        CollectionStatsResponse(
                            name=collection_name,
                            document_count=len(sources),
                            chunk_count=document_count,
                            total_tokens=None,  # Would require calculation
                            storage_size=None,  # Not easily available
                            created_at=None,  # Not tracked
                            last_updated=None,  # Not tracked
                        )
                    )

                except Exception as e:
                    logger.warning(
                        f"Failed to get stats for collection {collection_name}: {e}"
                    )
                    collections.append(
                        CollectionStatsResponse(
                            name=collection_name, document_count=0, chunk_count=0
                        )
                    )

            return collections

        except Exception as e:
            raise DatabaseError(f"Failed to list collections: {e!s}")

    loop = asyncio.get_event_loop()
    collections = await loop.run_in_executor(None, _get_collections)

    return CollectionListResponse(collections=collections, total_count=len(collections))


@router.get(
    "/collections/{collection_name}/stats", response_model=CollectionStatsResponse
)
async def get_collection_stats(
    collection_name: str,
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    config=Depends(get_config),
):
    """
    Get detailed statistics for a specific collection.
    """

    def _get_stats():
        try:
            collection = weaviate_client.collections.get(collection_name)

            # Get all objects to calculate statistics
            objects = collection.query.fetch_objects(limit=10000)  # Reasonable limit
            chunk_count = len(objects.objects) if objects else 0

            # Count unique sources
            sources = set()
            total_text_length = 0

            if objects and objects.objects:
                for obj in objects.objects:
                    if hasattr(obj, "properties") and obj.properties:
                        source = obj.properties.get("source", "")
                        if source:
                            sources.add(source)

                        text = obj.properties.get("text", "")
                        total_text_length += len(text)

            # Estimate storage size (very rough)
            estimated_size = total_text_length * 2  # Text + vector data approximation
            size_str = (
                f"{estimated_size // 1024}KB"
                if estimated_size > 1024
                else f"{estimated_size}B"
            )

            return CollectionStatsResponse(
                name=collection_name,
                document_count=len(sources),
                chunk_count=chunk_count,
                total_tokens=None,  # Would need tokenization
                storage_size=size_str,
                created_at=None,  # Not tracked
                last_updated=None,  # Not tracked
            )

        except Exception as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                raise NotFoundError("Collection", collection_name)
            else:
                raise DatabaseError(f"Failed to get collection stats: {e!s}")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_stats)


@router.delete(
    "/collections/{collection_name}", response_model=DeleteCollectionResponse
)
async def delete_collection(
    collection_name: str,
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    config=Depends(get_config),
):
    """
    Delete a collection and all its data.

    ⚠️ Warning: This operation is irreversible and will permanently delete
    all documents and chunks in the specified collection.
    """

    def _delete_collection():
        try:
            # First, get collection stats before deletion
            collection = weaviate_client.collections.get(collection_name)
            objects = collection.query.fetch_objects(limit=0)
            document_count = len(objects.objects) if objects else 0

            # Delete the collection
            weaviate_client.collections.delete(collection_name)

            return {
                "success": True,
                "collection": collection_name,
                "documents_removed": document_count,
                "message": f"Collection '{collection_name}' deleted successfully",
            }

        except Exception as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                raise NotFoundError("Collection", collection_name)
            else:
                raise DatabaseError(f"Failed to delete collection: {e!s}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _delete_collection)

    return DeleteCollectionResponse(**result)
