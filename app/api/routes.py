"""
FastAPI routes for the RAG system.
Implements /ingest, /query, /health endpoints.
"""

from pathlib import Path
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from prometheus_client import Counter, Histogram

from app.api.schemas import (
    IngestRequest, IngestResponse,
    QueryRequest, QueryResponse,
    HealthResponse, SystemStats,
    ErrorResponse
)
from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)

# Prometheus metrics
query_counter = Counter(
    "rag_queries_total",
    "Total number of queries processed"
)
query_duration = Histogram(
    "rag_query_duration_seconds",
    "Query processing duration"
)
ingestion_counter = Counter(
    "rag_ingestions_total",
    "Total number of ingestion jobs"
)

# Router
router = APIRouter()

# Global state (in production, use dependency injection)
# These will be initialized in main.py
_pipeline = None
_vector_store = None
_bm25_store = None
_hybrid_retriever = None
_reranker = None
_generator = None
_app_start_time = None


def get_dependencies():
    """
    Dependency injection for global components.
    In production, use proper DI framework.
    """
    if _pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Run /ingest first."
        )
    
    return {
        "pipeline": _pipeline,
        "vector_store": _vector_store,
        "bm25_store": _bm25_store,
        "hybrid_retriever": _hybrid_retriever,
        "reranker": _reranker,
        "generator": _generator
    }


# ============================================================================
# Ingestion Endpoint
# ============================================================================

@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest documents into RAG system",
    description="Load, chunk, embed, and index documents from a directory"
)
async def ingest_documents(
    request: IngestRequest
) -> IngestResponse:
    """
    Ingest documents from a directory.
    
    This endpoint:
    1. Loads documents (PDF, DOCX, TXT)
    2. Chunks them semantically
    3. Generates embeddings
    4. Indexes in Pinecone (vector) and BM25 (keyword)
    
    **Note:** This is a long-running operation for large datasets.
    Consider using async tasks (Celery) in production.
    """
    
    logger.info(f"Ingestion request received: {request.directory_path}")
    ingestion_counter.inc()
    
    start_time = time.time()
    
    try:
        # Validate directory
        directory = Path(request.directory_path)
        if not directory.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.directory_path}"
            )
        
        # Import dependencies here to avoid circular imports
        from app.ingestion.pipeline import IngestionPipeline
        from app.retrieval.vector_store import PineconeVectorStore
        from app.retrieval.bm25_store import BM25Store
        from app.retrieval.hybrid_retriever import HybridRetriever
        from app.retrieval.reranker import CohereReranker
        from app.generation.generator import RAGGenerator
        from app.ingestion.embedders import EmbeddingGenerator
        
        # Initialize global components
        global _pipeline, _vector_store, _bm25_store, _hybrid_retriever, _reranker, _generator
        
        # Create pipeline
        _pipeline = IngestionPipeline(
            use_advanced_chunking=request.use_advanced_chunking
        )
        
        # Process documents
        embedded_documents = _pipeline.process_directory(
            directory=directory,
            recursive=request.recursive
        )
        
        if not embedded_documents:
            return IngestResponse(
                status="error",
                message="No documents were processed",
                stats={},
                processing_time=time.time() - start_time
            )
        
        # Initialize stores
        _vector_store = PineconeVectorStore()
        _bm25_store = BM25Store()
        
        # Index documents
        logger.info("Indexing documents in Pinecone...")
        _vector_store.upsert_documents(embedded_documents)
        
        logger.info("Building BM25 index...")
        _bm25_store.build_index(embedded_documents)
        _bm25_store.save_index()
        
        # Initialize retrieval components
        embedder = EmbeddingGenerator()
        _hybrid_retriever = HybridRetriever(
            vector_store=_vector_store,
            bm25_store=_bm25_store,
            embedder=embedder
        )
        
        _reranker = CohereReranker()
        _generator = RAGGenerator()
        
        # Gather stats
        stats = _pipeline.get_stats()
        processing_time = time.time() - start_time
        
        logger.info(
            "Ingestion complete",
            extra={**stats, "processing_time": processing_time}
        )
        
        return IngestResponse(
            status="success",
            message=f"Successfully indexed {stats['total_chunks']} chunks from {stats['total_files']} documents",
            stats=stats,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


# ============================================================================
# Query Endpoint
# ============================================================================

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the RAG system",
    description="Ask questions and get grounded answers with citations"
)
async def query_rag(
    request: QueryRequest,
    deps: dict = Depends(get_dependencies)
) -> QueryResponse:
    """
    Query the RAG system.
    
    This endpoint:
    1. Performs hybrid retrieval (vector + BM25)
    2. Reranks results with Cohere
    3. Generates answer with LLM
    4. Extracts citations
    5. Optionally calculates confidence
    """
    
    logger.info(f"Query received: '{request.question[:50]}...'")
    query_counter.inc()
    
    start_time = time.time()
    
    try:
        hybrid_retriever = deps["hybrid_retriever"]
        reranker = deps["reranker"]
        generator = deps["generator"]
        
        # 1. Hybrid retrieval
        logger.debug("Performing hybrid retrieval...")
        retrieval_results = hybrid_retriever.retrieve(
            query=request.question,
            top_k=request.top_k * 2,  # Retrieve more for reranking
            filter_metadata={"category": request.filter_category} if request.filter_category else None
        )
        
        if not retrieval_results:
            return QueryResponse(
                question=request.question,
                answer="I couldn't find any relevant documents to answer your question. Please try rephrasing or check if documents have been ingested.",
                citations=[],
                context_used=[],
                model=settings.openai_model,
                processing_time=time.time() - start_time
            )
        
        # 2. Rerank
        logger.debug("Reranking results...")
        reranked_results = reranker.rerank(
            query=request.question,
            documents=retrieval_results,
            top_n=request.top_k
        )
        
        # 3. Generate answer
        logger.debug("Generating answer...")
        if request.include_confidence:
            result = generator.generate_with_confidence(
                question=request.question,
                context_documents=reranked_results
            )
        else:
            result = generator.generate(
                question=request.question,
                context_documents=reranked_results
            )
        
        # 4. Build response
        processing_time = time.time() - start_time
        query_duration.observe(processing_time)
        
        response = QueryResponse(
            question=request.question,
            answer=result["answer"],
            citations=result["citations"],
            context_used=result["context_used"],
            confidence=result.get("confidence"),
            confidence_level=result.get("confidence_level"),
            model=result["model"],
            processing_time=processing_time
        )
        
        logger.info(
            f"Query processed successfully in {processing_time:.2f}s",
            extra={
                "confidence": result.get("confidence"),
                "num_citations": len(result["citations"])
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check system health and component status"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
    - healthy: All components operational
    - degraded: Some components have issues
    - unhealthy: Critical components failing
    """
    
    components = {}
    
    # Check components
    try:
        if _vector_store:
            stats = _vector_store.get_index_stats()
            components["vector_store"] = "healthy" if stats else "unhealthy"
        else:
            components["vector_store"] = "not_initialized"
        
        if _bm25_store:
            components["bm25_store"] = "healthy" if _bm25_store.bm25 else "unhealthy"
        else:
            components["bm25_store"] = "not_initialized"
        
        if _generator:
            components["generator"] = "healthy"
        else:
            components["generator"] = "not_initialized"
        
        # Determine overall status
        if all(v == "healthy" for v in components.values()):
            status_val = "healthy"
        elif any(v == "unhealthy" for v in components.values()):
            status_val = "unhealthy"
        else:
            status_val = "degraded"
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        status_val = "unhealthy"
        components["error"] = str(e)
    
    return HealthResponse(
        status=status_val,
        components=components,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get(
    "/stats",
    response_model=SystemStats,
    status_code=status.HTTP_200_OK,
    summary="System statistics",
    description="Get detailed system statistics"
)
async def get_stats() -> SystemStats:
    """Get system statistics."""
    
    global _app_start_time
    if _app_start_time is None:
        _app_start_time = time.time()
    
    try:
        return SystemStats(
            total_documents_indexed=_vector_store.stats.get("total_upserted", 0) if _vector_store else 0,
            total_queries_processed=int(query_counter._value.get()) if hasattr(query_counter, '_value') else 0,
            avg_query_time=_generator.stats.get("avg_response_length", 0) if _generator else 0,
            vector_store_stats=_vector_store.get_stats() if _vector_store else {},
            bm25_store_stats=_bm25_store.get_stats() if _bm25_store else {},
            uptime_seconds=time.time() - _app_start_time
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )