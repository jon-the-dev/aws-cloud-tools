# Cost Optimization Commands

Cost optimization and pricing tools for AWS resource cost analysis and optimization recommendations.

## Commands

### `pricing`

Get AWS service pricing information.

```bash
aws-cloud-utilities costops pricing --service SERVICE
```

**Options:**
- `--service SERVICE` - AWS service (ec2, rds, lambda, etc.)
- `--region REGION` - Specific region for pricing
- `--instance-type TYPE` - Filter by instance type
- `--operating-system OS` - Filter by OS (Linux, Windows)

**Examples:**
```bash
# EC2 pricing
aws-cloud-utilities costops pricing --service ec2

# RDS pricing in specific region
aws-cloud-utilities costops pricing --service rds --region us-west-2

# Specific instance type
aws-cloud-utilities costops pricing --service ec2 --instance-type m5.large
```

### `gpu-spots`

Find cheapest GPU spot instances across regions.

```bash
aws-cloud-utilities costops gpu-spots
```

**Options:**
- `--instance-type TYPE` - GPU instance type (p3.2xlarge, g4dn.xlarge, etc.)
- `--max-price PRICE` - Maximum price per hour
- `--regions REGIONS` - Comma-separated list of regions
- `--availability-zones` - Include AZ-level pricing

**Examples:**
```bash
# All GPU spot prices
aws-cloud-utilities costops gpu-spots

# Specific instance type
aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge

# With price limit
aws-cloud-utilities costops gpu-spots --max-price 1.00

# Specific regions
aws-cloud-utilities costops gpu-spots --regions us-east-1,us-west-2
```

### `analyze`

Analyze current AWS costs and usage.

```bash
aws-cloud-utilities costops analyze
```

**Options:**
- `--start-date DATE` - Analysis start date (YYYY-MM-DD)
- `--end-date DATE` - Analysis end date (YYYY-MM-DD)
- `--group-by DIMENSION` - Group by service, region, or account
- `--service SERVICE` - Analyze specific service

**Examples:**
```bash
# Current month analysis
aws-cloud-utilities costops analyze

# Last 30 days
aws-cloud-utilities costops analyze --start-date 2024-01-01 --end-date 2024-01-31

# Group by service
aws-cloud-utilities costops analyze --group-by service

# EC2 costs only
aws-cloud-utilities costops analyze --service ec2
```

### `recommendations`

Get cost optimization recommendations.

```bash
aws-cloud-utilities costops recommendations
```

**Options:**
- `--service SERVICE` - Recommendations for specific service
- `--min-savings AMOUNT` - Minimum savings threshold
- `--recommendation-type TYPE` - Type of recommendation

**Examples:**
```bash
# All recommendations
aws-cloud-utilities costops recommendations

# EC2 recommendations only
aws-cloud-utilities costops recommendations --service ec2

# High-impact recommendations
aws-cloud-utilities costops recommendations --min-savings 100
```

### `savings-plans`

Analyze Savings Plans opportunities.

```bash
aws-cloud-utilities costops savings-plans
```

**Options:**
- `--term TERM` - Savings plan term (1year, 3year)
- `--payment-option OPTION` - Payment option (no-upfront, partial-upfront, all-upfront)
- `--service SERVICE` - Service for savings plans

**Examples:**
```bash
# All savings plans opportunities
aws-cloud-utilities costops savings-plans

# 1-year compute savings plans
aws-cloud-utilities costops savings-plans --term 1year

# EC2 instance savings plans
aws-cloud-utilities costops savings-plans --service ec2
```

### `rightsizing`

Get EC2 rightsizing recommendations.

```bash
aws-cloud-utilities costops rightsizing
```

**Options:**
- `--instance-id ID` - Specific instance analysis
- `--min-savings AMOUNT` - Minimum savings threshold
- `--lookback-period DAYS` - Analysis period in days

**Examples:**
```bash
# All rightsizing recommendations
aws-cloud-utilities costops rightsizing

# Specific instance
aws-cloud-utilities costops rightsizing --instance-id i-1234567890abcdef0

# High-impact recommendations
aws-cloud-utilities costops rightsizing --min-savings 50
```

### `reserved-instances`

Analyze Reserved Instance utilization and recommendations.

```bash
aws-cloud-utilities costops reserved-instances
```

**Options:**
- `--service SERVICE` - Service (ec2, rds, elasticache)
- `--utilization-threshold PERCENT` - Utilization threshold
- `--recommendation-type TYPE` - purchase, modify, or terminate

**Examples:**
```bash
# RI utilization analysis
aws-cloud-utilities costops reserved-instances

# EC2 RI recommendations
aws-cloud-utilities costops reserved-instances --service ec2

# Low utilization RIs
aws-cloud-utilities costops reserved-instances --utilization-threshold 50
```

## Global Options

All cost optimization commands support:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Monthly Cost Review

```bash
#!/bin/bash
# Monthly cost optimization review
echo "=== Cost Analysis ==="
aws-cloud-utilities costops analyze --output json > monthly-costs.json

echo "=== Optimization Recommendations ==="
aws-cloud-utilities costops recommendations --output json > recommendations.json

echo "=== Rightsizing Opportunities ==="
aws-cloud-utilities costops rightsizing --output json > rightsizing.json

echo "=== Savings Plans Analysis ==="
aws-cloud-utilities costops savings-plans --output json > savings-plans.json
```

### GPU Cost Optimization

```bash
#!/bin/bash
# Find cheapest GPU instances
echo "=== P3 Instance Pricing ==="
aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge

echo "=== G4 Instance Pricing ==="
aws-cloud-utilities costops gpu-spots --instance-type g4dn.xlarge

echo "=== Best GPU Deals ==="
aws-cloud-utilities costops gpu-spots --max-price 0.50
```

### Service-Specific Analysis

```bash
#!/bin/bash
# EC2 cost optimization
aws-cloud-utilities costops analyze --service ec2
aws-cloud-utilities costops recommendations --service ec2
aws-cloud-utilities costops rightsizing
aws-cloud-utilities costops reserved-instances --service ec2
```

## Common Use Cases

1. **Find Cheapest Resources**
   ```bash
   aws-cloud-utilities costops gpu-spots --instance-type p3.2xlarge
   aws-cloud-utilities costops pricing --service ec2 --instance-type m5.large
   ```

2. **Cost Analysis and Optimization**
   ```bash
   aws-cloud-utilities costops analyze
   aws-cloud-utilities costops recommendations
   ```

3. **Reserved Instance Management**
   ```bash
   aws-cloud-utilities costops reserved-instances
   aws-cloud-utilities costops savings-plans
   ```

4. **Rightsizing Analysis**
   ```bash
   aws-cloud-utilities costops rightsizing --min-savings 100
   ```

## Output Formats

All commands support multiple output formats:

```bash
# Table format (default)
aws-cloud-utilities costops analyze

# JSON for automation
aws-cloud-utilities costops recommendations --output json

# CSV for spreadsheets
aws-cloud-utilities costops gpu-spots --output csv

# YAML for configuration
aws-cloud-utilities costops savings-plans --output yaml
```
