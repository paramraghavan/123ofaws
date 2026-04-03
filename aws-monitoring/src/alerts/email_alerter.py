"""
Direct email alerter - sends alerts via SMTP or AWS SES.
"""

from typing import Optional, List
from monitors.base_monitor import ResourceHealth, HealthStatus
from utils.logger import get_logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = get_logger(__name__)


class EmailAlerter:
    """Send alerts via direct email (SMTP or AWS SES)."""

    def __init__(
        self,
        to_email: str,
        from_email: str = None,
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None,
        use_tls: bool = True,
        session_manager = None
    ):
        """
        Initialize email alerter.

        Args:
            to_email: Recipient email address(es) - comma-separated for multiple
            from_email: Sender email address
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com, mail.example.com)
            smtp_port: SMTP port (default 587 for TLS, 465 for SSL)
            smtp_user: SMTP authentication username
            smtp_password: SMTP authentication password
            use_tls: Use TLS encryption (default True)
            session_manager: AWSSessionManager for SES (alternative to SMTP)
        """
        self.to_email = to_email
        self.from_email = from_email or "aws-monitoring@example.com"
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.session_manager = session_manager
        self.logger = logger

        # Parse multiple email addresses
        self.to_emails = [e.strip() for e in to_email.split(',')]

        # Determine mode
        if self.smtp_host:
            self.mode = 'smtp'
            self.logger.info(f"Email alerter configured for SMTP: {self.smtp_host}:{self.smtp_port}")
        elif session_manager:
            self.mode = 'ses'
            self.logger.info("Email alerter configured for AWS SES")
        else:
            self.logger.warning("Email alerter not fully configured - no SMTP or SES settings")
            self.mode = 'none'

    def send(self, service_name: str, health: ResourceHealth) -> None:
        """
        Send alert email.

        Args:
            service_name: AWS service name
            health: ResourceHealth object
        """
        subject = self._format_subject(service_name, health)
        body = self._format_message(service_name, health)

        if self.mode == 'smtp':
            self._send_via_smtp(subject, body)
        elif self.mode == 'ses':
            self._send_via_ses(subject, body)
        else:
            self.logger.warning("Email alerter not configured - skipping email")

    def send_test(self, test_message: str) -> None:
        """Send a test email."""
        subject = "AWS Monitoring System - Test Email"
        body = f"""Test Email

{test_message}

This is a test of the monitoring system email alerting.

---
AWS Monitoring System
"""
        if self.mode == 'smtp':
            self._send_via_smtp(subject, body)
        elif self.mode == 'ses':
            self._send_via_ses(subject, body)
        else:
            self.logger.warning("Email alerter not configured")

    def _send_via_smtp(self, subject: str, body: str) -> None:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)

            # Attach plain text version
            msg.attach(MIMEText(body, 'plain'))

            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            # Authenticate if credentials provided
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # Send to all recipients
            server.sendmail(self.from_email, self.to_emails, msg.as_string())
            server.quit()

            self.logger.info(f"Email sent to {', '.join(self.to_emails)}")

        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            raise

    def _send_via_ses(self, subject: str, body: str) -> None:
        """Send email via AWS SES."""
        try:
            if not self.session_manager:
                raise Exception("Session manager not configured for SES")

            ses_client = self.session_manager.get_client('ses')

            # Verify sender email is allowed in SES
            ses_client.send_email(
                Source=self.from_email,
                Destination={
                    'ToAddresses': self.to_emails
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            self.logger.info(f"Email sent via SES to {', '.join(self.to_emails)}")

        except Exception as e:
            self.logger.error(f"Error sending email via SES: {e}")
            raise

    def _format_subject(self, service_name: str, health: ResourceHealth) -> str:
        """Format email subject line."""
        status_emoji = {
            HealthStatus.HEALTHY: '✓',
            HealthStatus.DEGRADED: '⚠',
            HealthStatus.UNHEALTHY: '✗',
            HealthStatus.UNKNOWN: '?'
        }
        emoji = status_emoji.get(health.status, '?')
        return f"{emoji} [{service_name.upper()}] {health.resource_name} is {health.status.value}"

    def _format_message(self, service_name: str, health: ResourceHealth) -> str:
        """Format email body."""
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
Email Alerter
"""
        return message
