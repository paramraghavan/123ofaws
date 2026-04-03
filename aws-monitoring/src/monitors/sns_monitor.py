"""Monitor AWS SNS topics."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class SNSMonitor(BaseMonitor):
    """Monitor SNS topic health and metrics."""

    @property
    def service_name(self) -> str:
        return 'sns'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of SNS topics."""
        health_results = []

        for topic_arn in resources:
            try:
                health = self._check_topic_health(topic_arn)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking SNS {topic_arn}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=topic_arn,
                        resource_name=topic_arn.split(':')[-1],
                        resource_type='SNS',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_topic_health(self, topic_arn: str) -> ResourceHealth:
        """Check health of a single SNS topic."""
        try:
            # Get topic attributes
            response = self.client.get_topic_attributes(TopicArn=topic_arn)
            attributes = response.get('Attributes', {})
            topic_name = topic_arn.split(':')[-1]

            metrics = {
                'subscriptions': int(attributes.get('SubscriptionsConfirmed', 0)) +
                                int(attributes.get('SubscriptionsPending', 0))
            }

            # Check if topic exists (attributes will be empty if deleted)
            if not attributes:
                return ResourceHealth(
                    resource_id=topic_arn,
                    resource_name=topic_name,
                    resource_type='SNS',
                    status=HealthStatus.UNHEALTHY,
                    message="Topic does not exist or is inaccessible",
                    region=self.region
                )

            status = HealthStatus.HEALTHY
            message = f"Topic is healthy with {metrics['subscriptions']} subscription(s)"

            return ResourceHealth(
                resource_id=topic_arn,
                resource_name=topic_name,
                resource_type='SNS',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFound':
                status = HealthStatus.UNHEALTHY
                message = "Topic does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=topic_arn,
            resource_name=topic_arn.split(':')[-1],
            resource_type='SNS',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/SNS'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        topic_name = resource_id.split(':')[-1]
        return [{'Name': 'TopicName', 'Value': topic_name}]
