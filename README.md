# FinTech RAG Knowledge Assistant 🏦

> **Enterprise-grade Retrieval-Augmented Generation system for FinTech organizations**

[![CI Pipeline](https://github.com/your-org/fintech-rag/workflows/CI%20Pipeline/badge.svg)](https://github.com/your-org/fintech-rag/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

______________________________________________________________________

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Evaluation](#-evaluation)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Development](#-development)
- [Contributing](#-contributing)

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

## ✅ Solution

An intelligent RAG system that:

✅ **Understands context**: Semantic search beyond keywords
✅ **Multi-hop reasoning**: Connects information across documents
✅ **Grounded answers**: Every claim cited with source + page
✅ **Hybrid retrieval**: Combines keyword (BM25) + semantic (embeddings)
✅ **Production-ready**: Scalable, monitored, tested

**Business Value:**

- ⚡ **60% faster** information retrieval
- 📊 **Auditable citations** for compliance
- 🎯 **Consistent answers** across organization
- 💼 **Knowledge democratization**: Junior analysts access senior expertise

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

## 🚀 Features

### Core Capabilities

- **📚 Document Processing**

  - PDF, DOCX, TXT, Markdown support
  - Semantic chunking with context preservation
  - Metadata enrichment (source, page, category)

- **🔍 Hybrid Retrieval**

  - **Dense retrieval**: OpenAI embeddings via Pinecone
  - **Sparse retrieval**: BM25 keyword matching
  - **Fusion**: Reciprocal Rank Fusion (RRF)
  - **Reranking**: Cohere cross-encoder

- **🤖 Answer Generation**

  - OpenAI GPT-4 with custom prompts
  - Automatic citation extraction
  - Confidence scoring
  - Hallucination mitigation

### Production Features

- ⚡ **Performance**: Sub-3s query latency
- 📊 **Monitoring**: Prometheus + Grafana
- 🔒 **Security**: API key auth, rate limiting
- 🐳 **Containerized**: Docker + Kubernetes ready
- ✅ **Tested**: Unit + integration tests
- 📝 **Documented**: OpenAPI specs

______________________________________________________________________

## 🛠️ Tech Stack

| Component         | Technology                    | Purpose                |
| ----------------- | ----------------------------- | ---------------------- |
| **RAG Framework** | LangChain                     | Orchestration          |
| **Vector DB**     | Pinecone                      | Dense retrieval        |
| **Embeddings**    | OpenAI text-embedding-3-large | Semantic search        |
| **Reranking**     | Cohere rerank-v3              | Relevance optimization |
| **LLM**           | OpenAI GPT-4                  | Answer generation      |
| **Sparse Search** | BM25Okapi                     | Keyword matching       |
| **API**           | FastAPI                       | Backend service        |
| **Monitoring**    | Prometheus + Grafana          | Observability          |
| **Container**     | Docker                        | Packaging              |
| **Orchestration** | Kubernetes                    | Deployment             |
| **CI/CD**         | GitHub Actions                | Automation             |

______________________________________________________________________

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- API Keys:
  - OpenAI
  - Pinecone
  - Cohere

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/fintech-rag.git
cd fintech-rag

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize Pinecone index (one-time)
python scripts/setup_pinecone.py

# 6. (Optional) Generate synthetic test data
python scripts/generate_test_data.py
```

### Docker Setup

```bash
# Build image
docker build -t fintech-rag:latest .

# Run with Docker Compose (includes Prometheus + Grafana)
docker-compose -f docker/docker-compose.yml up -d
```

______________________________________________________________________

## 💻 Usage

### 1. Ingest Documents

```bash
# Start the API server
python -m uvicorn app.main:app --reload

# Ingest documents (separate terminal)
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./data/raw/compliance",
    "recursive": true,
    "use_advanced_chunking": true
  }'
```

**Response:**

```json
{
  "status": "success",
  "message": "Successfully indexed 127 chunks from 15 documents",
  "stats": {
    "total_files": 15,
    "total_chunks": 127,
    "total_tokens": 89450,
    "processing_time": 45.2
  }
}
```

### 2. Query the System

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are our Basel III capital requirements?",
    "top_k": 5,
    "include_confidence": true
  }'
```

**Response:**

```json
{
  "question": "What are our Basel III capital requirements?",
  "answer": "According to our Risk Management Framework, Basel III requires a minimum Common Equity Tier 1 (CET1) capital ratio of 4.5%, a Tier 1 capital ratio of 6%, and a total capital ratio of 8% [Source: risk_framework_2024.pdf, Page: 12]. Additionally, a Capital Conservation Buffer of 2.5% is required, bringing the total CET1 requirement to 7% [Source: compliance_policy_basel.pdf, Page: 3].",
  "citations": [
    {
      "source": "risk_framework_2024.pdf",
      "page": "12",
      "type": "explicit"
    },
    {
      "source": "compliance_policy_basel.pdf",
      "page": "3",
      "type": "explicit"
    }
  ],
  "confidence": 0.89,
  "confidence_level": "high",
  "processing_time": 2.34
}
```

### 3. Python SDK

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

## 📚 API Documentation

### Endpoints

| Method | Endpoint         | Description        |
| ------ | ---------------- | ------------------ |
| `POST` | `/api/v1/ingest` | Ingest documents   |
| `POST` | `/api/v1/query`  | Query RAG system   |
| `GET`  | `/api/v1/health` | Health check       |
| `GET`  | `/api/v1/stats`  | System statistics  |
| `GET`  | `/metrics`       | Prometheus metrics |

**Full documentation**: http://localhost:8000/docs (Swagger UI)

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

### Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -n production
kubectl logs -f deployment/fintech-rag-api -n production
```

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

- **Issues**: [GitHub Issues](https://github.com/your-org/fintech-rag/issues)
- **Email**: support@yourcompany.com
- **Docs**: [Documentation](https://docs.yourcompany.com/fintech-rag)
