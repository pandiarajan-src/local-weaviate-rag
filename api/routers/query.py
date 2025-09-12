"""
Document query endpoints.
"""

import logging

from fastapi import APIRouter, Depends
from openai import OpenAI
import weaviate

from ..dependencies import get_config, get_openai_client, get_weaviate_client
from ..models import QueryRequest, QueryResponse
from ..services import QueryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    openai_client: OpenAI = Depends(get_openai_client),
    config=Depends(get_config),
):
    """
    Query documents and generate an AI-powered answer.

    This endpoint performs hybrid search (combining keyword and semantic search)
    across your document collection, retrieves relevant chunks, and uses GPT
    to generate a comprehensive answer based on the retrieved context.
    """
    service = QueryService(weaviate_client, openai_client)

    # Use provided options or fall back to defaults
    options = request.options or {}

    result = await service.process_query(
        query=request.query,
        collection_name=request.collection or config.rag_collection,
        embed_model=config.openai_embed_model,
        completions_model=config.openai_completions_model,
        top_k=getattr(options, "top_k", None) or config.top_k,
        hybrid_alpha=getattr(options, "hybrid_alpha", None) or config.hybrid_alpha,
        max_context_chunks=getattr(options, "max_context_chunks", None)
        or config.max_context_chunks,
        temperature=getattr(options, "temperature", 0.2),
    )

    return QueryResponse(**result)
