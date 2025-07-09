# Migration from v1

This guide helps you migrate from the original v1 script collection to the unified v2 CLI tool.

## Overview

AWS Cloud Utilities v2 consolidates all the individual v1 scripts into a single, unified command-line interface with enhanced functionality and better user experience.

## Key Changes

### From Scripts to Unified CLI

**v1 (Multiple Scripts)**
```bash
python support/aws_check_support.py
python account/aws_get_acct_info.py
python account/detect_control_tower.py
```

**v2 (Unified CLI)**
```bash
aws-cloud-utilities support check-level
aws-cloud-utilities account contact-info
aws-cloud-utilities account detect-control-tower
```

### Enhanced Command Structure

v2 follows a hierarchical structure:
```
aws-cloud-utilities [GLOBAL-OPTIONS] <service> <operation> [OPTIONS]
```

## Command Mapping

### Support Commands

| v1 Script | v2 Command | Notes |
|-----------|------------|-------|
| `support/aws_check_support.py` | `aws-cloud-utilities support check-level` | Enhanced with better error handling |
| `support/aws_check_support2.py` | `aws-cloud-utilities support check-level --method api` | Integrated as option |

**New in v2:**
```bash
aws-cloud-utilities support cases --status open
aws-cloud-utilities support services
aws-cloud-utilities support severity-levels
```

### Account Commands

| v1 Script | v2 Command | Notes |
|-----------|------------|-------|
| `account/aws_get_acct_info.py` | `aws-cloud-utilities account contact-info` | Enhanced output formatting |
| `account/detect_control_tower.py` | `aws-cloud-utilities account detect-control-tower` | Parallel region scanning |

**New in v2:**
```bash
aws-cloud-utilities account info
aws-cloud-utilities account regions
aws-cloud-utilities account limits
aws-cloud-utilities account validate
```

### Cost Optimization Commands

| v1 Script | v2 Command | Notes |
|-----------|------------|-------|
| `costops/aws_pricing.py` | `aws-cloud-utilities costops pricing` | Enhanced with more services |
| `costops/gpu_spot_prices.py` | `aws-cloud-utilities costops gpu-spots` | Better filtering and sorting |

**New in v2:**
```bash
aws-cloud-utilities costops analyze
aws-cloud-utilities costops recommendations
aws-cloud-utilities costops savings-plans
```

### Security Commands

| v1 Script | v2 Command | Notes |
|-----------|------------|-------|
| `security/blue_team_audit.py` | `aws-cloud-utilities security blue-team-audit` | Enhanced checks |
| `security/public_resources.py` | `aws-cloud-utilities security public-resources` | Better detection |

**New in v2:**
```bash
aws-cloud-utilities security audit
aws-cloud-utilities security compliance
aws-cloud-utilities iam analyze
```

## Migration Steps

### 1. Install v2

```bash
cd aws-cloud-tools/v2
pip install -e .
```

### 2. Update Your Scripts

**Before (v1):**
```bash
#!/bin/bash
cd /path/to/aws-cloud-tools
python support/aws_check_support.py
python account/aws_get_acct_info.py
```

**After (v2):**
```bash
#!/bin/bash
aws-cloud-utilities support check-level
aws-cloud-utilities account contact-info
```

### 3. Update Configuration

**v1 Configuration:**
- Individual script configurations
- Hardcoded values in scripts
- Environment variables scattered

**v2 Configuration:**
```bash
# Interactive setup
aws-cloud-utilities configure

# Or create ~/.aws-cloud-utilities.env
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
AWS_OUTPUT_FORMAT=table
WORKERS=4
```

### 4. Update Output Handling

**v1 Output:**
- Inconsistent formats
- Basic text output
- Limited formatting options

**v2 Output:**
```bash
# Multiple formats available
aws-cloud-utilities account info --output json
aws-cloud-utilities account info --output yaml
aws-cloud-utilities account info --output table
aws-cloud-utilities account info --output csv
```

## Feature Enhancements

### Improved Error Handling

**v1:**
- Basic error messages
- Script failures without context
- No graceful degradation

**v2:**
- Rich error messages with context
- Graceful degradation with limited permissions
- Actionable error guidance

### Better Performance

**v1:**
- Sequential operations
- No progress indicators
- Fixed timeouts

**v2:**
- Parallel processing with configurable workers
- Progress bars for long operations
- Configurable timeouts and retries

### Enhanced Output

**v1:**
- Plain text output
- Inconsistent formatting
- Limited data export options

**v2:**
- Rich console output with colors and tables
- Multiple export formats (JSON, YAML, CSV)
- Consistent formatting across all commands

## Automation Migration

### Cron Jobs

**Before:**
```bash
# /etc/cron.d/aws-audit
0 2 * * * user cd /path/to/scripts && python security/blue_team_audit.py > /var/log/audit.log
```

**After:**
```bash
# /etc/cron.d/aws-audit
0 2 * * * user aws-cloud-utilities security blue-team-audit --output json > /var/log/audit.json
```

### CI/CD Pipelines

**Before:**
```yaml
- name: Run AWS Audit
  run: |
    cd aws-cloud-tools
    python security/blue_team_audit.py
    python account/detect_control_tower.py
```

**After:**
```yaml
- name: Run AWS Audit
  run: |
    aws-cloud-utilities security blue-team-audit --output json > audit.json
    aws-cloud-utilities account detect-control-tower --output json > control-tower.json
```

### Monitoring Scripts

**Before:**
```python
import subprocess
result = subprocess.run(['python', 'support/aws_check_support.py'], capture_output=True)
```

**After:**
```python
import subprocess
result = subprocess.run(['aws-cloud-utilities', 'support', 'check-level', '--output', 'json'], capture_output=True)
```

## Backward Compatibility

### Environment Variables

Most v1 environment variables are still supported:

```bash
# Still works in v2
export AWS_PROFILE=production
export AWS_DEFAULT_REGION=us-west-2
```

### AWS Configuration

Your existing AWS configuration continues to work:

```bash
# ~/.aws/credentials and ~/.aws/config are still used
aws-cloud-utilities --profile production account info
```

## Testing Your Migration

### 1. Verify Installation

```bash
aws-cloud-utilities --version
aws-cloud-utilities --help
```

### 2. Test Basic Commands

```bash
# Test account access
aws-cloud-utilities account info

# Test with your profile
aws-cloud-utilities --profile your-profile account info
```

### 3. Compare Outputs

Run equivalent commands and compare:

```bash
# v1
python account/aws_get_acct_info.py > v1-output.txt

# v2
aws-cloud-utilities account contact-info > v2-output.txt
```

### 4. Test Automation

Update one automation script at a time and test thoroughly.

## Troubleshooting Migration

### Common Issues

1. **Command not found**
   ```bash
   # Ensure v2 is installed
   pip install -e /path/to/aws-cloud-tools/v2
   ```

2. **Different output format**
   ```bash
   # Use --output to match expected format
   aws-cloud-utilities account info --output json
   ```

3. **Missing functionality**
   ```bash
   # Check if command exists in v2
   aws-cloud-utilities --help
   aws-cloud-utilities <service> --help
   ```

4. **Permission errors**
   ```bash
   # Same AWS permissions needed
   aws sts get-caller-identity
   ```

### Getting Help

```bash
# General help
aws-cloud-utilities --help

# Service help
aws-cloud-utilities account --help

# Command help
aws-cloud-utilities account info --help
```

## Migration Checklist

- [ ] Install v2 CLI tool
- [ ] Test basic commands with your AWS profile
- [ ] Update automation scripts one by one
- [ ] Update cron jobs and CI/CD pipelines
- [ ] Update monitoring and alerting scripts
- [ ] Test all updated automation
- [ ] Update documentation and runbooks
- [ ] Train team members on new commands
- [ ] Remove v1 scripts (after thorough testing)

## Benefits After Migration

1. **Unified Interface**: Single command instead of multiple scripts
2. **Better UX**: Rich output, progress indicators, help system
3. **Enhanced Functionality**: More options and better error handling
4. **Consistent Patterns**: Same CLI patterns across all services
5. **Modern Python**: Type hints, proper packaging, testing
6. **Better Performance**: Parallel processing and optimization
7. **Easier Maintenance**: Single codebase instead of scattered scripts

## Next Steps

- [Quick Start](quick-start.md) - Learn the new commands
- [Configuration](configuration.md) - Set up your preferences
- [Command Reference](../commands/index.md) - Explore all available commands
- [Examples](../examples/common-use-cases.md) - See real-world usage patterns
