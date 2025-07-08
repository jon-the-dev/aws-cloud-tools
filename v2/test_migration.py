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
        from aws_cloud_utilities.commands.awsconfig import awsconfig_group
        from aws_cloud_utilities.commands.bedrock import bedrock_group
        from aws_cloud_utilities.commands.cloudformation import cloudformation_group
        from aws_cloud_utilities.commands.ecr import ecr_group
        from aws_cloud_utilities.commands.iam import iam_group
        from aws_cloud_utilities.commands.inventory import inventory_group
        from aws_cloud_utilities.commands.networking import networking_group
        from aws_cloud_utilities.commands.security import security_group
        from aws_cloud_utilities.commands.stepfunctions import stepfunctions_group
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
        
        # Test cloudformation help
        result = runner.invoke(main, ["cloudformation", "--help"])
        if result.exit_code == 0 and "CloudFormation management" in result.output:
            print("✓ CloudFormation command help works")
        else:
            print(f"✗ CloudFormation command help failed: {result.output}")
            return False
        
        # Test awsconfig help
        result = runner.invoke(main, ["awsconfig", "--help"])
        if result.exit_code == 0 and "Config service management" in result.output:
            print("✓ AWS Config command help works")
        else:
            print(f"✗ AWS Config command help failed: {result.output}")
            return False
        
        # Test ecr help
        result = runner.invoke(main, ["ecr", "--help"])
        if result.exit_code == 0 and "ECR" in result.output and "Container Registry" in result.output:
            print("✓ ECR command help works")
        else:
            print(f"✗ ECR command help failed: {result.output}")
            return False
        
        # Test iam help
        result = runner.invoke(main, ["iam", "--help"])
        if result.exit_code == 0 and "IAM management" in result.output:
            print("✓ IAM command help works")
        else:
            print(f"✗ IAM command help failed: {result.output}")
            return False
        
        # Test inventory help
        result = runner.invoke(main, ["inventory", "--help"])
        if result.exit_code == 0 and "inventory and discovery" in result.output:
            print("✓ Inventory command help works")
        else:
            print(f"✗ Inventory command help failed: {result.output}")
            return False
        
        # Test networking help
        result = runner.invoke(main, ["networking", "--help"])
        if result.exit_code == 0 and "networking and IP management" in result.output:
            print("✓ Networking command help works")
        else:
            print(f"✗ Networking command help failed: {result.output}")
            return False
        
        # Test security help
        result = runner.invoke(main, ["security", "--help"])
        if result.exit_code == 0 and "security monitoring" in result.output:
            print("✓ Security command help works")
        else:
            print(f"✗ Security command help failed: {result.output}")
            return False
        
        # Test stepfunctions help
        result = runner.invoke(main, ["stepfunctions", "--help"])
        if result.exit_code == 0 and "Step Functions management" in result.output:
            print("✓ Step Functions command help works")
        else:
            print(f"✗ Step Functions command help failed: {result.output}")
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
