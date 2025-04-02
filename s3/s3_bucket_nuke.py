#!/usr/bin/env python3
"""
This script will download all objects and versions from an S3 bucket and then delete the bucket.
It can be used to clean up a bucket and its contents, or to migrate the bucket to another account.
"""
import sys
import argparse
import boto3
import os
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


def configure_logging(dry_run):
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mode = "dry-run" if dry_run else "destroy"
    log_filename = f"bucket_{mode}_{timestamp}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return log_filename


def download_file_versioned(s3_client, bucket, key, version_id, download_dir, log):
    download_path = os.path.join(download_dir, key)
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    log.info(f"Downloading object {key} version {version_id} to {download_path}")
    s3_client.download_file(
        Bucket=bucket,
        Key=key,
        Filename=download_path,
        ExtraArgs={"VersionId": version_id},
    )


def download_file(s3_client, bucket, key, download_dir, log):
    download_path = os.path.join(download_dir, key)
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    log.info(f"Downloading object {key} to {download_path}")
    s3_client.download_file(bucket, key, download_path)


def download_objects(s3_client, bucket, download_dir, dry_run, log, workers=10):
    # Attempt to detect versioning
    versioning_status = s3_client.get_bucket_versioning(Bucket=bucket)
    versioned = versioning_status.get("Status") == "Enabled"

    if not os.path.exists(download_dir):
        if not dry_run:
            os.makedirs(download_dir, exist_ok=True)

    if versioned:
        paginator = s3_client.get_paginator("list_object_versions")
        iterator = paginator.paginate(Bucket=bucket)
        tasks = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for page in iterator:
                for version in page.get("Versions", []):
                    key = version["Key"]
                    version_id = version["VersionId"]
                    if key.endswith("/"):
                        log.info(f"Skipping folder marker {key} version {version_id}")
                        if dry_run:
                            print(f"Would skip folder marker: {key} (version: {version_id})")
                        continue
                    log.info(f"Scheduling download for object {key} version {version_id}")
                    if dry_run:
                        print(f"Would download {key} (version: {version_id})")
                    else:
                        task = executor.submit(download_file_versioned, s3_client, bucket, key, version_id, download_dir, log)
                        tasks.append(task)

            # Process delete markers (no download, just log if dry_run)
            for page in iterator:
                for marker in page.get("DeleteMarkers", []):
                    key = marker["Key"]
                    version_id = marker["VersionId"]
                    log.info(f"Not downloading delete marker {key} version {version_id}")
                    if dry_run:
                        print(f"Would skip download delete marker: {key} (version: {version_id})")

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    log.error(f"Error downloading a versioned object: {e}")
    else:
        paginator = s3_client.get_paginator("list_objects_v2")
        iterator = paginator.paginate(Bucket=bucket)
        tasks = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for page in iterator:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith("/"):
                        log.info(f"Skipping folder marker {key}")
                        if dry_run:
                            print(f"Would skip folder marker: {key}")
                        continue
                    log.info(f"Scheduling download for object {key}")
                    if dry_run:
                        print(f"Would download {key}")
                    else:
                        task = executor.submit(download_file, s3_client, bucket, key, download_dir, log)
                        tasks.append(task)

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    log.error(f"Error downloading an object: {e}")


def delete_objects_and_bucket(s3_client, bucket, dry_run, log):
    # Attempt to detect versioning
    versioning_status = s3_client.get_bucket_versioning(Bucket=bucket)
    versioned = versioning_status.get("Status") == "Enabled"

    if versioned:
        paginator = s3_client.get_paginator("list_object_versions")
        iterator = paginator.paginate(Bucket=bucket)

        to_delete = []
        count = 1
        for page in iterator:
            log.info(f"Processing page {count}")
            count += 1
            for version in page.get("Versions", []):
                to_delete.append(
                    {"Key": version["Key"], "VersionId": version["VersionId"]}
                )
            for marker in page.get("DeleteMarkers", []):
                to_delete.append(
                    {"Key": marker["Key"], "VersionId": marker["VersionId"]}
                )

        # Batch delete
        # Note: S3 delete_objects can handle up to 1000 keys at a time.
        for i in range(0, len(to_delete), 1000):
            batch = to_delete[i : i + 1000]
            log.info(
                f"Preparing to delete {len(batch)} objects/versions in batch {i // 1000 + 1} of {((len(to_delete)-1)//1000) + 1}."
            )
            if dry_run:
                for d in batch:
                    print(f"Would delete {d}")
            else:
                log.info(f"Deleting batch {i // 1000 + 1}: {batch}")
                s3_client.delete_objects(
                    Bucket=bucket, Delete={"Objects": batch, "Quiet": True}
                )
                log.info(f"Deleted batch {i // 1000 + 1} successfully.")

    else:
        # Non-versioned bucket
        paginator = s3_client.get_paginator("list_objects_v2")
        iterator = paginator.paginate(Bucket=bucket)

        to_delete = []
        for page in iterator:
            for obj in page.get("Contents", []):
                to_delete.append({"Key": obj["Key"]})

        for i in range(0, len(to_delete), 1000):
            batch = to_delete[i : i + 1000]
            log.info(
                f"Preparing to delete {len(batch)} objects in batch {i // 1000 + 1} of {((len(to_delete)-1)//1000) + 1}."
            )
            if dry_run:
                for d in batch:
                    print(f"Would delete {d}")
            else:
                log.info(f"Deleting batch {i // 1000 + 1}: {batch}")
                s3_client.delete_objects(
                    Bucket=bucket, Delete={"Objects": batch, "Quiet": True}
                )
                log.info(f"Deleted batch {i // 1000 + 1} successfully.")

    # Finally, delete the bucket
    if dry_run:
        print(f"Would delete bucket {bucket}")
    else:
        log.info(f"Deleting bucket {bucket}")
        s3_client.delete_bucket(Bucket=bucket)


def main():
    parser = argparse.ArgumentParser(description="Download and destroy an S3 bucket.")
    parser.add_argument("bucket", help="Name of the S3 bucket to destroy")
    parser.add_argument("--region", help="AWS region of the bucket", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the actions without making changes",
    )
    parser.add_argument('--workers', type=int, default=10, help='Number of concurrent download workers')

    args = parser.parse_args()

    bucket = args.bucket
    dry_run = args.dry_run
    region = args.region

    # Configure logging
    log_filename = configure_logging(dry_run)
    log = logging.getLogger(__name__)
    log.info(f"Starting {'dry-run' if dry_run else 'destroy'} for bucket {bucket}")

    # Create S3 client
    if region:
        s3_client = boto3.client("s3", region_name=region)
    else:
        s3_client = boto3.client("s3")

    # Check bucket existence
    try:
        s3_client.head_bucket(Bucket=bucket)
    except Exception as e:
        log.error(f"Bucket {bucket} does not seem to exist or not accessible.")
        print(f"Error: {e}")
        sys.exit(1)

    # Print bucket tags
    try:
        tags_response = s3_client.get_bucket_tagging(Bucket=bucket)
        tag_set = tags_response.get("TagSet", [])
        if tag_set:
            print("Bucket Tags:")
            for tag in tag_set:
                print(f"  {tag['Key']}: {tag['Value']}")
        else:
            print("No tags found for the bucket.")
    except Exception:
        print("No tags found for the bucket.")

    # Print bucket size from CloudWatch metrics
    cloudwatch_client = boto3.client("cloudwatch")
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(days=3)
    try:
        metrics_response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="BucketSizeBytes",
            Dimensions=[
                {"Name": "BucketName", "Value": bucket},
                {"Name": "StorageType", "Value": "StandardStorage"},
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Average"],
        )
        datapoints = metrics_response.get("Datapoints", [])
        if datapoints:
            latest_datapoint = sorted(
                datapoints, key=lambda d: d["Timestamp"], reverse=True
            )[0]
            bucket_size_bytes = latest_datapoint["Average"]
            print(f"Bucket Size (StandardStorage): {bucket_size_bytes} bytes")
        else:
            print("Bucket size metric not available.")
    except Exception:
        print("Error retrieving bucket size from CloudWatch.")

    # If not dry-run, warn user
    if not dry_run:
        print(
            "WARNING: You are about to PERMANENTLY delete this bucket and all of its objects and versions."
        )
        print(f"Bucket: {bucket}")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted by user.")
            log.info("Operation aborted by user.")
            sys.exit(0)

    download_dir = bucket  # Download to a directory named after the bucket
    download_objects(s3_client, bucket, download_dir, dry_run, log, workers=args.workers)
    delete_objects_and_bucket(s3_client, bucket, dry_run, log)

    log.info("Operation completed.")
    if dry_run:
        print("Dry-run completed. No changes were made.")
    else:
        print("Bucket and objects deleted.")

    print(f"Logs can be found in {log_filename}")


if __name__ == "__main__":
    main()
