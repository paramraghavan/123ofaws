# CloudWatch Monitoring for an S3 Ingestion Pipeline

## Purpose

This guide explains how to monitor a file-based ingestion pipeline that starts with files landing in Amazon S3 and continues through Lambda, SNS, SQS, and a downstream job-trigger Lambda. It focuses on practical CloudWatch metrics, alarms, dashboards, and troubleshooting queries.

The most important design point is this: only Lambda writes application logs to CloudWatch Logs. S3, SNS, and SQS publish service metrics directly to CloudWatch. You alarm on those native metrics without creating log groups for those services.

## Pipeline at a Glance

| Service | Role | How It Is Monitored |
| --- | --- | --- |
| S3 bucket | Receives incoming files and triggers the pipeline | Native CloudWatch metrics. S3 request metrics must be enabled for request-level metrics. |
| Trigger Lambda | Receives the S3 event and publishes to SNS | Lambda native metrics, CloudWatch Logs, metric filters, and Logs Insights |
| SNS topic | Fans file-arrival events out to SQS | Native CloudWatch metrics |
| SQS queue | Buffers jobs for the job-trigger Lambda | Native CloudWatch metrics |
| SQS DLQ | Receives messages that failed processing repeatedly | Native CloudWatch metrics; alarm on any visible message |
| Job-trigger Lambda | Polls SQS and performs or starts ingestion work | Lambda native metrics, CloudWatch Logs, metric filters, and Logs Insights |

## Monitoring Layers

There are four monitoring layers:

1. Lambda log groups capture application-level events from your code.
2. Metric filters turn selected log patterns into custom CloudWatch metrics.
3. Native AWS service metrics track Lambda, S3, SNS, and SQS behavior.
4. CloudWatch alarms evaluate metrics and notify a dedicated SNS alerts topic.

```text
Lambda code -> CloudWatch Logs -> Metric Filter -> Custom Metric
                                                   \
                                                    -> CloudWatch Alarm -> SNS alerts topic -> Email / Slack / PagerDuty
                                                   /
S3 / SNS / SQS / Lambda -> Native CloudWatch Metrics
```

Use a dedicated alerts SNS topic that is separate from the pipeline SNS topic. If the pipeline topic has delivery issues, the monitoring path must still be able to alert.

## Step 1: Create Lambda Log Groups and Retention Policies

Lambda automatically creates a log group the first time a function runs. Creating the log groups explicitly lets you set retention before logs accumulate.

```bash
aws logs create-log-group \
  --log-group-name /aws/lambda/ingest-trigger-lambda

aws logs create-log-group \
  --log-group-name /aws/lambda/job-trigger-lambda

aws logs put-retention-policy \
  --log-group-name /aws/lambda/ingest-trigger-lambda \
  --retention-in-days 30

aws logs put-retention-policy \
  --log-group-name /aws/lambda/job-trigger-lambda \
  --retention-in-days 30
```

These log group names are used later by metric filters, dashboards, and CloudWatch Logs Insights queries.

## Step 2: Emit Structured Logs from Lambda

Use structured JSON logs so every event is searchable by file, stage, status, and error. Also re-raise unexpected exceptions so the built-in `AWS/Lambda` `Errors` metric increments.

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    record = event["Records"][0]
    file_key = record["s3"]["object"]["key"]

    try:
        # Run ingestion logic here.
        logger.info(json.dumps({
            "status": "success",
            "file": file_key,
            "pipeline_stage": "ingest-trigger"
        }))
    except Exception as exc:
        logger.error(json.dumps({
            "status": "error",
            "error": str(exc),
            "file": file_key,
            "pipeline_stage": "ingest-trigger"
        }))
        raise
```

For SQS-driven Lambdas, log the SQS `messageId`, source file key, and pipeline stage in the same format.

## Step 3: Create Metric Filters on Lambda Log Groups
> create cloudwatch metrics

Metric filters scan log events and publish custom CloudWatch metrics when a pattern matches. Prefer matching the JSON field value instead of matching a broad string such as `ERROR`.

```bash
aws logs put-metric-filter \
  --log-group-name /aws/lambda/ingest-trigger-lambda \
  --filter-name ErrorFilter \
  --filter-pattern '{ $.status = "error" }' \
  --metric-transformations \
    metricName=IngestTriggerErrors,metricNamespace=YourPipeline,metricValue=1,defaultValue=0

aws logs put-metric-filter \
  --log-group-name /aws/lambda/job-trigger-lambda \
  --filter-name ErrorFilter \
  --filter-pattern '{ $.status = "error" }' \
  --metric-transformations \
    metricName=JobTriggerErrors,metricNamespace=YourPipeline,metricValue=1,defaultValue=0
```

In the `--metric-transformations` value, `metricValue=1,defaultValue=0` means:

- `metricValue=1`: every matching log event contributes `1` to the metric. If three log events match `{ $.status = "error" }` in a one-minute period, the metric sum for that minute is `3`.
- `defaultValue=0`: when no log events match during a period, CloudWatch publishes `0` instead of leaving the metric with no data.

For error counting, `metricValue=1,defaultValue=0` is usually the right choice because each matching error log should count as one error, and quiet periods should mean zero errors.

You can use different values when the log event represents something other than a single event. For example, `metricValue` can be a constant such as `1` or `5`, or it can come from a numeric field in the JSON log, such as a record count or processing duration.

| Example | Meaning | Typical Use |
| --- | --- | --- |
| `metricValue=1` | Count each matching log event as one unit. | Error count, retry count, success count |
| `metricValue=5` | Count each matching log event as five units. | Rare; useful only if one log line always represents five records, files, or work units |
| `metricValue=$.duration_ms` | Publish the numeric `duration_ms` field from the JSON log. | Processing duration or latency metrics |
| `metricValue=$.record_count` | Publish the numeric `record_count` field from the JSON log. | Total records processed |

`defaultValue=0` is important. Without it, quiet periods may show as missing data instead of zero errors, which can leave alarms in `INSUFFICIENT_DATA`.

## Step 4: Identify the Native Metrics That Matter

S3, SNS, SQS, and Lambda publish service metrics to CloudWatch. You do not create log groups or metric filters for these services.

### List Available Metrics

Use `list-metrics` to confirm the metric names and dimensions that have emitted data.

```bash
aws cloudwatch list-metrics \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=your-ingestion-queue

aws cloudwatch list-metrics \
  --namespace AWS/SNS \
  --dimensions Name=TopicName,Value=your-ingest-topic

aws cloudwatch list-metrics \
  --namespace AWS/S3 \
  --dimensions Name=BucketName,Value=your-bucket-name

aws cloudwatch list-metrics \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=ingest-trigger-lambda
```

A metric appears only after it has at least one data point. If a metric is missing, trigger a real test event and then check the namespace, resource name, and region.

### SQS Main Queue Metrics

| Metric | What It Tells You |
| --- | --- |
| `ApproximateNumberOfMessagesVisible` | Messages waiting to be picked up. A rising value usually means the job-trigger Lambda has stopped consuming. |
| `ApproximateAgeOfOldestMessage` | Age of the oldest unprocessed message. This is the best early signal for a stuck queue. |
| `ApproximateNumberOfMessagesNotVisible` | Messages in flight. High values may mean the Lambda is slow, failing mid-process, or timing out before deleting messages. |
| `NumberOfMessagesDeleted` | Messages successfully processed and deleted. A sudden drop can mean the consumer stopped. |

### SQS DLQ Metrics

The highest-priority DLQ alarm is `ApproximateNumberOfMessagesVisible > 0`. Any visible DLQ message means at least one file or job failed enough times to be abandoned by the main processing path.

### SNS Metrics

| Metric | What It Tells You |
| --- | --- |
| `NumberOfMessagesPublished` | Events SNS received from the trigger Lambda. This should roughly match file-arrival volume. |
| `NumberOfNotificationsDelivered` | Successful deliveries from SNS to subscriptions such as SQS. |
| `NumberOfNotificationsFailed` | Delivery failures. Even one failure can indicate a dropped pipeline event. |

### S3 Metrics

S3 daily storage metrics are automatic. S3 request metrics, such as `PutRequests`, `4xxErrors`, and `5xxErrors`, must be enabled per bucket or prefix.

```bash
aws s3api put-bucket-metrics-configuration \
  --bucket your-bucket-name \
  --id EntireBucket \
  --metrics-configuration '{"Id":"EntireBucket"}'
```

| Metric | What It Tells You |
| --- | --- |
| `PutRequests` | Files or objects being written. A sudden drop may indicate an upstream delivery issue. |
| `4xxErrors` | Client-side or permission errors accessing the bucket. |
| `5xxErrors` | S3-side server errors or transient service issues. |

### Lambda Native Metrics

| Metric | What It Tells You |
| --- | --- |
| `Errors` | Unhandled exceptions and failed invocations. |
| `Throttles` | Invocations rejected due to concurrency limits. |
| `Duration` | Function execution time. Rising duration can indicate downstream slowness. |
| `IteratorAge` | For stream-based sources only; not relevant to basic S3 or SQS eventing. |
| `ConcurrentExecutions` | Useful for capacity and concurrency planning. |

## Step 5: Create the Alerts SNS Topic

Create the dedicated SNS topic that CloudWatch alarms will publish to.

```bash
aws sns create-topic --name pipeline-alerts
```

The command returns a `TopicArn`, for example:

```text
arn:aws:sns:us-east-1:123456789012:pipeline-alerts
```

Subscribe the notification channels you use operationally:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:pipeline-alerts \
  --protocol email \
  --notification-endpoint oncall@yourcompany.com

aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:pipeline-alerts \
  --protocol https \
  --notification-endpoint https://events.pagerduty.com/integration/YOUR_KEY/enqueue

aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:pipeline-alerts \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:slack-notifier
```

Email subscriptions require confirmation before messages are delivered.

## Step 6: Create CloudWatch Alarms

Create one alarm per failure mode. The alarm shape is the same whether the metric comes from a metric filter or a native AWS service metric.

Set this variable in your shell to keep examples shorter:

```bash
ALERTS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:pipeline-alerts"
```

### Lambda Alarms

Create two alarm types for each Lambda:

| Alarm Type | Metric Source | What It Catches |
| --- | --- | --- |
| Native Lambda error alarm | `AWS/Lambda` `Errors` metric | Invocations that Lambda marks as failed, such as unhandled exceptions, timeouts, runtime crashes, or code that logs an error and then raises the exception. |
| Custom log-based error alarm | Custom metric in `YourPipeline` | Errors your application logs explicitly, including cases where the Lambda invocation completes but the pipeline logic still detected a problem. |

Using both gives better coverage. Native Lambda alarms tell you the function invocation failed. Custom log-based alarms tell you the application observed an error condition.

Built-in Lambda errors catch unhandled exceptions and failed invocations.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name IngestLambda-Errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=ingest-trigger-lambda \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"

aws cloudwatch put-metric-alarm \
  --alarm-name JobTriggerLambda-Errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=job-trigger-lambda \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"
```

These two alarms mean:

- `IngestLambda-Errors` fires when `ingest-trigger-lambda` has one or more failed invocations in a 60-second window.
- `JobTriggerLambda-Errors` fires when `job-trigger-lambda` has one or more failed invocations in a 60-second window.

Custom log-based metrics catch errors your code logs explicitly. These alarms do not include `--filter-name` or `--filter-pattern` because alarms do not read log lines directly. The filter pattern belongs to the earlier `aws logs put-metric-filter` command in Step 3.

The sequence is:

```text
Lambda logs {"status":"error"}
  -> CloudWatch Logs metric filter matches '{ $.status = "error" }'
  -> Metric filter increments YourPipeline/IngestTriggerErrors or YourPipeline/JobTriggerErrors
  -> CloudWatch alarm watches that custom metric
  -> SNS alert is sent
```

So these custom alarms are correct only after the matching metric filters have been created:

```bash
aws logs put-metric-filter \
  --log-group-name /aws/lambda/ingest-trigger-lambda \
  --filter-name ErrorFilter \
  --filter-pattern '{ $.status = "error" }' \
  --metric-transformations \
    metricName=IngestTriggerErrors,metricNamespace=YourPipeline,metricValue=1,defaultValue=0

aws logs put-metric-filter \
  --log-group-name /aws/lambda/job-trigger-lambda \
  --filter-name ErrorFilter \
  --filter-pattern '{ $.status = "error" }' \
  --metric-transformations \
    metricName=JobTriggerErrors,metricNamespace=YourPipeline,metricValue=1,defaultValue=0
```

After those metric filters exist, create alarms that reference the metric name and namespace. Do not add `--filter-name` or `--filter-pattern` to `aws cloudwatch put-metric-alarm`; those options are not valid for alarm creation.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name IngestLambda-LogErrors \
  --metric-name IngestTriggerErrors \
  --namespace YourPipeline \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"

aws cloudwatch put-metric-alarm \
  --alarm-name JobTriggerLambda-LogErrors \
  --metric-name JobTriggerErrors \
  --namespace YourPipeline \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"
```

These two alarms mean:

- `IngestLambda-LogErrors` fires when the custom metric `YourPipeline/IngestTriggerErrors` reaches one or more errors in a 60-second window.
- `JobTriggerLambda-LogErrors` fires when the custom metric `YourPipeline/JobTriggerErrors` reaches one or more errors in a 60-second window.

The important alarm parameters are:

| Parameter | Meaning |
| --- | --- |
| `--alarm-name` | Name of the CloudWatch alarm. |
| `--metric-name` | Metric being watched. `Errors` is built in; `IngestTriggerErrors` and `JobTriggerErrors` are custom metrics created by metric filters. |
| `--namespace` | Metric namespace. `AWS/Lambda` is AWS-native; `YourPipeline` is the custom namespace used by this guide. |
| `--dimensions` | Narrows an AWS metric to a specific Lambda function. Native Lambda metrics require `FunctionName`; the custom metrics in this guide do not use dimensions. |
| `--statistic Sum` | Adds up all metric values in the evaluation window. |
| `--period 60` | Evaluates the metric in 60-second windows. |
| `--threshold 1` | Alarm when the metric reaches at least one error. |
| `--comparison-operator GreaterThanOrEqualToThreshold` | Fires when the metric value is greater than or equal to the threshold. |
| `--evaluation-periods 1` | One failing period is enough to move the alarm to `ALARM`. |
| `--treat-missing-data notBreaching` | If no metric data arrives, treat it as OK rather than as a failure. |
| `--alarm-actions` | SNS topic to notify when the alarm enters `ALARM`. |
| `--ok-actions` | SNS topic to notify when the alarm returns to `OK`. |

### SQS Alarms

DLQ depth is the highest-priority alarm.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name SQS-DLQ-HasMessages \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=your-ingestion-dlq \
  --statistic Maximum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"
```

Message age detects stuck queues before the DLQ fills.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name SQS-MessageAge-High \
  --metric-name ApproximateAgeOfOldestMessage \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=your-ingestion-queue \
  --statistic Maximum \
  --period 60 \
  --threshold 300 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"
```

### SNS Alarm

SNS delivery failures indicate that events are not reaching subscribers such as SQS.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name SNS-DeliveryFailures \
  --metric-name NumberOfNotificationsFailed \
  --namespace AWS/SNS \
  --dimensions Name=TopicName,Value=your-ingest-topic \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"
```

### S3 Alarm

Create this after enabling S3 request metrics.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name S3-ServerErrors \
  --metric-name 5xxErrors \
  --namespace AWS/S3 \
  --dimensions Name=BucketName,Value=your-bucket-name Name=FilterId,Value=EntireBucket \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --treat-missing-data notBreaching \
  --alarm-actions "$ALERTS_TOPIC_ARN" \
  --ok-actions "$ALERTS_TOPIC_ARN"
```

## Step 7: Build a CloudWatch Dashboard

Dashboards are for diagnosis, not notification. They bring the key metrics into one place when an engineer is responding to an alarm.

Save this as `dashboard-body.json` and update the account, region, function names, queue names, and alarm ARNs.

```json
{
  "widgets": [
    {
      "type": "alarm",
      "x": 0,
      "y": 0,
      "width": 24,
      "height": 6,
      "properties": {
        "title": "Active alarms",
        "alarms": [
          "arn:aws:cloudwatch:us-east-1:123456789012:alarm:IngestLambda-Errors",
          "arn:aws:cloudwatch:us-east-1:123456789012:alarm:SQS-DLQ-HasMessages",
          "arn:aws:cloudwatch:us-east-1:123456789012:alarm:SQS-MessageAge-High",
          "arn:aws:cloudwatch:us-east-1:123456789012:alarm:SNS-DeliveryFailures"
        ]
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Lambda errors",
        "metrics": [
          ["AWS/Lambda", "Errors", "FunctionName", "ingest-trigger-lambda"],
          ["AWS/Lambda", "Errors", "FunctionName", "job-trigger-lambda"],
          ["YourPipeline", "IngestTriggerErrors"],
          ["YourPipeline", "JobTriggerErrors"]
        ],
        "stat": "Sum",
        "period": 60,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "SQS queue health",
        "metrics": [
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "your-ingestion-queue"],
          ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", "your-ingestion-queue"],
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "your-ingestion-dlq"]
        ],
        "stat": "Maximum",
        "period": 60,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "SNS delivery",
        "metrics": [
          ["AWS/SNS", "NumberOfMessagesPublished", "TopicName", "your-ingest-topic"],
          ["AWS/SNS", "NumberOfNotificationsDelivered", "TopicName", "your-ingest-topic"],
          ["AWS/SNS", "NumberOfNotificationsFailed", "TopicName", "your-ingest-topic"]
        ],
        "stat": "Sum",
        "period": 60,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "S3 request errors",
        "metrics": [
          ["AWS/S3", "4xxErrors", "BucketName", "your-bucket-name", "FilterId", "EntireBucket"],
          ["AWS/S3", "5xxErrors", "BucketName", "your-bucket-name", "FilterId", "EntireBucket"]
        ],
        "stat": "Sum",
        "period": 60,
        "region": "us-east-1"
      }
    }
  ]
}
```

Create or update the dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name IngestionPipeline \
  --dashboard-body file://dashboard-body.json
```

## End-to-End Alert Flow

When a file lands in S3 and the trigger Lambda fails, the alert path is:

1. File lands in S3.
2. S3 invokes `ingest-trigger-lambda`.
3. Lambda writes a structured error log to `/aws/lambda/ingest-trigger-lambda`.
4. Lambda re-raises the exception, incrementing the `AWS/Lambda` `Errors` metric.
5. The metric filter sees `status = "error"` and increments `YourPipeline/IngestTriggerErrors`.
6. The Lambda native alarm and log-based alarm transition to `ALARM`.
7. CloudWatch publishes alarm notifications to the dedicated `pipeline-alerts` SNS topic.
8. SNS fans out to email, PagerDuty, Slack, or any other subscribed channel.
9. The on-call engineer opens the CloudWatch dashboard to inspect Lambda errors, SQS depth, SNS delivery, and S3 errors together.
10. The engineer uses CloudWatch Logs Insights to identify the failing file and error message.

## Alarm Priority Reference

Implement alarms in this order:

| Priority | Alarm | Source | Why It Matters |
| --- | --- | --- | --- |
| P1 | SQS DLQ depth > 0 | `AWS/SQS` native metric | A file or job was abandoned and requires intervention. |
| P1 | SQS message age > 5 minutes | `AWS/SQS` native metric | The pipeline is stuck or falling behind. |
| P1 | SNS delivery failures > 0 | `AWS/SNS` native metric | Events may not be reaching SQS; Lambda errors may not fire. |
| P2 | Lambda errors > 0 | `AWS/Lambda` native metric | A Lambda is crashing or timing out. |
| P2 | Lambda log errors > 0 | Custom metric from log filter | Application code logged an explicit failure. |
| P3 | S3 5xx errors > 0 | `AWS/S3` request metric | S3 is returning service-side errors. |
| P3 | S3 4xx errors spike | `AWS/S3` request metric | Permissions or client requests may be broken. |

## Diagnosing Failures with CloudWatch Logs Insights

Run this query against the relevant Lambda log group:

```sql
fields @timestamp, status, error, file, pipeline_stage
| filter status = "error"
| sort @timestamp desc
| limit 20
```

For job-trigger Lambdas that process SQS messages, include message attributes if you log them:

```sql
fields @timestamp, status, error, file, pipeline_stage, message_id, run_id
| filter status = "error"
| sort @timestamp desc
| limit 50
```

Useful follow-up queries:

```sql
fields @timestamp, file, pipeline_stage, status
| filter file like /customer/
| sort @timestamp desc
| limit 50
```

```sql
stats count(*) as failures by pipeline_stage, error
| sort failures desc
| limit 20
```

## Operational Runbook

### If the DLQ Alarm Fires

1. Open the SQS DLQ and inspect the oldest message.
2. Capture the source file, run ID, message ID, receive count, and error context.
3. Check the job-trigger Lambda logs for the same file or message ID.
4. Determine whether the failure is retryable.
5. If retryable, redrive the message to the source queue after the issue is fixed.
6. If not retryable, move the source file to a quarantine path and create a data-quality or source-system ticket.

### If Message Age Is High

1. Check whether the job-trigger Lambda is enabled and has recent invocations.
2. Check Lambda concurrency, throttles, duration, and errors.
3. Check downstream dependencies such as databases, APIs, EMR jobs, or Snowflake loads.
4. Increase concurrency or worker capacity only after confirming the downstream system can handle it.

### If SNS Delivery Fails

1. Verify the SNS subscription status is `Confirmed`.
2. Check the SQS queue policy allows the SNS topic to send messages.
3. Check whether the subscription has filter policies that exclude expected events.
4. Review `NumberOfNotificationsFailed` and `NumberOfNotificationsDelivered` together.

### If S3 PutRequests Drop to Zero

1. Confirm whether upstream systems were expected to deliver files during the window.
2. Check AWS Transfer, MFT, or source-system logs.
3. Confirm bucket policy, IAM permissions, and KMS key access.
4. Check whether files landed under an unexpected prefix.

## Final Checklist

- Lambda log groups exist and have retention policies.
- Lambda logs are structured JSON and include `status`, `file`, and `pipeline_stage`.
- Metric filters exist for explicit application errors.
- Native alarms exist for Lambda errors, SQS queue age, DLQ depth, SNS delivery failures, and S3 errors.
- Alarms publish to a dedicated monitoring SNS topic, not the pipeline SNS topic.
- Email, Slack, or PagerDuty subscriptions are confirmed.
- The dashboard shows Lambda, SQS, SNS, and S3 metrics together.
- Logs Insights queries are documented for on-call use.
- DLQ redrive and quarantine procedures are documented and tested.
