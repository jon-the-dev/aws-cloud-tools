# AWS Cloud Utilities v2 - Makefile
# Provides convenient commands for testing, development, and deployment

.PHONY: help install test test-quick test-dry test-verbose test-ci clean lint format security \
        docs docs-gen docs-check docs-serve

# Default target
help:
	@echo "AWS Cloud Utilities v2 - Available Commands"
	@echo "==========================================="
	@echo ""
	@echo "Development:"
	@echo "  install      Install package in development mode"
	@echo "  clean        Clean up temporary files and caches"
	@echo "  format       Format code with black and isort"
	@echo "  lint         Run linting checks"
	@echo "  security     Run security scans"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run comprehensive test suite"
	@echo "  test-quick   Run quick tests only"
	@echo "  test-dry     Run dry-run tests (no AWS calls)"
	@echo "  test-verbose Run tests with verbose output"
	@echo "  test-ci      Run tests in CI mode"
	@echo "  test-help    Run help-only tests"
	@echo ""
	@echo "Documentation:"
	@echo "  docs         Regenerate, check, and build the docs site"
	@echo "  docs-gen     Regenerate command reference from the CLI"
	@echo "  docs-check   Verify docs match the CLI (no writes)"
	@echo "  docs-serve   Serve the docs locally with live reload"
	@echo ""
	@echo "Examples:"
	@echo "  make test REGION=us-west-2 PROFILE=dev"
	@echo "  make test-quick"
	@echo "  make lint"

# Variables
REGION ?= us-east-1
PROFILE ?= 
OUTPUT_DIR ?= ./test_results
# Check if pipenv is available and use it, otherwise fall back to python3
PYTHON ?= $(shell command -v pipenv >/dev/null 2>&1 && echo "pipenv run python" || echo "python3")

# Installation
install:
	@echo "📦 Installing AWS Cloud Utilities v2 in development mode..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e .
	@echo "✅ Installation complete"

# Testing targets
test:
	@echo "🧪 Running comprehensive test suite..."
	@if [ -n "$(PROFILE)" ]; then \
		./run_tests.sh --region $(REGION) --profile $(PROFILE) --output-dir $(OUTPUT_DIR); \
	else \
		./run_tests.sh --region $(REGION) --output-dir $(OUTPUT_DIR); \
	fi

test-quick:
	@echo "⚡ Running quick tests..."
	@if [ -n "$(PROFILE)" ]; then \
		./run_tests.sh --quick --region $(REGION) --profile $(PROFILE) --output-dir $(OUTPUT_DIR); \
	else \
		./run_tests.sh --quick --region $(REGION) --output-dir $(OUTPUT_DIR); \
	fi

test-dry:
	@echo "🔍 Running dry-run tests..."
	$(PYTHON) test_comprehensive.py --dry-run --region $(REGION) --output-file $(OUTPUT_DIR)/test_results_dry_run.json

test-verbose:
	@echo "📝 Running tests with verbose output..."
	@if [ -n "$(PROFILE)" ]; then \
		./run_tests.sh --verbose --region $(REGION) --profile $(PROFILE) --output-dir $(OUTPUT_DIR); \
	else \
		./run_tests.sh --verbose --region $(REGION) --output-dir $(OUTPUT_DIR); \
	fi

test-ci:
	@echo "🤖 Running tests in CI mode..."
	@if [ -n "$(PROFILE)" ]; then \
		./run_tests.sh --ci --region $(REGION) --profile $(PROFILE) --output-dir $(OUTPUT_DIR); \
	else \
		./run_tests.sh --ci --region $(REGION) --output-dir $(OUTPUT_DIR); \
	fi

test-help:
	@echo "❓ Running help-only tests..."
	$(PYTHON) test_comprehensive.py --dry-run --verbose | grep -A 20 "Testing Help Commands"

# Code quality
format:
	@echo "🎨 Formatting code..."
	$(PYTHON) -m black aws_cloud_utilities/ --line-length 120
	$(PYTHON) -m isort aws_cloud_utilities/ --profile black
	@echo "✅ Code formatting complete"

lint:
	@echo "🔍 Running linting checks..."
	@echo "Running flake8..."
	$(PYTHON) -m flake8 aws_cloud_utilities/ --max-line-length=120 --extend-ignore=E203,W503 || true
	@echo "Running black check..."
	$(PYTHON) -m black --check aws_cloud_utilities/ --line-length 120 || true
	@echo "Running isort check..."
	$(PYTHON) -m isort --check-only aws_cloud_utilities/ --profile black || true
	@echo "Running mypy..."
	$(PYTHON) -m mypy aws_cloud_utilities/ --ignore-missing-imports || true
	@echo "✅ Linting complete"

security:
	@echo "🔒 Running security scans..."
	@echo "Running bandit..."
	$(PYTHON) -m bandit -r aws_cloud_utilities/ || true
	@echo "Running safety check..."
	$(PYTHON) -m safety check || true
	@echo "✅ Security scan complete"

# Cleanup
clean:
	@echo "🧹 Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/
	rm -f test_results_*.json test_report_*.html
	@echo "✅ Cleanup complete"

# Documentation
docs: docs-gen docs-check
	@echo "📚 Building documentation site..."
	$(PYTHON) -m mkdocs build --strict
	@echo "✅ Site built in ./site"

docs-gen:
	@echo "📝 Regenerating command reference from the CLI..."
	$(PYTHON) scripts/gen_docs.py

docs-check:
	@echo "🔍 Checking documentation against the CLI..."
	$(PYTHON) scripts/gen_docs.py --check
	$(PYTHON) scripts/validate_docs.py

docs-serve:
	$(PYTHON) -m mkdocs serve

# Development helpers
dev-setup: install
	@echo "🛠️  Setting up development environment..."
	$(PYTHON) -m pip install black isort flake8 mypy bandit safety
	@echo "✅ Development environment ready"

check-aws:
	@echo "🔍 Checking AWS configuration..."
	@if [ -n "$(PROFILE)" ]; then \
		aws sts get-caller-identity --profile $(PROFILE) || echo "❌ AWS credentials not configured for profile $(PROFILE)"; \
	else \
		aws sts get-caller-identity || echo "❌ AWS credentials not configured"; \
	fi

# Multi-region testing
test-multi-region:
	@echo "🌍 Running tests across multiple regions..."
	@for region in us-east-1 us-west-2 eu-west-1; do \
		echo "Testing region: $$region"; \
		make test-quick REGION=$$region || true; \
	done

# Performance testing
test-performance:
	@echo "⏱️  Running performance tests..."
	@start_time=$$(date +%s); \
	make test-dry; \
	end_time=$$(date +%s); \
	duration=$$((end_time - start_time)); \
	echo "Dry-run test duration: $${duration}s"

# Validation
validate: format lint security test-dry
	@echo "✅ All validation checks complete"

# Release preparation
pre-release: clean validate test
	@echo "🚀 Pre-release checks complete"
	@echo "Ready for release!"

# Show current configuration
config:
	@echo "Current Configuration:"
	@echo "  Region: $(REGION)"
	@echo "  Profile: $(PROFILE)"
	@echo "  Output Dir: $(OUTPUT_DIR)"
	@echo "  Python: $(PYTHON)"
	@echo ""
	@echo "AWS Configuration:"
	@make check-aws
