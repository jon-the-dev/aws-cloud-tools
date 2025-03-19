#!/usr/bin/env python3
"""
This script downloads a Docker image and pushes it to an AWS ECR repository.
It uses the Docker CLI via Python's subprocess and boto3 for AWS ECR integration.
The script is written for Python 3 and leverages .aws/credentials for authentication.
It follows best practices for security, error handling, and scalability (pagination, retries, etc).
Note: This script assumes that Docker is installed and configured correctly on the host.
"""

import subprocess
import sys
import boto3
import botocore.exceptions
import argparse
import json
import os
import time

# Constants for retry and backoff in case of transient errors.
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds

def run_subprocess(cmd, capture_output=False):
    """
    Run a subprocess command and handle exceptions.
    This function centralizes subprocess execution for better error handling and potential retries.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            # Log executed command for debugging purposes
            print("Executing command: {}".format(" ".join(cmd)))
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE if capture_output else None, stderr=subprocess.PIPE, text=True)
            return result.stdout if capture_output else None
        except subprocess.CalledProcessError as e:
            # Provide detailed error output
            sys.stderr.write("Command failed with exit code {}: {}\n".format(e.returncode, e.stderr))
            attempt += 1
            if attempt < MAX_RETRIES:
                print("Retrying in {} seconds... (attempt {} of {})".format(RETRY_BACKOFF, attempt+1, MAX_RETRIES))
                time.sleep(RETRY_BACKOFF)
            else:
                sys.stderr.write("Max retries reached. Exiting.\n")
                sys.exit(e.returncode)
        except Exception as e:
            sys.stderr.write("Unexpected error: {}\n".format(str(e)))
            sys.exit(1)

def ecr_login(ecr_client, region):
    """
    Retrieve the Docker login command for ECR.
    Use boto3's get_authorization_token to authenticate with ECR.
    """
    try:
        response = ecr_client.get_authorization_token()
        # Extract the token from the first (and only) authorization data element.
        auth_data = response['authorizationData'][0]
        token = auth_data['authorizationToken']
        proxy_endpoint = auth_data['proxyEndpoint']
        # Use Docker login with the provided ECR credentials.
        login_cmd = [
            "docker", "login",
            "--username", "AWS",
            "--password-stdin",
            proxy_endpoint
        ]
        # Use the token (which is base64 encoded "AWS:password") as input for docker login.
        process = subprocess.Popen(login_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=token)
        if process.returncode != 0:
            sys.stderr.write("Docker login failed: {}\n".format(stderr))
            sys.exit(process.returncode)
        print("Docker login succeeded for endpoint: {}".format(proxy_endpoint))
        return proxy_endpoint
    except botocore.exceptions.ClientError as err:
        sys.stderr.write("Error during ECR login: {}\n".format(err))
        sys.exit(1)

def pull_docker_image(image):
    """
    Pull a Docker image from a registry.
    Uses docker pull command and retries on transient errors.
    """
    print("Pulling Docker image: {}".format(image))
    run_subprocess(["docker", "pull", image])

def tag_docker_image(source_image, target_image):
    """
    Tag the Docker image so that it is ready to be pushed to the target repository.
    """
    print("Tagging image {} to {}".format(source_image, target_image))
    run_subprocess(["docker", "tag", source_image, target_image])

def push_docker_image(target_image):
    """
    Push the Docker image to the repository.
    """
    print("Pushing Docker image: {}".format(target_image))
    run_subprocess(["docker", "push", target_image])

def parse_arguments():
    """
    Parse command-line arguments for specifying the source Docker image,
    target AWS ECR repository and optional AWS region.
    """
    parser = argparse.ArgumentParser(description='Download a Docker image and push it to an AWS ECR repository.')
    parser.add_argument('--source-image', required=True, help='The Docker image to pull (e.g., ubuntu:latest)')
    parser.add_argument('--ecr-repo', required=True, help='The AWS ECR repository URI (without tag) to push the image to (e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo)')
    parser.add_argument('--tag', default="latest", help='The tag to use for the image in ECR (default: latest)')
    parser.add_argument('--region', default=None, help='AWS region (if not set, boto3 will use configuration or environment variables)')
    return parser.parse_args()

def main():
    # Parse the command line arguments.
    args = parse_arguments()

    # Validate that Docker is installed; if not, exit immediately.
    if not shutil.which("docker"):
        sys.stderr.write("Docker is not installed or not available in PATH.\n")
        sys.exit(1)

    # Pull the specified Docker image
    pull_docker_image(args.source_image)

    # Instantiate a boto3 ECR client using the provided region or default configuration.
    try:
        if args.region:
            ecr_client = boto3.client('ecr', region_name=args.region)
        else:
            ecr_client = boto3.client('ecr')
    except botocore.exceptions.BotoCoreError as e:
        sys.stderr.write("Failed to create boto3 ECR client: {}\n".format(e))
        sys.exit(1)

    # Authenticate Docker with AWS ECR by obtaining a login token.
    ecr_registry_endpoint = ecr_login(ecr_client, args.region)

    # Construct the target image tag. It must be in the format: ECR repo URI:tag
    target_image = "{}:{}".format(args.ecr_repo, args.tag)

    # Tag the pulled Docker image with the new target image tag.
    tag_docker_image(args.source_image, target_image)

    # Push the tagged image to the specified AWS ECR repository.
    push_docker_image(target_image)

    print("Image {} has been successfully pushed to {}.".format(args.source_image, target_image))

if __name__ == "__main__":
    # Import shutil here to avoid global import if the module is never used.
    import shutil
    main()