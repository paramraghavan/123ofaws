# AWS DataSync Setup Guide - Step by Step

## Phase 1: Prerequisites & Setup

### 1.1 DataSync Agent Installation on Edge Node

```bash
# Download DataSync agent for your OS (Linux example)
wget https://s3.amazonaws.com/aws-datasync/latest/aws-datasync-agent-linux.tar.gz

# Extract and install
tar xzf aws-datasync-agent-linux.tar.gz
cd aws-datasync-agent/
./install.sh

# Start the agent
systemctl start aws-datasync-agent
systemctl enable aws-datasync-agent

# Verify status
systemctl status aws-datasync-agent
```

**Note**: Agent needs:
- Network connectivity to AWS (port 443)
- Local NFS mount accessible
- Outbound internet access

### 1.2 IAM Setup

#### A. Edge Node Service Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "datasync:DescribeAgent",
        "datasync:ListAgents",
        "datasync:UpdateAgent"
      ],
      "Resource": "*"
    }
  ]
}
```

#### B. Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
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
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket",
        "arn:aws:s3:::your-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:datasync-notifications"
    }
  ]
}
```

### 1.3 S3 Bucket Setup

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket your-datasync-bucket \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-datasync-bucket \
  --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption \
  --bucket your-datasync-bucket \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'

# Set lifecycle policy (optional - archive old data)
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-datasync-bucket \
  --lifecycle-configuration file://lifecycle-policy.json
```

### 1.4 Register DataSync Locations

#### A. NFS Location (Source)
```bash
aws datasync create-location-nfs \
  --subdirectory /mydata/prod/icm/datain/poolData \
  --server-hostname nas-server-ip-or-hostname \
  --on-prem-config AgentArns=arn:aws:datasync:region:account:agent/agent-id

# Output: "LocationArn": "arn:aws:datasync:region:account:location/nfs/xxxxx"
```

#### B. S3 Location (Destination)
```bash
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::your-datasync-bucket \
  --subdirectory /poolData \
  --s3-config BucketAccessRoleArn=arn:aws:iam::account:role/datasync-s3-role

# Output: "LocationArn": "arn:aws:datasync:region:account:location/s3/xxxxx"
```

---

## Phase 2: Python Implementation

### 2.1 Project Structure
```
datasync-orchestrator/
├── lambda_function.py          # Main Lambda handler
├── datasync_manager.py         # DataSync operations
├── date_logic.py               # Date calculation logic
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies
└── tests/
    ├── test_date_logic.py
    └── test_datasync_manager.py
```

### 2.2 Configuration File
See `config.py` in the implementation section below.

### 2.3 Deployment

```bash
# Install dependencies
pip install -r requirements.txt -t ./lambda_package/

# Package Lambda function
cd lambda_package
zip -r ../lambda_function.zip .
cd ..
zip lambda_function.zip lambda_function.py datasync_manager.py date_logic.py config.py

# Deploy to AWS Lambda
aws lambda create-function \
  --function-name datasync-orchestrator \
  --runtime python3.11 \
  --role arn:aws:iam::account:role/lambda-datasync-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 60 \
  --memory-size 256

# Set up CloudWatch Events (EventBridge) trigger for daily execution
# Scheduled for 00:30 UTC every day (adjust as needed)
aws events put-rule \
  --name datasync-daily-copy \
  --schedule-expression "cron(30 0 * * ? *)"

aws events put-targets \
  --rule datasync-daily-copy \
  --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:datasync-orchestrator"
```

### 2.4 Configuration Parameters

Update in AWS Systems Manager Parameter Store or Lambda environment variables:

```
DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:region:account:location/nfs/xxxxx
DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:region:account:location/s3/xxxxx
NAS_BASE_PATH=/mydata/prod/icm/datain/poolData
S3_BUCKET=your-datasync-bucket
S3_PREFIX=poolData
DATATYPES=datatype1,datatype2  # Comma-separated list
ENVIRONMENT=prod
SNS_TOPIC_ARN=arn:aws:sns:region:account:datasync-notifications
```

---

## Phase 3: Monitoring & Operations

### 3.1 CloudWatch Monitoring

```bash
# Monitor Lambda execution
aws logs tail /aws/lambda/datasync-orchestrator --follow

# Monitor DataSync task execution
aws datasync list-task-executions \
  --task-arn arn:aws:datasync:region:account:task/xxxxx

# Get task execution details
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:region:account:tasexecution/xxxxx
```

### 3.2 Alerts & Notifications

Lambda sends SNS notifications on:
- Task started
- Task completed successfully
- Task failed with error details
- Validation failures

### 3.3 Troubleshooting

Common issues and solutions documented in troubleshooting.md

