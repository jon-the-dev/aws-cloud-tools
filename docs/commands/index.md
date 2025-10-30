# Commands Overview

AWS Cloud Utilities v2 provides a comprehensive set of commands organized by AWS service and functionality. All commands follow a consistent pattern and support global options.

## Command Structure

```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

## Global Options

These options work with all commands:

| Option | Description | Default |
|--------|-------------|---------|
| `--profile` | AWS profile to use | `default` |
| `--region` | AWS region | `us-east-1` |
| `--output` | Output format (table, json, yaml, csv) | `table` |
| `--verbose` | Enable verbose output | `false` |
| `--debug` | Enable debug mode | `false` |
| `--config` | Configuration file path | `~/.aws-cloud-utilities.env` |

## Available Services

All 18 command groups with their complete subcommand list. Click any service name to see full documentation with examples and options.

### Core Services

| Service | Description | All Subcommands |
|---------|-------------|-----------------|
| [**account**](account.md) | Account information and management | `info`, `contact-info`, `detect-control-tower`, `regions`, `service-regions`, `limits`, `validate` (7 commands) |
| [**billing**](billing.md) | Billing and Cost & Usage Reports | `cur-list`, `cur-details`, `cur-create`, `cur-delete`, `cur-validate-bucket` (5 commands) |
| [**inventory**](inventory.md) | Resource discovery and inventory | `scan`, `workspaces`, `services`, `download-all` (4 commands) |
| [**security**](security.md) | Security auditing and tools | `metrics`, `create-certificate`, `list-certificates` (3 commands) |
| [**costops**](costops.md) | Cost optimization and pricing | `pricing`, `cost-analysis`, `ebs-optimization`, `usage-metrics`, `spot-pricing`, `spot-analysis` (6 commands) |

### AWS Service Management

| Service | Description | All Subcommands |
|---------|-------------|-----------------|
| [**awsconfig**](awsconfig.md) | AWS Config service operations | `download`, `show-rules`, `list-rules`, `compliance-status`, `compliance-checker` (5 commands) |
| [**bedrock**](bedrock.md) | Amazon Bedrock AI/ML operations | `list-models`, `model-details`, `list-custom-models`, `list-model-jobs`, `regions` (5 commands) |
| [**cloudformation**](cloudformation.md) | CloudFormation stack management | `backup`, `list-stacks`, `stack-details` (3 commands) |
| [**cloudfront**](cloudfront.md) | CloudFront distribution management | `update-logging`, `list-distributions`, `distribution-details`, `invalidate` (4 commands) |
| [**ecr**](ecr.md) | Elastic Container Registry operations | `copy-image`, `list-repositories`, `list-images`, `create-repository`, `delete-repository`, `get-login` (6 commands) |
| [**iam**](iam.md) | IAM management and auditing | `audit`, `list-roles`, `list-policies`, `role-details`, `policy-details` (5 commands) |
| [**logs**](logs.md) | CloudWatch logs management | `list-groups`, `download`, `set-retention`, `delete-group`, `combine`, `aggregate` (6 commands) |
| [**networking**](networking.md) | Network utilities and analysis | `ip-ranges`, `ip-summary` (2 commands) |
| [**rds**](rds.md) | RDS database management | `troubleshoot-mysql`, `list-instances` (2 commands) |
| [**s3**](s3.md) | S3 bucket operations | `list-buckets`, `create-bucket`, `download`, `nuke-bucket`, `bucket-details`, `delete-versions`, `restore-objects` (7 commands) |
| [**stepfunctions**](stepfunctions.md) | Step Functions workflow management | `list`, `describe`, `execute`, `list-executions`, `logs` (5 commands) |
| [**support**](support.md) | AWS support tools | `check-level`, `severity-levels`, `cases`, `services`, `cost-savings` (5 commands) |
| [**waf**](waf.md) | Web Application Firewall management | `list`, `stats`, `troubleshoot` (3 commands) |

**Total: 18 services, 80+ commands**

## Common Usage Patterns

### Getting Help

```bash
# General help
aws-cloud-utilities --help

# Service help
aws-cloud-utilities account --help

# Command help
aws-cloud-utilities account info --help
```

### Output Formats

```bash
# Default table format
aws-cloud-utilities account info

# JSON output
aws-cloud-utilities account info --output json

# YAML output
aws-cloud-utilities account info --output yaml

# CSV output (for tabular data)
aws-cloud-utilities inventory resources --output csv
```

### Using Profiles and Regions

```bash
# Specific profile
aws-cloud-utilities --profile production account info

# Specific region
aws-cloud-utilities --region eu-west-1 inventory resources

# Both profile and region
aws-cloud-utilities --profile staging --region us-west-2 security audit
```

### Verbose and Debug Output

```bash
# Verbose output
aws-cloud-utilities --verbose account info

# Debug mode
aws-cloud-utilities --debug security audit

# Both verbose and debug
aws-cloud-utilities --verbose --debug logs aggregate --log-group /aws/lambda/my-function
```

## Quick Reference

### Most Used Commands

```bash
# Account information
aws-cloud-utilities account info

# Resource inventory
aws-cloud-utilities inventory scan --all-regions

# Security metrics
aws-cloud-utilities security metrics

# Cost analysis
aws-cloud-utilities costops cost-analysis

# Log management
aws-cloud-utilities logs list-groups
```

### Multi-Region Operations

```bash
# All regions
aws-cloud-utilities inventory scan --all-regions

# Specific regions
aws-cloud-utilities inventory scan --regions us-east-1,us-west-2,eu-west-1

# Region-specific analysis
aws-cloud-utilities --region us-east-1 security metrics
```

### Filtering and Searching

```bash
# Filter by service
aws-cloud-utilities inventory scan --services ec2,s3,rds

# Filter by tag
aws-cloud-utilities costops ebs-optimization --tag-key Environment --tag-value production

# Download logs with filter
aws-cloud-utilities logs download /aws/lambda/my-function --filter-pattern "ERROR"
```

## Command Categories

### Information Gathering

- `account info` - Basic account information
- `account contact-info` - Contact details
- `inventory scan` - Resource inventory
- `support check-level` - Support plan information

### Security & Compliance

- `security metrics` - Collect security metrics
- `security create-certificate` - Create SSL/TLS certificates
- `iam audit` - IAM audit and backup
- `waf list` - List WAF Web ACLs

### Cost Management

- `costops pricing` - Service pricing information
- `costops cost-analysis` - Cost analysis
- `costops spot-analysis` - Spot instance savings
- `billing cur-list` - Cost and Usage Reports

### Operational Tasks

- `logs aggregate` - Aggregate S3 logs
- `logs download` - Download CloudWatch logs
- `rds list-instances` - RDS management
- `stepfunctions list` - List state machines

### Troubleshooting

- `logs download` - Download and analyze logs
- `support cases` - Support case management
- `rds troubleshoot-mysql` - Database troubleshooting
- `waf troubleshoot` - WAF troubleshooting

## Best Practices

### 1. Use Profiles for Different Environments

```bash
# Development
aws-cloud-utilities --profile dev account info

# Production
aws-cloud-utilities --profile prod security audit
```

### 2. Save Output for Analysis

```bash
# Save inventory for analysis
aws-cloud-utilities inventory scan --output-file inventory.json

# Save IAM audit results
aws-cloud-utilities iam audit --output-dir ./iam-audit-$(date +%Y%m%d)
```

### 3. Use Verbose Mode for Troubleshooting

```bash
# Debug connection issues
aws-cloud-utilities --verbose --debug account info

# Understand what's happening
aws-cloud-utilities --verbose inventory scan --all-regions
```

### 4. Combine Commands for Workflows

```bash
#!/bin/bash
# Daily security and compliance check
TIMESTAMP=$(date +%Y%m%d)

# Security metrics
aws-cloud-utilities security metrics --output json > daily-security-${TIMESTAMP}.json

# IAM audit
aws-cloud-utilities iam audit --output-dir ./iam-audit-${TIMESTAMP}

# Resource inventory
aws-cloud-utilities inventory scan --all-regions --output-file inventory-${TIMESTAMP}.json

# Cost analysis
aws-cloud-utilities costops cost-analysis --output-file costs-${TIMESTAMP}.json
```

## Error Handling

All commands provide clear error messages and suggestions:

```bash
# Permission errors show required permissions
aws-cloud-utilities security metrics

# Configuration errors show how to fix
aws-cloud-utilities --profile nonexistent account info

# Service errors provide context
aws-cloud-utilities logs download /nonexistent/group
```

## Next Steps

- Choose a service from the list above to explore specific commands
- See [Examples](../examples/common-use-cases.md) for real-world usage patterns
- Check [Configuration](../getting-started/configuration.md) for setup options
