# Stack Redeployment During Failover

## Overview
The failover system now includes intelligent stack redeployment for failed CloudFormation stacks. This feature helps recover from transient failures during the failover process.

## How It Works

### Fast Mode vs Normal Mode

#### Fast Mode (`fast_failover: true`)
- **Goal**: Speed - Get the secondary region operational quickly
- **Logic**: Skip all recreation/redeployment work
  - Skip stacks with successful status (CREATE_COMPLETE, UPDATE_COMPLETE, etc.)
  - **Skip stacks with failed status** (don't attempt to fix)
  - Only process stacks in intermediate states
- **Use Case**: Primary region is down, need to failover NOW
- **Risk**: Some stacks may remain in failed state

#### Normal Mode (`fast_failover: false`)
- **Goal**: Reliability - Ensure all stacks are healthy
- **Logic**: Attempt to recover from failures
  - Skip stacks with successful status (no need to recreate)
  - **Attempt to redeploy stacks with failed status**
  - Automatic recovery strategies:
    1. `ROLLBACK_COMPLETE` → Continue update rollback
    2. `CREATE_FAILED` → Delete and recreate
    3. `UPDATE_FAILED` → Continue update
- **Use Case**: Have time to ensure all resources are properly deployed
- **Benefit**: More robust, better chance of full recovery

## Redeployment Strategies

### Strategy 1: Continue Update Rollback
**When**: Stack status is `ROLLBACK_COMPLETE` or `UPDATE_ROLLBACK_COMPLETE`
**Action**: Call `continue_update_rollback` on the stack
**Benefit**: Recovers from partial rollback states, completes the update
```bash
aws cloudformation continue-update-rollback --stack-name my-stack
```

### Strategy 2: Delete and Recreate
**When**: Stack status is `CREATE_FAILED`
**Action**: Delete the failed stack, then recreate it
**Benefit**: Cleans up partially created resources, allows fresh deployment
**Process**:
1. `aws cloudformation delete-stack --stack-name my-stack`
2. Wait for deletion to complete
3. Recreate the stack from template

### Strategy 3: Generic Failover
**When**: Other states or strategies don't apply
**Action**: Proceed with standard failover process
**Benefit**: Handles edge cases and unknown states gracefully

## Configuration

### Enable/Disable Redeployment

```yaml
failover:
  enabled: true

  # Use fast mode to skip redeployment
  fast_failover: true   # Skip failed stacks

  # Use normal mode to attempt redeployment
  fast_failover: false  # Attempt to redeploy failed stacks
```

## Example Scenarios

### Scenario 1: Transient API Failure During CREATE

**Situation**:
- Primary region goes down
- During failover, Lambda stack hits temporary AWS API rate limit
- Stack status becomes `CREATE_FAILED`

**Normal Mode Behavior**:
```
1. Detect stack_status = 'CREATE_FAILED'
2. Identify should_redeploy = true (not in fast mode)
3. Execute: Delete stack
4. Stack gets cleaned up
5. Next failover attempt can recreate successfully
```

**Fast Mode Behavior**:
```
1. Detect stack_status = 'CREATE_FAILED'
2. Identify should_redeploy = false (in fast mode)
3. Skip redeployment
4. Move to next resource type
5. Lambda resources unavailable in secondary region
```

### Scenario 2: Partial Update with Rollback

**Situation**:
- Primary region fails during update operation
- Stack stuck in `UPDATE_ROLLBACK_COMPLETE` state
- Needs to continue the update

**Normal Mode Behavior**:
```
1. Detect stack_status = 'UPDATE_ROLLBACK_COMPLETE'
2. Execute: continue_update_rollback
3. CloudFormation continues the update process
4. Stack recovers to UPDATE_COMPLETE
```

### Scenario 3: Time-Critical Failover

**Situation**:
- Primary region completely down
- Need to switch to secondary region ASAP
- Can investigate failures later

**Fast Mode Behavior**:
```
1. Skip all stack checks
2. Move to next resource type immediately
3. Quick failover - secondary operational in minutes
4. Post-failover: Investigate and fix failed stacks manually
```

## Logging

Watch the logs to see redeployment decisions:

```bash
# Normal mode with redeployment
INFO  Failing over lambda resources...
WARN  Stack UPDATE_ROLLBACK_COMPLETE, will redeploy
🔄 Redeploying failed stack lambda...
INFO  Attempting to redeploy stack lambda (current status: UPDATE_ROLLBACK_COMPLETE)
INFO  Continuing update for lambda from rollback state...
INFO  Alert sent via SNS: MessageId

# Fast mode without redeployment
INFO  Failing over ec2 resources...
INFO  Stack CREATE_FAILED, skipping (fast mode)
⊘ Skipping ec2: Stack CREATE_FAILED, skipping (fast mode)
```

## Stack Status Reference

### Successful Statuses (Always Skipped)
- `CREATE_COMPLETE` - Stack created successfully
- `UPDATE_COMPLETE` - Stack updated successfully
- `UPDATE_ROLLBACK_COMPLETE` - Rollback completed successfully

### Failed Statuses
| Status | Normal Mode | Fast Mode | Recovery Strategy |
|--------|-------------|-----------|-------------------|
| `CREATE_FAILED` | Redeploy | Skip | Delete and recreate |
| `UPDATE_FAILED` | Redeploy | Skip | Continue update |
| `UPDATE_ROLLBACK_FAILED` | Redeploy | Skip | Manual intervention |
| `DELETE_FAILED` | Redeploy | Skip | Manual cleanup |
| `ROLLBACK_COMPLETE` | Redeploy | Skip | Continue rollback |

### In-Progress Statuses (Always Processed)
- `CREATE_IN_PROGRESS`
- `UPDATE_IN_PROGRESS`
- `DELETE_IN_PROGRESS`
- `ROLLBACK_IN_PROGRESS`

## Best Practices

### 1. Choose Mode Based on Recovery Time Objective (RTO)

```yaml
# Aggressive failover (RTO < 5 minutes)
failover:
  fast_failover: true   # Speed > Perfection

# Conservative failover (RTO < 15 minutes)
failover:
  fast_failover: false  # Perfection > Speed
```

### 2. Monitor Redeployment Activity

```bash
# Watch the monitoring logs
tail -f /var/log/aws-monitoring/system.log | grep -i redeploy

# Or check failover results
curl http://localhost:5000/api/failover/status | jq .
```

### 3. Post-Failover Validation

After failover, verify stack health:
```bash
# Check all stacks in secondary region
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --region us-west-2 | jq '.StackSummaries[] | {StackName, StackStatus}'

# Verify all resources are accessible
python src/main.py --config config/failover-secondary-config.yaml --check-health
```

### 4. Combine with Monitoring

Use the monitoring system to detect failed stacks post-failover:
```yaml
# Check CloudFormation stack status during monitoring
services:
  cfn:
    enabled: true
    check_interval: 300  # Every 5 minutes
```

## Troubleshooting

### Redeployment Failed

**Symptom**: Stack still in failed state after redeployment attempt

**Causes**:
- CloudFormation template has issues
- Insufficient IAM permissions
- Resource limits exceeded
- Dependencies not met

**Solutions**:
```bash
# Check stack events for detailed failure reason
aws cloudformation describe-stack-events \
  --stack-name my-stack \
  --query 'StackEvents[0:5]' | jq .

# Manually continue update rollback
aws cloudformation continue-update-rollback --stack-name my-stack

# Manually delete failed stack
aws cloudformation delete-stack --stack-name my-stack
```

### Redeployment Took Too Long

**Symptom**: Redeployment caused total failover time to exceed RTO

**Solution**: Switch to fast mode
```yaml
failover:
  fast_failover: true  # Redeployment disabled
```

### Some Stacks Skipped in Normal Mode

**Cause**: Stack status not in recovery list
**Solution**: Use `fast_failover: false` to ensure processing

## Implementation Details

### Stack Status Check Flow

```
1. get_cloudformation_stack_status(stack_name)
   ├─ Query current stack status
   │
   ├─ if status in [CREATE_COMPLETE, UPDATE_COMPLETE, ...]
   │  └─> should_skip = true (no redeployment needed)
   │
   ├─ if status in [CREATE_FAILED, UPDATE_FAILED, ...]
   │  ├─> if fast_failover == true
   │  │   └─> should_skip = true, should_redeploy = false
   │  │
   │  └─> if fast_failover == false
   │      └─> should_skip = false, should_redeploy = true
   │
   └─> return {should_skip, should_redeploy, reason}

2. if should_skip → continue to next resource
3. if should_redeploy → call _redeploy_failed_stack()
4. else → call _failover_resource_type()
```

### Redeployment Strategy Selection

```python
def _redeploy_failed_stack(stack_name):
    status = get_current_status(stack_name)

    if status in [ROLLBACK_COMPLETE, UPDATE_ROLLBACK_COMPLETE]:
        continue_update_rollback(stack_name)
    elif status == CREATE_FAILED:
        delete_stack(stack_name)
        # Next failover will recreate
    else:
        failover_resource_type(stack_name)  # Generic failover
```

## Files Modified

- `src/failover/failover_manager.py`:
  - Updated `_check_cloudformation_stack_status()` to return `should_redeploy` flag
  - Updated `execute_all_resources_failover()` to check and handle redeployment
  - Added `_redeploy_failed_stack()` method with recovery strategies

## Related Documentation

- [Failover Architecture](failover-architecture.md) - Overall failover system design
- [Manual Failover Guide](manual-failover-guide.md) - Step-by-step failover workflow
- [Quick Start](quick-start.md) - Configuration and deployment
