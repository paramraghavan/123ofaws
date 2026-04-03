"""Monitor AWS Elastic Load Balancer v2 (ALB/NLB)."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class ELBv2Monitor(BaseMonitor):
    """Monitor Application/Network Load Balancer health."""

    @property
    def service_name(self) -> str:
        return 'elbv2'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of load balancers."""
        health_results = []

        for lb_arn in resources:
            try:
                health = self._check_lb_health(lb_arn)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking ELBv2 {lb_arn}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=lb_arn,
                        resource_name=lb_arn.split(':')[-1],
                        resource_type='ELBv2',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_lb_health(self, lb_arn: str) -> ResourceHealth:
        """Check health of a single load balancer."""
        try:
            # Get load balancer info
            response = self.client.describe_load_balancers(LoadBalancerArns=[lb_arn])
            lbs = response.get('LoadBalancers', [])

            if not lbs:
                return ResourceHealth(
                    resource_id=lb_arn,
                    resource_name=lb_arn.split(':')[-1],
                    resource_type='ELBv2',
                    status=HealthStatus.UNHEALTHY,
                    message="Load balancer not found",
                    region=self.region
                )

            lb = lbs[0]
            lb_name = lb.get('LoadBalancerName')
            state = lb.get('State', {}).get('Code')
            scheme = lb.get('Scheme')

            metrics = {
                'state': state,
                'scheme': scheme,
                'vpc_id': lb.get('VpcId'),
                'type': lb.get('Type')
            }

            # Check load balancer state
            if state != 'active':
                return ResourceHealth(
                    resource_id=lb_arn,
                    resource_name=lb_name,
                    resource_type='ELBv2',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Load balancer state is {state}",
                    metrics=metrics,
                    region=self.region
                )

            # Check target groups
            targets_response = self.client.describe_target_groups(LoadBalancerArn=lb_arn)
            target_groups = targets_response.get('TargetGroups', [])
            metrics['target_groups'] = len(target_groups)

            if not target_groups:
                return ResourceHealth(
                    resource_id=lb_arn,
                    resource_name=lb_name,
                    resource_type='ELBv2',
                    status=HealthStatus.DEGRADED,
                    message="No target groups associated with load balancer",
                    metrics=metrics,
                    region=self.region
                )

            # Check health of each target group
            for tg in target_groups:
                tg_arn = tg.get('TargetGroupArn')
                try:
                    health_response = self.client.describe_target_health(
                        TargetGroupArn=tg_arn
                    )
                    targets = health_response.get('TargetHealthDescriptions', [])
                    healthy_targets = len([t for t in targets if t['TargetHealth']['State'] == 'healthy'])
                    total_targets = len(targets)

                    if total_targets > 0 and healthy_targets < total_targets:
                        metrics[f'tg_healthy_{tg.get("TargetGroupName")}'] = f"{healthy_targets}/{total_targets}"
                except Exception as e:
                    self.logger.debug(f"Error checking target health: {e}")

            status = HealthStatus.HEALTHY
            message = f"Load balancer is {state} with {len(target_groups)} target group(s)"

            return ResourceHealth(
                resource_id=lb_arn,
                resource_name=lb_name,
                resource_type='ELBv2',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'LoadBalancerNotFound':
                status = HealthStatus.UNHEALTHY
                message = "Load balancer not found"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=lb_arn,
            resource_name=lb_arn.split(':')[-1],
            resource_type='ELBv2',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/ApplicationELB'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        lb_name = resource_id.split(':')[-1]
        return [{'Name': 'LoadBalancer', 'Value': lb_name}]
