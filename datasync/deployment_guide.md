# Deployment Guide - DataSync Orchestrator

## Quick Start (5 minutes)

### Prerequisites
- AWS Account with appropriate permissions
- DataSync agent installed and registered on edge node
- S3 bucket created
- Python 3.9+ (for local testing)
- AWS CLI v2 configured

### 1. Clone/Copy Project

```bash
cd /Users/paramraghavan/dev/123ofaws/datasync
```

### 2. Configure Environment Variables

```bash
# Create .env file or set environment variables
export AWS_REGION=us-east-1
export DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/nfs/xxxxx
export DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/s3/yyyyy
export NAS_BASE_PATH=/mydata/prod/icm/datain/poolData
export S3_BUCKET=my-datasync-bucket
export DATATYPES=datatype1,datatype2,datatype3
export ENVIRONMENT=prod
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:datasync-notifications
```

### 3. Test Locally (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Test date logic
python -m pytest test_date_logic.py -v

# Test with today's date
python lambda_function.py daily

# Test with backdated scenario
python lambda_function.py backdated 2024/0721

# Test with range scenario
python lambda_function.py range 7
```

### 4. Deploy to Lambda

```bash
# Create deployment package
mkdir -p lambda_package
pip install -r requirements.txt -t ./lambda_package/

# Copy source files
cp lambda_function.py config.py date_logic.py datasync_manager.py lambda_package/

# Create ZIP
cd lambda_package
zip -r ../datasync-orchestrator.zip .
cd ..

# Create IAM role
aws iam create-role \
  --role-name datasync-orchestrator-lambda-role \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name datasync-orchestrator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Attach custom inline policy
aws iam put-role-policy \
  --role-name datasync-orchestrator-lambda-role \
  --policy-name datasync-policy \
  --policy-document file://lambda-policy.json

# Deploy Lambda function
aws lambda create-function \
  --function-name datasync-orchestrator \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/datasync-orchestrator-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://datasync-orchestrator.zip \
  --timeout 300 \
  --memory-size 256 \
  --environment "Variables={
    DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/nfs/xxxxx,
    DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/s3/yyyyy,
    NAS_BASE_PATH=/mydata/prod/icm/datain/poolData,
    S3_BUCKET=my-datasync-bucket,
    DATATYPES=datatype1,datatype2,datatype3,
    ENVIRONMENT=prod,
    SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:datasync-notifications,
    AWS_REGION=us-east-1
  }"
```

### 5. Create EventBridge Trigger (Daily Execution)

```bash
# Create EventBridge rule for daily execution at 00:30 UTC
aws events put-rule \
  --name datasync-daily-copy \
  --schedule-expression "cron(30 0 * * ? *)" \
  --state ENABLED \
  --description "Daily DataSync copy trigger"

# Add Lambda as target
aws events put-targets \
  --rule datasync-daily-copy \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:datasync-orchestrator","RoleArn"="arn:aws:iam::123456789012:role/eventbridge-invoke-lambda"

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name datasync-orchestrator \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:123456789012:rule/datasync-daily-copy
```

---

## Detailed Deployment Steps

### Step 1: Prepare AWS Environment

#### 1.1 Create IAM Role for Lambda

**File: `trust-policy.json`**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**File: `lambda-policy.json`**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DataSyncAccess",
      "Effect": "Allow",
      "Action": [
        "datasync:CreateTask",
        "datasync:UpdateTask",
        "datasync:ListTasks",
        "datasync:DescribeTask",
        "datasync:StartTaskExecution",
        "datasync:DescribeTaskExecution",
        "datasync:ListTaskExecutions",
        "datasync:ListLocations"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-datasync-bucket",
        "arn:aws:s3:::my-datasync-bucket/*"
      ]
    },
    {
      "Sid": "SNSPublish",
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:*"
    },
    {
      "Sid": "CloudWatchLogs",
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

#### 1.2 Create SNS Topic

```bash
aws sns create-topic --name datasync-notifications
# Output: "TopicArn": "arn:aws:sns:us-east-1:123456789012:datasync-notifications"

# Subscribe to topic (email example)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:datasync-notifications \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### Step 2: Test DataSync Agent

```bash
# Verify agent is running
aws datasync list-agents

# Test NFS location connectivity
aws datasync describe-location-nfs \
  --location-arn arn:aws:datasync:us-east-1:123456789012:location/nfs/xxxxx

# Verify S3 location is accessible
aws datasync describe-location-s3 \
  --location-arn arn:aws:datasync:us-east-1:123456789012:location/s3/yyyyy
```

### Step 3: Package and Deploy Lambda

```bash
# Navigate to project directory
cd /Users/paramraghavan/dev/123ofaws/datasync

# Create clean deployment package
rm -rf lambda_package datasync-orchestrator.zip

# Install dependencies
mkdir -p lambda_package
pip install -r requirements.txt -t ./lambda_package/

# Copy Python modules
cp lambda_function.py config.py date_logic.py datasync_manager.py lambda_package/

# Create ZIP file
cd lambda_package
zip -r ../datasync-orchestrator.zip . >/dev/null
cd ..

# Verify ZIP contains all files
unzip -l datasync-orchestrator.zip | head -20

# Deploy function
aws lambda create-function \
  --function-name datasync-orchestrator \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/datasync-orchestrator-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://datasync-orchestrator.zip \
  --timeout 300 \
  --memory-size 256 \
  --environment Variables={DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:us-east-1:123456789012:location/nfs/xxxxx}
```

### Step 4: Configure EventBridge Trigger

```bash
# Create EventBridge rule (daily at 00:30 UTC)
aws events put-rule \
  --name datasync-daily-copy \
  --schedule-expression "cron(30 0 * * ? *)" \
  --state ENABLED

# Add Lambda target
aws events put-targets \
  --rule datasync-daily-copy \
  --targets Id=1,Arn=arn:aws:lambda:us-east-1:123456789012:function:datasync-orchestrator

# Grant permission
aws lambda add-permission \
  --function-name datasync-orchestrator \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:123456789012:rule/datasync-daily-copy
```

### Step 5: Test Deployment

```bash
# Invoke function with daily scenario
aws lambda invoke \
  --function-name datasync-orchestrator \
  --payload '{"scenario":"daily"}' \
  response.json

# Check response
cat response.json | python -m json.tool

# Check CloudWatch logs
aws logs tail /aws/lambda/datasync-orchestrator --follow
```

---

## Monitoring After Deployment

### CloudWatch Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/datasync-orchestrator --follow

# View specific date execution
aws logs filter-log-events \
  --log-group-name /aws/lambda/datasync-orchestrator \
  --filter-pattern "2024/0804"

# Get log statistics
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/datasync-orchestrator
```

### DataSync Task Monitoring

```bash
# List all DataSync tasks
aws datasync list-tasks

# Get task details
aws datasync describe-task \
  --task-arn arn:aws:datasync:us-east-1:123456789012:task/xxxxx

# Monitor task execution
aws datasync list-task-executions \
  --task-arn arn:aws:datasync:us-east-1:123456789012:task/xxxxx

# Get execution details
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:us-east-1:123456789012:tasexecution/xxxxx
```

---

## Troubleshooting

See troubleshooting.md for common issues and solutions.

