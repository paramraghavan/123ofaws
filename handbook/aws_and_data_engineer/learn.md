# Learning AWS Data Engineering: Introductory Labs

**Prerequisites**: [Setup complete](setup.md), LocalStack started with `lstk start --type aws`, and the local Python
credentials/Region from `localstack.env` loaded before starting Jupyter. Use `lstk aws` for CLI calls. Check license coverage for
Lambda and Step Functions; see [Docker and endpoint configuration](localstack-docker-setup.md). These examples run
Python on the host; `localhost:4566` is not the endpoint for code running inside another container.

---

For Glue, EMR, Spark tuning, governance, streaming, and SSM, continue with the
[complete reference](complete-aws-data-engineering-handbook.md).

For notebook commands and file creation, use [the Jupyter lab instructions](jupyter-lan-setup.md#7-use-the-existing-labs-entirely-from-notebooks).
Choose **AWS Lab (Mac)** and run `%cd ~/my-aws-project` before these labs. Service concepts are in [the service overview](README.md#services-to-know)
and the full reference; this file contains the local API exercises.

## Table of Contents

1. [S3: Cloud Storage](#s3-cloud-storage)
2. [Lambda: Serverless Functions](#lambda-serverless-functions)
3. [SNS: Notifications](#sns-notifications)
4. [SQS: Message Queues](#sqs-message-queues)
5. [Step Functions: Orchestration](#step-functions-orchestration)
6. [Hands-On: Build a Pipeline](#hands-on-build-a-pipeline)

---

# S3: Cloud Storage

S3 stores objects under bucket/key names. These examples use `my-data-bucket` in LocalStack.

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

First create `data/input/customers.csv` using the [pipeline's sample data](#step-1-create-test-data).

```python
# Upload file
with open('data/input/customers.csv', 'rb') as f:
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

This isolated exercise deploys a small function to LocalStack; the later pipeline instead calls its handlers on the host.

## Create & Test Lambda

This isolated API example requires an existing Lambda execution role trusted by `lambda.amazonaws.com`; replace its
sample role ARN below. Wait for function activation before invoking. For real AWS, add the required logging/service
permissions. Container runtime/image support depends on your LocalStack version and license.

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
    Runtime='python3.12',
    Role='arn:aws:iam::123456789012:role/service-role',
    Handler='lambda_function.lambda_handler',
    Code={'ZipFile': zip_buffer.read()}
)
print('✓ Lambda function created')
lambda_client.get_waiter('function_active_v2').wait(FunctionName='hello-world')

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

SNS publishes messages to subscribers. The pipeline below supplies a complete SNS-to-SQS setup.

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
    Endpoint='arn:aws:lambda:us-east-1:000000000000:function:process'
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

SQS buffers messages for consumers. Delete a message only after successful processing.

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

Receiving a message hides it for the visibility timeout; it does not delete it. Delete with the receipt handle after
success. On failure, allow a retry; the configured redrive policy sends repeatedly received messages to the DLQ.
Standard queues can deliver duplicates, so consumers need idempotent processing.

# Step Functions: Orchestration

Step Functions coordinates workflow steps and failures. This section is a template requiring existing resources.

## Create Workflow

This is an orchestration template, not a self-contained deployment. Replace the example Lambda/topic/role ARNs with
existing resources. The validator must return a top-level Boolean `valid` for the Choice state below; the separate
hello-world function does not implement that contract. The execution role needs Lambda invoke and SNS publish access.

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
            "Resource": "arn:aws:lambda:us-east-1:000000000000:function:validate",
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
            "Resource": "arn:aws:lambda:us-east-1:000000000000:function:transform",
            "End": True
        },
        "SendAlert": {
            "Type": "Task",
            "Resource": "arn:aws:states:::sns:publish",
            "Parameters": {
                "TopicArn": "arn:aws:sns:us-east-1:000000000000:my-topic",
                "Message": "Validation failed"
            },
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

# Hands-On: Build a Pipeline

## Project: CSV → S3 → Validate → Transform → Output

This small-file lab uses LocalStack S3/SNS/SQS and calls Python handler functions on the Mac. It does not deploy
Lambda functions or configure automatic event triggers. Save the four Python files below beside one another in
`~/my-aws-project`; source the local environment before starting Jupyter.

```text
CSV -> S3 raw -> host validator -> SNS -> SQS -> host processor -> S3 processed
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

## Step 2: Set Up S3, SNS, And SQS

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

# Allow this SNS topic to deliver messages to this queue.
queue_policy = {
    'Version': '2012-10-17',
    'Statement': [{
        'Effect': 'Allow',
        'Principal': {'Service': 'sns.amazonaws.com'},
        'Action': 'sqs:SendMessage',
        'Resource': queue_arn,
        'Condition': {'ArnEquals': {'aws:SourceArn': topic_arn}}
    }]
}
sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={'Policy': json.dumps(queue_policy)})

# Step 4: Subscribe SQS to SNS (keep the default SNS envelope).
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

## Step 3: Save The Validator Handler

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

## Step 4: Save The Processor Handler

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

## Step 5: Run The Pipeline On Your Host

First run `python setup_pipeline.py`. Then save the following as `run_pipeline.py` and run `python run_pipeline.py`.
Keep the handler files beside this file. Receive the message once, convert its `Body` field to the handler event's
`body` field, process successfully, and only then delete it using its receipt handle. A second diagnostic receive would
hide the first message for its visibility timeout.

```python
import json
import boto3
from lambda_validator import lambda_handler as validate
from lambda_processor import lambda_handler as process

with open('pipeline_config.json') as config_file:
    config = json.load(config_file)
sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')
s3 = boto3.client('s3', endpoint_url='http://localhost:4566', region_name='us-east-1')

result = validate({
    'bucket': config['bucket'],
    'key': 'raw/customers.csv',
    'topic_arn': config['topic_arn']
}, None)
if result.get('statusCode') != 200:
    raise RuntimeError(f'Validation failed: {result}')

response = sqs.receive_message(
    QueueUrl=config['queue_url'], MaxNumberOfMessages=1, WaitTimeSeconds=20
)
messages = response.get('Messages', [])
if not messages:
    raise RuntimeError('No message arrived; inspect the subscription and queue policy before retrying.')

for message in messages:
    result = process({'Records': [{'body': message['Body']}]}, None)
    if result.get('statusCode') != 200:
        raise RuntimeError(f'Processing failed: {result}')
    sqs.delete_message(QueueUrl=config['queue_url'], ReceiptHandle=message['ReceiptHandle'])
    print('Processed and acknowledged:', result)

obj = s3.get_object(Bucket=config['bucket'], Key='processed/customers_clean.csv')
print(obj['Body'].read().decode())
```

Standard SNS/SQS delivery can contain duplicates. The processor writes to the same output key on retries, but a
production pipeline still needs an explicit idempotency/concurrency design. The handlers read the entire CSV into
memory: this is a small-file lab, not a big-data processing strategy.

For deployed Lambda, package the handlers, use runtime-compatible service endpoints (not host `localhost`), configure
execution roles and an SQS event-source mapping, and handle batch failures. See AWS's
[SNS-to-SQS policy requirements](https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html).

---

## Continue Learning

Change the validator or transformation and rerun the small-file lab. For distributed ETL, use Chapters 7–8 and 11–12 of
the [full reference](complete-aws-data-engineering-handbook.md). For deployed Lambda, add packaging, roles, runtime
endpoints, event-source configuration, and retry/idempotency handling before testing in an AWS sandbox.
