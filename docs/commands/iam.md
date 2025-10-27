# IAM Commands

IAM management and auditing commands for identity and access management analysis.

## Commands

### `audit`

Audit IAM roles and policies, saving them locally for analysis.

```bash
aws-cloud-utilities iam audit [OPTIONS]
```

**Features:**
- Exports all IAM roles and their attached policies
- Exports managed and inline policies
- Saves policies to local directory for offline analysis
- Generates comprehensive IAM configuration snapshot

**Options:**
- `--output-dir DIR` - Directory to save IAM audit files (default: ./iam-audit)
- `--include-aws-managed` - Include AWS-managed policies (default: customer-managed only)
- `--format FORMAT` - Output format (json, yaml)

**Examples:**
```bash
# Basic IAM audit
aws-cloud-utilities iam audit

# Save to specific directory
aws-cloud-utilities iam audit --output-dir /path/to/audit

# Include AWS-managed policies
aws-cloud-utilities iam audit --include-aws-managed

# Export as YAML
aws-cloud-utilities iam audit --format yaml --output-dir ./iam-backup
```

### `list-roles`

List all IAM roles with details.

```bash
aws-cloud-utilities iam list-roles [OPTIONS]
```

**Output includes:**
- Role name and ARN
- Creation date
- Last used information
- Attached policies count
- Trust relationships summary

**Options:**
- `--path-prefix PREFIX` - Filter roles by path prefix
- `--max-items NUM` - Maximum number of roles to list
- `--output-file FILE` - Save results to file (json, yaml, csv)

**Examples:**
```bash
# List all roles
aws-cloud-utilities iam list-roles

# Filter by path
aws-cloud-utilities iam list-roles --path-prefix /service-role/

# Export to file
aws-cloud-utilities iam list-roles --output-file roles.json
```

### `list-policies`

List IAM policies.

```bash
aws-cloud-utilities iam list-policies [OPTIONS]
```

**Options:**
- `--scope SCOPE` - Policy scope (All, AWS, Local) [default: Local]
- `--only-attached` - Show only policies attached to entities
- `--path-prefix PREFIX` - Filter by path prefix
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List customer-managed policies
aws-cloud-utilities iam list-policies

# List all policies including AWS-managed
aws-cloud-utilities iam list-policies --scope All

# Only attached policies
aws-cloud-utilities iam list-policies --only-attached

# Export to CSV
aws-cloud-utilities iam list-policies --output-file policies.csv
```

### `role-details`

Get detailed information about a specific IAM role.

```bash
aws-cloud-utilities iam role-details ROLE_NAME [OPTIONS]
```

**Arguments:**
- `ROLE_NAME` - Name of the IAM role

**Output includes:**
- Role metadata (ARN, creation date, last used)
- Trust relationship (assume role policy)
- Attached managed policies
- Inline policies
- Permission boundaries
- Tags

**Options:**
- `--output-file FILE` - Save results to file
- `--include-policy-versions` - Include all policy versions

**Examples:**
```bash
# Get role details
aws-cloud-utilities iam role-details MyAppRole

# Export to JSON
aws-cloud-utilities iam role-details MyAppRole --output-file role-details.json

# Include all policy versions
aws-cloud-utilities iam role-details MyAppRole --include-policy-versions
```

### `policy-details`

Get detailed information about a specific IAM policy.

```bash
aws-cloud-utilities iam policy-details POLICY_ARN [OPTIONS]
```

**Arguments:**
- `POLICY_ARN` - ARN of the IAM policy

**Output includes:**
- Policy metadata
- Default policy version
- Policy document (JSON)
- All policy versions
- Entities attached to

**Options:**
- `--version VERSION_ID` - Show specific policy version
- `--all-versions` - Show all policy versions
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# Get policy details
aws-cloud-utilities iam policy-details arn:aws:iam::123456789012:policy/MyPolicy

# Show all versions
aws-cloud-utilities iam policy-details arn:aws:iam::123456789012:policy/MyPolicy --all-versions

# Export to file
aws-cloud-utilities iam policy-details arn:aws:iam::123456789012:policy/MyPolicy --output-file policy.json
```

## Global Options

All IAM commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Common Use Cases

### Security Audit and Backup
```bash
# Complete IAM audit with backup
aws-cloud-utilities iam audit --output-dir ./iam-backup-$(date +%Y%m%d)

# List all roles for review
aws-cloud-utilities iam list-roles --output-file roles-audit.csv
```

### Role Analysis
```bash
# Analyze specific role
aws-cloud-utilities iam role-details MyApplicationRole

# Export role configuration
aws-cloud-utilities iam role-details MyApplicationRole --output-file role-config.json
```

### Policy Management
```bash
# List customer-managed policies
aws-cloud-utilities iam list-policies --scope Local

# Get policy details
aws-cloud-utilities iam policy-details arn:aws:iam::123456789012:policy/MyPolicy --all-versions
```

### Compliance Review
```bash
#!/bin/bash
# Daily IAM compliance check
echo "=== IAM Audit ==="
aws-cloud-utilities iam audit --output-dir ./iam-audit-$(date +%Y%m%d)

echo "=== All Roles ==="
aws-cloud-utilities iam list-roles --output-file roles-$(date +%Y%m%d).json

echo "=== Custom Policies ==="
aws-cloud-utilities iam list-policies --scope Local --output-file policies-$(date +%Y%m%d).json
```

## Examples

### Complete IAM Documentation

```bash
#!/bin/bash
# Generate complete IAM documentation
OUTPUT_DIR="./iam-docs-$(date +%Y%m%d)"
mkdir -p "$OUTPUT_DIR"

# Audit all roles and policies
aws-cloud-utilities iam audit --output-dir "$OUTPUT_DIR/audit"

# Export roles list
aws-cloud-utilities iam list-roles --output-file "$OUTPUT_DIR/roles.json"

# Export policies list
aws-cloud-utilities iam list-policies --scope All --output-file "$OUTPUT_DIR/policies.json"

echo "IAM documentation saved to: $OUTPUT_DIR"
```

### Multi-Account IAM Inventory

```bash
#!/bin/bash
# Multi-account IAM inventory
for profile in dev staging prod; do
    echo "=== Processing $profile account ==="
    aws-cloud-utilities --profile $profile iam audit --output-dir ./iam-audit-$profile
    aws-cloud-utilities --profile $profile iam list-roles --output-file ./roles-$profile.json
done
```
