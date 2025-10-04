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
                cluster_status = cluster_detail['Status']['State']

                # Check for scaling issues if cluster is running
                scaling_issues = []
                if cluster_status in ['RUNNING', 'WAITING']:
                    scaling_issues = self._check_scaling_issues(cluster_id, cluster_detail)

                # Determine overall status
                if scaling_issues:
                    overall_status = 'SCALING_ISSUE'
                else:
                    overall_status = cluster_status

                status_info = {
                    'resource_id': cluster_id,
                    'tag_name': cluster_detail['Name'],
                    'status': overall_status,
                    'cluster_state': cluster_status,
                    'cluster_name': cluster_detail['Name'],
                    'release_label': cluster_detail.get('ReleaseLabel', 'N/A'),
                    'master_dns': cluster_detail.get('MasterPublicDnsName', 'N/A'),
                    'scaling_issues': scaling_issues,
                    'timestamp': datetime.now().isoformat()
                }

                statuses.append(status_info)

        return statuses

    def _check_scaling_issues(self, cluster_id: str, cluster_detail: Dict) -> List[str]:
        """Check for EMR scaling issues"""
        issues = []

        try:
            # Check instance fleets first (newer approach)
            try:
                fleets_response = self.emr.list_instance_fleets(ClusterId=cluster_id)

                if fleets_response.get('InstanceFleets'):
                    for fleet in fleets_response['InstanceFleets']:
                        fleet_type = fleet['InstanceFleetType']

                        # Check on-demand capacity
                        target_on_demand = fleet.get('TargetOnDemandCapacity', 0)
                        provisioned_on_demand = fleet.get('ProvisionedOnDemandCapacity', 0)

                        if target_on_demand > 0 and provisioned_on_demand < target_on_demand:
                            issues.append(
                                f"{fleet_type} fleet: On-Demand capacity mismatch "
                                f"(Target: {target_on_demand}, Provisioned: {provisioned_on_demand})"
                            )

                        # Check spot capacity
                        target_spot = fleet.get('TargetSpotCapacity', 0)
                        provisioned_spot = fleet.get('ProvisionedSpotCapacity', 0)

                        if target_spot > 0 and provisioned_spot < target_spot:
                            issues.append(
                                f"{fleet_type} fleet: Spot capacity mismatch "
                                f"(Target: {target_spot}, Provisioned: {provisioned_spot})"
                            )

                        # Check for fleet status
                        fleet_status = fleet.get('Status', {}).get('State')
                        if fleet_status in ['RESIZING', 'SUSPENDED']:
                            issues.append(f"{fleet_type} fleet in {fleet_status} state")

                    return issues
            except:
                pass  # Fall through to instance groups check

            # Check instance groups (older approach)
            groups_response = self.emr.list_instance_groups(ClusterId=cluster_id)

            for group in groups_response['InstanceGroups']:
                group_type = group['InstanceGroupType']
                group_name = group.get('Name', group_type)

                # Check capacity mismatch
                requested = group['RequestedInstanceCount']
                running = group['RunningInstanceCount']

                if requested > running:
                    issues.append(
                        f"{group_name} ({group_type}): Instance count mismatch "
                        f"(Requested: {requested}, Running: {running})"
                    )

                # Check group status
                group_status = group['Status']['State']
                if group_status in ['RESIZING', 'ARRESTED', 'SHUTTING_DOWN']:
                    issues.append(f"{group_name} ({group_type}) in {group_status} state")

                # Check for spot instance interruptions
                if group['Market'] == 'SPOT':
                    # Check if spot instances are being terminated
                    terminated = len([i for i in group.get('Instances', [])
                                      if i.get('Status', {}).get('State') == 'TERMINATED'])
                    if terminated > 0:
                        issues.append(
                            f"{group_name} ({group_type}): {terminated} spot instances terminated"
                        )

            # Check for autoscaling issues
            try:
                for group in groups_response['InstanceGroups']:
                    if group.get('AutoScalingPolicy'):
                        policy_status = group['AutoScalingPolicy'].get('Status', {}).get('State')
                        if policy_status in ['FAILED', 'DETACHING']:
                            issues.append(
                                f"{group.get('Name', group['InstanceGroupType'])} "
                                f"autoscaling policy in {policy_status} state"
                            )
            except Exception as e:
                self.logger.debug(f"Could not check autoscaling policies: {e}")

            # Check cluster state reason for capacity issues
            state_change_reason = cluster_detail.get('Status', {}).get('StateChangeReason', {})
            if state_change_reason:
                code = state_change_reason.get('Code', '')
                message = state_change_reason.get('Message', '')

                if 'INSTANCE_FAILURE' in code or 'INTERNAL_ERROR' in code:
                    issues.append(f"Cluster issue: {message}")

        except Exception as e:
            self.logger.error(f"Error checking scaling for cluster {cluster_id}: {e}")
            issues.append(f"Error checking scaling: {str(e)}")

        return issues


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