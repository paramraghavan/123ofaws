# ETL Pipeline: Lambda → SNS → SQS → Lambda

**Complete architecture and working code for validating data in S3, then processing through SNS/SQS/Lambda pipeline.**

---

## Architecture Diagram

### High-Level Flow

```
S3 Bucket (Raw Data)
         ↓
    ┌─────────────────────────────┐
    │  Lambda 1: Validator        │
    │  (Check if data is valid)   │
    └──────────┬──────────────────┘
               │
         ┌─────▼──────────────────────────────┐
         │ If valid: Write S3 location to:   │
         │ "s3://bucket/folder/file.csv"     │
         └─────┬──────────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │   SNS Topic          │
    │ "data-validated"     │
    │ (broadcast message)  │
    └──────────┬───────────┘
               │
               │ SNS publishes S3 location
               │ to all subscribers
               │
               ▼
    ┌──────────────────────┐
    │   SQS Queue          │
    │ (subscriber to SNS)  │
    │                      │
    │ ┌──────────────────┐ │
    │ │ M1: s3://...1    │ │
    │ │ M2: s3://...2    │ │
    │ │ M3: s3://...3    │ │
    │ │ ... (max n msgs) │ │
    │ └──────────────────┘ │
    └──────────┬───────────┘
               │
      Lambda 2 polls queue
      (consumer Lambda)
               │
               ▼
    ┌──────────────────────┐
    │  Lambda 2: Processor │
    │  (Process S3 file)   │
    │                      │
    │  ├─ Read from S3     │
    │  ├─ Transform data   │
    │  ├─ Write output     │
    │  └─ Delete from SQS  │
    └──────────────────────┘
```

### Detailed Component View

```
┌───────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  STAGE 1: VALIDATION                                         │
│  ─────────────────────                                       │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │ S3 Raw Data      │────→│ Lambda-Validate  │              │
│  │                  │     │                  │              │
│  │ customers.csv    │     │ Check:           │              │
│  │ orders.csv       │     │ ├─ File exists?  │              │
│  │ data.json        │     │ ├─ Valid format? │              │
│  │                  │     │ ├─ Size OK?      │              │
│  │                  │     │ └─ Schema match? │              │
│  └──────────────────┘     └────────┬─────────┘              │
│                                    │                         │
│                           ┌────────▼────────┐               │
│                           │ Is Valid?       │               │
│                           ├─────────────────┤               │
│                           │ YES → Continue  │               │
│                           │ NO  → Log Error │               │
│                           └────────┬────────┘               │
│                                    │                         │
│  STAGE 2: BROADCAST                │                         │
│  ───────────────────               │                         │
│                            ┌───────▼─────────┐              │
│                            │ SNS Topic       │              │
│                            │ Publishes:      │              │
│                            │ {               │              │
│                            │  "s3_bucket":   │              │
│                            │    "raw-data"   │              │
│                            │  "s3_key":      │              │
│                            │    "..."        │              │
│                            │  "timestamp":   │              │
│                            │    "2024-10-21" │              │
│                            │ }               │              │
│                            └───────┬─────────┘              │
│                                    │                         │
│  STAGE 3: QUEUE                    │                         │
│  ─────────────                     │                         │
│                            ┌───────▼─────────┐              │
│                            │ SQS Queue       │              │
│                            │ (subscriber)    │              │
│                            │                 │              │
│                            │ ┌─────────────┐ │              │
│                            │ │ Message 1   │ │              │
│                            │ │ Message 2   │ │              │
│                            │ │ Message 3   │ │              │
│                            │ │ Message n   │ │              │
│                            │ └─────────────┘ │              │
│                            │                 │              │
│                            │ Max Queue Size: │              │
│                            │ n messages      │              │
│                            └───────┬─────────┘              │
│                                    │                         │
│  STAGE 4: PROCESSING               │                         │
│  ──────────────────                │                         │
│                            ┌───────▼──────────────┐          │
│                            │ Lambda-Processor     │          │
│                            │                      │          │
│                            │ 1. Poll SQS queue    │          │
│                            │ 2. Get S3 location   │          │
│                            │ 3. Download file     │          │
│                            │ 4. Transform data    │          │
│                            │ 5. Write output      │          │
│                            │ 6. Delete from SQS   │          │
│                            │                      │          │
│                            │ Multiple instances:  │          │
│                            │ ├─ Worker-1          │          │
│                            │ ├─ Worker-2          │          │
│                            │ └─ Worker-3          │          │
│                            └──────────────────────┘          │
│                                    │                         │
│  OUTPUT                            │                         │
│  ──────                            │                         │
│                            ┌───────▼──────────────┐          │
│                            │ S3 Output Folder     │          │
│                            │                      │          │
│                            │ processed/           │          │
│                            │ ├─ customers_final   │          │
│                            │ ├─ orders_final      │          │
│                            │ └─ summary.json      │          │
│                            └──────────────────────┘          │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Key Characteristics

```
┌─────────────────────────────────────────────────────────────┐
│ VALIDATION LAMBDA                                           │
├─────────────────────────────────────────────────────────────┤
│ ✓ Triggered by: S3 event or scheduled                       │
│ ✓ Checks: Data validity, format, schema                    │
│ ✓ Action: If valid → Publish S3 location to SNS            │
│ ✓ Timing: Runs once per file                               │
│ ✓ Duration: 5-30 seconds                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SNS TOPIC                                                   │
├─────────────────────────────────────────────────────────────┤
│ ✓ Subscribers: SQS queue + possibly email/Slack            │
│ ✓ Message: S3 location of valid data                       │
│ ✓ Timing: Publishes immediately                            │
│ ✓ Delivery: Instant to all subscribers                     │
│ ✓ Guarantee: Best effort (use SQS for reliability)         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SQS QUEUE                                                   │
├─────────────────────────────────────────────────────────────┤
│ ✓ Receives: From SNS (as subscriber)                        │
│ ✓ Stores: Up to 14 days                                     │
│ ✓ Size: Maximum n messages                                  │
│ ✓ Polling: Consumer Lambda polls regularly                 │
│ ✓ Visibility: Timeout = 300 seconds (5 min)                │
│ ✓ Retries: Auto-retry on failure                           │
│ ✓ DLQ: Failed messages after 3 retries                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PROCESSOR LAMBDA (Consumer)                                 │
├─────────────────────────────────────────────────────────────┤
│ ✓ Triggered by: SQS event source mapping                    │
│ ✓ Polling: AWS manages polling automatically               │
│ ✓ Batch Size: Default 10 messages per invocation            │
│ ✓ Action: Read S3, transform, write output                 │
│ ✓ Scaling: Auto-scales with queue depth                    │
│ ✓ Concurrency: Multiple workers in parallel                │
│ ✓ Deletion: Deletes from SQS on success                    │
│ ✓ Retry: Auto-retry on Lambda exception                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Working Code

### Part 1: Lambda 1 - Validator

```python
import boto3
import json
import logging
from datetime import datetime

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:data-validated"

def lambda_handler(event, context):
    """
    Lambda 1: Validate data in S3
    If valid, publish S3 location to SNS
    """

    try:
        # Extract S3 event details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        logger.info(f"Validating: s3://{bucket}/{key}")

        # Step 1: Check if file exists
        try:
            obj = s3_client.head_object(Bucket=bucket, Key=key)
            file_size = obj['ContentLength']
            logger.info(f"File size: {file_size} bytes")
        except:
            logger.error(f"File not found: s3://{bucket}/{key}")
            return {'statusCode': 404, 'body': 'File not found'}

        # Step 2: Validate file size
        MIN_SIZE = 100  # bytes
        MAX_SIZE = 100 * 1024 * 1024  # 100 MB

        if file_size < MIN_SIZE or file_size > MAX_SIZE:
            logger.error(f"Invalid file size: {file_size}")
            return {'statusCode': 400, 'body': 'Invalid file size'}

        # Step 3: Validate file format (check extension)
        valid_extensions = ['.csv', '.json', '.parquet']
        if not any(key.endswith(ext) for ext in valid_extensions):
            logger.error(f"Invalid file format: {key}")
            return {'statusCode': 400, 'body': 'Invalid file format'}

        # Step 4: Validate content (download sample and check)
        response = s3_client.get_object(Bucket=bucket, Key=key)
        sample = response['Body'].read(1000).decode('utf-8', errors='ignore')

        if not sample or len(sample) == 0:
            logger.error("File is empty")
            return {'statusCode': 400, 'body': 'File is empty'}

        logger.info("✓ File validation passed")

        # Step 5: File is valid - publish to SNS
        message = {
            'status': 'valid',
            's3_bucket': bucket,
            's3_key': key,
            's3_location': f"s3://{bucket}/{key}",
            'file_size': file_size,
            'timestamp': datetime.utcnow().isoformat(),
            'validated_by': 'lambda-validator'
        }

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Data Validation Success',
            Message=json.dumps(message, indent=2)
        )

        logger.info(f"✓ Published to SNS: {message['s3_location']}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File validated and published',
                'location': message['s3_location']
            })
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

---

### Part 2: SNS Topic + SQS Queue Setup

```python
import boto3
import json

sns = boto3.client('sns')
sqs = boto3.client('sqs')

# Step 1: Create SNS Topic
topic_response = sns.create_topic(Name='data-validated')
topic_arn = topic_response['TopicArn']
print(f"Created SNS Topic: {topic_arn}")

# Step 2: Create SQS Queue
queue_response = sqs.create_queue(
    QueueName='data-processing-queue',
    Attributes={
        'VisibilityTimeout': '300',  # 5 minutes
        'MessageRetentionPeriod': '86400',  # 1 day
        'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
    }
)
queue_url = queue_response['QueueUrl']
queue_arn = sqs.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=['QueueArn']
)['Attributes']['QueueArn']

print(f"Created SQS Queue: {queue_url}")
print(f"Queue ARN: {queue_arn}")

# Step 3: Create Dead Letter Queue
dlq_response = sqs.create_queue(QueueName='data-processing-dlq')
dlq_url = dlq_response['QueueUrl']
dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_url,
    AttributeNames=['QueueArn']
)['Attributes']['QueueArn']

print(f"Created DLQ: {dlq_url}")

# Step 4: Set redrive policy (DLQ)
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'  # After 3 failures → DLQ
        })
    }
)
print("✓ Configured DLQ (3 retries)")

# Step 5: Subscribe SQS to SNS
subscription = sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint=queue_arn
)
print(f"✓ SQS subscribed to SNS: {subscription['SubscriptionArn']}")

# Step 6: Allow SNS to publish to SQS
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'Policy': json.dumps({
            'Version': '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {'Service': 'sns.amazonaws.com'},
                'Action': 'sqs:SendMessage',
                'Resource': queue_arn,
                'Condition': {
                    'ArnEquals': {
                        'aws:SourceArn': topic_arn
                    }
                }
            }]
        })
    }
)
print("✓ SNS can publish to SQS")

print("\n" + "="*60)
print("SETUP COMPLETE")
print("="*60)
print(f"SNS Topic ARN:  {topic_arn}")
print(f"SQS Queue URL:  {queue_url}")
print(f"DLQ URL:        {dlq_url}")
print(f"Max Retries:    3 (then → DLQ)")
print(f"Visibility:     300 seconds")
```

---

### Part 3: Lambda 2 - Processor

**Note**: This Lambda uses **SQS Event Source Mapping**. AWS automatically:
- Polls SQS for messages
- Deletes successful messages
- Retains failed messages for retry
- Sends to DLQ after max retries

No manual deletion needed. Just process and handle errors.

```python
import boto3
import json
import logging
import csv
from io import StringIO

s3_client = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda 2: Process data from SQS queue

    Triggered by: SQS event source mapping (AWS manages polling & deletion)
    Input: SQS messages containing S3 locations
    Output: Processed data in S3

    ═════════════════════════════════════════════════════════════════════════
    KEY BEHAVIOR: Message Lifecycle Based on Lambda Success/Failure
    ═════════════════════════════════════════════════════════════════════════

    SUCCESS SCENARIO (Function returns normally):
    ├─ Lambda executes without exceptions
    ├─ All processing completes
    ├─ Function returns {'statusCode': 200, ...}
    │
    └─ AWS Lambda's internal behavior:
       ├─ Detects: SUCCESS ✓
       ├─ Calls: delete_message(ReceiptHandle=...) [BEHIND THE SCENES]
       ├─ Result: MESSAGE PURGED FROM QUEUE (gone forever)
       └─ No retry


    FAILURE SCENARIO (Function raises exception):
    ├─ Lambda encounters error (e.g., S3 read fails, network error)
    ├─ Exception raised with: raise e
    ├─ Function does NOT return successfully
    │
    └─ AWS Lambda's internal behavior:
       ├─ Detects: FAILURE ✗
       ├─ Does NOT call: delete_message()
       ├─ Result: MESSAGE STAYS IN QUEUE (invisible during processing)
       ├─ After visibility timeout expires (5 min):
       │  └─ Message becomes visible again
       ├─ SQS increments: ReceiveCount = 2
       ├─ Next Lambda poll: Same message is received
       ├─ After 3rd failure (ReceiveCount = 3):
       │  └─ Message sent to DEAD LETTER QUEUE
       └─ DLQ: Human reviews what went wrong


    VISIBILITY TIMEOUT DURING PROCESSING:
    ├─ Message invisible for: 300 seconds (5 minutes)
    ├─ If processing takes < 5 min AND succeeds:
    │  └─ Deleted before timeout (message never reappears)
    ├─ If processing takes < 5 min BUT fails:
    │  └─ Message stays, waits 5 min, retries
    └─ If processing takes > 5 min:
       └─ Change visibility (see code below) to extend timeout

    ═════════════════════════════════════════════════════════════════════════
    """

    processed_count = 0
    failed_messages = []

    try:
        # Process each message in batch
        for record in event['Records']:
            try:
                message_id = record['messageId']

                # SNS wraps the message when SNS→SQS, so unwrap
                sns_message = json.loads(record['body'])
                data_message = json.loads(sns_message['Message'])

                logger.info(f"Processing message: {message_id}")

                # Extract S3 location
                bucket = data_message['s3_bucket']
                key = data_message['s3_key']
                s3_location = data_message['s3_location']

                logger.info(f"Reading from: {s3_location}")

                # Step 1: Read file from S3
                response = s3_client.get_object(Bucket=bucket, Key=key)

                if key.endswith('.csv'):
                    # Simple CSV processing (no pandas needed)
                    content = response['Body'].read().decode('utf-8')
                    rows = list(csv.reader(content.strip().split('\n')))
                elif key.endswith('.json'):
                    # Simple JSON processing
                    content = response['Body'].read().decode('utf-8')
                    rows = json.loads(content)
                else:
                    raise ValueError(f"Unsupported file format: {key}")

                logger.info(f"Loaded {len(rows)} rows")

                # Step 2: Transform data
                # Example transformations:
                processed_rows = []
                for row in rows:
                    if isinstance(row, dict):
                        # JSON: convert values to uppercase
                        processed_rows.append({
                            k: v.upper() if isinstance(v, str) else v
                            for k, v in row.items()
                        })
                    elif isinstance(row, list):
                        # CSV: convert to uppercase
                        processed_rows.append([
                            col.upper() if isinstance(col, str) else col
                            for col in row
                        ])

                logger.info(f"After transformation: {len(processed_rows)} rows")
                logger.info("✓ Transformation complete")

                # Step 3: Write output to S3
                output_key = key.replace('raw/', 'processed/').replace('.csv', '_clean.csv')

                if key.endswith('.csv'):
                    output_buffer = StringIO()
                    writer = csv.writer(output_buffer)
                    writer.writerows(processed_rows)
                    output_body = output_buffer.getvalue()
                else:
                    output_body = json.dumps(processed_rows, indent=2)

                s3_client.put_object(
                    Bucket=bucket,
                    Key=output_key,
                    Body=output_body
                )
                logger.info(f"✓ Written to: s3://{bucket}/{output_key}")

                processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process message {record['messageId']}: {str(e)}")
                failed_messages.append(record['messageId'])

                # ═════════════════════════════════════════════════════════════
                # FAILURE PATH: Raise exception
                # ═════════════════════════════════════════════════════════════
                # When we raise exception here:
                # ├─ AWS Lambda catches the exception
                # ├─ Lambda detects: FAILURE ✗
                # ├─ Lambda does NOT call delete_message()
                # ├─ Message stays in queue (invisible during processing)
                # ├─ Visibility timeout expires (5 minutes)
                # ├─ SQS increments ReceiveCount + 1
                # ├─ Message becomes visible again
                # ├─ AWS Lambda polls again (automatic retry)
                # └─ After 3 total receives: Message → Dead Letter Queue
                # ═════════════════════════════════════════════════════════════
                raise e

        # ═════════════════════════════════════════════════════════════════════
        # SUCCESS PATH: Function returns normally (no exception)
        # ═════════════════════════════════════════════════════════════════════
        # When function returns here:
        # ├─ All messages processed successfully (no exceptions raised)
        # ├─ AWS Lambda detects: SUCCESS ✓
        # ├─ AWS Lambda internally calls: delete_message(ReceiptHandle=...)
        # │  (You don't see this call - it happens behind the scenes)
        # ├─ Message is PURGED from queue permanently
        # ├─ ReceiveCount not incremented (message is gone)
        # └─ No retry happens (processing completed successfully)
        # ═════════════════════════════════════════════════════════════════════

        return {
            'statusCode': 200,
            'processed': processed_count,
            'message': f'Processed {processed_count} messages'
        }

    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")

        # ═════════════════════════════════════════════════════════════════════
        # OUTER EXCEPTION: Re-raise to prevent any message from being deleted
        # ═════════════════════════════════════════════════════════════════════
        # This catches exceptions that happen before/after record processing
        # Re-raising ensures entire batch is retained for retry
        # ═════════════════════════════════════════════════════════════════════
        raise e
```

---

### Part 4: Create Lambda-2 Event Source Mapping

After deploying Lambda-2 and running the setup script, connect SQS to Lambda:

```python
import boto3

lambda_client = boto3.client('lambda')

# Create event source mapping (SQS → Lambda-2)
response = lambda_client.create_event_source_mapping(
    EventSourceArn='arn:aws:sqs:us-east-1:123456789012:data-processing-queue',
    FunctionName='processor-lambda',
    Enabled=True,
    BatchSize=10,  # Process up to 10 messages per invocation
    MaximumBatchingWindowInSeconds=5,  # Wait up to 5 sec for 10 messages
    FunctionResponseTypes=['ReportBatchItemFailures']  # Report individual failures
)

print(f"Event source mapping created: {response['UUID']}")
print(f"Status: {response['State']}")
```

**What this does:**
- AWS Lambda polls SQS queue every second
- Gets up to 10 messages at a time
- Invokes your Lambda-2 function
- **On success**: Deletes messages automatically
- **On exception**: Message stays in queue, retries, then DLQ

This is the key difference from manually deleting—AWS manages the lifecycle.

---

## LocalStack Setup (Testing Locally)

```bash
# Terminal 1: Start LocalStack
docker run -it -p 4566:4566 localstack/localstack

# Terminal 2: Setup SNS, SQS, DLQ
python3 setup_sns_sqs.py

# Terminal 2: Create test data in S3
cat > sample.csv << 'EOF'
name,age,city
alice,30,new york
bob,25,los angeles
alice,30,new york
,35,chicago
EOF

aws s3 cp sample.csv s3://my-bucket/raw/data.csv \
  --endpoint-url http://localhost:4566

# Terminal 2: Manually invoke Lambda-1 (Validator)
# Since S3 events are tricky in LocalStack, invoke directly
aws lambda invoke \
  --function-name validator-lambda \
  --payload '{"Records":[{"s3":{"bucket":{"name":"my-bucket"},"object":{"key":"raw/data.csv"}}}]}' \
  --endpoint-url http://localhost:4566 \
  response.json

# Terminal 2: Check queue
aws sqs receive-message \
  --queue-url http://localhost:4566/000000000000/data-processing-queue \
  --endpoint-url http://localhost:4566

# Terminal 2: Invoke Lambda-2 (Processor) with queued message
aws lambda invoke \
  --function-name processor-lambda \
  --payload '{"Records":[...]}' \
  --endpoint-url http://localhost:4566 \
  response.json

# Terminal 2: Check processed output
aws s3 ls s3://my-bucket/processed/ \
  --endpoint-url http://localhost:4566

aws s3 cp s3://my-bucket/processed/data_clean.csv - \
  --endpoint-url http://localhost:4566
```

---

## Execution Timeline

```
0s    - File uploaded to S3
        └─ S3 event triggers Lambda-1

2s    - Lambda-1 validation starts
        ├─ Check file exists ✓
        ├─ Check file size ✓
        ├─ Check format ✓
        └─ Validation passed ✓

3s    - Lambda-1 publishes to SNS
        └─ SNS immediately delivers to SQS

4s    - Message arrives in SQS queue
        └─ Waits for consumer

10s   - Lambda-2 (Processor) polls SQS
        ├─ Gets message from queue
        ├─ Reads from S3
        ├─ Transforms data (dedup, cleanup)
        ├─ Writes to S3 output
        └─ Deletes from queue

15s   - Processing complete ✓
        └─ Output file ready in S3
```

---

## Error Handling

```
SCENARIO 1: Invalid Data
──────────────────────
Lambda-1 checks data
    ↓
Invalid: Returns 400 error (doesn't publish to SNS)
    ↓
No message in queue
    ↓
Data rejected, not processed ✓

SCENARIO 2: Valid Data → Queue
──────────────────────────────
Lambda-1 checks data
    ↓
Valid: Publishes S3 location to SNS
    ↓
SNS delivers to SQS (subscriber)
    ↓
Message stored in queue ✓

SCENARIO 3: Lambda-2 Succeeds
─────────────────────────────
Lambda-2 processes message
    ↓
Transforms and writes to S3
    ↓
Returns successfully
    ↓
AWS Lambda deletes message from queue ✓
    ↓
Message gone, won't retry

SCENARIO 4: Lambda-2 Fails
──────────────────────────
Lambda-2 raises exception
    ↓
AWS Lambda does NOT delete message
    ↓
Visibility timeout expires (5 min)
    ↓
Message reappears in queue
    ↓
Retry 1, Retry 2, Retry 3
    ↓
After 3 retries: → Dead Letter Queue
    ↓
Human reviews DLQ and fixes issue
```

---

## Visibility Timeout & Retry Logic

**Visibility Timeout** = Time a message is hidden from other consumers while one consumer processes it.

### How It Works in Our Pipeline

```
Message lifecycle in SQS queue:

STEP 1: Message arrives (from SNS)
┌──────────────────────────┐
│ Message (VISIBLE)        │
│ ├─ Content: S3 location  │
│ ├─ Receive Count: 0      │
│ └─ Status: AVAILABLE     │
└──────────────────────────┘

STEP 2: Lambda-2 polls and receives
┌──────────────────────────────────┐
│ Message (INVISIBLE)              │
│ ├─ Visibility expires: 5 min     │
│ ├─ Receive Count: 1              │
│ └─ Status: IN_FLIGHT             │
└──────────────────────────────────┘
Lambda-2 starts processing...

STEP 3A: SUCCESS PATH ✓
──────────────────────
Lambda-2 finishes processing
    ↓
Writes output to S3
    ↓
Function returns success
    ↓
AWS Lambda calls: DeleteMessage(ReceiptHandle)
    ↓
┌──────────────────────────┐
│ Message DELETED          │
│ (permanently removed)    │
└──────────────────────────┘

STEP 3B: FAILURE PATH ✗
──────────────────────
Lambda-2 encounters error
    ↓
Raises exception
    ↓
AWS Lambda does NOT call DeleteMessage
    ↓
Message stays in queue (invisible)
    ↓
Visibility timeout expires (5 minutes pass)
    ↓
┌──────────────────────────────────┐
│ Message (VISIBLE again)          │
│ ├─ Receive Count: 2              │
│ └─ Status: AVAILABLE             │
└──────────────────────────────────┘
    ↓
Lambda-2 polls again (automatic retry)
    ↓
Processes again...
    ↓
Still fails? Repeat until Receive Count = 3
```

### Key Concept: SQS Decision Logic

SQS has **no way to know if processing succeeded or failed**. Instead, it uses:

```
Did the consumer call DeleteMessage?

YES (within visibility timeout)
    ↓
✓ Message deleted (success assumed)
✓ Message gone permanently
✓ No retry

NO (message not deleted before timeout)
    ↓
✗ Message reappears (failure assumed)
✗ Available for retry
✗ Retry continues up to maxReceiveCount
```

### Configuration in Our Pipeline

```python
# From Part 2: Setup script
sqs.create_queue(
    QueueName='data-processing-queue',
    Attributes={
        'VisibilityTimeout': '300',  # ← 5 minutes (300 seconds)
        'MessageRetentionPeriod': '86400',  # 1 day
        'ReceiveMessageWaitTimeSeconds': '20'
    }
)

# Retry logic
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'  # ← Max 3 attempts before DLQ
        })
    }
)
```

### Timeline Example

```
Our ETL pipeline with 5-minute visibility timeout:

0:00  File uploaded to S3
      └─ Lambda-1 validates and publishes to SNS

0:02  SNS delivers to SQS
      ┌──────────────────────────────┐
      │ Message 1 (VISIBLE)          │
      │ ├─ S3 location: s3://...     │
      │ ├─ Receive Count: 0          │
      │ └─ Status: AVAILABLE         │
      └──────────────────────────────┘

0:05  Lambda-2 event source mapping polls
      Message becomes invisible
      ┌──────────────────────────────┐
      │ Message 1 (INVISIBLE)        │
      │ ├─ Visibility expires: 5:05  │
      │ ├─ Receive Count: 1          │
      │ └─ Status: IN_FLIGHT         │
      └──────────────────────────────┘

0:10  Lambda-2 finishes processing ✓
      Calls DeleteMessage
      ✓ Message deleted permanently

5:05  (If it had failed instead)
      Visibility timeout expires
      ┌──────────────────────────────┐
      │ Message 1 (VISIBLE again)    │
      │ ├─ Receive Count: 2          │
      │ └─ Status: AVAILABLE         │
      └──────────────────────────────┘

5:08  Lambda-2 polls again (Retry 1)
      Processes...
      Still fails? Message stays in queue

10:08 Visibility timeout expires again
      ┌──────────────────────────────┐
      │ Message 1 (VISIBLE again)    │
      │ ├─ Receive Count: 3          │
      │ └─ Status: AVAILABLE         │
      └──────────────────────────────┘

10:11 Lambda-2 polls (Retry 2)
      Processes...
      Still fails? → Dead Letter Queue

10:12 ┌──────────────────────────────┐
      │ DLQ (DEAD LETTER QUEUE)      │
      │ ├─ Message 1 (for review)    │
      │ ├─ Receive Count: 3          │
      │ └─ Status: QUARANTINED       │
      └──────────────────────────────┘

      Human investigates why all 3 retries failed
      Fixes issue → redrive message or log for analysis
```

### When to Adjust Visibility Timeout

```
VISIBILITY TIMEOUT = How long can your processing take?

TOO SHORT (e.g., 30 seconds)
├─ Problem: Fast processes timeout prematurely
├─ Result: Unnecessary retries
├─ Example: Large file takes 2 minutes → retry happens at 30s
└─ Fix: Increase to match your actual processing time

JUST RIGHT (e.g., 300 seconds / 5 minutes)
├─ Problem: None (for most use cases)
├─ Gives processing time
├─ Allows for SQS polling delay
└─ Our pipeline uses this ✓

TOO LONG (e.g., 43200 seconds / 12 hours)
├─ Problem: Slow error detection
├─ Result: Failed messages wait too long to retry
├─ Example: Lambda fails at 0:05, message doesn't retry until 12:05
└─ Only use for very slow batch processes

For our pipeline:
├─ Processing: ~30 seconds to 2 minutes
├─ Network delays: ~5-10 seconds
├─ Buffer: Use 300 seconds (5 minutes) ✓
└─ If processing is slower, increase visibility timeout
```

### Extending Visibility During Processing

If your Lambda needs more time mid-processing:

```python
# In Lambda-2 Processor, if facing a long-running operation:
sqs_client = boto3.client('sqs')

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            # Start processing
            data = extract_data(record)

            # If taking longer than expected, extend timeout
            if is_long_running_operation(data):
                # Extend visibility by 5 more minutes
                sqs_client.change_message_visibility(
                    QueueUrl='YOUR_QUEUE_URL',
                    ReceiptHandle=record['receiptHandle'],
                    VisibilityTimeout=300  # 5 more minutes
                )
                logger.info("Extended visibility timeout")

            # Continue processing...
            result = expensive_operation(data)

            # Success → AWS Lambda deletes automatically
            return {'statusCode': 200}

        except Exception as e:
            # Failure → message stays, retries after timeout
            raise e
```

---

## How SQS Tracks Retry Count & Moves to DLQ

### ReceiveCount: SQS's Retry Counter

**ReceiveCount** = How many times this message has been received (polled) from the queue.

```
SQS automatically increments ReceiveCount each time a message is:
├─ Delivered to a consumer (Lambda, EC2, custom app)
├─ Made invisible (visibility timeout starts)
└─ Not deleted before timeout expires

SQS stores ReceiveCount as metadata on each message:

┌──────────────────────────────────┐
│ Message in SQS                   │
├──────────────────────────────────┤
│ {                                │
│   "MessageId": "abc123",         │
│   "Body": "S3 location...",      │
│   "ReceiveCount": 1,  ← SQS      │
│   "Attributes": {                │ automatically
│     "ApproximateReceiveCount": 1 │ tracks this
│   }                              │
│ }                                │
└──────────────────────────────────┘
```

### DLQ Decision Logic

SQS compares ReceiveCount against maxReceiveCount:

```
┌──────────────────────────────────────────────────────┐
│ When message visibility timeout expires:             │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Check: Is ReceiveCount >= maxReceiveCount?          │
│                                                      │
│ ┌─────────────┬──────────────────────────────────┐  │
│ │             │                                  │  │
│ │   YES       │          NO                      │  │
│ │             │                                  │  │
│ ├─────────────┴──────────────────────────────────┤  │
│ │                                                  │  │
│ │ Message already received:                       │  │
│ │ ReceiveCount = 3                               │  │
│ │ maxReceiveCount = 3                            │  │
│ │                                                  │  │
│ │ 3 >= 3? YES                                    │  │
│ │ ↓                                              │  │
│ │ SEND TO DLQ                                    │  │
│ │ └─ Message moved (not copied)                  │  │
│ │ └─ Removed from main queue                     │  │
│ │ └─ Available in DLQ for inspection             │  │
│ │                                                  │  │
│ └──────────────────────────────────────────────────┘  │
│ │                                                      │
│ │ Message not yet at limit:                           │
│ │ ReceiveCount = 1                                    │
│ │ maxReceiveCount = 3                                │
│ │                                                      │
│ │ 1 >= 3? NO                                         │
│ │ ↓                                                   │
│ │ RETURN TO QUEUE                                    │
│ │ └─ Message becomes visible                         │
│ │ └─ Lambda polls again (Retry)                      │
│ │ └─ ReceiveCount incremented on next receive        │
│ │                                                      │
│ └──────────────────────────────────────────────────────┘
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Our Pipeline Configuration

```python
# From Part 2: Setup script
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq_arn,
            'maxReceiveCount': '3'  # ← SQS limit for this queue
        })
    }
)

# This means:
# ├─ Allow 3 attempts (ReceiveCount = 1, 2, 3)
# ├─ On 4th visibility timeout (ReceiveCount would be 4):
# │  └─ Message moves to DLQ
# └─ No more retries (message leaves main queue)
```

### Timeline: How ReceiveCount Changes

```
Message lifecycle with ReceiveCount tracking:

0:00 Message arrives in SQS (from SNS)
     ┌────────────────────────────────┐
     │ Message                        │
     │ ├─ ReceiveCount: 0             │
     │ └─ Status: VISIBLE             │
     └────────────────────────────────┘

0:05 Lambda polls and receives
     ┌────────────────────────────────┐
     │ Message                        │
     │ ├─ ReceiveCount: 1  ← SQS sets │
     │ ├─ Visibility: 5:05 expires    │
     │ └─ Status: INVISIBLE           │
     └────────────────────────────────┘
     Lambda starts processing...

0:30 Lambda crashes ✗
     Message NOT deleted
     ReceiveCount stays 1 (not incremented yet)

5:05 Visibility timeout expires
     ┌────────────────────────────────┐
     │ Message                        │
     │ ├─ ReceiveCount: 2  ← SQS      │
     │ │  (incremented by SQS)        │
     │ ├─ Check: 2 >= 3? NO           │
     │ └─ Status: VISIBLE             │
     └────────────────────────────────┘
     Returned to queue for retry

5:10 Lambda polls again (Retry 1)
     Message invisible for 5 minutes
     Processing starts...

10:10 Lambda fails again ✗
      Message NOT deleted

10:10 Visibility timeout expires
      ┌────────────────────────────────┐
      │ Message                        │
      │ ├─ ReceiveCount: 3  ← SQS sets │
      │ ├─ Check: 3 >= 3? YES!         │
      │ └─ Status: VISIBLE             │
      └────────────────────────────────┘

10:11 ┌────────────────────────────────┐
      │ DEAD LETTER QUEUE              │
      │ Message moved here             │
      │ ├─ ReceiveCount: 3             │
      │ ├─ Reason: Exceeded retries    │
      │ └─ Status: QUARANTINED         │
      └────────────────────────────────┘

      Main queue: Message GONE
      DLQ: Message available for investigation
```

### How SQS Implements This

```
Behind the scenes, SQS stores per message:

┌─────────────────────────────────────────────────────┐
│ SQS Message Metadata (stored with each message)     │
├─────────────────────────────────────────────────────┤
│ MessageId: "unique-id"                             │
│ ReceiveCount: 1  ← Counter                         │
│ VisibilityDeadline: "2024-10-21T10:05:00Z"         │
│ ApproximateFirstReceiveTimestamp: "..."            │
│ ApproximateReceiveCount: 1  ← Same as ReceiveCount │
└─────────────────────────────────────────────────────┘

When visibility timeout expires, SQS:
├─ Checks: ReceiveCount < maxReceiveCount?
├─ If YES:
│  ├─ Increments ReceiveCount
│  ├─ Resets visibility timeout
│  └─ Message becomes visible (for retry)
└─ If NO:
   ├─ Moves message to DLQ
   └─ Removes from main queue

You can query ReceiveCount in code:
```python
# Get message and check ReceiveCount
response = sqs.receive_message(QueueUrl=queue_url)
for msg in response.get('Messages', []):
    attributes = msg.get('Attributes', {})
    receive_count = int(attributes.get('ApproximateReceiveCount', 0))
    print(f"Message received {receive_count} times")
    # receive_count = 1, 2, or 3 (then goes to DLQ)
```

### Dead Letter Queue: Quarantine for Failed Messages

DLQ is just another SQS queue configured as a destination:

```python
# DLQ is created and configured
dlq_response = sqs.create_queue(QueueName='data-processing-dlq')
dlq_url = dlq_response['QueueUrl']
dlq_arn = sqs.get_queue_attributes(
    QueueUrl=dlq_url,
    AttributeNames=['QueueArn']
)['Attributes']['QueueArn']

# Main queue configured to redirect failed messages
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq_arn,  # ← Points to DLQ
            'maxReceiveCount': '3'           # ← After 3 attempts
        })
    }
)

# Later: Monitor DLQ for failed messages
dlq_messages = sqs.receive_message(QueueUrl=dlq_url)
for msg in dlq_messages.get('Messages', []):
    print(f"Failed message: {msg['Body']}")
    # Investigate why it failed
    # Fix the issue
    # Manually move back to main queue or delete
```

### SQS Does NOT Have Built-In Retry Logic

**Important:** SQS itself has NO retry logic. It only:
- Increments ReceiveCount
- Checks maxReceiveCount
- Moves to DLQ

The actual **retry** happens because:
- Message stays in queue (not deleted)
- Consumer (Lambda) polls again
- Attempts processing again

```
┌─────────────────────────────────────────────────┐
│ Who does what:                                  │
├─────────────────────────────────────────────────┤
│                                                 │
│ SQS:                                            │
│ ├─ Tracks ReceiveCount ✓                       │
│ ├─ Makes message invisible ✓                   │
│ ├─ Compares count to maxReceiveCount ✓         │
│ ├─ Sends to DLQ ✓                              │
│ └─ Does NOT retry (doesn't poll itself) ✗      │
│                                                 │
│ Lambda:                                         │
│ ├─ Polls SQS (Event Source Mapping) ✓          │
│ ├─ Gets messages ✓                             │
│ ├─ Processes message ✓                         │
│ ├─ Deletes on success ✓                        │
│ ├─ Stays in queue on failure ✓ (indirectly)    │
│ └─ Polls again (automatic retry) ✓             │
│                                                 │
│ Together: Retry mechanism works ✓              │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Key Benefits

✅ **Validation first** - Bad data rejected before processing
✅ **Decoupled** - Validator and Processor independent
✅ **Scalable** - Multiple Processor Lambdas in parallel
✅ **Reliable** - SQS guarantees no message loss
✅ **Auto-retry** - Failed messages retry automatically
✅ **Dead Letter** - Failed messages tracked for review
✅ **No polling code** - AWS manages SQS polling
✅ **Cost effective** - Pay only for what you use

---

## Summary

| Component | Role | Timing |
|-----------|------|--------|
| **Lambda-1** | Validate S3 data | Instant (triggered by S3 event) |
| **SNS** | Broadcast valid data location | Instant (to all subscribers) |
| **SQS** | Queue for reliable processing | Stores up to 14 days |
| **Lambda-2** | Process queued data | Polls regularly, processes at own pace |

One SNS publish → Multiple SQS consumers can process → Auto-retry on failure → DLQ for issues.

Perfect for enterprise ETL pipelines! 🚀
