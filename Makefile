.PHONY: help install dev-install test lint format clean docker-build docker-run setup

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
DOCKER_IMAGE := fintech-rag
DOCKER_TAG := latest

help: ## Show this help message
	@echo "FinTech RAG Knowledge Assistant - Makefile Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Installation & Setup
# ============================================================================

install: ## Install production dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev-install: ## Install development dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	pre-commit install

setup: ## Initial project setup
	cp .env.example .env
	mkdir -p data/raw data/processed data/indexes logs
	$(PYTHON) scripts/setup_pinecone.py
	@echo "Setup complete! Edit .env with your API keys"

# ============================================================================
# Development
# ============================================================================

run: ## Run development server
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

shell: ## Start Python shell with app context
	$(PYTHON) -i -c "from app.core.config import settings; from app.ingestion.pipeline import IngestionPipeline"

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests only
	pytest tests/integration -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	ptw tests/ -- -v

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run all linters
	ruff check app/
	black --check app/
	isort --check-only app/
	mypy app/ --ignore-missing-imports

format: ## Format code with black and isort
	black app/ tests/
	isort app/ tests/

type-check: ## Run type checking
	mypy app/ --ignore-missing-imports

security: ## Run security checks
	bandit -r app/ -f json -o bandit-report.json
	safety check

# ============================================================================
# Data & Ingestion
# ============================================================================

generate-data: ## Generate synthetic test data
	$(PYTHON) scripts/generate_test_data.py

ingest-sample: ## Ingest sample documents
	curl -X POST "http://localhost:8000/api/v1/ingest" \
		-H "Content-Type: application/json" \
		-d '{"directory_path": "./data/raw", "recursive": true}'

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f docker/Dockerfile .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-compose-up: ## Start all services with docker-compose
	docker compose -f docker/docker-compose.yml up -d --build

docker-compose-down: ## Stop all services
	docker compose -f docker/docker-compose.yml down

docker-compose-logs: ## View docker-compose logs
	docker-compose -f docker/docker-compose.yml logs -f

docker-compose-ps: ## Show docker-compose services status
	docker-compose -f docker/docker-compose.yml ps

docker-compose-clean: ## Remove docker-compose volumes and containers
	docker-compose -f docker/docker-compose.yml down -v

docker-push: ## Push Docker image to registry
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) your-registry/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push your-registry/$(DOCKER_IMAGE):$(DOCKER_TAG)

# ============================================================================
# Evaluation
# ============================================================================

benchmark: ## Run retrieval benchmarks
	$(PYTHON) scripts/benchmark.py

evaluate: ## Run full evaluation suite
	$(PYTHON) -m app.evaluation.benchmark

# ============================================================================
# UI & Monitoring
# ============================================================================

streamlit: ## Run Streamlit UI
	streamlit run ui/streamlit_app.py

metrics: ## View Prometheus metrics
	@echo "Opening Prometheus: http://localhost:9091"
	@xdg-open http://localhost:9091 2>/dev/null || open http://localhost:9091 2>/dev/null || echo "Open http://localhost:9091 manually"

grafana: ## View Grafana dashboards
	@echo "Opening Grafana: http://localhost:3000"
	@xdg-open http://localhost:3000 2>/dev/null || open http://localhost:3000 2>/dev/null || echo "Open http://localhost:3000 manually"

logs: ## Tail application logs
	tail -f logs/app.log

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/

clean-data: ## Clean processed data (keeps raw)
	rm -rf data/processed/* data/indexes/*
	@echo "Processed data and indexes cleaned"

clean-all: clean clean-data ## Clean everything including data
	rm -rf data/*
	@echo "All data cleaned"

# ============================================================================
# Kubernetes Deployment
# ============================================================================

k8s-namespace: ## Create production namespace
	kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -

k8s-apply: ## Apply Kubernetes configurations (requires namespace first)
	kubectl apply -f k8s/

k8s-apply-full: ## Create namespace and apply all Kubernetes configurations
	@$(MAKE) k8s-namespace
	@$(MAKE) k8s-apply

k8s-delete: ## Delete Kubernetes resources
	kubectl delete -f k8s/

k8s-logs: ## View Kubernetes pod logs
	kubectl logs -f deployment/fintech-rag-api -n production

k8s-logs-all: ## View logs from all pods
	kubectl logs -l app=fintech-rag -n production --tail=100 -f

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods,svc,hpa -n production

k8s-ingress: ## Show Kubernetes ingress status
	kubectl get ingress -n production -o wide

k8s-hpa: ## Show HorizontalPodAutoscaler status
	kubectl get hpa -n production

k8s-describe: ## Describe all deployment resources
	kubectl describe deployment fintech-rag-api -n production

k8s-port-forward: ## Port forward to API (localhost:8000 -> pod:8000)
	kubectl port-forward svc/fintech-rag-api 8000:80 -n production

k8s-shell: ## Open shell in pod
	kubectl exec -it $$(kubectl get pod -l app=fintech-rag -n production -o jsonpath='{.items[0].metadata.name}') -n production -- sh

# ============================================================================
# Documentation
# ============================================================================

docs-serve: ## Serve API documentation
	@echo "API docs available at http://localhost:8000/docs"
	@echo "Redoc available at http://localhost:8000/redoc"

docs-build: ## Build documentation (if using Sphinx/MkDocs)
	@echo "Documentation build not configured yet"

docs-deployment: ## Open deployment guide
	@echo "See DEPLOYMENT_GUIDE.md for comprehensive deployment instructions"

# ============================================================================
# Database Operations
# ============================================================================

pinecone-reset: ## Reset Pinecone index (WARNING: deletes all data)
	@echo "This will delete all data in Pinecone index!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) -c "from app.retrieval.vector_store import PineconeVectorStore; PineconeVectorStore().delete_namespace()"; \
	fi

# ============================================================================
# Pre-commit
# ============================================================================

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

# ============================================================================
# Status & Info
# ============================================================================

stats: ## Show project statistics
	@echo "Lines of code:"
	@find app -name "*.py" | xargs wc -l | tail -1
	@echo ""
	@echo "Number of files:"
	@find app -name "*.py" | wc -l
	@echo ""
	@echo "Test coverage:"
	@pytest tests/ --cov=app --cov-report=term-missing | tail -1

status: ## Show overall project status
	@echo ""
	@echo "📊 Fintech RAG Project Status"
	@echo "======================================"
	@echo ""
	@curl -s http://localhost:8000/api/v1/health > /dev/null && echo "✅ API Server: Running" || echo "❌ API Server: Not running"
	@docker ps > /dev/null 2>&1 && echo "✅ Docker: Available" || echo "❌ Docker: Not available"
	@kubectl version > /dev/null 2>&1 && echo "✅ Kubernetes: Available" || echo "❌ Kubernetes: Not available"
	@echo ""
	@echo "📦 Project Components:"
	@echo "   • FastAPI Server: http://localhost:8000"
	@echo "   • API Docs: http://localhost:8000/docs"
	@echo "   • Streamlit UI: http://localhost:8501 (run 'make streamlit')"
	@echo "   • Prometheus: http://localhost:9091 (docker-compose)"
	@echo "   • Grafana: http://localhost:3000 (docker-compose)"
	@echo ""
	@echo "🚀 Deployment Options:"
	@echo "   • Local: make run"
	@echo "   • Docker: make docker-run"
	@echo "   • Docker Compose: make docker-compose-up"
	@echo "   • Kubernetes: make k8s-apply-full"
	@echo ""
	@echo "📚 Documentation: See DEPLOYMENT_GUIDE.md"
	@echo ""
