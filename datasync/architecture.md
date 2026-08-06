# How It Works

## Your Daily Flow

```
6:00 PM Every Day
    ↓
EventBridge wakes up Lambda
    ↓
Lambda checks: What's today's date?
    ↓
Today = 2025/0805 → Check /2025/0805/ folder
    ↓
DataSync Agent connects to NFS
    ↓
NFS: "Here are new files in /2025/0805/"
    ↓
DataSync copies them to S3
    ↓
S3: "Files received and stored"
    ↓
Lambda: "Done! ✓"
```

---

## Architecture

```
Your Brownfield Server (On-Premises)
┌─────────────────────┐
│   NFS Storage       │
│ /yyyy/mmdd/files    │
│  2025/0805/data.txt │
└──────────┬──────────┘
           │
           │ (NFS mount)
           │
┌──────────▼────────────────┐
│  EC2 Instance             │
│  DataSync Agent running   │
│  Mounts: /mnt/nfs         │
└──────────┬────────────────┘
           │
           │ (HTTPS, port 443)
           │
┌──────────▼────────────────┐
│  AWS DataSync Service     │
│  Copies files             │
└──────────┬────────────────┘
           │
           │
┌──────────▼────────────────┐
│  S3 Bucket                │
│  Files stored here ✓      │
└───────────────────────────┘
```

---

## What Happens at 6 PM

```
EventBridge (AWS Clock)
    │
    └─→ "It's 6 PM, trigger Lambda!"
         │
         └─→ Lambda Function Runs
              │
              ├─→ Get today's date: Aug 5, 2025
              │
              ├─→ Format as: 2025/0805
              │
              ├─→ Check /mydata/prod/icm/datain/poolData/2025/0805/
              │
              ├─→ DataSync Agent connects to NFS
              │
              ├─→ Find new files
              │
              └─→ Copy to S3
                  │
                  └─→ DONE! Next day at 6 PM, repeat
```

---

## The Three AWS Services Working Together

| Service | What It Does |
|---------|-------------|
| **DataSync Agent** | Lives on EC2, connects to your NFS |
| **DataSync Service** | Handles the actual file copy |
| **Lambda** | Runs the task every day at 6 PM |
| **EventBridge** | "Cron job" that triggers Lambda at 6 PM |
| **S3** | Stores your files in cloud |

---

## File Path Mapping

```
NFS Source:
  /mydata/prod/icm/datain/poolData/2025/0805/data.txt

S3 Destination:
  s3://your-bucket/2025/0805/data.txt
```

---

## What Happens If...

**New files added to /2025/0805/?**
→ Next 6 PM run, they get copied to S3

**No new files?**
→ Nothing happens (no wasted copy)

**Files already exist in S3?**
→ They get overwritten (latest version)

**Copy fails?**
→ Lambda returns error, you get logs in CloudWatch

---

## Costs

- DataSync: $0.0125 per GB transferred
- S3: $0.023 per GB per month (storage)
- Lambda: Free (< 1 minute/day)
- **Total**: Very cheap (~$1-10/month for typical usage)

---

## Security

- EC2 agent connects via HTTPS
- Data encrypted in transit
- NFS stays on-premises (only copies over)
- S3 can be encrypted
- IAM controls access
