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
- `--show-config` - Include full distribution configuration
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Basic distribution details
aws-cloud-utilities cloudfront distribution-details E1234567890123

# Include full configuration
aws-cloud-utilities cloudfront distribution-details E1234567890123 --show-config

# Save to file
aws-cloud-utilities cloudfront distribution-details E1234567890123 --output-file distribution-analysis.json
```

### `invalidate`

Invalidate CloudFront distribution cache by domain name or distribution ID.

```bash
aws-cloud-utilities cloudfront invalidate TARGET
```

**Arguments:**
- `TARGET` - Either a domain name (e.g., example.com) or distribution ID (e.g., E1234567890123)

**Options:**
- `--paths PATH` - Specific paths to invalidate (can be used multiple times, default: /*)
- `--output-file FILE` - Save invalidation details to file

**Examples:**
```bash
# Invalidate all paths for a domain
aws-cloud-utilities cloudfront invalidate example.com

# Invalidate specific paths
aws-cloud-utilities cloudfront invalidate example.com --paths /images/* --paths /css/*

# Invalidate by distribution ID
aws-cloud-utilities cloudfront invalidate E1234567890123

# Save invalidation details
aws-cloud-utilities cloudfront invalidate example.com --output-file invalidation-details.json
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

### Cache Invalidation Workflow

```bash
#!/bin/bash
# Deploy and invalidate CloudFront cache

DOMAIN="example.com"
PATHS_TO_INVALIDATE=("/api/*" "/static/css/*" "/static/js/*")

echo "=== Pre-Deployment Status ==="
aws-cloud-utilities cloudfront distribution-details $DOMAIN --show-config

echo "=== Deploying Application ==="
# Your deployment commands here
# ...

echo "=== Invalidating CloudFront Cache ==="
PATHS_ARGS=""
for path in "${PATHS_TO_INVALIDATE[@]}"; do
    PATHS_ARGS="$PATHS_ARGS --paths $path"
done

aws-cloud-utilities cloudfront invalidate $DOMAIN $PATHS_ARGS --output-file invalidation-$(date +%Y%m%d-%H%M%S).json

echo "=== Deployment Complete ==="
echo "Cache invalidation initiated. Check AWS Console for status."
```

## Common Use Cases

1. **Distribution Management**
   ```bash
   aws-cloud-utilities cloudfront list-distributions --include-disabled
   aws-cloud-utilities cloudfront distribution-details E1234567890123
   ```

2. **Cache Invalidation**
   ```bash
   # Invalidate all content
   aws-cloud-utilities cloudfront invalidate example.com
   
   # Invalidate specific paths
   aws-cloud-utilities cloudfront invalidate example.com --paths /api/* --paths /static/*
   
   # Invalidate by distribution ID
   aws-cloud-utilities cloudfront invalidate E1234567890123
   ```

3. **Logging Configuration**
   ```bash
   aws-cloud-utilities cloudfront update-logging --log-bucket my-logs-bucket --log-prefix cloudfront/
   aws-cloud-utilities cloudfront update-logging --dry-run
   ```

4. **Configuration Audit**
   ```bash
   aws-cloud-utilities cloudfront list-distributions --show-logging-status --output-file audit.json
   aws-cloud-utilities cloudfront distribution-details E1234567890123 --show-config
   ```

5. **Status Monitoring**
   ```bash
   aws-cloud-utilities cloudfront list-distributions --include-disabled
   aws-cloud-utilities cloudfront list-distributions --show-logging-status
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
