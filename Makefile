# Makefile for local-weaviate-rag project

.PHONY: help lint lint-fix test test-full format check install-dev clean

# Default target
help:
	@echo "Available targets:"
	@echo "  lint         - Run all linters (check only)"
	@echo "  lint-fix     - Run all linters with auto-fix"
	@echo "  format       - Format code with ruff and black"
	@echo "  check        - Check code quality without fixing"
	@echo "  test         - Run basic functionality tests"
	@echo "  test-full    - Run comprehensive functionality tests"
	@echo "  install-dev  - Install development dependencies"
	@echo "  clean        - Clean up temporary files and caches"
	@echo ""
	@echo "Examples:"
	@echo "  make lint-fix    # Fix all linting issues"
	@echo "  make test-full   # Run complete test suite"

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