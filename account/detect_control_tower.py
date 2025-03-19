#!/usr/bin/env python3
"""
This Python 3 script detects whether the currently logged in AWS account is part of
an AWS Control Tower or a Landing Zone deployment. It does so by querying the CloudFormation
stacks in the account for known naming patterns associated with Control Tower and Landing Zone.
The script follows security best practices (using boto3 with proper exception handling), scaling,
pagination, and error handling best practices.
"""

import boto3
import botocore
import argparse
import logging
import concurrent.futures

def get_caller_identity():
    """
    Use AWS STS to retrieve the current AWS account (caller) identity.
    This helps the user understand which account context the script is operating in.
    """
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        return identity
    except botocore.exceptions.BotoCoreError as e:
        # Use logging in production systems.
        print("Error retrieving caller identity: {}".format(e))
        exit(1)

def list_stacks(region):
    """
    List all CloudFormation stacks in the given region using pagination.
    """
    cf_client = boto3.client('cloudformation', region_name=region)
    paginator = cf_client.get_paginator('list_stacks')
    stack_status_filter = [
        'CREATE_COMPLETE',
        'UPDATE_COMPLETE',
        'CREATE_FAILED',
        'ROLLBACK_COMPLETE',
        'UPDATE_ROLLBACK_COMPLETE',
        'IMPORT_COMPLETE',
        'IMPORT_ROLLBACK_COMPLETE'
    ]
    stack_summaries = []
    try:
        for page in paginator.paginate(StackStatusFilter=stack_status_filter):
            stacks = page.get('StackSummaries', [])
            stack_summaries.extend(stacks)
        return stack_summaries
    except botocore.exceptions.BotoCoreError as e:
        print(f"Error listing CloudFormation stacks in {region}: {e}")
        return []

def get_all_regions():
    """
    Retrieve a list of all available AWS regions using EC2 describe_regions.
    """
    ec2_client = boto3.client('ec2')
    regions_info = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in regions_info['Regions']]
    return regions

def list_stacks_all_regions(verbose):
    """
    List CloudFormation stacks in all regions concurrently.
    Returns a dictionary with region as key and list of stacks as value.
    """
    regions = get_all_regions()
    all_stacks = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_region = {executor.submit(list_stacks, region): region for region in regions}
        for future in concurrent.futures.as_completed(future_to_region):
            region = future_to_region[future]
            try:
                stacks = future.result()
                all_stacks[region] = stacks
                if verbose:
                    logging.info(f"Retrieved {len(stacks)} stacks from region: {region}")
            except Exception as exc:
                if verbose:
                    logging.error(f"Error retrieving stacks from {region}: {exc}")
                all_stacks[region] = []
    return all_stacks

def detect_controltower_landingzone(stacks):
    """
    Detect if the account has deployments of AWS Control Tower and/or Landing Zone.
    This is done by matching stack names against known patterns.
    """
    # List of substrings/patterns that suggest a Control Tower deployment.
    controltower_patterns = ['AWSControlTower', 'AWS-Control-Tower']
    # List of substrings/patterns that suggest a Landing Zone deployment.
    landingzone_patterns = ['LandingZone', 'AWS-Landing-Zone']

    found_controltower = False
    found_landingzone = False

    for stack in stacks:
        stack_name = stack.get('StackName', '')
        # Check for control tower patterns
        for pattern in controltower_patterns:
            if pattern in stack_name:
                found_controltower = True
                # No need to check other patterns if already found
                break

        # Check for landing zone patterns
        for pattern in landingzone_patterns:
            if pattern in stack_name:
                found_landingzone = True
                break

        # If both are detected, we can break early for performance.
        if found_controltower and found_landingzone:
            break

    return found_controltower, found_landingzone

def main():
    parser = argparse.ArgumentParser(description='Detect AWS Control Tower or Landing Zone deployments across all regions.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Retrieve the caller identity
    identity = get_caller_identity()
    account_id = identity.get('Account', 'Unknown')
    print(f"AWS Account ID: {account_id}")

    # Retrieve stacks from all regions concurrently
    all_region_stacks = list_stacks_all_regions(args.verbose)

    # Aggregate stacks from all regions
    aggregated_stacks = []
    for region, stacks in all_region_stacks.items():
        if args.verbose:
            logging.info(f"Region {region} has {len(stacks)} stacks")
        aggregated_stacks.extend(stacks)

    # Analyze aggregated stacks
    controltower_detected, landingzone_detected = detect_controltower_landingzone(aggregated_stacks)

    if controltower_detected:
        print("Control Tower deployment detected in this account.")
    else:
        print("No Control Tower deployment detected in this account.")

    if landingzone_detected:
        print("Landing Zone deployment detected in this account.")
    else:
        print("No Landing Zone deployment detected in this account.")

if __name__ == '__main__':
    main()