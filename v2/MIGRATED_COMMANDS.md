# Migrated Commands Reference

This document shows the mapping between original v1 scripts and the new v2 unified CLI commands.

## Support Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `support/aws_check_support.py` | `aws-cloud-utilities support check-level` | Check AWS support level |
| `support/aws_check_support2.py` | `aws-cloud-utilities support check-level --method api` | Check support via API (fallback to severity) |

### New Enhanced Commands

```bash
# Check support level (primary method)
aws-cloud-utilities support check-level

# List available severity levels
aws-cloud-utilities support severity-levels

# List support cases
aws-cloud-utilities support cases --status open
aws-cloud-utilities support cases --status resolved --max-results 50

# List services available for support
aws-cloud-utilities support services
```

## Account Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `account/aws_get_acct_info.py` | `aws-cloud-utilities account contact-info` | Get account contact information |
| `account/detect_control_tower.py` | `aws-cloud-utilities account detect-control-tower` | Detect Control Tower/Landing Zone |

### Enhanced Account Commands

```bash
# Basic account information (enhanced from v1)
aws-cloud-utilities account info

# Get contact information (migrated)
aws-cloud-utilities account contact-info

# Detect Control Tower/Landing Zone (migrated with improvements)
aws-cloud-utilities account detect-control-tower
aws-cloud-utilities account detect-control-tower --verbose

# Additional account utilities (new in v2)
aws-cloud-utilities account regions
aws-cloud-utilities account service-regions --service lambda
aws-cloud-utilities account limits
aws-cloud-utilities account validate
```

## Key Improvements in v2

### Enhanced Error Handling
- Graceful degradation when permissions are limited
- Clear error messages with actionable guidance
- Proper handling of Basic vs Premium support plans

### Better Output Formatting
- Rich console output with colors and tables
- Multiple output formats: table, json, yaml, csv
- Progress indicators for long-running operations

### Parallel Processing
- Control Tower detection now scans all regions in parallel
- Configurable worker threads (default: 4)
- Progress bars for multi-region operations

### Configuration Management
- Global options: `--profile`, `--region`, `--output`, `--verbose`
- Environment variable support
- Configuration file support (.env)

## Migration Benefits

1. **Unified Interface**: Single command instead of multiple scripts
2. **Better UX**: Rich output, progress indicators, help system
3. **Enhanced Functionality**: More options and better error handling
4. **Consistent Patterns**: Same CLI patterns across all services
5. **Modern Python**: Type hints, proper packaging, testing

## Installation & Testing

```bash
# Install in development mode
cd v2
./install_dev.sh

# Test the migration
python test_migration.py

# Try the commands
aws-cloud-utilities --help
aws-cloud-utilities account info
aws-cloud-utilities support check-level
```

## Bedrock Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `bedrock/bedrock_models.py` | `aws-cloud-utilities bedrock list-models` | List Bedrock foundation models |

### New Enhanced Commands

```bash
# List all foundation models across regions (migrated with enhancements)
aws-cloud-utilities bedrock list-models

# List models from specific region
aws-cloud-utilities bedrock list-models --region us-east-1

# Filter by provider
aws-cloud-utilities bedrock list-models --provider anthropic

# Save results to file with account ID and timestamp
aws-cloud-utilities bedrock list-models --output-file bedrock_models.csv

# Get detailed information about a specific model
aws-cloud-utilities bedrock model-details anthropic.claude-3-sonnet-20240229-v1:0

# List custom models
aws-cloud-utilities bedrock list-custom-models

# List model customization jobs
aws-cloud-utilities bedrock list-model-jobs --status Completed

# List available Bedrock regions
aws-cloud-utilities bedrock regions
```

## IAM Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `iam/iam_auditor.py` | `aws-cloud-utilities iam audit` | Audit IAM roles and policies |

### New Enhanced Commands

```bash
# Enhanced migration of original functionality
aws-cloud-utilities iam audit
aws-cloud-utilities iam audit --output-dir ./my_audit
aws-cloud-utilities iam audit --include-aws-managed
aws-cloud-utilities iam audit --roles-only
aws-cloud-utilities iam audit --policies-only
aws-cloud-utilities iam audit --format yaml

# New functionality not in original
aws-cloud-utilities iam list-roles
aws-cloud-utilities iam list-roles --path-prefix /service-role/
aws-cloud-utilities iam list-policies --scope Local
aws-cloud-utilities iam list-policies --only-attached
aws-cloud-utilities iam role-details MyRole
aws-cloud-utilities iam policy-details arn:aws:iam::123456789012:policy/MyPolicy
```

## Inventory Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `inventory/inventory.py` | `aws-cloud-utilities inventory scan` | Comprehensive AWS resource discovery |
| `inventory/workspaces_inventory.py` | `aws-cloud-utilities inventory workspaces` | WorkSpaces inventory with metrics |

### New Enhanced Commands

```bash
# Enhanced migration of comprehensive inventory
aws-cloud-utilities inventory scan
aws-cloud-utilities inventory scan --services ec2,s3,rds
aws-cloud-utilities inventory scan --regions us-east-1,us-west-2
aws-cloud-utilities inventory scan --include-tags --format yaml
aws-cloud-utilities inventory scan --output-dir ./my_inventory

# Enhanced WorkSpaces inventory (migrated with improvements)
aws-cloud-utilities inventory workspaces
aws-cloud-utilities inventory workspaces --region us-east-1
aws-cloud-utilities inventory workspaces --include-metrics --lookback-days 30
aws-cloud-utilities inventory workspaces --output-file workspaces_report.csv
aws-cloud-utilities inventory workspaces --metric-names "Available,InSessionLatency"

# New functionality not in original
aws-cloud-utilities inventory services  # List all supported services
```

## CloudFormation & Networking Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `cloudformation/backup_stacks.py` | `aws-cloud-utilities cloudformation backup` | Dedicated CloudFormation stack backup |
| `networking/get_aws_ip_ranges.py` | `aws-cloud-utilities networking ip-ranges` | Download and analyze AWS IP ranges |

### New Enhanced Commands

```bash
# Dedicated CloudFormation commands (NEW STRUCTURE!)
aws-cloud-utilities cloudformation backup
aws-cloud-utilities cloudformation backup --regions us-east-1,us-west-2
aws-cloud-utilities cloudformation backup --output-dir ./cfn_backups
aws-cloud-utilities cloudformation backup --stack-status CREATE_COMPLETE,UPDATE_COMPLETE
aws-cloud-utilities cloudformation backup --parallel-regions 8 --parallel-stacks 4 --format yaml

# New CloudFormation management commands
aws-cloud-utilities cloudformation list-stacks
aws-cloud-utilities cloudformation list-stacks --all-regions
aws-cloud-utilities cloudformation list-stacks --stack-status CREATE_COMPLETE
aws-cloud-utilities cloudformation stack-details MyStack --region us-east-1
aws-cloud-utilities cloudformation stack-details MyStack --show-template --show-parameters

# Comprehensive inventory with optional CloudFormation backup
aws-cloud-utilities inventory download-all
aws-cloud-utilities inventory download-all --include-cloudformation
aws-cloud-utilities inventory download-all --include-workspaces-metrics
aws-cloud-utilities inventory download-all --services ec2,s3,rds --regions us-east-1

# Enhanced AWS IP ranges (migrated with major improvements)
aws-cloud-utilities networking ip-ranges
aws-cloud-utilities networking ip-ranges --filter-service EC2
aws-cloud-utilities networking ip-ranges --filter-region us-east-1
aws-cloud-utilities networking ip-ranges --ipv6 --output-file ip_ranges.json
aws-cloud-utilities networking ip-ranges --show-summary

# New networking functionality not in original
aws-cloud-utilities networking ip-summary
aws-cloud-utilities networking ip-summary --service S3
aws-cloud-utilities networking ip-summary --region eu-west-1
```

### Key Architectural Improvements

#### **Dedicated CloudFormation Commands**
- **Standalone Module**: CloudFormation now has its own dedicated command group
- **Enhanced Backup**: Multiple output formats (JSON, YAML) with comprehensive options
- **Stack Management**: List stacks, get details, show templates and parameters
- **Rich Interface**: Progress indicators, detailed summaries, and error handling

#### **Reorganized Inventory Structure**
- **Focused Scanning**: `inventory scan` for resource discovery only
- **Comprehensive Download**: `inventory download-all` for everything including optional CloudFormation
- **Modular Approach**: Choose what to include (tags, CloudFormation, WorkSpaces metrics)
- **Better Organization**: Structured output with separate directories for different data types

## Security & Step Functions Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `security/aws_get_sec_metrics.py` | `aws-cloud-utilities security metrics` | Security metrics from WAF, GuardDuty, Security Hub |
| `security/acm_create_cert.py` | `aws-cloud-utilities security create-certificate` | ACM certificate creation with Route53 validation |
| `step-functions/aws_step_manage.py` | `aws-cloud-utilities stepfunctions *` | Complete Step Functions management suite |

### New Enhanced Commands

```bash
# Enhanced security metrics collection (migrated with major improvements)
aws-cloud-utilities security metrics
aws-cloud-utilities security metrics --all-regions --time-range 48
aws-cloud-utilities security metrics --services waf,guardduty --region us-east-1
aws-cloud-utilities security metrics --output-file security_report.json

# Enhanced ACM certificate management (migrated with improvements)
aws-cloud-utilities security create-certificate example.com
aws-cloud-utilities security create-certificate example.com --alt-names www.example.com,api.example.com
aws-cloud-utilities security create-certificate example.com --wait-for-validation --timeout 600
aws-cloud-utilities security create-certificate example.com --hosted-zone-id Z123456789

# New security functionality not in original
aws-cloud-utilities security list-certificates
aws-cloud-utilities security list-certificates --all-regions --status ISSUED

# Enhanced Step Functions management (migrated with major improvements)
aws-cloud-utilities stepfunctions list
aws-cloud-utilities stepfunctions list --all-regions --output-file state_machines.csv
aws-cloud-utilities stepfunctions describe arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine
aws-cloud-utilities stepfunctions describe arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --show-definition

# Enhanced execution management (migrated with improvements)
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine
aws-cloud-utilities stepfunctions execute arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --input '{"key":"value"}' --wait
aws-cloud-utilities stepfunctions list-executions arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --status FAILED
aws-cloud-utilities stepfunctions logs arn:aws:states:us-east-1:123456789012:execution:MyExecution /aws/stepfunctions/MyStateMachine
```

### Key Security Enhancements

#### **Multi-Service Security Metrics**
- **Comprehensive Collection**: WAF, GuardDuty, and Security Hub metrics in one command
- **Multi-Region Support**: Collect metrics across all regions simultaneously
- **Flexible Filtering**: Choose specific services and time ranges
- **Rich Output**: Multiple formats with detailed summaries and error handling

#### **Enhanced Certificate Management**
- **Automated Validation**: Route53 DNS validation with hosted zone auto-detection
- **Wait for Completion**: Optional waiting for certificate validation
- **Rich Interface**: Progress indicators and detailed status reporting
- **Certificate Listing**: New functionality to list and filter certificates

### Key Step Functions Enhancements

#### **Complete Management Suite**
- **Enhanced Listing**: Multi-region support with detailed information
- **Rich Descriptions**: State machine details with optional definition display
- **Execution Management**: Start, monitor, and list executions with comprehensive options
- **Log Integration**: CloudWatch logs retrieval with structured output

#### **Improved User Experience**
- **Progress Indicators**: Visual feedback for long-running operations
- **Multiple Formats**: JSON, YAML, CSV output with automatic timestamping
- **Error Handling**: Comprehensive error recovery and detailed reporting
- **Rich CLI Interface**: Extensive help system and intuitive commands

## ECR (Elastic Container Registry) Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `ecr/download_and_push_docker_image_to_ecr.py` | `aws-cloud-utilities ecr copy-image` | Copy Docker images to ECR with enhancements |

### New Enhanced Commands

```bash
# Enhanced image copying (migrated with major improvements)
aws-cloud-utilities ecr copy-image ubuntu:latest my-app
aws-cloud-utilities ecr copy-image nginx:alpine my-nginx --tag v1.0
aws-cloud-utilities ecr copy-image my-image:latest my-repo --create-repo --force
aws-cloud-utilities ecr copy-image docker.io/library/redis:latest my-redis --region us-west-2

# New ECR management functionality not in original
aws-cloud-utilities ecr list-repositories
aws-cloud-utilities ecr list-repositories --all-regions --output-file repos.csv
aws-cloud-utilities ecr list-images my-repository
aws-cloud-utilities ecr list-images my-repository --max-results 50 --output-file images.json

# Repository management (new functionality)
aws-cloud-utilities ecr create-repository my-new-repo
aws-cloud-utilities ecr create-repository my-secure-repo --scan-on-push --image-tag-mutability IMMUTABLE
aws-cloud-utilities ecr delete-repository old-repo --force --confirm

# Authentication helpers (enhanced)
aws-cloud-utilities ecr get-login
aws-cloud-utilities ecr get-login --print-command --region us-east-1
```

### Key ECR Enhancements

#### **Enhanced Image Copying**
- **Progress Indicators**: Visual feedback for pull, tag, and push operations
- **Smart Repository Handling**: Auto-create repositories with --create-repo flag
- **Conflict Resolution**: Force overwrite existing images with --force flag
- **Rich Error Handling**: Detailed error messages and recovery suggestions
- **Image Details**: Automatic display of pushed image metadata

#### **Comprehensive Repository Management**
- **Multi-Region Listing**: List repositories across all regions simultaneously
- **Detailed Information**: Repository URIs, creation dates, encryption settings
- **Image Inventory**: List images with tags, sizes, and scan results
- **Repository Lifecycle**: Create and delete repositories with comprehensive options

#### **Enhanced Authentication**
- **Simplified Login**: Direct Docker authentication with ECR
- **Command Generation**: Print login commands for manual execution
- **Multi-Region Support**: Login to ECR in any AWS region
- **Error Recovery**: Fallback to manual commands when Docker unavailable

## Next Services to Migrate

1. **CostOps** - Cost optimization tools
2. **Logs** - CloudWatch logs management
3. **S3** - S3 operations
