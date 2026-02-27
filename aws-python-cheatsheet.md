# AWS Cheat Sheet for Python Developers, Data Engineers & Data Scientists

> **Run AWS services locally on your laptop using LocalStack!**

---

## 🚀 Quick Setup: LocalStack (Run AWS Locally)

### What is LocalStack?

LocalStack is a fully functional local AWS cloud stack that emulates AWS services on your laptop. Perfect for
development, testing, and learning without AWS costs.

### Installation Options

#### Option 1: Docker (Recommended)

```bash
# Install Docker first, then:
docker pull localstack/localstack

# Run LocalStack
docker run -d \
  --name localstack \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -e SERVICES=s3,lambda,sqs,sns,kinesis,dynamodb,iam,stepfunctions,secretsmanager \
  -e DEBUG=1 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  localstack/localstack
```

##### What's the above script doing

This script is the "starter pack" for running **LocalStack**, a tool that lets you run a mock AWS environment directly
on your laptop. Instead of paying for actual AWS resources while you develop and test, you run them locally.

Here is a breakdown of what each part of that command is doing:

---

### 1. Pulling the Image

`docker pull localstack/localstack`
This downloads the official LocalStack "container image" from Docker Hub. Think of this as downloading the software
installer before you actually run it.

### 2. Running the Container

`docker run -d`

* **`-d` (Detached):** This runs the container in the background. If you don't use this, the logs will take over your
  terminal window, and closing the window will stop the service.

### 3. Naming and Ports

* **`--name localstack`:** Gives the container a friendly name so you can stop it later using `docker stop localstack`
  instead of a random ID number.
* **`-p 4566:4566`:** This is the most important part. Port **4566** is the "Edge Port." Every AWS service you use (S3,
  DynamoDB, etc.) will be accessible through this single entry point.
* **`-p 4510-4559:4510-4559`:** These ports are reserved for external services like **AWS Lambda** functions to
  communicate back to LocalStack.

### 4. Environment Variables (`-e`)

These configure how the software behaves inside the container:

* **`SERVICES=s3,lambda...`:** Tells LocalStack exactly which AWS features to turn on. This saves memory by not loading
  services you don't need.
* **`DEBUG=1`:** Turns on "verbose" logging. If something goes wrong with your local S3 bucket, the terminal logs will
  show you exactly why.

### 5. The Docker Socket (`-v`)

* **`-v /var/run/docker.sock:/var/run/docker.sock`:** This allows LocalStack (which is inside a container) to talk to
  Docker (which is on your host machine).
* **Why?** This is specifically required for **AWS Lambda**. When you trigger a Lambda function, LocalStack needs to
  spin up *another* separate container to run your code. It can't do that without access to the Docker socket.

---

### How to use it once it's running

Once this is live, you can point your AWS CLI or your application code to your laptop instead of the real cloud. For
example:

```bash
# Create an S3 bucket on your own machine
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-test-bucket

```

#### Option 2: pip Install

```bash
pip install localstack
pip install awscli-local  # Wrapper for AWS CLI

# Start LocalStack
localstack start -d
```

#### Option 3: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,lambda,sqs,sns,kinesis,dynamodb,iam
      - DEBUG=1
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "./localstack-data:/var/lib/localstack"
```

```bash
docker-compose up -d
```

### Python Dependencies

```bash
pip install boto3 awscli-local localstack-client
```

### Configuration

```python
import boto3
from botocore.config import Config

# LocalStack endpoint (local development)
LOCALSTACK_ENDPOINT = "http://localhost:4566"


# Create client for LocalStack
def get_local_client(service_name):
    return boto3.client(
        service_name,
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )


# Create client for real AWS
def get_aws_client(service_name):
    return boto3.client(service_name, region_name="us-east-1")


# Environment-aware client factory
import os


def get_client(service_name):
    """Returns LocalStack client if LOCAL_DEV=true, else AWS client"""
    if os.environ.get("LOCAL_DEV", "false").lower() == "true":
        return get_local_client(service_name)
    return get_aws_client(service_name)
```

---

## 📦 S3 (Simple Storage Service)

### Basic Operations

```python
s3 = get_client('s3')

# Create bucket
s3.create_bucket(Bucket='my-data-bucket')

# Upload file
s3.upload_file('local_file.csv', 'my-data-bucket', 'data/file.csv')

# Upload with metadata
s3.upload_file(
    'local_file.csv',
    'my-data-bucket',
    'data/file.csv',
    ExtraArgs={'Metadata': {'processed': 'true', 'source': 'etl-job'}}
)

# Download file
s3.download_file('my-data-bucket', 'data/file.csv', 'downloaded.csv')

# List objects
response = s3.list_objects_v2(Bucket='my-data-bucket', Prefix='data/')
for obj in response.get('Contents', []):
    print(f"{obj['Key']} - {obj['Size']} bytes")

# Delete object
s3.delete_object(Bucket='my-data-bucket', Key='data/file.csv')

# Delete bucket (must be empty)
s3.delete_bucket(Bucket='my-data-bucket')
```

### Working with Data (Pandas/Parquet)

```python
import pandas as pd
import io

s3 = get_client('s3')

# Upload DataFrame as CSV
df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)
s3.put_object(Bucket='my-bucket', Key='data.csv', Body=csv_buffer.getvalue())

# Upload DataFrame as Parquet
parquet_buffer = io.BytesIO()
df.to_parquet(parquet_buffer, index=False)
s3.put_object(Bucket='my-bucket', Key='data.parquet', Body=parquet_buffer.getvalue())

# Read CSV from S3
response = s3.get_object(Bucket='my-bucket', Key='data.csv')
df = pd.read_csv(io.BytesIO(response['Body'].read()))

# Read Parquet from S3
response = s3.get_object(Bucket='my-bucket', Key='data.parquet')
df = pd.read_parquet(io.BytesIO(response['Body'].read()))
```

### S3 Select (Query Data in S3)

```python
# Query CSV data directly in S3 using SQL
response = s3.select_object_content(
    Bucket='my-bucket',
    Key='large_data.csv',
    ExpressionType='SQL',
    Expression="SELECT * FROM s3object s WHERE s.age > 30",
    InputSerialization={'CSV': {'FileHeaderInfo': 'Use'}},
    OutputSerialization={'CSV': {}}
)

# Process results
for event in response['Payload']:
    if 'Records' in event:
        print(event['Records']['Payload'].decode('utf-8'))
```

### Presigned URLs

```python
# Generate presigned URL for download (expires in 1 hour)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'data.csv'},
    ExpiresIn=3600
)

# Generate presigned URL for upload
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'upload.csv'},
    ExpiresIn=3600
)
```

---

## ⚡ Lambda (Serverless Functions)

### Create Lambda Function

```python
import zipfile
import json

lambda_client = get_client('lambda')

# Lambda function code
lambda_code = '''
import json

def handler(event, context):
    name = event.get('name', 'World')
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Hello, {name}!'})
    }
'''

# Create deployment package
with zipfile.ZipFile('lambda.zip', 'w') as z:
    z.writestr('lambda_function.py', lambda_code)

# Create Lambda function
with open('lambda.zip', 'rb') as f:
    lambda_client.create_function(
        FunctionName='my-function',
        Runtime='python3.11',
        Role='arn:aws:iam::000000000000:role/lambda-role',  # LocalStack dummy
        Handler='lambda_function.handler',
        Code={'ZipFile': f.read()},
        Timeout=30,
        MemorySize=256
    )
```

### Invoke Lambda

```python
# Synchronous invocation
response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='RequestResponse',
    Payload=json.dumps({'name': 'Alice'})
)
result = json.loads(response['Payload'].read())
print(result)  # {'statusCode': 200, 'body': '{"message": "Hello, Alice!"}'}

# Asynchronous invocation (fire and forget)
response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='Event',
    Payload=json.dumps({'name': 'Bob'})
)
```

### Lambda with S3 Trigger (Data Pipeline Example)

```python
# Lambda that processes files uploaded to S3
lambda_code = '''
import json
import boto3
import pandas as pd
import io

def handler(event, context):
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Read CSV
        response = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        
        # Transform
        df['processed'] = True
        df['timestamp'] = pd.Timestamp.now().isoformat()
        
        # Write to processed folder
        output_key = key.replace('raw/', 'processed/')
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        s3.put_object(Bucket=bucket, Key=output_key, Body=buffer.getvalue())
    
    return {'statusCode': 200, 'processed_files': len(event['Records'])}
'''
```

### Lambda Layers (Dependencies)

```python
# Create layer with dependencies
import subprocess
import shutil

# Create layer structure
subprocess.run(['pip', 'install', 'pandas', 'numpy', '-t', 'python/'])
shutil.make_archive('layer', 'zip', '.', 'python')

# Upload layer
with open('layer.zip', 'rb') as f:
    response = lambda_client.publish_layer_version(
        LayerName='data-processing-layer',
        Content={'ZipFile': f.read()},
        CompatibleRuntimes=['python3.11']
    )

layer_arn = response['LayerVersionArn']

# Update function to use layer
lambda_client.update_function_configuration(
    FunctionName='my-function',
    Layers=[layer_arn]
)
```

---

## 📬 SQS (Simple Queue Service)

### Queue Operations

```python
sqs = get_client('sqs')

# Create queue
response = sqs.create_queue(
    QueueName='data-processing-queue',
    Attributes={
        'DelaySeconds': '0',
        'MessageRetentionPeriod': '86400',  # 1 day
        'VisibilityTimeout': '300'  # 5 minutes
    }
)
queue_url = response['QueueUrl']

# Create FIFO queue (exactly-once processing)
response = sqs.create_queue(
    QueueName='ordered-queue.fifo',
    Attributes={
        'FifoQueue': 'true',
        'ContentBasedDeduplication': 'true'
    }
)
```

### Send Messages

```python
import json

# Send single message
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({'task': 'process_data', 'file_id': '12345'}),
    MessageAttributes={
        'Priority': {'StringValue': 'high', 'DataType': 'String'}
    }
)

# Send batch messages (up to 10)
entries = [
    {'Id': str(i), 'MessageBody': json.dumps({'file_id': f'file_{i}'})}
    for i in range(10)
]
sqs.send_message_batch(QueueUrl=queue_url, Entries=entries)

# Send to FIFO queue
sqs.send_message(
    QueueUrl=fifo_queue_url,
    MessageBody=json.dumps({'order_id': '123'}),
    MessageGroupId='orders',
    MessageDeduplicationId='unique-id-123'
)
```

### Receive and Process Messages

```python
# Receive messages (long polling)
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20,  # Long polling
    MessageAttributeNames=['All']
)

for message in response.get('Messages', []):
    body = json.loads(message['Body'])
    receipt_handle = message['ReceiptHandle']

    try:
        # Process message
        print(f"Processing: {body}")

        # Delete after successful processing
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    except Exception as e:
        print(f"Error: {e}")
        # Message will return to queue after visibility timeout
```

### Dead Letter Queue Pattern

```python
# Create DLQ
dlq_response = sqs.create_queue(QueueName='processing-dlq')
dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_response['QueueUrl'],
    AttributeNames=['QueueArn']
)['Attributes']['QueueArn']

# Create main queue with DLQ
sqs.create_queue(
    QueueName='processing-queue',
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'  # Move to DLQ after 3 failed attempts
        })
    }
)
```

---

## 📢 SNS (Simple Notification Service)

### Topic Operations

```python
sns = get_client('sns')

# Create topic
response = sns.create_topic(Name='data-events')
topic_arn = response['TopicArn']

# Subscribe email (requires confirmation in real AWS)
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='user@example.com'
)

# Subscribe SQS queue
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint=sqs_queue_arn
)

# Subscribe Lambda
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='lambda',
    Endpoint=lambda_function_arn
)

# Subscribe HTTP endpoint
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='https',
    Endpoint='https://myapi.example.com/webhook'
)
```

### Publish Messages

```python
import json

# Publish simple message
sns.publish(
    TopicArn=topic_arn,
    Message='Data processing completed!',
    Subject='ETL Job Status'
)

# Publish with message attributes
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'status': 'success', 'records_processed': 1000}),
    MessageAttributes={
        'event_type': {'DataType': 'String', 'StringValue': 'etl_complete'},
        'priority': {'DataType': 'Number', 'StringValue': '1'}
    }
)

# Publish with filter (subscribers can filter messages)
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'order_id': '123', 'status': 'shipped'}),
    MessageAttributes={
        'order_status': {'DataType': 'String', 'StringValue': 'shipped'}
    }
)
```

### SNS + SQS Fan-Out Pattern

```python
# Create SNS topic
topic = sns.create_topic(Name='order-events')
topic_arn = topic['TopicArn']

# Create multiple SQS queues for different services
queues = {
    'inventory': sqs.create_queue(QueueName='inventory-queue'),
    'shipping': sqs.create_queue(QueueName='shipping-queue'),
    'analytics': sqs.create_queue(QueueName='analytics-queue')
}

# Subscribe all queues to the topic
for name, queue in queues.items():
    queue_arn = sqs.get_queue_attributes(
        QueueUrl=queue['QueueUrl'],
        AttributeNames=['QueueArn']
    )['Attributes']['QueueArn']
    
    sns.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn)

# Now one publish goes to all queues
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'order_id': '123', 'items': ['A', 'B']})
)
```

---

## 🌊 Kinesis (Real-time Streaming)

### Create and Manage Streams

```python
kinesis = get_client('kinesis')

# Create stream
kinesis.create_stream(
    StreamName='clickstream-data',
    ShardCount=2  # Number of shards for parallelism
)

# Wait for stream to become active
waiter = kinesis.get_waiter('stream_exists')
waiter.wait(StreamName='clickstream-data')

# Describe stream
response = kinesis.describe_stream(StreamName='clickstream-data')
print(f"Status: {response['StreamDescription']['StreamStatus']}")
```

### Produce Data

```python
import json
import time
import random

# Put single record
kinesis.put_record(
    StreamName='clickstream-data',
    Data=json.dumps({
        'user_id': 'user_123',
        'event': 'page_view',
        'timestamp': time.time(),
        'page': '/products/item-1'
    }),
    PartitionKey='user_123'  # Records with same key go to same shard
)

# Put multiple records (batch)
records = [
    {
        'Data': json.dumps({
            'user_id': f'user_{i}',
            'event': random.choice(['click', 'view', 'purchase']),
            'timestamp': time.time()
        }),
        'PartitionKey': f'user_{i}'
    }
    for i in range(100)
]

response = kinesis.put_records(StreamName='clickstream-data', Records=records)
print(f"Failed records: {response['FailedRecordCount']}")
```

### Consume Data

```python
# Get shard iterator
response = kinesis.describe_stream(StreamName='clickstream-data')
shard_id = response['StreamDescription']['Shards'][0]['ShardId']

shard_iterator = kinesis.get_shard_iterator(
    StreamName='clickstream-data',
    ShardId=shard_id,
    ShardIteratorType='LATEST'  # or 'TRIM_HORIZON' for all records
)['ShardIterator']

# Read records
while True:
    response = kinesis.get_records(ShardIterator=shard_iterator, Limit=100)
    
    for record in response['Records']:
        data = json.loads(record['Data'])
        print(f"Sequence: {record['SequenceNumber']}, Data: {data}")
    
    shard_iterator = response['NextShardIterator']
    
    if not response['Records']:
        time.sleep(1)  # No records, wait before polling
```

### Kinesis Data Analytics Pattern

```python
# Process streaming data with windowing
from collections import defaultdict
from datetime import datetime, timedelta

class StreamProcessor:
    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.windows = defaultdict(lambda: defaultdict(int))
    
    def process_record(self, record):
        data = json.loads(record['Data'])
        window_key = self._get_window_key(data['timestamp'])
        event_type = data['event']
        
        self.windows[window_key][event_type] += 1
        
        # Emit completed windows
        self._emit_completed_windows()
    
    def _get_window_key(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        return dt.replace(second=0, microsecond=0)
    
    def _emit_completed_windows(self):
        current_window = self._get_window_key(time.time())
        
        for window_key in list(self.windows.keys()):
            if window_key < current_window - timedelta(seconds=self.window_seconds):
                stats = dict(self.windows[window_key])
                print(f"Window {window_key}: {stats}")
                del self.windows[window_key]
```

---

## 🔐 IAM (Identity and Access Management)

### Create Roles and Policies

```python
iam = get_client('iam')

# Create policy document
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-data-bucket",
                "arn:aws:s3:::my-data-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}

# Create policy
response = iam.create_policy(
    PolicyName='DataProcessingPolicy',
    PolicyDocument=json.dumps(policy_document),
    Description='Policy for data processing Lambda'
)
policy_arn = response['Policy']['Arn']

# Create role trust policy
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

# Create role
iam.create_role(
    RoleName='DataProcessingRole',
    AssumeRolePolicyDocument=json.dumps(trust_policy),
    Description='Role for data processing Lambda functions'
)

# Attach policy to role
iam.attach_role_policy(
    RoleName='DataProcessingRole',
    PolicyArn=policy_arn
)
```

### Common IAM Policies

```python
# S3 Read-Only Policy
s3_read_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": ["arn:aws:s3:::*"]
    }]
}

# SQS Full Access
sqs_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["sqs:*"],
        "Resource": ["arn:aws:sqs:*:*:my-queue-*"]
    }]
}

# Kinesis Producer Policy
kinesis_producer_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["kinesis:PutRecord", "kinesis:PutRecords"],
        "Resource": ["arn:aws:kinesis:*:*:stream/my-stream"]
    }]
}

# Glue Job Policy
glue_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["glue:*"],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": ["s3:*"],
            "Resource": [
                "arn:aws:s3:::my-data-lake",
                "arn:aws:s3:::my-data-lake/*"
            ]
        }
    ]
}
```

---

## 🗄️ DynamoDB (NoSQL Database)

### Table Operations

```python
dynamodb = get_client('dynamodb')

# Create table
dynamodb.create_table(
    TableName='user-events',
    KeySchema=[
        {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
    ],
    AttributeDefinitions=[
        {'AttributeName': 'user_id', 'AttributeType': 'S'},
        {'AttributeName': 'timestamp', 'AttributeType': 'N'}
    ],
    BillingMode='PAY_PER_REQUEST'  # Or 'PROVISIONED' with capacity
)

# Wait for table
waiter = dynamodb.get_waiter('table_exists')
waiter.wait(TableName='user-events')
```

### CRUD Operations

```python
from decimal import Decimal
import time

# Put item
dynamodb.put_item(
    TableName='user-events',
    Item={
        'user_id': {'S': 'user_123'},
        'timestamp': {'N': str(int(time.time()))},
        'event_type': {'S': 'purchase'},
        'amount': {'N': '99.99'},
        'items': {'L': [{'S': 'item_1'}, {'S': 'item_2'}]}
    }
)

# Get item
response = dynamodb.get_item(
    TableName='user-events',
    Key={
        'user_id': {'S': 'user_123'},
        'timestamp': {'N': '1699999999'}
    }
)
item = response.get('Item')

# Query (by partition key)
response = dynamodb.query(
    TableName='user-events',
    KeyConditionExpression='user_id = :uid AND #ts > :ts',
    ExpressionAttributeNames={'#ts': 'timestamp'},
    ExpressionAttributeValues={
        ':uid': {'S': 'user_123'},
        ':ts': {'N': str(int(time.time()) - 86400)}  # Last 24 hours
    }
)

# Scan (full table - use sparingly)
response = dynamodb.scan(
    TableName='user-events',
    FilterExpression='event_type = :et',
    ExpressionAttributeValues={':et': {'S': 'purchase'}}
)
```

### Using boto3.resource (Higher-level API)

```python
# Resource-based API (cleaner syntax)
dynamodb_resource = boto3.resource(
    'dynamodb',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

table = dynamodb_resource.Table('user-events')

# Put item (simpler syntax)
table.put_item(Item={
    'user_id': 'user_456',
    'timestamp': Decimal(str(time.time())),
    'event_type': 'view',
    'page': '/products'
})

# Query
response = table.query(
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': 'user_456'}
)

for item in response['Items']:
    print(item)
```

---

## 🔧 Step Functions (Workflow Orchestration)

### Define State Machine

```python
sfn = get_client('stepfunctions')

# State machine definition
state_machine_def = {
    "Comment": "Data Processing Pipeline",
    "StartAt": "ExtractData",
    "States": {
        "ExtractData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:000000000000:function:extract",
            "Next": "TransformData",
            "Catch": [{
                "ErrorEquals": ["States.ALL"],
                "Next": "HandleError"
            }]
        },
        "TransformData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:000000000000:function:transform",
            "Next": "LoadData"
        },
        "LoadData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:000000000000:function:load",
            "End": True
        },
        "HandleError": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:000000000000:function:handle-error",
            "End": True
        }
    }
}

# Create state machine
response = sfn.create_state_machine(
    name='data-pipeline',
    definition=json.dumps(state_machine_def),
    roleArn='arn:aws:iam::000000000000:role/step-functions-role'
)
state_machine_arn = response['stateMachineArn']
```

### Execute and Monitor

```python
# Start execution
response = sfn.start_execution(
    stateMachineArn=state_machine_arn,
    input=json.dumps({'source_bucket': 'raw-data', 'file_key': 'data.csv'})
)
execution_arn = response['executionArn']

# Check status
response = sfn.describe_execution(executionArn=execution_arn)
print(f"Status: {response['status']}")

# Get execution history
response = sfn.get_execution_history(executionArn=execution_arn)
for event in response['events']:
    print(f"{event['type']}: {event.get('stateEnteredEventDetails', {})}")
```

---

## 🔑 Secrets Manager

### Manage Secrets

```python
secrets = get_client('secretsmanager')

# Create secret
secrets.create_secret(
    Name='prod/database/credentials',
    SecretString=json.dumps({
        'username': 'admin',
        'password': 'super-secret-password',
        'host': 'db.example.com',
        'port': 5432
    })
)

# Get secret
response = secrets.get_secret_value(SecretId='prod/database/credentials')
credentials = json.loads(response['SecretString'])
print(f"Username: {credentials['username']}")

# Update secret
secrets.update_secret(
    SecretId='prod/database/credentials',
    SecretString=json.dumps({
        'username': 'admin',
        'password': 'new-super-secret-password',
        'host': 'db.example.com',
        'port': 5432
    })
)

# Rotate secret
secrets.rotate_secret(
    SecretId='prod/database/credentials',
    RotationLambdaARN='arn:aws:lambda:us-east-1:000000000000:function:rotate-secret'
)
```

### Secret Caching

```python
from botocore.exceptions import ClientError
import time

class SecretCache:
    def __init__(self, client, ttl_seconds=300):
        self.client = client
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get_secret(self, secret_id):
        now = time.time()
        
        if secret_id in self.cache:
            value, timestamp = self.cache[secret_id]
            if now - timestamp < self.ttl:
                return value
        
        response = self.client.get_secret_value(SecretId=secret_id)
        value = json.loads(response['SecretString'])
        self.cache[secret_id] = (value, now)
        return value

# Usage
secret_cache = SecretCache(secrets)
db_creds = secret_cache.get_secret('prod/database/credentials')
```

---

## 📊 Data Engineering Patterns

### ETL Pipeline with Lambda + SQS

```python
# Complete ETL pipeline example

# 1. S3 Event -> SQS -> Lambda pattern
def setup_etl_pipeline():
    # Create queues
    process_queue = sqs.create_queue(QueueName='file-processing')

    # Create Lambda function
    etl_lambda_code = '''
import json
import boto3
import pandas as pd
import io

def handler(event, context):
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
    
    for record in event['Records']:
        # Parse SQS message
        body = json.loads(record['body'])
        bucket = body['bucket']
        key = body['key']
        
        # Extract
        response = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))
        
        # Transform
        df = df.dropna()
        df['processed_at'] = pd.Timestamp.now().isoformat()
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        # Load
        output_key = f"processed/{key.split('/')[-1].replace('.csv', '.parquet')}"
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        s3.put_object(Bucket='data-warehouse', Key=output_key, Body=buffer.getvalue())
        
    return {'processed': len(event['Records'])}
'''

    # Create Lambda with SQS trigger
    # ... (Lambda creation code from above)
```

### Data Lake Architecture

```python
# Bronze/Silver/Gold data lake pattern

class DataLake:
    def __init__(self, s3_client, bucket):
        self.s3 = s3_client
        self.bucket = bucket

    def ingest_raw(self, data: bytes, source: str, file_name: str):
        """Bronze layer: raw data as-is"""
        key = f"bronze/{source}/{file_name}"
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
        return key

    def process_to_silver(self, bronze_key: str):
        """Silver layer: cleaned and validated"""
        response = self.s3.get_object(Bucket=self.bucket, Key=bronze_key)
        df = pd.read_csv(io.BytesIO(response['Body'].read()))

        # Clean data
        df = df.dropna()
        df = df.drop_duplicates()

        # Validate schema
        # ... validation logic ...

        silver_key = bronze_key.replace('bronze/', 'silver/').replace('.csv', '.parquet')
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        self.s3.put_object(Bucket=self.bucket, Key=silver_key, Body=buffer.getvalue())
        return silver_key

    def aggregate_to_gold(self, silver_keys: list, aggregation: str):
        """Gold layer: business-ready aggregates"""
        dfs = []
        for key in silver_keys:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            dfs.append(pd.read_parquet(io.BytesIO(response['Body'].read())))

        df = pd.concat(dfs)

        # Aggregate based on business logic
        if aggregation == 'daily_summary':
            result = df.groupby('date').agg({
                'revenue': 'sum',
                'orders': 'count',
                'customers': 'nunique'
            }).reset_index()

        gold_key = f"gold/{aggregation}.parquet"
        buffer = io.BytesIO()
        result.to_parquet(buffer, index=False)
        self.s3.put_object(Bucket=self.bucket, Key=gold_key, Body=buffer.getvalue())
        return gold_key
```

### Real-time Analytics Pipeline

```python
# Kinesis -> Lambda -> DynamoDB/S3

class RealtimeAnalytics:
    def __init__(self):
        self.kinesis = get_client('kinesis')
        self.dynamodb = get_client('dynamodb')
        self.s3 = get_client('s3')

    def process_stream(self, stream_name: str):
        """Process streaming events and compute real-time metrics"""

        # Lambda code for processing
        processor_code = '''
import json
import boto3
from decimal import Decimal
import base64

def handler(event, context):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4566')
    metrics_table = dynamodb.Table('realtime-metrics')
    
    for record in event['Records']:
        # Decode Kinesis data
        payload = json.loads(base64.b64decode(record['kinesis']['data']))
        
        # Update real-time metrics
        metrics_table.update_item(
            Key={'metric_key': payload['event_type']},
            UpdateExpression='ADD event_count :inc SET last_updated = :ts',
            ExpressionAttributeValues={
                ':inc': Decimal('1'),
                ':ts': payload['timestamp']
            }
        )
    
    return {'processed': len(event['Records'])}
'''
        return processor_code
```

---

## 🧪 Testing with LocalStack

### pytest Fixtures

```python
import pytest
import boto3


@pytest.fixture(scope='session')
def localstack_endpoint():
    return "http://localhost:4566"


@pytest.fixture(scope='session')
def s3_client(localstack_endpoint):
    return boto3.client(
        's3',
        endpoint_url=localstack_endpoint,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )


@pytest.fixture
def test_bucket(s3_client):
    bucket_name = 'test-bucket'
    s3_client.create_bucket(Bucket=bucket_name)
    yield bucket_name
    # Cleanup
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    for obj in response.get('Contents', []):
        s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
    s3_client.delete_bucket(Bucket=bucket_name)


def test_upload_and_download(s3_client, test_bucket):
    # Upload
    s3_client.put_object(
        Bucket=test_bucket,
        Key='test.txt',
        Body=b'Hello, World!'
    )

    # Download
    response = s3_client.get_object(Bucket=test_bucket, Key='test.txt')
    content = response['Body'].read()

    assert content == b'Hello, World!'
```

### Moto (Alternative to LocalStack)

```python
import boto3
from moto import mock_aws


@mock_aws
def test_s3_operations():
    # Moto mocks AWS calls in-memory
    s3 = boto3.client('s3', region_name='us-east-1')

    # Create bucket
    s3.create_bucket(Bucket='my-bucket')

    # Upload
    s3.put_object(Bucket='my-bucket', Key='test.txt', Body=b'test')

    # Verify
    response = s3.list_objects_v2(Bucket='my-bucket')
    assert len(response['Contents']) == 1


@mock_aws
def test_lambda_invocation():
    from moto import mock_lambda

    lambda_client = boto3.client('lambda', region_name='us-east-1')

    # Note: Moto has limitations for Lambda execution
    # Use LocalStack for actual Lambda execution testing
```

---

## 📝 Quick Reference Commands

### LocalStack CLI

```bash
# Start LocalStack
localstack start -d

# Check status
localstack status services

# Stop LocalStack
localstack stop

# View logs
localstack logs

# Reset (clear all data)
localstack stop && docker volume rm localstack_data
```

### AWS CLI with LocalStack

```bash
# Configure awslocal alias
alias awslocal="aws --endpoint-url=http://localhost:4566"

# S3 operations
awslocal s3 mb s3://my-bucket
awslocal s3 cp file.txt s3://my-bucket/
awslocal s3 ls s3://my-bucket/

# Lambda
awslocal lambda list-functions
awslocal lambda invoke --function-name my-func output.json

# SQS
awslocal sqs create-queue --queue-name my-queue
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/my-queue --message-body "test"

# DynamoDB
awslocal dynamodb list-tables
awslocal dynamodb scan --table-name my-table
```

---

## 🎯 Best Practices Summary

| Area                  | Best Practice                                     |
|-----------------------|---------------------------------------------------|
| **Local Development** | Use LocalStack for all AWS services locally       |
| **Configuration**     | Use environment variables for endpoint switching  |
| **S3**                | Use Parquet for analytics workloads               |
| **Lambda**            | Keep functions small, use layers for dependencies |
| **SQS**               | Use DLQ for failed message handling               |
| **Kinesis**           | Batch records for better throughput               |
| **IAM**               | Follow least privilege principle                  |
| **DynamoDB**          | Design for access patterns, not normalization     |
| **Secrets**           | Never hardcode, always use Secrets Manager        |
| **Testing**           | Use pytest fixtures with LocalStack               |

---

## 📚 Additional Resources

- **LocalStack Docs**: https://docs.localstack.cloud
- **Boto3 Docs**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **AWS CLI Reference**: https://awscli.amazonaws.com/v2/documentation/api/latest/index.html
- **Moto (Mocking)**: https://github.com/getmoto/moto

---
