# S3 Replication Verification Guide
## How to Check if S3 Replication is Enabled

---

## Method 1: AWS CLI - Get Replication Configuration

### Check if replication is configured

```bash
# Get replication configuration from source bucket
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1
```

### Expected Output (If replication IS enabled)

```json
{
    "ReplicationConfiguration": {
        "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
        "Rules": [
            {
                "Status": "Enabled",
                "Priority": 1,
                "DeleteMarkerReplication": {
                    "Status": "Enabled"
                },
                "Filter": {
                    "Prefix": ""
                },
                "Destination": {
                    "Bucket": "arn:aws:s3:::etl-data-us-east-2",
                    "ReplicationTime": {
                        "Status": "Enabled",
                        "Time": {
                            "Minutes": 15
                        }
                    },
                    "Metrics": {
                        "Status": "Enabled",
                        "EventThreshold": {
                            "Minutes": 15
                        }
                    }
                }
            }
        ]
    }
}
```

### Expected Output (If replication is NOT enabled)

```bash
# Error message:
An error occurred (ReplicationConfigurationNotFoundError) when calling the GetBucketReplication operation: The replication configuration was not found
```

---

## Method 2: AWS Console

### Step-by-step

1. **Open S3 Console**: https://s3.console.aws.amazon.com/s3/home
2. **Select bucket**: Click on `etl-data-us-east-1`
3. **Go to Management tab**: Click "Management" in left sidebar
4. **Check Replication rules**:
   - Look for "Replication rules" section
   - If present, it shows rules and their status
   - Status should be "Enabled" with green checkmark

### Visual Indicators

✅ **Replication ENABLED**:
- "Replication rules" section visible
- Rule shows "Enabled" status
- Green checkmark next to rule
- Destination bucket shown

❌ **Replication NOT ENABLED**:
- "Replication rules" section shows "No replication rules"
- Empty state message

---

## Method 3: Check Bucket Versioning (Required for Replication)

Replication requires versioning. Check if it's enabled:

```bash
# Check versioning status
aws s3api get-bucket-versioning \
  --bucket etl-data-us-east-1 \
  --region us-east-1
```

### Expected Output (If versioning IS enabled)

```json
{
    "Status": "Enabled"
}
```

### Expected Output (If versioning is NOT enabled)

```json
{}
```

**Important**: If versioning is empty/not shown, it means versioning is **Suspended or not enabled**.

---

## Method 4: Check Replication Metrics

```bash
# View replication metrics (requires replication to be enabled)
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1 | jq '.ReplicationConfiguration.Rules[0].Destination.Metrics'
```

### Expected Output (If metrics enabled)

```json
{
    "Status": "Enabled",
    "EventThreshold": {
        "Minutes": 15
    }
}
```

### What it means:
- **Status: Enabled** = Replication metrics are being tracked
- **Minutes: 15** = CloudWatch metrics updated every 15 minutes

---

## Method 5: Check Replication Status in CloudWatch

```bash
# List replication metrics
aws cloudwatch list-metrics \
  --namespace AWS/S3 \
  --metric-name ReplicationLatency
```

### Expected Output (If replication active)

```json
{
    "Metrics": [
        {
            "Namespace": "AWS/S3",
            "MetricName": "ReplicationLatency",
            "Dimensions": [
                {
                    "Name": "SourceBucket",
                    "Value": "etl-data-us-east-1"
                },
                {
                    "Name": "DestinationBucket",
                    "Value": "etl-data-us-east-2"
                }
            ]
        }
    ]
}
```

---

## Method 6: Verify Actual Replication Working

### Test: Upload file and verify it replicates

```bash
# Step 1: Upload test file to source bucket
aws s3 cp test-replication.txt \
  s3://etl-data-us-east-1/test/ \
  --region us-east-1

# Verify it's in source bucket
aws s3 ls s3://etl-data-us-east-1/test/ --region us-east-1
# Should show: test-replication.txt

# Step 2: Wait for replication (typically <1 minute, max 15 min)
sleep 30

# Step 3: Check if file replicated to destination bucket
aws s3 ls s3://etl-data-us-east-2/test/ --region us-east-2
# Should show: test-replication.txt (means replication working!)

# If file NOT present after waiting:
# - Replication may not be enabled
# - Or replication failed
# - Check CloudTrail for errors
```

---

## Method 7: Check CloudTrail for Replication Events

```bash
# View replication-related events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutBucketReplication \
  --max-items 10
```

### Expected Output (If replication was set up)

```json
{
    "Events": [
        {
            "EventId": "abc123...",
            "EventName": "PutBucketReplication",
            "EventTime": "2024-01-15T10:30:00Z",
            "Username": "your-username",
            "Resources": [
                {
                    "ARN": "arn:aws:s3:::etl-data-us-east-1",
                    "AccountId": "123456789012",
                    "Type": "AWS::S3::Bucket"
                }
            ]
        }
    ]
}
```

---

## Method 8: Compare File Counts Between Buckets

```bash
# Count files in source bucket
echo "Source bucket (us-east-1):"
aws s3 ls s3://etl-data-us-east-1/ --recursive --region us-east-1 | wc -l

# Count files in destination bucket
echo "Destination bucket (us-east-2):"
aws s3 ls s3://etl-data-us-east-2/ --recursive --region us-east-2 | wc -l

# If counts are similar, replication is likely working
# (May be slightly different if replication is still in progress)
```

---

## Complete Verification Script

Create this bash script to check everything at once:

```bash
#!/bin/bash

SOURCE_BUCKET="etl-data-us-east-1"
DEST_BUCKET="etl-data-us-east-2"
SOURCE_REGION="us-east-1"
DEST_REGION="us-east-2"

echo "=========================================="
echo "S3 REPLICATION VERIFICATION"
echo "=========================================="

# Check 1: Replication Configuration
echo ""
echo "1. CHECKING REPLICATION CONFIGURATION..."
REPLICATION=$(aws s3api get-bucket-replication \
  --bucket $SOURCE_BUCKET \
  --region $SOURCE_REGION 2>&1)

if echo "$REPLICATION" | grep -q "ReplicationConfigurationNotFoundError"; then
  echo "   ❌ REPLICATION NOT CONFIGURED"
  exit 1
else
  echo "   ✅ REPLICATION CONFIGURED"
  echo "   Rule Status: $(echo $REPLICATION | jq -r '.ReplicationConfiguration.Rules[0].Status')"
  echo "   Destination: $(echo $REPLICATION | jq -r '.ReplicationConfiguration.Rules[0].Destination.Bucket')"
fi

# Check 2: Versioning
echo ""
echo "2. CHECKING VERSIONING (REQUIRED FOR REPLICATION)..."
VERSIONING=$(aws s3api get-bucket-versioning \
  --bucket $SOURCE_BUCKET \
  --region $SOURCE_REGION)

if echo "$VERSIONING" | grep -q '"Status": "Enabled"'; then
  echo "   ✅ VERSIONING ENABLED"
else
  echo "   ❌ VERSIONING NOT ENABLED"
  echo "   Replication requires versioning!"
fi

# Check 3: Metrics
echo ""
echo "3. CHECKING REPLICATION METRICS..."
METRICS=$(echo $REPLICATION | jq -r '.ReplicationConfiguration.Rules[0].Destination.Metrics.Status' 2>/dev/null)

if [ "$METRICS" == "Enabled" ]; then
  echo "   ✅ REPLICATION METRICS ENABLED"
else
  echo "   ⚠️  REPLICATION METRICS NOT ENABLED"
fi

# Check 4: Test Replication
echo ""
echo "4. TESTING REPLICATION WITH TEST FILE..."
TEST_FILE="test-replication-$(date +%s).txt"

# Upload test file
aws s3 cp /dev/null s3://$SOURCE_BUCKET/test/$TEST_FILE --region $SOURCE_REGION

# Wait for replication
echo "   Waiting 30 seconds for replication..."
sleep 30

# Check if replicated
if aws s3 ls s3://$DEST_BUCKET/test/$TEST_FILE --region $DEST_REGION &>/dev/null; then
  echo "   ✅ TEST FILE REPLICATED SUCCESSFULLY"
  echo "      Source: s3://$SOURCE_BUCKET/test/$TEST_FILE"
  echo "      Destination: s3://$DEST_BUCKET/test/$TEST_FILE"

  # Clean up
  aws s3 rm s3://$SOURCE_BUCKET/test/$TEST_FILE --region $SOURCE_REGION
  aws s3 rm s3://$DEST_BUCKET/test/$TEST_FILE --region $DEST_REGION
else
  echo "   ❌ TEST FILE DID NOT REPLICATE"
  echo "   Check CloudTrail for replication errors"
fi

# Check 5: CloudWatch Metrics
echo ""
echo "5. CHECKING CLOUDWATCH METRICS..."
METRICS_FOUND=$(aws cloudwatch list-metrics \
  --namespace AWS/S3 \
  --metric-name ReplicationLatency | jq '.Metrics | length')

if [ "$METRICS_FOUND" -gt 0 ]; then
  echo "   ✅ REPLICATION METRICS FOUND IN CLOUDWATCH"
  echo "   Metrics count: $METRICS_FOUND"
else
  echo "   ⚠️  NO REPLICATION METRICS IN CLOUDWATCH"
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
```

### Run the script:

```bash
chmod +x verify_replication.sh
./verify_replication.sh
```

---

## Quick Checklist: Is Replication Enabled?

Use this quick checklist:

```
□ aws s3api get-bucket-replication returns configuration (not error)?
  → YES = Replication enabled ✅

□ Versioning is enabled on source bucket?
  → YES = Required check passes ✅

□ Destination bucket specified in replication rule?
  → YES = Configuration correct ✅

□ Rule status is "Enabled" (not "Disabled")?
  → YES = Rule is active ✅

□ Test file uploaded to source appears in destination within 1 minute?
  → YES = Replication actually working ✅

If ALL boxes checked = REPLICATION IS ENABLED AND WORKING
```

---

## Troubleshooting: Replication Not Working

If replication is configured but files aren't replicating:

### Issue 1: Versioning not enabled

```bash
# Check versioning
aws s3api get-bucket-versioning --bucket etl-data-us-east-1

# If empty or "Suspended", enable it:
aws s3api put-bucket-versioning \
  --bucket etl-data-us-east-1 \
  --versioning-configuration Status=Enabled
```

### Issue 2: IAM role doesn't have permissions

```bash
# Check the role in replication configuration
ROLE=$(aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 | jq -r '.ReplicationConfiguration.Role')

# Example: arn:aws:iam::123456789012:role/S3ReplicationRole

# Check role permissions
aws iam get-role-policy \
  --role-name S3ReplicationRole \
  --policy-name S3ReplicationPolicy

# Should have permissions for:
# - s3:GetReplicationConfiguration
# - s3:ListBucket
# - s3:GetObjectVersionForReplication
# - s3:GetObjectVersionAcl
# - s3:PutObject
# - s3:PutObjectAcl
```

### Issue 3: Destination bucket doesn't allow writes

```bash
# Verify destination bucket exists
aws s3 ls s3://etl-data-us-east-2 --region us-east-2

# Check if it's blocked by bucket policy
aws s3api get-bucket-policy --bucket etl-data-us-east-2 --region us-east-2

# If blocked, remove restrictions or add replication role to policy
```

### Issue 4: Check CloudTrail for replication errors

```bash
# Look for replication-related errors
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutBucketReplication \
  --query 'Events[?CloudTrailEvent contains `error`]'

# Or check all replication events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=Replication \
  --max-items 20 | jq '.Events[] | {EventName, CloudTrailEvent}'
```

---

## Summary: How to Know Replication is Enabled

**Easiest way**:
```bash
aws s3api get-bucket-replication --bucket etl-data-us-east-1 --region us-east-1
```

If you get JSON output (not an error) → **Replication is enabled** ✅

If you get "ReplicationConfigurationNotFoundError" → **Replication is NOT enabled** ❌

---

## For Your Failover Plan

**Before failover**, run:

```bash
# Verify replication is enabled
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1 | jq '.ReplicationConfiguration.Rules[0].Status'
# Should output: "Enabled"

# Verify destination bucket correct
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1 | jq '.ReplicationConfiguration.Rules[0].Destination.Bucket'
# Should output: "arn:aws:s3:::etl-data-us-east-2"

# Test with a file
aws s3 cp test.txt s3://etl-data-us-east-1/test/ --region us-east-1
sleep 30
aws s3 ls s3://etl-data-us-east-2/test/ --region us-east-2
# Should list test.txt (confirms replication working)
```

If all these pass, **replication is ready for failover!** ✅
