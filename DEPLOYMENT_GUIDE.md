# 🚀 Deployment Guide - FinTech RAG

Complete guide for deploying the FinTech RAG Knowledge Assistant using Docker, Docker Compose, Kubernetes, or Streamlit UI.

______________________________________________________________________

## 📋 Table of Contents

1. [Docker Deployment](#docker-deployment)
1. [Docker Compose Deployment](#docker-compose-deployment)
1. [Kubernetes Deployment](#kubernetes-deployment)
1. [Streamlit UI](#streamlit-ui)
1. [CI/CD Pipeline](#cicd-pipeline)
1. [Monitoring & Logging](#monitoring--logging)

______________________________________________________________________

## 🐳 Docker Deployment

### Build the Image

```bash
# Production image
docker build -t fintech-rag:latest -f docker/Dockerfile .

# Development image with additional tools
docker build -t fintech-rag:dev -f docker/Dockerfile.dev .
```

### Run the Container

```bash
# Run with environment variables
docker run -d \
  --name fintech-rag-api \
  -p 8000:8000 \
  -p 9090:9090 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  fintech-rag:latest

# View logs
docker logs -f fintech-rag-api

# Stop container
docker stop fintech-rag-api
docker rm fintech-rag-api
```

### Docker Commands

```bash
# List images
docker images | grep fintech-rag

# Inspect container
docker inspect fintech-rag-api

# Execute command in container
docker exec fintech-rag-api curl http://localhost:8000/health

# Push to registry
docker tag fintech-rag:latest your-registry/fintech-rag:latest
docker push your-registry/fintech-rag:latest
```

______________________________________________________________________

## 🐳 Docker Compose Deployment

### Start All Services

```bash
# Start in foreground (for debugging)
docker-compose -f docker/docker-compose.yml up

# Start in background
docker-compose -f docker/docker-compose.yml up -d

# Rebuild images
docker-compose -f docker/docker-compose.yml up -d --build
```

### Service Details

**Services Running:**

- **API** (FastAPI): http://localhost:8000
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000

### Access Services

```bash
# API Health
curl http://localhost:8000/api/v1/health

# API Documentation
curl http://localhost:8000/docs

# Prometheus Metrics
curl http://localhost:9091

# Grafana Dashboards
# Open: http://localhost:3000
# Default credentials: admin/admin
```

### Manage Services

```bash
# View logs
docker-compose -f docker/docker-compose.yml logs -f api

# Stop specific service
docker-compose -f docker/docker-compose.yml stop api

# Restart all services
docker-compose -f docker/docker-compose.yml restart

# Remove everything
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml down -v  # Remove volumes too
```

______________________________________________________________________

## ☸️ Kubernetes Deployment

### Prerequisites

```bash
# Check cluster access
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace production
```

### Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n production
kubectl get services -n production
kubectl get ingress -n production

# Watch deployment
kubectl rollout status deployment/fintech-rag-api -n production
```

### K8s Configuration Files

| File              | Purpose                                      |
| ----------------- | -------------------------------------------- |
| `deployment.yaml` | API deployment (3 replicas, rolling updates) |
| `service.yaml`    | Services for API, Prometheus, Grafana        |
| `ingress.yaml`    | Ingress rules + HPA auto-scaling             |
| `configmap.yaml`  | Configuration + Secrets                      |

### Access Services

```bash
# Port forward to local machine
kubectl port-forward -n production svc/fintech-rag-api 8000:80

# Access via Ingress (requires DNS setup)
curl http://fintech-rag.example.com/api/v1/health

# View pod logs
kubectl logs -n production deployment/fintech-rag-api
kubectl logs -n production deployment/fintech-rag-api -f  # Follow logs

# Execute command in pod
kubectl exec -n production -it deployment/fintech-rag-api -- bash
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment fintech-rag-api --replicas=5 -n production

# Auto-scaling (configured in ingress.yaml)
# Min: 2 replicas
# Max: 10 replicas
# Triggers: 70% CPU, 80% memory
```

### Update Deployment

```bash
# Update image
kubectl set image deployment/fintech-rag-api \
  api=fintech-rag:v2.0 \
  -n production

# Rollback if needed
kubectl rollout undo deployment/fintech-rag-api -n production

# Check rollout history
kubectl rollout history deployment/fintech-rag-api -n production
```

### Delete Resources

```bash
# Delete all resources
kubectl delete -f k8s/

# Delete namespace (removes everything in it)
kubectl delete namespace production
```

### Troubleshooting

```bash
# Check pod status
kubectl describe pod <pod-name> -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n production
kubectl top nodes

# Get pod shell access
kubectl exec -it <pod-name> -n production -- sh
```

______________________________________________________________________

## 🎨 Streamlit UI

### Installation

```bash
# Install dependencies
pip install streamlit requests

# Or use requirements
pip install -r requirements.txt
```

### Running Streamlit UI

```bash
# Default (localhost:8501)
streamlit run ui/streamlit_app.py

# Custom host and port
streamlit run ui/streamlit_app.py --server.port 8080 --server.address 0.0.0.0

# Configuration file
streamlit run ui/streamlit_app.py --config streamlit_config.toml
```

### UI Features

- 🔍 **Query Interface** - Ask questions, get answers with citations
- 📊 **Document Ingestion** - Upload and process documents
- 📈 **Statistics Dashboard** - Monitor system metrics
- 🏥 **Health Status** - Check component health

### Configuration

Create `~/.streamlit/config.toml`:

```toml
[client]
toolbarMode = "viewer"

[server]
port = 8501
enableXsrfProtection = true
maxUploadSize = 200

[logger]
level = "info"

[theme]
primaryColor = "#1f77b4"
```

### Docker Deployment (Streamlit)

```bash
# Create Dockerfile.streamlit
cat > docker/Dockerfile.streamlit << 'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY ui/ ./ui/
COPY .env.example .env

EXPOSE 8501

CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
EOF

# Build and run
docker build -t fintech-rag-ui:latest -f docker/Dockerfile.streamlit .
docker run -p 8501:8501 --env-file .env fintech-rag-ui:latest
```

______________________________________________________________________

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The project includes a complete CI/CD pipeline (`.github/workflows/ci.yml`) that:

1. **Linting** - Code quality checks
1. **Security** - Bandit security scanning
1. **Testing** - Unit and integration tests
1. **Building** - Docker image build
1. **Status Check** - Pipeline verification

### Pipeline Stages

```
Push/PR
  ↓
[Lint] [Security] [Tests] (parallel)
  ↓
[Build Docker Image]
  ↓
[Integration Tests]
  ↓
[Status Check]
```

### Manual Trigger

```bash
# Trigger via GitHub CLI
gh workflow run ci.yml --ref main

# View workflow run
gh run list
gh run view <run-id>
```

### Local Testing

```bash
# Test locally with act
# Install: brew install act

act -j lint
act -j test
act -j build
```

______________________________________________________________________

## 📊 Monitoring & Logging

### Prometheus Metrics

**Endpoint**: `/metrics` (port 9090)

**Key Metrics:**

- `rag_queries_total` - Total queries processed
- `rag_query_duration_seconds` - Query latency
- `rag_ingestions_total` - Total ingestions

### Grafana Dashboards

**Access**: http://localhost:3000

**Default Credentials**: `admin / admin`

**Pre-configured Dashboards:**

- API Performance
- Query Metrics
- Resource Usage
- Error Rates

### Application Logging

**Log Levels:**

- `DEBUG` - Development/troubleshooting
- `INFO` - General information
- `WARNING` - Warnings (default)
- `ERROR` - Errors
- `CRITICAL` - Critical errors

**Log Output:**

- Console (structured JSON)
- Files: `logs/app.log`
- Prometheus metrics

### View Logs

```bash
# Docker
docker logs -f fintech-rag-api

# Docker Compose
docker-compose -f docker/docker-compose.yml logs -f api

# Kubernetes
kubectl logs -f deployment/fintech-rag-api -n production

# Local
tail -f logs/app.log
```

______________________________________________________________________

## 🔐 Security Best Practices

### Environment Variables

```bash
# Use .env file (not in version control)
export $(cat .env | xargs)

# Or pass via docker
docker run --env-file .env fintech-rag:latest

# Or K8s secrets
kubectl create secret generic fintech-rag-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=PINECONE_API_KEY=... \
  -n production
```

### SSL/TLS

```bash
# For Kubernetes with cert-manager
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: fintech-rag-cert
  namespace: production
spec:
  secretName: fintech-rag-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - fintech-rag.example.com
EOF
```

### Network Policies

```bash
# Restrict traffic (Kubernetes)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fintech-rag-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: fintech-rag
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
EOF
```

______________________________________________________________________

## 📈 Performance Tuning

### Docker

```dockerfile
# In Dockerfile
ENV WORKERS=4
ENV TIMEOUT=120
ENV KEEP_ALIVE=5
```

### Kubernetes HPA

Configured in `ingress.yaml`:

- **Min Replicas**: 2
- **Max Replicas**: 10
- **CPU Trigger**: 70%
- **Memory Trigger**: 80%

### API Configuration

```bash
# In .env
CHUNK_SIZE=800
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K_VECTOR=20
RETRIEVAL_TOP_K_BM25=20
RETRIEVAL_RERANK_TOP_N=5
```

______________________________________________________________________

## 🆘 Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

#### Docker Build Fails

```bash
# Clean and rebuild
docker system prune -a
docker build -t fintech-rag:latest -f docker/Dockerfile . --no-cache
```

#### K8s Pod Pending

```bash
# Check resources
kubectl describe node
kubectl top nodes

# Check pod events
kubectl describe pod <pod-name> -n production
```

#### API Health Check Failing

```bash
# Test endpoint
curl -v http://localhost:8000/api/v1/health

# Check logs
docker logs fintech-rag-api
```

______________________________________________________________________

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

______________________________________________________________________

**Last Updated**: January 17, 2026
**Version**: 1.0.0
