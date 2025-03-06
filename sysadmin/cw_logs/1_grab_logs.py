#!/usr/bin/env python3
import boto3
import argparse
import os
import datetime
import re
import logging


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    """
    return re.sub(r'[\\/:"*?<>|]+', "_", name)


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

    paginator = client.get_paginator("describe_log_streams")
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
        with open(filename, "w", encoding="utf-8") as f:
            kwargs = {
                "logGroupName": log_group,
                "logStreamName": log_stream_name,
                "startTime": start_time,
                "endTime": now,
                "startFromHead": True,
            }
            repeated_token_count = 0
            max_repeated_token_count = 3
            while True:
                response = client.get_log_events(**kwargs)
                events = response.get("events", [])
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


def main():
    parser = argparse.ArgumentParser(
        description="Download CloudWatch logs for a given log group. Specify 'ALL' as the log_group to process every group in the region."
    )
    parser.add_argument(
        "log_group", help="Name of the CloudWatch log group, or 'ALL' for all groups."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days to look back for logs (default: 365)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region to use (default: us-east-1)"
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)
    # Also log to a file.
    fh = logging.FileHandler("download_cloudwatch_logs.log")
    fh.setLevel(log_level)
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh)

    download_logs(args.log_group, args.days, args.verbose, args.region)


if __name__ == "__main__":
    main()
