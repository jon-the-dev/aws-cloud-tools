# Account Commands

Account information and management commands for AWS account details, regions, and configuration.

## Commands

### `info`

Get comprehensive AWS account information.

```bash
aws-cloud-utilities account info
```

**Output includes:**
- Account ID and ARN
- Account alias
- IAM summary (users, groups, roles, policies)
- Service limits
- Current caller identity

**Options:**
- `--output` - Output format (table, json, yaml, csv)

**Examples:**
```bash
# Basic account info
aws-cloud-utilities account info

# JSON output for scripting
aws-cloud-utilities account info --output json

# With specific profile
aws-cloud-utilities --profile production account info
```

### `contact-info`

Get AWS account contact information.

```bash
aws-cloud-utilities account contact-info
```

**Output includes:**
- Billing contact information
- Operations contact information
- Security contact information

**Examples:**
```bash
# Get contact information
aws-cloud-utilities account contact-info

# Export to YAML
aws-cloud-utilities account contact-info --output yaml
```

### `regions`

List available AWS regions and their status.

```bash
aws-cloud-utilities account regions
```

**Options:**
- `--service SERVICE` - Filter regions by service availability
- `--enabled-only` - Show only enabled regions

**Examples:**
```bash
# All regions
aws-cloud-utilities account regions

# Regions with Lambda
aws-cloud-utilities account regions --service lambda

# Only enabled regions
aws-cloud-utilities account regions --enabled-only
```

### `detect-control-tower`

Detect AWS Control Tower or Landing Zone deployment.

```bash
aws-cloud-utilities account detect-control-tower
```

**Features:**
- Parallel region scanning
- Detects Control Tower resources
- Identifies Landing Zone components
- Shows organizational structure

**Options:**
- `--verbose` - Show detailed scanning progress
- `--all-regions` - Scan all regions (default: enabled regions only)

**Examples:**
```bash
# Basic detection
aws-cloud-utilities account detect-control-tower

# Verbose output with progress
aws-cloud-utilities --verbose account detect-control-tower

# Scan all regions
aws-cloud-utilities account detect-control-tower --all-regions
```

### `limits`

Show AWS service limits and current usage.

```bash
aws-cloud-utilities account limits
```

**Options:**
- `--service SERVICE` - Show limits for specific service
- `--region REGION` - Show limits for specific region

**Examples:**
```bash
# All service limits
aws-cloud-utilities account limits

# EC2 limits only
aws-cloud-utilities account limits --service ec2

# Limits in specific region
aws-cloud-utilities account limits --region us-west-2
```

### `validate`

Validate AWS account configuration and permissions.

```bash
aws-cloud-utilities account validate
```

**Checks:**
- AWS credentials validity
- Basic permissions
- Service availability
- Region accessibility

**Examples:**
```bash
# Validate current configuration
aws-cloud-utilities account validate

# Validate specific profile
aws-cloud-utilities --profile staging account validate
```

## Global Options

All account commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Daily Account Check

```bash
#!/bin/bash
# Daily account status check
echo "=== Account Information ==="
aws-cloud-utilities account info

echo "=== Control Tower Status ==="
aws-cloud-utilities account detect-control-tower

echo "=== Service Limits ==="
aws-cloud-utilities account limits --service ec2
```

### Multi-Profile Account Summary

```bash
#!/bin/bash
for profile in dev staging prod; do
    echo "=== $profile Account ==="
    aws-cloud-utilities --profile $profile account info --output json > ${profile}-account.json
done
```

## Common Use Cases

1. **Account Setup Verification**
   ```bash
   aws-cloud-utilities account info
   aws-cloud-utilities account contact-info
   aws-cloud-utilities account validate
   ```

2. **Control Tower Assessment**
   ```bash
   aws-cloud-utilities account detect-control-tower --verbose
   ```

3. **Service Limit Monitoring**
   ```bash
   aws-cloud-utilities account limits --service ec2 --output json
   ```

4. **Multi-Region Analysis**
   ```bash
   aws-cloud-utilities account regions --service lambda
   ```
