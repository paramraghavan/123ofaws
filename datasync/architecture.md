# Simple Architecture Diagram

## The Complete Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR COMPANY NETWORK                             │
│                          (On-Premises)                                   │
│                                                                           │
│    ┌──────────────────┐                                                  │
│    │   NAS Storage    │                                                  │
│    │  /vol/data/      │                                                  │
│    │  Files here      │                                                  │
│    └────────┬─────────┘                                                  │
│             │ (NFS mount)                                                │
│             │                                                            │
│    ┌────────▼──────────────────┐                                         │
│    │   EC2 Instance            │                                         │
│    │  (small Linux server)      │                                        │
│    │                            │                                        │
│    │  - DataSync Agent running  │                                        │
│    │  - /mnt/nfs mounted        │                                        │
│    │  - Port 443 to AWS         │                                        │
│    │                            │                                        │
│    └────────┬───────────────────┘                                        │
│             │                                                            │
└─────────────┼────────────────────────────────────────────────────────────┘
              │
              │ (HTTPS, port 443)
              │ (Agent talks to AWS)
              │
┌─────────────▼────────────────────────────────────────────────────────────┐
│                              AWS CLOUD                                    │
│                                                                           │
│    ┌──────────────────────────────┐                                      │
│    │    DataSync Service          │                                      │
│    │                              │                                      │
│    │  Task:                       │                                      │
│    │  - Reads from NFS via Agent  │                                      │
│    │  - Copies to S3              │                                      │
│    │  - Verifies data             │                                      │
│    └────────┬─────────────────────┘                                      │
│             │                                                            │
│    ┌────────▼──────────────────┐                                         │
│    │   S3 Bucket               │                                         │
│    │  s3://my-bucket/          │                                         │
│    │                            │                                        │
│    │  ✓ Files copied here       │                                        │
│    │  ✓ Stored in cloud         │                                        │
│    │  ✓ Backed up & protected   │                                        │
│    └────────────────────────────┘                                        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## How It Works (Step by Step)

### Step 1: Install DataSync Agent
```
You launch EC2 instance → Install DataSync Agent → Agent runs on EC2
```

### Step 2: Mount NFS
```
EC2 connects to your NAS → NFS mounted at /mnt/nfs → Files are accessible
```

### Step 3: Tell DataSync About Locations
```
AWS DataSync knows about:
  - Where to copy FROM (NFS via EC2 agent)
  - Where to copy TO (S3 bucket)
```

### Step 4: Run the Copy Task
```
DataSync reads files from NFS → Copies across network → Stores in S3
```

### Step 5: Monitor Progress
```
You check CloudWatch logs → See files being transferred → Task completes
```

---

## With Automation (Lambda)

```
┌─────────────────────────┐
│   EventBridge Rule      │
│   "Run daily at 2 AM"   │
└────────────┬────────────┘
             │
             │ (Trigger)
             │
┌────────────▼────────────┐
│  Lambda Function        │
│  "Start the copy task"  │
└────────────┬────────────┘
             │
             │ (Call DataSync API)
             │
┌────────────▼────────────┐
│  DataSync Copies Files  │
│  (same as manual)       │
└────────────┬────────────┘
             │
             │ (Files stored)
             │
┌────────────▼────────────┐
│  S3 Bucket              │
│  Files stored & ready   │
└─────────────────────────┘
```

---

## Data Flow

```
1. Morning: EventBridge wakes up Lambda

2. Lambda: "Hi DataSync, please copy files"

3. DataSync Agent: "I'll connect to NFS and get the files"

4. NFS: "Here are the new files"

5. DataSync: "Copying to S3..."

6. S3: "Files received and stored"

7. Lambda: "Great! Copy complete" (sends you a status)

8. Next day: Repeat!
```

---

## Key Components

| Component | What It Does | Where |
|-----------|-------------|-------|
| **NAS/NFS** | Stores your files | Your office |
| **EC2 Instance** | Runs DataSync Agent | AWS cloud |
| **DataSync Agent** | Connects to NFS, copies files | On the EC2 |
| **DataSync Service** | Orchestrates the copy | AWS managed |
| **S3 Bucket** | Stores copied files | AWS cloud |
| **Lambda** (optional) | Schedules daily copies | AWS managed |
| **EventBridge** (optional) | Triggers Lambda daily | AWS managed |

---

## Network Connectivity

```
Your Network          AWS Network
───────────────────────────────

┌──────────┐          ┌────────────┐
│   NAS    │ (NFS)    │ DataSync   │
├──────────┤◄────────►├────────────┤
│   EC2    │  port    │ Service    │
│ (Agent)  │  2049    └────────────┘
└──────────┘                │
                           │ (HTTPS)
                           │ port 443
                           │
                    ┌──────▼─────┐
                    │  S3 Bucket │
                    └────────────┘
```

---

## What AWS DataSync Does For You

✅ **Automatic retries** - If copy fails, it retries automatically
✅ **Data validation** - Verifies files copied correctly
✅ **Optimized transfer** - Uses bandwidth efficiently
✅ **Incremental copy** - Only copies new/changed files
✅ **Parallel transfers** - Copies multiple files at once
✅ **Monitoring** - Built-in logging and metrics

---

## Why Not Just Sync with S3 CLI?

DataSync is better because:
- ✅ Reliable for large files
- ✅ Handles partial transfers
- ✅ Built-in validation
- ✅ Better performance
- ✅ Easier to automate
- ✅ AWS manages the heavy lifting

---

## Cost Breakdown

| Service | Cost | Details |
|---------|------|---------|
| DataSync | $0.0125/GB | Only pay for transferred data |
| S3 Storage | $0.023/GB/month | Standard storage class |
| EC2 (agent) | $~10-50/month | Small t3.micro instance |
| Lambda | Free* | ~1 execution/day, free tier |
| Total | Low | Typically $100-300/month for small migration |

*AWS Free Tier covers most Lambda usage

---

## Simple Checklist

✓ Have NAS that you can access?
✓ Have AWS account?
✓ Can launch EC2 in same network as NAS?
✓ Have S3 bucket?
✓ Ready to copy files?

If yes to all → You're ready to go!

Start with: `SIMPLE_GUIDE.md`
