"""
Alert manager - orchestrates sending alerts through various channels.
"""

from typing import List, Any, Dict
from utils.logger import get_logger
from monitors.base_monitor import ResourceHealth

logger = get_logger(__name__)


class AlertManager:
    """Manage and send alerts for unhealthy resources."""

    def __init__(self, config: Any, session_manager: Any = None):
        """
        Initialize alert manager.

        Args:
            config: Alerts configuration
            session_manager: AWS session manager for SNS/SES
        """
        self.config = config
        self.session_manager = session_manager
        self.logger = logger
        self.alerters = []

        # Initialize direct email alerter if enabled (preferred method)
        if config.email_enabled and config.email:
            try:
                from alerts.email_alerter import EmailAlerter

                # Email alerter can use SMTP or AWS SES
                email_alerter = EmailAlerter(
                    to_email=config.email,
                    from_email=config.email_from,
                    smtp_host=config.smtp_host,
                    smtp_port=config.smtp_port,
                    smtp_user=config.smtp_user,
                    smtp_password=config.smtp_password,
                    use_tls=config.smtp_tls,
                    session_manager=session_manager
                )
                self.alerters.append(email_alerter)
                self.logger.info("Direct email alerter enabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize email alerter: {e}")

        # Initialize SNS alerter if enabled
        if config.sns_enabled and session_manager:
            try:
                from alerts.sns_alerter import SNSAlerter
                sns_alerter = SNSAlerter(
                    session_manager,
                    config.sns_topic_arn,
                    config.email
                )
                self.alerters.append(sns_alerter)
                self.logger.info("SNS alerter enabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize SNS alerter: {e}")

    def send_alert(self, service_name: str, health: ResourceHealth) -> bool:
        """
        Send alert for unhealthy resource.

        Args:
            service_name: Name of the service
            health: ResourceHealth object

        Returns:
            True if alert was sent successfully
        """
        if not self.alerters:
            self.logger.debug(f"No alerters configured, skipping alert for {health.resource_id}")
            return False

        success = True
        for alerter in self.alerters:
            try:
                alerter.send(service_name, health)
            except Exception as e:
                self.logger.error(f"Error sending alert via {alerter.__class__.__name__}: {e}")
                success = False

        return success

    def send_test_alert(self, test_message: str) -> bool:
        """Send a test alert to verify configuration."""
        if not self.alerters:
            self.logger.warning("No alerters configured")
            return False

        success = True
        for alerter in self.alerters:
            try:
                alerter.send_test(test_message)
            except Exception as e:
                self.logger.error(f"Error sending test alert via {alerter.__class__.__name__}: {e}")
                success = False

        return success
