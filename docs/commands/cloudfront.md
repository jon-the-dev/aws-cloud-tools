# CloudFront Commands

CloudFront distribution management commands for CDN operations and configuration.

## Commands

### `update-logging`

Update logging configuration for CloudFront distributions.

```bash
aws-cloud-utilities cloudfront update-logging
```

**Options:**
- `--distribution-id ID` - Specific distribution to update (default: all distributions)
- `--bucket BUCKET` - S3 bucket for access logs
- `--prefix PREFIX` - Log file prefix
- `--enable` - Enable logging
- `--disable` - Disable logging
- `--dry-run` - Show what would be changed without making changes

**Examples:**
```bash
# Enable logging for all distributions
aws-cloud-utilities cloudfront update-logging --enable --bucket my-logs-bucket --prefix cloudfront/

# Update specific distribution
aws-cloud-utilities cloudfront update-logging --distribution-id E1234567890123 --enable --bucket my-logs-bucket

# Disable logging for all distributions
aws-cloud-utilities cloudfront update-logging --disable

# Dry run to see changes
aws-cloud-utilities cloudfront update-logging --enable --bucket my-logs-bucket --dry-run
```

### `list-distributions`

List CloudFront distributions with status and configuration details.

```bash
aws-cloud-utilities cloudfront list-distributions
```

**Options:**
- `--status STATUS` - Filter by distribution status (Deployed, InProgress)
- `--include-config` - Include detailed configuration in output
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all distributions
aws-cloud-utilities cloudfront list-distributions

# List only deployed distributions
aws-cloud-utilities cloudfront list-distributions --status Deployed

# Include detailed configuration
aws-cloud-utilities cloudfront list-distributions --include-config

# Save to file
aws-cloud-utilities cloudfront list-distributions --output-file distributions.json
```

### `distribution-details`

Get comprehensive details about a specific CloudFront distribution.

```bash
aws-cloud-utilities cloudfront distribution-details DISTRIBUTION_ID
```

**Arguments:**
- `DISTRIBUTION_ID` - ID of the distribution to analyze

**Options:**
- `--include-config` - Include full distribution configuration
- `--include-origins` - Include origin configuration details
- `--include-behaviors` - Include cache behavior details
- `--include-invalidations` - Include recent invalidation history
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Basic distribution details
aws-cloud-utilities cloudfront distribution-details E1234567890123

# Comprehensive details
aws-cloud-utilities cloudfront distribution-details E1234567890123 --include-config --include-origins --include-behaviors

# Include invalidation history
aws-cloud-utilities cloudfront distribution-details E1234567890123 --include-invalidations

# Save to file
aws-cloud-utilities cloudfront distribution-details E1234567890123 --output-file distribution-analysis.json
```

## Global Options

All CloudFront commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region (CloudFront is global, but affects API endpoint)
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Distribution Audit Workflow

```bash
#!/bin/bash
# Comprehensive CloudFront audit

AUDIT_DIR="./cloudfront-audit-$(date +%Y%m%d)"
mkdir -p $AUDIT_DIR

echo "=== Distribution Overview ==="
aws-cloud-utilities cloudfront list-distributions --include-config --output-file $AUDIT_DIR/distributions.json

echo "=== Detailed Analysis ==="
# Get list of distribution IDs and analyze each one
aws-cloud-utilities cloudfront list-distributions --output json | \
jq -r '.[] | .Id' | \
while read dist_id; do
    echo "Analyzing distribution: $dist_id"
    aws-cloud-utilities cloudfront distribution-details $dist_id \
        --include-config \
        --include-origins \
        --include-behaviors \
        --include-invalidations \
        --output-file $AUDIT_DIR/distribution-$dist_id.json
done

echo "=== Audit Complete ==="
echo "Audit data saved to: $AUDIT_DIR"
```

### Logging Configuration Update

```bash
#!/bin/bash
# Update logging for all distributions

LOG_BUCKET="my-cloudfront-logs"
LOG_PREFIX="access-logs/"

echo "=== Current Distribution Status ==="
aws-cloud-utilities cloudfront list-distributions

echo "=== Updating Logging Configuration (Dry Run) ==="
aws-cloud-utilities cloudfront update-logging --enable --bucket $LOG_BUCKET --prefix $LOG_PREFIX --dry-run

echo "=== Applying Logging Configuration ==="
read -p "Apply changes? (y/N): " confirm
if [[ $confirm == [yY] ]]; then
    aws-cloud-utilities cloudfront update-logging --enable --bucket $LOG_BUCKET --prefix $LOG_PREFIX
    echo "Logging configuration updated"
else
    echo "Changes cancelled"
fi
```

### Distribution Health Check

```bash
#!/bin/bash
# Check health and status of all distributions

echo "=== Distribution Status Overview ==="
aws-cloud-utilities cloudfront list-distributions --output table

echo "=== In-Progress Distributions ==="
aws-cloud-utilities cloudfront list-distributions --status InProgress

echo "=== Deployed Distributions ==="
aws-cloud-utilities cloudfront list-distributions --status Deployed --output-file deployed-distributions.json

echo "=== Health Check Complete ==="
```

### Performance Analysis

```bash
#!/bin/bash
# Analyze distribution performance and configuration

DIST_ID="E1234567890123"
ANALYSIS_DIR="./cloudfront-performance-$(date +%Y%m%d)"

mkdir -p $ANALYSIS_DIR

echo "=== Distribution Configuration ==="
aws-cloud-utilities cloudfront distribution-details $DIST_ID \
    --include-config \
    --include-origins \
    --include-behaviors \
    --output-file $ANALYSIS_DIR/config-analysis.json

echo "=== Recent Invalidations ==="
aws-cloud-utilities cloudfront distribution-details $DIST_ID \
    --include-invalidations \
    --output-file $ANALYSIS_DIR/invalidations.json

echo "=== Analysis Complete ==="
echo "Performance data saved to: $ANALYSIS_DIR"
```

## Common Use Cases

1. **Distribution Management**
   ```bash
   aws-cloud-utilities cloudfront list-distributions --include-config
   aws-cloud-utilities cloudfront distribution-details E1234567890123
   ```

2. **Logging Configuration**
   ```bash
   aws-cloud-utilities cloudfront update-logging --enable --bucket my-logs-bucket --prefix cloudfront/
   aws-cloud-utilities cloudfront update-logging --dry-run
   ```

3. **Configuration Audit**
   ```bash
   aws-cloud-utilities cloudfront list-distributions --include-config --output-file audit.json
   aws-cloud-utilities cloudfront distribution-details E1234567890123 --include-origins --include-behaviors
   ```

4. **Status Monitoring**
   ```bash
   aws-cloud-utilities cloudfront list-distributions --status InProgress
   aws-cloud-utilities cloudfront list-distributions --status Deployed
   ```

## Integration with Other Commands

CloudFront commands work well with other AWS Cloud Utilities:

```bash
# Combine with S3 for log analysis
aws-cloud-utilities cloudfront update-logging --enable --bucket my-logs-bucket
aws-cloud-utilities s3 bucket-details my-logs-bucket --include-objects

# Combine with security audit
aws-cloud-utilities security blue-team-audit
aws-cloud-utilities cloudfront list-distributions --include-config
```

## Best Practices

- Use `--dry-run` before making configuration changes
- Enable logging for all distributions for security and performance monitoring
- Regularly audit distribution configurations for security best practices
- Monitor distribution status to catch deployment issues early
- Use JSON output for integration with monitoring and alerting systems
- Keep detailed records of distribution configurations for compliance
