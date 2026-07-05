# AWS Cloud Utilities v2

[![CI](https://github.com/jon-the-dev/aws-cloud-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/jon-the-dev/aws-cloud-tools/actions/workflows/ci.yml) [![Security Checks](https://github.com/jon-the-dev/aws-cloud-tools/actions/workflows/security-checks.yml/badge.svg)](https://github.com/jon-the-dev/aws-cloud-tools/actions/workflows/security-checks.yml) ![PyPI](https://img.shields.io/pypi/v/aws-cloud-utilities) ![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white) ![pipenv](https://img.shields.io/badge/pipenv-3776AB?logo=python&logoColor=white) ![License](https://img.shields.io/github/license/jon-the-dev/aws-cloud-tools) ![Issues](https://img.shields.io/github/issues/jon-the-dev/aws-cloud-tools) ![Last Commit](https://img.shields.io/github/last-commit/jon-the-dev/aws-cloud-tools)

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
- **HTML Report Generation**: Create comprehensive, responsive HTML reports for analysis and auditing
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

# Inventory all resources in your account
aws-cloud-utilities inventory scan

# Provision a Cost and Usage Report data source end-to-end
aws-cloud-utilities billing cur-setup --bucket my-cur-bucket

# Find the cheapest spot instances
aws-cloud-utilities costops spot-analysis

# Troubleshoot MySQL RDS connection issues
aws-cloud-utilities rds troubleshoot-mysql my-mysql-db

# Aggregate CloudWatch logs
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function

# Collect security metrics (WAF, GuardDuty, Security Hub)
aws-cloud-utilities security metrics

# Analyze S3 encryption (generates HTML report)
aws-cloud-utilities s3 analyze-encryption --workers 20
```

## Command Structure

The CLI follows a hierarchical structure similar to the AWS CLI:

```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

### Global Options

- `--profile`: AWS profile to use
- `--region`: AWS region
- `--output`: Output format (json, yaml, table)
- `--verbose`: Enable verbose logging
- `--debug`: Enable debug mode

## Command Index

Every command group and its operations. Invoke as
`aws-cloud-utilities <group> <command> [OPTIONS]`.

| Group | Purpose |
|-------|---------|
| [`account`](#account) | Account information and management |
| [`awsconfig`](#awsconfig) | AWS Config compliance monitoring |
| [`bedrock`](#bedrock) | Amazon Bedrock model management |
| [`billing`](#billing) | Billing and Cost & Usage Report (CUR) management |
| [`cloudformation`](#cloudformation) | CloudFormation management and backup |
| [`cloudfront`](#cloudfront) | CloudFront distribution management |
| [`costops`](#costops) | Cost optimization and pricing analysis |
| [`dynamodb`](#dynamodb) | DynamoDB cost and capacity analysis |
| [`ecr`](#ecr) | Elastic Container Registry management |
| [`iam`](#iam) | IAM management and auditing |
| [`inventory`](#inventory) | Resource discovery and inventory |
| [`logs`](#logs) | CloudWatch Logs management and processing |
| [`networking`](#networking) | Networking and IP-range utilities |
| [`rds`](#rds) | RDS management and troubleshooting |
| [`s3`](#s3) | S3 bucket and object management |
| [`security`](#security) | Security monitoring and certificates |
| [`stepfunctions`](#stepfunctions) | Step Functions management and monitoring |
| [`trusted-advisor`](#trusted-advisor) | Trusted Advisor and AWS support tools |
| [`waf`](#waf) | WAF management and troubleshooting |

### account

- `info` — Get AWS account information
- `contact-info` — Get AWS account contact information
- `detect-control-tower` — Detect AWS Control Tower or Landing Zone deployments
- `regions` — List all available AWS regions
- `service-regions` — List available regions for a specific AWS service
- `limits` — Get AWS service limits and usage
- `validate` — Validate AWS credentials and permissions

### awsconfig

- `download` — Download and process AWS Config files from S3 into CSV or JSON
- `show-rules` — Show AWS Config rules with compliance metrics
- `list-rules` — List AWS Config rules with basic information
- `compliance-status` — Compliance status summary across rules and resources
- `compliance-checker` — Comprehensive compliance checker for various resource types

### bedrock

- `list-models` — List Amazon Bedrock foundation models across regions
- `model-details` — Get detailed information about a specific Bedrock model
- `list-custom-models` — List custom Bedrock models
- `list-model-jobs` — List Bedrock model customization jobs
- `regions` — List regions where Amazon Bedrock is available

### billing

- `cur-setup` — Provision an end-to-end CUR data source: bucket, policy, and Parquet report **(new)**
- `cur-list` — List all existing Cost and Usage Reports
- `cur-details` — Show detailed configuration for a specific CUR report
- `cur-create` — Create a new Cost and Usage Report (CUR 2.0)
- `cur-delete` — Delete a Cost and Usage Report
- `cur-validate-bucket` — Validate S3 bucket permissions for CUR delivery

### cloudformation

- `backup` — Backup CloudFormation stacks and templates across regions
- `list-stacks` — List CloudFormation stacks with details
- `stack-details` — Get detailed information about a specific stack

### cloudfront

- `update-logging` — Enable logging on distributions and optionally set up alarms
- `list-distributions` — List CloudFront distributions with configuration details
- `distribution-details` — Get detailed information about a specific distribution
- `invalidate` — Invalidate distribution cache by domain name or distribution ID

### costops

- `pricing` — Get AWS pricing information for services
- `cost-analysis` — Analyze AWS costs using Cost Explorer
- `ebs-optimization` — Analyze EBS volumes for cost optimization opportunities
- `usage-metrics` — Get detailed usage metrics for a specific AWS service
- `spot-pricing` — Collect and analyze EC2 spot pricing across regions
- `spot-analysis` — Analyze collected spot pricing to find cheapest options

### dynamodb

- `cost-analysis` — Analyze DynamoDB tables for capacity usage and estimated monthly cost

### ecr

- `copy-image` — Copy a Docker image from any registry to AWS ECR
- `list-repositories` — List ECR repositories with details
- `list-images` — List images in an ECR repository
- `create-repository` — Create a new ECR repository
- `delete-repository` — Delete an ECR repository
- `get-login` — Get Docker login command for ECR or execute login directly

### iam

- `audit` — Audit IAM roles and policies, saving them locally
- `list-roles` — List IAM roles with details
- `list-policies` — List IAM policies
- `role-details` — Get detailed information about a specific IAM role
- `policy-details` — Get detailed information about a specific IAM policy

### inventory

- `scan` — Comprehensive AWS resource inventory scan across services and regions
- `workspaces` — Generate a WorkSpaces inventory report with optional metrics
- `services` — List all supported services for inventory scanning
- `download-all` — Download comprehensive inventory of all AWS resources

### logs

- `list-groups` — List CloudWatch log groups with details
- `download` — Download logs for a specific log group or all groups
- `set-retention` — Set retention policy for a log group
- `delete-group` — Delete a CloudWatch log group
- `combine` — Combine multiple log files into a single sorted file
- `aggregate` — Aggregate log files into larger files for efficient processing

### networking

- `ip-ranges` — Download and analyze AWS IP ranges
- `ip-summary` — Show summary statistics of AWS IP ranges

### rds

- `troubleshoot-mysql` — Troubleshoot MySQL RDS connection issues
- `list-instances` — List RDS instances in the current region

### s3

- `list-buckets` — List S3 buckets with region and optional size information
- `create-bucket` — Create a new S3 bucket with optional configuration
- `download` — Download objects from a bucket with parallel processing
- `nuke-bucket` — Completely delete a bucket and all its contents (including versions)
- `bucket-details` — Get comprehensive details about a bucket
- `delete-versions` — Delete object versions from a bucket
- `restore-objects` — Restore objects from Glacier or other archive classes
- `analyze-encryption` — Analyze bucket encryption configurations (parallel)

### security

- `metrics` — Collect security metrics from WAF, GuardDuty, and Security Hub
- `create-certificate` — Create an ACM certificate with Route53 DNS validation
- `list-certificates` — List ACM certificates with details

### stepfunctions

- `list` — List all Step Functions state machines
- `describe` — Get detailed information about a state machine
- `execute` — Start an execution of a state machine
- `list-executions` — List executions of a state machine
- `logs` — Show CloudWatch logs for an execution

### trusted-advisor

- `check-level` — Check AWS support level using different methods
- `severity-levels` — List available support severity levels
- `cases` — List AWS support cases
- `services` — List AWS services available for support cases
- `cost-savings` — Analyze Trusted Advisor cost optimization opportunities

### waf

- `list` — List all Web ACLs in the account
- `stats` — Get comprehensive WAF statistics for troubleshooting
- `troubleshoot` — Generate a comprehensive WAF troubleshooting report

## Configuration

Create a `.env` file in your project directory or home directory:

```env
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
AWS_OUTPUT_FORMAT=table
WORKERS=4
```

## CI/CD Integration

### Slack Notifications

The repository includes a `slack-notify.sh` script for sending notifications to Slack channels from CI/CD pipelines.

**Quick Start:**
```bash
# Set your Slack webhook URL
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Send a simple message
./slack-notify.sh "Build completed successfully"

# Send with styling
./slack-notify.sh "Deployment finished!" \
    --emoji ":rocket:" \
    --color "good" \
    --title "Production Deployment"
```

**Features:**
- Simple command-line interface
- Customizable emojis, colors, and formatting
- Support for success/warning/error color schemes
- Works with all major CI/CD platforms (GitHub Actions, GitLab CI, Jenkins, CircleCI)

For complete documentation, see [slack-notify.md](slack-notify.md).

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
