import boto3
import datetime
import json
import logging
import argparse
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_cloudwatch_metric_sum(
    cloudwatch, namespace, metric_name, dimensions, start_time, end_time, period
):
    """
    Query CloudWatch for the given metric and sum the datapoints over the specified time window.
    """
    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        Statistics=["Sum"],
    )
    total = sum(dp["Sum"] for dp in response.get("Datapoints", []))
    return total


def get_waf_metrics(time_range_hours, region):
    """
    Retrieves AWS WAF metrics by:
      - Listing all REGIONAL Web ACLs.
      - For each Web ACL, querying CloudWatch for AllowedRequests and BlockedRequests.
      - Getting detailed rule configuration for each Web ACL and then retrieving rule-level BlockedRequests.
    """
    logging.info("Collecting WAF metrics")
    waf_client = boto3.client("wafv2", region_name=region)
    cw_client = boto3.client("cloudwatch", region_name=region)
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(hours=time_range_hours)
    period = 300  # 5 minutes (in seconds)

    waf_metrics = {}

    try:
        # List REGIONAL web ACLs with manual pagination
        response = waf_client.list_web_acls(Scope="REGIONAL")
        web_acls = response.get("WebACLs", [])
        while "NextMarker" in response:
            response = waf_client.list_web_acls(
                Scope="REGIONAL", NextMarker=response["NextMarker"]
            )
            web_acls.extend(response.get("WebACLs", []))
    except Exception as e:
        logging.error(f"Error retrieving WAF ACLs: {e}")
        return {"WAF_Error": f"Error retrieving WAF ACLs: {e}"}

    if not web_acls:
        logging.info("No WAF ACLs found in region")
        return {"WAF_Message": "No WAF ACLs found in region"}

    for acl in web_acls:
        acl_name = acl.get("Name")
        acl_id = acl.get("Id")
        logging.info(f"Processing WebACL: {acl_name}")
        # Query overall metrics for the web ACL (using the ACL name as the dimension value)
        dimensions = [{"Name": "WebACL", "Value": acl_name}]
        allowed = get_cloudwatch_metric_sum(
            cw_client,
            "AWS/WAFV2",
            "AllowedRequests",
            dimensions,
            start_time,
            end_time,
            period,
        )
        blocked = get_cloudwatch_metric_sum(
            cw_client,
            "AWS/WAFV2",
            "BlockedRequests",
            dimensions,
            start_time,
            end_time,
            period,
        )

        # Get detailed ACL info to retrieve rule names
        details = waf_client.get_web_acl(Id=acl_id, Name=acl_name, Scope="REGIONAL")
        rules = details.get("WebACL", {}).get("Rules", [])
        rule_metrics = {}
        for rule in rules:
            rule_name = rule.get("Name")
            logging.info(f"Processing rule: {rule_name} in WebACL: {acl_name}")
            # Query rule-level metrics (use both WebACL and Rule dimensions)
            rule_dimensions = [
                {"Name": "WebACL", "Value": acl_name},
                {"Name": "Rule", "Value": rule_name},
            ]
            rule_blocked = get_cloudwatch_metric_sum(
                cw_client,
                "AWS/WAFV2",
                "BlockedRequests",
                rule_dimensions,
                start_time,
                end_time,
                period,
            )
            rule_metrics[rule_name] = rule_blocked

        waf_metrics[acl_name] = {
            "AllowedRequests": allowed,
            "BlockedRequests": blocked,
            "Rules": rule_metrics,
        }
    return waf_metrics


def get_guardduty_metrics(time_range_hours, region):
    """
    Retrieves GuardDuty metrics by:
      - Listing detector IDs.
      - Paginating through findings.
      - Filtering findings by their UpdatedAt timestamp and aggregating counts by finding Type.
    """
    logging.info("Collecting GuardDuty metrics")
    gd_client = boto3.client("guardduty", region_name=region)
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(hours=time_range_hours)

    try:
        detectors_response = gd_client.list_detectors()
        detector_ids = detectors_response.get("DetectorIds", [])
    except Exception as e:
        logging.error(f"Error retrieving GuardDuty detectors: {e}")
        return {"GuardDuty_Error": f"Error retrieving GuardDuty detectors: {e}"}

    if not detector_ids:
        logging.info("No GuardDuty detectors found in region")
        return {"GuardDuty_Message": "No GuardDuty detectors found in region"}

    gd_metrics = defaultdict(int)

    for detector_id in detector_ids:
        paginator = gd_client.get_paginator("list_findings")
        finding_ids = []
        for page in paginator.paginate(DetectorId=detector_id):
            finding_ids.extend(page.get("FindingIds", []))
        # GuardDuty allows up to 50 IDs per GetFindings call
        for i in range(0, len(finding_ids), 50):
            batch_ids = finding_ids[i : i + 50]
            findings_response = gd_client.get_findings(
                DetectorId=detector_id, FindingIds=batch_ids
            )
            for finding in findings_response.get("Findings", []):
                # Use the UpdatedAt timestamp to filter within the desired time range
                updated_at_str = finding.get("UpdatedAt")
                try:
                    updated_at = datetime.datetime.strptime(
                        updated_at_str, "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                except ValueError:
                    updated_at = datetime.datetime.strptime(
                        updated_at_str, "%Y-%m-%dT%H:%SZ"
                    )
                updated_at = updated_at.replace(tzinfo=datetime.timezone.utc)
                if not (start_time <= updated_at <= end_time):
                    continue
                finding_type = finding.get("Type")
                gd_metrics[finding_type] += 1
    return dict(gd_metrics)


def get_securityhub_metrics(time_range_hours, region):
    """
    Retrieves Security Hub metrics by:
      - Paginating through Security Hub findings.
      - Filtering findings by their CreatedAt timestamp.
      - Aggregating counts by the primary type (first entry in the Types list).
    """
    logging.info("Collecting SecurityHub metrics")
    sh_client = boto3.client("securityhub", region_name=region)
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(hours=time_range_hours)
    sh_metrics = defaultdict(int)

    try:
        paginator = sh_client.get_paginator("get_findings")
    except Exception as e:
        logging.error(f"Error initializing SecurityHub paginator: {e}")
        return {"SecurityHub_Error": f"Error initializing SecurityHub paginator: {e}"}

    try:
        for page in paginator.paginate():
            findings = page.get("Findings", [])
            for finding in findings:
                created_at_str = finding.get("CreatedAt")
                try:
                    created_at = datetime.datetime.strptime(
                        created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                except ValueError:
                    created_at = datetime.datetime.strptime(
                        created_at_str, "%Y-%m-%dT%H:%M:%SZ"
                    )
                created_at = created_at.replace(tzinfo=datetime.timezone.utc)
                if not (start_time <= created_at <= end_time):
                    continue
                types = finding.get("Types", [])
                if types:
                    # For simplicity, group by the first type
                    primary_type = types[0]
                    sh_metrics[primary_type] += 1
    except Exception as e:
        logging.error(f"Error retrieving SecurityHub findings: {e}")
        return {"SecurityHub_Error": f"Error retrieving SecurityHub findings: {e}"}

    if not sh_metrics:
        logging.info("No SecurityHub findings found in region")
        return {"SecurityHub_Message": "No SecurityHub findings found in region"}
    return dict(sh_metrics)


def main(args):
    results = {}
    if not args.skip_waf:
        results["WAF"] = get_waf_metrics(args.time_range, args.region)
    else:
        logging.info("Skipping WAF metrics")
    if not args.skip_guardduty:
        results["GuardDuty"] = get_guardduty_metrics(args.time_range, args.region)
    else:
        logging.info("Skipping GuardDuty metrics")
    if not args.skip_securityhub:
        results["SecurityHub"] = get_securityhub_metrics(args.time_range, args.region)
    else:
        logging.info("Skipping SecurityHub metrics")

    # Print out the results in JSON format
    print(json.dumps(results, indent=4, default=str))
    return results


def lambda_handler(event, context):
    # For Lambda, you can define default arguments or extract them from the event
    # Here we assume default values for region and time_range
    class Args:
        region = None
        skip_waf = False
        skip_guardduty = False
        skip_securityhub = False
        time_range = 24

    return main(Args())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AWS Security Services Metrics Utility"
    )
    parser.add_argument(
        "--region", type=str, default="us-east-1", help="AWS region to use"
    )
    parser.add_argument(
        "--skip-waf", action="store_true", help="Skip WAF metrics collection"
    )
    parser.add_argument(
        "--skip-guardduty",
        action="store_true",
        help="Skip GuardDuty metrics collection",
    )
    parser.add_argument(
        "--skip-securityhub",
        action="store_true",
        help="Skip SecurityHub metrics collection",
    )
    parser.add_argument(
        "--time-range",
        type=int,
        default=24,
        help="Time range in hours for metrics collection",
    )
    args = parser.parse_args()
    main(args)
