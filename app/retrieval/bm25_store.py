"""
BM25 index for keyword-based sparse retrieval.
Complements dense vector search with traditional IR algorithms.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

from rank_bm25 import BM25Okapi
from langchain.schema import Document

from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)


class BM25Store:
    """
    BM25 keyword search index.
    
    BM25 (Best Matching 25) is a ranking function used for information retrieval.
    It excels at:
    - Exact keyword matches
    - Rare term detection
    - Short, precise queries
    
    Complements dense retrieval which is better at:
    - Semantic understanding
    - Paraphrasing
    - Context-aware matching
    """
    
    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize BM25 store.
        
        Args:
            index_path: Path to save/load index
        """
        
        self.index_path = index_path or settings.index_dir / "bm25_index.pkl"
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
        
        logger.info(f"BM25 store initialized with path: {self.index_path}")
    
    def build_index(self, documents: List[Document]) -> None:
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of documents to index
        """
        
        if not documents:
            logger.warning("No documents to index")
            return
        
        logger.info(f"Building BM25 index from {len(documents)} documents")
        
        self.documents = documents
        
        # Tokenize documents
        self.tokenized_corpus = [
            self._tokenize(doc.page_content) for doc in documents
        ]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        logger.info(
            "BM25 index built",
            extra={
                "num_docs": len(documents),
                "avg_tokens": sum(len(tokens) for tokens in self.tokenized_corpus) / len(self.tokenized_corpus)
            }
        )
    
    def search(
        self,
        query: str,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search BM25 index.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of results with scores
        """
        
        if self.bm25 is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = scores.argsort()[-top_k:][::-1]
        
        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                doc = self.documents[idx]
                results.append({
                    "id": self._get_doc_id(doc),
                    "score": float(scores[idx]),
                    "document": doc,
                    "metadata": doc.metadata
                })
        
        logger.debug(
            f"BM25 search returned {len(results)} results",
            extra={"query": query[:50], "top_k": top_k}
        )
        
        return results
    
    def save_index(self) -> None:
        """
        Save index to disk.
        Enables fast loading without re-indexing.
        """
        
        if self.bm25 is None:
            logger.warning("No index to save")
            return
        
        logger.info(f"Saving BM25 index to {self.index_path}")
        
        # Ensure directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save index data
        index_data = {
            "bm25": self.bm25,
            "documents": self.documents,
            "tokenized_corpus": self.tokenized_corpus
        }
        
        try:
            with open(self.index_path, "wb") as f:
                pickle.dump(index_data, f)
            
            logger.info(
                f"Index saved successfully",
                extra={"size_mb": self.index_path.stat().st_size / 1024 / 1024}
            )
        except Exception as e:
            logger.error(f"Failed to save index: {e}", exc_info=True)
            raise
    
    def load_index(self) -> bool:
        """
        Load index from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        
        if not self.index_path.exists():
            logger.info(f"No index found at {self.index_path}")
            return False
        
        logger.info(f"Loading BM25 index from {self.index_path}")
        
        try:
            with open(self.index_path, "rb") as f:
                index_data = pickle.load(f)
            
            self.bm25 = index_data["bm25"]
            self.documents = index_data["documents"]
            self.tokenized_corpus = index_data["tokenized_corpus"]
            
            logger.info(
                f"Index loaded successfully",
                extra={"num_docs": len(self.documents)}
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}", exc_info=True)
            return False
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.
        
        Simple whitespace tokenization with basic normalization.
        For production, consider using proper tokenizers (spaCy, nltk).
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        
        # Lowercase
        text = text.lower()
        
        # Simple split on whitespace and punctuation
        # Keep alphanumeric and some special chars (for financial terms like "10-K")
        import re
        tokens = re.findall(r'\b[\w\-\.]+\b', text)
        
        return tokens
    
    def _get_doc_id(self, document: Document) -> str:
        """Generate document ID."""
        source = document.metadata.get("source", "unknown")
        page = document.metadata.get("page", 0)
        chunk = document.metadata.get("chunk_index", 0)
        return f"{source}:p{page}:c{chunk}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "indexed": self.bm25 is not None,
            "num_documents": len(self.documents),
            "index_exists": self.index_path.exists()
        }