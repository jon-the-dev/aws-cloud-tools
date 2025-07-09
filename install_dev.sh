#!/bin/bash

# AWS Cloud Utilities v2 - Development Installation Script

set -e

echo "AWS Cloud Utilities v2 - Development Installation"
echo "================================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the v2 directory."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Warning: Python $required_version or higher is recommended. Found: $python_version"
fi

echo "Installing AWS Cloud Utilities in development mode..."

# Install in development mode
pip install -e ".[dev]"

echo ""
echo "Installation complete!"
echo ""
echo "Test the installation:"
echo "  python test_migration.py"
echo ""
echo "Try the CLI:"
echo "  aws-cloud-utilities --help"
echo "  aws-cloud-utilities account --help"
echo "  aws-cloud-utilities support --help"
echo ""
echo "Note: You'll need valid AWS credentials configured to use most commands."
