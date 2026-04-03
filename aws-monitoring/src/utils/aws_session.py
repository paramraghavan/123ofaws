"""
AWS session management with profile and LocalStack support.
Pattern from: cost_calculator.py
"""

import boto3
from typing import Optional
from botocore.exceptions import NoCredentialsError


class AWSSessionManager:
    """Manage AWS sessions with profile support and LocalStack compatibility."""

    def __init__(
        self,
        profile_name: Optional[str] = None,
        region: str = 'us-east-1',
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize AWS session manager.

        Args:
            profile_name: AWS profile name (optional)
            region: AWS region (default: us-east-1)
            endpoint_url: Custom endpoint URL (for LocalStack or other services)

        Raises:
            Exception: If AWS credentials cannot be found
        """
        try:
            if profile_name:
                self.session = boto3.Session(profile_name=profile_name)
            else:
                self.session = boto3.Session()

            self.region = region
            self.endpoint_url = endpoint_url

            # Test credentials are valid by getting STS identity
            sts = self.get_client('sts')
            sts.get_caller_identity()

        except NoCredentialsError as e:
            raise Exception(
                "AWS credentials not found. Please configure your credentials "
                "or specify a profile name."
            ) from e

    def get_client(self, service_name: str):
        """
        Get a boto3 client for the specified service.

        Args:
            service_name: AWS service name (e.g., 'lambda', 'ec2')

        Returns:
            Configured boto3 client
        """
        return self.session.client(
            service_name,
            region_name=self.region,
            endpoint_url=self.endpoint_url
        )

    def get_resource(self, service_name: str):
        """
        Get a boto3 resource for the specified service.

        Args:
            service_name: AWS service name (e.g., 's3')

        Returns:
            Configured boto3 resource
        """
        return self.session.resource(
            service_name,
            region_name=self.region,
            endpoint_url=self.endpoint_url
        )
