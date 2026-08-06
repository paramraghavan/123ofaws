# Daily DataSync - Copy New Files from NFS to S3

**Copy files from on-premises NFS to AWS S3 every day at 6 PM**

---

## Your Setup

**Today:** Aug 5, 2025
**Check folder:** `/mydata/prod/icm/datain/poolData/2025/0805/`
**Schedule:** Every day at 6 PM
**Action:** Find new files → Send to S3

---

## How It Works

```
6:00 PM (Daily) → Lambda triggers → Checks /yyyy/mmdd/ folder → Finds new files → Sends to S3
```

---

## Step 1: Set Up DataSync Agent (One-time, 30 min)

### On EC2 (in your AWS account)

```bash
# SSH into EC2
ssh ec2-user@your-ec2-instance

# Install DataSync agent
cd /opt
sudo wget https://s3.amazonaws.com/aws-datasync/latest/aws-datasync-agent-linux.tar.gz
sudo tar xzf aws-datasync-agent-linux.tar.gz
cd aws-datasync-agent
sudo ./install.sh
sudo systemctl start aws-datasync-agent

# Mount your NFS (replace with your actual NAS IP)
sudo mount -t nfs 192.168.1.100:/vol/xxx1nas456av45mir /mnt/nfs

# Verify
ls /mnt/nfs
ls /mnt/nfs/2025/0805  # Should see your files
```

---

## Step 2: Create DataSync Locations (AWS CLI, 10 min)

```bash
# Get your EC2 agent ID
aws datasync list-agents --query 'Agents[0].AgentArn' --output text
# Save this as: AGENT_ARN

# Create NFS location
aws datasync create-location-nfs \
  --subdirectory /mnt/nfs \
  --server-hostname 10.0.0.50 \
  --on-prem-config AgentArns=arn:aws:datasync:us-east-1:123456789012:agent/abc123

# Save the output ARN as: NFS_LOCATION_ARN

# Create S3 location
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::your-bucket \
  --s3-config BucketAccessRoleArn=arn:aws:iam::123456789012:role/datasync-s3-role

# Save the output ARN as: S3_LOCATION_ARN
```

---

## Step 3: Deploy Lambda Function (5 min)

**Edit `daily_sync.py`:**
- Replace `NFS_LOCATION_ARN` with your NFS ARN
- Replace `S3_LOCATION_ARN` with your S3 ARN

**Deploy:**
```bash
zip lambda.zip daily_sync.py
aws lambda create-function \
  --function-name daily-nfs-sync \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/lambda-datasync-role \
  --handler daily_sync.lambda_handler \
  --zip-file fileb://lambda.zip \
  --timeout 900
```

---

## Step 4: Schedule Daily at 6 PM (5 min)

```bash
# Create EventBridge rule (6 PM UTC = 18:00)
aws events put-rule \
  --name daily-sync-6pm \
  --schedule-expression "cron(0 18 * * ? *)"

# Add Lambda as target
aws events put-targets \
  --rule daily-sync-6pm \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:daily-nfs-sync"

# Grant EventBridge permission
aws lambda add-permission \
  --function-name daily-nfs-sync \
  --statement-id AllowEventBridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:123456789012:rule/daily-sync-6pm
```

---

## That's It!

**Every day at 6 PM:**
- Lambda runs
- Checks `/yyyy/mmdd/` folder (today's date)
- Finds new files
- Sends to S3

---

## Check If It's Working

```bash
# View Lambda logs
aws logs tail /aws/lambda/daily-nfs-sync --follow

# Check S3
aws s3 ls s3://your-bucket/ --recursive
```

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `daily_sync.py` | Lambda function (copy files) |
| `ARCHITECTURE.md` | How it works (optional) |
| `SETUP.md` | Detailed setup (optional) |

---

## That's All You Need

✓ Copy files daily from NFS to S3
✓ Automatic at 6 PM
✓ New files only
✓ Done!
