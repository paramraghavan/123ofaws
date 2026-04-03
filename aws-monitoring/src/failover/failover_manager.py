"""
Failover management - handles manual and automatic resource failover to secondary region.

Supports:
1. Manual failover: User selects resources to failover
2. Automatic failover: Secondary region auto-fails over if primary goes down
3. Heartbeat detection: Primary sends heartbeat, secondary detects failure
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.logger import get_logger
import boto3

logger = get_logger(__name__)


class FailoverManager:
    """Manage manual and automatic failover operations."""

    def __init__(self, session_manager, config: Dict[str, Any]):
        """
        Initialize failover manager.

        Args:
            session_manager: AWSSessionManager instance
            config: Failover configuration with:
                - enabled: Enable failover support
                - mode: 'primary' or 'secondary'
                - auto_failover: Enable automatic failover (secondary only)
                - manual_only: Only allow manual failover
                - secondary_region: Target failover region
                - primary_failure_timeout: Time before considering primary down
                - heartbeat_enabled: Enable heartbeat detection
                - heartbeat_table: DynamoDB table for heartbeat
        """
        self.session_manager = session_manager
        self.config = config
        self.logger = logger
        self.primary_region = session_manager.region
        self.secondary_region = config.get('secondary_region')
        self.enabled = config.get('enabled', False)
        self.mode = config.get('mode', 'primary')  # 'primary' or 'secondary'
        self.auto_failover = config.get('auto_failover', False)
        self.manual_only = config.get('manual_only', True)

        # Heartbeat settings
        self.heartbeat_enabled = config.get('heartbeat_enabled', False)
        self.heartbeat_table = config.get('heartbeat_table', 'monitoring-heartbeat')
        self.heartbeat_interval = config.get('heartbeat_interval', 60)  # seconds
        self.primary_failure_timeout = config.get('primary_failure_timeout', 300)  # 5 minutes
        self.failure_threshold = config.get('failover_threshold', 2)  # Confirm twice before failover

        # DynamoDB for heartbeat
        self.dynamodb = None
        if self.heartbeat_enabled:
            try:
                self.dynamodb = session_manager.get_client('dynamodb')
                self.logger.info(f"Heartbeat enabled using DynamoDB table: {self.heartbeat_table}")
            except Exception as e:
                self.logger.warning(f"Could not initialize DynamoDB for heartbeat: {e}")

    def execute_failover(
        self,
        service: str,
        resource_id: str,
        target_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute manual failover for a resource.

        Args:
            service: AWS service name
            resource_id: Resource ID/ARN
            target_region: Target region (uses secondary_region if not specified)

        Returns:
            Result dictionary
        """
        if not self.enabled:
            return {
                'success': False,
                'message': 'Failover is disabled'
            }

        target = target_region or self.secondary_region
        if not target:
            return {
                'success': False,
                'message': 'No target region specified'
            }

        self.logger.info(f"Executing failover for {service}/{resource_id} to {target}")

        try:
            result = self._failover_resource(service, resource_id, target)
            self.logger.info(f"Failover completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Failover failed: {e}", exc_info=True)
            return {
                'success': False,
                'message': str(e)
            }

    def _failover_resource(
        self,
        service: str,
        resource_id: str,
        target_region: str
    ) -> Dict[str, Any]:
        """
        Execute service-specific failover logic.

        Args:
            service: AWS service name
            resource_id: Resource ID
            target_region: Target region

        Returns:
            Result dictionary
        """
        # This is a placeholder for service-specific failover logic
        # In production, implement actual failover for each service

        failover_handlers = {
            'lambda': self._failover_lambda,
            'ec2': self._failover_ec2,
            's3': self._failover_s3,
            # Add handlers for other services
        }

        handler = failover_handlers.get(service)
        if handler:
            return handler(resource_id, target_region)
        else:
            return {
                'success': False,
                'message': f'No failover handler for service: {service}'
            }

    def _failover_lambda(self, function_name: str, target_region: str) -> Dict[str, Any]:
        """Failover Lambda function."""
        # This would involve:
        # 1. Create session in target region
        # 2. Copy function code/configuration
        # 3. Update DNS/routing
        return {
            'success': True,
            'service': 'lambda',
            'resource': function_name,
            'target_region': target_region,
            'message': 'Lambda failover initiated (placeholder)'
        }

    def _failover_ec2(self, instance_id: str, target_region: str) -> Dict[str, Any]:
        """Failover EC2 instance."""
        # This would involve:
        # 1. Create AMI from current instance
        # 2. Launch in target region
        # 3. Update load balancer
        return {
            'success': True,
            'service': 'ec2',
            'resource': instance_id,
            'target_region': target_region,
            'message': 'EC2 failover initiated (placeholder)'
        }

    def _failover_s3(self, bucket_name: str, target_region: str) -> Dict[str, Any]:
        """Failover S3 bucket."""
        # This would involve:
        # 1. Enable cross-region replication if not enabled
        # 2. Update Route53/DNS
        return {
            'success': True,
            'service': 's3',
            'resource': bucket_name,
            'target_region': target_region,
            'message': 'S3 failover initiated (placeholder)'
        }

    # ===================== Heartbeat Management =====================

    def send_heartbeat(self) -> bool:
        """
        Send heartbeat from primary region.
        Indicates primary region is healthy.

        Returns:
            True if heartbeat sent successfully
        """
        if not self.heartbeat_enabled or not self.dynamodb:
            return False

        if self.mode != 'primary':
            return False

        try:
            response = self.dynamodb.put_item(
                TableName=self.heartbeat_table,
                Item={
                    'region': {'S': self.primary_region},
                    'last_heartbeat': {'S': datetime.utcnow().isoformat()},
                    'status': {'S': 'healthy'},
                    'timestamp': {'N': str(int(datetime.utcnow().timestamp()))}
                }
            )
            self.logger.debug(f"Heartbeat sent to {self.heartbeat_table}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
            return False

    def check_primary_heartbeat(self) -> Dict[str, Any]:
        """
        Check primary region's heartbeat (secondary region only).
        Used to detect if primary region is down.

        Returns:
            {
                'healthy': bool,
                'heartbeat_age_seconds': int,
                'is_primary_down': bool,
                'last_heartbeat': str
            }
        """
        if not self.heartbeat_enabled or not self.dynamodb:
            return {
                'healthy': True,
                'heartbeat_age_seconds': 0,
                'is_primary_down': False,
                'last_heartbeat': 'N/A'
            }

        if self.mode != 'secondary':
            return {
                'healthy': True,
                'heartbeat_age_seconds': 0,
                'is_primary_down': False,
                'last_heartbeat': 'Primary region (not secondary)'
            }

        try:
            response = self.dynamodb.get_item(
                TableName=self.heartbeat_table,
                Key={'region': {'S': self.session_manager.region}}  # Look for primary heartbeat
            )

            if 'Item' not in response:
                # No heartbeat found
                return {
                    'healthy': False,
                    'heartbeat_age_seconds': float('inf'),
                    'is_primary_down': True,
                    'last_heartbeat': 'Never'
                }

            last_heartbeat_str = response['Item']['last_heartbeat']['S']
            last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
            heartbeat_age = (datetime.utcnow() - last_heartbeat).total_seconds()

            is_primary_down = heartbeat_age > self.primary_failure_timeout

            return {
                'healthy': heartbeat_age < self.primary_failure_timeout,
                'heartbeat_age_seconds': int(heartbeat_age),
                'is_primary_down': is_primary_down,
                'last_heartbeat': last_heartbeat_str
            }

        except Exception as e:
            self.logger.error(f"Error checking primary heartbeat: {e}")
            return {
                'healthy': False,
                'heartbeat_age_seconds': float('inf'),
                'is_primary_down': True,
                'last_heartbeat': f'Error: {e}'
            }

    # ===================== Automatic Failover =====================

    def check_and_failover_if_needed(self) -> Optional[Dict[str, Any]]:
        """
        Check if primary is down and automatically failover if secondary mode.

        Returns:
            Failover result or None if no failover needed
        """
        if not self.enabled or not self.auto_failover or self.mode != 'secondary':
            return None

        heartbeat_status = self.check_primary_heartbeat()

        if not heartbeat_status['is_primary_down']:
            self.logger.debug("Primary region is healthy, no failover needed")
            return None

        self.logger.warning(
            f"Primary region down! Heartbeat age: {heartbeat_status['heartbeat_age_seconds']}s"
        )

        # Check if we should failover
        if heartbeat_status['heartbeat_age_seconds'] < self.primary_failure_timeout:
            self.logger.info("Waiting for confirmation of primary failure...")
            return None

        self.logger.critical(
            f"PRIMARY REGION FAILURE DETECTED! Initiating automatic failover!"
        )

        # Execute automatic failover for all resources
        return self.execute_all_resources_failover()

    def execute_all_resources_failover(self) -> Dict[str, Any]:
        """
        Execute failover for ALL resources to secondary region.
        Called when primary region is completely down.

        Returns:
            Failover execution result
        """
        self.logger.warning("EXECUTING AUTOMATIC FAILOVER FOR ALL RESOURCES")

        result = {
            'status': 'in_progress',
            'timestamp': datetime.utcnow().isoformat(),
            'primary_region': self.primary_region,
            'target_region': self.secondary_region,
            'resources_failover': [],
            'errors': []
        }

        # Resource types to failover
        resource_types = [
            'lambda', 'ec2', 's3', 'sqs', 'sns', 'rds', 'asg',
            'cfn', 'ssm', 'iam', 'elbv2', 'kms', 'transfer'
        ]

        for resource_type in resource_types:
            try:
                self.logger.info(f"Failing over {resource_type} resources...")
                failover_result = self._failover_resource_type(resource_type)
                result['resources_failover'].append(failover_result)
            except Exception as e:
                error_msg = f"Error failing over {resource_type}: {e}"
                self.logger.error(error_msg)
                result['errors'].append(error_msg)

        result['status'] = 'completed' if not result['errors'] else 'completed_with_errors'
        self.logger.warning(f"Automatic failover result: {result}")

        return result

    def _failover_resource_type(self, resource_type: str) -> Dict[str, Any]:
        """
        Failover all resources of a specific type.

        Returns:
            Result for this resource type
        """
        return {
            'resource_type': resource_type,
            'status': 'failover_initiated',
            'count': 0,  # Placeholder - actual count would come from discovery
            'target_region': self.secondary_region
        }

    # ===================== Manual Failover =====================

    def get_failover_status(self) -> Dict[str, Any]:
        """Get current failover configuration and status."""
        heartbeat_status = self.check_primary_heartbeat()

        return {
            'enabled': self.enabled,
            'mode': self.mode,
            'manual_only': self.manual_only,
            'auto_failover': self.auto_failover,
            'primary_region': self.primary_region,
            'secondary_region': self.secondary_region,
            'heartbeat': {
                'enabled': self.heartbeat_enabled,
                'primary_healthy': heartbeat_status['healthy'],
                'age_seconds': heartbeat_status['heartbeat_age_seconds'],
                'last_heartbeat': heartbeat_status['last_heartbeat']
            }
        }
