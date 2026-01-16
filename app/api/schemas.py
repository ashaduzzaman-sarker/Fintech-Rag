"""
Pydantic schemas for API request/response models.
Provides validation, documentation, and type safety.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator


# ============================================================================
# Ingestion Schemas
# ============================================================================

class IngestRequest(BaseModel):
    """Request to ingest documents."""
    
    directory_path: str = Field(
        ...,
        description="Path to directory containing documents",
        example="./data/raw/compliance"
    )
    recursive: bool = Field(
        default=True,
        description="Search subdirectories recursively"
    )
    use_advanced_chunking: bool = Field(
        default=True,
        description="Use structure-aware chunking"
    )


class IngestResponse(BaseModel):
    """Response from document ingestion."""
    
    status: Literal["success", "error"]
    message: str
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Ingestion statistics"
    )
    processing_time: float = Field(
        description="Processing time in seconds"
    )


# ============================================================================
# Query Schemas
# ============================================================================

class QueryRequest(BaseModel):
    """Request to query the RAG system."""
    
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Question to answer",
        example="What are our Basel III capital requirements?"
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return"
    )
    include_confidence: bool = Field(
        default=True,
        description="Include confidence scoring"
    )
    filter_category: Optional[str] = Field(
        default=None,
        description="Filter by document category",
        example="compliance"
    )
    
    @validator("question")
    def validate_question(cls, v):
        """Ensure question is not empty after stripping."""
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class Citation(BaseModel):
    """Citation reference."""
    
    source: str = Field(description="Source document path/filename")
    page: str = Field(description="Page number or section")
    type: Literal["explicit", "inferred"] = Field(
        description="How citation was extracted"
    )


class ContextDocument(BaseModel):
    """Context document used for answer generation."""
    
    source: str
    page: str
    score: float = Field(description="Relevance score")


class QueryResponse(BaseModel):
    """Response from RAG query."""
    
    question: str
    answer: str
    citations: List[Citation]
    context_used: List[ContextDocument]
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    confidence_level: Optional[Literal["low", "medium", "high"]] = None
    model: str = Field(description="LLM model used")
    processing_time: float = Field(description="Processing time in seconds")


# ============================================================================
# Health & Status Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str = "1.0.0"
    components: Dict[str, str] = Field(
        description="Status of system components"
    )
    timestamp: str


class SystemStats(BaseModel):
    """System statistics."""
    
    total_documents_indexed: int
    total_queries_processed: int
    avg_query_time: float
    vector_store_stats: Dict[str, Any]
    bm25_store_stats: Dict[str, Any]
    uptime_seconds: float


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )