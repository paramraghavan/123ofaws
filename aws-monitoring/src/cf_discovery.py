"""
CloudFormation resource discovery.
Discovers AWS resources from CloudFormation stacks by stack name prefix.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from utils.logger import get_logger
from utils.aws_session import AWSSessionManager

logger = get_logger(__name__)


@dataclass
class DiscoveredResource:
    """Represents a discovered AWS resource."""
    resource_type: str  # e.g., 'Lambda', 'EC2', 'S3'
    service_name: str   # e.g., 'lambda', 'ec2', 's3'
    logical_id: str     # CloudFormation logical ID
    physical_id: str    # Actual AWS resource ID/ARN
    stack_name: str     # Source CloudFormation stack
    region: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CloudFormationDiscovery:
    """Discover AWS resources from CloudFormation stacks."""

    # Mapping of CloudFormation resource types to service names
    CF_TYPE_MAPPING = {
        'AWS::Lambda::Function': 'lambda',
        'AWS::EC2::Instance': 'ec2',
        'AWS::S3::Bucket': 's3',
        'AWS::SQS::Queue': 'sqs',
        'AWS::SNS::Topic': 'sns',
        'AWS::EMR::Cluster': 'emr',
        'AWS::AutoScaling::AutoScalingGroup': 'asg',
        'AWS::CloudFormation::Stack': 'cfn',
        'AWS::SSM::Document': 'ssm',
        'AWS::IAM::Role': 'iam',
        'AWS::ElasticLoadBalancingV2::LoadBalancer': 'elbv2',
        'AWS::KMS::Key': 'kms',
        'AWS::Transfer::Server': 'transfer',
    }

    def __init__(self, session_manager: AWSSessionManager):
        """
        Initialize CloudFormation discovery.

        Args:
            session_manager: AWSSessionManager instance
        """
        self.session_manager = session_manager
        self.cf_client = session_manager.get_client('cloudformation')
        self.region = session_manager.region

    def discover_resources(
        self,
        stack_prefix: str,
        enabled_services: List[str]
    ) -> Dict[str, List[DiscoveredResource]]:
        """
        Discover resources from CloudFormation stacks matching prefix.

        Args:
            stack_prefix: Stack name prefix filter (e.g., 'uat-top')
            enabled_services: List of services to monitor (e.g., ['lambda', 'ec2'])

        Returns:
            Dictionary mapping service names to lists of discovered resources
        """
        logger.info(f"Discovering resources with stack prefix: {stack_prefix}")

        # Get all stacks
        stacks = self._get_stacks_by_prefix(stack_prefix)
        logger.info(f"Found {len(stacks)} stacks matching prefix '{stack_prefix}'")

        # Extract resources from stacks
        resources_by_service = {}
        for service in enabled_services:
            resources_by_service[service] = []

        for stack_name in stacks:
            try:
                stack_resources = self._get_stack_resources(stack_name)
                for resource in stack_resources:
                    service = resource.service_name
                    if service in enabled_services:
                        if service not in resources_by_service:
                            resources_by_service[service] = []
                        resources_by_service[service].append(resource)
                        logger.debug(
                            f"Discovered {resource.resource_type} ({resource.physical_id}) "
                            f"from stack {stack_name}"
                        )
            except Exception as e:
                logger.error(f"Error processing stack {stack_name}: {e}")

        # Log summary
        for service, resources in resources_by_service.items():
            logger.info(f"Found {len(resources)} {service} resources")

        return resources_by_service

    def _get_stacks_by_prefix(self, prefix: str) -> List[str]:
        """
        Get all stack names matching prefix.

        Args:
            prefix: Stack name prefix filter

        Returns:
            List of stack names
        """
        stack_names = []
        paginator = self.cf_client.get_paginator('list_stacks')

        try:
            for page in paginator.paginate(
                StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
            ):
                for stack in page.get('StackSummaries', []):
                    stack_name = stack['StackName']
                    if stack_name.startswith(prefix):
                        stack_names.append(stack_name)
        except Exception as e:
            logger.error(f"Error listing CloudFormation stacks: {e}")

        return stack_names

    def _get_stack_resources(self, stack_name: str) -> List[DiscoveredResource]:
        """
        Get resources from a specific CloudFormation stack.

        Args:
            stack_name: Name of the CloudFormation stack

        Returns:
            List of discovered resources
        """
        resources = []
        paginator = self.cf_client.get_paginator('list_stack_resources')

        try:
            for page in paginator.paginate(StackName=stack_name):
                for resource in page.get('StackResourceSummaries', []):
                    cf_type = resource.get('ResourceType')
                    logical_id = resource.get('LogicalResourceId')
                    physical_id = resource.get('PhysicalResourceId')

                    # Skip if not a resource we monitor
                    if cf_type not in self.CF_TYPE_MAPPING:
                        continue

                    # Skip if resource creation failed
                    if resource.get('ResourceStatus') in [
                        'CREATE_FAILED',
                        'DELETE_COMPLETE',
                        'DELETE_FAILED'
                    ]:
                        continue

                    service_name = self.CF_TYPE_MAPPING[cf_type]
                    discovered = DiscoveredResource(
                        resource_type=cf_type,
                        service_name=service_name,
                        logical_id=logical_id,
                        physical_id=physical_id,
                        stack_name=stack_name,
                        region=self.region,
                        metadata={
                            'resource_status': resource.get('ResourceStatus'),
                            'last_updated': resource.get('LastUpdatedTimestamp', '').isoformat()
                            if resource.get('LastUpdatedTimestamp') else None
                        }
                    )
                    resources.append(discovered)

        except Exception as e:
            logger.error(f"Error getting resources from stack {stack_name}: {e}")

        return resources

    def validate_stack_access(self, stack_prefix: str) -> bool:
        """
        Validate that we can access CloudFormation stacks.

        Args:
            stack_prefix: Stack name prefix to validate

        Returns:
            True if we have access, False otherwise
        """
        try:
            stacks = self._get_stacks_by_prefix(stack_prefix)
            logger.info(f"CloudFormation access validated: {len(stacks)} stacks found")
            return True
        except Exception as e:
            logger.error(f"CloudFormation access validation failed: {e}")
            return False
