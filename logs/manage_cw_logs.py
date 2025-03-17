#!/usr/bin/env python3
import boto3
import argparse
import os
import datetime
import re
import logging
import sys
import io
import concurrent.futures
import json


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    """
    return re.sub(r'[\\/:"*?<>|]+', "_", name)


def human_readable_size(num):
    """
    Convert a byte value into a human-readable string (e.g., MB, GB, TB).
    """
    if not isinstance(num, (int, float)):
        return str(num)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} PB"


def capture_list_log_groups(region: str, verbose: bool) -> str:
    """
    Capture the output of list_log_groups for a given region and return it as a string.
    """
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        list_log_groups(region, verbose)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


def download_logs_for_group(client, log_group: str, days: int, verbose: bool):
    """
    Downloads logs from the specified CloudWatch log group for the last 'days' days.
    Each log stream's events are saved into a separate file under a directory named for the log group.
    """
    now = int(datetime.datetime.now().timestamp() * 1000)
    start_time = int(
        (datetime.datetime.now() - datetime.timedelta(days=days)).timestamp() * 1000
    )

    logging.info(f"Downloading logs for log group: {log_group}")
    output_dir = f"logs_{sanitize_filename(log_group)}"
    os.makedirs(output_dir, exist_ok=True)

    client_logs = boto3.client("logs", region_name=client.meta.region_name)
    paginator = client_logs.get_paginator("describe_log_streams")
    log_streams = []
    for page in paginator.paginate(logGroupName=log_group):
        streams_in_page = page.get("logStreams", [])
        log_streams.extend(streams_in_page)
        if verbose:
            logging.debug(
                f"Retrieved {len(streams_in_page)} streams for group '{log_group}'. Total so far: {len(log_streams)}"
            )

    logging.info(f"Found {len(log_streams)} log streams in log group '{log_group}'.")

    for stream in log_streams:
        log_stream_name = stream.get("logStreamName")
        logging.info(
            f"Downloading logs for stream: {log_stream_name} in group: {log_group}"
        )
        filename = os.path.join(output_dir, f"{sanitize_filename(log_stream_name)}.log")
        with open(filename, "a", encoding="utf-8") as f:
            kwargs = {
                "logGroupName": log_group,
                "logStreamName": log_stream_name,
                "startTime": start_time,
                "endTime": now,
                "startFromHead": True,
            }
            iteration_count = 0
            total_events_downloaded = 0
            repeated_token_count = 0
            max_repeated_token_count = 3
            while True:
                iteration_count += 1
                response = client_logs.get_log_events(**kwargs)
                events = response.get("events", [])
                total_events_downloaded += len(events)
                logging.info(
                    f"Stream '{log_stream_name}': iteration {iteration_count}, total events downloaded: {total_events_downloaded}"
                )
                if verbose:
                    logging.debug(
                        f"Retrieved {len(events)} events for stream '{log_stream_name}' (token: {kwargs.get('nextToken')})"
                    )
                for event in events:
                    ts = datetime.datetime.fromtimestamp(
                        event["timestamp"] / 1000
                    ).isoformat()
                    message = event["message"]
                    f.write(f"[{ts}] {message}\n")
                next_token = response.get("nextForwardToken")
                if kwargs.get("nextToken") == next_token:
                    repeated_token_count += 1
                    logging.debug(
                        f"Token unchanged for stream '{log_stream_name}' (repeated count: {repeated_token_count})"
                    )
                    if repeated_token_count >= max_repeated_token_count:
                        logging.warning(
                            f"Token hasn't changed after {max_repeated_token_count} iterations for stream '{log_stream_name}'. Exiting pagination."
                        )
                        break
                else:
                    repeated_token_count = 0
                kwargs["nextToken"] = next_token
                if not events:
                    break
        logging.info(f"Logs for stream '{log_stream_name}' written to {filename}")


def download_logs(log_group: str, days: int, verbose: bool, region: str):
    """
    Downloads logs for a specified log group. If 'ALL' is provided as the log_group name,
    the script will loop through all log groups in the given region.
    """
    client = boto3.client("logs", region_name=region)
    if log_group.upper() == "ALL":
        paginator = client.get_paginator("describe_log_groups")
        all_groups = []
        for page in paginator.paginate():
            groups = page.get("logGroups", [])
            all_groups.extend(groups)
            if verbose:
                logging.debug(
                    f"Retrieved {len(groups)} groups in current page. Total so far: {len(all_groups)}"
                )
        logging.info(f"Found {len(all_groups)} log groups in region {region}.")
        for group in all_groups:
            group_name = group.get("logGroupName")
            download_logs_for_group(client, group_name, days, verbose)
    else:
        download_logs_for_group(client, log_group, days, verbose)


def list_log_groups(region: str, verbose: bool):
    """
    Lists all CloudWatch log groups in the specified region along with their stored size, retention policy, and tags (printed on multiple rows).
    """
    client = boto3.client("logs", region_name=region)
    paginator = client.get_paginator("describe_log_groups")
    all_groups = []
    for page in paginator.paginate():
        groups = page.get("logGroups", [])
        all_groups.extend(groups)
        if verbose:
            logging.debug(
                f"Retrieved {len(groups)} groups in current page. Total so far: {len(all_groups)}"
            )
    logging.info(f"Found {len(all_groups)} log groups in region {region}.")

    # Retrieve tags and retention for each log group
    for group in all_groups:
        log_group_name = group.get("logGroupName", "")
        try:
            tag_response = client.list_tags_log_group(logGroupName=log_group_name)
            tags_dict = tag_response.get("tags", {})
            # Store tags as a list of strings
            tags_list = [f"{k}:{v}" for k, v in tags_dict.items()]
        except Exception as e:
            if verbose:
                logging.debug(f"Failed to get tags for log group {log_group_name}: {e}")
            tags_list = []
        group["Tags"] = tags_list
        # Get retention policy if set, otherwise use 'Never'
        retention = group.get("retentionInDays", "Never")
        group["Retention"] = str(retention)

    # Determine dynamic widths for columns
    name_header = "Log Group Name"
    size_header = "Size"
    retention_header = "Retention"
    name_width = (
        max(
            len(name_header),
            *(len(group.get("logGroupName", "")) for group in all_groups),
        )
        if all_groups
        else len(name_header)
    )
    size_width = (
        max(
            len(size_header),
            *(
                len(human_readable_size(group.get("storedBytes", 0)))
                for group in all_groups
            ),
        )
        if all_groups
        else len(size_header)
    )
    retention_width = (
        max(
            len(retention_header),
            *(len(group.get("Retention", "")) for group in all_groups),
        )
        if all_groups
        else len(retention_header)
    )

    header = f"{name_header:<{name_width}} {size_header:<{size_width}} {retention_header:<{retention_width}}"
    print(header)
    print("-" * (name_width + size_width + retention_width + 2))
    for group in all_groups:
        log_name = group.get("logGroupName", "")
        stored_bytes = group.get("storedBytes", 0)
        hr_size = human_readable_size(stored_bytes)
        retention = group.get("Retention", "Never")
        print(
            f"{log_name:<{name_width}} {hr_size:<{size_width}} {retention:<{retention_width}}"
        )
        tags_list = group.get("Tags", [])
        if tags_list:
            for tag in tags_list:
                # Print each tag on a new indented line
                print(
                    f"{'':<{name_width}} {'':<{size_width}} {'':<{retention_width}}  Tag: {tag}"
                )


def set_retention(
    log_group: str, retention: int, region: str, verbose: bool, if_never: bool = False
):
    """
    Sets the retention policy for a specified log group. If 'if_never' is True, then the retention will only be set if the current retention is 'Never'.
    Before setting the retention, all logs for the log group are downloaded.
    """
    client = boto3.client("logs", region_name=region)

    if if_never:
        # Describe the log group to check current retention
        response = client.describe_log_groups(logGroupNamePrefix=log_group)
        groups = response.get("logGroups", [])
        current_retention = "Never"
        for group in groups:
            if group.get("logGroupName") == log_group:
                if "retentionInDays" in group:
                    current_retention = group["retentionInDays"]
                break
        if current_retention != "Never":
            logging.info(
                f"Log group '{log_group}' already has retention set to {current_retention}. Skipping update."
            )
            return

    # Download ALL logs for this log group before setting retention
    # Use a very large number of days to approximate 'all logs'
    download_days = 10000
    logging.info(
        f"Downloading all logs for log group '{log_group}' before setting retention."
    )
    download_logs_for_group(client, log_group, download_days, verbose)

    try:
        client.put_retention_policy(logGroupName=log_group, retentionInDays=retention)
        logging.info(
            f"Retention policy for log group '{log_group}' set to {retention} days."
        )
    except Exception as e:
        logging.error(
            f"Failed to set retention policy for log group '{log_group}': {e}"
        )
        sys.exit(1)


def delete_log_group(log_group: str, region: str, verbose: bool):
    """
    Deletes a specified log group.
    """
    client = boto3.client("logs", region_name=region)
    try:
        client.delete_log_group(logGroupName=log_group)
        logging.info(f"Log group '{log_group}' deleted.")
    except Exception as e:
        logging.error(f"Failed to delete log group '{log_group}': {e}")
    sys.exit(1)


def export_logs(log_group: str, start: int, end: int, region: str, verbose: bool):
    """
    Exports logs from a CloudWatch log group to an S3 bucket.
    The destination bucket is named "cw-logs-export-$acctid-$region". If the bucket doesn't exist, it is created.
    The export is stored under the prefix "$log_group_modified/start-end", where '/' in log group names are replaced with '-'.
    The start and end times are expected as epoch seconds and are converted to milliseconds.
    """
    # Get AWS account ID
    sts_client = boto3.client("sts")
    acct_id = sts_client.get_caller_identity().get("Account")

    # Build destination bucket name
    s3_bucket = f"cw-logs-export-{acct_id}-{region}"

    # Ensure the S3 bucket exists
    s3 = boto3.client("s3", region_name=region)
    try:
        s3.head_bucket(Bucket=s3_bucket)
        logging.info(f"S3 bucket {s3_bucket} already exists.")
    except Exception as e:
        logging.info(f"S3 bucket {s3_bucket} does not exist. Creating...")
        try:
            if region == "us-east-1":
                s3.create_bucket(Bucket=s3_bucket)
            else:
                s3.create_bucket(
                    Bucket=s3_bucket,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            logging.info(f"S3 bucket {s3_bucket} created.")
        except Exception as ce:
            logging.error(f"Failed to create S3 bucket {s3_bucket}: {ce}")
            sys.exit(1)

    # Check if CloudWatch Logs has permission to access the S3 bucket
    try:
        s3.get_bucket_acl(Bucket=s3_bucket)
    except Exception as e:
        logging.error(
            f"CloudWatch Logs may not have permission to access bucket {s3_bucket}: {e}. Please update the bucket policy to allow CloudWatch Logs to perform GetBucketAcl."
        )
        sys.exit(1)

    # Attach bucket policy to allow CloudWatch Logs export
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudWatchLogsExport",
                "Effect": "Allow",
                "Principal": {"Service": "logs.amazonaws.com"},
                "Action": ["s3:GetBucketAcl", "s3:PutObject"],
                "Resource": [
                    f"arn:aws:s3:::{s3_bucket}",
                    f"arn:aws:s3:::{s3_bucket}/*",
                ],
            }
        ],
    }
    policy_json = json.dumps(bucket_policy)
    try:
        s3.put_bucket_policy(Bucket=s3_bucket, Policy=policy_json)
        logging.info(f"Bucket policy attached to {s3_bucket}.")
    except Exception as e:
        logging.error(f"Failed to attach bucket policy to {s3_bucket}: {e}")
        sys.exit(1)

    # Prepare export task parameters
    # Replace '/' with '-' in the log group name for S3 prefix
    log_group_modified = log_group.replace("/", "-")
    destination_prefix = f"{log_group_modified}/{start}-{end}"
    task_name = f"export-{log_group_modified}-{start}-{end}"

    # Convert start and end times to milliseconds
    start_ms = start * 1000
    end_ms = end * 1000

    logs_client = boto3.client("logs", region_name=region)
    try:
        params = {
            "taskName": task_name,
            "logGroupName": log_group,
            "from": start_ms,
            "to": end_ms,
            "destination": s3_bucket,
            "destinationPrefix": destination_prefix,
        }
        response = logs_client.create_export_task(**params)
        task_id = response.get("taskId", "N/A")
        logging.info(f"Export task created with taskId: {task_id}")
    except Exception as e:
        logging.error(f"Failed to create export task: {e}")
        sys.exit(1)


def list_exports(region: str, verbose: bool, pending: bool, wait: bool):
    """Lists export tasks for CloudWatch logs. By default, all export tasks are displayed.
    If --pending is provided, only pending (or running) tasks are shown.
    If --wait is provided, the function will wait for running tasks to complete, updating the status with exponential backoff.
    """
    import time

    import time

    logs_client = boto3.client("logs", region_name=region)
    # Initialize wait time for exponential backoff if waiting
    wait_time = 60 if wait else 0
    while True:
        paginator = logs_client.get_paginator("describe_export_tasks")
        tasks = []
        for page in paginator.paginate():
            tasks.extend(page.get("exportTasks", []))

        # Filter tasks based on --pending flag
        if pending:
            filtered_tasks = [
                task
                for task in tasks
                if task.get("status", {}).get("code", "").upper()
                in ["PENDING", "RUNNING"]
            ]
        else:
            filtered_tasks = tasks

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nStatus update as of {now_str}")
        if not filtered_tasks:
            print("No export tasks found with the specified criteria.")
        else:
            if verbose:
                header = f"{'Task ID':<15} {'Task Name':<25} {'Status':<12} {'Creation Time':<20} {'Destination':<20} {'Prefix':<20} {'Completion Time':<20}"
            else:
                header = f"{'Task ID':<15} {'Task Name':<25} {'Status':<12} {'Creation Time':<20}"
            print(header)
            print("-" * len(header))
            for task in filtered_tasks:
                task_id = task.get("taskId", "N/A")
                task_name = task.get("taskName", "N/A")
                status_code = task.get("status", {}).get("code", "N/A")
                exec_info = task.get("executionInfo", {})
                creation_time = exec_info.get("creationTime", 0)
                creation_dt = (
                    datetime.datetime.fromtimestamp(creation_time / 1000).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if creation_time
                    else "N/A"
                )
                if verbose:
                    destination = task.get("destination", "N/A")
                    prefix = task.get("destinationPrefix", "N/A")
                    comp_time = exec_info.get("completionTime", None)
                    if comp_time:
                        comp_time_str = datetime.datetime.fromtimestamp(
                            comp_time / 1000
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        comp_time_str = "N/A"
                    print(
                        f"{task_id:<15} {task_name:<25} {status_code:<12} {creation_dt:<20} {destination:<20} {prefix:<20} {comp_time_str:<20}"
                    )
                else:
                    print(
                        f"{task_id:<15} {task_name:<25} {status_code:<12} {creation_dt:<20}"
                    )

        if not wait:
            break

        # Check if any tasks are still running
        running_tasks = [
            task
            for task in filtered_tasks
            if task.get("status", {}).get("code", "").upper() == "RUNNING"
        ]
        if not running_tasks:
            break

        print(
            f"Some tasks are still running. Waiting {wait_time} seconds for update...\n"
        )
        time.sleep(wait_time)
        wait_time *= 2


def main():
    parser = argparse.ArgumentParser(
        description="Manage CloudWatch logs and log groups."
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Sub-command to run"
    )

    # Sub-command: list
    list_parser = subparsers.add_parser("list", help="List CloudWatch log groups.")
    list_parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    list_parser.add_argument(
        "--all-regions",
        action="store_true",
        help="List log groups from all available regions.",
    )
    list_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Sub-command: download
    download_parser = subparsers.add_parser(
        "download", help="Download logs for a log group."
    )
    download_parser.add_argument(
        "log_group", help="Name of the CloudWatch log group, or 'ALL' for all groups."
    )
    download_parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days to look back for logs (default: 365)",
    )
    download_parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    download_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Sub-command: set-retention
    retention_parser = subparsers.add_parser(
        "set-retention", help="Set retention policy for a log group."
    )
    retention_parser.add_argument("log_group", help="Name of the CloudWatch log group.")
    retention_parser.add_argument(
        "retention",
        type=int,
        nargs="?",
        default=30,
        help="Retention period in days (default: 30) if targeting log groups with 'Never' retention.",
    )
    retention_parser.add_argument(
        "--if-never",
        action="store_true",
        help="Only set retention if current retention is 'Never'.",
    )
    retention_parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    retention_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Sub-command: delete
    delete_parser = subparsers.add_parser("delete", help="Delete a log group.")
    delete_parser.add_argument("log_group", help="Name of the CloudWatch log group.")
    delete_parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    delete_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Sub-command: list-exports
    exports_parser = subparsers.add_parser(
        "list-exports",
        help="List export tasks for CloudWatch logs. By default, all export tasks are displayed. If --pending is provided, only pending (or running) tasks are shown. Use --wait to refresh status every 60 seconds if tasks are still running.",
    )
    exports_parser.add_argument(
        "--pending",
        action="store_true",
        help="Show only pending (or running) export tasks.",
    )
    exports_parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait and refresh status every 60 seconds if any tasks are still running.",
    )
    exports_parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    exports_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Sub-command: export
    export_parser = subparsers.add_parser("export", help="Export a log group to S3.")
    export_parser.add_argument("log_group", help="Name of the CloudWatch log group.")
    export_parser.add_argument(
        "--start",
        type=int,
        default=int(
            (datetime.datetime.now() - datetime.timedelta(days=5 * 365)).timestamp()
        ),
        help="Start time in epoch seconds. Defaults to 5 years ago.",
    )
    export_parser.add_argument(
        "--end",
        type=int,
        default=int(datetime.datetime.now().timestamp()),
        help="End time in epoch seconds. Defaults to now.",
    )
    export_parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    export_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)
    if getattr(args, "verbose", False):
        fh = logging.FileHandler("manage_cw_logs.log")
        fh.setLevel(log_level)
        formatter = logging.Formatter(log_format)
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    if args.command == "list":
        if args.all_regions:
            session = boto3.session.Session()
            regions = session.get_available_regions("logs")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_region = {
                    executor.submit(
                        capture_list_log_groups, region, args.verbose
                    ): region
                    for region in regions
                }
                for future in concurrent.futures.as_completed(future_to_region):
                    region = future_to_region[future]
                    try:
                        output = future.result()
                        print(f"Region: {region}")
                        print(output)
                        print()  # Blank line for separation
                    except Exception as exc:
                        logging.error(f"Region {region} generated an exception: {exc}")
        else:
            list_log_groups(args.region, args.verbose)
    elif args.command == "download":
        download_logs(args.log_group, args.days, args.verbose, args.region)
    elif args.command == "set-retention":
        set_retention(
            args.log_group,
            args.retention,
            args.region,
            args.verbose,
            if_never=args.if_never,
        )
    elif args.command == "delete":
        delete_log_group(args.log_group, args.region, args.verbose)
    elif args.command == "export":
        export_logs(args.log_group, args.start, args.end, args.region, args.verbose)
    elif args.command == "list-exports":
        list_exports(args.region, args.verbose, args.pending, args.wait)
    else:
        parser.error("Invalid command")


if __name__ == "__main__":
    main()
