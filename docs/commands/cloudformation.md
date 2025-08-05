# CloudFormation Commands

CloudFormation stack management commands for infrastructure as code operations.

## Commands

### `backup`

Backup CloudFormation stacks by downloading templates and parameters.

```bash
aws-cloud-utilities cloudformation backup
```

**Options:**
- `--region REGION` - AWS region to backup from (default: all regions)
- `--stack-name NAME` - Backup specific stack (default: all stacks)
- `--output-dir DIR` - Directory to save backup files (default: ./cf-backup)
- `--include-parameters` - Include stack parameters in backup
- `--include-outputs` - Include stack outputs in backup
- `--include-resources` - Include resource details in backup

**Examples:**
```bash
# Backup all stacks
aws-cloud-utilities cloudformation backup

# Backup specific stack
aws-cloud-utilities cloudformation backup --stack-name my-application-stack

# Backup from specific region
aws-cloud-utilities cloudformation backup --region us-east-1

# Comprehensive backup with all details
aws-cloud-utilities cloudformation backup --include-parameters --include-outputs --include-resources
```

### `list-stacks`

List CloudFormation stacks with status and details.

```bash
aws-cloud-utilities cloudformation list-stacks
```

**Options:**
- `--region REGION` - AWS region to query (default: all regions)
- `--status STATUS` - Filter by stack status (CREATE_COMPLETE, UPDATE_COMPLETE, DELETE_COMPLETE, etc.)
- `--include-deleted` - Include deleted stacks in results
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all active stacks
aws-cloud-utilities cloudformation list-stacks

# List stacks in specific region
aws-cloud-utilities cloudformation list-stacks --region us-west-2

# Filter by status
aws-cloud-utilities cloudformation list-stacks --status CREATE_COMPLETE

# Include deleted stacks
aws-cloud-utilities cloudformation list-stacks --include-deleted

# Save to file
aws-cloud-utilities cloudformation list-stacks --output-file stacks.json
```

### `stack-details`

Get comprehensive details about a specific CloudFormation stack.

```bash
aws-cloud-utilities cloudformation stack-details STACK_NAME
```

**Arguments:**
- `STACK_NAME` - Name or ARN of the stack to analyze

**Options:**
- `--region REGION` - AWS region where the stack exists
- `--include-template` - Include the stack template in output
- `--include-events` - Include stack events in output
- `--include-resources` - Include detailed resource information
- `--include-drift` - Include drift detection results
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Basic stack details
aws-cloud-utilities cloudformation stack-details my-stack

# Comprehensive details
aws-cloud-utilities cloudformation stack-details my-stack --include-template --include-events --include-resources

# Include drift detection
aws-cloud-utilities cloudformation stack-details my-stack --include-drift

# Save to file
aws-cloud-utilities cloudformation stack-details my-stack --output-file stack-analysis.json
```

## Global Options

All CloudFormation commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Stack Backup Workflow

```bash
#!/bin/bash
# Comprehensive stack backup

BACKUP_DIR="./cf-backup-$(date +%Y%m%d)"

echo "=== Creating Backup Directory ==="
mkdir -p $BACKUP_DIR

echo "=== Listing All Stacks ==="
aws-cloud-utilities cloudformation list-stacks --output-file $BACKUP_DIR/stack-list.json

echo "=== Backing Up All Stacks ==="
aws-cloud-utilities cloudformation backup --output-dir $BACKUP_DIR --include-parameters --include-outputs --include-resources

echo "=== Backup Complete ==="
echo "Backup saved to: $BACKUP_DIR"
```

### Stack Analysis Script

```bash
#!/bin/bash
# Analyze specific stack

STACK_NAME="my-production-stack"
ANALYSIS_DIR="./stack-analysis-$(date +%Y%m%d)"

mkdir -p $ANALYSIS_DIR

echo "=== Stack Overview ==="
aws-cloud-utilities cloudformation stack-details $STACK_NAME --output-file $ANALYSIS_DIR/overview.json

echo "=== Detailed Analysis ==="
aws-cloud-utilities cloudformation stack-details $STACK_NAME \
    --include-template \
    --include-events \
    --include-resources \
    --include-drift \
    --output-file $ANALYSIS_DIR/detailed-analysis.json

echo "=== Analysis Complete ==="
echo "Analysis saved to: $ANALYSIS_DIR"
```

### Multi-Region Stack Inventory

```bash
#!/bin/bash
# Inventory stacks across multiple regions

REGIONS=("us-east-1" "us-west-2" "eu-west-1" "ap-southeast-1")
INVENTORY_DIR="./cf-inventory-$(date +%Y%m%d)"

mkdir -p $INVENTORY_DIR

for region in "${REGIONS[@]}"; do
    echo "=== Scanning $region ==="
    aws-cloud-utilities cloudformation list-stacks --region $region --output-file $INVENTORY_DIR/stacks-$region.json
done

echo "=== Inventory Complete ==="
echo "Inventory saved to: $INVENTORY_DIR"
```

### Stack Health Check

```bash
#!/bin/bash
# Check health of all stacks

echo "=== Failed/Rollback Stacks ==="
aws-cloud-utilities cloudformation list-stacks --status CREATE_FAILED
aws-cloud-utilities cloudformation list-stacks --status ROLLBACK_COMPLETE
aws-cloud-utilities cloudformation list-stacks --status UPDATE_ROLLBACK_COMPLETE

echo "=== In-Progress Operations ==="
aws-cloud-utilities cloudformation list-stacks --status CREATE_IN_PROGRESS
aws-cloud-utilities cloudformation list-stacks --status UPDATE_IN_PROGRESS
aws-cloud-utilities cloudformation list-stacks --status DELETE_IN_PROGRESS
```

## Common Use Cases

1. **Infrastructure Backup**
   ```bash
   aws-cloud-utilities cloudformation backup --include-parameters --include-outputs
   ```

2. **Stack Monitoring**
   ```bash
   aws-cloud-utilities cloudformation list-stacks --status CREATE_FAILED
   aws-cloud-utilities cloudformation list-stacks --status ROLLBACK_COMPLETE
   ```

3. **Detailed Stack Analysis**
   ```bash
   aws-cloud-utilities cloudformation stack-details my-stack --include-template --include-drift
   ```

4. **Multi-Region Inventory**
   ```bash
   aws-cloud-utilities cloudformation list-stacks --region us-east-1
   aws-cloud-utilities cloudformation list-stacks --region us-west-2
   ```

## Integration with Other Commands

CloudFormation commands work well with other AWS Cloud Utilities:

```bash
# Combine with inventory for resource analysis
aws-cloud-utilities inventory resources --resource-type cloudformation
aws-cloud-utilities cloudformation list-stacks

# Combine with security audit
aws-cloud-utilities security blue-team-audit
aws-cloud-utilities cloudformation stack-details my-stack --include-drift
```

## Best Practices

- Regular backups of critical stacks using the `backup` command
- Monitor stack status regularly to catch failed deployments
- Use drift detection to ensure infrastructure matches templates
- Include all details (`--include-*` flags) for comprehensive analysis
- Organize backups by date and environment for easy recovery
- Use JSON output for integration with other tools and automation
