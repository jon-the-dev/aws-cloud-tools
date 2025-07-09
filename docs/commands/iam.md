# IAM Commands

IAM management and auditing commands for identity and access management analysis.

## Commands

### `analyze`

Analyze IAM configuration and permissions.

```bash
aws-cloud-utilities iam analyze
```

**Analysis includes:**
- User and role permissions
- Policy attachments
- Permission boundaries
- Cross-account access
- Unused permissions

**Options:**
- `--user USER` - Analyze specific user
- `--role ROLE` - Analyze specific role
- `--policy POLICY` - Analyze specific policy
- `--include-unused` - Include unused permissions

**Examples:**
```bash
# Full IAM analysis
aws-cloud-utilities iam analyze

# Specific user analysis
aws-cloud-utilities iam analyze --user my-user

# Include unused permissions
aws-cloud-utilities iam analyze --include-unused
```

### `unused-permissions`

Find unused IAM permissions.

```bash
aws-cloud-utilities iam unused-permissions
```

**Options:**
- `--days DAYS` - Lookback period for usage analysis
- `--user USER` - Check specific user
- `--role ROLE` - Check specific role
- `--service SERVICE` - Check specific AWS service

**Examples:**
```bash
# All unused permissions
aws-cloud-utilities iam unused-permissions

# Unused permissions in last 90 days
aws-cloud-utilities iam unused-permissions --days 90

# Specific user's unused permissions
aws-cloud-utilities iam unused-permissions --user my-user
```

### `policy-simulator`

Simulate IAM policy effects.

```bash
aws-cloud-utilities iam policy-simulator --principal PRINCIPAL --action ACTION --resource RESOURCE
```

**Options:**
- `--principal PRINCIPAL` - IAM principal (user/role ARN)
- `--action ACTION` - AWS action to test
- `--resource RESOURCE` - Resource ARN
- `--context KEY=VALUE` - Request context

**Examples:**
```bash
# Test S3 access
aws-cloud-utilities iam policy-simulator --principal arn:aws:iam::123456789012:user/test-user --action s3:GetObject --resource arn:aws:s3:::my-bucket/*

# Test with context
aws-cloud-utilities iam policy-simulator --principal arn:aws:iam::123456789012:role/test-role --action ec2:DescribeInstances --resource "*" --context aws:RequestedRegion=us-east-1
```

## Common Use Cases

### Security Audit
```bash
# Comprehensive IAM analysis
aws-cloud-utilities iam analyze --include-unused

# Find overprivileged users
aws-cloud-utilities iam unused-permissions --days 30
```

### Permission Testing
```bash
# Test user permissions
aws-cloud-utilities iam policy-simulator --principal arn:aws:iam::123456789012:user/developer --action s3:PutObject --resource arn:aws:s3:::dev-bucket/*
```

### Compliance Review
```bash
# Analyze all IAM entities
aws-cloud-utilities iam analyze --output json > iam-analysis.json

# Check for unused permissions
aws-cloud-utilities iam unused-permissions --output csv > unused-permissions.csv
```
