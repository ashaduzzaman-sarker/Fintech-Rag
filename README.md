# FinTech RAG Knowledge Assistant 🏦

**Production-ready Retrieval-Augmented Generation (RAG) assistant for financial institutions.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

______________________________________________________________________

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Local Setup](#-local-setup)
- [Quick Start](#-quick-start)
- [API Overview](#-api-overview)
- [Evaluation](#-evaluation)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Development](#-development)

______________________________________________________________________

## 🎯 Problem Statement

Financial institutions manage **1,000+ regulatory documents, policies, and reports**. Key challenges:

- ❌ **Time-consuming searches**: Analysts spend 40-60% of time finding information
- ❌ **Keyword search limitations**: Traditional search misses semantic relationships
- ❌ **Knowledge silos**: Information scattered across departments
- ❌ **Compliance risk**: Inconsistent interpretation of regulations
- ❌ **No source attribution**: Answers without citations create audit issues

**Business Impact:**

- 10+ hours/week wasted per analyst
- Delayed decision-making
- Regulatory compliance risks

______________________________________________________________________

## ✅ Solution Overview

FinTech RAG is an opinionated, end-to-end RAG system designed for **regulatory, risk, and policy documents** in financial services. It provides:

- ✅ **Semantic understanding** beyond keyword search
- ✅ **Hybrid retrieval** combining BM25 and dense embeddings
- ✅ **Reranking** using a cross-encoder for better relevance
- ✅ **Grounded answers** with explicit citations
- ✅ **Observable, testable, deployable** backend ready for real use

______________________________________________________________________

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                  (Streamlit / API Client / Slack)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ Ingestion API  │  │  Query API   │  │  Monitoring API    │ │
│  └────────────────┘  └──────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐
│  Ingestion       │ │  Retrieval   │ │  Generation     │
│  Pipeline        │ │  Engine      │ │  Engine         │
│                  │ │              │ │                 │
│ • PDF Loader     │ │ • Pinecone   │ │ • OpenAI GPT-4  │
│ • Chunker        │ │ • BM25       │ │ • Prompts       │
│ • Embedder       │ │ • Cohere     │ │ • Citations     │
└──────────────────┘ └──────────────┘ └─────────────────┘
         │                   │                  │
         ▼                   ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│                    Storage Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐│
│  │  Pinecone    │  │  BM25 Index  │  │  Document      ││
│  │  (Vector DB) │  │  (Local)     │  │  Storage       ││
│  └──────────────┘  └──────────────┘  └────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion** (Batch):

   ```
   Documents → Load → Chunk → Embed → Index (Pinecone + BM25)
   ```

1. **Query** (Real-time):

   ```
   Query → Hybrid Search → Rerank → Generate → Validate → Response
   ```

______________________________________________________________________

## 🚀 Key Features

### Core RAG Capabilities

- **📚 Document Processing**

  - PDF, DOCX, TXT, Markdown support
  - Semantic and structure-aware chunking
  - Metadata enrichment (source, page, category, tokens)

- **🔍 Hybrid Retrieval**

  - **Dense retrieval**: OpenAI embeddings stored in Pinecone
  - **Sparse retrieval**: BM25 keyword index
  - **Fusion**: Reciprocal Rank Fusion (RRF)
  - **Reranking**: Cohere cross-encoder (`rerank-english-v3.0`)

- **🤖 Answer Generation**

  - OpenAI chat models (default: `gpt-4-turbo-preview`)
  - System prompts tuned for FinTech compliance and risk
  - Structured citation extraction from generated answers
  - Optional citation validation and confidence assessment

### Operational Features

- ⚙️ **Configurable** via Pydantic settings and `.env`
- 📊 **Monitoring** with Prometheus metrics and Grafana dashboards
- 🔒 **Security primitives** for API key auth and rate limiting
- 🐳 **Docker & Kubernetes** manifests for production deployment
- ✅ **Tests**: unit, integration, and benchmark utilities
- 🧪 **Evaluation tools** for retrieval quality and RAG performance

______________________________________________________________________

docker build -t fintech-rag:latest .

## 🛠️ Tech Stack

| Component             | Technology                         | Purpose                |
| --------------------- | ---------------------------------- | ---------------------- |
| **API**               | FastAPI                            | Backend service        |
| **RAG Orchestration** | LangChain ecosystem (OpenAI, docs) | Ingestion & generation |
| **Vector DB**         | Pinecone                           | Dense retrieval        |
| **Embeddings**        | OpenAI `text-embedding-3-large`    | Semantic search        |
| **Reranking**         | Cohere `rerank-english-v3.0`       | Relevance optimization |
| **LLM**               | OpenAI `gpt-4-turbo-preview`       | Answer generation      |
| **Sparse Search**     | BM25 (in-memory index)             | Keyword matching       |
| **Config**            | Pydantic Settings                  | Typed configuration    |
| **Monitoring**        | Prometheus + Grafana               | Observability          |
| **Container**         | Docker                             | Packaging              |
| **Orchestration**     | Kubernetes                         | Deployment             |

______________________________________________________________________

## 📦 Local Setup

For a full step-by-step walkthrough, see [QUICKSTART.md](QUICKSTART.md).

### Prerequisites

- Python 3.11+
- Git
- (Optional) Docker & Docker Compose
- API keys:
  - OpenAI (`OPENAI_API_KEY`)
  - Pinecone (`PINECONE_API_KEY`)
  - Cohere (`COHERE_API_KEY`)

### One-time Setup

```bash
git clone https://github.com/ashaduzzaman-sarker/Fintech-Rag.git
cd Fintech-Rag

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initial project setup (env file, data dirs, Pinecone index)
make setup
```

Then edit `.env` with your API keys and environment-specific settings.

______________________________________________________________________

## ⚡ Quick Start

The following is the minimal happy-path to see the system working end-to-end. Details and variations are documented in [QUICKSTART.md](QUICKSTART.md) and [STARTUP_GUIDE.md](STARTUP_GUIDE.md).

### 1. Start the API server

```bash
make run
# or
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs to explore the API.

### 2. Generate sample data (optional but recommended)

```bash
python scripts/generate_test_data.py
```

### 3. Ingest documents

```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./data/raw",
    "recursive": true,
    "use_advanced_chunking": true
  }'
```

### 4. Ask a question

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are our Basel III capital requirements?",
    "top_k": 5,
    "include_confidence": true
  }'
```

The response includes the answer, citations, context used, and model metadata.

______________________________________________________________________

## 📚 API Overview

### Endpoints

| Method | Endpoint         | Description        |
| ------ | ---------------- | ------------------ |
| `POST` | `/api/v1/ingest` | Ingest documents   |
| `POST` | `/api/v1/query`  | Query RAG system   |
| `GET`  | `/api/v1/health` | Health check       |
| `GET`  | `/api/v1/stats`  | System statistics  |
| `GET`  | `/metrics`       | Prometheus metrics |

Interactive documentation is available at http://localhost:8000/docs when the server is running.

### Programmatic Usage (Python)

```python
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.vector_store import PineconeVectorStore
from app.retrieval.bm25_store import BM25Store
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import CohereReranker
from app.generation.generator import RAGGenerator
from app.ingestion.embedders import EmbeddingGenerator

# Initialize pipeline
pipeline = IngestionPipeline()
documents = pipeline.process_directory("./data/raw")

# Setup retrieval
vector_store = PineconeVectorStore()
bm25_store = BM25Store()
vector_store.upsert_documents(documents)
bm25_store.build_index(documents)

# Query
embedder = EmbeddingGenerator()
retriever = HybridRetriever(vector_store, bm25_store, embedder)
reranker = CohereReranker()
generator = RAGGenerator()

query = "What are the AML screening requirements?"
results = retriever.retrieve(query, top_k=10)
reranked = reranker.rerank(query, results, top_n=5)
answer = generator.generate_with_confidence(query, reranked)

print(answer["answer"])
```

______________________________________________________________________

## 📊 Evaluation

### Retrieval Quality

Run benchmarks comparing systems:

```python
from app.evaluation.metrics import EvaluationSuite

evaluator = EvaluationSuite()

# Compare dense-only vs hybrid
results = evaluator.compare_systems(
    queries=test_queries,
    system_a_results=dense_results,
    system_b_results=hybrid_results,
    relevant_sets=ground_truth,
    system_a_name="Dense Only",
    system_b_name="Hybrid + Rerank",
)

print(results)
```

**Typical Results:**

```
Dense Only:    MAP=0.67, MRR=0.72, P@5=0.58
Hybrid+Rerank: MAP=0.81, MRR=0.88, P@5=0.74

Improvements: +20.9% MAP, +22.2% MRR
```

### Metrics

- **Precision@K**: Relevance of top-K results
- **Recall@K**: Coverage of relevant documents
- **MAP**: Mean Average Precision
- **MRR**: Mean Reciprocal Rank
- **NDCG**: Normalized Discounted Cumulative Gain

______________________________________________________________________

## 🚢 Deployment

For detailed deployment options (Docker, Docker Compose, Kubernetes, and Streamlit UI), see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

Typical local Docker Compose flow:

```bash
make docker-build
make docker-compose-up
```

This starts the API, Prometheus, and Grafana services.

______________________________________________________________________

## 📈 Monitoring

When running via Docker Compose or your own deployment:

- Prometheus metrics: http://localhost:9091
- Grafana dashboards: http://localhost:3000 (default: `admin` / `admin`)

See [monitoring/prometheus.yml](monitoring/prometheus.yml) and the Grafana dashboards under [monitoring/grafana/dashboards](monitoring/grafana/dashboards) for configuration.

______________________________________________________________________

## 🧑‍💻 Development

Common Make targets for local development:

```bash
make dev-install     # Install dev dependencies + pre-commit
make test            # Run all tests
make lint            # Run linters
make format          # Format code
make stats           # Show basic project stats
```

For a more detailed operator-focused view of the current state of the project and commands, see [STARTUP_GUIDE.md](STARTUP_GUIDE.md).

______________________________________________________________________

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

### Scaling

Horizontal Pod Autoscaler (HPA) configured for:

- **Min replicas**: 3
- **Max replicas**: 10
- **Scale on**: CPU (70%), Memory (80%)

______________________________________________________________________

## 📈 Monitoring

Access dashboards:

- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)

### Key Metrics

- `rag_queries_total`: Total queries processed
- `rag_query_duration_seconds`: Query latency
- `rag_ingestions_total`: Documents indexed

### Alerts

Configure alerts in Prometheus for:

- High error rates (>5%)
- Slow queries (>5s p95)
- Low confidence scores (\<0.4)

______________________________________________________________________

## 🔧 Development

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# With coverage
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check app/

# Formatting
black app/

# Type checking
mypy app/ --ignore-missing-imports
```

______________________________________________________________________

## 🤝 Contributing

We welcome contributions! Please follow:

1. Fork the repository
1. Create feature branch (`git checkout -b feature/amazing-feature`)
1. Commit changes (`git commit -m 'Add amazing feature'`)
1. Push to branch (`git push origin feature/amazing-feature`)
1. Open Pull Request

### Development Workflow

- Write tests for new features
- Ensure CI passes
- Update documentation
- Follow coding standards (Black, Ruff, mypy)

______________________________________________________________________

## 📄 License

MIT License - see [LICENSE](LICENSE) file

______________________________________________________________________

## 🙏 Acknowledgments

- **LangChain**: RAG framework
- **Pinecone**: Vector database
- **OpenAI**: Embeddings & LLM
- **Cohere**: Reranking
- **FastAPI**: API framework

______________________________________________________________________

## 📞 Support

- **Issues**: https://github.com/ashaduzzaman-sarker/Fintech-Rag/issues
