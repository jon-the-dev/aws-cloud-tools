# Docker to AWS ECR Image Uploader

## Overview

This script automates the process of pulling a Docker image from a public or private registry and pushing it to an AWS ECR (Elastic Container Registry) repository. It leverages the Docker CLI via Python's subprocess module and utilizes boto3 for AWS ECR integration. The script is written in Python 3 and follows best practices for security, error handling, and scalability, including features like pagination and retries for transient errors.

## Features

- Pulls a specified Docker image from a registry.
- Tags the pulled image appropriately for AWS ECR.
- Authenticates with AWS ECR using boto3 and AWS credentials configured in ~/.aws/credentials or environment variables.
- Pushes the tagged image to your AWS ECR repository.
- Implements retry logic with configurable attempts and backoff to handle transient errors.
- Provides detailed logging and error messages to facilitate troubleshooting.

## Requirements

- **Python 3.x**: Ensure you are running Python 3.
- **Docker**: Docker must be installed and properly configured on your host machine.
- **AWS CLI or boto3 configuration**: Your AWS credentials should be configured (e.g., via ~/.aws/credentials or environment variables).
- **Python Packages**:
  - boto3
  - botocore

You can install the required Python packages using pip:

bash
pip install boto3 botocore


## Usage

Run the script from the command line with the following options:

bash
./script.py --source-image <SOURCE_IMAGE> --ecr-repo <ECR_REPO_URI> [--tag <TAG>] [--region <AWS_REGION>]


### Options

- `--source-image`: (Required) The Docker image to pull. Example: `ubuntu:latest`.
- `--ecr-repo`: (Required) The AWS ECR repository URI (without tag) where the image will be pushed. Example: `123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo`.
- `--tag`: (Optional) The tag to apply to the image in ECR. Default is `latest`.
- `--region`: (Optional) The AWS region to use. If not provided, boto3 will use the configured default region.

### Example

Pull the `ubuntu:latest` image and push it to your ECR repository with the `latest` tag:

bash
./script.py --source-image ubuntu:latest --ecr-repo 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo


Or, specifying a different tag and region:

bash
./script.py --source-image ubuntu:latest --ecr-repo 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo --tag stable --region us-east-1


## Additional Information

- The script uses a maximum of 3 retries with a 5-second backoff in case of transient errors during Docker commands.
- The AWS ECR login is performed automatically via boto3, extracting the authorization token and logging in via the Docker CLI.
- Ensure that Docker is installed and available in your system `PATH` before running the script.
- Error messages and logs are printed to aid in debugging if issues occur during image pull, tag, or push operations.

Happy Deploying!