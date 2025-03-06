#!/usr/bin/env python3
import boto3
import argparse
from datetime import datetime, timezone
import concurrent.futures
import json

MAX_WORKERS = 6


def get_gpu_instance_types(client, min_gpu_ram, min_cores, min_ram):
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
    # Use timezone-aware datetime to avoid deprecation warnings
    now = datetime.now(timezone.utc)
    try:
        response = client.describe_spot_price_history(
            InstanceTypes=instance_types,
            StartTime=now,
            EndTime=now,
            ProductDescriptions=["Linux/UNIX (Amazon VPC)"],
            MaxResults=1000,
        )
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
    print(f"Checking region: {region}")
    client = boto3.client("ec2", region_name=region)
    gpu_instance_dict = get_gpu_instance_types(
        client, args.min_gpu_ram, args.min_cores, args.min_ram
    )
    # with open(f"{region}-gpu.json", "w") as f:
    #     json.dump(gpu_instance_dict, f)
    if not gpu_instance_dict:
        print(f"[!]  No GPU instance types meeting criteria in {region}.")
        return None

    instance_types = list(gpu_instance_dict.keys())
    spot_record = get_cheapest_spot_price(client, instance_types)
    # with open(f"{region}-spot.json", "w") as f:
    #     json.dump(spot_record, f, default=str)
    if not spot_record:
        print(f"[-]  No spot price data found in {region}.")
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
        f"[+]  Best in {region}: {instance_type} at ${spot_record['SpotPrice']} in {spot_record['AvailabilityZone']}"
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
        "--auto-mode", action="store_true", help="Act like lambda and output json"
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

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_region = {
            executor.submit(process_region, region, args): region for region in regions
        }
        for future in concurrent.futures.as_completed(future_to_region):
            result = future.result()
            if result:
                if overall_best is None or result["price"] < overall_best:
                    overall_best = result["price"]
                    overall_details = result

    if overall_details and not args.auto_mode:
        print("\nCheapest GPU spot instance found:")
        print("  Region:              ", overall_details["region"])
        print("  Availability Zone:   ", overall_details["availability_zone"])
        print("  Instance Type:       ", overall_details["instance_type"])
        print("  Spot Price:          $", overall_details["price"], " per hour")
        print("  Daily Price:         $", overall_details["price"] * 24, " per day")
        print(
            "  Monthly Price:        $",
            overall_details["price"] * 24 * 31,
            " per month",
        )
        print("  Price Timestamp:     ", overall_details["timestamp"])
        print("  vCPUs:               ", overall_details["vcpus"])
        print("  System Memory (GB):  ", overall_details["memory_gb"])
        print("  GPU Memory (GB):     ", overall_details["gpu_memory_gb"])
    elif args.auto_mode and overall_details:
        print(json.dumps(overall_details, default=str, indent=4))
    else:
        print("No suitable GPU instance found in the selected regions.")


if __name__ == "__main__":
    main()
