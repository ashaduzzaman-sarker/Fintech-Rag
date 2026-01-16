"""
Evaluation metrics for retrieval and generation quality.

Implements industry-standard metrics:
- Precision@K: Fraction of retrieved documents that are relevant
- Recall@K: Fraction of relevant documents that are retrieved
- MRR (Mean Reciprocal Rank): Average of reciprocal ranks of first relevant result
- NDCG (Normalized Discounted Cumulative Gain): Ranking quality metric
"""

from typing import List, Dict, Set, Any
import numpy as np
from collections import defaultdict

from app.core.logging import get_logger


logger = get_logger(__name__)


class RetrievalMetrics:
    """
    Metrics for evaluating retrieval quality.
    
    Requires ground truth: which documents are relevant for each query.
    """
    
    @staticmethod
    def precision_at_k(
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Precision@K: Fraction of top-K retrieved docs that are relevant.
        
        Formula: P@K = |retrieved ∩ relevant| / K
        
        Args:
            retrieved: List of retrieved document IDs (ordered by rank)
            relevant: Set of relevant document IDs (ground truth)
            k: Number of top results to consider
            
        Returns:
            Precision score (0-1)
        """
        if not retrieved or not relevant:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_retrieved = len([doc for doc in top_k if doc in relevant])
        
        return relevant_retrieved / min(k, len(top_k))
    
    @staticmethod
    def recall_at_k(
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Recall@K: Fraction of relevant docs that are in top-K retrieved.
        
        Formula: R@K = |retrieved ∩ relevant| / |relevant|
        
        Args:
            retrieved: List of retrieved document IDs
            relevant: Set of relevant document IDs
            k: Number of top results to consider
            
        Returns:
            Recall score (0-1)
        """
        if not relevant:
            return 0.0
        if not retrieved:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_retrieved = len([doc for doc in top_k if doc in relevant])
        
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def average_precision(
        retrieved: List[str],
        relevant: Set[str]
    ) -> float:
        """
        Average Precision (AP): Average of P@K for each relevant doc.
        
        Formula: AP = (Σ P@k * rel(k)) / |relevant|
        
        Args:
            retrieved: List of retrieved document IDs (ordered)
            relevant: Set of relevant document IDs
            
        Returns:
            Average precision score (0-1)
        """
        if not relevant or not retrieved:
            return 0.0
        
        precisions = []
        relevant_count = 0
        
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                relevant_count += 1
                precision = relevant_count / (i + 1)
                precisions.append(precision)
        
        return sum(precisions) / len(relevant) if precisions else 0.0
    
    @staticmethod
    def mean_reciprocal_rank(
        retrieved_lists: List[List[str]],
        relevant_sets: List[Set[str]]
    ) -> float:
        """
        Mean Reciprocal Rank (MRR): Average of 1/rank of first relevant result.
        
        Formula: MRR = (1/|Q|) * Σ 1/rank_i
        
        Args:
            retrieved_lists: List of retrieved document lists (one per query)
            relevant_sets: List of relevant document sets (one per query)
            
        Returns:
            MRR score (0-1)
        """
        if not retrieved_lists or not relevant_sets:
            return 0.0
        
        reciprocal_ranks = []
        
        for retrieved, relevant in zip(retrieved_lists, relevant_sets):
            if not relevant:
                continue
            
            # Find rank of first relevant document
            for rank, doc_id in enumerate(retrieved, start=1):
                if doc_id in relevant:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                # No relevant document found
                reciprocal_ranks.append(0.0)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    @staticmethod
    def ndcg_at_k(
        retrieved: List[str],
        relevant: Set[str],
        k: int,
        relevance_scores: Dict[str, float] = None
    ) -> float:
        """
        Normalized Discounted Cumulative Gain (NDCG@K).
        
        Accounts for:
        - Position (earlier is better)
        - Graded relevance (if provided)
        
        Formula: NDCG@K = DCG@K / IDCG@K
        DCG@K = Σ (2^rel - 1) / log2(i + 1)
        
        Args:
            retrieved: List of retrieved document IDs
            relevant: Set of relevant document IDs
            k: Number of top results to consider
            relevance_scores: Optional graded relevance (0-1 or 0-5)
            
        Returns:
            NDCG score (0-1)
        """
        if not retrieved or not relevant:
            return 0.0
        
        # Default binary relevance
        if relevance_scores is None:
            relevance_scores = {doc: 1.0 for doc in relevant}
        
        def dcg(doc_list: List[str], k: int) -> float:
            dcg_score = 0.0
            for i, doc_id in enumerate(doc_list[:k]):
                rel = relevance_scores.get(doc_id, 0.0)
                dcg_score += (2 ** rel - 1) / np.log2(i + 2)
            return dcg_score
        
        # Calculate DCG
        dcg_score = dcg(retrieved, k)
        
        # Calculate IDCG (ideal DCG)
        ideal_order = sorted(
            relevance_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        ideal_docs = [doc for doc, _ in ideal_order]
        idcg_score = dcg(ideal_docs, k)
        
        return dcg_score / idcg_score if idcg_score > 0 else 0.0


class GenerationMetrics:
    """
    Metrics for evaluating answer generation quality.
    """
    
    @staticmethod
    def exact_match(
        prediction: str,
        reference: str,
        normalize: bool = True
    ) -> bool:
        """
        Exact match between prediction and reference.
        
        Args:
            prediction: Generated answer
            reference: Ground truth answer
            normalize: Lowercase and strip whitespace
            
        Returns:
            True if exact match
        """
        if normalize:
            prediction = prediction.lower().strip()
            reference = reference.lower().strip()
        
        return prediction == reference
    
    @staticmethod
    def f1_score(
        prediction: str,
        reference: str
    ) -> float:
        """
        Token-level F1 score.
        
        Measures overlap of tokens between prediction and reference.
        
        Args:
            prediction: Generated answer
            reference: Ground truth answer
            
        Returns:
            F1 score (0-1)
        """
        pred_tokens = set(prediction.lower().split())
        ref_tokens = set(reference.lower().split())
        
        if not pred_tokens or not ref_tokens:
            return 0.0
        
        common = pred_tokens & ref_tokens
        
        if not common:
            return 0.0
        
        precision = len(common) / len(pred_tokens)
        recall = len(common) / len(ref_tokens)
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def citation_accuracy(
        predicted_citations: List[Dict[str, str]],
        reference_citations: List[Dict[str, str]]
    ) -> float:
        """
        Measure accuracy of citations.
        
        Args:
            predicted_citations: Citations in generated answer
            reference_citations: Ground truth citations
            
        Returns:
            Citation accuracy (0-1)
        """
        if not reference_citations:
            return 1.0 if not predicted_citations else 0.0
        
        # Normalize citations to (source, page) tuples
        pred_set = {
            (c.get("source", ""), c.get("page", ""))
            for c in predicted_citations
        }
        ref_set = {
            (c.get("source", ""), c.get("page", ""))
            for c in reference_citations
        }
        
        # Calculate precision and recall
        correct = pred_set & ref_set
        
        if not pred_set:
            return 0.0
        
        precision = len(correct) / len(pred_set)
        recall = len(correct) / len(ref_set)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)


class EvaluationSuite:
    """
    Complete evaluation suite for RAG system.
    """
    
    def __init__(self):
        self.retrieval_metrics = RetrievalMetrics()
        self.generation_metrics = GenerationMetrics()
    
    def evaluate_retrieval(
        self,
        queries: List[str],
        retrieved_lists: List[List[str]],
        relevant_sets: List[Set[str]],
        k_values: List[int] = [1, 3, 5, 10]
    ) -> Dict[str, Any]:
        """
        Comprehensive retrieval evaluation.
        
        Args:
            queries: List of test queries
            retrieved_lists: Retrieved document IDs for each query
            relevant_sets: Ground truth relevant document IDs
            k_values: K values for P@K and R@K
            
        Returns:
            Dictionary of metrics
        """
        
        logger.info(f"Evaluating retrieval on {len(queries)} queries")
        
        results = {
            "num_queries": len(queries),
            "precision_at_k": {},
            "recall_at_k": {},
            "map": 0.0,  # Mean Average Precision
            "mrr": 0.0
        }
        
        # Precision@K and Recall@K
        for k in k_values:
            precisions = []
            recalls = []
            
            for retrieved, relevant in zip(retrieved_lists, relevant_sets):
                p = self.retrieval_metrics.precision_at_k(retrieved, relevant, k)
                r = self.retrieval_metrics.recall_at_k(retrieved, relevant, k)
                precisions.append(p)
                recalls.append(r)
            
            results["precision_at_k"][f"p@{k}"] = np.mean(precisions)
            results["recall_at_k"][f"r@{k}"] = np.mean(recalls)
        
        # MAP
        aps = []
        for retrieved, relevant in zip(retrieved_lists, relevant_sets):
            ap = self.retrieval_metrics.average_precision(retrieved, relevant)
            aps.append(ap)
        results["map"] = np.mean(aps)
        
        # MRR
        results["mrr"] = self.retrieval_metrics.mean_reciprocal_rank(
            retrieved_lists,
            relevant_sets
        )
        
        logger.info("Retrieval evaluation complete", extra=results)
        
        return results
    
    def compare_systems(
        self,
        queries: List[str],
        system_a_results: List[List[str]],
        system_b_results: List[List[str]],
        relevant_sets: List[Set[str]],
        system_a_name: str = "Baseline",
        system_b_name: str = "Hybrid"
    ) -> Dict[str, Any]:
        """
        Compare two retrieval systems.
        
        Args:
            queries: Test queries
            system_a_results: Results from system A
            system_b_results: Results from system B
            relevant_sets: Ground truth
            system_a_name: Name of system A
            system_b_name: Name of system B
            
        Returns:
            Comparison results
        """
        
        logger.info(f"Comparing {system_a_name} vs {system_b_name}")
        
        eval_a = self.evaluate_retrieval(queries, system_a_results, relevant_sets)
        eval_b = self.evaluate_retrieval(queries, system_b_results, relevant_sets)
        
        comparison = {
            system_a_name: eval_a,
            system_b_name: eval_b,
            "improvements": {}
        }
        
        # Calculate improvements
        for metric in ["map", "mrr"]:
            improvement = ((eval_b[metric] - eval_a[metric]) / eval_a[metric] * 100
                          if eval_a[metric] > 0 else 0)
            comparison["improvements"][metric] = f"{improvement:+.2f}%"
        
        logger.info("System comparison complete", extra=comparison)
        
        return comparison