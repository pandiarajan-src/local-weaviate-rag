"""
Background task management for long-running operations.
"""

from datetime import datetime
import logging
import uuid

from ..dependencies.clients import create_openai_client, create_weaviate_client
from ..exceptions import FileProcessingError
from ..models import JobStatus
from .ingestion import IngestionService

logger = logging.getLogger(__name__)

# In-memory job storage (in production, use Redis or database)
_job_storage: dict[str, JobStatus] = {}


class BackgroundJobManager:
    """Manager for background job tracking and execution."""

    @staticmethod
    def create_job(job_type: str, filename: str = "") -> str:
        """Create a new background job."""
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        job = JobStatus(
            job_id=job_id,
            status="queued",
            progress=0,
            message=f"Job created for {job_type}",
            created_at=now,
            updated_at=now,
        )

        _job_storage[job_id] = job
        logger.info(f"Created background job {job_id} for {job_type}")
        return job_id

    @staticmethod
    def get_job_status(job_id: str) -> JobStatus | None:
        """Get current job status."""
        return _job_storage.get(job_id)

    @staticmethod
    def update_job(
        job_id: str,
        status: str,
        progress: int | None = None,
        message: str | None = None,
    ) -> None:
        """Update job status."""
        if job_id in _job_storage:
            job = _job_storage[job_id]
            job.status = status
            if progress is not None:
                job.progress = progress
            if message is not None:
                job.message = message
            job.updated_at = datetime.utcnow().isoformat()

            logger.info(f"Job {job_id} updated: {status} ({progress}%) - {message}")

    @staticmethod
    def cleanup_old_jobs(max_age_hours: int = 24) -> None:
        """Clean up old completed jobs."""
        # Implementation would check timestamps and remove old jobs
        # For now, we'll keep it simple
        pass


async def process_file_content_ingestion(
    job_id: str,
    text: str,
    filename: str,
    file_size: int,
    source: str,
    config,
) -> None:
    """
    Background task for processing file content ingestion.
    """
    try:
        BackgroundJobManager.update_job(
            job_id, "processing", 10, "Starting file processing..."
        )

        # Validate file size
        if file_size > config.max_file_size:
            raise FileProcessingError(
                f"File too large: {file_size} bytes (max {config.max_file_size})"
            )

        # Check file extension
        allowed_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".json",
            ".csv",
            ".html",
            ".xml",
            ".rst",
            ".tex",
        }
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

        if file_ext and file_ext not in allowed_extensions:
            raise FileProcessingError(
                f"File type '{file_ext}' not supported. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}"
            )

        BackgroundJobManager.update_job(
            job_id, "processing", 25, "Validating file content..."
        )

        if not text.strip():
            raise FileProcessingError("File content is empty")

        BackgroundJobManager.update_job(
            job_id, "processing", 50, "Processing text and generating embeddings..."
        )

        # Create fresh client connections for the background task
        weaviate_client = create_weaviate_client(config)
        openai_client = create_openai_client(config)

        try:
            # Create ingestion service with fresh clients
            ingestion_service = IngestionService(weaviate_client, openai_client)

            # Process the text using ingestion service
            result = await ingestion_service.ingest_text(
                text=text,
                source=source or filename,
                collection_name=config.rag_collection,
                embed_model=config.openai_embed_model,
                chunk_tokens=config.chunk_tokens,
                chunk_overlap=config.chunk_overlap,
            )

            BackgroundJobManager.update_job(
                job_id,
                "completed",
                100,
                f"Successfully ingested {result['chunks_created']} chunks from {filename}",
            )

            logger.info(f"Background file ingestion completed for job {job_id}")

        except FileProcessingError as e:
            BackgroundJobManager.update_job(
                job_id, "failed", None, f"File processing error: {e.message}"
            )
            logger.error(f"File processing failed for job {job_id}: {e.message}")

        except Exception as e:
            BackgroundJobManager.update_job(
                job_id, "failed", None, f"Unexpected error: {e!s}"
            )
            logger.error(f"Unexpected error in background job {job_id}: {e}", exc_info=True)
        
        finally:
            # Always close clients when done
            try:
                weaviate_client.close()
            except Exception as e:
                logger.warning(f"Error closing Weaviate client: {e}")

    except Exception as e:
        # Outer exception handler for critical failures before client creation
        BackgroundJobManager.update_job(
            job_id, "failed", None, f"Critical error: {e!s}"
        )
        logger.error(f"Critical error in background job {job_id}: {e}", exc_info=True)
