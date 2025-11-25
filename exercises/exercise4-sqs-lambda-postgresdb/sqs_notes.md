## SQS Batch Size for Lambda

The number of messages Lambda reads at one time is controlled by the **Batch Size** setting when you configure the SQS trigger.

### Default and Limits

| Setting | Value |
|---------|-------|
| **Default** | 10 messages |
| **Minimum** | 1 message |
| **Maximum** | 10,000 messages (for standard queues) |

### Where to Configure

**In AWS Console:**
1. Go to your Lambda → **Configuration** → **Triggers**
2. Click on the SQS trigger
3. Edit **Batch size**

**In the code I provided:**
```python
# In test_local.py - when manually polling SQS
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,  # ← This controls batch size (max 10 for manual polling)
)
```

### How It Works

```
SQS Queue has 25 messages waiting
         │
         ▼
┌─────────────────────────────┐
│  Lambda Trigger             │
│  Batch Size = 10            │
│                             │
│  Invocation 1: 10 messages  │
│  Invocation 2: 10 messages  │
│  Invocation 3: 5 messages   │
└─────────────────────────────┘
```

### Recommendations

| Scenario | Batch Size | Why |
|----------|------------|-----|
| Small loans (quick processing) | 100-500 | Higher throughput |
| Large loans (heavy processing) | 10-50 | Avoid timeouts |
| Need ordering | 1 | Process one at a time |
| Your case (6 rows per message) | **10** | Good balance |

### Additional Setting: Batch Window

You can also set a **Batch Window** (0-300 seconds):
- Lambda waits up to this time to gather messages before invoking
- Useful if messages arrive slowly but you want to batch them

```
Batch Size: 10
Batch Window: 5 seconds

→ Lambda waits up to 5 seconds to collect 10 messages
→ Invokes with whatever it has (1-10 messages)
```