"""Core utilities and configuration for AWS Cloud Utilities."""

from .config import Config
from .auth import AWSAuth
from .utils import get_aws_account_id, get_all_regions
from .exceptions import AWSCloudUtilitiesError, ConfigurationError, AWSError
from .html_report import (
    HTMLReportGenerator,
    ReportMetadata,
    ReportSection,
    create_table_html,
    create_stats_grid_html,
    create_badge,
    create_list_html,
)

__all__ = [
    "Config",
    "AWSAuth",
    "get_aws_account_id",
    "get_all_regions",
    "AWSCloudUtilitiesError",
    "ConfigurationError",
    "AWSError",
    "HTMLReportGenerator",
    "ReportMetadata",
    "ReportSection",
    "create_table_html",
    "create_stats_grid_html",
    "create_badge",
    "create_list_html",
]
