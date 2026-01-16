"""
Configuration management using Pydantic Settings.
Validates environment variables at startup and provides type-safe access.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="FinTech RAG Assistant")
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 2048

    # Pinecone
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_environment: str = "us-east-1-aws"
    pinecone_index_name: str = "fintech-rag-prod"
    pinecone_dimension: int = 3072
    pinecone_metric: Literal["cosine", "euclidean", "dotproduct"] = "cosine"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Cohere
    cohere_api_key: str = Field(..., description="Cohere API key")
    cohere_rerank_model: str = "rerank-english-v3.0"
    cohere_rerank_top_n: int = 10

    # Retrieval Configuration
    retrieval_top_k_vector: int = Field(
        default=20, 
        ge=1, 
        le=100,
        description="Number of results from vector search"
    )
    retrieval_top_k_bm25: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of results from BM25 search"
    )
    retrieval_rerank_top_n: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Final number of reranked results"
    )
    chunk_size: int = Field(default=800, ge=100, le=2000)
    chunk_overlap: int = Field(default=200, ge=0, le=500)

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError(f"chunk_overlap ({v}) must be < chunk_size ({chunk_size})")
        return v

    # Generation Configuration
    rag_context_window: int = Field(
        default=4000,
        description="Max tokens for RAG context"
    )
    rag_system_prompt_version: str = "v1"
    enable_citation_validation: bool = True

    # Data Paths
    data_dir: Path = Field(default=Path("./data"))
    raw_data_dir: Path = Field(default=Path("./data/raw"))
    processed_data_dir: Path = Field(default=Path("./data/processed"))
    index_dir: Path = Field(default=Path("./data/indexes"))

    # Security
    api_key_name: str = "X-API-Key"
    api_key: str | None = None

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, ge=1)

    # Optional: Local LLM
    local_llm_enabled: bool = False
    local_llm_model_path: Path | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        for path in [self.data_dir, self.raw_data_dir, 
                     self.processed_data_dir, self.index_dir]:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure singleton behavior.
    """
    return Settings()


# Convenience export
settings = get_settings()