#!/usr/bin/env python3
import argparse
import os
import sys
import logging
import boto3
import botocore
import json
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from random import shuffle

DEFAULT_CONFIG = Config(connect_timeout=10, read_timeout=10)

REGION_WORKERS = 5
CFN_THREADS = 2

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_all_regions() -> List[str]:
    """Get all AWS regions available for CloudFormation using EC2's describe_regions."""
    try:
        ec2 = boto3.client("ec2", config=DEFAULT_CONFIG)
        regions_info = ec2.describe_regions()["Regions"]
        regions = [region["RegionName"] for region in regions_info]
        logging.info("Retrieved all available regions.")
        shuffle(regions)  # Shuffle the regions for random processing order
        print(regions)
        return regions
    except botocore.exceptions.BotoCoreError as e:
        logging.error("Error retrieving regions: %s", e)
        sys.exit(1)


def get_account_id() -> str:
    """Retrieve the AWS account id using STS get_caller_identity."""
    try:
        sts = boto3.client("sts", config=DEFAULT_CONFIG)
        identity = sts.get_caller_identity()
        account_id = identity.get("Account")
        logging.info("Account ID retrieved: %s", account_id)
        return account_id
    except botocore.exceptions.BotoCoreError as e:
        logging.error("Error retrieving account id: %s", e)
        sys.exit(1)


def backup_stack(region: str, stack: Dict, base_dir: str) -> None:
    """Back up a single stack's template and parameters to the file system."""
    stack_name = stack.get("StackName")
    logging.info("Processing stack %s in region %s", stack_name, region)
    cf = boto3.client("cloudformation", region_name=region, config=DEFAULT_CONFIG)
    region_dir = os.path.join(base_dir, region)
    os.makedirs(region_dir, exist_ok=True)

    template_file = os.path.join(region_dir, f"{stack_name}.json")
    params_file = os.path.join(region_dir, f"{stack_name}-parameters.json")

    # Check if backup already exists: for stacks with parameters, ensure both files exist; for stacks without parameters, just check the template file
    parameters = stack.get("Parameters", [])
    if os.path.exists(template_file) and (not parameters or os.path.exists(params_file)):
        logging.info("Stack %s in region %s already backed up. Skipping.", stack_name, region)
        return

    # Retrieve the stack template
    try:
        template_response = cf.get_template(StackName=stack_name)
        template_body = template_response.get("TemplateBody", "")
    except botocore.exceptions.ClientError as e:
        logging.error(
            "Error retrieving template for stack %s in region %s: %s",
            stack_name,
            region,
            e,
        )
        return

    # Validate that template_body is not empty
    if not template_body:
        logging.warning(
            "Template for stack %s in region %s is empty. Skipping writing template.",
            stack_name,
            region,
        )
    else:
        # If the template is a dict (e.g., OrderedDict), convert it to JSON formatted string
        if isinstance(template_body, dict):
            try:
                template_str = json.dumps(template_body, indent=4)
            except Exception as e:
                logging.error(
                    "Error converting template for stack %s in region %s to JSON: %s",
                    stack_name,
                    region,
                    e,
                )
                return
        else:
            template_str = template_body

        # Write the template to file (using JSON format)
        try:
            with open(template_file, "w") as tf:
                tf.write(template_str)
            logging.info("Template saved for stack %s in %s", stack_name, template_file)
        except Exception as e:
            logging.error("Error writing template file for stack %s: %s", stack_name, e)

    # Save the stack parameters
    parameters = stack.get("Parameters", [])
    if not parameters:
        logging.warning(
            "No parameters found for stack %s in region %s. Skipping writing parameters.",
            stack_name,
            region,
        )
    else:
        # Convert parameters to a dict for JSON output
        params_dict = {
            param.get("ParameterKey"): param.get("ParameterValue")
            for param in parameters
        }
        try:
            params_str = json.dumps(params_dict, indent=4)
        except Exception as e:
            logging.error(
                "Error converting parameters for stack %s in region %s to JSON: %s",
                stack_name,
                region,
                e,
            )
            params_str = ""

        if params_str:
            try:
                with open(params_file, "w") as pf:
                    pf.write(params_str)
                logging.info(
                    "Parameters saved for stack %s in %s", stack_name, params_file
                )
            except Exception as e:
                logging.error(
                    "Error writing parameters file for stack %s: %s", stack_name, e
                )


def process_region(region: str, base_dir: str) -> None:
    """Retrieve all stacks in a given region and process each one."""
    logging.info("Processing region: %s", region)
    cf = boto3.client("cloudformation", region_name=region, config=DEFAULT_CONFIG)
    stacks = []
    try:
        paginator = cf.get_paginator("describe_stacks")
        for page in paginator.paginate():
            for stack in page.get("Stacks", []):
                if stack.get("StackStatus") != "DELETE_COMPLETE":
                    stacks.append(stack)
    except botocore.exceptions.ClientError as e:
        logging.error("Error describing stacks in region %s: %s", region, e)
        return

    if not stacks:
        logging.info("No stacks found in region %s", region)
        return

    with ThreadPoolExecutor(max_workers=CFN_THREADS) as executor:
        futures = {
            executor.submit(backup_stack, region, stack, base_dir): stack
            for stack in stacks
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error("Error processing stack in region %s: %s", region, e)


def main():
    parser = argparse.ArgumentParser(
        description="Backup AWS CloudFormation stacks and templates."
    )
    parser.add_argument(
        "--regions",
        type=str,
        help="Comma separated list of regions to process. If not provided, all regions are processed.",
    )
    parser.add_argument(
        "--destination",
        type=str,
        default=".",
        help="Destination directory where backups will be stored. Defaults to the current directory.",
    )
    args = parser.parse_args()

    if args.regions:
        regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    else:
        regions = get_all_regions()

    account_id = get_account_id()
    base_dir = os.path.join(args.destination, account_id)
    os.makedirs(base_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=REGION_WORKERS) as executor:
        futures = {
            executor.submit(process_region, region, base_dir): region
            for region in regions
        }
        for future in as_completed(futures):
            region = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.error("Error processing region %s: %s", region, e)


if __name__ == "__main__":
    main()
