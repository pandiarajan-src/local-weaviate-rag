"""
System endpoints for health checks and monitoring.
"""

from datetime import datetime
import logging

from fastapi import APIRouter, Depends
from openai import OpenAI
import weaviate

from ..dependencies import get_config, get_openai_client, get_weaviate_client
from ..models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    openai_client: OpenAI = Depends(get_openai_client),
    config=Depends(get_config),
) -> HealthResponse:
    """
    Health check endpoint that verifies all system dependencies.
    """
    dependencies = {}
    overall_status = "healthy"

    # Check Weaviate
    try:
        if weaviate_client.is_ready():
            dependencies["weaviate"] = "healthy"
        else:
            dependencies["weaviate"] = "unhealthy"
            overall_status = "degraded"
    except Exception as e:
        dependencies["weaviate"] = f"error: {e!s}"
        overall_status = "unhealthy"

    # Check OpenAI (simple API key validation)
    try:
        # Try to list models as a lightweight API test
        models = openai_client.models.list()
        if models and len(models.data) > 0:
            dependencies["openai"] = "healthy"
        else:
            dependencies["openai"] = "unknown"
            overall_status = "degraded"
    except Exception as e:
        dependencies["openai"] = f"error: {e!s}"
        if overall_status == "healthy":
            overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        dependencies=dependencies,
    )
