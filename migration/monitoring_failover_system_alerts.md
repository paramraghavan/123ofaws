# Alerting When Monitoring/Failover System Fails

**How to get alerted when EC2, Lambda, or the entire AWS region fails while your monitoring/failover script is running**

---

## Table of Contents

1. [The Problem](#the-problem)
2. [Solution Overview](#solution-overview)
3. [Alerting Strategy for EC2-Based Monitoring](#alerting-strategy-for-ec2-based-monitoring)
4. [Alerting Strategy for Lambda-Based Monitoring](#alerting-strategy-for-lambda-based-monitoring)
5. [Region Failure Detection](#region-failure-detection)
6. [Multi-Region Redundancy](#multi-region-redundancy)
7. [Dashboard & Real-Time Monitoring](#dashboard--real-time-monitoring)
8. [Complete Setup Guide](#complete-setup-guide)

---

## The Problem

**You have a critical problem:**
- Your failover script runs on EC2 or Lambda
- It monitors other resources
- **But who monitors the monitor?**

If your EC2 instance or Lambda function fails:
- ❌ Your resources won't be monitored
- ❌ Failures won't be detected
- ❌ Failover won't be triggered
- ❌ Your business is down (silently)

**Solution:** Multi-layer alerting that detects when your monitoring system itself fails

---

## Solution Overview

### Three Layers of Alerts

```
Layer 1: Heartbeat Monitoring
├─ EC2 writes heartbeat every 5 minutes
├─ Lambda writes heartbeat after each run
└─ CloudWatch alarm triggers if heartbeat > 20 min old

Layer 2: System Health Monitoring
├─ CloudWatch metrics for EC2 (CPU, memory, disk)
├─ CloudWatch logs for Lambda errors
├─ SNS alerts for failures

Layer 3: Region Failure Detection
├─ Health check from secondary region
├─ Cross-region failover activation
└─ Automated script migration to backup region
```

### Alert Channels (SNS Topics)

```
SNS Topic: monitoring-system-alerts
├─ Email: ops-team@company.com
├─ SMS: +1-555-0123 (for critical)
├─ Slack: #aws-alerts
├─ PagerDuty: integration
└─ CloudWatch Dashboard: Real-time view
```

---

## Alerting Strategy for EC2-Based Monitoring

### EC2 Heartbeat Monitoring

**How it works:**
1. Your failover script writes a heartbeat file to S3 every 5 minutes
2. CloudWatch alarm checks if heartbeat is fresh (< 20 min old)
3. If no recent heartbeat → alarm triggers → SNS alert sent

### Step 1: Add Heartbeat to Your Script

**Before (your current script):**
```python
def failover_check():
    """Check and failover resources"""
    primary_healthy = check_primary()
    if not primary_healthy:
        execute_failover()
    log.info("Failover check complete")
```

**After (with heartbeat):**
```python
import boto3
import json
from datetime import datetime

s3 = boto3.client('s3')
HEARTBEAT_BUCKET = 'monitoring-heartbeat-logs'

def failover_check():
    """Check and failover resources"""
    try:
        primary_healthy = check_primary()
        if not primary_healthy:
            execute_failover()
        log.info("Failover check complete")

        # Write heartbeat
        write_heartbeat('success')
    except Exception as e:
        log.error(f"Error: {e}")
        write_heartbeat('error', str(e))

def write_heartbeat(status, error_msg=None):
    """Write heartbeat to S3 so external system can verify we're alive"""
    heartbeat = {
        'timestamp': datetime.utcnow().isoformat(),
        'hostname': socket.gethostname(),
        'status': status,
        'instance_id': get_instance_id(),
        'error': error_msg
    }

    s3.put_object(
        Bucket=HEARTBEAT_BUCKET,
        Key='heartbeat.json',
        Body=json.dumps(heartbeat),
        Metadata={'timestamp': str(int(time.time()))}
    )

def get_instance_id():
    """Get EC2 instance ID from metadata"""
    response = requests.get(
        'http://169.254.169.254/latest/meta-data/instance-id',
        timeout=1
    )
    return response.text
```

### Step 2: Create CloudWatch Alarm for Heartbeat Age

**Using Terraform:**
```hcl
# Create S3 bucket for heartbeat logs
resource "aws_s3_bucket" "heartbeat_logs" {
  bucket = "monitoring-heartbeat-logs-${data.aws_caller_identity.current.account_id}"
}

# Create CloudWatch alarm for stale heartbeat
resource "aws_cloudwatch_metric_alarm" "heartbeat_age" {
  alarm_name          = "failover-script-heartbeat-alarm"
  alarm_description   = "Alert if failover script heartbeat is stale (> 20 min)"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HeartbeatAge"
  namespace           = "CustomMonitoring/Failover"
  period              = 300  # Check every 5 minutes
  statistic           = "Maximum"
  threshold           = 1200  # 20 minutes in seconds
  alarm_actions       = [aws_sns_topic.monitoring_alerts.arn]

  treat_missing_data = "breaching"  # Alert if metric is missing
}

# Create SNS topic for alerts
resource "aws_sns_topic" "monitoring_alerts" {
  name = "monitoring-system-alerts"
}

resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.monitoring_alerts.arn
  protocol  = "email"
  endpoint  = "ops-team@company.com"
}

resource "aws_sns_topic_subscription" "slack_alerts" {
  topic_arn = aws_sns_topic.monitoring_alerts.arn
  protocol  = "https"
  endpoint  = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
}
```

**Using CloudFormation:**
```yaml
Resources:
  HeartbeatBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'monitoring-heartbeat-logs-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  MonitoringAlertsTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: monitoring-system-alerts
      DisplayName: Monitoring System Alerts

  EmailSubscription:
    Type: AWS::SNS::Subscription
    Properties:
      Protocol: email
      TopicArn: !Ref MonitoringAlertsTopic
      Endpoint: ops-team@company.com

  HeartbeatAgeAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: failover-script-heartbeat-alarm
      AlarmDescription: Alert if failover script heartbeat is stale (> 20 min)
      MetricName: HeartbeatAge
      Namespace: CustomMonitoring/Failover
      Statistic: Maximum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 1200
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref MonitoringAlertsTopic
      TreatMissingData: breaching
```

### Step 3: Lambda Function to Check Heartbeat Age

**Create a Lambda that runs every 5 minutes to calculate and publish heartbeat age:**

```python
import boto3
import json
from datetime import datetime, timedelta

s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

HEARTBEAT_BUCKET = 'monitoring-heartbeat-logs'

def lambda_handler(event, context):
    """
    Check heartbeat from EC2 monitoring script
    If stale, publish metric that triggers alarm
    """
    try:
        # Read heartbeat from S3
        response = s3.get_object(
            Bucket=HEARTBEAT_BUCKET,
            Key='heartbeat.json'
        )
        heartbeat = json.loads(response['Body'].read())

        # Calculate age
        last_update = datetime.fromisoformat(heartbeat['timestamp'])
        age_seconds = (datetime.utcnow() - last_update).total_seconds()

        # Publish metric
        cloudwatch.put_metric_data(
            Namespace='CustomMonitoring/Failover',
            MetricData=[
                {
                    'MetricName': 'HeartbeatAge',
                    'Value': age_seconds,
                    'Unit': 'Seconds',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'HeartbeatStatus',
                    'Value': 1 if heartbeat['status'] == 'success' else 0,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

        return {
            'statusCode': 200,
            'heartbeat_age': age_seconds,
            'instance_id': heartbeat.get('instance_id'),
            'status': heartbeat['status']
        }

    except s3.exceptions.NoSuchKey:
        # No heartbeat found - publish high age value to trigger alarm
        cloudwatch.put_metric_data(
            Namespace='CustomMonitoring/Failover',
            MetricData=[
                {
                    'MetricName': 'HeartbeatAge',
                    'Value': 9999,  # Very large number to trigger alarm
                    'Unit': 'Seconds'
                }
            ]
        )
        raise Exception("No heartbeat found from EC2 monitoring script")

    except Exception as e:
        print(f"Error: {e}")
        raise

# EventBridge trigger (run every 5 minutes)
# {
#   "Name": "check-monitoring-heartbeat",
#   "ScheduleExpression": "rate(5 minutes)",
#   "Targets": [
#     {
#       "Arn": "arn:aws:lambda:region:account:function:check-heartbeat",
#       "RoleArn": "arn:aws:iam::account:role/service-role"
#     }
#   ]
# }
```

### Step 4: EC2 System Health Monitoring

**Monitor EC2 instance health itself:**

```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.client('ec2')

def publish_system_metrics():
    """
    Publish EC2 system metrics to CloudWatch
    Called by your monitoring script every 5 minutes
    """
    import psutil

    metrics = [
        {
            'MetricName': 'CPUUtilization',
            'Value': psutil.cpu_percent(interval=1),
            'Unit': 'Percent'
        },
        {
            'MetricName': 'MemoryUtilization',
            'Value': psutil.virtual_memory().percent,
            'Unit': 'Percent'
        },
        {
            'MetricName': 'DiskUtilization',
            'Value': psutil.disk_usage('/').percent,
            'Unit': 'Percent'
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='CustomMonitoring/EC2Instance',
        MetricData=metrics
    )

# Set up alarms for system health
def create_ec2_health_alarms():
    """Create alarms for CPU, memory, disk"""

    alarms = [
        {
            'AlarmName': 'monitoring-ec2-high-cpu',
            'MetricName': 'CPUUtilization',
            'Threshold': 80,
            'ComparisonOperator': 'GreaterThanThreshold'
        },
        {
            'AlarmName': 'monitoring-ec2-high-memory',
            'MetricName': 'MemoryUtilization',
            'Threshold': 85,
            'ComparisonOperator': 'GreaterThanThreshold'
        },
        {
            'AlarmName': 'monitoring-ec2-high-disk',
            'MetricName': 'DiskUtilization',
            'Threshold': 90,
            'ComparisonOperator': 'GreaterThanThreshold'
        }
    ]

    for alarm in alarms:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm['AlarmName'],
            MetricName=alarm['MetricName'],
            Namespace='CustomMonitoring/EC2Instance',
            Statistic='Average',
            Period=300,
            EvaluationPeriods=2,
            Threshold=alarm['Threshold'],
            ComparisonOperator=alarm['ComparisonOperator'],
            AlarmActions=[SNS_TOPIC_ARN],
            TreatMissingData='notBreaching'
        )
```

---

## Alerting Strategy for Lambda-Based Monitoring

### Lambda Heartbeat Pattern

**How it works:**
1. Lambda writes heartbeat after each execution
2. CloudWatch alarm checks if Lambda ran in last N minutes
3. If Lambda failed or didn't run → alarm triggers

### Step 1: Lambda Handler with Heartbeat

```python
import boto3
import json
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

HEARTBEAT_BUCKET = 'monitoring-heartbeat-logs'
HEARTBEAT_KEY = 'lambda-heartbeat.json'

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        # Your monitoring logic here
        result = run_monitoring()

        # Write heartbeat on success
        write_heartbeat('success', result)

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error in monitoring: {e}")
        # Write heartbeat even on error
        write_heartbeat('error', {'error': str(e)})
        raise

def write_heartbeat(status, data=None):
    """Write heartbeat indicating Lambda is alive"""
    heartbeat = {
        'timestamp': datetime.utcnow().isoformat(),
        'lambda_function': 'monitoring-failover',
        'aws_request_id': context.aws_request_id,
        'status': status,
        'data': data
    }

    try:
        s3.put_object(
            Bucket=HEARTBEAT_BUCKET,
            Key=HEARTBEAT_KEY,
            Body=json.dumps(heartbeat),
            ServerSideEncryption='AES256'
        )
        logger.info("Heartbeat written to S3")
    except Exception as e:
        logger.error(f"Failed to write heartbeat: {e}")

def run_monitoring():
    """Your actual monitoring logic"""
    # Check resources, execute failover, etc.
    return {'resources_checked': 10, 'failovers': 0}

# Required: Get context as global for heartbeat
context = None

def lambda_handler_wrapper(event, context_param):
    global context
    context = context_param
    return lambda_handler(event, context_param)
```

**Better approach: Use context within lambda_handler:**

```python
def lambda_handler(event, context):
    """Lambda handler with proper context"""
    try:
        # Your monitoring logic
        result = run_monitoring()

        # Write heartbeat
        write_heartbeat_with_context(context, 'success', result)

        # Publish success metric
        cloudwatch.put_metric_data(
            Namespace='CustomMonitoring/Lambda',
            MetricData=[{
                'MetricName': 'ExecutionStatus',
                'Value': 1,  # 1 = success
                'Unit': 'Count'
            }]
        )

        return {'statusCode': 200, 'body': json.dumps(result)}

    except Exception as e:
        logger.error(f"Error: {e}")
        write_heartbeat_with_context(context, 'error', {'error': str(e)})

        # Publish failure metric
        cloudwatch.put_metric_data(
            Namespace='CustomMonitoring/Lambda',
            MetricData=[{
                'MetricName': 'ExecutionStatus',
                'Value': 0,  # 0 = failure
                'Unit': 'Count'
            }]
        )
        raise

def write_heartbeat_with_context(context, status, data):
    """Write heartbeat with Lambda context"""
    heartbeat = {
        'timestamp': datetime.utcnow().isoformat(),
        'lambda_function': context.function_name,
        'lambda_version': context.function_version,
        'request_id': context.aws_request_id,
        'memory_limit': context.memory_limit_in_mb,
        'status': status,
        'data': data
    }

    s3.put_object(
        Bucket='monitoring-heartbeat-logs',
        Key='lambda-heartbeat.json',
        Body=json.dumps(heartbeat)
    )
```

### Step 2: CloudWatch Alarm for Lambda Execution

**Monitor if Lambda is actually running:**

```yaml
Resources:
  LambdaHeartbeatAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: lambda-monitoring-heartbeat
      AlarmDescription: Alert if monitoring Lambda hasn't executed in 20 min
      MetricName: Invocations
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300  # 5 minutes
      EvaluationPeriods: 4  # 20 minutes total
      Threshold: 0  # Expect at least 1 invocation per 5 min
      ComparisonOperator: LessThanOrEqualToThreshold
      Dimensions:
        - Name: FunctionName
          Value: monitoring-failover-lambda
      AlarmActions:
        - !Ref MonitoringAlertsTopic
      TreatMissingData: breaching

  LambdaErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: lambda-monitoring-errors
      AlarmDescription: Alert if monitoring Lambda has errors
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      Dimensions:
        - Name: FunctionName
          Value: monitoring-failover-lambda
      AlarmActions:
        - !Ref MonitoringAlertsTopic

  LambdaTimeoutAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: lambda-monitoring-timeout
      AlarmDescription: Alert if monitoring Lambda times out
      MetricName: Duration
      Namespace: AWS/Lambda
      Statistic: Maximum
      Period: 300
      Threshold: 55000  # 55 seconds (60 second timeout)
      ComparisonOperator: GreaterThanOrEqualToThreshold
      Dimensions:
        - Name: FunctionName
          Value: monitoring-failover-lambda
      AlarmActions:
        - !Ref MonitoringAlertsTopic
```

### Step 3: Monitor Lambda Logs for Errors

```python
import boto3
from datetime import datetime, timedelta

logs = boto3.client('logs')

def check_lambda_logs_for_errors():
    """
    Check CloudWatch logs for errors in last 15 minutes
    Alert if errors found
    """
    log_group = '/aws/lambda/monitoring-failover'

    # Query logs for errors
    start_time = int((datetime.utcnow() - timedelta(minutes=15)).timestamp() * 1000)
    end_time = int(datetime.utcnow().timestamp() * 1000)

    response = logs.filter_log_events(
        logGroupName=log_group,
        startTime=start_time,
        endTime=end_time,
        filterPattern='ERROR'  # Only ERROR level logs
    )

    if response['events']:
        # Errors found - send alert
        error_message = '\n'.join([
            f"[{event['timestamp']}] {event['message']}"
            for event in response['events']
        ])

        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:region:account:monitoring-system-alerts',
            Subject='Lambda Monitoring Script Errors Detected',
            Message=f"Errors found in Lambda logs:\n\n{error_message}"
        )
```

---

## Region Failure Detection

### The Problem: AWS Region Failure

**If an entire AWS region fails:**
- Your monitoring Lambda/EC2 stops running
- Resources in that region become unreachable
- But monitoring system itself is down

### Solution: Cross-Region Monitoring

**Deploy secondary monitoring system in another region:**

```
Primary Region (us-east-1):
├─ EC2/Lambda monitoring script
├─ S3 heartbeat logs
└─ SNS alerts

Secondary Region (us-west-2):
├─ Read-only Lambda checking primary heartbeat
├─ Detects primary region failure
├─ Activates automatic failover
└─ Starts monitoring from secondary region
```

### Step 1: Secondary Region Health Check

```python
import boto3
from datetime import datetime, timedelta

s3_primary = boto3.client('s3', region_name='us-east-1')
s3_secondary = boto3.client('s3', region_name='us-west-2')
sns = boto3.client('sns', region_name='us-west-2')

HEARTBEAT_BUCKET_PRIMARY = 'monitoring-heartbeat-logs-us-east-1'

def lambda_handler_secondary_region(event, context):
    """
    Run in secondary region
    Check if primary region monitoring is healthy
    """

    try:
        # Try to read heartbeat from primary region
        response = s3_primary.get_object(
            Bucket=HEARTBEAT_BUCKET_PRIMARY,
            Key='heartbeat.json'
        )

        heartbeat = json.loads(response['Body'].read())
        last_update = datetime.fromisoformat(heartbeat['timestamp'])
        age = (datetime.utcnow() - last_update).total_seconds()

        if age > 1200:  # > 20 minutes
            # Primary monitoring is stale
            trigger_region_failover(heartbeat)
            return {
                'statusCode': 500,
                'message': 'Primary region monitoring is stale - failover activated'
            }

        return {
            'statusCode': 200,
            'heartbeat_age': age,
            'message': 'Primary region healthy'
        }

    except Exception as e:
        # Can't reach primary region - assume failure
        trigger_region_failover({'error': str(e)})
        return {
            'statusCode': 500,
            'message': f'Primary region unreachable: {e}'
        }

def trigger_region_failover(primary_heartbeat):
    """
    Activate secondary region failover
    """
    # Notify operations team
    sns.publish(
        TopicArn='arn:aws:sns:us-west-2:account:critical-alerts',
        Subject='🚨 PRIMARY REGION FAILURE - Activating Secondary Region',
        Message=f"""
        PRIMARY REGION (us-east-1) FAILURE DETECTED

        Last heartbeat: {primary_heartbeat.get('timestamp', 'Unknown')}
        Error: {primary_heartbeat.get('error', 'No recent heartbeat')}

        SECONDARY REGION (us-west-2) ACTIVATED

        Actions taken:
        1. Starting monitoring script in secondary region
        2. Updating Route 53 to use secondary endpoints
        3. Checking all resources in secondary region
        4. Notifying team

        Please verify:
        - Primary region services (may be restored)
        - Secondary region resources are healthy
        - Traffic is correctly routed
        """
    )

    # Start monitoring in secondary region
    activate_secondary_monitoring()

def activate_secondary_monitoring():
    """Start full monitoring in secondary region"""
    lambda_secondary = boto3.client('lambda', region_name='us-west-2')

    # Invoke secondary monitoring Lambda
    lambda_secondary.invoke(
        FunctionName='monitoring-failover-secondary',
        InvocationType='Event'  # Async
    )
```

### Step 2: Terraform for Multi-Region Setup

```hcl
# Primary region (us-east-1)
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

# Secondary region (us-west-2)
provider "aws" {
  alias  = "secondary"
  region = "us-west-2"
}

# Primary Lambda
resource "aws_lambda_function" "monitoring_primary" {
  provider = aws.primary
  filename = "lambda_monitoring.zip"
  function_name = "monitoring-failover-primary"
  # ... other config
}

# Secondary Lambda (read-only health check)
resource "aws_lambda_function" "monitoring_secondary" {
  provider = aws.secondary
  filename = "lambda_secondary_check.zip"
  function_name = "monitoring-failover-secondary"
  # ... other config
}

# EventBridge in secondary region (every 5 minutes)
resource "aws_cloudwatch_event_rule" "secondary_health_check" {
  provider            = aws.secondary
  name                = "check-primary-region-health"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "secondary_health_check" {
  provider  = aws.secondary
  rule      = aws_cloudwatch_event_rule.secondary_health_check.name
  target_id = "lambda-secondary-health-check"
  arn       = aws_lambda_function.monitoring_secondary.arn
}
```

---

## Multi-Region Redundancy

### Recommended Setup

```
                    ┌─────────────────┐
                    │   MONITORING    │
                    │    SYSTEM       │
                    └────────┬────────┘
                             │
                    ┌────────┴─────────┐
                    │                  │
            ┌───────▼────────┐  ┌──────▼───────┐
            │  Primary       │  │  Secondary   │
            │  Region        │  │  Region      │
            │  (us-east-1)   │  │  (us-west-2) │
            │                │  │              │
            │ ┌────────────┐ │  │ ┌──────────┐ │
            │ │ EC2/Lambda │ │  │ │ Standby  │ │
            │ │ Monitoring │ │  │ │ Lambda   │ │
            │ └──────┬─────┘ │  │ │ (check   │ │
            │        │       │  │ │  health) │ │
            │ ┌──────▼─────┐ │  │ └──────────┘ │
            │ │ Heartbeat  │ │  │              │
            │ │ S3 Bucket  │ │  │ ┌──────────┐ │
            │ └────────────┘ │  │ │ Failover │ │
            │                │  │ │ S3 Bucket│ │
            │ ┌────────────┐ │  │ └──────────┘ │
            │ │ SNS Topic  │ │  │              │
            │ │ (alerts)   │ │  │ ┌──────────┐ │
            │ └────────────┘ │  │ │ SNS Topic│ │
            └────────────────┘  │ │(failover)│ │
                                 │ └──────────┘ │
                                 └──────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │ Alert Channels:  │
                            │ • Email          │
                            │ • SMS (critical) │
                            │ • Slack          │
                            │ • PagerDuty      │
                            └──────────────────┘
```

---

## Dashboard & Real-Time Monitoring

### CloudWatch Dashboard

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def create_monitoring_dashboard():
    """Create dashboard showing monitoring system health"""

    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
                        [".", "Errors", {"stat": "Sum"}],
                        [".", "Duration", {"stat": "Average"}],
                        ["CustomMonitoring/Failover", "HeartbeatAge"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Monitoring Lambda Health"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["CustomMonitoring/EC2Instance", "CPUUtilization"],
                        [".", "MemoryUtilization"],
                        [".", "DiskUtilization"]
                    ],
                    "title": "Monitoring EC2 Instance Health"
                }
            },
            {
                "type": "log",
                "properties": {
                    "query": """
                    fields @timestamp, @message, @logStream
                    | filter @message like /ERROR/
                    | stats count() by @logStream
                    """,
                    "region": "us-east-1",
                    "title": "Error Count by Log Stream"
                }
            }
        ]
    }

    cloudwatch.put_dashboard(
        DashboardName='Monitoring-System-Health',
        DashboardBody=json.dumps(dashboard_body)
    )
```

### Slack Integration for Alerts

```python
import requests
import json

SLACK_WEBHOOK = 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

def send_slack_alert(status, details):
    """Send alert to Slack"""

    if status == 'critical':
        color = 'danger'
        icon = '🚨'
    elif status == 'warning':
        color = 'warning'
        icon = '⚠️'
    else:
        color = 'good'
        icon = '✅'

    message = {
        "attachments": [
            {
                "color": color,
                "title": f"{icon} Monitoring System Alert",
                "text": details['message'],
                "fields": [
                    {
                        "title": "Timestamp",
                        "value": details.get('timestamp'),
                        "short": True
                    },
                    {
                        "title": "Severity",
                        "value": status.upper(),
                        "short": True
                    },
                    {
                        "title": "Details",
                        "value": details.get('details', 'N/A'),
                        "short": False
                    }
                ]
            }
        ]
    }

    response = requests.post(
        SLACK_WEBHOOK,
        data=json.dumps(message),
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        raise ValueError(f'Slack webhook failed: {response.status_code}')
```

---

## Complete Setup Guide

### Quick Start: Add Alerts to Your Monitoring System

#### For EC2-Based Monitoring

```bash
# 1. Create S3 bucket for heartbeat
aws s3 mb s3://monitoring-heartbeat-logs-$(aws sts get-caller-identity --query Account --output text)

# 2. Create SNS topic
aws sns create-topic --name monitoring-system-alerts

# 3. Subscribe to email
aws sns subscribe \
  --topic-arn arn:aws:sns:region:account:monitoring-system-alerts \
  --protocol email \
  --notification-endpoint ops-team@company.com

# 4. Update EC2 script with heartbeat code (see examples above)

# 5. Create CloudWatch alarm for heartbeat
aws cloudwatch put-metric-alarm \
  --alarm-name failover-script-heartbeat \
  --alarm-description "Alert if failover script heartbeat is stale" \
  --metric-name HeartbeatAge \
  --namespace CustomMonitoring/Failover \
  --statistic Maximum \
  --period 300 \
  --evaluation-periods 4 \
  --threshold 1200 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:region:account:monitoring-system-alerts

# 6. Deploy Lambda to check heartbeat age (see code above)
zip check_heartbeat.zip check_heartbeat.py
aws lambda create-function \
  --function-name check-monitoring-heartbeat \
  --runtime python3.11 \
  --role arn:aws:iam::account:role/lambda-execution-role \
  --handler check_heartbeat.lambda_handler \
  --zip-file fileb://check_heartbeat.zip

# 7. Add EventBridge trigger
aws events put-rule \
  --name check-monitoring-heartbeat \
  --schedule-expression "rate(5 minutes)"

aws events put-targets \
  --rule check-monitoring-heartbeat \
  --targets "Id=1,Arn=arn:aws:lambda:region:account:function:check-monitoring-heartbeat,RoleArn=arn:aws:iam::account:role/service-role"
```

#### For Lambda-Based Monitoring

```bash
# 1. Create S3 bucket for heartbeat
aws s3 mb s3://monitoring-heartbeat-logs-$(aws sts get-caller-identity --query Account --output text)

# 2. Create SNS topic
aws sns create-topic --name monitoring-system-alerts

# 3. Update Lambda code with heartbeat (see examples above)

# 4. Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-monitoring-invocations \
  --metric-name Invocations \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=monitoring-failover-lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 4 \
  --threshold 0 \
  --comparison-operator LessThanOrEqualToThreshold

aws cloudwatch put-metric-alarm \
  --alarm-name lambda-monitoring-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=monitoring-failover-lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold
```

---

## Summary: Monitoring the Monitor

**Your monitoring system now has 3 layers of protection:**

| Layer | Watches | Alert On |
|-------|---------|----------|
| **Heartbeat** | EC2/Lambda writing heartbeat | > 20 min without heartbeat |
| **System Health** | EC2 CPU/Memory/Disk, Lambda errors | High resource usage, Lambda failures |
| **Region** | Primary region from secondary | Primary region unavailable |

**Alert Channels:**
- Email (immediate)
- SMS (critical only)
- Slack (team notification)
- PagerDuty (on-call rotation)
- CloudWatch Dashboard (real-time view)

**Result:** If your monitoring system fails for ANY reason, you'll know within 5-20 minutes and can activate backup procedures.

