"""
Configuration dependencies for the FastAPI application.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Weaviate Configuration
    weaviate_scheme: str = Field(default="http", alias="WEAVIATE_SCHEME")
    weaviate_host: str = Field(default="localhost", alias="WEAVIATE_HOST")
    weaviate_port: int = Field(default=8080, alias="WEAVIATE_PORT")
    weaviate_grpc_port: int = Field(default=50051, alias="WEAVIATE_GRPC_PORT")
    weaviate_api_key: str = Field(alias="WEAVIATE_API_KEY")

    # OpenAI Configuration
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_embed_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBED_MODEL")
    openai_completions_model: str = Field(default="gpt-4o", alias="OPENAI_COMPLETIONS_MODEL")

    # RAG Configuration
    rag_collection: str = Field(default="Documents", alias="RAG_COLLECTION")
    chunk_tokens: int = Field(default=400, alias="CHUNK_TOKENS")
    chunk_overlap: int = Field(default=60, alias="CHUNK_OVERLAP")
    hybrid_alpha: float = Field(default=0.5, alias="HYBRID_ALPHA")
    top_k: int = Field(default=5, alias="TOP_K")
    max_context_chunks: int = Field(default=6, alias="MAX_CONTEXT_CHUNKS")

    # API Configuration
    max_file_size: int = Field(default=50 * 1024 * 1024, alias="MAX_FILE_SIZE")  # 50MB
    max_text_size: int = Field(default=1024 * 1024, alias="MAX_TEXT_SIZE")  # 1MB

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    def validate_required_settings(self):
        """Validate that all required settings are present."""
        if (
            not self.weaviate_api_key
            or self.weaviate_api_key == "your-secure-api-key-here"
        ):
            raise ConfigurationError("WEAVIATE_API_KEY is not properly configured")

        if not self.openai_api_key or self.openai_api_key.startswith("sk-your"):
            raise ConfigurationError("OPENAI_API_KEY is not properly configured")


@lru_cache
def get_settings() -> Settings:
    """Get application settings (cached)."""
    settings = Settings()
    settings.validate_required_settings()
    return settings


def get_config() -> Settings:
    """FastAPI dependency for getting configuration."""
    return get_settings()
