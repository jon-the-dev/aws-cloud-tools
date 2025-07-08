.PHONY: help install install-dev test test-cov lint format clean build publish docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install package in development mode
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=aws_cloud_utilities --cov-report=html --cov-report=term

lint: ## Run linting
	flake8 aws_cloud_utilities tests
	mypy aws_cloud_utilities

format: ## Format code
	black aws_cloud_utilities tests
	isort aws_cloud_utilities tests

format-check: ## Check code formatting
	black --check aws_cloud_utilities tests
	isort --check-only aws_cloud_utilities tests

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build package
	python -m build

publish-test: build ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	python -m twine upload dist/*

docs: ## Build documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

check: format-check lint test ## Run all checks

# Development shortcuts
dev-setup: install-dev ## Set up development environment
	@echo "Development environment set up successfully!"

dev-test: ## Quick development test
	pytest tests/test_cli.py -v

dev-run: ## Run CLI in development mode
	python -m aws_cloud_utilities.cli --help
