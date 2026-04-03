"""Monitor Control-M service and job health."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from utils.logger import get_logger
import os
import requests

logger = get_logger(__name__)


class ControlMMonitor(BaseMonitor):
    """Monitor Control-M service and job health."""

    @property
    def service_name(self) -> str:
        return 'controlm'

    def __init__(self, session_manager, config: Dict[str, Any]):
        """
        Initialize Control-M monitor.

        Args:
            session_manager: AWSSessionManager instance
            config: Service-specific configuration including Control-M API endpoint
        """
        super().__init__(session_manager, config)
        self.logger = logger

        # Control-M API details from config or environment
        self.controlm_endpoint = config.get('controlm_endpoint', os.getenv('CONTROLM_ENDPOINT'))
        self.controlm_user = config.get('controlm_user', os.getenv('CONTROLM_USER'))
        self.controlm_password = config.get('controlm_password', os.getenv('CONTROLM_PASSWORD'))
        self.verify_ssl = config.get('verify_ssl', True)

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """
        Check health of Control-M services and jobs.

        Args:
            resources: List of service names or job names

        Returns:
            List of ResourceHealth objects
        """
        health_results = []

        # First check if Control-M service itself is up
        service_health = self._check_controlm_service()
        health_results.append(service_health)

        # If service is down, return early
        if service_health.status == HealthStatus.UNHEALTHY:
            return health_results

        # Check individual resources (jobs, agents, etc.)
        for resource in resources:
            try:
                health = self._check_controlm_resource(resource)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking Control-M {resource}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=resource,
                        resource_name=resource,
                        resource_type='Control-M',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_controlm_service(self) -> ResourceHealth:
        """Check if Control-M service is running."""
        try:
            if not self.controlm_endpoint:
                return ResourceHealth(
                    resource_id='controlm-service',
                    resource_name='Control-M Service',
                    resource_type='Control-M',
                    status=HealthStatus.UNKNOWN,
                    message="Control-M endpoint not configured. "
                           "Set controlm_endpoint in config or CONTROLM_ENDPOINT env var",
                    region=self.region
                )

            # Test API health endpoint
            response = requests.get(
                f"{self.controlm_endpoint}/api/v2/monitoring/health",
                auth=(self.controlm_user, self.controlm_password) if self.controlm_user else None,
                verify=self.verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown').lower()

                if status == 'healthy' or status == 'ok':
                    return ResourceHealth(
                        resource_id='controlm-service',
                        resource_name='Control-M Service',
                        resource_type='Control-M',
                        status=HealthStatus.HEALTHY,
                        message="Control-M service is operational",
                        metrics={'status': status},
                        region=self.region
                    )
                else:
                    return ResourceHealth(
                        resource_id='controlm-service',
                        resource_name='Control-M Service',
                        resource_type='Control-M',
                        status=HealthStatus.DEGRADED,
                        message=f"Control-M service status: {status}",
                        metrics={'status': status},
                        region=self.region
                    )
            else:
                return ResourceHealth(
                    resource_id='controlm-service',
                    resource_name='Control-M Service',
                    resource_type='Control-M',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Control-M API returned {response.status_code}",
                    region=self.region
                )

        except requests.exceptions.Timeout:
            return ResourceHealth(
                resource_id='controlm-service',
                resource_name='Control-M Service',
                resource_type='Control-M',
                status=HealthStatus.UNHEALTHY,
                message="Control-M API timeout",
                region=self.region
            )
        except requests.exceptions.ConnectionError as e:
            return ResourceHealth(
                resource_id='controlm-service',
                resource_name='Control-M Service',
                resource_type='Control-M',
                status=HealthStatus.UNHEALTHY,
                message=f"Cannot connect to Control-M: {str(e)}",
                region=self.region
            )
        except Exception as e:
            self.logger.error(f"Error checking Control-M service: {e}")
            return ResourceHealth(
                resource_id='controlm-service',
                resource_name='Control-M Service',
                resource_type='Control-M',
                status=HealthStatus.UNKNOWN,
                message=str(e),
                region=self.region
            )

    def _check_controlm_resource(self, resource_name: str) -> ResourceHealth:
        """Check health of a Control-M resource (job, agent, etc.)."""
        try:
            if not self.controlm_endpoint:
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Control-M',
                    status=HealthStatus.UNKNOWN,
                    message="Control-M endpoint not configured",
                    region=self.region
                )

            # Get job/agent status from Control-M API
            response = requests.get(
                f"{self.controlm_endpoint}/api/v2/jobs/{resource_name}",
                auth=(self.controlm_user, self.controlm_password) if self.controlm_user else None,
                verify=self.verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                job_data = response.json()
                job_status = job_data.get('status', 'unknown')
                job_name = job_data.get('name', resource_name)

                metrics = {
                    'status': job_status,
                    'type': 'job'
                }

                # Map Control-M status to health status
                if job_status in ['Executing', 'Scheduled', 'Ready']:
                    health_status = HealthStatus.HEALTHY
                    message = f"Job {job_name} status: {job_status}"
                elif job_status in ['On Hold', 'Suspended']:
                    health_status = HealthStatus.DEGRADED
                    message = f"Job {job_name} is {job_status}"
                elif job_status in ['Failed', 'Aborted', 'Ended Not Ok']:
                    health_status = HealthStatus.UNHEALTHY
                    message = f"Job {job_name} {job_status}"
                else:
                    health_status = HealthStatus.UNKNOWN
                    message = f"Job {job_name} status: {job_status}"

                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=job_name,
                    resource_type='Control-M',
                    status=health_status,
                    message=message,
                    metrics=metrics,
                    region=self.region
                )

            elif response.status_code == 404:
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Control-M',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Job '{resource_name}' not found in Control-M",
                    region=self.region
                )
            else:
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Control-M',
                    status=HealthStatus.UNKNOWN,
                    message=f"Control-M API returned {response.status_code}",
                    region=self.region
                )

        except Exception as e:
            self.logger.error(f"Error checking Control-M resource {resource_name}: {e}")
            return ResourceHealth(
                resource_id=resource_name,
                resource_name=resource_name,
                resource_type='Control-M',
                status=HealthStatus.UNKNOWN,
                message=str(e),
                region=self.region
            )

    def _get_cloudwatch_namespace(self) -> str:
        return 'ControlM'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'JobName', 'Value': resource_id}]
