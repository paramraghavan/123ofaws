# SNS & SQS: Messaging Services

Simple explanation of AWS messaging services with practical examples.

---

## What is SNS? (Simple Notification Service)

**SNS = Broadcast/Push Notification Service**

Sends messages from a **publisher** to multiple **subscribers** simultaneously.

```
Publisher writes one message to SNS Topic
         ↓
SNS immediately delivers to ALL subscribers
         ↓
Each subscriber handles independently
```

**Key characteristic**: Messages are **pushed** instantly (broadcast). No storage.

---

## What is SQS? (Simple Queue Service)

**SQS = Message Queue Storage Service**

Stores messages in a queue. **Consumers** retrieve (poll) messages when ready.

```
Producer sends message to SQS Queue
         ↓
SQS stores the message (up to 14 days)
         ↓
Consumer polls and retrieves one message at a time
         ↓
Consumer processes and deletes
```

**Key characteristic**: Messages are **pulled** by consumers. Reliable storage.

---

## SNS vs SQS at a Glance

| Aspect | SNS | SQS |
|--------|-----|-----|
| **Type** | Broadcast | Queue |
| **Delivery** | Push (instant) | Pull (polling) |
| **Storage** | No | Yes (14 days) |
| **Subscribers** | Many (all get it) | One per message |
| **Timing** | Immediate | Delayed (consumer pace) |
| **Use Case** | Notifications, alerts | Reliable, decoupled work |

---

## SNS: How to Use It

### 1. Create a Topic
```python
import boto3

sns = boto3.client('sns')

# Create topic
response = sns.create_topic(Name='alerts')
topic_arn = response['TopicArn']
print(f"Created: {topic_arn}")
```

### 2. Add Subscribers to the Topic
```python
# Subscribe different resource types
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='admin@company.com'
)

sns.subscribe(
    TopicArn=topic_arn,
    Protocol='lambda',
    Endpoint='arn:aws:lambda:us-east-1:123:function:my-func'
)

sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint='arn:aws:sqs:us-east-1:123:my-queue'
)

sns.subscribe(
    TopicArn=topic_arn,
    Protocol='https',
    Endpoint='https://example.com/webhook'
)
```

### 3. Publish Messages
```python
# Publish to all subscribers
sns.publish(
    TopicArn=topic_arn,
    Subject='Alert',
    Message='Something happened'
)
```

---

## SNS Subscribers: What Resources Can Listen?

| Resource | Protocol | What Happens |
|----------|----------|--------------|
| **Email** | `email` | Sends email to address |
| **SMS** | `sms` | Sends text message |
| **Lambda** | `lambda` | Invokes Lambda function |
| **SQS** | `sqs` | Puts message in queue |
| **HTTP/HTTPS** | `https` | POSTs to webhook URL |
| **SNS Topic** | `sns` | Forwards to another topic |
| **Mobile Push** | `application` | Sends to mobile app |

**Key point**: When you publish to SNS, ALL subscribers receive the message **simultaneously**.

---

## SQS: How to Use It

### 1. Create a Queue
```python
import boto3

sqs = boto3.client('sqs')

# Create queue
response = sqs.create_queue(
    QueueName='my-queue',
    Attributes={
        'VisibilityTimeout': '300',  # 5 minutes
        'MessageRetentionPeriod': '86400'  # 1 day
    }
)
queue_url = response['QueueUrl']
print(f"Created: {queue_url}")
```

### 2. Send Messages (Producer)
```python
import json

# Send message to queue
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({
        'file': 'data.csv',
        'action': 'process'
    })
)
```

### 3. Receive Messages (Consumer)
```python
# Poll for messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1
)

# Process message
for message in response.get('Messages', []):
    body = json.loads(message['Body'])
    print(f"Processing: {body['file']}")

    # Delete after successful processing
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )
```

---

## SQS: What Resources Can Listen to Messages?

| Resource | How It Works |
|----------|--------------|
| **Lambda** | AWS automatically polls SQS, invokes Lambda with messages |
| **ECS Task** | Container polls SQS and processes |
| **EC2 Instance** | Code on EC2 polls SQS |
| **Custom App** | Any application that calls `receive_message()` |
| **SNS Subscriber** | Can subscribe SQS to SNS topic |

**Key point**: Consumer must **actively poll** (ask for messages). SQS doesn't push.

---

## Active Queue Size: What Does It Mean?

**Active Queue Size** = Number of messages currently in the queue waiting to be processed.

### Why It Matters

```
Queue with 10 messages (Active Size = 10):
┌─────────────────────────┐
│ M1, M2, M3, M4, M5      │
│ M6, M7, M8, M9, M10     │
│ Active Size = 10        │
└─────────────────────────┘

Consumer polls, gets 1 message:
┌─────────────────────────┐
│ M2, M3, M4, M5          │
│ M6, M7, M8, M9, M10     │
│ Active Size = 9         │
└─────────────────────────┘

Consumer finishes, deletes:
┌─────────────────────────┐
│ M3, M4, M5              │
│ M6, M7, M8, M9, M10     │
│ Active Size = 8         │
└─────────────────────────┘
```

### Key Points About Queue Size

1. **Monitor backlog**: Large queue size = work piling up
2. **Scale consumers**: If queue growing → add more workers
3. **Visibility timeout**: Message hidden while being processed
4. **Message retention**: Stored up to 14 days (configurable)

### Example Monitoring

```python
# Get queue depth
attributes = sqs.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=['ApproximateNumberOfMessages']
)

queue_size = int(attributes['Attributes']['ApproximateNumberOfMessages'])
print(f"Messages in queue: {queue_size}")

# If growing, add more consumers/workers
if queue_size > 100:
    print("Queue depth high! Consider scaling consumers")
```

---

## Real-World Pattern: SNS → SQS → Lambda

```
Event (Pipeline completes)
         ↓
SNS Topic publishes
    ├─ Email alert (to admin)
    ├─ Lambda function (invoked)
    └─ SQS queue (stores message)
             ↓
Consumer Lambda polls SQS
    ├─ Gets message from queue
    ├─ Processes (validates, transforms)
    ├─ Writes output
    └─ Deletes from queue

Result:
✓ Admin alerted instantly (SNS → Email)
✓ Automation triggered instantly (SNS → Lambda)
✓ Work queued reliably (SNS → SQS)
✓ Processing happens at own pace (SQS → Lambda consumer)
```

---

## Common Use Cases

### SNS: When to Use
- ✅ Send alerts (Email, SMS)
- ✅ Notify multiple services instantly
- ✅ Fan-out to many subscribers
- ✅ Real-time notifications

### SQS: When to Use
- ✅ Decouple producer and consumer
- ✅ Handle traffic bursts
- ✅ Reliable, asynchronous processing
- ✅ Retry failed messages
- ✅ Process at consumer's pace

### SNS + SQS: When to Use Both
- ✅ Notify instantly AND process reliably
- ✅ Event triggers multiple independent actions
- ✅ Enterprise data pipelines
- ✅ Best reliability + flexibility

---

## Configuration: Key Attributes

### SNS Topic
- **No storage**: Messages are not saved
- **No retry**: If subscriber fails, message lost
- **Subscribers know topic ARN**: Must subscribe to receive

### SQS Queue
- **Visibility Timeout**: How long message hidden during processing (default 30s)
- **Message Retention Period**: How long to keep messages (default 4 days, max 14 days)
- **Dead Letter Queue**: Where failed messages go (after max retries)
- **Batch Size**: How many messages per poll (default 1-10)

---

## Cost Estimate

For 1,000 messages/day:

| Service | Cost/Month |
|---------|-----------|
| SNS (1000 publishes) | $0.0005 |
| SQS (1000 requests) | $0.0004 |
| **Total** | **< $1/month** |

Very affordable!

---

## Summary Table

| Question | SNS | SQS |
|----------|-----|-----|
| What does it do? | Broadcasts messages | Stores messages |
| How are messages delivered? | Pushed (instant) | Pulled (polling) |
| Storage? | No | Yes (14 days) |
| How to add listeners? | Subscribe to topic | Consumer polls |
| Best for? | Notifications | Reliable work |

---

## See It In Action

→ **[etl-sqs-sns-lambda.md](./etl-sqs-sns-lambda.md)** - Complete working example with code

This example shows:
- Lambda validates S3 data
- Publishes to SNS if valid
- SQS receives and stores
- Another Lambda processes from queue
- Auto-retry on failure

Perfect for enterprise ETL pipelines! 🚀

---

## Quick Reference

```python
import boto3

# SNS: Create and publish
sns = boto3.client('sns')
topic = sns.create_topic(Name='alerts')
sns.subscribe(TopicArn=topic['TopicArn'], Protocol='email', Endpoint='...')
sns.publish(TopicArn=topic['TopicArn'], Message='Alert!')

# SQS: Create and use
sqs = boto3.client('sqs')
queue = sqs.create_queue(QueueName='tasks')
sqs.send_message(QueueUrl=queue['QueueUrl'], MessageBody='Task 1')
messages = sqs.receive_message(QueueUrl=queue['QueueUrl'])
sqs.delete_message(QueueUrl=queue['QueueUrl'], ReceiptHandle=...)
```

---

## Files in This Folder

| File | Purpose |
|------|---------|
| **README.md** | This guide (What, How, Subscribers, Resources) |
| **etl-sqs-sns-lambda.md** | Complete working example with Lambda code |

Done! Clean and focused. 📚
