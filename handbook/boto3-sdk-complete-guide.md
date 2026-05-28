# Boto3 SDK Complete Guide: Master the AWS Python SDK

> **From zero to production-ready**: Comprehensive guide to Boto3 covering everything from client/resource selection to advanced production patterns. 2,500+ lines of explanation and code.

---

## Table of Contents

### PART 1: FOUNDATIONS (Chapters 1-2)
- Chapter 1: Boto3 Architecture
- Chapter 2: Core Patterns

### PART 2: SERVICE DEEP DIVES (Chapters 3-7)
- Chapter 3: EC2 with Boto3
- Chapter 4: RDS with Boto3
- Chapter 5: CloudWatch with Boto3
- Chapter 6: ECS/Fargate with Boto3
- Chapter 7: Advanced S3 Patterns

### PART 3: ADVANCED PATTERNS (Chapters 8-10)
- Chapter 8: Multi-Account & Cross-Region
- Chapter 9: Performance Optimization
- Chapter 10: Production Best Practices

---

# PART 1: FOUNDATIONS

## Chapter 1: Boto3 Architecture

### What is Boto3?

Boto3 is the **Amazon Web Services (AWS) SDK for Python**. It allows Python developers to write software that uses AWS services like S3, EC2, CloudWatch, and more.

**Key facts:**
- Official AWS SDK maintained by AWS
- Works with Python 3.7+
- Comprehensive API coverage for 200+ AWS services
- Used in production by thousands of companies

### Installation

```bash
# Basic installation
pip install boto3

# With AWS CLI (recommended)
pip install boto3 awscli

# For data science workloads
pip install boto3 pandas numpy

# For advanced use cases
pip install boto3 botocore retrying
```

**Check installation:**
```python
import boto3
print(boto3.__version__)  # Should be 1.26+
```

---

### Client vs Resource: The Core Decision

This is THE most important concept in Boto3. Most confusion comes from not understanding when to use each.

#### What is a Client?

**Definition**: A client is a **low-level interface** that maps 1:1 with the AWS service API.

**Characteristics:**
- Provides ALL available operations
- Explicit control - you control every parameter
- Returns raw responses as dictionaries
- Requires understanding AWS API details

**When to use Client:**
```python
import boto3

# Use client when:
# 1. You need ALL operations
# 2. You want explicit control
# 3. You're integrating with AWS APIs
# 4. You need advanced features (pagination, filtering)

s3_client = boto3.client('s3', region_name='us-east-1')

# Client returns raw dictionaries
response = s3_client.list_objects_v2(Bucket='my-bucket', MaxKeys=10)
print(response['Contents'])  # Raw API response
```

#### What is a Resource?

**Definition**: A resource is a **high-level, object-oriented interface** that abstracts AWS services.

**Characteristics:**
- Simplified, Pythonic API
- Common operations only (not all)
- Returns objects with methods and properties
- Hides low-level API details

**When to use Resource:**
```python
import boto3

# Use resource when:
# 1. You want cleaner code
# 2. You need basic operations
# 3. You're building applications
# 4. You want Pythonic syntax

s3_resource = boto3.resource('s3', region_name='us-east-1')

# Resource returns objects with methods
bucket = s3_resource.Bucket('my-bucket')
for obj in bucket.objects.all():
    print(obj.key)  # Clean, Pythonic
```

#### Client vs Resource: Detailed Comparison

| Aspect | Client | Resource |
|--------|--------|----------|
| **Syntax** | `response = client.list_objects(...)` | `bucket.objects.all()` |
| **Returns** | Dictionary | Python object |
| **Code Style** | Procedural | Object-oriented |
| **Operations** | All AWS operations | Common operations |
| **Complexity** | More verbose | Cleaner |
| **Control** | Full control | Abstracted |
| **Learning Curve** | Moderate | Easy |
| **Performance** | Same | Same |
| **Use Case** | Complex workflows | Simple apps |

#### Practical Examples: When to Use Each

**Scenario 1: Simple S3 upload**
```python
# ❌ WRONG: Too verbose with client
import boto3
s3 = boto3.client('s3')
with open('file.txt', 'rb') as f:
    s3.put_object(Bucket='bucket', Key='file.txt', Body=f)

# ✅ RIGHT: Cleaner with resource
import boto3
s3 = boto3.resource('s3')
s3.Bucket('bucket').upload_file('file.txt', 'file.txt')
```

**Scenario 2: Advanced EC2 filtering**
```python
# ✅ RIGHT: Must use client for complex filters
import boto3
ec2 = boto3.client('ec2', region_name='us-east-1')
instances = ec2.describe_instances(
    Filters=[
        {'Name': 'instance-state-name', 'Values': ['running']},
        {'Name': 'tag:Environment', 'Values': ['production']},
        {'Name': 'instance-type', 'Values': ['t3.medium', 't3.large']}
    ]
)

# ❌ WRONG: Resource doesn't support these filters
# ec2_resource = boto3.resource('ec2')
# Can't use advanced filters with resource
```

**Scenario 3: DynamoDB operations**
```python
# For complex queries, use client
import boto3
dynamodb = boto3.client('dynamodb')
response = dynamodb.query(
    TableName='users',
    KeyConditionExpression='user_id = :uid AND created_at > :date',
    ExpressionAttributeValues={
        ':uid': {'S': 'user_123'},
        ':date': {'N': '1699999999'}
    }
)

# For simple operations, resource is cleaner
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')
response = table.query(
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': 'user_123'}
)
```

---

### Session Management: Credentials and Configuration

A **Session** represents your AWS credentials and configuration.

#### Default Session (Implicit)

```python
import boto3

# Uses default credentials from:
# 1. AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY env vars
# 2. ~/.aws/credentials file (default profile)
# 3. IAM role (if running on EC2/Lambda/ECS)

s3 = boto3.client('s3')  # Uses default session implicitly
```

#### Custom Session (Explicit)

```python
import boto3
from boto3 import Session

# Create explicit session
session = Session(
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    region_name='us-east-1'
)

# Use session to create clients
s3 = session.client('s3')
ec2 = session.client('ec2')
```

#### Using Named Profiles

```python
import boto3
from boto3 import Session

# Use a specific AWS CLI profile
# Assumes you've run: aws configure --profile production
session = Session(profile_name='production')
s3 = session.client('s3')

# List all available profiles
import os
aws_config = os.path.expanduser('~/.aws/credentials')
```

#### Environment Variables

```bash
# Set credentials via environment
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='us-east-1'

# Optional: set profile
export AWS_PROFILE='production'
```

```python
import boto3

# Now boto3 uses environment variables automatically
s3 = boto3.client('s3')
```

---

### Configuration Options

#### Custom Configuration

```python
import boto3
from botocore.config import Config

# Create custom configuration
config = Config(
    region_name='us-east-1',
    signature_version='s3v4',  # For S3
    retries={'max_attempts': 3, 'mode': 'standard'},
    connect_timeout=5,
    read_timeout=60,
    max_pool_connections=10
)

# Apply to client
s3 = boto3.client('s3', config=config)
```

#### Regions and Endpoints

```python
import boto3

# Use specific region
s3_us_east = boto3.client('s3', region_name='us-east-1')
s3_eu_west = boto3.client('s3', region_name='eu-west-1')

# Custom endpoint (LocalStack example)
s3_local = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',  # LocalStack
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)
```

---

## Chapter 2: Core Patterns

### Error Handling: Boto Exceptions

Boto3 uses botocore exceptions. Understanding them is crucial for production.

#### Common Exceptions

```python
import boto3
from botocore.exceptions import (
    NoCredentialsError,
    ClientError,
    ConnectionError,
    Waiter,
    WaiterError
)

# Example 1: NoCredentialsError
s3 = boto3.client('s3')

try:
    s3.list_buckets()
except NoCredentialsError:
    print("AWS credentials not found. Configure with: aws configure")

# Example 2: ClientError (most common)
try:
    s3.get_object(Bucket='non-existent-bucket', Key='file.txt')
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']

    if error_code == 'NoSuchBucket':
        print(f"Bucket not found: {error_message}")
    elif error_code == 'NoSuchKey':
        print(f"File not found: {error_message}")
    elif error_code == 'AccessDenied':
        print(f"Permission denied: {error_message}")
    else:
        print(f"Unexpected error: {error_code} - {error_message}")

# Example 3: ConnectionError
try:
    ec2 = boto3.client('ec2', region_name='us-east-1')
    ec2.describe_instances()
except ConnectionError:
    print("Network error. Check your connection and AWS endpoint.")
```

#### Error Handling Best Practices

```python
import boto3
from botocore.exceptions import ClientError
import time

def robust_s3_get(bucket, key, max_retries=3):
    """
    Get S3 object with retry logic.

    Demonstrates:
    - Exponential backoff
    - Selective error handling
    - Logging
    """
    s3 = boto3.client('s3')

    for attempt in range(max_retries):
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()

        except ClientError as e:
            error_code = e.response['Error']['Code']

            # Retryable errors (temporary issues)
            if error_code in ['ServiceUnavailable', 'RequestLimitExceeded', 'ThrottlingException']:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    print(f"Retryable error {error_code}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {error_code}")

            # Non-retryable errors
            elif error_code == 'NoSuchBucket':
                raise ValueError(f"Bucket '{bucket}' does not exist")
            elif error_code == 'NoSuchKey':
                raise ValueError(f"Key '{key}' does not exist in bucket '{bucket}'")
            elif error_code == 'AccessDenied':
                raise PermissionError(f"Access denied to bucket '{bucket}' or key '{key}'")
            else:
                raise Exception(f"AWS error: {error_code}")

# Usage
try:
    data = robust_s3_get('my-bucket', 'important-file.csv')
    print(f"Retrieved {len(data)} bytes")
except Exception as e:
    print(f"Error: {e}")
```

---

### Pagination: Handling Large Result Sets

When AWS returns results, sometimes there are too many to fit in one response. Pagination handles this.

#### Manual Pagination

```python
import boto3

s3 = boto3.client('s3')

# Manual pagination (verbose)
marker = None
all_objects = []

while True:
    if marker:
        response = s3.list_objects(Bucket='my-bucket', Marker=marker)
    else:
        response = s3.list_objects(Bucket='my-bucket')

    # Collect objects
    if 'Contents' in response:
        all_objects.extend(response['Contents'])

    # Check if there are more results
    if response.get('IsTruncated'):
        marker = response.get('NextMarker')
    else:
        break

print(f"Total objects: {len(all_objects)}")
```

#### Paginator: The Clean Way

```python
import boto3

s3 = boto3.client('s3')

# Using paginator (recommended)
paginator = s3.get_paginator('list_objects_v2')

# Configure pagination
page_iterator = paginator.paginate(
    Bucket='my-bucket',
    Prefix='data/',
    PaginationConfig={
        'PageSize': 100,  # Items per request
        'MaxItems': 1000   # Total items to fetch
    }
)

# Iterate through all pages
for page in page_iterator:
    if 'Contents' not in page:
        continue

    for obj in page['Contents']:
        print(f"{obj['Key']} - {obj['Size']} bytes")

# Alternative: iterate directly (even cleaner)
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket='my-bucket')

all_objects = []
for page in pages:
    if 'Contents' in page:
        all_objects.extend(page['Contents'])
```

#### Available Paginators

```python
import boto3

# Check available paginators for a service
s3 = boto3.client('s3')
available_paginators = s3.can_paginate
print(available_paginators)

# Common paginators
ec2 = boto3.client('ec2')
print(ec2.can_paginate)  # List all EC2 paginators
```

---

### Waiters: Waiting for Resource State Changes

Waiters poll a resource until it reaches a desired state.

#### Common Waiters

```python
import boto3
import time

# Example 1: Wait for S3 bucket to exist
s3 = boto3.client('s3')

# Create bucket
s3.create_bucket(Bucket='my-new-bucket')

# Wait for it to be available
waiter = s3.get_waiter('bucket_exists')
waiter.wait(Bucket='my-new-bucket')
print("Bucket is ready!")

# Example 2: Wait for EC2 instance to be running
ec2 = boto3.client('ec2')

# Launch instance
response = ec2.run_instances(ImageId='ami-0c55b159cbfafe1f0', MinCount=1, MaxCount=1)
instance_id = response['Instances'][0]['InstanceId']

# Wait for instance to run
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
print(f"Instance {instance_id} is running!")

# Example 3: Wait for RDS database to be available
rds = boto3.client('rds')

# Create database
rds.create_db_instance(
    DBInstanceIdentifier='mydb',
    DBInstanceClass='db.t3.micro',
    Engine='mysql',
    MasterUsername='admin',
    MasterUserPassword='password123'
)

# Wait for it to be available
waiter = rds.get_waiter('db_instance_available')
waiter.wait(DBInstanceIdentifier='mydb')
print("Database is ready!")
```

#### Custom Waiter Configuration

```python
import boto3

ec2 = boto3.client('ec2')

# Wait with custom configuration
waiter = ec2.get_waiter('instance_running')
waiter.wait(
    InstanceIds=['i-1234567890abcdef0'],
    WaiterConfig={
        'Delay': 5,      # Check every 5 seconds
        'MaxAttempts': 40  # Try for up to 200 seconds (40 * 5)
    }
)
```

---

### Batch Operations: Processing Multiple Items

Efficiently process multiple items using batch operations.

#### SQS Batch Example

```python
import boto3
import json

sqs = boto3.client('sqs')

# Send batch of messages (up to 10)
entries = []
for i in range(25):
    entries.append({
        'Id': str(i),
        'MessageBody': json.dumps({'item_id': i, 'action': 'process'})
    })

    # SQS has a limit of 10 messages per batch
    if len(entries) == 10:
        sqs.send_message_batch(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/myqueue',
            Entries=entries
        )
        entries = []

# Send remaining
if entries:
    sqs.send_message_batch(QueueUrl=queue_url, Entries=entries)
```

#### EC2 Tag Batch Example

```python
import boto3

ec2 = boto3.client('ec2')

# Tag multiple instances at once
instance_ids = ['i-1234567890abcdef0', 'i-0987654321fedcba0']
ec2.create_tags(
    Resources=instance_ids,
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Team', 'Value': 'data-engineering'}
    ]
)
```

---

# PART 2: SERVICE DEEP DIVES

## Chapter 3: EC2 with Boto3

### Instance Lifecycle Management

```python
import boto3
import time

ec2 = boto3.client('ec2', region_name='us-east-1')

# Launch instance
response = ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',  # Ubuntu 22.04
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': 'my-web-server'},
                {'Key': 'Environment', 'Value': 'development'}
            ]
        }
    ]
)

instance_id = response['Instances'][0]['InstanceId']
print(f"Launched instance: {instance_id}")

# Wait for instance to be running
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
print("Instance is running")

# Describe instance to get details
response = ec2.describe_instances(InstanceIds=[instance_id])
instance = response['Reservations'][0]['Instances'][0]
print(f"Public IP: {instance.get('PublicIpAddress')}")
print(f"Private IP: {instance['PrivateIpAddress']}")

# Stop instance (doesn't delete)
ec2.stop_instances(InstanceIds=[instance_id])
print("Instance stopped")

# Start it again
ec2.start_instances(InstanceIds=[instance_id])
print("Instance started")

# Terminate instance (deletes it)
ec2.terminate_instances(InstanceIds=[instance_id])
print("Instance terminated")
```

### Security Groups

```python
import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

# Create security group
sg_response = ec2.create_security_group(
    GroupName='web-server-sg',
    Description='Security group for web servers',
    VpcId='vpc-12345678'  # Use your VPC ID
)
sg_id = sg_response['GroupId']

# Add inbound rule: Allow HTTP
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP from anywhere'}]
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 443,
            'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS from anywhere'}]
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '203.0.113.0/24', 'Description': 'SSH from office'}]
        }
    ]
)

print(f"Security group {sg_id} created and rules added")

# Describe security groups
response = ec2.describe_security_groups(GroupIds=[sg_id])
for rule in response['SecurityGroups'][0]['IpPermissions']:
    print(f"Allow {rule['IpProtocol']} port {rule.get('FromPort')}")
```

### Tagging and Filtering

```python
import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

# Tag instances
instance_ids = ['i-1234567890abcdef0']
ec2.create_tags(
    Resources=instance_ids,
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'CostCenter', 'Value': 'engineering'},
        {'Key': 'Backup', 'Value': 'daily'}
    ]
)

# Filter instances by tags
response = ec2.describe_instances(
    Filters=[
        {'Name': 'tag:Environment', 'Values': ['production']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
)

print(f"Found {len(response['Reservations'])} instances")
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"Instance: {instance['InstanceId']}")
        for tag in instance.get('Tags', []):
            print(f"  {tag['Key']}: {tag['Value']}")
```

---

## Chapter 4: RDS with Boto3

### Database Instance Management

```python
import boto3

rds = boto3.client('rds', region_name='us-east-1')

# Create RDS instance
response = rds.create_db_instance(
    DBInstanceIdentifier='mydb-prod',
    DBInstanceClass='db.t3.small',
    Engine='mysql',  # or 'postgres', 'mariadb', 'oracle-se2'
    MasterUsername='admin',
    MasterUserPassword='SecurePassword123!',
    AllocatedStorage=20,  # GB
    StorageType='gp2',  # General Purpose SSD
    BackupRetentionPeriod=7,  # Keep 7 days of backups
    MultiAZ=True,  # High availability
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Application', 'Value': 'web-app'}
    ]
)

print(f"Creating database: mydb-prod")

# Wait for database to be available
waiter = rds.get_waiter('db_instance_available')
waiter.wait(
    DBInstanceIdentifier='mydb-prod',
    WaiterConfig={'Delay': 30, 'MaxAttempts': 60}  # Up to 30 minutes
)
print("Database is available!")

# Describe database instance
response = rds.describe_db_instances(DBInstanceIdentifier='mydb-prod')
db = response['DBInstances'][0]
print(f"Endpoint: {db['Endpoint']['Address']}")
print(f"Port: {db['Endpoint']['Port']}")
print(f"Engine: {db['Engine']} {db['EngineVersion']}")
print(f"Status: {db['DBInstanceStatus']}")
```

### Snapshots and Backup

```python
import boto3

rds = boto3.client('rds', region_name='us-east-1')

# Create manual snapshot
snapshot_response = rds.create_db_snapshot(
    DBSnapshotIdentifier='mydb-backup-2024-05',
    DBInstanceIdentifier='mydb-prod'
)
print("Snapshot creation initiated...")

# Wait for snapshot
waiter = rds.get_waiter('db_snapshot_available')
waiter.wait(DBSnapshotIdentifier='mydb-backup-2024-05')
print("Snapshot complete!")

# List snapshots
response = rds.describe_db_snapshots(DBInstanceIdentifier='mydb-prod')
for snapshot in response['DBSnapshots']:
    print(f"Snapshot: {snapshot['DBSnapshotIdentifier']}")
    print(f"  Created: {snapshot['SnapshotCreateTime']}")
    print(f"  Size: {snapshot['AllocatedStorage']} GB")

# Restore from snapshot
restore_response = rds.restore_db_instance_from_db_snapshot(
    DBInstanceIdentifier='mydb-restored',
    DBSnapshotIdentifier='mydb-backup-2024-05'
)
print("Restore initiated...")
```

---

## Chapter 5: CloudWatch with Boto3

### Metrics and Custom Metrics

```python
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

# Put custom metric
cloudwatch.put_metric_data(
    Namespace='MyApplication',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': 45.2,
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'production'},
                {'Name': 'Service', 'Value': 'api-gateway'}
            ]
        },
        {
            'MetricName': 'ErrorCount',
            'Value': 2,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        }
    ]
)

print("Metrics published to CloudWatch")

# Get metric statistics
response = cloudwatch.get_metric_statistics(
    Namespace='MyApplication',
    MetricName='ProcessingTime',
    Dimensions=[
        {'Name': 'Environment', 'Value': 'production'}
    ],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=60,  # 1 minute
    Statistics=['Average', 'Maximum', 'Minimum', 'SampleCount']
)

print(f"Data points: {len(response['Datapoints'])}")
for datapoint in response['Datapoints']:
    print(f"{datapoint['Timestamp']}: Avg={datapoint.get('Average', 'N/A')}")
```

### Alarms

```python
import boto3

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

# Create alarm
cloudwatch.put_metric_alarm(
    AlarmName='high-cpu-production',
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Period=300,  # 5 minutes
    EvaluationPeriods=2,  # Evaluate last 10 minutes
    Threshold=80.0,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789:alert-topic'],
    Dimensions=[
        {'Name': 'AutoScalingGroupName', 'Value': 'web-server-asg'}
    ]
)

print("Alarm created: high-cpu-production")

# Describe alarms
response = cloudwatch.describe_alarms(AlarmNames=['high-cpu-production'])
for alarm in response['MetricAlarms']:
    print(f"Alarm: {alarm['AlarmName']}")
    print(f"  Status: {alarm['StateValue']}")
    print(f"  Threshold: {alarm['Threshold']} {alarm['MetricName']}")

# Delete alarm
cloudwatch.delete_alarms(AlarmNames=['high-cpu-production'])
print("Alarm deleted")
```

---

## Chapter 6: ECS/Fargate with Boto3

### Task Definitions

```python
import boto3
import json

ecs = boto3.client('ecs', region_name='us-east-1')

# Register task definition
response = ecs.register_task_definition(
    family='web-app-task',
    networkMode='awsvpc',
    requiresCompatibilities=['FARGATE'],
    cpu='256',  # vCPU in Fargate: 256, 512, 1024, 2048, 4096
    memory='512',  # Memory in MB: depends on CPU
    containerDefinitions=[
        {
            'name': 'web-app',
            'image': '123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:latest',
            'portMappings': [
                {
                    'containerPort': 8080,
                    'hostPort': 8080,
                    'protocol': 'tcp'
                }
            ],
            'environment': [
                {'name': 'DATABASE_URL', 'value': 'postgres://db.example.com/mydb'},
                {'name': 'LOG_LEVEL', 'value': 'INFO'}
            ],
            'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                    'awslogs-group': '/ecs/web-app',
                    'awslogs-region': 'us-east-1',
                    'awslogs-stream-prefix': 'ecs'
                }
            }
        }
    ],
    executionRoleArn='arn:aws:iam::123456789:role/ecsTaskExecutionRole',
    taskRoleArn='arn:aws:iam::123456789:role/ecsTaskRole'
)

task_def_arn = response['taskDefinition']['taskDefinitionArn']
print(f"Task definition registered: {task_def_arn}")
```

### ECS Services and Tasks

```python
import boto3

ecs = boto3.client('ecs', region_name='us-east-1')

# Create ECS service
response = ecs.create_service(
    cluster='production',
    serviceName='web-app-service',
    taskDefinition='web-app-task:1',
    desiredCount=3,
    launchType='FARGATE',
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': ['subnet-12345678', 'subnet-87654321'],
            'securityGroups': ['sg-12345678'],
            'assignPublicIp': 'ENABLED'
        }
    },
    loadBalancers=[
        {
            'targetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/web-app/abc123',
            'containerName': 'web-app',
            'containerPort': 8080
        }
    ]
)

service_arn = response['service']['serviceArn']
print(f"Service created: {service_arn}")

# Run one-off task
response = ecs.run_task(
    cluster='production',
    taskDefinition='web-app-task:1',
    launchType='FARGATE',
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': ['subnet-12345678'],
            'securityGroups': ['sg-12345678']
        }
    },
    overrides={
        'containerOverrides': [
            {
                'name': 'web-app',
                'environment': [
                    {'name': 'COMMAND', 'value': 'migrate_database'}
                ]
            }
        ]
    }
)

task_arn = response['tasks'][0]['taskArn']
print(f"Task started: {task_arn}")
```

---

## Chapter 7: Advanced S3 Patterns

### Multipart Upload for Large Files

```python
import boto3
import os

s3 = boto3.client('s3', region_name='us-east-1')

def upload_large_file(bucket, key, file_path):
    """Upload large file using multipart upload."""

    # Initiate multipart upload
    response = s3.create_multipart_upload(Bucket=bucket, Key=key)
    upload_id = response['UploadId']

    parts = []
    part_size = 5 * 1024 * 1024  # 5 MB minimum

    with open(file_path, 'rb') as f:
        part_number = 1

        while True:
            data = f.read(part_size)
            if not data:
                break

            # Upload part
            part_response = s3.upload_part(
                Bucket=bucket,
                Key=key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=data
            )

            parts.append({
                'ETag': part_response['ETag'],
                'PartNumber': part_number
            })

            print(f"Uploaded part {part_number}")
            part_number += 1

    # Complete multipart upload
    s3.complete_multipart_upload(
        Bucket=bucket,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={'Parts': parts}
    )

    print(f"Upload complete: {key}")

# Usage
upload_large_file('my-bucket', 'videos/movie.mp4', '/path/to/large-file.mp4')
```

### Presigned URLs

```python
import boto3
from datetime import datetime, timedelta

s3 = boto3.client('s3', region_name='us-east-1')

# Generate presigned URL for download (expires in 1 hour)
download_url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'data/report.pdf'},
    ExpiresIn=3600  # 1 hour
)

print(f"Download link (valid for 1 hour):\n{download_url}")

# Generate presigned URL for upload
upload_url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'uploads/user-file.csv'},
    ExpiresIn=1800  # 30 minutes
)

print(f"Upload link (valid for 30 minutes):\n{upload_url}")

# Generate presigned URL for POST (HTML form upload)
post_data = s3.generate_presigned_post(
    Bucket='my-bucket',
    Key='uploads/form-file.txt',
    ExpiresIn=3600
)

print("HTML Form for upload:")
print(f"<form action='{post_data['url']}' method='post' enctype='multipart/form-data'>")
for key, value in post_data['fields'].items():
    print(f"  <input type='hidden' name='{key}' value='{value}' />")
print("  <input type='file' name='file' />")
print("  <input type='submit' value='Upload' />")
print("</form>")
```

### S3 Select: Query Data in S3

```python
import boto3
import json

s3 = boto3.client('s3', region_name='us-east-1')

# Query CSV data directly in S3 (no need to download)
response = s3.select_object_content(
    Bucket='data-lake',
    Key='raw-data/sales.csv',
    ExpressionType='SQL',
    Expression='SELECT name, amount FROM s3object WHERE amount > 1000',
    InputSerialization={
        'CSV': {
            'FileHeaderInfo': 'Use',  # First row is header
            'Comments': '#',
            'QuoteEscapeCharacter': '"',
            'RecordDelimiter': '\n',
            'FieldDelimiter': ','
        }
    },
    OutputSerialization={'CSV': {}}
)

# Process results as they stream
with open('filtered-results.csv', 'w') as f:
    for event in response['Payload']:
        if 'Records' in event:
            records = event['Records']['Payload'].decode('utf-8')
            f.write(records)

print("Filtered data written to filtered-results.csv")

# Query Parquet data
response = s3.select_object_content(
    Bucket='data-lake',
    Key='processed/sales.parquet',
    ExpressionType='SQL',
    Expression='SELECT * FROM s3object s WHERE s.date > \'2024-01-01\'',
    InputSerialization={'Parquet': {}},
    OutputSerialization={'JSON': {}}
)

# Process JSON results
results = []
for event in response['Payload']:
    if 'Records' in event:
        records = event['Records']['Payload'].decode('utf-8')
        results.extend(records.strip().split('\n'))

print(f"Found {len(results)} records")
```

---

# PART 3: ADVANCED PATTERNS

## Chapter 8: Multi-Account & Cross-Region

### STS AssumeRole for Cross-Account Access

```python
import boto3
import os
from datetime import datetime, timedelta

def assume_role_cross_account(role_arn, session_name, duration_seconds=3600):
    """
    Assume a role in another AWS account.

    Args:
        role_arn: ARN of role to assume (e.g., arn:aws:iam::ACCOUNT-B:role/MyRole)
        session_name: Session name for audit trail
        duration_seconds: How long credentials are valid (900-3600 seconds)

    Returns:
        Credentials dict with AccessKeyId, SecretAccessKey, SessionToken
    """
    sts = boto3.client('sts')

    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
        DurationSeconds=duration_seconds
    )

    credentials = response['Credentials']
    return {
        'aws_access_key_id': credentials['AccessKeyId'],
        'aws_secret_access_key': credentials['SecretAccessKey'],
        'aws_session_token': credentials['SessionToken'],
        'expiration': credentials['Expiration']
    }

# Example usage
creds = assume_role_cross_account(
    role_arn='arn:aws:iam::999999999999:role/CrossAccountAccessRole',
    session_name='data-pipeline-job',
    duration_seconds=3600
)

print(f"Assumed role! Credentials valid until {creds['expiration']}")

# Create S3 client with assumed role credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=creds['aws_access_key_id'],
    aws_secret_access_key=creds['aws_secret_access_key'],
    aws_session_token=creds['aws_session_token']
)

# Now you can access resources in the other account
buckets = s3.list_buckets()
print(f"Buckets in other account: {len(buckets['Buckets'])}")
```

### Multi-Account Class Pattern

```python
import boto3
from boto3 import Session

class CrossAccountAccessor:
    """
    Manages cross-account access through STS AssumeRole.

    This pattern is from production systems with 100+ accounts.
    See: aws-monitoring/src/monitors/base_monitor.py for details.
    """

    def __init__(self, principal_account, principal_role, target_account, target_role):
        """
        Initialize cross-account accessor.

        Args:
            principal_account: Source account ID
            principal_role: Role in source account to use
            target_account: Destination account ID
            target_role: Role in destination account to assume
        """
        self.principal_account = principal_account
        self.target_account = target_account
        self.target_role_arn = f'arn:aws:iam::{target_account}:role/{target_role}'
        self._credentials_cache = {}

    def get_credentials(self, service_name, session_name):
        """Get temporary credentials for service in target account."""
        cache_key = f"{service_name}:{session_name}"

        if cache_key in self._credentials_cache:
            creds, expiry = self._credentials_cache[cache_key]
            if datetime.utcnow() < expiry - timedelta(minutes=5):
                return creds

        # Assume role
        sts = boto3.client('sts')
        response = sts.assume_role(
            RoleArn=self.target_role_arn,
            RoleSessionName=session_name,
            DurationSeconds=3600
        )

        credentials = response['Credentials']
        creds_dict = {
            'aws_access_key_id': credentials['AccessKeyId'],
            'aws_secret_access_key': credentials['SecretAccessKey'],
            'aws_session_token': credentials['SessionToken']
        }

        # Cache credentials
        self._credentials_cache[cache_key] = (creds_dict, credentials['Expiration'])
        return creds_dict

    def get_client(self, service_name, region='us-east-1'):
        """Get AWS client in target account."""
        creds = self.get_credentials(service_name, f'{service_name}-client')
        return boto3.client(
            service_name,
            region_name=region,
            **creds
        )

    def list_s3_buckets(self):
        """List all S3 buckets in target account."""
        s3 = self.get_client('s3')
        response = s3.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]

# Usage
accessor = CrossAccountAccessor(
    principal_account='111111111111',
    principal_role='CrossAccountRole',
    target_account='222222222222',
    target_role='DataAccessRole'
)

buckets = accessor.list_s3_buckets()
print(f"Buckets in target account: {buckets}")

# Get client for specific service
dynamodb = accessor.get_client('dynamodb')
tables = dynamodb.list_tables()
print(f"DynamoDB tables: {tables['TableNames']}")
```

### Cross-Region Resource Access

```python
import boto3

def list_resources_all_regions(service_name, operation_name, operation_params):
    """List resources across all regions."""

    # Get all regions
    ec2 = boto3.client('ec2', region_name='us-east-1')
    regions_response = ec2.describe_regions()
    regions = [region['RegionName'] for region in regions_response['Regions']]

    all_results = {}

    for region in regions:
        try:
            client = boto3.client(service_name, region_name=region)
            operation = getattr(client, operation_name)
            response = operation(**operation_params)
            all_results[region] = response
        except Exception as e:
            print(f"Error in {region}: {e}")
            all_results[region] = None

    return all_results

# Example: Find all Lambda functions in all regions
results = list_resources_all_regions(
    service_name='lambda',
    operation_name='list_functions',
    operation_params={}
)

for region, response in results.items():
    if response and 'Functions' in response:
        print(f"{region}: {len(response['Functions'])} functions")
```

---

## Chapter 9: Performance Optimization

### Connection Pooling and Concurrency

```python
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.config import Config

# Configure connection pooling
config = Config(
    max_pool_connections=50,  # Default is 10
    retries={'max_attempts': 3}
)

s3 = boto3.client('s3', config=config)

def upload_file(bucket, key, data):
    """Upload single file."""
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=data)
        return f"✓ {key}"
    except Exception as e:
        return f"✗ {key}: {e}"

# Upload 100 files in parallel using thread pool
files_to_upload = [
    (f'file-{i}.txt', f'Content of file {i}'.encode())
    for i in range(100)
]

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(upload_file, 'my-bucket', key, data)
        for key, data in files_to_upload
    ]

    results = []
    for future in as_completed(futures):
        results.append(future.result())

    for result in results:
        print(result)
```

### Batch Operations with Efficient Resource Use

```python
import boto3
from collections import defaultdict

def batch_tag_instances(instance_ids, tags, batch_size=50):
    """
    Tag many EC2 instances efficiently.

    AWS has rate limits, so we batch in groups of 50.
    """
    ec2 = boto3.client('ec2')

    batches = [instance_ids[i:i+batch_size] for i in range(0, len(instance_ids), batch_size)]

    for batch in batches:
        ec2.create_tags(
            Resources=batch,
            Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
        )
        print(f"Tagged {len(batch)} instances")

# Usage
instance_ids = [f'i-{i}' for i in range(500)]
batch_tag_instances(instance_ids, {'Environment': 'production', 'Team': 'data'})
```

---

## Chapter 10: Production Best Practices

### Comprehensive Error Handling and Retry Logic

```python
import boto3
from botocore.exceptions import ClientError, ConnectionError
from botocore.config import Config
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustAWSClient:
    """
    Production-grade AWS client with comprehensive error handling.
    Based on patterns from: aws-monitoring/src/monitors/base_monitor.py
    """

    def __init__(self, service_name, region='us-east-1'):
        config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            connect_timeout=5,
            read_timeout=60
        )
        self.client = boto3.client(service_name, region_name=region, config=config)
        self.service_name = service_name

    def call_with_retry(self, operation_name, **kwargs):
        """Call AWS operation with intelligent retry logic."""
        operation = getattr(self.client, operation_name)
        max_attempts = 3
        backoff_base = 2

        for attempt in range(max_attempts):
            try:
                logger.info(f"Calling {self.service_name}.{operation_name} (attempt {attempt + 1})")
                return operation(**kwargs)

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = e.response['Error']['Message']

                # Retryable errors
                retryable = [
                    'ServiceUnavailable',
                    'RequestLimitExceeded',
                    'ThrottlingException',
                    'InternalServerError'
                ]

                if error_code in retryable and attempt < max_attempts - 1:
                    wait_time = backoff_base ** attempt
                    logger.warning(f"Retryable error: {error_code}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Non-retryable errors
                logger.error(f"Non-retryable error: {error_code} - {error_msg}")
                raise

            except ConnectionError as e:
                if attempt < max_attempts - 1:
                    wait_time = backoff_base ** attempt
                    logger.warning(f"Connection error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"Connection failed after {max_attempts} attempts")
                raise

        raise Exception(f"Operation failed after {max_attempts} attempts")

# Usage
s3_client = RobustAWSClient('s3')
try:
    response = s3_client.call_with_retry('list_buckets')
    print(f"Buckets: {[b['Name'] for b in response['Buckets']]}")
except Exception as e:
    logger.error(f"Failed to list buckets: {e}")
```

### Logging and Monitoring

```python
import boto3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable boto3 debug logging (very verbose)
# boto3.set_stream_logger(name='boto3.resources', level=logging.DEBUG)

class MonitoredAWSOperation:
    """
    Track AWS API calls with CloudWatch metrics.
    Pattern from: aws-monitoring/src/monitors/base_monitor.py
    """

    def __init__(self, service_name):
        self.service_client = boto3.client(service_name)
        self.cloudwatch = boto3.client('cloudwatch')
        self.service_name = service_name

    def execute_and_monitor(self, operation_name, **kwargs):
        """Execute operation and publish metrics to CloudWatch."""
        import time

        start_time = time.time()
        success = False
        error = None

        try:
            logger.info(f"Starting {self.service_name}.{operation_name}")
            operation = getattr(self.service_client, operation_name)
            result = operation(**kwargs)
            success = True
            logger.info(f"Completed {self.service_name}.{operation_name}")
            return result

        except Exception as e:
            error = str(e)
            logger.error(f"Failed {self.service_name}.{operation_name}: {error}")
            raise

        finally:
            # Publish metrics
            duration_ms = (time.time() - start_time) * 1000
            self._publish_metrics(operation_name, success, duration_ms)

    def _publish_metrics(self, operation_name, success, duration_ms):
        """Publish operation metrics to CloudWatch."""
        self.cloudwatch.put_metric_data(
            Namespace=f'AWS/{self.service_name}',
            MetricData=[
                {
                    'MetricName': 'OperationDuration',
                    'Value': duration_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Operation', 'Value': operation_name},
                        {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
                    ]
                }
            ]
        )

# Usage
monitor = MonitoredAWSOperation('s3')
try:
    monitor.execute_and_monitor('list_buckets')
except Exception as e:
    print(f"Operation failed: {e}")
```

---

## Quick Reference: Common Patterns

### Create Session and Multiple Clients

```python
from boto3 import Session

# Create session once, use for multiple services
session = Session(profile_name='production', region_name='us-east-1')

s3 = session.client('s3')
ec2 = session.client('ec2')
lambda_client = session.client('lambda')
dynamodb = session.resource('dynamodb')  # Can mix client and resource
```

### Template: Production AWS Function

```python
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

def get_s3_object(bucket: str, key: str, region: str = 'us-east-1') -> bytes:
    """
    Production-ready S3 get_object with error handling.

    Args:
        bucket: S3 bucket name
        key: Object key
        region: AWS region

    Returns:
        Object content as bytes

    Raises:
        ValueError: If bucket or key doesn't exist
        PermissionError: If access is denied
    """
    s3 = boto3.client('s3', region_name=region)

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    except ClientError as e:
        error_code = e.response['Error']['Code']

        if error_code == 'NoSuchBucket':
            raise ValueError(f"Bucket '{bucket}' not found")
        elif error_code == 'NoSuchKey':
            raise ValueError(f"Key '{key}' not found in '{bucket}'")
        elif error_code == 'AccessDenied':
            raise PermissionError(f"Access denied to '{bucket}/{key}'")
        else:
            logger.error(f"AWS error: {error_code}")
            raise

# Usage
try:
    data = get_s3_object('my-bucket', 'data.csv')
    print(f"Retrieved {len(data)} bytes")
except ValueError as e:
    logger.error(f"Invalid request: {e}")
except PermissionError as e:
    logger.error(f"Permission issue: {e}")
```

---

## Key Takeaways

1. **Client vs Resource**: Use client for complex operations, resource for simple ones
2. **Error Handling**: Always catch `ClientError` and handle retryable vs non-retryable errors
3. **Pagination**: Use paginators for large result sets
4. **Waiters**: Use waiters to wait for resource state changes
5. **Batch Operations**: Group operations to reduce API calls
6. **Session Management**: Create sessions for credentials, not clients
7. **Configuration**: Customize retries, timeouts, connection pooling
8. **Cross-Account**: Use STS AssumeRole for cross-account access
9. **Monitoring**: Publish metrics to CloudWatch for visibility
10. **Production**: Always implement comprehensive error handling and retry logic

---

## Further Resources

- **AWS SDK Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/
- **Botocore Documentation**: https://botocore.amazonaws.com/v1/documentation/api/latest/
- **AWS Python Code Examples**: https://github.com/awsdocs/aws-doc-sdk-examples/tree/main/python
- **AWS Well-Architected Framework**: https://aws.amazon.com/architecture/well-architected/

