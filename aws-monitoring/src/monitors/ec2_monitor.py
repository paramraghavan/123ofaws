"""Monitor AWS EC2 instances."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class EC2Monitor(BaseMonitor):
    """Monitor EC2 instance health and performance."""

    @property
    def service_name(self) -> str:
        return 'ec2'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """
        Check health of EC2 instances.

        Args:
            resources: List of instance IDs

        Returns:
            List of ResourceHealth objects
        """
        health_results = []

        for instance_id in resources:
            try:
                health = self._check_instance_health(instance_id)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking EC2 {instance_id}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=instance_id,
                        resource_name=instance_id,
                        resource_type='EC2',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_instance_health(self, instance_id: str) -> ResourceHealth:
        """Check health of a single EC2 instance."""
        try:
            # Get instance details
            response = self.client.describe_instances(InstanceIds=[instance_id])

            if not response['Reservations']:
                return ResourceHealth(
                    resource_id=instance_id,
                    resource_name=instance_id,
                    resource_type='EC2',
                    status=HealthStatus.UNHEALTHY,
                    message="Instance not found",
                    region=self.region
                )

            instance = response['Reservations'][0]['Instances'][0]
            instance_name = self._get_instance_name(instance)
            state = instance['State']['Name']

            # Check instance state
            if state not in ['running', 'pending']:
                return ResourceHealth(
                    resource_id=instance_id,
                    resource_name=instance_name,
                    resource_type='EC2',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Instance state is {state}",
                    region=self.region
                )

            # Check status checks
            status_checks = self._get_instance_status_checks(instance_id)
            if not status_checks['instance_status'] or not status_checks['system_status']:
                return ResourceHealth(
                    resource_id=instance_id,
                    resource_name=instance_name,
                    resource_type='EC2',
                    status=HealthStatus.DEGRADED,
                    message=f"Status check failed: {status_checks['status_message']}",
                    metrics=status_checks,
                    region=self.region
                )

            # Check CPU utilization
            cpu_util = self.get_cloudwatch_metrics(
                instance_id,
                'CPUUtilization',
                'Average',
                5
            )
            cpu_threshold = self._get_threshold('cpu_utilization', 80.0)
            if cpu_util and cpu_util > cpu_threshold:
                return ResourceHealth(
                    resource_id=instance_id,
                    resource_name=instance_name,
                    resource_type='EC2',
                    status=HealthStatus.DEGRADED,
                    message=f"CPU utilization {cpu_util:.1f}% exceeds threshold {cpu_threshold}%",
                    metrics={'cpu_utilization': cpu_util},
                    region=self.region
                )

            # Instance is healthy
            return ResourceHealth(
                resource_id=instance_id,
                resource_name=instance_name,
                resource_type='EC2',
                status=HealthStatus.HEALTHY,
                message="Instance is running and healthy",
                metrics={
                    'state': state,
                    'cpu_utilization': cpu_util,
                    **status_checks
                },
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
                status = HealthStatus.UNHEALTHY
                message = "Instance not found"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=instance_id,
            resource_name=instance_id,
            resource_type='EC2',
            status=status,
            message=message,
            region=self.region
        )

    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """Extract instance name from tags."""
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return instance['InstanceId']

    def _get_instance_status_checks(self, instance_id: str) -> Dict[str, Any]:
        """Get instance status checks."""
        try:
            response = self.client.describe_instance_status(InstanceIds=[instance_id])

            if not response['InstanceStatuses']:
                return {
                    'instance_status': True,
                    'system_status': True,
                    'status_message': 'No status information'
                }

            status = response['InstanceStatuses'][0]
            instance_ok = status['InstanceStatus']['Status'] == 'ok'
            system_ok = status['SystemStatus']['Status'] == 'ok'

            message = []
            if not instance_ok:
                message.append(f"Instance status: {status['InstanceStatus']['Status']}")
            if not system_ok:
                message.append(f"System status: {status['SystemStatus']['Status']}")

            return {
                'instance_status': instance_ok,
                'system_status': system_ok,
                'status_message': ', '.join(message) if message else 'All checks passed'
            }
        except Exception as e:
            self.logger.debug(f"Error getting status checks for {instance_id}: {e}")
            return {
                'instance_status': True,
                'system_status': True,
                'status_message': f"Could not retrieve: {e}"
            }

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/EC2'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'InstanceId', 'Value': resource_id}]
