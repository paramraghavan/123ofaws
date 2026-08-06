# How DataSync Works - Detailed Explanation

**Understanding Lambda, DataSync Service, and DataSync Agent**

---

## The Three Key Components

### 1. **Lambda Function**
- **What it is**: Your Python code running in AWS (serverless)
- **What it does**: Orchestrates the copy operation
- **When it runs**: Every day at 6 PM (triggered by EventBridge)
- **Talks to**: DataSync Service (via AWS API)

### 2. **DataSync Service**
- **What it is**: AWS managed service (you don't install anything)
- **What it does**: Manages the actual file copy operation
- **Where it runs**: AWS cloud (managed by Amazon)
- **Talks to**: Lambda + DataSync Agent

### 3. **DataSync Agent**
- **What it is**: Software installed on your EC2 instance
- **What it does**: Reads files from your NFS
- **Where it runs**: On EC2 in your VPC
- **Talks to**: DataSync Service + NFS mount

---

## Communication Flow

### **Lambda does NOT directly use DataSync Agent**

```
WRONG:
Lambda ──directly──> DataSync Agent ──> NFS
❌ This doesn't happen

CORRECT:
Lambda ──API call──> DataSync Service ──HTTPS──> DataSync Agent ──NFS mount──> NFS
✓ This is what actually happens
```

---

## Step-by-Step: What Happens at 6 PM

### **STEP 1: EventBridge Triggers Lambda (6:00 PM)**

```python
# EventBridge rule: "cron(0 18 * * ? *)"
# Time: 6:00 PM UTC every day
# Action: Trigger Lambda function

Lambda starts executing:
  daily_sync.py
```

### **STEP 2: Lambda Gets Today's Date**

```python
from datetime import datetime

today = datetime.now()
year = today.strftime('%Y')      # 2025
month_day = today.strftime('%m%d')  # 0805

print(f"Today is: {year}/{month_day}")  # 2025/0805
```

### **STEP 3: Lambda Calls DataSync Service API**

```python
import boto3

datasync = boto3.client('datasync')

# Lambda does NOT connect to Agent
# Lambda connects to DataSync Service
response = datasync.start_task_execution(TaskArn=task_arn)

# This is an HTTPS API call to AWS
# Goes to: https://datasync.us-east-1.amazonaws.com/
# Not to: EC2 instance or DataSync Agent
```

**What Lambda is really doing:**
```
Lambda → AWS API Endpoint (HTTPS)
         "Start the task with ARN: arn:aws:datasync:..."
```

### **STEP 4: DataSync Service Receives Command**

**Inside AWS Cloud:**
```
DataSync Service receives Lambda's request:
  • Task ARN: arn:aws:datasync:us-east-1:123456789012:task/abc123
  • Action: start_task_execution()

DataSync Service says:
  "I need to tell my Agent on EC2 to start copying"
```

### **STEP 5: DataSync Service Connects to DataSync Agent**

**Connection Details:**
```
Source:       DataSync Service (AWS Cloud)
Destination:  DataSync Agent (on EC2)
Protocol:     HTTPS (port 443, encrypted)
Command:      "Read files from /mnt/nfs and send them to me"

Over HTTPS, DataSync Service sends:
  • Location of NFS: /mnt/nfs
  • Files to copy: /2025/0805/
  • Where to send: S3 bucket details
```

### **STEP 6: DataSync Agent Reads from NFS**

**On the EC2 Instance:**
```bash
DataSync Agent receives command from Service:
  "Read files from /mnt/nfs/2025/0805/"

Agent actions:
  1. Connects to NFS mount point: /mnt/nfs
  2. Reads /2025/0805/ directory
  3. Lists all files
  4. Checks which are new (not already in S3)
  5. Starts reading file contents
```

### **STEP 7: DataSync Agent Sends Files to DataSync Service**

**The Data Path:**
```
NFS Files
    ↓ (read via NFS protocol)
EC2 DataSync Agent (buffers the data)
    ↓ (sends via HTTPS to AWS)
DataSync Service (in AWS cloud)
    ↓ (writes to S3)
S3 Bucket (files stored)
```

### **STEP 8: DataSync Service Validates and Stores**

```
DataSync Service:
  1. Receives file data from Agent
  2. Calculates checksums (MD5/SHA)
  3. Validates data integrity
  4. Writes to S3
  5. Verifies S3 write successful
  6. Reports back to Agent: "Received and stored ✓"
```

### **STEP 9: Agent Reports Status Back**

```
DataSync Agent → DataSync Service (HTTPS):
  "Completed! Sent 5 files, 250 MB"

DataSync Service → Lambda (API Response):
  "Task completed successfully"
```

### **STEP 10: Lambda Gets Result**

```python
# Lambda was waiting for response
response = datasync.describe_task_execution(TaskExecutionArn=execution_arn)

status = response['Status']  # 'SUCCESS'
files = response['FilesTransferred']  # 5
bytes_copied = response['BytesCopied']  # 262144000

print(f"✓ Copied {files} files ({bytes_copied} bytes)")
```

---

## Network Diagram: The Complete Picture

```
┌──────────────────────────────────────────────────────────────┐
│                    YOUR DATA CENTER                          │
│                   (On-Premises Network)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              NAS / NFS Storage                     │     │
│  │         /mydata/prod/icm/datain/poolData/          │     │
│  │              /2025/0805/                           │     │
│  │           • data.txt (50 MB)                       │     │
│  │           • file.dat (100 MB)                      │     │
│  │           • report.pdf (75 MB)                     │     │
│  └────────────────────┬─────────────────────────────┘     │
│                       │ (NFS Protocol)                      │
│                       │ Local network                       │
│                       │                                     │
│  ┌────────────────────▼──────────────────────────┐         │
│  │         EC2 Instance (t3.micro)               │         │
│  │                                               │         │
│  │  ┌────────────────────────────────────────┐   │         │
│  │  │    DataSync Agent (Software)           │   │         │
│  │  │  • Mounts: /mnt/nfs                    │   │         │
│  │  │  • Listens for commands from AWS       │   │         │
│  │  │  • Reads files from NFS mount          │   │         │
│  │  │  • Sends via HTTPS to AWS              │   │         │
│  │  │  • Reports progress                    │   │         │
│  │  │                                         │   │         │
│  │  │  Status: ✓ Running                     │   │         │
│  │  └────────────────┬──────────────────────┘   │         │
│  │                   │ HTTPS (port 443)         │         │
│  │                   │ Encrypted connection     │         │
│  │                   │                          │         │
│  └────────────────────┼──────────────────────────┘         │
│                       │                                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ INTERNET
                        │ HTTPS (TLS encrypted)
                        │ Very Secure
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     AWS CLOUD                               │
│                                                             │
│  ┌─────────────────────────────────┐                       │
│  │   AWS DataSync Service          │                       │
│  │  (Managed by Amazon)            │                       │
│  │                                 │                       │
│  │  Receives from:                 │                       │
│  │  • Lambda (start command)       │                       │
│  │  • DataSync Agent (file data)   │                       │
│  │                                 │                       │
│  │  Sends to:                      │                       │
│  │  • DataSync Agent (commands)    │                       │
│  │  • S3 (file storage)            │                       │
│  │  • Lambda (progress/status)     │                       │
│  │                                 │                       │
│  │  Does:                          │                       │
│  │  • Orchestrates transfer        │                       │
│  │  • Validates data integrity     │                       │
│  │  • Optimizes performance        │                       │
│  │  • Tracks progress              │                       │
│  └──────────────┬────────────────┬─┘                       │
│                 │                │                         │
│                 │                │                         │
│  ┌──────────────▼─┐    ┌────────▼────────────┐             │
│  │   Lambda       │    │   S3 Bucket         │             │
│  │   Function     │    │                     │             │
│  │                │    │  /2025/0805/        │             │
│  │  Orchestrates: │    │  • data.txt ✓       │             │
│  │  • Gets date   │    │  • file.dat ✓       │             │
│  │  • Calls API   │    │  • report.pdf ✓     │             │
│  │  • Monitors    │    │                     │             │
│  │  • Gets status │    │  Files stored       │             │
│  │                │    │  Backed up          │             │
│  └────────────────┘    │  Available 24/7     │             │
│                        └─────────────────────┘             │
│                                                             │
│  ┌─────────────────────────────────────────────┐           │
│  │        CloudWatch Logs                      │           │
│  │  (Monitoring & Logging)                     │           │
│  │                                             │           │
│  │  Logs from:                                 │           │
│  │  • Lambda execution                         │           │
│  │  • DataSync task progress                   │           │
│  │  • Errors (if any)                          │           │
│  │  • Performance metrics                      │           │
│  └─────────────────────────────────────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Timeline: 6 PM Execution

```
TIME        COMPONENT           ACTION
────────────────────────────────────────────────────────────
6:00:00 PM  EventBridge         Trigger Lambda
6:00:01 PM  Lambda              Start executing
6:00:02 PM  Lambda              Get today's date: 2025/0805
6:00:03 PM  Lambda              Call DataSync API
6:00:04 PM  DataSync Service    Receive command
6:00:05 PM  DataSync Service    Connect to Agent
6:00:06 PM  DataSync Agent      Receive command
6:00:07 PM  DataSync Agent      Connect to NFS
6:00:08 PM  DataSync Agent      List files in /2025/0805/
6:00:09 PM  DataSync Agent      Find 5 new files
6:00:10 PM  DataSync Agent      Start reading file 1
6:00:15 PM  DataSync Agent      Send file 1 to Service
6:00:18 PM  DataSync Service    Receive file 1
6:00:19 PM  DataSync Service    Write to S3
6:00:20 PM  DataSync Service    Verify file 1 in S3
...        (repeat for files 2-5)
6:02:30 PM  DataSync Agent      Send final file
6:02:35 PM  DataSync Service    All files stored
6:02:36 PM  DataSync Service    Send status to Lambda
6:02:37 PM  Lambda              Receive success response
6:02:38 PM  Lambda              Log results
6:02:39 PM  CloudWatch          Log entry recorded
6:02:40 PM  COMPLETE            ✓ All done!

Total time: ~2-3 minutes for 250 MB of files
```

---

## What Goes Wrong & Where

### **If NFS is unreachable:**
```
Lambda → DataSync Service → DataSync Agent → NFS
                                              ↓
                                         FAILS HERE
                                         (No connection)
Error propagates back:
  NFS → Agent → Service → Lambda → CloudWatch logs
  "Error: Unable to connect to NFS"
```

### **If DataSync Agent crashes:**
```
Lambda → DataSync Service → DataSync Agent
                                ↓
                           FAILS HERE
                           (No response)
Error:
  "Agent not responding"
  Service times out
  Lambda gets error
```

### **If S3 write fails:**
```
Agent → Service → S3
                   ↓
              FAILS HERE
              (Access denied)
Error:
  "S3 permission denied"
  Service can't write
  Agent stops sending
  Lambda gets error
```

---

## The Complete Data Journey

### **File: data.txt (50 MB)**

```
1. Location: /mydata/prod/icm/datain/poolData/2025/0805/data.txt
   Status: On NAS storage

2. NFS reads it
   Status: Data buffered

3. DataSync Agent buffers
   Status: In memory on EC2

4. Sends via HTTPS to AWS
   Status: In transit (encrypted)

5. DataSync Service receives
   Status: In AWS

6. DataSync Service validates
   Status: Checked (MD5 hash verified)

7. Written to S3
   Status: s3://your-bucket/2025/0805/data.txt

8. S3 stores with redundancy
   Status: Multiple copies, backed up

9. Available forever
   Status: Accessible 24/7
```

---

## Security: How Data is Protected

```
┌─────────────────────────────────────────────────────┐
│  STEP 1: NFS Read (On-Premises)                    │
│  • Local network (your data center)                │
│  • NFS protocol (standard)                         │
│  • No exposure to internet yet                     │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  STEP 2: HTTPS Transmission (Encrypted)            │
│  • TLS 1.2+ encryption                             │
│  • Port 443 (standard HTTPS)                       │
│  • Nobody can read the data in transit             │
│  • AWS certificate verified                        │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  STEP 3: S3 Storage (Encrypted & Redundant)        │
│  • Server-side encryption (AES-256)                │
│  • Multiple data center replicas                   │
│  • Access controlled by IAM                        │
│  • Audit logs in CloudTrail                        │
└─────────────────────────────────────────────────────┘
```

---

## Summary

| Component | Function | Connects To |
|-----------|----------|------------|
| **Lambda** | Orchestrator | DataSync Service (API) |
| **DataSync Service** | Manager | Lambda + DataSync Agent |
| **DataSync Agent** | Worker | DataSync Service + NFS |

**The Key Point:**
```
Lambda does NOT directly control the Agent.
Lambda tells the Service what to do.
The Service tells the Agent what to do.
The Agent does the actual file reading.
```

---

## Your Daily 6 PM Process

1. **6:00 PM** → EventBridge wakes Lambda
2. **Lambda** → Calls DataSync Service API
3. **Service** → Sends HTTPS command to Agent
4. **Agent** → Reads files from NFS
5. **Agent** → Sends files to Service via HTTPS
6. **Service** → Writes to S3
7. **Service** → Sends success to Lambda
8. **Lambda** → Logs result
9. **Done!** → Files in S3, ready to use

**Repeat every day at 6 PM automatically** ✓
