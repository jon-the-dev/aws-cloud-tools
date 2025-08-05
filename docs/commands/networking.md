# Networking Commands

Network utilities and analysis commands for AWS networking operations.

## Commands

### `ip-ranges`

Get AWS IP ranges for services and regions with filtering options.

```bash
aws-cloud-utilities networking ip-ranges
```

**Options:**
- `--service SERVICE` - Filter by AWS service (e.g., EC2, S3, CLOUDFRONT, ROUTE53)
- `--region REGION` - Filter by AWS region
- `--network-border-group GROUP` - Filter by network border group
- `--output-file FILE` - Save results to file
- `--format FORMAT` - Output format (cidr, json, csv) [default: table]

**Examples:**
```bash
# Get all AWS IP ranges
aws-cloud-utilities networking ip-ranges

# Get IP ranges for specific service
aws-cloud-utilities networking ip-ranges --service EC2

# Get IP ranges for specific region
aws-cloud-utilities networking ip-ranges --region us-east-1

# Get CloudFront IP ranges
aws-cloud-utilities networking ip-ranges --service CLOUDFRONT

# Save to file in CIDR format
aws-cloud-utilities networking ip-ranges --service S3 --format cidr --output-file s3-ranges.txt

# Get ranges for specific service and region
aws-cloud-utilities networking ip-ranges --service EC2 --region us-west-2
```

### `ip-summary`

Get summary statistics of AWS IP ranges by service and region.

```bash
aws-cloud-utilities networking ip-summary
```

**Options:**
- `--by-service` - Group summary by AWS service
- `--by-region` - Group summary by AWS region
- `--include-ipv6` - Include IPv6 ranges in summary
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Get overall IP range summary
aws-cloud-utilities networking ip-summary

# Summary grouped by service
aws-cloud-utilities networking ip-summary --by-service

# Summary grouped by region
aws-cloud-utilities networking ip-summary --by-region

# Include IPv6 ranges
aws-cloud-utilities networking ip-summary --include-ipv6

# Save summary to file
aws-cloud-utilities networking ip-summary --by-service --output-file ip-summary.json
```

## Global Options

All networking commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region (for API calls, not filtering)
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Security Group Rule Generation

```bash
#!/bin/bash
# Generate security group rules for AWS services

SERVICE="S3"
OUTPUT_DIR="./security-rules-$(date +%Y%m%d)"

mkdir -p $OUTPUT_DIR

echo "=== Getting $SERVICE IP Ranges ==="
aws-cloud-utilities networking ip-ranges --service $SERVICE --format cidr --output-file $OUTPUT_DIR/${SERVICE,,}-ranges.txt

echo "=== Generating Security Group Rules ==="
# Convert CIDR ranges to security group rules format
while read cidr; do
    echo "aws ec2 authorize-security-group-ingress --group-id sg-xxxxxxxx --protocol tcp --port 443 --cidr $cidr"
done < $OUTPUT_DIR/${SERVICE,,}-ranges.txt > $OUTPUT_DIR/${SERVICE,,}-sg-rules.sh

chmod +x $OUTPUT_DIR/${SERVICE,,}-sg-rules.sh

echo "=== Rules Generated ==="
echo "Security group rules saved to: $OUTPUT_DIR/${SERVICE,,}-sg-rules.sh"
```

### Firewall Configuration Script

```bash
#!/bin/bash
# Generate firewall rules for AWS services

SERVICES=("EC2" "S3" "CLOUDFRONT" "ROUTE53")
FIREWALL_DIR="./firewall-rules-$(date +%Y%m%d)"

mkdir -p $FIREWALL_DIR

for service in "${SERVICES[@]}"; do
    echo "=== Processing $service ==="
    
    # Get IP ranges
    aws-cloud-utilities networking ip-ranges --service $service --format cidr --output-file $FIREWALL_DIR/${service,,}-ranges.txt
    
    # Generate iptables rules
    echo "# $service IP ranges" > $FIREWALL_DIR/${service,,}-iptables.rules
    while read cidr; do
        echo "iptables -A OUTPUT -d $cidr -j ACCEPT" >> $FIREWALL_DIR/${service,,}-iptables.rules
    done < $FIREWALL_DIR/${service,,}-ranges.txt
    
    echo "$service rules generated"
done

echo "=== Firewall Rules Complete ==="
echo "Rules saved to: $FIREWALL_DIR"
```

### Network Analysis Report

```bash
#!/bin/bash
# Generate comprehensive network analysis report

REPORT_DIR="./network-analysis-$(date +%Y%m%d)"
mkdir -p $REPORT_DIR

echo "=== AWS IP Range Analysis ==="

# Overall summary
aws-cloud-utilities networking ip-summary --output-file $REPORT_DIR/overall-summary.json

# Service breakdown
aws-cloud-utilities networking ip-summary --by-service --output-file $REPORT_DIR/service-summary.json

# Region breakdown
aws-cloud-utilities networking ip-summary --by-region --output-file $REPORT_DIR/region-summary.json

# IPv6 analysis
aws-cloud-utilities networking ip-summary --include-ipv6 --output-file $REPORT_DIR/ipv6-summary.json

# Service-specific ranges
SERVICES=("EC2" "S3" "CLOUDFRONT" "ROUTE53" "DYNAMODB")
for service in "${SERVICES[@]}"; do
    aws-cloud-utilities networking ip-ranges --service $service --output-file $REPORT_DIR/${service,,}-ranges.json
done

echo "=== Analysis Complete ==="
echo "Report saved to: $REPORT_DIR"
```

### Regional Network Planning

```bash
#!/bin/bash
# Plan network configuration for specific regions

REGIONS=("us-east-1" "us-west-2" "eu-west-1" "ap-southeast-1")
PLANNING_DIR="./network-planning-$(date +%Y%m%d)"

mkdir -p $PLANNING_DIR

for region in "${REGIONS[@]}"; do
    echo "=== Analyzing $region ==="
    
    # Get EC2 ranges for the region
    aws-cloud-utilities networking ip-ranges --service EC2 --region $region --output-file $PLANNING_DIR/ec2-$region.json
    
    # Get S3 ranges for the region
    aws-cloud-utilities networking ip-ranges --service S3 --region $region --output-file $PLANNING_DIR/s3-$region.json
    
    echo "$region analysis complete"
done

# Generate regional summary
aws-cloud-utilities networking ip-summary --by-region --output-file $PLANNING_DIR/regional-summary.json

echo "=== Network Planning Complete ==="
echo "Planning data saved to: $PLANNING_DIR"
```

## Common Use Cases

1. **Security Group Configuration**
   ```bash
   aws-cloud-utilities networking ip-ranges --service S3 --format cidr
   aws-cloud-utilities networking ip-ranges --service CLOUDFRONT --format cidr
   ```

2. **Firewall Rule Generation**
   ```bash
   aws-cloud-utilities networking ip-ranges --service EC2 --region us-east-1 --format cidr
   aws-cloud-utilities networking ip-ranges --service ROUTE53 --format cidr
   ```

3. **Network Planning**
   ```bash
   aws-cloud-utilities networking ip-summary --by-service
   aws-cloud-utilities networking ip-summary --by-region
   ```

4. **Compliance and Auditing**
   ```bash
   aws-cloud-utilities networking ip-ranges --output-file aws-ip-ranges.json
   aws-cloud-utilities networking ip-summary --include-ipv6
   ```

## Integration with Other Tools

Networking commands work well with other AWS Cloud Utilities:

```bash
# Combine with security audit
aws-cloud-utilities security blue-team-audit
aws-cloud-utilities networking ip-ranges --service EC2

# Combine with inventory
aws-cloud-utilities inventory resources --resource-type vpc
aws-cloud-utilities networking ip-summary --by-region
```

## Use Cases by Service

### EC2 Security Groups
```bash
# Get EC2 IP ranges for security group rules
aws-cloud-utilities networking ip-ranges --service EC2 --region us-east-1 --format cidr
```

### CloudFront Access Control
```bash
# Get CloudFront IP ranges for origin access control
aws-cloud-utilities networking ip-ranges --service CLOUDFRONT --format cidr
```

### S3 Bucket Policies
```bash
# Get S3 IP ranges for bucket policy conditions
aws-cloud-utilities networking ip-ranges --service S3 --format cidr
```

### Route 53 Health Checks
```bash
# Get Route 53 IP ranges for health check allowlists
aws-cloud-utilities networking ip-ranges --service ROUTE53 --format cidr
```

## Best Practices

- Regularly update firewall rules with latest AWS IP ranges
- Use service-specific IP ranges rather than broad ranges when possible
- Consider regional requirements when filtering IP ranges
- Automate IP range updates in security configurations
- Monitor AWS IP range changes for security impact
- Use CIDR format for most firewall and security group applications
- Include IPv6 ranges in modern network configurations
