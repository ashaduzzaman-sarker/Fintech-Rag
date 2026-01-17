# ⚡ Quick Start Guide

Get the FinTech RAG system running in **5 minutes**.

______________________________________________________________________

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] API keys ready:
  - [ ] OpenAI API key ([get one here](https://platform.openai.com/api-keys))
  - [ ] Pinecone API key ([get one here](https://www.pinecone.io/))
  - [ ] Cohere API key ([get one here](https://cohere.com/))

______________________________________________________________________

## Step 1: Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/ashaduzzaman-sarker/Fintech-Rag.git
cd Fintech-Rag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
make setup
# This creates .env, directories, and initializes Pinecone
```

**Edit `.env` file** with your API keys:

```bash
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-pinecone-key
COHERE_API_KEY=your-cohere-key
```

______________________________________________________________________

## Step 2: Generate Test Data (1 minute)

```bash
# Generate synthetic FinTech documents
python scripts/generate_test_data.py

# This creates ~15 documents in data/raw/
# Topics: AML, Basel III, KYC, Risk Management, Products
```

**Output:**

```
✓ Generated: data/raw/compliance/aml_policy.txt
✓ Generated: data/raw/compliance/basel_iii_capital_requirements.txt
✓ Generated: data/raw/risk/market_risk_framework.txt
...
✓ Successfully generated 15 documents
```

______________________________________________________________________

## Step 3: Start the API (30 seconds)

```bash
# Option A: Using Makefile
make run

# Option B: Direct command
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's running:**

```bash
curl http://localhost:8000/api/v1/health
```

**Expected response:**

```json
{
  "status": "degraded",
  "components": {
    "vector_store": "not_initialized",
    "bm25_store": "not_initialized",
    "generator": "not_initialized"
  }
}
```

*(Status will be "healthy" after ingestion)*

______________________________________________________________________

## Step 4: Ingest Documents (1-2 minutes)

### Option A: Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./data/raw",
    "recursive": true,
    "use_advanced_chunking": true
  }'
```

### Option B: Using Makefile

```bash
make ingest-sample
```

### Option C: Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/ingest",
    json={
        "directory_path": "./data/raw",
        "recursive": True,
        "use_advanced_chunking": True,
    },
)

print(response.json())
```

**Expected output:**

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

______________________________________________________________________

## Step 5: Ask Your First Question! 🎉

### Sample Queries

#### Query 1: AML Policy

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the AML transaction monitoring thresholds?",
    "top_k": 5,
    "include_confidence": true
  }'
```

#### Query 2: Basel III Requirements

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the minimum Common Equity Tier 1 capital ratio under Basel III?",
    "top_k": 5
  }'
```

#### Query 3: KYC Procedures

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What documents are required for customer identification?",
    "top_k": 3
  }'
```

______________________________________________________________________

## Understanding the Response

```json
{
  "question": "What are the AML transaction monitoring thresholds?",
  "answer": "According to the Anti-Money Laundering Policy, automated systems monitor for suspicious patterns including unusual transaction volumes exceeding $10,000 daily [Source: aml_policy.txt, Page: 1]. The policy requires filing a Suspicious Activity Report (SAR) within 30 days of detection [Source: aml_policy.txt, Page: 1].",

  "citations": [
    {
      "source": "aml_policy.txt",
      "page": "1",
      "type": "explicit"
    }
  ],

  "context_used": [
    {
      "source": "./data/raw/compliance/aml_policy.txt",
      "page": "N/A",
      "score": 0.92
    }
  ],

  "confidence": 0.89,
  "confidence_level": "high",
  "model": "gpt-4-turbo-preview",
  "processing_time": 2.34
}
```

**Key Fields:**

- `answer`: Generated response with inline citations
- `citations`: Source documents referenced
- `confidence`: How confident the system is (0-1)
- `processing_time`: End-to-end latency

______________________________________________________________________

## Next Steps

### 1. Explore the API Documentation

```bash
# Open in browser
open http://localhost:8000/docs
```

Interactive Swagger UI with:

- Full API reference
- Try-it-out functionality
- Request/response schemas

### 2. Try More Complex Queries

```bash
# Multi-hop reasoning
"Compare AML requirements with KYC procedures"

# Numerical queries
"What is our maximum Value at Risk limit?"

# Comparative queries
"What are the differences between standard and enhanced CDD?"

# Specific details
"List all the sanctions screening lists we use"
```

### 3. Check System Stats

```bash
curl http://localhost:8000/api/v1/stats
```

### 4. View Metrics (if running with Docker Compose)

```bash
# Start with monitoring stack
docker-compose -f docker/docker-compose.yml up -d

# Access dashboards
open http://localhost:9091  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)
```

______________________________________________________________________

## Troubleshooting

### Issue: "Index not found" error

**Solution:** Ensure Pinecone index is created

```bash
python scripts/setup_pinecone.py
```

### Issue: "API key not found"

**Solution:** Check `.env` file has all keys

```bash
cat .env | grep API_KEY
```

### Issue: Slow ingestion

**Reasons:**

- Large documents take time to embed
- OpenAI API rate limits
- Network latency

**Solutions:**

- Use smaller test dataset initially
- Check OpenAI usage limits
- Enable caching (development only)

### Issue: Low confidence scores

**Reasons:**

- Question not related to documents
- Poor document quality
- Ambiguous phrasing

**Solutions:**

- Verify documents are ingested
- Rephrase question more specifically
- Check document content matches query domain

______________________________________________________________________

## Quick Command Reference

```bash
# Development
make run                 # Start dev server
make test                # Run tests
make lint                # Check code quality

# Data
make generate-data       # Create test documents
make ingest-sample       # Ingest to system

# Docker
make docker-build        # Build image
make docker-compose-up   # Start all services

# Monitoring
make metrics             # Open Prometheus
make grafana             # Open Grafana
make logs                # View logs

# Cleanup
make clean               # Clean cache
make clean-data          # Clean processed data
```

______________________________________________________________________

## What You've Built

✅ **Production RAG System** with:

- Hybrid search (vector + BM25)
- Cohere reranking
- OpenAI GPT-4 generation
- Citation tracking
- Confidence scoring

✅ **API** with:

- FastAPI backend
- Pydantic validation
- OpenAPI docs
- Health checks

✅ **Infrastructure** ready for:

- Docker deployment
- Kubernetes scaling
- Prometheus monitoring
- CI/CD automation

______________________________________________________________________

## Learn More

- 📖 Project overview: README.md
- 🚀 Startup & operations: STARTUP_GUIDE.md
- ⚡ Quick reference (this guide): QUICKSTART.md
- 📦 Deployment options: DEPLOYMENT_GUIDE.md
- ✅ Verification summary: VERIFICATION_REPORT.md

______________________________________________________________________

## Support

- **Issues**: https://github.com/ashaduzzaman-sarker/Fintech-Rag/issues
