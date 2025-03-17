#!/usr/bin/env python3
"""Manage S3 buckets using boto3 and argparse.

This script allows you to list S3 buckets along with their regions and sizes (using CloudWatch metrics), and create new S3 buckets with a default region of us-west-2 (unless specified otherwise).

The listing command now supports parallel processing with configurable worker threads, dynamic column alignment, filtering by region unless the --all-regions flag is provided, and an option to save the bucket list to a CSV file (raw bytes exported).
"""

import argparse
import boto3
import concurrent.futures
import logging
import sys
import datetime
import csv


def human_readable_size(num):
    if not isinstance(num, (int, float)):
        return str(num)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} PB"


def process_bucket(bucket, s3, verbose):
    bucket_name = bucket["Name"]
    try:
        location_response = s3.get_bucket_location(Bucket=bucket_name)
        region = location_response.get("LocationConstraint")
        if region is None:
            region = "us-east-1"
    except Exception as e:
        logging.error(f"Failed to get location for bucket {bucket_name}: {e}")
        region = "unknown"

    size = "N/A"
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = now - datetime.timedelta(days=2)
        end_time = now - datetime.timedelta(days=1)
        # CloudWatch metrics for S3 buckets are reported in us-east-1
        cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
        metric_response = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="BucketSizeBytes",
            Dimensions=[
                {"Name": "BucketName", "Value": bucket_name},
                {"Name": "StorageType", "Value": "StandardStorage"}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Average"]
        )
        datapoints = metric_response.get("Datapoints", [])
        if datapoints:
            size = int(datapoints[0].get("Average", 0))
        else:
            size = 0
    except Exception as e:
        if verbose:
            logging.debug(f"Failed to get metrics for bucket {bucket_name}: {e}")
        size = 0

    return {"Name": bucket_name, "Region": region, "SizeBytes": size}


def list_buckets(verbose, workers, region_filter, all_regions, csv_filename=None):
    s3 = boto3.client("s3")
    try:
        response = s3.list_buckets()
    except Exception as e:
        logging.error(f"Failed to list buckets: {e}")
        sys.exit(1)

    buckets = response.get("Buckets", [])
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_bucket, bucket, s3, verbose): bucket for bucket in buckets}
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                logging.error(f"Bucket generated an exception: {exc}")

    # If not listing all regions, filter by the specified region
    if not all_regions and region_filter:
        results = [r for r in results if r["Region"] == region_filter]

    # Determine dynamic width for Bucket Name column and human-readable size column
    name_header = "Bucket Name"
    name_width = max(len(name_header), *(len(r["Name"]) for r in results)) if results else len(name_header)
    region_header = "Region"
    region_width = 15
    size_header = "Size"
    hr_sizes = [human_readable_size(r["SizeBytes"]) for r in results]
    size_width = max(len(size_header), *(len(s) for s in hr_sizes)) if results else len(size_header)

    header = f"{name_header:<{name_width}} {region_header:<{region_width}} {size_header:<{size_width}}"
    print(header)
    print("-" * len(header))
    for r in results:
        hr_size = human_readable_size(r["SizeBytes"])
        print(f"{r['Name']:<{name_width}} {r['Region']:<{region_width}} {hr_size:<{size_width}}")

    if csv_filename:
        try:
            with open(csv_filename, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Bucket Name", "Region", "SizeBytes"])
                for r in results:
                    writer.writerow([r["Name"], r["Region"], r["SizeBytes"]])
            logging.info(f"Bucket list saved to {csv_filename}")
        except Exception as e:
            logging.error(f"Failed to save CSV file {csv_filename}: {e}")


def create_bucket(bucket_name, region, verbose):
    s3 = boto3.client("s3", region_name=region)
    try:
        if region == "us-west-2":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        logging.info(f"Bucket {bucket_name} created in region {region}.")
    except Exception as e:
        logging.error(f"Failed to create bucket {bucket_name}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Manage S3 buckets.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command to run")

    # Sub-command to list buckets
    list_parser = subparsers.add_parser("list", help="List all S3 buckets with region and size.")
    list_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    list_parser.add_argument("--workers", type=int, default=10, help="Number of worker threads for parallel processing (default: 10)")
    list_parser.add_argument("--region", default="us-west-2", help="Region to filter buckets (default: us-west-2)")
    list_parser.add_argument("--all-regions", action="store_true", help="List buckets from all regions")
    list_parser.add_argument("--save-csv", help="Save bucket list to CSV file (exports raw bytes)", default=None)

    # Sub-command to create a bucket
    create_parser = subparsers.add_parser("create", help="Create a new S3 bucket.")
    create_parser.add_argument("bucket_name", help="Name of the bucket to create")
    create_parser.add_argument("--region", default="us-west-2", help="Region to create the bucket in (default: us-west-2)")
    create_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    if args.command == "list":
        list_buckets(args.verbose, args.workers, args.region, args.all_regions, args.save_csv)
    elif args.command == "create":
        create_bucket(args.bucket_name, args.region, args.verbose)
    else:
        parser.error("Invalid command")


if __name__ == "__main__":
    main()
