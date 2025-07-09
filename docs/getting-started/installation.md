# Installation

This guide covers different ways to install AWS Cloud Utilities v2.

## Prerequisites

- Python 3.12 or higher
- AWS CLI configured with appropriate credentials
- pip package manager

## Installation Methods

### From PyPI (Recommended)

!!! note "Coming Soon"
    PyPI installation will be available once the package is published.

```bash
pip install aws-cloud-utilities
```

### From Source (Development)

For the latest features or development:

```bash
# Clone the repository
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools/v2

# Install in development mode
pip install -e .
```

### Using the Development Script

For quick development setup:

```bash
cd aws-cloud-tools/v2
./install_dev.sh
```

This script will:
- Create a virtual environment (if needed)
- Install the package in development mode
- Install development dependencies
- Set up pre-commit hooks

## Verify Installation

After installation, verify everything works:

```bash
# Check version
aws-cloud-utilities --version

# Get help
aws-cloud-utilities --help

# Test basic functionality
aws-cloud-utilities account info
```

## Dependencies

The tool automatically installs these key dependencies:

- **boto3**: AWS SDK for Python
- **click**: Command-line interface framework
- **rich**: Rich text and beautiful formatting
- **pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management
- **PyYAML**: YAML file support

## Development Dependencies

For development and testing:

```bash
pip install -e ".[dev]"
```

This includes:
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## AWS Configuration

Ensure your AWS credentials are configured:

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

## Troubleshooting

### Permission Issues

If you encounter permission errors:

```bash
# Use --user flag
pip install --user aws-cloud-utilities

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install aws-cloud-utilities
```

### Python Version Issues

Check your Python version:

```bash
python --version
# Should be 3.12 or higher
```

If you have multiple Python versions:

```bash
python3.12 -m pip install aws-cloud-utilities
```

### AWS Credentials Issues

Test your AWS credentials:

```bash
aws sts get-caller-identity
```

If this fails, reconfigure your AWS credentials:

```bash
aws configure
```

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with basic commands
- [Configuration](configuration.md) - Configure profiles and settings
- [Command Reference](../commands/index.md) - Explore available commands
