# Production Patterns Cookbook
## Real-World AWS Solutions from Battle-Tested Code

### Table of Contents
1. Pattern 1: Multi-Service Monitoring System
2. Pattern 2: Cost Management & Chargeback
3. Pattern 3: Cross-Account Resource Access
4. Pattern 4: CloudFormation Stack Discovery
5. Pattern 5: SSM Remote Execution
6. Pattern 6: S3 SQL Query Engine
7. Pattern 7: Lambda Layer Deployment
8. Pattern 8: Step Functions Orchestration

---

## Pattern 1: Multi-Service Monitoring System

### Mental Model
Watching 17+ AWS services for health problems. Like a hospital that checks patients across multiple departments (Emergency, Cardiology, Neurology, etc.) and sends alerts when something's wrong.

### Problem
You need to:
- Monitor Lambda, EC2, S3, SQS, SNS, RDS, DynamoDB, and 10+ other services
- Check health status for each resource
- Compare actual values against thresholds
- Send alerts when problems occur
- Log all checks for auditing

### Solution: Base Monitor Pattern

**Architecture**: Abstract base class + service-specific implementations

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class HealthStatus(Enum):
    """Health status indicators."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ResourceHealth:
    """Health status of a single resource."""
    resource_id: str
    resource_name: str
    resource_type: str
    status: HealthStatus
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    region: str = 'us-east-1'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
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

class BaseMonitor(ABC):
    """Abstract base class for all service monitors."""

    def __init__(self, session_manager, config: Dict[str, Any]):
        """
        Initialize monitor.

        Args:
            session_manager: Manages AWS credentials and regions
            config: Service-specific configuration with thresholds
        """
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
        """
        Check health of provided resources.

        Args:
            resources: List of resource IDs/ARNs to check

        Returns:
            List of ResourceHealth objects
        """
        pass

    def should_alert(self, health: ResourceHealth) -> bool:
        """Determine if resource health warrants an alert."""
        return health.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]

    def get_cloudwatch_metrics(
        self,
        resource_id: str,
        metric_name: str,
        statistic: str = 'Average',
        period_minutes: int = 5
    ) -> Optional[float]:
        """
        Get CloudWatch metric for a resource.

        Args:
            resource_id: Resource identifier
            metric_name: CloudWatch metric name
            statistic: Statistic to retrieve (Average, Sum, Maximum, etc.)
            period_minutes: Period in minutes to look back

        Returns:
            Metric value or None if not available
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=period_minutes)

            response = self.cloudwatch.get_metric_statistics(
                Namespace=self._get_cloudwatch_namespace(),
                MetricName=metric_name,
                Dimensions=self._get_cloudwatch_dimensions(resource_id),
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=[statistic]
            )

            if response.get('Datapoints'):
                return response['Datapoints'][-1].get(statistic)

        except Exception as e:
            self.logger.debug(f"Error getting metric {metric_name}: {e}")

        return None

    def _check_threshold(
        self,
        value: float,
        threshold: float,
        operator: str = 'greater_than'
    ) -> bool:
        """
        Check if a value exceeds a threshold.

        Args:
            value: Actual value
            threshold: Threshold value
            operator: 'greater_than' or 'less_than'

        Returns:
            True if threshold is exceeded
        """
        if value is None:
            return False

        if operator == 'greater_than':
            return value > threshold
        elif operator == 'less_than':
            return value < threshold
        return False

    def _get_threshold(self, threshold_key: str, default: float = None) -> Optional[float]:
        """Get threshold value from config."""
        return self.config.get('thresholds', {}).get(threshold_key, default)
```

### Concrete Implementation: Lambda Monitor

```python
class LambdaMonitor(BaseMonitor):
    """Monitor Lambda functions for performance and errors."""

    @property
    def service_name(self) -> str:
        return 'lambda'

    def check_health(self, function_names: List[str]) -> List[ResourceHealth]:
        """
        Check health of Lambda functions.

        Returns:
            List of health status for each function
        """
        health_list = []

        for func_name in function_names:
            try:
                # Get function configuration
                response = self.client.get_function(FunctionName=func_name)
                config = response['Configuration']

                # Check error rate
                error_rate = self.get_cloudwatch_metrics(
                    func_name, 'Errors', statistic='Sum', period_minutes=5
                )

                # Check duration
                duration = self.get_cloudwatch_metrics(
                    func_name, 'Duration', statistic='Average', period_minutes=5
                )

                # Determine health status
                status = HealthStatus.HEALTHY
                message = f"Function {func_name} is running normally"

                if error_rate and error_rate > self._get_threshold('error_rate_max', 5):
                    status = HealthStatus.UNHEALTHY
                    message = f"High error rate: {error_rate} errors"

                if duration and duration > self._get_threshold('duration_max_ms', 10000):
                    status = HealthStatus.DEGRADED
                    message = f"Slow execution: {duration}ms average"

                health = ResourceHealth(
                    resource_id=config['FunctionArn'],
                    resource_name=func_name,
                    resource_type='lambda:function',
                    status=status,
                    message=message,
                    metrics={
                        'error_rate': error_rate,
                        'duration_ms': duration,
                        'memory_mb': config['MemorySize'],
                        'timeout_s': config['Timeout']
                    },
                    region=self.region
                )

                health_list.append(health)

            except Exception as e:
                health = ResourceHealth(
                    resource_id=func_name,
                    resource_name=func_name,
                    resource_type='lambda:function',
                    status=HealthStatus.UNKNOWN,
                    message=f"Error checking health: {e}",
                    region=self.region
                )
                health_list.append(health)

        return health_list

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/Lambda'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'FunctionName', 'Value': resource_id}]
```

### Usage Example

```python
# Configure monitors
config = {
    'thresholds': {
        'error_rate_max': 5,
        'duration_max_ms': 10000,
        'memory_utilization_max': 80
    }
}

lambda_monitor = LambdaMonitor(session_manager, config)

# Check health of all functions
functions = ['process-data', 'api-gateway-handler', 'scheduled-job']
health_results = lambda_monitor.check_health(functions)

# Send alerts for unhealthy resources
for health in health_results:
    if lambda_monitor.should_alert(health):
        send_alert(health.to_dict())
```

### Why This Pattern Works

1. **Extensible**: Add new service monitors by extending BaseMonitor
2. **Consistent**: All monitors follow same interface and structure
3. **Maintainable**: Common logic in base class, service-specific logic in subclasses
4. **Testable**: Abstract base makes it easy to mock and test
5. **Scalable**: Works with 1 service or 17 services equally well

---

## Pattern 2: Cost Management & Chargeback

### Mental Model
Accountant for your cloud spending. Tracks who spent what, calculates bills per team/project, and shows ROI.

### Problem
You need to:
- Know how much each EMR job actually costs
- Allocate AWS costs to different teams/projects
- Track cost trends over time
- Create chargeback reports

### Solution: Cost Calculator Pattern

```python
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class CostData:
    """Cost information for a resource."""
    resource_id: str
    resource_type: str
    start_date: str
    end_date: str
    total_cost: float
    currency: str = 'USD'
    service_breakdown: Dict[str, float] = None

class EMRCostCalculator:
    """Calculate costs for EMR clusters and jobs."""

    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize the EMR Cost Calculator

        Args:
            region_name: AWS region name
        """
        self.cost_explorer = boto3.client('ce', region_name=region_name)
        self.emr_client = boto3.client('emr', region_name=region_name)
        self.region = region_name

    def get_cluster_info(self, cluster_id: Optional[str] = None,
                         cluster_name: Optional[str] = None) -> List[Dict]:
        """
        Get EMR cluster information by ID or name

        Args:
            cluster_id: EMR cluster ID
            cluster_name: EMR cluster name

        Returns:
            List of cluster information dictionaries
        """
        clusters = []

        try:
            if cluster_id:
                # Get specific cluster by ID
                response = self.emr_client.describe_cluster(ClusterId=cluster_id)
                clusters.append({
                    'Id': response['Cluster']['Id'],
                    'Name': response['Cluster']['Name'],
                    'Status': response['Cluster']['Status']['State'],
                    'CreationDateTime': response['Cluster']['Status']['Timeline'].get('CreationDateTime'),
                    'EndDateTime': response['Cluster']['Status']['Timeline'].get('EndDateTime')
                })

            elif cluster_name:
                # List clusters and filter by name (pagination pattern)
                paginator = self.emr_client.get_paginator('list_clusters')

                for page in paginator.paginate():
                    for cluster in page['Clusters']:
                        if cluster['Name'] == cluster_name:
                            clusters.append({
                                'Id': cluster['Id'],
                                'Name': cluster['Name'],
                                'Status': cluster['Status']['State'],
                                'CreationDateTime': cluster['Status']['Timeline'].get('CreationDateTime'),
                                'EndDateTime': cluster['Status']['Timeline'].get('EndDateTime')
                            })

            return clusters

        except Exception as e:
            print(f"Error getting cluster information: {e}")
            return []

    def get_cluster_costs(self, cluster_id: str,
                         start_date: str, end_date: str) -> Optional[float]:
        """
        Get costs for a specific EMR cluster using Cost Explorer API.

        Args:
            cluster_id: EMR cluster ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Total cost in USD or None if error
        """
        try:
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Filter={
                    'Tags': {
                        'Key': 'cluster-id',
                        'Values': [cluster_id]
                    }
                },
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )

            total_cost = 0.0
            service_breakdown = {}

            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    service_breakdown[service_name] = cost
                    total_cost += cost

            return CostData(
                resource_id=cluster_id,
                resource_type='emr:cluster',
                start_date=start_date,
                end_date=end_date,
                total_cost=total_cost,
                service_breakdown=service_breakdown
            )

        except Exception as e:
            print(f"Error getting cluster costs: {e}")
            return None

    def allocate_costs_by_team(self, cluster_ids: List[str],
                               cost_allocation_map: Dict[str, float]) -> Dict[str, float]:
        """
        Allocate cluster costs to teams.

        Args:
            cluster_ids: List of cluster IDs
            cost_allocation_map: Map of cluster ID to team allocation percentage

        Returns:
            Dictionary of team -> total cost
        """
        team_costs = {}

        for cluster_id in cluster_ids:
            cost_data = self.get_cluster_costs(
                cluster_id,
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d')
            )

            if cost_data:
                allocation_pct = cost_allocation_map.get(cluster_id, 100)
                allocated_cost = cost_data.total_cost * (allocation_pct / 100)

                # Add to team costs (simplified - normally would have cluster-to-team mapping)
                team = cluster_id.split('-')[0]  # Extract team from cluster ID
                team_costs[team] = team_costs.get(team, 0) + allocated_cost

        return team_costs
```

### Usage Example

```python
calculator = EMRCostCalculator()

# Get cost for specific cluster
cost_data = calculator.get_cluster_costs(
    cluster_id='j-1234567890ABC',
    start_date='2024-01-01',
    end_date='2024-01-31'
)

if cost_data:
    print(f"Cluster {cost_data.resource_id} cost: ${cost_data.total_cost:.2f}")
    print("Service breakdown:")
    for service, cost in cost_data.service_breakdown.items():
        print(f"  {service}: ${cost:.2f}")

# Allocate costs to teams
clusters = ['analytics-cluster-1', 'analytics-cluster-2', 'ml-cluster-1']
allocation = {
    'analytics-cluster-1': 50,   # Analytics team: 50% of cost
    'analytics-cluster-2': 50,   # Analytics team: 50% of cost
    'ml-cluster-1': 100          # ML team: 100% of cost
}

team_costs = calculator.allocate_costs_by_team(clusters, allocation)
for team, cost in team_costs.items():
    print(f"{team}: ${cost:.2f}")
```

### Why This Pattern Works

1. **Accurate**: Uses AWS Cost Explorer API for actual billing data
2. **Flexible**: Supports multiple allocation methods
3. **Auditable**: Tracks costs with clear breakdowns
4. **Scalable**: Works with 1 cluster or 1000 clusters

---

## Pattern 3: Cross-Account Resource Access

### Mental Model
Getting keys to another company's warehouse (different AWS account). Use a temporary pass (STS assume role) instead of keeping permanent keys.

### Problem
You need to:
- Access resources in another AWS account
- Use temporary credentials instead of permanent keys
- Maintain security with minimal risk
- Implement clear access control

### Solution: STS AssumeRole Pattern

```python
import boto3
from boto3 import Session
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from dataclasses import dataclass

@dataclass
class AssumedRoleCredentials:
    """Temporary credentials from STS AssumeRole."""
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: str
    assumed_role_arn: str

class CrossAccountAccessManager:
    """Manage cross-account access using STS AssumeRole."""

    def __init__(self, source_account_credentials: Optional[Dict[str, str]] = None):
        """
        Initialize the manager.

        Args:
            source_account_credentials: Optional explicit credentials for source account
        """
        if source_account_credentials:
            session = Session(
                aws_access_key_id=source_account_credentials['access_key'],
                aws_secret_access_key=source_account_credentials['secret_key']
            )
            self.sts = session.client('sts')
        else:
            self.sts = boto3.client('sts')

    def assume_role(self, role_arn: str,
                   role_session_name: str,
                   duration_seconds: int = 3600) -> Optional[AssumedRoleCredentials]:
        """
        Assume a role in another account.

        Args:
            role_arn: ARN of role to assume
            role_session_name: Unique session identifier
            duration_seconds: How long credentials are valid (900-43200 seconds)

        Returns:
            AssumedRoleCredentials or None if error
        """
        try:
            response = self.sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=role_session_name,
                DurationSeconds=duration_seconds
            )

            credentials = response['Credentials']

            return AssumedRoleCredentials(
                access_key_id=credentials['AccessKeyId'],
                secret_access_key=credentials['SecretAccessKey'],
                session_token=credentials['SessionToken'],
                expiration=credentials['Expiration'].isoformat(),
                assumed_role_arn=response['AssumedRoleUser']['Arn']
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                print(f"Access denied assuming role {role_arn}")
            elif error_code == 'InvalidInput':
                print(f"Invalid role ARN or session name")
            else:
                print(f"Error assuming role: {error_code}")
            return None

    def get_cross_account_client(self, service_name: str,
                                role_arn: str,
                                region_name: str = 'us-east-1') -> Optional[Any]:
        """
        Get a service client in a cross-account role.

        Args:
            service_name: AWS service name (e.g., 's3', 'ec2')
            role_arn: Role to assume
            region_name: AWS region

        Returns:
            Boto3 client or None if error
        """
        # Assume the role
        creds = self.assume_role(
            role_arn=role_arn,
            role_session_name=f'{service_name}-session'
        )

        if not creds:
            return None

        # Create session with assumed role credentials
        session = Session(
            aws_access_key_id=creds.access_key_id,
            aws_secret_access_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            region_name=region_name
        )

        return session.client(service_name)

    def list_cross_account_buckets(self, role_arn: str) -> Optional[list]:
        """
        List S3 buckets accessible via cross-account role.

        Args:
            role_arn: Role to assume

        Returns:
            List of bucket names or None if error
        """
        s3_client = self.get_cross_account_client('s3', role_arn)

        if not s3_client:
            return None

        try:
            response = s3_client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]

        except ClientError as e:
            print(f"Error listing buckets: {e}")
            return None

    def query_cross_account_instances(self, role_arn: str,
                                     region_name: str = 'us-east-1') -> Optional[list]:
        """
        Query EC2 instances in cross-account role.

        Args:
            role_arn: Role to assume
            region_name: AWS region

        Returns:
            List of instance IDs or None if error
        """
        ec2_client = self.get_cross_account_client('ec2', role_arn, region_name)

        if not ec2_client:
            return None

        try:
            response = ec2_client.describe_instances()
            instance_ids = []

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append({
                        'InstanceId': instance['InstanceId'],
                        'State': instance['State']['Name'],
                        'InstanceType': instance['InstanceType']
                    })

            return instance_ids

        except ClientError as e:
            print(f"Error describing instances: {e}")
            return None
```

### Usage Example

```python
manager = CrossAccountAccessManager()

# Assume role in another account
role_arn = 'arn:aws:iam::987654321:role/CrossAccountAccessRole'

# Get S3 client in remote account
s3 = manager.get_cross_account_client('s3', role_arn)
if s3:
    response = s3.list_buckets()
    print(f"Remote buckets: {[b['Name'] for b in response['Buckets']]}")

# Query EC2 instances in remote account
instances = manager.query_cross_account_instances(
    role_arn=role_arn,
    region_name='us-east-1'
)
if instances:
    for instance in instances:
        print(f"Instance {instance['InstanceId']}: {instance['State']}")
```

### Why This Pattern Works

1. **Secure**: Uses temporary credentials, not long-lived keys
2. **Auditable**: Each assume-role is logged in CloudTrail
3. **Time-limited**: Credentials expire automatically
4. **Flexible**: Works with any AWS service
5. **Scalable**: Manage access to multiple accounts

---

## Pattern 4: CloudFormation Stack Discovery

### Mental Model
Treasure map for your infrastructure. Discovers all resources created by CloudFormation stacks, groups them logically.

### Problem
You need to:
- Find all resources created by a specific stack
- List all stacks in your account
- Filter stacks by tag or name
- Handle pagination for large results

### Solution: Stack Discovery Pattern

```python
import boto3
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass

@dataclass
class StackResource:
    """Information about a resource in a CloudFormation stack."""
    logical_id: str
    physical_id: str
    resource_type: str
    resource_status: str
    timestamp: str

class CloudFormationDiscovery:
    """Discover and enumerate CloudFormation stacks and resources."""

    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize CloudFormation discovery.

        Args:
            region_name: AWS region
        """
        self.cfn = boto3.client('cloudformation', region_name=region_name)
        self.region = region_name

    def list_all_stacks(self) -> Generator[Dict, None, None]:
        """
        Generator for all stacks (handles pagination).

        Yields:
            Stack information dictionaries
        """
        paginator = self.cfn.get_paginator('list_stacks')

        # Exclude deleted stacks
        page_iterator = paginator.paginate(
            StackStatusFilter=[
                'CREATE_COMPLETE',
                'UPDATE_COMPLETE',
                'UPDATE_ROLLBACK_COMPLETE'
            ]
        )

        for page in page_iterator:
            for stack in page.get('StackSummaries', []):
                yield {
                    'StackName': stack['StackName'],
                    'StackId': stack['StackId'],
                    'StackStatus': stack['StackStatus'],
                    'CreationTime': stack['CreationTime'].isoformat(),
                    'LastUpdatedTime': stack.get('LastUpdatedTime', '').isoformat()
                }

    def get_stack_resources(self, stack_name: str) -> List[StackResource]:
        """
        Get all resources created by a stack.

        Args:
            stack_name: Name of CloudFormation stack

        Returns:
            List of StackResource objects
        """
        resources = []

        try:
            paginator = self.cfn.get_paginator('list_stack_resources')
            page_iterator = paginator.paginate(StackName=stack_name)

            for page in page_iterator:
                for resource in page.get('StackResourceSummaries', []):
                    resources.append(StackResource(
                        logical_id=resource['LogicalResourceId'],
                        physical_id=resource['PhysicalResourceId'],
                        resource_type=resource['ResourceType'],
                        resource_status=resource['ResourceStatus'],
                        timestamp=resource['LastUpdatedTimestamp'].isoformat()
                    ))

        except Exception as e:
            print(f"Error getting stack resources: {e}")

        return resources

    def find_stacks_by_tag(self, tag_key: str, tag_value: str) -> List[Dict]:
        """
        Find stacks with specific tag.

        Args:
            tag_key: Tag key to search for
            tag_value: Tag value to match

        Returns:
            List of matching stacks
        """
        matching_stacks = []

        for stack in self.list_all_stacks():
            try:
                response = self.cfn.describe_stacks(StackName=stack['StackName'])
                tags = response['Stacks'][0].get('Tags', [])

                for tag in tags:
                    if tag['Key'] == tag_key and tag['Value'] == tag_value:
                        matching_stacks.append(stack)
                        break

            except Exception as e:
                print(f"Error checking tags for {stack['StackName']}: {e}")

        return matching_stacks

    def get_stack_resources_by_type(self, stack_name: str,
                                    resource_type: str) -> List[StackResource]:
        """
        Get resources of specific type from a stack.

        Args:
            stack_name: Stack name
            resource_type: Resource type (e.g., 'AWS::S3::Bucket')

        Returns:
            List of matching resources
        """
        all_resources = self.get_stack_resources(stack_name)
        return [r for r in all_resources if r.resource_type == resource_type]

    def export_stack_inventory(self) -> Dict[str, List]:
        """
        Export inventory of all stacks and their resources.

        Returns:
            Dictionary of stack name -> list of resources
        """
        inventory = {}

        for stack in self.list_all_stacks():
            stack_name = stack['StackName']
            resources = self.get_stack_resources(stack_name)
            inventory[stack_name] = [
                {
                    'logical_id': r.logical_id,
                    'physical_id': r.physical_id,
                    'type': r.resource_type,
                    'status': r.resource_status
                }
                for r in resources
            ]

        return inventory
```

### Usage Example

```python
discovery = CloudFormationDiscovery(region_name='us-east-1')

# List all stacks
print("All stacks:")
for stack in discovery.list_all_stacks():
    print(f"  {stack['StackName']}: {stack['StackStatus']}")

# Get resources in a specific stack
stack_resources = discovery.get_stack_resources('my-app-stack')
print(f"\nResources in my-app-stack:")
for resource in stack_resources:
    print(f"  {resource.logical_id} ({resource.resource_type}): {resource.resource_status}")

# Find stacks by tag
prod_stacks = discovery.find_stacks_by_tag('Environment', 'production')
print(f"\nProduction stacks:")
for stack in prod_stacks:
    print(f"  {stack['StackName']}")

# Get only S3 buckets from a stack
s3_resources = discovery.get_stack_resources_by_type(
    'my-app-stack',
    'AWS::S3::Bucket'
)
print(f"\nS3 buckets in my-app-stack:")
for resource in s3_resources:
    print(f"  {resource.logical_id}: {resource.physical_id}")

# Export full inventory
inventory = discovery.export_stack_inventory()
import json
print(json.dumps(inventory, indent=2))
```

### Why This Pattern Works

1. **Complete**: Finds all resources across all stacks
2. **Flexible**: Filter by name, tag, or resource type
3. **Scalable**: Uses pagination for large inventories
4. **Auditable**: Tracks creation and modification times
5. **Exportable**: Can generate reports and inventories

---

## Pattern 5: SSM Remote Execution

### Mental Model
Remote control for your servers. Run commands on EC2 instances without SSH/bastion hosts. Send commands through AWS Systems Manager.

### Problem
You need to:
- Run commands on EC2 instances without SSH access
- Target instances dynamically (by tag, name, etc.)
- Get command output and execution status
- Avoid managing SSH keys

### Solution: SSM Remote Execution Pattern

```python
import boto3
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import time

@dataclass
class CommandExecution:
    """Result of SSM command execution."""
    command_id: str
    instance_id: str
    status: str
    output: str
    error_output: str

class SSMCommandExecutor:
    """Execute commands on EC2 instances via Systems Manager."""

    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize SSM command executor.

        Args:
            region_name: AWS region
        """
        self.ssm = boto3.client('ssm', region_name=region_name)
        self.ec2 = boto3.client('ec2', region_name=region_name)

    def find_instances_by_tag(self, tag_key: str, tag_value: str) -> List[str]:
        """
        Find instances by tag.

        Args:
            tag_key: Tag key to search for
            tag_value: Tag value to match

        Returns:
            List of instance IDs
        """
        response = self.ec2.describe_instances(
            Filters=[
                {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])

        return instance_ids

    def find_least_loaded_instance(self, instance_ids: List[str]) -> Optional[str]:
        """
        Find instance with least CPU utilization.

        Args:
            instance_ids: List of instance IDs to check

        Returns:
            Instance ID with lowest CPU or None
        """
        if not instance_ids:
            return None

        cloudwatch = boto3.client('cloudwatch')
        cpu_loads = {}

        for instance_id in instance_ids:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=datetime.utcnow() - timedelta(minutes=5),
                    EndTime=datetime.utcnow(),
                    Period=60,
                    Statistics=['Average']
                )

                if response['Datapoints']:
                    cpu_loads[instance_id] = response['Datapoints'][-1]['Average']
                else:
                    cpu_loads[instance_id] = 0  # No data = assume low load

            except Exception as e:
                print(f"Error checking CPU for {instance_id}: {e}")
                cpu_loads[instance_id] = 999  # Assume high load on error

        # Return instance with lowest CPU
        return min(cpu_loads, key=cpu_loads.get)

    def execute_command(self, instance_ids: List[str],
                       command: str,
                       wait_for_completion: bool = True,
                       timeout_seconds: int = 300) -> List[CommandExecution]:
        """
        Execute command on EC2 instances.

        Args:
            instance_ids: List of instance IDs
            command: Shell command to execute
            wait_for_completion: Wait for command to finish
            timeout_seconds: Timeout if waiting

        Returns:
            List of CommandExecution results
        """
        # Send command
        response = self.ssm.send_command(
            InstanceIds=instance_ids,
            DocumentName='AWS-RunShellScript',
            Parameters={'command': [command]},
            TimeoutSeconds=[timeout_seconds]
        )

        command_id = response['Command']['CommandId']
        print(f"Command {command_id} sent to {len(instance_ids)} instances")

        results = []

        if wait_for_completion:
            # Wait for all instances to complete
            start_time = time.time()

            while time.time() - start_time < timeout_seconds:
                response = self.ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=instance_ids[0]  # Check first instance
                )

                status = response['Status']

                if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                    # Command completed on this instance
                    break

                time.sleep(5)  # Check every 5 seconds

            # Get results from all instances
            for instance_id in instance_ids:
                try:
                    response = self.ssm.get_command_invocation(
                        CommandId=command_id,
                        InstanceId=instance_id
                    )

                    results.append(CommandExecution(
                        command_id=command_id,
                        instance_id=instance_id,
                        status=response['Status'],
                        output=response.get('StandardOutputContent', ''),
                        error_output=response.get('StandardErrorContent', '')
                    ))

                except Exception as e:
                    results.append(CommandExecution(
                        command_id=command_id,
                        instance_id=instance_id,
                        status='Error',
                        output='',
                        error_output=str(e)
                    ))

        return results

    def execute_on_tagged_instances(self, tag_key: str, tag_value: str,
                                   command: str) -> List[CommandExecution]:
        """
        Execute command on all instances with specific tag.

        Args:
            tag_key: Tag key to search for
            tag_value: Tag value to match
            command: Command to execute

        Returns:
            List of execution results
        """
        # Find instances by tag
        instance_ids = self.find_instances_by_tag(tag_key, tag_value)

        if not instance_ids:
            print(f"No instances found with tag {tag_key}={tag_value}")
            return []

        print(f"Found {len(instance_ids)} instances: {instance_ids}")

        # Execute command
        return self.execute_command(instance_ids, command)
```

### Usage Example

```python
executor = SSMCommandExecutor()

# Execute on specific instances
instances = ['i-1234567890abcdef0', 'i-0987654321fedcba0']
results = executor.execute_command(
    instance_ids=instances,
    command='df -h'  # Show disk space
)

for result in results:
    print(f"{result.instance_id}: {result.status}")
    print(f"Output:\n{result.output}")

# Execute on all instances with a tag
results = executor.execute_on_tagged_instances(
    tag_key='Environment',
    tag_value='production',
    command='systemctl restart myservice'
)

# Find least loaded instance
instance_ids = executor.find_instances_by_tag('Application', 'api-server')
least_loaded = executor.find_least_loaded_instance(instance_ids)
print(f"Least loaded instance: {least_loaded}")
```

### Why This Pattern Works

1. **Secure**: No SSH keys to manage
2. **Audited**: All commands logged in CloudTrail
3. **Scalable**: Run on 1 or 1000 instances
4. **Flexible**: Target by tag, name, or explicit list
5. **Safe**: IAM policies control what can be executed

---

## Summary Table

| Pattern | Problem | Solution |
|---------|---------|----------|
| **Monitoring** | Track 17+ services | Base monitor + service-specific implementations |
| **Cost** | Who spent what | Cost Explorer API + allocation logic |
| **Cross-Account** | Access remote account resources | STS AssumeRole + temporary credentials |
| **Discovery** | Find all resources | CloudFormation stack enumeration |
| **Execution** | Run commands on EC2 | SSM command execution |
| **SQL on S3** | Query data in S3 | PySpark + Athena integration |
| **Layers** | Share code across functions | Lambda layer deployment automation |
| **Orchestration** | Complex workflows | Step Functions state machines |

---

## Key Takeaways

1. **Abstraction**: Build abstract base classes for extensibility
2. **Pagination**: Always use paginators for list operations
3. **Error Handling**: Wrap all AWS calls in try-except
4. **Credentials**: Use IAM roles/STS, never hardcode keys
5. **Monitoring**: Log operations, send metrics, alert on problems
6. **Cost**: Track spending, allocate to teams, prevent surprises
7. **Security**: Use least privilege, temporary credentials, audit trails

---

**Last Updated**: 2024
**Target Audience**: AWS developers building production systems
**Estimated Reading Time**: 2-3 hours (patterns are independent)
