# SFTP to S3: Auto-Copy Files - Beginner's Guide

## What You're Building

Imagine you have a mailbox (SFTP server) where files arrive. You want AWS to:
1. **Check the mailbox** every 5 minutes
2. **Find new files** (ones that arrived since last check)
3. **Copy them to S3** (your cloud storage)
4. **Remember what we copied** (don't copy twice)

That's exactly what this does! ✅

---

## The Simple Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SFTP TO S3 AUTO-COPY SYSTEM                  │
└─────────────────────────────────────────────────────────────────┘

TIME: Every 5 minutes
      │
      ▼
┌─────────────────────────────┐
│  CloudWatch Events Rule     │
│  (Trigger schedule)         │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│   AWS Lambda Function       │ ← Your code runs here
│                             │
│  1. Connect to SFTP         │
│  2. List files              │
│  3. Check if NEW            │
│  4. Download from SFTP      │
│  5. Upload to S3            │
│  6. Record filename         │
└─────────┬───────────────────┘
          │
        ┌─┴─────────────────────────┬──────────────┐
        │                           │              │
        ▼                           ▼              ▼
   ┌────────────┐            ┌──────────┐    ┌─────────┐
   │ SFTP       │            │ S3       │    │DynamoDB │
   │ Server     │            │ Bucket   │    │(Tracking)
   │            │            │          │    │         │
   │file1.txt ──┼──────────→ │file1.txt │    │file1 ✓  │
   │file2.csv ──┼──────────→ │file2.csv │    │file2 ✓  │
   │file3.json ─┼──────────→ │file3.json│    │file3 ✓  │
   └────────────┘            └──────────┘    └─────────┘
   (Source)                   (Destination)  (Memory)

   ▲ Check here              ▼ Copy here       ▼ Remember
   (Every 5 min)                              what we copied
```

---

## How It Works - Step by Step

### Step 1: Lambda Wakes Up ⏰

Every 5 minutes, CloudWatch Events rule triggers Lambda function

```
Time: 5:00 PM → Lambda starts
Time: 5:05 PM → Lambda runs again
Time: 5:10 PM → Lambda runs again
...and so on
```

### Step 2: Connect to SFTP Server 🔌

Lambda connects to your SFTP server using credentials from Parameter Store

```python
ssh.connect('sftp.example.com', username='user', password='pass')
sftp = ssh.open_sftp()
files = sftp.listdir()  # Get list of files
# Returns: ['file1.txt', 'file2.csv', 'file3.json']
```

### Step 3: Check Which Files Are New 📝

Lambda remembers which files it already copied (using DynamoDB table)

```
Files on SFTP server:
  ├─ file1.txt     ← Already copied? Check DynamoDB → YES, skip
  ├─ file2.csv     ← Already copied? Check DynamoDB → YES, skip
  ├─ file3.json    ← Already copied? Check DynamoDB → NO, copy!
  └─ file4.xlsx    ← Already copied? Check DynamoDB → NO, copy!

Files to copy: file3.json, file4.xlsx
```

### Step 4: Copy New Files to S3 📦

For each NEW file:
1. Download from SFTP
2. Upload to S3
3. Remember that we copied it

```python
# Download from SFTP
sftp.get('file3.json', '/tmp/file3.json')

# Upload to S3
s3.upload_file('/tmp/file3.json', 'my-bucket', 'file3.json')

# Remember (store in DynamoDB)
dynamodb.put_item(
    TableName='copied-files',
    Item={'filename': 'file3.json', 'copied_at': '2024-01-06'}
)
```

### Step 5: Repeat ♻️

In 5 minutes, Lambda runs again and repeats the process

```
Second run (5:05 PM):
  - Check SFTP for new files
  - file3.json, file4.xlsx already in DynamoDB → skip
  - file5.pdf is new → copy it!
  - Remember file5.pdf
```

---

## The Architecture (Simple Version)

```
SFTP Server           AWS Lambda            AWS Services
(External)            (Your Code)           (Managed)

    │                     │                      │
    ├─ file1.txt         │                      │
    ├─ file2.csv         │                      │
    ├─ file3.json ───────┼──→ Check SFTP        │
    ├─ file4.xlsx        │    List files        │
    └─ file5.pdf         │    Compare with      │
                         │    DynamoDB          │
                         │         │             │
                         │         ├──→ Download file
                         │         │         │
                         │         │         ├──→ Upload to S3
                         │         │         │
                         │         ├──→ Save to DynamoDB
                         │         │         │
                         └─────────┴─────────┘
                         (Process every 5 min)
```

---

## What You Need (Simple List)

### AWS Services (already exist, just configure):
1. ✅ **Lambda** - Runs the copy code
2. ✅ **CloudWatch Events** - Triggers Lambda every 5 minutes
3. ✅ **S3 Bucket** - Where files get copied
4. ✅ **DynamoDB Table** - Remember copied files
5. ✅ **Parameter Store** - Store SFTP credentials
6. ✅ **IAM Role** - Permissions for Lambda

### Code:
- ✅ Python + Paramiko (SFTP library)
- ✅ Boto3 (AWS library)

---

## Complete Lambda Function

```python
import paramiko
import boto3
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
ssm = boto3.client('ssm')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

SFTP_TABLE = dynamodb.Table('copied-files')
S3_BUCKET = 'my-bucket'

def lambda_handler(event, context):
    """
    Main function: Check SFTP, copy new files to S3
    """

    try:
        # 1. Get SFTP credentials
        hostname = ssm.get_parameter(Name='/sftp/hostname', WithDecryption=True)['Parameter']['Value']
        username = ssm.get_parameter(Name='/sftp/username', WithDecryption=True)['Parameter']['Value']
        password = ssm.get_parameter(Name='/sftp/password', WithDecryption=True)['Parameter']['Value']

        # 2. Connect to SFTP
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=10)
        sftp = ssh.open_sftp()

        logger.info("✅ Connected to SFTP server")

        # 3. List files on SFTP
        files = sftp.listdir()
        logger.info(f"📁 Found {len(files)} files on SFTP server")

        copied_count = 0

        # 4. For each file: check if already copied
        for filename in files:
            # Skip directories
            if is_directory(sftp, filename):
                continue

            # Check if we already copied this file
            if file_already_copied(filename):
                logger.info(f"⏭️  Skipping {filename} (already copied)")
                continue

            # File is new! Copy it
            logger.info(f"📦 Copying {filename} to S3...")

            try:
                # Download from SFTP to Lambda temp storage
                local_path = f'/tmp/{filename}'
                sftp.get(filename, local_path)
                logger.info(f"   ✓ Downloaded {filename}")

                # Upload to S3
                s3.upload_file(local_path, S3_BUCKET, filename)
                logger.info(f"   ✓ Uploaded {filename} to S3")

                # Remember that we copied this file
                mark_file_as_copied(filename)
                logger.info(f"   ✓ Recorded {filename} in DynamoDB")

                copied_count += 1

            except Exception as e:
                logger.error(f"   ❌ Error copying {filename}: {str(e)}")

        # Close connections
        sftp.close()
        ssh.close()

        logger.info(f"✅ Copy job complete! Copied {copied_count} new files")

        return {
            'statusCode': 200,
            'body': f'Successfully copied {copied_count} files'
        }

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

def is_directory(sftp, filename):
    """Check if file is actually a directory"""
    try:
        sftp.stat(filename).st_mode
        import stat
        mode = sftp.stat(filename).st_mode
        return stat.S_ISDIR(mode)
    except:
        return False

def file_already_copied(filename):
    """Check DynamoDB: have we already copied this file?"""
    try:
        response = SFTP_TABLE.get_item(Key={'filename': filename})
        return 'Item' in response
    except:
        return False

def mark_file_as_copied(filename):
    """Record in DynamoDB that we copied this file"""
    SFTP_TABLE.put_item(Item={
        'filename': filename,
        'copied_at': datetime.now().isoformat(),
        'status': 'completed'
    })
```

---

## Setup Instructions (Quick Version)

### 1. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name copied-files \
  --attribute-definitions AttributeName=filename,AttributeType=S \
  --key-schema AttributeName=filename,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 2. Store SFTP Credentials

```bash
aws ssm put-parameter --name /sftp/hostname --value "sftp.example.com" --type String
aws ssm put-parameter --name /sftp/username --value "user" --type String
aws ssm put-parameter --name /sftp/password --value "password" --type SecureString
```

### 3. Create S3 Bucket

```bash
aws s3 mb s3://my-bucket-for-copied-files
```

### 4. Deploy Lambda Function

Save the code above as `lambda_function.py`, then:

```bash
# Install dependencies
pip install paramiko boto3 -t .

# Create zip
zip -r function.zip .

# Create Lambda function
aws lambda create-function \
  --function-name sftp-to-s3-copy \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 512
```

### 5. Create CloudWatch Events Rule

```bash
# Create rule (trigger every 5 minutes)
aws events put-rule \
  --name sftp-to-s3-copy-schedule \
  --schedule-expression 'rate(5 minutes)'

# Add Lambda as target
aws events put-targets \
  --rule sftp-to-s3-copy-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:sftp-to-s3-copy"

# Allow CloudWatch to invoke Lambda
aws lambda add-permission \
  --function-name sftp-to-s3-copy \
  --statement-id AllowCloudWatchInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:ACCOUNT_ID:rule/sftp-to-s3-copy-schedule
```

### 6. Create IAM Role with Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/sftp/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket-for-copied-files/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/copied-files"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

## Real-World Example: Blacknight Files

Imagine files arrive at Blacknight SFTP server at these times:

```
Timeline:
─────────────────────────────────────────────────────────

5:00 PM: Lambda checks SFTP
         Files found: data-2024-01-06.csv
         → Not in DynamoDB yet
         → Copy to S3 ✓
         → Remember it

5:05 PM: Lambda checks SFTP
         Files found: data-2024-01-06.csv, new-file.json
         → data-2024-01-06.csv in DynamoDB (skip)
         → new-file.json not in DynamoDB
         → Copy to S3 ✓
         → Remember it

5:10 PM: Lambda checks SFTP
         Files found: data-2024-01-06.csv, new-file.json, report.xlsx
         → Both old files in DynamoDB (skip)
         → report.xlsx is new
         → Copy to S3 ✓
         → Remember it

Result:
├─ S3 Bucket contains:
│  ├─ data-2024-01-06.csv
│  ├─ new-file.json
│  └─ report.xlsx
│
└─ DynamoDB remembers all 3 files copied
```

---

## Key Concepts Explained Simply

### Why Use DynamoDB?

Without DynamoDB:
```
Problem: Lambda has no memory!
Every 5 minutes it runs fresh
Without tracking, it would copy the same file 288 times per day! 😱
```

With DynamoDB:
```
✅ Lambda remembers: "I already copied file1.txt"
✅ Won't copy twice
✅ Cheap ($1/month for storage)
✅ Fast lookup
```

### Why Use Parameter Store?

Without Parameter Store:
```
❌ Bad: Password hardcoded in Lambda code
password = "MySecurePassword123"  // VISIBLE TO ANYONE!
```

With Parameter Store:
```
✅ Good: Password stored encrypted in AWS
password = ssm.get_parameter(Name='/sftp/password')
// Only Lambda with IAM permission can access
```

### Why Every 5 Minutes?

```
Every 5 min = 288 times per day
           = $0.20/month (cheaper than coffee!)
           = ~17 seconds per check

More frequent (1 min) = More cost, less benefit
Less frequent (hourly) = Might miss files
5 minutes = Sweet spot ✅
```

---

## Flow Diagram (Detailed)

```
START (Every 5 minutes)
│
├─ Get SFTP credentials from Parameter Store
│  └─→ Encrypted, secure
│
├─ Connect to SFTP server
│  └─→ If fails → Log error → Stop
│
├─ List all files on SFTP
│  └─→ Returns: ['file1.txt', 'file2.csv', ...]
│
├─ For each file:
│  │
│  ├─ Is it a directory?
│  │  └─→ YES: Skip
│  │  └─→ NO: Continue
│  │
│  ├─ Check DynamoDB: Did we already copy this?
│  │  └─→ YES: Skip to next file
│  │  └─→ NO: Continue
│  │
│  ├─ Download file from SFTP
│  │  └─→ If fails: Log error → Continue to next file
│  │  └─→ Success: Continue
│  │
│  ├─ Upload file to S3
│  │  └─→ If fails: Log error → Continue to next file
│  │  └─→ Success: Continue
│  │
│  └─ Save filename in DynamoDB
│     └─→ Remember: "We copied this file"
│
├─ Close SFTP connection
│
└─ Done! Wait 5 minutes for next run
```

---

## Testing This Locally

### Test 1: Can Lambda connect to SFTP?

```python
# In Lambda or EC2
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('sftp.example.com', username='user', password='pass')
    print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
```

### Test 2: Can Lambda list files?

```python
sftp = ssh.open_sftp()
files = sftp.listdir()
print(f"Files: {files}")
```

### Test 3: Can Lambda write to DynamoDB?

```python
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('copied-files')
table.put_item(Item={'filename': 'test.txt'})
print("✅ DynamoDB write successful!")
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Connection timeout" | Network blocked | Check security groups, IP whitelisting |
| "Authentication failed" | Wrong credentials | Verify in Parameter Store |
| "File copied multiple times" | Missing DynamoDB table | Create DynamoDB table |
| "S3 upload fails" | Lambda no S3 permission | Add `s3:PutObject` to IAM role |
| "Lambda timeout" | Files too large | Increase Lambda timeout to 300s |

---

## Next Steps

1. ✅ Understand the diagram (you now do!)
2. ✅ Set up DynamoDB table (5 minutes)
3. ✅ Store SFTP credentials (5 minutes)
4. ✅ Deploy Lambda function (10 minutes)
5. ✅ Test manually (5 minutes)
6. ✅ Create CloudWatch rule (5 minutes)
7. ✅ Monitor logs (ongoing)

**Total setup time: ~30 minutes** ⚡

---

## Summary

```
WHAT:   Automatically copy files from SFTP server to S3
WHERE:  AWS Lambda (serverless)
WHEN:   Every 5 minutes
HOW:    Check SFTP → Compare with DynamoDB → Copy new files → Remember
COST:   ~$0.50-1/month
RESULT: Files in S3, no manual work needed ✅
```

This is the simplest, cheapest way to do SFTP-to-S3 copying on AWS! 🚀
