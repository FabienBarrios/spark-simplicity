# Makefile for Spark Simplicity
# Professional development workflow automation

.PHONY: help install install-dev clean lint format type-check test test-unit test-integration test-performance test-all coverage build docs serve-docs

# Default target
help:
	@echo "Spark Simplicity - Development Commands"
	@echo "======================================"
	@echo "Setup:"
	@echo "  install      Install package in production mode"
	@echo "  install-dev  Install package in development mode with all dependencies"
	@echo "  clean        Clean build artifacts and cache files"
	@echo ""
	@echo "Code Quality:"
	@echo "  format       Format code with black and isort"
	@echo "  lint         Run linting with flake8"
	@echo "  type-check   Run type checking with mypy"
	@echo "  check-all    Run all code quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-unit    Run only unit tests"
	@echo "  test-integration Run only integration tests"
	@echo "  test-performance Run only performance tests"
	@echo "  coverage     Run tests with coverage report"
	@echo ""
	@echo "Build & Docs:"
	@echo "  build        Build distribution packages"
	@echo "  docs         Generate documentation"
	@echo "  serve-docs   Serve documentation locally"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install hypothesis

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Code formatting
format:
	black spark_simplicity/ tests/
	isort spark_simplicity/ tests/

# Linting
lint:
	flake8 spark_simplicity/ tests/

# Type checking
type-check:
	mypy spark_simplicity/

# All quality checks
check-all: format lint type-check

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration and not performance and not slow"

test-integration:
	pytest tests/ -v -m integration

test-performance:
	pytest tests/ -v -m performance

test-all: test-unit test-integration test-performance

# Coverage
coverage:
	pytest tests/ --cov=spark_simplicity --cov-report=html --cov-report=term-missing --cov-fail-under=90

# Build
build: clean
	python -m build

# Documentation
docs:
	@echo "Documentation generation would go here"
	@echo "Consider using Sphinx, MkDocs, or similar"

serve-docs:
	@echo "Documentation serving would go here"

# CI/CD simulation
ci: install-dev check-all coverage
	@echo "✅ All CI checks passed!"