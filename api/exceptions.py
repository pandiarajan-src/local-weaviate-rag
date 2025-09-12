"""
Custom exception classes for the RAG API.
"""

from typing import Any


class RAGAPIError(Exception):
    """Base exception for RAG API errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Any | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationError(RAGAPIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=400,
            details=details,
        )


class NotFoundError(RAGAPIError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} '{identifier}' not found",
            error_code="not_found",
            status_code=404,
        )


class ExternalServiceError(RAGAPIError):
    """Raised when external service (OpenAI, Weaviate) fails."""

    def __init__(self, service: str, message: str, details: Any | None = None):
        super().__init__(
            message=f"{service} service error: {message}",
            error_code="external_service_error",
            status_code=502,
            details=details,
        )


class DatabaseError(RAGAPIError):
    """Raised when database operations fail."""

    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=f"Database error: {message}",
            error_code="database_error",
            status_code=500,
            details=details,
        )


class ConfigurationError(RAGAPIError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(
            message=f"Configuration error: {message}",
            error_code="configuration_error",
            status_code=500,
        )


class FileProcessingError(RAGAPIError):
    """Raised when file processing fails."""

    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=f"File processing error: {message}",
            error_code="file_processing_error",
            status_code=422,
            details=details,
        )


class InternalProcessingError(RAGAPIError):
    """Raised when internal processing fails."""

    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=f"Processing error: {message}",
            error_code="processing_error",
            status_code=500,
            details=details,
        )
