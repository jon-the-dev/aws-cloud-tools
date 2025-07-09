# Inventory Commands

Resource discovery and inventory commands for comprehensive AWS resource management and analysis.

## Commands

### `resources`

List all AWS resources across services and regions.

```bash
aws-cloud-utilities inventory resources
```

**Options:**
- `--service SERVICE` - Filter by AWS service (ec2, s3, rds, etc.)
- `--region REGION` - Specific region
- `--all-regions` - Scan all regions
- `--tag KEY=VALUE` - Filter by tag
- `--resource-type TYPE` - Filter by resource type

**Examples:**
```bash
# All resources
aws-cloud-utilities inventory resources

# EC2 resources only
aws-cloud-utilities inventory resources --service ec2

# All regions
aws-cloud-utilities inventory resources --all-regions

# Tagged resources
aws-cloud-utilities inventory resources --tag Environment=Production

# Specific resource type
aws-cloud-utilities inventory resources --resource-type instance
```

### `unused-resources`

Find potentially unused or idle AWS resources.

```bash
aws-cloud-utilities inventory unused-resources
```

**Detects:**
- Stopped EC2 instances
- Unattached EBS volumes
- Unused Elastic IPs
- Empty S3 buckets
- Idle load balancers
- Unused security groups

**Options:**
- `--service SERVICE` - Check specific service
- `--age-threshold DAYS` - Minimum age for unused resources
- `--include-recent` - Include recently created resources

**Examples:**
```bash
# All unused resources
aws-cloud-utilities inventory unused-resources

# EC2 unused resources
aws-cloud-utilities inventory unused-resources --service ec2

# Resources unused for 30+ days
aws-cloud-utilities inventory unused-resources --age-threshold 30
```

### `health-check`

Check health status of AWS resources.

```bash
aws-cloud-utilities inventory health-check
```

**Checks:**
- EC2 instance status
- RDS database status
- Load balancer health
- Auto Scaling group health
- ECS service health

**Options:**
- `--service SERVICE` - Check specific service
- `--unhealthy-only` - Show only unhealthy resources
- `--include-warnings` - Include warning states

**Examples:**
```bash
# All resource health
aws-cloud-utilities inventory health-check

# Unhealthy resources only
aws-cloud-utilities inventory health-check --unhealthy-only

# EC2 health check
aws-cloud-utilities inventory health-check --service ec2
```

### `tagging-audit`

Audit resource tagging compliance.

```bash
aws-cloud-utilities inventory tagging-audit
```

**Checks:**
- Missing required tags
- Tag value compliance
- Tagging consistency
- Cost allocation tags

**Options:**
- `--required-tags TAGS` - Comma-separated required tags
- `--tag-policy FILE` - Tag policy file
- `--untagged-only` - Show only untagged resources

**Examples:**
```bash
# Basic tagging audit
aws-cloud-utilities inventory tagging-audit

# Check required tags
aws-cloud-utilities inventory tagging-audit --required-tags Environment,Owner,Project

# Untagged resources only
aws-cloud-utilities inventory tagging-audit --untagged-only
```

### `cost-analysis`

Analyze resource costs and usage patterns.

```bash
aws-cloud-utilities inventory cost-analysis
```

**Analysis includes:**
- Resource cost breakdown
- Usage patterns
- Cost trends
- Optimization opportunities

**Options:**
- `--service SERVICE` - Analyze specific service
- `--time-period PERIOD` - Analysis time period
- `--group-by DIMENSION` - Group by tag, service, or region

**Examples:**
```bash
# All resource costs
aws-cloud-utilities inventory cost-analysis

# EC2 cost analysis
aws-cloud-utilities inventory cost-analysis --service ec2

# Group by environment tag
aws-cloud-utilities inventory cost-analysis --group-by tag:Environment
```

### `compliance-check`

Check resource compliance against policies.

```bash
aws-cloud-utilities inventory compliance-check
```

**Checks:**
- Resource configuration compliance
- Security compliance
- Tagging compliance
- Naming convention compliance

**Options:**
- `--policy-file FILE` - Compliance policy file
- `--framework FRAMEWORK` - Compliance framework
- `--non-compliant-only` - Show only non-compliant resources

**Examples:**
```bash
# Basic compliance check
aws-cloud-utilities inventory compliance-check

# Custom policy
aws-cloud-utilities inventory compliance-check --policy-file compliance.yaml

# Non-compliant resources only
aws-cloud-utilities inventory compliance-check --non-compliant-only
```

### `resource-map`

Generate resource relationship map.

```bash
aws-cloud-utilities inventory resource-map
```

**Maps:**
- Resource dependencies
- Network relationships
- Security group associations
- IAM role assignments

**Options:**
- `--resource-id ID` - Map specific resource
- `--depth LEVEL` - Relationship depth
- `--format FORMAT` - Output format (json, dot, svg)

**Examples:**
```bash
# Full resource map
aws-cloud-utilities inventory resource-map

# Specific instance map
aws-cloud-utilities inventory resource-map --resource-id i-1234567890abcdef0

# DOT format for visualization
aws-cloud-utilities inventory resource-map --format dot > resources.dot
```

## Global Options

All inventory commands support:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Complete Resource Inventory

```bash
#!/bin/bash
# Complete resource inventory
echo "=== All Resources ==="
aws-cloud-utilities inventory resources --all-regions --output json > complete-inventory.json

echo "=== Resource Health ==="
aws-cloud-utilities inventory health-check --output json > health-status.json

echo "=== Tagging Audit ==="
aws-cloud-utilities inventory tagging-audit --output json > tagging-audit.json
```

### Cost Optimization Discovery

```bash
#!/bin/bash
# Find cost optimization opportunities
echo "=== Unused Resources ==="
aws-cloud-utilities inventory unused-resources --output json > unused-resources.json

echo "=== Cost Analysis ==="
aws-cloud-utilities inventory cost-analysis --output json > cost-analysis.json

echo "=== Resource Utilization ==="
aws-cloud-utilities inventory health-check --include-warnings
```

### Compliance Reporting

```bash
#!/bin/bash
# Generate compliance report
echo "=== Resource Inventory ==="
aws-cloud-utilities inventory resources --output csv > resources.csv

echo "=== Tagging Compliance ==="
aws-cloud-utilities inventory tagging-audit --required-tags Environment,Owner,CostCenter

echo "=== Security Compliance ==="
aws-cloud-utilities inventory compliance-check --framework cis
```

### Multi-Region Analysis

```bash
#!/bin/bash
# Multi-region resource analysis
for region in us-east-1 us-west-2 eu-west-1; do
    echo "=== $region Resources ==="
    aws-cloud-utilities --region $region inventory resources --output json > ${region}-resources.json
    
    echo "=== $region Unused Resources ==="
    aws-cloud-utilities --region $region inventory unused-resources
done
```

## Common Use Cases

1. **Resource Discovery**
   ```bash
   aws-cloud-utilities inventory resources --all-regions
   aws-cloud-utilities inventory resource-map
   ```

2. **Cost Optimization**
   ```bash
   aws-cloud-utilities inventory unused-resources
   aws-cloud-utilities inventory cost-analysis
   ```

3. **Compliance Auditing**
   ```bash
   aws-cloud-utilities inventory tagging-audit --required-tags Environment,Owner
   aws-cloud-utilities inventory compliance-check
   ```

4. **Health Monitoring**
   ```bash
   aws-cloud-utilities inventory health-check --unhealthy-only
   ```

## Output Formats

### Table Format (Default)
Human-readable tables with resource information.

### JSON Format
Structured data for automation and integration:
```bash
aws-cloud-utilities inventory resources --output json
```

### CSV Format
Spreadsheet-compatible format:
```bash
aws-cloud-utilities inventory resources --output csv > resources.csv
```

### YAML Format
Configuration-friendly format:
```bash
aws-cloud-utilities inventory resources --output yaml
```

## Integration Examples

### With Cost Optimization
```bash
# Find unused resources and analyze costs
aws-cloud-utilities inventory unused-resources --output json | \
  jq '.[] | select(.estimated_monthly_cost > 100)'
```

### With Security Tools
```bash
# Find untagged resources for security review
aws-cloud-utilities inventory tagging-audit --untagged-only --output json | \
  jq '.[] | select(.resource_type == "security-group")'
```

### With Automation
```bash
# Daily inventory report
aws-cloud-utilities inventory resources --output json > daily-inventory-$(date +%Y%m%d).json
aws-cloud-utilities inventory unused-resources --output json > unused-$(date +%Y%m%d).json
```
