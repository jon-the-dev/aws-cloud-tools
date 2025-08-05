# AWS Config Commands

AWS Config service operations for compliance monitoring, configuration management, and rule evaluation.

## Commands

### `download`

Download AWS Config configuration snapshots and history.

```bash
aws-cloud-utilities awsconfig download
```

**Options:**
- `--region REGION` - AWS region to download from (default: all regions)
- `--output-dir DIR` - Directory to save downloaded files (default: ./config-download)
- `--resource-type TYPE` - Filter by specific resource type
- `--start-time TIME` - Start time for configuration history (ISO format)
- `--end-time TIME` - End time for configuration history (ISO format)
- `--include-snapshots` - Include configuration snapshots
- `--include-history` - Include configuration history

**Examples:**
```bash
# Download all Config data
aws-cloud-utilities awsconfig download

# Download from specific region
aws-cloud-utilities awsconfig download --region us-east-1

# Download specific resource type
aws-cloud-utilities awsconfig download --resource-type AWS::EC2::Instance

# Download with time range
aws-cloud-utilities awsconfig download --start-time 2024-01-01T00:00:00Z --end-time 2024-01-31T23:59:59Z
```

### `show-rules`

Display detailed information about AWS Config rules.

```bash
aws-cloud-utilities awsconfig show-rules
```

**Options:**
- `--region REGION` - AWS region to query (default: all regions)
- `--rule-name NAME` - Show specific rule details
- `--compliance-status STATUS` - Filter by compliance status (COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE)
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Show all rules
aws-cloud-utilities awsconfig show-rules

# Show specific rule
aws-cloud-utilities awsconfig show-rules --rule-name s3-bucket-public-access-prohibited

# Filter by compliance status
aws-cloud-utilities awsconfig show-rules --compliance-status NON_COMPLIANT

# Save to file
aws-cloud-utilities awsconfig show-rules --output-file config-rules.json
```

### `list-rules`

List AWS Config rules with summary information.

```bash
aws-cloud-utilities awsconfig list-rules
```

**Options:**
- `--region REGION` - AWS region to query (default: all regions)
- `--rule-type TYPE` - Filter by rule type (AWS_MANAGED, CUSTOM_LAMBDA, CUSTOM_POLICY)
- `--compliance-status STATUS` - Filter by compliance status
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all rules
aws-cloud-utilities awsconfig list-rules

# List only AWS managed rules
aws-cloud-utilities awsconfig list-rules --rule-type AWS_MANAGED

# List non-compliant rules
aws-cloud-utilities awsconfig list-rules --compliance-status NON_COMPLIANT
```

### `compliance-status`

Get compliance status for resources and rules.

```bash
aws-cloud-utilities awsconfig compliance-status
```

**Options:**
- `--region REGION` - AWS region to query (default: all regions)
- `--resource-type TYPE` - Filter by resource type
- `--resource-id ID` - Check specific resource
- `--rule-name NAME` - Check specific rule
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Get overall compliance status
aws-cloud-utilities awsconfig compliance-status

# Check specific resource type
aws-cloud-utilities awsconfig compliance-status --resource-type AWS::S3::Bucket

# Check specific resource
aws-cloud-utilities awsconfig compliance-status --resource-id my-bucket-name

# Check specific rule
aws-cloud-utilities awsconfig compliance-status --rule-name s3-bucket-ssl-requests-only
```

### `compliance-checker`

Run comprehensive compliance checks across your AWS environment.

```bash
aws-cloud-utilities awsconfig compliance-checker
```

**Options:**
- `--region REGION` - AWS region to check (default: all regions)
- `--framework FRAMEWORK` - Check against specific compliance framework
- `--severity LEVEL` - Filter by severity level (HIGH, MEDIUM, LOW)
- `--output-file FILE` - Save results to file
- `--detailed` - Include detailed findings and remediation guidance

**Examples:**
```bash
# Run comprehensive compliance check
aws-cloud-utilities awsconfig compliance-checker

# Check specific framework
aws-cloud-utilities awsconfig compliance-checker --framework CIS

# High severity issues only
aws-cloud-utilities awsconfig compliance-checker --severity HIGH

# Detailed report with remediation
aws-cloud-utilities awsconfig compliance-checker --detailed --output-file compliance-report.json
```

## Global Options

All AWS Config commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Compliance Monitoring Workflow

```bash
#!/bin/bash
# Daily compliance monitoring

echo "=== Config Rules Status ==="
aws-cloud-utilities awsconfig list-rules --compliance-status NON_COMPLIANT

echo "=== Detailed Rule Analysis ==="
aws-cloud-utilities awsconfig show-rules --compliance-status NON_COMPLIANT --output-file non-compliant-rules.json

echo "=== Compliance Check ==="
aws-cloud-utilities awsconfig compliance-checker --severity HIGH --output-file compliance-issues.json
```

### Configuration Audit

```bash
#!/bin/bash
# Comprehensive configuration audit

AUDIT_DIR="./config-audit-$(date +%Y%m%d)"
mkdir -p $AUDIT_DIR

echo "=== Downloading Configuration Data ==="
aws-cloud-utilities awsconfig download --output-dir $AUDIT_DIR --include-snapshots --include-history

echo "=== Rules Analysis ==="
aws-cloud-utilities awsconfig show-rules --output-file $AUDIT_DIR/rules-analysis.json

echo "=== Compliance Status ==="
aws-cloud-utilities awsconfig compliance-status --output-file $AUDIT_DIR/compliance-status.json

echo "=== Audit Complete ==="
echo "Audit data saved to: $AUDIT_DIR"
```

### Resource-Specific Compliance Check

```bash
#!/bin/bash
# Check compliance for specific resource types

RESOURCE_TYPES=("AWS::S3::Bucket" "AWS::EC2::Instance" "AWS::RDS::DBInstance" "AWS::IAM::Role")

for resource_type in "${RESOURCE_TYPES[@]}"; do
    echo "=== Checking $resource_type ==="
    aws-cloud-utilities awsconfig compliance-status --resource-type $resource_type --output-file ${resource_type//::/-}-compliance.json
done
```

## Common Use Cases

1. **Daily Compliance Monitoring**
   ```bash
   aws-cloud-utilities awsconfig list-rules --compliance-status NON_COMPLIANT
   aws-cloud-utilities awsconfig compliance-checker --severity HIGH
   ```

2. **Configuration Backup**
   ```bash
   aws-cloud-utilities awsconfig download --include-snapshots --include-history
   ```

3. **Rule Management**
   ```bash
   aws-cloud-utilities awsconfig show-rules --rule-name my-custom-rule
   aws-cloud-utilities awsconfig compliance-status --rule-name my-custom-rule
   ```

4. **Resource Compliance Analysis**
   ```bash
   aws-cloud-utilities awsconfig compliance-status --resource-type AWS::S3::Bucket
   aws-cloud-utilities awsconfig compliance-status --resource-id my-specific-resource
   ```

## Integration with Other Tools

AWS Config commands work well with other AWS Cloud Utilities commands:

```bash
# Combine with security audit
aws-cloud-utilities security blue-team-audit
aws-cloud-utilities awsconfig compliance-checker --detailed

# Combine with inventory
aws-cloud-utilities inventory resources --resource-type s3
aws-cloud-utilities awsconfig compliance-status --resource-type AWS::S3::Bucket
```

## Best Practices

- Run compliance checks regularly as part of your security monitoring
- Use `--detailed` flag for comprehensive remediation guidance
- Combine Config data with other security tools for complete visibility
- Set up automated compliance monitoring using the JSON output
- Filter by severity to focus on critical issues first
