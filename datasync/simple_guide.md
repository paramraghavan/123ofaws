# Simple DataSync Solution - Copy NFS to S3

**5-Minute Understanding, 1-Hour Setup**

---

## What is DataSync?

AWS DataSync is a service that automatically copies files from your on-premises storage to AWS S3.

**Your Setup:**
```
Your Company Server (NFS)  →  DataSync Agent (EC2)  →  AWS S3
     /mydata/data/             Copy tool                Cloud storage
```

---

## 3 Simple Steps

### Step 1: Install Agent on EC2

You need a small EC2 instance that can reach your NFS server.

```bash
# On the EC2 instance:
ssh ec2-user@your-ec2-instance

# Install DataSync Agent
cd /opt
sudo wget https://s3.amazonaws.com/aws-datasync/latest/aws-datasync-agent-linux.tar.gz
sudo tar xzf aws-datasync-agent-linux.tar.gz
cd aws-datasync-agent
sudo ./install.sh

# Start it
sudo systemctl start aws-datasync-agent

# Mount your NFS
sudo mount -t nfs your-nas-ip:/vol/data /mnt/nfs
```

**That's it for Step 1!**

---

### Step 2: Tell DataSync Where to Copy From/To

Use AWS CLI (or console):

```bash
# Tell DataSync where your NFS is
aws datasync create-location-nfs \
  --subdirectory /mnt/nfs \
  --server-hostname 10.0.0.50 \
  --on-prem-config AgentArns=arn:aws:datasync:us-east-1:123456789012:agent/12345678

# Get the ARN from the output, save it as: NFS_ARN=arn:aws:datasync:...

# Tell DataSync where to copy files (S3)
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::my-data-bucket \
  --s3-config BucketAccessRoleArn=arn:aws:iam::123456789012:role/datasync-s3-role

# Get the ARN from the output, save it as: S3_ARN=arn:aws:datasync:...
```

**That's it for Step 2!**

---

### Step 3: Copy Files

**Option A: One-Time Copy (Manual)**

```python
# File: copy_now.py
import boto3

datasync = boto3.client('datasync', region_name='us-east-1')

# Paste your ARNs from Step 2
NFS_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123'
S3_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789'

# Create task (defines what to copy)
task = datasync.create_task(
    SourceLocationArn=NFS_ARN,
    DestinationLocationArn=S3_ARN,
    Name='NFS-to-S3-Copy'
)

# Start copying
execution = datasync.start_task_execution(TaskArn=task['TaskArn'])

print(f"Copying files... Task: {execution['TaskExecutionArn']}")
print("Check AWS Console > DataSync > Task Executions to see progress")
```

**Run it:**
```bash
pip install boto3
python copy_now.py
```

**Option B: Automatic Daily Copy (Lambda)**

```python
# File: lambda_handler.py
import boto3
import time

datasync = boto3.client('datasync')

NFS_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123'
S3_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789'

def lambda_handler(event, context):
    # Create or reuse task
    tasks = datasync.list_tasks()['Tasks']
    
    task_arn = None
    for t in tasks:
        if t['Name'] == 'Daily-Copy':
            task_arn = t['TaskArn']
            break
    
    if not task_arn:
        task = datasync.create_task(
            SourceLocationArn=NFS_ARN,
            DestinationLocationArn=S3_ARN,
            Name='Daily-Copy'
        )
        task_arn = task['TaskArn']
    
    # Start the copy
    exec_resp = datasync.start_task_execution(TaskArn=task_arn)
    exec_arn = exec_resp['TaskExecutionArn']
    
    # Wait for it to finish
    while True:
        status = datasync.describe_task_execution(TaskExecutionArn=exec_arn)
        
        if status['Status'] == 'SUCCESS':
            return {
                'statusCode': 200,
                'message': f"Copied {status.get('FilesTransferred', 0)} files"
            }
        
        if status['Status'] == 'FAILED':
            return {
                'statusCode': 500,
                'message': f"Copy failed: {status.get('ErrorCode')}"
            }
        
        time.sleep(5)
```

**Deploy to Lambda:**
```bash
# Create function
zip lambda.zip lambda_handler.py
aws lambda create-function \
  --function-name daily-copy \
  --runtime python3.11 \
  --role arn:aws:iam::account:role/lambda-datasync-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda.zip

# Make it run daily (2 AM UTC)
aws events put-rule --name daily-copy-rule \
  --schedule-expression "cron(0 2 * * ? *)"

aws events put-targets --rule daily-copy-rule \
  --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:daily-copy"
```

**That's it for Step 3!**

---

## Check If It's Working

### View S3 Files
```bash
aws s3 ls s3://my-data-bucket/ --recursive
```

### View Task Status
```bash
# List all copy tasks
aws datasync list-tasks

# Get details
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:...
```

---

## Common Issues

| Problem | Fix |
|---------|-----|
| "Can't reach NFS" | Check EC2 security group allows port 2049 |
| "Agent not found" | Check agent is running: `sudo systemctl status aws-datasync-agent` |
| "S3 access denied" | Add S3 permissions to Lambda role |
| "No files copied" | Check NFS path exists and has files |

---

## That's All!

You now have a working solution:

✅ Files copy from NFS to S3
✅ Runs automatically daily
✅ AWS handles the heavy lifting
✅ Simple to monitor

---

## Next: Make It Production-Ready

1. **Add IAM roles** (from IAM section below)
2. **Add error handling** (email on failure)
3. **Monitor CloudWatch** (set up alarms)
4. **Test with small data** first

---

## IAM Roles Needed

### For Lambda

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "datasync:CreateTask",
        "datasync:ListTasks",
        "datasync:StartTaskExecution",
        "datasync:DescribeTaskExecution"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::my-data-bucket/*"
    }
  ]
}
```

### For DataSync Agent (EC2)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["datasync:DescribeAgent"],
      "Resource": "*"
    }
  ]
}
```

---

## Questions?

- **Why DataSync?** Because it handles retries, checks for errors, and optimizes performance automatically
- **Why not just AWS CLI?** DataSync is more reliable for large files and handles partial copies
- **How much does it cost?** ~$0.0125 per GB transferred (very cheap)
- **How long to set up?** About 1-2 hours total

Done! Your files will now copy automatically. 🚀
