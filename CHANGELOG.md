# Changelog

All notable changes to AWS Cloud Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

## [2.1.5] - 2026-08-05

### Fixed

- `cloudfront update-logging` treated every distribution as having logging
  disabled, because it read `DistributionConfig` off `list_distributions`
  results, where that key does not exist. Using `.get(..., {})` meant it saw an
  empty config rather than failing. On an account with 94 distributions it
  reported all 94 as needing logging enabled when 42 were already configured
  correctly; run for real it would have rewritten those 42 and given every
  distribution the same flat `--log-prefix` instead of the intended per-alias
  prefix. Logging state now comes from a `GetDistributionConfig` call per
  distribution, which is the only place it is available.
- `cloudfront list-distributions` failed with `KeyError: 'DistributionConfig'`
  for any account that has distributions. All variants were affected, including
  `--include-disabled` and `--show-logging-status`.
- `cloudfront invalidate <domain-name>` silently reported the distribution as not
  found. The same `KeyError` was swallowed by an enclosing handler that returns
  `None`. Passing a distribution ID was unaffected.

### Changed

- `list-distributions --show-logging-status` and `update-logging` now issue one
  additional API call per distribution, since `DistributionSummary` carries no
  logging configuration. Documented in the CloudFront command page, along with
  guidance to omit `--show-logging-status` when only the inventory is needed.

## [2.1.4] - 2026-08-05

### Fixed

- `waf list`, `waf stats`, and `waf troubleshoot` were completely non-functional,
  failing with `'dict' object has no attribute 'region'`. The module was the only
  one using `@click.pass_obj`, which passes the context dict where a `Config` was
  expected. `waf list` and `waf stats` also reported the failure but still exited
  0, so callers saw success.
- `security metrics` always failed with `object of type 'NoneType' has no len()`.
  `_collect_security_metrics` assembled its result but never returned it.
- `iam list-roles --max-items` was ignored and returned every role. `MaxItems` was
  sent as a service parameter, which botocore treats as a page size, and the
  paginator then walked every page.
- `s3 bucket-details --include-lifecycle` (and therefore `--include-all`) crashed
  on botocore 1.43+, which no longer exposes `NoSuchLifecycleConfiguration` on the
  S3 exception factory. Buckets with no lifecycle rules — the normal case — took
  down the whole command.
- Corrected the `Examples:` block in the CLI's root help, which referenced
  commands and options that do not exist.

### Changed

- The command reference in the docs is now generated from the Click command tree
  by `scripts/gen_docs.py` rather than maintained by hand. Validating the previous
  docs found 465 of 927 examples referenced commands or options that do not
  exist; `docs/commands/security.md` documented seven commands that were entirely
  invented while omitting all three real ones.
- `scripts/validate_docs.py` checks every documented example against the live CLI
  and runs in CI, so documentation cannot drift from the code again.
- Documented `billing cur-setup`, `s3 analyze-encryption`, `support
  trusted-advisor`, and the top-level `configure` and `info` commands, none of
  which previously appeared in the docs.
- The GitHub Pages workflow now uploads a build artifact and deploys it, matching
  the repository's `build_type: workflow` Pages configuration. It previously ran
  `mkdocs gh-deploy`, which pushes to a branch that Pages ignores in that mode, so
  the published site had been stale since 2025-07-25.

### Removed

- `slack-notify.sh` and `slack-notify.md`, along with all references to them.

## [2.1.3] - 2026-07-05

### Added

- Documented the PyPI publishing workflow, including GitHub trusted publishing,
  TestPyPI dry runs, production release creation, and post-release checks.
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
