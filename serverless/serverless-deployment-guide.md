# Serverless Framework Deployment Guide

> **Complete guide to deploying serverless applications without AWS console login**: Learn how Serverless Framework authenticates to AWS, deploys Lambda functions, and integrates with CI/CD pipelines—all from the command line.

---

## Table of Contents

1. [Quick Answer](#quick-answer)
2. [How Serverless Deploy Works](#how-serverless-deploy-works)
3. [Authentication Methods](#authentication-methods)
4. [Complete Deployment Example](#complete-deployment-example)
5. [Do You Need AWS Console?](#do-you-need-aws-console)
6. [Serverless Commands](#common-serverless-deploy-commands)
7. [CI/CD Integration](#real-world-cicd-example)
8. [Best Practices](#aws-credentials-best-practices)
9. [Troubleshooting](#troubleshooting-deployment)
10. [Quick Start](#quick-start-5-minutes)

---

## Quick Answer

**Do I need to login to AWS console to deploy?**

❌ **NO!** Serverless Framework deploys entirely from the command line using AWS credentials. No console login required.

---

## How Serverless Deploy Works

### The Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Your Local Machine                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  serverless deploy                                          │
│        ↓                                                    │
│  Read serverless.yml                                        │
│        ↓                                                    │
│  Load AWS Credentials                                       │
│  (from ~/.aws/credentials or env vars)                      │
│        ↓                                                    │
│  Package code (zip files)                                   │
│        ↓                                                    │
│  Create CloudFormation template                             │
│        ↓                                                    │
│  Upload to S3                                               │
│        ↓                                                    │
│  Call AWS CloudFormation API                                │
│        ↓                                                    │
│  AWS creates Lambda, API Gateway, etc.                      │
│        ↓                                                    │
│  Deploy complete ✅                                         │
└─────────────────────────────────────────────────────────────┘
```

### What Happens Behind the Scenes

1. **Read Configuration**: Serverless reads your `serverless.yml`
2. **Authenticate**: Uses AWS credentials to authenticate
3. **Package Code**: Zips your Lambda functions and dependencies
4. **Generate CloudFormation**: Creates infrastructure-as-code template
5. **Upload Artifacts**: Uploads zip files to S3
6. **Create Stack**: Uses CloudFormation to create/update AWS resources
7. **Deploy**: Lambda, API Gateway, IAM roles, and other resources are created
8. **Verify**: Tests connectivity and outputs function details

---

## Authentication Methods

### Method 1: AWS Credentials File (Recommended)

The most common and secure method for local development.

```bash
# Step 1: Create AWS credentials locally
aws configure

# This creates ~/.aws/credentials file:
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = us-east-1

# Step 2: Deploy (Serverless automatically finds credentials)
serverless deploy
```

**Benefits:**
- ✅ Credentials stored locally and securely
- ✅ Automatic discovery by Serverless
- ✅ Works with AWS CLI as well
- ✅ Supports multiple profiles

### Method 2: Environment Variables

Use environment variables for CI/CD or temporary access.

```bash
# Export credentials as environment variables
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1

# Deploy (Serverless uses environment variables)
serverless deploy
```

**Use cases:**
- ✅ GitHub Actions workflows
- ✅ Jenkins/GitLab CI
- ✅ Docker containers
- ✅ Temporary deployments

### Method 3: Named Profiles

Use different credentials for different environments.

```bash
# Configure multiple profiles
aws configure --profile production
aws configure --profile staging
aws configure --profile development

# Use specific profile in deployment
serverless deploy --aws-profile production

# Or set default profile
export AWS_PROFILE=production
serverless deploy
```

**Best for:**
- ✅ Multiple environments
- ✅ Multiple AWS accounts
- ✅ Team collaboration

### Method 4: IAM Role (Brownfield/CI/CD)

For servers, containers, or EC2 instances with attached IAM roles.

```bash
# On EC2/Outpost/Lambda, assumes attached IAM role
# No credentials needed - AWS SDK auto-detects role!
serverless deploy

# Verify role is being used
aws sts get-caller-identity
```

**Perfect for:**
- ✅ EC2 instances with instance profiles
- ✅ Lambda functions (if deploying from Lambda)
- ✅ AWS Outposts/Wavelength
- ✅ Container services

---

## Complete Deployment Example

### Step 1️⃣: Create serverless.yml

```yaml
service: my-data-processor

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  stage: ${opt:stage, 'dev'}

  # IAM permissions for Lambda execution
  iamRoleStatements:
    - Effect: Allow
      Action:
        - s3:GetObject
        - s3:PutObject
      Resource: "arn:aws:s3:::my-bucket/*"
    - Effect: Allow
      Action:
        - logs:CreateLogGroup
        - logs:CreateLogStream
        - logs:PutLogEvents
      Resource: "*"
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:Query
      Resource: "arn:aws:dynamodb:us-east-1:*:table/events"

functions:
  processData:
    handler: handler.process_data
    timeout: 300
    memorySize: 512
    environment:
      BUCKET_NAME: my-bucket
      TABLE_NAME: events
    events:
      # Trigger on S3 upload
      - s3:
          bucket: my-bucket
          event: s3:ObjectCreated:*
          rules:
            - prefix: uploads/
            - suffix: .csv
      # Trigger on HTTP request
      - http:
          path: process
          method: post
          cors: true

  notifyCompletion:
    handler: handler.notify_completion
    timeout: 60
    memorySize: 256
    events:
      # Trigger from SQS queue
      - sqs:
          arn:
            Fn::GetAtt:
              - ProcessingQueue
              - Arn
          batchSize: 10

resources:
  Resources:
    ProcessingQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: processing-queue-${self:provider.stage}
        VisibilityTimeout: 300

plugins:
  - serverless-python-requirements
  - serverless-plugin-tracing

package:
  individually: true
  patterns:
    - '!node_modules/**'
    - '!.git/**'
    - '!.env'
```

### Step 2️⃣: Create Lambda Handler

```python
# handler.py
import json
import boto3
import logging
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

BUCKET_NAME = os.environ['BUCKET_NAME']
TABLE_NAME = os.environ['TABLE_NAME']

def process_data(event, context):
    """
    Process S3 upload or HTTP request.

    S3 Event Structure:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "my-bucket"},
                "object": {"key": "uploads/data.csv"}
            }
        }]
    }

    HTTP Event Structure:
    {
        "body": "...",
        "pathParameters": {...},
        "queryStringParameters": {...}
    }
    """

    try:
        # Determine event type
        if 'Records' in event:
            # S3 event
            return handle_s3_event(event)
        elif 'body' in event:
            # HTTP event
            return handle_http_event(event)
        else:
            raise ValueError("Unknown event type")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_s3_event(event):
    """Handle S3 ObjectCreated event"""
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    logger.info(f"Processing s3://{bucket}/{key}")

    # Read file from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    data = response['Body'].read().decode('utf-8')

    # Process data
    lines = data.strip().split('\n')
    logger.info(f"Processed {len(lines)} lines")

    # Store result in DynamoDB
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            'file_key': {'S': key},
            'processed_at': {'S': datetime.utcnow().isoformat()},
            'line_count': {'N': str(len(lines))},
            'status': {'S': 'completed'}
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processing successful',
            'lines_processed': len(lines)
        })
    }


def handle_http_event(event):
    """Handle HTTP POST request"""
    body = json.loads(event['body'])

    logger.info(f"Processing HTTP request: {body}")

    # Perform processing
    result = {
        'processed': True,
        'input': body,
        'timestamp': datetime.utcnow().isoformat()
    }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }


def notify_completion(event, context):
    """Handle SQS messages for completion notifications"""

    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            logger.info(f"Processing notification: {message}")

            # Send notification (email, SNS, etc.)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    return {'statusCode': 200, 'body': 'Notifications sent'}
```

### Step 3️⃣: Create requirements.txt

```txt
boto3>=1.26.0
python-dateutil>=2.8.0
```

### Step 4️⃣: Install Serverless

```bash
# Install serverless framework globally
npm install -g serverless

# Or install locally in project
npm init -y
npm install --save-dev serverless

# Install plugins
npm install --save-dev serverless-python-requirements
npm install --save-dev serverless-plugin-tracing
```

### Step 5️⃣: Deploy to AWS

```bash
# Deploy to dev environment
serverless deploy --stage dev

# Or deploy to production
serverless deploy --stage prod

# Deploy with verbose output to see details
serverless deploy --stage prod --verbose

# Deploy specific function only (faster)
serverless deploy function -f processData --stage prod
```

### 🎉 What Serverless Creates

```
AWS CloudFormation Stack: my-data-processor-dev
├── Lambda Function
│   ├── my-data-processor-dev-processData
│   └── my-data-processor-dev-notifyCompletion
├── IAM Role (for Lambda execution)
├── CloudWatch Log Groups
│   ├── /aws/lambda/my-data-processor-dev-processData
│   └── /aws/lambda/my-data-processor-dev-notifyCompletion
├── S3 Event Configuration
├── API Gateway
│   └── POST /process endpoint
└── SQS Queue
    └── processing-queue-dev
```

---

## Do You Need AWS Console?

### Deployment Tasks (No Console Needed)

| Task | Console Needed? | How to Do It |
|------|-----------------|-------------|
| **Deploy** | ❌ NO | `serverless deploy` |
| **Deploy specific function** | ❌ NO | `serverless deploy function -f myFunction` |
| **Invoke function** | ❌ NO | `serverless invoke -f myFunction` |
| **View logs** | ❌ NO | `serverless logs -f myFunction --tail` |
| **Update code** | ❌ NO | `serverless deploy function -f myFunction` |
| **Delete stack** | ❌ NO | `serverless remove` |
| **Get function info** | ❌ NO | `serverless info` |

### Monitoring Tasks (Console Optional but Helpful)

| Task | Console Needed? | How to Do It |
|------|-----------------|-------------|
| **Monitor metrics** | ✅ YES (helpful) | AWS CloudWatch console |
| **View X-Ray traces** | ✅ YES (helpful) | AWS X-Ray console |
| **Set up alarms** | ❌ NO (optional) | Serverless dashboard or AWS console |
| **View error details** | ❌ NO | `serverless logs -f myFunction` |
| **Troubleshoot issues** | ✅ YES (helpful) | AWS CloudWatch Logs console |

---

## Common Serverless Deploy Commands

### Deployment

```bash
# Deploy everything to dev
serverless deploy

# Deploy to specific stage
serverless deploy --stage production

# Deploy to specific region
serverless deploy --region eu-west-1

# Deploy specific function only (faster)
serverless deploy function -f processData

# Deploy with verbose output
serverless deploy --verbose

# Dry run - see what would happen without deploying
serverless deploy --noDeploy

# Deploy with different AWS profile
serverless deploy --aws-profile production

# Deploy with custom variables
serverless deploy --param="key=value"
```

### Invocation and Testing

```bash
# Invoke function locally (for testing)
serverless invoke local -f processData -d '{"test": "data"}'

# Invoke function in AWS
serverless invoke -f processData -d '{"test": "data"}'

# Invoke with JSON file
serverless invoke -f processData --path event.json

# Invoke and get response
serverless invoke -f processData --log
```

### Logs and Monitoring

```bash
# View logs from past 1 hour
serverless logs -f processData

# Tail logs in real-time
serverless logs -f processData --tail

# View logs with filter
serverless logs -f processData --filter "ERROR"

# View logs from past 30 minutes
serverless logs -f processData --startTime 30m
```

### Information and Cleanup

```bash
# Get function information
serverless info

# Get all functions
serverless info --verbose

# Remove entire stack (DELETE ALL RESOURCES)
serverless remove

# Remove with confirmation
serverless remove --stage prod
```

---

## Real-World CI/CD Example

### GitHub Actions Deployment

Deploy automatically when code is pushed to main branch - no console login needed!

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Serverless
        run: npm install -g serverless

      - name: Install dependencies
        run: npm install --save-dev serverless-python-requirements

      - name: Deploy to AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            serverless deploy --stage prod
          else
            serverless deploy --stage dev
          fi

      - name: Get deployment info
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
        run: serverless info --stage prod
```

**How it works:**
1. Push code to main branch
2. GitHub Actions automatically triggers
3. Serverless deploys using credentials from GitHub Secrets
4. Deployment completes without any console interaction
5. Get deployment info and verify success

### GitLab CI/CD Deployment

```yaml
# .gitlab-ci.yml
stages:
  - deploy

deploy_production:
  stage: deploy
  image: node:18

  before_script:
    - npm install -g serverless
    - npm install --save-dev serverless-python-requirements
    - apt-get update && apt-get install -y python3-pip

  script:
    - serverless deploy --stage prod

  environment:
    name: production

  only:
    - main

  variables:
    AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
    AWS_REGION: us-east-1
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        AWS_ACCESS_KEY_ID = credentials('aws_access_key_id')
        AWS_SECRET_ACCESS_KEY = credentials('aws_secret_access_key')
        AWS_REGION = 'us-east-1'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    npm install -g serverless
                    npm install --save-dev serverless-python-requirements
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh 'serverless deploy --stage prod'
            }
        }

        stage('Verify') {
            steps {
                sh 'serverless info --stage prod'
            }
        }
    }
}
```

---

## AWS Credentials: Best Practices

### ✅ DO: Recommended Practices

```bash
# 1. Create IAM user with minimal permissions
aws iam create-user --user-name serverless-deployer

# 2. Create programmatic access key
aws iam create-access-key --user-name serverless-deployer

# 3. Attach minimal policy (CloudFormation + Lambda + S3)
aws iam put-user-policy \
    --user-name serverless-deployer \
    --policy-name ServerlessDeployPolicy \
    --policy-document file://policy.json
```

**Minimal IAM Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "s3:*",
        "apigateway:*",
        "logs:*",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:DeleteRole",
        "iam:DeleteRolePolicy",
        "events:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### ❌ DON'T: Never Do This

```bash
# ❌ Never hardcode credentials in code
serverless deploy \
  --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
  --aws-secret-access-key wJalrXUtnFEMI/K7MDENG

# ❌ Never commit credentials to git
git add .env  # BAD: Contains secrets

# ❌ Never add credentials to serverless.yml
provider:
  credentials:
    accessKeyId: AKIAIOSFODNN7EXAMPLE
    secretAccessKey: wJalrXUtnFEMI/K7MDENG

# ❌ Never use root AWS account credentials
# ❌ Never share credentials via Slack/email
# ❌ Never leave credentials in history
```

### Secure Credential Management

```python
# Use AWS Secrets Manager for storing credentials
import boto3
import json

def get_serverless_credentials():
    """Retrieve Serverless deployment credentials from Secrets Manager"""
    secrets = boto3.client('secretsmanager')

    response = secrets.get_secret_value(
        SecretId='serverless/deployment-credentials'
    )

    creds = json.loads(response['SecretString'])

    return creds['access_key_id'], creds['secret_access_key']
```

---

## Troubleshooting Deployment

### "Unable to assume role" or "No credentials found"

**Error:**
```
Error: AWS credentials not configured. Unable to deploy.
```

**Solution:**
```bash
# Check if credentials are configured
aws sts get-caller-identity

# If error, configure credentials
aws configure

# Verify credentials file exists
cat ~/.aws/credentials

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### "Permission denied" during deploy

**Error:**
```
An error occurred (AccessDenied) when calling the CreateRole operation
```

**Solution:**
```bash
# Check IAM user permissions
aws iam get-user-policy \
    --user-name serverless-deployer \
    --policy-name ServerlessDeployPolicy

# Add missing permissions to policy
aws iam put-user-policy \
    --user-name serverless-deployer \
    --policy-name ServerlessDeployPolicy \
    --policy-document file://updated-policy.json

# Try deployment again
serverless deploy --stage prod
```

### "CloudFormation stack already exists"

**Error:**
```
Stack with id my-data-processor-dev already exists
```

**Solution:**
```bash
# This is normal - just update the existing stack
serverless deploy --stage dev

# Or if you want fresh start
serverless remove --stage dev
serverless deploy --stage dev

# Or just update specific function
serverless deploy function -f processData --stage dev
```

### "Timeout during deployment"

**Error:**
```
Deployment timed out
```

**Solution:**
```bash
# Increase timeout (default is 120 seconds)
serverless deploy --verbose

# Check CloudFormation directly
aws cloudformation describe-stacks \
    --stack-name my-data-processor-dev

# Check CloudWatch logs for Lambda errors
serverless logs -f processData
```

### "Package size too large"

**Error:**
```
An error occurred (CodeSizeTooLarge) when calling the CreateFunction
```

**Solution:**
```bash
# Use serverless-python-requirements plugin to exclude dependencies
# In serverless.yml:
package:
  individually: true
  patterns:
    - '!node_modules/**'
    - '!.git/**'
    - '!__pycache__/**'
    - '!.pytest_cache/**'

# Use Lambda Layers for large dependencies
# Or compress code better
npm install --save-dev serverless-plugin-optimize
```

### Debugging Commands

```bash
# See detailed deployment logs
serverless deploy --verbose

# Check CloudFormation events
aws cloudformation describe-stack-events \
    --stack-name my-data-processor-dev \
    --query 'StackEvents[0:10]'

# Check Lambda function
aws lambda get-function --function-name my-data-processor-dev-processData

# Check IAM role
aws iam get-role --role-name my-data-processor-dev-iam-role

# View recent errors
aws logs tail /aws/lambda/my-data-processor-dev-processData --follow
```

---

## Quick Start (5 Minutes)

### Step 1: Install Tools

```bash
# Install Node.js (if not already installed)
node --version

# Install Serverless Framework
npm install -g serverless
serverless --version
```

### Step 2: Configure AWS Credentials (One Time)

```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [your access key]
# AWS Secret Access Key: [your secret key]
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 3: Create Project Structure

```bash
# Create project directory
mkdir my-serverless-app
cd my-serverless-app

# Initialize
npm init -y

# Create files:
# serverless.yml (from template above)
# handler.py (from template above)
# requirements.txt
```

### Step 4: Deploy

```bash
# Install Serverless plugins
npm install --save-dev serverless-python-requirements

# Deploy to AWS
serverless deploy

# You should see:
# Deploying my-serverless-app to stage dev (us-east-1)
# Packaging lambda functions...
# Creating CloudFormation stack...
# ...
# Service deployed successfully.
# Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/process
```

### Step 5: Test and Monitor

```bash
# Invoke function
serverless invoke -f processData -d '{"test": "data"}'

# View logs
serverless logs -f processData --tail

# Get info
serverless info

# Clean up when done
serverless remove
```

---

## Summary Table

| Feature | Serverless | AWS Console |
|---------|-----------|-------------|
| **Deploy** | ✅ CLI only | ❌ Manual clicking |
| **Speed** | ✅ Fast (automated) | ❌ Slow (manual steps) |
| **Repeatable** | ✅ Same result every time | ❌ Error-prone |
| **CI/CD** | ✅ Perfect fit | ❌ Difficult |
| **Monitoring** | ⚠️ Basic (logs) | ✅ Full dashboard |
| **Cost** | ✅ Pay-per-use | ✅ Pay-per-use |
| **Learning curve** | ⚠️ Moderate | ⚠️ Steep |

---

## Key Takeaways

✅ **No console login needed** - Serverless is completely CLI-based
✅ **Authenticate once** - Configure credentials locally or use environment variables
✅ **Deploy with one command** - `serverless deploy`
✅ **Works in CI/CD** - Perfect for GitHub Actions, GitLab CI, Jenkins
✅ **Monitor without console** - Use `serverless logs` for real-time viewing
✅ **Repeatable deployments** - Same result every time
✅ **Least privilege** - Use minimal IAM permissions for security
✅ **Instant updates** - Redeploy changed functions quickly

---

## Next Steps

1. **Install Serverless**: `npm install -g serverless`
2. **Configure AWS**: `aws configure`
3. **Create project**: Use template from this guide
4. **Deploy**: `serverless deploy`
5. **Monitor**: `serverless logs -f myFunction --tail`
6. **Iterate**: Update code and redeploy

**You're ready to deploy serverless applications without touching the AWS console!** 🚀

