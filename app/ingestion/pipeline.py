"""
Ingestion pipeline orchestrator.
Coordinates loading, chunking, embedding, and indexing.
"""

import time
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.core.logging import get_logger
from app.ingestion.chunkers import AdvancedSemanticChunker, SemanticChunker
from app.ingestion.embedders import EmbeddingGenerator
from app.ingestion.loaders import DocumentLoader

logger = get_logger(__name__)


class IngestionPipeline:
    """
    Orchestrates the complete ingestion pipeline:
    Load → Chunk → Embed → Index

    Designed for:
    - Batch processing (1000+ documents)
    - Progress tracking
    - Error recovery
    - Idempotency
    """

    def __init__(self, use_advanced_chunking: bool = True, batch_size: int = 100):
        """
        Initialize pipeline components.

        Args:
            use_advanced_chunking: Use structure-aware chunking
            batch_size: Embedding batch size
        """

        self.loader = DocumentLoader()

        self.chunker = AdvancedSemanticChunker() if use_advanced_chunking else SemanticChunker()

        self.embedder = EmbeddingGenerator(batch_size=batch_size)

        self.stats = {
            "total_files": 0,
            "total_chunks": 0,
            "total_tokens": 0,
            "failed_files": 0,
            "processing_time": 0.0,
        }

        logger.info(
            "Ingestion pipeline initialized", extra={"advanced_chunking": use_advanced_chunking}
        )

    def process_directory(self, directory: Path, recursive: bool = True) -> list[Document]:
        """
        Process all documents in a directory.

        Args:
            directory: Directory containing documents
            recursive: Search subdirectories

        Returns:
            List of processed document chunks with embeddings
        """

        logger.info(f"Starting ingestion from {directory}")
        start_time = time.time()

        try:
            # Step 1: Load documents
            logger.info("Step 1/3: Loading documents")
            raw_documents = self.loader.load_directory(directory=directory, recursive=recursive)

            if not raw_documents:
                logger.warning("No documents loaded")
                return []

            self.stats["total_files"] = self.loader.stats["total_loaded"]

            # Step 2: Chunk documents
            logger.info(f"Step 2/3: Chunking {len(raw_documents)} documents")
            chunked_documents = self.chunker.chunk_documents(raw_documents)
            self.stats["total_chunks"] = len(chunked_documents)

            # Calculate total tokens
            self.stats["total_tokens"] = sum(
                doc.metadata.get("chunk_tokens", 0) for doc in chunked_documents
            )

            # Step 3: Generate embeddings
            logger.info(f"Step 3/3: Generating embeddings for {len(chunked_documents)} chunks")
            embedded_documents = self.embedder.embed_documents(chunked_documents)

            # Update stats
            self.stats["processing_time"] = time.time() - start_time
            self.stats["failed_files"] = self.loader.stats["failed"]

            logger.info(
                "Ingestion complete",
                extra={
                    **self.stats,
                    "avg_chunks_per_file": self.stats["total_chunks"]
                    / max(1, self.stats["total_files"]),
                    "docs_per_second": self.stats["total_chunks"]
                    / max(1, self.stats["processing_time"]),
                },
            )

            return embedded_documents

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def process_file(self, file_path: Path) -> list[Document]:
        """
        Process a single file through the pipeline.

        Args:
            file_path: Path to document file

        Returns:
            List of processed chunks
        """

        logger.info(f"Processing single file: {file_path.name}")
        start_time = time.time()

        try:
            # Load
            raw_documents = self.loader.load_document(file_path)

            # Chunk
            chunked_documents = self.chunker.chunk_documents(raw_documents)

            # Embed
            embedded_documents = self.embedder.embed_documents(chunked_documents)

            elapsed = time.time() - start_time
            logger.info(
                f"Processed {file_path.name}",
                extra={"chunks": len(embedded_documents), "time": f"{elapsed:.2f}s"},
            )

            return embedded_documents

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}", exc_info=True)
            raise

    def process_documents(
        self, documents: list[Document], skip_embedding: bool = False
    ) -> list[Document]:
        """
        Process pre-loaded documents (useful for incremental updates).

        Args:
            documents: List of documents
            skip_embedding: Skip embedding generation

        Returns:
            Processed documents
        """

        logger.info(f"Processing {len(documents)} pre-loaded documents")

        # Chunk
        chunked_documents = self.chunker.chunk_documents(documents)

        if skip_embedding:
            return chunked_documents

        # Embed
        embedded_documents = self.embedder.embed_documents(chunked_documents)

        return embedded_documents

    def estimate_cost(self, directory: Path, recursive: bool = True) -> dict[str, Any]:
        """
        Estimate processing cost before running pipeline.

        Args:
            directory: Directory to analyze
            recursive: Search subdirectories

        Returns:
            Cost estimate with token counts and pricing
        """

        logger.info(f"Estimating cost for {directory}")

        # Load documents (fast, no embedding)
        raw_documents = self.loader.load_directory(directory, recursive)

        if not raw_documents:
            return {"error": "No documents found"}

        # Chunk to get accurate token counts
        chunked_documents = self.chunker.chunk_documents(raw_documents)

        total_tokens = sum(doc.metadata.get("chunk_tokens", 0) for doc in chunked_documents)

        # Estimate embedding cost (OpenAI pricing as of 2024)
        # text-embedding-3-large: $0.13 per 1M tokens
        embedding_cost = (total_tokens / 1_000_000) * 0.13

        estimate = {
            "total_files": len(raw_documents),
            "total_chunks": len(chunked_documents),
            "total_tokens": total_tokens,
            "avg_chunk_size": total_tokens / len(chunked_documents) if chunked_documents else 0,
            "estimated_embedding_cost_usd": round(embedding_cost, 4),
            "estimated_time_minutes": round(len(chunked_documents) / 100, 1),  # ~100 chunks/min
        }

        logger.info("Cost estimate complete", extra=estimate)

        return estimate

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        return {
            **self.stats,
            "loader_stats": self.loader.get_stats(),
            "embedder_stats": self.embedder.get_stats(),
        }
