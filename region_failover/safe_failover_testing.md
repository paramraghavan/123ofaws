# Safe Failover Testing Guide
## Testing DR Without Impacting Production

---

## Overview: 3 Testing Approaches

| Approach | Risk | Cost | Realism | Best For |
|----------|------|------|---------|----------|
| **Isolated Test Environment** | Very Low | Low | Low | Initial validation |
| **Dry-Run (Simulated)** | Very Low | Very Low | Medium | Procedure validation |
| **Shadow Testing** | Low | Medium | High | Production readiness |
| **Canary Failover** | Low-Medium | Medium | Very High | Real-world testing |
| **Full Production Test** | High | High | Very High | Full DR validation |

---

## APPROACH 1: Isolated Test Environment (SAFEST)

### Setup: Separate AWS Accounts or Organizations

```
AWS Account 1 (Production):
├─ us-east-1: Running production
└─ us-east-2: Standby (not touched during test)

AWS Account 2 (Testing):
├─ us-east-1-test: Mirror of production
└─ us-east-2-test: Standby for testing
```

### Implementation Steps

#### Step 1: Create Test Infrastructure

```bash
# In test AWS account, create test versions of everything:

# Test S3 buckets
aws s3 mb s3://etl-data-us-east-1-test --region us-east-1
aws s3 mb s3://etl-data-us-east-2-test --region us-east-2

# Test DynamoDB table
aws dynamodb create-table \
  --table-name etl-active-region-test \
  --attribute-definitions AttributeName=config_key,AttributeType=S \
  --key-schema AttributeName=config_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Test Lambda functions
aws lambda create-function \
  --function-name etl-processor-test \
  --runtime python3.11 \
  --role arn:aws:iam::TEST_ACCOUNT:role/lambda-role \
  --handler lambda_patterns.lambda_handler_s3_trigger \
  --zip-file fileb://lambda-function.zip \
  --region us-east-1

# ... repeat in us-east-2
```

#### Step 2: Copy Sample Data

```bash
# Copy production data to test environment (one-time)
aws s3 cp s3://etl-data-us-east-1/input/ \
         s3://etl-data-us-east-1-test/input/ \
         --recursive \
         --region us-east-1
```

#### Step 3: Run Failover Test

```bash
# Test in isolated environment - no production impact
# Follow MANUAL_FAILOVER_PLAN.md steps exactly
# Everything is replicated, not shared with production
```

### Advantages

✅ **Zero production impact**: Completely isolated
✅ **Easy rollback**: Just delete test resources
✅ **Repeat testing**: Can test as many times as needed
✅ **Safe for learning**: Team can practice procedures

### Disadvantages

❌ **Low realism**: Test data, not real Snowflake
❌ **Cost**: Duplicate AWS resources
❌ **Data drift**: Test data becomes stale

---

## APPROACH 2: Dry-Run Testing (FASTEST)

### No Actual Changes to AWS - Just Verify Steps

#### Step 1: Run Failover Plan in Dry-Run Mode

```bash
# All scripts have dry-run mode - shows what WOULD happen
# without actually executing

# From MANUAL_FAILOVER_PLAN.md Phase 2, run each step with --dry-run:

# Step 1: Drain jobs (simulate)
echo "DRY RUN: Would disable S3 trigger on east-1"
echo "DRY RUN: Would wait for jobs to complete"

# Step 2: Final Snowflake sync (simulate)
echo "DRY RUN: Would run ALTER DATABASE ANALYTICS REFRESH;"

# Step 3: Switch region (simulate)
echo "DRY RUN: Would update DynamoDB ACTIVE_REGION to us-east-2"

# etc...
```

#### Step 2: Validation

```bash
# Verify without changing anything:

# Check replication configured
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1

# Check Lambda functions exist in both regions
aws lambda list-functions --region us-east-1
aws lambda list-functions --region us-east-2

# Check Snowflake connectivity
# (Dry-run, don't execute)

# Check S3 triggers configured
aws s3api get-bucket-notification-configuration \
  --bucket etl-data-us-east-1
```

### Advantages

✅ **Zero risk**: No actual changes
✅ **Very fast**: Just checking configuration
✅ **Cost-free**: No AWS changes
✅ **Good starting point**: Validate procedures

### Disadvantages

❌ **Low confidence**: Not testing actual failover
❌ **Doesn't prove it works**: Just checks configuration
❌ **Can't test rollback**: No actual state to rollback

---

## APPROACH 3: Shadow Testing (RECOMMENDED FOR PRODUCTION READINESS)

### Mirror Data to Standby, But Don't Switch Processing

```
PRODUCTION SETUP (Normal):
Upstream → east-1 bucket
         → Lambda/Python/Spark process
         → Snowflake

SHADOW SETUP (During Test):
Upstream → COPIES TO → east-2 bucket (via S3 replication or sync)
                    → Lambda/Python/Spark process (isolated)
                    → Test Snowflake (separate from production)
```

#### Step 1: Set Up Shadow Processing

```bash
# Create shadow Lambda function that processes from us-east-2
# but doesn't write to production Snowflake

cat > lambda_shadow_handler.py << 'EOF'
import json
from lambda_patterns import ETLOrchestrator

def lambda_handler(event, context):
    """Shadow Lambda handler - processes but logs only"""

    orchestrator = ETLOrchestrator()

    # Get data from us-east-2
    region = "us-east-2"  # Force to east-2 for shadow testing
    bucket = f"etl-data-{region}"

    print(f"[SHADOW TEST] Processing in region: {region}")
    print(f"[SHADOW TEST] Using bucket: {bucket}")

    # Process file
    # But instead of writing to production Snowflake:
    # Write to test/shadow Snowflake or just log results

    # Write to shadow Snowflake table (not production)
    conn = snowflake.connector.connect(
        account=...,
        database="ANALYTICS_SHADOW",  # Shadow database
        schema="PUBLIC_SHADOW"  # Shadow schema
    )

    print(f"[SHADOW TEST] Data would be processed: {json.dumps(event)}")
    print(f"[SHADOW TEST] Validation: Success")

    return {
        'statusCode': 200,
        'message': '[SHADOW TEST] Processing validated',
        'region': region
    }
EOF

# Deploy shadow Lambda
aws lambda create-function \
  --function-name etl-processor-shadow \
  --runtime python3.11 \
  --handler lambda_shadow_handler.lambda_handler \
  --region us-east-1
```

#### Step 2: Mirror Data to us-east-2

```bash
# Option A: Use S3 replication (already set up)
# Files automatically sync from us-east-1 to us-east-2

# Option B: Use S3 sync
aws s3 sync s3://etl-data-us-east-1/input/ \
          s3://etl-data-us-east-2/input/ \
          --region us-east-1
```

#### Step 3: Trigger Shadow Test

```bash
# Upload file that triggers shadow processing

# Create test file
echo '{"id": 123, "value": "shadow-test"}' > shadow-test.json

# Upload to us-east-1
# Replication automatically syncs to us-east-2

# Lambda in us-east-2 processes from shadow bucket
# Results go to shadow Snowflake (not production)

# Check logs
aws logs tail /aws/lambda/etl-processor-shadow --follow --region us-east-2
```

#### Step 4: Validate Shadow Processing

```bash
# Check that shadow Lambda processed the file
aws logs tail /aws/lambda/etl-processor-shadow --region us-east-2 | grep "SHADOW TEST"

# Check shadow Snowflake received data
SELECT COUNT(*) FROM ANALYTICS_SHADOW.PUBLIC_SHADOW.my_table;

# Compare with production Snowflake
SELECT COUNT(*) FROM ANALYTICS.PUBLIC.my_table;
```

### Advantages

✅ **Real-world testing**: Using production infrastructure
✅ **Isolated results**: Shadow DB/Lambda, not production
✅ **Ongoing validation**: Can run continuously
✅ **Confidence builder**: Proves east-2 processing works
✅ **Low risk**: Separate processing pipeline

### Disadvantages

⚠️ **Setup complexity**: Need shadow resources
⚠️ **Ongoing cost**: Running shadow processing
⚠️ **Still not full test**: Not actual failover

---

## APPROACH 4: Canary Failover (ADVANCED)

### Test With Real Production Data, But Minimal Blast Radius

```
PRODUCTION (Normal):
100% traffic → us-east-1

TEST (Canary):
5% traffic → us-east-2 (for real testing)
95% traffic → us-east-1 (production as normal)
```

#### Step 1: Route Small Percentage to us-east-2

```bash
# Option A: Lambda version aliasing
aws lambda create-alias \
  --function-name etl-processor \
  --name canary \
  --function-version 1 \
  --routing-config AdditionalVersionWeight=0.05  # 5% to new version
  --region us-east-1

# Option B: S3 trigger with conditional routing
# 5% of uploaded files → us-east-2 trigger
# 95% of uploaded files → us-east-1 trigger (normal)
```

#### Step 2: Configure Canary Lambda for us-east-2

```python
def lambda_handler(event, context):
    """Canary test - 5% of traffic routes here"""

    # Force region to us-east-2 for canary
    os.environ['ACTIVE_REGION'] = 'us-east-2'

    # Process normally but track that it's a canary
    print(f"[CANARY TEST] Processing file: {event['key']}")

    # Process and load to Snowflake
    # Tag data with canary marker
    cursor.execute("""
        INSERT INTO my_table (data, is_canary_test)
        VALUES (%s, TRUE)
    """)

    return {'statusCode': 200}
```

#### Step 3: Monitor Canary Results

```bash
# Monitor: Are canary processed files correct?
SELECT COUNT(*) as canary_count FROM my_table WHERE is_canary_test = TRUE;

# Compare with normal production results
SELECT COUNT(*) as normal_count FROM my_table WHERE is_canary_test = FALSE;

# Check error rates
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=etl-processor-canary \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T02:00:00Z \
  --period 300 \
  --statistics Sum
```

### Advantages

✅ **Real production testing**: Actual data and systems
✅ **Minimal blast radius**: Only 5% affected
✅ **Realistic metrics**: Real performance data
✅ **Confidence**: Proves system works under production load

### Disadvantages

⚠️ **Some production impact**: Even 5% is production
⚠️ **Complexity**: Traffic splitting setup
⚠️ **Monitoring overhead**: Must watch canary closely

---

## APPROACH 5: Full Production Failover Test (HIGHEST FIDELITY)

### Scheduled Maintenance: Actual Complete Failover

```
Window: Saturday 2 AM - Sunday 2 AM
Risk: High if not carefully managed
Benefit: Proves everything works under real conditions
```

### Prerequisites

```
□ All teams notified (24+ hour notice)
□ Rollback plan reviewed and tested
□ Incident commander assigned
□ Monitoring dashboards ready
□ On-call team assembled
□ Upstream systems paused (no new uploads)
□ Snowflake teams notified
```

### Execution

```bash
# Follow MANUAL_FAILOVER_PLAN.md exactly
# But in a scheduled maintenance window

# Timeline: 2-4 hours total
# - 30 min: Pre-failover validation
# - 45 min: Failover execution (Phase 2)
# - 30 min: Post-failover validation
# - 30 min: Stabilization & monitoring
# - 30 min: Rollback (if needed)
# - 30 min: Post-analysis
```

### Advantages

✅ **Complete validation**: Entire failover process tested
✅ **Real conditions**: Production infrastructure under load
✅ **Confidence**: Team practices actual procedures
✅ **Identifies gaps**: Real issues surface

### Disadvantages

⚠️ **High risk**: Impacts production (even with rollback)
⚠️ **High effort**: Requires team coordination
⚠️ **High stress**: Team pressure to complete successfully

---

## RECOMMENDED TESTING SEQUENCE

### Week 1-2: Foundation Testing (Risk: Very Low)

```
Monday:
  - Test 1: Dry-run testing (Approach 2)
    - Verify all AWS resources exist
    - Review procedures without making changes
    - Time: 1 hour

Tuesday-Wednesday:
  - Test 2: Isolated test environment (Approach 1)
    - Create shadow infrastructure
    - Practice entire failover procedure
    - Full rollback test
    - Time: 4-6 hours
```

### Week 3: Shadow Testing (Risk: Low)

```
Thursday-Friday:
  - Test 3: Shadow testing (Approach 3)
    - Set up shadow Lambda and Snowflake
    - Run continuous shadow processing
    - Validate data integrity
    - Time: 2 hours setup, ongoing monitoring
```

### Week 4: Canary & Production Tests (Risk: Low-High)

```
Saturday (Canary):
  - Test 4: Canary failover (Approach 4)
    - Route 5% traffic to us-east-2
    - Monitor for 8+ hours
    - Validate results
    - Time: Ongoing monitoring

Next Saturday (Full Test):
  - Test 5: Full production failover (Approach 5)
    - Scheduled 4-hour maintenance window
    - Complete failover and rollback
    - Team practices actual procedures
    - Time: 4 hours + post-analysis
```

---

## SAFEST STARTING POINT: Dry-Run → Isolated → Shadow

### Step 1: Dry-Run (Today - 1 hour)

```bash
# Just verify everything is configured
# No changes made

# Check 1: Can we read failover procedures?
cat MANUAL_FAILOVER_PLAN.md

# Check 2: Do all AWS resources exist?
aws s3 ls s3://etl-data-us-east-1/
aws s3 ls s3://etl-data-us-east-2/
aws dynamodb get-item --table-name etl-active-region --key 'config_key={S=ACTIVE_REGION}'
aws lambda list-functions --region us-east-1 | grep etl-processor
aws lambda list-functions --region us-east-2 | grep etl-processor

# Check 3: Is S3 replication configured?
aws s3api get-bucket-replication --bucket etl-data-us-east-1 --region us-east-1

# Check 4: Are S3 triggers configured?
aws s3api get-bucket-notification-configuration --bucket etl-data-us-east-1

# ✅ All checks passed = Ready for next step
```

### Step 2: Isolated Environment Test (This week)

```bash
# Create separate test AWS account or use non-prod account

# Copy procedures exactly
# Execute MANUAL_FAILOVER_PLAN.md in test environment
# Test with sample data

# This allows:
# - Team practices procedures
# - No production impact
# - Easy to repeat and fix issues
# - Safe learning environment
```

### Step 3: Shadow Testing (Next week)

```bash
# Set up shadow resources in production account
# but isolated from production

# Create:
# - etl-processor-shadow Lambda
# - ANALYTICS_SHADOW.PUBLIC_SHADOW Snowflake schema
# - Mirror from us-east-1 to us-east-2 via S3 replication

# Run continuously
# Validate that us-east-2 processing works
# Without impacting production
```

### Step 4: Canary Test (2 weeks from now)

```bash
# Route 5% of real production traffic to us-east-2
# Monitor results
# Expand to 10%, then 20% as confidence increases
```

### Step 5: Full Production Test (Scheduled Maintenance)

```bash
# Once all previous tests pass
# Schedule 4-hour maintenance window
# Execute full failover and rollback with team
# Validate procedures one final time
```

---

## Safety Checklist for Each Test

```
BEFORE ANY TEST:
□ Backup current configuration (DynamoDB, S3, Lambda env vars)
□ Document current ACTIVE_REGION value
□ Notify team: What test, when, expected impact
□ Have rollback plan ready
□ Enable CloudWatch detailed monitoring

DURING TEST:
□ Watch logs in real-time
□ Monitor: Lambda errors, S3 replication, Snowflake sync
□ Stop immediately if unexpected errors appear
□ Document any issues found

AFTER TEST:
□ Validate everything rolled back correctly
□ Confirm ACTIVE_REGION back to us-east-1
□ Verify production data unchanged
□ Document findings and improvements
□ Update procedures based on learnings
```

---

## What to Validate in Each Test

| Test Type | What to Validate |
|-----------|------------------|
| **Dry-Run** | Configuration exists, procedures make sense |
| **Isolated** | Full failover works in test environment |
| **Shadow** | us-east-2 processing works correctly |
| **Canary** | Real production data processes in us-east-2 |
| **Full** | Complete failover and rollback works |

---

## Key Success Metrics

After each test, measure:

1. **Time to failover**: How long did the switch take?
2. **Data integrity**: Did all data replicate correctly?
3. **Snowflake sync**: Did replication catch up?
4. **Processing success**: Did Lambda/Spark work in us-east-2?
5. **Rollback success**: Did reverting to us-east-1 work cleanly?
6. **Team confidence**: How prepared does the team feel?

---

## Recommended Test Schedule

```
Week 1:
  Monday: Dry-run testing (1 hour, 0 risk)
  Wednesday: Isolated test environment (4 hours, 0 risk)

Week 2:
  Monday: Shadow testing setup (2 hours, very low risk)
  Tuesday-Sunday: Continuous shadow monitoring

Week 3:
  Saturday: Canary failover test (8 hours, low risk)

Week 4:
  Saturday: Full production failover test (4 hours, high risk but controlled)
  Sunday: Post-analysis and documentation
```

---

## Bottom Line

✅ **Start with Dry-Run** (today, 0 risk)
✅ **Move to Isolated Testing** (this week, 0 risk)
✅ **Progress to Shadow Testing** (next week, very low risk)
✅ **Advance to Canary Testing** (2 weeks, low risk)
✅ **Execute Full Production Test** (3-4 weeks, high but controlled risk)

By following this sequence, your team gains confidence at each step without ever putting production at serious risk! 🎯
