# Quick Start

Get up and running with AWS Cloud Utilities v2 in minutes.

## First Steps

### 1. Install the Tool

```bash
# From source (current method)
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools/v2
pip install -e .
```

### 2. Verify Installation

```bash
aws-cloud-utilities --version
```

### 3. Check Your AWS Connection

```bash
aws-cloud-utilities account info
```

This command will show your AWS account details and verify your credentials are working.

## Essential Commands

### Account Information

```bash
# Basic account info
aws-cloud-utilities account info

# Contact information
aws-cloud-utilities account contact-info

# Available regions
aws-cloud-utilities account regions

# Service limits
aws-cloud-utilities account limits
```

### Resource Inventory

```bash
# List all resources
aws-cloud-utilities inventory resources

# Resources in specific region
aws-cloud-utilities inventory resources --region us-west-2

# Filter by service
aws-cloud-utilities inventory resources --service ec2

# Export to JSON
aws-cloud-utilities inventory resources --output json > resources.json
```

### Cost Optimization

```bash
# Get pricing for EC2 instances
aws-cloud-utilities costops pricing --service ec2

# Find cheapest spot instances
aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge

# Cost analysis
aws-cloud-utilities costops analyze

# Savings recommendations
aws-cloud-utilities costops recommendations
```

### Security Auditing

```bash
# Basic security audit
aws-cloud-utilities security audit

# Blue team security assessment
aws-cloud-utilities security blue-team-audit

# Check for public resources
aws-cloud-utilities security public-resources

# IAM analysis
aws-cloud-utilities iam analyze
```

### Log Management

```bash
# List log groups
aws-cloud-utilities logs groups

# Aggregate logs from a group
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function

# Search logs
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "ERROR"

# Export logs
aws-cloud-utilities logs export --log-group /aws/lambda/my-function --start-time "2024-01-01"
```

## Common Workflows

### 1. New Account Setup Audit

```bash
# Get account overview
aws-cloud-utilities account info
aws-cloud-utilities account contact-info

# Security baseline check
aws-cloud-utilities security audit
aws-cloud-utilities iam analyze

# Resource inventory
aws-cloud-utilities inventory resources
```

### 2. Cost Optimization Review

```bash
# Current resource inventory
aws-cloud-utilities inventory resources --output json > current-resources.json

# Cost analysis
aws-cloud-utilities costops analyze

# Find optimization opportunities
aws-cloud-utilities costops recommendations

# Check for unused resources
aws-cloud-utilities inventory unused-resources
```

### 3. Security Assessment

```bash
# Comprehensive security audit
aws-cloud-utilities security blue-team-audit

# Check for public resources
aws-cloud-utilities security public-resources

# IAM permissions analysis
aws-cloud-utilities iam analyze
aws-cloud-utilities iam unused-permissions

# Network security
aws-cloud-utilities networking security-groups
```

### 4. Troubleshooting Issues

```bash
# Check CloudWatch logs
aws-cloud-utilities logs groups
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "ERROR"

# Resource health check
aws-cloud-utilities inventory health-check

# Support case management
aws-cloud-utilities support cases --status open
```

## Output Formats

All commands support multiple output formats:

```bash
# Table format (default)
aws-cloud-utilities account info

# JSON format
aws-cloud-utilities account info --output json

# YAML format
aws-cloud-utilities account info --output yaml

# CSV format (for tabular data)
aws-cloud-utilities inventory resources --output csv
```

## Global Options

Use these options with any command:

```bash
# Specify AWS profile
aws-cloud-utilities --profile production account info

# Specify region
aws-cloud-utilities --region eu-west-1 inventory resources

# Verbose output
aws-cloud-utilities --verbose security audit

# Debug mode
aws-cloud-utilities --debug logs aggregate --log-group /aws/lambda/my-function
```

## Configuration

Create a configuration file for default settings:

```bash
# Interactive configuration
aws-cloud-utilities configure
```

Or create `~/.aws-cloud-utilities.env`:

```env
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
AWS_OUTPUT_FORMAT=table
WORKERS=4
```

## Getting Help

```bash
# General help
aws-cloud-utilities --help

# Service-specific help
aws-cloud-utilities account --help

# Command-specific help
aws-cloud-utilities account info --help
```

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Command Reference](../commands/index.md) - Complete command documentation
- [Examples](../examples/common-use-cases.md) - Real-world usage examples
- [Migration Guide](migration.md) - Migrate from v1 scripts
