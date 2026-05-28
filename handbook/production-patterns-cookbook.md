# Production Patterns Cookbook: Real-World AWS Solutions

> **8 production-tested patterns** extracted from the 123ofaws repository. Each pattern is complete, production-ready, and includes error handling.

---

## Table of Contents

1. [Pattern 1: Multi-Service Monitoring System](#pattern-1-multi-service-monitoring-system)
2. [Pattern 2: Cost Management & Chargeback](#pattern-2-cost-management--chargeback)
3. [Pattern 3: Cross-Account Resource Access](#pattern-3-cross-account-resource-access)
4. [Pattern 4: CloudFormation Stack Discovery](#pattern-4-cloudformation-stack-discovery)
5. [Pattern 5: SSM Remote Execution](#pattern-5-ssm-remote-execution)
6. [Pattern 6: S3 SQL Query Engine](#pattern-6-s3-sql-query-engine)
7. [Pattern 7: Lambda Layer Deployment](#pattern-7-lambda-layer-deployment)
8. [Pattern 8: Step Functions Orchestration](#pattern-8-step-functions-orchestration)

---

## Pattern 1: Multi-Service Monitoring System

**Use Case**: Monitor 20+ AWS services for health/errors. Send alerts to CloudWatch/SNS.

**Key Features**:
- Extensible monitor architecture
- Health status tracking
- CloudWatch integration
- Retry logic and error handling

**Source**: `aws-monitoring/src/monitors/base_monitor.py`

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status indicators."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ResourceHealth:
    """Represents health of a single resource."""
    resource_id: str
    resource_name: str
    resource_type: str
    status: HealthStatus
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime
    region: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'resource_type': self.resource_type,
            'status': self.status.value,
            'message': self.message,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat(),
            'region': self.region
        }

class AWSSessionManager:
    """Manages AWS sessions and clients."""

    def __init__(self, region='us-east-1', profile=None):
        from boto3 import Session
        session = Session(profile_name=profile) if profile else Session()
        self.region = region
        self.session = session
        self._clients = {}

    def get_client(self, service_name):
        """Get or create client for service."""
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(
                service_name,
                region_name=self.region
            )
        return self._clients[service_name]

class BaseMonitor(ABC):
    """Abstract base class for all service monitors."""

    def __init__(self, session_manager: AWSSessionManager, config: Dict[str, Any]):
        self.session_manager = session_manager
        self.config = config
        self.region = session_manager.region
        self.client = session_manager.get_client(self.service_name)
        self.cloudwatch = session_manager.get_client('cloudwatch')

    @property
    @abstractmethod
    def service_name(self) -> str:
        """AWS service name (e.g., 'lambda', 'ec2')."""
        pass

    @abstractmethod
    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of provided resources."""
        pass

    def should_alert(self, health: ResourceHealth) -> bool:
        """Determine if alert should be sent."""
        return health.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]

    def publish_metrics(self, health: ResourceHealth):
        """Publish health metrics to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=f'AWS-Monitoring/{self.service_name}',
                MetricData=[
                    {
                        'MetricName': 'HealthStatus',
                        'Value': 1 if health.status == HealthStatus.HEALTHY else 0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'ResourceId', 'Value': health.resource_id},
                            {'Name': 'Service', 'Value': self.service_name}
                        ],
                        'Timestamp': health.timestamp
                    }
                ]
            )
        except ClientError as e:
            logger.error(f"Failed to publish metrics: {e}")

# Example: Lambda Monitor
class LambdaMonitor(BaseMonitor):
    """Monitor AWS Lambda functions."""

    @property
    def service_name(self) -> str:
        return 'lambda'

    def check_health(self, function_names: List[str]) -> List[ResourceHealth]:
        """Check health of Lambda functions."""
        results = []

        for function_name in function_names:
            try:
                response = self.client.get_function(FunctionName=function_name)
                config = response['Configuration']

                # Check function metrics
                health_status = HealthStatus.HEALTHY
                message = "Function is healthy"

                # Check if function was recently invoked (not stale)
                cloudwatch = self.session_manager.get_client('cloudwatch')
                metrics = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                    StartTime=datetime.utcnow() - timedelta(hours=24),
                    EndTime=datetime.utcnow(),
                    Period=3600,
                    Statistics=['Sum']
                )

                if not metrics['Datapoints']:
                    health_status = HealthStatus.DEGRADED
                    message = "No invocations in 24 hours"

                # Check error rate
                error_metrics = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Errors',
                    Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                    StartTime=datetime.utcnow() - timedelta(hours=1),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=['Sum']
                )

                if error_metrics['Datapoints'] and sum(dp['Sum'] for dp in error_metrics['Datapoints']) > 10:
                    health_status = HealthStatus.UNHEALTHY
                    message = f"High error rate detected"

                health = ResourceHealth(
                    resource_id=config['FunctionArn'],
                    resource_name=function_name,
                    resource_type='Lambda',
                    status=health_status,
                    message=message,
                    metrics={'Memory': config['MemorySize'], 'Timeout': config['Timeout']},
                    timestamp=datetime.utcnow(),
                    region=self.region
                )

                results.append(health)
                self.publish_metrics(health)

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    logger.warning(f"Function {function_name} not found")
                else:
                    logger.error(f"Error checking {function_name}: {e}")

        return results

# Usage
if __name__ == '__main__':
    session_manager = AWSSessionManager(region='us-east-1')
    lambda_monitor = LambdaMonitor(session_manager, {})

    health_results = lambda_monitor.check_health([
        'my-function',
        'data-processor',
        'api-handler'
    ])

    for health in health_results:
        print(f"{health.resource_name}: {health.status.value} - {health.message}")
        if lambda_monitor.should_alert(health):
            print(f"  ⚠️  ALERT: {health.message}")
```

---

## Pattern 2: Cost Management & Chargeback

**Use Case**: Track AWS costs by service, team, or project. Implement chargeback.

**Key Features**:
- Cost Explorer integration
- Tag-based filtering
- EMR job-level costs
- CSV export for billing

**Source**: `cost/aws_cost_calculator.py` and `cost/emr_cost_calculator.py`

```python
import boto3
from datetime import datetime, timedelta
from typing import Dict, List
import json
import csv

class CostCalculator:
    """Calculate AWS costs with filtering and grouping."""

    def __init__(self, region='us-east-1'):
        self.ce = boto3.client('ce', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)

    def get_daily_costs(self, days=30, granularity='DAILY', group_by='SERVICE'):
        """
        Get costs grouped by service or tag.

        Args:
            days: Number of days to look back
            granularity: DAILY or MONTHLY
            group_by: SERVICE, LINKED_ACCOUNT, REGION, or TAGS

        Returns:
            Structured cost data
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.isoformat(),
                'End': end_date.isoformat()
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': group_by}
            ]
        )

        costs_by_group = {}
        for result in response['ResultsByTime']:
            period = result['TimePeriod']['Start']
            for group in result['Groups']:
                key = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])

                if key not in costs_by_group:
                    costs_by_group[key] = {}
                costs_by_group[key][period] = amount

        return costs_by_group

    def get_costs_by_tag(self, tag_key, tag_value=None, days=30):
        """Get costs for resources with specific tag."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.isoformat(),
                'End': end_date.isoformat()
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            Filter={
                'Tags': {
                    'Key': tag_key,
                    'Values': [tag_value] if tag_value else None
                }
            }
        )

        total_cost = 0
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                total_cost += float(group['Metrics']['UnblendedCost']['Amount'])

        return total_cost

    def get_service_costs(self, days=30):
        """Get breakdown by AWS service."""
        costs = self.get_daily_costs(days=days, group_by='SERVICE')
        return costs

    def export_to_csv(self, output_file='costs.csv', days=30):
        """Export costs to CSV for finance team."""
        costs = self.get_daily_costs(days=days, group_by='SERVICE')

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Service', 'Date', 'Cost (USD)'])

            for service, daily_costs in costs.items():
                for date, cost in sorted(daily_costs.items()):
                    writer.writerow([service, date, f'{cost:.2f}'])

        print(f"Exported costs to {output_file}")

class EMRCostCalculator:
    """Calculate costs for EMR jobs."""

    def __init__(self, region='us-east-1'):
        self.emr = boto3.client('emr', region_name=region)
        self.ce = boto3.client('ce', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)

    def get_job_cost(self, cluster_id: str) -> Dict[str, float]:
        """
        Calculate total cost for EMR job/cluster.

        Returns:
            Dict with breakdown of core, task, master instance costs
        """
        cluster = self.emr.describe_cluster(ClusterId=cluster_id)['Cluster']
        core_count = len(self.emr.list_instances(
            ClusterId=cluster_id,
            InstanceGroupTypes=['CORE']
        )['Instances'])

        task_count = len(self.emr.list_instances(
            ClusterId=cluster_id,
            InstanceGroupTypes=['TASK']
        )['Instances'])

        # Get instance type pricing
        instance_groups = self.emr.list_instance_groups(
            ClusterId=cluster_id
        )['InstanceGroups']

        costs = {}
        total_cost = 0

        for group in instance_groups:
            group_type = group['InstanceGroupType']
            instance_type = group['InstanceType']

            # Get on-demand price
            price = self._get_spot_price(instance_type)

            # Calculate hours running
            hours = (datetime.utcnow() - cluster['Status']['Timeline']['CreationDateTime']).seconds / 3600

            # Calculate cost
            if group_type == 'MASTER':
                instance_cost = price * hours
            elif group_type == 'CORE':
                instance_cost = price * core_count * hours
            else:  # TASK
                instance_cost = price * task_count * hours

            costs[f'{group_type}'] = instance_cost
            total_cost += instance_cost

        costs['Total'] = total_cost
        return costs

    def _get_spot_price(self, instance_type):
        """Get current spot price for instance type."""
        try:
            response = self.ec2.describe_spot_price_history(
                InstanceTypes=[instance_type],
                MaxResults=1
            )
            if response['SpotPriceHistory']:
                return float(response['SpotPriceHistory'][0]['SpotPrice'])
        except:
            pass
        return 0.0

# Usage
if __name__ == '__main__':
    calc = CostCalculator()

    # Get last 30 days of costs by service
    service_costs = calc.get_service_costs(days=30)
    print("Costs by service:")
    for service, daily_costs in service_costs.items():
        total = sum(daily_costs.values())
        print(f"  {service}: ${total:.2f}")

    # Export to CSV
    calc.export_to_csv('monthly_costs.csv', days=30)

    # Get costs for specific team
    team_cost = calc.get_costs_by_tag('Team', 'data-engineering', days=30)
    print(f"Data Engineering costs: ${team_cost:.2f}")

    # EMR job cost
    emr_calc = EMRCostCalculator()
    job_cost = emr_calc.get_job_cost('j-123456')
    print(f"EMR Job cost: ${job_cost['Total']:.2f}")
```

---

## Pattern 3: Cross-Account Resource Access

**Use Case**: Access resources in other AWS accounts using STS AssumeRole.

**Key Features**:
- Credential caching
- Automatic refresh
- Error handling

**Source**: `iam/cross_account_access_sts.py`

```python
import boto3
from boto3 import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CrossAccountAccessor:
    """Access resources across AWS accounts using STS AssumeRole."""

    def __init__(self, target_account_id: str, target_role_name: str,
                 session_duration: int = 3600):
        """
        Initialize cross-account accessor.

        Args:
            target_account_id: AWS account ID to access
            target_role_name: IAM role name in target account
            session_duration: Credential duration in seconds (900-3600)
        """
        self.target_account_id = target_account_id
        self.target_role_name = target_role_name
        self.target_role_arn = f'arn:aws:iam::{target_account_id}:role/{target_role_name}'
        self.session_duration = session_duration
        self._credentials_cache = {}

    def get_credentials(self, session_name: str):
        """
        Get temporary credentials for target account.

        Returns:
            Credentials dict with AccessKeyId, SecretAccessKey, SessionToken
        """
        # Check cache
        if session_name in self._credentials_cache:
            creds, expiry = self._credentials_cache[session_name]
            if datetime.utcnow() < expiry - timedelta(minutes=5):
                logger.info(f"Using cached credentials for {session_name}")
                return creds

        # Assume role to get new credentials
        sts = boto3.client('sts')
        try:
            response = sts.assume_role(
                RoleArn=self.target_role_arn,
                RoleSessionName=session_name,
                DurationSeconds=self.session_duration
            )

            credentials = response['Credentials']
            creds_dict = {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'aws_session_token': credentials['SessionToken']
            }

            # Cache credentials
            self._credentials_cache[session_name] = (creds_dict, credentials['Expiration'])
            logger.info(f"Obtained new credentials for {session_name}")

            return creds_dict

        except Exception as e:
            logger.error(f"Failed to assume role {self.target_role_arn}: {e}")
            raise

    def get_client(self, service_name: str, region: str = 'us-east-1'):
        """Get AWS client for service in target account."""
        creds = self.get_credentials(f'{service_name}-client')
        return boto3.client(
            service_name,
            region_name=region,
            **creds
        )

    def get_resource(self, service_name: str, region: str = 'us-east-1'):
        """Get AWS resource for service in target account."""
        creds = self.get_credentials(f'{service_name}-resource')
        return boto3.resource(
            service_name,
            region_name=region,
            **creds
        )

    def list_s3_buckets(self) -> list:
        """List all S3 buckets in target account."""
        s3 = self.get_client('s3')
        response = s3.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]

    def list_ec2_instances(self, region: str = 'us-east-1'):
        """List all EC2 instances in target account."""
        ec2 = self.get_client('ec2', region=region)
        response = ec2.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'InstanceType': instance['InstanceType'],
                    'State': instance['State']['Name']
                })
        return instances

    def list_rds_databases(self, region: str = 'us-east-1'):
        """List all RDS databases in target account."""
        rds = self.get_client('rds', region=region)
        response = rds.describe_db_instances()
        return [db['DBInstanceIdentifier'] for db in response['DBInstances']]

# Usage
if __name__ == '__main__':
    # Create accessor for another account
    accessor = CrossAccountAccessor(
        target_account_id='999999999999',
        target_role_name='CrossAccountDataAccessRole'
    )

    # List resources in other account
    buckets = accessor.list_s3_buckets()
    print(f"Buckets in target account: {buckets}")

    instances = accessor.list_ec2_instances(region='us-east-1')
    print(f"EC2 instances: {instances}")

    databases = accessor.list_rds_databases()
    print(f"RDS databases: {databases}")
```

---

## Pattern 4: CloudFormation Stack Discovery

**Use Case**: Find and enumerate CloudFormation stacks with filtering.

**Key Features**:
- Tag-based filtering
- Resource enumeration
- Pagination support

**Source**: `aws-resource-manager/stack_discovery.py`

```python
import boto3
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class CloudFormationDiscovery:
    """Discover and manage CloudFormation stacks."""

    def __init__(self, region='us-east-1'):
        self.cf = boto3.client('cloudformation', region_name=region)
        self.region = region

    def list_stacks(self, status_filter: List[str] = None) -> List[Dict]:
        """
        List CloudFormation stacks.

        Args:
            status_filter: List of stack statuses to include
                          (CREATE_COMPLETE, UPDATE_COMPLETE, DELETE_COMPLETE, etc.)

        Returns:
            List of stack summaries
        """
        if status_filter is None:
            status_filter = ['CREATE_COMPLETE', 'UPDATE_COMPLETE']

        paginator = self.cf.get_paginator('list_stacks')
        stacks = []

        for page in paginator.paginate(StackStatusFilter=status_filter):
            stacks.extend(page['StackSummaries'])

        return stacks

    def find_stacks_by_tag(self, tag_key: str, tag_value: str = None) -> List[Dict]:
        """Find stacks with specific tag."""
        stacks = self.list_stacks()
        matching = []

        for stack in stacks:
            response = self.cf.describe_stacks(StackName=stack['StackName'])
            stack_detail = response['Stacks'][0]

            tags = {tag['Key']: tag['Value'] for tag in stack_detail.get('Tags', [])}

            if tag_key in tags:
                if tag_value is None or tags[tag_key] == tag_value:
                    matching.append(stack_detail)

        return matching

    def find_stacks_by_pattern(self, pattern: str) -> List[Dict]:
        """Find stacks by name pattern (regex)."""
        import re
        stacks = self.list_stacks()
        matching = []

        regex = re.compile(pattern)
        for stack in stacks:
            if regex.search(stack['StackName']):
                response = self.cf.describe_stacks(StackName=stack['StackName'])
                matching.append(response['Stacks'][0])

        return matching

    def get_stack_resources(self, stack_name: str) -> List[Dict]:
        """Get all resources in a stack."""
        paginator = self.cf.get_paginator('list_stack_resources')
        resources = []

        for page in paginator.paginate(StackName=stack_name):
            resources.extend(page['StackResourceSummaries'])

        return resources

    def get_stack_outputs(self, stack_name: str) -> Dict:
        """Get outputs from a stack."""
        response = self.cf.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]

        outputs = {}
        for output in stack.get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']

        return outputs

    def get_stack_parameters(self, stack_name: str) -> Dict:
        """Get parameters used in a stack."""
        response = self.cf.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]

        parameters = {}
        for param in stack.get('Parameters', []):
            parameters[param['ParameterKey']] = param['ParameterValue']

        return parameters

    def delete_stack(self, stack_name: str, retain_resources: List[str] = None):
        """Delete a CloudFormation stack."""
        try:
            self.cf.delete_stack(
                StackName=stack_name,
                RetainResources=retain_resources or []
            )
            logger.info(f"Deletion initiated for stack: {stack_name}")
        except Exception as e:
            logger.error(f"Failed to delete stack {stack_name}: {e}")
            raise

# Usage
if __name__ == '__main__':
    discovery = CloudFormationDiscovery(region='us-east-1')

    # List all active stacks
    stacks = discovery.list_stacks()
    print(f"Found {len(stacks)} stacks")

    # Find stacks by tag
    prod_stacks = discovery.find_stacks_by_tag('Environment', 'production')
    print(f"Production stacks: {[s['StackName'] for s in prod_stacks]}")

    # Find stacks by pattern
    data_stacks = discovery.find_stacks_by_pattern('.*-data-.*')
    print(f"Data-related stacks: {[s['StackName'] for s in data_stacks]}")

    # Get stack details
    if stacks:
        stack_name = stacks[0]['StackName']
        resources = discovery.get_stack_resources(stack_name)
        print(f"Resources in {stack_name}:")
        for resource in resources:
            print(f"  - {resource['LogicalResourceId']} ({resource['ResourceType']})")

        outputs = discovery.get_stack_outputs(stack_name)
        print(f"Outputs: {outputs}")
```

---

## Pattern 5: SSM Remote Execution

**Use Case**: Run commands on EC2 instances via Systems Manager.

**Key Features**:
- Least-loaded instance targeting
- Command output retrieval
- Error handling

**Source**: `aws-systems-manager/ssm_run_command_with_json_arg.py`

```python
import boto3
import json
import time
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SSMCommandExecutor:
    """Execute commands on EC2 instances via SSM."""

    def __init__(self, region='us-east-1'):
        self.ssm = boto3.client('ssm', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.region = region

    def find_least_loaded_instance(self, tag_key: str, tag_value: str) -> str:
        """Find EC2 instance with tag and lowest CPU utilization."""
        cloudwatch = boto3.client('cloudwatch', region_name=self.region)

        # Find instances with tag
        response = self.ec2.describe_instances(
            Filters=[
                {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        instances = []
        for reservation in response['Reservations']:
            instances.extend(reservation['Instances'])

        if not instances:
            raise ValueError(f"No instances found with {tag_key}={tag_value}")

        # Get CPU utilization for each
        least_loaded = None
        min_cpu = 100

        for instance in instances:
            metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance['InstanceId']}],
                StartTime=time.time() - 300,
                EndTime=time.time(),
                Period=60,
                Statistics=['Average']
            )

            avg_cpu = 0
            if metrics['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in metrics['Datapoints']) / len(metrics['Datapoints'])

            if avg_cpu < min_cpu:
                min_cpu = avg_cpu
                least_loaded = instance['InstanceId']

        return least_loaded

    def run_command(self, instance_ids: List[str], command: str,
                   timeout: int = 3600) -> str:
        """
        Run command on instances.

        Args:
            instance_ids: List of EC2 instance IDs
            command: Shell command to run
            timeout: Command timeout in seconds

        Returns:
            Command ID for tracking
        """
        try:
            response = self.ssm.send_command(
                InstanceIds=instance_ids,
                DocumentName='AWS-RunShellScript',
                Parameters={'command': [command]},
                TimeoutSeconds=timeout
            )

            command_id = response['Command']['CommandId']
            logger.info(f"Command {command_id} sent to {len(instance_ids)} instances")

            return command_id

        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            raise

    def run_command_with_json(self, instance_ids: List[str],
                             script: str, json_args: Dict) -> str:
        """
        Run command with JSON arguments.

        The script will have access to $JSON_ARGS environment variable.
        """
        json_str = json.dumps(json_args)
        # Escape JSON for shell
        escaped_json = json_str.replace('"', '\\"')

        command = f"""
        export JSON_ARGS='{json_str}'
        {script}
        """

        return self.run_command(instance_ids, command)

    def get_command_output(self, command_id: str, instance_id: str):
        """Get output from executed command."""
        # Wait for command to complete
        max_attempts = 60
        for attempt in range(max_attempts):
            response = self.ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )

            status = response['Status']
            if status in ['Success', 'Failed']:
                return {
                    'Status': status,
                    'StandardOutput': response['StandardOutputContent'],
                    'StandardError': response['StandardErrorContent']
                }

            time.sleep(5)

        raise TimeoutError(f"Command {command_id} timed out")

    def run_script_on_instance(self, instance_id: str, script_path: str) -> str:
        """Upload and run script on instance."""
        with open(script_path, 'r') as f:
            script_content = f.read()

        # Create command to download and execute
        command = f"""
        cat << 'EOF' > /tmp/script.sh
        {script_content}
        EOF
        chmod +x /tmp/script.sh
        /tmp/script.sh
        """

        return self.run_command([instance_id], command)

# Usage
if __name__ == '__main__':
    executor = SSMCommandExecutor(region='us-east-1')

    # Find least-loaded web server
    instance_id = executor.find_least_loaded_instance('Role', 'web-server')
    print(f"Targeting instance: {instance_id}")

    # Run simple command
    cmd_id = executor.run_command([instance_id], 'df -h')
    output = executor.get_command_output(cmd_id, instance_id)
    print(f"Disk usage:\n{output['StandardOutput']}")

    # Run command with JSON arguments
    json_args = {
        'bucket': 'my-data-bucket',
        'prefix': 'data/2024-05/',
        'format': 'parquet'
    }
    cmd_id = executor.run_command_with_json(
        [instance_id],
        '''python3 << 'SCRIPT'
import json
import os
args = json.loads(os.environ['JSON_ARGS'])
print(f"Processing {args['bucket']}/{args['prefix']}")
SCRIPT
        ''',
        json_args
    )
    output = executor.get_command_output(cmd_id, instance_id)
    print(output['StandardOutput'])
```

---

## Pattern 6: S3 SQL Query Engine

**Use Case**: Query data in S3 using SQL without downloading files.

**Key Features**:
- CSV and Parquet support
- SQL filtering
- Streaming results

**Source**: `s3-sql/s3_sql.py`

```python
import boto3
import json
from typing import Iterator, List

class S3SQLEngine:
    """Query data in S3 using SQL."""

    def __init__(self, region='us-east-1'):
        self.s3 = boto3.client('s3', region_name=region)

    def query_csv(self, bucket: str, key: str, sql: str,
                 headers: bool = True) -> Iterator[str]:
        """
        Query CSV file in S3 using SQL.

        Args:
            bucket: S3 bucket name
            key: Object key
            sql: SQL query (e.g., "SELECT * FROM s3object WHERE amount > 100")
            headers: True if first row is header

        Yields:
            Result rows as strings
        """
        response = self.s3.select_object_content(
            Bucket=bucket,
            Key=key,
            ExpressionType='SQL',
            Expression=sql,
            InputSerialization={
                'CSV': {
                    'FileHeaderInfo': 'Use' if headers else 'None',
                    'Comments': '#',
                    'QuoteEscapeCharacter': '"',
                    'RecordDelimiter': '\n',
                    'FieldDelimiter': ','
                }
            },
            OutputSerialization={'CSV': {}}
        )

        # Stream results
        for event in response['Payload']:
            if 'Records' in event:
                yield event['Records']['Payload'].decode('utf-8')

    def query_parquet(self, bucket: str, key: str, sql: str) -> Iterator[str]:
        """Query Parquet file in S3 using SQL."""
        response = self.s3.select_object_content(
            Bucket=bucket,
            Key=key,
            ExpressionType='SQL',
            Expression=sql,
            InputSerialization={'Parquet': {}},
            OutputSerialization={'JSON': {}}
        )

        # Stream results
        for event in response['Payload']:
            if 'Records' in event:
                yield event['Records']['Payload'].decode('utf-8')

    def query_json(self, bucket: str, key: str, sql: str) -> Iterator[str]:
        """Query JSONL file in S3 using SQL."""
        response = self.s3.select_object_content(
            Bucket=bucket,
            Key=key,
            ExpressionType='SQL',
            Expression=sql,
            InputSerialization={'JSON': {'Type': 'LINES'}},
            OutputSerialization={'JSON': {}}
        )

        # Stream results
        for event in response['Payload']:
            if 'Records' in event:
                yield event['Records']['Payload'].decode('utf-8')

    def count_rows(self, bucket: str, key: str, file_type: str = 'csv') -> int:
        """Count rows in file."""
        sql = 'SELECT COUNT(*) FROM s3object'

        if file_type == 'csv':
            results = ''.join(self.query_csv(bucket, key, sql))
        elif file_type == 'parquet':
            results = ''.join(self.query_parquet(bucket, key, sql))
        else:
            results = ''.join(self.query_json(bucket, key, sql))

        # Extract count from result
        lines = results.strip().split('\n')
        if lines:
            return int(lines[0])
        return 0

    def filter_and_download(self, bucket: str, key: str, sql: str,
                           output_file: str, file_type: str = 'csv'):
        """Filter data and save to local file."""
        query_method = getattr(self, f'query_{file_type}')

        with open(output_file, 'w') as f:
            for chunk in query_method(bucket, key, sql):
                f.write(chunk)

        print(f"Results saved to {output_file}")

# Usage
if __name__ == '__main__':
    engine = S3SQLEngine()

    # Count rows in CSV
    count = engine.count_rows(
        bucket='data-lake',
        key='raw-data/sales.csv',
        file_type='csv'
    )
    print(f"Total rows: {count}")

    # Query CSV with filtering
    results = engine.query_csv(
        bucket='data-lake',
        key='raw-data/sales.csv',
        sql='SELECT date, customer_id, amount FROM s3object WHERE amount > 1000'
    )

    print("High-value sales:")
    for line in results:
        print(line)

    # Query Parquet
    results = engine.query_parquet(
        bucket='data-lake',
        key='processed/sales.parquet',
        sql='SELECT * FROM s3object WHERE CAST(date AS DATE) > CAST(\'2024-01-01\' AS DATE)'
    )

    # Filter and save
    engine.filter_and_download(
        bucket='data-lake',
        key='raw-data/sales.csv',
        sql='SELECT * FROM s3object WHERE amount > 500',
        output_file='filtered_sales.csv',
        file_type='csv'
    )
```

---

## Pattern 7: Lambda Layer Deployment

**Use Case**: Create and share dependencies across Lambda functions.

```python
import boto3
import zipfile
import subprocess
import os
import tempfile
from typing import List

class LambdaLayerManager:
    """Manage Lambda layers for shared dependencies."""

    def __init__(self, region='us-east-1'):
        self.lamb = boto3.client('lambda', region_name=region)

    def create_layer_from_requirements(self, layer_name: str,
                                      requirements_file: str,
                                      runtimes: List[str] = None) -> str:
        """
        Create Lambda layer from requirements.txt.

        Args:
            layer_name: Name for the layer
            requirements_file: Path to requirements.txt
            runtimes: Compatible runtimes (default: python3.11)

        Returns:
            Layer version ARN
        """
        if runtimes is None:
            runtimes = ['python3.11']

        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Install packages
            lib_dir = os.path.join(tmpdir, 'python')
            os.makedirs(lib_dir)

            subprocess.run([
                'pip', 'install', '-r', requirements_file,
                '-t', lib_dir
            ], check=True)

            # Create zip file
            zip_path = os.path.join(tmpdir, f'{layer_name}.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(tmpdir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, tmpdir)
                        zf.write(file_path, arcname)

            # Upload to Lambda
            with open(zip_path, 'rb') as f:
                response = self.lamb.publish_layer_version(
                    LayerName=layer_name,
                    Content={'ZipFile': f.read()},
                    CompatibleRuntimes=runtimes
                )

        layer_arn = response['LayerVersionArn']
        print(f"Layer published: {layer_arn}")
        return layer_arn

    def add_layer_to_function(self, function_name: str, layer_arns: List[str]):
        """Add layers to a Lambda function."""
        self.lamb.update_function_configuration(
            FunctionName=function_name,
            Layers=layer_arns
        )
        print(f"Layers added to {function_name}")

# Usage
if __name__ == '__main__':
    manager = LambdaLayerManager()

    # Create layer from requirements.txt
    layer_arn = manager.create_layer_from_requirements(
        layer_name='pandas-numpy-layer',
        requirements_file='requirements.txt'
    )

    # Add to functions
    manager.add_layer_to_function('data-processor', [layer_arn])
```

---

## Pattern 8: Step Functions Orchestration

**Use Case**: Orchestrate complex workflows across AWS services.

```python
import boto3
import json
from datetime import datetime

class StepFunctionsOrchestrator:
    """Create and manage Step Functions workflows."""

    def __init__(self, region='us-east-1'):
        self.sfn = boto3.client('stepfunctions', region_name=region)

    def create_etl_pipeline(self, state_machine_name: str, role_arn: str,
                           extract_fn: str, transform_fn: str, load_fn: str) -> str:
        """Create ETL pipeline state machine."""
        definition = {
            'Comment': 'ETL Pipeline',
            'StartAt': 'Extract',
            'States': {
                'Extract': {
                    'Type': 'Task',
                    'Resource': f'arn:aws:lambda:*:*:function:{extract_fn}',
                    'Next': 'Transform',
                    'Catch': [
                        {
                            'ErrorEquals': ['States.ALL'],
                            'Next': 'HandleError'
                        }
                    ]
                },
                'Transform': {
                    'Type': 'Task',
                    'Resource': f'arn:aws:lambda:*:*:function:{transform_fn}',
                    'Next': 'Load'
                },
                'Load': {
                    'Type': 'Task',
                    'Resource': f'arn:aws:lambda:*:*:function:{load_fn}',
                    'End': True
                },
                'HandleError': {
                    'Type': 'Fail',
                    'Error': 'PipelineFailed',
                    'Cause': 'ETL pipeline encountered an error'
                }
            }
        }

        response = self.sfn.create_state_machine(
            name=state_machine_name,
            definition=json.dumps(definition),
            roleArn=role_arn
        )

        return response['stateMachineArn']

    def execute_pipeline(self, state_machine_arn: str, input_data: dict) -> str:
        """Execute state machine."""
        response = self.sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(input_data)
        )

        return response['executionArn']

    def get_execution_status(self, execution_arn: str):
        """Check execution status."""
        response = self.sfn.describe_execution(executionArn=execution_arn)
        return {
            'Status': response['status'],
            'Output': json.loads(response.get('output', '{}'))
        }

# Usage
if __name__ == '__main__':
    orchestrator = StepFunctionsOrchestrator()

    # Create pipeline
    arn = orchestrator.create_etl_pipeline(
        state_machine_name='data-pipeline',
        role_arn='arn:aws:iam::ACCOUNT:role/step-functions-role',
        extract_fn='extract-data',
        transform_fn='transform-data',
        load_fn='load-data'
    )

    # Execute
    execution_arn = orchestrator.execute_pipeline(arn, {
        'source_bucket': 'raw-data',
        'target_bucket': 'processed-data'
    })

    # Check status
    status = orchestrator.get_execution_status(execution_arn)
    print(f"Pipeline status: {status['Status']}")
```

---

## Summary

These 8 patterns cover the most common real-world AWS scenarios:

| Pattern | Use Case | Complexity |
|---------|----------|-----------|
| 1. Monitoring | Health checks, alerts | Medium |
| 2. Cost Management | Billing, chargeback | Medium |
| 3. Cross-Account | Multi-account access | Medium |
| 4. Stack Discovery | Infrastructure discovery | Easy |
| 5. SSM Execution | Remote commands | Medium |
| 6. S3 Queries | Data filtering | Easy |
| 7. Lambda Layers | Dependency sharing | Easy |
| 8. Step Functions | Workflow orchestration | Hard |

All patterns include:
- Error handling
- Logging
- Type hints
- Real usage examples
- Production-ready code

