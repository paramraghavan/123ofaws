# S3 Failover & Integrated Monitoring Guide

This guide explains how the **aws-lambda-monitoring** system performs S3 auto-failover and integrates with the broader **failover_ver3** system.

## Quick Overview

### What This System Does

| Component | Does This | Frequency |
|-----------|-----------|-----------|
| **aws-lambda-monitoring** | Detects S3 bucket failures | Every 10 min |
| **S3 Auto-Failover** | Logs failover, initiates replica switch | On failure |
| **SNS Alerts** | Notifies about EC2/EMR failures | On failure |
| **failover_ver3** | Recovers EC2/EMR resources | On alert |

## S3 Failover Architecture

```
Primary S3 Bucket (us-east-1)
        ↓
   [FAIL] ← Lambda detects
        ↓
Failover Triggered:
  1. Log event to failover_logs/
  2. Copy objects to replica
  3. Update DNS/Parameter Store
        ↓
Replica S3 Bucket (us-west-2)
```

## Setup Instructions

### Step 1: Create S3 Buckets

```bash
# Primary bucket (where your app normally writes)
aws s3api create-bucket \
  --bucket my-app-data \
  --region us-east-1

# Replica bucket (for failover)
aws s3api create-bucket \
  --bucket my-app-data-replica \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# Enable versioning on both (recommended)
aws s3api put-bucket-versioning \
  --bucket my-app-data \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
  --bucket my-app-data-replica \
  --versioning-configuration Status=Enabled

# Tag primary bucket for monitoring
aws s3api put-bucket-tagging \
  --bucket my-app-data \
  --tagging 'TagSet=[{Key=Name,Value=production}]'
```

### Step 2: Configure Monitoring Lambda

Edit `serverless.yml`:

```yaml
provider:
  environment:
    TAG_NAME: production              # Matches your S3 bucket tag
    LOG_BUCKET: simple-aws-monitoring-logs-ACCOUNT_ID
    SNS_TOPIC_ARN: arn:aws:sns:us-east-1:ACCOUNT_ID:simple-aws-monitoring-alerts
    S3_REPLICA_REGION: us-west-2     # Your replica region
```

### Step 3: Implement Failover Logic

Edit `monitor_lambda.py` - customize the `failover_s3_bucket()` function:

#### Option A: Copy Objects to Replica

```python
def failover_s3_bucket(bucket_name):
    """Copy critical objects to replica bucket"""
    s3 = boto3.client('s3')
    replica_bucket = f"{bucket_name}-replica"

    try:
        # Get all objects
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)

        copy_count = 0
        for page in pages:
            for obj in page.get('Contents', []):
                try:
                    s3.copy_object(
                        Bucket=replica_bucket,
                        CopySource={'Bucket': bucket_name, 'Key': obj['Key']},
                        Key=obj['Key']
                    )
                    copy_count += 1
                except ClientError as e:
                    print(f"Error copying {obj['Key']}: {str(e)}")

        # Log result
        log_failover(bucket_name, replica_bucket, f"Copied {copy_count} objects")

    except Exception as e:
        print(f"Failover error: {str(e)}")
        raise


def log_failover(bucket_name, replica_bucket, details):
    """Log failover action"""
    s3 = boto3.client('s3')
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'failover_completed',
        'bucket': bucket_name,
        'replica_bucket': replica_bucket,
        'details': details
    }
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=f'failover_logs/{bucket_name}-{datetime.utcnow().timestamp()}.json',
        Body=json.dumps(log_entry, indent=2)
    )
```

#### Option B: Update Route53 DNS

```python
def failover_s3_bucket(bucket_name):
    """Update Route53 to point to replica bucket"""
    route53 = boto3.client('route53')
    replica_bucket = f"{bucket_name}-replica"

    try:
        # Update DNS record to replica bucket
        route53.change_resource_record_sets(
            HostedZoneId='Z1234567890ABC',  # Your hosted zone ID
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 's3-data.example.com',  # Your DNS name
                        'Type': 'A',
                        'AliasTarget': {
                            'HostedZoneId': 'Z3AQQSTJ8BH7EE',  # S3 website zone ID
                            'DNSName': f'{replica_bucket}.s3-website-us-west-2.amazonaws.com',
                            'EvaluateTargetHealth': False
                        }
                    }
                }]
            }
        )
        print(f"DNS updated to replica bucket: {replica_bucket}")
    except Exception as e:
        print(f"DNS update error: {str(e)}")
        raise
```

#### Option C: Update Parameter Store

```python
def failover_s3_bucket(bucket_name):
    """Update Parameter Store - application reads from here"""
    ssm = boto3.client('ssm')
    replica_bucket = f"{bucket_name}-replica"

    try:
        # Application reads this parameter
        ssm.put_parameter(
            Name='/myapp/s3-bucket-name',
            Value=replica_bucket,
            Overwrite=True,
            Description='S3 bucket for app data (failover)'
        )
        print(f"Parameter Store updated to: {replica_bucket}")
    except Exception as e:
        print(f"Parameter Store error: {str(e)}")
        raise
```

### Step 4: Deploy

```bash
# Using Serverless
cd aws-lambda-monitoring
serverless deploy

# OR Using CloudFormation
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=CodeBucketName,ParameterValue=your-bucket \
  --capabilities CAPABILITY_NAMED_IAM
```

## Testing S3 Failover

### Test 1: Simulate Bucket Failure

```bash
# Step 1: Block access to primary bucket
aws s3api put-bucket-policy \
  --bucket my-app-data \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::my-app-data/*"
    }]
  }'

# Step 2: Manually trigger monitoring Lambda
serverless invoke -f monitor

# Step 3: Check status
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/status/latest.json - | jq .s3_buckets

# Expected output:
# [
#   {
#     "name": "my-app-data",
#     "status": "failed",
#     "error": "..."
#   }
# ]

# Step 4: Check failover logs
aws s3 ls s3://simple-aws-monitoring-logs-ACCOUNT/failover_logs/

# Step 5: View the log file
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/failover_logs/my-app-data-*.json -

# Step 6: Restore bucket policy
aws s3api delete-bucket-policy --bucket my-app-data
```

### Test 2: Check Automatic Scheduling

```bash
# Monitoring runs every 10 minutes via EventBridge
# Check Lambda invocations:
aws lambda get-function-concurrency --function-name simple-aws-monitoring-monitor

# View CloudWatch logs:
serverless logs -f monitor --tail

# Or via AWS Console:
# CloudWatch > Log Groups > /aws/lambda/simple-aws-monitoring-monitor
```

### Test 3: SNS Alerts

```bash
# Subscribe to alerts email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:simple-aws-monitoring-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm in your email
# Then test failure scenario - you'll receive alert
```

## Integration with failover_ver3

When your system uses both monitoring and failover:

### Workflow

1. **aws-lambda-monitoring detects failure** (every 10 min)
   ```
   S3 bucket down → Failover triggered → SNS alert sent
   ```

2. **failover_ver3 receives alert** (via SNS)
   ```
   SNS → CloudWatch → failover_ver3 trigger
   ```

3. **failover_ver3 handles EC2/EMR**
   ```
   EC2 stopped → Start it
   EMR terminated → Recreate it (auto-discovered config)
   ```

4. **Both log to shared location**
   ```
   s3://LOG_BUCKET/status/latest.json       (monitoring)
   s3://LOG_BUCKET/failover_logs/           (failover events)
   ```

5. **Dashboard shows complete status**
   ```
   aws-lambda-monitoring dashboard + failover_ver3 dashboard
   ```

### Setup SNS Integration with failover_ver3

```bash
# 1. Get SNS topic ARN from monitoring stack
SNS_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name simple-aws-monitoring \
  --query 'Stacks[0].Outputs[?OutputKey==`SNSTopicArn`].OutputValue' \
  --output text)

# 2. Create CloudWatch alarm that triggers failover_ver3
# (failover_ver3 can be set up as SNS subscriber)
```

## Monitoring Dashboard

Access your dashboard:

```
https://simple-aws-monitoring-logs-{ACCOUNT_ID}.s3-website-us-east-1.amazonaws.com/dashboard/index.html
```

The dashboard shows:
- **S3 Buckets**: Status (available/failed), region
- **EC2 Instances**: State (running/stopped/terminated)
- **EMR Clusters**: Status (RUNNING/WAITING/TERMINATED)
- **Last Updated**: Timestamp of last monitoring run

## Troubleshooting

### Dashboard not updating

```bash
# Check if monitoring Lambda is running
aws logs tail /aws/lambda/simple-aws-monitoring-monitor --follow

# Check status file exists
aws s3 ls s3://simple-aws-monitoring-logs-ACCOUNT/status/

# View status content
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/status/latest.json - | jq .
```

### Failover not triggered

```bash
# 1. Check IAM permissions
aws iam get-role-policy \
  --role-name simple-aws-monitoring-us-east-1-lambdaRole \
  --policy-name simple-aws-monitoring-us-east-1-policy

# 2. Check Lambda logs for errors
serverless logs -f monitor --tail

# 3. Check bucket access manually
aws s3api head-bucket --bucket my-app-data
# If this fails, bucket is down

# 4. Verify tag exists
aws s3api get-bucket-tagging --bucket my-app-data
```

### Replica bucket not getting objects

```bash
# 1. Verify replica bucket exists
aws s3 ls s3://my-app-data-replica/

# 2. Check IAM permission for s3:PutObject
aws s3api put-object \
  --bucket my-app-data-replica \
  --key test.txt \
  --body /dev/null

# 3. Check function code has copy logic implemented
# Edit monitor_lambda.py failover_s3_bucket() function
```

## Cost Breakdown

| Service | Usage | Cost/Month |
|---------|-------|-----------|
| Lambda (monitor) | 4,320 invocations × 200ms | $0.90 |
| Lambda (dashboard) | 8,640 invocations × 100ms | $0.45 |
| S3 (logs bucket) | 1-2 MB + requests | $0.05 |
| SNS | 5-10 alerts | $0.01 |
| CloudWatch | Logs + alarms | $0.50 |
| **Total** | | **~$2/month** |

## Best Practices

1. **Test Failover in Dev First**
   ```bash
   # Create dev buckets
   aws s3api create-bucket --bucket my-app-data-dev
   # Test with dev Lambda
   ```

2. **Set Up Proper Alerting**
   - Subscribe to SNS topic
   - Test email delivery
   - Set up SMS alerts for critical systems

3. **Automate Replica Sync**
   - Use S3 Cross-Region Replication (CRR) for continuous sync
   - Or copy objects on every change

4. **Monitor the Monitoring System**
   - Watch heartbeat.json age
   - Set CloudWatch alarm if heartbeat > 20 min old
   - Ensure Lambda is running

5. **Document Your Failover**
   - Keep runbook for manual recovery
   - Document replica bucket names
   - Keep DNS change procedures documented

## Next Steps

1. ✅ Create S3 buckets (primary + replica)
2. ✅ Deploy monitoring system
3. ✅ Implement failover logic in monitor_lambda.py
4. ✅ Test failover in non-production environment
5. ✅ Set up SNS alerts
6. ✅ Deploy to production
7. ✅ Monitor dashboard regularly

See the main `README.md` for complete documentation!
