# Complete Setup (1-2 hours)

## Prerequisites

```bash
# Install AWS CLI
aws --version

# Configure credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-east-1
```

---

## STEP 1: Install DataSync Agent on EC2 (30 min)

### Launch EC2 Instance

1. AWS Console → EC2 → Launch Instance
2. Choose: Amazon Linux 2
3. Instance type: t3.micro (free tier)
4. Security group: Allow port 2049 (NFS) inbound from your network
5. Launch

### SSH Into EC2 and Install Agent

```bash
ssh ec2-user@your-ec2-public-ip

# Download and install DataSync agent
cd /opt
sudo wget https://s3.amazonaws.com/aws-datasync/latest/aws-datasync-agent-linux.tar.gz
sudo tar xzf aws-datasync-agent-linux.tar.gz
cd aws-datasync-agent
sudo ./install.sh

# Start the service
sudo systemctl start aws-datasync-agent
sudo systemctl enable aws-datasync-agent

# Verify it's running
sudo systemctl status aws-datasync-agent
# Should show: "active (running)"
```

### Mount Your NFS

```bash
# Create mount point
sudo mkdir -p /mnt/nfs

# Mount (replace YOUR_NAS_IP with actual IP)
sudo mount -t nfs YOUR_NAS_IP:/vol/xxx1nas456av45mir /mnt/nfs

# Verify
mount | grep nfs
ls /mnt/nfs
ls /mnt/nfs/2025/0805  # Should see your files
```

**If mount fails:**
- Check NAS IP is correct
- Check security group allows port 2049
- Check NAS export allows this IP

---

## STEP 2: Get DataSync Agent ARN

```bash
aws datasync list-agents --query 'Agents[0].AgentArn' --output text

# Copy this ARN, you'll need it in Step 3
# Example: arn:aws:datasync:us-east-1:123456789012:agent/abc123def456
```

---

## STEP 3: Create DataSync Locations

### Get Agent ARN From Step 2

```bash
# Define variables (replace with your values)
AGENT_ARN="arn:aws:datasync:us-east-1:123456789012:agent/abc123"
NAS_IP="192.168.1.100"  # Your actual NAS IP
AWS_ACCOUNT="123456789012"  # Your AWS account ID
```

### Create NFS Location

```bash
aws datasync create-location-nfs \
  --subdirectory /mnt/nfs \
  --server-hostname $NAS_IP \
  --on-prem-config AgentArns=$AGENT_ARN

# Save the LocationArn from output
# Example: arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123
# Store as: NFS_LOCATION_ARN
```

### Create S3 Location

First, create IAM role for DataSync:

```bash
# Create role
aws iam create-role \
  --role-name datasync-s3-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "datasync.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Add S3 permissions
aws iam put-role-policy \
  --role-name datasync-s3-role \
  --policy-name s3-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": "arn:aws:s3:::your-bucket/*"
    }]
  }'
```

Now create S3 location:

```bash
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::your-bucket \
  --s3-config BucketAccessRoleArn=arn:aws:iam::$AWS_ACCOUNT:role/datasync-s3-role

# Save the LocationArn from output
# Example: arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789
# Store as: S3_LOCATION_ARN
```

---

## STEP 4: Edit Lambda Function

Edit `daily_sync.py`:

```python
# Line 8-9, replace with your ARNs from Step 3:
NFS_LOCATION_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123'
S3_LOCATION_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789'
```

---

## STEP 5: Deploy Lambda Function

### Create IAM Role for Lambda

```bash
aws iam create-role \
  --role-name lambda-datasync-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Add DataSync permissions
aws iam put-role-policy \
  --role-name lambda-datasync-role \
  --policy-name datasync-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "datasync:CreateTask",
        "datasync:ListTasks",
        "datasync:StartTaskExecution",
        "datasync:DescribeTaskExecution"
      ],
      "Resource": "*"
    }]
  }'

# Add CloudWatch Logs permissions
aws iam put-role-policy \
  --role-name lambda-datasync-role \
  --policy-name logs-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }]
  }'
```

### Deploy Function

```bash
# Package
zip lambda.zip daily_sync.py

# Create function
aws lambda create-function \
  --function-name daily-nfs-sync \
  --runtime python3.11 \
  --role arn:aws:iam::$AWS_ACCOUNT:role/lambda-datasync-role \
  --handler daily_sync.lambda_handler \
  --zip-file fileb://lambda.zip \
  --timeout 900 \
  --memory-size 256
```

---

## STEP 6: Schedule Daily at 6 PM

### Create EventBridge Rule

```bash
# 6 PM UTC (adjust if you need different timezone)
aws events put-rule \
  --name daily-sync-6pm \
  --schedule-expression "cron(0 18 * * ? *)" \
  --state ENABLED
```

### Add Lambda Target

```bash
aws events put-targets \
  --rule daily-sync-6pm \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:$AWS_ACCOUNT:function:daily-nfs-sync"
```

### Grant Permission

```bash
aws lambda add-permission \
  --function-name daily-nfs-sync \
  --statement-id AllowEventBridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:$AWS_ACCOUNT:rule/daily-sync-6pm
```

---

## STEP 7: Test It

### Manual Trigger (Test)

```bash
aws lambda invoke \
  --function-name daily-nfs-sync \
  --payload '{}' \
  response.json

cat response.json
```

### Check Logs

```bash
aws logs tail /aws/lambda/daily-nfs-sync --follow
```

### Check S3

```bash
aws s3 ls s3://your-bucket/ --recursive
```

---

## Done!

Every day at 6 PM:
- Lambda wakes up
- Checks /yyyy/mmdd/ folder
- Copies new files to S3
- Done!

Monitor with CloudWatch logs:
```bash
aws logs tail /aws/lambda/daily-nfs-sync --follow
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent won't start | Check EC2 instance, verify agent service is running |
| Can't mount NFS | Check NAS IP, check security group allows 2049 |
| No files copied | Check /yyyy/mmdd/ folder exists and has files |
| Lambda fails | Check CloudWatch logs for error |
| EventBridge not triggering | Verify rule is ENABLED and Lambda has permission |
