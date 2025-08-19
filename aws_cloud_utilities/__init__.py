"""AWS Cloud Utilities - A unified toolkit for AWS operations."""

__version__ = "2.1.2"
__author__ = "Jon"
__email__ = "jon@zer0day.net"
__description__ = (
    "A unified command-line toolkit for AWS operations with enhanced functionality"
)

from .core.config import Config
from .core.utils import get_aws_account_id, get_all_regions

__all__ = [
    "Config",
    "get_aws_account_id",
    "get_all_regions",
    "__version__",
]
