"""Custom exceptions for AWS Cloud Utilities."""


class AWSCloudUtilitiesError(Exception):
    """Base exception for AWS Cloud Utilities."""

    def __init__(self, message: str, error_code: str = None):
        """Initialize exception.

        Args:
            message: Error message
            error_code: Optional error code
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(AWSCloudUtilitiesError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str):
        """Initialize configuration error.

        Args:
            message: Error message
        """
        super().__init__(message, "CONFIG_ERROR")


class AWSError(AWSCloudUtilitiesError):
    """Exception raised for AWS-related errors."""

    def __init__(self, message: str, aws_error_code: str = None):
        """Initialize AWS error.

        Args:
            message: Error message
            aws_error_code: AWS error code
        """
        super().__init__(message, aws_error_code or "AWS_ERROR")
        self.aws_error_code = aws_error_code


class AuthenticationError(AWSError):
    """Exception raised for AWS authentication errors."""

    def __init__(self, message: str):
        """Initialize authentication error.

        Args:
            message: Error message
        """
        super().__init__(message, "AUTH_ERROR")


class ValidationError(AWSCloudUtilitiesError):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str = None):
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
        """
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field


class ResourceNotFoundError(AWSError):
    """Exception raised when AWS resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        """Initialize resource not found error.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
        """
        message = f"{resource_type} '{resource_id}' not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.resource_type = resource_type
        self.resource_id = resource_id


class PermissionError(AWSError):
    """Exception raised for AWS permission errors."""

    def __init__(self, action: str, resource: str = None):
        """Initialize permission error.

        Args:
            action: Action that was denied
            resource: Resource that was accessed
        """
        if resource:
            message = f"Permission denied for action '{action}' on resource '{resource}'"
        else:
            message = f"Permission denied for action '{action}'"
        super().__init__(message, "PERMISSION_DENIED")
        self.action = action
        self.resource = resource


class RateLimitError(AWSError):
    """Exception raised when AWS API rate limit is exceeded."""

    def __init__(self, service: str, retry_after: int = None):
        """Initialize rate limit error.

        Args:
            service: AWS service that was rate limited
            retry_after: Seconds to wait before retrying
        """
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.service = service
        self.retry_after = retry_after


class TimeoutError(AWSCloudUtilitiesError):
    """Exception raised for timeout errors."""

    def __init__(self, operation: str, timeout: int):
        """Initialize timeout error.

        Args:
            operation: Operation that timed out
            timeout: Timeout value in seconds
        """
        message = f"Operation '{operation}' timed out after {timeout} seconds"
        super().__init__(message, "TIMEOUT_ERROR")
        self.operation = operation
        self.timeout = timeout


class DataError(AWSCloudUtilitiesError):
    """Exception raised for data processing errors."""

    def __init__(self, message: str, data_type: str = None):
        """Initialize data error.

        Args:
            message: Error message
            data_type: Type of data that caused the error
        """
        super().__init__(message, "DATA_ERROR")
        self.data_type = data_type
