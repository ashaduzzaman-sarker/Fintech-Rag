"""
Embedding generation with batching, caching, and error handling.
Supports OpenAI embeddings with retry logic and rate limiting.
"""

from typing import List, Dict, Any, Optional
import hashlib
import time

from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import openai

from app.core.logging import get_logger
from app.core.config import settings


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
        self,
        model_name: Optional[str] = None,
        batch_size: int = 100,
        cache_enabled: bool = False
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
        
        # Initialize embeddings model
        self.embeddings = OpenAIEmbeddings(
            model=self.model_name,
            openai_api_key=settings.openai_api_key,
            # Adjust batch size for rate limits
            chunk_size=batch_size
        )
        
        # Simple in-memory cache (development only)
        self._cache: Dict[str, List[float]] = {}
        
        # Stats
        self.stats = {
            "total_embedded": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "total_tokens": 0
        }
        
        logger.info(
            "Embedding generator initialized",
            extra={
                "model": self.model_name,
                "batch_size": self.batch_size,
                "cache_enabled": self.cache_enabled
            }
        )
    
    def embed_documents(self, documents: List[Document]) -> List[Document]:
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
        for doc, embedding in zip(documents, all_embeddings):
            doc.metadata["embedding"] = embedding
            doc.metadata["embedding_model"] = self.model_name
        
        elapsed = time.time() - start_time
        logger.info(
            f"Embedded {len(documents)} documents in {elapsed:.2f}s",
            extra={
                "docs_per_second": len(documents) / elapsed,
                "stats": self.stats
            }
        )
        
        return documents
    
    def _embed_texts_batched(self, texts: List[str]) -> List[List[float]]:
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
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
            
            logger.debug(
                f"Processing batch {batch_num}/{total_batches}",
                extra={"batch_size": len(batch)}
            )
            
            try:
                batch_embeddings = self._embed_batch_with_cache(batch)
                all_embeddings.extend(batch_embeddings)
                self.stats["total_embedded"] += len(batch)
            except Exception as e:
                logger.error(
                    f"Failed to embed batch {batch_num}: {str(e)}",
                    exc_info=True
                )
                # Return zero vectors for failed batch (or raise)
                raise
        
        return all_embeddings
    
    def _embed_batch_with_cache(self, texts: List[str]) -> List[List[float]]:
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
        embeddings = []
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
                embeddings.append(None)  # Placeholder
        
        # Embed uncached texts
        if texts_to_embed:
            new_embeddings = self._embed_batch_with_retry(texts_to_embed)
            
            # Store in cache and insert into results
            for idx, text, embedding in zip(indices_to_embed, texts_to_embed, new_embeddings):
                cache_key = self._get_cache_key(text)
                self._cache[cache_key] = embedding
                embeddings[idx] = embedding
        
        return embeddings
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True
    )
    def _embed_batch_with_retry(self, texts: List[str]) -> List[List[float]]:
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
        return hashlib.md5(
            f"{self.model_name}:{text}".encode()
        ).hexdigest()
    
    def embed_query(self, query: str) -> List[float]:
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        stats = self.stats.copy()
        stats["cache_size"] = len(self._cache)
        return stats