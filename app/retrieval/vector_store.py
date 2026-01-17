"""
Pinecone vector store wrapper with production features.
Handles index management, upserts, queries, and metadata filtering.
"""

import time
from typing import Any

from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PineconeVectorStore:
    """
    Production-ready Pinecone vector store.

    Features:
    - Automatic index creation
    - Batch upserts with progress tracking
    - Metadata filtering
    - Namespace support (multi-tenancy)
    """

    def __init__(self, index_name: str | None = None, namespace: str = "default"):
        """
        Initialize Pinecone client and connect to index.

        Args:
            index_name: Name of Pinecone index
            namespace: Namespace for multi-tenancy
        """

        self.index_name = index_name or settings.pinecone_index_name
        self.namespace = namespace

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.pinecone_api_key)

        # Connect to index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

        # Stats
        self.stats = {"total_upserted": 0, "total_queries": 0, "avg_query_time": 0}

        logger.info(
            "Pinecone store initialized",
            extra={"index": self.index_name, "namespace": self.namespace},
        )

    def _ensure_index_exists(self) -> None:
        """
        Create index if it doesn't exist.
        Uses serverless spec for cost efficiency.
        """

        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name in existing_indexes:
            logger.info(f"Index '{self.index_name}' already exists")
            return

        logger.info(f"Creating index '{self.index_name}'")

        try:
            self.pc.create_index(
                name=self.index_name,
                dimension=settings.pinecone_dimension,
                metric=settings.pinecone_metric,
                spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
            )

            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            time.sleep(10)  # Serverless indexes are usually ready quickly

            logger.info(f"Index '{self.index_name}' created successfully")

        except Exception as e:
            logger.error(f"Failed to create index: {e}", exc_info=True)
            raise

    def upsert_documents(
        self, documents: list[Document], batch_size: int = 100, show_progress: bool = True
    ) -> None:
        """
        Upsert documents to Pinecone with embeddings.

        Args:
            documents: List of documents with embeddings in metadata
            batch_size: Number of vectors per upsert batch
            show_progress: Log progress
        """

        if not documents:
            logger.warning("No documents to upsert")
            return

        logger.info(f"Upserting {len(documents)} documents to namespace '{self.namespace}'")
        start_time = time.time()

        # Prepare vectors
        vectors = []
        for doc in documents:
            vector_id = self._generate_id(doc)
            embedding = doc.metadata.get("embedding")

            if not embedding:
                logger.warning(
                    f"Document missing embedding: {doc.metadata.get('source', 'unknown')}"
                )
                continue

            # Prepare metadata (Pinecone has metadata size limits)
            metadata = self._prepare_metadata(doc)

            vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

        # Upsert in batches
        total_batches = (len(vectors) + batch_size - 1) // batch_size

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            batch_num = i // batch_size + 1

            try:
                self.index.upsert(vectors=batch, namespace=self.namespace)

                self.stats["total_upserted"] += len(batch)

                if show_progress:
                    logger.info(
                        f"Batch {batch_num}/{total_batches} upserted", extra={"vectors": len(batch)}
                    )

            except Exception as e:
                logger.error(f"Failed to upsert batch {batch_num}: {e}", exc_info=True)
                raise

        elapsed = time.time() - start_time
        logger.info(
            f"Upsert complete: {len(vectors)} vectors in {elapsed:.2f}s",
            extra={"vectors_per_second": len(vectors) / elapsed},
        )

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 20,
        filter_metadata: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Query Pinecone for similar vectors.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            filter_metadata: Metadata filters (e.g., {"category": "compliance"})
            include_metadata: Return metadata in results

        Returns:
            List of matches with scores and metadata
        """

        start_time = time.time()

        try:
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=self.namespace,
                filter=filter_metadata,
                include_metadata=include_metadata,
            )

            # Update stats
            query_time = time.time() - start_time
            self.stats["total_queries"] += 1
            self.stats["avg_query_time"] = (
                self.stats["avg_query_time"] * (self.stats["total_queries"] - 1) + query_time
            ) / self.stats["total_queries"]

            logger.debug(
                f"Vector query returned {len(response.matches)} results in {query_time:.3f}s",
                extra={"top_k": top_k, "filter": filter_metadata},
            )

            return [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {},
                }
                for match in response.matches
            ]

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            raise

    def delete_namespace(self, namespace: str | None = None) -> None:
        """
        Delete all vectors in a namespace.

        Args:
            namespace: Namespace to delete (defaults to current)
        """

        ns = namespace or self.namespace
        logger.warning(f"Deleting all vectors in namespace '{ns}'")

        try:
            self.index.delete(delete_all=True, namespace=ns)
            logger.info(f"Namespace '{ns}' deleted")
        except Exception as e:
            logger.error(f"Failed to delete namespace: {e}", exc_info=True)
            raise

    def get_index_stats(self) -> dict[str, Any]:
        """Get index statistics."""

        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "namespaces": dict(stats.namespaces.items()),
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}

    def _generate_id(self, document: Document) -> str:
        """
        Generate unique ID for document.
        Format: {source}:{page}:{chunk_index}
        """

        source = document.metadata.get("source", "unknown")
        page = document.metadata.get("page", 0)
        chunk = document.metadata.get("chunk_index", 0)

        # Create deterministic ID
        return f"{source}:p{page}:c{chunk}"

    def _prepare_metadata(self, document: Document) -> dict[str, Any]:
        """
        Prepare metadata for Pinecone.

        Pinecone limits:
        - Metadata size: 40KB per vector
        - No nested objects
        - Values must be strings, numbers, booleans, or lists
        """

        metadata = document.metadata.copy()

        # Remove embedding (already stored as vector)
        metadata.pop("embedding", None)

        # Remove large fields
        if len(document.page_content) > 10000:
            # Store truncated content
            metadata["content"] = document.page_content[:10000] + "..."
        else:
            metadata["content"] = document.page_content

        # Ensure all values are JSON-serializable
        clean_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, str | int | float | bool):
                clean_metadata[key] = value
            elif isinstance(value, list) and all(isinstance(v, str | int | float) for v in value):
                clean_metadata[key] = value
            else:
                # Convert complex types to string
                clean_metadata[key] = str(value)

        return clean_metadata

    def get_stats(self) -> dict[str, Any]:
        """Get store statistics."""
        return {**self.stats, **self.get_index_stats()}
