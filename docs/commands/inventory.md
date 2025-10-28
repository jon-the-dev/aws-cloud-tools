# Inventory Commands

Resource discovery and inventory commands for comprehensive AWS resource management and analysis.

## Commands

### `scan`

Perform a comprehensive AWS resource inventory scan across services and regions.

```bash
aws-cloud-utilities inventory scan [OPTIONS]
```

**Features:**
- Scans multiple AWS services across regions
- Discovers and catalogs all resources
- Collects resource metadata and tags
- Generates comprehensive inventory reports
- Supports parallel region scanning for performance

**Options:**
- `--services SERVICES` - Comma-separated list of services to scan (default: all)
- `--regions REGIONS` - Comma-separated list of regions (default: all enabled regions)
- `--all-regions` - Scan all AWS regions
- `--include-tags` - Include resource tags in output
- `--output-file FILE` - Save results to file (json, yaml, csv)
- `--parallel-regions NUM` - Number of regions to scan in parallel
- `--resource-types TYPES` - Filter by specific resource types

**Supported Services:**
- EC2 (instances, volumes, security groups, VPCs)
- S3 (buckets)
- RDS (database instances)
- Lambda (functions)
- DynamoDB (tables)
- ECS (clusters, services, tasks)
- And many more...

**Examples:**
```bash
# Complete inventory scan
aws-cloud-utilities inventory scan

# Scan all regions
aws-cloud-utilities inventory scan --all-regions

# Scan specific services
aws-cloud-utilities inventory scan --services ec2,s3,rds

# Scan specific regions
aws-cloud-utilities inventory scan --regions us-east-1,us-west-2

# Include resource tags
aws-cloud-utilities inventory scan --include-tags

# Parallel scanning for performance
aws-cloud-utilities inventory scan --all-regions --parallel-regions 4

# Save to file
aws-cloud-utilities inventory scan --output-file inventory.json
```

### `workspaces`

List Amazon WorkSpaces instances and configurations.

```bash
aws-cloud-utilities inventory workspaces [OPTIONS]
```

**Output includes:**
- WorkSpace ID and directory ID
- User name
- WorkSpace state and running mode
- Compute type and bundle ID
- IP address
- Volume encryption status
- Root and user volume sizes

**Options:**
- `--directory-id DIR_ID` - Filter by directory ID
- `--user-name USER` - Filter by user name
- `--region REGION` - Specific region (default: current region)
- `--all-regions` - List WorkSpaces from all regions
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all WorkSpaces
aws-cloud-utilities inventory workspaces

# WorkSpaces in all regions
aws-cloud-utilities inventory workspaces --all-regions

# Filter by directory
aws-cloud-utilities inventory workspaces --directory-id d-12345abcde

# Filter by user
aws-cloud-utilities inventory workspaces --user-name john.doe

# Export to CSV
aws-cloud-utilities inventory workspaces --output-file workspaces.csv
```

### `services`

Discover and list available AWS services in your account.

```bash
aws-cloud-utilities inventory services [OPTIONS]
```

**Features:**
- Lists all AWS services available in your account
- Shows service availability by region
- Identifies enabled and available services
- Helps with service discovery and planning

**Options:**
- `--region REGION` - Check service availability in specific region
- `--all-regions` - Check service availability across all regions
- `--service-category CATEGORY` - Filter by service category
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List available services
aws-cloud-utilities inventory services

# Services in specific region
aws-cloud-utilities inventory services --region us-east-1

# Services across all regions
aws-cloud-utilities inventory services --all-regions

# Export to JSON
aws-cloud-utilities inventory services --output-file services.json
```

### `download-all`

Download all resource data in bulk for offline analysis.

```bash
aws-cloud-utilities inventory download-all [OPTIONS]
```

**Features:**
- Downloads comprehensive resource inventory
- Saves data locally for offline analysis
- Includes metadata, configurations, and tags
- Organizes data by service and region
- Creates timestamped backups

**Options:**
- `--output-dir DIR` - Directory to save inventory data (default: ./inventory-data)
- `--services SERVICES` - Comma-separated list of services to download
- `--regions REGIONS` - Comma-separated list of regions
- `--all-regions` - Download from all regions
- `--format FORMAT` - Output format (json, yaml) [default: json]
- `--compress` - Compress output files

**Examples:**
```bash
# Download all inventory data
aws-cloud-utilities inventory download-all

# Download to specific directory
aws-cloud-utilities inventory download-all --output-dir ./backup

# Download specific services
aws-cloud-utilities inventory download-all --services ec2,s3,rds

# Download from all regions
aws-cloud-utilities inventory download-all --all-regions

# Compress output
aws-cloud-utilities inventory download-all --compress

# YAML format
aws-cloud-utilities inventory download-all --format yaml --output-dir ./inventory-yaml
```

## Global Options

All inventory commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Complete Resource Inventory

```bash
#!/bin/bash
# Complete resource inventory across all regions
echo "=== Comprehensive Inventory Scan ==="
aws-cloud-utilities inventory scan --all-regions --include-tags --output-file complete-inventory.json

echo "=== WorkSpaces Inventory ==="
aws-cloud-utilities inventory workspaces --all-regions --output-file workspaces.json

echo "=== Available Services ==="
aws-cloud-utilities inventory services --output-file services.json
```

### Bulk Data Download for Analysis

```bash
#!/bin/bash
# Download all inventory data for offline analysis
BACKUP_DIR="./inventory-backup-$(date +%Y%m%d)"

echo "=== Downloading All Inventory Data ==="
aws-cloud-utilities inventory download-all --output-dir "$BACKUP_DIR" --all-regions --compress

echo "=== Download Complete ==="
echo "Data saved to: $BACKUP_DIR"
```

### Multi-Service Inventory

```bash
#!/bin/bash
# Scan specific services across multiple regions
echo "=== Scanning Core Services ==="
aws-cloud-utilities inventory scan \
  --services ec2,s3,rds,lambda \
  --regions us-east-1,us-west-2,eu-west-1 \
  --include-tags \
  --output-file core-services-inventory.json

echo "=== Parallel Region Scanning ==="
aws-cloud-utilities inventory scan \
  --all-regions \
  --parallel-regions 8 \
  --output-file parallel-scan.json
```

### WorkSpaces Management

```bash
#!/bin/bash
# WorkSpaces inventory and analysis
echo "=== All WorkSpaces ==="
aws-cloud-utilities inventory workspaces --all-regions

echo "=== WorkSpaces by Directory ==="
aws-cloud-utilities inventory workspaces --directory-id d-12345abcde

echo "=== Export WorkSpaces Data ==="
aws-cloud-utilities inventory workspaces --all-regions --output-file workspaces-report.csv
```

## Common Use Cases

1. **Resource Discovery**
   ```bash
   # Discover all resources across account
   aws-cloud-utilities inventory scan --all-regions --include-tags

   # List available services
   aws-cloud-utilities inventory services
   ```

2. **Service-Specific Inventory**
   ```bash
   # EC2 and S3 only
   aws-cloud-utilities inventory scan --services ec2,s3

   # WorkSpaces inventory
   aws-cloud-utilities inventory workspaces --all-regions
   ```

3. **Data Backup and Export**
   ```bash
   # Download all inventory data
   aws-cloud-utilities inventory download-all --all-regions --compress

   # Export to CSV for spreadsheet analysis
   aws-cloud-utilities inventory scan --output-file inventory.csv
   ```

4. **Multi-Region Analysis**
   ```bash
   # Scan all regions with parallel processing
   aws-cloud-utilities inventory scan --all-regions --parallel-regions 4
   ```

## Output Formats

### Table Format (Default)
Human-readable tables with resource information displayed in the terminal.

### JSON Format
Structured data perfect for automation and integration:
```bash
aws-cloud-utilities inventory scan --output-file inventory.json
```

### CSV Format
Spreadsheet-compatible format for analysis in Excel or Google Sheets:
```bash
aws-cloud-utilities inventory scan --output-file inventory.csv
```

### YAML Format
Configuration-friendly format for documentation:
```bash
aws-cloud-utilities inventory download-all --format yaml
```

## Integration Examples

### With Automation Scripts
```bash
#!/bin/bash
# Daily automated inventory
DATE=$(date +%Y%m%d)
aws-cloud-utilities inventory scan --all-regions --output-file "inventory-${DATE}.json"
aws-cloud-utilities inventory workspaces --all-regions --output-file "workspaces-${DATE}.csv"
```

### With Data Analysis Tools
```bash
# Export for analysis with jq
aws-cloud-utilities inventory scan --output-file inventory.json
cat inventory.json | jq '.resources[] | select(.service == "ec2")'
```

### Multi-Account Inventory
```bash
#!/bin/bash
# Multi-account inventory collection
for profile in dev staging prod; do
    echo "=== Scanning $profile account ==="
    aws-cloud-utilities --profile $profile inventory scan \
      --all-regions \
      --output-file "inventory-${profile}.json"

    aws-cloud-utilities --profile $profile inventory download-all \
      --output-dir "./backup-${profile}" \
      --all-regions
done
```

## Performance Tips

1. **Use Parallel Scanning**: Speed up multi-region scans with `--parallel-regions`
   ```bash
   aws-cloud-utilities inventory scan --all-regions --parallel-regions 8
   ```

2. **Filter Services**: Only scan needed services to reduce time
   ```bash
   aws-cloud-utilities inventory scan --services ec2,s3,rds
   ```

3. **Regional Scoping**: Limit to specific regions if global scan isn't needed
   ```bash
   aws-cloud-utilities inventory scan --regions us-east-1,us-west-2
   ```

## Best Practices

1. **Regular Inventory Scans**: Schedule periodic scans to track resource changes
2. **Tag Inclusion**: Always use `--include-tags` for comprehensive data
3. **Data Backup**: Use `download-all` for compliance and audit records
4. **Multi-Format Export**: Keep both JSON (for automation) and CSV (for analysis)
