"""Monitor AWS EMR clusters."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class EMRMonitor(BaseMonitor):
    """Monitor EMR cluster health and status."""

    @property
    def service_name(self) -> str:
        return 'emr'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of EMR clusters."""
        health_results = []

        for cluster_id in resources:
            try:
                health = self._check_cluster_health(cluster_id)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking EMR {cluster_id}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=cluster_id,
                        resource_name=cluster_id,
                        resource_type='EMR',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_cluster_health(self, cluster_id: str) -> ResourceHealth:
        """Check health of a single EMR cluster."""
        try:
            # Get cluster info
            response = self.client.describe_cluster(ClusterId=cluster_id)
            cluster = response.get('Cluster', {})

            cluster_name = cluster.get('Name', cluster_id)
            status = cluster.get('Status', {}).get('State')
            status_code = cluster.get('Status', {}).get('StateChangeReason', '')

            metrics = {
                'state': status,
                'log_uri': cluster.get('LogUri', ''),
                'master_public_dns': cluster.get('MasterPublicDNS', 'N/A')
            }

            # Map EMR states to health status
            if status in ['TERMINATED', 'TERMINATED_WITH_ERRORS']:
                health_status = HealthStatus.UNHEALTHY
                message = f"Cluster is {status}"
            elif status in ['TERMINATING', 'WAITING']:
                health_status = HealthStatus.HEALTHY
                message = f"Cluster is {status}"
            elif status in ['RUNNING', 'BOOTSTRAPPING']:
                health_status = HealthStatus.HEALTHY
                message = f"Cluster is {status}"
            else:
                health_status = HealthStatus.UNKNOWN
                message = f"Cluster state is {status}"

            return ResourceHealth(
                resource_id=cluster_id,
                resource_name=cluster_name,
                resource_type='EMR',
                status=health_status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidRequestException':
                status = HealthStatus.UNHEALTHY
                message = "Cluster does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=cluster_id,
            resource_name=cluster_id,
            resource_type='EMR',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/ElasticMapReduce'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'JobFlowId', 'Value': resource_id}]
