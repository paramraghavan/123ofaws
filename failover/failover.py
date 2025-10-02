import boto3
import json
import logging
from datetime import datetime
from typing import List, Dict
import time
from config import Config


class AWSFailoverManager:
    def __init__(self, profile_name: str = None):
        """Initialize AWS Failover Manager with specified profile"""
        self.profile_name = profile_name or Config.AWS_PROFILE
        self.session = boto3.Session(profile_name=self.profile_name)
        self.ec2_client = self.session.client('ec2', region_name=Config.AWS_REGION)
        self.emr_client = self.session.client('emr', region_name=Config.AWS_REGION)

        # Setup logging
        self.setup_logging()
        self.logger.info(f"Initialized AWS Failover Manager with profile: {self.profile_name}")

    def setup_logging(self):
        """Configure logging to file and console"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def detect_ec2_instances(self, tags: Dict = None) -> List[Dict]:
        """Detect EC2 instances based on tags or get all instances"""
        self.logger.info("Detecting EC2 instances...")

        filters = []
        if tags:
            for key, value in tags.items():
                filters.append({'Name': f'tag:{key}', 'Values': [value]})

        try:
            if filters:
                response = self.ec2_client.describe_instances(Filters=filters)
            else:
                response = self.ec2_client.describe_instances()

            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_info = {
                        'instance_id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'instance_type': instance['InstanceType'],
                        'launch_time': str(instance['LaunchTime']),
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    }
                    instances.append(instance_info)
                    self.logger.info(f"Found EC2: {instance_info['instance_id']} - State: {instance_info['state']}")

            return instances
        except Exception as e:
            self.logger.error(f"Error detecting EC2 instances: {str(e)}")
            return []

    def detect_emr_clusters(self, states: List[str] = None) -> List[Dict]:
        """Detect EMR clusters based on states"""
        self.logger.info("Detecting EMR clusters...")

        if states is None:
            states = ['RUNNING', 'WAITING', 'STARTING']

        try:
            response = self.emr_client.list_clusters(ClusterStates=states)

            clusters = []
            for cluster in response.get('Clusters', []):
                cluster_detail = self.emr_client.describe_cluster(ClusterId=cluster['Id'])['Cluster']

                cluster_info = {
                    'cluster_id': cluster['Id'],
                    'name': cluster['Name'],
                    'state': cluster['Status']['State'],
                    'created_time': str(cluster_detail['Status']['Timeline'].get('CreationDateTime', '')),
                    'instance_type': cluster_detail.get('InstanceCollectionType', 'N/A')
                }
                clusters.append(cluster_info)
                self.logger.info(f"Found EMR: {cluster_info['cluster_id']} - State: {cluster_info['state']}")

            return clusters
        except Exception as e:
            self.logger.error(f"Error detecting EMR clusters: {str(e)}")
            return []

    def log_status(self, instances: List[Dict], clusters: List[Dict]):
        """Log comprehensive status of all resources"""
        status_log = {
            'timestamp': datetime.now().isoformat(),
            'ec2_instances': instances,
            'emr_clusters': clusters,
            'summary': {
                'total_ec2': len(instances),
                'total_emr': len(clusters),
                'ec2_running': sum(1 for i in instances if i['state'] == 'running'),
                'emr_active': sum(1 for c in clusters if c['state'] in ['RUNNING', 'WAITING'])
            }
        }

        # Write to JSON log file
        try:
            with open(Config.STATUS_LOG_FILE, 'a') as f:
                f.write(json.dumps(status_log) + '\n')
            self.logger.info(f"Status logged: {status_log['summary']}")
        except Exception as e:
            self.logger.error(f"Error writing status log: {str(e)}")

        return status_log

    def restart_ec2_instance(self, instance_id: str) -> bool:
        """Restart a specific EC2 instance"""
        self.logger.info(f"Restarting EC2 instance: {instance_id}")

        try:
            # Stop instance
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            self.logger.info(f"Stopping instance {instance_id}...")

            # Wait for instance to stop
            waiter = self.ec2_client.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[instance_id])
            self.logger.info(f"Instance {instance_id} stopped")

            # Start instance
            self.ec2_client.start_instances(InstanceIds=[instance_id])
            self.logger.info(f"Starting instance {instance_id}...")

            # Wait for instance to start
            waiter = self.ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            self.logger.info(f"Instance {instance_id} restarted successfully")

            return True
        except Exception as e:
            self.logger.error(f"Error restarting instance {instance_id}: {str(e)}")
            return False

    def restart_emr_cluster(self, cluster_id: str) -> str:
        """Restart EMR cluster by terminating and recreating with same configuration"""
        self.logger.info(f"Restarting EMR cluster: {cluster_id}")
        return self.recreate_emr_cluster(cluster_id)

    def recreate_emr_cluster(self, cluster_id: str) -> str:
        """Terminate and recreate EMR cluster with complete configuration"""
        self.logger.info(f"Recreating EMR cluster: {cluster_id}")

        try:
            # Get complete cluster configuration
            cluster_detail = self.emr_client.describe_cluster(ClusterId=cluster_id)['Cluster']

            # List all instance groups (Master, Core, Task)
            instance_groups_response = self.emr_client.list_instance_groups(ClusterId=cluster_id)
            instance_groups = instance_groups_response.get('InstanceGroups', [])

            # Log current configuration
            self.logger.info(f"Cluster config - Release: {cluster_detail['ReleaseLabel']}")
            for ig in instance_groups:
                self.logger.info(f"  {ig['InstanceGroupType']}: {ig['InstanceType']} "
                                 f"({ig['RequestedInstanceCount']} instances, {ig['Market']})")

            # Terminate existing cluster
            self.emr_client.terminate_job_flows(JobFlowIds=[cluster_id])
            self.logger.info(f"Terminating cluster {cluster_id}...")

            # Wait for termination
            time.sleep(30)

            # Build instance groups configuration with full details
            new_instance_groups = []
            for ig in instance_groups:
                instance_group_config = {
                    'Name': ig['Name'],
                    'InstanceRole': ig['InstanceGroupType'],
                    'InstanceType': ig['InstanceType'],
                    'InstanceCount': ig['RequestedInstanceCount'],
                    'Market': ig['Market']  # ON_DEMAND or SPOT
                }

                # Add spot-specific configuration if applicable
                if ig['Market'] == 'SPOT':
                    if 'BidPrice' in ig:
                        instance_group_config['BidPrice'] = ig['BidPrice']
                    # Add spot timeout and provisioning specification
                    if 'Configurations' in ig:
                        instance_group_config['Configurations'] = ig['Configurations']

                # Add EBS configuration if present
                if 'EbsBlockDevices' in ig and ig['EbsBlockDevices']:
                    ebs_config = {
                        'EbsBlockDeviceConfigs': []
                    }
                    for ebs in ig['EbsBlockDevices']:
                        volume_spec = ebs['VolumeSpecification']
                        ebs_config['EbsBlockDeviceConfigs'].append({
                            'VolumeSpecification': {
                                'VolumeType': volume_spec['VolumeType'],
                                'SizeInGB': volume_spec['SizeInGB']
                            },
                            'VolumesPerInstance': 1
                        })
                    instance_group_config['EbsConfiguration'] = ebs_config

                # Add autoscaling policy if present
                if 'AutoScalingPolicy' in ig:
                    instance_group_config['AutoScalingPolicy'] = ig['AutoScalingPolicy']

                new_instance_groups.append(instance_group_config)

                self.logger.info(f"Configured {ig['InstanceGroupType']}: {ig['InstanceType']} "
                                 f"x{ig['RequestedInstanceCount']} ({ig['Market']})")

            # Build complete cluster configuration
            new_cluster_config = {
                'Name': cluster_detail['Name'] + '_recreated_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
                'ReleaseLabel': cluster_detail['ReleaseLabel'],
                'Instances': {
                    'InstanceGroups': new_instance_groups,
                    'KeepJobFlowAliveWhenNoSteps': True,
                    'TerminationProtected': False,
                },
                'Applications': [{'Name': app['Name']} for app in cluster_detail.get('Applications', [])],
                'VisibleToAllUsers': cluster_detail.get('VisibleToAllUsers', True),
                'JobFlowRole': cluster_detail['Ec2InstanceAttributes']['IamInstanceProfile'].split('/')[-1],
                'ServiceRole': cluster_detail['ServiceRole']
            }

            # Add EC2 attributes if present
            if 'Ec2InstanceAttributes' in cluster_detail:
                ec2_attrs = cluster_detail['Ec2InstanceAttributes']
                instances_config = new_cluster_config['Instances']

                if 'Ec2KeyName' in ec2_attrs:
                    instances_config['Ec2KeyName'] = ec2_attrs['Ec2KeyName']
                if 'Ec2SubnetId' in ec2_attrs:
                    instances_config['Ec2SubnetId'] = ec2_attrs['Ec2SubnetId']
                if 'EmrManagedMasterSecurityGroup' in ec2_attrs:
                    instances_config['EmrManagedMasterSecurityGroup'] = ec2_attrs['EmrManagedMasterSecurityGroup']
                if 'EmrManagedSlaveSecurityGroup' in ec2_attrs:
                    instances_config['EmrManagedSlaveSecurityGroup'] = ec2_attrs['EmrManagedSlaveSecurityGroup']
                if 'AdditionalMasterSecurityGroups' in ec2_attrs:
                    instances_config['AdditionalMasterSecurityGroups'] = ec2_attrs['AdditionalMasterSecurityGroups']
                if 'AdditionalSlaveSecurityGroups' in ec2_attrs:
                    instances_config['AdditionalSlaveSecurityGroups'] = ec2_attrs['AdditionalSlaveSecurityGroups']

            # Add configurations if present
            if 'Configurations' in cluster_detail:
                new_cluster_config['Configurations'] = cluster_detail['Configurations']

            # Add tags if present
            if 'Tags' in cluster_detail:
                new_cluster_config['Tags'] = cluster_detail['Tags']

            # Create new cluster
            response = self.emr_client.run_job_flow(**new_cluster_config)
            new_cluster_id = response['JobFlowId']

            self.logger.info(f"New cluster created: {new_cluster_id}")
            self.logger.info(f"  Master: {new_instance_groups[0]['InstanceType'] if new_instance_groups else 'N/A'}")
            if len(new_instance_groups) > 1:
                self.logger.info(
                    f"  Core: {new_instance_groups[1]['InstanceType']} x{new_instance_groups[1]['InstanceCount']}")
            if len(new_instance_groups) > 2:
                self.logger.info(
                    f"  Task: {new_instance_groups[2]['InstanceType']} x{new_instance_groups[2]['InstanceCount']}")

            return new_cluster_id

        except Exception as e:
            self.logger.error(f"Error recreating cluster {cluster_id}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def run_failover(self, instance_ids: List[str] = None, cluster_ids: List[str] = None,
                     restart_clusters: bool = False):
        """Execute failover process for specified resources

        Args:
            instance_ids: List of EC2 instance IDs to restart
            cluster_ids: List of EMR cluster IDs to recreate/restart
            restart_clusters: If True, use restart method; if False, use recreate method
        """
        self.logger.info("Starting failover process...")

        failover_results = {
            'timestamp': datetime.now().isoformat(),
            'ec2_results': {},
            'emr_results': {},
            'operation': 'restart' if restart_clusters else 'recreate'
        }

        # Restart EC2 instances
        if instance_ids:
            for instance_id in instance_ids:
                success = self.restart_ec2_instance(instance_id)
                failover_results['ec2_results'][instance_id] = 'SUCCESS' if success else 'FAILED'

        # Recreate or restart EMR clusters
        if cluster_ids:
            for cluster_id in cluster_ids:
                if restart_clusters:
                    new_cluster_id = self.restart_emr_cluster(cluster_id)
                else:
                    new_cluster_id = self.recreate_emr_cluster(cluster_id)
                failover_results['emr_results'][cluster_id] = new_cluster_id if new_cluster_id else 'FAILED'

        # Log failover results
        try:
            with open(Config.FAILOVER_LOG_FILE, 'a') as f:
                f.write(json.dumps(failover_results) + '\n')
        except Exception as e:
            self.logger.error(f"Error writing failover log: {str(e)}")

        self.logger.info(f"Failover completed: {failover_results}")
        return failover_results


def main():
    """Main execution function"""
    print("AWS Failover Manager Starting...")

    # Initialize manager
    manager = AWSFailoverManager()

    # Detect resources
    instances = manager.detect_ec2_instances()
    clusters = manager.detect_emr_clusters()

    # Log status
    status = manager.log_status(instances, clusters)
    print(f"\nStatus Summary:")
    print(f"EC2 Instances: {status['summary']['total_ec2']} (Running: {status['summary']['ec2_running']})")
    print(f"EMR Clusters: {status['summary']['total_emr']} (Active: {status['summary']['emr_active']})")

    # Optional: Run failover for specific resources
    # Uncomment and modify as needed

    # Example 1: Restart non-running EC2 instances
    # instance_ids = [i['instance_id'] for i in instances if i['state'] != 'running']
    # if instance_ids:
    #     manager.run_failover(instance_ids=instance_ids)

    # Example 2: Restart specific EMR clusters (terminates and recreates)
    # cluster_ids = ['j-XXXXXXXXXXXXX']
    # manager.run_failover(cluster_ids=cluster_ids, restart_clusters=True)

    # Example 3: Recreate all non-running clusters
    # cluster_ids = [c['cluster_id'] for c in clusters if c['state'] not in ['RUNNING', 'WAITING']]
    # if cluster_ids:
    #     manager.run_failover(cluster_ids=cluster_ids, restart_clusters=False)

    # EMR clusters cannot be stopped and started like EC2 instances - they can only be terminated and recreated.
    # Example 4: Full failover - restart everything that's not healthy
    # instance_ids = [i['instance_id'] for i in instances if i['state'] == 'terminated']
    # cluster_ids = [c['cluster_id'] for c in clusters if c['state'] == 'TERMINATED']
    # if instance_ids or cluster_ids:
    #     manager.run_failover(
    #         instance_ids=instance_ids,
    #         cluster_ids=cluster_ids,
    #         restart_clusters=True
    #     )


if __name__ == "__main__":
    main()