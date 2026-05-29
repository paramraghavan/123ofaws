# Serverless Framework Deployment Guide

> **Complete guide to deploying serverless applications without AWS console login**: Learn how Serverless Framework authenticates to AWS, deploys Lambda functions, and integrates with CI/CD pipelines—all from the command line.

---

## Table of Contents

1. [Quick Answer](#quick-answer)
2. [How Serverless Deploy Works](#how-serverless-deploy-works)
3. [Authentication Methods](#authentication-methods)
4. [Complete Deployment Example](#complete-deployment-example)
5. [Understanding Stage Variables](#understanding-stage-variables)
6. [Understanding Fn::GetAtt](#understanding-fngetatt)
7. [Understanding Lambda Event Sources](#understanding-lambda-event-sources)
8. [Do You Need AWS Console?](#do-you-need-aws-console)
9. [Serverless Commands](#common-serverless-deploy-commands)
10. [CI/CD Integration](#real-world-cicd-example)
11. [Best Practices](#aws-credentials-best-practices)
12. [Troubleshooting](#troubleshooting-deployment)
13. [Quick Start](#quick-start-5-minutes)

---

## Quick Answer

**Do I need to login to AWS console to deploy?**

❌ **NO!** Serverless Framework deploys entirely from the command line using AWS credentials. No console login required.

---

## How Serverless Deploy Works

### The Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Your Local Machine                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  serverless deploy                                          │
│        ↓                                                    │
│  Read serverless.yml                                        │
│        ↓                                                    │
│  Load AWS Credentials                                       │
│  (from ~/.aws/credentials or env vars)                      │
│        ↓                                                    │
│  Package code (zip files)                                   │
│        ↓                                                    │
│  Create CloudFormation template                             │
│        ↓                                                    │
│  Upload to S3                                               │
│        ↓                                                    │
│  Call AWS CloudFormation API                                │
│        ↓                                                    │
│  AWS creates Lambda, API Gateway, etc.                      │
│        ↓                                                    │
│  Deploy complete ✅                                         │
└─────────────────────────────────────────────────────────────┘
```

### What Happens Behind the Scenes

1. **Read Configuration**: Serverless reads your `serverless.yml`
2. **Authenticate**: Uses AWS credentials to authenticate
3. **Package Code**: Zips your Lambda functions and dependencies
4. **Generate CloudFormation**: Creates infrastructure-as-code template
5. **Upload Artifacts**: Uploads zip files to S3
6. **Create Stack**: Uses CloudFormation to create/update AWS resources
7. **Deploy**: Lambda, API Gateway, IAM roles, and other resources are created
8. **Verify**: Tests connectivity and outputs function details

---

## Authentication Methods

### Method 1: AWS Credentials File (Recommended)

The most common and secure method for local development.

```bash
# Step 1: Create AWS credentials locally
aws configure

# This creates ~/.aws/credentials file:
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = us-east-1

# Step 2: Deploy (Serverless automatically finds credentials)
serverless deploy
```

**Benefits:**
- ✅ Credentials stored locally and securely
- ✅ Automatic discovery by Serverless
- ✅ Works with AWS CLI as well
- ✅ Supports multiple profiles

### Method 2: Environment Variables

Use environment variables for CI/CD or temporary access.

```bash
# Export credentials as environment variables
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1

# Deploy (Serverless uses environment variables)
serverless deploy
```

**Use cases:**
- ✅ GitHub Actions workflows
- ✅ Jenkins/GitLab CI
- ✅ Docker containers
- ✅ Temporary deployments

### Method 3: Named Profiles

Use different credentials for different environments.

```bash
# Configure multiple profiles
aws configure --profile production
aws configure --profile staging
aws configure --profile development

# Use specific profile in deployment
serverless deploy --aws-profile production

# Or set default profile
export AWS_PROFILE=production
serverless deploy
```

**Best for:**
- ✅ Multiple environments
- ✅ Multiple AWS accounts
- ✅ Team collaboration

### Method 4: IAM Role (Brownfield/CI/CD)

For servers, containers, or EC2 instances with attached IAM roles.

```bash
# On EC2/Outpost/Lambda, assumes attached IAM role
# No credentials needed - AWS SDK auto-detects role!
serverless deploy

# Verify role is being used
aws sts get-caller-identity
```

**Perfect for:**
- ✅ EC2 instances with instance profiles
- ✅ Lambda functions (if deploying from Lambda)
- ✅ AWS Outposts/Wavelength
- ✅ Container services

---

## Complete Deployment Example

### Step 1️⃣: Create serverless.yml

```yaml
service: my-data-processor

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

  # IAM permissions for Lambda execution
  iamRoleStatements:
    - Effect: Allow
      Action:
        - s3:GetObject
        - s3:PutObject
      Resource: "arn:aws:s3:::my-bucket/*"
    - Effect: Allow
      Action:
        - logs:CreateLogGroup
        - logs:CreateLogStream
        - logs:PutLogEvents
      Resource: "*"
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:Query
      Resource: "arn:aws:dynamodb:us-east-1:*:table/events"

functions:
  processData:
    handler: handler.process_data
    timeout: 300
    memorySize: 512
    environment:
      BUCKET_NAME: my-bucket
      TABLE_NAME: events
    events:
      # Trigger on S3 upload
      - s3:
          bucket: my-bucket
          event: s3:ObjectCreated:*
          rules:
            - prefix: uploads/
            - suffix: .csv
      # Trigger on HTTP request
      - http:
          path: process
          method: post
          cors: true

  notifyCompletion:
    handler: handler.notify_completion
    timeout: 60
    memorySize: 256
    events:
      # Trigger from SQS queue
      - sqs:
          arn:
            Fn::GetAtt:
              - ProcessingQueue
              - Arn
          batchSize: 10

resources:
  Resources:
    ProcessingQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}
        VisibilityTimeout: 300

plugins:
  - serverless-python-requirements
  - serverless-plugin-tracing

package:
  individually: true
  patterns:
    - '!node_modules/**'
    - '!.git/**'
    - '!.env'
```

### Step 2️⃣: Create Lambda Handler

```python
# handler.py
import json
import boto3
import logging
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

BUCKET_NAME = os.environ['BUCKET_NAME']
TABLE_NAME = os.environ['TABLE_NAME']

def process_data(event, context):
    """
    Process S3 upload or HTTP request.

    S3 Event Structure:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "my-bucket"},
                "object": {"key": "uploads/data.csv"}
            }
        }]
    }

    HTTP Event Structure:
    {
        "body": "...",
        "pathParameters": {...},
        "queryStringParameters": {...}
    }
    """

    try:
        # Determine event type
        if 'Records' in event:
            # S3 event
            return handle_s3_event(event)
        elif 'body' in event:
            # HTTP event
            return handle_http_event(event)
        else:
            raise ValueError("Unknown event type")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_s3_event(event):
    """Handle S3 ObjectCreated event"""
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    logger.info(f"Processing s3://{bucket}/{key}")

    # Read file from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    data = response['Body'].read().decode('utf-8')

    # Process data
    lines = data.strip().split('\n')
    logger.info(f"Processed {len(lines)} lines")

    # Store result in DynamoDB
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            'file_key': {'S': key},
            'processed_at': {'S': datetime.utcnow().isoformat()},
            'line_count': {'N': str(len(lines))},
            'status': {'S': 'completed'}
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processing successful',
            'lines_processed': len(lines)
        })
    }


def handle_http_event(event):
    """Handle HTTP POST request"""
    body = json.loads(event['body'])

    logger.info(f"Processing HTTP request: {body}")

    # Perform processing
    result = {
        'processed': True,
        'input': body,
        'timestamp': datetime.utcnow().isoformat()
    }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }


def notify_completion(event, context):
    """Handle SQS messages for completion notifications"""

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            logger.info(f"Processing notification: {message}")

            # Send notification (email, SNS, etc.)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    return {'statusCode': 200, 'body': 'Notifications sent'}
```

### Step 3️⃣: Create requirements.txt

```txt
boto3>=1.26.0
python-dateutil>=2.8.0
```

### Step 4️⃣: Install Serverless

```bash
# Install serverless framework globally
npm install -g serverless

# Or install locally in project
npm init -y
npm install --save-dev serverless

# Install plugins
npm install --save-dev serverless-python-requirements
npm install --save-dev serverless-plugin-tracing
```

### Step 5️⃣: Deploy to AWS

```bash
# Deploy to dev environment
serverless deploy --stage dev

# Or deploy to production
serverless deploy --stage prod

# Deploy with verbose output to see details
serverless deploy --stage prod --verbose

# Deploy specific function only (faster)
serverless deploy function -f processData --stage prod
```

### 🎉 What Serverless Creates

```
AWS CloudFormation Stack: my-data-processor-dev
├── Lambda Function
│   ├── my-data-processor-dev-processData
│   └── my-data-processor-dev-notifyCompletion
├── IAM Role (for Lambda execution)
├── CloudWatch Log Groups
│   ├── /aws/lambda/my-data-processor-dev-processData
│   └── /aws/lambda/my-data-processor-dev-notifyCompletion
├── S3 Event Configuration
├── API Gateway
│   └── POST /process endpoint
└── SQS Queue
    └── processing-queue-dev
```

---

## Resource Naming & Event Triggers Explained

As a tutor, it's important to understand **why resources have different names** and **how events trigger Lambda functions**. Let's break down the serverless.yml example.

### Question: Why Different Names?

Looking at the complete deployment example, you might notice:

```yaml
service: my-data-processor

functions:
  notifyCompletion:
    ...

resources:
  Resources:
    ProcessingQueue:
      Properties:
        QueueName: processing-queue-${self:provider.stage}  # ← This becomes: processing-queue-dev
```

**After deployment, you get:**
- Lambda function name: `my-data-processor-dev-notifyCompletion`
- SQS queue name: `processing-queue-dev`

**Why are they different?** Great question!

---

### Understanding Naming Conventions

#### Lambda Function Naming (Automatic)

**Formula:**
```
{service}-{stage}-{function-name}
```

**Applied to your example:**
```
my-data-processor   -   dev   -   notifyCompletion
      ↓              ↓        ↓
    service        stage   function key

Result: my-data-processor-dev-notifyCompletion
```

**Lambda names are AUTO-GENERATED because:**
- Serverless Framework manages Lambda naming
- It ensures uniqueness across AWS regions
- It makes infrastructure-as-code reproducible
- It follows AWS Lambda naming conventions

---

#### SQS Queue Naming (You Control It)

**In your serverless.yml:**
```yaml
resources:
  Resources:
    ProcessingQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}  # ← YOU decide the name
```

**You have full control:**
```
processing-queue-${self:provider.stage}
      ↓
  + Resolves to: processing-queue-dev  (when stage is 'dev')
  + Resolves to: processing-queue-prod (when stage is 'prod')
```

**Why SQS queue names are explicit:**
- SQS queues are **resources you create**, not functions Serverless manages
- You might want a specific queue name for integration with other systems
- CloudFormation (which creates it) requires an explicit name property
- Your application code might reference the queue by this exact name

---

### Visual Comparison

```
LAMBDA FUNCTIONS (Auto-named by Serverless)
├─ processData
│  └─ Full name: my-data-processor-dev-processData
│  └─ Generated by: {service}-{stage}-{function-name}
│
└─ notifyCompletion
   └─ Full name: my-data-processor-dev-notifyCompletion
   └─ Generated by: {service}-{stage}-{function-name}


SQS QUEUES (Explicitly named in resources)
└─ ProcessingQueue
   └─ Queue name: processing-queue-dev
   └─ Defined by: QueueName property in YAML
```

---

### How notify_completion Lambda Function Works

Now let's understand the complete flow of the `notify_completion` Lambda function.

#### The Configuration

```yaml
functions:
  notifyCompletion:
    handler: handler.notify_completion      # ← Python function to execute
    timeout: 60                              # ← Max 60 seconds per invocation
    memorySize: 256                          # ← 256 MB RAM
    events:
      - sqs:                                 # ← Event source: SQS queue
          arn:
            Fn::GetAtt:
              - ProcessingQueue               # ← Which queue?
              - Arn                           # ← Get its ARN
          batchSize: 10                      # ← Process 10 messages at a time
```

#### The Complete Flow

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: Message Arrives in SQS Queue                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Publisher sends message:                                    │
│  {                                                           │
│    "order_id": "ORD-123",                                   │
│    "customer": "John Doe"                                   │
│  }                                                           │
│                                                              │
│  Message sits in: processing-queue-dev                       │
│  (waiting to be processed)                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: Serverless Detects Message (Event Mapping)          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  At deployment, Serverless creates an Event Source Mapping: │
│  - Lambda function: my-data-processor-dev-notifyCompletion  │
│  - SQS source: processing-queue-dev (via Fn::GetAtt ARN)    │
│  - Batch size: 10 messages                                  │
│                                                              │
│  This mapping continuously polls the queue for messages     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: Messages Batched & Lambda Triggered                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  When messages arrive:                                       │
│  - SQS Event Source Mapping collects up to 10 messages      │
│  - Invokes Lambda function with batched event              │
│                                                              │
│  Event structure passed to Lambda:                          │
│  {                                                           │
│    "Records": [                                             │
│      {                                                       │
│        "messageId": "msg-1",                                │
│        "receiptHandle": "handle-1",                         │
│        "body": "{\"order_id\": \"ORD-123\", ...}",         │
│        "attributes": {                                       │
│          "ApproximateReceiveCount": "1",                    │
│          "SentTimestamp": "1234567890",                     │
│          "SequenceNumber": "1",                             │
│          "ApproximateFirstReceiveTimestamp": "1234567890"   │
│        }                                                     │
│      },                                                      │
│      ... (up to 9 more messages)                            │
│    ]                                                         │
│  }                                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: Lambda Function Processes Messages                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Handler code (from handler.py):                            │
│                                                              │
│  def notify_completion(event, context):                     │
│    for record in event['Records']:                          │
│      message = json.loads(record['body'])                   │
│      # Process the message                                  │
│      send_notification(message)                             │
│                                                              │
│    return {'statusCode': 200, 'body': 'Notifications sent'} │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 5: Success - Message Deleted from Queue                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  If Lambda returns successfully (no exception):             │
│  - SQS automatically deletes the message from queue         │
│  - Message will NOT be reprocessed                          │
│                                                              │
│  If Lambda fails or crashes:                                │
│  - Message stays in queue                                   │
│  - After VisibilityTimeout (300s), message reappears       │
│  - SQS retries the message with Lambda again               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```
>  AWS doesn't need you to explicitly say "success" - if your handler completes without throwing an exception, it's success.
---

### Detailed Handler Code Explained

Here's the actual Python code with tutoring annotations:

```python
# handler.py
import json
import boto3
import logging
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def notify_completion(event, context):
    """
    Lambda function triggered by SQS queue

    Args:
        event: Contains up to 10 SQS messages (batch)
        context: Lambda execution context

    Returns:
        Response indicating success/failure
    """

    # STEP 1: Iterate through all messages in the batch
    # (Usually 1-10 messages depending on queue and timing)
    for record in event['Records']:
        try:
            # STEP 2: Extract the actual message body
            # Note: SQS wraps the message, we need to unwrap it
            message_body = record['body']

            # If the message came from SNS→SQS, it's double-wrapped
            # Check if it's SNS format
            if 'Message' in message_body:
                # It's from SNS subscription
                sns_message = json.loads(message_body)
                order = json.loads(sns_message['Message'])
            else:
                # Direct SQS message
                order = json.loads(message_body)

            # STEP 3: Process the message
            logger.info(f"Processing completion notification for order: {order['order_id']}")

            # Example: Send email, SMS, or webhook
            send_notification(
                customer_email=order.get('customer_email'),
                customer_phone=order.get('customer_phone'),
                order_id=order['order_id'],
                status='Order processing complete!'
            )

            # STEP 4: Log success
            logger.info(f"✓ Successfully notified customer for order {order['order_id']}")

        except Exception as e:
            # If processing fails, Lambda will raise exception
            # SQS will keep the message in queue and retry
            logger.error(f"✗ Error processing message: {str(e)}", exc_info=True)

            # Important: Re-raise to signal failure
            # This causes message to remain in queue for retry
            raise e

    # STEP 5: Return success (all messages processed)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Notifications sent',
            'processed_count': len(event['Records'])
        })
    }


def send_notification(customer_email, customer_phone, order_id, status):
    """Helper function to send notifications"""
    # In production: Actually send email/SMS/webhook
    # For this example: Just log it
    logger.info(f"Sending notification to {customer_email} about order {order_id}: {status}")
```

---

### Key Concepts

#### 1. Event Source Mapping (The Connection)

```yaml
events:
  - sqs:
      arn: !GetAtt ProcessingQueue.Arn   # ← CloudFormation fetches the ARN
      batchSize: 10                       # ← Batch up to 10 messages
```

**What this does:**
- Creates an Event Source Mapping between SQS and Lambda
- Lambda automatically invokes when messages arrive
- No manual polling needed

**How it works:**
```
AWS Event Source Mapping (invisible to you)
┌─────────────────────────────────────────┐
│ Continuously polls SQS queue             │
│ Every 1-2 seconds (configurable)         │
│ Collects up to 10 messages               │
│ Invokes Lambda with batch                │
└─────────────────────────────────────────┘
           ↓
    my-data-processor-dev-notifyCompletion
           ↓
    Lambda processes batch
           ↓
    Returns success?
    → YES: Delete messages from SQS
    → NO: Keep in queue, retry later
```

---

#### 2. Fn::GetAtt - Dynamic Resource Linking

```yaml
arn:
  Fn::GetAtt:
    - ProcessingQueue    # ← The CloudFormation resource name
    - Arn               # ← What attribute to fetch
```

**Why this is important:**
```
❌ WITHOUT Fn::GetAtt (hardcoded):
   arn: "arn:aws:sqs:us-east-1:123456789012:processing-queue-dev"
   Problems:
   - Hardcoded account ID (not portable)
   - Hardcoded region (not portable)
   - Hardcoded queue name (breaks if queue renamed)
   - Must manually update if stack name changes

✅ WITH Fn::GetAtt (dynamic):
   arn: !GetAtt ProcessingQueue.Arn
   Benefits:
   - Always correct (auto-generated)
   - Works across regions (dynamic)
   - Works across AWS accounts (dynamic)
   - Auto-updates if resource changes
```

---

#### 3. Batch Processing

```yaml
batchSize: 10
```

**What happens with 15 messages in queue:**

```
Polling cycle 1:
  - Collects messages 1-10
  - Invokes Lambda with batch of 10

Lambda processes all 10 messages:
  for record in event['Records']:  # 10 iterations
    process(record)

Polling cycle 2 (after Lambda finishes):
  - Collects remaining 5 messages
  - Invokes Lambda with batch of 5

Lambda processes all 5 messages:
  for record in event['Records']:  # 5 iterations
    process(record)
```

**Cost implication:**
```
15 messages with batchSize=10:
- 2 Lambda invocations (10 + 5)
- Cost: $0.0000002 × 2 = $0.0000004

15 messages with batchSize=1:
- 15 Lambda invocations
- Cost: $0.0000002 × 15 = $0.000003

Batching saves 7.5x on Lambda invocation costs!
```

---

### Common Scenarios

#### Scenario 1: Message Arrives, Lambda Processes Successfully

```
Queue: processing-queue-dev
  Message: {order_id: 123}
    ↓
Serverless Event Mapping detects
    ↓
Lambda: my-data-processor-dev-notifyCompletion
  Receives event with 1 message
  Processes successfully
  Returns {statusCode: 200}
    ↓
AWS: Message deleted from queue
Result: ✅ Message processed and gone
```

#### Scenario 2: Message Arrives, Lambda Crashes

```
Queue: processing-queue-dev
  Message: {order_id: 123}
    ↓
Serverless Event Mapping detects
    ↓
Lambda: my-data-processor-dev-notifyCompletion
  Receives event with 1 message
  Crashes: Exception raised!
    ↓
AWS: Message NOT deleted from queue
  After VisibilityTimeout (300s):
  Message reappears in queue
    ↓
Serverless Event Mapping detects again
    ↓
Lambda: Invoked again
  Retries processing
Result: ⚠️ Message processed eventually (retried)
```

#### Scenario 3: Multiple Messages, Partial Failure

```
Queue: processing-queue-dev
  Message 1: {order_id: 123}  ← OK
  Message 2: {order_id: 124}  ← Bad format!
  Message 3: {order_id: 125}  ← OK
    ↓
Lambda processes batch of 3:
  Message 1: Success ✓
  Message 2: Fails ✗ (raises exception)
  Message 3: Never reached

Result:
  - ALL 3 messages stay in queue
  - Lambda marked as failed
  - Entire batch retried
  - Message 1 processed again (wasted work)

Best practice: Handle one message error,
               don't fail entire batch
```

**Better handler code:**
```python
def notify_completion(event, context):
    """Process each message independently"""

    failed_messages = []

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            send_notification(message)
            logger.info(f"✓ Processed: {message['order_id']}")
        except Exception as e:
            # Log but don't crash
            logger.error(f"✗ Failed: {str(e)}")
            failed_messages.append(record['messageId'])

    # Return success even if some failed
    # This deletes the successful messages
    # Failed messages stay in queue and retry
    return {
        'batchItemFailures': [
            {'itemId': msg_id} for msg_id in failed_messages
        ]
    }
```

---

### Summary Table

| Aspect | Lambda Functions | SQS Queues |
|--------|-----------------|-----------|
| **Naming** | Auto-generated: `{service}-{stage}-{function}` | You control: explicitly named |
| **Example** | `my-data-processor-dev-notifyCompletion` | `processing-queue-dev` |
| **Who manages** | Serverless Framework | CloudFormation (via resources) |
| **Reason for difference** | Serverless adds service/stage prefix | SQS is external AWS resource |
| **Can you customize?** | Limited (via individual naming) | Yes (via QueueName property) |

---

## Understanding Stage Variables

### What Does `stage: ${opt:stage, 'dev'}` Mean?

The `stage` configuration in your `serverless.yml` determines which environment you're deploying to. The special syntax `${opt:stage, 'dev'}` is Serverless Framework's variable syntax.

#### Breaking It Down

```yaml
stage: ${opt:stage, 'dev'}
       └─────┬─────┘  └─┬─┘
         Variable    Default
```

| Part | Meaning |
|------|---------|
| `${...}` | Serverless variable reference syntax |
| `opt:stage` | Get `stage` from CLI options (`--stage` flag) |
| `,` | Separator (means "OR") |
| `'dev'` | Default value if no CLI option provided |

### How It Works

```bash
# Example 1: User provides --stage flag
serverless deploy --stage production

# Serverless evaluates: ${opt:stage, 'dev'}
# Finds: --stage production
# Result: stage = 'production'

# Example 2: User doesn't provide --stage flag
serverless deploy

# Serverless evaluates: ${opt:stage, 'dev'}
# Doesn't find: --stage (not provided)
# Uses default: 'dev'
# Result: stage = 'dev'
```

### Real-World Example

When you deploy with different stages, everything changes:

```bash
# Deploy to development (default)
serverless deploy

# Stack created: my-data-processor-dev
# Lambda functions:
#   - my-data-processor-dev-processData
#   - my-data-processor-dev-notifyCompletion
# API endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/

# Deploy to production
serverless deploy --stage production

# Stack created: my-data-processor-production
# Lambda functions:
#   - my-data-processor-production-processData
#   - my-data-processor-production-notifyCompletion
# API endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/production/
```

### How Stage Affects Resources

```
Stage: dev
├── Function name: my-app-dev-myFunction
├── Stack name: my-app-dev
├── S3 bucket: my-app-dev-data
├── Database: my-app-dev-db
└── API endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/

Stage: staging
├── Function name: my-app-staging-myFunction
├── Stack name: my-app-staging
├── S3 bucket: my-app-staging-data
├── Database: my-app-staging-db
└── API endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/staging/

Stage: production
├── Function name: my-app-prod-myFunction
├── Stack name: my-app-prod
├── S3 bucket: my-app-prod-data
├── Database: my-app-prod-db
└── API endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/
```

### Using Stage in Your Lambda Code

You can pass the stage as an environment variable to your Lambda functions:

```yaml
# serverless.yml

provider:
  stage: ${opt:stage, 'dev'}

  # Pass stage to all Lambda functions
  environment:
    ENVIRONMENT: ${self:provider.stage}

functions:
  processData:
    handler: handler.process_data
    environment:
      # Use stage in table name
      TABLE_NAME: users-${self:provider.stage}
```

Then in your Lambda handler:

```python
# handler.py
import os

def process_data(event, context):
    environment = os.environ.get('ENVIRONMENT')
    table_name = os.environ.get('TABLE_NAME')

    if environment == 'production':
        # Production-specific logic
        debug = False
        retention = 30
    else:
        # Development logic
        debug = True
        retention = 7

    return {
        'statusCode': 200,
        'body': f'Running in {environment} - Using table {table_name}'
    }
```

### Common Stage Variables

| Syntax | Meaning | Example |
|--------|---------|---------|
| `${opt:stage}` | CLI option `--stage` | `--stage production` |
| `${opt:region}` | CLI option `--region` | `--region eu-west-1` |
| `${env:VAR_NAME}` | Environment variable | `$BUCKET_NAME` |
| `${self:service}` | Service name | `my-app` |
| `${self:provider.region}` | Provider region | `us-east-1` |
| `${aws:accountId}` | AWS account ID | `123456789012` |
| `${file(./config.json):setting}` | File reference | From JSON file |

### Complete Multi-Stage Example

```yaml
# serverless.yml

service: my-data-app

provider:
  name: aws
  runtime: python3.11
  region: ${opt:region, 'us-east-1'}
  stage: ${opt:stage, 'dev'}

  # Pass stage to all functions
  environment:
    ENVIRONMENT: ${self:provider.stage}
    AWS_ACCOUNT_ID: ${aws:accountId}

functions:
  processData:
    handler: handler.process_data
    timeout: 300
    memorySize: ${self:custom.memorySize.${self:provider.stage}}
    environment:
      # Use stage-specific table name
      TABLE_NAME: data-${self:provider.stage}
    events:
      - s3:
          bucket: my-app-${self:provider.stage}-bucket
          event: s3:ObjectCreated:*

custom:
  # Different memory settings per stage
  memorySize:
    dev: 256
    staging: 512
    production: 1024
```

### Deployment Commands for Different Stages

```bash
# Deploy to all environments

# Development (uses default 'dev')
serverless deploy
# Creates: my-data-app-dev

# Staging
serverless deploy --stage staging
# Creates: my-data-app-staging

# Production
serverless deploy --stage production
# Creates: my-data-app-production

# Different region
serverless deploy --stage prod --region eu-west-1
# Creates: my-data-app-prod in eu-west-1

# Invoke in specific stage
serverless invoke -f processData --stage production

# View logs from specific stage
serverless logs -f processData --stage staging --tail
```

### Why Use Stage Variables?

✅ **Single codebase, multiple environments** - One serverless.yml, many deployments
✅ **No environment-specific files** - Don't need dev.yml, prod.yml, staging.yml
✅ **CLI flexibility** - Choose stage at deploy time
✅ **Default behavior** - Falls back to 'dev' if not specified
✅ **Easy testing** - Deploy test version: `--stage test-123`
✅ **Clean separation** - Each stage has completely separate AWS resources
✅ **No cross-stage conflicts** - Prod won't interfere with dev

---

## Understanding Fn::GetAtt

### What Is Fn::GetAtt?

`Fn::GetAtt` is a **CloudFormation intrinsic function** that retrieves attributes (properties) of AWS resources you've created. Think of it as CloudFormation's way of asking "Hey, what's the ARN (or URL, or ID) of that resource I just created?"

#### For New Users: The Analogy

Imagine you created an SQS queue and need its ARN (Amazon Resource Name) to give to another service. You have two choices:

1. ❌ **Hardcode the ARN** - Create queue, manually copy its ARN, paste it in code (error-prone, breaks if you recreate the queue)
2. ✅ **Use Fn::GetAtt** - Tell CloudFormation to automatically fetch the queue's ARN (always correct, updates automatically)

#### For Experienced Users: The Technical Details

`Fn::GetAtt` is a CloudFormation intrinsic function that:
- Resolves at **stack creation/update time** (not at invocation time)
- Returns **logical resource attributes** from the CloudFormation stack
- Supports **cross-stack references** via the return value
- Replaces placeholders with actual AWS resource values in the generated template
- Is evaluated **before** Lambda function execution (values are baked into environment variables, IAM policies, event source mappings, etc.)

---

### The Syntax

```yaml
Fn::GetAtt:
  - LogicalResourceName
  - AttributeName
```

Or in JSON format:

```json
{"Fn::GetAtt": ["LogicalResourceName", "AttributeName"]}
```

#### Breaking It Down

| Part | Meaning | Example |
|------|---------|---------|
| `Fn::GetAtt` | The CloudFormation function name | — |
| `LogicalResourceName` | The resource ID in serverless.yml | `ProcessingQueue` |
| `AttributeName` | Which attribute to fetch | `Arn`, `Url`, `QueueName` |

---

### Real Example from Your Code

In the complete deployment example, you have:

```yaml
resources:
  Resources:
    ProcessingQueue:           # ← LogicalResourceName
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}
        VisibilityTimeout: 300

functions:
  notifyCompletion:
    handler: handler.notify_completion
    events:
      - sqs:
          arn:
            Fn::GetAtt:        # ← The function
              - ProcessingQueue # ← Which resource?
              - Arn            # ← Which attribute?
          batchSize: 10
```

**What happens:**

1. CloudFormation creates the SQS queue named `processing-queue-dev`
2. The queue gets an ARN like: `arn:aws:sqs:us-east-1:123456789012:processing-queue-dev`
3. `Fn::GetAtt: [ProcessingQueue, Arn]` retrieves that ARN
4. Lambda function is configured to read from that SQS queue using the ARN

---

### How Fn::GetAtt Works (Step-by-Step)

#### Step 1: Define a Resource

```yaml
resources:
  Resources:
    MyQueue:                      # Logical name
      Type: AWS::SQS::Queue       # Resource type
      Properties:
        QueueName: my-queue-dev
```

#### Step 2: Use Fn::GetAtt to Reference It

```yaml
functions:
  myFunction:
    events:
      - sqs:
          arn:
            Fn::GetAtt: [MyQueue, Arn]   # Get the ARN of MyQueue
```

#### Step 3: CloudFormation Generates the Template

```yaml
# Behind the scenes, CloudFormation creates:
Resources:
  MyQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: my-queue-dev

  MyFunctionLambda:
    Type: AWS::Lambda::Function
    Properties:
      EventSourceMappings:
        - EventSourceArn: !GetAtt MyQueue.Arn  # Replaced with actual ARN
          BatchSize: 10
```

#### Step 4: At Deploy Time

```
AWS Creates Queue → ARN = arn:aws:sqs:us-east-1:123456789012:my-queue-dev
                           ↓
                   Fn::GetAtt fetches it
                           ↓
                   Lambda EventSourceMapping updated with actual ARN
                           ↓
                   Lambda can now read from queue ✅
```

---

### Common Use Cases

#### 1. Lambda Triggered by SQS

**Problem:** You create an SQS queue but don't know its ARN yet.

**Solution:** Use Fn::GetAtt

```yaml
resources:
  Resources:
    DataQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: data-processing-queue

functions:
  processQueue:
    handler: handler.process
    events:
      - sqs:
          arn: !GetAtt DataQueue.Arn  # Shorthand for Fn::GetAtt
          batchSize: 5
```

#### 2. Lambda Granted Permission to Access S3

**Problem:** Lambda needs IAM permission to access an S3 bucket. You need the bucket ARN.

**Solution:** Use Fn::GetAtt

```yaml
resources:
  Resources:
    DataBucket:
      Type: AWS::S3::Bucket
      Properties:
        BucketName: my-app-data-${self:provider.stage}

provider:
  iamRoleStatements:
    - Effect: Allow
      Action:
        - s3:GetObject
      Resource:
        - !Sub "${DataBucket.Arn}/*"  # Get bucket ARN dynamically
```

#### 3. SNS Topic Subscription

**Problem:** Lambda needs to subscribe to an SNS topic. You need the topic ARN.

**Solution:** Use Fn::GetAtt

```yaml
resources:
  Resources:
    AlertTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: alerts-${self:provider.stage}

functions:
  alertHandler:
    handler: handler.process_alert
    events:
      - sns:
          arn: !GetAtt AlertTopic.Arn
          topicName: alerts-${self:provider.stage}
```

#### 4. DynamoDB Stream Processing

**Problem:** Lambda needs to consume from a DynamoDB stream. You need the stream ARN.

**Solution:** Use Fn::GetAtt

```yaml
resources:
  Resources:
    EventsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: events-${self:provider.stage}
        BillingMode: PAY_PER_REQUEST
        StreamSpecification:
          StreamViewType: NEW_AND_OLD_IMAGES
        AttributeDefinitions:
          - AttributeName: id
            AttributeType: S
        KeySchema:
          - AttributeName: id
            KeyType: HASH

functions:
  processStream:
    handler: handler.process
    events:
      - stream:
          type: dynamodb
          arn: !GetAtt EventsTable.StreamArn  # Get stream ARN
          batchSize: 100
```

#### 5. Pass Resource ARN to Another Service

**Problem:** You need to pass an SQS queue's ARN as an environment variable to Lambda.

**Solution:** Use Fn::GetAtt

```yaml
resources:
  Resources:
    OutputQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: output-${self:provider.stage}

functions:
  processData:
    handler: handler.process
    environment:
      OUTPUT_QUEUE_ARN: !GetAtt OutputQueue.Arn
```

Then in your Lambda code:

```python
import os

def process(event, context):
    queue_arn = os.environ['OUTPUT_QUEUE_ARN']
    print(f"Sending to queue: {queue_arn}")
```

---

### Common Attributes by Resource Type

#### SQS Queue

```yaml
!GetAtt MyQueue.Arn        # arn:aws:sqs:us-east-1:123456789012:my-queue
!GetAtt MyQueue.QueueName  # my-queue
!GetAtt MyQueue.QueueUrl   # https://sqs.us-east-1.amazonaws.com/123456789012/my-queue
```

#### SNS Topic

```yaml
!GetAtt MyTopic.TopicName  # my-topic
!GetAtt MyTopic.TopicArn   # arn:aws:sns:us-east-1:123456789012:my-topic
```

#### DynamoDB Table

```yaml
!GetAtt MyTable.Arn        # arn:aws:dynamodb:us-east-1:123456789012:table/my-table
!GetAtt MyTable.StreamArn  # arn:aws:dynamodb:us-east-1:123456789012:table/my-table/stream/2015-06-27T00:48:05.899
```

#### S3 Bucket

```yaml
!GetAtt MyBucket.Arn       # arn:aws:s3:::my-bucket
!GetAtt MyBucket.DomainName # my-bucket.s3.amazonaws.com
```

#### Lambda Function

```yaml
!GetAtt MyFunction.Arn     # arn:aws:lambda:us-east-1:123456789012:function:my-function
```

#### API Gateway

```yaml
!GetAtt MyRestApi.RootResourceId  # Resource ID
!GetAtt MyRestApi.RestApiId       # API ID
```

---

### Comparison with Other CloudFormation Functions

| Function | Use Case | Example |
|----------|----------|---------|
| `Ref` | Get logical ID or ARN (simpler) | `!Ref MyQueue` |
| `Fn::GetAtt` | Get specific attribute | `!GetAtt MyQueue.Arn` |
| `Fn::Sub` | String substitution | `${MyQueue.Arn}` |
| `Fn::Join` | Concatenate strings | `!Join [":", ["arn:aws:sqs", MyQueue]]` |
| `Fn::ImportValue` | Cross-stack reference | For nested stacks |

**When to use `Ref` vs `Fn::GetAtt`:**

```yaml
# Use Ref when you need the basic identifier
MyQueue: !Ref ProcessingQueue          # Returns logical ID
MyTopic: !Ref NotificationTopic        # Returns logical ID

# Use Fn::GetAtt when you need a specific property
MyArn: !GetAtt ProcessingQueue.Arn     # Returns ARN
MyUrl: !GetAtt ProcessingQueue.QueueUrl # Returns HTTPS URL
```

---

### Complete Real-World Example

Here's a complete serverless.yml showing multiple Fn::GetAtt patterns:

```yaml
service: order-processing

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

  iamRoleStatements:
    - Effect: Allow
      Action:
        - sqs:SendMessage
        - sqs:DeleteMessage
      Resource:
        - !GetAtt OrderQueue.Arn           # Queue ARN
        - !GetAtt DeadLetterQueue.Arn      # DLQ ARN
    - Effect: Allow
      Action:
        - dynamodb:PutItem
      Resource:
        - !GetAtt OrdersTable.Arn          # Table ARN
    - Effect: Allow
      Action:
        - sns:Publish
      Resource:
        - !GetAtt NotificationTopic.TopicArn  # Topic ARN

functions:
  receiveOrder:
    handler: handler.receive_order
    events:
      - sqs:
          arn: !GetAtt OrderQueue.Arn    # Trigger from queue
          batchSize: 5
    environment:
      ORDERS_TABLE: !Ref OrdersTable     # Table name
      NOTIFICATION_TOPIC: !GetAtt NotificationTopic.TopicArn
      DLQ_URL: !GetAtt DeadLetterQueue.QueueUrl

  processOrder:
    handler: handler.process_order
    environment:
      ORDERS_TABLE: !Ref OrdersTable
      ORDER_STREAM: !GetAtt OrdersTable.StreamArn  # DynamoDB stream
    events:
      - stream:
          type: dynamodb
          arn: !GetAtt OrdersTable.StreamArn
          batchSize: 100

resources:
  Resources:
    OrderQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: orders-${self:provider.stage}
        VisibilityTimeout: 300
        RedrivePolicy:
          deadLetterTargetArn: !GetAtt DeadLetterQueue.Arn  # Link to DLQ
          maxReceiveCount: 3

    DeadLetterQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: orders-dlq-${self:provider.stage}
        MessageRetentionPeriod: 1209600  # 14 days

    NotificationTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: order-notifications-${self:provider.stage}
        DisplayName: Order Notifications

    OrdersTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: orders-${self:provider.stage}
        BillingMode: PAY_PER_REQUEST
        StreamSpecification:
          StreamViewType: NEW_AND_OLD_IMAGES
        AttributeDefinitions:
          - AttributeName: orderId
            AttributeType: S
          - AttributeName: createdAt
            AttributeType: S
        KeySchema:
          - AttributeName: orderId
            KeyType: HASH
          - AttributeName: createdAt
            KeyType: RANGE
```

**What's happening here:**

1. `!GetAtt OrderQueue.Arn` - Gets SQS queue ARN for Lambda permissions
2. `!GetAtt NotificationTopic.TopicArn` - Gets SNS topic ARN for publishing messages
3. `!GetAtt OrdersTable.Arn` - Gets DynamoDB table ARN for permissions
4. `!GetAtt OrdersTable.StreamArn` - Gets DynamoDB stream ARN for event source
5. `!GetAtt DeadLetterQueue.Arn` - Gets DLQ ARN to link for failed messages
6. `!Ref OrdersTable` - Gets table name (simpler reference)

---

### Debugging Fn::GetAtt

If Fn::GetAtt isn't working, try these debugging steps:

**1. Verify Resource Exists**

```yaml
resources:
  Resources:
    MyQueue:  # ← This name must match exactly
      Type: AWS::SQS::Queue
```

```yaml
functions:
  myFunc:
    events:
      - sqs:
          arn: !GetAtt MyQueue.Arn  # ← Must be exact match
```

**2. Check Attribute Name**

```bash
# View available attributes in AWS docs
# For SQS: Arn, QueueName, QueueUrl
# For SNS: TopicArn, TopicName
# For DynamoDB: Arn, StreamArn
```

**3. Check Deployment Logs**

```bash
serverless deploy --verbose

# Look for CloudFormation errors:
# "GetAtt attribute MyQueue does not exist"
# "Resource MyQueue not found"
```

**4. Verify in CloudFormation**

```bash
# Check what was actually created
aws cloudformation describe-stack-resources \
  --stack-name my-app-dev \
  --query 'StackResources[*].[LogicalResourceId,PhysicalResourceId]'
```

---

### Key Takeaways

✅ **Fn::GetAtt retrieves resource properties dynamically** - No hardcoding needed
✅ **Always use it for ARNs and URLs** - Ensures correctness and automatic updates
✅ **Resolved at stack creation time** - Values are baked into the stack, not looked up at runtime
✅ **Supports all AWS resource types** - Each has different available attributes
✅ **Works seamlessly with Serverless Framework** - Use `!GetAtt` shorthand syntax
✅ **Essential for infrastructure-as-code** - Links resources together automatically
✅ **Perfect for multi-environment deployments** - Stage variables + Fn::GetAtt = automation

---

## Understanding Lambda Event Sources

As a tutor, you need to understand **how Lambda gets triggered**. This is done through **Event Sources**, and we specify them in the `events` section of your serverless.yml file.

### What Is an Event Source?

An **Event Source** is anything that triggers your Lambda function:
- S3 bucket upload
- SQS queue message
- HTTP request
- DynamoDB stream update
- CloudWatch schedule
- SNS topic notification

**Where to specify:** The `events:` section in your serverless.yml

---

### Question 1: Where Do We Specify Lambda Polls SQS?

#### The Answer: In the `events` section

```yaml
functions:
  notifyCompletion:
    handler: handler.notify_completion
    events:                          # ← HERE
      - sqs:                         # ← Event type: SQS
          arn:
            Fn::GetAtt:
              - ProcessingQueue
              - Arn
          batchSize: 10              # ← How many messages per invocation
```

**What this does:**
- Tells Serverless Framework to create an **Event Source Mapping**
- Event Source Mapping automatically polls the SQS queue
- When messages arrive, Lambda is invoked with a batch (up to 10 messages)
- No manual polling code needed!

---

### How SQS Polling Works (Behind the Scenes)

```
┌─────────────────────────────────────────────────────────────┐
│ AWS Event Source Mapping (Created at deploy time)           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Continuously monitors: processing-queue-dev               │
│  Every 1-2 seconds:                                         │
│    1. Check queue for messages                              │
│    2. Collect up to 10 messages (batchSize)                 │
│    3. Invoke Lambda with batch                              │
│    4. Wait for Lambda to finish                             │
│    5. Repeat                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                         ↓
                   (Auto-managed)
                   You don't code this!
```

#### SQS Event Configuration

```yaml
events:
  - sqs:
      arn: !GetAtt ProcessingQueue.Arn    # Which queue to poll
      batchSize: 10                        # Max messages per invocation
      maximumBatchingWindowInSeconds: 5    # Wait up to 5 seconds for batch
      functionResponseType: ReportBatchItemFailures  # Handle partial failures
```

| Parameter | Default | Range | Meaning |
|-----------|---------|-------|---------|
| `batchSize` | 10 | 1-10 | Messages per Lambda invocation |
| `maximumBatchingWindowInSeconds` | 0 | 0-300 | Wait time to collect batch |
| `functionResponseType` | `ReportBatchItemFailures` | — | Handle failures per message |

**Real-world examples:**

```yaml
# Fast processing - smaller batches
events:
  - sqs:
      arn: !GetAtt FastQueue.Arn
      batchSize: 1                    # Process 1 at a time
      maximumBatchingWindowInSeconds: 0  # Don't wait

# Batch processing - larger batches
events:
  - sqs:
      arn: !GetAtt BatchQueue.Arn
      batchSize: 10                   # Process 10 at a time
      maximumBatchingWindowInSeconds: 5  # Wait up to 5 seconds
```

---

### Question 2: How Do We Configure S3 Trigger for Lambda?

#### The Answer: Also in the `events` section

```yaml
functions:
  processData:
    handler: handler.process_data
    events:                            # ← HERE
      - s3:                            # ← Event type: S3
          bucket: my-bucket
          event: s3:ObjectCreated:*    # Which S3 events trigger
          rules:
            - prefix: uploads/         # Only files in uploads/ folder
            - suffix: .csv             # Only CSV files
```

**What this does:**
- Creates an S3 Event Notification
- Whenever a file matching the rules is uploaded to S3
- Lambda is automatically invoked
- Event contains the bucket and object key

---

### S3 Event Configuration

#### Supported S3 Events

```yaml
events:
  - s3:
      bucket: my-bucket
      event: s3:ObjectCreated:*        # ANY file upload
      # OR
      event: s3:ObjectCreated:Put      # Direct upload only
      event: s3:ObjectCreated:Post     # Form upload only
      event: s3:ObjectRemoved:*        # ANY file deletion
      event: s3:ObjectRemoved:Delete   # File deleted
      event: s3:ObjectRemoved:DeleteMarkerCreated  # Version marker
```

#### With Filtering Rules

```yaml
events:
  - s3:
      bucket: my-bucket
      event: s3:ObjectCreated:*
      rules:
        - prefix: uploads/data/        # Only in this folder
        - suffix: .csv                 # Only CSV files
        - prefix: backups/
          suffix: .zip
```

**Example filtering combinations:**

```yaml
# Only CSV files in uploads/ folder
rules:
  - prefix: uploads/
  - suffix: .csv

# Only image files
rules:
  - suffix: .jpg
  - suffix: .png
  - suffix: .gif

# Only files in specific folder
rules:
  - prefix: data/processing/

# Files in folder but not subdirectories
rules:
  - prefix: batch/data/
    suffix: .json
```

---

### Comparison: SQS Polling vs S3 Push

| Aspect | SQS | S3 |
|--------|-----|-----|
| **Trigger type** | **Poll** (Lambda asks) | **Push** (S3 notifies) |
| **Lambda waits?** | Yes (polls queue) | No (triggered on event) |
| **Configuration** | `batchSize`, `maximumBatchingWindowInSeconds` | `event`, `prefix`, `suffix` |
| **Data passed** | Message body in array | S3 bucket/key in event |
| **When used** | Queue processing, buffering | File uploads, batch jobs |

---

### Complete Example: Both SQS and S3 Events

```yaml
service: data-processor

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

functions:
  # FUNCTION 1: Triggered when files upload to S3
  processUpload:
    handler: handler.process_s3_upload
    timeout: 300
    events:
      - s3:                              # ← S3 TRIGGER (PUSH)
          bucket: data-bucket
          event: s3:ObjectCreated:*
          rules:
            - prefix: uploads/
            - suffix: .csv
    environment:
      BUCKET_NAME: data-bucket

  # FUNCTION 2: Triggered by SQS queue messages
  processQueue:
    handler: handler.process_queue_messages
    timeout: 60
    events:
      - sqs:                             # ← SQS TRIGGER (POLL)
          arn: !GetAtt ProcessingQueue.Arn
          batchSize: 10
          maximumBatchingWindowInSeconds: 5
    environment:
      QUEUE_URL: !Ref ProcessingQueue

  # FUNCTION 3: Triggered by HTTP request
  apiHandler:
    handler: handler.handle_request
    timeout: 30
    events:
      - http:                            # ← HTTP TRIGGER (PUSH)
          path: api/process
          method: post
          cors: true

resources:
  Resources:
    ProcessingQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}
        VisibilityTimeout: 300
```

---

### Event Flow Diagrams

#### S3 Push Model (S3 → Lambda)

```
File uploaded to S3
    ↓
S3 detects event
    ↓
S3 IMMEDIATELY invokes Lambda
    ↓
Lambda handler(event, context)
    │
    └─ event = {
         'Records': [{
           's3': {
             'bucket': {'name': 'data-bucket'},
             'object': {'key': 'uploads/data.csv'}
           }
         }]
       }
    ↓
Lambda processes file
    ↓
Done
```

#### SQS Poll Model (Lambda ← SQS)

```
Message sent to SQS
    ↓
Message waits in queue
    ↓
Event Source Mapping polls queue
    ↓
Up to 10 messages collected
    ↓
Lambda invoked with batch
    ↓
Lambda handler(event, context)
    │
    └─ event = {
         'Records': [{
           'body': '{"order_id": "123"}',
           'receiptHandle': 'xyz...'
         }]
       }
    ↓
Lambda processes messages
    ↓
Lambda returns success/failure
    ↓
Delete messages from queue
```

---

### Handler Code: S3 Event

```python
# handler.py - Process S3 upload

import json
import boto3
import logging

logger = logging.getLogger()
s3 = boto3.client('s3')

def process_s3_upload(event, context):
    """
    Triggered when file uploaded to S3

    S3 automatically invokes this function
    We don't poll S3 - S3 pushes to us!
    """

    # S3 sends event with bucket and key
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        logger.info(f"Processing S3 upload: s3://{bucket}/{key}")

        # Download file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()

        # Process the CSV file
        process_csv(file_content)

        logger.info(f"✓ Processed: {key}")

    return {'statusCode': 200, 'body': 'File processed'}


def process_csv(content):
    """Process CSV file"""
    lines = content.decode('utf-8').split('\n')
    print(f"Processing {len(lines)} rows")
    # Process each row
    for row in lines:
        # Do something with row
        pass
```

---

### Handler Code: SQS Event

```python
# handler.py - Process SQS messages

import json
import boto3
import logging

logger = logging.getLogger()
sqs = boto3.client('sqs')

def process_queue_messages(event, context):
    """
    Triggered by SQS queue messages

    Event Source Mapping continuously polls the queue
    We don't poll - Serverless does it for us!
    """

    # Event Source Mapping sends up to 10 messages
    for record in event['Records']:
        try:
            # Extract message from SQS wrapper
            message_body = json.loads(record['body'])
            message_id = record['messageId']

            logger.info(f"Processing SQS message: {message_id}")

            # Process the message
            process_order(message_body)

            logger.info(f"✓ Processed: {message_id}")

        except Exception as e:
            # Log error but continue with other messages
            logger.error(f"Error processing message: {e}")
            # Return failed message ID for requeue
            return {
                'batchItemFailures': [
                    {'itemId': record['messageId']}
                ]
            }

    # All messages processed successfully
    return {'batchItemFailures': []}


def process_order(order):
    """Process order message"""
    print(f"Order {order['order_id']} processing...")
    # Do something with order
    pass
```

---

### Key Differences in Handler Events

#### S3 Event Structure
```python
def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        # Process file
```

#### SQS Event Structure
```python
def handler(event, context):
    for record in event['Records']:
        message_id = record['messageId']
        receipt_handle = record['receiptHandle']
        body = json.loads(record['body'])
        # Process message
```

#### HTTP Event Structure
```python
def handler(event, context):
    body = json.loads(event.get('body', '{}'))
    path = event.get('path')
    method = event.get('httpMethod')
    # Process request
```

---

### Common Mistakes

#### Mistake 1: Thinking You Need to Poll SQS in Code

```python
# ❌ WRONG - Don't do this!
import time

def handler(event, context):
    while True:  # Infinite loop!
        messages = sqs.receive_message(...)
        for msg in messages:
            process(msg)
        time.sleep(1)  # Why are you polling?
```

**Why it's wrong:**
- Serverless already creates Event Source Mapping to poll
- Your code will never finish (Lambda has timeout!)
- You're duplicating AWS infrastructure

```python
# ✅ CORRECT - Let Serverless handle polling
def handler(event, context):
    # event already contains messages (pre-polled)
    for record in event['Records']:
        process(record)
    # Done! Handler returns
```

#### Mistake 2: Not Configuring S3 Trigger

```yaml
# ❌ WRONG - S3 upload won't trigger Lambda
functions:
  processFile:
    handler: handler.process
    # Missing events section!
```

```yaml
# ✅ CORRECT - S3 knows to trigger Lambda
functions:
  processFile:
    handler: handler.process
    events:
      - s3:
          bucket: my-bucket
          event: s3:ObjectCreated:*
```

#### Mistake 3: Wrong batchSize for Use Case

```yaml
# ❌ WRONG - batchSize=1 wastes Lambda invocations
events:
  - sqs:
      arn: !GetAtt Queue.Arn
      batchSize: 1  # One at a time!
```

**Cost impact:**
```
100 messages with batchSize=1:
- 100 Lambda invocations
- Cost: 100 × $0.0000002 = $0.00002

100 messages with batchSize=10:
- 10 Lambda invocations
- Cost: 10 × $0.0000002 = $0.000002

SAVINGS: 10x cheaper with batching!
```

---

### Summary: Where to Specify Events

| Event Type | Configuration Location | When Triggered | How |
|-----------|----------------------|-----------------|-----|
| **SQS** | `events: - sqs:` | When message arrives | Serverless polls queue |
| **S3** | `events: - s3:` | When file uploaded | S3 pushes event |
| **HTTP** | `events: - http:` | When request received | API Gateway receives |
| **Schedule** | `events: - schedule:` | On timer | CloudWatch triggers |
| **SNS** | `events: - sns:` | When message published | SNS pushes event |

---

### Best Practices Checklist

✅ **SQS: Specify in events section**
  - Don't write polling code yourself
  - Use appropriate `batchSize` (10 for most cases)
  - Handle `batchItemFailures` for partial failures

✅ **S3: Specify in events section**
  - Use `prefix` and `suffix` to filter files
  - Only trigger on specific file types
  - Handle timeouts for large files

✅ **All events**
  - Configure timeout appropriate to your work
  - Use `maximumBatchingWindowInSeconds` for better batching
  - Monitor Lambda execution in CloudWatch

✅ **Know the difference**
  - SQS = **Pull** (Lambda polls)
  - S3 = **Push** (S3 notifies)
  - HTTP = **Push** (Client requests)

---

### How SQS Messages Trigger Lambda: The Complete Flow

As a tutor, let me break down **exactly how** a message in the SQS queue triggers the Lambda function. This ties together Fn::GetAtt, Event Source Mapping, and Lambda invocation.

#### The Configuration

```yaml
resources:
  Resources:
    ProcessingQueue:           # ← Logical name in CloudFormation
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}  # ← Actual queue name
        VisibilityTimeout: 300

functions:
  notifyCompletion:
    handler: handler.notify_completion
    events:
      - sqs:
          arn:
            Fn::GetAtt:                 # ← How do we get the ARN?
              - ProcessingQueue         # ← Reference logical resource
              - Arn                     # ← Fetch its ARN attribute
          batchSize: 10
```

#### Step-by-Step Resolution

**Step 1: You Write in serverless.yml**
```yaml
Fn::GetAtt: [ProcessingQueue, Arn]
```

**Step 2: Serverless Deploys & CloudFormation Takes Over**
```
Serverless reads: "Get the Arn attribute of ProcessingQueue resource"
  ↓
CloudFormation creates the SQS queue:
  - Logical name: ProcessingQueue
  - Queue name: processing-queue-dev (after variable substitution)
  - AWS assigns: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
```

**Step 3: Fn::GetAtt Resolves**
```
Fn::GetAtt looks up: ProcessingQueue resource
  ↓
Gets its ARN attribute:
  arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
  ↓
Returns the full ARN
```

**Step 4: Event Source Mapping Created**
```
Serverless takes the ARN and creates an Event Source Mapping:
  Lambda: my-data-processor-dev-notifyCompletion
  SQS Queue ARN: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
  Batch Size: 10
  ↓
Mapping now lives in AWS (invisible but real!)
```

**Step 5: Message Arrives**
```
Producer sends message to queue:
  POST to sqs.us-east-1.amazonaws.com/123456789012/processing-queue-dev
  Message: {"order_id": "ORD-123", "customer": "John"}
  ↓
Message sits in queue waiting
```

**Step 6: Event Source Mapping Detects Message**
```
Event Source Mapping continuously polls:
  Every 1-2 seconds: "Any messages in
  arn:aws:sqs:us-east-1:123456789012:processing-queue-dev?"
  ↓
  YES! Found 1 message
  ↓
  Collects messages (up to batchSize: 10)
```

**Step 7: Lambda Invoked**
```
Event Source Mapping invokes Lambda with the message:
  Function: my-data-processor-dev-notifyCompletion
  Event: {
    "Records": [{
      "messageId": "msg-id-123",
      "receiptHandle": "handle-xyz",
      "body": "{\"order_id\": \"ORD-123\", \"customer\": \"John\"}"
    }]
  }
```

**Step 8: Lambda Processes & Returns**
```
Lambda handler processes the message
  ↓
Lambda returns success
  ↓
Event Source Mapping deletes message from queue
  ↓
Message is GONE from queue permanently
```

---

#### Visual Mapping Process

```
┌─────────────────────────────────────────────────────────────┐
│ DEPLOYMENT TIME (serverless deploy)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Step 1: serverless.yml contains:                           │
│   Fn::GetAtt: [ProcessingQueue, Arn]                       │
│                                                             │
│ Step 2: Serverless Framework processes it:                 │
│   "ProcessingQueue is a CloudFormation resource"           │
│   "Create it with: QueueName: processing-queue-dev"        │
│                                                             │
│ Step 3: CloudFormation creates queue:                      │
│   Name: processing-queue-dev                              │
│   ARN: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
│                                                             │
│ Step 4: Fn::GetAtt gets the ARN:                           │
│   Returns: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
│                                                             │
│ Step 5: Event Source Mapping created:                      │
│   Links Lambda to that specific ARN                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ RUNTIME (After deployment)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Step 6: Message arrives in queue:                          │
│   SQS Queue: processing-queue-dev (ARN: arn:aws:sqs:...)   │
│   Message: {order_id: 123}                                 │
│                                                             │
│ Step 7: Event Source Mapping detects it:                   │
│   "I'm monitoring arn:aws:sqs:...:processing-queue-dev"    │
│   "Found 1 message!"                                        │
│                                                             │
│ Step 8: Lambda invoked:                                    │
│   Function: my-data-processor-dev-notifyCompletion         │
│   Event contains message from that queue                   │
│                                                             │
│ Step 9: Lambda processes & deletes:                        │
│   Message deleted from queue                              │
│   Queue now empty                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### Real Values at Each Step

Let's trace through with actual values:

**serverless.yml:**
```yaml
service: my-data-processor
provider:
  stage: dev
  region: us-east-1

resources:
  Resources:
    ProcessingQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}

functions:
  notifyCompletion:
    events:
      - sqs:
          arn:
            Fn::GetAtt: [ProcessingQueue, Arn]
```

**After deployment:**
```
┌─────────────────────────────────────────────────────────┐
│ What Actually Gets Created in AWS                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. SQS Queue                                           │
│    Name: processing-queue-dev                         │
│    Full ARN: arn:aws:sqs:us-east-1:123456789012:      │
│             processing-queue-dev                      │
│                                                         │
│ 2. Lambda Function                                    │
│    Name: my-data-processor-dev-notifyCompletion       │
│    ARN: arn:aws:lambda:us-east-1:123456789012:        │
│          function:my-data-processor-dev-notifyCompletion
│                                                         │
│ 3. Event Source Mapping (The Connection)              │
│    Links Lambda to SQS:                               │
│    - Lambda: my-data-processor-dev-notifyCompletion   │
│    - Queue: arn:aws:sqs:us-east-1:123456789012:       │
│            processing-queue-dev                       │
│    - Batch Size: 10                                   │
│    - Status: ENABLED                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

#### How Fn::GetAtt Prevents Hardcoding

**Without Fn::GetAtt (❌ DON'T DO THIS):**

```yaml
functions:
  notifyCompletion:
    events:
      - sqs:
          arn: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
```

**Problems:**
- Account ID hardcoded (not portable)
- Region hardcoded (can't deploy to eu-west-1)
- Queue name hardcoded (breaks if queue renamed)
- Not infrastructure-as-code

**With Fn::GetAtt (✅ CORRECT):**

```yaml
functions:
  notifyCompletion:
    events:
      - sqs:
          arn: !GetAtt ProcessingQueue.Arn
```

**Benefits:**
- Account ID auto-filled (from current AWS account)
- Region auto-filled (from provider.region)
- Queue name auto-resolved (from logical resource reference)
- Always correct, always portable

---

#### Understanding the Event Structure

When a message arrives in `processing-queue-dev`, here's **exactly** what Lambda receives:

```python
def notify_completion(event, context):
    """
    Event structure when SQS triggers Lambda
    """

    # event = {
    #   "Records": [
    #     {
    #       "messageId": "12345",
    #       "receiptHandle": "xyz789==",
    #       "body": "{\"order_id\": \"123\"}",
    #       "attributes": {
    #         "ApproximateReceiveCount": "1",
    #         "SentTimestamp": "1622000000",
    #         "SequenceNumber": "1",
    #         "ApproximateFirstReceiveTimestamp": "1622000001"
    #       },
    #       "messageAttributes": {},
    #       "md5OfBody": "abc123def456",
    #       "eventSource": "aws:sqs",
    #       "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:processing-queue-dev",
    #       "awsRegion": "us-east-1"
    #     }
    #   ]
    # }

    for record in event['Records']:
        # Which queue did this come from?
        source_arn = record['eventSourceARN']
        # ↓
        # Result: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
        # (Same ARN from Fn::GetAtt!)

        # Get the actual message
        message_body = json.loads(record['body'])
        order_id = message_body['order_id']

        # Process the order
        process_order(order_id)

        # AWS automatically deletes after handler returns success
```

**Key insight:** The `eventSourceARN` in the Lambda event is the **exact same ARN** that Fn::GetAtt resolved to!

---

#### Multiple Queues to Same Lambda

You can trigger one Lambda from multiple queues:

```yaml
resources:
  Resources:
    OrderQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: orders-${self:provider.stage}

    NotificationQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: notifications-${self:provider.stage}

functions:
  processMessages:
    handler: handler.process
    events:
      # Trigger from Order Queue
      - sqs:
          arn: !GetAtt OrderQueue.Arn
          batchSize: 10

      # Also trigger from Notification Queue
      - sqs:
          arn: !GetAtt NotificationQueue.Arn
          batchSize: 5
```

**What happens:**
```
OrderQueue message arrives
  ↓
Event Source Mapping 1 detects
  ↓
Lambda invoked with OrderQueue ARN in eventSourceARN

NotificationQueue message arrives
  ↓
Event Source Mapping 2 detects
  ↓
Lambda invoked with NotificationQueue ARN in eventSourceARN

Handler code can check eventSourceARN to know which queue it came from:

def process(event, context):
    for record in event['Records']:
        source = record['eventSourceARN']

        if 'orders' in source:
            # From order queue
            process_order(record)
        elif 'notifications' in source:
            # From notification queue
            process_notification(record)
```

---

#### Troubleshooting: Queue Not Triggering Lambda

**Symptom:** Messages in queue but Lambda not invoked

**Checklist:**

```
1. ✅ Queue created?
   aws sqs list-queues | grep processing-queue-dev

2. ✅ Event Source Mapping created?
   aws lambda list-event-source-mappings \
     --function-name my-data-processor-dev-notifyCompletion
   Should show:
     - State: Enabled
     - EventSourceArn: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev

3. ✅ IAM permissions?
   Lambda needs permission to:
   - sqs:ReceiveMessage
   - sqs:DeleteMessage
   - sqs:GetQueueAttributes
   (Serverless adds these automatically)

4. ✅ Queue visible to Lambda?
   Lambda must be in VPC with queue access
   (usually not an issue for standard setup)

5. ✅ Lambda timeout sufficient?
   Default is 30s - increase if processing takes longer

6. ✅ Queue URL matches ARN?
   Queue URL: https://sqs.us-east-1.amazonaws.com/123456789012/processing-queue-dev
   Queue ARN: arn:aws:sqs:us-east-1:123456789012:processing-queue-dev
   Should match!
```

**Common issue:** Event Source Mapping created but **Disabled**
```bash
# Check status
aws lambda list-event-source-mappings \
  --function-name my-data-processor-dev-notifyCompletion \
  --query 'EventSourceMappings[0].State'

# If Disabled, enable it:
aws lambda update-event-source-mapping \
  --uuid <UUID-from-above> \
  --enabled
```

---

### How Lambda Signals Success/Failure to SQS

As a tutor, understanding **how Lambda communicates to the Event Source Mapping whether a message was processed successfully** is critical. This determines whether the message gets deleted or retried.

#### The Simple Rule

**Lambda signals success by:**
- Handler completes without throwing an exception
- Handler returns any value (doesn't matter what)

**Lambda signals failure by:**
- Handler throws an exception
- Handler times out
- Handler crashes

---

#### Success Scenario: Handler Completes Normally

```python
def notify_completion(event, context):
    """Handler completes successfully"""

    for record in event['Records']:
        message = json.loads(record['body'])

        # Process the message
        logger.info(f"Processing order: {message['order_id']}")
        send_email(message['customer_email'])
        logger.info(f"✓ Email sent")

    # Handler returns (no exception)
    return {
        'statusCode': 200,
        'body': 'Notifications sent'
    }

# What happens:
# 1. Handler executes successfully
# 2. Returns value (AWS ignores the actual return value)
# 3. Event Source Mapping sees: SUCCESS
# 4. Messages DELETED from SQS queue
# 5. Done!
```

**Timeline:**
```
10:00:00 AM
  Message in queue: {order_id: 123}
  ↓
  Event Source Mapping invokes Lambda
  ↓
10:00:01 AM
  Lambda handler processes
  send_email(email)
  logger.info("✓ Email sent")
  ↓
  Handler returns (no exception)
  ↓
10:00:02 AM
  Event Source Mapping: "Handler succeeded!"
  ↓
  Message DELETED from queue
  ↓
  Queue is now empty
  ✅ SUCCESS
```

---

#### Failure Scenario 1: Exception in Handler

```python
def notify_completion(event, context):
    """Handler throws exception"""

    for record in event['Records']:
        message = json.loads(record['body'])

        try:
            # This fails!
            send_email(message['customer_email'])
        except EmailServiceDown as e:
            # Exception is thrown
            logger.error(f"✗ Email service failed: {e}")
            raise e  # ← Propagate the exception

    # Handler never reaches here

# What happens:
# 1. Handler execution
# 2. Exception thrown: EmailServiceDown
# 3. Event Source Mapping sees: FAILURE
# 4. Message STAYS in queue
# 5. After visibility timeout (300s), message reappears
# 6. Event Source Mapping retries
```

**Timeline:**
```
10:00:00 AM
  Message in queue: {order_id: 123}
  ↓
  Event Source Mapping invokes Lambda
  ↓
10:00:01 AM
  Lambda handler processes
  send_email(email)
  ↓
  EMAIL SERVICE DOWN! ❌
  Exception raised: EmailServiceDown
  ↓
10:00:02 AM
  Event Source Mapping: "Handler failed!"
  ↓
  Message NOT deleted from queue
  ↓
  Message becomes hidden (visibility timeout = 300s)
  ↓
10:05:02 AM (300 seconds later)
  Visibility timeout expires
  ↓
  Message reappears in queue
  ↓
  Event Source Mapping retries
  ↓
10:05:03 AM
  Lambda invoked again (Attempt 2)
  ↓
  If email service back up: ✅ Succeeds
  If email service still down: ❌ Fails again
  ↓
  Cycle repeats until success
```

---

#### Failure Scenario 2: Unhandled Exception

```python
def notify_completion(event, context):
    """Unhandled exception"""

    for record in event['Records']:
        message = json.loads(record['body'])
        order_id = message['order_id']

        # Bug: Forgot to check if email exists
        email = message['email']  # KeyError if 'email' missing!
        send_email(email)

# If message doesn't have 'email' key:
# 1. KeyError raised
# 2. Exception not caught
# 3. Handler crashes
# 4. Event Source Mapping sees: FAILURE
# 5. Message stays in queue
# 6. Retried after visibility timeout

# Result: Message retried forever with same error!
```

**How to fix:**
```python
def notify_completion(event, context):
    """Proper error handling"""

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            email = message.get('email')  # ← Check if exists

            if not email:
                logger.warning(f"No email found, skipping")
                continue  # Skip to next message

            send_email(email)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Don't re-raise - handler continues
            # This message fails silently
            # But next message in batch is still processed

    # Handler returns successfully (even if some failed)
    return {'statusCode': 200}
```

---

#### Batch Processing: Partial Failures

When processing multiple messages, one failure doesn't have to fail the whole batch:

```python
def process_orders(event, context):
    """Process batch - handle partial failures"""

    failed_messages = []

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            order_id = message['order_id']

            # Process order
            process_payment(order_id)
            update_inventory(order_id)
            send_confirmation(order_id)

            logger.info(f"✓ Order {order_id} processed")

        except PaymentFailedError as e:
            # This order failed - mark it
            logger.error(f"✗ Order {order_id} payment failed: {e}")
            failed_messages.append({'itemId': record['messageId']})

        except Exception as e:
            # Unexpected error
            logger.error(f"✗ Order {order_id} error: {e}")
            failed_messages.append({'itemId': record['messageId']})

    # Return which messages failed
    return {
        'batchItemFailures': failed_messages
    }

# What happens:
# Batch of 3 orders arrives:
#   Order 1: Processes ✓ (deleted)
#   Order 2: Payment fails ✗ (stays in queue)
#   Order 3: Processes ✓ (deleted)
#
# Result:
#   2 messages deleted
#   1 message stays for retry
#   No wasted work retrying successful orders!
```

---

#### Configuration: ReportBatchItemFailures

To enable per-message failure handling, use:

```yaml
functions:
  processOrders:
    handler: handler.process_orders
    events:
      - sqs:
          arn: !GetAtt OrderQueue.Arn
          batchSize: 10
          functionResponseType: ReportBatchItemFailures
```

**What this does:**
- Allows Lambda to report which messages failed
- Successful messages deleted immediately
- Failed messages stay in queue for retry
- Much better than all-or-nothing failure

**Without `ReportBatchItemFailures`:**
```
Batch of 3 messages:
  Message 1: ✓ Success
  Message 2: ✗ Failure
  Message 3: ✓ Success

Result:
  ❌ ENTIRE batch marked as FAILED
  ALL 3 messages stay in queue
  Wasted work retrying 1 and 3!
```

**With `ReportBatchItemFailures`:**
```
Batch of 3 messages:
  Message 1: ✓ Success → DELETED
  Message 2: ✗ Failure → STAYS for retry
  Message 3: ✓ Success → DELETED

Result:
  ✅ 2 messages cleaned up
  Only 1 message retried
  Efficient!
```

---

#### How AWS Knows Success/Failure (The Details)

**Behind the scenes:**

```
┌─────────────────────────────────────────────────────────────┐
│ Lambda Execution                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. Handler starts                                          │
│    ↓                                                        │
│ 2. Handler logic executes                                  │
│    ↓                                                        │
│ 3a. NO EXCEPTION                                           │
│     Handler returns normally                               │
│     Lambda runtime → EXIT CODE 0 (Success)                 │
│                                                             │
│ 3b. EXCEPTION THROWN                                       │
│     Handler crashes                                        │
│     Lambda runtime → EXIT CODE 1 (Failure)                 │
│                                                             │
│ 3c. TIMEOUT                                                │
│     Handler takes >300 seconds                             │
│     Lambda runtime → KILL PROCESS (Failure)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Event Source Mapping Checks Result                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ EXIT CODE 0? → SUCCESS                                     │
│   Delete messages from queue                              │
│                                                             │
│ EXIT CODE 1? → FAILURE                                     │
│   Messages stay in queue                                  │
│   Schedule retry after visibility timeout                 │
│                                                             │
│ TIMEOUT? → FAILURE                                         │
│   Messages stay in queue                                  │
│   Schedule retry after visibility timeout                 │
│                                                             │
│ REPORTS FAILED ITEMS? → PARTIAL FAILURE                    │
│   Delete successful messages                              │
│   Keep failed messages for retry                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### Monitoring Success/Failure in CloudWatch

```bash
# View Lambda logs to see what happened
serverless logs -f processOrders --tail

# Output:
# START RequestId: abc-123-xyz
# 2024-01-15 10:00:01 Processing order: ORD-123
# 2024-01-15 10:00:02 ✓ Order processed
# 2024-01-15 10:00:03 Processing order: ORD-124
# 2024-01-15 10:00:04 ✗ Payment failed
# 2024-01-15 10:00:05 Processing order: ORD-125
# 2024-01-15 10:00:06 ✓ Order processed
# END RequestId: abc-123-xyz
# REPORT Duration: 6ms
# Batchitemfailures: 1

# Check if messages still in queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/order-queue \
  --attribute-names ApproximateNumberOfMessages

# Output:
# {
#   "Attributes": {
#     "ApproximateNumberOfMessages": "1"
#   }
# }
# → 1 message still in queue (the one that failed)
```

---

#### Dead Letter Queue (DLQ) for Permanently Failed Messages

When a message fails repeatedly, send it to a Dead Letter Queue:

```yaml
resources:
  Resources:
    OrderQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: order-queue-${self:provider.stage}
        VisibilityTimeout: 300
        RedrivePolicy:
          deadLetterTargetArn: !GetAtt OrderDLQ.Arn
          maxReceiveCount: 3  # After 3 failures → DLQ

    OrderDLQ:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: order-queue-dlq-${self:provider.stage}
        MessageRetentionPeriod: 1209600  # 14 days for investigation
```

**Flow:**
```
Message arrives in order-queue
  ↓
Attempt 1: Fails → Back to queue
Attempt 2: Fails → Back to queue
Attempt 3: Fails → Back to queue
Attempt 4: Fails → MOVED TO DLQ
  ↓
DLQ keeps message for 14 days
  ↓
Operator can investigate:
  "Why did this order fail 3 times?"
  "Do we need to fix it manually?"
```

---

#### Complete Example: Proper Error Handling

```python
import json
import boto3
import logging

sqs = boto3.client('sqs')
logger = logging.getLogger()

def process_orders(event, context):
    """
    Process orders with proper error handling
    Signals success/failure correctly to SQS
    """

    failed_messages = []

    for record in event['Records']:
        message_id = record['messageId']

        try:
            # Extract order
            order = json.loads(record['body'])
            order_id = order['order_id']

            logger.info(f"Processing order: {order_id}")

            # Step 1: Validate
            if not validate_order(order):
                logger.warning(f"Invalid order format: {order_id}")
                # Invalid data - delete it (don't retry forever)
                continue

            # Step 2: Process
            payment_result = charge_card(order['card_token'], order['amount'])
            update_inventory(order['items'])
            send_confirmation_email(order['customer_email'])

            logger.info(f"✓ Order {order_id} processed successfully")

        except PaymentDeclinedError as e:
            # Temporary failure - retry later
            logger.error(f"Payment declined for {order_id}: {e}")
            failed_messages.append({'itemId': message_id})

        except NetworkError as e:
            # Temporary failure - retry later
            logger.error(f"Network error for {order_id}: {e}")
            failed_messages.append({'itemId': message_id})

        except ValueError as e:
            # Invalid data - delete and skip
            logger.error(f"Bad data for {order_id}: {e}")
            # Don't add to failed_messages - will be deleted

        except Exception as e:
            # Unexpected error - retry
            logger.exception(f"Unexpected error for {order_id}: {e}")
            failed_messages.append({'itemId': message_id})

    # Report which messages failed
    return {
        'batchItemFailures': failed_messages
    }

def validate_order(order):
    """Return False for invalid orders"""
    required_fields = ['order_id', 'customer_email', 'amount', 'items']
    return all(field in order for field in required_fields)

def charge_card(token, amount):
    """Return payment result"""
    # Simulate payment processing
    return {'success': True, 'transaction_id': 'txn-123'}

def update_inventory(items):
    """Update stock"""
    pass

def send_confirmation_email(email):
    """Send confirmation"""
    pass
```

---

#### Summary: How Lambda Signals Success

| Scenario | Lambda Action | Result | Queue |
|----------|---------------|--------|-------|
| **Handler completes, no exception** | Returns normally (exit code 0) | ✅ SUCCESS | Message DELETED |
| **Handler throws exception** | Exception raised (exit code 1) | ❌ FAILURE | Message STAYS (retry later) |
| **Handler timeout** | Takes >timeout seconds | ❌ FAILURE | Message STAYS (retry later) |
| **Partial failure reported** | Returns `{'batchItemFailures': [...]}` | ⚠️ MIXED | Successful DELETED, failed STAY |
| **Invalid data, delete intentionally** | Return normally without adding to failed list | ✅ SUCCESS | Message DELETED |

---

## Do You Need AWS Console?

### Deployment Tasks (No Console Needed)

| Task | Console Needed? | How to Do It |
|------|-----------------|-------------|
| **Deploy** | ❌ NO | `serverless deploy` |
| **Deploy specific function** | ❌ NO | `serverless deploy function -f myFunction` |
| **Invoke function** | ❌ NO | `serverless invoke -f myFunction` |
| **View logs** | ❌ NO | `serverless logs -f myFunction --tail` |
| **Update code** | ❌ NO | `serverless deploy function -f myFunction` |
| **Delete stack** | ❌ NO | `serverless remove` |
| **Get function info** | ❌ NO | `serverless info` |

### Monitoring Tasks (Console Optional but Helpful)

| Task | Console Needed? | How to Do It |
|------|-----------------|-------------|
| **Monitor metrics** | ✅ YES (helpful) | AWS CloudWatch console |
| **View X-Ray traces** | ✅ YES (helpful) | AWS X-Ray console |
| **Set up alarms** | ❌ NO (optional) | Serverless dashboard or AWS console |
| **View error details** | ❌ NO | `serverless logs -f myFunction` |
| **Troubleshoot issues** | ✅ YES (helpful) | AWS CloudWatch Logs console |

---

## Common Serverless Deploy Commands

### Deployment

```bash
# Deploy everything to dev
serverless deploy

# Deploy to specific stage
serverless deploy --stage production

# Deploy to specific region
serverless deploy --region eu-west-1

# Deploy specific function only (faster)
serverless deploy function -f processData

# Deploy with verbose output
serverless deploy --verbose

# Dry run - see what would happen without deploying
serverless deploy --noDeploy

# Deploy with different AWS profile
serverless deploy --aws-profile production

# Deploy with custom variables
serverless deploy --param="key=value"
```

### Invocation and Testing

```bash
# Invoke function locally (for testing)
serverless invoke local -f processData -d '{"test": "data"}'

# Invoke function in AWS
serverless invoke -f processData -d '{"test": "data"}'

# Invoke with JSON file
serverless invoke -f processData --path event.json

# Invoke and get response
serverless invoke -f processData --log
```

### Logs and Monitoring

```bash
# View logs from past 1 hour
serverless logs -f processData

# Tail logs in real-time
serverless logs -f processData --tail

# View logs with filter
serverless logs -f processData --filter "ERROR"

# View logs from past 30 minutes
serverless logs -f processData --startTime 30m
```

### Information and Cleanup

```bash
# Get function information
serverless info

# Get all functions
serverless info --verbose

# Remove entire stack (DELETE ALL RESOURCES)
serverless remove

# Remove with confirmation
serverless remove --stage prod
```

---

## Real-World CI/CD Example

### GitHub Actions Deployment

Deploy automatically when code is pushed to main branch - no console login needed!

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Serverless
        run: npm install -g serverless

      - name: Install dependencies
        run: npm install --save-dev serverless-python-requirements

      - name: Deploy to AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            serverless deploy --stage prod
          else
            serverless deploy --stage dev
          fi

      - name: Get deployment info
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
        run: serverless info --stage prod
```

**How it works:**
1. Push code to main branch
2. GitHub Actions automatically triggers
3. Serverless deploys using credentials from GitHub Secrets
4. Deployment completes without any console interaction
5. Get deployment info and verify success

### GitLab CI/CD Deployment

```yaml
# .gitlab-ci.yml
stages:
  - deploy

deploy_production:
  stage: deploy
  image: node:18

  before_script:
    - npm install -g serverless
    - npm install --save-dev serverless-python-requirements
    - apt-get update && apt-get install -y python3-pip

  script:
    - serverless deploy --stage prod

  environment:
    name: production

  only:
    - main

  variables:
    AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
    AWS_REGION: us-east-1
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        AWS_ACCESS_KEY_ID = credentials('aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = credentials('aws_secret_access_key')
        AWS_REGION = 'us-east-1'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    npm install -g serverless
                    npm install --save-dev serverless-python-requirements
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh 'serverless deploy --stage prod'
            }
        }

        stage('Verify') {
            steps {
                sh 'serverless info --stage prod'
            }
        }
    }
}
```

---

## AWS Credentials: Best Practices

### ✅ DO: Recommended Practices

```bash
# 1. Create IAM user with minimal permissions
aws iam create-user --user-name serverless-deployer

# 2. Create programmatic access key
aws iam create-access-key --user-name serverless-deployer

# 3. Attach minimal policy (CloudFormation + Lambda + S3)
aws iam put-user-policy \
    --user-name serverless-deployer \
    --policy-name ServerlessDeployPolicy \
    --policy-document file://policy.json
```

**Minimal IAM Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "s3:*",
        "apigateway:*",
        "logs:*",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:DeleteRole",
        "iam:DeleteRolePolicy",
        "events:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### ❌ DON'T: Never Do This

```bash
# ❌ Never hardcode credentials in code
serverless deploy \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG

# ❌ Never commit credentials to git
git add .env  # BAD: Contains secrets

# ❌ Never add credentials to serverless.yml
provider:
  credentials:
    accessKeyId: AKIAIOSFODNN7EXAMPLE
    secretAccessKey: wJalrXUtnFEMI/K7MDENG

# ❌ Never use root AWS account credentials
# ❌ Never share credentials via Slack/email
# ❌ Never leave credentials in history
```

### Secure Credential Management

```python
# Use AWS Secrets Manager for storing credentials
import boto3
import json

def get_serverless_credentials():
    """Retrieve Serverless deployment credentials from Secrets Manager"""
    secrets = boto3.client('secretsmanager')

    response = secrets.get_secret_value(
        SecretId='serverless/deployment-credentials'
    )

    creds = json.loads(response['SecretString'])

    return creds['access_key_id'], creds['secret_access_key']
```

---

## Troubleshooting Deployment

### "Unable to assume role" or "No credentials found"

**Error:**
```
Error: AWS credentials not configured. Unable to deploy.
```

**Solution:**
```bash
# Check if credentials are configured
aws sts get-caller-identity

# If error, configure credentials
aws configure

# Verify credentials file exists
cat ~/.aws/credentials

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### "Permission denied" during deploy

**Error:**
```
An error occurred (AccessDenied) when calling the CreateRole operation
```

**Solution:**
```bash
# Check IAM user permissions
aws iam get-user-policy \
    --user-name serverless-deployer \
    --policy-name ServerlessDeployPolicy

# Add missing permissions to policy
aws iam put-user-policy \
    --user-name serverless-deployer \
    --policy-name ServerlessDeployPolicy \
    --policy-document file://updated-policy.json

# Try deployment again
serverless deploy --stage prod
```

### "CloudFormation stack already exists"

**Error:**
```
Stack with id my-data-processor-dev already exists
```

**Solution:**
```bash
# This is normal - just update the existing stack
serverless deploy --stage dev

# Or if you want fresh start
serverless remove --stage dev
serverless deploy --stage dev

# Or just update specific function
serverless deploy function -f processData --stage dev
```

### "Timeout during deployment"

**Error:**
```
Deployment timed out
```

**Solution:**
```bash
# Increase timeout (default is 120 seconds)
serverless deploy --verbose

# Check CloudFormation directly
aws cloudformation describe-stacks \
    --stack-name my-data-processor-dev

# Check CloudWatch logs for Lambda errors
serverless logs -f processData
```

### "Package size too large"

**Error:**
```
An error occurred (CodeSizeTooLarge) when calling the CreateFunction
```

**Solution:**
```bash
# Use serverless-python-requirements plugin to exclude dependencies
# In serverless.yml:
package:
  individually: true
  patterns:
    - '!node_modules/**'
    - '!.git/**'
    - '!__pycache__/**'
    - '!.pytest_cache/**'

# Use Lambda Layers for large dependencies
# Or compress code better
npm install --save-dev serverless-plugin-optimize
```

### Debugging Commands

```bash
# See detailed deployment logs
serverless deploy --verbose

# Check CloudFormation events
aws cloudformation describe-stack-events \
    --stack-name my-data-processor-dev \
    --query 'StackEvents[0:10]'

# Check Lambda function
aws lambda get-function --function-name my-data-processor-dev-processData

# Check IAM role
aws iam get-role --role-name my-data-processor-dev-iam-role

# View recent errors
aws logs tail /aws/lambda/my-data-processor-dev-processData --follow
```

---

## Quick Start (5 Minutes)

### Step 1: Install Tools

```bash
# Install Node.js (if not already installed)
node --version

# Install Serverless Framework
npm install -g serverless
serverless --version
```

### Step 2: Configure AWS Credentials (One Time)

```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [your access key]
# AWS Secret Access Key: [your secret key]
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 3: Create Project Structure

```bash
# Create project directory
mkdir my-serverless-app
cd my-serverless-app

# Initialize
npm init -y

# Create files:
# serverless.yml (from template above)
# handler.py (from template above)
# requirements.txt
```

### Step 4: Deploy

```bash
# Install Serverless plugins
npm install --save-dev serverless-python-requirements

# Deploy to AWS
serverless deploy

# You should see:
# Deploying my-serverless-app to stage dev (us-east-1)
# Packaging lambda functions...
# Creating CloudFormation stack...
# ...
# Service deployed successfully.
# Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/process
```

### Step 5: Test and Monitor

```bash
# Invoke function
serverless invoke -f processData -d '{"test": "data"}'

# View logs
serverless logs -f processData --tail

# Get info
serverless info

# Clean up when done
serverless remove
```

---

## Summary Table

| Feature | Serverless | AWS Console |
|---------|-----------|-------------|
| **Deploy** | ✅ CLI only | ❌ Manual clicking |
| **Speed** | ✅ Fast (automated) | ❌ Slow (manual steps) |
| **Repeatable** | ✅ Same result every time | ❌ Error-prone |
| **CI/CD** | ✅ Perfect fit | ❌ Difficult |
| **Monitoring** | ⚠️ Basic (logs) | ✅ Full dashboard |
| **Cost** | ✅ Pay-per-use | ✅ Pay-per-use |
| **Learning curve** | ⚠️ Moderate | ⚠️ Steep |

---

## Key Takeaways

✅ **No console login needed** - Serverless is completely CLI-based
✅ **Authenticate once** - Configure credentials locally or use environment variables
✅ **Deploy with one command** - `serverless deploy`
✅ **Works in CI/CD** - Perfect for GitHub Actions, GitLab CI, Jenkins
✅ **Monitor without console** - Use `serverless logs` for real-time viewing
✅ **Repeatable deployments** - Same result every time
✅ **Least privilege** - Use minimal IAM permissions for security
✅ **Instant updates** - Redeploy changed functions quickly

---

## Next Steps

1. **Install Serverless**: `npm install -g serverless`
2. **Configure AWS**: `aws configure`
3. **Create project**: Use template from this guide
4. **Deploy**: `serverless deploy`
5. **Monitor**: `serverless logs -f myFunction --tail`
6. **Iterate**: Update code and redeploy

**You're ready to deploy serverless applications without touching the AWS console!** 🚀

