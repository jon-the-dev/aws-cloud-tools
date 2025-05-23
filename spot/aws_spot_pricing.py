#!/usr/bin/env python3

import argparse
import boto3
import csv
import datetime
import os
import time
from multiprocessing import Pool, cpu_count
from botocore.config import Config


def get_all_regions():
    """Return a list of all available AWS region names."""
    ec2_client = boto3.client("ec2", region_name="us-east-1")
    regions_data = ec2_client.describe_regions(AllRegions=True)
    regions = [r["RegionName"] for r in regions_data["Regions"]]
    return regions


def gather_spot_prices(region):
    """
    Gathers spot price history for all instance types in the specified region
    and saves the results to a CSV file named 'spot_prices_{region}.csv'.
    """
    # Configure the client with retries to avoid throttling
    ec2_client = boto3.client(
        "ec2", region_name=region, config=Config(retries={"max_attempts": 10})
    )

    # Determine the earliest time window for spot pricing data (e.g., last 24 hours)
    # Adjust as needed or retrieve a shorter window to reduce data size.
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(hours=24)

    # We'll paginate through describe_spot_price_history to get all results
    # Example filter: product_description="Linux/UNIX"
    paginator = ec2_client.get_paginator("describe_spot_price_history")
    page_iterator = paginator.paginate(
        StartTime=start_time,
        EndTime=end_time,
        ProductDescriptions=["Linux/UNIX"],
        Filters=[],
    )
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    output_filename = f"{DATA_DIR}/spot_prices_{region}.csv"
    with open(output_filename, mode="w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["Region", "InstanceType", "AZ", "SpotPrice", "Timestamp"])
        for page in page_iterator:
            for item in page["SpotPriceHistory"]:
                csv_writer.writerow(
                    [
                        region,
                        item["InstanceType"],
                        item["AvailabilityZone"],
                        item["SpotPrice"],
                        item["Timestamp"],
                    ]
                )


def download_all_spot_data():
    """Discovers all regions and uses multiprocessing to gather spot prices."""
    regions = get_all_regions()

    # Use a pool of workers to speed up the retrieval
    pool_size = min(len(regions), cpu_count())
    with Pool(pool_size) as p:
        p.map(gather_spot_prices, regions)


def analyze_data():
    """
    Reads all 'spot_prices_*.csv' files, finds the cheapest instance types
    (lowest average spot price across time in the file), and prints out
    pricing details plus an estimate for 30 days.
    """
    from glob import glob
    import statistics

    csv_files = glob("spot_prices_*.csv")
    if not csv_files:
        print("No spot pricing CSV files found. Please run data download first.")
        return

    # Structure: dict of { (region, instance_type, az): [list of spot prices across time] }
    price_map = {}

    for csv_file in csv_files:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                region = row["Region"]
                instance_type = row["InstanceType"]
                az = row["AZ"]
                spot_price = float(row["SpotPrice"])
                key = (region, instance_type, az)
                if key not in price_map:
                    price_map[key] = []
                price_map[key].append(spot_price)

    # Compute average spot price for each key
    avg_prices = {}
    for key, prices in price_map.items():
        avg_price = statistics.mean(prices)
        avg_prices[key] = avg_price

    # Sort by average spot price ascending
    sorted_avg_prices = sorted(avg_prices.items(), key=lambda x: x[1])

    # Print out the top 10 cheapest (region, instance_type, az) combos
    print(
        "Cheapest instance type combinations (avg spot price) with 30d cost estimate:"
    )
    for i, ((region, instance_type, az), price) in enumerate(
        sorted_avg_prices[:10], start=1
    ):
        # Spot prices are in USD/hr; to get 30d cost estimate:
        # 30 days ~ 720 hours (30 * 24).
        monthly_est = price * 720
        print(
            f"{i}. Region: {region}, InstanceType: {instance_type}, AZ: {az}, "
            f"AvgPrice: {price:.6f}, 30dEstimate: {monthly_est:.2f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Download and analyze AWS EC2 spot pricing data."
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Run the download step every hour in a loop.",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze existing CSV files and print cheapest instances.",
    )
    args = parser.parse_args()

    if args.poll:
        while True:
            print("[*] Polling spot pricing data...")
            download_all_spot_data()
            print("[*] Waiting 1 hour to poll again...")
            time.sleep(3600)  # 1 hour
    else:
        # By default, run once.
        download_all_spot_data()

    if args.analyze:
        analyze_data()


if __name__ == "__main__":
    main()
