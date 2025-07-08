# AWS Cloud Utilities v2 - Conversion Plan

## Overview

Convert the existing collection of AWS scripts into a single, unified Python package called `aws-cloud-utilities` that will be published to PyPI. The new package will provide a CLI interface similar to the AWS CLI but with enhanced functionality and "super powers" for AWS operations.

## Current State Analysis

### Existing Directory Structure

```
aws-cloud-tools/
├── account/          # Account information scripts
├── cloudformation/   # CloudFormation utilities
├── cloudfront/       # CloudFront management
├── costops/          # Cost optimization tools
├── devopstools/      # DevOps utilities
├── ecr/              # ECR management
├── iam/              # IAM auditing
├── inventory/        # Resource inventory
├── logs/             # CloudWatch logs management
├── networking/       # Network utilities
├── s3/               # S3 operations
├── security/         # Security tools
├── step-functions/   # Step Functions utilities
└── support/          # Support tools
```

### Key Scripts Identified

- **CostOps**: `aws_pricing.py`, `gpu_spots.py`, `spot_manager.py`, `costexplorer_click.py`
- **Inventory**: `inventory.py`, `bedrock_models.py`, `workspaces_inventory.py`
- **Logs**: `aws_logs_aggregator.py`, `manage_cw_logs.py`, `combine_logs.py`
- **Security**: `aws_blue_team.py`, `acm_create_cert.py`
- **S3**: Various S3 management scripts
- **IAM**: IAM auditing tools
- **Support**: Support level checking

## Target Architecture

### Package Structure

```
v2/
├── aws_cloud_utilities/
│   ├── __init__.py
│   ├── cli.py                    # Main CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   ├── auth.py              # AWS authentication
│   │   ├── utils.py             # Common utilities
│   │   └── exceptions.py        # Custom exceptions
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── account.py           # Account operations
│   │   ├── costops.py           # Cost optimization
│   │   ├── inventory.py         # Resource inventory
│   │   ├── logs.py              # Log management
│   │   ├── security.py          # Security tools
│   │   ├── s3.py                # S3 operations
│   │   ├── iam.py               # IAM management
│   │   ├── networking.py        # Network utilities
│   │   ├── cloudformation.py    # CloudFormation tools
│   │   ├── cloudfront.py        # CloudFront management
│   │   ├── ecr.py               # ECR operations
│   │   ├── stepfunctions.py     # Step Functions
│   │   └── support.py           # Support tools
│   └── models/
│       ├── __init__.py
│       └── aws_resources.py     # Data models
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_commands/
│   └── fixtures/
├── docs/
│   ├── index.md
│   ├── commands/
│   └── examples/
├── setup.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── CHANGELOG.md
└── .env.example
```

## Implementation Plan

### Phase 1: Foundation Setup (Week 1)

1. **Create v2 directory structure**
   - Set up the new package structure
   - Initialize `__init__.py` files
   - Create basic `setup.py` and `pyproject.toml`

2. **Core Infrastructure**
   - Implement `core/config.py` for configuration management
   - Create `core/auth.py` for AWS authentication
   - Build `core/utils.py` with common utilities
   - Set up logging framework
   - Create `core/exceptions.py` for error handling

3. **CLI Framework**
   - Implement main CLI entry point using Click or argparse
   - Create command group structure
   - Add global options (--profile, --region, --verbose, etc.)

### Phase 2: Command Migration (Weeks 2-4)

Migrate existing scripts to command modules in priority order:

#### Week 2: High-Priority Commands

1. **Account Commands** (`commands/account.py`)
   - Migrate account information scripts
   - Add account ID retrieval, region listing

2. **Inventory Commands** (`commands/inventory.py`)
   - Migrate `inventory.py` functionality
   - Add Bedrock models inventory
   - Add WorkSpaces inventory
   - Implement parallel resource discovery

3. **Cost Operations** (`commands/costops.py`)
   - Migrate pricing tools
   - Add GPU spot instance finder
   - Integrate Cost Explorer functionality
   - Add spot instance manager

#### Week 3: Core Operations

4. **S3 Commands** (`commands/s3.py`)
   - Migrate S3 bucket operations
   - Add bucket nuke functionality
   - Implement S3 utilities

5. **Logs Commands** (`commands/logs.py`)
   - Migrate CloudWatch logs aggregator
   - Add log management utilities
   - Implement log combination tools

6. **Security Commands** (`commands/security.py`)
   - Migrate blue team tools
   - Add ACM certificate creation
   - Implement security auditing

#### Week 4: Additional Services

7. **IAM Commands** (`commands/iam.py`)
   - Migrate IAM auditing tools
   - Add role and policy management

8. **Networking Commands** (`commands/networking.py`)
   - Migrate IP range tools
   - Add network utilities

9. **Support Commands** (`commands/support.py`)
   - Migrate support level checking

### Phase 3: Advanced Features (Week 5)

1. **Configuration Management**
   - Implement `.env` file support
   - Add profile management
   - Create configuration validation

2. **Output Formatting**
   - Add JSON, YAML, table output formats
   - Implement colored output
   - Add progress bars for long operations

3. **Error Handling & Logging**
   - Comprehensive error handling
   - Structured logging
   - Debug mode support

### Phase 4: Testing & Documentation (Week 6)

1. **Testing**
   - Unit tests for all commands
   - Integration tests
   - Mock AWS services for testing

2. **Documentation**
   - Command documentation
   - Usage examples
   - API documentation

3. **Packaging**
   - Finalize `setup.py` and `pyproject.toml`
   - Create distribution packages
   - Test installation

### Phase 5: Publishing & Deployment (Week 7)

1. **PyPI Preparation**
   - Package validation
   - Version management
   - Release notes

2. **CI/CD Setup**
   - GitHub Actions for testing
   - Automated PyPI publishing
   - Version tagging

## Technical Specifications

### CLI Interface Design

```bash
# Main command structure
aws-cloud-utilities [GLOBAL-OPTIONS] <command> [COMMAND-OPTIONS]

# Examples:
aws-cloud-utilities account info
aws-cloud-utilities inventory resources --region us-east-1
aws-cloud-utilities costops pricing --service ec2
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function
aws-cloud-utilities s3 nuke-bucket --bucket-name my-bucket --confirm
aws-cloud-utilities security blue-team-audit
```

### Global Options

- `--profile`: AWS profile to use
- `--region`: AWS region
- `--output`: Output format (json, yaml, table)
- `--verbose`: Enable verbose logging
- `--debug`: Enable debug mode
- `--config`: Custom config file path

### Configuration Management

- Support for `.env` files
- AWS profile integration
- Default region and output format
- Threading configuration (default: 4 workers)

### Dependencies

```python
# Core dependencies
boto3>=1.34.0
click>=8.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
rich>=13.0.0  # For beautiful CLI output
tabulate>=0.9.0  # For table formatting

# Optional dependencies
pandas>=2.0.0  # For data analysis features
requests>=2.31.0  # For API calls
```

### Error Handling Strategy

1. **Graceful Degradation**: Continue operations when possible
2. **Detailed Error Messages**: Clear, actionable error descriptions
3. **Retry Logic**: Automatic retries for transient failures
4. **Logging**: Comprehensive logging for debugging

### Performance Considerations

1. **Threading**: Use ThreadPoolExecutor for parallel operations
2. **Caching**: Cache AWS service clients and common data
3. **Pagination**: Handle AWS API pagination efficiently
4. **Rate Limiting**: Respect AWS API rate limits

## Migration Strategy

### Script Conversion Process

For each existing script:

1. **Analyze Functionality**: Understand what the script does
2. **Extract Core Logic**: Separate business logic from CLI handling
3. **Create Command Function**: Wrap logic in Click command
4. **Add Error Handling**: Implement proper error handling
5. **Add Tests**: Create unit tests for the functionality
6. **Update Documentation**: Document the new command

### Backward Compatibility

- Maintain similar command-line interfaces where possible
- Provide migration guide for users
- Keep original scripts until v2 is stable

## Quality Assurance

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints throughout
- Implement comprehensive docstrings
- Use Black for code formatting
- Use pylint/flake8 for linting

### Testing Strategy

- Unit tests for all command functions
- Integration tests with mocked AWS services
- End-to-end tests with real AWS resources (in test account)
- Performance tests for resource-intensive operations

### Documentation Requirements

- README with installation and basic usage
- Command reference documentation
- Examples and tutorials
- API documentation for developers
- Migration guide from v1 scripts

## Success Metrics

### Functionality

- [ ] All existing script functionality preserved
- [ ] Unified CLI interface working
- [ ] Package installable via pip
- [ ] All tests passing

### Usability

- [ ] Intuitive command structure
- [ ] Helpful error messages
- [ ] Comprehensive help system
- [ ] Good performance (parallel operations)

### Quality

- [ ] >90% test coverage
- [ ] No critical security vulnerabilities
- [ ] Documentation complete
- [ ] Code quality metrics met

## Risks & Mitigation

### Technical Risks

1. **AWS API Changes**: Use latest boto3, implement proper error handling
2. **Performance Issues**: Profile and optimize critical paths
3. **Dependency Conflicts**: Pin versions, use virtual environments

### Project Risks

1. **Scope Creep**: Stick to migration plan, defer new features
2. **Timeline Delays**: Prioritize core functionality first
3. **Quality Issues**: Implement testing early and often

## Timeline Summary

| Week | Focus | Deliverables |
|------|-------|-------------|
| 1 | Foundation | Core infrastructure, CLI framework |
| 2 | Core Commands | Account, Inventory, CostOps commands |
| 3 | Service Commands | S3, Logs, Security commands |
| 4 | Additional Services | IAM, Networking, Support commands |
| 5 | Advanced Features | Configuration, formatting, error handling |
| 6 | Testing & Docs | Comprehensive testing and documentation |
| 7 | Publishing | PyPI package, CI/CD, release |

## Current Progress ✅

### Completed (Phase 1 - Foundation)
- [x] **Created v2 directory structure** - Complete package structure in place
- [x] **Core Infrastructure** - All core modules implemented:
  - [x] Configuration management (`core/config.py`)
  - [x] AWS authentication (`core/auth.py`) 
  - [x] Common utilities (`core/utils.py`)
  - [x] Custom exceptions (`core/exceptions.py`)
- [x] **CLI Framework** - Main CLI entry point with Click framework
- [x] **Command Structure** - All command groups created with placeholders
- [x] **Account Commands** - Fully implemented account management commands
- [x] **Data Models** - Pydantic models for AWS resources
- [x] **Packaging Setup** - Modern Python packaging with pyproject.toml
- [x] **Development Tools** - Makefile, requirements files, testing structure
- [x] **Documentation** - README, CHANGELOG, and basic docs structure

### Ready for Testing
The foundation is complete and ready for:
1. **Installation testing** - `pip install -e .` in v2 directory
2. **Basic CLI testing** - `aws-cloud-utilities --help`
3. **Account commands testing** - `aws-cloud-utilities account info`

## Next Steps (Phase 2 - Command Migration)

### Immediate Actions (This Week)
1. **Test Installation** - Verify package installs correctly
2. **Validate CLI** - Test basic CLI functionality
3. **Begin Command Migration** - Start with high-priority commands:
   - CostOps commands (pricing, GPU spots, spot manager)
   - Inventory commands (resource discovery, Bedrock models)
   - Logs commands (aggregation, management)

### Command Migration Priority
1. **CostOps** (`commands/costops.py`) - Migrate from `costops/` directory
2. **Inventory** (`commands/inventory.py`) - Migrate from `inventory/` directory  
3. **Logs** (`commands/logs.py`) - Migrate from `logs/` directory
4. **Security** (`commands/security.py`) - Migrate from `security/` directory
5. **S3** (`commands/s3.py`) - Migrate from `s3/` directory
6. **IAM** (`commands/iam.py`) - Migrate from `iam/` directory

### Installation Instructions
```bash
cd /Users/jon/code/aws-cloud-tools/v2
pip install -e ".[dev]"  # Install in development mode
aws-cloud-utilities --help  # Test CLI
aws-cloud-utilities account info  # Test account commands
```

This plan provides a structured approach to converting the existing AWS scripts into a professional, publishable Python package while maintaining all existing functionality and adding significant improvements in usability and maintainability.

## ✅ **Migration Progress Update**

### Recently Completed (Support & Account Commands)
- [x] **Support Commands** (`commands/support.py`) - MIGRATED ✅
  - `check-level`: Check AWS support level using severity levels method
  - `severity-levels`: List available support severity levels  
  - `cases`: List AWS support cases with filtering
  - `services`: List AWS services available for support
  - Migrated from `support/aws_check_support.py` and `support/aws_check_support2.py`

- [x] **Enhanced Account Commands** (`commands/account.py`) - ENHANCED ✅
  - `info`: Basic account information (existing)
  - `contact-info`: Get primary and alternate contact information
  - `detect-control-tower`: Detect Control Tower/Landing Zone deployments
  - `regions`: List available regions (existing)
  - `service-regions`: List regions for specific services (existing)
  - `limits`: Get service limits (existing)
  - `validate`: Validate credentials (existing)
  - Migrated from `account/aws_get_acct_info.py` and `account/detect_control_tower.py`

### Testing Infrastructure Added
- [x] **Migration Test Script** (`test_migration.py`) - Tests imports, config, and CLI help
- [x] **Development Installation** (`install_dev.sh`) - Easy setup script
- [x] **Enhanced Error Handling** - Better error messages and graceful degradation

### Available Commands Now
```bash
# Account commands
aws-cloud-utilities account info
aws-cloud-utilities account contact-info
aws-cloud-utilities account detect-control-tower --verbose
aws-cloud-utilities account regions
aws-cloud-utilities account validate

# Support commands  
aws-cloud-utilities support check-level
aws-cloud-utilities support severity-levels
aws-cloud-utilities support cases --status open
aws-cloud-utilities support services
```

**Status**: Support & Account Migration Complete ✅ - Ready for Next Service Migration
