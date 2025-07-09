# Security Commands

Security auditing and tools for AWS security assessment, compliance checking, and vulnerability detection.

## Commands

### `audit`

Perform basic security audit of AWS account.

```bash
aws-cloud-utilities security audit
```

**Checks:**
- IAM configuration
- S3 bucket security
- Security group rules
- CloudTrail configuration
- Basic compliance checks

**Options:**
- `--service SERVICE` - Audit specific service
- `--severity LEVEL` - Filter by severity (low, medium, high, critical)
- `--compliance-framework FRAMEWORK` - Check against specific framework

**Examples:**
```bash
# Basic security audit
aws-cloud-utilities security audit

# High severity issues only
aws-cloud-utilities security audit --severity high

# S3 security audit
aws-cloud-utilities security audit --service s3
```

### `blue-team-audit`

Comprehensive security assessment for blue team operations.

```bash
aws-cloud-utilities security blue-team-audit
```

**Enhanced checks:**
- Advanced IAM analysis
- Network security assessment
- Encryption status
- Logging and monitoring
- Incident response readiness
- Compliance posture

**Options:**
- `--detailed` - Include detailed findings
- `--export-format FORMAT` - Export format for reports
- `--include-remediation` - Include remediation steps

**Examples:**
```bash
# Comprehensive audit
aws-cloud-utilities security blue-team-audit

# Detailed report with remediation
aws-cloud-utilities security blue-team-audit --detailed --include-remediation

# Export to JSON
aws-cloud-utilities security blue-team-audit --output json > security-audit.json
```

### `public-resources`

Find publicly accessible AWS resources.

```bash
aws-cloud-utilities security public-resources
```

**Detects:**
- Public S3 buckets
- Open security groups
- Public RDS instances
- Exposed Lambda functions
- Public ELB/ALB endpoints

**Options:**
- `--service SERVICE` - Check specific service
- `--region REGION` - Check specific region
- `--severity LEVEL` - Filter by risk level

**Examples:**
```bash
# All public resources
aws-cloud-utilities security public-resources

# Public S3 buckets only
aws-cloud-utilities security public-resources --service s3

# High-risk exposures
aws-cloud-utilities security public-resources --severity high
```

### `compliance`

Check compliance against security frameworks.

```bash
aws-cloud-utilities security compliance --framework FRAMEWORK
```

**Supported frameworks:**
- CIS AWS Foundations Benchmark
- AWS Security Best Practices
- SOC 2
- PCI DSS
- HIPAA

**Options:**
- `--framework FRAMEWORK` - Compliance framework
- `--control CONTROL` - Specific control check
- `--export-report` - Generate compliance report

**Examples:**
```bash
# CIS compliance check
aws-cloud-utilities security compliance --framework cis

# SOC 2 compliance
aws-cloud-utilities security compliance --framework soc2

# Specific control
aws-cloud-utilities security compliance --framework cis --control 1.1
```

### `encryption-status`

Check encryption status across AWS services.

```bash
aws-cloud-utilities security encryption-status
```

**Checks:**
- EBS volume encryption
- S3 bucket encryption
- RDS encryption
- Lambda environment variables
- Parameter Store encryption

**Options:**
- `--service SERVICE` - Check specific service
- `--unencrypted-only` - Show only unencrypted resources

**Examples:**
```bash
# All encryption status
aws-cloud-utilities security encryption-status

# Unencrypted resources only
aws-cloud-utilities security encryption-status --unencrypted-only

# S3 encryption status
aws-cloud-utilities security encryption-status --service s3
```

### `network-analysis`

Analyze network security configuration.

```bash
aws-cloud-utilities security network-analysis
```

**Analysis includes:**
- Security group rules
- NACL configuration
- VPC flow logs
- Internet gateway exposure
- NAT gateway configuration

**Options:**
- `--vpc-id VPC` - Analyze specific VPC
- `--show-flows` - Include flow log analysis
- `--risky-rules-only` - Show only risky rules

**Examples:**
```bash
# All network analysis
aws-cloud-utilities security network-analysis

# Specific VPC
aws-cloud-utilities security network-analysis --vpc-id vpc-12345678

# Risky rules only
aws-cloud-utilities security network-analysis --risky-rules-only
```

### `secrets-scan`

Scan for exposed secrets and credentials.

```bash
aws-cloud-utilities security secrets-scan
```

**Scans:**
- Lambda environment variables
- EC2 user data
- CloudFormation templates
- Parameter Store values
- Secrets Manager usage

**Options:**
- `--service SERVICE` - Scan specific service
- `--pattern PATTERN` - Custom secret pattern
- `--exclude-encrypted` - Skip encrypted values

**Examples:**
```bash
# Full secrets scan
aws-cloud-utilities security secrets-scan

# Lambda functions only
aws-cloud-utilities security secrets-scan --service lambda

# Custom pattern
aws-cloud-utilities security secrets-scan --pattern "api[_-]?key"
```

## Global Options

All security commands support:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Daily Security Check

```bash
#!/bin/bash
# Daily security monitoring
echo "=== Security Audit ==="
aws-cloud-utilities security audit --output json > daily-audit-$(date +%Y%m%d).json

echo "=== Public Resources ==="
aws-cloud-utilities security public-resources --output json > public-resources-$(date +%Y%m%d).json

echo "=== Encryption Status ==="
aws-cloud-utilities security encryption-status --unencrypted-only
```

### Comprehensive Security Assessment

```bash
#!/bin/bash
# Full security assessment
echo "=== Blue Team Audit ==="
aws-cloud-utilities security blue-team-audit --detailed --include-remediation

echo "=== Compliance Check ==="
aws-cloud-utilities security compliance --framework cis

echo "=== Network Analysis ==="
aws-cloud-utilities security network-analysis

echo "=== Secrets Scan ==="
aws-cloud-utilities security secrets-scan
```

### Incident Response

```bash
#!/bin/bash
# Security incident response
echo "=== Public Exposures ==="
aws-cloud-utilities security public-resources --severity high

echo "=== Network Security ==="
aws-cloud-utilities security network-analysis --risky-rules-only

echo "=== Recent Changes ==="
aws-cloud-utilities security audit --severity critical
```

## Common Use Cases

1. **Regular Security Monitoring**
   ```bash
   aws-cloud-utilities security audit
   aws-cloud-utilities security public-resources
   ```

2. **Compliance Reporting**
   ```bash
   aws-cloud-utilities security compliance --framework cis --export-report
   aws-cloud-utilities security blue-team-audit --detailed
   ```

3. **Incident Investigation**
   ```bash
   aws-cloud-utilities security public-resources --severity high
   aws-cloud-utilities security network-analysis --risky-rules-only
   ```

4. **Security Hardening**
   ```bash
   aws-cloud-utilities security encryption-status --unencrypted-only
   aws-cloud-utilities security secrets-scan
   ```

## Security Findings Format

Security findings include:

- **Severity**: Critical, High, Medium, Low
- **Resource**: Affected AWS resource
- **Finding**: Description of security issue
- **Remediation**: Steps to fix the issue
- **Compliance**: Related compliance frameworks

Example output:
```json
{
  "severity": "HIGH",
  "resource": "s3://my-bucket",
  "finding": "S3 bucket allows public read access",
  "remediation": "Remove public read permissions from bucket policy",
  "compliance": ["CIS-2.3", "SOC2-CC6.1"]
}
```

## Integration with Other Tools

Security commands integrate well with:

- **IAM commands**: `aws-cloud-utilities iam analyze`
- **S3 commands**: `aws-cloud-utilities s3 security-audit`
- **Networking commands**: `aws-cloud-utilities networking security-groups`
- **Inventory commands**: `aws-cloud-utilities inventory resources`
