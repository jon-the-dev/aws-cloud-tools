#!/usr/bin/env python3
"""
Example script demonstrating RDS MySQL troubleshooting capabilities.

This script shows how to use the aws-cloud-utilities RDS troubleshooting
functionality programmatically.
"""

import json
import logging
from aws_cloud_utilities.core.config import Config
from aws_cloud_utilities.core.auth import AWSAuth
from aws_cloud_utilities.commands.rds import RDSManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def troubleshoot_mysql_instance(db_instance_identifier: str, profile: str = None, region: str = None):
    """
    Troubleshoot a MySQL RDS instance for connection issues.
    
    Args:
        db_instance_identifier: RDS instance identifier
        profile: AWS profile name (optional)
        region: AWS region (optional)
    """
    try:
        # Initialize configuration
        config = Config()
        if region:
            config.aws_default_region = region
        
        # Initialize AWS authentication
        aws_auth = AWSAuth(profile_name=profile, region_name=region)
        
        # Create RDS manager
        rds_manager = RDSManager(config, aws_auth)
        
        # Run troubleshooting analysis
        logger.info(f"Starting troubleshooting analysis for {db_instance_identifier}")
        results = rds_manager.troubleshoot_mysql_connections(db_instance_identifier)
        
        if 'error' in results:
            logger.error(f"Troubleshooting failed: {results['error']}")
            return None
        
        # Display key findings
        print(f"\n=== MySQL Troubleshooting Results for {db_instance_identifier} ===\n")
        
        # Instance info
        instance_info = results.get('instance_info', {})
        if instance_info:
            print(f"Instance Class: {instance_info.get('instance_class', 'N/A')}")
            print(f"Engine Version: {instance_info.get('engine_version', 'N/A')}")
            print(f"Status: {instance_info.get('status', 'N/A')}")
            print(f"Multi-AZ: {instance_info.get('multi_az', 'N/A')}")
            print(f"Performance Insights: {instance_info.get('performance_insights_enabled', 'N/A')}")
        
        # Connection metrics
        metrics = results.get('connection_metrics', {})
        if metrics:
            print(f"\n--- Connection Metrics (Last 24 Hours) ---")
            db_connections = metrics.get('DatabaseConnections', {})
            if isinstance(db_connections, dict):
                print(f"Current Connections: {db_connections.get('current_avg', 'N/A')} avg, {db_connections.get('current_max', 'N/A')} max")
                print(f"Peak Connections: {db_connections.get('peak_avg', 'N/A')} avg, {db_connections.get('peak_max', 'N/A')} max")
            
            aborted_connections = metrics.get('AbortedConnections', {})
            if isinstance(aborted_connections, dict):
                print(f"Aborted Connections: {aborted_connections.get('peak_max', 'N/A')} peak")
        
        # Error logs
        error_logs = results.get('error_logs', {})
        if error_logs and 'total_connection_errors' in error_logs:
            print(f"\n--- Error Analysis ---")
            print(f"Connection-related errors found: {error_logs['total_connection_errors']}")
            if error_logs.get('connection_errors'):
                print("Recent connection errors:")
                for error in error_logs['connection_errors'][:3]:  # Show first 3
                    print(f"  - {error}")
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            print(f"\n--- Recommendations ---")
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                print(f"{i}. {rec}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during troubleshooting: {e}")
        return None


def main():
    """Main function for example usage."""
    # Example usage - replace with your actual RDS instance identifier
    db_instance_identifier = "my-mysql-db"
    
    # You can specify profile and region
    profile = None  # or "my-aws-profile"
    region = "us-east-1"  # or your preferred region
    
    print("RDS MySQL Troubleshooting Example")
    print("=" * 40)
    
    # Run the troubleshooting
    results = troubleshoot_mysql_instance(
        db_instance_identifier=db_instance_identifier,
        profile=profile,
        region=region
    )
    
    if results:
        # Optionally save results to file
        output_file = f"rds_troubleshooting_{db_instance_identifier}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {output_file}")
    else:
        print("Troubleshooting failed. Check the logs for more information.")


if __name__ == "__main__":
    main()
