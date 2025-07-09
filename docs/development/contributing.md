# Contributing

We welcome contributions to AWS Cloud Utilities v2! This guide will help you get started with contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- AWS CLI configured
- Virtual environment tool (venv, conda, etc.)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/jon-the-dev/aws-cloud-tools.git
cd aws-cloud-tools/v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Development Script

Use the provided development setup script:

```bash
./install_dev.sh
```

This script will:
- Create a virtual environment
- Install the package in development mode
- Install development dependencies
- Set up pre-commit hooks
- Run initial tests

## Project Structure

```
aws_cloud_utilities/
├── __init__.py
├── cli.py                 # Main CLI entry point
├── core/                  # Core functionality
│   ├── auth.py           # AWS authentication
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exceptions
│   └── utils.py          # Utility functions
├── commands/             # Command implementations
│   ├── account.py
│   ├── costops.py
│   ├── security.py
│   └── ...
└── models/              # Data models
    └── ...
```

## Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
# Ensure you're on main and have latest code
git checkout main
git pull origin main

# Create new branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aws_cloud_utilities

# Run specific test file
pytest tests/test_cli.py

# Run integration tests
pytest tests/integration/
```

### 4. Code Quality Checks

```bash
# Format code
black aws_cloud_utilities tests

# Lint code
flake8 aws_cloud_utilities tests

# Type checking
mypy aws_cloud_utilities

# Run all quality checks
make lint
```

### 5. Commit Changes

```bash
# Add changes
git add .

# Commit with descriptive message
git commit -m "feat: add new cost optimization command"

# Push to your branch
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Create a pull request on GitHub
- Provide clear description of changes
- Link any related issues
- Ensure CI checks pass

## Code Style Guidelines

### Python Code Style

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all functions
- Use docstrings for all public functions and classes
- Use f-strings for string formatting

### Example Function

```python
def get_account_info(
    aws_auth: AWSAuth,
    include_limits: bool = False
) -> Dict[str, Any]:
    """Get AWS account information.
    
    Args:
        aws_auth: AWS authentication instance
        include_limits: Whether to include service limits
        
    Returns:
        Dictionary containing account information
        
    Raises:
        AWSError: If unable to retrieve account information
    """
    try:
        caller_identity = aws_auth.get_caller_identity()
        
        result = {
            "account_id": caller_identity.get("Account"),
            "user_arn": caller_identity.get("Arn"),
            "user_id": caller_identity.get("UserId")
        }
        
        if include_limits:
            result["limits"] = get_service_limits(aws_auth)
            
        return result
        
    except Exception as e:
        raise AWSError(f"Failed to get account info: {e}") from e
```

### Command Structure

All commands should follow this pattern:

```python
@click.group(name="service")
def service_group():
    """Service description."""
    pass


@service_group.command()
@click.option("--option", help="Option description")
@click.pass_context
def command_name(ctx: click.Context, option: str) -> None:
    """Command description.
    
    Args:
        ctx: Click context
        option: Option description
    """
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    try:
        # Command implementation
        result = do_something(aws_auth, option)
        
        # Output result
        print_output(
            result,
            output_format=config.aws_output_format,
            title="Command Results"
        )
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_cli.py
│   ├── test_auth.py
│   └── commands/
│       ├── test_account.py
│       └── test_costops.py
├── integration/          # Integration tests
│   ├── test_aws_integration.py
│   └── test_command_integration.py
└── fixtures/            # Test fixtures
    └── sample_data.py
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from aws_cloud_utilities.commands.account import get_account_info
from aws_cloud_utilities.core.auth import AWSAuth


class TestAccountCommands:
    """Test account commands."""
    
    @patch('aws_cloud_utilities.commands.account.boto3.client')
    def test_get_account_info_success(self, mock_boto_client):
        """Test successful account info retrieval."""
        # Arrange
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.get_caller_identity.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/test",
            "UserId": "AIDACKCEVSQ6C2EXAMPLE"
        }
        
        aws_auth = AWSAuth()
        
        # Act
        result = get_account_info(aws_auth)
        
        # Assert
        assert result["account_id"] == "123456789012"
        assert "arn:aws:iam::123456789012:user/test" in result["user_arn"]
        mock_client.get_caller_identity.assert_called_once()
    
    def test_get_account_info_with_invalid_auth(self):
        """Test account info with invalid authentication."""
        # Arrange
        aws_auth = Mock()
        aws_auth.get_caller_identity.side_effect = Exception("Invalid credentials")
        
        # Act & Assert
        with pytest.raises(AWSError):
            get_account_info(aws_auth)
```

### Integration Tests

Integration tests require AWS credentials:

```python
@pytest.mark.integration
class TestAWSIntegration:
    """Integration tests requiring AWS credentials."""
    
    def test_real_account_info(self):
        """Test with real AWS account."""
        # Skip if no AWS credentials
        if not has_aws_credentials():
            pytest.skip("No AWS credentials available")
            
        aws_auth = AWSAuth()
        result = get_account_info(aws_auth)
        
        assert "account_id" in result
        assert len(result["account_id"]) == 12
```

## Documentation Guidelines

### Docstring Format

Use Google-style docstrings:

```python
def process_resources(
    resources: List[Dict[str, Any]],
    filter_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Process AWS resources with optional filtering.
    
    Args:
        resources: List of AWS resource dictionaries
        filter_type: Optional resource type filter
        
    Returns:
        Filtered and processed list of resources
        
    Raises:
        ValueError: If resources list is empty
        
    Example:
        >>> resources = [{"type": "ec2", "id": "i-123"}]
        >>> filtered = process_resources(resources, "ec2")
        >>> len(filtered)
        1
    """
```

### Command Documentation

Each command should have:

- Clear description
- Usage examples
- Option descriptions
- Output format examples

### README Updates

Update relevant README files when:

- Adding new commands
- Changing command behavior
- Adding new features
- Fixing significant bugs

## Adding New Commands

### 1. Create Command File

Create a new file in `aws_cloud_utilities/commands/`:

```python
# aws_cloud_utilities/commands/newservice.py
"""New service commands."""

import click
from ..core.config import Config
from ..core.auth import AWSAuth
from ..core.utils import print_output


@click.group(name="newservice")
def newservice_group():
    """New service management commands."""
    pass


@newservice_group.command()
@click.option("--option", help="Command option")
@click.pass_context
def new_command(ctx: click.Context, option: str) -> None:
    """New command description."""
    config: Config = ctx.obj["config"]
    aws_auth: AWSAuth = ctx.obj["aws_auth"]
    
    # Implementation here
    result = {"message": "Hello from new command"}
    
    print_output(
        result,
        output_format=config.aws_output_format,
        title="New Command Results"
    )
```

### 2. Register Command

Add to `cli.py`:

```python
from .commands import newservice

# Add to main CLI
main.add_command(newservice.newservice_group)
```

### 3. Add Tests

Create test file:

```python
# tests/unit/commands/test_newservice.py
import pytest
from aws_cloud_utilities.commands.newservice import new_command


class TestNewServiceCommands:
    """Test new service commands."""
    
    def test_new_command(self):
        """Test new command functionality."""
        # Test implementation
        pass
```

### 4. Update Documentation

- Add command to documentation
- Update command index
- Add usage examples

## Release Process

### Version Numbering

We use semantic versioning (SemVer):

- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Create pull request
6. Merge to main
7. Create GitHub release
8. Publish to PyPI (when ready)

## Getting Help

### Communication Channels

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Pull Request Reviews: Code-specific discussions

### Code Review Process

1. All changes require pull request
2. At least one approval required
3. All CI checks must pass
4. Documentation must be updated
5. Tests must be included

### Common Issues

**Import Errors**
```bash
# Reinstall in development mode
pip install -e ".[dev]"
```

**Test Failures**
```bash
# Run specific test with verbose output
pytest -v tests/unit/test_cli.py::test_specific_function
```

**Linting Errors**
```bash
# Auto-fix formatting
black aws_cloud_utilities tests

# Check specific issues
flake8 aws_cloud_utilities/commands/account.py
```

## Best Practices

1. **Write tests first** (TDD approach)
2. **Keep functions small** and focused
3. **Use type hints** everywhere
4. **Handle errors gracefully** with clear messages
5. **Document everything** that's not obvious
6. **Follow existing patterns** in the codebase
7. **Test with real AWS resources** when possible
8. **Consider backward compatibility** for changes

Thank you for contributing to AWS Cloud Utilities v2!
