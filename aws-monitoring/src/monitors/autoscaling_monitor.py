"""Monitor AWS Auto Scaling groups."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class AutoScalingMonitor(BaseMonitor):
    """Monitor Auto Scaling group health and configuration."""

    @property
    def service_name(self) -> str:
        return 'asg'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of Auto Scaling groups."""
        health_results = []

        for asg_name in resources:
            try:
                health = self._check_asg_health(asg_name)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking ASG {asg_name}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=asg_name,
                        resource_name=asg_name,
                        resource_type='AutoScaling',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_asg_health(self, asg_name: str) -> ResourceHealth:
        """Check health of a single Auto Scaling group."""
        try:
            # Get ASG details
            response = self.client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )

            if not response.get('AutoScalingGroups'):
                return ResourceHealth(
                    resource_id=asg_name,
                    resource_name=asg_name,
                    resource_type='AutoScaling',
                    status=HealthStatus.UNHEALTHY,
                    message="Auto Scaling group not found",
                    region=self.region
                )

            asg = response['AutoScalingGroups'][0]
            desired = asg.get('DesiredCapacity', 0)
            current = len(asg.get('Instances', []))
            healthy = len([i for i in asg.get('Instances', [])
                          if i.get('HealthStatus') == 'Healthy'])
            in_service = len([i for i in asg.get('Instances', [])
                             if i.get('LifecycleState') == 'InService'])

            metrics = {
                'desired_capacity': desired,
                'current_capacity': current,
                'healthy_instances': healthy,
                'in_service_instances': in_service,
                'min_size': asg.get('MinSize', 0),
                'max_size': asg.get('MaxSize', 0)
            }

            # Check if capacity matches desired
            if current < desired:
                return ResourceHealth(
                    resource_id=asg_name,
                    resource_name=asg_name,
                    resource_type='AutoScaling',
                    status=HealthStatus.DEGRADED,
                    message=f"Only {current} of {desired} desired instances running",
                    metrics=metrics,
                    region=self.region
                )

            # Check if all instances are healthy
            if healthy < current:
                return ResourceHealth(
                    resource_id=asg_name,
                    resource_name=asg_name,
                    resource_type='AutoScaling',
                    status=HealthStatus.DEGRADED,
                    message=f"Only {healthy} of {current} instances are healthy",
                    metrics=metrics,
                    region=self.region
                )

            status = HealthStatus.HEALTHY
            message = f"ASG healthy: {in_service} of {desired} instances in service"

            return ResourceHealth(
                resource_id=asg_name,
                resource_name=asg_name,
                resource_type='AutoScaling',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                status = HealthStatus.UNHEALTHY
                message = "Auto Scaling group not found"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=asg_name,
            resource_name=asg_name,
            resource_type='AutoScaling',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/AutoScaling'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'AutoScalingGroupName', 'Value': resource_id}]
