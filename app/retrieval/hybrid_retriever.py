"""
Hybrid retrieval combining dense (vector) and sparse (BM25) search.
Uses Reciprocal Rank Fusion (RRF) to merge results.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from langchain.schema import Document

from app.core.logging import get_logger
from app.core.config import settings
from app.retrieval.vector_store import PineconeVectorStore
from app.retrieval.bm25_store import BM25Store
from app.ingestion.embedders import EmbeddingGenerator


logger = get_logger(__name__)


class HybridRetriever:
    """
    Hybrid retrieval system combining:
    1. Dense retrieval (semantic similarity via embeddings)
    2. Sparse retrieval (keyword matching via BM25)
    
    Uses Reciprocal Rank Fusion to combine results.
    
    Why Hybrid?
    - Dense: Good for semantic queries, paraphrasing, context
    - Sparse: Good for exact matches, rare terms, acronyms
    - Together: Best of both worlds
    
    Example:
    Query: "What are our Basel III capital requirements?"
    - Dense finds: sections about "capital adequacy", "regulatory requirements"
    - Sparse finds: exact matches for "Basel III"
    - RRF combines both for optimal results
    """
    
    def __init__(
        self,
        vector_store: PineconeVectorStore,
        bm25_store: BM25Store,
        embedder: EmbeddingGenerator,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: Pinecone vector store
            bm25_store: BM25 keyword store
            embedder: Embedding generator for queries
            vector_weight: Weight for dense retrieval (0-1)
            bm25_weight: Weight for sparse retrieval (0-1)
        """
        
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.embedder = embedder
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        
        # Validate weights
        if not (0 <= vector_weight <= 1 and 0 <= bm25_weight <= 1):
            raise ValueError("Weights must be between 0 and 1")
        
        logger.info(
            "Hybrid retriever initialized",
            extra={
                "vector_weight": vector_weight,
                "bm25_weight": bm25_weight
            }
        )
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        vector_top_k: int = None,
        bm25_top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval with RRF fusion.
        
        Args:
            query: Search query
            top_k: Final number of results (after fusion)
            vector_top_k: Number of vector results to fetch
            bm25_top_k: Number of BM25 results to fetch
            filter_metadata: Metadata filters for vector search
            
        Returns:
            Fused and ranked results
        """
        
        top_k = top_k or settings.retrieval_rerank_top_n
        vector_top_k = vector_top_k or settings.retrieval_top_k_vector
        bm25_top_k = bm25_top_k or settings.retrieval_top_k_bm25
        
        logger.info(
            f"Hybrid retrieval for query: '{query[:50]}...'",
            extra={
                "vector_top_k": vector_top_k,
                "bm25_top_k": bm25_top_k,
                "final_top_k": top_k
            }
        )
        
        # 1. Dense retrieval
        vector_results = self._vector_search(
            query=query,
            top_k=vector_top_k,
            filter_metadata=filter_metadata
        )
        
        # 2. Sparse retrieval
        bm25_results = self._bm25_search(
            query=query,
            top_k=bm25_top_k
        )
        
        # 3. Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            bm25_results=bm25_results,
            top_k=top_k
        )
        
        logger.info(
            f"Retrieved {len(fused_results)} results",
            extra={
                "vector_count": len(vector_results),
                "bm25_count": len(bm25_results),
                "fused_count": len(fused_results)
            }
        )
        
        return fused_results
    
    def _vector_search(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Dense vector search.
        
        Args:
            query: Search query
            top_k: Number of results
            filter_metadata: Metadata filters
            
        Returns:
            List of results with scores
        """
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Search Pinecone
        matches = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Format results
        results = []
        for match in matches:
            results.append({
                "id": match["id"],
                "score": match["score"],
                "metadata": match["metadata"],
                "content": match["metadata"].get("content", ""),
                "source": "vector"
            })
        
        return results
    
    def _bm25_search(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Sparse BM25 search.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of results with scores
        """
        
        results = self.bm25_store.search(query=query, top_k=top_k)
        
        # Format results consistently
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result["id"],
                "score": result["score"],
                "metadata": result["metadata"],
                "content": result["document"].page_content,
                "source": "bm25"
            })
        
        return formatted_results
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm.
        
        RRF Formula:
        score(d) = Σ 1 / (k + rank(d))
        
        where:
        - d: document
        - rank(d): position in result list
        - k: constant (typically 60)
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            top_k: Number of final results
            k: RRF constant
            
        Returns:
            Fused and re-ranked results
        """
        
        # Build rank dictionaries
        vector_ranks = {r["id"]: idx for idx, r in enumerate(vector_results)}
        bm25_ranks = {r["id"]: idx for idx, r in enumerate(bm25_results)}
        
        # Collect all unique document IDs
        all_ids = set(vector_ranks.keys()) | set(bm25_ranks.keys())
        
        # Calculate RRF scores
        rrf_scores = {}
        doc_map = {}  # Store document data
        
        for doc_id in all_ids:
            score = 0.0
            
            # Add vector contribution
            if doc_id in vector_ranks:
                score += self.vector_weight / (k + vector_ranks[doc_id] + 1)
                # Store document from first source
                if doc_id not in doc_map:
                    doc = next(r for r in vector_results if r["id"] == doc_id)
                    doc_map[doc_id] = doc
            
            # Add BM25 contribution
            if doc_id in bm25_ranks:
                score += self.bm25_weight / (k + bm25_ranks[doc_id] + 1)
                # Store document if not already stored
                if doc_id not in doc_map:
                    doc = next(r for r in bm25_results if r["id"] == doc_id)
                    doc_map[doc_id] = doc
            
            rrf_scores[doc_id] = score
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Build final results
        fused_results = []
        for doc_id in sorted_ids[:top_k]:
            doc = doc_map[doc_id]
            doc["rrf_score"] = rrf_scores[doc_id]
            doc["in_vector"] = doc_id in vector_ranks
            doc["in_bm25"] = doc_id in bm25_ranks
            fused_results.append(doc)
        
        return fused_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            "vector_store": self.vector_store.get_stats(),
            "bm25_store": self.bm25_store.get_stats(),
            "weights": {
                "vector": self.vector_weight,
                "bm25": self.bm25_weight
            }
        }