# AWS Cloud Utilities v2 - Testing Guide

This document describes the comprehensive test suite for AWS Cloud Utilities v2, covering all non-destructive functions across all migrated commands.

## Overview

The test suite validates all read-only operations including:
- Resource listing and inventory
- Cost analysis and optimization recommendations
- Security assessments
- Configuration analysis
- Help system functionality

## Test Structure

### Test Categories

1. **Help Commands** - CLI help system validation
2. **Account Operations** - Account information and metadata
3. **CloudFront Operations** - Distribution and origin analysis
4. **CloudWatch Logs Operations** - Log group management
5. **S3 Operations** - Bucket listing and analysis
6. **Cost Optimization Operations** - Pricing and cost analysis
7. **IAM Operations** - Identity and access management
8. **Inventory Operations** - Resource discovery
9. **Networking Operations** - Network resource analysis
10. **Security Operations** - Security group analysis
11. **Support Operations** - Support level verification

### Test Types

- **Unit Tests**: Individual command validation
- **Integration Tests**: Multi-service workflow validation
- **Help Tests**: CLI help system validation
- **Output Tests**: File output and format validation

## Running Tests

### Quick Start

```bash
# Run all tests with default settings
python test_comprehensive.py

# Run tests with specific AWS profile and region
python test_comprehensive.py --profile dev --region us-west-2

# Dry run to see what would be tested
python test_comprehensive.py --dry-run

# Verbose output for debugging
python test_comprehensive.py --verbose
```

### Using the Test Runner Script

```bash
# Run all tests
./run_tests.sh

# Run with specific configuration
./run_tests.sh --profile dev --region us-west-2 --verbose

# Quick tests only (skip slow operations)
./run_tests.sh --quick

# CI mode with structured output
./run_tests.sh --ci --output-dir ./ci_results

# Dry run mode
./run_tests.sh --dry-run
```

### Test Configuration

The test suite can be configured using `test_config.yaml`:

```yaml
# Enable/disable test categories
test_categories:
  help_commands: true
  account_operations: true
  cloudfront_operations: true
  # ... other categories

# Specific test configurations
tests:
  costops:
    cost_analysis:
      months: 1  # Short period for testing
  inventory:
    resources:
      service_limit: 5  # Limit services for faster testing
```

## Test Requirements

### AWS Credentials

Most tests require valid AWS credentials. The test suite will:
- Automatically detect available credentials
- Skip AWS-dependent tests if credentials are unavailable
- Run help-only tests without credentials

### Permissions

The test suite requires read-only permissions for:
- Account information (`sts:GetCallerIdentity`)
- CloudFront (`cloudfront:List*`)
- CloudWatch Logs (`logs:Describe*`)
- S3 (`s3:ListAllMyBuckets`, `s3:GetBucketLocation`)
- Cost Explorer (`ce:Get*`)
- IAM (`iam:List*`)
- EC2 (`ec2:Describe*`)
- Support (`support:DescribeServices`)

### Python Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

## Test Output

### Console Output

```
🧪 AWS Cloud Utilities v2 - Comprehensive Test Suite
============================================================

Testing Help Commands...
✅ Help Commands: 11/11 tests passed

Testing Account Operations...
✅ Account Operations: 2/2 tests passed

...

============================================================
📊 Test Summary
============================================================
Total Tests: 35
Passed: 35
Failed: 0
Success Rate: 100.0%
Duration: 45.23 seconds
```

### JSON Output

```json
{
  "total_tests": 35,
  "passed_tests": 35,
  "failed_tests": 0,
  "success_rate": 100.0,
  "duration": 45.23,
  "results": {
    "Help Commands": {
      "main_help": true,
      "account_help": true,
      ...
    },
    ...
  },
  "failures": []
}
```

### HTML Report

When `jq` is available, an HTML report is automatically generated with:
- Visual test metrics
- Detailed results breakdown
- Failure analysis
- Test execution timeline

## CI/CD Integration

### GitHub Actions

The test suite includes a GitHub Actions workflow (`.github/workflows/test.yml`) that:
- Runs tests on multiple Python versions (3.9-3.12)
- Tests across multiple AWS regions
- Generates test reports and artifacts
- Performs security scanning and linting

### Environment Variables

```bash
# AWS credentials (optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Test configuration
TEST_REGION=us-east-1
TEST_PROFILE=default
TEST_VERBOSE=false
```

## Test Development

### Adding New Tests

1. **Add test method to appropriate category**:
```python
def test_new_operation(self) -> Dict[str, bool]:
    tests = {}
    
    result = self.run_cli_command(["service", "new-command"])
    tests["new_operation"] = result["success"]
    
    return tests
```

2. **Update test configuration**:
```yaml
tests:
  service:
    new_operation:
      enabled: true
      parameters: ["--param", "value"]
```

3. **Add to test runner**:
```python
test_categories.append(("New Operations", self.test_new_operation))
```

### Test Best Practices

- **Non-Destructive Only**: Only test read-only operations
- **Timeout Handling**: All tests have 5-minute timeout
- **Error Handling**: Graceful handling of missing credentials
- **Resource Cleanup**: Automatic cleanup of test artifacts
- **Parallel Safety**: Tests can run in parallel safely

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   - Configure AWS credentials via `aws configure`
   - Set environment variables
   - Use `--profile` parameter

2. **Permission Denied**
   - Ensure IAM user/role has required read permissions
   - Check AWS region availability

3. **Timeout Errors**
   - Increase timeout in test configuration
   - Check network connectivity
   - Verify AWS service availability

4. **Import Errors**
   - Install package in development mode: `pip install -e .`
   - Check Python path configuration

### Debug Mode

```bash
# Enable verbose logging
python test_comprehensive.py --verbose

# Run specific test category only
python test_comprehensive.py --dry-run | grep "Testing Account"

# Check AWS connectivity
aws sts get-caller-identity
```

## Performance Considerations

### Test Execution Time

- **Help Tests**: ~1 second
- **Account Tests**: ~5 seconds
- **Service Tests**: ~10-30 seconds each
- **Full Suite**: ~2-5 minutes (depending on AWS response times)

### Optimization Strategies

- **Parallel Execution**: Tests run sequentially by default for stability
- **Region Limiting**: Use single region for faster testing
- **Service Filtering**: Limit inventory operations to specific services
- **Caching**: Results cached where appropriate

## Security Considerations

### Data Handling

- **No Sensitive Data**: Tests don't access or store sensitive information
- **Read-Only Operations**: All operations are non-destructive
- **Temporary Files**: Test artifacts cleaned up automatically
- **Credential Safety**: Credentials never logged or stored

### Network Security

- **HTTPS Only**: All AWS API calls use HTTPS
- **No External Dependencies**: Tests only interact with AWS APIs
- **Timeout Protection**: All operations have timeout limits

## Reporting Issues

When reporting test failures, include:

1. **Test Output**: Full console output or JSON results
2. **Environment**: Python version, OS, AWS region
3. **Configuration**: Test parameters and AWS profile used
4. **Error Details**: Specific error messages and stack traces

Example issue template:
```
**Test Failure Report**

Environment:
- Python: 3.11
- OS: Ubuntu 22.04
- Region: us-east-1
- Profile: default

Command:
```bash
python test_comprehensive.py --verbose
```

Output:
```
[paste test output here]
```

Expected: All tests should pass
Actual: 2 tests failed with permission errors
```

## Future Enhancements

### Planned Features

- **Performance Benchmarking**: Track test execution times
- **Coverage Reporting**: Command coverage analysis
- **Load Testing**: High-volume operation testing
- **Mock Testing**: Offline testing capabilities
- **Custom Test Suites**: User-defined test combinations

### Integration Opportunities

- **AWS Config Rules**: Compliance testing integration
- **AWS Well-Architected**: Best practices validation
- **Cost Optimization**: Automated recommendations testing
- **Security Scanning**: Enhanced security validation
