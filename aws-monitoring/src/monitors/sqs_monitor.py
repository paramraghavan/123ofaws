"""Monitor AWS SQS queues."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class SQSMonitor(BaseMonitor):
    """Monitor SQS queue health and metrics."""

    @property
    def service_name(self) -> str:
        return 'sqs'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of SQS queues."""
        health_results = []

        for queue_url in resources:
            try:
                health = self._check_queue_health(queue_url)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking SQS {queue_url}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=queue_url,
                        resource_name=queue_url,
                        resource_type='SQS',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_queue_health(self, queue_url: str) -> ResourceHealth:
        """Check health of a single SQS queue."""
        try:
            # Get queue attributes
            response = self.client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['All']
            )

            attributes = response.get('Attributes', {})
            queue_name = queue_url.split('/')[-1]

            messages = int(attributes.get('ApproximateNumberOfMessages', 0))
            not_visible = int(attributes.get('ApproximateNumberOfNotVisibleMessages', 0))

            metrics = {
                'messages': messages,
                'not_visible_messages': not_visible
            }

            # Check message threshold
            message_threshold = self._get_threshold('message_count', None)
            if message_threshold and messages > message_threshold:
                return ResourceHealth(
                    resource_id=queue_url,
                    resource_name=queue_name,
                    resource_type='SQS',
                    status=HealthStatus.DEGRADED,
                    message=f"Message count {messages} exceeds threshold {message_threshold}",
                    metrics=metrics,
                    region=self.region
                )

            status = HealthStatus.HEALTHY
            message = "Queue is accessible and functioning normally"

            return ResourceHealth(
                resource_id=queue_url,
                resource_name=queue_name,
                resource_type='SQS',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'QueueDoesNotExist':
                status = HealthStatus.UNHEALTHY
                message = "Queue does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=queue_url,
            resource_name=queue_url.split('/')[-1],
            resource_type='SQS',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/SQS'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        queue_name = resource_id.split('/')[-1]
        return [{'Name': 'QueueName', 'Value': queue_name}]
