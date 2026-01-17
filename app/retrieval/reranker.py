"""
Cohere reranking for retrieval quality improvement.

Reranking is a two-stage retrieval approach:
1. Initial retrieval (fast, approximate)
2. Reranking (slow, accurate)

Why rerank?
- Cross-encoders are more accurate than bi-encoders (embeddings)
- But they're too slow to run on entire corpus
- Solution: retrieve candidates, then rerank top-K

Performance improvement: typically +10-20% in relevance metrics
"""

from typing import Any

import cohere
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CohereReranker:
    """
    Cohere cross-encoder reranker.

    Takes initial retrieval results and reorders them by relevance
    using a more sophisticated model.
    """

    def __init__(self, model: str | None = None, top_n: int | None = None):
        """
        Initialize Cohere reranker.

        Args:
            model: Cohere rerank model name
            top_n: Number of top results to return after reranking
        """

        self.model = model or settings.cohere_rerank_model
        self.top_n = top_n or settings.cohere_rerank_top_n

        # Initialize Cohere client
        self.client = cohere.Client(api_key=settings.cohere_api_key)

        # Stats
        self.stats = {
            "total_reranks": 0,
            "total_documents": 0,
            "avg_rerank_time": 0.0,
        }

        logger.info("Cohere reranker initialized", extra={"model": self.model, "top_n": self.top_n})

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True
    )
    def rerank(
        self, query: str, documents: list[dict[str, Any]], top_n: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Rerank documents using Cohere.

        Args:
            query: Search query
            documents: List of documents to rerank (from hybrid retrieval)
            top_n: Number of top results to return

        Returns:
            Reranked documents with relevance scores
        """

        if not documents:
            logger.warning("No documents to rerank")
            return []

        top_n = top_n or self.top_n

        logger.info(
            f"Reranking {len(documents)} documents", extra={"query": query[:50], "top_n": top_n}
        )

        # Extract texts for reranking
        texts = [doc.get("content", "") for doc in documents]

        # Ensure texts are not empty
        texts = [text if text else " " for text in texts]

        try:
            import time

            start_time = time.time()

            # Call Cohere rerank API
            response = self.client.rerank(
                query=query, documents=texts, model=self.model, top_n=min(top_n, len(documents))
            )

            # Update stats
            rerank_time = time.time() - start_time
            self.stats["total_reranks"] += 1
            self.stats["total_documents"] += len(documents)
            self.stats["avg_rerank_time"] = (
                self.stats["avg_rerank_time"] * (self.stats["total_reranks"] - 1) + rerank_time
            ) / self.stats["total_reranks"]

            # Build reranked results
            reranked = []
            for result in response.results:
                # Get original document
                doc = documents[result.index].copy()

                # Update with rerank score
                doc["rerank_score"] = result.relevance_score
                doc["rerank_index"] = result.index

                reranked.append(doc)

            logger.info(
                f"Reranked {len(documents)} → {len(reranked)} documents in {rerank_time:.3f}s",
                extra={
                    "top_score": reranked[0]["rerank_score"] if reranked else None,
                    "bottom_score": reranked[-1]["rerank_score"] if reranked else None,
                },
            )

            return reranked

        except Exception as e:
            logger.error(
                f"Reranking failed: {e}",
                exc_info=True,
                extra={"query": query[:50], "num_docs": len(documents)},
            )

            # Fallback: return original documents
            logger.warning("Returning original order due to reranking failure")
            return documents[:top_n]

    def rerank_with_threshold(
        self,
        query: str,
        documents: list[dict[str, Any]],
        threshold: float = 0.5,
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Rerank and filter by relevance threshold.

        Useful for ensuring quality: only return highly relevant results.

        Args:
            query: Search query
            documents: Documents to rerank
            threshold: Minimum relevance score (0-1)
            top_n: Maximum number of results

        Returns:
            Filtered and reranked documents
        """

        reranked = self.rerank(query, documents, top_n)

        # Filter by threshold
        filtered = [doc for doc in reranked if doc.get("rerank_score", 0) >= threshold]

        logger.info(
            f"Filtered reranked results: {len(reranked)} → {len(filtered)} (threshold={threshold})"
        )

        return filtered

    def compare_ranking(
        self,
        query: str,
        documents: list[dict[str, Any]],
        original_key: str = "rrf_score",
        rerank_key: str = "rerank_score",
    ) -> dict[str, Any]:
        """
        Compare original ranking vs reranking.
        Useful for evaluation and debugging.

        Args:
            query: Search query
            documents: Documents with both original and rerank scores
            original_key: Key for original scores
            rerank_key: Key for rerank scores

        Returns:
            Comparison statistics
        """

        if not documents:
            return {}

        # Sort by original scores
        original_order = sorted(
            enumerate(documents), key=lambda x: x[1].get(original_key, 0), reverse=True
        )

        # Sort by rerank scores
        rerank_order = sorted(
            enumerate(documents), key=lambda x: x[1].get(rerank_key, 0), reverse=True
        )

        # Calculate rank changes
        rank_changes = []
        for new_rank, (orig_idx, _doc) in enumerate(rerank_order):
            orig_rank = next(i for i, (idx, _) in enumerate(original_order) if idx == orig_idx)
            rank_change = orig_rank - new_rank
            rank_changes.append(rank_change)

        # Statistics
        avg_rank_change = sum(abs(c) for c in rank_changes) / len(rank_changes)
        max_improvement = max(rank_changes)  # Positive = moved up
        max_decline = min(rank_changes)  # Negative = moved down

        return {
            "num_documents": len(documents),
            "avg_rank_change": avg_rank_change,
            "max_improvement": max_improvement,
            "max_decline": max_decline,
            "top_3_changed": rank_changes[:3] != [0, 0, 0],
            "rerank_improved": avg_rank_change > 0,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get reranking statistics."""
        return self.stats.copy()
