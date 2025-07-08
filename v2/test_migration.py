#!/usr/bin/env python3
"""Test script for migrated commands."""

import sys
import os

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing imports...")
        
        # Test core modules
        from aws_cloud_utilities.core.config import Config
        from aws_cloud_utilities.core.auth import AWSAuth
        from aws_cloud_utilities.core.utils import get_aws_account_id
        from aws_cloud_utilities.core.exceptions import AWSCloudUtilitiesError
        print("✓ Core modules imported successfully")
        
        # Test command modules
        from aws_cloud_utilities.commands.account import account_group
        from aws_cloud_utilities.commands.bedrock import bedrock_group
        from aws_cloud_utilities.commands.support import support_group
        print("✓ Command modules imported successfully")
        
        # Test CLI
        from aws_cloud_utilities.cli import main
        print("✓ CLI module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    try:
        print("\nTesting configuration...")
        
        from aws_cloud_utilities.core.config import Config
        
        # Test default config
        config = Config()
        print(f"✓ Default config created: {config.workers} workers, {config.log_level} log level")
        
        # Test config loading
        config = Config.load_config()
        print(f"✓ Config loaded from environment: {config}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_cli_help():
    """Test CLI help functionality."""
    try:
        print("\nTesting CLI help...")
        
        from click.testing import CliRunner
        from aws_cloud_utilities.cli import main
        
        runner = CliRunner()
        
        # Test main help
        result = runner.invoke(main, ["--help"])
        if result.exit_code == 0 and "AWS Cloud Utilities" in result.output:
            print("✓ Main CLI help works")
        else:
            print(f"✗ Main CLI help failed: {result.output}")
            return False
        
        # Test account help
        result = runner.invoke(main, ["account", "--help"])
        if result.exit_code == 0 and "Account information" in result.output:
            print("✓ Account command help works")
        else:
            print(f"✗ Account command help failed: {result.output}")
            return False
        
        # Test bedrock help
        result = runner.invoke(main, ["bedrock", "--help"])
        if result.exit_code == 0 and "Bedrock management" in result.output:
            print("✓ Bedrock command help works")
        else:
            print(f"✗ Bedrock command help failed: {result.output}")
            return False
        
        # Test support help
        result = runner.invoke(main, ["support", "--help"])
        if result.exit_code == 0 and "support tools" in result.output:
            print("✓ Support command help works")
        else:
            print(f"✗ Support command help failed: {result.output}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ CLI help test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("AWS Cloud Utilities v2 - Migration Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration successful.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
