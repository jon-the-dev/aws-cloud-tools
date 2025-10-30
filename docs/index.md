# AWS Cloud Utilities v2

A unified command-line toolkit for AWS operations with enhanced functionality. This package consolidates various AWS management scripts into a single, powerful CLI tool.

## ✨ Features

- **🎯 Unified CLI**: Single command interface for all AWS operations
- **⚡ Parallel Processing**: Multi-threaded operations for improved performance  
- **🎨 Rich Output**: Beautiful, formatted output with tables and colors
- **⚙️ Flexible Configuration**: Support for AWS profiles, regions, and custom settings
- **📊 Comprehensive Coverage**: Tools for cost optimization, inventory, security, logs, and more
- **🔒 Security First**: Built-in security auditing and best practices
- **📈 Cost Optimization**: Advanced cost analysis and optimization tools

## 🚀 Quick Start

```bash
# Install from PyPI (when published)
pip install aws-cloud-utilities

# Install from source
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools/v2
pip install -e .
```

### Basic Usage

```bash
# Get account information
aws-cloud-utilities account info

# Scan all resources in your account
aws-cloud-utilities inventory scan --all-regions

# Analyze EBS volumes for cost savings
aws-cloud-utilities costops ebs-optimization --all-regions

# Collect spot pricing data
aws-cloud-utilities costops spot-pricing --all-regions

# Download CloudWatch logs
aws-cloud-utilities logs download /aws/lambda/my-function

# Get security metrics
aws-cloud-utilities security metrics
```

## 🏗️ Command Structure

The CLI follows a hierarchical structure similar to the AWS CLI:

```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

### Available Services

Click on any service name to see full documentation for all subcommands.

| Service | Description | Subcommands |
|---------|-------------|-------------|
| [**account**](commands/account.md) | Account information and management | `info`, `contact-info`, `detect-control-tower`, `regions`, `service-regions`, `limits`, `validate` |
| [**awsconfig**](commands/awsconfig.md) | AWS Config service operations | `download`, `show-rules`, `list-rules`, `compliance-status`, `compliance-checker` |
| [**bedrock**](commands/bedrock.md) | Amazon Bedrock AI/ML operations | `list-models`, `model-details`, `list-custom-models`, `list-model-jobs`, `regions` |
| [**billing**](commands/billing.md) | Billing and cost analysis | `cur-list`, `cur-details`, `cur-create`, `cur-delete`, `cur-validate-bucket` |
| [**cloudformation**](commands/cloudformation.md) | CloudFormation stack management | `backup`, `list-stacks`, `stack-details` |
| [**cloudfront**](commands/cloudfront.md) | CloudFront distribution management | `update-logging`, `list-distributions`, `distribution-details`, `invalidate` |
| [**costops**](commands/costops.md) | Cost optimization and pricing tools | `pricing`, `cost-analysis`, `ebs-optimization`, `usage-metrics`, `spot-pricing`, `spot-analysis` |
| [**ecr**](commands/ecr.md) | Elastic Container Registry operations | `copy-image`, `list-repositories`, `list-images`, `create-repository`, `delete-repository`, `get-login` |
| [**iam**](commands/iam.md) | IAM management and auditing | `audit`, `list-roles`, `list-policies`, `role-details`, `policy-details` |
| [**inventory**](commands/inventory.md) | Resource discovery and inventory | `scan`, `workspaces`, `services`, `download-all` |
| [**logs**](commands/logs.md) | CloudWatch logs management | `list-groups`, `download`, `set-retention`, `delete-group`, `combine`, `aggregate` |
| [**networking**](commands/networking.md) | Network utilities and analysis | `ip-ranges`, `ip-summary` |
| [**rds**](commands/rds.md) | RDS database management | `troubleshoot-mysql`, `list-instances` |
| [**s3**](commands/s3.md) | S3 bucket operations | `list-buckets`, `create-bucket`, `download`, `nuke-bucket`, `bucket-details`, `delete-versions`, `restore-objects` |
| [**security**](commands/security.md) | Security auditing and tools | `metrics`, `create-certificate`, `list-certificates` |
| [**stepfunctions**](commands/stepfunctions.md) | Step Functions workflow management | `list`, `describe`, `execute`, `list-executions`, `logs` |
| [**support**](commands/support.md) | AWS support tools | `check-level`, `severity-levels`, `cases`, `services`, `cost-savings` |
| [**waf**](commands/waf.md) | Web Application Firewall management | `list`, `stats`, `troubleshoot` |

### Global Options

- `--profile`: AWS profile to use
- `--region`: AWS region
- `--output`: Output format (json, yaml, table, csv)
- `--verbose`: Enable verbose logging
- `--debug`: Enable debug mode

## 🎯 Key Improvements from v1

### Enhanced User Experience
- **Rich Console Output**: Beautiful tables, colors, and progress indicators
- **Multiple Output Formats**: JSON, YAML, table, and CSV support
- **Better Error Handling**: Clear error messages with actionable guidance
- **Unified Interface**: Single command instead of multiple scripts

### Performance & Reliability
- **Parallel Processing**: Multi-threaded operations with configurable workers
- **Graceful Degradation**: Works with limited permissions
- **Robust Error Handling**: Proper exception handling and recovery
- **Modern Python**: Type hints, proper packaging, comprehensive testing

### Advanced Features
- **Configuration Management**: Environment variables and config file support
- **Flexible Authentication**: Multiple AWS profile and region support
- **Extensible Architecture**: Plugin-ready design for future enhancements
- **Comprehensive Testing**: Unit tests, integration tests, and CI/CD

## 📚 Documentation

- [Installation Guide](getting-started/installation.md) - Get up and running quickly
- [Configuration](getting-started/configuration.md) - Configure AWS profiles and settings
- [Command Reference](commands/index.md) - Complete command documentation
- [Examples](examples/common-use-cases.md) - Real-world usage examples
- [Migration Guide](getting-started/migration.md) - Migrate from v1 scripts

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](development/contributing.md) for details on:

- Setting up the development environment
- Running tests
- Code style guidelines
- Submitting pull requests

## 📄 License

MIT License - see [LICENSE](https://github.com/jon-the-dev/aws-cloud-tools/blob/main/LICENSE) file for details.

## 🆘 Support

- [GitHub Issues](https://github.com/jon-the-dev/aws-cloud-tools/issues) - Bug reports and feature requests
- [Documentation](https://jon-the-dev.github.io/aws-cloud-tools/) - Complete documentation
- [Examples](examples/common-use-cases.md) - Usage examples and tutorials

---

*AWS Cloud Utilities v2 - Making AWS management simple, powerful, and efficient.*
