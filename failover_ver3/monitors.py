"""
Resource Monitors
Monitors for different AWS and non-AWS resources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging
from datetime import datetime


class BaseMonitor(ABC):
    """Abstract base class for resource monitors"""

    def __init__(self, tag_name: str = None):
        self.tag_name = tag_name
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def check_status(self) -> List[Dict[str, Any]]:
        """Check status of resources. Returns list of status dictionaries"""
        pass


class EC2Monitor(BaseMonitor):
    """Monitor EC2 instances"""

    def __init__(self, session, tag_name: str):
        super().__init__(tag_name)
        self.ec2 = session.client('ec2')
        self.session = session

    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []

        # Get instances with matching tag
        filters = [{'Name': f'tag:Name', 'Values': [self.tag_name]}]

        response = self.ec2.describe_instances(Filters=filters)

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                state = instance['State']['Name']

                # Get instance name from tags
                instance_name = self.tag_name
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        break

                status_info = {
                    'resource_id': instance_id,
                    'tag_name': instance_name,
                    'status': state,
                    'instance_type': instance['InstanceType'],
                    'availability_zone': instance['Placement']['AvailabilityZone'],
                    'launch_time': instance.get('LaunchTime', datetime.now()).isoformat(),
                    'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                    'public_ip': instance.get('PublicIpAddress', 'N/A'),
                    'timestamp': datetime.now().isoformat()
                }

                statuses.append(status_info)

        return statuses


class EMRMonitor(BaseMonitor):
    """Monitor EMR clusters"""

    def __init__(self, session, tag_name: str):
        super().__init__(tag_name)
        self.emr = session.client('emr')
        self.session = session

    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []

        # List all clusters
        response = self.emr.list_clusters(
            ClusterStates=['STARTING', 'BOOTSTRAPPING', 'RUNNING',
                           'WAITING', 'TERMINATING', 'TERMINATED', 'TERMINATED_WITH_ERRORS']
        )

        for cluster in response['Clusters']:
            cluster_id = cluster['Id']

            # Get cluster details
            cluster_detail = self.emr.describe_cluster(ClusterId=cluster_id)['Cluster']

            # Check if cluster has matching tag
            tags = {tag['Key']: tag['Value'] for tag in cluster_detail.get('Tags', [])}

            if tags.get('Name') == self.tag_name:
                status_info = {
                    'resource_id': cluster_id,
                    'tag_name': cluster_detail['Name'],
                    'status': cluster_detail['Status']['State'],
                    'cluster_name': cluster_detail['Name'],
                    'release_label': cluster_detail.get('ReleaseLabel', 'N/A'),
                    'master_instance_type': cluster_detail.get('MasterPublicDnsName', 'N/A'),
                    'timestamp': datetime.now().isoformat()
                }

                statuses.append(status_info)

        return statuses


class LambdaMonitor(BaseMonitor):
    """Monitor Lambda functions"""

    def __init__(self, session, tag_name: str):
        super().__init__(tag_name)
        self.lambda_client = session.client('lambda')
        self.session = session

    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []

        # List all functions
        paginator = self.lambda_client.get_paginator('list_functions')

        for page in paginator.paginate():
            for function in page['Functions']:
                function_name = function['FunctionName']

                # Get function tags
                try:
                    tags_response = self.lambda_client.list_tags(
                        Resource=function['FunctionArn']
                    )
                    tags = tags_response.get('Tags', {})

                    if tags.get('Name') == self.tag_name:
                        # Get function configuration
                        status_info = {
                            'resource_id': function['FunctionArn'],
                            'tag_name': function_name,
                            'status': function['State'],
                            'runtime': function['Runtime'],
                            'memory': function['MemorySize'],
                            'timeout': function['Timeout'],
                            'last_modified': function['LastModified'],
                            'timestamp': datetime.now().isoformat()
                        }

                        statuses.append(status_info)

                except Exception as e:
                    self.logger.warning(f"Error checking Lambda {function_name}: {e}")

        return statuses


class AutoScalingMonitor(BaseMonitor):
    """Monitor Auto Scaling Groups"""

    def __init__(self, session, tag_name: str):
        super().__init__(tag_name)
        self.autoscaling = session.client('autoscaling')
        self.session = session

    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []

        # Describe all auto scaling groups
        paginator = self.autoscaling.get_paginator('describe_auto_scaling_groups')

        for page in paginator.paginate():
            for asg in page['AutoScalingGroups']:
                asg_name = asg['AutoScalingGroupName']

                # Check tags
                tags = {tag['Key']: tag['Value'] for tag in asg.get('Tags', [])}

                if tags.get('Name') == self.tag_name:
                    # Determine status based on instances and capacity
                    desired = asg['DesiredCapacity']
                    current = len(asg['Instances'])
                    healthy = len([i for i in asg['Instances'] if i['HealthStatus'] == 'Healthy'])

                    if current == 0:
                        status = 'stopped'
                    elif healthy < desired:
                        status = 'degraded'
                    else:
                        status = 'running'

                    status_info = {
                        'resource_id': asg_name,
                        'tag_name': asg_name,
                        'status': status,
                        'desired_capacity': desired,
                        'current_capacity': current,
                        'healthy_instances': healthy,
                        'min_size': asg['MinSize'],
                        'max_size': asg['MaxSize'],
                        'timestamp': datetime.now().isoformat()
                    }

                    statuses.append(status_info)

        return statuses


class SnowflakeMonitor(BaseMonitor):
    """Monitor Snowflake instances (example non-AWS service)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.enabled = config.get('enabled', False)

    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []

        if not self.enabled:
            return statuses

        try:
            # Placeholder for Snowflake connection check
            # In production, would use snowflake-connector-python

            account = self.config.get('account', 'N/A')

            status_info = {
                'resource_id': f'snowflake_{account}',
                'tag_name': account,
                'status': 'running',  # Would check actual connection
                'account': account,
                'timestamp': datetime.now().isoformat()
            }

            statuses.append(status_info)

        except Exception as e:
            self.logger.error(f"Error checking Snowflake: {e}")
            statuses.append({
                'resource_id': 'snowflake',
                'tag_name': 'snowflake',
                'status': 'DOWN',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

        return statuses


class TokenMonitor(BaseMonitor):
    """Monitor token validity (example non-AWS service)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.enabled = config.get('enabled', False)

    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []

        if not self.enabled:
            return statuses

        try:
            # Check token validity
            # This is a placeholder - in production would validate actual tokens
            token_name = self.config.get('name', 'api_token')

            # Example: check if token is expired
            is_valid = True  # Would perform actual validation

            status_info = {
                'resource_id': token_name,
                'tag_name': token_name,
                'status': 'VALID' if is_valid else 'INVALID',
                'token_type': self.config.get('type', 'bearer'),
                'timestamp': datetime.now().isoformat()
            }

            statuses.append(status_info)

        except Exception as e:
            self.logger.error(f"Error checking token: {e}")
            statuses.append({
                'resource_id': 'token',
                'tag_name': 'token',
                'status': 'INVALID',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

        return statuses