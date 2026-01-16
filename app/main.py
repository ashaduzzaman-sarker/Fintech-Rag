"""
FastAPI application entry point.
Configures app, middleware, routing, and startup/shutdown events.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api import routes


# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown logic.
    """
    # Startup
    logger.info("Starting FinTech RAG API")
    logger.info(
        "Configuration loaded",
        extra={
            "environment": settings.environment,
            "model": settings.openai_model,
            "pinecone_index": settings.pinecone_index_name
        }
    )
    
    # Initialize app start time
    routes._app_start_time = time.time()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FinTech RAG API")


# Create FastAPI app
app = FastAPI(
    title="FinTech RAG Knowledge Assistant",
    description="""
    Enterprise-grade Retrieval-Augmented Generation system for FinTech.
    
    ## Features
    - **Hybrid Search**: Combines vector (semantic) and BM25 (keyword) retrieval
    - **Reranking**: Cohere cross-encoder for optimal relevance
    - **Citations**: Every answer includes source attribution
    - **Production-Ready**: Monitoring, logging, error handling
    
    ## Endpoints
    - `POST /ingest`: Ingest documents into the system
    - `POST /query`: Ask questions and get grounded answers
    - `GET /health`: Health check
    - `GET /stats`: System statistics
    - `GET /metrics`: Prometheus metrics
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================================
# Middleware
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    
    start_time = time.time()
    
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Log completion
    duration = time.time() - start_time
    logger.info(
        f"Request completed: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": f"{duration:.3f}s"
        }
    )
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.is_development else "An unexpected error occurred",
            "path": request.url.path
        }
    )


# ============================================================================
# Routes
# ============================================================================

# Include API routes
app.include_router(
    routes.router,
    prefix="/api/v1",
    tags=["RAG"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FinTech RAG Knowledge Assistant",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/v1/health",
        "environment": settings.environment
    }


# Prometheus metrics endpoint
if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        f"Starting server on {settings.api_host}:{settings.api_port}",
        extra={"environment": settings.environment}
    )
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_config=None  # Use our custom logging
    )