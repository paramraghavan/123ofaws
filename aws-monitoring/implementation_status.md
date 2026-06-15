# AWS Monitoring System - Implementation Status

## Latest Features Implemented

### ✅ SNS FIFO Queue Alerting (Completed)
**When**: SNS topic ARN ends with `.fifo`
**What**: Automatically routes alerts to SQS FIFO queue instead of email
**Benefit**: Guaranteed ordering, deduplication, scalable alert processing
**Files**:
- `src/alerts/sqs_alerter.py` - New SQS alerter
- `src/alerts/alert_manager.py` - FIFO detection and routing
- `docs/fifo-queue-alerting.md` - Complete guide
- `FIFO_ALERTING_IMPLEMENTATION.md` - Feature summary

### ✅ Stack Redeployment During Failover (Completed)
**When**: CloudFormation stacks fail during failover
**What**: Attempts to recover failed stacks in normal mode, skips in fast mode
**Benefit**: Better reliability in normal mode, faster failover in fast mode
**Files**:
- `src/failover/failover_manager.py` - Enhanced stack checking and redeployment logic
- `STACK_REDEPLOYMENT_FEATURE.md` - Detailed feature documentation

---

## Feature Details

### Stack Redeployment Logic

#### Configuration Option
```yaml
failover:
  # Control how to handle failed stacks during failover
  fast_failover: true   # Skip failed stacks (speed)
  fast_failover: false  # Redeploy failed stacks (reliability)
```

#### Decision Tree
```
During Failover:
  For Each CloudFormation Stack:
    1. Get current stack status
    2. If CREATE_COMPLETE/UPDATE_COMPLETE/etc. → SKIP (already good)
    3. If CREATE_FAILED/UPDATE_FAILED/etc.:
       a. If fast_failover=true → SKIP (speed priority)
       b. If fast_failover=false → REDEPLOY (reliability priority)
    4. Otherwise → FAILOVER (standard process)
```

#### Redeployment Strategies
1. **Continue Update Rollback** (for ROLLBACK_COMPLETE)
   - Calls `continue_update_rollback` on stack
   - Completes partial rollback operations

2. **Delete and Recreate** (for CREATE_FAILED)
   - Deletes failed stack
   - Allows fresh recreation on next failover attempt

3. **Generic Failover** (fallback)
   - Standard failover for other states

#### Result Tracking
```python
failover_results = {
    'success': [...],    # Successfully deployed stacks
    'errors': [...],     # Stacks with errors
    'skipped': [...]     # Stacks skipped (fast mode or already complete)
}
```

### SNS FIFO Queue Alerting Logic

#### Automatic Detection
```python
if sns_topic_arn.endswith('.fifo'):
    # Use SQS FIFO queue alerter
    queue_url = convert_arn_to_queue_url(sns_topic_arn)
    alerter = SQSAlerter(session_manager, queue_url)
else:
    # Use standard SNS alerter
    alerter = SNSAlerter(session_manager, sns_topic_arn)
```

#### Alert Message Format (FIFO)
JSON message sent to SQS FIFO queue:
```json
{
  "alert_type": "resource_health",
  "service": "lambda",
  "resource_id": "arn:aws:lambda:...",
  "resource_name": "my-function",
  "status": "unhealthy",
  "emoji": "✗",
  "message": "Function error rate exceeds threshold",
  "timestamp": "2024-01-15T10:30:45.123456",
  "region": "us-east-1",
  "metrics": {...}
}
```

#### Deduplication
- MessageDeduplicationId: SHA256 hash of (resource_id + timestamp)
- MessageGroupId: Service name (e.g., "lambda-alerts")
- Prevents duplicate processing within 5-minute window

---

## Configuration Examples

### Example 1: Fast Failover (Speed Priority)
```yaml
failover:
  enabled: true
  mode: secondary
  fast_failover: true  # Skip failed stacks
  secondary_region: us-west-2

alerts:
  email_enabled: true
  email: ops@example.com
```
**Use Case**: Primary region is down, need secondary operational in <5 minutes
**What Happens**:
- Failed stacks are skipped
- Only successfully completed stacks are left untouched
- Fastest possible failover
- Post-failover, ops team can manually fix any failed stacks

### Example 2: Reliable Failover (Reliability Priority)
```yaml
failover:
  enabled: true
  mode: secondary
  fast_failover: false  # Attempt to redeploy failed stacks
  secondary_region: us-west-2

alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789012:monitoring-alerts
```
**Use Case**: Have 15 minutes to ensure all resources are properly deployed
**What Happens**:
- Failed stacks are automatically redeployed
- Better chance of full recovery
- Takes longer but more reliable
- SNS alerts sent on failures

### Example 3: Dual Alerting with FIFO Queue
```yaml
failover:
  enabled: true
  fast_failover: false

alerts:
  # Email alerts (primary)
  email_enabled: true
  email: ops@example.com
  smtp_host: smtp.gmail.com
  # ...

  # FIFO queue alerts (secondary, for processing/integration)
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789012:monitoring-alerts.fifo
```
**Result**:
- Ops team gets instant email
- Alert messages go to SQS FIFO queue for automated processing
- Can trigger Lambda, send to Slack, create tickets, etc.

---

## File Changes Summary

### New Files
- `src/alerts/sqs_alerter.py` - SQS FIFO alerter implementation
- `docs/fifo-queue-alerting.md` - FIFO queue setup and usage guide
- `STACK_REDEPLOYMENT_FEATURE.md` - Stack redeployment documentation
- `FIFO_ALERTING_IMPLEMENTATION.md` - FIFO alerting feature summary
- `config/config-fifo-alerts.yaml` - Example FIFO configuration

### Modified Files
- `src/failover/failover_manager.py`:
  - `_check_cloudformation_stack_status()` - Added `should_redeploy` flag
  - `execute_all_resources_failover()` - Enhanced stack checking logic
  - `_redeploy_failed_stack()` - New method for redeploying failed stacks

- `src/alerts/alert_manager.py`:
  - FIFO topic detection logic
  - Dynamic alerter selection (SQS vs SNS)
  - `_convert_topic_arn_to_queue_url()` - ARN to URL conversion

- Configuration files (all):
  - `config/config.example.yaml` - Added fast_failover and heartbeat options
  - `config/failover-primary-config.yaml` - Added fast_failover option
  - `config/failover-secondary-config.yaml` - Added fast_failover option

- Documentation:
  - `quick-start.md` - Updated with FIFO alerting info
  - `implementation-summary.md` - Updated to mention FIFO alerts

---

## Testing Checklist

### Stack Redeployment Testing
- [ ] Deploy stack in ROLLBACK_COMPLETE state
- [ ] Run failover with fast_failover=false
- [ ] Verify `continue_update_rollback` is called
- [ ] Check logs show "Redeploying failed stack"
- [ ] Verify failover_results tracks success/skip

- [ ] Deploy stack in CREATE_FAILED state
- [ ] Run failover with fast_failover=false
- [ ] Verify stack is deleted (delete_stack API called)
- [ ] Check logs show "Deleting failed stack for recreation"
- [ ] Verify failover_results tracks success

- [ ] Deploy stack in CREATE_FAILED state
- [ ] Run failover with fast_failover=true
- [ ] Verify stack is skipped (no deletion)
- [ ] Check logs show "Skipping (fast mode)"
- [ ] Verify failover_results shows in 'skipped' list

### FIFO Alerting Testing
- [ ] Create SNS FIFO topic (ending with .fifo)
- [ ] Create SQS FIFO queue
- [ ] Subscribe queue to topic
- [ ] Configure system with FIFO topic ARN
- [ ] Trigger unhealthy resource alert
- [ ] Verify JSON message in SQS queue
- [ ] Check message deduplication (send duplicate alert, verify not duplicated)
- [ ] Verify MessageGroupId = service name

- [ ] Configure system with standard SNS topic (no .fifo)
- [ ] Verify SNS alerter is used (not SQS)
- [ ] Trigger alert
- [ ] Verify message goes to SNS (not SQS)

- [ ] Configure both email and FIFO alerting
- [ ] Trigger alert
- [ ] Verify email is sent
- [ ] Verify message in SQS queue

---

## Performance Characteristics

### Stack Redeployment
- **Check status**: ~100ms (CloudFormation describe_stacks API)
- **Continue rollback**: ~500ms-2s (depends on CloudFormation operation)
- **Delete stack**: ~500ms-5s (depends on resource cleanup)
- **Fast mode vs Normal**: 2-5 minute difference in total failover time

### FIFO Alerting
- **Detection**: Instant (string endswith check)
- **Send to queue**: ~100ms per message
- **Deduplication**: Automatic (AWS managed)
- **Message size**: ~1-2KB per alert

---

## Troubleshooting

### Stack Won't Redeploy
**Symptom**: Stack stays in FAILED state even with fast_failover=false
**Causes**:
- Template has errors → Fix template
- Insufficient IAM permissions → Update role
- Resource limits → Increase limits
- CloudFormation service issues → Check CloudFormation API status

**Solution**:
```bash
# Check stack events for error
aws cloudformation describe-stack-events --stack-name my-stack

# Manually continue rollback
aws cloudformation continue-update-rollback --stack-name my-stack

# Manually delete
aws cloudformation delete-stack --stack-name my-stack
```

### Alerts Not Going to FIFO Queue
**Symptom**: SNS topic configured with .fifo but messages not in queue
**Causes**:
- Queue not subscribed to topic
- SNS topic permissions missing
- SQS queue doesn't exist

**Solution**:
```bash
# Check subscription
aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:...:.fifo

# Verify queue exists
aws sqs get-queue-attributes --queue-url https://sqs.../my-queue.fifo --attribute-names All

# Check permissions
aws sqs get-queue-attributes --queue-url ... --attribute-names Policy
```

### Failover Takes Too Long
**Symptom**: Failover exceeds RTO even though fast_failover=true
**Cause**: Still redeploying stacks (fast_failover might be false)

**Solution**:
```yaml
failover:
  fast_failover: true  # Ensure this is true
```

---

## Next Steps

1. **Test in Non-Production Environment**
   - Create test stacks that will fail
   - Test redeployment logic
   - Measure failover time

2. **Configure Alerting**
   - Set up FIFO queue if needed
   - Create Lambda consumer for FIFO messages
   - Test alert delivery

3. **Document Your Configuration**
   - Which mode: fast vs normal?
   - Which alerts: email, SNS, FIFO?
   - RTO targets and actual times

4. **Train Operations Team**
   - When to use fast vs normal mode
   - How to manually fix failed stacks
   - How to monitor redeployment progress

5. **Monitor in Production**
   - Set up CloudWatch dashboards for failover metrics
   - Monitor stack redeployment success rate
   - Track alert processing time

---

## Documentation References

- [Stack Redeployment Feature](STACK_REDEPLOYMENT_FEATURE.md) - Detailed feature guide
- [FIFO Queue Alerting](FIFO_ALERTING_IMPLEMENTATION.md) - FIFO setup and usage
- [FIFO Queue Setup Guide](docs/fifo-queue-alerting.md) - Step-by-step instructions
- [Failover Architecture](failover-architecture.md) - Overall system design
- [Manual Failover Guide](manual-failover-guide.md) - Operational procedures
- [Quick Start Guide](quick-start.md) - Configuration and deployment

