# SFTP Server Monitoring with AWS - Complete Tutorial

## Overview

This directory contains **complete, production-ready guides** for monitoring third-party SFTP servers using AWS services.

### What You Can Do

✅ **Monitor SFTP Connection** - Know when connection fails
✅ **Track File Arrivals** - Alert when files arrive
✅ **Auto-Copy to S3** - Automatically copy files from SFTP to S3
✅ **Create Custom Metrics** - Track file counts, transfer speeds, etc.
✅ **Send Alerts** - Email, Slack, or SMS notifications

---

## The Guides

### 1. **README.md** (this file) - Navigation & Overview
Quick overview of all available guides, learning paths, and use cases

### 2. **sftp-to-s3-copy.md** - Auto-Copy SFTP Files to S3
**Best for:** Automatically monitoring and copying files from SFTP server to S3

**Topics covered:**
- Simple architecture diagrams (easy to understand)
- How the system works step-by-step
- Complete Lambda function code (production-ready)
- DynamoDB tracking (avoid copying files twice)
- Setup instructions (from scratch)
- Real-world examples with timelines
- Testing guide (verify each part works)
- Troubleshooting (common issues & solutions)

**What you'll learn:**
- ✅ How to use Paramiko library (SFTP connections)
- ✅ How to use AWS Lambda (serverless code)
- ✅ How to use S3 (cloud storage)
- ✅ How to use DynamoDB (tracking copied files)
- ✅ How to use Parameter Store (store credentials securely)

**Time to setup:** 30 minutes - 2 hours
**Cost:** ~$1-2/month
**Complexity:** Beginner-friendly

---

## Quick Start

### 📦 Auto-Copy SFTP Files to S3 (30 min - 2 hours)

→ Read: **sftp-to-s3-copy.md**

**What you get:**
- Lambda function that monitors SFTP server
- Automatically copies new files to S3
- Never copies the same file twice (uses DynamoDB)
- Complete setup instructions
- Real-world examples

**What happens:**
```
Every 5 minutes:
├─ Lambda checks SFTP server
├─ Finds new files (not copied before)
├─ Downloads from SFTP
├─ Uploads to S3
└─ Remembers the filename (in DynamoDB)
```

---

## Architecture at a Glance

```
Your SFTP Server
        │
        │ (Lambda checks every 5 min)
        ▼
    AWS Lambda ◄─── Credentials from Parameter Store
        │
        ├─→ CloudWatch Metrics
        │       │
        │       ▼
        │   CloudWatch Alarms ◄─── Triggers if thresholds breached
        │       │
        │       ▼
        │   SNS Notifications
        │       │
        │       ├─→ Email
        │       ├─→ Slack
        │       └─→ SMS
        │
        └─→ (Optional) Copy files to S3 + DynamoDB (tracking)
```

---

## Common Use Cases Covered

### ✅ "Auto-copy files from SFTP to S3"
**Where:** sftp-to-s3-copy.md
**Setup:** 30 min - 2 hours
**Cost:** ~$1-2/month

### ✅ "Monitor SFTP server"
**Where:** sftp-to-s3-copy.md (Lambda connects every 5 min)
**Setup:** Included in main setup
**Cost:** Included in total

### ✅ "Track which files were copied"
**Where:** sftp-to-s3-copy.md (uses DynamoDB)
**Setup:** Included in main setup
**Cost:** Included in total

### ✅ "Don't copy files twice"
**Where:** sftp-to-s3-copy.md (DynamoDB remembers)
**Setup:** Included in main setup
**Cost:** Included in total

---

## File Organization

```
monitoring/SFTP/
├── README.md                     ← Navigation & overview (You are here)
└── sftp-to-s3-copy.md            ← Complete auto-copy guide with diagrams
```

**Total:** 2 files, ~1,500 lines of comprehensive tutoring content

---

## Learning Path

### Step 1: Read This README (5 minutes)
Understand what you're building and what it costs

### Step 2: Read sftp-to-s3-copy.md (20-30 minutes)
- Understand the architecture with diagrams
- Learn how the Lambda function works
- See real-world examples

### Step 3: Follow Setup Instructions (30 minutes - 1 hour)
- Create DynamoDB table
- Store SFTP credentials
- Deploy Lambda function
- Test it works

### Step 4: Monitor & Verify (10-15 minutes)
- Check CloudWatch logs
- Verify files copied to S3
- Test with new files

**Total time:** 1-2 hours
**Result:** Automated SFTP monitoring system ✅

---

## Key Concepts

### Paramiko
Python library for SFTP connections - lets Lambda talk to your SFTP server

### Lambda
Serverless compute - runs your code without managing servers

### CloudWatch
AWS monitoring service - tracks metrics and stores alarms

### Parameter Store
Encrypted vault - stores SFTP credentials securely

### DynamoDB
Database - remembers which files we've already copied (for SFTP→S3)

### SNS
Notification service - sends email, SMS, Slack messages

---

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| Lambda | $0.20/month | ~1,000 invocations |
| CloudWatch Metrics | $0.10/month | 1 metric |
| CloudWatch Logs | $0.50/month | Lambda logs |
| DynamoDB | $0.25/month | If using auto-copy |
| SNS | Free | First 1,000 alerts free |
| **Total** | **$1-2/month** | Extremely cheap! |

---

## Getting Started

### Step-by-Step:

1. **Read README.md** (this file)
   - Understand what you're building
   - Review cost breakdown
   - Know how long setup takes

2. **Read sftp-to-s3-copy.md**
   - Study the diagrams
   - Understand Lambda code
   - Follow the setup instructions

3. **Set up AWS Resources**
   - Create DynamoDB table
   - Store SFTP credentials
   - Create S3 bucket

4. **Deploy Lambda Function**
   - Follow exact commands in guide
   - Test manually first
   - Verify files copy correctly

5. **Monitor & Verify**
   - Check CloudWatch logs
   - Verify files in S3
   - Add new test files

6. **Optimize** (optional)
   - Adjust timing (currently every 5 min)
   - Add file filtering
   - Add error notifications

---

## Troubleshooting

**All troubleshooting guides are in: sftp-to-s3-copy.md**

| Problem | Where to Find Solution |
|---------|---------|
| Can't connect to SFTP | sftp-to-s3-copy.md → Troubleshooting section |
| Lambda timeout | sftp-to-s3-copy.md → Common Issues & Solutions |
| Files not copying to S3 | sftp-to-s3-copy.md → Common Issues & Solutions |
| DynamoDB errors | sftp-to-s3-copy.md → Testing section |

---

## Getting Help

Each guide has:
- ✅ Complete code examples
- ✅ Step-by-step instructions
- ✅ Troubleshooting section
- ✅ Real-world scenarios
- ✅ Best practices

**Start with the guide matching your use case!**

---

## Summary

You have **one comprehensive, production-ready guide** for auto-copying SFTP files to S3:

### sftp-to-s3-copy.md
- ✅ Simple diagrams explaining how it works
- ✅ Complete Lambda code (copy & paste ready)
- ✅ Step-by-step setup instructions
- ✅ Real-world examples with timelines
- ✅ Troubleshooting section
- ✅ Testing guide

**Follow this guide and you're done!** ✅

**Cost:** ~$1-2/month
**Setup Time:** 30 min - 2 hours
**Result:** Professional-grade SFTP monitoring system with auto-copy to S3
