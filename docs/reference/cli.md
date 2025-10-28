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
| `info` | Get AWS account information and summary |
| `contact-info` | Get AWS account contact information |
| `detect-control-tower` | Detect AWS Control Tower or Landing Zone |
| `regions` | List all available AWS regions |
| `service-regions` | List regions for a specific AWS service |
| `limits` | Get AWS service limits and usage quotas |
| `validate` | Validate AWS credentials and permissions |

### awsconfig
AWS Config service operations

```bash
aws-cloud-utilities awsconfig <command> [options]
```

| Command | Description |
|---------|-------------|
| `download` | Download AWS Config files from S3 and convert |
| `show-rules` | Show AWS Config rules with details |
| `list-rules` | List AWS Config rules |
| `compliance-status` | Show compliance status of resources |
| `compliance-checker` | Check compliance against rules |

### bedrock
Amazon Bedrock AI/ML operations

```bash
aws-cloud-utilities bedrock <command> [options]
```

| Command | Description |
|---------|-------------|
| `list-models` | List Amazon Bedrock foundation models |
| `model-details` | Get detailed information about a model |
| `list-custom-models` | List custom/fine-tuned models |
| `list-model-jobs` | List model training and customization jobs |
| `regions` | List regions where Bedrock is available |

### billing
AWS Billing & Cost Management

```bash
aws-cloud-utilities billing <command> [options]
```

| Command | Description |
|---------|-------------|
| `cur-list` | List existing Cost and Usage Reports |
| `cur-details` | Get detailed information about a CUR report |
| `cur-create` | Create a new Cost and Usage Report |
| `cur-delete` | Delete an existing Cost and Usage Report |
| `cur-validate-bucket` | Validate S3 bucket for CUR delivery |

### cloudformation
CloudFormation stack management

```bash
aws-cloud-utilities cloudformation <command> [options]
```

| Command | Description |
|---------|-------------|
| `backup` | Backup stacks and templates across regions |
| `list-stacks` | List CloudFormation stacks with status |
| `stack-details` | Get detailed information about a stack |

### cloudfront
CloudFront distribution management

```bash
aws-cloud-utilities cloudfront <command> [options]
```

| Command | Description |
|---------|-------------|
| `update-logging` | Enable logging and setup CloudWatch alarms |
| `list-distributions` | List CloudFront distributions |
| `distribution-details` | Get detailed distribution information |
| `invalidate` | Create cache invalidation |

### costops
Cost optimization and pricing tools

```bash
aws-cloud-utilities costops <command> [options]
```

| Command | Description |
|---------|-------------|
| `pricing` | Get AWS pricing information for services |
| `cost-analysis` | Analyze costs using Cost Explorer |
| `ebs-optimization` | Analyze EBS volume optimization |
| `usage-metrics` | Collect usage metrics from CloudWatch |
| `spot-pricing` | Get EC2 Spot instance pricing |
| `spot-analysis` | Analyze Spot instance savings |

### ecr
Elastic Container Registry operations

```bash
aws-cloud-utilities ecr <command> [options]
```

| Command | Description |
|---------|-------------|
| `copy-image` | Copy Docker image to AWS ECR |
| `list-repositories` | List all ECR repositories |
| `list-images` | List images in an ECR repository |
| `create-repository` | Create a new ECR repository |
| `delete-repository` | Delete an ECR repository |
| `get-login` | Get ECR login credentials |

### iam
IAM management and auditing

```bash
aws-cloud-utilities iam <command> [options]
```

| Command | Description |
|---------|-------------|
| `audit` | Audit IAM roles and policies, save locally |
| `list-roles` | List all IAM roles with details |
| `list-policies` | List IAM policies |
| `role-details` | Get detailed information about a role |
| `policy-details` | Get detailed information about a policy |

### inventory
Resource discovery and inventory

```bash
aws-cloud-utilities inventory <command> [options]
```

| Command | Description |
|---------|-------------|
| `scan` | Comprehensive resource inventory scan |
| `workspaces` | List WorkSpaces instances and configs |
| `services` | Discover available AWS services |
| `download-all` | Download all resource data in bulk |

### logs
CloudWatch logs management

```bash
aws-cloud-utilities logs <command> [options]
```

| Command | Description |
|---------|-------------|
| `list-groups` | List CloudWatch log groups with details |
| `download` | Download logs from CloudWatch |
| `set-retention` | Set or update log retention policies |
| `delete-group` | Delete log groups (with confirmation) |
| `combine` | Combine logs from multiple sources |
| `aggregate` | Aggregate logs from S3 (CloudTrail, etc.) |

### networking
Network utilities and analysis

```bash
aws-cloud-utilities networking <command> [options]
```

| Command | Description |
|---------|-------------|
| `ip-ranges` | Download and analyze AWS IP ranges |
| `ip-summary` | Show summary statistics of IP ranges |

### rds
RDS database management

```bash
aws-cloud-utilities rds <command> [options]
```

| Command | Description |
|---------|-------------|
| `troubleshoot-mysql` | Troubleshoot MySQL RDS connections |
| `list-instances` | List RDS instances with details |

### s3
S3 bucket operations

```bash
aws-cloud-utilities s3 <command> [options]
```

| Command | Description |
|---------|-------------|
| `list-buckets` | List S3 buckets with details |
| `create-bucket` | Create a new S3 bucket |
| `download` | Download objects from S3 buckets |
| `nuke-bucket` | Delete all objects and versions from bucket |
| `bucket-details` | Get detailed bucket configuration |
| `delete-versions` | Delete specific object versions |
| `restore-objects` | Restore objects from Glacier/Deep Archive |

### security
Security auditing and tools

```bash
aws-cloud-utilities security <command> [options]
```

| Command | Description |
|---------|-------------|
| `metrics` | Collect security metrics (WAF, GuardDuty, etc.) |
| `create-certificate` | Create SSL/TLS certificates in ACM |
| `list-certificates` | List SSL/TLS certificates |

### stepfunctions
Step Functions workflow management

```bash
aws-cloud-utilities stepfunctions <command> [options]
```

| Command | Description |
|---------|-------------|
| `list` | List all Step Functions state machines |
| `describe` | Get detailed information about state machine |
| `execute` | Execute a state machine |
| `list-executions` | List executions of a state machine |
| `logs` | View logs for state machine executions |

### support
AWS support tools

```bash
aws-cloud-utilities support <command> [options]
```

| Command | Description |
|---------|-------------|
| `check-level` | Check AWS support level |
| `severity-levels` | List available support severity levels |
| `cases` | List support cases |
| `services` | List services covered by support plan |

**Trusted Advisor Commands:**

| Command | Description |
|---------|-------------|
| `cost-savings` | Get Trusted Advisor cost optimization recommendations |

### waf
Web Application Firewall management

```bash
aws-cloud-utilities waf <command> [options]
```

| Command | Description |
|---------|-------------|
| `list` | List all Web ACLs (REGIONAL or CLOUDFRONT) |
| `stats` | Get CloudWatch metrics for Web ACLs |
| `troubleshoot` | Troubleshoot WAF blocks and issues |

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
