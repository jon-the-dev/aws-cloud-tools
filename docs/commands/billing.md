# Billing Commands

The billing commands provide management capabilities for AWS billing and Cost and Usage Reports (CUR).

## Overview

Cost and Usage Reports (CUR) provide detailed information about your AWS costs and usage. These commands help you manage CUR 2.0 reports, which provide enhanced capabilities for cost analysis and optimization.

## Available Commands

### cur-list

List all existing Cost and Usage Reports in your AWS account.

```bash
aws-cloud-utilities billing cur-list [OPTIONS]
```

**Options:**
- `--output-file`: Output file for CUR reports list (supports .json, .yaml, .csv)

**Examples:**
```bash
# List all CUR reports
aws-cloud-utilities billing cur-list

# Export list to JSON file
aws-cloud-utilities billing cur-list --output-file cur-reports.json
```

### cur-details

Show detailed configuration for a specific CUR report.

```bash
aws-cloud-utilities billing cur-details REPORT_NAME [OPTIONS]
```

**Arguments:**
- `REPORT_NAME`: Name of the CUR report to show details for

**Options:**
- `--output-file`: Output file for CUR report details (supports .json, .yaml)

**Examples:**
```bash
# Show details for a specific report
aws-cloud-utilities billing cur-details my-cur-report

# Export details to file
aws-cloud-utilities billing cur-details my-cur-report --output-file report-details.json
```

### cur-create

Create a new Cost and Usage Report (CUR 2.0).

```bash
aws-cloud-utilities billing cur-create [OPTIONS]
```

**Required Options:**
- `--report-name`: Name for the new CUR report
- `--bucket`: S3 bucket name for CUR delivery

**Optional Options:**
- `--prefix`: S3 prefix for CUR files (default: cur-reports)
- `--format`: Report format - textORcsv or Parquet (default: textORcsv)
- `--compression`: Compression type - GZIP, ZIP, or Parquet (default: GZIP)
- `--schema-elements`: Additional schema elements (default: RESOURCES)

**Examples:**
```bash
# Create a basic CUR report
aws-cloud-utilities billing cur-create \
  --report-name my-cur-report \
  --bucket my-cur-bucket

# Create CUR report with custom settings
aws-cloud-utilities billing cur-create \
  --report-name detailed-cur-report \
  --bucket my-cur-bucket \
  --prefix billing/cur-data \
  --format Parquet \
  --compression Parquet \
  --schema-elements RESOURCES
```

### cur-delete

Delete a Cost and Usage Report.

```bash
aws-cloud-utilities billing cur-delete REPORT_NAME [OPTIONS]
```

**Arguments:**
- `REPORT_NAME`: Name of the CUR report to delete

**Options:**
- `--confirm`: Skip confirmation prompt

**Examples:**
```bash
# Delete a CUR report (with confirmation)
aws-cloud-utilities billing cur-delete my-cur-report

# Delete without confirmation prompt
aws-cloud-utilities billing cur-delete my-cur-report --confirm
```

### cur-validate-bucket

Validate S3 bucket permissions for CUR delivery.

```bash
aws-cloud-utilities billing cur-validate-bucket BUCKET_NAME [OPTIONS]
```

**Arguments:**
- `BUCKET_NAME`: S3 bucket name to validate

**Options:**
- `--prefix`: S3 prefix for CUR files (optional)

**Examples:**
```bash
# Validate bucket permissions
aws-cloud-utilities billing cur-validate-bucket my-cur-bucket

# Validate with specific prefix
aws-cloud-utilities billing cur-validate-bucket my-cur-bucket --prefix cur-data
```

## Cost and Usage Reports (CUR) Overview

### What are Cost and Usage Reports?

Cost and Usage Reports (CUR) provide the most comprehensive set of AWS cost and usage data available. These reports include additional metadata about AWS services, pricing, and reservations that can help you better understand your costs.

### CUR 2.0 Features

- **Hourly granularity**: Get detailed cost information at hourly intervals
- **Resource-level data**: Track costs down to individual resources
- **Multiple output formats**: Support for CSV and Parquet formats
- **Integration ready**: Works with Amazon Athena, Amazon Redshift, and Amazon QuickSight
- **Automated delivery**: Reports are automatically delivered to your S3 bucket

### S3 Bucket Requirements

To create a CUR report, you need an S3 bucket with proper permissions. The bucket policy must allow the AWS billing service to:

1. Get bucket ACL and policy
2. Put objects in the specified bucket and prefix

The `cur-create` command will automatically configure the required bucket policy if it doesn't exist.

### Report Schema Elements

- **RESOURCES**: Include resource IDs for each line item (recommended)
- Additional schema elements can be specified during report creation

### Cost Analysis Workflow

1. **Create CUR report**: Use `cur-create` to set up automated cost reporting
2. **Validate setup**: Use `cur-validate-bucket` to ensure proper permissions
3. **Monitor reports**: Use `cur-list` to track available reports
4. **Analyze data**: Reports are delivered to S3 within 24 hours and can be analyzed using:
   - Amazon Athena for SQL queries
   - Amazon QuickSight for visualization
   - Custom analytics tools

## Prerequisites

- AWS CLI configured with appropriate credentials
- IAM permissions for:
  - `cur:DescribeReportDefinitions`
  - `cur:PutReportDefinition`
  - `cur:DeleteReportDefinition`
  - `s3:GetBucketAcl`
  - `s3:GetBucketPolicy`
  - `s3:PutBucketPolicy`
  - `s3:PutObject` (for the target S3 bucket)

## Notes

- CUR API is only available in the us-east-1 region
- Reports are generated within 24 hours of creation
- Historical data is not included in new reports
- Reports can be quite large; consider using compression and appropriate S3 storage classes