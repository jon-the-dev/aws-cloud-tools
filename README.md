# AWS Cloud Utilities v2

A unified command-line toolkit for AWS operations with enhanced functionality. This package consolidates various AWS management scripts into a single, powerful CLI tool.

## Prerequisites

- Python 3.x
- Boto3 library
- AWS credentials configured (e.g., via ~/.aws/credentials or environment variables)

## Installation

1. Clone this repo
2. Install the required Python packages (Pipenv in repo)
   1. `pipenv sync`

## Features

- **Unified CLI**: Single command interface for all AWS operations
- **Parallel Processing**: Multi-threaded operations for improved performance
- **Rich Output**: Beautiful, formatted output with tables and colors
- **Flexible Configuration**: Support for AWS profiles, regions, and custom settings
- **Comprehensive Coverage**: Tools for cost optimization, inventory, security, logs, and more

## Installation

```bash
# Install from PyPI (when published)
pip install aws-cloud-utilities

# Install from source
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools/v2
pip install -e .
```

## Quick Start

```bash
# Get account information
aws-cloud-utilities account info

# List all resources in your account
aws-cloud-utilities inventory resources

# Find cheapest GPU spot instances
aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge

# Troubleshoot MySQL RDS connection issues
aws-cloud-utilities rds troubleshoot-mysql my-mysql-db

# Aggregate CloudWatch logs
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function

# Security audit
aws-cloud-utilities security blue-team-audit
```

## Command Structure

The CLI follows a hierarchical structure similar to the AWS CLI:

```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

### Available Services

- **account**: Account information and management
- **costops**: Cost optimization and pricing tools
- **inventory**: Resource discovery and inventory
- **logs**: CloudWatch logs management
- **rds**: RDS management and troubleshooting
- **security**: Security auditing and tools
- **s3**: S3 bucket operations
- **iam**: IAM management and auditing
- **networking**: Network utilities
- **support**: AWS support tools

### Global Options

- `--profile`: AWS profile to use
- `--region`: AWS region
- `--output`: Output format (json, yaml, table)
- `--verbose`: Enable verbose logging
- `--debug`: Enable debug mode

## Configuration

Create a `.env` file in your project directory or home directory:

```env
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
AWS_OUTPUT_FORMAT=table
WORKERS=4
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools/v2

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aws_cloud_utilities

# Run specific test file
pytest tests/test_cli.py
```

### Code Quality

```bash
# Format code
black aws_cloud_utilities tests

# Lint code
flake8 aws_cloud_utilities tests

# Type checking
mypy aws_cloud_utilities
```

## Migration from v1

If you're migrating from the original script collection, see our [Migration Guide](docs/migration.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- [GitHub Issues](https://github.com/jon-the-dev/aws-cloud-tools/issues)
- [Documentation](https://github.com/jon-the-dev/aws-cloud-tools/tree/main/docs)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
