# CLI Reference

Complete command-line interface reference for AWS Cloud Utilities v2.

## Global Options

These options are available for all commands:

| Option | Short | Environment Variable | Default | Description |
|--------|-------|---------------------|---------|-------------|
| `--profile` | `-p` | `AWS_PROFILE` | `default` | AWS profile to use |
| `--region` | `-r` | `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |
| `--output` | `-o` | `AWS_OUTPUT_FORMAT` | `table` | Output format |
| `--verbose` | `-v` | `VERBOSE` | `false` | Enable verbose output |
| `--debug` | `-d` | `DEBUG` | `false` | Enable debug mode |
| `--config` | `-c` | `CONFIG_FILE` | `~/.aws-cloud-utilities.env` | Configuration file |
| `--version` | | | | Show version and exit |
| `--help` | `-h` | | | Show help and exit |

## Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `table` | Rich formatted tables | Human-readable output |
| `json` | JSON format | Automation and scripting |
| `yaml` | YAML format | Configuration files |
| `csv` | CSV format | Spreadsheet import |

## Command Structure

```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

## Services and Commands

### account
Account information and management

```bash
aws-cloud-utilities account <command> [options]
```

| Command | Description |
|---------|-------------|
| `info` | Get AWS account information |
| `contact-info` | Get account contact information |
| `regions` | List available AWS regions |
| `detect-control-tower` | Detect Control Tower deployment |
| `limits` | Show service limits |
| `validate` | Validate account configuration |

### awsconfig
AWS Config service operations

```bash
aws-cloud-utilities awsconfig <command> [options]
```

| Command | Description |
|---------|-------------|
| `rules` | List Config rules |
| `compliance` | Check compliance status |
| `remediation` | Manage remediation actions |

### bedrock
Amazon Bedrock AI/ML operations

```bash
aws-cloud-utilities bedrock <command> [options]
```

| Command | Description |
|---------|-------------|
| `models` | List available models |
| `inference` | Run inference |
| `fine-tuning` | Manage fine-tuning jobs |

### cloudformation
CloudFormation stack management

```bash
aws-cloud-utilities cloudformation <command> [options]
```

| Command | Description |
|---------|-------------|
| `stacks` | List CloudFormation stacks |
| `drift-detection` | Detect stack drift |
| `template-analysis` | Analyze templates |

### cloudfront
CloudFront distribution management

```bash
aws-cloud-utilities cloudfront <command> [options]
```

| Command | Description |
|---------|-------------|
| `distributions` | List distributions |
| `cache-analysis` | Analyze cache performance |
| `security` | Security configuration audit |

### costops
Cost optimization and pricing tools

```bash
aws-cloud-utilities costops <command> [options]
```

| Command | Description |
|---------|-------------|
| `pricing` | Get service pricing |
| `gpu-spots` | Find GPU spot prices |
| `analyze` | Analyze current costs |
| `recommendations` | Get optimization recommendations |
| `savings-plans` | Analyze Savings Plans |
| `rightsizing` | Get rightsizing recommendations |
| `reserved-instances` | Analyze Reserved Instances |

### ecr
Elastic Container Registry operations

```bash
aws-cloud-utilities ecr <command> [options]
```

| Command | Description |
|---------|-------------|
| `repositories` | List ECR repositories |
| `images` | Manage container images |
| `security-scan` | Security vulnerability scanning |

### iam
IAM management and auditing

```bash
aws-cloud-utilities iam <command> [options]
```

| Command | Description |
|---------|-------------|
| `analyze` | Analyze IAM configuration |
| `unused-permissions` | Find unused permissions |
| `policy-simulator` | Simulate IAM policies |

### inventory
Resource discovery and inventory

```bash
aws-cloud-utilities inventory <command> [options]
```

| Command | Description |
|---------|-------------|
| `resources` | List all resources |
| `unused-resources` | Find unused resources |
| `health-check` | Check resource health |
| `tagging-audit` | Audit resource tagging |
| `cost-analysis` | Analyze resource costs |
| `compliance-check` | Check compliance |
| `resource-map` | Generate resource map |

### logs
CloudWatch logs management

```bash
aws-cloud-utilities logs <command> [options]
```

| Command | Description |
|---------|-------------|
| `groups` | List log groups |
| `aggregate` | Aggregate log data |
| `search` | Search log entries |
| `export` | Export log data |

### networking
Network utilities and analysis

```bash
aws-cloud-utilities networking <command> [options]
```

| Command | Description |
|---------|-------------|
| `security-groups` | Analyze security groups |
| `vpc-analysis` | VPC configuration analysis |
| `connectivity` | Test network connectivity |

### s3
S3 bucket operations

```bash
aws-cloud-utilities s3 <command> [options]
```

| Command | Description |
|---------|-------------|
| `list-buckets` | List S3 buckets |
| `analyze-costs` | Analyze S3 costs |
| `security-audit` | S3 security audit |

### security
Security auditing and tools

```bash
aws-cloud-utilities security <command> [options]
```

| Command | Description |
|---------|-------------|
| `audit` | Basic security audit |
| `blue-team-audit` | Comprehensive security audit |
| `public-resources` | Find public resources |
| `compliance` | Compliance checking |
| `encryption-status` | Check encryption status |
| `network-analysis` | Network security analysis |
| `secrets-scan` | Scan for exposed secrets |

### stepfunctions
Step Functions workflow management

```bash
aws-cloud-utilities stepfunctions <command> [options]
```

| Command | Description |
|---------|-------------|
| `state-machines` | List state machines |
| `executions` | Manage executions |
| `analysis` | Analyze workflows |

### support
AWS support tools

```bash
aws-cloud-utilities support <command> [options]
```

| Command | Description |
|---------|-------------|
| `check-level` | Check support level |
| `cases` | Manage support cases |
| `services` | List support services |
| `severity-levels` | List severity levels |

## Common Option Patterns

### Filtering Options

Many commands support filtering:

```bash
--service SERVICE          # Filter by AWS service
--region REGION           # Filter by region
--tag KEY=VALUE          # Filter by tag
--resource-type TYPE     # Filter by resource type
--status STATUS          # Filter by status
```

### Time-based Options

Commands dealing with time-based data:

```bash
--start-time TIME        # Start time for analysis
--end-time TIME         # End time for analysis
--age-threshold DAYS    # Age threshold in days
--lookback-period DAYS  # Lookback period
```

### Output Control Options

Control output behavior:

```bash
--max-results NUMBER     # Maximum number of results
--sort-by FIELD         # Sort results by field
--ascending             # Sort in ascending order
--descending            # Sort in descending order
--include-details       # Include detailed information
--summary-only          # Show summary only
```

## Environment Variables

All CLI options can be set via environment variables:

```bash
# AWS Configuration
export AWS_PROFILE=production
export AWS_DEFAULT_REGION=us-west-2
export AWS_OUTPUT_FORMAT=json

# Tool Configuration
export VERBOSE=true
export DEBUG=false
export WORKERS=8
export CONFIG_FILE=/path/to/config.env

# Logging
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/aws-cloud-utilities.log
```

## Configuration File

Create `~/.aws-cloud-utilities.env`:

```env
# AWS Settings
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
AWS_OUTPUT_FORMAT=table

# Performance
WORKERS=4
TIMEOUT=30
RETRY_ATTEMPTS=3

# Logging
LOG_LEVEL=INFO
VERBOSE=false
DEBUG=false

# Output
SHOW_PROGRESS=true
COLOR_OUTPUT=true
TABLE_MAX_WIDTH=120
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | AWS authentication error |
| 4 | AWS permission error |
| 5 | Resource not found |
| 6 | Invalid input |

## Examples

### Basic Usage

```bash
# Get account information
aws-cloud-utilities account info

# List resources with specific output format
aws-cloud-utilities inventory resources --output json

# Security audit with verbose output
aws-cloud-utilities --verbose security audit
```

### Advanced Usage

```bash
# Multi-region resource inventory
aws-cloud-utilities inventory resources --all-regions --output csv > resources.csv

# Cost optimization for specific service
aws-cloud-utilities costops analyze --service ec2 --start-date 2024-01-01

# Security audit with specific profile and region
aws-cloud-utilities --profile prod --region us-west-2 security blue-team-audit
```

### Automation Examples

```bash
# Daily security check
aws-cloud-utilities security audit --severity high --output json > security-$(date +%Y%m%d).json

# Weekly cost analysis
aws-cloud-utilities costops analyze --group-by service --output yaml > weekly-costs.yaml

# Resource health monitoring
aws-cloud-utilities inventory health-check --unhealthy-only --output table
```

## Help System

### Getting Help

```bash
# General help
aws-cloud-utilities --help

# Service help
aws-cloud-utilities account --help

# Command help
aws-cloud-utilities account info --help

# Show version
aws-cloud-utilities --version
```

### Help Output Format

Help output includes:

- Command description
- Usage syntax
- Available options
- Examples
- Related commands

## Debugging

### Debug Mode

Enable debug mode for troubleshooting:

```bash
aws-cloud-utilities --debug account info
```

Debug mode shows:
- Configuration loading
- AWS API calls
- Error stack traces
- Performance timing

### Verbose Mode

Enable verbose output for detailed information:

```bash
aws-cloud-utilities --verbose inventory resources
```

Verbose mode shows:
- Progress indicators
- Detailed status messages
- Resource processing information
- Summary statistics
