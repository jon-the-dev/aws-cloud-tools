# AWS Cloud Tools

A collection of snippets used for AWS APIs.

## Features

### Account

* `aws_get_acct_info.py` - Get general account information.

### CostOps

* `aws_pricing.py` - Get current AWS pricing info available.
* `gpu_spots.py` - Find the cheapest place to fun your GPU Spot workload.

### Inventory

* `inventory.py` - Grab a list of all resources I could find via the boto3 library.

### Iam

* `iam_auditor.py` - Audit IAM and save all roles and policies locally.

### Networking

* `aws_ip_ranges.py` - Grab a list of IPranges for AWS Services. Good for DevSecOps Investigations.

### Support

* `aws_check_support.py` - Tool for verifying your AWS Support level.

### Sysadmin

* `s3_bucket_nuke.py` - Delete a bucket, all versions, all everything. Nuke it.
* `cw_logs\1_grab_logs.py` - Download all streams for a CloudWatch Log Group locally.
* `cw_logs\2_log_sizes.py` - List all log groups and streams and their sizes.
