"""Configuration management for AWS Cloud Utilities."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class Config(BaseModel):
    """Configuration settings for AWS Cloud Utilities."""

    # AWS Configuration
    aws_profile: Optional[str] = Field(default=None, description="AWS profile to use")
    aws_region: Optional[str] = Field(default=None, description="Default AWS region")
    aws_output_format: str = Field(default="table", description="Output format")

    # Application Configuration
    workers: int = Field(default=4, description="Number of worker threads")
    log_level: str = Field(default="INFO", description="Logging level")
    data_dir: Optional[str] = Field(default=None, description="Data directory path")

    # Output Configuration
    verbose: bool = Field(default=False, description="Enable verbose output")
    debug: bool = Field(default=False, description="Enable debug mode")
    no_color: bool = Field(default=False, description="Disable colored output")

    class Config:
        """Pydantic configuration."""

        env_prefix = "AWS_"
        case_sensitive = False

    @validator("workers")
    def validate_workers(cls, v: int) -> int:
        """Validate worker count."""
        if v < 1:
            return 1
        if v > 50:
            return 50
        return v

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            return "INFO"
        return v.upper()

    @validator("aws_output_format")
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        valid_formats = ["table", "json", "yaml", "csv"]
        if v.lower() not in valid_formats:
            return "table"
        return v.lower()

    @classmethod
    def load_config(cls, config_file: Optional[str] = None, **overrides: Any) -> "Config":
        """Load configuration from environment and files."""
        # Load from .env files
        env_files = [".env", Path.home() / ".aws-cloud-utilities.env", Path.home() / ".env"]

        if config_file:
            env_files.insert(0, config_file)

        for env_file in env_files:
            if Path(env_file).exists():
                load_dotenv(env_file)
                break

        # Get configuration from environment
        config_data = {
            "aws_profile": os.getenv("AWS_PROFILE"),
            "aws_region": os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION"),
            "aws_output_format": os.getenv("AWS_OUTPUT_FORMAT", "table"),
            "workers": int(os.getenv("WORKERS", "4")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "data_dir": os.getenv("DATA_DIR"),
            "verbose": os.getenv("VERBOSE", "false").lower() == "true",
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "no_color": os.getenv("NO_COLOR", "false").lower() == "true",
        }

        # Apply overrides
        config_data.update(overrides)

        # Remove None values
        config_data = {k: v for k, v in config_data.items() if v is not None}

        return cls(**config_data)

    def setup_logging(self) -> None:
        """Set up logging configuration."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        if self.debug:
            level = logging.DEBUG
        else:
            level = getattr(logging, self.log_level)

        logging.basicConfig(level=level, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")

        # Reduce boto3 logging noise
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        if self.data_dir:
            data_dir = Path(self.data_dir)
        else:
            data_dir = Path.home() / "data" / "aws-cloud-utilities"

        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()

    def __str__(self) -> str:
        """String representation of configuration."""
        config_items = []
        for key, value in self.dict().items():
            if key.startswith("aws_") and value:
                config_items.append(f"{key}: {value}")
        return f"Config({', '.join(config_items)})"
