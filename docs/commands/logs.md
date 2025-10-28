# Logs Commands

CloudWatch logs management commands for log analysis, aggregation, and monitoring.

## Commands

### `list-groups`

List CloudWatch log groups with details and optional size information.

```bash
aws-cloud-utilities logs list-groups [OPTIONS]
```

**Output includes:**
- Log group name
- Creation time
- Retention policy
- Stored bytes (optional)
- Metric filters count

**Options:**
- `--region REGION` - AWS region (default: current region)
- `--all-regions` - List log groups from all regions
- `--prefix PREFIX` - Filter by log group name prefix
- `--include-size` - Include size information from CloudWatch metrics
- `--output-file FILE` - Save results to file (json, yaml, csv)

**Examples:**
```bash
# List all log groups
aws-cloud-utilities logs list-groups

# List across all regions
aws-cloud-utilities logs list-groups --all-regions

# Filter Lambda log groups
aws-cloud-utilities logs list-groups --prefix /aws/lambda/

# Include size information
aws-cloud-utilities logs list-groups --include-size

# Export to file
aws-cloud-utilities logs list-groups --output-file log-groups.json
```

### `download`

Download logs from CloudWatch log groups.

```bash
aws-cloud-utilities logs download LOG_GROUP_NAME [OPTIONS]
```

**Arguments:**
- `LOG_GROUP_NAME` - Name of the log group to download

**Options:**
- `--start-time TIME` - Start time for log download (ISO format or relative)
- `--end-time TIME` - End time for log download
- `--output-dir DIR` - Directory to save downloaded logs
- `--output-file FILE` - Specific output file name
- `--filter-pattern PATTERN` - CloudWatch Logs filter pattern
- `--streams STREAMS` - Comma-separated list of log streams to download
- `--format FORMAT` - Output format (json, text) [default: text]

**Examples:**
```bash
# Download all recent logs
aws-cloud-utilities logs download /aws/lambda/my-function

# Download with time range
aws-cloud-utilities logs download /aws/lambda/my-function \
  --start-time "2024-01-01 00:00:00" \
  --end-time "2024-01-01 23:59:59"

# Download to specific directory
aws-cloud-utilities logs download /aws/lambda/my-function --output-dir ./logs

# Apply filter pattern
aws-cloud-utilities logs download /aws/lambda/my-function --filter-pattern "ERROR"

# Download as JSON
aws-cloud-utilities logs download /aws/lambda/my-function --format json
```

### `set-retention`

Set or update log retention policies for CloudWatch log groups.

```bash
aws-cloud-utilities logs set-retention LOG_GROUP_NAME RETENTION_DAYS [OPTIONS]
```

**Arguments:**
- `LOG_GROUP_NAME` - Name of the log group
- `RETENTION_DAYS` - Retention period in days (1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653)

**Options:**
- `--region REGION` - AWS region
- `--all-log-groups` - Apply to all log groups (use with caution)
- `--prefix PREFIX` - Apply to log groups matching prefix
- `--dry-run` - Show what would be changed without applying

**Examples:**
```bash
# Set retention for specific log group
aws-cloud-utilities logs set-retention /aws/lambda/my-function 30

# Set retention for all Lambda functions
aws-cloud-utilities logs set-retention --prefix /aws/lambda/ --retention-days 7

# Dry run to see what would change
aws-cloud-utilities logs set-retention --prefix /aws/lambda/ --retention-days 14 --dry-run

# Apply to all log groups (use carefully!)
aws-cloud-utilities logs set-retention --all-log-groups 90
```

### `delete-group`

Delete CloudWatch log groups with confirmation.

```bash
aws-cloud-utilities logs delete-group LOG_GROUP_NAME [OPTIONS]
```

**Arguments:**
- `LOG_GROUP_NAME` - Name of the log group to delete

**Options:**
- `--region REGION` - AWS region
- `--force` - Skip confirmation prompt
- `--prefix PREFIX` - Delete all log groups matching prefix (dangerous!)

**Examples:**
```bash
# Delete specific log group (with confirmation)
aws-cloud-utilities logs delete-group /aws/lambda/old-function

# Delete without confirmation
aws-cloud-utilities logs delete-group /aws/lambda/old-function --force

# Delete all log groups with prefix (very dangerous!)
aws-cloud-utilities logs delete-group --prefix /aws/lambda/test- --force
```

### `combine`

Combine and aggregate logs from multiple CloudWatch log sources.

```bash
aws-cloud-utilities logs combine [OPTIONS]
```

**Features:**
- Merges logs from multiple log groups
- Sorts logs chronologically
- Combines log streams
- Deduplicates entries

**Options:**
- `--log-groups GROUPS` - Comma-separated list of log groups
- `--prefix PREFIX` - Combine all log groups matching prefix
- `--start-time TIME` - Start time for log combination
- `--end-time TIME` - End time for log combination
- `--output-file FILE` - Output file for combined logs
- `--format FORMAT` - Output format (json, text)

**Examples:**
```bash
# Combine multiple log groups
aws-cloud-utilities logs combine \
  --log-groups /aws/lambda/function1,/aws/lambda/function2,/aws/lambda/function3

# Combine all Lambda logs
aws-cloud-utilities logs combine --prefix /aws/lambda/

# Combine with time range
aws-cloud-utilities logs combine \
  --log-groups /aws/lambda/function1,/aws/lambda/function2 \
  --start-time "2024-01-01" \
  --end-time "2024-01-02" \
  --output-file combined-logs.txt
```

### `aggregate`

Aggregate logs from S3 sources (CloudTrail, CloudFront, ELB, ALB, Route53).

```bash
aws-cloud-utilities logs aggregate [OPTIONS]
```

**Supported log types:**
- AWS CloudTrail logs
- CloudFront access logs
- ELB (Classic Load Balancer) logs
- ALB (Application Load Balancer) logs
- Route53 query logs

**Options:**
- `--bucket BUCKET` - S3 bucket containing logs
- `--prefix PREFIX` - S3 prefix for logs
- `--log-type TYPE` - Type of logs (cloudtrail, cloudfront, elb, alb, route53)
- `--start-date DATE` - Start date for aggregation
- `--end-date DATE` - End date for aggregation
- `--output-file FILE` - Output file for aggregated logs
- `--format FORMAT` - Output format (json, csv, text)

**Examples:**
```bash
# Aggregate CloudTrail logs
aws-cloud-utilities logs aggregate \
  --bucket my-cloudtrail-bucket \
  --prefix AWSLogs/123456789012/CloudTrail/ \
  --log-type cloudtrail

# Aggregate CloudFront logs
aws-cloud-utilities logs aggregate \
  --bucket my-cloudfront-logs \
  --log-type cloudfront \
  --start-date 2024-01-01 \
  --end-date 2024-01-31

# Aggregate ALB logs to CSV
aws-cloud-utilities logs aggregate \
  --bucket my-alb-logs \
  --log-type alb \
  --format csv \
  --output-file alb-analysis.csv

# Aggregate with specific prefix
aws-cloud-utilities logs aggregate \
  --bucket my-logs-bucket \
  --prefix elasticloadbalancing/ \
  --log-type elb \
  --output-file elb-logs.json
```

## Global Options

All logs commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Common Use Cases

### Log Group Management

```bash
#!/bin/bash
# Manage CloudWatch log groups

echo "=== List All Log Groups ==="
aws-cloud-utilities logs list-groups --include-size

echo "=== Set Retention for Lambda Logs ==="
aws-cloud-utilities logs set-retention --prefix /aws/lambda/ 30

echo "=== Delete Old Test Log Groups ==="
aws-cloud-utilities logs delete-group --prefix /aws/lambda/test- --force
```

### Log Download and Analysis

```bash
#!/bin/bash
# Download logs for analysis

FUNCTION_NAME="my-lambda-function"
DATE=$(date +%Y%m%d)

echo "=== Downloading Logs ==="
aws-cloud-utilities logs download /aws/lambda/$FUNCTION_NAME \
  --start-time "24 hours ago" \
  --output-file "logs-${DATE}.txt"

echo "=== Downloading Error Logs ==="
aws-cloud-utilities logs download /aws/lambda/$FUNCTION_NAME \
  --filter-pattern "ERROR" \
  --output-file "errors-${DATE}.txt"
```

### Multi-Service Log Aggregation

```bash
#!/bin/bash
# Aggregate logs from multiple services

echo "=== Combining Application Logs ==="
aws-cloud-utilities logs combine \
  --log-groups /aws/lambda/api,/aws/lambda/processor,/aws/lambda/worker \
  --start-time "2024-01-01" \
  --output-file combined-app-logs.txt

echo "=== Aggregating CloudTrail Logs ==="
aws-cloud-utilities logs aggregate \
  --bucket my-cloudtrail-bucket \
  --log-type cloudtrail \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output-file cloudtrail-january.json
```

### S3 Log Analysis

```bash
#!/bin/bash
# Analyze S3-based logs

echo "=== CloudFront Log Analysis ==="
aws-cloud-utilities logs aggregate \
  --bucket my-cloudfront-logs \
  --log-type cloudfront \
  --format csv \
  --output-file cloudfront-analysis.csv

echo "=== ALB Log Analysis ==="
aws-cloud-utilities logs aggregate \
  --bucket my-alb-logs \
  --log-type alb \
  --format json \
  --output-file alb-requests.json
```

### Retention Policy Management

```bash
#!/bin/bash
# Manage log retention across account

echo "=== Checking Current Retention ==="
aws-cloud-utilities logs list-groups --all-regions --output-file current-retention.csv

echo "=== Setting Standard Retention ==="
# Lambda functions: 30 days
aws-cloud-utilities logs set-retention --prefix /aws/lambda/ 30

# API Gateway: 14 days
aws-cloud-utilities logs set-retention --prefix /aws/apigateway/ 14

# ECS: 7 days
aws-cloud-utilities logs set-retention --prefix /aws/ecs/ 7
```

## Best Practices

1. **Set Retention Policies**: Always set appropriate retention to control costs
   ```bash
   aws-cloud-utilities logs set-retention --prefix /aws/lambda/ 30
   ```

2. **Regular Log Downloads**: Download important logs for long-term storage
   ```bash
   aws-cloud-utilities logs download /aws/lambda/critical-function --output-dir ./archives
   ```

3. **Use Filters**: Apply filter patterns to reduce download size
   ```bash
   aws-cloud-utilities logs download /aws/lambda/function --filter-pattern "ERROR"
   ```

4. **Aggregate S3 Logs**: Regularly aggregate S3 logs for analysis
   ```bash
   aws-cloud-utilities logs aggregate --bucket logs --log-type cloudtrail
   ```

## Performance Tips

1. **Parallel Downloads**: Download from multiple log groups in parallel
2. **Time Range Filters**: Always specify time ranges to reduce data transfer
3. **Filter Patterns**: Use CloudWatch filter patterns to reduce download volume
4. **Regional Downloads**: Specify region to avoid unnecessary API calls
