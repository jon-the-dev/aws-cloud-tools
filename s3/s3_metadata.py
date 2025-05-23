#!/usr/bin/env python3
"""
This script lists all S3 buckets, their metadata like HTTP website, tags, etc.,
and available CloudWatch metrics, saving the results to a CSV file.
"""

import argparse
import csv
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Common S3 metrics to extract as separate columns
COMMON_METRICS = [
    'BucketSizeBytes',
    'NumberOfObjects',
    'AllRequests',
    'GetRequests',
    'PutRequests',
    'DeleteRequests',
    'HeadRequests',
    '4xxErrors',
    '5xxErrors',
    'FirstByteLatency',
    'TotalRequestLatency'
]


def get_bucket_website(s3_client, bucket_name: str) -> Dict[str, Any]:
    """Get bucket website configuration if enabled."""
    try:
        return s3_client.get_bucket_website(Bucket=bucket_name)
    except s3_client.exceptions.ClientError:
        return {}


def get_bucket_tags(s3_client, bucket_name: str) -> Dict[str, str]:
    """Get bucket tags if any."""
    try:
        response = s3_client.get_bucket_tagging(Bucket=bucket_name)
        return {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
    except s3_client.exceptions.ClientError:
        return {}


def get_bucket_metrics(cloudwatch_client, bucket_name: str) -> Dict[str, Any]:
    """Get available CloudWatch metrics for the bucket."""
    metrics_data = {metric: {} for metric in COMMON_METRICS}
    
    # Define the time range for metrics (last 24 hours)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    
    # List metrics for this bucket
    response = cloudwatch_client.list_metrics(
        Namespace='AWS/S3',
        Dimensions=[{'Name': 'BucketName', 'Value': bucket_name}]
    )
    
    for metric in response['Metrics']:
        metric_name = metric['MetricName']
        
        # Skip metrics not in our common list
        if metric_name not in COMMON_METRICS:
            continue
        
        # Get statistics for each metric
        try:
            stats = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName=metric_name,
                Dimensions=metric['Dimensions'],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 24 hours in seconds
                Statistics=['Average', 'Sum', 'Maximum']
            )
            
            if stats['Datapoints']:
                # Get the most recent datapoint
                latest = sorted(stats['Datapoints'], key=lambda x: x['Timestamp'], reverse=True)[0]
                metrics_data[metric_name] = {
                    'Average': latest.get('Average', 0),
                    'Sum': latest.get('Sum', 0),
                    'Maximum': latest.get('Maximum', 0),
                    'Timestamp': latest.get('Timestamp')
                }
        except Exception as e:
            metrics_data[metric_name] = {'Error': str(e)}
    
    return metrics_data


def get_bucket_info(bucket_name: str) -> Dict[str, Any]:
    """Get all information for a single bucket."""
    s3_client = boto3.client('s3')
    cloudwatch_client = boto3.client('cloudwatch')
    
    print(f"Processing bucket: {bucket_name}")
    
    # Get basic bucket information
    bucket_info = {
        'Name': bucket_name,
        'CreationDate': None,
        'Region': None
    }
    
    try:
        # Get bucket location
        location = s3_client.get_bucket_location(Bucket=bucket_name)
        bucket_info['Region'] = location.get('LocationConstraint') or 'us-east-1'
        
        # Get bucket creation date if available
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            if 'Contents' in response and response['Contents']:
                bucket_info['CreationDate'] = response['Contents'][0].get('LastModified')
        except Exception:
            pass
        
        # Get website configuration
        website = get_bucket_website(s3_client, bucket_name)
        bucket_info['WebsiteEnabled'] = bool(website)
        if website:
            bucket_info['WebsiteIndexDocument'] = website.get('IndexDocument', {}).get('Suffix', '')
            bucket_info['WebsiteErrorDocument'] = website.get('ErrorDocument', {}).get('Key', '')
        
        # Get tags
        tags = get_bucket_tags(s3_client, bucket_name)
        for key, value in tags.items():
            bucket_info[f'Tag_{key}'] = value
        
        # Get metrics
        metrics = get_bucket_metrics(cloudwatch_client, bucket_name)
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict) and 'Average' in metric_data:
                bucket_info[f'Metric_{metric_name}_Avg'] = metric_data['Average']
                bucket_info[f'Metric_{metric_name}_Sum'] = metric_data['Sum']
                bucket_info[f'Metric_{metric_name}_Max'] = metric_data['Maximum']
        
    except Exception as e:
        bucket_info['Error'] = str(e)
    
    return bucket_info


def get_aws_account_id() -> str:
    """Get the current AWS account ID."""
    try:
        sts_client = boto3.client('sts')
        return sts_client.get_caller_identity()['Account']
    except Exception:
        return 'unknown-account'


def get_all_buckets_info() -> List[Dict[str, Any]]:
    """Get information for all S3 buckets."""
    s3_client = boto3.client('s3')
    response = s3_client.list_buckets()
    
    buckets = []
    for bucket in response['Buckets']:
        buckets.append({
            'Name': bucket['Name'],
            'CreationDate': bucket['CreationDate']
        })
    
    # Use threading to get bucket details in parallel
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_bucket_info, bucket['Name']): bucket['Name'] for bucket in buckets}
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                results.append({
                    'Name': futures[future],
                    'Error': str(e)
                })
    
    return results


def generate_default_filename() -> str:
    """Generate a default filename with account ID and timestamp."""
    account_id = get_aws_account_id()
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    return f"s3_buckets_info_{account_id}_{timestamp}.csv"


def save_to_csv(buckets_info: List[Dict[str, Any]], output_file: str) -> None:
    """Save bucket information to a CSV file."""
    if not buckets_info:
        print("No bucket information to save.")
        return
    
    # Get all possible field names
    fieldnames = set()
    for bucket in buckets_info:
        fieldnames.update(bucket.keys())
    
    # Sort fieldnames for consistent output
    fieldnames = sorted(fieldnames)
    
    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(buckets_info)
    
    print(f"Bucket information saved to {output_file}")


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description='List S3 buckets, their metadata, and CloudWatch metrics.'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output CSV file path (default: s3_buckets_info_ACCOUNT_ID_TIMESTAMP.csv)'
    )
    args = parser.parse_args()
    
    # Generate default filename if not specified
    output_file = args.output or generate_default_filename()
    
    print("Fetching S3 bucket information...")
    buckets_info = get_all_buckets_info()
    print(f"Found {len(buckets_info)} buckets.")
    
    save_to_csv(buckets_info, output_file)


if __name__ == "__main__":
    main()