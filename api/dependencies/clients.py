"""
Client dependencies for external services.
"""

from collections.abc import Generator
import logging

from openai import OpenAI
import weaviate
from weaviate.classes.init import AdditionalConfig

from ..exceptions import ConfigurationError, ExternalServiceError
from .config import get_settings

logger = logging.getLogger(__name__)


def get_weaviate_client() -> Generator[weaviate.WeaviateClient, None, None]:
    """
    FastAPI dependency for getting Weaviate client.
    Manages client lifecycle automatically.
    """
    settings = get_settings()
    client = None

    try:
        client = weaviate.connect_to_custom(
            http_host=settings.weaviate_host,
            http_port=settings.weaviate_port,
            http_secure=(settings.weaviate_scheme == "https"),
            grpc_host=settings.weaviate_host,
            grpc_port=settings.weaviate_grpc_port,
            grpc_secure=(settings.weaviate_scheme == "https"),
            auth_credentials=weaviate.auth.AuthApiKey(
                api_key=settings.weaviate_api_key
            ),
            additional_config=AdditionalConfig(timeout=(5, 60)),
        )

        # Test connection
        if not client.is_ready():
            raise ExternalServiceError(
                "Weaviate", "Database is not ready or connection failed"
            )

        yield client

    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise ExternalServiceError(
                "Weaviate",
                f"Could not connect to Weaviate at {settings.weaviate_scheme}://{settings.weaviate_host}:{settings.weaviate_port}. "
                f"Make sure Weaviate is running.",
            )
        elif "auth" in str(e).lower():
            raise ExternalServiceError(
                "Weaviate",
                "Authentication failed. Check WEAVIATE_API_KEY configuration.",
            )
        else:
            raise ExternalServiceError("Weaviate", str(e))
    finally:
        if client:
            try:
                client.close()
            except Exception as e:
                logger.warning(f"Error closing Weaviate client: {e}")


def get_openai_client() -> OpenAI:
    """
    FastAPI dependency for getting OpenAI client.
    """
    settings = get_settings()

    try:
        client_kwargs = {"api_key": settings.openai_api_key}

        # Set base URL if provided, otherwise use default
        if settings.openai_base_url and settings.openai_base_url.strip():
            client_kwargs["base_url"] = settings.openai_base_url.strip()
        else:
            client_kwargs["base_url"] = "https://api.openai.com/v1"

        client = OpenAI(**client_kwargs)

        return client

    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        if "api_key" in str(e).lower():
            raise ConfigurationError("Invalid OpenAI API key")
        else:
            raise ExternalServiceError("OpenAI", str(e))


def create_weaviate_client(config):
    """
    Create a new Weaviate client instance without dependency management.
    For use in background tasks where client lifecycle needs manual control.
    """
    try:
        client = weaviate.connect_to_custom(
            http_host=config.weaviate_host,
            http_port=config.weaviate_port,
            http_secure=(config.weaviate_scheme == "https"),
            grpc_host=config.weaviate_host,
            grpc_port=config.weaviate_grpc_port,
            grpc_secure=(config.weaviate_scheme == "https"),
            auth_credentials=weaviate.auth.AuthApiKey(
                api_key=config.weaviate_api_key
            ),
            additional_config=AdditionalConfig(timeout=(5, 60)),
        )

        # Test connection
        if not client.is_ready():
            raise ExternalServiceError(
                "Weaviate", "Database is not ready or connection failed"
            )

        return client

    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise ExternalServiceError(
                "Weaviate",
                f"Could not connect to Weaviate at {config.weaviate_scheme}://{config.weaviate_host}:{config.weaviate_port}. "
                f"Make sure Weaviate is running.",
            )
        elif "auth" in str(e).lower():
            raise ExternalServiceError(
                "Weaviate",
                "Authentication failed. Check WEAVIATE_API_KEY configuration.",
            )
        else:
            raise ExternalServiceError("Weaviate", str(e))


def create_openai_client(config):
    """
    Create a new OpenAI client instance.
    For use in background tasks.
    """
    try:
        client_kwargs = {"api_key": config.openai_api_key}

        # Set base URL if provided, otherwise use default
        if config.openai_base_url and config.openai_base_url.strip():
            client_kwargs["base_url"] = config.openai_base_url.strip()
        else:
            client_kwargs["base_url"] = "https://api.openai.com/v1"

        client = OpenAI(**client_kwargs)

        return client

    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        if "api_key" in str(e).lower():
            raise ConfigurationError("Invalid OpenAI API key")
        else:
            raise ExternalServiceError("OpenAI", str(e))


class ClientDependency:
    """Container for client dependencies."""

    def __init__(self, weaviate_client: weaviate.WeaviateClient, openai_client: OpenAI):
        self.weaviate = weaviate_client
        self.openai = openai_client
