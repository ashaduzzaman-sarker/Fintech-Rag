"""
Embedding generation with batching, caching, and error handling.
Supports OpenAI embeddings with retry logic and rate limiting.
"""

import hashlib
import time
from typing import Any, cast

import openai
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Manages embedding generation with production-grade features:
    - Batch processing
    - Retry logic for transient failures
    - Progress tracking
    - Optional caching
    """

    def __init__(
        self, model_name: str | None = None, batch_size: int = 100, cache_enabled: bool = False
    ):
        """
        Initialize embedding generator.

        Args:
            model_name: OpenAI embedding model
            batch_size: Number of texts to embed in one API call
            cache_enabled: Whether to cache embeddings (development only)
        """

        self.model_name = model_name or settings.openai_embedding_model
        self.batch_size = batch_size
        self.cache_enabled = cache_enabled and settings.is_development

        # Initialize embeddings model (API key is read from environment)
        self.embeddings = OpenAIEmbeddings(
            model=self.model_name,
            # Adjust batch size for rate limits
            chunk_size=batch_size,
        )

        # Simple in-memory cache (development only)
        self._cache: dict[str, list[float]] = {}

        # Stats
        self.stats = {"total_embedded": 0, "cache_hits": 0, "api_calls": 0, "total_tokens": 0}

        logger.info(
            "Embedding generator initialized",
            extra={
                "model": self.model_name,
                "batch_size": self.batch_size,
                "cache_enabled": self.cache_enabled,
            },
        )

    def embed_documents(self, documents: list[Document]) -> list[Document]:
        """
        Generate embeddings for a list of documents.

        Args:
            documents: Documents to embed

        Returns:
            Documents with 'embedding' added to metadata
        """

        if not documents:
            logger.warning("No documents to embed")
            return []

        logger.info(f"Embedding {len(documents)} documents")
        start_time = time.time()

        # Extract texts
        texts = [doc.page_content for doc in documents]

        # Generate embeddings in batches
        all_embeddings = self._embed_texts_batched(texts)

        # Attach embeddings to documents
        for doc, embedding in zip(documents, all_embeddings, strict=False):
            doc.metadata["embedding"] = embedding
            doc.metadata["embedding_model"] = self.model_name

        elapsed = time.time() - start_time
        logger.info(
            f"Embedded {len(documents)} documents in {elapsed:.2f}s",
            extra={"docs_per_second": len(documents) / elapsed, "stats": self.stats},
        )

        return documents

    def _embed_texts_batched(self, texts: list[str]) -> list[list[float]]:
        """
        Embed texts in batches with error handling.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

            logger.debug(
                f"Processing batch {batch_num}/{total_batches}", extra={"batch_size": len(batch)}
            )

            try:
                batch_embeddings = self._embed_batch_with_cache(batch)
                all_embeddings.extend(batch_embeddings)
                self.stats["total_embedded"] += len(batch)
            except Exception as e:
                logger.error(f"Failed to embed batch {batch_num}: {str(e)}", exc_info=True)
                # Return zero vectors for failed batch (or raise)
                raise

        return all_embeddings

    def _embed_batch_with_cache(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts, using cache when available.

        Args:
            texts: Batch of texts

        Returns:
            List of embeddings
        """

        if not self.cache_enabled:
            return self._embed_batch_with_retry(texts)

        # Check cache
        embeddings: list[list[float] | None] = []
        texts_to_embed = []
        indices_to_embed = []

        for idx, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                embeddings.append(self._cache[cache_key])
                self.stats["cache_hits"] += 1
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(idx)
                embeddings.append(None)  # Placeholder for later fill

        # Embed uncached texts
        if texts_to_embed:
            new_embeddings = self._embed_batch_with_retry(texts_to_embed)

            # Store in cache and insert into results
            for idx, text, embedding in zip(
                indices_to_embed, texts_to_embed, new_embeddings, strict=False
            ):
                cache_key = self._get_cache_key(text)
                self._cache[cache_key] = embedding
                embeddings[idx] = embedding

        # At this point all placeholders should be filled (or every entry came from cache)
        return cast(list[list[float]], embeddings)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
    def _embed_batch_with_retry(self, texts: list[str]) -> list[list[float]]:
        """
        Embed batch with automatic retry on transient failures.

        Args:
            texts: Batch of texts

        Returns:
            List of embeddings
        """

        self.stats["api_calls"] += 1

        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit hit, retrying: {e}")
            raise
        except openai.APITimeoutError as e:
            logger.warning(f"API timeout, retrying: {e}")
            raise
        except Exception as e:
            logger.error(f"Embedding error: {e}", exc_info=True)
            raise

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        # Use SHA-256 to avoid insecure hash warnings from security linters
        return hashlib.sha256(f"{self.model_name}:{text}".encode()).hexdigest()

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a single query text.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """

        cache_key = self._get_cache_key(query)

        if self.cache_enabled and cache_key in self._cache:
            self.stats["cache_hits"] += 1
            return self._cache[cache_key]

        try:
            embedding = self.embeddings.embed_query(query)

            if self.cache_enabled:
                self._cache[cache_key] = embedding

            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}", exc_info=True)
            raise

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings from this model.

        Returns:
            Embedding dimension
        """

        # Embedding dimensions for common OpenAI models
        dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }

        return dimensions.get(self.model_name, 1536)

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get embedding statistics."""
        stats = self.stats.copy()
        stats["cache_size"] = len(self._cache)
        return stats
