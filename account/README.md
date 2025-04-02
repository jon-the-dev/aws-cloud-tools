# Account Tools

## `aws_get_axt_info.py`

This script retrieves the contact information and alternate contacts for an AWS account using the AWS SDK for Python (Boto3).

### Usage

Run the script to retrieve the contact information and alternate contacts for your AWS account:

### Output

The script will print the account contact information and alternate contacts in JSON format. Example output:

### Logging

The script uses Python's logging module to log debug and error messages. By default, the logging level is set to ERROR. You can change the logging level by modifying the `logging.basicConfig(level=logging.ERROR)` line in the script.

----

## `detect_control_tower.py`

This Python script detects whether the currently logged-in AWS account is part of an AWS Control Tower or a Landing Zone deployment. It does so by querying the CloudFormation stacks in the account and looking for known naming patterns associated with these deployments.

## Overview

The script uses the AWS SDK for Python (boto3) to interact with AWS services. It follows best practices for security, exception handling, and scalability by using:

- AWS STS to retrieve the current account identity.
- CloudFormation API with pagination to list stacks.
- Pattern matching on stack names to detect specific deployments:
  - AWS Control Tower deployments.
  - AWS Landing Zone deployments.

## Features

- **Account Identification:** Retrieves the current AWS account ID using AWS STS.
- **CloudFormation Stack Listing:** Uses boto3 pagination to efficiently list all non-deleted CloudFormation stacks.
- **Deployment Detection:** Checks the stack names for keywords indicative of AWS Control Tower or Landing Zone deployments.
- **Robust Error Handling:** Catches and handles errors during AWS API calls, providing informative output.

## Requirements

- Python 3.x
- boto3
- botocore

To install the required packages, you can run:

bash
pip install boto3 botocore

## Usage

1. Ensure that you have valid AWS credentials configured (e.g., using the AWS CLI or environment variables).

2. Run the script using Python 3:

    bash
    python3 aws_deployment_detector.py

3. The script will output:
   - The AWS Account ID being used.
   - Whether an AWS Control Tower deployment is detected.
   - Whether an AWS Landing Zone deployment is detected.

Example output:

AWS Account ID: 123456789012
Control Tower deployment detected in this account.
No Landing Zone deployment detected in this account.

## Notes

- The script scans only CloudFormation stacks that are active or completed (and even some failed states) by using a pre-defined filter based on stack status.
- Modify the substrings/patterns in the script (`controltower_patterns` and `landingzone_patterns`) if your deployments follow different naming conventions.

For any issues or questions, please refer to the AWS documentation or open an issue in the repository.
