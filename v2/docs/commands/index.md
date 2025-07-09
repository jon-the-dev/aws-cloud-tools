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
| [**account**](account.md) | Account information and management | `info`, `contact-info`, `regions`, `limits` |
| [**inventory**](inventory.md) | Resource discovery and inventory | `resources`, `unused-resources`, `health-check` |
| [**security**](security.md) | Security auditing and tools | `audit`, `blue-team-audit`, `public-resources` |
| [**costops**](costops.md) | Cost optimization and pricing | `pricing`, `analyze`, `recommendations`, `gpu-spots` |

### AWS Services

| Service | Description | Key Commands |
|---------|-------------|--------------|
| [**iam**](iam.md) | IAM management and auditing | `analyze`, `unused-permissions`, `policy-simulator` |
| [**s3**](s3.md) | S3 bucket operations | `list-buckets`, `analyze-costs`, `security-audit` |
| [**logs**](logs.md) | CloudWatch logs management | `groups`, `aggregate`, `search`, `export` |
| [**networking**](networking.md) | Network utilities and analysis | `security-groups`, `vpc-analysis`, `connectivity` |

### Advanced Services

| Service | Description | Key Commands |
|---------|-------------|--------------|
| [**awsconfig**](awsconfig.md) | AWS Config service operations | `rules`, `compliance`, `remediation` |
| [**bedrock**](bedrock.md) | Amazon Bedrock AI/ML operations | `models`, `inference`, `fine-tuning` |
| [**cloudformation**](cloudformation.md) | CloudFormation stack management | `stacks`, `drift-detection`, `template-analysis` |
| [**cloudfront**](cloudfront.md) | CloudFront distribution management | `distributions`, `cache-analysis`, `security` |
| [**ecr**](ecr.md) | Elastic Container Registry operations | `repositories`, `images`, `security-scan` |
| [**stepfunctions**](stepfunctions.md) | Step Functions workflow management | `state-machines`, `executions`, `analysis` |
| [**support**](support.md) | AWS support tools | `check-level`, `cases`, `services` |

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
aws-cloud-utilities inventory resources

# Security audit
aws-cloud-utilities security audit

# Cost analysis
aws-cloud-utilities costops analyze

# Log analysis
aws-cloud-utilities logs groups
```

### Multi-Region Operations

```bash
# All regions
aws-cloud-utilities inventory resources --all-regions

# Specific regions
aws-cloud-utilities inventory resources --regions us-east-1,us-west-2,eu-west-1

# Region-specific analysis
aws-cloud-utilities --region us-east-1 security audit
```

### Filtering and Searching

```bash
# Filter by service
aws-cloud-utilities inventory resources --service ec2

# Filter by tag
aws-cloud-utilities inventory resources --tag Environment=Production

# Search logs
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "ERROR"
```

## Command Categories

### Information Gathering

- `account info` - Basic account information
- `account contact-info` - Contact details
- `inventory resources` - Resource inventory
- `support check-level` - Support plan information

### Security & Compliance

- `security audit` - Basic security audit
- `security blue-team-audit` - Comprehensive security assessment
- `iam analyze` - IAM analysis
- `awsconfig compliance` - Compliance status

### Cost Management

- `costops pricing` - Service pricing information
- `costops analyze` - Cost analysis
- `costops recommendations` - Cost optimization suggestions
- `inventory unused-resources` - Find unused resources

### Operational Tasks

- `logs aggregate` - Log aggregation
- `logs search` - Log searching
- `cloudformation stacks` - Stack management
- `s3 security-audit` - S3 security review

### Troubleshooting

- `networking connectivity` - Network connectivity tests
- `logs search` - Error log analysis
- `support cases` - Support case management
- `inventory health-check` - Resource health status

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
aws-cloud-utilities inventory resources --output json > inventory.json

# Save security audit results
aws-cloud-utilities security audit --output yaml > security-audit.yaml
```

### 3. Use Verbose Mode for Troubleshooting

```bash
# Debug connection issues
aws-cloud-utilities --verbose --debug account info

# Understand what's happening
aws-cloud-utilities --verbose inventory resources
```

### 4. Combine Commands for Workflows

```bash
#!/bin/bash
# Daily security check
aws-cloud-utilities security audit --output json > daily-security-$(date +%Y%m%d).json
aws-cloud-utilities iam analyze --output json > daily-iam-$(date +%Y%m%d).json
aws-cloud-utilities inventory unused-resources --output json > unused-resources-$(date +%Y%m%d).json
```

## Error Handling

All commands provide clear error messages and suggestions:

```bash
# Permission errors show required permissions
aws-cloud-utilities security audit

# Configuration errors show how to fix
aws-cloud-utilities --profile nonexistent account info

# Service errors provide context
aws-cloud-utilities logs aggregate --log-group /nonexistent/group
```

## Next Steps

- Choose a service from the list above to explore specific commands
- See [Examples](../examples/common-use-cases.md) for real-world usage patterns
- Check [Configuration](../getting-started/configuration.md) for setup options
