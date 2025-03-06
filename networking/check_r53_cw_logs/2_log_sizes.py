#!/usr/bin/env python3
import boto3
import argparse
import logging


def convert_to_mb(byte_value: int) -> float:
    """Convert bytes to megabytes."""
    return byte_value / (1024 * 1024)


def list_log_groups(region: str, verbose: bool):
    """List all CloudWatch log groups with their log streams and stored bytes in MB.

    By default, only groups with a total stored size > 0.00 MB are shown.
    With --verbose, all groups are listed.
    """
    client = boto3.client("logs", region_name=region)
    log_groups = []
    paginator = client.get_paginator("describe_log_groups")
    for page in paginator.paginate():
        groups = page.get("logGroups", [])
        log_groups.extend(groups)
        if verbose:
            logging.debug(f"Retrieved {len(groups)} log groups in current page.")

    if not log_groups:
        logging.info("No log groups found.")
        return

    for group in log_groups:
        group_name = group.get("logGroupName")
        total_group_bytes = 0

        # Retrieve all log streams for the log group.
        streams = []
        stream_paginator = client.get_paginator("describe_log_streams")
        for stream_page in stream_paginator.paginate(logGroupName=group_name):
            stream_list = stream_page.get("logStreams", [])
            streams.extend(stream_list)
            if verbose:
                logging.debug(
                    f"Retrieved {len(stream_list)} streams for log group '{group_name}'."
                )

        if not streams:
            if verbose:
                logging.debug(f"No log streams found for log group '{group_name}'.")
            continue

        # Process each stream.
        for stream in streams:
            stored_bytes = stream.get("storedBytes", 0)
            total_group_bytes += stored_bytes
            size_mb = convert_to_mb(stored_bytes)
            logging.info(
                f"Log Group: {group_name} | Stream: {stream.get('logStreamName')} - Size: {size_mb:.2f} MB"
            )

        total_group_mb = convert_to_mb(total_group_bytes)
        # If not verbose, only output groups with >0.00 MB total.
        if not verbose and total_group_mb <= 0.0:
            continue

        logging.info(f"Log Group: {group_name} | Total Size: {total_group_mb:.2f} MB\n")


def main():
    parser = argparse.ArgumentParser(
        description="List all CloudWatch log groups with their streams and stored bytes in MB. By default, only groups with stored bytes > 0 are shown unless --verbose is specified."
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging to show all groups regardless of stored size",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)
    # Also log to a file.
    fh = logging.FileHandler("list_log_groups.log")
    fh.setLevel(log_level)
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh)

    list_log_groups(args.region, args.verbose)


if __name__ == "__main__":
    main()
