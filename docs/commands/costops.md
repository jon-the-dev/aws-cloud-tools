# Cost Optimization Commands

Cost optimization and pricing tools for AWS resource cost analysis and optimization recommendations.

## Commands

### `pricing`

Get AWS service pricing information from the AWS Pricing API.

```bash
aws-cloud-utilities costops pricing [OPTIONS]
```

**Options:**
- `--service SERVICE` - Specific AWS service to get pricing for (e.g., AmazonEC2, AmazonS3)
- `--output-dir DIR` - Output directory for pricing data (default: `./aws_pricing_<timestamp>`)
- `--list-services` - List all available AWS services for pricing
- `--format FORMAT` - Output format: `json` (raw data) or `summary` (processed, default)

**Examples:**
```bash
# List all available services
aws-cloud-utilities costops pricing --list-services

# Get EC2 pricing information
aws-cloud-utilities costops pricing --service AmazonEC2

# Get S3 pricing in specific output directory
aws-cloud-utilities costops pricing --service AmazonS3 --output-dir ./pricing-data

# Get pricing in raw JSON format
aws-cloud-utilities costops pricing --service AmazonRDS --format json
```

---

### `cost-analysis`

Analyze AWS costs using Cost Explorer for trends and spending patterns.

```bash
aws-cloud-utilities costops cost-analysis [OPTIONS]
```

**Options:**
- `--months MONTHS` - Number of months to analyze (default: 3)
- `--service SERVICE` - Specific AWS service to analyze (e.g., "Amazon Elastic Compute Cloud - Compute")
- `--group-by DIMENSION` - Group costs by: `service`, `usage_type`, `region`, or `account` (default: service)
- `--output-file FILE` - Output file for cost analysis (supports .json, .yaml, .csv)

**Examples:**
```bash
# Analyze costs for last 3 months
aws-cloud-utilities costops cost-analysis

# Analyze EC2 costs for last 6 months
aws-cloud-utilities costops cost-analysis --months 6 --service "Amazon Elastic Compute Cloud - Compute"

# Group by region
aws-cloud-utilities costops cost-analysis --group-by region

# Save to file
aws-cloud-utilities costops cost-analysis --output-file costs.json
```

---

### `ebs-optimization`

Analyze EBS volumes for cost optimization opportunities (e.g., gp2 to gp3 upgrades, underutilized volumes).

```bash
aws-cloud-utilities costops ebs-optimization [OPTIONS]
```

**Options:**
- `--region REGION` - AWS region to analyze (default: current region)
- `--all-regions` - Analyze EBS volumes across all regions
- `--volume-type TYPE` - Filter by specific volume type (`gp2`, `gp3`, `io1`, `io2`, `st1`, `sc1`, `standard`)
- `--show-recommendations` - Show optimization recommendations (default: enabled)
- `--include-cost-estimates` - Include cost savings estimates
- `--output-file FILE` - Output file for EBS analysis (supports .json, .yaml, .csv)
- `--tag-key KEY` - Filter EBS volumes by tag key
- `--tag-value VALUE` - Filter EBS volumes by tag value (requires `--tag-key`)

**Examples:**
```bash
# Analyze EBS volumes in current region
aws-cloud-utilities costops ebs-optimization

# Analyze all gp2 volumes across all regions
aws-cloud-utilities costops ebs-optimization --all-regions --volume-type gp2

# Include cost savings estimates
aws-cloud-utilities costops ebs-optimization --include-cost-estimates

# Filter by environment tag
aws-cloud-utilities costops ebs-optimization --tag-key Environment --tag-value production

# Save analysis to file
aws-cloud-utilities costops ebs-optimization --output-file ebs-analysis.json
```

---

### `usage-metrics`

Get detailed usage metrics for a specific AWS service using Cost Explorer.

```bash
aws-cloud-utilities costops usage-metrics SERVICE_NAME [OPTIONS]
```

**Arguments:**
- `SERVICE_NAME` - Name of the AWS service to analyze (required)

**Options:**
- `--months MONTHS` - Number of months to analyze (default: 3)
- `--metric-type TYPE` - Type of metrics: `cost`, `usage`, or `both` (default: both)
- `--group-by DIMENSION` - Group metrics by: `usage_type`, `region`, `instance_type`, or `operation` (default: usage_type)
- `--output-file FILE` - Output file for usage metrics (supports .json, .yaml, .csv)

**Examples:**
```bash
# Get EC2 usage metrics
aws-cloud-utilities costops usage-metrics "Amazon Elastic Compute Cloud - Compute"

# Get S3 cost metrics for last 6 months
aws-cloud-utilities costops usage-metrics "Amazon Simple Storage Service" --months 6 --metric-type cost

# Group by region
aws-cloud-utilities costops usage-metrics "Amazon RDS Service" --group-by region

# Save to file
aws-cloud-utilities costops usage-metrics "AWS Lambda" --output-file lambda-usage.json
```

---

### `spot-pricing`

Collect and analyze EC2 spot pricing data across regions.

```bash
aws-cloud-utilities costops spot-pricing [OPTIONS]
```

**Options:**
- `--region REGION` - Specific AWS region to collect spot pricing for
- `--all-regions` - Collect spot pricing data from all regions
- `--time-range HOURS` - Time range in hours for spot pricing data (default: 24)
- `--instance-types TYPES` - Comma-separated list of instance types (e.g., `m5.large,c5.xlarge`)
- `--product-description DESC` - Product description filter (default: "Linux/UNIX")
- `--output-dir DIR` - Output directory for spot pricing data (default: `./spot_pricing_<timestamp>`)
- `--output-file FILE` - Output file for consolidated analysis (supports .json, .yaml, .csv)

**Examples:**
```bash
# Collect spot pricing for current region
aws-cloud-utilities costops spot-pricing

# Collect from all regions for last 48 hours
aws-cloud-utilities costops spot-pricing --all-regions --time-range 48

# Filter by specific instance types
aws-cloud-utilities costops spot-pricing --instance-types "m5.large,m5.xlarge,c5.large"

# Windows instances
aws-cloud-utilities costops spot-pricing --product-description "Windows" --all-regions

# Save analysis to file
aws-cloud-utilities costops spot-pricing --all-regions --output-file spot-analysis.json
```

---

### `spot-analysis`

Analyze previously collected spot pricing data to find cheapest options.

```bash
aws-cloud-utilities costops spot-analysis DATA_DIRECTORY [OPTIONS]
```

**Arguments:**
- `DATA_DIRECTORY` - Path to directory containing spot pricing data (required)

**Options:**
- `--top-n N` - Number of top cheapest instances to show (default: 10)
- `--estimate-period DAYS` - Period in days for cost estimation (default: 30)
- `--instance-type-filter PATTERN` - Filter by instance type pattern (e.g., "m5", "c5.large")
- `--region-filter REGION` - Filter results by region
- `--output-file FILE` - Output file for analysis results (supports .json, .yaml, .csv)

**Examples:**
```bash
# Analyze collected spot pricing data
aws-cloud-utilities costops spot-analysis ./spot_pricing_20240115

# Show top 20 cheapest instances
aws-cloud-utilities costops spot-analysis ./spot_pricing_20240115 --top-n 20

# Filter by m5 instance types
aws-cloud-utilities costops spot-analysis ./spot_pricing_20240115 --instance-type-filter m5

# Filter by region
aws-cloud-utilities costops spot-analysis ./spot_pricing_20240115 --region-filter us-east-1

# Estimate costs for 90 days
aws-cloud-utilities costops spot-analysis ./spot_pricing_20240115 --estimate-period 90 --output-file analysis.json
```

---

## Global Options

All cost optimization commands support:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

---

## Complete Workflow Examples

### Monthly Cost Review

```bash
#!/bin/bash
# Comprehensive monthly cost optimization review

echo "=== Cost Analysis ==="
aws-cloud-utilities costops cost-analysis --months 3 --output-file monthly-costs.json

echo "=== EC2 Cost Breakdown ==="
aws-cloud-utilities costops cost-analysis --service "Amazon Elastic Compute Cloud - Compute" --group-by region

echo "=== EBS Optimization Opportunities ==="
aws-cloud-utilities costops ebs-optimization --all-regions --include-cost-estimates

echo "=== S3 Usage Metrics ==="
aws-cloud-utilities costops usage-metrics "Amazon Simple Storage Service" --months 6
```

### Spot Instance Cost Optimization

```bash
#!/bin/bash
# Find cheapest spot instances for workload

echo "=== Collecting Spot Pricing Data ==="
aws-cloud-utilities costops spot-pricing --all-regions --time-range 72 --output-dir ./spot-data

echo "=== Analyzing Best Spot Options ==="
aws-cloud-utilities costops spot-analysis ./spot-data --top-n 20 --estimate-period 30

echo "=== M5 Instance Analysis ==="
aws-cloud-utilities costops spot-analysis ./spot-data --instance-type-filter m5 --output-file m5-analysis.json

echo "=== C5 Instance Analysis ==="
aws-cloud-utilities costops spot-analysis ./spot-data --instance-type-filter c5 --output-file c5-analysis.json
```

### Service-Specific Cost Analysis

```bash
#!/bin/bash
# Analyze costs for specific AWS services

services=(
    "Amazon Elastic Compute Cloud - Compute"
    "Amazon Simple Storage Service"
    "Amazon RDS Service"
    "AWS Lambda"
)

for service in "${services[@]}"; do
    echo "=== Analyzing $service ==="
    aws-cloud-utilities costops cost-analysis --service "$service" --months 6
    aws-cloud-utilities costops usage-metrics "$service" --months 6
done
```

### EBS Optimization Campaign

```bash
#!/bin/bash
# Comprehensive EBS optimization analysis

echo "=== All EBS Volumes ==="
aws-cloud-utilities costops ebs-optimization --all-regions --include-cost-estimates --output-file all-volumes.json

echo "=== GP2 Volumes (Upgrade to GP3) ==="
aws-cloud-utilities costops ebs-optimization --all-regions --volume-type gp2 --output-file gp2-upgrade.json

echo "=== IO1 Volumes (Upgrade to IO2) ==="
aws-cloud-utilities costops ebs-optimization --all-regions --volume-type io1 --output-file io1-upgrade.json

echo "=== Production Environment Only ==="
aws-cloud-utilities costops ebs-optimization --all-regions --tag-key Environment --tag-value production
```

---

## Common Use Cases

### 1. Find AWS Service Pricing
```bash
# List available services
aws-cloud-utilities costops pricing --list-services

# Get specific service pricing
aws-cloud-utilities costops pricing --service AmazonEC2
```

### 2. Analyze Monthly Spending
```bash
# Overall cost analysis
aws-cloud-utilities costops cost-analysis --months 6

# By service
aws-cloud-utilities costops cost-analysis --group-by service

# By region
aws-cloud-utilities costops cost-analysis --group-by region
```

### 3. EBS Cost Optimization
```bash
# Find all gp2 volumes that can be upgraded to gp3
aws-cloud-utilities costops ebs-optimization --all-regions --volume-type gp2 --include-cost-estimates
```

### 4. Spot Instance Price Shopping
```bash
# Collect pricing data
aws-cloud-utilities costops spot-pricing --all-regions --time-range 72

# Find cheapest options
aws-cloud-utilities costops spot-analysis ./spot_pricing_<timestamp> --top-n 20
```

### 5. Service Usage Tracking
```bash
# Track EC2 usage
aws-cloud-utilities costops usage-metrics "Amazon Elastic Compute Cloud - Compute" --months 12

# Track Lambda costs
aws-cloud-utilities costops usage-metrics "AWS Lambda" --metric-type cost
```

---

## Output Formats

All commands support multiple output formats:

```bash
# Table format (default, human-readable)
aws-cloud-utilities costops cost-analysis

# JSON for automation and scripting
aws-cloud-utilities costops cost-analysis --output json

# CSV for spreadsheet analysis
aws-cloud-utilities costops ebs-optimization --all-regions --output csv

# YAML for configuration
aws-cloud-utilities costops pricing --service AmazonEC2 --output yaml
```

---

## Tips and Best Practices

1. **Regular Cost Reviews**: Run monthly cost analysis to track spending trends
2. **EBS Optimization**: Regularly scan for gp2→gp3 upgrade opportunities (typically 20% savings)
3. **Spot Pricing**: Collect pricing data over 48-72 hours for accurate trends
4. **Tag Filtering**: Use tags to analyze costs by environment, project, or team
5. **Output Files**: Save analysis results with timestamps for historical comparison
6. **Multi-Region**: Always use `--all-regions` for comprehensive coverage
7. **Cost Explorer**: The `cost-analysis` and `usage-metrics` commands require Cost Explorer to be enabled in your AWS account
