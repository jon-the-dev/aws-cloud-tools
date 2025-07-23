# WAF Commands

The WAF commands provide comprehensive monitoring and troubleshooting capabilities for AWS WAF (Web Application Firewall) to help identify whether blocks are due to WAF rules, application issues, or end-user problems.

## Available Commands

### `waf list`

List all Web ACLs in your AWS account.

```bash
aws-cloud-utilities waf list [OPTIONS]
```

**Options:**
- `--scope [REGIONAL|CLOUDFRONT]`: WAF scope (default: REGIONAL)
- `--output-file FILE`: Save output to file

**Examples:**
```bash
# List regional Web ACLs
aws-cloud-utilities waf list

# List CloudFront Web ACLs
aws-cloud-utilities waf list --scope CLOUDFRONT

# Save output to file
aws-cloud-utilities waf list --output-file web-acls.json
```

### `waf stats`

Get comprehensive WAF statistics for troubleshooting.

```bash
aws-cloud-utilities waf stats --web-acl WEB_ACL_NAME [OPTIONS]
```

**Options:**
- `--web-acl TEXT`: Web ACL name to analyze (required)
- `--hours INTEGER`: Hours of data to analyze (default: 24)
- `--scope [REGIONAL|CLOUDFRONT]`: WAF scope (default: REGIONAL)
- `--output-file FILE`: Save output to file

**Examples:**
```bash
# Get 24-hour stats for a Web ACL
aws-cloud-utilities waf stats --web-acl my-web-acl

# Get 7-day stats
aws-cloud-utilities waf stats --web-acl my-web-acl --hours 168

# Save stats to file
aws-cloud-utilities waf stats --web-acl my-web-acl --output-file waf-stats.json
```

**Output includes:**
- Total requests (blocked and allowed)
- Block rate percentage
- Recent activity (last hour)
- Time range analysis
- Basic recommendations

### `waf troubleshoot`

Generate comprehensive WAF troubleshooting report.

```bash
aws-cloud-utilities waf troubleshoot --web-acl WEB_ACL_NAME [OPTIONS]
```

**Options:**
- `--web-acl TEXT`: Web ACL name to troubleshoot (required)
- `--hours INTEGER`: Hours of data to analyze (default: 24)
- `--output-file FILE`: Save troubleshooting report to file

**Examples:**
```bash
# Generate troubleshooting report
aws-cloud-utilities waf troubleshoot --web-acl my-web-acl

# Analyze last 48 hours
aws-cloud-utilities waf troubleshoot --web-acl my-web-acl --hours 48

# Save report to file
aws-cloud-utilities waf troubleshoot --web-acl my-web-acl --output-file troubleshoot-report.json
```

**Report includes:**
- Comprehensive metrics analysis
- Block rate analysis (high/very high alerts)
- Recent spike detection
- Traffic pattern analysis
- Detailed recommendations for optimization

## Troubleshooting Scenarios

### High Block Rate (>20%)
When the troubleshoot command detects a very high block rate:

**Possible Causes:**
- WAF rules are too restrictive (false positives)
- Legitimate traffic patterns changed
- New application features triggering rules

**Recommended Actions:**
1. Review WAF rule configurations
2. Check for recent rule changes
3. Analyze blocked request patterns
4. Consider rule tuning or exceptions

### No Traffic Detected
When no requests are detected:

**Possible Causes:**
- WAF not properly associated with resources
- Load balancer or CloudFront not configured
- DNS routing issues

**Recommended Actions:**
1. Verify WAF association with ALB/CloudFront
2. Check load balancer configuration
3. Verify DNS routing
4. Test application accessibility

### Recent Traffic Spikes
When sudden increases in blocked requests are detected:

**Possible Causes:**
- DDoS or bot attacks
- New WAF rules activated
- Application deployment changes

**Recommended Actions:**
1. Investigate source IPs and patterns
2. Review recent rule changes
3. Check application logs
4. Consider rate limiting adjustments

## Integration with Load Balancers

The WAF commands work with:

- **Application Load Balancer (ALB)**: Use REGIONAL scope
- **CloudFront**: Use CLOUDFRONT scope
- **API Gateway**: Use REGIONAL scope

## Best Practices

1. **Regular Monitoring**: Run stats command daily to establish baselines
2. **Automated Alerts**: Use troubleshoot command in monitoring scripts
3. **Historical Analysis**: Save outputs to files for trend analysis
4. **Rule Optimization**: Use insights to fine-tune WAF rules

## Output Formats

All commands support multiple output formats:
- `--output json`: JSON format
- `--output yaml`: YAML format  
- `--output table`: Human-readable table (default)

## Common Use Cases

### Daily Health Check
```bash
aws-cloud-utilities waf stats --web-acl production-waf --hours 24
```

### Incident Investigation
```bash
aws-cloud-utilities waf troubleshoot --web-acl production-waf --hours 2 --output-file incident-report.json
```

### Weekly Review
```bash
aws-cloud-utilities waf stats --web-acl production-waf --hours 168 --output-file weekly-stats.json
```

## Error Handling

The WAF commands include comprehensive error handling for:
- Invalid Web ACL names
- Missing permissions
- CloudWatch API limits
- Network connectivity issues

Common errors and solutions:
- **AccessDenied**: Ensure IAM permissions for WAF and CloudWatch
- **ResourceNotFound**: Verify Web ACL name and scope
- **Throttling**: Commands include automatic retry logic
