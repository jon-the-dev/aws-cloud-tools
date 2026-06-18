"""Core utilities and configuration for AWS Cloud Utilities."""

from .auth import AWSAuth
from .config import Config
from .exceptions import AWSCloudUtilitiesError, AWSError, ConfigurationError
from .html_report import (
    HTMLReportGenerator,
    ReportMetadata,
    ReportSection,
    create_badge,
    create_list_html,
    create_stats_grid_html,
    create_table_html,
)
from .utils import get_all_regions, get_aws_account_id

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
