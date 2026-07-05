# Changelog

All notable changes to AWS Cloud Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `billing cur-setup` command: provisions an end-to-end Cost and Usage Report
  data source in one step — creates and configures the delivery S3 bucket
  (public-access block, AES256 encryption, lifecycle policy, and the
  billing-service bucket policy) and registers a Parquet CUR report definition
  with resource IDs. Mirrors the reference Terraform module.
- `--dry-run` support for `cur-setup` to preview the plan without creating any
  resources, plus idempotent detection of existing buckets and report
  definitions.

## [2.1.2] - 2025-08-18

### Added

- Fixed pyyaml dependency for pypi

## [2.1.0] - 2025-01-19

### Added

- CloudFront cache invalidation command
- Support for invalidating specific paths or entire distributions
- Configurable invalidation options and batch processing

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
