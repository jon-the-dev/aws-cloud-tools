"""Tests for RDS command module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from aws_cloud_utilities.commands.rds import RDSManager
from aws_cloud_utilities.core.config import Config
from aws_cloud_utilities.core.auth import AWSAuth


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = Mock(spec=Config)
    config.aws_default_region = "us-east-1"
    config.debug = False
    return config


@pytest.fixture
def mock_aws_auth():
    """Mock AWS authentication."""
    auth = Mock(spec=AWSAuth)
    session = Mock()
    auth.session = session
    return auth


@pytest.fixture
def mock_rds_client():
    """Mock RDS client."""
    return Mock()


@pytest.fixture
def mock_cloudwatch_client():
    """Mock CloudWatch client."""
    return Mock()


@pytest.fixture
def rds_manager(mock_config, mock_aws_auth, mock_rds_client, mock_cloudwatch_client):
    """RDS manager with mocked dependencies."""
    with patch.object(mock_aws_auth.session, 'client') as mock_client:
        def client_side_effect(service_name):
            if service_name == 'rds':
                return mock_rds_client
            elif service_name == 'cloudwatch':
                return mock_cloudwatch_client
            return Mock()
        
        mock_client.side_effect = client_side_effect
        
        manager = RDSManager(mock_config, mock_aws_auth)
        manager.rds_client = mock_rds_client
        manager.cloudwatch_client = mock_cloudwatch_client
        
        return manager


class TestRDSManager:
    """Test RDS Manager functionality."""
    
    def test_get_instance_info_success(self, rds_manager, mock_rds_client):
        """Test successful instance info retrieval."""
        # Arrange
        mock_response = {
            'DBInstances': [{
                'DBInstanceIdentifier': 'test-mysql-db',
                'DBInstanceClass': 'db.t3.micro',
                'Engine': 'mysql',
                'EngineVersion': '8.0.35',
                'DBInstanceStatus': 'available',
                'AllocatedStorage': 20,
                'MultiAZ': False,
                'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-12345'}],
                'DBParameterGroups': [{'DBParameterGroupName': 'default.mysql8.0'}],
                'Endpoint': {'Address': 'test-mysql-db.cluster-xyz.us-east-1.rds.amazonaws.com', 'Port': 3306},
                'BackupRetentionPeriod': 7,
                'PreferredBackupWindow': '03:00-04:00',
                'PreferredMaintenanceWindow': 'sun:04:00-sun:05:00',
                'PerformanceInsightsEnabled': False
            }]
        }
        mock_rds_client.describe_db_instances.return_value = mock_response
        
        # Act
        result = rds_manager._get_instance_info('test-mysql-db')
        
        # Assert
        assert result['instance_class'] == 'db.t3.micro'
        assert result['engine'] == 'mysql'
        assert result['status'] == 'available'
        assert result['endpoint'] == 'test-mysql-db.cluster-xyz.us-east-1.rds.amazonaws.com'
        assert result['port'] == 3306
        assert result['performance_insights_enabled'] is False
        mock_rds_client.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier='test-mysql-db'
        )
    
    def test_get_connection_metrics_success(self, rds_manager, mock_cloudwatch_client):
        """Test successful connection metrics retrieval."""
        # Arrange
        mock_datapoints = [
            {
                'Timestamp': datetime.utcnow() - timedelta(hours=1),
                'Average': 10.5,
                'Maximum': 15.0
            },
            {
                'Timestamp': datetime.utcnow(),
                'Average': 12.3,
                'Maximum': 18.0
            }
        ]
        
        mock_response = {
            'Datapoints': mock_datapoints
        }
        mock_cloudwatch_client.get_metric_statistics.return_value = mock_response
        
        # Act
        result = rds_manager._get_connection_metrics('test-mysql-db')
        
        # Assert
        assert 'DatabaseConnections' in result
        db_connections = result['DatabaseConnections']
        assert db_connections['current_avg'] == 12.3
        assert db_connections['current_max'] == 18.0
        assert db_connections['peak_avg'] == 12.3
        assert db_connections['peak_max'] == 18.0
        assert db_connections['datapoints_count'] == 2
    
    def test_get_parameter_info_success(self, rds_manager, mock_rds_client):
        """Test successful parameter info retrieval."""
        # Arrange
        instance_response = {
            'DBInstances': [{
                'DBParameterGroups': [{'DBParameterGroupName': 'test-param-group'}]
            }]
        }
        
        params_response = {
            'Parameters': [
                {
                    'ParameterName': 'max_connections',
                    'ParameterValue': '100',
                    'Source': 'user',
                    'IsModifiable': True,
                    'Description': 'Maximum number of connections'
                },
                {
                    'ParameterName': 'wait_timeout',
                    'ParameterValue': '28800',
                    'Source': 'system',
                    'IsModifiable': True,
                    'Description': 'Wait timeout in seconds'
                },
                {
                    'ParameterName': 'other_param',
                    'ParameterValue': 'value',
                    'Source': 'system',
                    'IsModifiable': False,
                    'Description': 'Other parameter'
                }
            ]
        }
        
        mock_rds_client.describe_db_instances.return_value = instance_response
        mock_rds_client.describe_db_parameters.return_value = params_response
        
        # Act
        result = rds_manager._get_parameter_info('test-mysql-db')
        
        # Assert
        assert 'test-param-group' in result
        param_group = result['test-param-group']
        connection_params = param_group['connection_parameters']
        
        # Should only include connection-related parameters
        assert 'max_connections' in connection_params
        assert 'wait_timeout' in connection_params
        assert 'other_param' not in connection_params
        
        max_conn_param = connection_params['max_connections']
        assert max_conn_param['value'] == '100'
        assert max_conn_param['source'] == 'user'
        assert max_conn_param['is_modifiable'] is True
    
    def test_get_error_logs_success(self, rds_manager, mock_rds_client):
        """Test successful error logs retrieval."""
        # Arrange
        log_files_response = {
            'DescribeDBLogFiles': [
                {
                    'LogFileName': 'error/mysql-error.log',
                    'Size': 1024,
                    'LastWritten': 1234567890
                }
            ]
        }
        
        log_content = """2024-01-01 12:00:00 [ERROR] Too many connections
2024-01-01 12:01:00 [WARNING] Aborted connection 123
2024-01-01 12:02:00 [INFO] Normal log entry
2024-01-01 12:03:00 [ERROR] Connection refused"""
        
        log_download_response = {
            'LogFileData': log_content
        }
        
        mock_rds_client.describe_db_log_files.return_value = log_files_response
        mock_rds_client.download_db_log_file_portion.return_value = log_download_response
        
        # Act
        result = rds_manager._get_error_logs('test-mysql-db')
        
        # Assert
        assert result['log_file_name'] == 'error/mysql-error.log'
        assert result['log_size'] == 1024
        assert result['total_connection_errors'] == 3
        assert len(result['connection_errors']) == 3
        assert 'Too many connections' in result['connection_errors'][0]
        assert 'Aborted connection' in result['connection_errors'][1]
        assert 'Connection refused' in result['connection_errors'][2]
    
    def test_generate_recommendations(self, rds_manager):
        """Test recommendation generation."""
        # Arrange
        results = {
            'connection_metrics': {
                'DatabaseConnections': {
                    'peak_max': 95.0
                },
                'AbortedConnections': {
                    'peak_max': 15.0
                }
            },
            'error_logs': {
                'total_connection_errors': 25
            },
            'instance_info': {
                'instance_class': 'db.t2.micro',
                'performance_insights_enabled': False
            }
        }
        
        # Act
        recommendations = rds_manager._generate_recommendations(results)
        
        # Assert
        assert len(recommendations) > 0
        
        # Check for specific recommendations based on the test data
        high_connection_rec = any('HIGH: Peak connection count' in rec for rec in recommendations)
        assert high_connection_rec
        
        aborted_connection_rec = any('High aborted connections' in rec for rec in recommendations)
        assert aborted_connection_rec
        
        error_log_rec = any('connection-related errors in logs' in rec for rec in recommendations)
        assert error_log_rec
        
        burstable_instance_rec = any('burstable instance type' in rec for rec in recommendations)
        assert burstable_instance_rec
        
        performance_insights_rec = any('Performance Insights' in rec for rec in recommendations)
        assert performance_insights_rec
    
    def test_troubleshoot_mysql_connections_integration(self, rds_manager, mock_rds_client, mock_cloudwatch_client):
        """Test full troubleshooting integration."""
        # Arrange - Mock all the individual method calls
        with patch.object(rds_manager, '_get_instance_info') as mock_instance_info, \
             patch.object(rds_manager, '_get_connection_metrics') as mock_metrics, \
             patch.object(rds_manager, '_get_parameter_info') as mock_params, \
             patch.object(rds_manager, '_get_error_logs') as mock_logs, \
             patch.object(rds_manager, '_generate_recommendations') as mock_recommendations:
            
            mock_instance_info.return_value = {'instance_class': 'db.t3.micro'}
            mock_metrics.return_value = {'DatabaseConnections': {'peak_max': 50}}
            mock_params.return_value = {'param-group': {'connection_parameters': {}}}
            mock_logs.return_value = {'total_connection_errors': 5}
            mock_recommendations.return_value = ['Test recommendation']
            
            # Act
            result = rds_manager.troubleshoot_mysql_connections('test-mysql-db')
            
            # Assert
            assert 'instance_info' in result
            assert 'connection_metrics' in result
            assert 'parameter_info' in result
            assert 'error_logs' in result
            assert 'recommendations' in result
            assert result['recommendations'] == ['Test recommendation']
            
            # Verify all methods were called
            mock_instance_info.assert_called_once_with('test-mysql-db')
            mock_metrics.assert_called_once_with('test-mysql-db')
            mock_params.assert_called_once_with('test-mysql-db')
            mock_logs.assert_called_once_with('test-mysql-db')
            mock_recommendations.assert_called_once()


class TestRDSCommandIntegration:
    """Test RDS command integration."""
    
    @patch('aws_cloud_utilities.commands.rds.RDSManager')
    def test_troubleshoot_mysql_command(self, mock_rds_manager_class):
        """Test the troubleshoot-mysql command."""
        # This would require more complex mocking of the Click context
        # For now, we'll test the core logic through the RDSManager tests
        pass
