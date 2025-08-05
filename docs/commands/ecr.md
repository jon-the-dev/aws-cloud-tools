# ECR Commands

Elastic Container Registry (ECR) operations for container image management.

## Commands

### `copy-image`

Copy container images between ECR repositories or regions.

```bash
aws-cloud-utilities ecr copy-image SOURCE_URI DESTINATION_URI
```

**Arguments:**
- `SOURCE_URI` - Source image URI (e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:tag)
- `DESTINATION_URI` - Destination image URI

**Options:**
- `--source-region REGION` - Source region (if different from current)
- `--destination-region REGION` - Destination region (if different from current)
- `--force` - Overwrite existing image if it exists
- `--dry-run` - Show what would be copied without actually copying

**Examples:**
```bash
# Copy image between repositories
aws-cloud-utilities ecr copy-image \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/source-repo:v1.0 \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/dest-repo:v1.0

# Copy image between regions
aws-cloud-utilities ecr copy-image \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:v1.0 \
    123456789012.dkr.ecr.us-west-2.amazonaws.com/my-repo:v1.0 \
    --destination-region us-west-2

# Dry run to see what would be copied
aws-cloud-utilities ecr copy-image source:tag dest:tag --dry-run
```

### `list-repositories`

List ECR repositories with details and statistics.

```bash
aws-cloud-utilities ecr list-repositories
```

**Options:**
- `--region REGION` - AWS region to query (default: all regions)
- `--include-images` - Include image count and details
- `--include-size` - Include repository size information
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all repositories
aws-cloud-utilities ecr list-repositories

# List repositories in specific region
aws-cloud-utilities ecr list-repositories --region us-east-1

# Include image statistics
aws-cloud-utilities ecr list-repositories --include-images --include-size

# Save to file
aws-cloud-utilities ecr list-repositories --output-file repositories.json
```

### `list-images`

List images in ECR repositories with detailed information.

```bash
aws-cloud-utilities ecr list-images REPOSITORY_NAME
```

**Arguments:**
- `REPOSITORY_NAME` - Name of the repository to list images from

**Options:**
- `--region REGION` - AWS region where repository exists
- `--tag-status STATUS` - Filter by tag status (TAGGED, UNTAGGED, ANY) [default: ANY]
- `--include-vulnerabilities` - Include vulnerability scan results
- `--max-results NUM` - Maximum number of images to return
- `--output-file FILE` - Save results to file

**Examples:**
```bash
# List all images in repository
aws-cloud-utilities ecr list-images my-app

# List only tagged images
aws-cloud-utilities ecr list-images my-app --tag-status TAGGED

# Include vulnerability scan results
aws-cloud-utilities ecr list-images my-app --include-vulnerabilities

# Limit results and save to file
aws-cloud-utilities ecr list-images my-app --max-results 50 --output-file images.json
```

### `create-repository`

Create a new ECR repository with optional configuration.

```bash
aws-cloud-utilities ecr create-repository REPOSITORY_NAME
```

**Arguments:**
- `REPOSITORY_NAME` - Name of the repository to create

**Options:**
- `--region REGION` - AWS region to create repository in
- `--image-scanning` - Enable image vulnerability scanning
- `--immutable-tags` - Enable tag immutability
- `--encryption-type TYPE` - Encryption type (AES256, KMS) [default: AES256]
- `--kms-key KEY` - KMS key for encryption (if using KMS)

**Examples:**
```bash
# Create basic repository
aws-cloud-utilities ecr create-repository my-new-app

# Create repository with security features
aws-cloud-utilities ecr create-repository my-secure-app --image-scanning --immutable-tags

# Create repository with KMS encryption
aws-cloud-utilities ecr create-repository my-encrypted-app --encryption-type KMS --kms-key alias/my-key

# Create in specific region
aws-cloud-utilities ecr create-repository my-regional-app --region us-west-2
```

### `delete-repository`

Delete an ECR repository and all its images.

```bash
aws-cloud-utilities ecr delete-repository REPOSITORY_NAME
```

**Arguments:**
- `REPOSITORY_NAME` - Name of the repository to delete

**Options:**
- `--region REGION` - AWS region where repository exists
- `--force` - Force deletion without confirmation
- `--delete-images` - Delete all images in repository (required for non-empty repositories)

**Examples:**
```bash
# Delete empty repository
aws-cloud-utilities ecr delete-repository my-old-repo

# Delete repository with all images
aws-cloud-utilities ecr delete-repository my-old-repo --delete-images

# Force delete without confirmation
aws-cloud-utilities ecr delete-repository my-old-repo --delete-images --force
```

### `get-login`

Get Docker login command for ECR authentication.

```bash
aws-cloud-utilities ecr get-login
```

**Options:**
- `--region REGION` - AWS region for ECR registry
- `--registry-ids IDS` - Comma-separated list of registry IDs
- `--no-include-email` - Omit email flag from docker login command

**Examples:**
```bash
# Get login command for current region
aws-cloud-utilities ecr get-login

# Get login for specific region
aws-cloud-utilities ecr get-login --region us-west-2

# Get login for specific registry
aws-cloud-utilities ecr get-login --registry-ids 123456789012
```

## Global Options

All ECR commands support these global options:

- `--profile PROFILE` - AWS profile to use
- `--region REGION` - AWS region
- `--output FORMAT` - Output format (table, json, yaml, csv)
- `--verbose` - Enable verbose output
- `--debug` - Enable debug mode

## Examples

### Repository Management Workflow

```bash
#!/bin/bash
# Complete repository management workflow

APP_NAME="my-application"
REGION="us-east-1"

echo "=== Creating Repository ==="
aws-cloud-utilities ecr create-repository $APP_NAME --region $REGION --image-scanning --immutable-tags

echo "=== Getting Docker Login ==="
aws-cloud-utilities ecr get-login --region $REGION

echo "=== Repository Details ==="
aws-cloud-utilities ecr list-repositories --region $REGION --include-images --include-size

echo "=== Setup Complete ==="
```

### Image Migration Script

```bash
#!/bin/bash
# Migrate images between regions

SOURCE_REGION="us-east-1"
DEST_REGION="us-west-2"
REPO_NAME="my-app"

echo "=== Source Repository Images ==="
aws-cloud-utilities ecr list-images $REPO_NAME --region $SOURCE_REGION

echo "=== Creating Destination Repository ==="
aws-cloud-utilities ecr create-repository $REPO_NAME --region $DEST_REGION --image-scanning

echo "=== Copying Images ==="
# This would typically involve pulling and pushing images
# The copy-image command can help with this process

echo "=== Migration Complete ==="
```

### Security Audit Script

```bash
#!/bin/bash
# Security audit of ECR repositories

AUDIT_DIR="./ecr-audit-$(date +%Y%m%d)"
mkdir -p $AUDIT_DIR

echo "=== Repository Inventory ==="
aws-cloud-utilities ecr list-repositories --include-images --include-size --output-file $AUDIT_DIR/repositories.json

echo "=== Vulnerability Scan Results ==="
aws-cloud-utilities ecr list-repositories --output json | \
jq -r '.[].repositoryName' | \
while read repo; do
    echo "Scanning repository: $repo"
    aws-cloud-utilities ecr list-images $repo --include-vulnerabilities --output-file $AUDIT_DIR/vulnerabilities-$repo.json
done

echo "=== Audit Complete ==="
echo "Audit data saved to: $AUDIT_DIR"
```

### Cleanup Script

```bash
#!/bin/bash
# Clean up old and unused repositories

echo "=== Current Repositories ==="
aws-cloud-utilities ecr list-repositories --include-images

echo "=== Repositories to Delete ==="
# List repositories with no images or old images
aws-cloud-utilities ecr list-repositories --output json | \
jq -r '.[] | select(.imageCount == 0) | .repositoryName' | \
while read repo; do
    echo "Empty repository: $repo"
    read -p "Delete $repo? (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        aws-cloud-utilities ecr delete-repository $repo --force
    fi
done
```

## Common Use Cases

1. **Repository Management**
   ```bash
   aws-cloud-utilities ecr create-repository my-app --image-scanning --immutable-tags
   aws-cloud-utilities ecr list-repositories --include-images --include-size
   ```

2. **Image Operations**
   ```bash
   aws-cloud-utilities ecr list-images my-app --include-vulnerabilities
   aws-cloud-utilities ecr copy-image source:tag dest:tag
   ```

3. **Authentication**
   ```bash
   aws-cloud-utilities ecr get-login
   $(aws-cloud-utilities ecr get-login --no-include-email)
   ```

4. **Security Auditing**
   ```bash
   aws-cloud-utilities ecr list-repositories --include-images
   aws-cloud-utilities ecr list-images my-app --include-vulnerabilities
   ```

## Integration with Docker

ECR commands integrate well with Docker workflows:

```bash
# Get login and authenticate
$(aws-cloud-utilities ecr get-login --no-include-email)

# Build and tag image
docker build -t my-app:latest .
docker tag my-app:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest

# Push image
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest

# Verify upload
aws-cloud-utilities ecr list-images my-app
```

## Best Practices

- Enable image scanning for security vulnerability detection
- Use tag immutability for production repositories
- Regularly audit repositories for unused images
- Use lifecycle policies to manage image retention
- Implement proper IAM policies for ECR access
- Monitor repository sizes and costs
- Use multi-region replication for critical images
