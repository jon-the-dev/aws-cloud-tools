# Logs Commands

CloudWatch logs management commands for log analysis, aggregation, and monitoring.

## Commands

### `groups`

List CloudWatch log groups.

```bash
aws-cloud-utilities logs groups
```

**Options:**
- `--filter PATTERN` - Filter log groups by name pattern
- `--service SERVICE` - Filter by AWS service
- `--retention-days DAYS` - Filter by retention period

**Examples:**
```bash
# All log groups
aws-cloud-utilities logs groups

# Lambda log groups
aws-cloud-utilities logs groups --filter lambda

# Log groups with specific retention
aws-cloud-utilities logs groups --retention-days 30
```

### `aggregate`

Aggregate log data from a log group.

```bash
aws-cloud-utilities logs aggregate --log-group LOG_GROUP
```

**Options:**
- `--log-group GROUP` - Log group name (required)
- `--start-time TIME` - Start time for aggregation
- `--end-time TIME` - End time for aggregation
- `--interval MINUTES` - Aggregation interval

**Examples:**
```bash
# Aggregate last 24 hours
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function

# Specific time range
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function --start-time "2024-01-01 00:00:00" --end-time "2024-01-01 23:59:59"

# 5-minute intervals
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function --interval 5
```

### `search`

Search log entries for specific patterns.

```bash
aws-cloud-utilities logs search --log-group LOG_GROUP --query QUERY
```

**Options:**
- `--log-group GROUP` - Log group name (required)
- `--query QUERY` - Search query (required)
- `--start-time TIME` - Search start time
- `--end-time TIME` - Search end time
- `--max-results NUMBER` - Maximum results to return

**Examples:**
```bash
# Search for errors
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "ERROR"

# Search with time range
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "timeout" --start-time "1 hour ago"

# Limit results
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "ERROR" --max-results 50
```

### `export`

Export log data to files.

```bash
aws-cloud-utilities logs export --log-group LOG_GROUP
```

**Options:**
- `--log-group GROUP` - Log group name (required)
- `--start-time TIME` - Export start time
- `--end-time TIME` - Export end time
- `--format FORMAT` - Export format (json, text)
- `--output-file FILE` - Output file path

**Examples:**
```bash
# Export to JSON
aws-cloud-utilities logs export --log-group /aws/lambda/my-function --format json --output-file logs.json

# Export specific time range
aws-cloud-utilities logs export --log-group /aws/lambda/my-function --start-time "2024-01-01" --end-time "2024-01-02"

# Export as text
aws-cloud-utilities logs export --log-group /aws/lambda/my-function --format text --output-file logs.txt
```

## Common Use Cases

### Error Analysis
```bash
# Find all errors in the last hour
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "ERROR" --start-time "1 hour ago"

# Aggregate error patterns
aws-cloud-utilities logs aggregate --log-group /aws/lambda/my-function --start-time "24 hours ago"
```

### Performance Monitoring
```bash
# Search for timeout issues
aws-cloud-utilities logs search --log-group /aws/lambda/my-function --query "timeout"

# Monitor response times
aws-cloud-utilities logs search --log-group /aws/apigateway/my-api --query "duration"
```

### Log Management
```bash
# List all log groups and their sizes
aws-cloud-utilities logs groups --output table

# Export logs for archival
aws-cloud-utilities logs export --log-group /aws/lambda/my-function --format json
```
