# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "Access Denied" Error on NFS Location

**Symptoms:**
```
Error: PermissionError accessing NFS location
ClientError: An error occurred (InvalidLocationArn) when calling the CreateTask operation
```

**Root Causes:**
1. DataSync agent doesn't have NFS mount permissions
2. Agent security group doesn't allow NFS traffic (port 2049)
3. NAS is not accessible from agent network

**Solutions:**

```bash
# 1. Verify NFS mount is accessible from agent
ssh ec2-user@agent-ip
mount | grep poolData
ls -la /mydata/prod/icm/datain/poolData/

# 2. Check NFS permissions
getfacl /mydata/prod/icm/datain/poolData/

# 3. Fix agent security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 2049 \
  --cidr 10.0.0.0/8

# 4. Verify NAS export configuration
# On NAS server, check /etc/exports:
# /vol/xxx1nas456av45mir/he7unx999 *(rw,sync,no_subtree_check)

# 5. Restart DataSync agent
ssh ec2-user@agent-ip
sudo systemctl restart aws-datasync-agent
```

---

### Issue 2: "Task Execution Failed" - No Files Copied

**Symptoms:**
```
Task execution status: FAILED
BytesCopied: 0
FilesTransferred: 0
ErrorCode: ERROR_INVALID_LOCATION_OR_MISSING_FILES
```

**Root Causes:**
1. Source path doesn't exist on NAS
2. Date format is incorrect
3. No files exist for the requested date
4. Source path configuration is wrong

**Solutions:**

```bash
# 1. Verify NAS path exists
ssh ec2-user@agent-ip
ls -la /mydata/prod/icm/datain/poolData/datatype1/2024/0804/

# 2. Check date format (should be YYYY/MMDD)
# Correct: /mydata/prod/icm/datain/poolData/datatype1/2024/0804/
# Incorrect: /mydata/prod/icm/datain/poolData/datatype1/2024-08-04/

# 3. Verify files exist in the directory
find /mydata/prod/icm/datain/poolData/datatype1/2024/0804/ -type f | head -5

# 4. Check config path settings
cat config.py | grep NAS_BASE_PATH

# 5. Debug by checking Lambda function logs
aws logs tail /aws/lambda/datasync-orchestrator --follow
```

---

### Issue 3: Lambda Function Timeout

**Symptoms:**
```
Lambda response: Task timed out after 300 seconds
```

**Root Causes:**
1. TASK_TIMEOUT_SECONDS too short for data volume
2. DataSync task taking longer than expected
3. Multiple large files being transferred

**Solutions:**

```bash
# 1. Increase Lambda timeout
aws lambda update-function-configuration \
  --function-name datasync-orchestrator \
  --timeout 900  # Increase to 15 minutes

# 2. Check DataSync task execution time
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:us-east-1:123456789012:tasexecution/xxxxx
# Look for "StartTime" and "EndTime"

# 3. Increase DataSync task timeout in config.py
# TASK_TIMEOUT_SECONDS = 3600  # 1 hour

# 4. For large transfers, use wait_for_completion=False
# Lambda will start task but not wait for completion
python lambda_function.py daily  # Check logs later

# 5. Monitor data size
du -sh /mydata/prod/icm/datain/poolData/datatype1/2024/0804/
```

---

### Issue 4: S3 Destination Permissions Error

**Symptoms:**
```
Error: ClientError - Access Denied (S3 bucket)
DataSync agent missing PutObject permission
```

**Root Causes:**
1. DataSync S3 location doesn't have correct IAM role
2. S3 bucket policy doesn't allow DataSync agent
3. S3 bucket encryption key access issue

**Solutions:**

```bash
# 1. Verify DataSync S3 location IAM role
aws datasync describe-location-s3 \
  --location-arn arn:aws:datasync:us-east-1:123456789012:location/s3/yyyyy
# Check "S3Config.BucketAccessRoleArn"

# 2. Update S3 location with correct role
aws datasync update-location-s3 \
  --location-arn arn:aws:datasync:us-east-1:123456789012:location/s3/yyyyy \
  --s3-config BucketAccessRoleArn=arn:aws:iam::123456789012:role/datasync-s3-role

# 3. Create S3 IAM role if needed
aws iam create-role \
  --role-name datasync-s3-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "datasync.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 4. Attach S3 permissions
aws iam put-role-policy \
  --role-name datasync-s3-role \
  --policy-name s3-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::my-datasync-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::my-datasync-bucket"
    }]
  }'

# 5. For encrypted buckets, add KMS permissions
aws iam put-role-policy \
  --role-name datasync-s3-role \
  --policy-name kms-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/xxxxx"
    }]
  }'
```

---

### Issue 5: SNS Notification Not Received

**Symptoms:**
```
Lambda function succeeds but no email notification
```

**Root Causes:**
1. SNS topic ARN not configured correctly
2. Email subscription not confirmed
3. SNS publish permission missing from Lambda role

**Solutions:**

```bash
# 1. Verify SNS topic exists
aws sns list-topics | grep datasync-notifications

# 2. Check email subscription status
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:123456789012:datasync-notifications

# 3. Confirm subscription (check email for confirmation link)
# Look for "AWS Notification" email

# 4. Check Lambda environment variable
aws lambda get-function-configuration \
  --function-name datasync-orchestrator \
  | grep SNS_TOPIC_ARN

# 5. Verify Lambda role has SNS publish permission
aws iam get-role-policy \
  --role-name datasync-orchestrator-lambda-role \
  --policy-name datasync-policy

# 6. Test SNS publish manually
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789012:datasync-notifications \
  --subject "Test Message" \
  --message "This is a test"
```

---

### Issue 6: Task Created But Not Executing

**Symptoms:**
```
DataSync task exists but never starts
Status: READY, but no TaskExecutionArn
```

**Root Causes:**
1. Lambda not calling start_task_execution
2. Task schedule is set to auto-run but EventBridge trigger missing
3. Task permissions issue

**Solutions:**

```bash
# 1. Check Lambda logs for task creation
aws logs tail /aws/lambda/datasync-orchestrator --follow

# 2. Manually trigger Lambda with test event
aws lambda invoke \
  --function-name datasync-orchestrator \
  --payload '{"scenario":"daily"}' \
  response.json

# 3. Verify EventBridge rule is enabled
aws events describe-rule --name datasync-daily-copy

# 4. List task executions
aws datasync list-task-executions \
  --task-arn arn:aws:datasync:us-east-1:123456789012:task/xxxxx

# 5. Check task status
aws datasync describe-task \
  --task-arn arn:aws:datasync:us-east-1:123456789012:task/xxxxx
```

---

### Issue 7: Date Calculation Wrong

**Symptoms:**
```
Expected to copy 2024/0804 but copied 2024/0805
Or copied multiple dates when only today expected
```

**Root Causes:**
1. Timezone mismatch (Lambda runs in UTC)
2. Date format incorrect
3. Scenario parameter wrong

**Solutions:**

```bash
# 1. Check Lambda timezone (runs in UTC)
aws lambda invoke \
  --function-name datasync-orchestrator \
  --payload '{"scenario":"daily"}' \
  response.json
cat response.json | python -m json.tool | grep date

# 2. For specific date, use backdated scenario
aws lambda invoke \
  --function-name datasync-orchestrator \
  --payload '{"scenario":"backdated","custom_date":"2024/0804"}' \
  response.json

# 3. Test date logic locally
python -c "
from date_logic import DateLogic
print('Today:', DateLogic.get_today())
print('Yesterday:', DateLogic.get_yesterdays_date())
"

# 4. Verify date format is YYYY/MMDD
# Correct: 2024/0804
# Incorrect: 2024-08-04 or 2024/08/04
```

---

### Issue 8: "Agent Not Available" Error

**Symptoms:**
```
Error: DataSync agent not found or offline
ClientError: The agent for this location is not available
```

**Root Causes:**
1. Agent service stopped or crashed
2. Agent network connectivity issue
3. Agent credentials expired

**Solutions:**

```bash
# 1. SSH to agent and check status
ssh ec2-user@agent-ip
sudo systemctl status aws-datasync-agent

# 2. Restart agent
sudo systemctl restart aws-datasync-agent

# 3. Check agent logs
sudo tail -f /var/log/datasync/agent.log

# 4. Verify network connectivity
ping google.com
curl -I https://aws.amazon.com

# 5. Check DNS resolution
nslookup datasync.amazonaws.com

# 6. Check security group outbound rules
# Agent needs outbound HTTPS (port 443)

# 7. List agents and verify registration
aws datasync list-agents
```

---

## Debug Tips

### Enable Debug Logging

```bash
# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name datasync-orchestrator \
  --environment "Variables={LOG_LEVEL=DEBUG}"

# View detailed logs
aws logs tail /aws/lambda/datasync-orchestrator --follow --log-stream-names lambda-xxx
```

### Local Testing

```bash
# Install dependencies locally
pip install -r requirements.txt

# Test with different scenarios
python lambda_function.py daily
python lambda_function.py backdated 2024/0721
python lambda_function.py range 7

# Run unit tests
python -m pytest test_date_logic.py -v
```

### Manual DataSync Task Execution

```bash
# Create task manually to test
aws datasync create-task \
  --source-location-arn arn:aws:datasync:us-east-1:123456789012:location/nfs/xxxxx \
  --destination-location-arn arn:aws:datasync:us-east-1:123456789012:location/s3/yyyyy \
  --name "manual-test-task" \
  --options VerifyMode=POINT_IN_TIME_CONSISTENT,OverwriteMode=ALWAYS

# Start execution
aws datasync start-task-execution \
  --task-arn arn:aws:datasync:us-east-1:123456789012:task/manual-test

# Monitor
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:us-east-1:123456789012:tasexecution/manual-test
```

---

## Getting Help

- Check AWS DataSync documentation: https://docs.aws.amazon.com/datasync/
- Review CloudWatch Logs in detail
- Check DataSync agent logs on edge node
- Open AWS Support ticket for infrastructure issues

