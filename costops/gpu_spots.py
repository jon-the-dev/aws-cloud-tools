#!/usr/bin/env python3
import boto3
import argparse
import json
from datetime import datetime, timezone
import concurrent.futures
import botocore.exceptions


def get_gpu_instance_types(client, min_gpu_ram, min_cores, min_ram):
    """
    Retrieve instance types in the region that have NVIDIA GPUs
    and meet the minimum resource criteria.
    """
    gpu_instance_types = {}
    paginator = client.get_paginator("describe_instance_types")
    for page in paginator.paginate():
        for itype in page["InstanceTypes"]:
            if "GpuInfo" not in itype:
                continue

            instance_type = itype["InstanceType"]
            gpu_info = itype["GpuInfo"]
            if not gpu_info.get("Gpus"):
                continue

            has_nvidia = False
            total_gpu_memory = 0
            for gpu in gpu_info["Gpus"]:
                if gpu.get("Manufacturer", "").lower() == "nvidia":
                    has_nvidia = True
                    if "MemoryInfo" in gpu:
                        total_gpu_memory += gpu["MemoryInfo"].get("SizeInMiB", 0)
            if not has_nvidia:
                continue

            if min_gpu_ram is not None and total_gpu_memory < min_gpu_ram * 1024:
                continue

            vcpus = itype["VCpuInfo"]["DefaultVCpus"]
            if min_cores is not None and vcpus < min_cores:
                continue

            memory = itype["MemoryInfo"]["SizeInMiB"]
            if min_ram is not None and memory < min_ram * 1024:
                continue

            gpu_instance_types[instance_type] = {
                "gpu_memory": total_gpu_memory,
                "vcpus": vcpus,
                "memory": memory,
            }
    return gpu_instance_types


def get_cheapest_spot_price(client, instance_types):
    """
    Query the spot price history for the given instance types (Linux/UNIX)
    using a narrow time window and return the record with the lowest price.
    """
    now = datetime.now(timezone.utc)
    try:
        response = client.describe_spot_price_history(
            InstanceTypes=instance_types,
            StartTime=now,
            EndTime=now,
            ProductDescriptions=["Linux/UNIX (Amazon VPC)"],
            MaxResults=1000,
        )
    except botocore.exceptions.ConnectTimeoutError as e:
        print("Connection timeout when retrieving spot price history:", e)
        return None
    except Exception as e:
        print("Error retrieving spot price history:", e)
        return None

    best_record = None
    for record in response.get("SpotPriceHistory", []):
        try:
            price = float(record["SpotPrice"])
        except ValueError:
            continue
        if best_record is None or price < float(best_record["SpotPrice"]):
            best_record = record
    return best_record


def process_region(region, args):
    """
    Process a single region: retrieve qualifying GPU instance types and
    determine the cheapest spot price available.
    """
    print(f"Checking region: {region}")
    try:
        client = boto3.client("ec2", region_name=region)
    except botocore.exceptions.BotoCoreError as e:
        print(f"Error connecting to region {region}: {e}")
        return None

    try:
        gpu_instance_dict = get_gpu_instance_types(
            client, args.min_gpu_ram, args.min_cores, args.min_ram
        )
    except botocore.exceptions.ConnectTimeoutError as e:
        print(
            f"Connection timeout when retrieving instance types for region {region}: {e}"
        )
        return None
    except Exception as e:
        print(f"Error retrieving instance types in region {region}: {e}")
        return None

    if not gpu_instance_dict:
        print(f"  No GPU instance types meeting criteria in {region}.")
        return None

    instance_types = list(gpu_instance_dict.keys())
    try:
        spot_record = get_cheapest_spot_price(client, instance_types)
    except botocore.exceptions.ConnectTimeoutError as e:
        print(
            f"Connection timeout when retrieving spot prices for region {region}: {e}"
        )
        return None
    except Exception as e:
        print(f"Error retrieving spot price data in region {region}: {e}")
        return None

    if not spot_record:
        print(f"  No spot price data found in {region}.")
        return None

    price = float(spot_record["SpotPrice"])
    instance_type = spot_record["InstanceType"]
    details = gpu_instance_dict.get(instance_type, {})
    vcpus = details.get("vcpus", "N/A")
    memory_mib = details.get("memory", 0)
    gpu_memory_mib = details.get("gpu_memory", 0)
    memory_gb = round(memory_mib / 1024, 2) if memory_mib else "N/A"
    gpu_memory_gb = round(gpu_memory_mib / 1024, 2) if gpu_memory_mib else "N/A"

    print(
        f"  Best in {region}: {instance_type} at ${spot_record['SpotPrice']} in {spot_record['AvailabilityZone']}"
    )
    return {
        "region": region,
        "instance_type": instance_type,
        "availability_zone": spot_record["AvailabilityZone"],
        "price": price,
        "timestamp": spot_record["Timestamp"],
        "vcpus": vcpus,
        "memory_gb": memory_gb,
        "gpu_memory_gb": gpu_memory_gb,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Find the cheapest AWS GPU spot instance for your workload."
    )
    parser.add_argument(
        "--us-only", action="store_true", help="Limit search to US regions"
    )
    parser.add_argument(
        "--eu-only", action="store_true", help="Limit search to EU regions"
    )
    parser.add_argument("--min-gpu-ram", type=float, help="Minimum total GPU RAM in GB")
    parser.add_argument("--min-cores", type=int, help="Minimum number of CPU cores")
    parser.add_argument("--min-ram", type=float, help="Minimum system RAM in GB")
    parser.add_argument(
        "--save-data",
        action="store_true",
        help="Save the results to JSON files locally",
    )
    args = parser.parse_args()

    ec2_global = boto3.client("ec2")
    regions_data = ec2_global.describe_regions()["Regions"]
    regions = [r["RegionName"] for r in regions_data]
    if args.us_only:
        regions = [r for r in regions if r.startswith("us-")]
    elif args.eu_only:
        regions = [r for r in regions if r.startswith("eu-")]

    overall_best = None
    overall_details = None
    region_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_region = {
            executor.submit(process_region, region, args): region for region in regions
        }
        for future in concurrent.futures.as_completed(future_to_region):
            result = future.result()
            if result:
                region_results.append(result)
                if overall_best is None or result["price"] < overall_best:
                    overall_best = result["price"]
                    overall_details = result

    if overall_details:
        print("\nCheapest GPU spot instance found:")
        print("  Region:              ", overall_details["region"])
        print("  Availability Zone:   ", overall_details["availability_zone"])
        print("  Instance Type:       ", overall_details["instance_type"])
        print("  Spot Price:          $", overall_details["price"], " per hour")
        print("  Price Timestamp:     ", overall_details["timestamp"])
        print("  vCPUs:               ", overall_details["vcpus"])
        print("  System Memory (GB):  ", overall_details["memory_gb"])
        print("  GPU Memory (GB):     ", overall_details["gpu_memory_gb"])
    else:
        print("No suitable GPU instance found in the selected regions.")

    if args.save_data:
        try:
            with open("gpu_spot_region_results.json", "w") as f:
                json.dump(region_results, f, default=str, indent=2)
            if overall_details:
                with open("gpu_spot_best_result.json", "w") as f:
                    json.dump(overall_details, f, default=str, indent=2)
            print(
                "Data saved to 'gpu_spot_region_results.json' and 'gpu_spot_best_result.json'"
            )
        except Exception as e:
            print("Error saving data to JSON:", e)


if __name__ == "__main__":
    main()
