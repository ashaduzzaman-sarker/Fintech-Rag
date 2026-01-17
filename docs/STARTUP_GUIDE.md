# 🚀 FinTech RAG - Quick Start Guide

## ✅ Project Status: OPERATIONAL

Your FinTech RAG Knowledge Assistant is ready to use! All components have been verified and configured.

______________________________________________________________________

## 🎯 Quick Start

### 1. Start the API Server

**Option A: Using Make**

```bash
cd /workspaces/Fintech-Rag
make run
```

**Option B: Direct Python**

```bash
cd /workspaces/Fintech-Rag
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

### 2. Access the API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Test Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected Response:

```json
{
    "status": "degraded",
    "version": "1.0.0",
    "components": {
        "vector_store": "not_initialized",
        "bm25_store": "not_initialized",
        "generator": "not_initialized"
    },
    "timestamp": "2026-01-17T12:15:20.754286"
}
```

______________________________________________________________________

## 📝 Available Commands

```bash
# Installation
make install              # Install production dependencies
make dev-install         # Install development dependencies + pre-commit

# Running
make run                 # Run dev server with reload
make run-prod           # Run production server
make shell              # Start Python shell with app context

# Testing
make test               # Run all tests
make test-unit          # Run unit tests only
make test-integration   # Run integration tests only
make test-cov          # Run tests with coverage report
make test-watch        # Run tests in watch mode

# Code Quality
make lint              # Run all linters
make format            # Format code with black/isort
make type-check        # Run mypy type checking
make security          # Run security checks

# Docker
make docker-build      # Build Docker image
make docker-run        # Run Docker container
make docker-compose-up # Start with Docker Compose
make docker-compose-down # Stop Docker Compose

# Data
make generate-data     # Generate synthetic test data
make ingest-sample     # Ingest sample documents
make clean-data        # Clean processed data
make clean-all         # Clean everything

# Utilities
make help              # Show all available commands
make stats             # Show project statistics
```

______________________________________________________________________

## 🔧 Configuration

All configuration is in `.env`. Key variables:

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# API Keys (already configured)
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk_...
COHERE_API_KEY=...

# Retrieval Settings
RETRIEVAL_TOP_K_VECTOR=20
RETRIEVAL_TOP_K_BM25=20
CHUNK_SIZE=800
CHUNK_OVERLAP=200

# Data Paths
DATA_DIR=./data
RAW_DATA_DIR=./data/raw
PROCESSED_DATA_DIR=./data/processed
INDEX_DIR=./data/indexes
```

______________________________________________________________________

## 📂 Project Structure

```
FinTech-Rag/
├── app/                          # Application code
│   ├── main.py                   # FastAPI entry point
│   ├── api/                      # API module
│   │   ├── routes.py             # Endpoint definitions
│   │   ├── schemas.py            # Request/response models
│   │   └── dependencies.py       # Dependency injection
│   ├── ingestion/                # Document processing
│   │   ├── pipeline.py           # Ingestion orchestration
│   │   ├── loaders.py            # Document loaders
│   │   ├── chunkers.py           # Text chunking
│   │   └── embedders.py          # Embedding generation
│   ├── retrieval/                # Hybrid search
│   │   ├── hybrid_retriever.py   # Hybrid search engine
│   │   ├── vector_store.py       # Vector DB integration
│   │   ├── bm25_store.py         # BM25 keyword search
│   │   └── reranker.py           # Result reranking
│   ├── generation/               # RAG generation
│   │   ├── generator.py          # Answer generation
│   │   ├── citation_builder.py   # Citation extraction
│   │   └── validator.py          # Response validation
│   ├── agents/                   # Agent orchestration
│   │   └── orchestrator.py       # Multi-agent coordination
│   ├── core/                     # Core utilities
│   │   ├── config.py             # Configuration management
│   │   ├── logging.py            # Logging setup
│   │   ├── security.py           # Security utilities
│   │   └── exceptions.py         # Custom exceptions
│   └── evaluation/               # Evaluation tools
│       ├── benchmark.py          # Performance benchmarking
│       ├── metrics.py            # Evaluation metrics
│       └── datasets.py           # Test datasets
├── data/                         # Data storage
│   ├── raw/                      # Raw documents
│   ├── processed/                # Processed documents
│   └── indexes/                  # Vector indexes
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test fixtures
├── docker/                       # Docker configuration
├── k8s/                          # Kubernetes manifests
├── scripts/                      # Utility scripts
├── notebooks/                    # Jupyter notebooks
├── Makefile                      # Build automation
├── pyproject.toml                # Project metadata
├── requirements.txt              # Dependencies
└── .env                          # Configuration
```

______________________________________________________________________

## 🧪 Testing

### Run Unit Tests

```bash
make test-unit
```

### Run Integration Tests

```bash
make test-integration
```

### Run All Tests with Coverage

```bash
make test-cov
```

Open `htmlcov/index.html` to view coverage report.

______________________________________________________________________

## 🐳 Docker Deployment

### Build Image

```bash
make docker-build
```

### Run Container

```bash
make docker-run
```

### Docker Compose (with all services)

```bash
make docker-compose-up
```

Services include:

- FastAPI application
- Prometheus monitoring
- Grafana dashboards

______________________________________________________________________

## 📊 Monitoring

### Prometheus Metrics

```bash
# View metrics
make metrics
# URL: http://localhost:9091
```

### Grafana Dashboards

```bash
# View dashboards
make grafana
# URL: http://localhost:3000
# Default credentials: admin / admin
```

### Application Logs

```bash
make logs
```

______________________________________________________________________

## 🔍 API Endpoints

### Health Check

```bash
GET /api/v1/health
```

### Ingest Documents

```bash
POST /api/v1/ingest
Content-Type: application/json

{
    "directory_path": "./data/raw",
    "recursive": true,
    "use_advanced_chunking": true
}
```

### Query RAG System

```bash
POST /api/v1/query
Content-Type: application/json

{
    "query": "What are the main AML regulations?",
    "retrieval_type": "hybrid",
    "top_k": 5
}
```

### System Statistics

```bash
GET /api/v1/stats
```

______________________________________________________________________

## ✨ Features

- ✅ **Hybrid Search**: Semantic (vector) + keyword (BM25) retrieval
- ✅ **Reranking**: Cohere cross-encoder for optimal relevance
- ✅ **Citations**: Every answer includes source attribution
- ✅ **Multi-format**: PDF, DOCX, TXT document support
- ✅ **Semantic Chunking**: Context-aware text splitting
- ✅ **Production-Ready**: Error handling, logging, monitoring
- ✅ **API Documentation**: Swagger UI + ReDoc
- ✅ **Docker Support**: Container-ready deployment
- ✅ **Kubernetes Ready**: K8s manifests included
- ✅ **Monitoring**: Prometheus + Grafana integration

______________________________________________________________________

## 🔧 Troubleshooting

### Port 8000 Already in Use

```bash
# Kill existing process
pkill -f uvicorn

# Or use different port
python -m uvicorn app.main:app --port 8001
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

### API Keys Not Working

```bash
# Check .env file is loaded
source .env
echo $OPENAI_API_KEY

# Restart server after .env changes
pkill -f uvicorn
make run
```

### Module Not Found

```bash
# Install missing module
pip install <module_name>

# Update requirements.txt
pip freeze > requirements.txt
```

______________________________________________________________________

## 📚 Documentation

- `README.md` - Project overview
- `QUICKSTART.md` - Quick start guide
- `VERIFICATION_REPORT.md` - Verification results
- API Docs: http://localhost:8000/docs

______________________________________________________________________

## 🚨 Important Notes

### For Development

- Use `ENVIRONMENT=development` in `.env`
- API keys are already configured
- CORS is set to allow all origins (change for production)
- Debug mode is enabled

### For Production

- Change `ENVIRONMENT=production` in `.env`
- Use secure secret management (not .env)
- Configure proper CORS settings
- Set up SSL/TLS certificates
- Enable authentication/authorization
- Configure rate limiting
- Use persistent volumes for indexes
- Set up proper monitoring/alerting

______________________________________________________________________

## ✅ What's Been Verified

- ✅ Python 3.12.12 environment
- ✅ All dependencies installed
- ✅ Fixed deprecated imports
- ✅ API server starts successfully
- ✅ All endpoints accessible
- ✅ Configuration properly set
- ✅ Data directories created
- ✅ API documentation available
- ✅ Core modules importable
- ✅ Health check endpoint working

______________________________________________________________________

## 🎯 Next Steps

1. **Upload documents**: Add files to `data/raw/`
1. **Ingest**: Run `curl -X POST http://localhost:8000/api/v1/ingest ...`
1. **Query**: Ask questions via `/api/v1/query`
1. **Monitor**: Check `/api/v1/stats` and `/metrics`

______________________________________________________________________

**Status**: ✅ READY TO USE
**Last Verified**: January 17, 2026
**Version**: 1.0.0
