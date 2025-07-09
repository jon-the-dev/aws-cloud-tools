# Common Use Cases

Real-world examples of using AWS Cloud Utilities v2 for common AWS management tasks.

## Account Setup and Validation

### New Account Onboarding

```bash
#!/bin/bash
# Complete new account setup validation
echo "=== Account Information ==="
aws-cloud-utilities account info

echo "=== Contact Information ==="
aws-cloud-utilities account contact-info

echo "=== Available Regions ==="
aws-cloud-utilities account regions

echo "=== Service Limits ==="
aws-cloud-utilities account limits

echo "=== Control Tower Detection ==="
aws-cloud-utilities account detect-control-tower

echo "=== Initial Security Audit ==="
aws-cloud-utilities security audit

echo "=== Support Level ==="
aws-cloud-utilities support check-level
```

### Multi-Account Management

```bash
#!/bin/bash
# Check multiple AWS accounts
accounts=("dev" "staging" "prod")

for account in "${accounts[@]}"; do
    echo "=== $account Account ==="
    aws-cloud-utilities --profile $account account info --output json > ${account}-info.json
    aws-cloud-utilities --profile $account security audit --output json > ${account}-security.json
    aws-cloud-utilities --profile $account inventory resources --output json > ${account}-resources.json
done
```

## Daily Operations

### Daily Health Check

```bash
#!/bin/bash
# Daily AWS environment health check
DATE=$(date +%Y%m%d)

echo "=== Resource Health Check ==="
aws-cloud-utilities inventory health-check --unhealthy-only

echo "=== Security Issues ==="
aws-cloud-utilities security audit --severity high

echo "=== Public Resources ==="
aws-cloud-utilities security public-resources

echo "=== Support Cases ==="
aws-cloud-utilities support cases --status open

# Save results
aws-cloud-utilities inventory health-check --output json > health-${DATE}.json
aws-cloud-utilities security audit --output json > security-${DATE}.json
```

### Resource Monitoring

```bash
#!/bin/bash
# Monitor resource changes and usage
echo "=== Resource Inventory ==="
aws-cloud-utilities inventory resources --all-regions --output csv > resources-$(date +%Y%m%d).csv

echo "=== Unused Resources ==="
aws-cloud-utilities inventory unused-resources --age-threshold 7

echo "=== Cost Analysis ==="
aws-cloud-utilities costops analyze --group-by service

echo "=== Tagging Compliance ==="
aws-cloud-utilities inventory tagging-audit --required-tags Environment,Owner,Project
```

## Cost Management

### Monthly Cost Review

```bash
#!/bin/bash
# Monthly cost optimization review
MONTH=$(date +%Y%m)

echo "=== Cost Analysis ==="
aws-cloud-utilities costops analyze --start-date $(date -d "1 month ago" +%Y-%m-01) --output json > cost-analysis-${MONTH}.json

echo "=== Optimization Recommendations ==="
aws-cloud-utilities costops recommendations --min-savings 50 --output json > recommendations-${MONTH}.json

echo "=== Unused Resources ==="
aws-cloud-utilities inventory unused-resources --output json > unused-resources-${MONTH}.json

echo "=== Rightsizing Opportunities ==="
aws-cloud-utilities costops rightsizing --min-savings 25 --output json > rightsizing-${MONTH}.json

echo "=== Savings Plans Analysis ==="
aws-cloud-utilities costops savings-plans --output json > savings-plans-${MONTH}.json

# Generate summary report
echo "=== Cost Summary ==="
echo "Total recommendations: $(jq length recommendations-${MONTH}.json)"
echo "Potential monthly savings: $(jq '[.[].estimated_monthly_savings] | add' recommendations-${MONTH}.json)"
```

### GPU Cost Optimization

```bash
#!/bin/bash
# Find cheapest GPU instances for ML workloads
echo "=== P3 Instance Pricing ==="
aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge --output table

echo "=== P4 Instance Pricing ==="
aws-cloud-utilities costops gpu-spots --instance-type p4d.xlarge --output table

echo "=== G4 Instance Pricing ==="
aws-cloud-utilities costops gpu-spots --instance-type g4dn.xlarge --output table

echo "=== Best GPU Deals Under $1/hour ==="
aws-cloud-utilities costops gpu-spots --max-price 1.00 --output csv > gpu-deals.csv

echo "=== Multi-Region GPU Pricing ==="
aws-cloud-utilities costops gpu-spots --regions us-east-1,us-west-2,eu-west-1 --instance-type p3.2xlarge
```

## Security Operations

### Security Audit Workflow

```bash
#!/bin/bash
# Comprehensive security audit
DATE=$(date +%Y%m%d)

echo "=== Blue Team Security Audit ==="
aws-cloud-utilities security blue-team-audit --detailed --include-remediation --output json > security-audit-${DATE}.json

echo "=== Public Resource Exposure ==="
aws-cloud-utilities security public-resources --output json > public-resources-${DATE}.json

echo "=== IAM Analysis ==="
aws-cloud-utilities iam analyze --output json > iam-analysis-${DATE}.json

echo "=== Network Security ==="
aws-cloud-utilities security network-analysis --risky-rules-only --output json > network-security-${DATE}.json

echo "=== Encryption Status ==="
aws-cloud-utilities security encryption-status --unencrypted-only --output json > encryption-status-${DATE}.json

echo "=== Compliance Check ==="
aws-cloud-utilities security compliance --framework cis --output json > compliance-${DATE}.json

# Generate security summary
echo "=== Security Summary ==="
echo "Critical findings: $(jq '[.[] | select(.severity == "CRITICAL")] | length' security-audit-${DATE}.json)"
echo "High findings: $(jq '[.[] | select(.severity == "HIGH")] | length' security-audit-${DATE}.json)"
echo "Public resources: $(jq length public-resources-${DATE}.json)"
```

### Incident Response

```bash
#!/bin/bash
# Security incident response checklist
echo "=== Immediate Security Assessment ==="

echo "1. Check for public exposures"
aws-cloud-utilities security public-resources --severity critical

echo "2. Review recent IAM changes"
aws-cloud-utilities iam analyze --recent-changes

echo "3. Check network security"
aws-cloud-utilities security network-analysis --risky-rules-only

echo "4. Review CloudTrail logs"
aws-cloud-utilities logs search --log-group CloudTrail --query "ERROR" --start-time "1 hour ago"

echo "5. Check for unusual activity"
aws-cloud-utilities security audit --severity critical

echo "6. Review support cases"
aws-cloud-utilities support cases --status open
```

## Log Management

### Log Analysis Workflow

```bash
#!/bin/bash
# Comprehensive log analysis
LOG_GROUP="/aws/lambda/my-function"
START_TIME="24 hours ago"

echo "=== Log Groups Overview ==="
aws-cloud-utilities logs groups

echo "=== Error Analysis ==="
aws-cloud-utilities logs search --log-group $LOG_GROUP --query "ERROR" --start-time "$START_TIME"

echo "=== Warning Analysis ==="
aws-cloud-utilities logs search --log-group $LOG_GROUP --query "WARN" --start-time "$START_TIME"

echo "=== Log Aggregation ==="
aws-cloud-utilities logs aggregate --log-group $LOG_GROUP --start-time "$START_TIME" --output json > log-summary.json

echo "=== Export Logs ==="
aws-cloud-utilities logs export --log-group $LOG_GROUP --start-time "$START_TIME" --format json > exported-logs.json
```

### Multi-Service Log Monitoring

```bash
#!/bin/bash
# Monitor logs across multiple services
services=("lambda" "api-gateway" "ecs" "rds")

for service in "${services[@]}"; do
    echo "=== $service Logs ==="
    
    # Find log groups for service
    aws-cloud-utilities logs groups --filter $service
    
    # Search for errors in the last hour
    for log_group in $(aws-cloud-utilities logs groups --filter $service --output json | jq -r '.[].logGroupName'); do
        echo "Checking $log_group for errors..."
        aws-cloud-utilities logs search --log-group $log_group --query "ERROR" --start-time "1 hour ago" --max-results 10
    done
done
```

## Automation and Reporting

### Weekly Report Generation

```bash
#!/bin/bash
# Generate weekly AWS report
WEEK=$(date +%Y-W%U)
REPORT_DIR="reports/$WEEK"
mkdir -p $REPORT_DIR

echo "=== Generating Weekly Report for $WEEK ==="

# Account summary
aws-cloud-utilities account info --output json > $REPORT_DIR/account-info.json

# Resource inventory
aws-cloud-utilities inventory resources --all-regions --output json > $REPORT_DIR/resources.json

# Security audit
aws-cloud-utilities security audit --output json > $REPORT_DIR/security-audit.json

# Cost analysis
aws-cloud-utilities costops analyze --output json > $REPORT_DIR/cost-analysis.json

# Unused resources
aws-cloud-utilities inventory unused-resources --output json > $REPORT_DIR/unused-resources.json

# Health check
aws-cloud-utilities inventory health-check --output json > $REPORT_DIR/health-check.json

# Generate summary
cat > $REPORT_DIR/summary.md << EOF
# AWS Weekly Report - $WEEK

## Summary
- Total resources: $(jq length $REPORT_DIR/resources.json)
- Security findings: $(jq length $REPORT_DIR/security-audit.json)
- Unused resources: $(jq length $REPORT_DIR/unused-resources.json)
- Unhealthy resources: $(jq '[.[] | select(.status != "healthy")] | length' $REPORT_DIR/health-check.json)

## Cost Analysis
- Monthly spend: $(jq '.total_cost' $REPORT_DIR/cost-analysis.json)
- Potential savings: $(jq '.potential_savings' $REPORT_DIR/unused-resources.json)

Generated on: $(date)
EOF

echo "Report generated in $REPORT_DIR/"
```

### Compliance Monitoring

```bash
#!/bin/bash
# Automated compliance monitoring
COMPLIANCE_DIR="compliance/$(date +%Y%m%d)"
mkdir -p $COMPLIANCE_DIR

echo "=== CIS Compliance Check ==="
aws-cloud-utilities security compliance --framework cis --output json > $COMPLIANCE_DIR/cis-compliance.json

echo "=== Tagging Compliance ==="
aws-cloud-utilities inventory tagging-audit --required-tags Environment,Owner,CostCenter --output json > $COMPLIANCE_DIR/tagging-compliance.json

echo "=== Encryption Compliance ==="
aws-cloud-utilities security encryption-status --output json > $COMPLIANCE_DIR/encryption-status.json

echo "=== IAM Compliance ==="
aws-cloud-utilities iam analyze --output json > $COMPLIANCE_DIR/iam-analysis.json

# Generate compliance score
TOTAL_CHECKS=$(jq length $COMPLIANCE_DIR/cis-compliance.json)
PASSED_CHECKS=$(jq '[.[] | select(.status == "PASS")] | length' $COMPLIANCE_DIR/cis-compliance.json)
COMPLIANCE_SCORE=$(echo "scale=2; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc)

echo "=== Compliance Summary ==="
echo "CIS Compliance Score: $COMPLIANCE_SCORE%"
echo "Passed: $PASSED_CHECKS/$TOTAL_CHECKS checks"
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/aws-audit.yml
name: AWS Security Audit
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Install AWS Cloud Utilities
        run: pip install aws-cloud-utilities

      - name: Run Security Audit
        run: |
          aws-cloud-utilities security audit --output json > security-audit.json
          aws-cloud-utilities security public-resources --output json > public-resources.json

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: security-audit-results
          path: |
            security-audit.json
            public-resources.json
```

### Monitoring Integration

```bash
#!/bin/bash
# Integration with monitoring systems
# Send metrics to CloudWatch

# Get resource counts
TOTAL_RESOURCES=$(aws-cloud-utilities inventory resources --output json | jq length)
UNHEALTHY_RESOURCES=$(aws-cloud-utilities inventory health-check --unhealthy-only --output json | jq length)
SECURITY_FINDINGS=$(aws-cloud-utilities security audit --severity high --output json | jq length)

# Send to CloudWatch
aws cloudwatch put-metric-data --namespace "AWS/CloudUtilities" --metric-data \
  MetricName=TotalResources,Value=$TOTAL_RESOURCES,Unit=Count \
  MetricName=UnhealthyResources,Value=$UNHEALTHY_RESOURCES,Unit=Count \
  MetricName=SecurityFindings,Value=$SECURITY_FINDINGS,Unit=Count
```

These examples demonstrate practical, real-world usage patterns that can be adapted for specific environments and requirements.
