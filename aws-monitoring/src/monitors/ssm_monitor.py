"""Monitor AWS Systems Manager documents."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class SSMMonitor(BaseMonitor):
    """Monitor Systems Manager documents and parameters."""

    @property
    def service_name(self) -> str:
        return 'ssm'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of SSM documents."""
        health_results = []

        for doc_name in resources:
            try:
                health = self._check_document_health(doc_name)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking SSM {doc_name}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=doc_name,
                        resource_name=doc_name,
                        resource_type='SSM',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_document_health(self, doc_name: str) -> ResourceHealth:
        """Check health of an SSM document."""
        try:
            # Get document info
            response = self.client.describe_document(Name=doc_name)
            document = response.get('Document', {})

            doc_type = document.get('DocumentType')
            status = document.get('DocumentStatus')
            version = document.get('LatestVersionNumber')

            metrics = {
                'type': doc_type,
                'status': status,
                'latest_version': version
            }

            # Check document status
            if status not in ['Active', 'Draft']:
                return ResourceHealth(
                    resource_id=doc_name,
                    resource_name=doc_name,
                    resource_type='SSM',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Document status is {status}",
                    metrics=metrics,
                    region=self.region
                )

            health_status = HealthStatus.HEALTHY
            message = f"Document is {status}"

            return ResourceHealth(
                resource_id=doc_name,
                resource_name=doc_name,
                resource_type='SSM',
                status=health_status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidDocument':
                status = HealthStatus.UNHEALTHY
                message = "Document does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=doc_name,
            resource_name=doc_name,
            resource_type='SSM',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/SSM'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'DocumentName', 'Value': resource_id}]
