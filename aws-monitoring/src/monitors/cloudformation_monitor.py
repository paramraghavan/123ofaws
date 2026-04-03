"""Monitor AWS CloudFormation stacks."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class CloudFormationMonitor(BaseMonitor):
    """Monitor CloudFormation stack health and status."""

    @property
    def service_name(self) -> str:
        return 'cfn'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of CloudFormation stacks."""
        health_results = []

        for stack_name in resources:
            try:
                health = self._check_stack_health(stack_name)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking CFN stack {stack_name}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=stack_name,
                        resource_name=stack_name,
                        resource_type='CloudFormation',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_stack_health(self, stack_name: str) -> ResourceHealth:
        """Check health of a single CloudFormation stack."""
        try:
            # Get stack info
            response = self.client.describe_stacks(StackName=stack_name)
            stacks = response.get('Stacks', [])

            if not stacks:
                return ResourceHealth(
                    resource_id=stack_name,
                    resource_name=stack_name,
                    resource_type='CloudFormation',
                    status=HealthStatus.UNHEALTHY,
                    message="Stack not found",
                    region=self.region
                )

            stack = stacks[0]
            status = stack.get('StackStatus')
            status_reason = stack.get('StackStatusReason', '')

            metrics = {
                'status': status,
                'creation_time': stack.get('CreationTime', '').isoformat()
                                if stack.get('CreationTime') else None,
                'last_update': stack.get('LastUpdatedTime', '').isoformat()
                               if stack.get('LastUpdatedTime') else None
            }

            # Map CloudFormation status to health status
            if 'FAILED' in status or 'ROLLBACK' in status:
                health_status = HealthStatus.UNHEALTHY
                message = f"Stack is {status}: {status_reason}"
            elif status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
                health_status = HealthStatus.HEALTHY
                message = f"Stack is {status}"
            elif 'IN_PROGRESS' in status:
                health_status = HealthStatus.DEGRADED
                message = f"Stack is {status}"
            else:
                health_status = HealthStatus.UNKNOWN
                message = f"Stack status is {status}"

            return ResourceHealth(
                resource_id=stack_name,
                resource_name=stack_name,
                resource_type='CloudFormation',
                status=health_status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                status = HealthStatus.UNHEALTHY
                message = "Stack not found"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=stack_name,
            resource_name=stack_name,
            resource_type='CloudFormation',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/CloudFormation'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'StackName', 'Value': resource_id}]
