"""Tag filtering utilities for AWS resources."""

import logging
from typing import Any, Dict, List, Optional, Set
from botocore.exceptions import ClientError

from .auth import AWSAuth
from .exceptions import AWSError

logger = logging.getLogger(__name__)


class TagFilter:
    """Utility class for filtering AWS resources by tags."""

    def __init__(
        self,
        tag_key: Optional[str] = None,
        tag_value: Optional[str] = None,
        aws_auth: Optional[AWSAuth] = None,
    ):
        """Initialize tag filter.

        Args:
            tag_key: The tag key to filter by
            tag_value: The tag value to filter by
            aws_auth: AWS authentication instance (for Resource Groups Tagging API)
        """
        self.tag_key = tag_key
        self.tag_value = tag_value
        self.aws_auth = aws_auth
        self.enabled = bool(tag_key)

    def matches(self, resource: Dict[str, Any]) -> bool:
        """Check if a resource matches the tag filter.

        Args:
            resource: AWS resource dictionary

        Returns:
            True if resource matches filter (or filter is disabled), False otherwise
        """
        if not self.enabled:
            return True

        # Try different common tag formats in AWS resources
        tags = self._extract_tags(resource)

        if not tags:
            return False

        # Check if the tag key exists and matches the value (if specified)
        for key, value in tags.items():
            if key == self.tag_key:
                if self.tag_value is None:
                    return True  # Key exists, value not specified
                return value == self.tag_value

        return False

    def _extract_tags(self, resource: Dict[str, Any]) -> Dict[str, str]:
        """Extract tags from a resource in various formats.

        AWS resources can have tags in different formats:
        - List of dicts: [{"Key": "Environment", "Value": "Production"}]
        - Dict: {"Environment": "Production"}
        - Tags field: resource["Tags"]
        - TagList field: resource["TagList"]

        Args:
            resource: AWS resource dictionary

        Returns:
            Dictionary of tag key-value pairs
        """
        tags = {}

        # Check for Tags field (most common)
        if "Tags" in resource:
            tags_data = resource["Tags"]

            # Handle list of dicts format
            if isinstance(tags_data, list):
                for tag in tags_data:
                    if isinstance(tag, dict):
                        if "Key" in tag and "Value" in tag:
                            tags[tag["Key"]] = tag["Value"]
                        elif "key" in tag and "value" in tag:
                            tags[tag["key"]] = tag["value"]

            # Handle dict format
            elif isinstance(tags_data, dict):
                tags = tags_data

        # Check for TagList field (WorkSpaces, RDS, etc.)
        elif "TagList" in resource:
            tag_list = resource["TagList"]
            if isinstance(tag_list, list):
                for tag in tag_list:
                    if isinstance(tag, dict) and "Key" in tag and "Value" in tag:
                        tags[tag["Key"]] = tag["Value"]

        # Check for direct tag keys in resource (EC2 instances often have this)
        elif "tag_name" in resource or "Name" in resource:
            # Some resources have flattened tag structure
            for key, value in resource.items():
                if key.startswith("tag:") or key.startswith("Tag:"):
                    clean_key = key.split(":", 1)[1]
                    tags[clean_key] = value

        return tags

    def filter_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a list of resources by tags.

        Args:
            resources: List of AWS resource dictionaries

        Returns:
            Filtered list of resources
        """
        if not self.enabled:
            return resources

        return [resource for resource in resources if self.matches(resource)]

    def get_resource_arns_by_tag(
        self, resource_type_filters: Optional[List[str]] = None, region: Optional[str] = None
    ) -> Set[str]:
        """Get resource ARNs using AWS Resource Groups Tagging API.

        This is more efficient for large-scale filtering as it queries server-side.

        Args:
            resource_type_filters: List of resource types to filter (e.g., ["ec2:instance", "rds:db"])
            region: AWS region to query

        Returns:
            Set of resource ARNs that match the tag filter

        Raises:
            AWSError: If unable to query Resource Groups Tagging API
        """
        if not self.enabled or not self.aws_auth:
            return set()

        try:
            client = self.aws_auth.get_client("resourcegroupstaggingapi", region_name=region)

            # Build tag filters
            tag_filters = [{"Key": self.tag_key}]
            if self.tag_value:
                tag_filters[0]["Values"] = [self.tag_value]

            # Query parameters
            params = {"TagFilters": tag_filters}
            if resource_type_filters:
                params["ResourceTypeFilters"] = resource_type_filters

            # Paginate through results
            resource_arns = set()
            paginator = client.get_paginator("get_resources")

            for page in paginator.paginate(**params):
                for resource in page.get("ResourceTagMappingList", []):
                    resource_arns.add(resource["ResourceARN"])

            logger.info(
                f"Found {len(resource_arns)} resources with tag {self.tag_key}={self.tag_value or '*'}"
            )
            return resource_arns

        except ClientError as e:
            logger.warning(f"Error querying Resource Groups Tagging API: {e}")
            # Return empty set to fall back to client-side filtering
            return set()

    def create_filter_display(self) -> str:
        """Create a display string for the current filter.

        Returns:
            Human-readable filter description
        """
        if not self.enabled:
            return "No tag filter"

        if self.tag_value:
            return f"{self.tag_key}={self.tag_value}"
        else:
            return f"Tag key: {self.tag_key} (any value)"


def create_tag_filter_options(command_func: callable) -> callable:
    """Decorator to add tag filter options to a Click command.

    Args:
        command_func: Click command function to decorate

    Returns:
        Decorated command function
    """
    command_func = click.option(
        "--tag-key",
        help="Filter resources by tag key (e.g., Environment)",
    )(command_func)

    command_func = click.option(
        "--tag-value",
        help="Filter resources by tag value (requires --tag-key)",
    )(command_func)

    return command_func


# Import click for the decorator
import click
