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

# List all resources in your account
aws-cloud-utilities inventory resources

# Find cheapest GPU spot instances
aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge

# Aggregate CloudWatch logs
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function

# Security audit
aws-cloud-utilities security blue-team-audit
```

## 🏗️ Command Structure

The CLI follows a hierarchical structure similar to the AWS CLI:

```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

### Available Services

| Service | Description |
|---------|-------------|
| **account** | Account information and management |
| **awsconfig** | AWS Config service operations |
| **bedrock** | Amazon Bedrock AI/ML operations |
| **cloudformation** | CloudFormation stack management |
| **cloudfront** | CloudFront distribution management |
| **costops** | Cost optimization and pricing tools |
| **ecr** | Elastic Container Registry operations |
| **iam** | IAM management and auditing |
| **inventory** | Resource discovery and inventory |
| **logs** | CloudWatch logs management |
| **networking** | Network utilities and analysis |
| **s3** | S3 bucket operations |
| **security** | Security auditing and tools |
| **stepfunctions** | Step Functions workflow management |
| **support** | AWS support tools |

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
