# Learning AWS Data Engineering: Complete Guide

**Time**: 3-4 hours
**Hands-on**: Yes (copy-paste code examples)
**Prerequisites**: Setup complete (see setup.md)

---

## Table of Contents

1. [S3: Cloud Storage](#s3-cloud-storage)
2. [Lambda: Serverless Functions](#lambda-serverless-functions)
3. [SNS: Notifications](#sns-notifications)
4. [SQS: Message Queues](#sqs-message-queues)
5. [Step Functions: Orchestration](#step-functions-orchestration)
6. [Azure → AWS Bridge](#azure--aws-bridge)
7. [Hands-On: Build a Pipeline](#hands-on-build-a-pipeline)

---

# S3: Cloud Storage

## What is S3?

**S3 = Simple Storage Service = Cloud file storage**

```
Your Laptop (Local)          AWS (Cloud)

my-files/                    S3 Bucket
├─ data.csv          →       └─ my-bucket/
├─ image.jpg                    ├─ data.csv
└─ video.mp4                    ├─ image.jpg
                                └─ video.mp4

Cost: $0.023 per GB/month
Reliability: 99.999999999% (11 nines!)
Access: Anywhere with internet
```

## S3 Concepts

```
BUCKET (like a folder on the cloud):

s3://my-data-bucket/
├─ raw/
│  ├─ customers.csv
│  ├─ orders.csv
│  └─ products.csv
│
├─ processed/
│  ├─ customers_clean.csv
│  ├─ orders_clean.csv
│  └─ products_clean.csv
│
└─ archive/
   ├─ 2024-01-data.tar.gz
   └─ 2024-02-data.tar.gz


KEY (like a file path):

Bucket: my-data-bucket
Key: raw/customers.csv
Full path: s3://my-data-bucket/raw/customers.csv
```

## Working with S3

### Create Bucket

```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',  # LocalStack
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Create bucket
s3.create_bucket(Bucket='my-data-bucket')
print('✓ Bucket created')

# List buckets
response = s3.list_buckets()
for bucket in response['Buckets']:
    print(f"  - {bucket['Name']}")
```

### Upload File

```python
# Upload file
with open('data/customers.csv', 'rb') as f:
    s3.put_object(
        Bucket='my-data-bucket',
        Key='raw/customers.csv',
        Body=f.read()
    )
print('✓ File uploaded to S3')

# Upload text
s3.put_object(
    Bucket='my-data-bucket',
    Key='test.txt',
    Body=b'Hello from S3!'
)
```

### Download File

```python
# Download file
response = s3.get_object(
    Bucket='my-data-bucket',
    Key='raw/customers.csv'
)

# Read content
content = response['Body'].read()

# Save locally
with open('downloaded_customers.csv', 'wb') as f:
    f.write(content)
print('✓ File downloaded')
```

### List Objects

```python
# List all files in a prefix (folder)
response = s3.list_objects_v2(
    Bucket='my-data-bucket',
    Prefix='raw/'
)

for obj in response.get('Contents', []):
    print(f"  - {obj['Key']} ({obj['Size']} bytes)")

# Output:
#   - raw/customers.csv (1024 bytes)
#   - raw/orders.csv (2048 bytes)
```

### Delete Object

```python
# Delete single file
s3.delete_object(
    Bucket='my-data-bucket',
    Key='raw/temp.csv'
)
print('✓ File deleted')

# Delete multiple files
s3.delete_objects(
    Bucket='my-data-bucket',
    Delete={
        'Objects': [
            {'Key': 'raw/old1.csv'},
            {'Key': 'raw/old2.csv'}
        ]
    }
)
print('✓ Files deleted')
```

---

# Lambda: Serverless Functions

## What is Lambda?

**Lambda = Serverless code execution (no server management)**

```
Traditional Server               Lambda (Serverless)

You manage:                      AWS manages:
├─ OS updates                    ├─ OS updates
├─ Security patches              ├─ Security patches
├─ Capacity planning             ├─ Scaling
├─ Monitoring                    ├─ Monitoring
└─ Cost optimization             └─ Cost optimization

Cost: Pay per 100ms execution    Cost: Only when running
Maintenance: High               Maintenance: Zero
```

## How Lambda Works

```
Event happens:

S3 file uploaded
     ↓
┌────────────────────────────┐
│ Lambda triggers            │
├────────────────────────────┤
│ ✓ Run your code            │
│ ✓ With the event data      │
│ ✓ Complete and exit        │
│ ✓ Return result            │
└────────────────────────────┘
     ↓
Event processed!


YOUR LAMBDA CODE:

def lambda_handler(event, context):
    # event = what triggered Lambda
    # context = execution info (time, logs, etc)

    # Your code here
    result = process(event)

    # Return response
    return {
        'statusCode': 200,
        'body': 'Done!'
    }
```

## Create & Test Lambda

```python
# Create a Lambda function (LocalStack)

import boto3
import zipfile
import io

lambda_client = boto3.client(
    'lambda',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Step 1: Write function code
lambda_code = '''
def lambda_handler(event, context):
    name = event.get('name', 'World')
    return {
        'statusCode': 200,
        'body': f'Hello, {name}!'
    }
'''

# Step 2: Package as ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w') as z:
    z.writestr('lambda_function.py', lambda_code)
zip_buffer.seek(0)

# Step 3: Create function
lambda_client.create_function(
    FunctionName='hello-world',
    Runtime='python3.9',
    Role='arn:aws:iam::123456789012:role/service-role',
    Handler='lambda_function.lambda_handler',
    Code={'ZipFile': zip_buffer.read()}
)
print('✓ Lambda function created')

# Step 4: Invoke function
response = lambda_client.invoke(
    FunctionName='hello-world',
    Payload=b'{"name": "Alice"}'
)

# Read response
import json
result = json.loads(response['Payload'].read())
print(f"Result: {result}")
# Output: Result: {'statusCode': 200, 'body': 'Hello, Alice!'}
```

## Lambda with S3

```python
# Lambda triggered by S3 upload:

def lambda_handler(event, context):
    """
    Triggered when file uploaded to S3
    """

    # Extract S3 details from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    print(f'Processing: s3://{bucket}/{key}')

    # Download from S3
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read()

    # Process file
    lines = content.decode().split('\n')
    print(f'File has {len(lines)} lines')

    # Upload result
    s3.put_object(
        Bucket=bucket,
        Key=f'processed/{key}',
        Body=json.dumps({'lines': len(lines)})
    )

    return {'statusCode': 200, 'message': 'Processed!'}
```

---

# SNS: Notifications

## What is SNS?

**SNS = Simple Notification Service = Broadcast messages**

```
Publisher sends one message:

Data validated ✓
     ↓
SNS Topic publishes
     ↓
Subscribers receive:

├─ Email: admin@company.com ✓
├─ Lambda: process_data() ✓
├─ SQS: data-queue ✓
└─ Webhook: https://example.com ✓

All receive simultaneously!
```

## SNS Setup & Publish

```python
import boto3
import json

sns = boto3.client(
    'sns',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1'
)

# Create topic
topic_response = sns.create_topic(Name='data-events')
topic_arn = topic_response['TopicArn']
print(f'Topic ARN: {topic_arn}')

# Add subscribers
# Email subscriber
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='admin@example.com'
)

# Lambda subscriber
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='lambda',
    Endpoint='arn:aws:lambda:us-east-1:123:function:process'
)

# SQS subscriber
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint='arn:aws:sqs:us-east-1:123:my-queue'
)

# Publish message
message = {
    'event': 'data-validated',
    's3_location': 's3://bucket/file.csv',
    'timestamp': '2024-10-21T10:30:00Z'
}

sns.publish(
    TopicArn=topic_arn,
    Subject='Data Event',
    Message=json.dumps(message, indent=2)
)
print('✓ Message published to all subscribers')
```

---

# SQS: Message Queues

## What is SQS?

**SQS = Simple Queue Service = Reliable message storage**

```
Producer puts message:

Send CSV to queue
     ↓
┌──────────────────────────────┐
│ SQS Queue (stores message)   │
│                              │
│ ┌────────────────────────┐   │
│ │ Message 1: file1.csv   │   │
│ │ Message 2: file2.csv   │   │
│ │ Message 3: file3.csv   │   │
│ └────────────────────────┘   │
│                              │
│ Storage: Up to 14 days       │
│ Guarantee: No message loss   │
└──────────────────────────────┘
     ↓
Consumer polls queue:

Get 1 message, process, delete
Get 1 message, process, delete
Get 1 message, process, delete
```

## SQS Setup

```python
import boto3
import json

sqs = boto3.client(
    'sqs',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1'
)

# Create queue
queue_response = sqs.create_queue(
    QueueName='data-processing',
    Attributes={
        'VisibilityTimeout': '300',  # 5 minutes
        'MessageRetentionPeriod': '86400'  # 1 day
    }
)
queue_url = queue_response['QueueUrl']
print(f'Queue URL: {queue_url}')

# Create Dead Letter Queue (for failed messages)
dlq_response = sqs.create_queue(QueueName='data-processing-dlq')
dlq_url = dlq_response['QueueUrl']

# Get DLQ ARN
dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_url,
    AttributeNames=['QueueArn']
)['Attributes']['QueueArn']

# Set redrive policy (DLQ config)
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'  # After 3 failures → DLQ
        })
    }
)
print('✓ Queue created with DLQ')
```

## Send & Receive Messages

```python
# Send message
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({
        'file': 'data.csv',
        'bucket': 'my-bucket'
    })
)
print('✓ Message sent to queue')

# Receive message
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=20  # Long polling
)

# Process message
for message in response.get('Messages', []):
    body = json.loads(message['Body'])
    print(f"Processing: {body['file']}")

    # Do work...
    process_file(body)

    # Delete message (only if successful)
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )
    print('✓ Message deleted from queue')
```

## Message Lifecycle

```
Timeline with visibility timeout:

0:00  Message arrives (visible)
      ├─ Status: AVAILABLE
      └─ ReceiveCount: 0
           ↓
0:05  Consumer polls (message invisible for 5 min)
      ├─ Status: IN_FLIGHT
      ├─ ReceiveCount: 1
      ├─ Visibility expires: 5:05
           ↓
0:10  Consumer finishes ✓ or fails ✗
      │
      ├─ SUCCESS: delete_message() called
      │  └─ Message DELETED permanently
      │
      └─ FAILURE: No delete call
         └─ Message stays invisible
              ↓
5:05       Visibility timeout expires
           ├─ Status: AVAILABLE again
           ├─ ReceiveCount: 2
                ↓
5:10       Consumer polls again (Retry 1)
           ... repeat until maxReceiveCount
                ↓
After 3 failures:
           Message → Dead Letter Queue
           Human investigates why it failed
```

---

# Step Functions: Orchestration

## What is Step Functions?

**Step Functions = Workflow automation (like Data Factory pipelines)**

```
Your Workflow:

┌────────────────┐
│ 1. Validate    │
│    S3 file     │
└────────┬───────┘
         │
         ↓
    ┌────────────┐
    │ Valid?     │
    └┬───────┬───┘
     │       │
    YES     NO
     │       └──→ Send alert
     │
     ↓
┌────────────────┐
│ 2. Transform   │
│    with Lambda │
└────────┬───────┘
         │
         ↓
┌────────────────┐
│ 3. Load to     │
│    database    │
└────────┬───────┘
         │
         ↓
    ✓ Complete!
```

## Create Workflow

```python
import boto3
import json

stepfunctions = boto3.client(
    'stepfunctions',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1'
)

# Define workflow (State Machine)
definition = {
    "Comment": "Data Pipeline",
    "StartAt": "ValidateData",
    "States": {
        "ValidateData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123:function:validate",
            "Next": "IsValid"
        },
        "IsValid": {
            "Type": "Choice",
            "Choices": [
                {
                    "Variable": "$.valid",
                    "BooleanEquals": True,
                    "Next": "TransformData"
                }
            ],
            "Default": "SendAlert"
        },
        "TransformData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123:function:transform",
            "End": True
        },
        "SendAlert": {
            "Type": "Task",
            "Resource": "arn:aws:sns:us-east-1:123:my-topic",
            "End": True
        }
    }
}

# Create state machine
response = stepfunctions.create_state_machine(
    name='data-pipeline',
    definition=json.dumps(definition),
    roleArn='arn:aws:iam::123456789012:role/service-role'
)
state_machine_arn = response['stateMachineArn']
print(f'✓ State Machine: {state_machine_arn}')

# Execute workflow
execution = stepfunctions.start_execution(
    stateMachineArn=state_machine_arn,
    input=json.dumps({
        'bucket': 'my-bucket',
        'key': 'data.csv'
    })
)
print(f'✓ Execution started: {execution["executionArn"]}')
```

---

# Azure → AWS Bridge

## Service Mapping

```
Your Azure Knowledge              AWS Equivalent

┌─────────────────────┐          ┌─────────────────────┐
│ Azure Blob Storage  │ ──95%──→ │ AWS S3              │
│ (cloud storage)     │          │ (object storage)    │
└─────────────────────┘          └─────────────────────┘

┌─────────────────────┐          ┌─────────────────────┐
│ Synapse Spark       │ ──90%──→ │ AWS Glue / EMR      │
│ (big data compute)  │          │ (managed Spark)     │
└─────────────────────┘          └─────────────────────┘

┌─────────────────────┐          ┌─────────────────────┐
│ Azure Data Factory  │ ──100%─→ │ Step Functions      │
│ (orchestration)     │          │ (workflow)          │
└─────────────────────┘          └─────────────────────┘

┌─────────────────────┐          ┌─────────────────────┐
│ Azure Functions     │ ──100%─→ │ AWS Lambda          │
│ (serverless code)   │          │ (serverless code)   │
└─────────────────────┘          └─────────────────────┘

┌─────────────────────┐          ┌─────────────────────┐
│ Event Hub           │ ──100%─→ │ SNS / SQS / Kinesis │
│ (messaging)         │          │ (messaging)         │
└─────────────────────┘          └─────────────────────┘
```

## SQL → Spark SQL

```
Your SQL Skills Transfer Perfectly!

AZURE (T-SQL)                    AWS (Spark SQL)

SELECT                           SELECT
  customer_id,                     customer_id,
  COUNT(*) as orders               COUNT(*) as orders
FROM customers                   FROM customers
WHERE status = 'active'          WHERE status = 'active'
GROUP BY customer_id             GROUP BY customer_id

99% identical syntax!
```

## PySpark Code (Same Everywhere)

```python
from pyspark.sql import SparkSession

# Same code works:
# - Locally (Spark Standalone)
# - On AWS Glue
# - On AWS EMR

spark = SparkSession.builder \
    .appName("MyApp") \
    .getOrCreate()

# Read data
df = spark.read.csv('s3://bucket/data.csv', header=True)

# Transform
result = df.filter(df.amount > 100) \
    .groupBy('customer_id') \
    .count()

# Write output
result.write.csv('s3://bucket/output/')
```

---

# Hands-On: Build a Pipeline

## Project: CSV → S3 → Validate → Transform → Output

```
Your Pipeline Architecture:

┌────────────────┐
│ Sample Data    │
│ (local CSV)    │
└────────┬───────┘
         │ Upload
         ↓
┌────────────────────────────────┐
│ S3 Bucket (raw/)               │
│ ├─ customers.csv              │
│ └─ orders.csv                 │
└────────┬───────────────────────┘
         │ Trigger
         ↓
┌────────────────────────────────┐
│ Lambda 1: Validate             │
│ ├─ Check file exists           │
│ ├─ Check format (.csv)         │
│ └─ Check size (not empty)      │
└────────┬───────────────────────┘
         │ If valid: publish
         ↓
┌────────────────────────────────┐
│ SNS Topic: data-validated      │
│ Broadcasts message to:         │
│ ├─ SQS Queue                   │
│ └─ Email notification          │
└────────┬───────────────────────┘
         │
         ↓
┌────────────────────────────────┐
│ SQS Queue: data-processing     │
│ ├─ Message 1: file1            │
│ ├─ Message 2: file2            │
│ └─ Awaiting consumer           │
└────────┬───────────────────────┘
         │ Poll
         ↓
┌────────────────────────────────┐
│ Lambda 2: Processor            │
│ ├─ Read from S3               │
│ ├─ Remove duplicates          │
│ ├─ Remove null values         │
│ ├─ Convert to uppercase       │
│ └─ Write output               │
└────────┬───────────────────────┘
         │
         ↓
┌────────────────────────────────┐
│ S3 Bucket (processed/)         │
│ ├─ customers_clean.csv        │
│ └─ orders_clean.csv           │
└────────────────────────────────┘
```

## Step 1: Create Test Data

```bash
# Create sample data
mkdir -p data/input data/output

cat > data/input/customers.csv << 'EOF'
customer_id,name,email,status
1,alice,alice@example.com,active
2,bob,bob@example.com,active
1,alice,alice@example.com,active
3,,charlie@example.com,inactive
4,david,david@example.com,active
EOF

# Verify file
head data/input/customers.csv
```

## Step 2: Setup SNS, SQS, Lambda

```python
# setup_pipeline.py

import boto3
import json
import os

# Initialize clients
sns = boto3.client('sns', endpoint_url='http://localhost:4566', region_name='us-east-1')
sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')
s3 = boto3.client('s3', endpoint_url='http://localhost:4566', region_name='us-east-1')

print("Setting up pipeline...")

# Step 1: Create S3 buckets
s3.create_bucket(Bucket='pipeline-data')
print("✓ S3 bucket created")

# Upload sample data
with open('data/input/customers.csv', 'rb') as f:
    s3.put_object(Bucket='pipeline-data', Key='raw/customers.csv', Body=f.read())
print("✓ Sample data uploaded")

# Step 2: Create SNS topic
topic = sns.create_topic(Name='data-validated')
topic_arn = topic['TopicArn']
print(f"✓ SNS topic created: {topic_arn}")

# Step 3: Create SQS queue and DLQ
queue = sqs.create_queue(
    QueueName='data-processing',
    Attributes={
        'VisibilityTimeout': '300',
        'MessageRetentionPeriod': '86400'
    }
)
queue_url = queue['QueueUrl']

dlq = sqs.create_queue(QueueName='data-processing-dlq')
dlq_url = dlq['QueueUrl']
dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=['QueueArn'])['Attributes']['QueueArn']

# Set DLQ
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={'RedrivePolicy': json.dumps({'deadLetterTargetArn': dlq_arn, 'maxReceiveCount': '3'})}
)
queue_arn = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn'])['Attributes']['QueueArn']
print(f"✓ SQS queue created: {queue_url}")

# Step 4: Subscribe SQS to SNS
sns.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn)
print("✓ SQS subscribed to SNS")

# Step 5: Save config for later
with open('pipeline_config.json', 'w') as f:
    json.dump({
        'topic_arn': topic_arn,
        'queue_url': queue_url,
        'bucket': 'pipeline-data'
    }, f)
print("✓ Configuration saved")

print("\n" + "="*50)
print("PIPELINE SETUP COMPLETE!")
print("="*50)
```

## Step 3: Create Lambda 1 (Validator)

```python
# lambda_validator.py

import boto3
import json
import logging

s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
sns = boto3.client('sns', endpoint_url='http://localhost:4566')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Validate CSV file in S3"""

    bucket = event.get('bucket', 'pipeline-data')
    key = event.get('key', 'raw/customers.csv')
    topic_arn = event.get('topic_arn')

    logger.info(f"Validating: s3://{bucket}/{key}")

    try:
        # Check if file exists
        obj = s3.head_object(Bucket=bucket, Key=key)
        file_size = obj['ContentLength']
        logger.info(f"File size: {file_size} bytes")

        # Download and check format
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        lines = content.strip().split('\n')

        # Validate
        if len(lines) < 2:
            logger.error("File is empty or too small")
            return {'statusCode': 400, 'message': 'Invalid file'}

        if not key.endswith('.csv'):
            logger.error("Not a CSV file")
            return {'statusCode': 400, 'message': 'Invalid format'}

        logger.info("✓ File validation passed")

        # Publish to SNS
        if topic_arn:
            message = {
                'status': 'valid',
                's3_bucket': bucket,
                's3_key': key,
                's3_location': f"s3://{bucket}/{key}",
                'row_count': len(lines) - 1
            }
            sns.publish(
                TopicArn=topic_arn,
                Subject='Data Validation Success',
                Message=json.dumps(message, indent=2)
            )
            logger.info("✓ Published to SNS")

        return {'statusCode': 200, 'message': 'Validated!'}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}
```

## Step 4: Create Lambda 2 (Processor)

```python
# lambda_processor.py

import boto3
import json
import csv
import logging
from io import StringIO

s3 = boto3.client('s3', endpoint_url='http://localhost:4566')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Process CSV from SQS queue"""

    processed_count = 0

    try:
        # Process each message
        for record in event['Records']:
            # Extract S3 location from message
            sns_message = json.loads(record['body'])
            data_message = json.loads(sns_message['Message'])

            bucket = data_message['s3_bucket']
            key = data_message['s3_key']

            logger.info(f"Processing: {key}")

            # Read file
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')

            # Parse CSV
            reader = csv.DictReader(StringIO(content))
            rows = list(reader)
            logger.info(f"Loaded {len(rows)} rows")

            # Transform: Remove duplicates, nulls, uppercase
            seen = set()
            processed_rows = []

            for row in rows:
                # Skip if all values are empty
                if not any(row.values()):
                    continue

                # Skip duplicates
                row_tuple = tuple(sorted(row.items()))
                if row_tuple in seen:
                    continue
                seen.add(row_tuple)

                # Uppercase string fields
                clean_row = {
                    k: v.upper() if isinstance(v, str) else v
                    for k, v in row.items()
                }
                processed_rows.append(clean_row)

            logger.info(f"After cleaning: {len(processed_rows)} rows")

            # Write output
            output_key = key.replace('raw/', 'processed/').replace('.csv', '_clean.csv')
            output_buffer = StringIO()

            if processed_rows:
                writer = csv.DictWriter(output_buffer, fieldnames=processed_rows[0].keys())
                writer.writeheader()
                writer.writerows(processed_rows)

            s3.put_object(
                Bucket=bucket,
                Key=output_key,
                Body=output_buffer.getvalue()
            )

            logger.info(f"✓ Output: s3://{bucket}/{output_key}")
            processed_count += 1

        return {'statusCode': 200, 'processed': processed_count}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e
```

## Step 5: Run the Pipeline

```bash
# 1. Setup
python3 setup_pipeline.py

# 2. Invoke Lambda 1 (Validator)
python3 << 'EOF'
import boto3
import json

lambda_client = boto3.client('lambda', endpoint_url='http://localhost:4566')
config = json.load(open('pipeline_config.json'))

response = lambda_client.invoke(
    FunctionName='validator-lambda',
    Payload=json.dumps({
        'bucket': 'pipeline-data',
        'key': 'raw/customers.csv',
        'topic_arn': config['topic_arn']
    })
)

result = json.loads(response['Payload'].read())
print(f"Validator result: {result}")
EOF

# 3. Check SQS queue
python3 << 'EOF'
import boto3
import json

sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')
config = json.load(open('pipeline_config.json'))

response = sqs.receive_message(QueueUrl=config['queue_url'])
print(f"Messages in queue: {len(response.get('Messages', []))}")
EOF

# 4. Invoke Lambda 2 (Processor)
python3 << 'EOF'
import boto3
import json

lambda_client = boto3.client('lambda', endpoint_url='http://localhost:4566')

# Get message from queue to pass to Lambda
sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')
config = json.load(open('pipeline_config.json'))
response = sqs.receive_message(QueueUrl=config['queue_url'])

# Invoke processor with queue message
lambda_client.invoke(
    FunctionName='processor-lambda',
    Payload=json.dumps({'Records': response.get('Messages', [])})
)

print("✓ Processing complete")
EOF

# 5. Check output
python3 << 'EOF'
import boto3
import csv

s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

response = s3.get_object(Bucket='pipeline-data', Key='processed/customers_clean.csv')
content = response['Body'].read().decode()

print("Output file content:")
print(content)
EOF
```

---

## Summary

```
You now understand:

┌─────────────────────────────────────────┐
│ ✓ S3: Cloud storage                     │
│   └─ Buckets, keys, upload/download    │
│                                         │
│ ✓ Lambda: Serverless functions         │
│   └─ Triggered by events               │
│                                         │
│ ✓ SNS: Broadcast notifications         │
│   └─ Publish to multiple subscribers   │
│                                         │
│ ✓ SQS: Reliable message queues         │
│   └─ Store, retrieve, process          │
│                                         │
│ ✓ Step Functions: Orchestration        │
│   └─ Automate workflows                │
│                                         │
│ ✓ Azure → AWS mapping                  │
│   └─ Your skills transfer!             │
│                                         │
│ ✓ Built a complete pipeline:           │
│   └─ Validate → Notify → Process       │
│                                         │
│ ═════════════════════════════════════ │
│   READY FOR REAL AWS! 🚀               │
└─────────────────────────────────────────┘
```

---

## Next Steps

1. **Modify the pipeline** - Change validation logic, transformations, etc.
2. **Add more Lambda functions** - Do more complex processing
3. **Use real AWS** - Same code, just different endpoint_url
4. **Build your own** - Create a pipeline for your data

Good luck! 🎉
