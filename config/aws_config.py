code  #!/usr/bin/env python3

import argparse
import os
import re
import json
import csv
from datetime import datetime
import boto3


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Download and flatten AWS Config JSON files into a single CSV."
    )
    parser.add_argument("--bucket", required=True, help="S3 bucket name.")
    parser.add_argument("--prefix", required=True, help="S3 prefix for config files.")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD).")
    parser.add_argument(
        "--output-file", required=True, help="Name of the output CSV file."
    )
    return parser.parse_args()


def flatten_json(nested_json, parent_key="", sep="."):
    """
    Recursively flattens a nested JSON object into a single dict.
    Example:
        {
          "a": {
            "b": 1,
            "c": 2
          },
          "d": 3
        }
    Becomes:
        {
          "a.b": 1,
          "a.c": 2,
          "d": 3
        }
    """
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Flatten each item in the list with a numeric index in the key
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_json(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    return dict(items)


def main():
    args = parse_arguments()
    bucket_name = args.bucket
    prefix = args.prefix
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    output_file = args.output_file

    s3_client = boto3.client("s3")

    # Regex to match date in format YYYY-MM-DD.
    # Adjust this pattern to match your actual S3 config naming scheme.
    # Example key: path/to/config/files/2025-01-15T12-00-00Z_config.json
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")

    # List to store all flattened records
    all_records = []

    # Paginate through all objects under the prefix
    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    for page in page_iterator:
        if "Contents" not in page:
            continue
        for obj in page["Contents"]:
            key = obj["Key"]

            # Extract date from the key using the regex
            match = date_pattern.search(key)
            if match:
                file_date_str = match.group(1)
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                # Check if the file date is within the specified range
                if start_date <= file_date <= end_date:
                    # Download the file
                    local_filename = os.path.basename(key)
                    s3_client.download_file(bucket_name, key, local_filename)

                    # Open and flatten the JSON
                    with open(local_filename, "r") as f:
                        try:
                            data = json.load(f)
                            # If the top-level JSON is a list, flatten each element
                            if isinstance(data, list):
                                for item in data:
                                    flattened = flatten_json(item)
                                    all_records.append(flattened)
                            else:
                                flattened = flatten_json(data)
                                all_records.append(flattened)
                        except json.JSONDecodeError:
                            pass  # Could log or handle decode errors as needed

                    # Remove local file if you don't need to keep it
                    os.remove(local_filename)

    # Get a superset of all fields for CSV header
    header_fields = set()
    for record in all_records:
        header_fields.update(record.keys())
    header_fields = sorted(header_fields)

    # Write out CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header_fields)
        writer.writeheader()
        for record in all_records:
            writer.writerow(record)

    print(f"Aggregated {len(all_records)} records into {output_file}")


if __name__ == "__main__":
    main()
