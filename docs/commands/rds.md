# RDS Commands

The RDS command group provides tools for managing and troubleshooting Amazon RDS instances, with specialized support for MySQL connection issues.

## Commands

### troubleshoot-mysql

Analyze MySQL RDS instances for connection-related issues, including the common "too many connections" error.

```bash
aws-cloud-utilities rds troubleshoot-mysql <DB_INSTANCE_IDENTIFIER> [OPTIONS]
```

#### Arguments

- `DB_INSTANCE_IDENTIFIER`: The RDS instance identifier to troubleshoot

#### Options

- `--output-file FILE`: Save detailed results to a JSON file
- `--profile PROFILE`: AWS profile to use
- `--region REGION`: AWS region
- `--output FORMAT`: Output format (table, json, yaml, csv)

#### Examples

```bash
# Basic troubleshooting
aws-cloud-utilities rds troubleshoot-mysql my-mysql-db

# Save detailed results to file
aws-cloud-utilities rds troubleshoot-mysql my-mysql-db --output-file mysql-analysis.json

# Use specific profile and region
aws-cloud-utilities rds troubleshoot-mysql my-mysql-db --profile production --region us-west-2
```

#### What it analyzes

1. **Instance Information**
   - Instance class and specifications
   - Engine version and status
   - Multi-AZ configuration
   - Performance Insights status

2. **Connection Metrics (Last 24 Hours)**
   - Database connections (current and peak)
   - Connection attempts
   - Aborted connections
   - Thread statistics

3. **Parameter Groups**
   - Connection-related parameters
   - Current values and sources
   - Modifiable parameters

4. **Error Logs**
   - Recent connection-related errors
   - "Too many connections" occurrences
   - Connection timeouts and resets

5. **Recommendations**
   - Prioritized action items
   - Configuration suggestions
   - Best practice recommendations

### list-instances

List RDS instances in the current region with optional filtering.

```bash
aws-cloud-utilities rds list-instances [OPTIONS]
```

#### Options

- `--engine ENGINE`: Filter by database engine (mysql, postgres, etc.)
- `--status STATUS`: Filter by instance status (available, stopped, etc.)

#### Examples

```bash
# List all RDS instances
aws-cloud-utilities rds list-instances

# List only MySQL instances
aws-cloud-utilities rds list-instances --engine mysql

# List only available instances
aws-cloud-utilities rds list-instances --status available
```

## Common MySQL Connection Issues

### Too Many Connections Error

This error occurs when the number of concurrent connections exceeds the `max_connections` parameter value.

**Common causes:**
- Application not using connection pooling
- Connection leaks in application code
- Insufficient `max_connections` setting
- High traffic without proper scaling

**Solutions:**
1. Implement connection pooling in your application
2. Increase `max_connections` parameter
3. Upgrade to a larger instance class
4. Use read replicas to distribute load
5. Fix connection leaks in application code

### High Aborted Connections

Indicates connections being terminated unexpectedly.

**Common causes:**
- Network timeouts
- Application connection handling issues
- Security group or firewall issues
- Client-side connection drops

**Solutions:**
1. Check network connectivity
2. Review application connection handling
3. Adjust timeout parameters
4. Monitor security group rules

## Parameter Tuning

### Key Connection Parameters

- `max_connections`: Maximum number of concurrent connections
- `connect_timeout`: Connection establishment timeout
- `wait_timeout`: Time to wait for activity on a connection
- `interactive_timeout`: Timeout for interactive connections
- `thread_cache_size`: Number of threads to cache for reuse

### Best Practices

1. **Connection Pooling**: Always use connection pooling in applications
2. **Right-sizing**: Choose appropriate instance classes for your workload
3. **Monitoring**: Set up CloudWatch alarms for connection metrics
4. **Read Replicas**: Use read replicas to distribute read traffic
5. **Parameter Groups**: Create custom parameter groups for production workloads

## Monitoring and Alerting

### Recommended CloudWatch Alarms

```bash
# Database connections approaching limit
DatabaseConnections > 80% of max_connections

# High aborted connections
AbortedConnections > 10 per 5 minutes

# High connection attempts
ConnectionAttempts > normal baseline + 50%
```

### Performance Insights

Enable Performance Insights for detailed analysis of:
- Top SQL statements
- Wait events
- Database load
- Connection patterns

## Troubleshooting Workflow

1. **Run the troubleshoot command**
   ```bash
   aws-cloud-utilities rds troubleshoot-mysql your-db-instance
   ```

2. **Review the analysis results**
   - Check current connection metrics
   - Look for error patterns in logs
   - Review parameter configurations

3. **Implement recommendations**
   - Start with high-priority items
   - Test changes in non-production first
   - Monitor impact of changes

4. **Follow up monitoring**
   - Set up CloudWatch alarms
   - Enable Performance Insights
   - Regular health checks

## Integration with Other Tools

The RDS troubleshooting tool integrates with:
- CloudWatch metrics and logs
- Performance Insights (when enabled)
- Parameter groups
- Security groups (via instance info)

## Output Formats

### Table Format (Default)
Provides a clean, readable summary with color-coded recommendations.

### JSON Format
Detailed machine-readable output suitable for automation and further analysis.

### File Output
Save complete analysis results to a JSON file for:
- Historical tracking
- Sharing with team members
- Integration with other tools
- Compliance documentation

## Security Considerations

- The tool only reads RDS configuration and metrics
- No sensitive data is displayed in output
- Uses your existing AWS credentials and permissions
- Follows AWS IAM best practices

## Required Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances",
                "rds:DescribeDBParameters",
                "rds:DescribeDBLogFiles",
                "rds:DownloadDBLogFilePortion",
                "cloudwatch:GetMetricStatistics"
            ],
            "Resource": "*"
        }
    ]
}
```
