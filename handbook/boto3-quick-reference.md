# Boto3 Quick Reference: 30-60 Second Answers

> **TL;DR for Boto3**: Quick syntax lookups for common operations. No explanations, just code you can copy-paste.

---

## Table of Contents
- [Setup](#setup)
- [Client vs Resource](#client-vs-resource)
- [S3](#s3)
- [Lambda](#lambda)
- [EC2](#ec2)
- [RDS](#rds)
- [DynamoDB](#dynamodb)
- [SQS](#sqs)
- [SNS](#sns)
- [CloudWatch](#cloudwatch)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [Waiters](#waiters)
- [Sessions](#sessions)

---

## Setup

```python
# Basic setup
import boto3

# Client (low-level)
s3 = boto3.client('s3', region_name='us-east-1')

# Resource (high-level, object-oriented)
s3_resource = boto3.resource('s3', region_name='us-east-1')

# Get credentials info
sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(identity['Account'], identity['Arn'], identity['UserId'])
```

---

## Client vs Resource

| Operation | Client | Resource |
|-----------|--------|----------|
| **List S3 buckets** | `s3.list_buckets()` | `[b.name for b in s3.buckets.all()]` |
| **Upload file** | `s3.upload_file(...)` | `bucket.upload_file(...)` |
| **Get DynamoDB item** | `dynamodb.get_item(...)` | `table.get_item(...)` |
| **Advanced filters** | ✓ Yes | ✗ No |
| **Simple operations** | Verbose | Clean |

---

## S3

### Basics
```python
s3 = boto3.client('s3')

# Create bucket
s3.create_bucket(Bucket='my-bucket')

# List buckets
s3.list_buckets()['Buckets']

# List objects
s3.list_objects_v2(Bucket='my-bucket')['Contents']

# Upload
s3.upload_file('local.txt', 'my-bucket', 'remote.txt')

# Download
s3.download_file('my-bucket', 'remote.txt', 'local.txt')

# Get object
response = s3.get_object(Bucket='my-bucket', Key='file.txt')
content = response['Body'].read()

# Put object
s3.put_object(Bucket='my-bucket', Key='file.txt', Body=b'content')

# Delete object
s3.delete_object(Bucket='my-bucket', Key='file.txt')

# Delete bucket
s3.delete_bucket(Bucket='my-bucket')

# Check if bucket exists
try:
    s3.head_bucket(Bucket='my-bucket')
    print("Exists")
except:
    print("Doesn't exist")
```

### Metadata & Tags
```python
# Get object metadata
response = s3.head_object(Bucket='my-bucket', Key='file.txt')
print(response['ContentLength'], response['LastModified'])

# Upload with metadata
s3.put_object(
    Bucket='my-bucket',
    Key='file.txt',
    Body=b'content',
    Metadata={'key': 'value'}
)

# Get metadata
response = s3.head_object(Bucket='my-bucket', Key='file.txt')
print(response['Metadata'])
```

### Presigned URLs
```python
# Download URL (1 hour)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'file.txt'},
    ExpiresIn=3600
)

# Upload URL
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'file.txt'},
    ExpiresIn=3600
)
```

### S3 Select (Query)
```python
response = s3.select_object_content(
    Bucket='my-bucket',
    Key='data.csv',
    ExpressionType='SQL',
    Expression='SELECT * FROM s3object WHERE amount > 100',
    InputSerialization={'CSV': {'FileHeaderInfo': 'Use'}},
    OutputSerialization={'CSV': {}}
)

for event in response['Payload']:
    if 'Records' in event:
        print(event['Records']['Payload'].decode('utf-8'))
```

### Using Resource (Cleaner)
```python
s3 = boto3.resource('s3')

# List buckets
for bucket in s3.buckets.all():
    print(bucket.name)

# Get bucket
bucket = s3.Bucket('my-bucket')

# List objects
for obj in bucket.objects.all():
    print(obj.key, obj.size)

# Upload
bucket.upload_file('local.txt', 'remote.txt')

# Download
bucket.download_file('remote.txt', 'local.txt')
```

---

## Lambda

### Functions
```python
lamb = boto3.client('lambda')

# Create function
lamb.create_function(
    FunctionName='my-function',
    Runtime='python3.11',
    Role='arn:aws:iam::ACCOUNT:role/lambda-role',
    Handler='index.handler',
    Code={'ZipFile': b'code_bytes'},
    Timeout=30,
    MemorySize=128
)

# Update code
lamb.update_function_code(
    FunctionName='my-function',
    ZipFile=b'new_code'
)

# Update config
lamb.update_function_configuration(
    FunctionName='my-function',
    Timeout=60,
    MemorySize=256
)

# Delete
lamb.delete_function(FunctionName='my-function')

# Describe
lamb.get_function(FunctionName='my-function')

# List
lamb.list_functions()['Functions']
```

### Invoke
```python
# Synchronous
response = lamb.invoke(
    FunctionName='my-function',
    InvocationType='RequestResponse',
    Payload=json.dumps({'key': 'value'})
)
result = json.loads(response['Payload'].read())

# Asynchronous (fire and forget)
lamb.invoke(
    FunctionName='my-function',
    InvocationType='Event',
    Payload=json.dumps({'key': 'value'})
)
```

### Layers
```python
# Publish layer
response = lamb.publish_layer_version(
    LayerName='my-layer',
    Content={'ZipFile': b'code'},
    CompatibleRuntimes=['python3.11']
)

# Add to function
lamb.update_function_configuration(
    FunctionName='my-function',
    Layers=[response['LayerVersionArn']]
)
```

---

## EC2

### Instances
```python
ec2 = boto3.client('ec2')

# Launch
response = ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro'
)
instance_id = response['Instances'][0]['InstanceId']

# Describe
ec2.describe_instances(InstanceIds=[instance_id])

# Stop
ec2.stop_instances(InstanceIds=[instance_id])

# Start
ec2.start_instances(InstanceIds=[instance_id])

# Terminate
ec2.terminate_instances(InstanceIds=[instance_id])

# Wait for running
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
```

### Tags
```python
# Add tags
ec2.create_tags(
    Resources=[instance_id],
    Tags=[
        {'Key': 'Environment', 'Value': 'prod'},
        {'Key': 'Name', 'Value': 'web-server'}
    ]
)

# Filter by tag
response = ec2.describe_instances(
    Filters=[
        {'Name': 'tag:Environment', 'Values': ['prod']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
)
```

### Security Groups
```python
# Create
sg = ec2.create_security_group(
    GroupName='web-sg',
    Description='Web server SG',
    VpcId='vpc-123'
)
sg_id = sg['GroupId']

# Add rule
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)

# Remove rule
ec2.revoke_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[...]
)

# Describe
ec2.describe_security_groups(GroupIds=[sg_id])

# Delete
ec2.delete_security_group(GroupId=sg_id)
```

---

## RDS

### Instances
```python
rds = boto3.client('rds')

# Create
rds.create_db_instance(
    DBInstanceIdentifier='mydb',
    DBInstanceClass='db.t3.micro',
    Engine='mysql',
    MasterUsername='admin',
    MasterUserPassword='password123',
    AllocatedStorage=20
)

# Wait
waiter = rds.get_waiter('db_instance_available')
waiter.wait(DBInstanceIdentifier='mydb')

# Describe
rds.describe_db_instances(DBInstanceIdentifier='mydb')

# Modify
rds.modify_db_instance(
    DBInstanceIdentifier='mydb',
    AllocatedStorage=50,
    ApplyImmediately=True
)

# Delete
rds.delete_db_instance(
    DBInstanceIdentifier='mydb',
    SkipFinalSnapshot=True
)
```

### Snapshots
```python
# Create snapshot
rds.create_db_snapshot(
    DBSnapshotIdentifier='mydb-backup',
    DBInstanceIdentifier='mydb'
)

# Restore
rds.restore_db_instance_from_db_snapshot(
    DBInstanceIdentifier='mydb-restored',
    DBSnapshotIdentifier='mydb-backup'
)

# List snapshots
rds.describe_db_snapshots(DBInstanceIdentifier='mydb')

# Delete snapshot
rds.delete_db_snapshot(DBSnapshotIdentifier='mydb-backup')
```

---

## DynamoDB

### Client (Low-level)
```python
ddb = boto3.client('dynamodb')

# Create table
ddb.create_table(
    TableName='users',
    KeySchema=[
        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'user_id', 'AttributeType': 'S'},
        {'AttributeName': 'timestamp', 'AttributeType': 'N'}
    ],
    BillingMode='PAY_PER_REQUEST'
)

# Put item
ddb.put_item(
    TableName='users',
    Item={
        'user_id': {'S': 'user_123'},
        'name': {'S': 'Alice'},
        'age': {'N': '30'}
    }
)

# Get item
ddb.get_item(
    TableName='users',
    Key={'user_id': {'S': 'user_123'}}
)

# Query
ddb.query(
    TableName='users',
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': {'S': 'user_123'}}
)

# Scan
ddb.scan(TableName='users')

# Delete item
ddb.delete_item(
    TableName='users',
    Key={'user_id': {'S': 'user_123'}}
)

# Delete table
ddb.delete_table(TableName='users')
```

### Resource (High-level)
```python
ddb = boto3.resource('dynamodb')

# Get table
table = ddb.Table('users')

# Put item (simpler)
table.put_item(Item={'user_id': 'user_123', 'name': 'Alice', 'age': 30})

# Get item
table.get_item(Key={'user_id': 'user_123'})

# Query
table.query(
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': 'user_123'}
)

# Scan
table.scan()

# Update item
table.update_item(
    Key={'user_id': 'user_123'},
    UpdateExpression='SET #n = :name',
    ExpressionAttributeNames={'#n': 'name'},
    ExpressionAttributeValues={':name': 'Bob'}
)
```

---

## SQS

### Queue Operations
```python
sqs = boto3.client('sqs')

# Create queue
response = sqs.create_queue(
    QueueName='my-queue',
    Attributes={
        'VisibilityTimeout': '300',
        'MessageRetentionPeriod': '86400'
    }
)
queue_url = response['QueueUrl']

# Send message
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({'key': 'value'})
)

# Send batch
sqs.send_message_batch(
    QueueUrl=queue_url,
    Entries=[
        {'Id': '1', 'MessageBody': json.dumps({'id': 1})},
        {'Id': '2', 'MessageBody': json.dumps({'id': 2})}
    ]
)

# Receive messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)

for msg in response.get('Messages', []):
    print(json.loads(msg['Body']))
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=msg['ReceiptHandle']
    )

# Delete queue
sqs.delete_queue(QueueUrl=queue_url)
```

### FIFO Queue
```python
# Create FIFO
response = sqs.create_queue(
    QueueName='my-queue.fifo',
    Attributes={'FifoQueue': 'true'}
)

# Send to FIFO
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({'data': 'value'}),
    MessageGroupId='group-1',
    MessageDeduplicationId='unique-id'
)
```

---

## SNS

### Topics & Messages
```python
sns = boto3.client('sns')

# Create topic
response = sns.create_topic(Name='my-topic')
topic_arn = response['TopicArn']

# Subscribe
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='user@example.com'
)

# Publish
sns.publish(
    TopicArn=topic_arn,
    Message='Hello',
    Subject='Alert'
)

# Delete topic
sns.delete_topic(TopicArn=topic_arn)
```

---

## CloudWatch

### Metrics
```python
cw = boto3.client('cloudwatch')

# Put metric
cw.put_metric_data(
    Namespace='MyApp',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': 45.5,
            'Unit': 'Milliseconds',
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'prod'}
            ]
        }
    ]
)

# Get metrics
cw.get_metric_statistics(
    Namespace='AWS/EC2',
    MetricName='CPUUtilization',
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300,
    Statistics=['Average', 'Maximum']
)
```

### Alarms
```python
# Create alarm
cw.put_metric_alarm(
    AlarmName='high-cpu',
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Period=300,
    EvaluationPeriods=2,
    Threshold=80.0,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:ACCOUNT:topic']
)

# Delete alarm
cw.delete_alarms(AlarmNames=['high-cpu'])
```

---

## Error Handling

### Basic
```python
from botocore.exceptions import ClientError

try:
    s3.get_object(Bucket='bucket', Key='key')
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchBucket':
        print("Bucket not found")
    elif error_code == 'AccessDenied':
        print("Permission denied")
    else:
        raise
```

### With Retry
```python
import time

def call_with_retry(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except ClientError as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)
```

### Specific Errors
```python
from botocore.exceptions import (
    NoCredentialsError,
    ConnectionError,
    Waiter
)

try:
    s3.list_buckets()
except NoCredentialsError:
    print("Configure AWS credentials")
except ConnectionError:
    print("Network error")
```

---

## Pagination

### Using Paginator
```python
s3 = boto3.client('s3')

# Get paginator
paginator = s3.get_paginator('list_objects_v2')

# Paginate
page_iterator = paginator.paginate(
    Bucket='my-bucket',
    PaginationConfig={'PageSize': 100}
)

for page in page_iterator:
    for obj in page.get('Contents', []):
        print(obj['Key'])
```

---

## Waiters

### Common Waiters
```python
# EC2 instance running
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=['i-123'])

# S3 bucket exists
waiter = s3.get_waiter('bucket_exists')
waiter.wait(Bucket='my-bucket')

# RDS available
waiter = rds.get_waiter('db_instance_available')
waiter.wait(DBInstanceIdentifier='mydb')

# Lambda function exists
waiter = lamb.get_waiter('function_exists')
waiter.wait(FunctionName='my-function')

# With custom config
waiter.wait(
    InstanceIds=['i-123'],
    WaiterConfig={'Delay': 10, 'MaxAttempts': 60}
)
```

---

## Sessions

### Create Session
```python
from boto3 import Session

# Default session
session = Session()

# Custom credentials
session = Session(
    aws_access_key_id='KEY',
    aws_secret_access_key='SECRET',
    region_name='us-east-1'
)

# Named profile
session = Session(profile_name='production')

# Create clients from session
s3 = session.client('s3')
ec2 = session.resource('ec2')
```

### Cross-Account (AssumeRole)
```python
sts = boto3.client('sts')

response = sts.assume_role(
    RoleArn='arn:aws:iam::ACCOUNT:role/Role',
    RoleSessionName='session',
    DurationSeconds=3600
)

creds = response['Credentials']
session = Session(
    aws_access_key_id=creds['AccessKeyId'],
    aws_secret_access_key=creds['SecretAccessKey'],
    aws_session_token=creds['SessionToken']
)

s3 = session.client('s3')
```

---

## Cheat Sheet by Use Case

### "I want to upload a file"
```python
s3 = boto3.client('s3')
s3.upload_file('local.txt', 'bucket', 'remote.txt')
# or
s3 = boto3.resource('s3')
s3.Bucket('bucket').upload_file('local.txt', 'remote.txt')
```

### "I want to list all resources"
```python
# S3 buckets
s3.list_buckets()['Buckets']

# EC2 instances
ec2.describe_instances()

# Lambda functions
lamb.list_functions()['Functions']

# RDS databases
rds.describe_db_instances()['DBInstances']
```

### "I want to handle errors"
```python
from botocore.exceptions import ClientError

try:
    # AWS operation
except ClientError as e:
    if e.response['Error']['Code'] == 'TargetError':
        # Handle specific error
    else:
        raise
```

### "I want to wait for something"
```python
# Get waiter
waiter = ec2.get_waiter('instance_running')

# Wait with timeout
waiter.wait(InstanceIds=['i-123'], WaiterConfig={'MaxAttempts': 30})

# Now safe to use
print("Instance is running!")
```

### "I want to do many operations"
```python
# Use batch operations
sqs.send_message_batch(QueueUrl=url, Entries=[...])  # Up to 10
ec2.create_tags(Resources=[...], Tags=[...])  # Many resources
ddb.batch_write_item(RequestItems={...})  # Many items
```

---

## Common Imports

```python
import boto3
from boto3 import Session
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import json
from datetime import datetime, timedelta
import time
```

