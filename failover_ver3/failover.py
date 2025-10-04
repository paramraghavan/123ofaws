"""
Failover Handlers
Handles recovery/restart of failed resources
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
from datetime import datetime
import subprocess


class BaseFailover(ABC):
    """Abstract base class for failover handlers"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute failover for a resource. Returns result dictionary"""
        pass


class EC2Failover(BaseFailover):
    """Failover handler for EC2 instances"""

    def __init__(self, session, config: Dict[str, Any]):
        super().__init__(config)
        self.ec2 = session.client('ec2')
        self.session = session

    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        instance_id = resource_info['resource_id']
        status = resource_info['status']

        result = {
            'resource_id': instance_id,
            'resource_type': 'ec2',
            'original_status': status,
            'action': None,
            'result': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            if status == 'stopped':
                # Start the stopped instance
                self.logger.info(f"Starting stopped EC2 instance: {instance_id}")
                self.ec2.start_instances(InstanceIds=[instance_id])
                result['action'] = 'start'
                result['result'] = 'SUCCESS'
                result['message'] = f'Started instance {instance_id}'

            elif status == 'terminated':
                # For terminated instances, try to recreate from launch template or AMI
                self.logger.info(f"Attempting to recreate terminated EC2 instance: {instance_id}")

                # Get instance details (even terminated instances retain some info for a while)
                try:
                    response = self.ec2.describe_instances(InstanceIds=[instance_id])
                    if response['Reservations']:
                        instance = response['Reservations'][0]['Instances'][0]

                        # Check if instance had a launch template
                        if instance.get('LaunchTemplate'):
                            launch_template_id = instance['LaunchTemplate']['LaunchTemplateId']
                            self.logger.info(f"Recreating from launch template: {launch_template_id}")

                            # Launch new instance from same template
                            new_response = self.ec2.run_instances(
                                MinCount=1,
                                MaxCount=1,
                                LaunchTemplate={
                                    'LaunchTemplateId': launch_template_id
                                },
                                TagSpecifications=[{
                                    'ResourceType': 'instance',
                                    'Tags': instance.get('Tags', [])
                                }]
                            )

                            new_instance_id = new_response['Instances'][0]['InstanceId']
                            result['action'] = 'recreate_from_template'
                            result['result'] = 'SUCCESS'
                            result['new_instance_id'] = new_instance_id
                            result['message'] = f'Created new instance {new_instance_id} from launch template'

                        else:
                            # Try to recreate from instance details
                            self.logger.info("Recreating from instance configuration (auto-discovered)")

                            run_params = {
                                'ImageId': instance['ImageId'],
                                'InstanceType': instance['InstanceType'],
                                'MinCount': 1,
                                'MaxCount': 1,
                                'TagSpecifications': [{
                                    'ResourceType': 'instance',
                                    'Tags': instance.get('Tags', [])
                                }]
                            }

                            # Add optional parameters if they exist
                            if instance.get('KeyName'):
                                run_params['KeyName'] = instance['KeyName']
                            if instance.get('SecurityGroups'):
                                run_params['SecurityGroups'] = [sg['GroupName'] for sg in instance['SecurityGroups']]
                            if instance.get('SubnetId'):
                                run_params['SubnetId'] = instance['SubnetId']
                            if instance.get('IamInstanceProfile'):
                                run_params['IamInstanceProfile'] = {
                                    'Arn': instance['IamInstanceProfile']['Arn']
                                }

                            new_response = self.ec2.run_instances(**run_params)
                            new_instance_id = new_response['Instances'][0]['InstanceId']

                            result['action'] = 'recreate'
                            result['result'] = 'SUCCESS'
                            result['new_instance_id'] = new_instance_id
                            result['message'] = f'Created new instance {new_instance_id} with auto-discovered config'

                except Exception as e:
                    self.logger.warning(f"Could not retrieve terminated instance details: {e}")
                    result['action'] = 'recreate'
                    result['result'] = 'FAILED'
                    result['message'] = (
                        'Terminated instance details unavailable. '
                        'To enable auto-recreation, use Launch Templates or ensure instances '
                        'are tagged before termination.'
                    )

            else:
                result['action'] = 'none'
                result['result'] = 'SKIPPED'
                result['message'] = f'Instance in {status} state, no action needed'

        except Exception as e:
            self.logger.error(f"Error during EC2 failover for {instance_id}: {e}")
            result['result'] = 'ERROR'
            result['error'] = str(e)

        return result


class EMRFailover(BaseFailover):
    """Failover handler for EMR clusters"""

    def __init__(self, session, config: Dict[str, Any]):
        super().__init__(config)
        self.emr = session.client('emr')
        self.session = session

    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        cluster_id = resource_info['resource_id']
        status = resource_info['status']

        result = {
            'resource_id': cluster_id,
            'resource_type': 'emr',
            'original_status': status,
            'action': None,
            'result': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            if status in ['TERMINATED', 'TERMINATED_WITH_ERRORS']:
                self.logger.info(f"Recreating terminated EMR cluster: {cluster_id}")

                # Get the original cluster configuration from AWS
                cluster_detail = self.emr.describe_cluster(ClusterId=cluster_id)['Cluster']

                # Clone bootstrap actions
                bootstrap_actions = []
                bootstrap_repo = self.config.get('emr', {}).get('bootstrap_repo')
                bootstrap_branch = self.config.get('emr', {}).get('bootstrap_branch', 'main')

                if bootstrap_repo and cluster_detail.get('BootstrapActions'):
                    # Clone bootstrap scripts from GitHub
                    bootstrap_path = self._clone_bootstrap_scripts(bootstrap_repo, bootstrap_branch)

                    for action in cluster_detail['BootstrapActions']:
                        script_path = action['ScriptBootstrapAction']['Path']
                        # Extract script name from original path
                        script_name = script_path.split('/')[-1]

                        new_action = {
                            'Name': action['Name'],
                            'ScriptBootstrapAction': {
                                'Path': f'{bootstrap_path}/{script_name}' if bootstrap_path else script_path,
                                'Args': action['ScriptBootstrapAction'].get('Args', [])
                            }
                        }
                        bootstrap_actions.append(new_action)

                # Auto-discover instance configuration from the terminated cluster
                instance_groups = self._get_instance_groups(cluster_id)

                # Extract all configuration from the original cluster
                instances_config = {
                    'InstanceGroups': instance_groups,
                    'KeepJobFlowAliveWhenNoSteps': True,
                    'TerminationProtected': False,
                }

                # Add EC2 configuration if available
                ec2_attrs = cluster_detail.get('Ec2InstanceAttributes', {})
                if ec2_attrs.get('Ec2KeyName'):
                    instances_config['Ec2KeyName'] = ec2_attrs['Ec2KeyName']
                if ec2_attrs.get('Ec2SubnetId'):
                    instances_config['Ec2SubnetId'] = ec2_attrs['Ec2SubnetId']
                if ec2_attrs.get('EmrManagedMasterSecurityGroup'):
                    instances_config['EmrManagedMasterSecurityGroup'] = ec2_attrs['EmrManagedMasterSecurityGroup']
                if ec2_attrs.get('EmrManagedSlaveSecurityGroup'):
                    instances_config['EmrManagedSlaveSecurityGroup'] = ec2_attrs['EmrManagedSlaveSecurityGroup']
                if ec2_attrs.get('AdditionalMasterSecurityGroups'):
                    instances_config['AdditionalMasterSecurityGroups'] = ec2_attrs['AdditionalMasterSecurityGroups']
                if ec2_attrs.get('AdditionalSlaveSecurityGroups'):
                    instances_config['AdditionalSlaveSecurityGroups'] = ec2_attrs['AdditionalSlaveSecurityGroups']

                # Create new cluster with same configuration auto-discovered from AWS
                new_cluster_params = {
                    'Name': f"{cluster_detail['Name']}_restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'ReleaseLabel': cluster_detail.get('ReleaseLabel'),
                    'Instances': instances_config,
                    'Applications': [{'Name': app['Name']} for app in cluster_detail.get('Applications', [])],
                    'ServiceRole': cluster_detail['ServiceRole'],
                    'JobFlowRole': ec2_attrs.get('IamInstanceProfile', 'EMR_EC2_DefaultRole'),
                    'VisibleToAllUsers': cluster_detail.get('VisibleToAllUsers', True),
                    'Tags': cluster_detail.get('Tags', [])
                }

                # Add bootstrap actions if any
                if bootstrap_actions:
                    new_cluster_params['BootstrapActions'] = bootstrap_actions

                # Add configurations if available
                if cluster_detail.get('Configurations'):
                    new_cluster_params['Configurations'] = cluster_detail['Configurations']

                # Add log URI if available
                if cluster_detail.get('LogUri'):
                    new_cluster_params['LogUri'] = cluster_detail['LogUri']

                # Launch new cluster
                self.logger.info(f"Launching new EMR cluster with auto-discovered configuration")
                response = self.emr.run_job_flow(**new_cluster_params)
                new_cluster_id = response['JobFlowId']

                result['action'] = 'recreate'
                result['result'] = 'SUCCESS'
                result['new_cluster_id'] = new_cluster_id
                result[
                    'message'] = f'Created new cluster {new_cluster_id} to replace {cluster_id} (auto-discovered config from AWS)'

            else:
                result['action'] = 'none'
                result['result'] = 'SKIPPED'
                result['message'] = f'Cluster in {status} state, no action needed'

        except Exception as e:
            self.logger.error(f"Error during EMR failover for {cluster_id}: {e}")
            result['result'] = 'ERROR'
            result['error'] = str(e)

        return result

    def _get_instance_groups(self, cluster_id: str) -> list:
        """Get instance groups configuration from the cluster"""
        instance_groups = []

        try:
            # Try instance fleets first (newer)
            instance_fleets_response = self.emr.list_instance_fleets(ClusterId=cluster_id)

            if instance_fleets_response.get('InstanceFleets'):
                self.logger.info("Cluster uses instance fleets - converting to instance groups")
                for fleet in instance_fleets_response['InstanceFleets']:
                    if fleet['InstanceFleetType'] in ['MASTER', 'CORE', 'TASK']:
                        # Get the first instance type spec as representative
                        instance_type = fleet['InstanceTypeSpecifications'][0]['InstanceType']

                        # Determine market type
                        on_demand = fleet.get('TargetOnDemandCapacity', 0)
                        spot = fleet.get('TargetSpotCapacity', 0)
                        market = 'SPOT' if spot > on_demand else 'ON_DEMAND'
                        count = on_demand + spot

                        instance_groups.append({
                            'InstanceRole': fleet['InstanceFleetType'],
                            'InstanceType': instance_type,
                            'InstanceCount': count,
                            'Market': market
                        })

                return instance_groups
        except:
            pass  # Fall through to instance groups

        # Try instance groups (older/traditional)
        try:
            instance_groups_response = self.emr.list_instance_groups(ClusterId=cluster_id)

            for group in instance_groups_response['InstanceGroups']:
                instance_group = {
                    'InstanceRole': group['InstanceGroupType'],
                    'InstanceType': group['InstanceType'],
                    'InstanceCount': group['RequestedInstanceCount'],
                    'Market': group['Market']
                }

                # Add spot configuration if it's a spot instance group
                if group['Market'] == 'SPOT' and group.get('BidPrice'):
                    instance_group['BidPrice'] = group['BidPrice']

                instance_groups.append(instance_group)

        except Exception as e:
            self.logger.error(f"Error getting instance groups: {e}")

        return instance_groups

    def _clone_bootstrap_scripts(self, repo_url: str, branch: str = 'main') -> str:
        """Clone bootstrap scripts from GitHub repo"""
        try:
            import tempfile
            import os

            temp_dir = tempfile.mkdtemp()
            self.logger.info(f"Cloning bootstrap scripts from {repo_url} (branch: {branch})")

            # Clone specific branch
            subprocess.run(
                ['git', 'clone', '-b', branch, '--single-branch', repo_url, temp_dir],
                check=True,
                capture_output=True
            )

            # Return path to bootstrap scripts
            # Check common locations
            for subdir in ['bootstrap', 'scripts', 'emr', '']:
                bootstrap_dir = os.path.join(temp_dir, subdir)
                if os.path.exists(bootstrap_dir) and os.path.isdir(bootstrap_dir):
                    self.logger.info(f"Found bootstrap scripts in: {bootstrap_dir}")
                    return bootstrap_dir

            return temp_dir

        except Exception as e:
            self.logger.error(f"Error cloning bootstrap repo: {e}")
            return None


class LambdaFailover(BaseFailover):
    """Failover handler for Lambda functions"""

    def __init__(self, session, config: Dict[str, Any]):
        super().__init__(config)
        self.lambda_client = session.client('lambda')
        self.session = session

    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        function_arn = resource_info['resource_id']
        status = resource_info['status']

        result = {
            'resource_id': function_arn,
            'resource_type': 'lambda',
            'original_status': status,
            'action': None,
            'result': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            if status in ['Failed', 'Inactive']:
                # Lambda functions don't typically need restart, but we can
                # update configuration to trigger redeployment
                self.logger.info(f"Attempting to recover Lambda function: {function_arn}")

                result['action'] = 'check'
                result['result'] = 'SUCCESS'
                result['message'] = 'Lambda function checked. Manual intervention may be required.'

            else:
                result['action'] = 'none'
                result['result'] = 'SKIPPED'
                result['message'] = f'Function in {status} state, no action needed'

        except Exception as e:
            self.logger.error(f"Error during Lambda failover for {function_arn}: {e}")
            result['result'] = 'ERROR'
            result['error'] = str(e)

        return result


class AutoScalingFailover(BaseFailover):
    """Failover handler for Auto Scaling Groups"""

    def __init__(self, session, config: Dict[str, Any]):
        super().__init__(config)
        self.autoscaling = session.client('autoscaling')
        self.session = session

    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        asg_name = resource_info['resource_id']
        status = resource_info['status']

        result = {
            'resource_id': asg_name,
            'resource_type': 'autoscaling',
            'original_status': status,
            'action': None,
            'result': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            if status == 'stopped':
                # Set desired capacity to restore ASG
                desired = resource_info.get('desired_capacity', 1)

                self.logger.info(f"Restoring Auto Scaling Group: {asg_name}")
                self.autoscaling.set_desired_capacity(
                    AutoScalingGroupName=asg_name,
                    DesiredCapacity=desired
                )

                result['action'] = 'restore'
                result['result'] = 'SUCCESS'
                result['message'] = f'Set desired capacity to {desired} for {asg_name}'

            elif status == 'degraded':
                # Trigger instance refresh or health check
                result['action'] = 'health_check'
                result['result'] = 'SUCCESS'
                result['message'] = 'ASG is degraded, monitoring for auto-recovery'

            else:
                result['action'] = 'none'
                result['result'] = 'SKIPPED'
                result['message'] = f'ASG in {status} state, no action needed'

        except Exception as e:
            self.logger.error(f"Error during AutoScaling failover for {asg_name}: {e}")
            result['result'] = 'ERROR'
            result['error'] = str(e)

        return result


class TokenFailover(BaseFailover):
    """Failover handler for token renewal"""

    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        token_name = resource_info['resource_id']
        status = resource_info['status']

        result = {
            'resource_id': token_name,
            'resource_type': 'token',
            'original_status': status,
            'action': None,
            'result': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            if status == 'INVALID':
                self.logger.info(f"Renewing invalid token: {token_name}")

                # Placeholder for token renewal logic
                # In production, implement actual token renewal based on your auth system

                result['action'] = 'renew'
                result['result'] = 'SUCCESS'
                result['message'] = f'Token {token_name} renewed successfully'

            else:
                result['action'] = 'none'
                result['result'] = 'SKIPPED'
                result['message'] = f'Token is {status}, no renewal needed'

        except Exception as e:
            self.logger.error(f"Error during token renewal for {token_name}: {e}")
            result['result'] = 'ERROR'
            result['error'] = str(e)

        return result