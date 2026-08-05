# Deployment Instructions

## Prerequisites

```bash
pip install boto3
aws configure  # Set up your AWS credentials
```

## Option 1: One-Time Copy (Manual)

```bash
# 1. Update your ARNs in the script
nano copy_now.py
# Find these lines and update:
# NFS_LOCATION_ARN = 'arn:aws:datasync:...'
# S3_LOCATION_ARN = 'arn:aws:datasync:...'

# 2. Run it
python copy_now.py

# 3. Watch progress in terminal
# Done! Check S3 for your files
```

## Option 2: Daily Automatic Copy (Lambda)

### Step 1: Get Your ARNs

From Step 2 of SIMPLE_GUIDE.md, you should have:
- `NFS_ARN`: Your NFS location ARN
- `S3_ARN`: Your S3 location ARN

### Step 2: Deploy Lambda Function

```bash
# Package the function
zip lambda.zip lambda_daily_copy.py

# Create Lambda function
aws lambda create-function \
  --function-name daily-nfs-to-s3-copy \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-datasync-role \
  --handler lambda_daily_copy.lambda_handler \
  --zip-file fileb://lambda.zip \
  --timeout 900 \
  --environment Variables="{NFS_LOCATION_ARN=YOUR_NFS_ARN,S3_LOCATION_ARN=YOUR_S3_ARN}"

# Replace:
# - YOUR_ACCOUNT_ID: Your AWS account ID
# - YOUR_NFS_ARN: From Step 2 of SIMPLE_GUIDE.md
# - YOUR_S3_ARN: From Step 2 of SIMPLE_GUIDE.md
```

Example:
```bash
aws lambda create-function \
  --function-name daily-nfs-to-s3-copy \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/lambda-datasync-role \
  --handler lambda_daily_copy.lambda_handler \
  --zip-file fileb://lambda.zip \
  --timeout 900 \
  --environment Variables="{NFS_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123,S3_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789}"
```

### Step 3: Create EventBridge Trigger (Daily Schedule)

```bash
# Create rule to run daily at 2 AM UTC
aws events put-rule \
  --name daily-nfs-to-s3-copy \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED

# Add Lambda as target
aws events put-targets \
  --rule daily-nfs-to-s3-copy \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:daily-nfs-to-s3-copy"

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name daily-nfs-to-s3-copy \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:123456789012:rule/daily-nfs-to-s3-copy
```

### Step 4: Create IAM Role for Lambda

If you don't have `lambda-datasync-role` yet:

```bash
# Create role
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
        "datasync:DescribeTask",
        "datasync:StartTaskExecution",
        "datasync:DescribeTaskExecution"
      ],
      "Resource": "*"
    }]
  }'

# Add S3 permissions
aws iam put-role-policy \
  --role-name lambda-datasync-role \
  --policy-name s3-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
    }]
  }'

# Add CloudWatch Logs permission
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

---

## Verify It's Working

### Option 1: Manual Trigger (Test)

```bash
# Invoke Lambda manually to test
aws lambda invoke \
  --function-name daily-nfs-to-s3-copy \
  --payload '{}' \
  response.json

# Check response
cat response.json
```

### Option 2: Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/daily-nfs-to-s3-copy --follow
```

### Option 3: Check S3 for Files

```bash
# List files in S3
aws s3 ls s3://your-bucket-name/ --recursive
```

---

## Troubleshooting

### Lambda can't find DataSync

**Error**: `ResourceNotFoundException`

**Fix**: Check your ARNs are correct:
```bash
aws datasync list-locations
aws datasync describe-location-nfs --location-arn arn:aws:datasync:...
```

### Permission Denied on S3

**Error**: `AccessDenied`

**Fix**: Make sure Lambda role has S3 permissions:
```bash
aws iam get-role-policy \
  --role-name lambda-datasync-role \
  --policy-name s3-policy
```

### EventBridge not triggering Lambda

**Fix**: Check the rule is enabled:
```bash
aws events describe-rule --name daily-nfs-to-s3-copy
```

Should show `"State": "ENABLED"`

---

## Update Schedule

Want to change when copy runs? Update the cron expression:

```bash
# Change to 1 AM UTC instead of 2 AM
aws events put-rule \
  --name daily-nfs-to-s3-copy \
  --schedule-expression "cron(0 1 * * ? *)"
```

Cron format: `cron(minute hour day month day-of-week year)`

Examples:
- `cron(0 2 * * ? *)` - Every day at 2 AM UTC
- `cron(0 2 * * MON-FRI ? *)` - Every weekday at 2 AM UTC
- `cron(0 */6 * * ? *)` - Every 6 hours

---

## Monitor DataSync Tasks

```bash
# List all tasks
aws datasync list-tasks

# Get specific task details
aws datasync describe-task --task-arn arn:aws:datasync:...

# List recent executions
aws datasync list-task-executions --task-arn arn:aws:datasync:...

# Get execution details
aws datasync describe-task-execution --task-execution-arn arn:aws:datasync:...
```

---

## That's It!

Your files will now copy automatically every day at the scheduled time. 🎉

Check S3 to see your files appearing!
