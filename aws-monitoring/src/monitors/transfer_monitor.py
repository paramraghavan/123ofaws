"""Monitor AWS Transfer servers."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class TransferMonitor(BaseMonitor):
    """Monitor AWS Transfer server health and status."""

    @property
    def service_name(self) -> str:
        return 'transfer'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of Transfer servers."""
        health_results = []

        for server_id in resources:
            try:
                health = self._check_server_health(server_id)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking Transfer {server_id}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=server_id,
                        resource_name=server_id,
                        resource_type='Transfer',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_server_health(self, server_id: str) -> ResourceHealth:
        """Check health of a single Transfer server."""
        try:
            # Get server info
            response = self.client.describe_server(ServerId=server_id)
            server = response.get('Server', {})

            server_state = server.get('State')
            protocols = server.get('Protocols', [])
            identity_provider_type = server.get('IdentityProviderType')

            metrics = {
                'state': server_state,
                'protocols': protocols,
                'identity_provider': identity_provider_type,
                'arn': server.get('Arn')
            }

            # Check server state
            if server_state == 'OFFLINE':
                return ResourceHealth(
                    resource_id=server_id,
                    resource_name=server_id,
                    resource_type='Transfer',
                    status=HealthStatus.UNHEALTHY,
                    message="Server is offline",
                    metrics=metrics,
                    region=self.region
                )

            if server_state != 'ONLINE':
                return ResourceHealth(
                    resource_id=server_id,
                    resource_name=server_id,
                    resource_type='Transfer',
                    status=HealthStatus.DEGRADED,
                    message=f"Server state is {server_state}",
                    metrics=metrics,
                    region=self.region
                )

            # Check if protocols are configured
            if not protocols:
                return ResourceHealth(
                    resource_id=server_id,
                    resource_name=server_id,
                    resource_type='Transfer',
                    status=HealthStatus.DEGRADED,
                    message="No protocols are enabled on this server",
                    metrics=metrics,
                    region=self.region
                )

            status = HealthStatus.HEALTHY
            message = f"Server is {server_state} with {', '.join(protocols)} protocol(s)"

            return ResourceHealth(
                resource_id=server_id,
                resource_name=server_id,
                resource_type='Transfer',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                status = HealthStatus.UNHEALTHY
                message = "Server does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=server_id,
            resource_name=server_id,
            resource_type='Transfer',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/Transfer'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'ServerId', 'Value': resource_id}]
