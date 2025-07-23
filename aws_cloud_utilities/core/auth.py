"""AWS authentication and session management."""

import boto3
import logging
from typing import Optional, Dict, Any
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

from .exceptions import AWSError, ConfigurationError

logger = logging.getLogger(__name__)


class AWSAuth:
    """AWS authentication and session management."""

    def __init__(
        self,
        profile_name: Optional[str] = None,
        region_name: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize AWS authentication.

        Args:
            profile_name: AWS profile name
            region_name: AWS region name
            timeout: Connection timeout in seconds
            max_retries: Maximum number of retries
        """
        self.profile_name = profile_name
        self.region_name = region_name
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[boto3.Session] = None
        self._account_id: Optional[str] = None

        # Boto3 configuration
        self._boto_config = BotoConfig(
            connect_timeout=timeout, read_timeout=timeout, retries={"max_attempts": max_retries}
        )

    @property
    def session(self) -> boto3.Session:
        """Get or create boto3 session."""
        if self._session is None:
            try:
                if self.profile_name:
                    self._session = boto3.Session(profile_name=self.profile_name, region_name=self.region_name)
                else:
                    self._session = boto3.Session(region_name=self.region_name)

                # Test the session by getting caller identity
                self._test_credentials()

            except ProfileNotFound as e:
                raise ConfigurationError(f"AWS profile '{self.profile_name}' not found: {e}")
            except NoCredentialsError as e:
                raise ConfigurationError(f"AWS credentials not found: {e}")
            except Exception as e:
                raise AWSError(f"Failed to create AWS session: {e}")

        return self._session

    def _test_credentials(self) -> None:
        """Test AWS credentials by calling STS get_caller_identity."""
        try:
            sts_client = self.session.client("sts", config=self._boto_config)
            response = sts_client.get_caller_identity()
            self._account_id = response["Account"]
            logger.debug(f"AWS credentials validated for account: {self._account_id}")
        except ClientError as e:
            raise AWSError(f"AWS credentials validation failed: {e}")

    def get_client(self, service_name: str, region_name: Optional[str] = None) -> Any:
        """Get AWS service client.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')
            region_name: Override region for this client

        Returns:
            Boto3 client instance
        """
        try:
            return self.session.client(
                service_name, region_name=region_name or self.region_name, config=self._boto_config
            )
        except Exception as e:
            raise AWSError(f"Failed to create {service_name} client: {e}")

    def get_resource(self, service_name: str, region_name: Optional[str] = None) -> Any:
        """Get AWS service resource.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')
            region_name: Override region for this resource

        Returns:
            Boto3 resource instance
        """
        try:
            return self.session.resource(
                service_name, region_name=region_name or self.region_name, config=self._boto_config
            )
        except Exception as e:
            raise AWSError(f"Failed to create {service_name} resource: {e}")

    def get_account_id(self) -> str:
        """Get AWS account ID.

        Returns:
            AWS account ID
        """
        if self._account_id is None:
            self._test_credentials()
        return self._account_id or ""

    def get_caller_identity(self) -> Dict[str, Any]:
        """Get caller identity information.

        Returns:
            Dictionary with UserId, Account, and Arn
        """
        try:
            sts_client = self.get_client("sts")
            return sts_client.get_caller_identity()
        except ClientError as e:
            raise AWSError(f"Failed to get caller identity: {e}")

    def get_available_regions(self, service_name: str = "ec2") -> list[str]:
        """Get available regions for a service.

        Args:
            service_name: AWS service name

        Returns:
            List of region names
        """
        try:
            client = self.get_client(service_name)
            if hasattr(client, "describe_regions"):
                response = client.describe_regions()
                return [region["RegionName"] for region in response["Regions"]]
            else:
                # Fallback to session regions
                return list(self.session.get_available_regions(service_name))
        except Exception as e:
            logger.warning(f"Failed to get regions for {service_name}: {e}")
            # Return common regions as fallback
            return [
                "us-east-1",
                "us-east-2",
                "us-west-1",
                "us-west-2",
                "eu-west-1",
                "eu-west-2",
                "eu-central-1",
                "ap-southeast-1",
                "ap-southeast-2",
                "ap-northeast-1",
            ]

    def validate_region(self, region_name: str, service_name: str = "ec2") -> bool:
        """Validate if a region is available for a service.

        Args:
            region_name: Region name to validate
            service_name: AWS service name

        Returns:
            True if region is valid, False otherwise
        """
        try:
            available_regions = self.get_available_regions(service_name)
            return region_name in available_regions
        except Exception:
            return False

    def __str__(self) -> str:
        """String representation."""
        return f"AWSAuth(profile={self.profile_name}, region={self.region_name})"
