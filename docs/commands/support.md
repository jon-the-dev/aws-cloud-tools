# Support Commands

AWS support tools for managing support cases and checking support levels.

## Commands

### `check-level`

Check AWS support level and plan details.

```bash
aws-cloud-utilities support check-level
```

**Options:**
- `--method METHOD` - Check method (api, severity) - defaults to api with fallback
- `--verbose` - Show detailed support plan information

**Examples:**
```bash
# Check support level
aws-cloud-utilities support check-level

# Verbose output with plan details
aws-cloud-utilities support check-level --verbose

# Use severity method
aws-cloud-utilities support check-level --method severity
```

### `cases`

List and manage AWS support cases.

```bash
aws-cloud-utilities support cases
```

**Options:**
- `--status STATUS` - Filter by case status (open, resolved, all)
- `--max-results NUMBER` - Maximum number of cases to return
- `--language LANGUAGE` - Language for case communication

**Examples:**
```bash
# All open cases
aws-cloud-utilities support cases --status open

# All resolved cases (limited)
aws-cloud-utilities support cases --status resolved --max-results 50

# All cases
aws-cloud-utilities support cases --status all
```

### `services`

List AWS services available for support.

```bash
aws-cloud-utilities support services
```

**Options:**
- `--language LANGUAGE` - Language for service names

**Examples:**
```bash
# List all support services
aws-cloud-utilities support services

# Services in specific language
aws-cloud-utilities support services --language ja
```

### `severity-levels`

List available support case severity levels.

```bash
aws-cloud-utilities support severity-levels
```

**Options:**
- `--language LANGUAGE` - Language for severity descriptions

**Examples:**
```bash
# List severity levels
aws-cloud-utilities support severity-levels

# Severity levels in specific language
aws-cloud-utilities support severity-levels --language es
```

## Support Plan Detection

The tool automatically detects your AWS support plan:

- **Basic**: Free support plan (limited features)
- **Developer**: Business hours support via email
- **Business**: 24/7 support via phone, email, and chat
- **Enterprise**: Dedicated Technical Account Manager

## Common Use Cases

### Support Plan Verification
```bash
# Check current support level
aws-cloud-utilities support check-level --verbose
```

### Case Management
```bash
# Review open cases
aws-cloud-utilities support cases --status open

# Export case history
aws-cloud-utilities support cases --status all --output json > support-cases.json
```

### Support Planning
```bash
# List available services for support
aws-cloud-utilities support services --output table

# Check severity levels for case creation
aws-cloud-utilities support severity-levels
```

## Error Handling

The support commands handle different support plans gracefully:

- **Basic Support**: Limited API access, uses alternative detection methods
- **Premium Support**: Full API access to all support features
- **No Support API Access**: Falls back to severity level detection

## Integration Examples

### Monitoring Script
```bash
#!/bin/bash
# Check for open support cases
OPEN_CASES=$(aws-cloud-utilities support cases --status open --output json | jq length)

if [ "$OPEN_CASES" -gt 0 ]; then
    echo "Warning: $OPEN_CASES open support cases"
    aws-cloud-utilities support cases --status open
fi
```

### Support Plan Audit
```bash
#!/bin/bash
# Audit support configuration
echo "=== Support Plan ==="
aws-cloud-utilities support check-level --verbose

echo "=== Available Services ==="
aws-cloud-utilities support services

echo "=== Open Cases ==="
aws-cloud-utilities support cases --status open
```
