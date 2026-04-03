"""Monitor AWS IAM resources."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError
from datetime import datetime, timedelta


class IAMMonitor(BaseMonitor):
    """Monitor IAM roles, users, and credentials."""

    @property
    def service_name(self) -> str:
        return 'iam'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of IAM roles."""
        health_results = []

        for role_name in resources:
            try:
                health = self._check_role_health(role_name)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking IAM {role_name}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=role_name,
                        resource_name=role_name,
                        resource_type='IAM',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_role_health(self, role_name: str) -> ResourceHealth:
        """Check health of an IAM role."""
        try:
            # Get role info
            response = self.client.get_role(RoleName=role_name)
            role = response.get('Role', {})

            create_date = role.get('CreateDate')
            role_arn = role.get('Arn')

            # Get role policies
            policies_response = self.client.list_role_policies(RoleName=role_name)
            inline_policies = len(policies_response.get('PolicyNames', []))

            # Get managed policies
            managed_response = self.client.list_attached_role_policies(RoleName=role_name)
            attached_policies = len(managed_response.get('AttachedPolicies', []))

            metrics = {
                'inline_policies': inline_policies,
                'attached_policies': attached_policies,
                'create_date': create_date.isoformat() if create_date else None,
                'arn': role_arn
            }

            # Check if role has any policies
            total_policies = inline_policies + attached_policies
            if total_policies == 0:
                return ResourceHealth(
                    resource_id=role_name,
                    resource_name=role_name,
                    resource_type='IAM',
                    status=HealthStatus.DEGRADED,
                    message="Role has no attached policies",
                    metrics=metrics,
                    region=self.region
                )

            health_status = HealthStatus.HEALTHY
            message = f"Role has {total_policies} policy(ies) attached"

            return ResourceHealth(
                resource_id=role_name,
                resource_name=role_name,
                resource_type='IAM',
                status=health_status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                status = HealthStatus.UNHEALTHY
                message = "Role does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=role_name,
            resource_name=role_name,
            resource_type='IAM',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/IAM'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'RoleName', 'Value': resource_id}]
