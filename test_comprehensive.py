#!/usr/bin/env python3
"""
Comprehensive Test Suite for AWS Cloud Utilities v2

This test suite covers all non-destructive functions across all migrated commands.
It tests listing resources, inventory operations, cost analysis, and other read-only operations.

Usage:
    python test_comprehensive.py [--region REGION] [--profile PROFILE] [--verbose] [--dry-run]

Test Categories:
- Account Information
- CloudFront Operations
- CloudWatch Logs Operations  
- S3 Operations
- Cost Optimization Operations
- IAM Operations
- Inventory Operations
- Networking Operations
- Security Operations
- Support Operations
"""

import os
import sys
import argparse
import logging
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import time

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from aws_cloud_utilities.core.config import Config
from aws_cloud_utilities.core.auth import AWSAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    """Comprehensive test suite for AWS Cloud Utilities v2."""
    
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None, verbose: bool = False, dry_run: bool = False):
        self.region = region
        self.profile = profile
        self.verbose = verbose
        self.dry_run = dry_run
        self.test_results = {}
        self.failed_tests = []
        self.skipped_tests = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aws_test_"))
        
        # Initialize AWS auth for credential checks
        try:
            self.config = Config()
            self.aws_auth = AWSAuth(profile_name=profile)
            self.credentials_available = True
        except Exception as e:
            logger.warning(f"AWS credentials not available: {e}")
            self.credentials_available = False
    
    def run_cli_command(self, command: List[str], expect_success: bool = True) -> Dict[str, Any]:
        """Run a CLI command and return results."""
        
        full_command = ["python", "-m", "aws_cloud_utilities.cli"] + command
        
        if self.profile:
            full_command.extend(["--profile", self.profile])
        
        if self.verbose:
            logger.info(f"Running command: {' '.join(full_command)}")
        
        if self.dry_run:
            return {
                "success": True,
                "stdout": "DRY RUN - Command not executed",
                "stderr": "",
                "return_code": 0
            }
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=project_root
            )
            
            success = (result.returncode == 0) if expect_success else (result.returncode != 0)
            
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    def test_account_operations(self) -> Dict[str, bool]:
        """Test account-related operations."""
        
        tests = {}
        
        # Test account info
        result = self.run_cli_command(["account", "info"])
        tests["account_info"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"account info: {result['stderr']}")
        
        # Test account info with output file
        output_file = self.temp_dir / "account_info.json"
        result = self.run_cli_command(["account", "info", "--output-file", str(output_file)])
        tests["account_info_with_output"] = result["success"] and output_file.exists()
        if not tests["account_info_with_output"]:
            self.failed_tests.append(f"account info with output: {result['stderr']}")
        
        return tests
    
    def test_cloudfront_operations(self) -> Dict[str, bool]:
        """Test CloudFront operations."""
        
        tests = {}
        
        # Test list distributions
        result = self.run_cli_command(["cloudfront", "list-distributions"])
        tests["cloudfront_list_distributions"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"cloudfront list-distributions: {result['stderr']}")
        
        # Test list distributions with output file
        output_file = self.temp_dir / "cloudfront_distributions.json"
        result = self.run_cli_command([
            "cloudfront", "list-distributions", 
            "--output-file", str(output_file)
        ])
        tests["cloudfront_list_with_output"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"cloudfront list with output: {result['stderr']}")
        
        # Test list origins
        result = self.run_cli_command(["cloudfront", "list-origins"])
        tests["cloudfront_list_origins"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"cloudfront list-origins: {result['stderr']}")
        
        # Test analyze performance
        result = self.run_cli_command(["cloudfront", "analyze-performance"])
        tests["cloudfront_analyze_performance"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"cloudfront analyze-performance: {result['stderr']}")
        
        return tests
    
    def test_logs_operations(self) -> Dict[str, bool]:
        """Test CloudWatch Logs operations."""
        
        tests = {}
        
        # Test list log groups
        result = self.run_cli_command(["logs", "list-groups"])
        tests["logs_list_groups"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"logs list-groups: {result['stderr']}")
        
        # Test list log groups with size info
        result = self.run_cli_command(["logs", "list-groups", "--include-size"])
        tests["logs_list_groups_with_size"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"logs list-groups with size: {result['stderr']}")
        
        # Test list log groups with output file
        output_file = self.temp_dir / "log_groups.json"
        result = self.run_cli_command([
            "logs", "list-groups", 
            "--output-file", str(output_file)
        ])
        tests["logs_list_with_output"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"logs list with output: {result['stderr']}")
        
        return tests
    
    def test_s3_operations(self) -> Dict[str, bool]:
        """Test S3 operations."""
        
        tests = {}
        
        # Test list buckets
        result = self.run_cli_command(["s3", "list-buckets"])
        tests["s3_list_buckets"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"s3 list-buckets: {result['stderr']}")
        
        # Test list buckets with size info
        result = self.run_cli_command(["s3", "list-buckets", "--include-size"])
        tests["s3_list_buckets_with_size"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"s3 list-buckets with size: {result['stderr']}")
        
        # Test list buckets with output file
        output_file = self.temp_dir / "s3_buckets.json"
        result = self.run_cli_command([
            "s3", "list-buckets", 
            "--output-file", str(output_file)
        ])
        tests["s3_list_with_output"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"s3 list with output: {result['stderr']}")
        
        return tests
    
    def test_costops_operations(self) -> Dict[str, bool]:
        """Test Cost Optimization operations."""
        
        tests = {}
        
        # Test pricing list services
        result = self.run_cli_command(["costops", "pricing", "--list-services"])
        tests["costops_pricing_list_services"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"costops pricing list-services: {result['stderr']}")
        
        # Test cost analysis (shorter time period for testing)
        result = self.run_cli_command([
            "costops", "cost-analysis", 
            "--months", "1"
        ])
        tests["costops_cost_analysis"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"costops cost-analysis: {result['stderr']}")
        
        # Test EBS optimization analysis
        result = self.run_cli_command([
            "costops", "ebs-optimization", 
            "--region", self.region
        ])
        tests["costops_ebs_optimization"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"costops ebs-optimization: {result['stderr']}")
        
        return tests
    
    def test_iam_operations(self) -> Dict[str, bool]:
        """Test IAM operations."""
        
        tests = {}
        
        # Test list users
        result = self.run_cli_command(["iam", "list-users"])
        tests["iam_list_users"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"iam list-users: {result['stderr']}")
        
        # Test list roles
        result = self.run_cli_command(["iam", "list-roles"])
        tests["iam_list_roles"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"iam list-roles: {result['stderr']}")
        
        # Test list policies
        result = self.run_cli_command(["iam", "list-policies"])
        tests["iam_list_policies"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"iam list-policies: {result['stderr']}")
        
        return tests
    
    def test_inventory_operations(self) -> Dict[str, bool]:
        """Test inventory operations."""
        
        tests = {}
        
        # Test inventory resources
        result = self.run_cli_command([
            "inventory", "resources", 
            "--region", self.region
        ])
        tests["inventory_resources"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"inventory resources: {result['stderr']}")
        
        # Test inventory with output file
        output_file = self.temp_dir / "inventory.json"
        result = self.run_cli_command([
            "inventory", "resources", 
            "--region", self.region,
            "--output-file", str(output_file)
        ])
        tests["inventory_with_output"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"inventory with output: {result['stderr']}")
        
        return tests
    
    def test_networking_operations(self) -> Dict[str, bool]:
        """Test networking operations."""
        
        tests = {}
        
        # Test list VPCs
        result = self.run_cli_command([
            "networking", "list-vpcs", 
            "--region", self.region
        ])
        tests["networking_list_vpcs"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"networking list-vpcs: {result['stderr']}")
        
        # Test get IP ranges
        result = self.run_cli_command(["networking", "ip-ranges"])
        tests["networking_ip_ranges"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"networking ip-ranges: {result['stderr']}")
        
        return tests
    
    def test_security_operations(self) -> Dict[str, bool]:
        """Test security operations."""
        
        tests = {}
        
        # Test security groups
        result = self.run_cli_command([
            "security", "list-security-groups", 
            "--region", self.region
        ])
        tests["security_list_security_groups"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"security list-security-groups: {result['stderr']}")
        
        return tests
    
    def test_support_operations(self) -> Dict[str, bool]:
        """Test support operations."""
        
        tests = {}
        
        # Test support level
        result = self.run_cli_command(["support", "check-level"])
        tests["support_check_level"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"support check-level: {result['stderr']}")
        
        return tests
    
    def test_help_commands(self) -> Dict[str, bool]:
        """Test help commands for all modules."""
        
        tests = {}
        
        # Test main help
        result = self.run_cli_command(["--help"])
        tests["main_help"] = result["success"]
        if not result["success"]:
            self.failed_tests.append(f"main help: {result['stderr']}")
        
        # Test module help commands
        modules = [
            "account", "cloudfront", "logs", "s3", "costops", 
            "iam", "inventory", "networking", "security", "support"
        ]
        
        for module in modules:
            result = self.run_cli_command([module, "--help"])
            tests[f"{module}_help"] = result["success"]
            if not result["success"]:
                self.failed_tests.append(f"{module} help: {result['stderr']}")
        
        return tests
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories."""
        
        print("🧪 AWS Cloud Utilities v2 - Comprehensive Test Suite")
        print("=" * 60)
        
        if not self.credentials_available:
            print("⚠️  AWS credentials not available - some tests will be skipped")
            print()
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - Commands will not be executed")
            print()
        
        start_time = time.time()
        all_results = {}
        
        # Test categories
        test_categories = [
            ("Help Commands", self.test_help_commands),
        ]
        
        # Add AWS-dependent tests only if credentials are available
        if self.credentials_available:
            test_categories.extend([
                ("Account Operations", self.test_account_operations),
                ("CloudFront Operations", self.test_cloudfront_operations),
                ("CloudWatch Logs Operations", self.test_logs_operations),
                ("S3 Operations", self.test_s3_operations),
                ("Cost Optimization Operations", self.test_costops_operations),
                ("IAM Operations", self.test_iam_operations),
                ("Inventory Operations", self.test_inventory_operations),
                ("Networking Operations", self.test_networking_operations),
                ("Security Operations", self.test_security_operations),
                ("Support Operations", self.test_support_operations),
            ])
        
        # Run tests
        for category_name, test_function in test_categories:
            print(f"Testing {category_name}...")
            
            try:
                category_results = test_function()
                all_results[category_name] = category_results
                
                # Show results
                passed = sum(1 for result in category_results.values() if result)
                total = len(category_results)
                
                if passed == total:
                    print(f"✅ {category_name}: {passed}/{total} tests passed")
                else:
                    print(f"❌ {category_name}: {passed}/{total} tests passed")
                
            except Exception as e:
                print(f"💥 {category_name}: Error running tests - {e}")
                all_results[category_name] = {"error": str(e)}
                self.failed_tests.append(f"{category_name}: {str(e)}")
            
            print()
        
        # Calculate overall results
        total_tests = 0
        passed_tests = 0
        
        for category_results in all_results.values():
            if isinstance(category_results, dict) and "error" not in category_results:
                for test_result in category_results.values():
                    total_tests += 1
                    if test_result:
                        passed_tests += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(passed_tests/max(total_tests, 1)*100):.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Test Output Directory: {self.temp_dir}")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"  • {failure}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed!")
            return_code = 0
        else:
            print(f"\n⚠️  {len(self.failed_tests)} tests failed")
            return_code = 1
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": len(self.failed_tests),
            "success_rate": passed_tests/max(total_tests, 1)*100,
            "duration": duration,
            "return_code": return_code,
            "results": all_results,
            "failures": self.failed_tests
        }


def main():
    """Main function."""
    
    parser = argparse.ArgumentParser(
        description="Comprehensive test suite for AWS Cloud Utilities v2"
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region for testing (default: us-east-1)"
    )
    parser.add_argument(
        "--profile",
        help="AWS profile to use for testing"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tested without executing commands"
    )
    parser.add_argument(
        "--output-file",
        help="Save test results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Create test suite
    test_suite = ComprehensiveTestSuite(
        region=args.region,
        profile=args.profile,
        verbose=args.verbose,
        dry_run=args.dry_run
    )
    
    # Run tests
    results = test_suite.run_all_tests()
    
    # Save results if requested
    if args.output_file:
        output_path = Path(args.output_file)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Test results saved to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(results["return_code"])


if __name__ == "__main__":
    main()
