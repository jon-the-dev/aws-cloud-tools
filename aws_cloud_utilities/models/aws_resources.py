"""Data models for AWS resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AWSResource(BaseModel):
    """Base model for AWS resources."""

    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Type of AWS resource")
    region: str = Field(..., description="AWS region")
    account_id: str = Field(..., description="AWS account ID")
    tags: Dict[str, str] = Field(default_factory=dict, description="Resource tags")
    created_date: Optional[datetime] = Field(None, description="Creation date")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class EC2Instance(AWSResource):
    """EC2 instance model."""

    instance_type: str = Field(..., description="Instance type")
    state: str = Field(..., description="Instance state")
    public_ip: Optional[str] = Field(None, description="Public IP address")
    private_ip: Optional[str] = Field(None, description="Private IP address")
    vpc_id: Optional[str] = Field(None, description="VPC ID")
    subnet_id: Optional[str] = Field(None, description="Subnet ID")
    security_groups: List[str] = Field(default_factory=list, description="Security group IDs")
    key_name: Optional[str] = Field(None, description="Key pair name")
    launch_time: Optional[datetime] = Field(None, description="Launch time")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "EC2Instance"


class S3Bucket(AWSResource):
    """S3 bucket model."""

    bucket_name: str = Field(..., description="Bucket name")
    versioning_enabled: bool = Field(False, description="Versioning enabled")
    encryption_enabled: bool = Field(False, description="Encryption enabled")
    public_access_blocked: bool = Field(True, description="Public access blocked")
    size_bytes: Optional[int] = Field(None, description="Bucket size in bytes")
    object_count: Optional[int] = Field(None, description="Number of objects")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "S3Bucket"


class RDSInstance(AWSResource):
    """RDS instance model."""

    db_instance_class: str = Field(..., description="DB instance class")
    engine: str = Field(..., description="Database engine")
    engine_version: str = Field(..., description="Engine version")
    db_name: Optional[str] = Field(None, description="Database name")
    status: str = Field(..., description="Instance status")
    endpoint: Optional[str] = Field(None, description="Database endpoint")
    port: Optional[int] = Field(None, description="Database port")
    multi_az: bool = Field(False, description="Multi-AZ deployment")
    backup_retention_period: int = Field(0, description="Backup retention period")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "RDSInstance"


class LambdaFunction(AWSResource):
    """Lambda function model."""

    function_name: str = Field(..., description="Function name")
    runtime: str = Field(..., description="Runtime")
    handler: str = Field(..., description="Handler")
    memory_size: int = Field(..., description="Memory size in MB")
    timeout: int = Field(..., description="Timeout in seconds")
    last_modified: Optional[datetime] = Field(None, description="Last modified date")
    code_size: Optional[int] = Field(None, description="Code size in bytes")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "LambdaFunction"


class IAMRole(AWSResource):
    """IAM role model."""

    role_name: str = Field(..., description="Role name")
    path: str = Field("/", description="Role path")
    assume_role_policy: Dict[str, Any] = Field(..., description="Assume role policy document")
    max_session_duration: int = Field(3600, description="Maximum session duration")
    attached_policies: List[str] = Field(default_factory=list, description="Attached policy ARNs")
    inline_policies: List[str] = Field(default_factory=list, description="Inline policy names")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "IAMRole"


class BedrockModel(AWSResource):
    """Bedrock foundation model."""

    model_id: str = Field(..., description="Model identifier")
    model_name: str = Field(..., description="Model name")
    provider_name: str = Field(..., description="Model provider")
    model_arn: Optional[str] = Field(None, description="Model ARN")
    input_modalities: List[str] = Field(default_factory=list, description="Input modalities")
    output_modalities: List[str] = Field(default_factory=list, description="Output modalities")
    response_streaming_supported: bool = Field(False, description="Response streaming support")
    customizations_supported: List[str] = Field(default_factory=list, description="Customization types")
    inference_types_supported: List[str] = Field(default_factory=list, description="Inference types")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "BedrockModel"


class BedrockCustomModel(AWSResource):
    """Bedrock custom model."""

    model_name: str = Field(..., description="Custom model name")
    model_arn: str = Field(..., description="Custom model ARN")
    base_model_arn: str = Field(..., description="Base model ARN")
    status: str = Field(..., description="Model status")
    job_name: Optional[str] = Field(None, description="Training job name")
    job_arn: Optional[str] = Field(None, description="Training job ARN")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "BedrockCustomModel"


class IAMRole(AWSResource):
    """IAM role model."""

    role_name: str = Field(..., description="Role name")
    path: str = Field("/", description="Role path")
    assume_role_policy: Dict[str, Any] = Field(..., description="Assume role policy document")
    max_session_duration: int = Field(3600, description="Maximum session duration")
    attached_policies: List[str] = Field(default_factory=list, description="Attached policy ARNs")
    inline_policies: List[str] = Field(default_factory=list, description="Inline policy names")
    description: Optional[str] = Field(None, description="Role description")
    permissions_boundary: Optional[str] = Field(None, description="Permissions boundary ARN")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "IAMRole"


class IAMPolicy(AWSResource):
    """IAM policy model."""

    policy_name: str = Field(..., description="Policy name")
    policy_arn: str = Field(..., description="Policy ARN")
    path: str = Field("/", description="Policy path")
    policy_document: Dict[str, Any] = Field(..., description="Policy document")
    default_version_id: str = Field(..., description="Default version ID")
    attachment_count: int = Field(0, description="Number of entities attached to")
    permissions_boundary_usage_count: int = Field(0, description="Permissions boundary usage count")
    is_attachable: bool = Field(True, description="Whether policy is attachable")
    description: Optional[str] = Field(None, description="Policy description")
    is_aws_managed: bool = Field(False, description="Whether this is an AWS managed policy")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "IAMPolicy"


class IAMUser(AWSResource):
    """IAM user model."""

    user_name: str = Field(..., description="User name")
    path: str = Field("/", description="User path")
    user_id: str = Field(..., description="User ID")
    arn: str = Field(..., description="User ARN")
    password_last_used: Optional[datetime] = Field(None, description="Password last used")
    attached_policies: List[str] = Field(default_factory=list, description="Attached policy ARNs")
    inline_policies: List[str] = Field(default_factory=list, description="Inline policy names")
    groups: List[str] = Field(default_factory=list, description="Group memberships")
    permissions_boundary: Optional[str] = Field(None, description="Permissions boundary ARN")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "IAMUser"


class CloudWatchLogGroup(AWSResource):
    """CloudWatch log group model."""

    log_group_name: str = Field(..., description="Log group name")
    retention_in_days: Optional[int] = Field(None, description="Retention period in days")
    stored_bytes: Optional[int] = Field(None, description="Stored bytes")
    metric_filter_count: int = Field(0, description="Number of metric filters")

    @property
    def resource_type(self) -> str:
        """Resource type."""
        return "CloudWatchLogGroup"
