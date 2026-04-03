"""
SNS-based alerter for email notifications.
"""

from typing import Optional
from monitors.base_monitor import ResourceHealth, HealthStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class SNSAlerter:
    """Send alerts via SNS to email."""

    def __init__(
        self,
        session_manager,
        topic_arn: str,
        email: Optional[str] = None
    ):
        """
        Initialize SNS alerter.

        Args:
            session_manager: AWS session manager
            topic_arn: SNS topic ARN
            email: Email address for subscriptions
        """
        self.session_manager = session_manager
        self.topic_arn = topic_arn
        self.email = email
        self.logger = logger
        self.sns_client = session_manager.get_client('sns')

    def send(self, service_name: str, health: ResourceHealth) -> None:
        """
        Send alert via SNS.

        Args:
            service_name: AWS service name
            health: ResourceHealth object
        """
        subject = self._format_subject(service_name, health)
        message = self._format_message(service_name, health)

        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            self.logger.info(f"Alert sent via SNS: {response.get('MessageId')}")
        except Exception as e:
            self.logger.error(f"Failed to send SNS alert: {e}")
            raise

    def send_test(self, test_message: str) -> None:
        """Send a test alert."""
        subject = "AWS Monitoring System - Test Alert"
        message = f"Test Alert\n\n{test_message}\n\nThis is a test of the monitoring system."

        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            self.logger.info(f"Test alert sent via SNS: {response.get('MessageId')}")
        except Exception as e:
            self.logger.error(f"Failed to send test SNS alert: {e}")
            raise

    def _format_subject(self, service_name: str, health: ResourceHealth) -> str:
        """Format alert subject line."""
        status_emoji = {
            HealthStatus.HEALTHY: '✓',
            HealthStatus.DEGRADED: '⚠',
            HealthStatus.UNHEALTHY: '✗',
            HealthStatus.UNKNOWN: '?'
        }
        emoji = status_emoji.get(health.status, '?')
        return f"{emoji} [{service_name.upper()}] {health.resource_name} is {health.status.value}"

    def _format_message(self, service_name: str, health: ResourceHealth) -> str:
        """Format alert message body."""
        message = f"""AWS Monitoring Alert

Service: {service_name.upper()}
Resource: {health.resource_name}
Resource ID: {health.resource_id}
Status: {health.status.value.upper()}
Message: {health.message}

Timestamp: {health.timestamp.isoformat()}
Region: {health.region}

Metrics:
"""
        if health.metrics:
            for key, value in health.metrics.items():
                message += f"  {key}: {value}\n"
        else:
            message += "  (no metrics available)\n"

        message += f"""
Please investigate and take appropriate action.

---
AWS Monitoring System
"""
        return message
