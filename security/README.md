# AWS Security Tools

## `aws_blue_team.py`

This utility script gathers metrics from AWS security services such as WAF, GuardDuty, and Security Hub. It can run as a standalone script or be deployed as an AWS Lambda function.

## Features

- **WAF Metrics:** Retrieves overall allowed and blocked request counts for each Web ACL and provides per-rule blocked request counts by querying CloudWatch.
- **GuardDuty Metrics:** Aggregates GuardDuty findings counts by type, filtering by the finding update time.
- **Security Hub Metrics:** Aggregates Security Hub findings by type based on the creation timestamp.

## Requirements

- Python 3.x
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library

## Configuration

- **Time Window:** By default, the script aggregates data for the last 24 hours. Adjust the `time_range_hours` parameter in the functions if needed.
- **CloudWatch Period:** The WAF CloudWatch queries use a period of 300 seconds (5 minutes). Adjust this value in the script as necessary.

## Usage

### As a Standalone Script

Run the script directly from the command line:

```bash
python script_name.py
```
