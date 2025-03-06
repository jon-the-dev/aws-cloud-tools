import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import json

# Define your AWS Region and CloudWatch log group name
AWS_REGION = "us-east-1"  # Replace with your AWS region
CLOUDWATCH_LOG_GROUP = (
    "/aws/route53/main"  # Replace with your CloudWatch log group name
)

# Define a whitelist of IPs that are allowed to access the DNS service
IP_WHITELIST = ["192.0.2.1", "192.0.2.2"]  # 1  # 2  # Replace with your whitelisted IPs


# Define a function to check if an IP is in the whitelist
def ip_in_whitelist(ip):
    return ip in IP_WHITELIST


# Function to fetch and parse CloudWatch logs for DNS queries
def get_dns_queries():
    # Initialize Boto3 clients
    logs = boto3.client("logs", region_name=AWS_REGION)

    # Define the time range for the log query
    end_time = datetime.now()
    start_time = end_time - timedelta(
        days=365
    )  # Adjust to desired periodicity (e.g., 24h, etc.)

    # Set up the log filter pattern if needed (see AWS documentation for patterns)
    log_filter_pattern = {
        "logGroupName": CLOUDWATCH_LOG_GROUP,
        "startTime": int(start_time.timestamp() * 1000),
        "endTime": int(end_time.timestamp() * 1000),
        "filterPattern": "",  # Define the filter pattern as needed
    }

    try:
        # Fetch logs
        response = logs.get_log_events(**log_filter_pattern)

        # Extract DNS queries from the logs
        dns_queries = []
        for event in response["events"]:
            query = json.loads(event["message"])
            if "DNSQuery" in query and not ip_in_whitelist(query["sourceIPAddress"]):
                dns_queries.append(
                    (query["DNSQuery"]["name"], query["sourceIPAddress"])
                )

        return dns_queries

    except ClientError as e:
        print(f"An error occurred while fetching logs: {e}")
        return []


# Function to check for a high volume of failed DNS lookups from an unknown IP
def check_dns_failures():
    dns_queries = get_dns_queries()
    with open("queries.txt", "w") as file:
        file.write(f"{dns_queries}")

    # Define the threshold for number of requests per domain
    domain_threshold = 50  # Adjust as needed

    failed_domains = {}
    for query in dns_queries:
        if "FAILED" in query[0]:
            domain, ip = query
            if domain not in failed_domains:
                failed_domains[domain] = []
            failed_domains[domain].append(ip)

    # Check for domains with more than the threshold of requests from unknown IPs
    for domain, ips in failed_domains.items():
        if len(ips) > domain_threshold:
            print(
                f"High volume of DNS lookups detected against {domain} from {len(ips)} unique IPs."
            )


try:
    check_dns_failures()
except Exception as e:
    print(f"An error occurred during DNS lookup check: {e}")
