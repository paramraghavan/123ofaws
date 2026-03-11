# AWS Failover & Monitoring System - Complete Learning Guide

**A comprehensive guide for AWS learners to understand, deploy, and extend automated failover and monitoring systems.**

---

## Table of Contents

1. [Vision & Learning Goals](#vision--learning-goals)
2. [What is Failover & Why It Matters](#what-is-failover--why-it-matters)
3. [System Overview](#system-overview)
4. [Two Systems: Quick Comparison](#two-systems-quick-comparison)
5. [Getting Started (5 Minutes)](#getting-started-5-minutes)
6. [Deployment Guide](#deployment-guide)
7. [Understanding How It Works](#understanding-how-it-works)
8. [Tagging & Resource Management](#tagging--resource-management)
9. [Adding New Resources & Features](#adding-new-resources--features)
10. [Real-World Scenarios](#real-world-scenarios)
11. [Troubleshooting](#troubleshooting)
12. [Learning Path](#learning-path)

---

## Vision & Learning Goals

### 🎓 For AWS Learners

This guide helps you learn:

- **Failover Concepts:** Why it matters, how it works, when to use it
- **Serverless Monitoring:** Using Lambda for continuous resource monitoring
- **Infrastructure Automation:** Auto-detecting and recreating AWS resources
- **Event-Driven Architecture:** Using EventBridge, SNS, CloudWatch
- **Tagging Strategy:** Organizing and filtering AWS resources
- **System Extension:** Adding new services and monitoring capabilities
- **Production Patterns:** Best practices for reliability and cost optimization

### 🎯 Learning Approach

This documentation follows these principles:

1. **Learn by Doing:** Hands-on examples you can run immediately
2. **Start Simple:** Basic setup (5 minutes), then add complexity
3. **Understand the Why:** Not just "how" but "why" we do it this way
4. **Progressive Complexity:** Build from basic monitoring to advanced failover
5. **Real-World Examples:** Copy-paste ready, production-tested patterns
6. **Extensibility First:** Design allows easy addition of new services

---

## What is Failover & Why It Matters

### The Problem: Resource Failures

Your AWS resources can fail:

```
EC2 Instance → Crashes or runs out of memory → Application down
EMR Cluster  → Job fails, cluster terminates → Data pipeline breaks
S3 Bucket    → Connection issues → Data inaccessible
Database     → Replica lag, connection timeouts → Queries fail
```

**Impact:**
- Loss of revenue
- Customer dissatisfaction
- Data corruption
- Compliance violations

### The Solution: Automatic Failover

**Failover** = Automatically switch to a backup/replica when primary fails

```
Primary Resource (Down)
        ↓
    DETECT FAILURE
        ↓
Automatic Failover Action
        ↓
Backup/Replica Resource (Active)
        ↓
Service Restored (users don't notice!)
```

### Types of Failover

| Type | What Happens | Example |
|------|-------------|---------|
| **Active-Passive** | Backup takes over when primary fails | S3 → S3 replica |
| **Active-Active** | Both run simultaneously, traffic balanced | Multi-region deployment |
| **Health-Check Based** | Regular checks detect failures | Our monitoring system |
| **Automatic** | No human action needed | EC2 auto-start |
| **Manual** | Human decides when to failover | Runbooks & alerts |

### Your Two Failover Systems

```
┌─────────────────────────────────────────────────────────┐
│  aws-lambda-monitoring (Continuous Detection)           │
│  ├─ Runs every 10 minutes (serverless)                  │
│  ├─ Detects S3, EC2, EMR failures                       │
│  ├─ S3: Auto-failover (customizable)                    │
│  ├─ EC2/EMR: SNS alerts                                 │
│  └─ Cost: $2-3/month                                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  failover_ver3 (Intelligent Recovery)                   │
│  ├─ Runs on-demand (local Python)                       │
│  ├─ Receives SNS alerts from monitoring                 │
│  ├─ Auto-discovers resource configs from AWS            │
│  ├─ EC2: Auto-restart, EMR: Auto-recreate              │
│  └─ Cost: Free (your infrastructure)                    │
└─────────────────────────────────────────────────────────┘
```

---

## System Overview

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    YOUR AWS RESOURCES                         │
├──────────────────────────────────────────────────────────────┤
│  EC2 Instances | EMR Clusters | S3 Buckets | RDS | DynamoDB │
│  (tagged with Name=production, Name=uat, etc.)              │
└────┬─────────────────────────────────────────────────────────┘
     │
     │ Every 10 minutes
     ↓
┌──────────────────────────────────────────────────────────────┐
│         aws-lambda-monitoring (EventBridge Trigger)          │
│                                                               │
│  monitor_lambda.py:                                          │
│  ├─ Check all S3 buckets for accessibility                 │
│  ├─ Check all EC2 instances for "running" state             │
│  ├─ Check all EMR clusters for active state                │
│  │                                                           │
│  ├─ If S3 fails → Failover to replica (customizable)       │
│  ├─ If EC2/EMR fails → Send SNS alert                      │
│  │                                                           │
│  └─ Write status.json to S3                                │
└────┬──────────────────────────┬──────────────────┬──────────┘
     │                          │                  │
     ↓                          ↓                  ↓
┌──────────┐           ┌──────────────┐    ┌────────────┐
│  S3 Logs │           │  SNS Alerts  │    │ CloudWatch │
│          │           │              │    │  Alarms    │
│ status/  │           │   (Email)    │    │ (Heartbeat)│
│ latest   │           │              │    │            │
└──────────┘           └──────┬───────┘    └────────────┘
     │                        │
     │                        ↓
     │                 ┌──────────────────┐
     │                 │  failover_ver3   │
     │                 │  (Triggered)     │
     │                 │                  │
     │                 │ Receives SNS alert
     │                 │ Auto-discovers config
     │                 │ Restarts EC2      │
     │                 │ Recreates EMR     │
     │                 │ Logs results      │
     │                 └──────────────────┘
     │
     ↓
┌──────────────────────────────────────┐
│    dashboard/index.html (S3)         │
│    Generated every 5 minutes         │
│    Shows real-time status            │
│    Auto-refreshes                    │
└──────────────────────────────────────┘
```

### What Gets Monitored?

**S3 Buckets:**
- Accessibility (head_bucket test)
- Region
- Auto-failover to replica if down

**EC2 Instances:**
- Instance state (running/stopped/terminated)
- Instance type
- Availability zone
- Alert if not running

**EMR Clusters:**
- Cluster state (RUNNING/WAITING/TERMINATED)
- Cluster ID and name
- Alert if terminated

**Extensible to:**
- RDS databases
- DynamoDB tables
- SNS topics
- Lambda functions
- ElastiCache
- ECS services
- Kubernetes (EKS)
- Custom services

---

## Two Systems: Quick Comparison

### System 1: aws-lambda-monitoring

**What it does:**
- Monitors resources continuously (every 10 min)
- Detects failures immediately
- Auto-fails over S3 buckets
- Sends alerts for EC2/EMR failures
- Generates HTML dashboard

**When to use:**
- Need continuous monitoring
- Want serverless (no infrastructure)
- Need quick failure detection
- Cost-sensitive ($2-3/month)

**How it works:**
```
EventBridge Trigger → Lambda Runs → Check Resources → S3 Logs → Dashboard
     (10 min)         (Serverless)  (S3/EC2/EMR)     (Status)  (HTML)
```

**Key Files:**
- `aws-lambda-monitoring/monitor_lambda.py` - Main monitoring
- `aws-lambda-monitoring/generate_dashboard.py` - Dashboard generator
- `aws-lambda-monitoring/serverless.yml` - Deployment config

### System 2: failover_ver3

**What it does:**
- Responds to alerts from monitoring system
- Auto-discovers AWS resource configurations
- Restarts stopped EC2 instances
- Recreates terminated EMR clusters (exact copy)
- Detects and fixes EMR scaling issues

**When to use:**
- Need intelligent recovery (not just alerts)
- Want to recreate resources automatically
- Need multi-environment management
- Want detailed action logs

**How it works:**
```
SNS Alert → failover_ver3 Reads → Auto-Discovers Config → Takes Action
(From monitoring)   (Local Python)  (From AWS API)      (Restart/Recreate)
```

**Key Files:**
- `failover_ver3/failover_main.py` - Main orchestrator
- `failover_ver3/monitors.py` - Resource monitors
- `failover_ver3/failover.py` - Failover handlers
- `failover_ver3/config.json` - Configuration

### Using Them Together

```
aws-lambda-monitoring + failover_ver3 = Complete Failover System
```

**Workflow:**
1. Lambda monitors resources (continuous)
2. Detects S3 bucket failure → Auto-failover
3. Detects EC2 instance failure → SNS alert
4. failover_ver3 receives alert
5. Auto-discovers EC2 config
6. Restarts EC2 instance
7. Everything logged and tracked

---

## Getting Started (5 Minutes)

### Prerequisites

```bash
# Check you have these installed
aws --version              # AWS CLI
python --version          # Python 3.11+
node --version            # Node.js (for serverless deploy)
```

### Step 1: Clone/Navigate to Repository

```bash
cd /Users/paramraghavan/dev/123ofaws
```

### Step 2: Deploy Monitoring System

```bash
cd aws-lambda-monitoring
serverless deploy
```

Expected output:
```
Service deployed successfully
...
dashboard URL: https://simple-aws-monitoring-logs-ACCOUNT.s3-website-us-east-1.amazonaws.com/dashboard/index.html
```

### Step 3: Tag Your First Resource

```bash
# Tag an EC2 instance
aws ec2 create-tags \
  --resources i-0123456789abcdef0 \
  --tags Key=Name,Value=production
```

### Step 4: Subscribe to Alerts

```bash
# Get SNS topic ARN from deployment output
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:simple-aws-monitoring-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

Confirm subscription in your email!

### Step 5: View Dashboard

```bash
# Open in browser
https://simple-aws-monitoring-logs-ACCOUNT_ID.s3-website-us-east-1.amazonaws.com/dashboard/index.html
```

**Done!** Your monitoring system is now running. 🎉

---

## Deployment Guide

### Option 1: Serverless Framework (Recommended)

**Best for:** Teams with Node.js, development, rapid iteration

**Installation:**
```bash
npm install -g serverless
aws configure  # Configure AWS credentials
```

**Deploy:**
```bash
cd aws-lambda-monitoring
serverless deploy
```

**View outputs:**
```bash
serverless info --verbose
```

**See:** `aws-lambda-monitoring/README.md` → Installation & Deployment

### Option 2: CloudFormation

**Best for:** Enterprise, pure AWS, no external dependencies

**Deploy:**
```bash
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters file://params.json \
  --capabilities CAPABILITY_NAMED_IAM
```

**Monitor:**
```bash
aws cloudformation describe-stacks --stack-name simple-aws-monitoring
```

**See:** `aws-lambda-monitoring/README.md` → CloudFormation Approach

### Option 3: AWS SAM (AWS Serverless Application Model)

**Best for:** AWS-native serverless deployment

```bash
sam build
sam deploy --guided
```

### Configuration

Set your environment in `serverless.yml`:

```yaml
provider:
  environment:
    TAG_NAME: production      # What tag value to monitor
    LOG_BUCKET: simple-aws-monitoring-logs-${aws:accountId}
    S3_REPLICA_REGION: us-west-2  # For S3 failover
```

---

## Understanding How It Works

### How Monitoring Works

#### Step 1: EventBridge Trigger (Every 10 Minutes)

EventBridge is AWS's event scheduler:

```yaml
# In serverless.yml
events:
  - schedule:
      rate: rate(10 minutes)  # Run every 10 minutes
      enabled: true
```

**What happens:** Lambda function automatically invoked every 10 minutes, even if you're asleep!

#### Step 2: Lambda Checks Resources

```python
# In monitor_lambda.py
def lambda_handler(event, context):
    # Runs every 10 minutes

    # 1. Check S3 buckets
    s3_status = check_s3_buckets()

    # 2. Check EC2 instances
    ec2_status = check_ec2_instances()

    # 3. Check EMR clusters
    emr_status = check_emr_clusters()

    # 4. Return all status
    return {
        's3_buckets': s3_status,
        'ec2_instances': ec2_status,
        'emr_clusters': emr_status
    }
```

**Key Concept: Tag Filtering**

Lambda only monitors resources tagged with your tag:

```python
# In monitor_lambda.py
if has_matching_tag(resource_tags, TAG_NAME):  # TAG_NAME = "production"
    # Monitor this resource
```

So if you set `TAG_NAME: production`, only resources with tag `Name=production` are monitored.

#### Step 3: Check Implementation

**S3 Example:**
```python
def check_s3_buckets():
    s3 = boto3.client('s3')

    # Get all buckets
    buckets = s3.list_buckets()['Buckets']

    for bucket in buckets:
        # Get tags
        tags = s3.get_bucket_tagging(Bucket=bucket['Name'])

        # Check if matches TAG_NAME
        if matches_production_tag(tags):
            # Try to access bucket
            try:
                s3.head_bucket(Bucket=bucket['Name'])
                status = 'available'  # ✅ Success
            except:
                status = 'failed'      # ❌ Failure

            results.append({
                'name': bucket['Name'],
                'status': status
            })
```

**Key Learning:**
- `head_bucket` is a lightweight test to check if bucket is accessible
- If it fails (ClientError), we know bucket is down
- This is cheap and fast

#### Step 4: Handle Failures

**For S3 Failures:**
```python
if s3_status == 'failed':
    failover_s3_bucket(bucket_name)  # Execute failover
```

**For EC2/EMR Failures:**
```python
if ec2_status == 'stopped' or emr_status == 'terminated':
    send_sns_alert(failure_details)  # Send email alert
```

#### Step 5: Log Status to S3

```python
s3.put_object(
    Bucket=LOG_BUCKET,
    Key='status/latest.json',
    Body=json.dumps(results)
)
```

This creates: `s3://LOG_BUCKET/status/latest.json`

#### Step 6: Generate Dashboard

Every 5 minutes, another Lambda runs:

```python
# In generate_dashboard.py
def lambda_handler(event, context):
    # Read latest.json
    status = read_s3_file('status/latest.json')

    # Generate HTML
    html = generate_html(status)

    # Upload to S3
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key='dashboard/index.html',
        Body=html
    )
```

Now accessible at: `https://LOG_BUCKET.s3-website.amazonaws.com/dashboard/index.html`

### How Failover Works

#### S3 Failover

**Setup:**
```bash
# Create replica bucket
aws s3api create-bucket --bucket my-bucket-replica --region us-west-2
```

**Detection:**
```python
def check_s3_buckets():
    # head_bucket fails → status = 'failed'
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        # Bucket is down! Trigger failover
        failover_s3_bucket(bucket_name)
```

**Failover Action (Customizable):**

Option A - Copy Objects:
```python
def failover_s3_bucket(bucket_name):
    replica = f"{bucket_name}-replica"

    # Copy all objects
    for obj in s3.list_objects_v2(Bucket=bucket_name)['Contents']:
        s3.copy_object(
            Bucket=replica,
            CopySource=f'{bucket_name}/{obj["Key"]}',
            Key=obj['Key']
        )
```

Option B - Update DNS:
```python
def failover_s3_bucket(bucket_name):
    route53 = boto3.client('route53')

    # Point DNS to replica
    route53.change_resource_record_sets(
        HostedZoneId='Z123',
        ChangeBatch={
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 's3data.myapp.com',
                    'Type': 'A',
                    'AliasTarget': {
                        'DNSName': 'replica-bucket.s3.amazonaws.com'
                    }
                }
            }]
        }
    )
```

See `aws-lambda-monitoring/FAILOVER_GUIDE.md` for more examples.

#### EC2/EMR Failover (with failover_ver3)

**Monitoring Detects Failure:**
```
EC2 instance state = 'stopped' → Failure detected
```

**SNS Alert Sent:**
```python
sns.publish(
    TopicArn=SNS_TOPIC,
    Subject='EC2 Instance Failed',
    Message='i-0123456789 is stopped'
)
```

**failover_ver3 Receives Alert:**

You can configure failover_ver3 to subscribe to SNS topic:

```python
# In failover_ver3
def handle_ec2_failure(instance_id):
    # 1. Auto-discover current config
    ec2 = boto3.client('ec2')
    current = ec2.describe_instances(InstanceIds=[instance_id])
    config = extract_config(current)

    # 2. Restart if stopped
    if current['State'] == 'stopped':
        ec2.start_instances(InstanceIds=[instance_id])

    # 3. Recreate if terminated
    if current['State'] == 'terminated':
        new_instance = ec2.run_instances(
            ImageId=config['ImageId'],
            InstanceType=config['InstanceType'],
            # ... other config
        )
```

**Key Learning:** Auto-discovery means no manual config file needed!

### Understanding Costs

| Component | Cost | Why |
|-----------|------|-----|
| Lambda (monitor) | $0.90/mo | 4,320 invocations × 200ms |
| Lambda (dashboard) | $0.45/mo | 8,640 invocations × 100ms |
| S3 storage | $0.05/mo | ~2 MB of logs |
| SNS | $0.01/mo | ~10 alerts |
| CloudWatch | $0.50/mo | Logs and alarms |
| **Total** | **~$2/mo** | Very cost-effective! |

---

## Tagging & Resource Management

### Why Tagging Matters

Tags are **how the system knows which resources to monitor**:

```python
# In monitor_lambda.py
if has_matching_tag(resource.tags, TAG_NAME):  # TAG_NAME = "production"
    # Monitor this resource
```

**No tags = Not monitored!**

### Tagging Strategy

**Simple (Recommended for learning):**
```
Name = "production"
Name = "uat"
Name = "dev"
```

**Descriptive (For larger systems):**
```
Name = "production-web"
Name = "production-data"
Name = "uat-database"
```

**Enterprise (For complex organizations):**
```
Name = "production-web"
Environment = "prod"
Owner = "platform-team"
CostCenter = "engineering"
Application = "web-app"
Tier = "frontend"
```

### How to Tag Each Service

**EC2 Instances:**
```bash
aws ec2 create-tags --resources i-xxx --tags Key=Name,Value=production
```

**S3 Buckets:**
```bash
aws s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[{Key=Name,Value=production}]'
```

**EMR Clusters:**
```bash
aws emr add-tags --resource-id j-xxx --tags Key=Name,Value=production
```

**RDS Databases:**
```bash
aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:ACCOUNT:db:my-db \
  --tags Key=Name,Value=production
```

**DynamoDB Tables:**
```bash
aws dynamodb tag-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:ACCOUNT:table/my-table \
  --tags Key=Name,Value=production
```

**SNS Topics:**
```bash
aws sns tag-resource \
  --resource-arn arn:aws:sns:us-east-1:ACCOUNT:my-topic \
  --tags Key=Name,Value=production
```

**Lambda Functions:**
```bash
aws lambda tag-resource \
  --resource arn:aws:lambda:us-east-1:ACCOUNT:function:my-function \
  --tags Name=production
```

### Naming Convention Rules

| Rule | Good | Bad |
|------|------|-----|
| **Case** | `production` | `PRODUCTION` or `Production` |
| **Consistency** | Always `production` | Mix of `prod`, `production`, `PROD` |
| **Naming** | `production-web` | `prod_web` or `web-prod` |
| **Special chars** | `production-web` | `production.web` or `production_web` |

**KEY:** Tag values are **case-sensitive**! If you set `TAG_NAME: production` in serverless.yml, resources must have `Name=production` (lowercase).

### Managing Tags at Scale

**Find all untagged resources:**
```bash
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[?!Tags[?Key==`Name`]].InstanceId'
```

**Find resources by tag:**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=production"
```

**Update tags in bulk:**
```bash
# Tag all instances in an ASG
aws autoscaling create-or-update-tags \
  --tags \
    ResourceId=my-asg,ResourceType=auto-scaling-group,Key=Name,Value=production,PropagateAtLaunch=true
```

### Multi-Environment Tagging

**Production:**
```bash
aws ec2 create-tags --resources i-prod001 --tags Key=Name,Value=production
aws emr add-tags --resource-id j-prod001 --tags Key=Name,Value=production
```

**UAT:**
```bash
aws ec2 create-tags --resources i-uat001 --tags Key=Name,Value=uat
aws emr add-tags --resource-id j-uat001 --tags Key=Name,Value=uat
```

**Development:**
```bash
aws ec2 create-tags --resources i-dev001 --tags Key=Name,Value=dev
aws emr add-tags --resource-id j-dev001 --tags Key=Name,Value=dev
```

Then deploy monitoring for each:
```bash
# Production monitoring
serverless deploy --config serverless-prod.yml

# UAT monitoring
serverless deploy --config serverless-uat.yml

# Dev monitoring
serverless deploy --config serverless-dev.yml
```

See: `aws-lambda-monitoring/TAGGING_STRATEGY.md` for complete guide

---

## Adding New Resources & Features

### Adding New AWS Services

**Example: Monitor RDS Databases**

#### Step 1: Write Check Function

Add to `monitor_lambda.py`:

```python
def check_rds_databases():
    """Check RDS instances with matching tag"""
    rds = boto3.client('rds')
    databases = []

    try:
        response = rds.describe_db_instances()

        for db in response['DBInstances']:
            # Get tags
            tags = rds.list_tags_for_resource(
                ResourceName=db['DBResourceIdentifier']
            )

            # Check if matches TAG_NAME
            if has_matching_tag(tags['TagList'], TAG_NAME):
                databases.append({
                    'id': db['DBInstanceIdentifier'],
                    'status': db['DBInstanceStatus'],
                    'engine': db['Engine'],
                    'instance_type': db['DBInstanceClass']
                })

    except Exception as e:
        print(f"Error in check_rds_databases: {str(e)}")

    return databases
```

#### Step 2: Call in lambda_handler

```python
def lambda_handler(event, context):
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        's3_buckets': check_s3_buckets(),
        'ec2_instances': check_ec2_instances(),
        'emr_clusters': check_emr_clusters(),
        'rds_databases': check_rds_databases(),  # ADD THIS
    }
```

#### Step 3: Add to Dashboard

In `dashboard_template.html`:

```html
<h2>RDS Databases</h2>
<table id="rds-table"></table>

<script>
    renderTable('rds-table', status.rds_databases || [],
                ['id', 'status', 'engine', 'instance_type']);
</script>
```

#### Step 4: Update IAM Permissions

In `serverless.yml`:

```yaml
- Effect: Allow
  Action:
    - rds:DescribeDBInstances
    - rds:ListTagsForResource
  Resource: '*'
```

#### Step 5: Deploy

```bash
serverless deploy
```

#### Step 6: Tag RDS

```bash
aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:ACCOUNT:db:my-db \
  --tags Key=Name,Value=production
```

#### Step 7: Test

```bash
# Manually invoke
serverless invoke -f monitor

# Check results
aws s3 cp s3://LOG_BUCKET/status/latest.json - | jq .rds_databases

# View dashboard
# https://...s3-website.amazonaws.com/dashboard/index.html
```

### Complete Examples for Other Services

**DynamoDB:**
```python
def check_dynamodb_tables():
    dynamodb = boto3.client('dynamodb')
    tables = []
    for table_name in dynamodb.list_tables()['TableNames']:
        table = dynamodb.describe_table(TableName=table_name)
        tags = dynamodb.list_tags_of_resource(ResourceArn=table['TableArn'])
        if has_matching_tag(tags['Tags'], TAG_NAME):
            tables.append({
                'name': table_name,
                'status': table['Table']['TableStatus'],
                'items': table['Table']['ItemCount']
            })
    return tables
```

**SNS Topics:**
```python
def check_sns_topics():
    sns = boto3.client('sns')
    topics = []
    for topic in sns.list_topics()['Topics']:
        tags = sns.list_tags_for_resource(ResourceArn=topic['TopicArn'])
        if has_matching_tag(tags['Tags'], TAG_NAME):
            topics.append({
                'name': topic['TopicArn'].split(':')[-1],
                'status': 'active'
            })
    return topics
```

**Lambda Functions:**
```python
def check_lambda_functions():
    lambda_client = boto3.client('lambda')
    functions = []
    for func in lambda_client.list_functions()['Functions']:
        tags = lambda_client.list_tags(Resource=func['FunctionArn'])
        tags_list = [{'Key': k, 'Value': v} for k, v in tags.get('Tags', {}).items()]
        if has_matching_tag(tags_list, TAG_NAME):
            functions.append({
                'name': func['FunctionName'],
                'runtime': func['Runtime'],
                'memory': func['MemorySize']
            })
    return functions
```

See: `aws-lambda-monitoring/EXTENDING_SERVICES.md` for more examples

### Adding Custom Failover Logic

**Example: Custom S3 Failover**

Edit `monitor_lambda.py` → `failover_s3_bucket()`:

```python
def failover_s3_bucket(bucket_name):
    """Custom S3 failover logic"""

    # Option 1: Copy critical objects to replica
    replica_bucket = f"{bucket_name}-replica"
    s3 = boto3.client('s3')

    for obj in s3.list_objects_v2(Bucket=bucket_name)['Contents']:
        s3.copy_object(
            Bucket=replica_bucket,
            CopySource=f'{bucket_name}/{obj["Key"]}',
            Key=obj['Key']
        )

    # Option 2: Update Route53 DNS
    route53 = boto3.client('route53')
    route53.change_resource_record_sets(
        HostedZoneId='Z123',
        ChangeBatch={...}  # Update DNS to point to replica
    )

    # Option 3: Update Parameter Store
    ssm = boto3.client('ssm')
    ssm.put_parameter(
        Name='/myapp/s3-bucket',
        Value=replica_bucket,
        Overwrite=True
    )

    # Log the failover
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'bucket': bucket_name,
        'action': 'failover_completed'
    }
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=f'failover_logs/{bucket_name}.json',
        Body=json.dumps(log_entry)
    )
```

### Adding Kubernetes Monitoring

**Option A: Monitor EKS Clusters (AWS)**

```python
def check_eks_clusters():
    """Monitor EKS clusters"""
    eks = boto3.client('eks')
    clusters = []

    for cluster_arn in eks.list_clusters()['clusters']:
        cluster = eks.describe_cluster(name=cluster_arn)['cluster']

        tags = cluster.get('tags', {})
        if TAG_NAME in str(tags.values()):
            clusters.append({
                'name': cluster['name'],
                'status': cluster['status'],
                'version': cluster['version']
            })

    return clusters
```

**Option B: Monitor Inside Kubernetes**

Deploy a monitoring pod that reports to SNS/S3:

```python
# Python script running in K8s pod
import boto3
import json

def report_k8s_health():
    """Report K8s cluster health to AWS"""
    # Get health from K8s API
    health_data = {
        'healthy_pods': 95,
        'total_pods': 100,
        'nodes_ready': 5
    }

    # Report to S3
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key='k8s-status/cluster-health.json',
        Body=json.dumps(health_data)
    )
```

See: `aws-lambda-monitoring/EXTENDING_SERVICES.md` for more details

---

## Real-World Scenarios

### Scenario 1: E-Commerce Platform (Small Company)

**Resources:**
- 2 web servers (EC2)
- 1 database (RDS)
- 1 S3 bucket for images
- 1 EMR cluster for analytics

**Tagging:**
```
All production resources: Name=production
```

**Monitoring:**
```
# Deploy monitoring
cd aws-lambda-monitoring
serverless deploy

# Tag resources
aws ec2 create-tags --resources i-web1 i-web2 --tags Key=Name,Value=production
aws rds add-tags-to-resource --resource-name arn:aws:rds:...db:prod --tags Key=Name,Value=production
aws s3api put-bucket-tagging --bucket prod-images --tagging 'TagSet=[{Key=Name,Value=production}]'
aws emr add-tags --resource-id j-analytics --tags Key=Name,Value=production
```

**Failover:**
- S3 images → Replica in another region
- Web servers → Auto-restart if stopped
- Database → RDS multi-AZ (already built-in)
- Analytics → Alert ops team to restart manually

### Scenario 2: Multi-Environment SaaS

**Environments:**
- Production (prod-*)
- Staging (staging-*)
- Development (dev-*)

**Tagging Strategy:**
```
All prod: Name=production
All staging: Name=staging
All dev: Name=dev
```

**Deployment:**
```bash
# Production monitoring
TAG_NAME=production serverless deploy -c serverless-prod.yml

# Staging monitoring
TAG_NAME=staging serverless deploy -c serverless-uat.yml

# Dev monitoring
TAG_NAME=dev serverless deploy -c serverless-dev.yml
```

**Result:**
- 3 separate monitoring systems
- Each monitors only its own resources
- Each can have different alert settings

### Scenario 3: Data Pipeline Company

**Resources:**
- EMR clusters (for Spark jobs)
- S3 data lakes
- RDS database
- Lambda functions (data processing)
- SNS topics (notifications)

**Setup:**
```bash
# Monitor everything
aws ec2 create-tags --resources ... --tags Key=Name,Value=production
aws emr add-tags --resource-id ... --tags Key=Name,Value=production
aws s3api put-bucket-tagging --bucket ... --tagging 'TagSet=[{Key=Name,Value=production}]'
aws dynamodb tag-resource --resource-arn ... --tags Key=Name,Value=production
aws lambda tag-resource --resource ... --tags Name=production
aws sns tag-resource --resource-arn ... --tags Key=Name,Value=production
```

**Failover Strategy:**
- S3: Auto-failover to replica
- EMR: Alert + manual restart (expensive resource)
- Lambda: Alert + investigate (usually code issue)
- RDS: Use read replicas in different AZ

---

## Troubleshooting

### "Resources not showing in monitoring"

**Cause:** Resource not tagged with correct tag

**Fix:**
```bash
# Verify tag exists and matches TAG_NAME
aws ec2 describe-tags --filters "Name=resource-id,Values=i-xxx"

# Update TAG_NAME in serverless.yml
# Must match exactly (case-sensitive!)
```

### "No resources found in dashboard"

**Check 1: Verify deployment**
```bash
serverless info --verbose
# Should show deployed Lambda functions
```

**Check 2: Check Lambda logs**
```bash
serverless logs -f monitor --tail
# Look for errors
```

**Check 3: Manually invoke Lambda**
```bash
serverless invoke -f monitor --log
# See real-time output
```

**Check 4: Verify S3 bucket**
```bash
# Does status file exist?
aws s3 ls s3://simple-aws-monitoring-logs-ACCOUNT/status/

# What's in it?
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/status/latest.json - | jq .
```

### "Failover not triggering"

**Check 1: Verify S3 bucket is actually down**
```bash
aws s3api head-bucket --bucket my-bucket
# If this fails, bucket is down
```

**Check 2: Check failover code**
```python
# In monitor_lambda.py
# Is failover_s3_bucket() being called?
# Does it have the logic you want?
```

**Check 3: Check logs**
```bash
serverless logs -f monitor --tail
# Look for "failover_initiated" messages
```

### "EC2/EMR alerts not received"

**Check 1: SNS subscription**
```bash
# List subscriptions
aws sns list-subscriptions

# Confirm in your email
```

**Check 2: SNS topic**
```bash
# Does topic exist?
aws sns list-topics | grep simple-aws-monitoring

# Get topic ARN
aws cloudformation describe-stacks \
  --stack-name simple-aws-monitoring \
  --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`]'
```

**Check 3: IAM permissions**
```bash
# Does Lambda role have sns:Publish?
aws iam get-role-policy \
  --role-name simple-aws-monitoring-us-east-1-lambdaRole \
  --policy-name simple-aws-monitoring-us-east-1-policy
```

### "Dashboard not updating"

**Check 1: Dashboard generator**
```bash
serverless invoke -f dashboard --log
# Check for errors
```

**Check 2: S3 bucket permissions**
```bash
# Can Lambda write to bucket?
aws s3 ls s3://simple-aws-monitoring-logs-ACCOUNT/dashboard/
```

**Check 3: Browser cache**
```bash
# Clear cache or use incognito
# Force refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Linux/Windows)
```

---

## Learning Path

### Week 1: Understanding Concepts

**Day 1-2: AWS Fundamentals**
- [ ] Learn EC2 basics (instances, states, lifecycle)
- [ ] Learn S3 basics (buckets, objects, access)
- [ ] Learn IAM basics (roles, policies, permissions)
- [ ] Watch: AWS Architecture Overview videos

**Day 3: Failover Concepts**
- [ ] Read: "What is Failover & Why It Matters" (above)
- [ ] Understand: Active-passive, active-active failover
- [ ] Learn: Types of failures and recovery strategies
- [ ] Watch: AWS Resilience videos

**Day 4-5: This System**
- [ ] Read: "System Overview" (above)
- [ ] Read: "Two Systems: Quick Comparison" (above)
- [ ] Understand: How aws-lambda-monitoring works
- [ ] Understand: How failover_ver3 complements it

**Day 6-7: Hands-On Setup**
- [ ] Deploy monitoring system (5 min)
- [ ] Tag your first resource
- [ ] Subscribe to SNS alerts
- [ ] View dashboard

### Week 2: Hands-On Deployment

**Day 1: Deploy Monitoring**
- [ ] Follow: "Getting Started (5 Minutes)"
- [ ] Deploy aws-lambda-monitoring
- [ ] Tag 5 resources
- [ ] View dashboard with real data

**Day 2: Understanding Tags**
- [ ] Read: "Tagging & Resource Management" (above)
- [ ] Read: `aws-lambda-monitoring/TAGGING_STRATEGY.md`
- [ ] Create tagging policy for your environment
- [ ] Tag resources by environment (prod, uat, dev)

**Day 3: Deploy Failover System**
- [ ] Read: `failover_ver3/README.md`
- [ ] Create `config.json`
- [ ] Test locally: `python failover_main.py --mode monitor`
- [ ] View web dashboard

**Day 4: Test Failures**
- [ ] Scenario 1: Stop EC2 instance
  - [ ] Watch monitoring detect it
  - [ ] Receive email alert
  - [ ] Run failover_ver3 to restart
  - [ ] See it come back online
- [ ] Scenario 2: Simulate S3 failure
  - [ ] Block S3 bucket access
  - [ ] Watch failover trigger
  - [ ] Restore bucket

**Day 5: Alerting & Actions**
- [ ] Set up email alerts
- [ ] Set up Slack integration (optional)
- [ ] Create runbook for manual failover
- [ ] Test alert workflow

**Day 6-7: Review & Documentation**
- [ ] Document your deployment
- [ ] Create runbook for your team
- [ ] Review costs
- [ ] Plan for production rollout

### Week 3: Extension & Customization

**Day 1: Add New Services**
- [ ] Read: `aws-lambda-monitoring/EXTENDING_SERVICES.md`
- [ ] Add RDS monitoring
- [ ] Add DynamoDB monitoring
- [ ] Deploy and test

**Day 2: Custom Failover Logic**
- [ ] Read: `aws-lambda-monitoring/FAILOVER_GUIDE.md`
- [ ] Implement S3 failover strategy
- [ ] Choose: Copy objects, Update DNS, or Parameter Store
- [ ] Test failover end-to-end

**Day 3: Multi-Environment**
- [ ] Deploy separate monitoring for prod/uat/dev
- [ ] Configure different failover rules per environment
- [ ] Test isolation (prod failure doesn't affect dev)

**Day 4: Integration**
- [ ] Integrate monitoring with incident management
- [ ] Add custom webhooks (optional)
- [ ] Create dashboards in CloudWatch (optional)

**Day 5: Optimization**
- [ ] Review costs
- [ ] Optimize Lambda memory/timeout
- [ ] Consider caching strategies
- [ ] Plan for scale

**Day 6-7: Production Readiness**
- [ ] Create deployment checklist
- [ ] Document all procedures
- [ ] Train your team
- [ ] Deploy to production!

### Recommended Reading Order

1. **Start:** This document (you're reading it!)
2. **Concepts:**
   - `aws-lambda-monitoring/SYSTEM_OVERVIEW.md` - Architecture
   - `aws-lambda-monitoring/README.md` - Complete reference
3. **Tagging:**
   - `aws-lambda-monitoring/TAGGING_STRATEGY.md` - Comprehensive guide
   - `failover_ver3/config.json` - See how it's configured
4. **Failover:**
   - `aws-lambda-monitoring/FAILOVER_GUIDE.md` - S3 failover patterns
   - `failover_ver3/README.md` - Intelligent failover system
5. **Extension:**
   - `aws-lambda-monitoring/EXTENDING_SERVICES.md` - Add new services
   - `aws-lambda-monitoring/CONFIGURATION_REFERENCE.md` - Config options

---

## Key Learnings Summary

### Core Concepts

| Concept | What It Is | Why It Matters |
|---------|-----------|-----------------|
| **Failover** | Automatic switch to backup when primary fails | Keeps system running even with failures |
| **Tagging** | Key-value pairs on resources | Lets system know what to monitor |
| **Auto-Discovery** | Reading configs from AWS API | No manual config file needed |
| **Event-Driven** | Lambda runs on schedule, triggered by EventBridge | Serverless, cost-effective, reliable |
| **Health Check** | Test if resource is working (head_bucket, describe_instances) | Detects failures early |
| **Active-Passive** | One active, one ready for backup | Cost-effective failover |

### Best Practices

1. **Tag Early:** Tag resources at creation time, not after
2. **Consistent Naming:** Use same tag values across environment
3. **Test Failover:** Don't just assume it works - test it
4. **Monitor the Monitor:** Use CloudWatch alarms on Lambda heartbeat
5. **Document Procedures:** Write runbooks for manual intervention
6. **Review Costs:** Monitor Lambda and S3 costs monthly
7. **Regular Audits:** Check for untagged or misconfigured resources

### What You've Learned

After going through this guide, you should understand:

- ✅ What failover is and why it's important
- ✅ How the monitoring system detects failures
- ✅ How failover responds to failures
- ✅ How to tag resources for monitoring
- ✅ How to extend the system to new services
- ✅ How to customize failover logic
- ✅ How to set up multi-environment monitoring
- ✅ How to troubleshoot common issues

---

## Next Steps

### For Immediate Setup (Today)
1. Deploy aws-lambda-monitoring: `serverless deploy`
2. Tag your first resource
3. Subscribe to SNS alerts
4. View dashboard

### For This Week
1. Read all documentation
2. Deploy to dev/uat environments
3. Test failure scenarios
4. Create runbooks

### For This Month
1. Deploy failover_ver3
2. Add custom failover logic
3. Add new services to monitoring
4. Train your team

### For Production
1. Deploy to production environment
2. Set up incident management integration
3. Create monitoring dashboards
4. Document everything
5. Do disaster recovery drills

---

## Resources & Documentation

### In This Repository

```
aws-lambda-monitoring/
├── INDEX.md                         # Navigation guide
├── SYSTEM_OVERVIEW.md              # High-level overview
├── README.md                       # Complete reference
├── FAILOVER_GUIDE.md              # S3 failover setup
├── CONFIGURATION_REFERENCE.md     # Configuration options
├── TAGGING_STRATEGY.md            # Comprehensive tagging guide
├── EXTENDING_SERVICES.md          # Add new services
├── monitor_lambda.py              # Main monitoring code
├── generate_dashboard.py          # Dashboard generator
├── serverless.yml                 # Deployment config
└── requirements.txt               # Dependencies

failover_ver3/
├── README.md                      # Complete guide
├── config.json                    # Configuration
├── failover_main.py              # Main orchestrator
├── monitors.py                   # Resource monitors
└── failover.py                   # Failover handlers
```

### External Resources

- [AWS Architecture Best Practices](https://aws.amazon.com/architecture/)
- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [AWS Resilience Hub](https://aws.amazon.com/resilience-hub/)
- [AWS Systems Manager](https://aws.amazon.com/systems-manager/)
- [Boto3 Documentation](https://boto3.amazonaws.com/)

---

## Getting Help

### Documentation

- **Can't understand tagging?** → `TAGGING_STRATEGY.md`
- **Want to add a service?** → `EXTENDING_SERVICES.md`
- **Need S3 failover examples?** → `FAILOVER_GUIDE.md`
- **Full reference?** → `README.md`
- **Specific configuration?** → `CONFIGURATION_REFERENCE.md`

### Debugging

- **Check Lambda logs:** `serverless logs -f monitor --tail`
- **Manually invoke:** `serverless invoke -f monitor --log`
- **Check status:** `aws s3 cp s3://LOG_BUCKET/status/latest.json - | jq .`
- **View dashboard:** Open in browser

### Questions?

1. Search documentation for your question
2. Check troubleshooting section
3. Review CloudWatch logs for errors
4. Test with simpler scenario first

---

## Conclusion

You now have:

✅ **Complete monitoring system** - Detects failures automatically
✅ **Automatic failover** - Responds to failures without human action
✅ **Visual dashboard** - See status of all resources in real-time
✅ **Extensible architecture** - Easy to add new services
✅ **Production-ready code** - Error handling, logging, security
✅ **Comprehensive documentation** - Learn and understand every part
✅ **Cost-effective** - ~$2-3/month for monitoring
✅ **AWS-native** - Uses services you already pay for

### You're Ready to:

- ✅ Monitor your AWS resources automatically
- ✅ Detect failures in minutes
- ✅ Auto-failover S3 buckets
- ✅ Alert your team for EC2/EMR failures
- ✅ Add monitoring for new services
- ✅ Customize failover behavior
- ✅ Manage multi-environment setups
- ✅ Learn AWS best practices

**Happy monitoring and failover! 🚀**

---

**Last Updated:** March 2026
**Status:** Production Ready
**Version:** 1.0
**Audience:** AWS Learners, DevOps Engineers, Cloud Architects
