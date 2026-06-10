`# Boto3 Quick Reference
## 30-60 Second Lookup for Common Operations

### Table of Contents
- Client vs Resource Decision
- Common Service Operations
- Error Handling Patterns
- Pagination & Waiters
- Session Management
- Configuration Patterns

---

## Client vs Resource - Quick Comparison

| Need | Use | Code |
|------|-----|------|
| Simple operations | Resource | `s3 = boto3.resource('s3')` |
| All AWS features | Client | `s3 = boto3.client('s3')` |
| Control & flexibility | Client | Map 1:1 with AWS API |
| Readable code | Resource | Higher-level abstractions |
| Learning/Prototyping | Resource | Beginner-friendly |
| Production automation | Client | Explicit control |

**Quick Test**:
```python
# If you need all features → Client
client = boto3.client('s3')

# If you want simple code → Resource
resource = boto3.resource('s3')
```

---

## S3: Common Operations

### Upload File
```python
s3 = boto3.client('s3')
s3.upload_file('local.txt', 'my-bucket', 'remote.txt')
```

### Download File
```python
s3.download_file('my-bucket', 'remote.txt', 'local.txt')
```

### List Objects
```python
# Using client (need pagination)
response = s3.list_objects_v2(Bucket='my-bucket')
for obj in response['Contents']:
    print(obj['Key'])

# Using resource (automatic)
bucket = boto3.resource('s3').Bucket('my-bucket')
for obj in bucket.objects.all():
    print(obj.key)
```

### Delete Object
```python
s3.delete_object(Bucket='my-bucket', Key='file.txt')
```

### Generate Presigned URL
```python
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'file.txt'},
    ExpiresIn=3600
)
print(url)  # Share this link (expires in 1 hour)
```

### Copy Object
```python
s3.copy_object(
    Bucket='dest-bucket',
    CopySource={'Bucket': 'source-bucket', 'Key': 'file.txt'},
    Key='file.txt'
)
```

### Check If Object Exists
```python
try:
    s3.head_object(Bucket='my-bucket', Key='file.txt')
    print("File exists")
except s3.exceptions.NoSuchKey:
    print("File doesn't exist")
```

### Get Object ETag
```python
response = s3.head_object(Bucket='my-bucket', Key='file.txt')
etag = response['ETag']  # "5d41402abc4b2a76b9719d911017c592"
```

### Multipart Upload
```python
# For large files, use upload_fileobj (automatic multipart)
with open('large-file.zip', 'rb') as f:
    s3.upload_fileobj(f, 'my-bucket', 'large-file.zip')
```

---

## EC2: Common Operations

### List Instances
```python
ec2 = boto3.client('ec2')

# All instances
response = ec2.describe_instances()
for r in response['Reservations']:
    for instance in r['Instances']:
        print(f"{instance['InstanceId']}: {instance['State']['Name']}")

# Running only
response = ec2.describe_instances(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)
```

### Launch Instance
```python
response = ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',  # Amazon Linux 2
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro'
)
instance_id = response['Instances'][0]['InstanceId']
```

### Wait for Running
```python
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=['i-1234567890abcdef0'])
```

### Stop Instance
```python
ec2.stop_instances(InstanceIds=['i-1234567890abcdef0'])
```

### Terminate Instance
```python
ec2.terminate_instances(InstanceIds=['i-1234567890abcdef0'])
```

### Create Security Group
```python
response = ec2.create_security_group(
    GroupName='web-sg',
    Description='Web server security group',
    VpcId='vpc-12345'
)
sg_id = response['GroupId']

# Add HTTP rule
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }]
)
```

### Add Tags
```python
ec2.create_tags(
    Resources=['i-1234567890abcdef0'],
    Tags=[
        {'Key': 'Name', 'Value': 'my-server'},
        {'Key': 'Environment', 'Value': 'prod'}
    ]
)
```

### Get Instance By Tag
```python
response = ec2.describe_instances(
    Filters=[{'Name': 'tag:Name', 'Values': ['my-server']}]
)
```

---

## Lambda: Common Operations

### Invoke Function
```python
lambda_client = boto3.client('lambda')

# Synchronous invocation
response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='RequestResponse',  # Wait for response
    Payload='{"key": "value"}'
)

result = json.loads(response['Payload'].read())
print(result)
```

### Invoke Async
```python
# Fire and forget
lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='Event'  # Async
)
```

### List Functions
```python
response = lambda_client.list_functions()
for func in response['Functions']:
    print(f"{func['FunctionName']}: {func['Runtime']}")
```

### Update Function Code
```python
with open('lambda_function.zip', 'rb') as f:
    lambda_client.update_function_code(
        FunctionName='my-function',
        ZipFile=f.read()
    )
```

### Update Configuration
```python
lambda_client.update_function_configuration(
    FunctionName='my-function',
    Timeout=60,      # seconds
    MemorySize=256,  # MB
    Environment={'Variables': {'KEY': 'value'}}
)
```

### Create Function
```python
with open('lambda_function.zip', 'rb') as f:
    response = lambda_client.create_function(
        FunctionName='my-function',
        Runtime='python3.11',
        Role='arn:aws:iam::123456789:role/lambda-role',
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': f.read()}
    )
```

---

## DynamoDB: Common Operations

### Put Item
```python
dynamodb = boto3.client('dynamodb')

dynamodb.put_item(
    TableName='Users',
    Item={
        'id': {'S': 'user123'},
        'name': {'S': 'Alice'},
        'email': {'S': 'alice@example.com'}
    }
)
```

### Get Item
```python
response = dynamodb.get_item(
    TableName='Users',
    Key={'id': {'S': 'user123'}}
)
item = response['Item']
print(item['name']['S'])  # 'Alice'
```

### Query Items
```python
response = dynamodb.query(
    TableName='Users',
    KeyConditionExpression='id = :id',
    ExpressionAttributeValues={':id': {'S': 'user123'}}
)
for item in response['Items']:
    print(item)
```

### Scan All Items
```python
response = dynamodb.scan(TableName='Users')
for item in response['Items']:
    print(item)
```

### Update Item
```python
dynamodb.update_item(
    TableName='Users',
    Key={'id': {'S': 'user123'}},
    UpdateExpression='SET email = :email',
    ExpressionAttributeValues={':email': {'S': 'newemail@example.com'}}
)
```

### Delete Item
```python
dynamodb.delete_item(
    TableName='Users',
    Key={'id': {'S': 'user123'}}
)
```

### Using Resource (simpler)
```python
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

# Put
table.put_item(Item={'id': 'user123', 'name': 'Alice'})

# Get
response = table.get_item(Key={'id': 'user123'})
print(response['Item'])

# Update
table.update_item(
    Key={'id': 'user123'},
    UpdateExpression='SET email = :email',
    ExpressionAttributeValues={':email': 'new@example.com'}
)
```

---

## RDS: Common Operations

### List Databases
```python
rds = boto3.client('rds')

response = rds.describe_db_instances()
for db in response['DBInstances']:
    print(f"{db['DBInstanceIdentifier']}: {db['DBInstanceStatus']}")
```

### Create Database
```python
response = rds.create_db_instance(
    DBInstanceIdentifier='mydb',
    DBInstanceClass='db.t2.micro',
    Engine='postgres',
    MasterUsername='admin',
    MasterUserPassword='MyPassword123',
    AllocatedStorage=20
)
```

### Wait for Available
```python
waiter = rds.get_waiter('db_instance_available')
waiter.wait(DBInstanceIdentifier='mydb')
```

### Get Connection Details
```python
response = rds.describe_db_instances(DBInstanceIdentifier='mydb')
db = response['DBInstances'][0]
print(f"Host: {db['Endpoint']['Address']}")
print(f"Port: {db['Endpoint']['Port']}")
```

### Create Snapshot
```python
rds.create_db_snapshot(
    DBSnapshotIdentifier='mydb-backup',
    DBInstanceIdentifier='mydb'
)
```

### Restore from Snapshot
```python
rds.restore_db_instance_from_db_snapshot(
    DBInstanceIdentifier='mydb-restored',
    DBSnapshotIdentifier='mydb-backup'
)
```

---

## CloudWatch: Common Operations

### Put Metric
```python
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='MyApp',
    MetricData=[{
        'MetricName': 'ProcessingTime',
        'Value': 45.5,
        'Unit': 'Milliseconds'
    }]
)
```

### Get Metrics
```python
from datetime import datetime, timedelta

response = cloudwatch.get_metric_statistics(
    Namespace='MyApp',
    MetricName='ProcessingTime',
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300,  # 5 minutes
    Statistics=['Average', 'Maximum']
)

for point in response['Datapoints']:
    print(f"{point['Timestamp']}: {point['Average']}")
```

### Create Alarm
```python
cloudwatch.put_metric_alarm(
    AlarmName='HighProcessingTime',
    MetricName='ProcessingTime',
    Namespace='MyApp',
    Statistic='Average',
    Period=300,
    EvaluationPeriods=2,
    Threshold=100,
    ComparisonOperator='GreaterThanThreshold'
)
```

### Delete Alarm
```python
cloudwatch.delete_alarms(AlarmNames=['HighProcessingTime'])
```

---

## Error Handling Patterns

### Basic Try-Except
```python
from botocore.exceptions import ClientError

try:
    s3.get_object(Bucket='my-bucket', Key='file.txt')
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchKey':
        print("File not found")
    else:
        print(f"Error: {error_code}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### With Retry
```python
import time
from botocore.exceptions import ClientError

def retry_operation(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            raise

result = retry_operation(
    lambda: s3.list_objects_v2(Bucket='my-bucket')
)
```

### With Auto-Retry Config
```python
from botocore.config import Config

config = Config(
    retries={'max_attempts': 3, 'mode': 'adaptive'}
)
s3 = boto3.client('s3', config=config)
# Retries happen automatically
```

---

## Pagination Patterns

### Client with Paginator
```python
s3 = boto3.client('s3')

paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket='my-bucket')

for page in pages:
    for obj in page.get('Contents', []):
        print(obj['Key'])
```

### Resource (Automatic)
```python
s3 = boto3.resource('s3')
bucket = s3.Bucket('my-bucket')

for obj in bucket.objects.all():
    print(obj.key)
```

### Manual with ContinuationToken
```python
s3 = boto3.client('s3')
continuation_token = None

while True:
    if continuation_token:
        response = s3.list_objects_v2(
            Bucket='my-bucket',
            ContinuationToken=continuation_token
        )
    else:
        response = s3.list_objects_v2(Bucket='my-bucket')

    for obj in response.get('Contents', []):
        print(obj['Key'])

    if response.get('IsTruncated'):
        continuation_token = response['NextContinuationToken']
    else:
        break
```

---

## Waiter Patterns

### Wait for Instance
```python
ec2 = boto3.client('ec2')
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=['i-1234567890abcdef0'])
```

### Wait for S3 Object
```python
s3 = boto3.client('s3')
waiter = s3.get_waiter('object_exists')
waiter.wait(Bucket='my-bucket', Key='file.txt')
```

### With Timeout
```python
waiter.wait(
    InstanceIds=['i-1234567890abcdef0'],
    WaiterConfig={
        'Delay': 15,      # Check every 15 seconds
        'MaxAttempts': 40 # Max 10 minutes
    }
)
```

### List Available Waiters
```python
s3 = boto3.client('s3')
print(s3.waiter_names)
# ['bucket_exists', 'bucket_not_exists', 'object_exists', 'object_not_exists']
```

---

## Session Patterns

### Default Session
```python
import boto3

# Uses credentials from environment/config
s3 = boto3.client('s3')
```

### Specific Profile
```python
session = boto3.Session(profile_name='production')
s3 = session.client('s3')
```

### Assume Role (Cross-Account)
```python
sts = boto3.client('sts')

response = sts.assume_role(
    RoleArn='arn:aws:iam::987654321:role/RemoteRole',
    RoleSessionName='session-name'
)

credentials = response['Credentials']
session = boto3.Session(
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)

s3 = session.client('s3')
```

### Specific Region
```python
session = boto3.Session(region_name='eu-west-1')
s3 = session.client('s3')

# Or in client
s3 = boto3.client('s3', region_name='eu-west-1')
```

### Custom Credentials
```python
session = boto3.Session(
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET',
    region_name='us-east-1'
)
```

---

## Configuration Patterns

### Increase Timeouts
```python
from botocore.config import Config

config = Config(
    connect_timeout=60,
    read_timeout=60
)
s3 = boto3.client('s3', config=config)
```

### Enable Retries
```python
from botocore.config import Config

config = Config(
    retries={'max_attempts': 5, 'mode': 'adaptive'}
)
s3 = boto3.client('s3', config=config)
```

### Max Connection Pool
```python
from botocore.config import Config

config = Config(max_pool_connections=20)
s3 = boto3.client('s3', config=config)
```

### Combined Config
```python
from botocore.config import Config

config = Config(
    max_pool_connections=20,
    connect_timeout=60,
    read_timeout=60,
    retries={'max_attempts': 3, 'mode': 'adaptive'}
)
s3 = boto3.client('s3', config=config)
```

---

## Common Code Patterns

### Batch Upload
```python
import os
import boto3

s3 = boto3.client('s3')

for filename in os.listdir('/path/to/files'):
    filepath = os.path.join('/path/to/files', filename)
    if os.path.isfile(filepath):
        s3.upload_file(filepath, 'my-bucket', filename)
        print(f"Uploaded {filename}")
```

### Batch Download
```python
s3 = boto3.client('s3')

paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket='my-bucket'):
    for obj in page.get('Contents', []):
        s3.download_file('my-bucket', obj['Key'], f"local/{obj['Key']}")
```

### Batch Delete
```python
s3 = boto3.client('s3')

response = s3.list_objects_v2(Bucket='my-bucket')
for obj in response.get('Contents', []):
    s3.delete_object(Bucket='my-bucket', Key=obj['Key'])
    print(f"Deleted {obj['Key']}")
```

### Filter by Tag
```python
ec2 = boto3.client('ec2')

response = ec2.describe_instances(
    Filters=[
        {'Name': 'tag:Environment', 'Values': ['production']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
)

for r in response['Reservations']:
    for instance in r['Instances']:
        print(instance['InstanceId'])
```

### Parallel Operations
```python
from concurrent.futures import ThreadPoolExecutor

def download_file(bucket, key):
    s3.download_file(bucket, key, f'local/{key}')

s3 = boto3.client('s3')
files = [('bucket', f'file{i}.txt') for i in range(10)]

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(lambda args: download_file(*args), files)
```

---

## Service Cheat Sheet

| Service | Create | Read | Update | Delete |
|---------|--------|------|--------|--------|
| **S3** | `put_object` | `get_object` | `put_object` | `delete_object` |
| **EC2** | `run_instances` | `describe_instances` | `modify_instance` | `terminate_instances` |
| **Lambda** | `create_function` | `get_function` | `update_function_code` | `delete_function` |
| **DynamoDB** | `put_item` | `get_item` | `update_item` | `delete_item` |
| **RDS** | `create_db_instance` | `describe_db_instances` | `modify_db_instance` | `delete_db_instance` |
| **SNS** | `create_topic` | `list_topics` | `set_topic_attributes` | `delete_topic` |
| **SQS** | `create_queue` | `list_queues` | `set_queue_attributes` | `delete_queue` |
| **IAM** | `create_user` | `get_user` | `update_user` | `delete_user` |

---

## Debugging Quick Checks

```python
# Check credentials
sts = boto3.client('sts')
print(sts.get_caller_identity())

# Check region
session = boto3.Session()
print(session.region_name)

# List available services
print(session.get_available_services())

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Resources

- **Docs**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **Examples**: https://github.com/aws/aws-sdk-examples
- **LocalStack**: https://localstack.cloud/ (test locally)

---

**Last Updated**: 2024
**Target Audience**: AWS developers needing quick reference
**Estimated Reading Time**: 15-30 minutes to scan, seconds to lookup
