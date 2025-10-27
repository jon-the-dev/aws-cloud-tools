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

### Core Services

| Service | Description | Key Commands |
|---------|-------------|--------------|
| [**account**](account.md) | Account information and management | `info`, `contact-info`, `detect-control-tower`, `regions`, `limits` |
| [**billing**](billing.md) | Billing and cost analysis | `cur-list`, `cur-create`, `cur-details`, `cur-validate-bucket` |
| [**inventory**](inventory.md) | Resource discovery and inventory | `scan`, `workspaces`, `services`, `download-all` |
| [**security**](security.md) | Security auditing and tools | `metrics`, `create-certificate`, `list-certificates` |
| [**costops**](costops.md) | Cost optimization and pricing | `pricing`, `cost-analysis`, `spot-pricing`, `ebs-optimization` |

### AWS Services

| Service | Description | Key Commands |
|---------|-------------|--------------|
| [**awsconfig**](awsconfig.md) | AWS Config service operations | `download`, `show-rules`, `list-rules`, `compliance-status` |
| [**bedrock**](bedrock.md) | Amazon Bedrock AI/ML operations | `list-models`, `model-details`, `list-custom-models`, `regions` |
| [**cloudformation**](cloudformation.md) | CloudFormation stack management | `backup`, `list-stacks`, `stack-details` |
| [**cloudfront**](cloudfront.md) | CloudFront distribution management | `update-logging`, `list-distributions`, `distribution-details`, `invalidate` |
| [**ecr**](ecr.md) | Elastic Container Registry operations | `copy-image`, `list-repositories`, `list-images`, `create-repository` |
| [**iam**](iam.md) | IAM management and auditing | `audit`, `list-roles`, `list-policies`, `role-details`, `policy-details` |
| [**logs**](logs.md) | CloudWatch logs management | `list-groups`, `download`, `set-retention`, `aggregate`, `combine` |
| [**networking**](networking.md) | Network utilities and analysis | `ip-ranges`, `ip-summary` |
| [**rds**](rds.md) | RDS database management | `troubleshoot-mysql`, `list-instances` |
| [**s3**](s3.md) | S3 bucket operations | `list-buckets`, `create-bucket`, `download`, `nuke-bucket`, `bucket-details` |
| [**stepfunctions**](stepfunctions.md) | Step Functions workflow management | `list`, `describe`, `execute`, `list-executions`, `logs` |
| [**support**](support.md) | AWS support tools | `check-level`, `cases`, `services`, `cost-savings` |
| [**waf**](waf.md) | Web Application Firewall management | `list`, `stats`, `troubleshoot` |

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
aws-cloud-utilities inventory scan --services ec2

# Filter by tag
aws-cloud-utilities inventory scan --include-tags

# Download logs
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
aws-cloud-utilities security metrics --output json > daily-security-$(date +%Y%m%d).json
aws-cloud-utilities iam audit --output-dir ./iam-audit-$(date +%Y%m%d)
aws-cloud-utilities inventory scan --all-regions --output-file inventory-$(date +%Y%m%d).json
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
