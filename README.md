# Fintech-Rag
Enterprise Retrieval-Augmented Generation (RAG) System - FinTech Knowledge Assistant

## Project Structure
fintech-rag/
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/                          # FastAPI application layer
│   │   ├── __init__.py
│   │   ├── routes.py                 # API endpoints (/ingest, /query, /health)
│   │   ├── schemas.py                # Pydantic request/response models
│   │   ├── dependencies.py           # Dependency injection (DB, services)
│   │   └── middleware.py             # Logging, auth, rate limiting
│   │
│   ├── core/                         # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings (Pydantic BaseSettings)
│   │   ├── logging.py                # Structured logging setup
│   │   ├── exceptions.py             # Custom exception classes
│   │   └── security.py               # API key validation, RBAC
│   │
│   ├── ingestion/                    # Document processing pipeline
│   │   ├── __init__.py
│   │   ├── loaders.py                # PDF/DOCX/TXT parsers
│   │   ├── chunkers.py               # Semantic chunking strategies
│   │   ├── embedders.py              # Embedding generation (OpenAI, local)
│   │   ├── metadata.py               # Metadata extraction & enrichment
│   │   └── pipeline.py               # Orchestration (ingest coordinator)
│   │
│   ├── retrieval/                    # Hybrid search engine
│   │   ├── __init__.py
│   │   ├── vector_store.py           # Pinecone client wrapper
│   │   ├── bm25_store.py             # BM25 index manager
│   │   ├── hybrid_retriever.py       # Fusion logic (RRF)
│   │   ├── reranker.py               # Cohere cross-encoder
│   │   └── query_processor.py        # Query analysis & routing
│   │
│   ├── generation/                   # LLM answer generation
│   │   ├── __init__.py
│   │   ├── generator.py              # RAG prompt engineering
│   │   ├── citation_builder.py       # Source tracking & formatting
│   │   └── validator.py              # Hallucination detection
│   │
│   ├── evaluation/                   # Metrics & benchmarking
│   │   ├── __init__.py
│   │   ├── metrics.py                # Precision@K, Recall@K, MRR
│   │   ├── benchmark.py              # Test suite runner
│   │   └── datasets.py               # Ground truth Q&A pairs
│   │
│   ├── agents/                       # Optional agentic workflows
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # LangGraph state machine
│   │   └── tools.py                  # Custom tool definitions
│   │
│   └── main.py                       # FastAPI app factory
│
├── data/                             # Local data storage (gitignored)
│   ├── raw/                          # Original documents
│   ├── processed/                    # Chunked + embedded
│   └── indexes/                      # BM25 index files
│
├── tests/                            # Comprehensive test suite
│   ├── unit/
│   │   ├── test_chunkers.py
│   │   ├── test_retrieval.py
│   │   └── test_generation.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   └── fixtures/
│       └── sample_docs.py
│
├── docker/                           # Container definitions
│   ├── Dockerfile                    # Multi-stage production build
│   ├── Dockerfile.dev                # Development with hot reload
│   └── docker-compose.yml            # Local stack (API + Prometheus)
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint, test, build
│       └── deploy.yml                # CD to K8s
│
├── k8s/                              # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
│
├── monitoring/                       # Observability configs
│   ├── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
├── scripts/                          # Utility scripts
│   ├── setup_pinecone.py             # Index initialization
│   ├── generate_test_data.py        # Synthetic FinTech docs
│   └── benchmark.py                  # Run evaluation suite
│
├── notebooks/                        # Analysis & experiments
│   └── retrieval_analysis.ipynb
│
├── .env.example                      # Template for secrets
├── .gitignore
├── .pre-commit-config.yaml           # Code quality hooks
├── pyproject.toml                    # Black, isort, mypy config
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Dev tools (pytest, ruff)
├── Makefile                          # Common commands
└── README.md                         # Comprehensive documentation
