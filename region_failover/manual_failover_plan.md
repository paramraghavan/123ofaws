# Manual Failover Plan: us-east-1 → us-east-2
## Based on Your Exact Requirements from notes.md

**Your Scenario**:
- ETL pipelines triggered by S3 file uploads
- Files ingested into Snowflake
- Snowflake replicated east-1 → east-2
- Upstream systems write to east-1 S3 bucket
- Lambda, Spark, Python jobs processing files
- Need to switch to east-2 with minimal upstream changes

---

## HIGH-LEVEL FAILOVER FLOW

### Before Failover

```
┌─────────────────────────────────────────┐
│ PRODUCTION - us-east-1 (ACTIVE)        │
├─────────────────────────────────────────┤
│                                         │
│ Upstream Systems                        │
│       ↓ (write files)                   │
│                                         │
│ S3 Bucket: etl-data-us-east-1          │
│       ↓ (trigger Lambda)                │
│                                         │
│ Lambda/Python/Spark Jobs                │
│       ↓ (process & load)                │
│                                         │
│ Snowflake (east-1)                     │
│       ↓ (replicate)                     │
│                                         │
│ Snowflake (east-2) [READ-ONLY REPLICA] │
│                                         │
└─────────────────────────────────────────┘
```

### During Failover (Key Steps)

```
Step 1: DRAIN east-1
        - Stop accepting new files
        - Wait for in-flight jobs to complete
        - Disable S3 trigger on east-1

Step 2: FINALIZE east-1 DATA
        - Force final Snowflake replication (east-1 → east-2)
        - Ensure all data is in east-2 Snowflake

Step 3: SWITCH TO east-2
        - Update code to use ACTIVE_REGION = "us-east-2"
        - Enable S3 trigger on east-2
        - Promote east-2 Snowflake from replica to primary

Step 4: REDIRECT UPSTREAM
        - Configure upstream to write to east-2 S3 bucket
        - (Or keep writing to east-1, with sync mechanism)

Step 5: REVERSE REPLICATION
        - Change Snowflake replication: east-2 → east-1
        - (For disaster recovery, maintain replica in east-1)
```

### After Failover

```
┌─────────────────────────────────────────┐
│ PRODUCTION - us-east-2 (ACTIVE)        │
├─────────────────────────────────────────┤
│                                         │
│ Upstream Systems                        │
│       ↓ (write files)                   │
│                                         │
│ S3 Bucket: etl-data-us-east-2          │
│       ↓ (trigger Lambda)                │
│                                         │
│ Lambda/Python/Spark Jobs                │
│       ↓ (process & load)                │
│                                         │
│ Snowflake (east-2) [ACTIVE/PRIMARY]    │
│       ↓ (replicate)                     │
│                                         │
│ Snowflake (east-1) [READ-ONLY REPLICA] │
│                                         │
└─────────────────────────────────────────┘
```

---

## DETAILED IMPLEMENTATION PLAN

### PHASE 1: PRE-FAILOVER PREPARATION (1-2 weeks before)

#### 1.1 Code Changes (Region-Agnostic Implementation)

**Requirement from notes**: "can we have placeholder for region name like `<region>` and update the regions run time base on the detected the region"

**Solution**: Create `region_config.py` and use it everywhere

```python
# region_config.py
import os
import boto3
from functools import lru_cache

class RegionConfig:
    """Configuration for each region"""
    S3_BUCKETS = {
        "us-east-1": "etl-data-us-east-1",
        "us-east-2": "etl-data-us-east-2",
    }

    SNS_TOPICS = {
        "us-east-1": "arn:aws:sns:us-east-1:ACCOUNT_ID:etl-notifications",
        "us-east-2": "arn:aws:sns:us-east-2:ACCOUNT_ID:etl-notifications",
    }

    SQS_QUEUES = {
        "us-east-1": "https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/etl-jobs",
        "us-east-2": "https://sqs.us-east-2.amazonaws.com/ACCOUNT_ID/etl-jobs",
    }

    SNOWFLAKE_CONFIG = {
        "us-east-1": {
            "account": "xy12345",
            "warehouse": "COMPUTE_WH",
            "database": "ANALYTICS"
        },
        "us-east-2": {
            "account": "xy12345",  # Same account
            "warehouse": "COMPUTE_WH",
            "database": "ANALYTICS"
        }
    }

def get_active_region() -> str:
    """Get active region from environment or DynamoDB"""
    # Try environment variable first (set by operator)
    region = os.getenv("ACTIVE_REGION")
    if region:
        return region

    # Try DynamoDB Global Table
    try:
        dynamodb = boto3.client('dynamodb')
        response = dynamodb.get_item(
            TableName='etl-active-region',
            Key={'config_key': {'S': 'ACTIVE_REGION'}}
        )
        if 'Item' in response:
            return response['Item']['value']['S']
    except:
        pass

    # Default
    return "us-east-1"

def get_s3_bucket() -> str:
    """Get S3 bucket for active region"""
    region = get_active_region()
    return RegionConfig.S3_BUCKETS[region]

def get_sns_topic() -> str:
    """Get SNS topic ARN for active region"""
    region = get_active_region()
    return RegionConfig.SNS_TOPICS[region]

def get_sqs_queue() -> str:
    """Get SQS queue URL for active region"""
    region = get_active_region()
    return RegionConfig.SQS_QUEUES[region]

def get_snowflake_config() -> dict:
    """Get Snowflake config for active region"""
    region = get_active_region()
    return RegionConfig.SNOWFLAKE_CONFIG[region]

def get_boto3_client(service: str):
    """Create boto3 client for active region"""
    region = get_active_region()
    return boto3.client(service, region_name=region)
```

**Answers from notes:**
- "The topic name and queue name are unique across aws?" → **No, they're region-specific**. Topic ARN: `arn:aws:sns:REGION:ACCOUNT:name`. Queue URL: `https://sqs.REGION.amazonaws.com/ACCOUNT/name`
- "can we use the same topic name and queue name in different regions?" → **Yes, same name, different ARNs/URLs**

#### 1.2 Update Lambda Functions

```python
# Lambda handler - region-agnostic
from region_config import get_active_region, get_s3_bucket, get_boto3_client, get_sns_topic

def lambda_handler(event, context):
    """Lambda handler for S3 trigger"""

    region = get_active_region()
    bucket = get_s3_bucket()

    print(f"Processing in region: {region}")
    print(f"Using bucket: {bucket}")

    # Create S3 client for active region
    s3 = get_boto3_client('s3')

    # Get object from S3
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    obj = s3.get_object(Bucket=source_bucket, Key=key)
    data = obj['Body'].read()

    # Process and load to Snowflake
    # ... your processing logic ...

    # Send notification
    sns = get_boto3_client('sns')
    sns.publish(
        TopicArn=get_sns_topic(),
        Subject=f"ETL Complete - {region}",
        Message=f"Processed file: {key}"
    )

    return {'statusCode': 200, 'region': region}
```

#### 1.3 Update Python Edge Node Jobs

```python
# Edge node job - region-agnostic
from region_config import get_active_region, get_s3_bucket, get_snowflake_config, get_boto3_client

def process_etl_job():
    """Python job triggered via AWS Systems Manager"""

    region = get_active_region()
    bucket = get_s3_bucket()
    sf_config = get_snowflake_config()

    print(f"Processing in region: {region}")

    # Download from S3
    s3 = get_boto3_client('s3')
    response = s3.list_objects_v2(Bucket=bucket, Prefix='input/')

    # Load to Snowflake
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=sf_config['account'],
        user='USERNAME',
        password='PASSWORD',
        database=sf_config['database'],
        warehouse=sf_config['warehouse']
    )

    cursor = conn.cursor()
    # ... load data ...
    conn.close()

if __name__ == "__main__":
    process_etl_job()
```

#### 1.4 Update PySpark Jobs

```python
# Spark job - region-agnostic
from region_config import get_active_region, get_s3_bucket, get_boto3_client

def main():
    """Spark job for ETL processing"""

    from pyspark.sql import SparkSession

    region = get_active_region()
    bucket = get_s3_bucket()

    print(f"Spark job running in region: {region}")

    # Create Spark session
    spark = SparkSession.builder \
        .appName(f"etl-{region}") \
        .getOrCreate()

    # Configure S3 for active region
    spark.sparkContext._jsc.hadoopConfiguration().set(
        "fs.s3a.endpoint",
        f"https://s3.{region}.amazonaws.com"
    )

    # Read from region-specific bucket
    input_path = f"s3a://{bucket}/input/"
    df = spark.read.parquet(input_path)

    # Process
    processed = df.filter(df.id > 0)

    # Write to output
    output_path = f"s3a://{bucket}/output/"
    processed.write.parquet(output_path, mode='overwrite')

    print(f"Completed in {region}")

if __name__ == "__main__":
    main()
```

#### 1.5 Deploy Code to Both Regions

```bash
# Deploy to us-east-1
./deploy.sh us-east-1

# Deploy to us-east-2
./deploy.sh us-east-2

# Both versions have region_config.py
# On failover, just change ACTIVE_REGION environment variable
```

#### 1.6 Create DynamoDB Global Table for Configuration

```bash
# Optional but recommended - for runtime region switching

# Create table in us-east-1
aws dynamodb create-table \
  --table-name etl-active-region \
  --attribute-definitions AttributeName=config_key,AttributeType=S \
  --key-schema AttributeName=config_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamViewType=NEW_AND_OLD_IMAGES \
  --region us-east-1

# Create global table
aws dynamodb create-global-table \
  --global-table-name etl-active-region \
  --replication-group RegionName=us-east-1 RegionName=us-east-2 \
  --region us-east-1

# Initialize
aws dynamodb put-item \
  --table-name etl-active-region \
  --item 'config_key={S=ACTIVE_REGION},value={S=us-east-1}' \
  --region us-east-1
```

---

### PHASE 2: FAILOVER DAY (The Actual Switch)

#### 2.1 Pre-Failover Checklist (1 hour before)

```
□ Verify resources exist in both regions
  □ S3 buckets: etl-data-us-east-1 and etl-data-us-east-2
  □ Lambda functions deployed in both regions
  □ SNS topics exist in both regions
  □ SQS queues exist in both regions
  □ Snowflake replicas are in sync

□ Verify upstream systems ready
  □ Test writing to east-2 S3 bucket
  □ Verify no conflicts with east-1 writing

□ Monitoring ready
  □ CloudWatch dashboards for both regions
  □ Snowflake query editor open
  □ S3 access logs monitoring

□ Backup configuration
  □ Save current ACTIVE_REGION = "us-east-1"
  □ Save Snowflake replication direction
  □ Document current S3 trigger configuration
```

#### 2.2 STEP 1: Drain In-Flight Jobs from east-1 (10 minutes)

**Answer from notes**: "do we turn off trigger in s3 or down tell upstream to write to s3 bucket of new region"

**Solution**: Stop accepting NEW files, wait for in-flight jobs to complete

```bash
# Stop S3 trigger on east-1 (disable, don't delete)
aws s3api put-bucket-notification-configuration \
  --bucket etl-data-us-east-1 \
  --notification-configuration '{}' \
  --region us-east-1

# Verify it's disabled
aws s3api get-bucket-notification-configuration \
  --bucket etl-data-us-east-1 \
  --region us-east-1
# Should be empty

# Wait for in-flight Lambda/Python/Spark jobs to complete
# Monitor CloudWatch logs:
aws logs tail /aws/lambda/your-function --follow --region us-east-1

# Wait until no new invocations appear (typically 2-5 minutes)
```

#### 2.3 STEP 2: Final Snowflake Replication (5 minutes)

**Requirement from notes**: "Once all jobs are done on east-1, force replicate snowflake from east-1 to east-2"

```sql
-- In Snowflake (primary us-east-1)

-- Force immediate replication
ALTER DATABASE ANALYTICS REFRESH;

-- Monitor replication lag
SELECT
    REPLICATION_PHASE,
    REPLICATION_LAG_MS,
    LAST_REFRESH_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.REPLICATION_USAGE_HISTORY
WHERE DATABASE_NAME = 'ANALYTICS'
ORDER BY LAST_REFRESH_TIME DESC
LIMIT 1;

-- Wait for lag to be < 1000 ms (typically <100ms)
-- Verify all rows in east-1 are replicated to east-2
SELECT COUNT(*) FROM ANALYTICS.PUBLIC.my_table;
-- Note this count
```

#### 2.4 STEP 3: Switch to us-east-2 (5 minutes)

**Requirement from notes**: "We point will etl to s3 on east-2, what is the standard practice"

**Answer**: Update ACTIVE_REGION to us-east-2 in ONE place

```bash
# Option A: Update DynamoDB (if using it)
aws dynamodb put-item \
  --table-name etl-active-region \
  --item 'config_key={S=ACTIVE_REGION},value={S=us-east-2}' \
  --region us-east-1

# Verify replication to us-east-2
aws dynamodb get-item \
  --table-name etl-active-region \
  --key 'config_key={S=ACTIVE_REGION}' \
  --region us-east-2
# Should show: value = "us-east-2"

# Option B: Update environment variables manually
# In Lambda:
aws lambda update-function-configuration \
  --function-name your-function \
  --environment Variables="ACTIVE_REGION=us-east-2" \
  --region us-east-1

# On edge nodes:
# SSH and: export ACTIVE_REGION=us-east-2

# In EMR:
# Update spark-submit environment or configuration
```

#### 2.5 STEP 4: Enable S3 Trigger on east-2 (5 minutes)

**Requirement from notes**: "The ingestion pipeline triggers on east-2"

```bash
# Create notification configuration for east-2
cat > s3-notification-config.json << 'EOF'
{
  "LambdaFunctionConfigurations": [{
    "LambdaFunctionArn": "arn:aws:lambda:us-east-2:ACCOUNT_ID:function:your-function",
    "Events": ["s3:ObjectCreated:*"],
    "Filter": {
      "Key": {
        "FilterRules": [
          {"Name": "prefix", "Value": "input/"}
        ]
      }
    }
  }]
}
EOF

# Enable trigger on east-2
aws s3api put-bucket-notification-configuration \
  --bucket etl-data-us-east-2 \
  --notification-configuration file://s3-notification-config.json \
  --region us-east-2

# Verify it's enabled
aws s3api get-bucket-notification-configuration \
  --bucket etl-data-us-east-2 \
  --region us-east-2
# Should show Lambda trigger configured

# Grant S3 permission to invoke Lambda in us-east-2
aws lambda add-permission \
  --function-name your-function \
  --statement-id AllowS3Invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::etl-data-us-east-2 \
  --region us-east-2
```

#### 2.6 STEP 5: Promote east-2 Snowflake (5 minutes)

**Requirement from notes**: "Stop replication and change rule to replicate from east-2 to east-1 snowflake"

```sql
-- In Snowflake PRIMARY account (still us-east-1 for now)

-- If using database replication, promote east-2 replica
-- (If using account-level replication, different steps)

-- Option A: Database Replication
-- In SECONDARY account (us-east-2):
ALTER DATABASE ANALYTICS PROMOTE;

-- Verify it's now primary in us-east-2
SHOW REPLICATION DATABASES;
-- Should show PRIMARY_REPLICA = FALSE for ANALYTICS

-- Option B: Check if it worked
-- In us-east-2:
INSERT INTO ANALYTICS.PUBLIC.my_table VALUES (...);
-- Should succeed (no longer read-only)
```

#### 2.7 STEP 6: Reverse Replication (5 minutes)

**Requirement from notes**: "reverse replication from east-2 to east-1"

```sql
-- In Snowflake PRIMARY account (now us-east-2)

-- Set up replication back to east-1 (for DR)
ALTER DATABASE ANALYTICS
ENABLE REPLICATION TO ACCOUNT eastone.us-east-1;

-- Monitor replication
SELECT * FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.REPLICATION_STATUS());

-- Verify east-1 is now replica
-- In us-east-1:
SELECT IS_REPLICA FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASES
WHERE DATABASE_NAME = 'ANALYTICS';
-- Should return TRUE (is now replica)
```

#### 2.8 STEP 7: Redirect Upstream Systems (5-30 minutes)

**Requirement from notes**: "Upstream jobs write to s3 bucket - how can we switch regions with asking upstream jobs to change"

**Best Practice Options**:

**Option A: Upstream writes to BOTH buckets (Recommended for safety)**
```
Upstream → etl-data-us-east-1 (continues writing)
        → etl-data-us-east-2 (also writes now)

East-1 Lambda: DISABLED (no trigger)
East-2 Lambda: ENABLED (processes)

Risk: Low (east-1 acts as backup)
Complexity: Medium (upstream must change)
```

**Option B: Use S3 replication (Automatic sync)**
```
etl-data-us-east-1 → S3 Replication → etl-data-us-east-2
Upstream → etl-data-us-east-1

East-1 Lambda: DISABLED (no trigger)
East-2 Lambda: ENABLED (processes replicated files)

Risk: Medium (replication lag 15-30 sec)
Complexity: Low (no upstream changes needed initially)
```

**Option C: DNS/Load Balancer (If upstream uses DNS)**
```
upstream.company.com → Points to east-1 S3 initially
                    → Update to point to east-2 S3

Risk: High if not coordinated
Complexity: High (DNS/network changes)
```

**Recommended**: **Option B - S3 Replication**

```bash
# Set up S3 replication (east-1 → east-2)
# This copies files automatically

# Create replication role
cat > replication-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "s3.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name S3ReplicationRole \
  --assume-role-policy-document file://replication-policy.json

# Attach policy for S3 access
aws iam attach-role-policy \
  --role-name S3ReplicationRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Enable replication configuration
cat > replication-config.json << 'EOF'
{
  "Role": "arn:aws:iam::ACCOUNT_ID:role/S3ReplicationRole",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "DeleteMarkerReplication": {"Status": "Enabled"},
      "Filter": {"Prefix": ""},
      "Destination": {
        "Bucket": "arn:aws:s3:::etl-data-us-east-2",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {"Minutes": 15}
        }
      }
    }
  ]
}
EOF

# Enable versioning first (required for replication)
aws s3api put-bucket-versioning \
  --bucket etl-data-us-east-1 \
  --versioning-configuration Status=Enabled \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket etl-data-us-east-2 \
  --versioning-configuration Status=Enabled \
  --region us-east-2

# Set replication configuration
aws s3api put-bucket-replication \
  --bucket etl-data-us-east-1 \
  --replication-configuration file://replication-config.json \
  --region us-east-1

# Verify replication is working
# Upload file to east-1, wait 1-2 minutes, check east-2
aws s3 cp test.txt s3://etl-data-us-east-1/input/ --region us-east-1
sleep 60
aws s3 ls s3://etl-data-us-east-2/input/ --region us-east-2
# Should see test.txt replicated
```

---

### PHASE 3: POST-FAILOVER VALIDATION (30 minutes)

#### 3.1 Verify Lambda is Processing in east-2

```bash
# Upload test file
aws s3 cp test.csv s3://etl-data-us-east-2/input/ --region us-east-2

# Check CloudWatch logs for east-2
aws logs tail /aws/lambda/your-function --follow --region us-east-2

# Should see:
# "Processing in region: us-east-2"
# "Using bucket: etl-data-us-east-2"
```

#### 3.2 Verify Python Jobs Work in east-2

```bash
# SSH to edge node and run job
ssh ec2-user@edge-node

# Verify ACTIVE_REGION is set
echo $ACTIVE_REGION
# Should output: us-east-2

# Run job
python edge_node_job.py

# Should process from east-2 bucket and load to Snowflake
```

#### 3.3 Verify Spark Jobs Work in east-2

```bash
# Submit Spark job
spark-submit spark_job.py

# Check logs for:
# Spark job running in region: us-east-2
# fs.s3a.endpoint = https://s3.us-east-2.amazonaws.com
```

#### 3.4 Verify Snowflake Receiving Data

```sql
-- In Snowflake (now primary in us-east-2)

-- Check recent data
SELECT COUNT(*) as recent_count FROM ANALYTICS.PUBLIC.my_table
WHERE created_at > DATEADD(hour, -1, CURRENT_TIMESTAMP());

-- Should match the count from before failover + any new data

-- Check replication to east-1
SELECT * FROM TABLE(SNOWFLAKE.INFORMATION_SCHEMA.REPLICATION_STATUS());

-- Should show east-1 as replica receiving data
```

#### 3.5 Verify S3 Triggers

```bash
# Verify east-1 trigger is disabled
aws s3api get-bucket-notification-configuration \
  --bucket etl-data-us-east-1 \
  --region us-east-1
# Should return empty

# Verify east-2 trigger is enabled
aws s3api get-bucket-notification-configuration \
  --bucket etl-data-us-east-2 \
  --region us-east-2
# Should show Lambda trigger
```

#### 3.6 Verify S3 Replication (if using)

```bash
# Check replication metrics
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1
# Should show replication to east-2 enabled

# Monitor replication lag
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name ReplicationLatency \
  --dimensions Name=SourceBucket,Value=etl-data-us-east-1 \
            Name=DestinationBucket,Value=etl-data-us-east-2 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Maximum
```

#### 3.7 Full Checklist

```
POST-FAILOVER VALIDATION:

□ Lambda processed test file in us-east-2
□ Lambda logs show correct region and bucket
□ Python job processed from us-east-2 bucket
□ Python job loaded to Snowflake
□ Spark job processed from us-east-2 bucket
□ Snowflake received new data
□ Snowflake data count matches or increased
□ East-1 S3 trigger is disabled
□ East-2 S3 trigger is enabled
□ S3 replication working (if enabled)
□ East-2 Snowflake is primary (can write)
□ East-1 Snowflake is replica (read-only)
□ Replication direction reversed (east-2 → east-1)
□ CloudWatch shows east-2 metrics increasing
□ No errors in any logs
□ All upstream systems still writing to east-1 (for replication)

✓ FAILOVER COMPLETE AND VALIDATED
```

---

### PHASE 4: ROLLBACK (If Needed)

**If something goes wrong**, revert in reverse order:

```bash
# Step 1: Disable east-2 trigger
aws s3api put-bucket-notification-configuration \
  --bucket etl-data-us-east-2 \
  --notification-configuration '{}' \
  --region us-east-2

# Step 2: Re-enable east-1 trigger
aws s3api put-bucket-notification-configuration \
  --bucket etl-data-us-east-1 \
  --notification-configuration file://s3-notification-config.json \
  --region us-east-1

# Step 3: Change ACTIVE_REGION back to us-east-1
aws dynamodb put-item \
  --table-name etl-active-region \
  --item 'config_key={S=ACTIVE_REGION},value={S=us-east-1}' \
  --region us-east-1

# Step 4: Demote east-2 Snowflake back to replica
# In east-1:
ALTER DATABASE ANALYTICS DEMOTE;

# Step 5: Wait for resynchronization
# Monitor replication until caught up

# Test: Upload file to east-1, verify Lambda processes it
```

---

## SUMMARY TABLE

| Step | What | Where | Time |
|------|------|-------|------|
| 1 | Drain in-flight jobs | East-1 | 10 min |
| 2 | Final Snowflake sync | Snowflake | 5 min |
| 3 | Update ACTIVE_REGION | DynamoDB or Env | 1 min |
| 4 | Enable east-2 trigger | S3 console/CLI | 5 min |
| 5 | Promote east-2 SF | Snowflake SQL | 5 min |
| 6 | Reverse replication | Snowflake SQL | 5 min |
| 7 | Redirect upstream (opt) | Upstream config | 5-30 min |
| **Total** | **Complete switch** | **All systems** | **~45 minutes** |

---

## KEY ANSWERS FROM YOUR notes.md

| Question | Answer |
|----------|--------|
| "special coding for lambdas or spark jobs" | Create `region_config.py`, use `get_active_region()` and `get_s3_bucket()` |
| "can we have placeholder for region name" | Yes - use `<region>` in code, replaced at runtime from config |
| "best way to detect region changes" | Read from `ACTIVE_REGION` environment variable or DynamoDB |
| "topic name and queue name unique across AWS" | No, they're region-specific. Use ARNs/URLs |
| "can we use same topic/queue name in different regions" | Yes, same name but different ARNs/URLs |
| "do we turn off trigger on S3" | Yes, disable on east-1, enable on east-2 |
| "how to switch without asking upstream to change" | Use S3 replication (east-1 → east-2 automatic sync) |
| "We point ETL to S3 on east-2" | Update `ACTIVE_REGION` to "us-east-2", all code reads from it |
| "Do we stop S3 trigger on east-1" | Yes, disable it (don't delete, keep for rollback) |
| "force replicate snowflake from east-1 to east-2" | Run `ALTER DATABASE ANALYTICS REFRESH;` |
| "Stop replication and change rule" | Promote east-2 to primary, set up east-2 → east-1 replication |

---

## Best Practices Applied

✅ **Industry Standard**: Drain, sync, switch, redirect, reverse
✅ **Zero Data Loss**: Force final sync before switching
✅ **Minimal Upstream Changes**: Use S3 replication
✅ **Easy Rollback**: Keep east-1 enabled (disabled, not deleted)
✅ **Single Point of Control**: ACTIVE_REGION drives all decisions
✅ **Monitoring**: CloudWatch, Snowflake replication status
✅ **DR Maintained**: Reverse replication keeps east-1 as backup

