# Changelog

All notable changes to AWS Cloud Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-07-08

### Added

- Initial v2 release with unified CLI interface
- Core infrastructure with configuration management
- AWS authentication and session management
- Rich console output with tables and colors
- Account management commands
- Modular command structure for all AWS services
- Comprehensive error handling and logging
- Configuration file support with .env files
- Global options for profile, region, output format
- Parallel processing capabilities
- Type hints throughout codebase
- Comprehensive documentation

### Changed

- Complete rewrite from individual scripts to unified package
- Modern Python packaging with pyproject.toml
- Click-based CLI instead of argparse
- Rich output formatting instead of plain text
- Pydantic-based configuration management
- Structured logging with configurable levels

### Migration from v1

- All original script functionality preserved
- New unified command structure: `aws-cloud-utilities <service> <operation>`
- Configuration now centralized in .env files
- Enhanced error handling and user feedback
- Improved performance with parallel processing

## [1.x] - Legacy Scripts

- Individual Python scripts for various AWS operations
- Basic argparse-based CLI interfaces
- Direct boto3 usage without abstraction
- Manual configuration management
