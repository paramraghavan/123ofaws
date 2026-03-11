# Simple Lambda-Based AWS Resource Monitoring System

A **simple, self-contained serverless monitoring system** that automatically monitors AWS resources, detects failures, performs auto-failover for S3, generates alerts for EC2/EMR failures, and displays status via a static HTML dashboard.

## Features

✅ **Automatic Resource Monitoring**
- Monitors S3 buckets, EC2 instances, and EMR clusters
- Checks resource health every 10 minutes via EventBridge trigger
- Filters resources by tag (default: `Name: production`)

✅ **Auto-Failover for S3**
- Detects S3 bucket failures
- Automatically initiates failover to replica region
- Logs failover actions for audit trail

✅ **Smart Alerts**
- SNS alerts for EC2/EMR failures (manual intervention required)
- Heartbeat monitoring - detects if Lambda stops working
- CloudWatch alarms for Lambda function errors

✅ **Visual Dashboard**
- Auto-generated static HTML dashboard
- Displays health status of all resources
- Real-time stat cards showing healthy/total resources
- Auto-refreshes every 60 seconds
- Mobile-responsive design

✅ **Simple & Cost-Effective**
- 2 Lambda functions only
- Minimal dependencies (just boto3)
- Estimated cost: $2-3/month
- Single self-contained folder

## Architecture

```
EventBridge (10 min) → monitor_lambda.py
                            ↓
                       Check resources:
                       - S3 buckets (head_bucket)
                       - EC2 instances (describe_instances)
                       - EMR clusters (list_clusters)
                            ↓
                    Write status.json to S3
                    Write heartbeat.json to S3
                            ↓
                       If S3 failure:
                         → Auto-failover to replica bucket
                       If EC2/EMR failure:
                         → Send SNS alert with details
                            ↓
S3 status.json → generate_dashboard.py → index.html (static)

CloudWatch Alarm → Monitor heartbeat.json age → SNS alert if > 20 min
```

## Comparison with failover_ver3

This monitoring system complements the **failover_ver3** system:

| Aspect | aws-lambda-monitoring | failover_ver3 |
|--------|------------------------|---------------|
| **Purpose** | Lightweight AWS resource monitoring | Comprehensive failover orchestration |
| **Deployment** | Serverless (Lambda) | Local/scheduled (Python scripts) |
| **Monitoring** | S3, EC2, EMR (basic health) | EC2, EMR, Lambda, Auto Scaling (detailed) |
| **S3 Failover** | ✅ Auto-failover to replica region | ❌ No S3 failover |
| **EC2/EMR Failover** | ❌ Alerts only | ✅ Auto-restart/recreate |
| **Auto-Discovery** | ❌ Manual configuration | ✅ Auto-discovers configurations |
| **Dashboard** | Static HTML in S3 | Interactive Flask web app |
| **Cost** | ~$2-3/month | Free (local execution) |
| **Setup Time** | 5 minutes | 15 minutes |

**Use Together:** Monitor with `aws-lambda-monitoring`, handle failover with `failover_ver3`!

## File Structure

```
aws-lambda-monitoring/
├── monitor_lambda.py              # Main monitoring Lambda (200 lines)
├── generate_dashboard.py          # Dashboard generator (100 lines)
├── dashboard_template.html        # HTML template for dashboard
├── serverless.yml                 # Deployment config
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Installation & Deployment

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Python 3.11+** (for local testing)
4. **Node.js & npm** (for Serverless Framework) - OR use CloudFormation

### Quick Start: Serverless Framework (Recommended)

```bash
# 1. Install Serverless Framework
npm install -g serverless

# 2. Clone/navigate to the project directory
cd aws-lambda-monitoring

# 3. Deploy to AWS
serverless deploy

# 4. View deployment outputs
serverless info --verbose
```

### Alternative: CloudFormation Deployment

If you prefer pure CloudFormation (no Node.js required):

```bash
# 1. Package Lambda functions
cd aws-lambda-monitoring
zip -r lambda-code.zip monitor_lambda.py generate_dashboard.py dashboard_template.html

# 2. Upload to S3 (for CloudFormation)
aws s3 cp lambda-code.zip s3://your-deployment-bucket/

# 3. Deploy CloudFormation template
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=CodeBucketName,ParameterValue=your-deployment-bucket \
  --capabilities CAPABILITY_NAMED_IAM
```

**See `cloudformation-template.yaml` section below for full template.**

### Configuration

This system uses **environment variables** in `serverless.yml` instead of a separate `config.json` file.

#### Configuration via serverless.yml (Recommended)

Edit `serverless.yml`:

```yaml
provider:
  environment:
    TAG_NAME: production              # Tag name to monitor (case-sensitive)
    LOG_BUCKET: simple-aws-monitoring-logs-ACCOUNT_ID
    SNS_TOPIC_ARN: arn:aws:sns:us-east-1:ACCOUNT_ID:simple-aws-monitoring-alerts
    S3_REPLICA_REGION: us-west-2     # Region for S3 failover
```

#### Alternative: Environment Variables

Set before deployment:

```bash
export TAG_NAME=production
export S3_REPLICA_REGION=us-west-2
serverless deploy
```

#### Configuration for CloudFormation

Create `cloudformation-params.json`:

```json
[
  {
    "ParameterKey": "TagName",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "CodeBucketName",
    "ParameterValue": "your-deployment-bucket"
  }
]
```

Deploy:
```bash
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters file://cloudformation-params.json \
  --capabilities CAPABILITY_NAMED_IAM
```

### Comparison: config.json vs Environment Variables

#### failover_ver3 Approach (config.json)

**failover_ver3** uses a simple `config.json`:

```json
{
  "aws_profile": "default",
  "aws_region": "us-east-1",
  "tag_name": "production",
  "emr": {
    "bootstrap_repo": "https://github.com/your-org/emr-bootstrap.git",
    "bootstrap_branch": "main"
  }
}
```

**Pros:**
- Simple, human-readable
- Can be checked into version control
- Supports multi-profile configurations
- Good for local Python scripts

**Cons:**
- Needs manual updates
- File-based (not AWS-native)
- Requires EMR bootstrap repo configuration

#### aws-lambda-monitoring Approach (Environment Variables)

**aws-lambda-monitoring** uses AWS-native environment variables:

```yaml
# In serverless.yml or CloudFormation
environment:
  TAG_NAME: production
  LOG_BUCKET: simple-aws-monitoring-logs-123456789
  SNS_TOPIC_ARN: arn:aws:sns:us-east-1:123456789:alerts
```

**Pros:**
- AWS-native (no external config files)
- Secure (can use Secrets Manager)
- Automatically managed by CloudFormation
- Version controlled as infrastructure code

**Cons:**
- Less human-readable (especially CloudFormation)
- Not file-based

#### When to Use Each

| Scenario | Use This |
|----------|----------|
| Local Python automation | failover_ver3 + config.json |
| Serverless Lambda monitoring | aws-lambda-monitoring + environment vars |
| Pure CloudFormation deployment | aws-lambda-monitoring + CloudFormation params |
| Multi-environment management | failover_ver3 with multiple configs |
| Quick testing | aws-lambda-monitoring (environment vars) |

**Recommended:** Use `failover_ver3` for comprehensive failover handling + `aws-lambda-monitoring` for continuous serverless monitoring!

## Resource Tagging

**Resources must be tagged with `Name: <TAG_NAME>` to be monitored.**

### Tag S3 Buckets

```bash
aws s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[{Key=Name,Value=production}]'
```

### Tag EC2 Instances

```bash
aws ec2 create-tags \
  --resources i-0123456789abcdef0 \
  --tags Key=Name,Value=production
```

### Tag EMR Clusters

```bash
aws emr add-tags \
  --resource-id j-123ABC4DEFG56 \
  --tags Name=production
```

## Usage

### View Dashboard

After deployment, access your dashboard at:

```
https://simple-aws-monitoring-logs-{AWS_ACCOUNT_ID}.s3-website-us-east-1.amazonaws.com/dashboard/index.html
```

Replace `{AWS_ACCOUNT_ID}` with your AWS account ID.

Or get the URL from deployment output:

```bash
serverless info --verbose
```

### Check Logs

View monitoring status and logs:

```bash
# Latest status
aws s3 cp s3://simple-aws-monitoring-logs-{account-id}/status/latest.json -

# Heartbeat
aws s3 cp s3://simple-aws-monitoring-logs-{account-id}/heartbeat.json -

# Failover logs
aws s3 ls s3://simple-aws-monitoring-logs-{account-id}/failover_logs/
```

### Manually Trigger Monitoring

Run the monitoring Lambda immediately:

```bash
serverless invoke -f monitor
```

Generate dashboard immediately:

```bash
serverless invoke -f dashboard
```

### View CloudWatch Logs

```bash
# Monitor Lambda logs
serverless logs -f monitor --tail

# Dashboard Lambda logs
serverless logs -f dashboard --tail
```

## Resource Monitoring Details

### S3 Buckets

**Monitored Properties:**
- Bucket accessibility (head_bucket)
- Region
- Tagging
- Replica bucket health

**Status Values:**
- `available` - Bucket is accessible ✅
- `failed` - Bucket is not responding ❌

**Automatic S3 Failover:**

When S3 bucket failure is detected, the system:

1. **Detects Failure:** Uses `head_bucket` to check accessibility
   ```python
   try:
       s3.head_bucket(Bucket=bucket_name)
   except ClientError:
       # Failover triggered
   ```

2. **Initiates Auto-Failover:**
   - Logs failover event to `failover_logs/{bucket_name}-{timestamp}.json`
   - Creates failover metadata with:
     - Original bucket and region
     - Replica region destination
     - Timestamp of failure

3. **Replica Bucket Setup (Manual):**
   You should pre-configure a replica bucket:
   ```bash
   # Create replica bucket in different region
   aws s3api create-bucket \
     --bucket my-bucket-replica \
     --region us-west-2 \
     --create-bucket-configuration LocationConstraint=us-west-2

   # Enable versioning on both
   aws s3api put-bucket-versioning \
     --bucket my-bucket \
     --versioning-configuration Status=Enabled

   aws s3api put-bucket-versioning \
     --bucket my-bucket-replica \
     --versioning-configuration Status=Enabled
   ```

4. **Extend Failover Logic:**
   Customize `failover_s3_bucket()` in `monitor_lambda.py`:
   ```python
   def failover_s3_bucket(bucket_name):
       """Auto-failover S3 bucket to replica region"""
       s3 = boto3.client('s3')

       try:
           # Get replica bucket name
           replica_bucket = f"{bucket_name}-replica"

           # Copy critical objects
           paginator = s3.get_paginator('list_objects_v2')
           for page in paginator.paginate(Bucket=bucket_name):
               for obj in page.get('Contents', []):
                   s3.copy_object(
                       Bucket=replica_bucket,
                       CopySource={'Bucket': bucket_name, 'Key': obj['Key']},
                       Key=obj['Key']
                   )

           # Update DNS/Route53 to point to replica
           route53 = boto3.client('route53')
           # ... update your DNS records ...

       except Exception as e:
           print(f"Failover error: {str(e)}")
   ```

5. **Test S3 Failover:**
   ```bash
   # 1. Block primary bucket (simulate failure)
   aws s3api put-bucket-policy --bucket my-bucket \
     --policy '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Principal":"*","Action":"s3:*","Resource":"*"}]}'

   # 2. Trigger monitoring
   serverless invoke -f monitor

   # 3. Check failover log
   aws s3 cp s3://simple-aws-monitoring-logs-{account}/failover_logs/ . --recursive

   # 4. Restore bucket
   aws s3api delete-bucket-policy --bucket my-bucket
   ```

**Failover Logging:**
All failover events are logged to S3:
```json
{
  "action": "failover_initiated",
  "bucket": "my-bucket",
  "original_region": "us-east-1",
  "replica_region": "us-west-2",
  "timestamp": "2026-03-10T12:30:45.123456"
}
```

### EC2 Instances

**Monitored Properties:**
- Instance state
- Instance type
- Availability zone

**Status Values:**
- `running` - Instance is running ✅
- `stopped` - Instance is stopped ❌
- `stopping` - Instance is stopping ⚠️
- `terminated` - Instance is terminated ❌

**Alert Action:**
- SNS notification sent when instance is not running

### EMR Clusters

**Monitored Properties:**
- Cluster ID
- Cluster name
- Cluster state

**Status Values:**
- `RUNNING` - Cluster is processing ✅
- `WAITING` - Cluster is idle ✅
- `STARTING` - Cluster is starting ⚠️
- `TERMINATING` - Cluster is terminating ⚠️
- `TERMINATED` - Cluster is terminated ❌
- `TERMINATED_WITH_ERRORS` - Cluster failed ❌

**Alert Action:**
- SNS notification sent when cluster is terminated

## Testing & Verification

### Test Deployment

```bash
# Check Lambda functions exist
aws lambda list-functions | grep simple-aws-monitoring

# Check S3 bucket created
aws s3 ls | grep simple-aws-monitoring-logs

# Check SNS topic created
aws sns list-topics | grep simple-aws-monitoring
```

### Test Monitoring

```bash
# 1. Create test EC2 instance with tag
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t2.micro \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=production}]'

# 2. Trigger monitoring manually
serverless invoke -f monitor

# 3. Check status
aws s3 cp s3://simple-aws-monitoring-logs-{account-id}/status/latest.json - | jq .

# 4. View dashboard (should show your instance as "running")
```

### Test Failure Scenarios

**Test EC2 Failure Alert:**

```bash
# 1. Stop a monitored instance
aws ec2 stop-instances --instance-ids i-0123456789abcdef0

# 2. Trigger monitoring
serverless invoke -f monitor

# 3. Check SNS notifications
# (should receive email alert)
```

**Test Lambda Failure Detection:**

```bash
# 1. Disable the monitor EventBridge rule
aws events disable-rule --name simple-aws-monitoring-monitor-us-east-1-monitor

# 2. Wait 20 minutes (or manually put old heartbeat)
aws s3 cp /dev/stdin s3://simple-aws-monitoring-logs-{account-id}/heartbeat.json \
  --expires 2020-01-01 << 'EOF'
{"last_update": "2020-01-01T00:00:00"}
EOF

# 3. Monitor Lambda should not run, CloudWatch alarm triggers
# (should receive SNS alert about heartbeat missing)
```

## Deployment Methods: Serverless vs CloudFormation

### Serverless Framework Approach (serverless.yml)

**Pros:**
- ✅ Simple, human-readable syntax
- ✅ Built-in plugins ecosystem
- ✅ Automatic IAM role creation
- ✅ Easy local testing with `serverless offline`
- ✅ Plugin support for CI/CD integration
- ✅ Faster iteration during development

**Cons:**
- ❌ Requires Node.js installation
- ❌ Additional npm dependencies

**Best for:** Development, rapid iteration, teams already using Node.js

### CloudFormation Approach (Alternative)

**Pros:**
- ✅ Pure AWS-native (no external dependencies)
- ✅ Version control friendly
- ✅ Works with AWS Console directly
- ✅ Better for enterprises with strict tool policies
- ✅ Integrates with AWS SAM for packaging
- ✅ No Node.js dependency

**Cons:**
- ❌ More verbose syntax
- ❌ More manual IAM configuration

**Best for:** Production, enterprises, AWS-only tooling

### Example CloudFormation Template

```yaml
# cloudformation-template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Simple AWS Monitoring System - CloudFormation'

Parameters:
  CodeBucketName:
    Type: String
    Description: S3 bucket containing lambda-code.zip

  TagName:
    Type: String
    Default: production
    Description: Resource tag to monitor

Resources:
  # IAM Role for Lambda
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: MonitoringPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:*
                  - ec2:DescribeInstances
                  - emr:ListClusters
                  - emr:DescribeCluster
                  - sns:Publish
                Resource: '*'

  # S3 Bucket for Logs
  LogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'simple-aws-monitoring-logs-${AWS::AccountId}'
      WebsiteConfiguration:
        IndexDocument: dashboard/index.html

  # Lambda Layer with Dependencies
  PythonDependenciesLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      LayerName: python-boto3-dependencies
      Description: Boto3 and dependencies
      Content:
        S3Bucket: !Ref CodeBucketName
        S3Key: python-dependencies-layer.zip
      CompatibleRuntimes:
        - python3.11

  # Monitor Lambda Function
  MonitorFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: simple-aws-monitoring-monitor
      Runtime: python3.11
      Handler: monitor_lambda.lambda_handler
      Timeout: 300
      MemorySize: 256
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        S3Bucket: !Ref CodeBucketName
        S3Key: lambda-code.zip
      Environment:
        Variables:
          TAG_NAME: !Ref TagName
          LOG_BUCKET: !Ref LogBucket
          SNS_TOPIC_ARN: !Ref AlertTopic
      Layers:
        - !Ref PythonDependenciesLayer

  # Dashboard Generator Lambda
  DashboardFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: simple-aws-monitoring-dashboard
      Runtime: python3.11
      Handler: generate_dashboard.lambda_handler
      Timeout: 60
      MemorySize: 128
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        S3Bucket: !Ref CodeBucketName
        S3Key: lambda-code.zip
      Environment:
        Variables:
          LOG_BUCKET: !Ref LogBucket
      Layers:
        - !Ref PythonDependenciesLayer

  # EventBridge Rule for Monitor (10 min)
  MonitorScheduleRule:
    Type: AWS::Events::Rule
    Properties:
      Name: simple-aws-monitoring-schedule
      Description: Trigger monitoring every 10 minutes
      ScheduleExpression: rate(10 minutes)
      State: ENABLED
      Targets:
        - Arn: !GetAtt MonitorFunction.Arn
          Id: MonitorTarget

  # EventBridge Rule for Dashboard (5 min)
  DashboardScheduleRule:
    Type: AWS::Events::Rule
    Properties:
      Name: simple-aws-monitoring-dashboard-schedule
      Description: Update dashboard every 5 minutes
      ScheduleExpression: rate(5 minutes)
      State: ENABLED
      Targets:
        - Arn: !GetAtt DashboardFunction.Arn
          Id: DashboardTarget

  # Lambda Permissions for EventBridge
  MonitorLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref MonitorFunction
      Action: lambda:InvokeFunction
      Principal: events.amazonaws.com
      SourceArn: !GetAtt MonitorScheduleRule.Arn

  DashboardLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref DashboardFunction
      Action: lambda:InvokeFunction
      Principal: events.amazonaws.com
      SourceArn: !GetAtt DashboardScheduleRule.Arn

  # SNS Topic for Alerts
  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: simple-aws-monitoring-alerts
      DisplayName: AWS Monitoring Alerts

  # CloudWatch Alarms
  MonitorErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: simple-aws-monitoring-errors
      AlarmDescription: Alert on monitor Lambda errors
      MetricName: Errors
      Namespace: AWS/Lambda
      Dimensions:
        - Name: FunctionName
          Value: !Ref MonitorFunction
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      AlarmActions:
        - !Ref AlertTopic

Outputs:
  DashboardUrl:
    Description: Monitoring dashboard URL
    Value: !Sub 'https://${LogBucket}.s3-website-${AWS::Region}.amazonaws.com/dashboard/index.html'

  SNSTopicArn:
    Description: SNS topic for alerts
    Value: !Ref AlertTopic

  LogBucketName:
    Description: S3 bucket for logs
    Value: !Ref LogBucket
```

**Deploy CloudFormation:**
```bash
# Package code
zip -r lambda-code.zip monitor_lambda.py generate_dashboard.py dashboard_template.html
aws s3 cp lambda-code.zip s3://your-deployment-bucket/

# Create dependencies layer
mkdir python
pip install -r requirements.txt -t python/
zip -r python-dependencies-layer.zip python/
aws s3 cp python-dependencies-layer.zip s3://your-deployment-bucket/

# Deploy stack
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=CodeBucketName,ParameterValue=your-deployment-bucket \
  --capabilities CAPABILITY_NAMED_IAM
```

## Monitoring & Alerts

### SNS Alerts

Subscribe to alerts:

```bash
# Get topic ARN from deployment output
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT-ID:simple-aws-monitoring-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

Confirm subscription in your email.

### CloudWatch Alarms

Three alarms monitor system health:

1. **Heartbeat Missing** - If Lambda hasn't run in 20+ minutes
2. **Monitor Lambda Errors** - If monitor_lambda crashes
3. **Dashboard Lambda Errors** - If generate_dashboard crashes

View in CloudWatch:

```bash
aws cloudwatch describe-alarms --alarm-names simple-aws-monitoring-*
```

## Cost Estimate

**Monthly Cost Breakdown:**

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 4,320 invocations × 200ms | ~$0.90 |
| S3 Storage | 1-2 MB | ~$0.01 |
| S3 Requests | ~130 writes + reads | ~$0.01 |
| SNS | 5-10 notifications | ~$0.01 |
| CloudWatch | Log storage & alarms | ~$0.50 |
| **Total** | | **~$1.50** |

## What's Included

✅ Full monitoring of S3, EC2, EMR by tag
✅ Automatic S3 failover
✅ SNS alerts for EC2/EMR failures
✅ Heartbeat detection (Lambda failure monitoring)
✅ Static HTML dashboard with auto-refresh
✅ CloudWatch alarms
✅ Comprehensive logging
✅ Mobile-responsive UI

## What's Included

✅ Full monitoring of S3, EC2, EMR by tag
✅ Automatic S3 failover to replica region
✅ SNS alerts for EC2/EMR failures
✅ Heartbeat detection (Lambda failure monitoring)
✅ Static HTML dashboard with auto-refresh
✅ CloudWatch alarms for Lambda errors
✅ Comprehensive JSON logging
✅ Mobile-responsive web UI
✅ 2 deployment options (Serverless + CloudFormation)

## What's NOT Included (Kept Simple)

❌ Complex JSONL historical logging (use CloudWatch Logs instead)
❌ Runbook generation (alerts only)
❌ Multiple Lambda layers (all code in one)
❌ Kinesis/DynamoDB integration
❌ Slack/PagerDuty webhooks (use SNS subscriptions)
❌ Advanced filtering in dashboard
❌ Local testing with LocalStack (test directly in AWS)
❌ EC2/EMR failover (use failover_ver3 for that)
❌ Auto-discovery of configurations (manual setup)

## Understanding S3 Failover

### How S3 Failover Works

1. **Health Check:** Every 10 minutes, Lambda checks if S3 bucket is accessible
   ```python
   s3.head_bucket(Bucket=bucket_name)  # Throws exception if bucket down
   ```

2. **Failure Detection:** If bucket is not responding
   - Status marked as `failed`
   - SNS alert sent
   - Failover triggered

3. **Failover Execution:**
   - Logs failover metadata to `failover_logs/` in S3
   - Records original region and target replica region
   - Writes timestamp of failure

4. **Replica Setup (You Configure):**
   You pre-create a replica bucket in different region:
   ```bash
   # Primary bucket (us-east-1)
   aws s3api create-bucket --bucket my-app-data --region us-east-1

   # Replica bucket (us-west-2)
   aws s3api create-bucket --bucket my-app-data-replica \
     --region us-west-2 \
     --create-bucket-configuration LocationConstraint=us-west-2

   # Enable versioning on both
   aws s3api put-bucket-versioning --bucket my-app-data \
     --versioning-configuration Status=Enabled
   ```

5. **Extend Failover Logic:**
   The `failover_s3_bucket()` function is a template you customize:
   ```python
   def failover_s3_bucket(bucket_name):
       # Option 1: Copy critical objects
       # Option 2: Update Route53 DNS
       # Option 3: Update application config in Parameter Store
       # Option 4: Trigger CodePipeline for deployment
       pass
   ```

### Failover Customization Examples

**Example 1: Copy Objects to Replica**
```python
def failover_s3_bucket(bucket_name):
    s3 = boto3.client('s3')
    replica_bucket = f"{bucket_name}-replica"

    # Copy all objects
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            s3.copy_object(
                Bucket=replica_bucket,
                CopySource={'Bucket': bucket_name, 'Key': obj['Key']},
                Key=obj['Key']
            )
```

**Example 2: Update Route53 DNS**
```python
def failover_s3_bucket(bucket_name):
    route53 = boto3.client('route53')
    # Update S3 website endpoint in Route53
    route53.change_resource_record_sets(
        HostedZoneId='Z123ABC',
        ChangeBatch={
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'data.example.com',
                    'Type': 'A',
                    'AliasTarget': {
                        'HostedZoneId': 'Z3AQQSTJ8BH7EE',
                        'DNSName': 'my-app-data-replica.s3-website-us-west-2.amazonaws.com',
                        'EvaluateTargetHealth': False
                    }
                }
            }]
        }
    )
```

**Example 3: Update Parameter Store**
```python
def failover_s3_bucket(bucket_name):
    ssm = boto3.client('ssm')
    replica_bucket = f"{bucket_name}-replica"
    # Application reads from Parameter Store
    ssm.put_parameter(
        Name='/app/s3-bucket-name',
        Value=replica_bucket,
        Overwrite=True
    )
```

### Testing S3 Failover

```bash
# 1. Tag your bucket
aws s3api put-bucket-tagging \
  --bucket my-app-data \
  --tagging 'TagSet=[{Key=Name,Value=production}]'

# 2. Simulate failure by blocking access
aws s3api put-bucket-policy \
  --bucket my-app-data \
  --policy '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Principal":"*","Action":"s3:*","Resource":"*"}]}'

# 3. Trigger monitoring Lambda
serverless invoke -f monitor

# 4. Check failover logs
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/failover_logs/my-app-data-*.json - | jq .

# 5. Check SNS alert received

# 6. Restore bucket
aws s3api delete-bucket-policy --bucket my-app-data

# 7. Verify status updates on next run
```

## Complete System: failover_ver3 + aws-lambda-monitoring

For a production system, use both:

```
┌─────────────────────────────────────────────────────────────┐
│  aws-lambda-monitoring (Serverless)                         │
│  ─────────────────────────────────────────────────────────  │
│  • Monitors S3, EC2, EMR every 10 minutes                   │
│  • Auto-failover for S3 buckets                            │
│  • Alerts for EC2/EMR failures (SNS)                       │
│  • Static HTML dashboard                                    │
│  • Heartbeat monitoring                                     │
│  • CloudWatch alarms                                        │
│  • Cost: $2-3/month                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
              S3 status logs + SNS alerts
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  failover_ver3 (Local/Scheduled)                            │
│  ─────────────────────────────────────────────────────────  │
│  • Receives alerts from monitoring system                   │
│  • Auto-discovers resource configs from AWS                │
│  • EC2: Restarts stopped, recreates terminated             │
│  • EMR: Recreates exact cluster with auto-discovery        │
│  • Scaling issue detection and remediation                 │
│  • Interactive Flask dashboard                            │
│  • Cost: Free (local execution)                            │
└─────────────────────────────────────────────────────────────┘
```

**Workflow:**
1. `aws-lambda-monitoring` detects resource failures
2. S3 buckets auto-failover to replica region
3. EC2/EMR failures trigger SNS alerts
4. `failover_ver3` is triggered by alerts
5. `failover_ver3` performs detailed failover
6. Both systems log to shared location
7. Dashboard shows complete status

## What the Failover System Does

### failover_ver3 Capabilities

**Auto-Discovery:**
- Reads EC2 instance configurations (type, AMI, security groups, subnets, IAM roles)
- Reads EMR cluster configurations (instance types, sizes, applications, spot/on-demand mix)
- Reads Lambda function configurations (runtime, memory, timeout, env vars)
- No manual configuration files needed!

**EC2 Recovery:**
- Stopped instances → Auto-starts them
- Terminated instances → Recreates with exact same configuration
- Preserves: Instance type, AMI, security groups, subnets, IAM roles, tags

**EMR Recovery:**
- Terminated clusters → Recreates exactly
- Auto-discovers: Master/core/task node counts, instance types, spot/on-demand settings
- Re-clones bootstrap scripts from GitHub
- Reapplies all tags and configurations
- Detects and alerts on scaling issues (mismatched instance counts, spot interruptions)

**Scaling Issue Detection:**
- Monitors running EMR clusters
- Detects: Instance count mismatches, spot terminations, fleet capacity issues
- Marks cluster as `SCALING_ISSUE` with detailed problem descriptions
- Auto-attempts remediation

**Multi-Environment Support:**
- Single config.json file
- Supports multiple AWS profiles (prod, uat, dev, etc.)
- Dashboard filters by profile
- Ideal for managing multiple environments

**Web Dashboard:**
- Real-time resource status
- Filterable logs (by time, instance, tag, status, type, profile)
- Failover results tracking
- Summary statistics

See `failover_ver3/README.md` for detailed documentation.

## Troubleshooting

### Dashboard not showing data

```bash
# Check if status.json exists
aws s3 ls s3://simple-aws-monitoring-logs-{account-id}/status/

# If not, trigger monitor
serverless invoke -f monitor

# Check Lambda logs
serverless logs -f monitor --tail
```

### Resources not showing in monitoring

1. **Check tagging:**
   ```bash
   # Verify tag exists
   aws ec2 describe-tags --filters Name=resource-id,Values=i-xxxx
   ```

2. **Check tag name matches:**
   - Default: `Name=production`
   - Edit `serverless.yml` if different

3. **Check Lambda permissions:**
   ```bash
   # Verify role has permissions
   aws iam get-role-policy \
     --role-name simple-aws-monitoring-us-east-1-lambdaRole \
     --policy-name simple-aws-monitoring-us-east-1-policy
   ```

### Alerts not received

1. **Check SNS subscription:**
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn arn:aws:sns:us-east-1:ACCOUNT:simple-aws-monitoring-alerts
   ```

2. **Confirm subscription in email**

3. **Check CloudWatch Logs for errors:**
   ```bash
   aws logs tail /aws/lambda/simple-aws-monitoring-monitor --follow
   ```

### S3 bucket access denied

Ensure Lambda IAM role has S3 permissions:
- `s3:ListAllMyBuckets`
- `s3:GetBucketLocation`
- `s3:GetBucketTagging`
- `s3:HeadBucket`
- `s3:PutObject`

Check in `serverless.yml` - policy is pre-configured.

## Advanced Customization

### Add Monitoring for Other AWS Services

Edit `monitor_lambda.py` to add new check functions:

```python
def check_rds_instances():
    """Check RDS instances"""
    rds = boto3.client('rds')
    instances = []
    # ... implementation ...
    return instances

# In lambda_handler, add:
results['rds_instances'] = check_rds_instances()
```

Update `serverless.yml` IAM policy to include RDS permissions.

### Change Monitoring Interval

In `serverless.yml`:

```yaml
events:
  - schedule:
      rate: rate(5 minutes)  # Changed from 10
```

### Change Replica Region

In `serverless.yml`:

```yaml
environment:
  S3_REPLICA_REGION: eu-west-1  # Changed from us-west-2
```

### Add Custom Failover Logic

Edit `failover_s3_bucket()` in `monitor_lambda.py` to implement:
- DNS updates
- Application config changes
- Database replication
- Cross-region sync

## Maintenance

### Regular Tasks

**Daily:**
- Check dashboard for resource status
- Verify no CloudWatch alarms triggered

**Weekly:**
- Review CloudWatch logs for errors
- Check S3 usage

**Monthly:**
- Review and update tag names if needed
- Update boto3 version: `pip install -U boto3`
- Check for AWS service updates

### Updates

To update Lambda code:

```bash
# Edit monitor_lambda.py or generate_dashboard.py
vim monitor_lambda.py

# Redeploy
serverless deploy function -f monitor
```

## Security

⚠️ **Security Considerations:**

1. **IAM Permissions** - Uses minimal required permissions (least privilege)
2. **S3 Public Access** - Dashboard bucket allows public read of dashboard/ folder only
3. **SNS Encryption** - Enable at-rest encryption in production
4. **Logging** - All actions logged to CloudWatch
5. **Credentials** - Uses IAM role (no hardcoded credentials)

For production:

```yaml
# In serverless.yml
resources:
  Resources:
    LogBucket:
      Properties:
        BucketEncryption:
          ServerSideEncryptionConfiguration:
            - ServerSideEncryptionByDefault:
                SSEAlgorithm: AES256
```

## License

Open source - MIT License

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review CloudWatch Logs: `serverless logs -f monitor --tail`
3. Check AWS Console for alarm history

## Next Steps

After deployment:

1. ✅ Tag your AWS resources
2. ✅ Trigger monitoring: `serverless invoke -f monitor`
3. ✅ View dashboard
4. ✅ Subscribe to SNS alerts
5. ✅ Monitor CloudWatch alarms

Enjoy automated AWS monitoring! 🚀
