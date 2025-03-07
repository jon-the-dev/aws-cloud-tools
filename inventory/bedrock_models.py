import boto3
import csv
import concurrent.futures
from botocore.config import Config


def list_models_in_region(region, boto_config):
    models_list = []
    try:
        client = boto3.client("bedrock", region_name=region, config=boto_config)
        next_token = None
        while True:
            params = {}
            if next_token:
                params["NextToken"] = next_token
            response = client.list_foundation_models(**params)
            for model in response.get("modelSummaries", []):
                models_list.append(
                    {
                        "Region": region,
                        "ModelId": model.get("modelId", ""),
                        "ModelName": model.get("modelName", ""),
                    }
                )
            next_token = response.get("NextToken")
            if not next_token:
                break
    except Exception as e:
        # Skip regions that raise exceptions (e.g., unsupported or timeout issues)
        print(f"Error listing models in region {region}: {e}")
    return models_list


def main():
    session = boto3.session.Session()
    regions = session.get_available_regions("bedrock")

    # Configure boto3 client with a 5-second timeout for both connect and read.
    boto_config = Config(
        connect_timeout=5, read_timeout=30, retries={"max_attempts": 1}
    )

    all_models = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(regions)) as executor:
        future_to_region = {
            executor.submit(list_models_in_region, region, boto_config): region
            for region in regions
        }
        for future in concurrent.futures.as_completed(future_to_region):
            region = future_to_region[future]
            try:
                region_models = future.result()
                all_models.extend(region_models)
            except Exception as e:
                print(f"Thread for region {region} generated an exception: {e}")

    csv_file = "bedrock_models.csv"
    with open(csv_file, "w", newline="") as csvfile:
        fieldnames = ["Region", "ModelId", "ModelName"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_models:
            writer.writerow(row)

    print(f"CSV file '{csv_file}' created with {len(all_models)} models.")


if __name__ == "__main__":
    main()
