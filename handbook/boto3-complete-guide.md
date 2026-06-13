# Boto3 Complete Guide
## Quick Reference + Comprehensive Learning (30 seconds to 4 hours)

### Table of Contents
**PART 0: QUICK REFERENCE** (30-60 second lookups)
- Client vs Resource Decision
- S3, EC2, Lambda, DynamoDB, RDS, CloudWatch Operations
- Error Handling, Pagination, Waiters
- Session Management, Configuration Patterns

**PART 1: FOUNDATIONS** (2-3 hours)
- Chapter 1: Boto3 Architecture
- Chapter 2: Core Patterns

**PART 2: SERVICE DEEP DIVES** (3-4 hours)
- Chapter 3: EC2 with Boto3
- Chapter 4: RDS with Boto3
- Chapter 5: CloudWatch with Boto3
- Chapter 6: ECS/Fargate with Boto3
- Chapter 7: Advanced S3 Patterns

**PART 3: ADVANCED PATTERNS** (2-3 hours)
- Chapter 8: Multi-Account & Cross-Region
- Chapter 9: Performance Optimization
- Chapter 10: Production Best Practices

**APPENDIX**: Common Services Reference

---

# PART 0: QUICK REFERENCE
## 30-60 Second Lookup for Common Operations

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

# PART 1: FOUNDATIONS

### Chapter 1: Boto3 Architecture

#### The Basics: What is Boto3?

Boto3 is the AWS SDK for Python. It allows you to write Python code that interacts with AWS services like S3, EC2, Lambda, and 200+ other services.

**History Note**: Boto derives its name from the Portuguese word for a type of dolphin native to the Amazon River. The name stuck because it swims in the Amazon (AWS), and someone thought it was clever.

**Official Resources**:
- [AWS SDK for Python Documentation](https://docs.aws.amazon.com/pythonsdk/)
- [Boto3 API Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html)

#### Mental Model: Boto3 = Phone Line to AWS

Think of Boto3 as a phone line to AWS:
- **AWS Services** = People at AWS offices (S3, EC2, Lambda, etc.)
- **Boto3 Client** = Direct phone line - you speak to the person directly (technical, low-level)
- **Boto3 Resource** = Phone receptionist - they handle details for you (simpler, higher-level)
- **Session** = Your phone account - credentials + region configuration

#### Client vs Resource: The Core Decision

This is THE most important decision you'll make when using Boto3. Choose wrong, and you'll write verbose or awkward code.

##### When to Use Client (Low-Level)

**Use Client when you need**:
- Complete control over AWS API parameters
- Access to ALL service operations
- Direct mapping to AWS API documentation
- Building custom abstractions
- Services without Resource support

**Client Characteristics**:
- Maps 1:1 to AWS API
- More verbose
- More powerful and flexible
- Returns dictionaries
- Required for less common operations

**Example: S3 Client**:
```python
import boto3

client = boto3.client('s3')

# Upload a file
response = client.put_object(
    Bucket='my-bucket',
    Key='data.txt',
    Body=b'Hello, World!'
)

# List objects
response = client.list_objects_v2(Bucket='my-bucket')
for obj in response.get('Contents', []):
    print(obj['Key'])
```

**When This is Better**:
- Uploading to S3 with specific metadata
- Configuring advanced options (SSE, ACLs, etc.)
- Building automation tools
- Accessing every AWS API parameter

##### When to Use Resource (High-Level)

**Use Resource when you want**:
- Simpler, more Pythonic code
- Object-oriented interface
- Less boilerplate
- Quick prototyping
- Clear relationships (Bucket → Object → Content)

**Resource Characteristics**:
- Higher abstraction level
- Cleaner code
- Manages pagination automatically
- Returns objects (not just dicts)
- Simpler learning curve

**Example: S3 Resource**:
```python
import boto3

s3 = boto3.resource('s3')

# Upload a file
bucket = s3.Bucket('my-bucket')
bucket.put_object(Key='data.txt', Body=b'Hello, World!')

# List objects
for obj in bucket.objects.all():
    print(obj.key)
```

**When This is Better**:
- Quick scripts and prototyping
- Standard operations (upload, download, list)
- Learning AWS with Boto3
- Working with related objects (iterate bucket → objects)

##### Quick Comparison Table

| Feature | Client | Resource |
|---------|--------|----------|
| **API Mapping** | 1:1 with AWS | Higher abstraction |
| **Code Length** | Verbose | Concise |
| **Learning Curve** | Steeper | Gentle |
| **Operations** | All AWS operations | Common operations |
| **Return Type** | Dictionary | Python objects |
| **Flexibility** | Maximum | Good |
| **Best For** | Production, automation | Learning, prototyping |
| **Example** | `put_object()` | `bucket.put_object()` |

**Real Example: EC2**:
```python
# CLIENT: List instances by state
client = boto3.client('ec2')
response = client.describe_instances(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(instance['InstanceId'])

# RESOURCE: List instances by state
ec2 = boto3.resource('ec2')
running_instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)
for instance in running_instances:
    print(instance.id)
```

#### Sessions: Your AWS Identity

A Session stores AWS credentials and configuration. It's how Boto3 knows WHO you are and WHERE (region) you're accessing.

**Default Session** (easiest):
```python
import boto3

# Uses default AWS credentials automatically
s3 = boto3.client('s3')
ec2 = boto3.client('ec2')
```

**Custom Session** (explicit control):
```python
import boto3

# Create explicit session with specific profile
session = boto3.Session(profile_name='my-profile')
s3 = session.client('s3')
ec2 = session.client('ec2', region_name='us-west-2')
```

**Session Configuration Sources** (checked in order):
1. Parameters passed to Session()
2. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
3. ~/.aws/credentials (AWS credentials file)
4. ~/.aws/config (AWS configuration file)
5. IAM role (if running on EC2)

**Session Attributes**:
```python
session = boto3.Session()

print(session.get_credentials())      # AccessKey, SecretKey, Token
print(session.get_config_variable('region'))  # Current region
print(session.available_services)     # All available AWS services
```

#### Configuration: Where Credentials Come From

Boto3 looks for credentials in this order:
1. **Passed to Session/Client**: `boto3.client('s3', aws_access_key_id='...', aws_secret_access_key='...')`
2. **Environment Variables**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`
3. **Credentials File**: `~/.aws/credentials`
4. **Config File**: `~/.aws/config`
5. **IAM Role**: If running on EC2, ECS, Lambda, etc.

**Best Practice**:
```python
# DON'T: Hardcode credentials
client = boto3.client('s3', aws_access_key_id='...', aws_secret_access_key='...')

# DO: Use environment variables or IAM role
client = boto3.client('s3')

# DO: Use profiles for multiple accounts
session = boto3.Session(profile_name='prod-account')
client = session.client('s3')
```

#### Regions and Endpoints

Every AWS service runs in multiple regions. You specify which region you want to use.

**Standard Region Specification**:
```python
# Region in client call
s3_client = boto3.client('s3', region_name='us-east-1')

# Region in session
session = boto3.Session(region_name='eu-west-1')
s3 = session.client('s3')

# Environment variable
import os
os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-1'
client = boto3.client('s3')
```

**Region Naming**:
- `us-east-1` = N. Virginia (oldest, often cheapest)
- `us-west-2` = Oregon
- `eu-west-1` = Ireland
- `ap-southeast-1` = Singapore
- See [AWS Regions](https://docs.aws.amazon.com/general/latest/gr/rande.html) for complete list

**Get All Available Regions for a Service**:
```python
import boto3

client = boto3.client('ec2', region_name='us-east-1')
response = client.describe_regions()
for region in response['Regions']:
    print(f"{region['RegionName']}: {region['RegionEndpoint']}")
```

---

### Chapter 2: Core Patterns

#### Error Handling: Expect Things to Fail

AWS operations can fail for many reasons: invalid credentials, rate limiting, resource not found, etc. Always handle errors gracefully.

**Exception Hierarchy**:
```
botocore.exceptions.BotoCoreError (base exception)
├── ClientError (most common - something went wrong with your AWS call)
├── NoCredentialsError (can't find AWS credentials)
├── PartialCredentialsError (incomplete credentials)
├── InvalidConfigError (bad config)
└── ... (20+ other exceptions)
```

**Catching ClientError** (99% of what you need):
```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

try:
    s3.head_object(Bucket='my-bucket', Key='data.txt')
    print("File exists")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print("File not found")
    elif error_code == 'AccessDenied':
        print("No permission to access bucket")
    else:
        print(f"Unexpected error: {error_code}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**Common Error Codes**:
| Code | Meaning | Your Action |
|------|---------|------------|
| `NoCredentialsError` | AWS credentials not found | Check AWS_ACCESS_KEY_ID, ~/.aws/credentials |
| `AccessDenied` | IAM policy blocks operation | Check IAM permissions |
| `NoSuchBucket` | S3 bucket doesn't exist | Verify bucket name and region |
| `ThrottlingException` | Too many requests | Implement exponential backoff |
| `RequestLimitExceeded` | Service limit hit | Add delays, use async |
| `InvalidParameterValue` | Bad parameter | Check API docs for valid values |

**Retry Pattern with Exponential Backoff**:
```python
import time
from botocore.exceptions import ClientError

def retry_operation(operation, max_attempts=3):
    """Retry an operation with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return operation()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait_time = 2 ** attempt  # 1, 2, 4 seconds
                print(f"Throttled. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception(f"Failed after {max_attempts} attempts")

# Usage
response = retry_operation(
    lambda: s3.list_objects_v2(Bucket='my-bucket')
)
```

**Better: Use Boto3's Built-in Retries**:
```python
from botocore.config import Config

# Configure automatic retries
config = Config(retries={'max_attempts': 3, 'mode': 'adaptive'})
s3 = boto3.client('s3', config=config)

# Now automatic retries happen internally
response = s3.list_objects_v2(Bucket='my-bucket')
```

#### Pagination: Handling Large Result Sets

AWS limits response sizes to prevent overload. Use pagination to fetch all results.

**Without Pagination** (Wrong):
```python
# This only gets first 1000 objects!
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='my-bucket')
for obj in response.get('Contents', []):
    print(obj['Key'])
# Stops after 1000 if bucket has more
```

**Manual Pagination** (Works but tedious):
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

**Using Paginator** (Recommended):
```python
s3 = boto3.client('s3')

# Get paginator for this operation
paginator = s3.get_paginator('list_objects_v2')

# Create page iterator
pages = paginator.paginate(Bucket='my-bucket')

# Iterate through all pages
for page in pages:
    for obj in page.get('Contents', []):
        print(obj['Key'])
```

**Even Cleaner: build_full_result**:
```python
s3 = boto3.client('s3')
paginator = s3.get_paginator('list_objects_v2')

# Automatically handles pagination
for obj in paginator.paginate(Bucket='my-bucket').build_full_result().get('Contents', []):
    print(obj['Key'])
```

**Available Paginators** (check which operations support pagination):
```python
s3 = boto3.client('s3')
print(s3.can_paginate('list_objects_v2'))  # True
print(s3.can_paginate('put_object'))       # False (single operation)

# List all paginatable operations
print(s3.meta.service_model.operation_names)
```

**Pagination with Filtering**:
```python
paginator = s3.get_paginator('list_objects_v2')

# Filter only .txt files
pages = paginator.paginate(Bucket='my-bucket')
txt_files = []
for page in pages:
    for obj in page.get('Contents', []):
        if obj['Key'].endswith('.txt'):
            txt_files.append(obj['Key'])
```

#### Waiters: Waiting for Async Operations

Many AWS operations are asynchronous. Waiters poll the service until an operation completes.

**Mental Model**: Waiter = Automated "are we done yet?" polling

**Common Wait Scenarios**:
- EC2 instance starting up
- RDS database becoming available
- S3 object existing after creation
- Lambda function updating

**Using Waiters**:
```python
ec2 = boto3.client('ec2')

# Start instances
response = ec2.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=1)
instance_id = response['Instances'][0]['InstanceId']

# Wait for instance to be running
waiter = ec2.get_waiter('instance_running')
print("Waiting for instance to start...")
waiter.wait(InstanceIds=[instance_id])
print("Instance is running!")
```

**Available Waiters** (service specific):
```python
ec2 = boto3.client('ec2')
print(ec2.waiter_names)
# ['bundle_task_complete', 'conversion_task_cancelled', 'conversion_task_completed', ...]

# For S3
s3 = boto3.client('s3')
print(s3.waiter_names)
# ['bucket_exists', 'bucket_not_exists', 'object_exists', 'object_not_exists']
```

**Waiter Example: S3 Object Upload**:
```python
s3 = boto3.client('s3')

# Upload file
s3.put_object(Bucket='my-bucket', Key='data.txt', Body=b'Hello')

# Wait for object to be accessible
waiter = s3.get_waiter('object_exists')
waiter.wait(Bucket='my-bucket', Key='data.txt')
print("Object is now accessible!")
```

**Waiter Configuration** (timeout, delay):
```python
ec2 = boto3.client('ec2')
waiter = ec2.get_waiter('instance_running')

# Configure waiter behavior
waiter.wait(
    InstanceIds=['i-123456'],
    WaiterConfig={
        'Delay': 15,        # Check every 15 seconds (default: 15)
        'MaxAttempts': 40   # Max 40 checks = 10 minutes (default: 40)
    }
)
```

**Handling Waiter Timeouts**:
```python
from botocore.exceptions import WaiterError

ec2 = boto3.client('ec2')
waiter = ec2.get_waiter('instance_running')

try:
    waiter.wait(InstanceIds=['i-123456'])
except WaiterError as e:
    print(f"Instance failed to start: {e}")
    # Check instance status
    response = ec2.describe_instances(InstanceIds=['i-123456'])
    state = response['Reservations'][0]['Instances'][0]['State']
    print(f"Current state: {state['Name']}")
```

#### Response Structure Navigation

AWS API responses are dictionaries (for clients) or objects (for resources). Learning to navigate them is essential.

**Understanding Response Structure**:
```python
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='my-bucket')

# Response is a dictionary
print(type(response))  # <class 'dict'>
print(response.keys()) # dict_keys(['ResponseMetadata', 'Contents', ...])

# Access nested data
for obj in response.get('Contents', []):  # Use .get() to avoid KeyError
    print(f"Key: {obj['Key']}, Size: {obj['Size']} bytes")

# ResponseMetadata is always present
print(response['ResponseMetadata']['HTTPStatusCode'])  # 200
print(response['ResponseMetadata']['RequestId'])       # AWS request ID
```

**Safe Navigation Pattern** (always use .get()):
```python
# BAD: KeyError if 'Contents' doesn't exist
for obj in response['Contents']:
    print(obj['Key'])

# GOOD: .get() returns [] if Contents doesn't exist
for obj in response.get('Contents', []):
    print(obj['Key'])
```

**Resource Objects** (cleaner):
```python
s3 = boto3.resource('s3')
bucket = s3.Bucket('my-bucket')

# Objects are accessed as attributes
for obj in bucket.objects.all():
    print(f"Key: {obj.key}, Size: {obj.size}")

# Compare to client (dictionary access)
client = boto3.client('s3')
response = client.list_objects_v2(Bucket='my-bucket')
for obj in response['Contents']:
    print(f"Key: {obj['Key']}, Size: {obj['Size']}")
```

#### Batch Operations

Perform multiple operations efficiently using batch patterns.

**Batch Upload** (S3):
```python
s3 = boto3.client('s3')
import os

# Upload all files from directory
for filename in os.listdir('/path/to/files'):
    filepath = os.path.join('/path/to/files', filename)
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as f:
            s3.put_object(
                Bucket='my-bucket',
                Key=f'uploads/{filename}',
                Body=f
            )
        print(f"Uploaded {filename}")
```

**Batch Download** (S3):
```python
import boto3
import os

s3 = boto3.client('s3')

response = s3.list_objects_v2(Bucket='my-bucket', Prefix='data/')
for obj in response.get('Contents', []):
    # Download object
    filename = obj['Key'].split('/')[-1]
    s3.download_file('my-bucket', obj['Key'], f'/local/path/{filename}')
    print(f"Downloaded {filename}")
```

**Batch Delete**:
```python
s3 = boto3.client('s3')

# Delete up to 1000 objects in one call
objects_to_delete = [
    {'Key': 'file1.txt'},
    {'Key': 'file2.txt'},
    {'Key': 'file3.txt'}
]

response = s3.delete_objects(
    Bucket='my-bucket',
    Delete={'Objects': objects_to_delete}
)

# Check results
for deleted in response['Deleted']:
    print(f"Deleted {deleted['Key']}")

for error in response.get('Errors', []):
    print(f"Failed to delete {error['Key']}: {error['Message']}")
```

**Batch with Threading** (parallel operations):
```python
import boto3
from concurrent.futures import ThreadPoolExecutor

s3 = boto3.client('s3')

def upload_file(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        s3.put_object(Bucket='my-bucket', Key=filename, Body=f)
    return filename

files = ['/path/file1.txt', '/path/file2.txt', '/path/file3.txt']

# Upload 5 files in parallel
with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(upload_file, files)
    for filename in results:
        print(f"Uploaded {filename}")
```

---

# PART 2: SERVICE DEEP DIVES

### Chapter 3: EC2 with Boto3

#### Instance Lifecycle

EC2 instances go through several states. Understanding this is key to managing them.

**States**: pending → running → stopping → stopped → terminated

```python
import boto3

ec2 = boto3.client('ec2')

# 1. LAUNCH instances
response = ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',  # Amazon Linux 2
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [
            {'Key': 'Name', 'Value': 'my-server'},
            {'Key': 'Environment', 'Value': 'dev'}
        ]
    }]
)
instance_id = response['Instances'][0]['InstanceId']
print(f"Launched instance {instance_id}")

# 2. WAIT for instance to be running
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
print(f"Instance {instance_id} is running")

# 3. DESCRIBE instance details
response = ec2.describe_instances(InstanceIds=[instance_id])
instance = response['Reservations'][0]['Instances'][0]
print(f"Public IP: {instance.get('PublicIpAddress')}")
print(f"Private IP: {instance['PrivateIpAddress']}")
print(f"State: {instance['State']['Name']}")

# 4. STOP instance (can restart later)
ec2.stop_instances(InstanceIds=[instance_id])
waiter = ec2.get_waiter('instance_stopped')
waiter.wait(InstanceIds=[instance_id])
print(f"Instance {instance_id} stopped")

# 5. START instance again
ec2.start_instances(InstanceIds=[instance_id])
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
print(f"Instance {instance_id} restarted")

# 6. TERMINATE instance (permanent delete)
ec2.terminate_instances(InstanceIds=[instance_id])
print(f"Instance {instance_id} terminated")
```

#### Working with Security Groups

Security groups are like firewalls for EC2 instances.

```python
ec2 = boto3.client('ec2')

# CREATE security group
vpc_id = 'vpc-12345'  # Use your VPC ID
response = ec2.create_security_group(
    GroupName='web-server-sg',
    Description='Security group for web servers',
    VpcId=vpc_id
)
sg_id = response['GroupId']
print(f"Created security group {sg_id}")

# ADD INGRESS RULES (inbound traffic)
# Allow SSH from anywhere (not recommended for prod)
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH from anywhere'}]
        },
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
        }
    ]
)
print("Added ingress rules")

# LIST current rules
response = ec2.describe_security_groups(GroupIds=[sg_id])
sg = response['SecurityGroups'][0]
print("\nIngress Rules:")
for rule in sg['IpPermissions']:
    protocol = rule['IpProtocol']
    from_port = rule.get('FromPort', 'N/A')
    to_port = rule.get('ToPort', 'N/A')
    ip_ranges = rule.get('IpRanges', [])
    for ip in ip_ranges:
        print(f"  {protocol} {from_port}-{to_port} from {ip['CidrIp']}")

# REVOKE rule (remove)
ec2.revoke_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)
print("Removed SSH rule")

# DELETE security group
ec2.delete_security_group(GroupId=sg_id)
print(f"Deleted security group {sg_id}")
```

#### Instance Tags and Filtering

Tags are key-value pairs for organizing and finding instances.

```python
ec2 = boto3.client('ec2')

# LAUNCH instance with tags
response = ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',
    MinCount=1,
    MaxCount=1,
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [
            {'Key': 'Name', 'Value': 'production-server'},
            {'Key': 'Environment', 'Value': 'production'},
            {'Key': 'Team', 'Value': 'backend'},
            {'Key': 'CostCenter', 'Value': 'engineering'}
        ]
    }]
)

instance_id = response['Instances'][0]['InstanceId']

# CREATE tags on existing instance
ec2.create_tags(
    Resources=[instance_id],
    Tags=[
        {'Key': 'Backup', 'Value': 'daily'},
        {'Key': 'Owner', 'Value': 'alice@company.com'}
    ]
)

# FIND instances by tag
response = ec2.describe_instances(
    Filters=[
        {'Name': 'tag:Environment', 'Values': ['production']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
)

print("Production servers that are running:")
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
        print(f"  {instance['InstanceId']}: {tags.get('Name', 'No Name')}")

# DELETE a tag
ec2.delete_tags(
    Resources=[instance_id],
    Tags=[{'Key': 'Backup'}]  # Value not needed for deletion
)
```

---

### Chapter 4: RDS with Boto3

#### Creating and Managing DB Instances

```python
import boto3
from botocore.exceptions import ClientError

rds = boto3.client('rds')

# CREATE database instance
try:
    response = rds.create_db_instance(
        DBInstanceIdentifier='my-postgres-db',
        DBInstanceClass='db.t2.micro',
        Engine='postgres',
        MasterUsername='admin',
        MasterUserPassword='MySecurePassword123',
        AllocatedStorage=20,
        StorageType='gp2',
        VpcSecurityGroupIds=['sg-12345'],
        AvailabilityZone='us-east-1a',
        BackupRetentionPeriod=7,
        Tags=[
            {'Key': 'Name', 'Value': 'my-postgres-db'},
            {'Key': 'Environment', 'Value': 'development'}
        ]
    )
    print("Creating database instance...")
except ClientError as e:
    print(f"Error creating instance: {e}")

# WAIT for instance to be available
waiter = rds.get_waiter('db_instance_available')
print("Waiting for DB instance to be available...")
waiter.wait(DBInstanceIdentifier='my-postgres-db')
print("DB instance is available!")

# DESCRIBE instance details
response = rds.describe_db_instances(DBInstanceIdentifier='my-postgres-db')
db = response['DBInstances'][0]
print(f"Endpoint: {db['Endpoint']['Address']}")
print(f"Port: {db['Endpoint']['Port']}")
print(f"Status: {db['DBInstanceStatus']}")
print(f"Storage: {db['AllocatedStorage']} GB")

# MODIFY instance (e.g., increase storage)
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    AllocatedStorage=50,
    ApplyImmediately=False  # Apply during maintenance window
)
print("Modification scheduled")

# CREATE snapshot (backup)
response = rds.create_db_snapshot(
    DBSnapshotIdentifier='my-postgres-db-backup-2024-01-15',
    DBInstanceIdentifier='my-postgres-db'
)
print("Snapshot creation started...")

# WAIT for snapshot
snapshot_waiter = rds.get_waiter('db_snapshot_available')
snapshot_waiter.wait(DBSnapshotIdentifier='my-postgres-db-backup-2024-01-15')
print("Snapshot available!")

# RESTORE from snapshot
try:
    rds.restore_db_instance_from_db_snapshot(
        DBInstanceIdentifier='my-postgres-db-restored',
        DBSnapshotIdentifier='my-postgres-db-backup-2024-01-15'
    )
    print("Restoration started...")
except ClientError as e:
    print(f"Restore error: {e}")

# DELETE instance
rds.delete_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    SkipFinalSnapshot=False,
    FinalDBSnapshotIdentifier='final-snapshot'
)
print("Deletion started...")
```

#### Parameter Groups

Parameter groups control database configuration.

```python
rds = boto3.client('rds')

# CREATE parameter group
response = rds.create_db_parameter_group(
    DBParameterGroupName='custom-postgres-params',
    DBParameterGroupFamily='postgres14',
    Description='Custom parameters for production'
)
print(f"Created parameter group: {response['DBParameterGroup']['DBParameterGroupName']}")

# MODIFY parameters
rds.modify_db_parameter_group(
    DBParameterGroupName='custom-postgres-params',
    Parameters=[
        {
            'ParameterName': 'max_connections',
            'ParameterValue': '500',
            'ApplyMethod': 'pending-reboot'
        },
        {
            'ParameterName': 'shared_buffers',
            'ParameterValue': '16384',
            'ApplyMethod': 'pending-reboot'
        }
    ]
)
print("Parameters modified")

# DESCRIBE current parameters
response = rds.describe_db_parameters(
    DBParameterGroupName='custom-postgres-params'
)
print("\nCustom Parameters:")
for param in response['Parameters']:
    if param.get('ParameterValue'):
        print(f"  {param['ParameterName']} = {param['ParameterValue']}")

# ASSOCIATE parameter group with instance
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    DBParameterGroupName='custom-postgres-params',
    ApplyImmediately=False
)
print("Parameter group associated (pending reboot)")
```

---

### Chapter 5: CloudWatch with Boto3

#### Metrics and Alarms

```python
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch')

# PUT custom metric (application sends data)
cloudwatch.put_metric_data(
    Namespace='MyApplication',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': 45.5,
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'production'},
                {'Name': 'Service', 'Value': 'api-server'}
            ]
        },
        {
            'MetricName': 'ErrorCount',
            'Value': 3,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        }
    ]
)
print("Metrics published")

# GET metric statistics
response = cloudwatch.get_metric_statistics(
    Namespace='MyApplication',
    MetricName='ProcessingTime',
    Dimensions=[
        {'Name': 'Environment', 'Value': 'production'}
    ],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300,  # 5-minute buckets
    Statistics=['Average', 'Maximum', 'Minimum', 'Sum', 'SampleCount']
)

print("\nProcessing Time Statistics (last hour):")
for point in sorted(response['Datapoints'], key=lambda x: x['Timestamp']):
    print(f"  {point['Timestamp']}: Avg={point['Average']:.1f}ms, Max={point['Maximum']:.1f}ms")

# CREATE alarm (notify when threshold exceeded)
cloudwatch.put_metric_alarm(
    AlarmName='HighProcessingTime',
    MetricName='ProcessingTime',
    Namespace='MyApplication',
    Statistic='Average',
    Period=300,
    EvaluationPeriods=2,
    Threshold=100.0,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789:alerts']
)
print("Alarm created")

# DESCRIBE alarms
response = cloudwatch.describe_alarms(AlarmNames=['HighProcessingTime'])
for alarm in response['MetricAlarms']:
    print(f"\nAlarm: {alarm['AlarmName']}")
    print(f"  State: {alarm['StateValue']}")
    print(f"  Metric: {alarm['MetricName']}")
    print(f"  Threshold: {alarm['Threshold']}")
    print(f"  Last updated: {alarm['StateUpdatedTimestamp']}")

# DELETE alarm
cloudwatch.delete_alarms(AlarmNames=['HighProcessingTime'])
print("Alarm deleted")
```

#### Logs and Log Insights

```python
logs = boto3.client('logs')

# CREATE log group
logs.create_log_group(logGroupName='/aws/my-application')
print("Log group created")

# PUT log events
logs.put_log_events(
    logGroupName='/aws/my-application',
    logStreamName='server-1',
    logEvents=[
        {
            'timestamp': int(datetime.utcnow().timestamp() * 1000),
            'message': '2024-01-15 10:15:32 INFO Application started'
        },
        {
            'timestamp': int((datetime.utcnow() + timedelta(seconds=1)).timestamp() * 1000),
            'message': '2024-01-15 10:15:33 INFO Connected to database'
        }
    ]
)
print("Log events written")

# QUERY logs (CloudWatch Insights)
response = logs.start_query(
    logGroupName='/aws/my-application',
    startTime=int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
    endTime=int(datetime.utcnow().timestamp()),
    queryString='fields @timestamp, @message | filter @message like /ERROR/'
)

query_id = response['queryId']
print(f"Query started: {query_id}")

# WAIT for query to complete
import time
while True:
    response = logs.get_query_results(queryId=query_id)
    if response['status'] == 'Complete':
        print(f"\nFound {len(response['results'])} errors:")
        for result in response['results']:
            print(f"  {result}")
        break
    elif response['status'] == 'Failed':
        print(f"Query failed: {response.get('statistics')}")
        break
    time.sleep(0.5)

# DESCRIBE log groups
response = logs.describe_log_groups()
print("\nLog groups:")
for group in response['logGroups']:
    print(f"  {group['logGroupName']} ({group['storedBytes']} bytes)")
```

---

### Chapter 6: ECS/Fargate with Boto3

#### Task Definitions and Services

```python
import boto3
import json

ecs = boto3.client('ecs')

# REGISTER task definition
task_def = {
    'family': 'my-app',
    'networkMode': 'awsvpc',
    'requiresCompatibilities': ['FARGATE'],
    'cpu': '256',
    'memory': '512',
    'containerDefinitions': [
        {
            'name': 'my-app-container',
            'image': '123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:latest',
            'essential': True,
            'portMappings': [
                {
                    'containerPort': 8080,
                    'hostPort': 8080,
                    'protocol': 'tcp'
                }
            ],
            'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                    'awslogs-group': '/ecs/my-app',
                    'awslogs-region': 'us-east-1',
                    'awslogs-stream-prefix': 'ecs'
                }
            },
            'environment': [
                {'name': 'ENV', 'value': 'production'},
                {'name': 'LOG_LEVEL', 'value': 'info'}
            ]
        }
    ]
}

response = ecs.register_task_definition(**task_def)
print(f"Registered task definition: {response['taskDefinition']['taskDefinitionArn']}")

# CREATE service
response = ecs.create_service(
    cluster='my-cluster',
    serviceName='my-app-service',
    taskDefinition='my-app:1',
    desiredCount=2,
    launchType='FARGATE',
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': ['subnet-12345', 'subnet-67890'],
            'securityGroups': ['sg-12345'],
            'assignPublicIp': 'ENABLED'
        }
    },
    loadBalancers=[
        {
            'targetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/my-app/abc123',
            'containerName': 'my-app-container',
            'containerPort': 8080
        }
    ]
)
print(f"Service created: {response['service']['serviceArn']}")

# LIST services
response = ecs.list_services(cluster='my-cluster')
print(f"\nServices: {response['serviceArns']}")

# DESCRIBE service
response = ecs.describe_services(
    cluster='my-cluster',
    services=['my-app-service']
)
service = response['services'][0]
print(f"\nService: {service['serviceName']}")
print(f"  Status: {service['status']}")
print(f"  Running: {service['runningCount']}/{service['desiredCount']}")
print(f"  Pending: {len(service['deployments'])} deployments")

# RUN task (one-time execution)
response = ecs.run_task(
    cluster='my-cluster',
    taskDefinition='my-app:1',
    launchType='FARGATE',
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': ['subnet-12345'],
            'securityGroups': ['sg-12345']
        }
    }
)
task_arn = response['tasks'][0]['taskArn']
print(f"\nTask started: {task_arn}")

# WAIT for task completion
waiter = ecs.get_waiter('tasks_stopped')
waiter.wait(cluster='my-cluster', tasks=[task_arn])
print("Task completed")

# STOP service (gracefully)
ecs.update_service(
    cluster='my-cluster',
    service='my-app-service',
    desiredCount=0
)
print("Service scaling down")
```

---

### Chapter 7: Advanced S3 Patterns

#### Multipart Uploads

```python
import boto3
import os

s3 = boto3.client('s3')

# INITIATE multipart upload
response = s3.create_multipart_upload(
    Bucket='my-bucket',
    Key='large-file.zip'
)
upload_id = response['UploadId']
print(f"Started multipart upload: {upload_id}")

# UPLOAD parts
parts = []
chunk_size = 10 * 1024 * 1024  # 10MB chunks

with open('/path/to/large-file.zip', 'rb') as f:
    part_number = 1
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break

        response = s3.upload_part(
            Bucket='my-bucket',
            Key='large-file.zip',
            PartNumber=part_number,
            UploadId=upload_id,
            Body=chunk
        )

        parts.append({
            'ETag': response['ETag'],
            'PartNumber': part_number
        })

        print(f"  Uploaded part {part_number}/{parts}")
        part_number += 1

# COMPLETE upload
response = s3.complete_multipart_upload(
    Bucket='my-bucket',
    Key='large-file.zip',
    UploadId=upload_id,
    MultipartUpload={'Parts': parts}
)

print(f"\nUpload complete!")
print(f"  Location: {response['Location']}")
print(f"  ETag: {response['ETag']}")
```

#### Presigned URLs

```python
import boto3
from datetime import timedelta

s3 = boto3.client('s3')

# GENERATE presigned URL for download (expires in 1 hour)
url = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'report.pdf'},
    ExpiresIn=3600
)
print(f"Download link (1 hour): {url}")

# GENERATE presigned URL for upload
url = s3.generate_presigned_url(
    ClientMethod='put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'user-upload.jpg'},
    ExpiresIn=3600
)
print(f"Upload link (1 hour): {url}")

# CUSTOM response headers
url = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': 'my-bucket',
        'Key': 'document.pdf',
        'ResponseContentDisposition': 'attachment; filename="report.pdf"',
        'ResponseContentType': 'application/pdf'
    },
    ExpiresIn=3600
)
print(f"Download with filename: {url}")
```

---

# PART 3: ADVANCED PATTERNS

### Chapter 8: Multi-Account & Cross-Region Access

#### STS AssumeRole

```python
import boto3
from botocore.exceptions import ClientError

# ASSUME role in different AWS account
sts = boto3.client('sts')

try:
    response = sts.assume_role(
        RoleArn='arn:aws:iam::987654321:role/CrossAccountRole',
        RoleSessionName='data-analysis-session',
        DurationSeconds=3600
    )

    # Extract temporary credentials
    credentials = response['Credentials']
    access_key = credentials['AccessKeyId']
    secret_key = credentials['SecretAccessKey']
    session_token = credentials['SessionToken']

    # CREATE new session with temporary credentials
    cross_account_session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token
    )

    # USE cross-account session
    s3 = cross_account_session.client('s3')
    response = s3.list_buckets()

    print("Buckets in cross-account:")
    for bucket in response['Buckets']:
        print(f"  {bucket['Name']}")

except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDenied':
        print("Access denied - verify trust relationship")
    else:
        print(f"Error: {error_code}")
```

#### Multi-Region Operations

```python
import boto3
from concurrent.futures import ThreadPoolExecutor

regions = ['us-east-1', 'eu-west-1', 'ap-southeast-1']

def check_instances_in_region(region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances()

    total = 0
    for reservation in response['Reservations']:
        total += len(reservation['Instances'])

    return region, total

# CHECK instances across regions in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(check_instances_in_region, regions)

    print("Instances by region:")
    for region, count in results:
        print(f"  {region}: {count} instances")
```

---

### Chapter 9: Performance Optimization

#### Connection Pooling

```python
import boto3
from botocore.config import Config

# CONFIGURE connection pooling
config = Config(
    max_pool_connections=20,  # Default is 10
    retries={'max_attempts': 3, 'mode': 'adaptive'},
    connect_timeout=5,
    read_timeout=60
)

s3 = boto3.client('s3', config=config)

# Now handles up to 20 concurrent connections
# Better for batch operations
```

#### Parallel Operations

```python
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed

s3 = boto3.client('s3')

def download_file(bucket, key, local_path):
    try:
        s3.download_file(bucket, key, local_path)
        return key, 'success'
    except Exception as e:
        return key, f'error: {e}'

# DOWNLOAD 50 files in parallel (10 workers)
files_to_download = [
    ('my-bucket', f'file-{i}.txt', f'/local/file-{i}.txt')
    for i in range(50)
]

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {
        executor.submit(download_file, bucket, key, path): (bucket, key)
        for bucket, key, path in files_to_download
    }

    for future in as_completed(futures):
        key, result = future.result()
        print(f"{key}: {result}")
```

---

### Chapter 10: Production Best Practices

#### Logging and Monitoring

```python
import boto3
import logging
from botocore.exceptions import ClientError

# CONFIGURE logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable Boto3 debug logging (verbose)
# boto3.set_stream_logger('', logging.DEBUG)

logger = logging.getLogger(__name__)

class S3Manager:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.logger = logger

    def upload_with_logging(self, bucket, key, filepath):
        try:
            self.logger.info(f"Uploading {filepath} to s3://{bucket}/{key}")

            file_size = os.path.getsize(filepath)
            with open(filepath, 'rb') as f:
                self.s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=f
                )

            self.logger.info(f"Upload successful: {bucket}/{key} ({file_size} bytes)")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"Upload failed: {error_code} - {bucket}/{key}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error uploading {filepath}")
            return False

# USAGE
s3_mgr = S3Manager()
s3_mgr.upload_with_logging('my-bucket', 'data.txt', '/path/data.txt')
```

#### Error Handling Strategies

```python
import boto3
import time
from botocore.exceptions import ClientError, ConnectionError

def robust_operation(operation, max_retries=3, backoff_factor=2):
    """
    Execute operation with retry logic and exponential backoff
    """
    for attempt in range(max_retries):
        try:
            return operation()
        except ClientError as e:
            error_code = e.response['Error']['Code']

            # Retryable errors
            if error_code in ['ThrottlingException', 'RequestLimitExceeded', 'InternalError']:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Retrying after {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

            # Non-retryable errors
            raise
        except ConnectionError as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"Connection error, retrying after {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise

# USAGE
s3 = boto3.client('s3')

def list_objects():
    return s3.list_objects_v2(Bucket='my-bucket')

try:
    response = robust_operation(list_objects)
    print(f"Found {len(response.get('Contents', []))} objects")
except ClientError as e:
    print(f"Operation failed: {e}")
```

#### Configuration Management

```python
import os
import boto3
from dataclasses import dataclass

@dataclass
class AWSConfig:
    region: str
    profile: str = None
    max_retries: int = 3

    @classmethod
    def from_env(cls):
        return cls(
            region=os.getenv('AWS_REGION', 'us-east-1'),
            profile=os.getenv('AWS_PROFILE'),
            max_retries=int(os.getenv('AWS_MAX_RETRIES', '3'))
        )

class AWSClientFactory:
    def __init__(self, config: AWSConfig):
        self.config = config
        self.session = boto3.Session(
            profile_name=config.profile,
            region_name=config.region
        )

    def get_s3_client(self):
        from botocore.config import Config
        config = Config(retries={'max_attempts': self.config.max_retries})
        return self.session.client('s3', config=config)

    def get_ec2_client(self):
        return self.session.client('ec2')

    def get_client(self, service_name):
        return self.session.client(service_name)

# USAGE
config = AWSConfig.from_env()
factory = AWSClientFactory(config)

s3 = factory.get_s3_client()
ec2 = factory.get_ec2_client()
```

---

## Summary

This guide covers Boto3 from fundamentals to production patterns:

**Key Takeaways**:
1. **Client vs Resource** - Choose based on your needs (control vs simplicity)
2. **Sessions** - They hold your credentials and region configuration
3. **Error Handling** - Always use try/except with ClientError
4. **Pagination** - Use paginators for large result sets
5. **Waiters** - Poll for async operations instead of sleep
6. **Services** - Master 2-3 services deeply (S3, EC2, Lambda) before breadth
7. **Production** - Logging, retries, configuration management are non-negotiable
8. **Testing** - Use LocalStack or moto for local development

**Next Steps**:
- Pick one service and build something with it
- Review [AWS Documentation](https://docs.aws.amazon.com/pythonsdk/)
- Check out [Boto3 Examples](https://github.com/aws/aws-sdk-examples) repo
- Learn [CloudFormation](https://aws.amazon.com/cloudformation/) for infrastructure-as-code

---

## Appendix: Common Services Reference

### Available Paginators by Service

```python
# Check if a service supports pagination
client = boto3.client('s3')
paginator_names = client.waiter_names  # Also list waiter names

# Common paginatable operations:
# S3: list_objects_v2, list_multipart_uploads
# EC2: describe_instances, describe_images, describe_volumes
# DynamoDB: scan, query
# Lambda: list_functions, list_layers
```

### Common Error Codes

| Service | Code | Meaning |
|---------|------|---------|
| **General** | NoCredentialsError | AWS credentials not configured |
| **General** | ClientError | Service returned error (check Code in response) |
| **S3** | NoSuchBucket | Bucket doesn't exist |
| **S3** | NoSuchKey | Object doesn't exist |
| **EC2** | InvalidInstanceID.NotFound | Instance doesn't exist |
| **Lambda** | ResourceNotFoundException | Function doesn't exist |
| **RDS** | DBInstanceNotFound | Database doesn't exist |
| **IAM** | NoSuchEntity | Role/user/policy doesn't exist |

### Resources for Learning

- **Official**: [AWS Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- **Interactive**: [AWS SDK Examples](https://github.com/aws/aws-sdk-examples)
- **Testing**: [LocalStack](https://localstack.cloud/) - Local AWS emulation
- **Practice**: [AWS Hands-On Labs](https://aws.amazon.com/training/hands-on-labs/)

---

**Last Updated**: 2024
**Target Audience**: Beginners to Intermediate Python developers
**Estimated Reading Time**: Quick Reference 15-30 min, Complete Guide 3-4 hours
