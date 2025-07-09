#!/bin/bash
# Documentation build and serve script

set -e

echo "Installing documentation dependencies..."
pip install -r docs-requirements.txt

echo "Building documentation..."
mkdocs build

echo "Starting documentation server..."
echo "Documentation will be available at: http://127.0.0.1:8000"
mkdocs serve
