# Makefile for local-weaviate-rag project

.PHONY: help lint lint-fix test test-full test-api format check install-dev clean start-api stop-api
.PHONY: docker-build docker-up docker-down docker-logs docker-restart docker-clean

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  lint         - Run all linters (check only)"
	@echo "  lint-fix     - Run all linters with auto-fix"
	@echo "  format       - Format code with ruff and black"
	@echo "  check        - Check code quality without fixing"
	@echo "  test         - Run basic functionality tests"
	@echo "  test-full    - Run comprehensive functionality tests"
	@echo "  test-api     - Test FastAPI service endpoints"
	@echo "  start-api    - Start FastAPI development server (local)"
	@echo "  stop-api     - Stop FastAPI server (if running in background)"
	@echo "  install-dev  - Install development dependencies"
	@echo "  clean        - Clean up temporary files and caches"
	@echo ""
	@echo "Docker (Production):"
	@echo "  docker-build   - Build Docker images for production"
	@echo "  docker-up      - Start all services in Docker (Weaviate + API)"
	@echo "  docker-down    - Stop and remove all Docker containers"
	@echo "  docker-logs    - View logs from all Docker containers"
	@echo "  docker-restart - Restart all Docker services"
	@echo "  docker-clean   - Stop containers and remove volumes (⚠️  deletes data)"
	@echo ""
	@echo "Examples:"
	@echo "  make lint-fix      # Fix all linting issues"
	@echo "  make test-full     # Run complete test suite"
	@echo "  make start-api     # Start API server locally"
	@echo "  make docker-up     # Start production stack in Docker"

# Install development dependencies
install-dev:
	uv sync --extra dev

# Run all linters (check only)
lint:
	./lint.sh

# Run all linters with auto-fix
lint-fix:
	./lint.sh --fix

# Format code
format:
	./lint.sh --ruff-only --fix
	./lint.sh --black-only --fix

# Check code quality without fixing
check:
	./lint.sh --quiet

# Run basic functionality tests
test:
	uv run python tests/test_functionality.py

# Run comprehensive functionality tests (alias for test)
test-full: test

# Test FastAPI service endpoints
test-api:
	uv run python test_api.py

# Start FastAPI development server
start-api:
	./start_api.sh


# Stop FastAPI server (kill process listening on API_PORT or default 8001)
stop-api:
	@echo "Stopping FastAPI server..."
	@API_PORT=$${API_PORT:-8001}; lsof -ti:$$API_PORT | xargs kill -9 2>/dev/null || echo "No server running on port $$API_PORT"


# Clean up temporary files and caches
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "Cleaned up temporary files and caches"

# === Docker Commands (Production) ===

# Build Docker images
docker-build:
	@echo "🔨 Building Docker images..."
	docker compose build --no-cache

# Start all services in Docker
docker-up:
	@echo "🚀 Starting all services in Docker..."
	docker compose up -d
	@echo "✅ Services started!"
	@echo "📊 Weaviate: http://localhost:$${WEAVIATE_PORT:-8080}"
	@echo "🌐 API: http://localhost:$${API_PORT:-8001}"
	@echo "📖 API Docs: http://localhost:$${API_PORT:-8001}/docs"
	@echo ""
	@echo "Use 'make docker-logs' to view logs"

# Stop and remove all containers
docker-down:
	@echo "🛑 Stopping all Docker services..."
	docker compose down
	@echo "✅ Services stopped"

# View logs from all containers
docker-logs:
	docker compose logs -f

# View logs from specific service
docker-logs-api:
	docker compose logs -f api

docker-logs-weaviate:
	docker compose logs -f weaviate

# Restart all services
docker-restart:
	@echo "🔄 Restarting all Docker services..."
	docker compose restart
	@echo "✅ Services restarted"

# Stop containers and remove volumes (deletes all data)
docker-clean:
	@echo "⚠️  WARNING: This will delete all data in Weaviate!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "🧹 Cleaning up Docker containers and volumes..."; \
		docker compose down -v; \
		echo "✅ Cleanup complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

# Rebuild and restart (useful after code changes)
docker-rebuild:
	@echo "🔄 Rebuilding and restarting services..."
	docker compose down
	docker compose build
	docker compose up -d
	@echo "✅ Rebuild complete!"

# Check Docker service status
docker-status:
	@echo "📊 Docker service status:"
	@docker compose ps