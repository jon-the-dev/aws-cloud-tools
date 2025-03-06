# check_r53_cw_logs.py README

This Python script monitors DNS queries and detects anomalies in network traffic using CloudWatch logs. It analyzes failed DNS lookups to identify potential abuse or unusual activity.

## Overview

The script retrieves log data from a specified CloudWatch log group related to DNS operations, processes the logs to identify failed DNS queries, and flags any domains experiencing high volumes of failed lookups from unknown IPs.

## Description

1. **Data Collection**:
   - The script collects log events from a specific CloudWatch log group for the past 24 hours.
   - It extracts DNS query data (source IP addresses and domain names) from the logs.

2. **Filtering and Analysis**:
   - Filters out DNS queries originating from a whitelist of trusted IPs.
   - Identifies domains that experience failed DNS lookups exceeding a configured threshold.
   - Flags domains with high volumes of failed requests from unknown IPs as potential security concerns.

## Function Descriptions

### `get_dns_queries()`

- Fetches log events from CloudWatch for the specified log group and time range.
- Processes the logs to extract DNS query data (source IP addresses and domain names).
- Filters out queries originating from a whitelist of trusted IPs.

### `check_dns_failures()`

- Analyzes the filtered DNS query data for domains experiencing failed lookups.
- Flags domains with more than a specified threshold of failed requests from unknown IPs.

## Usage

Run the script with these parameters:

```bash
python check_r53_cw_logs.py
```

**Parameters:**

1. **`AWS_REGION` (str)**:
   - The AWS region where your CloudWatch log group resides. Example: `us-east-1`.

2. **`CLOUD_WATCH_LOG_GROUP` (str)**:
   - The name of your CloudWatch log group that contains DNS query logs.

3. **`IP_WHITELIST` (list)**:
   - List of IPs that should not be flagged as failed queries. Example: `['192.0.2.1', '192.0.2.2']`.

4. **`DOMAIN_THRESHOLD` (int)**:
   - The number of failed requests per domain above which the script will flag it as suspicious.

5. **`CHECK_INTERVAL` (int)**:
   - The interval in seconds between executions of the script.

## Installation

1. Install required dependencies:

   ```bash
   pip install boto3 botocore datetime json
   ```

2. Ensure you have access to:
   - AWS CLI for local development (optional but recommended).
   - AWS credentials stored as environment variables (`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

## Configuration

Adjust these settings based on your setup:

1. **CloudWatch Log Group**:
   Replace the default value with your actual CloudWatch log group name.

2. **IP Whitelist**:
   Add or modify the list of IPs that should not be flagged as suspicious.

3. **Domain Threshold**:
   Set the number of failed requests per domain above which the script will flag it as suspicious (default: 50).

4. **Check Interval**:
   Define how often the script should run (e.g., `86400` for daily checks).

## License

MIT License (2023)

## Usage Instructions

1. Run the script with the required parameters.
2. The script will monitor DNS queries and flag any domains experiencing suspicious activity.

## Output

The script prints to stdout when it detects anomalies, or nothing if everything is within expected limits.

## Notes

- Ensure your AWS region matches where your CloudWatch log group is deployed (e.g., `us-east-1` for a region in East Coast, USA).
- Verify the CloudWatch log group name and path match exactly what you're monitoring.
