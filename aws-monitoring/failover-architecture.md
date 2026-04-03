# Failover Architecture & Strategy

## Current Limitation ⚠️

**Problem:** If primary region AWS goes down, the monitoring system running in the primary region also goes down and **cannot execute failover**.

```
Primary Region (us-east-1) DOWN
├── Monitoring System ❌ (DOWN - can't run)
├── Lambda Functions ❌
├── EC2 Instances ❌
└── Resources ❌

Secondary Region (us-west-2)
├── Standby Resources (idle)
└── No way to trigger failover (monitoring is down)
```

**Current Behavior:** Manual failover only works if monitoring system is still running.

---

## Solution: Active-Passive Failover Architecture

### Architecture Design

```
┌─────────────────────────────────────────────────────────────┐
│ Primary Region (us-east-1) - ACTIVE                         │
├─────────────────────────────────────────────────────────────┤
│ ✓ Monitoring System (active)                                │
│ ✓ Production Resources                                      │
│ ✓ Dashboard at http://primary-monitoring.example.com:5000  │
└─────────────────────────────────────────────────────────────┘
           ↓ (Sends heartbeat every minute)
        SNS/DynamoDB
           ↓
┌─────────────────────────────────────────────────────────────┐
│ Secondary Region (us-west-2) - STANDBY                      │
├─────────────────────────────────────────────────────────────┤
│ ✓ Monitoring System (passive, watching primary)             │
│ ✓ Standby Resources (cold, ready to activate)               │
│ ✓ Dashboard at http://secondary-monitoring.example.com:5000│
│ ✓ Auto-detects primary failure → Auto-activates failover   │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

#### **Phase 1: Normal Operation (Primary Region Active)**

```
Primary Monitoring System:
  1. Checks all resources every 5 minutes
  2. Sends heartbeat to DynamoDB/SNS every 60 seconds
  3. Sends alerts to ops team
  4. Dashboard shows all resources status

Secondary Monitoring System:
  1. Watches primary's heartbeat
  2. If heartbeat stops for 5 minutes → ALERT
  3. If still missing for 10 minutes → AUTO-FAILOVER
  4. Activates standby resources
```

#### **Phase 2: Primary Region Failure Detected**

```
Timeline:
  T+0:00 - Primary region AWS goes down
  T+1:00 - Primary monitoring system stops sending heartbeat
  T+5:00 - Secondary monitoring detects no heartbeat (still waiting)
  T+10:00 - Secondary monitoring confirms primary is down
           - Secondary monitoring initiates AUTOMATIC failover
           - Sends alert to ops team
           - Starts activating secondary resources
```

#### **Phase 3: Automatic Failover Execution**

```
Secondary Monitoring System Executes:
  1. For each resource in primary region:
     ├─ Create replica in secondary region (copy, replicate, etc.)
     ├─ Update DNS/Route53 to point to secondary
     ├─ Enable traffic to secondary resources
     ├─ Log the action
     └─ Send alert to ops team

  2. Monitor secondary resources
     ├─ Check if they're healthy
     ├─ Alert if activation fails
     └─ Continue monitoring

  3. Wait for manual intervention
     ├─ Ops team investigates primary region
     ├─ Once primary recovers
     ├─ Ops team initiates failback
     └─ Resources move back to primary
```

---

## Implementation: Dual-Region Monitoring

### Step 1: Deploy Monitoring in Both Regions

```bash
# Primary Region (us-east-1)
cd /Users/paramraghavan/dev/123ofaws/aws-monitoring
export AWS_REGION=us-east-1
python src/main.py --config config/primary-monitoring.yaml --prefix uat- &

# Secondary Region (us-west-2) - In separate terminal or EC2
export AWS_REGION=us-west-2
python src/main.py --config config/secondary-monitoring.yaml --prefix uat- &
```

### Step 2: Heartbeat & Failover Detection

**Primary Region Config:**
```yaml
# config/primary-monitoring.yaml
aws:
  primary_region: us-east-1
  secondary_region: us-west-2

monitoring:
  check_interval: 300
  heartbeat_enabled: true
  heartbeat_interval: 60  # Send heartbeat every 60 seconds
  heartbeat_table: monitoring-heartbeat

failover:
  enabled: true
  auto_failover: false  # Manual only in primary
  mode: primary

services:
  # ... all services enabled
```

**Secondary Region Config:**
```yaml
# config/secondary-monitoring.yaml
aws:
  primary_region: us-east-1    # Still references primary for standby resources
  secondary_region: us-west-2

monitoring:
  check_interval: 300
  heartbeat_enabled: true
  heartbeat_interval: 60

failover:
  enabled: true
  auto_failover: true          # AUTO failover in secondary!
  mode: secondary
  primary_failure_timeout: 300  # Failover after 5 min no heartbeat
  failover_threshold: 2         # Confirm twice before failover

services:
  # ... all services enabled
```

### Step 3: Heartbeat Detection

**DynamoDB Table:**
```
monitoring-heartbeat
├─ region: "us-east-1" (partition key)
├─ last_heartbeat: 2026-04-03T15:30:45.123456
├─ status: "healthy"
├─ resources_count: 45
└─ ttl: 2026-04-03T15:40:45  # Auto-delete old entries
```

**Secondary Monitors Heartbeat:**
```python
# Secondary monitoring system
def check_primary_heartbeat():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('monitoring-heartbeat')

    response = table.get_item(Key={'region': 'us-east-1'})

    if 'Item' not in response:
        # Primary is dead
        heartbeat_age = float('inf')
    else:
        last_beat = response['Item']['last_heartbeat']
        heartbeat_age = datetime.now() - last_beat

    if heartbeat_age > timedelta(minutes=5):
        logger.warning("Primary region heartbeat is stale!")
        initiate_failover()
```

---

## Failover Execution Steps

### Manual Failover (Current - Resources 1, 2, N)

**User:** "Failover Lambda function 1 and EC2 instance 2"

```
Step 1: User Input
  ├─ Dashboard: Select resources to failover
  ├─ Click "Initiate Failover"
  └─ System asks for confirmation

Step 2: Pre-Failover Checks
  ├─ Verify secondary region is healthy
  ├─ Check secondary resources don't already exist
  ├─ Verify DNS/Route53 access
  └─ If checks fail → abort, alert ops

Step 3: Failover Lambda Function
  ├─ Primary Region: Get function code
  │   └─ aws lambda get-function --function-name my-function
  ├─ Secondary Region: Create function
  │   └─ aws lambda create-function --code from-primary
  ├─ Secondary Region: Configure environment variables
  │   └─ Copy settings from primary function
  ├─ DNS Update: Point to secondary (Route53)
  │   └─ Update CNAME to secondary Lambda
  └─ Verify: Test function in secondary

Step 4: Failover EC2 Instance
  ├─ Primary Region: Create AMI from instance
  │   └─ aws ec2 create-image --instance-id i-xxxxx
  ├─ Copy AMI to Secondary Region
  │   └─ aws ec2 copy-image --source-ami ami-xxxxx
  ├─ Secondary Region: Launch instance from AMI
  │   └─ aws ec2 run-instances --image-id ami-yyyyy
  ├─ Update Load Balancer (if exists)
  │   └─ Add secondary instance to ALB target group
  ├─ Update DNS if needed
  │   └─ Point to secondary ELB/ALB
  └─ Verify: Test instance connectivity

Step 5: Failover S3 Bucket (if needed)
  ├─ Enable cross-region replication
  │   └─ Data auto-syncs to secondary
  ├─ Update Route53/DNS to point to secondary
  └─ Update application configs (if needed)

Step 6: Post-Failover Validation
  ├─ Test all failover resources
  ├─ Verify application functionality
  ├─ Monitor secondary resources
  ├─ Alert ops team with status
  └─ Log all actions for audit

Step 7: Ongoing Monitoring
  ├─ Monitor secondary resources (same checks as primary)
  ├─ Continue sending heartbeat to primary region
  ├─ Wait for manual failback decision
  └─ Document RTO/RPO achieved
```

### Automatic Failover (When Primary Region is Down)

**Trigger:** Primary region completely down (no AWS API access)

```
T+0:00 - Primary region AWS down
         ├─ Lambda functions unreachable
         ├─ EC2 instances in primary region down
         ├─ Primary monitoring system can't send heartbeat
         └─ Primary dashboard unreachable

T+5:00 - Secondary monitoring detects missing heartbeat
         ├─ Log: "Primary region heartbeat missing"
         ├─ Alert ops: "Primary region may be down"
         └─ Wait for confirmation

T+10:00 - Second heartbeat check confirms primary down
         ├─ Log: "CRITICAL: Primary region is down"
         ├─ Alert ops: "Initiating automatic failover"
         ├─ Secondary monitoring starts failover process
         └─ Begin steps 2-7 above (automatically)

T+15:00 - Lambda functions are being created in secondary
         ├─ Copying function code from primary (from S3 backup)
         ├─ Creating function in secondary region
         ├─ Updating Route53
         └─ Testing function

T+20:00 - EC2 instances being launched in secondary
         ├─ Using pre-made AMIs in secondary region
         ├─ Launching instances
         ├─ Configuring load balancers
         └─ Testing connectivity

T+30:00 - All failover complete
         ├─ Secondary monitoring confirms all resources healthy
         ├─ Alert ops: "Failover complete, application on secondary"
         ├─ Switchboard shows: "Primary: DOWN, Secondary: ACTIVE"
         └─ Ops team begins incident response

T+30:00+ - Ongoing monitoring
         ├─ Continue monitoring secondary resources
         ├─ Watch for primary region recovery
         ├─ Prepare for failback when primary recovered
         └─ Keep detailed logs
```

---

## Key Challenges & Solutions

### Challenge 1: Primary Region is Down, How Do We Failover?

**Answer:** Deploy secondary monitoring system in secondary region BEFORE primary goes down.

```
Before Failure:
  ✓ Primary monitoring running in us-east-1
  ✓ Secondary monitoring running in us-west-2 (passive, watching primary)
  ✓ Both have IAM roles to access both regions

Primary Region Down:
  ✓ Secondary monitoring system is STILL RUNNING in us-west-2
  ✓ Secondary monitoring detects primary is down
  ✓ Secondary monitoring initiates failover (running in us-west-2)
  ✓ Failover happens FROM secondary region TO secondary resources
```

### Challenge 2: How to Failover "All Resources" (1, 2, N)?

**Answer:** Iterate through all resources and failover each:

```python
# Pseudo-code for failover all resources
def failover_all_resources():
    for service in [lambda, ec2, s3, sqs, ...]:
        for resource in get_resources_in_primary(service):
            try:
                failover_resource(service, resource)
                log_success(service, resource)
            except Exception as e:
                log_error(service, resource, e)
                continue  # Don't stop, failover next

    send_alert("Failover complete. Check dashboard.")
```

### Challenge 3: Data Consistency During Failover

**Solution:** Different strategies by service:

```
Lambda:
  └─ Stateless, just redeploy code
  └─ No data sync needed (read from S3/DynamoDB)

EC2:
  └─ Use snapshots/AMIs for OS/config
  └─ Read data from EBS snapshots or S3

S3:
  └─ Use cross-region replication (automatic)
  └─ All data already in secondary

RDS:
  └─ Use read replicas in secondary region
  └─ Promote replica on failover

SQS/SNS:
  └─ Messages may be lost (accept as risk)
  └─ Re-create queues in secondary
```

### Challenge 4: Cost of Dual Region Monitoring

**Solution:** Optimize for standby mode:

```
Primary Region (us-east-1):
  ├─ Monitoring System: t3.micro
  ├─ Dashboard: t3.micro
  └─ Cost: ~$30/month

Secondary Region (us-west-2) PASSIVE:
  ├─ Monitoring System: t3.micro (light load, watching primary)
  ├─ Dashboard: t3.micro (low traffic)
  ├─ Standby Resources: Stopped/minimal config
  └─ Cost: ~$30/month

Total: ~$60/month for dual-region monitoring
(vs. downtime cost if primary fails)
```

---

## Implementation Plan

### Phase 1: Enable Manual Failover (Current)
- ✅ Single region monitoring
- ✅ Manual failover for specific resources
- ❌ Can't handle primary region failure

### Phase 2: Add Heartbeat Detection
- ✅ Deploy secondary monitoring (watch mode)
- ✅ Heartbeat to DynamoDB
- ✅ Alert ops when primary is down
- ❌ Still manual failover

### Phase 3: Enable Automatic Failover
- ✅ Secondary monitoring auto-fails over
- ✅ All resources moved to secondary
- ✅ Application continues on secondary
- ✅ Handles primary region complete failure

---

## FAQ

### Q: If primary region is down, how does secondary region know?

**A:**
```
1. Secondary monitoring system runs in secondary region
2. It periodically checks primary region's heartbeat in DynamoDB
3. DynamoDB is in BOTH regions (global table)
4. If heartbeat is missing, secondary region knows primary is down
5. Secondary region can then failover
```

### Q: What if DynamoDB itself is down in primary?

**A:**
```
Solution: Use DynamoDB Global Tables
├─ Table exists in both regions
├─ Writes to primary replicate to secondary
├─ If primary region down, use secondary copy
└─ Automatic failover at database level
```

### Q: How do we failover Lambda functions?

**A:**
```
1. Get source code from S3 (where it's stored)
2. Create function in secondary region with same config
3. Update Route53 DNS to point to secondary
4. Test the function
5. Done!
```

### Q: What about databases (RDS)?

**A:**
```
1. Set up RDS read replica in secondary region BEFORE failure
2. On failover, promote read replica to standalone DB
3. Update application connection strings
4. Done!
```

### Q: What about data loss?

**A:**
```
RPO (Recovery Point Objective) depends on service:
├─ S3: 0 (cross-region replication)
├─ RDS: Few seconds (read replica lag)
├─ Lambda: 0 (no state)
├─ SQS: Minutes (unprocessed messages may be lost)
└─ EC2: Depends on last snapshot/AMI

Minimize data loss with:
├─ Use cross-region replication for data stores
├─ Take frequent snapshots
├─ Use managed services with built-in HA
└─ Accept RPO/RTO for non-critical services
```

### Q: RTO - How long until secondary is active?

**A:**
```
Manual Failover: 15-30 minutes
├─ User clicks failover
├─ System copies resources
├─ DNS updates (5-10 min propagation)
├─ Testing and verification

Automatic Failover: 30-60 minutes
├─ Detect primary is down (10 min)
├─ Initiate failover (5 min)
├─ Copy resources (10-30 min depending on size)
├─ Update DNS and test (5-10 min)

Critical goal: < 1 hour RTO
```

---

## Recommended Setup for Your Use Case

### For UAT-Top, UAT-Bot, Production

```yaml
# Primary Region: us-east-1 (ACTIVE)
Monitoring System:
  └─ Monitors all uat-top, uat-bot, prod resources
  └─ Sends heartbeat every 60 seconds
  └─ Manual failover available

# Secondary Region: us-west-2 (STANDBY)
Monitoring System:
  └─ Watches primary's heartbeat
  └─ If primary down > 5 min: Alert ops
  └─ If primary down > 10 min: Auto-failover
  └─ Handles failover of all resources

# Failover Procedure
Manual:
  1. User selects resources on dashboard
  2. Click "Failover to us-west-2"
  3. System confirms, executes failover
  4. Resources move to secondary

Automatic (if primary region completely down):
  1. Secondary monitoring detects primary down
  2. Automatically initiates failover
  3. All resources move to secondary
  4. Ops team notified
  5. Application continues on secondary
```

---

## Next Steps

To implement this:

1. **Create secondary monitoring deployment**
   - Deploy monitoring system to us-west-2
   - Configure as "secondary/passive" mode

2. **Add heartbeat table**
   - Create DynamoDB table (or use global table)
   - Primary writes heartbeat every 60 seconds
   - Secondary reads heartbeat every minute

3. **Implement automatic failover**
   - If heartbeat missing 5+ minutes, alert
   - If heartbeat missing 10+ minutes, auto-failover
   - Execute failover for all resources

4. **Test failover**
   - Simulate primary region failure
   - Verify secondary takes over
   - Test application on secondary
   - Verify failback when primary recovers

This ensures your system can survive **complete primary region failure** and continue operating from the secondary region.

---

**Key Insight:**
> The monitoring system itself must be redundant. If your monitoring is only in the failed region, it can't help you failover. Deploy monitoring to BOTH regions so the secondary can detect and respond to primary failure.
