# Manual Failover Guide - Interactive Resource Selection

This guide explains the **manual failover workflow** where ops team receives alerts and manually selects which resources to failover.

## Workflow Overview

```
PRIMARY REGION DOWN
       ↓
SECONDARY MONITORING sends ALERT
       ↓
OPS TEAM receives alert email
       ↓
OPS TEAM runs failover script on SECONDARY region
       ↓
SCRIPT shows all resources
       ↓
USER selects which resources to failover (y/n)
       ↓
USER confirms final failover
       ↓
SCRIPT executes failover for selected resources
       ↓
SECONDARY REGION NOW ACTIVE
```

## Prerequisites

- **Secondary region monitoring** running and healthy
- **DynamoDB heartbeat table** created (for detecting primary failure)
- **AWS credentials** configured for secondary region
- **Email alerts** configured (to notify ops team)

## Step 1: Setup Dual-Region Monitoring

### Deploy Primary Region Monitoring

```bash
# On primary region server (us-east-1)
python src/main.py --config config/failover-primary-config.yaml --prefix uat-
```

**What it does:**
- Monitors all resources
- Sends heartbeat to DynamoDB every 60 seconds
- Continues normal monitoring

### Deploy Secondary Region Monitoring

```bash
# On secondary region server (us-west-2)
python src/main.py --config config/failover-secondary-config.yaml --prefix uat-
```

**What it does:**
- Monitors resources in secondary region (standby)
- Checks primary's heartbeat every 60 seconds
- **ALERTS OPS TEAM** if heartbeat missing for 5+ minutes
- Does NOT auto-failover (manual only)

## Step 2: Primary Region Goes Down

**Timeline:**
```
T+0:00  Primary AWS down
T+1:00  Primary monitoring heartbeat stops
T+5:00  Secondary monitoring alerts ops team
        Email subject: "⚠️ [MONITORING] Primary region heartbeat missing"
```

## Step 3: Execute Manual Failover

**When ops team is ready to failover:**

### Option A: Using Command Line Script (Recommended)

```bash
# On secondary region server, run:
python scripts/failover.py --config config/failover-secondary-config.yaml --prefix uat-
```

### Option B: Using Dashboard Failover Button (Future)

```
Dashboard → Click "Failover" button
→ Script launches in browser
→ Follow prompts
```

## Step 4: Interactive Resource Selection

The failover script will show you:

```
======================================================================
⚠️  PRIMARY REGION MONITORING ALERT
======================================================================

Primary Region: us-east-1
Secondary Region: us-west-2

Heartbeat Status:
  Healthy: False
  Age: 350 seconds
  Last seen: 2026-04-03T15:30:45.123456

🚨 PRIMARY REGION APPEARS TO BE DOWN!

Do you want to proceed with manual failover? (y/n):
```

### Select Each Resource

```
======================================================================
SELECT RESOURCES TO FAILOVER
======================================================================

📦 LAMBDA (3 resource(s))
----------------------------------------------------------------------

  [1] ✓ my-function-1
      ID: arn:aws:lambda:us-east-1:123456789:function:my-function-1
      Status: healthy
      Message: Function is active and performing normally
      Failover this resource? (y/n): y
      ✓ Selected for failover

  [2] ✓ my-function-2
      ID: arn:aws:lambda:us-east-1:123456789:function:my-function-2
      Status: healthy
      Message: Function is active and performing normally
      Failover this resource? (y/n): y
      ✓ Selected for failover

  [3] ✓ my-function-3
      ID: arn:aws:lambda:us-east-1:123456789:function:my-function-3
      Status: healthy
      Message: Function is active and performing normally
      Failover this resource? (y/n): n
      (skipped)

📦 EC2 (2 resource(s))
----------------------------------------------------------------------

  [1] ✓ web-server-1
      ID: i-0123456789abcdef0
      Status: healthy
      Message: Instance is running and healthy
      Failover this resource? (y/n): y
      ✓ Selected for failover

  [2] ✓ web-server-2
      ID: i-0987654321fedcba0
      Status: degraded
      Message: CPU utilization 85% exceeds threshold 80%
      Failover this resource? (y/n): y
      ✓ Selected for failover

📦 S3 (1 resource(s))
----------------------------------------------------------------------

  [1] ✓ my-bucket
      ID: my-bucket
      Status: healthy
      Message: Bucket is accessible and properly configured
      Failover this resource? (y/n): n
      (skipped)
```

### Final Confirmation

```
======================================================================
FAILOVER SUMMARY
======================================================================

Total resources to failover: 4

  LAMBDA:
    - arn:aws:lambda:us-east-1:123456789:function:my-function-1
    - arn:aws:lambda:us-east-1:123456789:function:my-function-2

  EC2:
    - i-0123456789abcdef0
    - i-0987654321fedcba0

Target Region: us-west-2

⚠️  WARNING: This will move resources to the secondary region.
    DNS/Routing will be updated to point to secondary region.
    Once failover starts, it cannot be easily reversed.

Final confirmation - proceed with failover? (yes/no): yes
```

## Step 5: Failover Execution

```
======================================================================
EXECUTING FAILOVER
======================================================================

🔄 Failing over LAMBDA (2 resource(s))...
   → arn:aws:lambda:us-east-1:123456789:function:my-function-1...✓
   → arn:aws:lambda:us-east-1:123456789:function:my-function-2...✓

🔄 Failing over EC2 (2 resource(s))...
   → i-0123456789abcdef0...✓
   → i-0987654321fedcba0...✓
```

## Step 6: Results

```
======================================================================
FAILOVER RESULTS
======================================================================

Status: completed
Primary Region: us-east-1
Target Region: us-west-2

Execution Results:

  LAMBDA:
    ✓ arn:aws:lambda:us-east-1:123456789:function:my-function-1: OK
    ✓ arn:aws:lambda:us-east-1:123456789:function:my-function-2: OK

  EC2:
    ✓ i-0123456789abcdef0: OK
    ✓ i-0987654321fedcba0: OK

======================================================================
NEXT STEPS:
----------------------------------------------------------------------
1. Verify failover resources are running in secondary region
2. Test application functionality
3. Update documentation/runbooks
4. Investigate primary region failure
5. Plan failback when primary recovers
======================================================================
```

## Benefits of Manual Approach

✅ **Human Decision Making** - Ops team decides which resources to failover
✅ **Selective Failover** - Don't have to failover everything
✅ **Safer** - No accidental automated failover
✅ **Flexible** - Can failover critical resources first
✅ **Auditable** - Every decision is logged
✅ **Time to Think** - Ops team can investigate before failover

## Example Scenarios

### Scenario 1: Failover Only Critical Services

**Situation:** Primary region down, but not critical to failover everything

```
Failover only:
  - Lambda API functions (critical)
  - RDS database (critical)

Skip:
  - Non-critical batch jobs
  - Development environments
  - Reporting databases
```

### Scenario 2: Partial Infrastructure Failure

**Situation:** Only EC2 cluster down, Lambda and S3 still working

```
Failover only:
  - EC2 instances in failed cluster

Skip:
  - Lambda functions (still working)
  - S3 buckets (still working)
  - RDS (in different AZ)
```

### Scenario 3: Failover Everything

**Situation:** Complete primary region failure

```
Failover all:
  - All Lambda functions
  - All EC2 instances
  - All databases
  - All storage
  - Everything
```

## Troubleshooting

### Script Won't Start

```bash
# Check secondary config is correct
cat config/failover-secondary-config.yaml

# Verify secondary region monitoring is running
curl http://localhost:5000/health

# Check AWS credentials
aws sts get-caller-identity --region us-west-2
```

### Heartbeat Detection Not Working

```bash
# Check DynamoDB table exists
aws dynamodb describe-table --table-name monitoring-heartbeat

# Check primary heartbeat is being written
aws dynamodb get-item \
  --table-name monitoring-heartbeat \
  --key '{"region": {"S": "us-east-1"}}'

# Check secondary monitoring logs
tail -f /tmp/monitoring.log | grep -i heartbeat
```

### Failover Stuck or Slow

- Failover can take 10-30 minutes depending on resource count
- Monitor script output for progress
- Check AWS CloudFormation events for resource creation status

## Testing Failover (Without Primary Failure)

To test the failover process without actual primary failure:

### Step 1: Simulate Primary Failure

```bash
# Temporarily stop primary monitoring
pkill -f "python src/main.py.*failover-primary-config"

# This simulates primary heartbeat stopping
```

### Step 2: Wait for Alert

Secondary monitoring will detect heartbeat missing in 5 minutes and alert.

### Step 3: Run Failover Script

```bash
python scripts/failover.py --config config/failover-secondary-config.yaml
```

### Step 4: Restart Primary

```bash
python src/main.py --config config/failover-primary-config.yaml --prefix uat- &
```

## Failback Procedure (After Primary Recovers)

Once primary region is restored:

### Step 1: Verify Primary is Healthy

```
Check on secondary dashboard:
  Primary Region Heartbeat: ✓ Healthy
  Last heartbeat: < 60 seconds ago
```

### Step 2: Plan Failback

Decide:
- Which resources to move back first (start with non-critical)
- Testing strategy before full failback
- Communication plan

### Step 3: Execute Failback

Similar process:
```bash
# On secondary, run manual failback script (future feature)
python scripts/failback.py --config config/failover-secondary-config.yaml
```

Or manually move resources back to primary region.

## Key Differences: Manual vs Automatic

| Aspect | Manual (Current) | Automatic (Not Used) |
|--------|-----------------|---------------------|
| **Decision Maker** | Human ops team | System automatically |
| **Resource Selection** | Choose which to failover | All resources |
| **Safety** | Higher - human checks | Lower - no verification |
| **Time to Failover** | 30-60 minutes | 20-30 minutes |
| **Error Recovery** | Can stop if issues found | Runs to completion |
| **Audit Trail** | Yes - user decisions | Limited |
| **Best For** | Selective failover | Complete region failure |

## FAQ

**Q: What if I select wrong resources by mistake?**
A: You get a final confirmation screen before execution. You can cancel at the last step.

**Q: How long does failover take?**
A: Typically 20-40 minutes depending on:
- Number of resources
- Resource type (Lambda vs EC2 vs RDS)
- Network/AWS API performance

**Q: Can I stop failover mid-execution?**
A: It's not recommended, but if you see failures:
- Stop the script (Ctrl+C)
- Check logs for what failed
- Manually clean up partial failover
- Restart when ready

**Q: What about data consistency?**
A: Depends on service:
- **Lambda**: Stateless, no data loss
- **S3**: Cross-region replication keeps data in sync
- **RDS**: Read replicas are used (minimal lag)
- **SQS**: Messages may be lost (accept risk or use DLQ)

**Q: Can we still access primary region during failover?**
A: If primary is completely down, no. If it's partially down, maybe:
- If API is accessible, primary monitoring continues
- Resources in secondary get activated
- During this time, you have dual resources (expensive!)

**Q: How do we fail back?**
A: When primary recovers, ops team must manually move resources back. Use similar interactive script.

---

## Summary

✅ **Manual, User-Controlled Failover**
✅ **Selective Resource Selection**
✅ **Heartbeat-Based Failure Detection**
✅ **Safe, Auditable, Reversible**
✅ **Step-by-Step Prompts**

This approach gives ops team full control while maintaining safety and auditability. Perfect for critical infrastructure where human decision-making is valued.
