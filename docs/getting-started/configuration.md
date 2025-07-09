# Configuration

AWS Cloud Utilities v2 provides flexible configuration options through environment variables, configuration files, and command-line options.

## Configuration Methods

Configuration is loaded in this order (later sources override earlier ones):

1. Default values
2. Configuration file (`~/.aws-cloud-utilities.env`)
3. Environment variables
4. Command-line options

## Interactive Configuration

The easiest way to configure the tool:

```bash
aws-cloud-utilities configure
```

This will prompt you for:
- AWS Profile
- Default AWS Region
- Output Format
- Number of Workers

## Configuration File

Create `~/.aws-cloud-utilities.env` with your preferred settings:

```env
# AWS Configuration
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
AWS_OUTPUT_FORMAT=table

# Performance Settings
WORKERS=4

# Logging
LOG_LEVEL=INFO
VERBOSE=false
DEBUG=false

# Output Settings
SHOW_PROGRESS=true
COLOR_OUTPUT=true
```

## Environment Variables

Set environment variables for temporary overrides:

```bash
# AWS settings
export AWS_PROFILE=production
export AWS_DEFAULT_REGION=eu-west-1
export AWS_OUTPUT_FORMAT=json

# Performance
export WORKERS=8

# Logging
export LOG_LEVEL=DEBUG
export VERBOSE=true
```

## Command-Line Options

Override any setting with command-line options:

```bash
aws-cloud-utilities --profile staging --region us-west-2 --output json account info
```

## Configuration Options

### AWS Settings

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| `--profile` | `AWS_PROFILE` | `default` | AWS profile to use |
| `--region` | `AWS_DEFAULT_REGION` | `us-east-1` | Default AWS region |
| `--output` | `AWS_OUTPUT_FORMAT` | `table` | Output format |

### Performance Settings

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| N/A | `WORKERS` | `4` | Number of parallel workers |
| N/A | `TIMEOUT` | `30` | Request timeout in seconds |
| N/A | `RETRY_ATTEMPTS` | `3` | Number of retry attempts |

### Logging Settings

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| `--verbose` | `VERBOSE` | `false` | Enable verbose output |
| `--debug` | `DEBUG` | `false` | Enable debug mode |
| N/A | `LOG_LEVEL` | `INFO` | Logging level |
| N/A | `LOG_FILE` | None | Log file path |

### Output Settings

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| N/A | `SHOW_PROGRESS` | `true` | Show progress bars |
| N/A | `COLOR_OUTPUT` | `true` | Enable colored output |
| N/A | `TABLE_MAX_WIDTH` | `120` | Maximum table width |

## AWS Profile Configuration

### Using AWS CLI Profiles

Configure multiple profiles with AWS CLI:

```bash
# Configure default profile
aws configure

# Configure named profile
aws configure --profile production
```

Then use with the tool:

```bash
aws-cloud-utilities --profile production account info
```

### Profile-Specific Settings

Create profile-specific configuration files:

```bash
# ~/.aws-cloud-utilities-production.env
AWS_PROFILE=production
AWS_DEFAULT_REGION=us-east-1
WORKERS=8
LOG_LEVEL=WARNING
```

Load with:

```bash
aws-cloud-utilities --config ~/.aws-cloud-utilities-production.env account info
```

## Region Configuration

### Default Region

Set a default region for all operations:

```env
AWS_DEFAULT_REGION=us-west-2
```

### Multi-Region Operations

Some commands support multi-region operations:

```bash
# Inventory across all regions
aws-cloud-utilities inventory resources --all-regions

# Specific regions
aws-cloud-utilities inventory resources --regions us-east-1,us-west-2,eu-west-1
```

## Output Format Configuration

### Supported Formats

- `table` - Rich formatted tables (default)
- `json` - JSON output
- `yaml` - YAML output  
- `csv` - CSV format (for tabular data)

### Format-Specific Settings

```env
# Table format settings
TABLE_MAX_WIDTH=120
TABLE_SHOW_LINES=true

# JSON format settings
JSON_INDENT=2
JSON_SORT_KEYS=true

# CSV format settings
CSV_DELIMITER=,
CSV_QUOTE_CHAR="
```

## Performance Tuning

### Worker Configuration

Adjust parallel processing:

```env
# More workers for faster processing (uses more resources)
WORKERS=8

# Fewer workers for limited resources
WORKERS=2
```

### Timeout Settings

Configure timeouts for different operations:

```env
# General timeout
TIMEOUT=30

# Long-running operations
LONG_OPERATION_TIMEOUT=300

# Connection timeout
CONNECTION_TIMEOUT=10
```

### Retry Configuration

Configure retry behavior:

```env
RETRY_ATTEMPTS=3
RETRY_BACKOFF=2
RETRY_MAX_DELAY=60
```

## Logging Configuration

### Log Levels

Available log levels:
- `DEBUG` - Detailed debugging information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages only

### Log File Configuration

```env
# Enable file logging
LOG_FILE=/var/log/aws-cloud-utilities.log

# Log rotation
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5
```

### Structured Logging

Enable structured JSON logging:

```env
LOG_FORMAT=json
LOG_INCLUDE_TIMESTAMP=true
LOG_INCLUDE_LEVEL=true
```

## Security Configuration

### Credential Management

```env
# Use IAM roles (recommended)
AWS_USE_IAM_ROLE=true

# Credential file location
AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials

# Config file location
AWS_CONFIG_FILE=~/.aws/config
```

### Session Configuration

```env
# Session duration
AWS_SESSION_DURATION=3600

# MFA settings
AWS_MFA_SERIAL=arn:aws:iam::123456789012:mfa/username
```

## Validation

Validate your configuration:

```bash
# Check configuration
aws-cloud-utilities info

# Test AWS connectivity
aws-cloud-utilities account info

# Validate specific profile
aws-cloud-utilities --profile production account validate
```

## Troubleshooting

### Common Issues

1. **Profile not found**
   ```bash
   aws configure list-profiles
   aws-cloud-utilities --profile correct-profile-name account info
   ```

2. **Region not available**
   ```bash
   aws-cloud-utilities account regions
   ```

3. **Permission errors**
   ```bash
   aws sts get-caller-identity
   aws-cloud-utilities --debug account info
   ```

### Debug Configuration

Enable debug mode to see configuration loading:

```bash
aws-cloud-utilities --debug --verbose account info
```

This will show:
- Configuration file locations
- Environment variables loaded
- Final configuration values
- AWS credential resolution

## Best Practices

1. **Use profiles** for different environments
2. **Set default region** to avoid specifying it repeatedly
3. **Use configuration files** for consistent settings
4. **Enable logging** for troubleshooting
5. **Tune workers** based on your system resources
6. **Use IAM roles** instead of access keys when possible

## Next Steps

- [Quick Start](quick-start.md) - Start using the tool
- [Command Reference](../commands/index.md) - Explore available commands
- [Examples](../examples/common-use-cases.md) - See real-world usage
