# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AWS Cloud Utilities v2.0.0 - A unified Python CLI toolkit for AWS operations. The project uses modern Python packaging with Click for CLI framework, Rich for terminal output, and Pydantic for configuration validation.

## Development Commands

### Setup and Installation
```bash
make install          # Install for development
make dev-setup        # Full development environment setup
pip install -e .      # Editable install
```

### Testing
```bash
make test             # Run comprehensive test suite
make test-quick       # Fast tests only  
./run_tests.sh        # Shell wrapper with options
python test_comprehensive.py --mode quick  # Direct test execution
python -m pytest tests/  # Unit tests only
```

### Code Quality
```bash
make lint             # Flake8 linting
make format           # Black code formatting (120 char lines)
make security         # Bandit security scanning
make validate         # All quality checks
mypy aws_cloud_utilities/  # Type checking
```

### Documentation
```bash
mkdocs serve          # Live documentation server
mkdocs build          # Build documentation
```

### Release Preparation
```bash
make pre-release      # Full validation pipeline
```

## Architecture Overview

### CLI Structure
- **Entry Points**: `aws-cloud-utilities` and `awscu` commands
- **Framework**: Click-based with command groups per AWS service
- **Global Options**: `--profile`, `--region`, `--output`, `--verbose`, `--debug`
- **Output**: Rich terminal formatting with multiple output formats (table, JSON, YAML, CSV)

### Core Components
- **`aws_cloud_utilities/cli.py`**: Main CLI entry point and global configuration
- **`aws_cloud_utilities/core/`**: Shared utilities (config, auth, common functions)
- **`aws_cloud_utilities/commands/`**: Service-specific command modules
- **Configuration**: Pydantic-based with environment variable support and AWS profile management

### Service Commands
Each AWS service has its own command module following consistent patterns:
- `account`, `awsconfig`, `bedrock`, `billing`, `cloudformation`, `cloudfront`, `costops`
- `ecr`, `iam`, `inventory`, `logs`, `networking`, `rds`, `s3`
- `security`, `stepfunctions`, `support`, `waf`

### Configuration Management
- **Hierarchy**: CLI args > environment variables > config files
- **Files**: `.env` support, YAML configuration
- **AWS Integration**: Profile and region handling through boto3
- **Validation**: Pydantic models for type safety

## Key Implementation Patterns

### Command Structure
Commands follow a consistent pattern with:
- Click command groups and subcommands
- Rich console output with progress bars
- Error handling with meaningful messages
- Parallel execution support for performance
- Support for multiple output formats

### Authentication Flow
- AWS credentials managed through boto3 sessions
- Profile-based authentication with fallback to environment
- Region configuration with multi-region support
- Client creation abstracted in core auth module

### Testing Philosophy
- **Non-destructive**: Tests use read-only AWS operations where possible
- **Configurable**: Multiple test modes (quick, verbose, dry-run, CI)
- **Comprehensive**: Both unit tests and integration tests
- **Reporting**: HTML and JSON output for CI/CD integration

## Migration Context

This is v2 of the project. Legacy v1 scripts are preserved in `/old/` directory:
- `MIGRATED_COMMANDS.md` documents command mappings from v1 to v2
- Enhanced functionality and improved architecture in v2
- Backwards compatibility considerations documented

## Development Guidelines

### Code Style
- Black formatting with 120 character line limit
- Type hints required for new code
- Pydantic models for configuration and data validation
- Rich library for all terminal output

### Adding New Commands
1. Create command module in `aws_cloud_utilities/commands/`
2. Register in `aws_cloud_utilities/commands/__init__.py`
3. Follow existing patterns for Click decorators and Rich output
4. Add comprehensive tests following existing test patterns
5. Update documentation in `/docs/`

### AWS Client Usage
- Use `aws_cloud_utilities/core/auth.py` for client creation
- Handle regions and profiles consistently
- Implement proper error handling for AWS API calls
- Consider parallel execution for bulk operations

## Current Development State

Active development with recent additions of RDS and WAF commands. The project is in active migration from v1 scripts with ongoing test suite enhancements and documentation updates.