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
                - fast_failover: Skip stacks that already completed successfully
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
        self.fast_failover = config.get('fast_failover', True)  # Skip successful stacks

        # Track success and errors during failover
        self.failover_results = {
            'success': [],
            'errors': [],
            'skipped': []
        }

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

    # ===================== Stack Status Check (Fast Failover) =====================

    def _check_cloudformation_stack_status(self, stack_name: str) -> Dict[str, Any]:
        """
        Check CloudFormation stack status.
        Used for fast failover to skip already-successful stacks.

        Returns:
            {
                'stack_name': str,
                'status': str,
                'should_skip': bool,
                'should_redeploy': bool,  # True if stack failed and should be redeployed
                'reason': str
            }
        """
        try:
            cfn_client = self.session_manager.get_client('cloudformation')
            response = cfn_client.describe_stacks(StackName=stack_name)

            if not response['Stacks']:
                return {
                    'stack_name': stack_name,
                    'status': 'NOT_FOUND',
                    'should_skip': False,
                    'should_redeploy': False,
                    'reason': 'Stack does not exist'
                }

            stack = response['Stacks'][0]
            status = stack['StackStatus']

            # Successful completion statuses - skip recreation
            successful_statuses = [
                'CREATE_COMPLETE',
                'UPDATE_COMPLETE',
                'UPDATE_ROLLBACK_COMPLETE'
            ]

            # Failed statuses - may need to redeploy (depends on fast_failover mode)
            failed_statuses = [
                'CREATE_FAILED',
                'UPDATE_FAILED',
                'UPDATE_ROLLBACK_FAILED',
                'DELETE_FAILED',
                'ROLLBACK_COMPLETE'
            ]

            if status in successful_statuses:
                return {
                    'stack_name': stack_name,
                    'status': status,
                    'should_skip': True,
                    'should_redeploy': False,
                    'reason': f'Stack already {status}, skipping'
                }
            elif status in failed_statuses:
                # In fast_failover mode, skip failed stacks
                # In normal mode, attempt to redeploy failed stacks
                skip_failed = self.fast_failover
                return {
                    'stack_name': stack_name,
                    'status': status,
                    'should_skip': skip_failed,
                    'should_redeploy': not skip_failed,  # Only redeploy if NOT in fast mode
                    'reason': f'Stack {status}, {"skipping (fast mode)" if skip_failed else "will redeploy"}'
                }
            else:
                return {
                    'stack_name': stack_name,
                    'status': status,
                    'should_skip': False,
                    'should_redeploy': False,
                    'reason': f'Stack in {status}, proceeding with failover'
                }

        except Exception as e:
            return {
                'stack_name': stack_name,
                'status': 'ERROR',
                'should_skip': False,
                'should_redeploy': False,
                'reason': str(e)
            }

    def execute_all_resources_failover(self) -> Dict[str, Any]:
        """
        Execute failover for ALL resources to secondary region.
        Called when primary region is completely down.

        With fast_failover enabled: Skip stacks that already completed successfully.
        Only recreate stacks that failed or need update.

        Returns:
            Failover execution result with detailed success/error tracking
        """
        self.logger.warning("EXECUTING AUTOMATIC FAILOVER FOR ALL RESOURCES")

        # Reset result tracking
        self.failover_results = {
            'success': [],
            'errors': [],
            'skipped': []
        }

        result = {
            'status': 'in_progress',
            'timestamp': datetime.utcnow().isoformat(),
            'primary_region': self.primary_region,
            'target_region': self.secondary_region,
            'fast_failover': self.fast_failover,
            'resources_failover': [],
            'success': [],
            'errors': [],
            'skipped': []
        }

        # Resource types to failover
        resource_types = [
            'lambda', 'ec2', 's3', 'sqs', 'sns', 'rds', 'asg',
            'cfn', 'ssm', 'iam', 'elbv2', 'kms', 'transfer'
        ]

        for resource_type in resource_types:
            try:
                self.logger.info(f"Failing over {resource_type} resources...")

                # Check stack status (applies to all modes, not just fast_failover)
                stack_status = self._check_cloudformation_stack_status(resource_type)

                # Skip if stack is already successful
                if stack_status['should_skip']:
                    self.logger.info(f"⊘ Skipping {resource_type}: {stack_status['reason']}")
                    result['skipped'].append({
                        'resource_type': resource_type,
                        'reason': stack_status['reason'],
                        'status': stack_status['status']
                    })
                    self.failover_results['skipped'].append(resource_type)
                    continue

                # Redeploy if stack failed and NOT in fast mode
                if stack_status['should_redeploy']:
                    self.logger.warning(f"🔄 Redeploying failed stack {resource_type}...")
                    failover_result = self._redeploy_failed_stack(resource_type)
                else:
                    failover_result = self._failover_resource_type(resource_type)

                result['resources_failover'].append(failover_result)
                result['success'].append({
                    'resource_type': resource_type,
                    'status': 'completed'
                })
                self.failover_results['success'].append(resource_type)

            except Exception as e:
                error_msg = f"Error failing over {resource_type}: {e}"
                self.logger.error(error_msg)
                result['errors'].append(error_msg)
                self.failover_results['errors'].append({
                    'resource_type': resource_type,
                    'error': str(e)
                })

        result['status'] = 'completed' if not result['errors'] else 'completed_with_errors'
        result['summary'] = {
            'total_resources': len(resource_types),
            'succeeded': len(result['success']),
            'failed': len(result['errors']),
            'skipped': len(result['skipped'])
        }

        self.logger.warning(f"Automatic failover result: {result}")

        return result

    def _redeploy_failed_stack(self, stack_name: str) -> Dict[str, Any]:
        """
        Redeploy a CloudFormation stack that failed.

        Attempts to recover from failed states:
        - ROLLBACK_COMPLETE: Continue update stack
        - CREATE_FAILED: Delete and recreate
        - UPDATE_FAILED: Continue update stack

        Args:
            stack_name: CloudFormation stack name

        Returns:
            Result dictionary with redeployment status
        """
        try:
            cfn_client = self.session_manager.get_client('cloudformation')

            # Get current stack status
            response = cfn_client.describe_stacks(StackName=stack_name)
            if not response['Stacks']:
                return {
                    'resource_type': stack_name,
                    'status': 'redeploy_failed',
                    'reason': 'Stack not found',
                    'target_region': self.secondary_region
                }

            stack = response['Stacks'][0]
            status = stack['StackStatus']

            self.logger.info(f"Attempting to redeploy stack {stack_name} (current status: {status})")

            # Strategy 1: Continue update if in rollback state
            if status in ['ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
                self.logger.info(f"Continuing update for {stack_name} from rollback state...")
                try:
                    cfn_client.continue_update_rollback(StackName=stack_name)
                    return {
                        'resource_type': stack_name,
                        'status': 'redeploy_initiated',
                        'action': 'continue_update_rollback',
                        'target_region': self.secondary_region
                    }
                except Exception as e:
                    self.logger.warning(f"Continue update failed for {stack_name}: {e}")
                    # Fall through to deletion strategy

            # Strategy 2: Delete and recreate for CREATE_FAILED
            if status == 'CREATE_FAILED':
                self.logger.info(f"Deleting failed stack {stack_name} for recreation...")
                try:
                    cfn_client.delete_stack(StackName=stack_name)
                    return {
                        'resource_type': stack_name,
                        'status': 'redeploy_initiated',
                        'action': 'delete_and_recreate',
                        'target_region': self.secondary_region
                    }
                except Exception as e:
                    self.logger.error(f"Failed to delete stack {stack_name}: {e}")
                    return {
                        'resource_type': stack_name,
                        'status': 'redeploy_failed',
                        'reason': f'Failed to delete: {e}',
                        'target_region': self.secondary_region
                    }

            # Strategy 3: Generic failover for other states
            return {
                'resource_type': stack_name,
                'status': 'failover_initiated',
                'action': 'failover',
                'count': 0,
                'target_region': self.secondary_region
            }

        except Exception as e:
            self.logger.error(f"Error redeploying stack {stack_name}: {e}")
            return {
                'resource_type': stack_name,
                'status': 'redeploy_failed',
                'reason': str(e),
                'target_region': self.secondary_region
            }

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
