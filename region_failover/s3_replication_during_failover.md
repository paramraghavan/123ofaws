# S3 Replication During Failover
## Do We Need to Change S3 Replication Configuration?

---

## Quick Answer

**SHORT ANSWER**: No, you don't HAVE to make changes to S3 replication east-1 → east-2, but you SHOULD make changes for optimal operation.

---

## What Happens if You DON'T Change Replication

### Scenario: Leave Replication as-is (east-1 → east-2)

```
BEFORE FAILOVER:
Upstream writes to → S3 east-1
                    ↓ (replicates automatically)
                    S3 east-2
                    ↓
                    Lambda/Python/Spark process from east-1

DURING/AFTER FAILOVER:
Upstream STILL writes to → S3 east-1
                          ↓ (replicates automatically)
                          S3 east-2 [NOW ACTIVE REGION]
                          ↓
                          Lambda/Python/Spark process from east-2
```

### What Works

✅ **Replication still works**: Files uploaded to east-1 automatically sync to east-2
✅ **Processing continues**: Lambda/Python/Spark read from east-2 bucket (where replicated files are)
✅ **Data integrity**: All data in east-1 is replicated to east-2

### What's the Problem

⚠️ **Replication lag**:
- Files uploaded to east-1
- Takes 1-30 seconds (or up to 15 minutes with Replication Time Control)
- Processing in east-2 might process file AFTER it's fully replicated

❌ **Cost inefficiency**:
- Still paying for cross-region replication FROM east-1 TO east-2
- But your ACTIVE processing is in east-2
- Replication is just for "backup" now, not active use

❌ **Confusing setup**:
- Upstream writes to east-1
- Processing reads from east-2
- Replication connects them
- On next DR test, what do you do?

---

## Best Practice: Change Replication After Failover

### Option A: Keep east-1 → east-2 Replication (Short-term)

**Use case**: You're stabilizing the failover, plan to revert to east-1 later

```
Timeline:
├─ Failover to east-2 (east-1 → east-2 replication unchanged)
├─ Monitor for 1-2 hours
├─ Confirm east-2 stable
├─ Once confirmed: Change replication
└─ Setup east-2 → east-1 (reverse for backup/DR)
```

**Keep because**: Keeps east-1 as a "warm backup"

---

### Option B: Switch Replication Direction (Recommended)

**Best for**: Permanent failover or when staying in east-2

```
BEFORE FAILOVER:
east-1 → east-2 (Upstream writes to east-1)

AFTER FAILOVER COMPLETES:
east-2 → east-1 (Upstream writes to east-2, replicate to east-1 for backup)
```

**Steps**:

1. **Disable old replication** (east-1 → east-2)
```bash
aws s3api delete-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1
```

2. **Enable new replication** (east-2 → east-1)
```bash
cat > replication-config-reverse.json << 'EOF'
{
  "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {"Prefix": ""},
      "Destination": {
        "Bucket": "arn:aws:s3:::etl-data-us-east-1",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {"Minutes": 15}
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-replication \
  --bucket etl-data-us-east-2 \
  --replication-configuration file://replication-config-reverse.json \
  --region us-east-2
```

3. **Verify new replication**
```bash
# Check east-2 bucket now has replication rule
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-2 \
  --region us-east-2

# Test: Upload file to east-2, check it appears in east-1
aws s3 cp test.txt s3://etl-data-us-east-2/test/ --region us-east-2
sleep 30
aws s3 ls s3://etl-data-us-east-1/test/ --region us-east-1
# Should see test.txt (confirms replication working)
```

**Benefits**:
- ✅ Upstream writes to east-2 (active region)
- ✅ Automatically replicated to east-1 (backup)
- ✅ Clear single source of truth (east-2)
- ✅ Better for disaster recovery planning

---

### Option C: Keep Both Directions (Bi-directional Replication)

**Use case**: Need data sync in both directions for disaster recovery

```
SETUP:
east-1 ← → east-2 (Bidirectional replication)

Pros:
✅ Both regions always in sync
✅ Can fail back easily
✅ True disaster recovery ready

Cons:
❌ Higher cost (2x replication)
❌ More complex (need to handle conflicts)
❌ Potential for circular replication issues
```

**Not recommended** for simple failover, but good for production DR.

---

## Your Specific Scenario

**From your notes.md**:
- Upstream writes to east-1
- ETL jobs triggered by S3 files
- Files ingested to Snowflake
- Failing over to east-2

### Recommended Approach for You

**Phase 1: During Failover (Keep replication as-is)**
```
east-1 → east-2 (unchanged)
Upstream continues writing to east-1 (unchanged)
Processing switches to east-2
Replication keeps east-2 in sync with east-1
```

**Phase 2: After Failover Stabilizes (Change replication)**
```
Option A: Tell upstream to write to east-2 now
├─ Disable: east-1 → east-2
└─ Enable: east-2 → east-1 (for backup/DR)

Option B: Keep upstream writing to east-1
├─ Keep: east-1 → east-2 (continue replication)
└─ Add: east-2 → east-1 (bidirectional)
```

---

## Step-by-Step: Change Replication After Failover

### Step 1: Verify Current State

```bash
# Check current replication (should be east-1 → east-2)
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1 | jq '.ReplicationConfiguration.Rules[0]'

# Should show Destination: arn:aws:s3:::etl-data-us-east-2
```

### Step 2: Disable East-1 → East-2 Replication

```bash
# Delete the old replication rule
aws s3api delete-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1

# Verify it's deleted
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1 2>&1
# Should show: ReplicationConfigurationNotFoundError (no longer exists)
```

### Step 3: Enable East-2 → East-1 Replication

```bash
# Create replication config (east-2 as source)
cat > replication-east2-to-east1.json << 'EOF'
{
  "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {"Prefix": ""},
      "Destination": {
        "Bucket": "arn:aws:s3:::etl-data-us-east-1",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {"Minutes": 15}
        }
      }
    }
  ]
}
EOF

# Enable replication on east-2 bucket
aws s3api put-bucket-replication \
  --bucket etl-data-us-east-2 \
  --replication-configuration file://replication-east2-to-east1.json \
  --region us-east-2
```

### Step 4: Verify New Replication Working

```bash
# Check configuration
aws s3api get-bucket-replication \
  --bucket etl-data-us-east-2 \
  --region us-east-2 | jq '.ReplicationConfiguration.Rules[0].Destination'

# Should show Destination: arn:aws:s3:::etl-data-us-east-1

# Test it works
echo "test-reverse-$(date +%s)" > test.txt
aws s3 cp test.txt s3://etl-data-us-east-2/test/ --region us-east-2

echo "Waiting 30 seconds for replication..."
sleep 30

# Check if it appeared in east-1
if aws s3 ls s3://etl-data-us-east-1/test/ --region us-east-1 | grep test; then
  echo "✅ Reverse replication working!"
else
  echo "❌ Reverse replication failed"
fi
```

---

## Complete Timeline for Your Failover

### T = -1 hour (Before Failover)
```
Replication: east-1 → east-2
Upstream writes to: east-1
Processing from: east-1
Status: Normal operation
```

### T = 0 (Failover Moment)
```
1. Disable east-1 S3 trigger
2. Drain jobs
3. Switch ACTIVE_REGION to east-2
4. Enable east-2 S3 trigger
5. Replication STILL: east-1 → east-2 (unchanged)
```

### T = +15 minutes (Failover Complete)
```
Replication: STILL east-1 → east-2
Upstream writes to: east-1 (NOT CHANGED YET)
Processing from: east-2
Status: Failover complete, files still flowing via replication
```

### T = +1 hour (Stabilized, Ready for Replication Change)
```
Verify east-2 stable for 1 hour
Then change replication:

OPTION A (Recommended):
├─ Tell upstream to write to east-2 bucket
├─ Disable: east-1 → east-2
└─ Enable: east-2 → east-1 (backup)

OPTION B (If upstream can't change immediately):
├─ Keep: east-1 → east-2
├─ Add: east-2 → east-1 (bidirectional)
└─ Plan to change upstream when ready
```

---

## Summary: Do You Need to Change Replication?

| Question | Answer |
|----------|--------|
| **Must I change it?** | No, but you should |
| **Can I leave it as-is?** | Yes, east-1 → east-2 still works |
| **Any problems leaving it?** | Minor: lag, cost, confusion |
| **When to change it?** | After failover stabilizes (1+ hour) |
| **What to change to?** | east-2 → east-1 (reverse for backup) |
| **What if upstream can't change?** | Keep east-1 → east-2, add reverse |

---

## Failover Checklist Addition

Add to your **SWITCH_DAY_CHECKLIST.md**:

```
POST-FAILOVER (After 1 hour, when stable):

□ Verify east-2 processing stable for 1+ hour
□ Decide replication strategy:
  □ Option A: Change upstream to write to east-2
     - Disable east-1 → east-2 replication
     - Enable east-2 → east-1 replication
  □ Option B: Keep upstream writing to east-1
     - Keep east-1 → east-2 replication
     - Add east-2 → east-1 replication (bidirectional)
□ Update S3 replication configuration
□ Test: Upload file, verify replication working in new direction
□ Document which option chosen for next failover test
```

---

## For Your MANUAL_FAILOVER_PLAN.md

Add this section after "Step 2.8: Redirect Upstream Systems":

**Step 2.9: Update S3 Replication (After Stabilization)**

Wait 1 hour, then:

**If upstream switched to east-2**:
```bash
# Disable old replication (east-1 → east-2)
aws s3api delete-bucket-replication \
  --bucket etl-data-us-east-1 \
  --region us-east-1

# Enable reverse replication (east-2 → east-1 for backup)
aws s3api put-bucket-replication \
  --bucket etl-data-us-east-2 \
  --replication-configuration file://replication-east2-to-east1.json \
  --region us-east-2
```

**If upstream still writing to east-1**:
```bash
# Keep east-1 → east-2 replication
# Add east-2 → east-1 replication (bidirectional)
aws s3api put-bucket-replication \
  --bucket etl-data-us-east-2 \
  --replication-configuration file://replication-east2-to-east1.json \
  --region us-east-2
```

---

## Key Takeaway

- **During failover**: Leave S3 replication east-1 → east-2 unchanged (it works fine)
- **After failover stabilizes**: Reverse the replication to east-2 → east-1 (for backup)
- **This setup**: Upstream → east-2, east-2 processes, east-2 replicates to east-1 for disaster recovery

This gives you the cleanest, most maintainable setup! ✅
