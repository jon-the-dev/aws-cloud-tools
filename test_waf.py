#!/usr/bin/env python3
"""Test script for WAF command functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from aws_cloud_utilities.commands.waf import WAFAnalyzer
from aws_cloud_utilities.core.auth import AWSAuth
from aws_cloud_utilities.core.config import Config

def test_waf_list():
    """Test WAF list functionality."""
    try:
        # Create config
        config = Config()
        
        # Create AWS auth
        aws_auth = AWSAuth(config)
        
        # Create analyzer
        analyzer = WAFAnalyzer(aws_auth, config.region)
        
        # Test listing Web ACLs
        print("Testing WAF list functionality...")
        web_acls = analyzer.list_web_acls('REGIONAL')
        
        print(f"Found {len(web_acls)} Web ACLs")
        for acl in web_acls:
            print(f"  - {acl.get('Name', 'Unknown')} ({acl.get('Id', 'Unknown')})")
        
        return True
        
    except Exception as e:
        print(f"Error testing WAF: {e}")
        return False

if __name__ == "__main__":
    success = test_waf_list()
    sys.exit(0 if success else 1)
