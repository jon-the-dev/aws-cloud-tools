# Tag Filtering Feature

## Overview

AWS Cloud Utilities now supports tag-based filtering across multiple commands, allowing you to scope operations to resources with specific tag keys and values. This enables you to:

- Filter inventory scans to specific environments (e.g., `Environment=Production`)
- Target cost optimization to tagged resources
- Limit operations to resources with specific owners or projects
- Narrow down analysis to tagged subsets of your infrastructure

## Usage

Tag filtering is available through two command-line options that can be added to supported commands:

- `--tag-key <KEY>`: Filter resources by tag key (e.g., `Environment`, `Owner`, `Project`)
- `--tag-value <VALUE>`: Filter resources by tag value (requires `--tag-key`)

### Basic Examples

```bash
# List all resources with the "Environment" tag (any value)
aws-cloud-utilities inventory scan --include-tags --tag-key Environment

# List only Production resources
aws-cloud-utilities inventory scan --include-tags --tag-key Environment --tag-value Production

# Analyze EBS volumes tagged with a specific project
aws-cloud-utilities costops ebs-optimization --tag-key Project --tag-value MyProject

# List RDS instances for a specific owner
aws-cloud-utilities rds list-instances --tag-key Owner --tag-value john@example.com

# List S3 buckets with specific tags
aws-cloud-utilities s3 list-buckets --tag-key CostCenter --tag-value Engineering
```

## Supported Commands

Tag filtering is currently supported in the following commands:

### Inventory Commands

#### 1. `inventory scan`
Comprehensive AWS resource inventory with tag-based filtering.

```bash
# Scan only Production resources across all services
aws-cloud-utilities inventory scan \
  --include-tags \
  --tag-key Environment \
  --tag-value Production \
  --output-dir ./prod-inventory

# Scan specific services with tag filter
aws-cloud-utilities inventory scan \
  --services ec2,rds,s3 \
  --include-tags \
  --tag-key Project \
  --tag-value WebApp \
  --regions us-east-1,us-west-2
```

**Note:** The `--include-tags` flag is automatically enabled when using `--tag-key`.

#### 2. `inventory download-all`
Comprehensive inventory download with tag filtering.

```bash
# Download full inventory for tagged resources
aws-cloud-utilities inventory download-all \
  --include-tags \
  --tag-key Department \
  --tag-value Engineering \
  --include-cloudformation \
  --output-dir ./eng-inventory
```

#### 3. `inventory workspaces`
WorkSpaces inventory with tag-based filtering.

```bash
# List WorkSpaces for a specific team
aws-cloud-utilities inventory workspaces \
  --tag-key Team \
  --tag-value DevOps \
  --include-metrics \
  --region us-east-1
```

### Cost Optimization Commands

#### 4. `costops ebs-optimization`
Analyze EBS volumes for optimization opportunities with tag filtering.

```bash
# Optimize only Production EBS volumes
aws-cloud-utilities costops ebs-optimization \
  --tag-key Environment \
  --tag-value Production \
  --all-regions \
  --include-cost-estimates

# Target specific project volumes
aws-cloud-utilities costops ebs-optimization \
  --tag-key Project \
  --tag-value Analytics \
  --volume-type gp2 \
  --show-recommendations
```

### Database Commands

#### 5. `rds list-instances`
List RDS instances with tag-based filtering.

```bash
# List Production MySQL databases
aws-cloud-utilities rds list-instances \
  --engine mysql \
  --tag-key Environment \
  --tag-value Production

# Find databases owned by a specific team
aws-cloud-utilities rds list-instances \
  --tag-key Team \
  --tag-value DataPlatform \
  --status available
```

### Storage Commands

#### 6. `s3 list-buckets`
List S3 buckets with tag-based filtering.

```bash
# List buckets for a specific cost center
aws-cloud-utilities s3 list-buckets \
  --tag-key CostCenter \
  --tag-value Marketing \
  --include-size

# Find buckets in a specific region with tags
aws-cloud-utilities s3 list-buckets \
  --region us-west-2 \
  --tag-key Project \
  --tag-value DataLake \
  --output-file buckets.csv
```

## How It Works

### Tag Matching

The tag filter matches resources based on:

1. **Tag Key Only**: If only `--tag-key` is specified, any resource with that tag key will match (regardless of value)
2. **Tag Key and Value**: If both `--tag-key` and `--tag-value` are specified, only resources with both the key AND the exact value will match

### Tag Format Support

The tag filter automatically handles various AWS tag formats:

- **List of dictionaries**: `[{"Key": "Environment", "Value": "Production"}]`
- **Dictionary format**: `{"Environment": "Production"}`
- **TagList format**: Used by RDS, WorkSpaces, and other services
- **TagSet format**: Used by S3

### Performance Considerations

1. **Inventory Commands**: Tag enrichment is performed during the scan, and filtering happens on the client side after tags are retrieved
2. **Resource-Specific Commands**: Tags are fetched individually for each resource (RDS, S3)
3. **Large-Scale Operations**: For better performance with many resources, the filter uses AWS Resource Groups Tagging API when possible

### Output and Reporting

When tag filtering is enabled:

- Commands display the active tag filter at the start: `Tag Filter: Environment=Production`
- Summary reports include the tag filter criteria
- Statistics show both total resources and filtered results
- Logs indicate how many resources were filtered out

## Common Use Cases

### 1. Environment-Based Operations

```bash
# Inventory Production environment
aws-cloud-utilities inventory scan \
  --include-tags \
  --tag-key Environment \
  --tag-value Production

# Optimize Development EBS volumes
aws-cloud-utilities costops ebs-optimization \
  --tag-key Environment \
  --tag-value Development \
  --all-regions
```

### 2. Project-Based Analysis

```bash
# Analyze all resources for a specific project
aws-cloud-utilities inventory scan \
  --include-tags \
  --tag-key Project \
  --tag-value MobileApp \
  --all-regions

# List RDS instances for the project
aws-cloud-utilities rds list-instances \
  --tag-key Project \
  --tag-value MobileApp
```

### 3. Cost Center Reporting

```bash
# Generate inventory for a cost center
aws-cloud-utilities inventory download-all \
  --include-tags \
  --tag-key CostCenter \
  --tag-value Engineering \
  --output-dir ./eng-costs

# Find S3 buckets for cost analysis
aws-cloud-utilities s3 list-buckets \
  --tag-key CostCenter \
  --tag-value Engineering \
  --include-size
```

### 4. Team-Based Resource Management

```bash
# List WorkSpaces for a specific team
aws-cloud-utilities inventory workspaces \
  --tag-key Team \
  --tag-value DevOps \
  --region us-east-1

# Find all RDS instances owned by a team
aws-cloud-utilities rds list-instances \
  --tag-key Team \
  --tag-value Backend
```

## Best Practices

1. **Consistent Tagging**: Ensure your AWS resources have consistent tag keys and values across your organization
2. **Tag Strategy**: Define a clear tagging strategy (e.g., Environment, Project, Owner, CostCenter)
3. **Include Tags Flag**: Remember to use `--include-tags` with inventory commands when filtering by tags
4. **Error Handling**: Resources without tags will be automatically excluded from filtered results
5. **Testing**: Test filters with `--tag-key` only first to see all possible values before adding `--tag-value`

## Implementation Details

### Architecture

The tag filtering feature is implemented through:

1. **TagFilter Class** (`core/tag_filter.py`): Central filtering logic
   - Handles multiple tag formats
   - Provides client-side filtering
   - Optionally uses AWS Resource Groups Tagging API

2. **Command Integration**: Commands pass tag filter to resource retrieval functions
3. **Backward Compatibility**: Filtering is optional and doesn't affect existing behavior

### Error Handling

- Resources without tags are excluded from filtered results
- Tag fetch errors are logged but don't stop the operation
- If tag filtering fails, commands gracefully fall back to showing all resources with a warning

## Future Enhancements

Potential future improvements:

1. **Multiple Tag Filters**: Support for multiple tag key-value pairs (AND logic)
2. **Tag Value Patterns**: Support for wildcard or regex patterns in tag values
3. **Negative Filters**: Exclude resources with specific tags
4. **Resource Groups Integration**: Direct integration with AWS Resource Groups
5. **Tag-Based Operations**: Actions like bulk tagging or tag modification

## Troubleshooting

### Issue: No results when using tag filter

**Possible causes:**
- Resources don't have the specified tags
- Tag key or value spelling doesn't match exactly (case-sensitive)
- For inventory commands, forgot to include `--include-tags`

**Solutions:**
```bash
# First, verify tags exist on resources
aws-cloud-utilities inventory scan --include-tags

# Try with just the key to see all values
aws-cloud-utilities inventory scan --include-tags --tag-key Environment

# Check for case sensitivity
aws-cloud-utilities inventory scan --include-tags --tag-key environment --tag-value production
```

### Issue: Tag filtering is slow

**Possible causes:**
- Many resources require individual tag lookups
- Network latency to AWS APIs

**Solutions:**
- Use `--region` to limit scope
- Use `--services` to filter specific services
- Run operations during off-peak hours for large accounts

## Contributing

To add tag filtering support to additional commands:

1. Import `TagFilter` from `core.tag_filter`
2. Add `--tag-key` and `--tag-value` options
3. Create TagFilter instance with the options
4. Pass filter to resource retrieval functions
5. Apply filtering using `tag_filter.matches()` or `tag_filter.filter_resources()`

See existing commands for implementation examples.

## Related Resources

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [AWS Resource Groups Tagging API](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/Welcome.html)
- [Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
