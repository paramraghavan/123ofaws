# SNS vs SQS: Comprehensive Tutoring Guide

> **Learn when and how to use AWS SNS (Simple Notification Service) and SQS (Simple Queue Service)**, including practical examples and the powerful SNS + SQS combined pattern.

---

## Table of Contents

1. [Quick Comparison](#quick-comparison)
2. [AWS Limits & Constraints](#aws-limits--constraints)
3. [SNS: The Publisher](#sns-the-publisher)
4. [SQS: The Queue](#sqs-the-queue)
5. [Processing & Deleting SQS Messages](#processing--deleting-sqs-messages)
6. [SNS + SQS: The Power Couple](#sns--sqs-the-power-couple)
7. [Real-World Use Cases](#real-world-use-cases)
8. [Code Examples](#code-examples)
9. [Decision Tree](#decision-tree)
10. [Architecture Patterns](#architecture-patterns)

---

## Quick Comparison

### Side-by-Side Comparison

| Feature | SNS | SQS |
|---------|-----|-----|
| **Architecture** | Push | Pull |
| **Pattern** | Publish/Subscribe | Queue |
| **Message Delivery** | Immediate broadcast | Stored until retrieved |
| **Subscribers** | Many (all notified) | One consumer per message |
| **Polling** | Not required | Required |
| **Message Retention** | Not stored | Up to 14 days |
| **Use Case** | Fan-out, notifications | Decoupling, buffering |
| **Subscribers Know** | Topic name | Queue URL |
| **Best For** | One message → Many recipients | One message → One consumer |

---

## AWS Limits & Constraints

As a tutor, it's important to understand the limits of AWS services. Here are the key constraints you'll encounter:

### Message Size Limits

#### SNS Message Size

| Aspect | Limit | Details |
|--------|-------|---------|
| **Maximum message size** | 256 KB | 262,144 bytes including all metadata |
| **Message attributes** | Not counted in size limit | Custom metadata attributes are separate |
| **Format** | JSON, plaintext, XML, binary | Any format supported |

**What happens if you exceed 256 KB?**
```python
# This will FAIL ❌
large_message = "x" * 300000  # 300 KB

sns.publish(
    TopicArn=topic_arn,
    Message=large_message  # Error: Message size exceeds maximum
)
```

#### SQS Message Size

| Aspect | Limit | Details |
|--------|-------|---------|
| **Standard queues** | 256 KB | 262,144 bytes per message |
| **FIFO queues** | 256 KB | Same limit as standard queues |
| **Message attributes** | Not counted in size limit | Custom metadata is separate |

**What happens if you exceed 256 KB?**
```python
# This will FAIL ❌
large_message = "x" * 300000  # 300 KB

sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=large_message  # Error: Message body cannot exceed 256KB
)
```

### How to Handle Large Messages

#### Solution 1: Store in S3, Send Reference (Recommended)

```python
import boto3
import json
import uuid

s3 = boto3.client('s3')
sns = boto3.client('sns')

# Large data to process
large_data = {
    'file': "x" * 1000000,  # 1 MB of data
    'metadata': {'type': 'report'}
}

# Step 1: Upload large data to S3
bucket = 'my-data-bucket'
s3_key = f'messages/{uuid.uuid4()}.json'

s3.put_object(
    Bucket=bucket,
    Key=s3_key,
    Body=json.dumps(large_data)
)

# Step 2: Send REFERENCE to SNS (just the S3 location)
small_message = {
    's3_bucket': bucket,
    's3_key': s3_key,
    'message_type': 'large_data_available'
}

sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(small_message)  # Only 150 bytes!
)

# Step 3: Subscriber receives reference and fetches from S3
def process_message(event):
    message = json.loads(event['Records'][0]['Sns']['Message'])

    # Fetch the actual data from S3
    response = s3.get_object(
        Bucket=message['s3_bucket'],
        Key=message['s3_key']
    )
    large_data = json.loads(response['Body'].read())

    # Process the large data
    return process(large_data)
```

#### Solution 2: Compression

```python
import json
import gzip
import base64

# Compress message
large_message = {"data": "x" * 100000}
compressed = gzip.compress(json.dumps(large_message).encode())
encoded = base64.b64encode(compressed).decode()

# Send compressed message (much smaller)
sns.publish(
    TopicArn=topic_arn,
    Message=encoded,
    MessageAttributes={
        'compression': {'DataType': 'String', 'StringValue': 'gzip'}
    }
)

# Subscriber decompresses
def process_message(event):
    encoded_msg = event['Records'][0]['Sns']['Message']
    compressed = base64.b64decode(encoded_msg)
    large_message = json.loads(gzip.decompress(compressed))
    return process(large_message)
```

---

### Queue Size Limits

#### SQS Queue Size

| Aspect | Limit | Details |
|--------|-------|---------|
| **Maximum messages in queue** | ✅ **UNLIMITED** | No limit on total queue depth |
| **Maximum queue retention** | 14 days | After 14 days, message is automatically deleted |
| **Minimum retention** | 1 minute | You can set custom retention period |
| **Messages per batch receive** | 10 messages max | One receive_message call gets max 10 messages |

**Important**: Unlike traditional queues, SQS has **NO SIZE LIMIT**. You can store millions of messages!

```python
# This is FINE ✅ - No matter how many messages
sqs = boto3.client('sqs')

# Queue can hold unlimited messages
for i in range(1000000):
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({'order_id': i})
    )

# Queue happily holds all 1 million messages
# Limited only by storage, not by AWS limits
```

#### SNS Topic Limits

| Aspect | Limit | Details |
|--------|-------|---------|
| **Messages per second** | High (auto-scales) | SNS scales automatically |
| **Topic size** | No practical limit | Topics don't store messages (they're pushed) |
| **Subscribers per topic** | 12.5 million theoretical | Practical limit is much lower (~millions) |
| **Subscriptions per account** | 100 million | Per AWS account |

**Key difference**: SNS topics don't "store" messages like SQS queues do. Messages are **pushed immediately** to subscribers.

---

### Message Retention & Visibility

#### SQS Message Retention

```python
# When creating a queue
sqs.create_queue(
    QueueName='my-queue',
    Attributes={
        'MessageRetentionPeriod': '86400'  # 1 day (default is 4 days)
    }
)

# Valid values:
# 60 seconds to 1,209,600 seconds (14 days)
```

| Retention Period | Use Case |
|-----------------|----------|
| 60 seconds | Real-time processing, fast consumers |
| 5 minutes | Hot cache, immediate processing |
| 1 hour | Typical processing windows |
| 1 day | Overnight batch processing |
| 7 days | Weekly batch jobs |
| 14 days | Monthly audits, backups |

**What happens after retention expires?**
```
┌─────────────────────────────────┐
│ Message arrives in queue        │
│ Timestamp: 12:00 PM             │
└─────────────────────────────────┘
         ↓
      (4 days later)
         ↓
┌─────────────────────────────────┐
│ 4:00 PM on Day 4                │
│ Message is automatically deleted │
│ GONE FOREVER                    │
└─────────────────────────────────┘
```

#### SQS Visibility Timeout

```python
# When consuming messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    VisibilityTimeout=300  # 5 minutes (default is 30 seconds)
)

# What this means:
# - Message is temporarily hidden from other consumers
# - If consumer crashes, message reappears after 300 seconds
# - Consumer has 300 seconds to process and delete
```

**Common VisibilityTimeout Values:**

| Value | Use Case |
|-------|----------|
| 30 seconds | Simple operations, fast processing |
| 5 minutes | Database writes, API calls |
| 15 minutes | Image processing, file uploads |
| 1 hour | Complex batch jobs |
| 12 hours | Long-running processes |

**Visual Example:**
```
Time: 0s
Consumer A receives message
Message becomes invisible to Consumer B
    ↓
Time: 5m (Message processing taking long)
Consumer A still processing...
Message still hidden from Consumer B
    ↓
Time: 10m (Consumer A crashes)
Consumer A went down, but message unprocessed
    ↓
Time: 5m 1s (Visibility timeout expired)
Message reappears in queue for Consumer B to process
```

---

### SQS Long Polling vs Short Polling

#### Short Polling (Default)

```python
# Short polling - returns immediately even if no messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    WaitTimeSeconds=0  # Return immediately
)

# Returns in <100ms regardless of queue status
# Hammers AWS API with many requests
# More expensive! (charged per request)
```

#### Long Polling (Recommended)

```python
# Long polling - waits up to 20 seconds for messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    WaitTimeSeconds=20  # Wait up to 20 seconds
)

# Waits up to 20 seconds for a message
# Returns as soon as message arrives
# Much fewer API calls (cheaper!)
# Reduces latency
```

**Comparison:**

| Aspect | Short Polling | Long Polling |
|--------|---------------|--------------|
| **Response time** | Immediate | Up to 20 seconds |
| **API calls** | High (expensive) | Low (cheaper) |
| **Best for** | Real-time only | Most use cases |
| **CPU usage** | Higher | Lower |
| **Cost** | Higher | Lower |

**Cost Example:**
```
Processing 1000 messages over 1 minute

Short Polling:
  - 100 API calls per second (checking every 10ms)
  - = 6,000 API calls per minute
  - Cost: 6,000 requests × $0.40 per million = $0.0024/minute

Long Polling:
  - 1 API call per message
  - = ~16 API calls per minute (1000 messages ÷ 60 seconds)
  - Cost: 16 requests × $0.40 per million = negligible

SAVINGS: 6,000 vs 16 API calls = 375x fewer requests!
```

**Best practice:**
```python
# Always use long polling (AWS recommended)
sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20  # ← Use this!
)
```

---

### Other Important Limits

#### Throughput Limits (Standard SQS)

| Metric | Limit | Details |
|--------|-------|---------|
| **Receive messages per second** | Unlimited | Auto-scales |
| **Send messages per second** | Unlimited | Auto-scales |
| **Batch send** | 10 messages max | Per send_message_batch call |
| **Batch delete** | 10 messages max | Per delete_message_batch call |

#### FIFO Queue Limits (Different from Standard)

| Metric | Limit | Details |
|--------|-------|---------|
| **Throughput** | 300 msg/sec | With batching: 3,000 msg/sec |
| **Message deduplication** | 5 minutes | Dedup ID window |
| **Content-based deduplication** | Optional | Based on message body hash |

---

### Practical Limits Checklist

**Before designing your system:**

```
✅ Message size: Max 256 KB per message
   → For larger: Use S3 reference pattern

✅ Queue size: Unlimited messages allowed
   → Designed to handle millions of messages

✅ Message retention: 1 minute to 14 days
   → Choose based on your retry strategy

✅ Visibility timeout: 0 seconds to 12 hours
   → Match your processing time

✅ Throughput: Auto-scales (unlimited)
   → No pre-provisioning needed

✅ Long polling: Always enable (WaitTimeSeconds=20)
   → Saves API calls and costs

✅ Batch operations: Max 10 messages per batch
   → Use for bulk send/delete

✅ SNS subscribers: Millions possible
   → But each subscriber needs to handle load
```

---

### Real-World Scenario: Handling Large Orders

```python
"""
Scenario: Handling large order data (500 KB) in SQS

Problem: Message is larger than 256 KB limit
Solution: Store in S3, send reference
"""

import json
import boto3
import uuid

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def send_large_order(order_data):
    """Send large order to SQS following best practices"""

    # Step 1: Store large order data in S3
    s3_key = f"orders/{uuid.uuid4()}.json"
    s3.put_object(
        Bucket='order-data-bucket',
        Key=s3_key,
        Body=json.dumps(order_data)
    )

    # Step 2: Send REFERENCE in SQS (small message)
    message = {
        'order_id': order_data['id'],
        's3_bucket': 'order-data-bucket',
        's3_key': s3_key,
        'timestamp': '2024-01-15T10:30:00Z'
    }

    sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/orders',
        MessageBody=json.dumps(message),
        MessageAttributes={
            'data_location': {
                'StringValue': 's3',
                'DataType': 'String'
            }
        }
    )
    print(f"Order reference sent: {s3_key}")

def process_order(sqs_message):
    """Process order by fetching from S3"""

    message = json.loads(sqs_message['Body'])

    # Fetch the actual order data from S3
    response = s3.get_object(
        Bucket=message['s3_bucket'],
        Key=message['s3_key']
    )
    order_data = json.loads(response['Body'].read())

    # Process the order
    print(f"Processing order: {order_data['id']}")

    # After processing, delete from S3 (optional cleanup)
    s3.delete_object(
        Bucket=message['s3_bucket'],
        Key=message['s3_key']
    )

    return True
```

---

## SNS: The Publisher

### What Is SNS?

**SNS (Simple Notification Service)** is AWS's **publish/subscribe** service. Think of it like a **newspaper publisher**:

- Publisher creates a topic
- Multiple subscribers subscribe to the topic
- Publisher publishes a message once
- All subscribers receive the message immediately
- **No waiting, no queuing**

### SNS Architecture Diagram

```
Publisher
    ↓
    │ Publishes message to Topic
    ↓
┌─────────────────────────┐
│   SNS Topic             │
│   "order-notifications" │
└─────────────────────────┘
    ↓ ↓ ↓ ↓
    │ │ │ │
    ↓ ↓ ↓ ↓
┌────┐ ┌────┐ ┌────┐ ┌────┐
│ SMS│ │Email│ │HTTP│ │SQS │
└────┘ └────┘ └────┘ └────┘

All subscribers get the message IMMEDIATELY
```

### SNS Characteristics

✅ **Push Model** - AWS pushes to subscribers
✅ **Broadcast** - One message to many recipients
✅ **Real-time** - Instant delivery
✅ **No Storage** - Messages not persisted
✅ **Lost if Missed** - If subscriber is down, message is lost
✅ **Multiple Protocols** - SMS, Email, HTTP, Lambda, SQS, etc.

### SNS Code Example

```python
import boto3
import json

# Create SNS client
sns = boto3.client('sns')

# Create a topic
response = sns.create_topic(Name='order-notifications')
topic_arn = response['TopicArn']
print(f"Created topic: {topic_arn}")

# Subscribe via Email
email_subscription = sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='admin@example.com'
)

# Subscribe via SMS
sms_subscription = sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sms',
    Endpoint='+1234567890'
)

# Publish a message
message = {
    'order_id': '12345',
    'customer': 'John Doe',
    'amount': '$99.99',
    'status': 'Order confirmed!'
}

sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(message),
    Subject='New Order Notification'
)

# Result: Email AND SMS subscriber BOTH receive the message immediately
```

### When to Use SNS

✅ **Send notifications to many recipients** - SMS, Email, Webhooks
✅ **Fan-out pattern** - One event triggers many actions
✅ **Real-time alerts** - Security incidents, price drops, alerts
✅ **Broadcasting** - News feed, system notifications
✅ **Mobile push notifications** - To iOS/Android apps

### When NOT to Use SNS

❌ **Need message persistence** - Messages aren't stored
❌ **Subscriber might be down** - Message will be lost
❌ **Need retries** - Limited retry mechanism
❌ **Need to decouple services** - Use SQS instead
❌ **Need message ordering** - SNS doesn't guarantee order

---

## SQS: The Queue

### What Is SQS?

**SQS (Simple Queue Service)** is AWS's **message queue** service. Think of it like a **mailbox**:

- Messages are placed in a queue
- One consumer pulls messages from the queue
- Consumer processes at their own pace
- Messages are **stored** until explicitly deleted
- **No loss of messages even if consumer is down**

### SQS Architecture Diagram

```
Producer 1     Producer 2     Producer 3
    ↓              ↓              ↓
    └──────────────┬──────────────┘
                   ↓
          ┌─────────────────┐
          │  SQS Queue      │
          │  "order-queue"  │
          │                 │
          │  Msg1  Msg2     │
          │  Msg3  Msg4     │
          │  Msg5  ...      │
          └─────────────────┘
                   ↓
              (Consumer polls)
                   ↓
            ┌─────────────┐
            │  Consumer   │
            │  Processes  │
            │   Messages  │
            └─────────────┘

Consumer controls pace - takes messages when ready
```

### SQS Characteristics

✅ **Pull Model** - Consumer pulls messages
✅ **Queue** - Messages stored until retrieved
✅ **Durable** - Messages persisted (up to 14 days)
✅ **No Message Loss** - Even if consumer crashes
✅ **One Consumer Per Message** - Message deleted after processing
✅ **Decoupling** - Producer and consumer independent

### SQS Code Example

```python
import boto3
import json
import time

# Create SQS client
sqs = boto3.client('sqs')

# Create a queue
response = sqs.create_queue(QueueName='order-queue')
queue_url = response['QueueUrl']
print(f"Created queue: {queue_url}")

# Producer: Send messages
for i in range(5):
    message = {
        'order_id': f'ORD-{i}',
        'customer': f'Customer {i}',
        'amount': f'${100 * (i + 1)}'
    }

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )
    print(f"Sent message: {message['order_id']}")

# Consumer: Pull messages
print("\nConsumer pulling messages...")
while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5  # Long polling
    )

    if 'Messages' not in response:
        print("No more messages in queue")
        break

    for message in response['Messages']:
        body = json.loads(message['Body'])
        print(f"Processing: {body['order_id']}")

        # Process the message
        time.sleep(1)  # Simulate processing

        # Delete message after successful processing
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        print(f"Deleted: {body['order_id']}")

# Result: Messages stay in queue until explicitly deleted
```

### When to Use SQS

✅ **Decouple services** - Producer and consumer don't need to know each other
✅ **Buffer traffic spikes** - Queue absorbs sudden load
✅ **Reliable message delivery** - Messages persisted until processed
✅ **Rate limiting** - Consumer processes at controlled pace
✅ **Retry logic** - Easy to reprocess failed messages
✅ **Microservices** - Pass data between independent services

### When NOT to Use SQS

❌ **Need immediate delivery to many** - Use SNS instead
❌ **Don't need message persistence** - SNS is simpler
❌ **Need real-time notifications** - SNS is faster
❌ **Broadcasting to many endpoints** - SNS fan-out is better

---

## Processing & Deleting SQS Messages

As a tutor, understanding **how to signal SQS that a message has been processed** is critical. This is the most common mistake beginners make!

### The Problem: Messages Don't Automatically Disappear

```python
# ❌ WRONG - Message stays in queue forever
sqs = boto3.client('sqs')

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1
)

message = response['Messages'][0]
body = json.loads(message['Body'])

# Process the message
process_order(body)

# BUG: Message is STILL in the queue!
# It will be reprocessed forever!
```

**What happens:**
```
1. Message arrives: {"order_id": 123}
   ↓
2. Consumer receives & processes it
   ↓
3. Order shipped successfully
   ↓
4. Message NOT deleted from queue
   ↓
5. Visibility timeout expires (30 seconds)
   ↓
6. Message reappears in queue
   ↓
7. Consumer receives AGAIN
   ↓
8. Order shipped AGAIN (duplicate!)
   ↓
9. Repeat forever... 😱
```

---

### The Solution: Delete the Message

```python
# ✅ CORRECT - Delete message after processing
sqs = boto3.client('sqs')

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1
)

message = response['Messages'][0]
body = json.loads(message['Body'])

# Process the message
process_order(body)

# SIGNAL SUCCESS: Delete the message
sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=message['ReceiptHandle']  # ← THE KEY!
)

# Result: Message is GONE from queue
```

---

### Understanding ReceiptHandle

**Question: Why not just use `message['MessageId']`?**

Great question! Let's understand the difference:

#### MessageId vs ReceiptHandle

| Aspect | MessageId | ReceiptHandle |
|--------|-----------|---------------|
| **What is it?** | Unique message identifier | Temporary access token |
| **Stays the same?** | Yes, forever | No, changes each time |
| **Used for** | Tracking, logging | Deletion, modification |
| **Example** | `550e8400-e29b-41d4-a716-446655440000` | `AQEBBjM4NTcyN...` (long string) |
| **Analogy** | Student ID number | Permission slip for today |

#### Why ReceiptHandle?

Think of it like a **parking meter ticket**:

```
MessageId = Your license plate (permanent identifier)
  - Identifies the car forever
  - Never changes
  - Used for tracking/logging

ReceiptHandle = Parking receipt with date/time
  - Gives you permission to use the spot RIGHT NOW
  - Expires after visibility timeout
  - Changes if you receive the message again
  - Required to pay (delete) the meter
```

**Real-world scenario:**
```
Message arrives at 10:00 AM
├─ MessageId: abc-123 (permanent)
└─ ReceiptHandle: xyz-789 (valid until 10:00:30)

Consumer A receives at 10:00 AM
├─ Gets MessageId: abc-123
└─ Gets ReceiptHandle: xyz-789 (for this specific receipt)

Consumer A tries to delete at 10:00:15
├ Uses: ReceiptHandle: xyz-789 ✅ WORKS (still valid)

Consumer A crashes at 10:00:20
├─ Doesn't delete the message

Visibility timeout expires at 10:00:30
├─ Message reappears in queue

Consumer B receives at 10:00:35
├─ Gets MessageId: abc-123 (SAME as before!)
└─ Gets ReceiptHandle: new-handle-111 (DIFFERENT)

Consumer A (revived) tries to delete at 10:00:40
├ Uses: ReceiptHandle: xyz-789
├ Error! ❌ "Invalid ReceiptHandle"
├ Reason: xyz-789 expired at 10:00:30

Consumer B deletes at 10:00:40
├ Uses: ReceiptHandle: new-handle-111 ✅ WORKS
├ Message finally deleted
```

---

### How to Delete Messages

#### Single Message Deletion

```python
import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/order-queue'

# Step 1: Receive message
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=20  # Long polling
)

if 'Messages' not in response:
    print("No messages")
else:
    # Step 2: Process message
    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']  # ← SAVE THIS
    body = json.loads(message['Body'])

    try:
        print(f"Processing order: {body['order_id']}")
        # Do your work here
        process_order(body)

        # Step 3: Delete message on success
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print(f"✓ Message deleted successfully")

    except Exception as e:
        # Don't delete on error
        # Message will reappear and retry
        print(f"✗ Error processing: {e}")
        # Don't delete - message stays for retry
```

#### Batch Delete (Multiple Messages)

```python
import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/order-queue'

# Step 1: Receive up to 10 messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)

if 'Messages' not in response:
    print("No messages")
else:
    messages_to_delete = []

    # Step 2: Process all messages
    for message in response['Messages']:
        body = json.loads(message['Body'])

        try:
            print(f"Processing: {body['order_id']}")
            process_order(body)

            # Mark for deletion
            messages_to_delete.append({
                'Id': message['MessageId'],          # ← Use MessageId for batch
                'ReceiptHandle': message['ReceiptHandle']  # ← Include ReceiptHandle
            })

        except Exception as e:
            print(f"✗ Error: {e}")
            # Don't add to delete list - message retries

    # Step 3: Delete all successfully processed messages
    if messages_to_delete:
        sqs.delete_message_batch(
            QueueUrl=queue_url,
            Entries=messages_to_delete
        )
        print(f"✓ Deleted {len(messages_to_delete)} messages")
```

---

### What Happens If You Don't Delete?

#### Scenario 1: Consumer Processes & Doesn't Delete

```
Timeline:
─────────────────────────────────────────────────

10:00:00 AM
  Message arrives: {"order_id": 123}
  ↓
  Consumer receives message
  ReceiptHandle valid until: 10:00:30

10:00:05 AM
  Consumer: "Order processed! Sending shipment..."
  ↓
  Order shipped
  ↓
  BUT: Doesn't call delete_message()

10:00:30 AM
  Visibility timeout expires
  ↓
  Message reappears in queue

10:00:35 AM
  Another consumer receives SAME message
  ↓
  Processes again
  ↓
  Ships order AGAIN (duplicate!)

10:01:00 AM
  Second visibility timeout expires
  ↓
  Message reappears
  ↓
  Third consumer processes
  ↓
  TRIPLE shipment! 😱

Result:
- Customer receives 3 shipments
- Inventory deducted 3x
- Refund requests
- Angry customer review
```

#### Scenario 2: Consumer Crashes During Processing

```
Timeline:
─────────────────────────────────────────────────

10:00:00 AM
  Message arrives: {"payment": "$1000"}
  ReceiptHandle valid until: 10:05:00 (5 minute timeout)

10:00:10 AM
  Consumer receives
  Starts processing: "Charging credit card..."

10:00:15 AM
  Consumer crashes! 💥
  Process dies before calling delete_message()

10:00:16 AM
  Message still locked (hidden)
  Only this consumer can delete it

10:05:01 AM
  Visibility timeout expires (5 minutes)
  Message reappears in queue
  Now visible to other consumers

10:05:05 AM
  New consumer receives message
  Retries payment processing
  ✓ Payment succeeds (automatic retry!)

Result:
- Message not lost ✅
- Automatic retry on failure ✅
- Visibility timeout prevents infinite loops ✅
```

---

### Visibility Timeout: The Safety Net

**Visibility Timeout** = How long SQS hides the message from other consumers

```yaml
Default: 30 seconds
Range: 0 seconds to 12 hours
```

**How it works:**

```
Step 1: Message in queue
  ├─ Visible to all consumers
  ├─ Status: AVAILABLE

Step 2: Consumer receives message
  ├─ Message becomes hidden
  ├─ Status: INVISIBLE for 30 seconds
  ├─ Only this consumer can delete it

Step 3 (Option A): Consumer processes & deletes successfully
  ├─ Calls delete_message()
  ├─ Message removed forever
  ├─ Status: DELETED
  └─ Other consumers never see it

Step 3 (Option B): Consumer crashes before deleting
  ├─ Visibility timeout expires (30 seconds)
  ├─ Message becomes visible again
  ├─ Status: AVAILABLE
  ├─ Another consumer can receive & retry
  └─ No permanent data loss!
```

---

### Error Handling: When NOT to Delete

```python
import boto3
import json
import logging

sqs = boto3.client('sqs')
logger = logging.getLogger()

def process_messages(queue_url):
    """
    Best practice: Only delete on guaranteed success
    """

    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )

    if 'Messages' not in response:
        return

    for message in response['Messages']:
        try:
            body = json.loads(message['Body'])

            # Step 1: Validate message
            if not validate_message(body):
                # Invalid message - delete it (don't retry forever)
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                logger.warning(f"Deleted invalid message: {body}")
                continue

            # Step 2: Process message
            result = process_order(body)

            # Step 3: Only delete on SUCCESS
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            logger.info(f"✓ Processed & deleted: {body['order_id']}")

        except ValueError as e:
            # JSON parse error - invalid message
            # Delete to avoid infinite retry
            logger.error(f"Invalid JSON: {e}")
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )

        except Exception as e:
            # Temporary error (network, timeout, etc.)
            # Don't delete - let it retry
            logger.error(f"Temporary error: {e}")
            # Message stays in queue
            # Will retry after visibility timeout
```

---

### Common Mistakes

#### Mistake 1: Using Wrong Handle for Batch Delete

```python
# ❌ WRONG
entries = [{
    'Id': message['ReceiptHandle'],  # WRONG - should be MessageId!
    'ReceiptHandle': message['MessageId']  # WRONG - should be ReceiptHandle!
}]

# ✅ CORRECT
entries = [{
    'Id': message['MessageId'],  # MessageId for batch operation
    'ReceiptHandle': message['ReceiptHandle']  # ReceiptHandle for deletion
}]
```

#### Mistake 2: Deleting Before Processing

```python
# ❌ WRONG - Deletes before processing
message = response['Messages'][0]
sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=message['ReceiptHandle']
)
# NOW process
process_order(message)  # If this fails, data is lost!

# ✅ CORRECT - Delete only after success
process_order(message)  # Process first
if success:
    sqs.delete_message(  # Delete only after confirming success
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )
```

#### Mistake 3: Ignoring Batch Failures

```python
# ❌ WRONG - Assumes all deletes succeed
response = sqs.delete_message_batch(
    QueueUrl=queue_url,
    Entries=entries
)
# Doesn't check if deletions failed!

# ✅ CORRECT - Handle partial failures
response = sqs.delete_message_batch(
    QueueUrl=queue_url,
    Entries=entries
)

# Check for failures
if 'Failed' in response and len(response['Failed']) > 0:
    logger.error(f"Failed to delete {len(response['Failed'])} messages")
    for failed in response['Failed']:
        logger.error(f"Message {failed['Id']}: {failed['Message']}")
```

---

### Best Practices Checklist

✅ **Always delete messages after successful processing**
✅ **Use ReceiptHandle (not MessageId) for deletion**
✅ **Delete AFTER processing, not before**
✅ **Check for errors in batch delete responses**
✅ **Handle different error types differently**:
   - Invalid message → Delete (don't retry forever)
   - Temporary failure → Don't delete (retry later)
   - Processing complete → Delete immediately
✅ **Set appropriate visibility timeout** (match your processing time)
✅ **Use long polling** to reduce API calls
✅ **Monitor dead letter queues** for permanently failed messages

---

### Real-World Example: E-Commerce Order Processing

```python
import boto3
import json
import logging
from datetime import datetime

sqs = boto3.client('sqs')
dynamodb = boto3.client('dynamodb')
logger = logging.getLogger()

def process_orders(queue_url):
    """Process orders from SQS queue"""

    while True:
        # Receive up to 10 messages
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            VisibilityTimeout=300  # 5 minutes to process
        )

        if 'Messages' not in response:
            logger.info("No orders to process")
            break

        messages_to_delete = []

        for message in response['Messages']:
            try:
                # Parse order
                order = json.loads(message['Body'])
                order_id = order['order_id']

                logger.info(f"Processing order: {order_id}")

                # Step 1: Validate
                validate_order(order)

                # Step 2: Process
                process_payment(order)
                update_inventory(order)
                send_confirmation_email(order)

                # Step 3: Store in DynamoDB
                dynamodb.put_item(
                    TableName='Orders',
                    Item={
                        'order_id': {'S': order_id},
                        'status': {'S': 'completed'},
                        'processed_at': {'S': datetime.utcnow().isoformat()}
                    }
                )

                # Step 4: Mark for deletion
                messages_to_delete.append({
                    'Id': message['MessageId'],
                    'ReceiptHandle': message['ReceiptHandle']
                })

                logger.info(f"✓ Order processed: {order_id}")

            except ValueError as e:
                # Invalid order - delete it
                logger.error(f"Invalid order format: {e}")
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

            except Exception as e:
                # Temporary error - keep message in queue
                logger.error(f"Processing error: {e}")
                # Don't delete - will retry after visibility timeout

        # Delete all successfully processed messages
        if messages_to_delete:
            delete_response = sqs.delete_message_batch(
                QueueUrl=queue_url,
                Entries=messages_to_delete
            )

            # Check for failures
            if 'Failed' in delete_response and delete_response['Failed']:
                logger.error(f"Some messages failed to delete: {delete_response['Failed']}")
            else:
                logger.info(f"✓ Deleted {len(messages_to_delete)} processed orders")

# Run the processor
process_orders('https://sqs.us-east-1.amazonaws.com/123456789012/orders')
```

---

## SNS + SQS: The Power Couple

### Why Combine Them?

Imagine you need **both**:
- Send a message to **many different systems** (SNS strength)
- But each system should **process at its own pace** (SQS strength)

**Solution: SNS publishes to SQS queues!**

### The Pattern

```
┌─────────────┐
│  Publisher  │
│   (Lambda)  │
└──────┬──────┘
       │
       │ Publishes event
       ↓
┌──────────────────────────┐
│   SNS Topic              │
│   "order-events"         │
└──────┬───┬───┬───────────┘
       │   │   │
       │   │   └─────────────────────────┐
       │   │                             │
       ↓   ↓                             ↓
   ┌─────────────┐  ┌──────────────┐  ┌────────────────┐
   │SQS Queue    │  │SQS Queue     │  │SQS Queue       │
   │"email-jobs" │  │"sms-jobs"    │  │"analytics-jobs"│
   └──────┬──────┘  └───────┬──────┘  └────────┬───────┘
          │                 │                  │
          ↓                 ↓                  ↓
     ┌────────────┐   ┌──────────┐    ┌───────────────┐
     │Email       │   │SMS       │    │Analytics      │
     │Service     │   │Service   │    │Service        │
     └────────────┘   └──────────┘    └───────────────┘

KEY: One SNS topic → Multiple SQS queues → Independent processing
```

### Why This Is Powerful

✅ **Broadcast + Decouple**: One event reaches many services
✅ **Independent Processing**: Each service processes at own pace
✅ **No Message Loss**: SQS stores messages if service is down
✅ **Scalability**: Add new services just by creating new queue
✅ **Resilience**: One service failure doesn't affect others

### SNS + SQS Code Example

```python
import boto3
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Setup
sns = boto3.client('sns')
sqs = boto3.client('sqs')

# Step 1: Create SNS Topic
topic_response = sns.create_topic(Name='order-events')
topic_arn = topic_response['TopicArn']
print(f"✓ Created SNS Topic: {topic_arn}")

# Step 2: Create SQS Queues
queues = {}
for queue_name in ['email-jobs', 'sms-jobs', 'analytics-jobs']:
    queue_response = sqs.create_queue(QueueName=queue_name)
    queue_url = queue_response['QueueUrl']
    queues[queue_name] = queue_url
    print(f"✓ Created SQS Queue: {queue_name}")

    # Step 3: Subscribe each queue to the topic
    sqs_attributes = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['QueueArn']
    )
    queue_arn = sqs_attributes['Attributes']['QueueArn']

    sns.subscribe(
        TopicArn=topic_arn,
        Protocol='sqs',
        Endpoint=queue_arn
    )
    print(f"✓ Subscribed {queue_name} to SNS topic")

# Step 4: Publish an order event to SNS (goes to ALL queues)
order = {
    'order_id': 'ORD-12345',
    'customer_email': 'john@example.com',
    'customer_phone': '+1234567890',
    'items': ['Item A', 'Item B'],
    'total': '$99.99'
}

sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(order),
    Subject='New Order Created'
)
print(f"\n✓ Published order event to SNS")

# Step 5: Each service consumes from its queue (independently)
def process_email_queue():
    """Email service processes messages"""
    print("\n📧 Email Service started processing...")
    response = sqs.receive_message(
        QueueUrl=queues['email-jobs'],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )

    if 'Messages' in response:
        message = response['Messages'][0]
        # SNS wraps the message in another JSON
        body = json.loads(message['Body'])
        order = json.loads(body['Message'])

        print(f"  → Sending email to {order['customer_email']}")
        time.sleep(1)  # Simulate email sending

        sqs.delete_message(
            QueueUrl=queues['email-jobs'],
            ReceiptHandle=message['ReceiptHandle']
        )
        print(f"  ✓ Email sent successfully")

def process_sms_queue():
    """SMS service processes messages"""
    print("\n📱 SMS Service started processing...")
    response = sqs.receive_message(
        QueueUrl=queues['sms-jobs'],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )

    if 'Messages' in response:
        message = response['Messages'][0]
        body = json.loads(message['Body'])
        order = json.loads(body['Message'])

        print(f"  → Sending SMS to {order['customer_phone']}")
        time.sleep(0.5)  # Simulate SMS sending

        sqs.delete_message(
            QueueUrl=queues['sms-jobs'],
            ReceiptHandle=message['ReceiptHandle']
        )
        print(f"  ✓ SMS sent successfully")

def process_analytics_queue():
    """Analytics service processes messages"""
    print("\n📊 Analytics Service started processing...")
    response = sqs.receive_message(
        QueueUrl=queues['analytics-jobs'],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )

    if 'Messages' in response:
        message = response['Messages'][0]
        body = json.loads(message['Body'])
        order = json.loads(body['Message'])

        print(f"  → Recording order analytics for {order['order_id']}")
        time.sleep(2)  # Simulate analytics processing

        sqs.delete_message(
            QueueUrl=queues['analytics-jobs'],
            ReceiptHandle=message['ReceiptHandle']
        )
        print(f"  ✓ Analytics recorded")

# Step 6: Run all services in parallel (simulating independent services)
print("\n" + "="*50)
print("SERVICES PROCESSING INDEPENDENTLY")
print("="*50)

with ThreadPoolExecutor(max_workers=3) as executor:
    executor.submit(process_email_queue)
    executor.submit(process_sms_queue)
    executor.submit(process_analytics_queue)

print("\n✓ All services processed the same order event independently!")
```

### Key Insights

```
SNS alone:
  Publisher → Topic → Email (lost if down)
                    → SMS (lost if down)
                    → Analytics (lost if down)
  Problem: If any service is down, message is lost

SNS + SQS:
  Publisher → Topic → SQS (email queue, persisted)
                    → SQS (SMS queue, persisted)
                    → SQS (Analytics queue, persisted)
             ↓         ↓            ↓
          Email      SMS      Analytics
  Benefit: Services can be down, messages wait in queue!
```

---

## Real-World Use Cases

### Use Case 1: E-Commerce Order Processing

**Scenario**: When an order is placed, multiple systems need to act:

```
Customer places order
        ↓
    Lambda function
        ↓
  SNS Topic: "order-placed"
        ↓
    ├─→ SQS: Email Queue (send confirmation)
    ├─→ SQS: SMS Queue (send SMS notification)
    ├─→ SQS: Inventory Queue (deduct stock)
    ├─→ SQS: Analytics Queue (record event)
    └─→ SQS: Fulfillment Queue (prepare shipment)

Benefits:
✓ All services notified instantly
✓ Each service processes at own pace
✓ If email service is slow, other services aren't blocked
✓ If SMS service is down, message waits in queue
✓ Easy to add new service (just add new SQS queue)
```

### Use Case 2: Real-Time Monitoring with Persistence

**Scenario**: System issues need immediate alerts but also must be logged

```
Monitoring System
        ↓
    SNS Topic: "system-alerts"
        ↓
    ├─→ SMS (immediate notification to ops team)
    ├─→ Email (documented notification)
    └─→ SQS: "audit-logs" (log for compliance)

Benefits:
✓ Ops team gets SMS immediately
✓ Even if audit service is down, logs won't be lost
✓ Can replay logs later if needed
```

### Use Case 3: Data Processing Pipeline

**Scenario**: Process files as they arrive

```
S3 Upload
    ↓
S3 → SNS: "file-uploaded"
         ↓
    SQS: "file-processing" queue
         ↓
  Multiple workers (auto-scaling)
  Pull messages and process files

Benefits:
✓ Workers scale based on queue depth
✓ If worker crashes, message stays in queue
✓ Easy to add more workers
```

---

## Code Examples

### Example 1: SNS Only (Simple Broadcasting)

```python
# Good for: Simple notifications where loss is acceptable

sns = boto3.client('sns')

# Create topic
topic = sns.create_topic(Name='stock-price-alerts')

# Subscribe multiple recipients
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='email', Endpoint='trader@example.com')
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='sms', Endpoint='+1234567890')
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='http', Endpoint='https://api.example.com/webhook')

# Publish alert
sns.publish(
    TopicArn=topic['TopicArn'],
    Message='TSLA dropped 5%! Current price: $250'
)

# Result: Email, SMS, and webhook all receive message immediately
```

### Example 2: SQS Only (Reliable Processing)

```python
# Good for: Decoupling services, buffering

sqs = boto3.client('sqs')

# Create queue
queue = sqs.create_queue(QueueName='image-processing')

# Producer: Upload images
for image_file in images:
    sqs.send_message(
        QueueUrl=queue['QueueUrl'],
        MessageBody=f'Process image: {image_file}'
    )

# Consumer: Process images at own pace
while True:
    response = sqs.receive_message(
ueueUrl=queue['QueueUrl'], MaxNumberOfMessages=5)

    if 'Messages' not in response:
        break

    for msg in response['Messages']:
        process_image(msg['Body'])
        sqs.delete_message(QueueUrl=queue['QueueUrl'], ReceiptHandle=msg['ReceiptHandle'])
```

### Example 3: SNS → SQS (Best of Both Worlds)

```python
# Good for: Broadcasting to decoupled services

sns = boto3.client('sns')
sqs = boto3.client('sqs')

# Create topic and queues
topic = sns.create_topic(Name='payments')
email_queue = sqs.create_queue(QueueName='payment-emails')
sms_queue = sqs.create_queue(QueueName='payment-sms')

# Subscribe queues to topic
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='sqs',
              Endpoint=email_queue['QueueUrl'])
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='sqs',
              Endpoint=sms_queue['QueueUrl'])

# Publish once to topic
sns.publish(TopicArn=topic['TopicArn'], Message='Payment received: $100')

# Both queues get the message (automatically)
# Each service processes independently
```

---

## Decision Tree

```
┌─ Do you need message persistence?
│  ├─ YES → SQS or SNS→SQS
│  └─ NO → SNS
│
├─ Do you have multiple subscribers?
│  ├─ YES → SNS or SNS→SQS
│  └─ NO → SQS
│
├─ Need immediate delivery?
│  ├─ YES → SNS
│  └─ NO (processing at own pace) → SQS
│
├─ Need services decoupled?
│  ├─ YES → SQS or SNS→SQS
│  └─ NO → SNS
│
└─ Bottom line:
   ├─ Simple broadcast → SNS
   ├─ Reliable processing → SQS
   └─ Broadcast + Reliable → SNS → SQS
```

---

## Architecture Patterns

### Pattern 1: Simple Fan-Out (SNS)

```yaml
Use Case: Breaking news notification
Architecture:
  News API → SNS Topic → Multiple Subscribers (Email, SMS, App Push)
Pros: Simple, fast
Cons: Message loss if subscriber down
```

### Pattern 2: Worker Pool (SQS)

```yaml
Use Case: Image resizing
Architecture:
  Upload → SQS Queue ← Multiple Workers (auto-scaling)
Pros: Reliable, scalable
Cons: Not good for broadcasting
```

### Pattern 3: Event-Driven Microservices (SNS → SQS)

```yaml
Use Case: E-commerce order system
Architecture:
  Order Created Event
    ↓
  SNS Topic
    ├→ SQS (Email Service)
    ├→ SQS (Inventory Service)
    ├→ SQS (Payment Service)
    ├→ SQS (Analytics Service)
    └→ SQS (Notification Service)

Pros: Scalable, decoupled, reliable, broadcast
Cons: More complex setup
```

### Pattern 4: Dead Letter Queue (SNS → SQS with DLQ)

```yaml
Use Case: Critical payment processing
Architecture:
  Order Event
    ↓
  SNS Topic
    ↓
  SQS Main Queue
    ├─ Success → Processed
    ├─ Retry 3x → DLQ (Dead Letter Queue)
    └─ Manual review

Pros: Handles failures gracefully
Cons: Requires monitoring
```

---

## Summary Table

| Aspect | SNS | SQS | SNS→SQS |
|--------|-----|-----|---------|
| **Architecture** | Push | Pull | Push→Pull |
| **Use Case** | Broadcast | Process | Both |
| **Message Storage** | No | Yes | Yes |
| **Subscribers** | Many | One | One per queue |
| **Resilience** | Poor | Excellent | Excellent |
| **Scalability** | Limited | Excellent | Excellent |
| **Latency** | Instant | Polling | Fast |
| **Complexity** | Simple | Simple | Moderate |

---

## References

- [AWS SNS Documentation](https://docs.aws.amazon.com/sns/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [Serverless Framework SNS](https://www.serverless.com/amazon-sns)
- [AWS Messaging Architecture Patterns](https://aws.amazon.com/architecture/)

---

**Key Takeaway**: Use **SNS for broadcasting** and **SQS for reliable processing**. Combine them with **SNS → SQS for the best of both worlds!** 🚀
