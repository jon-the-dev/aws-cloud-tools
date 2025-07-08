# Migrated Commands Reference

This document shows the mapping between original v1 scripts and the new v2 unified CLI commands.

## Support Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `support/aws_check_support.py` | `aws-cloud-utilities support check-level` | Check AWS support level |
| `support/aws_check_support2.py` | `aws-cloud-utilities support check-level --method api` | Check support via API (fallback to severity) |

### New Enhanced Commands

```bash
# Check support level (primary method)
aws-cloud-utilities support check-level

# List available severity levels
aws-cloud-utilities support severity-levels

# List support cases
aws-cloud-utilities support cases --status open
aws-cloud-utilities support cases --status resolved --max-results 50

# List services available for support
aws-cloud-utilities support services
```

## Account Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `account/aws_get_acct_info.py` | `aws-cloud-utilities account contact-info` | Get account contact information |
| `account/detect_control_tower.py` | `aws-cloud-utilities account detect-control-tower` | Detect Control Tower/Landing Zone |

### Enhanced Account Commands

```bash
# Basic account information (enhanced from v1)
aws-cloud-utilities account info

# Get contact information (migrated)
aws-cloud-utilities account contact-info

# Detect Control Tower/Landing Zone (migrated with improvements)
aws-cloud-utilities account detect-control-tower
aws-cloud-utilities account detect-control-tower --verbose

# Additional account utilities (new in v2)
aws-cloud-utilities account regions
aws-cloud-utilities account service-regions --service lambda
aws-cloud-utilities account limits
aws-cloud-utilities account validate
```

## Key Improvements in v2

### Enhanced Error Handling
- Graceful degradation when permissions are limited
- Clear error messages with actionable guidance
- Proper handling of Basic vs Premium support plans

### Better Output Formatting
- Rich console output with colors and tables
- Multiple output formats: table, json, yaml, csv
- Progress indicators for long-running operations

### Parallel Processing
- Control Tower detection now scans all regions in parallel
- Configurable worker threads (default: 4)
- Progress bars for multi-region operations

### Configuration Management
- Global options: `--profile`, `--region`, `--output`, `--verbose`
- Environment variable support
- Configuration file support (.env)

## Migration Benefits

1. **Unified Interface**: Single command instead of multiple scripts
2. **Better UX**: Rich output, progress indicators, help system
3. **Enhanced Functionality**: More options and better error handling
4. **Consistent Patterns**: Same CLI patterns across all services
5. **Modern Python**: Type hints, proper packaging, testing

## Installation & Testing

```bash
# Install in development mode
cd v2
./install_dev.sh

# Test the migration
python test_migration.py

# Try the commands
aws-cloud-utilities --help
aws-cloud-utilities account info
aws-cloud-utilities support check-level
```

## Bedrock Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `bedrock/bedrock_models.py` | `aws-cloud-utilities bedrock list-models` | List Bedrock foundation models |

### New Enhanced Commands

```bash
# List all foundation models across regions (migrated with enhancements)
aws-cloud-utilities bedrock list-models

# List models from specific region
aws-cloud-utilities bedrock list-models --region us-east-1

# Filter by provider
aws-cloud-utilities bedrock list-models --provider anthropic

# Save results to file with account ID and timestamp
aws-cloud-utilities bedrock list-models --output-file bedrock_models.csv

# Get detailed information about a specific model
aws-cloud-utilities bedrock model-details anthropic.claude-3-sonnet-20240229-v1:0

# List custom models
aws-cloud-utilities bedrock list-custom-models

# List model customization jobs
aws-cloud-utilities bedrock list-model-jobs --status Completed

# List available Bedrock regions
aws-cloud-utilities bedrock regions
```

## IAM Commands

### Original Scripts → New Commands

| Original Script | New Command | Description |
|----------------|-------------|-------------|
| `iam/iam_auditor.py` | `aws-cloud-utilities iam audit` | Audit IAM roles and policies |

### New Enhanced Commands

```bash
# Enhanced migration of original functionality
aws-cloud-utilities iam audit
aws-cloud-utilities iam audit --output-dir ./my_audit
aws-cloud-utilities iam audit --include-aws-managed
aws-cloud-utilities iam audit --roles-only
aws-cloud-utilities iam audit --policies-only
aws-cloud-utilities iam audit --format yaml

# New functionality not in original
aws-cloud-utilities iam list-roles
aws-cloud-utilities iam list-roles --path-prefix /service-role/
aws-cloud-utilities iam list-policies --scope Local
aws-cloud-utilities iam list-policies --only-attached
aws-cloud-utilities iam role-details MyRole
aws-cloud-utilities iam policy-details arn:aws:iam::123456789012:policy/MyPolicy
```

## Next Services to Migrate

1. **CostOps** - Cost optimization tools
2. **Inventory** - Resource discovery
3. **Logs** - CloudWatch logs management
4. **Security** - Security auditing tools
5. **S3** - S3 operations
