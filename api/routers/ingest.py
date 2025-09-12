"""
Document ingestion endpoints.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from openai import OpenAI
import weaviate

from ..dependencies import get_config, get_openai_client, get_weaviate_client
from ..exceptions import FileProcessingError, NotFoundError
from ..models import FileIngestResponse, IngestResponse, IngestTextRequest, JobStatus
from ..services import IngestionService
from ..services.background import BackgroundJobManager, process_file_content_ingestion

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(
    request: IngestTextRequest,
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    openai_client: OpenAI = Depends(get_openai_client),
    config=Depends(get_config),
) -> IngestResponse:
    """
    Ingest text content into the vector database.

    This endpoint takes raw text content, chunks it into appropriate sizes,
    generates embeddings using OpenAI, and stores the chunks in Weaviate
    for later retrieval.
    """
    service = IngestionService(weaviate_client, openai_client)

    result = await service.ingest_text(
        text=request.text,
        source=request.source or "API Upload",
        collection_name=config.rag_collection,
        embed_model=config.openai_embed_model,
        chunk_tokens=config.chunk_tokens,
        chunk_overlap=config.chunk_overlap,
    )

    return IngestResponse(**result)


@router.post("/ingest/file", response_model=FileIngestResponse)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form(""),
    weaviate_client: weaviate.WeaviateClient = Depends(get_weaviate_client),
    openai_client: OpenAI = Depends(get_openai_client),
    config=Depends(get_config),
) -> FileIngestResponse:
    """
    Ingest a file into the vector database via background processing.

    This endpoint accepts file uploads, validates them, and processes them
    in the background. Use the returned job_id to check processing status.

    Supported file types: .txt, .md, .py, .js, .json, .csv, .html, .xml, .rst, .tex
    Maximum file size: 50MB (configurable)
    """
    # Basic validation
    if not file.filename:
        raise FileProcessingError("Filename is required")

    if file.size and file.size > config.max_file_size:
        raise FileProcessingError(
            f"File too large: {file.size} bytes (max {config.max_file_size})"
        )

    # Create background job
    job_id = BackgroundJobManager.create_job("file_ingestion", file.filename)

    # Read file content before background processing
    try:
        content = await file.read()
        text = content.decode("utf-8")
        filename = file.filename or "unknown"
        file_size = file.size or len(content)
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception:
            raise FileProcessingError("Could not decode file as text")
    except Exception as e:
        raise FileProcessingError(f"Failed to read file: {e!s}")

    # Add background task with content - don't pass client instances directly
    background_tasks.add_task(
        process_file_content_ingestion,
        job_id=job_id,
        text=text,
        filename=filename,
        file_size=file_size,
        source=source,
        config=config,
    )

    return FileIngestResponse(
        job_id=job_id,
        status="queued",
        message="File upload received and queued for processing",
        filename=file.filename,
        file_size=file.size or 0,
    )


@router.get("/ingest/status/{job_id}", response_model=JobStatus)
async def get_ingestion_status(job_id: str) -> JobStatus:
    """
    Get the status of a background ingestion job.

    Returns the current status, progress, and any messages for the specified job.
    Job statuses: queued, processing, completed, failed
    """
    job_status = BackgroundJobManager.get_job_status(job_id)

    if not job_status:
        raise NotFoundError("Job", job_id)

    return job_status
