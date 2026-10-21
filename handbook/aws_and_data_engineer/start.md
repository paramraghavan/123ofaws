# AWS & Data Engineering - START HERE

**For**: SQL & Spark SQL engineers (Azure) new to AWS
**Goal**: Run ETL pipelines locally, then on real AWS
**Time**: 10 minutes to setup, 5-6 hours to learn

---

## What You'll Build

```
Your ETL Pipeline on AWS:

        CSV File
           ↓
      ┌─────────┐
      │    S3   │  ← Cloud storage (like Azure Blob)
      └────┬────┘
           │
      ┌────▼──────────────┐
      │   Lambda-1        │  ← Validates data
      │  (validate)       │
      └────┬──────────────┘
           │
      ┌────▼──────────────┐
      │    SNS Topic      │  ← Broadcasts message
      │ (notification)    │
      └────┬──────────────┘
           │
      ┌────▼──────────────┐
      │   SQS Queue       │  ← Reliable message queue
      │  (safe storage)   │
      └────┬──────────────┘
           │
      ┌────▼──────────────┐
      │   Lambda-2        │  ← Processes data
      │ (transform)       │
      └────┬──────────────┘
           │
           ↓
      Clean CSV Output
```

**All running on your Mac/Windows with LocalStack** (fake AWS in Docker)

---

## Your AWS Knowledge Transfer

```
What you know (Azure/Spark SQL):

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Azure Blob     │    │ Synapse Spark   │    │   Data Factory  │
│   Storage       │    │   (PySpark)     │    │ (orchestration) │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                       │                      │
         │ 95% transfers         │ 90% transfers        │ 100% transfers
         │                       │                      │
         ▼                       ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     AWS S3      │    │ AWS Glue/EMR    │    │ Step Functions  │
│   (storage)     │    │  (Spark jobs)   │    │ (workflows)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Your SQL skills → 100% works in Spark SQL
Your Spark skills → Works in Glue or EMR
Your ETL patterns → Same architecture everywhere
```

---

## LocalStack vs Real AWS

```
LOCALSTACK (Your Laptop)          REAL AWS (Cloud)
════════════════════════════════════════════════════════

┌─────────────────────┐           ┌──────────────────────┐
│   Docker Container  │           │   AWS Cloud          │
│                     │           │                      │
│ ├─ Fake S3          │           │ ├─ Real S3           │
│ ├─ Fake Lambda      │           │ ├─ Real Lambda       │
│ ├─ Fake SQS         │           │ ├─ Real SQS          │
│ ├─ Fake SNS         │           │ ├─ Real SNS          │
│ └─ Fake ...         │           │ └─ Real ...          │
│                     │           │                      │
└─────────────────────┘           └──────────────────────┘

Cost: $0                          Cost: $50-200/month

No internet needed                Internet required

Instant (microseconds)            Network latency

Same code everywhere!


WORKFLOW:

Development                       Production
┌──────────────────────┐         ┌──────────────────────┐
│ LocalStack           │         │ Real AWS             │
│                      │         │                      │
│ endpoint_url=        │  ✓ →    │ endpoint_url=        │
│ localhost:4566       │ COPY     │ s3.amazonaws.com     │
│                      │         │                      │
│ credentials="test"   │  ✓ →    │ credentials=         │
│                      │ UPDATE   │ (real AWS keys)      │
└──────────────────────┘         └──────────────────────┘

Same code works everywhere!
```

---

## 10-Minute Quick Start

### Step 1: Start LocalStack (Docker)

```bash
docker run -it -p 4566:4566 localstack/localstack
```

You'll see:
```
✓ LocalStack is running
✓ Ready to handle requests on http://localhost:4566
```

### Step 2: Test It Works

In another terminal:

```bash
python3 << 'PYTHON'
import boto3

# Connect to LocalStack
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Create a bucket
s3.create_bucket(Bucket="my-test-bucket")

# List buckets
response = s3.list_buckets()
print(f"✓ Created bucket: {response['Buckets'][0]['Name']}")
PYTHON
```

**If you see `✓ Created bucket:...` → You're ready!**

---

## Learning Path (5-6 Hours Total)

```
Phase 1: Setup (30 minutes)
┌──────────────────────────────────┐
│ setup.md                         │
│ ├─ Install Docker                │
│ ├─ Python environment            │
│ ├─ boto3 & CLI config            │
│ └─ Verify LocalStack works       │
└──────────────────────────────────┘
           ↓
Phase 2: Learn (3-4 hours)
┌──────────────────────────────────┐
│ learn.md                         │
│ ├─ S3 fundamentals               │
│ ├─ Lambda basics                 │
│ ├─ SNS (notifications)           │
│ ├─ SQS (queues)                  │
│ ├─ Step Functions (orchestration)│
│ └─ Hands-on: Build a pipeline    │
└──────────────────────────────────┘
           ↓
Phase 3: Practice (1-2 hours)
┌──────────────────────────────────┐
│ Build your own pipeline:         │
│ ├─ Upload CSV to S3              │
│ ├─ Lambda validates data         │
│ ├─ SNS/SQS routes messages       │
│ ├─ Lambda transforms data        │
│ └─ Output to S3                  │
└──────────────────────────────────┘
           ↓
    You're AWS-ready!
    (Optional: Deploy to real AWS)
```

---

## File Structure

```
aws_and_data_engineer/
├─ start.md              ← You are here
├─ setup.md              ← Next: Complete setup (30 min)
└─ learn.md              ← Then: Full learning content (3-4 hours)
```

---

## Next Steps

1. **Read setup.md** (30 minutes)
   - Get Docker running
   - Set up Python environment
   - Install boto3 and AWS CLI

2. **Read learn.md** (3-4 hours)
   - S3 fundamentals
   - Lambda, SNS, SQS
   - Complete working examples
   - Hands-on pipeline project

3. **Build** (1-2 hours)
   - Apply what you learned
   - Create your first ETL pipeline
   - Validate data, transform, output

---

## Prerequisites

- [ ] Python 3.9+
- [ ] Docker (or willing to install)
- [ ] Code editor (VS Code, PyCharm, etc.)
- [ ] Basic terminal comfort
- [ ] SQL knowledge (✓ you have this)
- [ ] Spark/PySpark basics (✓ you have this)

**If you checked most boxes, you're ready!**

---

## FAQ

**Q: Do I need AWS account?**
A: No! LocalStack runs locally on your Mac/Windows.

**Q: Will this help me with real AWS later?**
A: Yes! Same code, same patterns. Just change the endpoint URL.

**Q: How long does this take?**
A: 5-6 hours total. Can spread over several days.

**Q: What if I get stuck?**
A: See learn.md troubleshooting section.

---

## Start Now

```
→ Read setup.md next (30 minutes)
→ Then learn.md (3-4 hours)
→ Then build your pipeline (1-2 hours)
```

Let's go! 🚀
