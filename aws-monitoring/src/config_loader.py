"""
Configuration loader for AWS Monitoring System.
Loads config from YAML and validates required settings.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AWSConfig:
    """AWS configuration."""
    primary_region: str = 'us-east-1'
    secondary_region: Optional[str] = None
    profile: Optional[str] = None
    localstack: bool = False


@dataclass
class ServiceConfig:
    """Individual service configuration."""
    enabled: bool = False
    thresholds: Dict[str, Any] = None
    metrics: list = None

    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {}
        if self.metrics is None:
            self.metrics = []


@dataclass
class MonitoringConfig:
    """Monitoring daemon configuration."""
    check_interval: int = 300
    max_retries: int = 3
    retry_delay: int = 5


@dataclass
class AlertsConfig:
    """Alerts configuration."""
    # Direct email (SMTP or SES)
    email_enabled: bool = False
    email: Optional[str] = None                    # Recipient email(s)
    email_from: Optional[str] = "monitoring@example.com"  # Sender email
    smtp_host: Optional[str] = None               # SMTP server
    smtp_port: int = 587                          # SMTP port (587=TLS, 465=SSL)
    smtp_user: Optional[str] = None               # SMTP username
    smtp_password: Optional[str] = None           # SMTP password
    smtp_tls: bool = True                         # Use TLS encryption

    # SNS (legacy method, for SNS-to-email)
    sns_enabled: bool = False
    sns_topic_arn: Optional[str] = None


@dataclass
class FailoverConfig:
    """Failover configuration."""
    enabled: bool = False
    secondary_region: Optional[str] = None
    manual_only: bool = True


@dataclass
class StateConfig:
    """State storage configuration."""
    type: str = 'file'
    file_path: str = '/tmp/monitoring-state.json'


@dataclass
class CloudFormationConfig:
    """CloudFormation discovery configuration."""
    enabled: bool = True
    stack_prefix: str = 'uat-'
    stack_prefixes: list = None  # Multiple prefixes (overrides stack_prefix)
    resource_types: Dict[str, str] = None

    def __post_init__(self):
        # Support both single prefix and multiple prefixes
        if self.stack_prefixes is None:
            self.stack_prefixes = [self.stack_prefix]
        elif isinstance(self.stack_prefixes, str):
            # If string with commas, split it
            self.stack_prefixes = [p.strip() for p in self.stack_prefixes.split(',')]
        elif not isinstance(self.stack_prefixes, list):
            # If not list or string, convert to list
            self.stack_prefixes = [str(self.stack_prefixes)]

        if self.resource_types is None:
            self.resource_types = {
                'lambda': 'AWS::Lambda::Function',
                'ec2': 'AWS::EC2::Instance',
                's3': 'AWS::S3::Bucket',
                'sqs': 'AWS::SQS::Queue',
                'sns': 'AWS::SNS::Topic',
                'emr': 'AWS::EMR::Cluster',
                'rds': 'AWS::RDS::DBInstance',
                'asg': 'AWS::AutoScaling::AutoScalingGroup',
                'cfn': 'AWS::CloudFormation::Stack',
                'ssm': 'AWS::SSM::Document',
                'iam': 'AWS::IAM::Role',
                'elb': 'AWS::ElasticLoadBalancingV2::LoadBalancer',
                'kms': 'AWS::KMS::Key',
                'transfer': 'AWS::Transfer::Server',
            }


class ConfigLoader:
    """Load and validate monitoring configuration."""

    @staticmethod
    def load(config_path: str) -> 'Config':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml file

        Returns:
            Validated Config object
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}

        return ConfigLoader._parse_config(data)

    @staticmethod
    def _parse_config(data: Dict[str, Any]) -> 'Config':
        """Parse configuration data into typed objects."""
        aws_data = data.get('aws', {})
        monitoring_data = data.get('monitoring', {})
        alerts_data = data.get('alerts', {})
        failover_data = data.get('failover', {})
        state_data = data.get('state', {})
        cf_data = data.get('cloudformation', {})
        services_data = data.get('services', {})

        return Config(
            aws=AWSConfig(
                primary_region=aws_data.get('primary_region', 'us-east-1'),
                secondary_region=aws_data.get('secondary_region'),
                profile=aws_data.get('profile'),
                localstack=aws_data.get('localstack', False)
            ),
            monitoring=MonitoringConfig(
                check_interval=monitoring_data.get('check_interval', 300),
                max_retries=monitoring_data.get('max_retries', 3),
                retry_delay=monitoring_data.get('retry_delay', 5)
            ),
            alerts=AlertsConfig(
                # Direct email settings
                email_enabled=alerts_data.get('email_enabled', False),
                email=alerts_data.get('email'),
                email_from=alerts_data.get('email_from', 'monitoring@example.com'),
                smtp_host=alerts_data.get('smtp_host'),
                smtp_port=alerts_data.get('smtp_port', 587),
                smtp_user=alerts_data.get('smtp_user'),
                smtp_password=alerts_data.get('smtp_password'),
                smtp_tls=alerts_data.get('smtp_tls', True),
                # SNS settings (legacy)
                sns_topic_arn=alerts_data.get('sns_topic_arn'),
                sns_enabled=alerts_data.get('sns_enabled', False)
            ),
            failover=FailoverConfig(
                enabled=failover_data.get('enabled', False),
                secondary_region=failover_data.get('secondary_region'),
                manual_only=failover_data.get('manual_only', True)
            ),
            state=StateConfig(
                type=state_data.get('type', 'file'),
                file_path=state_data.get('file_path', '/tmp/monitoring-state.json')
            ),
            cloudformation=CloudFormationConfig(
                enabled=cf_data.get('enabled', True),
                stack_prefix=cf_data.get('stack_prefix', 'uat-')
            ),
            services=services_data
        )


@dataclass
class Config:
    """Complete monitoring configuration."""
    aws: AWSConfig
    monitoring: MonitoringConfig
    alerts: AlertsConfig
    failover: FailoverConfig
    state: StateConfig
    cloudformation: CloudFormationConfig
    services: Dict[str, Dict[str, Any]]

    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service."""
        service_data = self.services.get(service_name, {})
        return ServiceConfig(
            enabled=service_data.get('enabled', False),
            thresholds=service_data.get('thresholds', {}),
            metrics=service_data.get('metrics', [])
        )
