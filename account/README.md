# Account Tools

## AWS Account Information Script

This script retrieves the contact information and alternate contacts for an AWS account using the AWS SDK for Python (Boto3).

### Prerequisites

- Python 3.x
- Boto3 library
- AWS credentials configured (e.g., via ~/.aws/credentials or environment variables)

### Installation

1. Clone this repo
2. Install the required Python packages (Pipenv in repo)
   1. `pip install boto3`

### Usage

Run the script to retrieve the contact information and alternate contacts for your AWS account:

### Output

The script will print the account contact information and alternate contacts in JSON format. Example output:

### Logging

The script uses Python's logging module to log debug and error messages. By default, the logging level is set to ERROR. You can change the logging level by modifying the `logging.basicConfig(level=logging.ERROR)` line in the script.
