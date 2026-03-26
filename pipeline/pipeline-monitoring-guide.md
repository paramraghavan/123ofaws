**CloudWatch Monitoring for S3 Ingestion Pipeline**


**Your Pipeline at a Glance**

Before setting up monitoring, it helps to understand exactly what each
service does --- because this determines how each one is monitored.

  ------------- ------------------ ---------------------------------------
  **Service**   **Role**           **How it is monitored**

  S3 bucket     File lands here,   Native CloudWatch metrics
                triggers the       (auto-published, no setup)
                pipeline           

  Trigger       Receives S3 event, Log group + metric filters + Lambda
  Lambda        publishes to SNS   native metrics

  SNS topic     Fans the event out Native CloudWatch metrics
                to SQS             (auto-published, no setup)

  SQS queue     Buffers jobs for   Native CloudWatch metrics
                the job-trigger    (auto-published, no setup)
                lambda             

  SQS DLQ       Receives messages  Native CloudWatch metrics --- alarm on
                that failed        any message here
                processing         
                repeatedly         

  Job-trigger   Polls SQS,         Log group + metric filters + Lambda
  Lambda        performs actual    native metrics
                ingestion          
  ------------- ------------------ ---------------------------------------

  --------- -------------------------------------------------------------
  **Key     Only your two Lambdas produce CloudWatch Log Groups. S3, SNS,
  point**   and SQS publish metrics directly to CloudWatch --- no log
            group setup required for them. You alarm on their metrics
            directly.

  --------- -------------------------------------------------------------

**How the Monitoring Layers Connect**

There are three distinct layers. Each feeds the next:

-   Log groups (Lambda only) --- raw log lines written by your Lambda
    code

-   CloudWatch Metrics --- either extracted from logs via metric
    filters, or published natively by AWS services

-   Alarms --- evaluate metrics and trigger an SNS alerts topic when
    thresholds are breached

-   SNS alerts topic (separate from your pipeline SNS) --- fans out to
    email, Slack, PagerDuty

+-----------------------------------------------------------------------+
| Lambda code → Log Group → Metric Filter → Custom CW Metric ─┐         |
|                                                                       |
| ├──→ CW Alarm → SNS alerts topic → Email / Slack / PagerDuty          |
|                                                                       |
| S3 / SNS / SQS → Native CW Metrics (auto) ──────────────────────┘     |
+-----------------------------------------------------------------------+

**Step 1 --- Create Log Groups for Both Lambdas**

Lambda automatically creates a log group the first time it runs.
Creating it explicitly beforehand lets you set a retention policy before
any logs accumulate --- you cannot retroactively delete old logs.

+-----------------------------------------------------------------------+
| \# Create log groups (skip if your Lambdas have already run)          |
|                                                                       |
| aws logs create-log-group \--log-group-name                           |
| /aws/lambda/ingest-trigger-lambda                                     |
|                                                                       |
| aws logs create-log-group \--log-group-name                           |
| /aws/lambda/job-trigger-lambda                                        |
|                                                                       |
| \# Set retention to 30 days --- without this, logs accumulate forever |
|                                                                       |
| aws logs put-retention-policy \\                                      |
|                                                                       |
| \--log-group-name /aws/lambda/ingest-trigger-lambda \\                |
|                                                                       |
| \--retention-in-days 30                                               |
|                                                                       |
| aws logs put-retention-policy \\                                      |
|                                                                       |
| \--log-group-name /aws/lambda/job-trigger-lambda \\                   |
|                                                                       |
| \--retention-in-days 30                                               |
+-----------------------------------------------------------------------+

  ----------- -------------------------------------------------------------
  **Why this  Step 3 (metric filters) and Step 6 (dashboard) both point at
  matters**   these log group names. Without them nothing downstream works.

  ----------- -------------------------------------------------------------

**Step 2 --- Emit Structured Logs from Your Lambdas**

CloudWatch metric filters match on plain text patterns. Your log format
determines what you can alarm on. Emit structured JSON so every log line
is queryable and traceable to a specific file.

+-----------------------------------------------------------------------+
| import json, logging                                                  |
|                                                                       |
| logger = logging.getLogger()                                          |
|                                                                       |
| logger.setLevel(logging.INFO)                                         |
|                                                                       |
| def handler(event, context):                                          |
|                                                                       |
| file_key =                                                            |
| event\[\'Records\'\]\[0\]\[\'s3\'\]\[\'object\'\]\[\'key\'\]          |
|                                                                       |
| try:                                                                  |
|                                                                       |
| \# \... your ingestion logic \...                                     |
|                                                                       |
| \# SUCCESS: Step 3 metric filter can count these too                  |
|                                                                       |
| logger.info(json.dumps({                                              |
|                                                                       |
| \'status\': \'success\',                                              |
|                                                                       |
| \'file\': file_key,                                                   |
|                                                                       |
| \'pipeline_stage\': \'ingest-trigger\'                                |
|                                                                       |
| }))                                                                   |
|                                                                       |
| except Exception as e:                                                |
|                                                                       |
| \# FAILURE: \'ERROR\' in this line is what Step 3 metric filter       |
| matches                                                               |
|                                                                       |
| logger.error(json.dumps({                                             |
|                                                                       |
| \'status\': \'error\',                                                |
|                                                                       |
| \'error\': str(e),                                                    |
|                                                                       |
| \'file\': file_key,                                                   |
|                                                                       |
| \'pipeline_stage\': \'ingest-trigger\'                                |
|                                                                       |
| }))                                                                   |
|                                                                       |
| \# re-raise so Lambda marks invocation as FAILED                      |
|                                                                       |
| \# this feeds the built-in AWS/Lambda Errors metric used in Step 4    |
|                                                                       |
| raise                                                                 |
+-----------------------------------------------------------------------+

**Step 3 --- Create Metric Filters on Log Groups**

Metric filters are the translation layer. They watch the raw log stream
and every time a line matches a pattern, they increment a named
CloudWatch metric. That metric is what your alarms evaluate.

  ------------------ -------------------------------------------------------------
  **defaultValue=0   Without defaultValue=0, CloudWatch sees \'no data\' instead
  is critical**      of \'zero errors\' during quiet periods. This causes alarms
                     to enter an INSUFFICIENT_DATA state and miss recovery
                     notifications.

  ------------------ -------------------------------------------------------------

+-----------------------------------------------------------------------+
| \# Metric filter for the TRIGGER lambda                               |
|                                                                       |
| \# Scans every log line for the string \'ERROR\'                      |
|                                                                       |
| \# Match → adds 1 to IngestTriggerErrors metric                       |
|                                                                       |
| aws logs put-metric-filter \\                                         |
|                                                                       |
| \--log-group-name /aws/lambda/ingest-trigger-lambda \\                |
|                                                                       |
| \--filter-name \'ErrorFilter\' \\                                     |
|                                                                       |
| \--filter-pattern \'ERROR\' \\                                        |
|                                                                       |
| \--metric-transformations \\                                          |
|                                                                       |
| metricName=IngestTr                                                   |
| iggerErrors,metricNamespace=YourPipeline,metricValue=1,defaultValue=0 |
|                                                                       |
| \# Same for the JOB TRIGGER lambda --- separate metric so you know    |
| which stage failed                                                    |
|                                                                       |
| aws logs put-metric-filter \\                                         |
|                                                                       |
| \--log-group-name /aws/lambda/job-trigger-lambda \\                   |
|                                                                       |
| \--filter-name \'ErrorFilter\' \\                                     |
|                                                                       |
| \--filter-pattern \'ERROR\' \\                                        |
|                                                                       |
| \--metric-transformations \\                                          |
|                                                                       |
| metricName=JobTr                                                      |
| iggerErrors,metricNamespace=YourPipeline,metricValue=1,defaultValue=0 |
+-----------------------------------------------------------------------+

**Step 4 --- Identify Metrics for S3, SNS, and SQS**

Unlike Lambdas, these services do not write log groups. AWS publishes
their metrics automatically to CloudWatch. You point alarms directly at
the metric name, namespace, and dimension --- no log group or metric
filter involved.

**How to find metrics for a specific resource**

Use the AWS CLI to list metrics that already have data for your specific
queue, topic, or bucket:

+-----------------------------------------------------------------------+
| \# All metrics for your SQS queue                                     |
|                                                                       |
| aws cloudwatch list-metrics \\                                        |
|                                                                       |
| \--namespace AWS/SQS \\                                               |
|                                                                       |
| \--dimensions Name=QueueName,Value=your-ingestion-queue               |
|                                                                       |
| \# All metrics for your SNS topic                                     |
|                                                                       |
| aws cloudwatch list-metrics \\                                        |
|                                                                       |
| \--namespace AWS/SNS \\                                               |
|                                                                       |
| \--dimensions Name=TopicName,Value=your-ingest-topic                  |
|                                                                       |
| \# All metrics for your S3 bucket                                     |
|                                                                       |
| aws cloudwatch list-metrics \\                                        |
|                                                                       |
| \--namespace AWS/S3 \\                                                |
|                                                                       |
| \--dimensions Name=BucketName,Value=your-bucket-name                  |
|                                                                       |
| \# NOTE: a metric only appears here if it has had at least one data   |
| point.                                                                |
|                                                                       |
| \# If a metric is missing, trigger a real event first or check the    |
| namespace spelling.                                                   |
+-----------------------------------------------------------------------+

**The metrics that matter for this pipeline**

**SQS --- main ingestion queue**

  --------------------------------------- ----------------------------------------------
  **Metric name**                         **What it tells you**

  ApproximateNumberOfMessagesVisible      Messages waiting to be picked up. Rising =
                                          job-trigger lambda has stopped consuming.

  ApproximateAgeOfOldestMessage           Age of the oldest unprocessed message. Best
                                          early warning of a stuck queue --- spikes
                                          before DLQ fills.

  ApproximateNumberOfMessagesNotVisible   Messages in flight (received but not deleted).
                                          High = lambda is slow or failing mid-process.

  NumberOfMessagesDeleted                 Messages successfully processed. A sudden drop
                                          means lambda stopped consuming.
  --------------------------------------- ----------------------------------------------

**SQS --- Dead Letter Queue (DLQ)**

  ---------- -------------------------------------------------------------
  **Most     ApproximateNumberOfMessagesVisible on your DLQ. Any value \>
  critical   0 means a file failed processing enough times to be
  alarm**    permanently abandoned. Alarm on threshold = 1 and page
             immediately.

  ---------- -------------------------------------------------------------

**SNS**

  -------------------------------- ----------------------------------------------
  **Metric name**                  **What it tells you**

  NumberOfMessagesPublished        Events SNS received from S3/Lambda. Should
                                   match your file landing rate.

  NumberOfNotificationsFailed      Delivery failures from SNS to SQS. Even 1 = a
                                   file silently dropped from the pipeline.

  NumberOfNotificationsDelivered   Successful deliveries to SQS. Compare against
                                   Published to spot drop rate.
  -------------------------------- ----------------------------------------------

**S3**

S3 request metrics are opt-in per bucket. Enable them first:

+-----------------------------------------------------------------------+
| aws s3api put-bucket-metrics-configuration \\                         |
|                                                                       |
| \--bucket your-bucket-name \\                                         |
|                                                                       |
| \--id EntireBucket \\                                                 |
|                                                                       |
| \--metrics-configuration \'{\"Id\":\"EntireBucket\"}\'                |
+-----------------------------------------------------------------------+

  ------------------------ ----------------------------------------------
  **Metric name**          **What it tells you**

  PutRequests              Files landing in the bucket. A sudden drop =
                           upstream stopped sending, not a pipeline
                           failure.

  5xxErrors                Bucket server errors (throttling, internal
                           issues). Indicates S3-side problems.

  4xxErrors                Permission or client errors accessing the
                           bucket.
  ------------------------ ----------------------------------------------

**Step 5 --- Create CloudWatch Alarms**

Alarms evaluate metrics on a schedule and transition to ALARM state when
a threshold is breached. They are the bridge between metrics and your
alert notifications. Create one per failure mode.

  ---------- -------------------------------------------------------------
  **Two      Alarms work identically whether the metric came from a log
  sources,   group metric filter (your custom namespace) or from a native
  one alarm  AWS service (AWS/Lambda, AWS/SQS, AWS/SNS). The only
  style**    difference is the namespace and dimensions you specify.

  ---------- -------------------------------------------------------------

**Lambda alarms (native + log-based)**

+-----------------------------------------------------------------------+
| \# Alarm A: built-in Lambda Errors metric                             |
|                                                                       |
| \# Catches unhandled exceptions --- fires because you re-raised in    |
| Step 2                                                                |
|                                                                       |
| aws cloudwatch put-metric-alarm \\                                    |
|                                                                       |
| \--alarm-name \'IngestLambda-Errors\' \\                              |
|                                                                       |
| \--metric-name Errors \\                                              |
|                                                                       |
| \--namespace AWS/Lambda \\                                            |
|                                                                       |
| \--dimensions Name=FunctionName,Value=ingest-trigger-lambda \\        |
|                                                                       |
| \--statistic Sum \--period 60 \--threshold 1 \\                       |
|                                                                       |
| \--comparison-operator GreaterThanOrEqualToThreshold \\               |
|                                                                       |
| \--evaluation-periods 1 \\                                            |
|                                                                       |
| \--alarm-actions arn:aws:sns:\...:pipeline-alerts \\                  |
|                                                                       |
| \--ok-actions arn:aws:sns:\...:pipeline-alerts                        |
|                                                                       |
| \# Alarm B: custom log-based metric from Step 3                       |
|                                                                       |
| \# Catches caught errors you explicitly logged --- complements Alarm  |
| A                                                                     |
|                                                                       |
| aws cloudwatch put-metric-alarm \\                                    |
|                                                                       |
| \--alarm-name \'IngestLambda-LogErrors\' \\                           |
|                                                                       |
| \--metric-name IngestTriggerErrors \\                                 |
|                                                                       |
| \--namespace YourPipeline \\                                          |
|                                                                       |
| \--statistic Sum \--period 60 \--threshold 1 \\                       |
|                                                                       |
| \--comparison-operator GreaterThanOrEqualToThreshold \\               |
|                                                                       |
| \--evaluation-periods 1 \\                                            |
|                                                                       |
| \--alarm-actions arn:aws:sns:\...:pipeline-alerts                     |
|                                                                       |
| \# Repeat both alarms for job-trigger-lambda / JobTriggerErrors       |
+-----------------------------------------------------------------------+

**SQS alarms**

+-----------------------------------------------------------------------+
| \# DLQ depth --- your highest priority alarm                          |
|                                                                       |
| \# Even 1 message means a file was permanently abandoned              |
|                                                                       |
| aws cloudwatch put-metric-alarm \\                                    |
|                                                                       |
| \--alarm-name \'SQS-DLQ-HasMessages\' \\                              |
|                                                                       |
| \--metric-name ApproximateNumberOfMessagesVisible \\                  |
|                                                                       |
| \--namespace AWS/SQS \\                                               |
|                                                                       |
| \--dimensions Name=QueueName,Value=your-ingestion-dlq \\              |
|                                                                       |
| \--statistic Maximum \--period 60 \--threshold 1 \\                   |
|                                                                       |
| \--comparison-operator GreaterThanOrEqualToThreshold \\               |
|                                                                       |
| \--evaluation-periods 1 \\                                            |
|                                                                       |
| \--alarm-actions arn:aws:sns:\...:pipeline-alerts                     |
|                                                                       |
| \# Message age --- catches stuck queues before DLQ fills              |
|                                                                       |
| \# 300 seconds = 5 minutes without processing = something is wrong    |
|                                                                       |
| aws cloudwatch put-metric-alarm \\                                    |
|                                                                       |
| \--alarm-name \'SQS-MessageAge-High\' \\                              |
|                                                                       |
| \--metric-name ApproximateAgeOfOldestMessage \\                       |
|                                                                       |
| \--namespace AWS/SQS \\                                               |
|                                                                       |
| \--dimensions Name=QueueName,Value=your-ingestion-queue \\            |
|                                                                       |
| \--statistic Maximum \--period 60 \--threshold 300 \\                 |
|                                                                       |
| \--comparison-operator GreaterThanOrEqualToThreshold \\               |
|                                                                       |
| \--evaluation-periods 1 \\                                            |
|                                                                       |
| \--alarm-actions arn:aws:sns:\...:pipeline-alerts                     |
+-----------------------------------------------------------------------+

**SNS alarm**

+-----------------------------------------------------------------------+
| \# SNS delivery failures --- silent file drop detector                |
|                                                                       |
| \# If SNS cannot deliver to SQS, the file is lost with no Lambda      |
| error                                                                 |
|                                                                       |
| aws cloudwatch put-metric-alarm \\                                    |
|                                                                       |
| \--alarm-name \'SNS-DeliveryFailures\' \\                             |
|                                                                       |
| \--metric-name NumberOfNotificationsFailed \\                         |
|                                                                       |
| \--namespace AWS/SNS \\                                               |
|                                                                       |
| \--dimensions Name=TopicName,Value=your-ingest-topic \\               |
|                                                                       |
| \--statistic Sum \--period 60 \--threshold 1 \\                       |
|                                                                       |
| \--comparison-operator GreaterThanOrEqualToThreshold \\               |
|                                                                       |
| \--evaluation-periods 1 \\                                            |
|                                                                       |
| \--alarm-actions arn:aws:sns:\...:pipeline-alerts                     |
+-----------------------------------------------------------------------+

**Step 6 --- Create an SNS Alerts Topic and Wire Subscribers**

This SNS topic is separate from your pipeline\'s SNS topic. All alarms
send to it. It fans out to your notification channels. Keeping it
separate is important --- if your pipeline SNS has problems, you still
need to receive the alert about it.

+-----------------------------------------------------------------------+
| \# Create the dedicated alerts topic                                  |
|                                                                       |
| aws sns create-topic \--name pipeline-alerts                          |
|                                                                       |
| \# Returns: TopicArn: arn:aws:sns:us-east-1:123456789:pipeline-alerts |
|                                                                       |
| \# Paste this ARN into every \--alarm-actions in Step 5               |
|                                                                       |
| \# Email subscriber --- AWS sends a confirmation email; you must      |
| click it                                                              |
|                                                                       |
| aws sns subscribe \\                                                  |
|                                                                       |
| \--topic-arn arn:aws:sns:\...:pipeline-alerts \\                      |
|                                                                       |
| \--protocol email \\                                                  |
|                                                                       |
| \--notification-endpoint oncall@yourcompany.com                       |
|                                                                       |
| \# PagerDuty via HTTPS webhook --- for critical DLQ alarms            |
|                                                                       |
| aws sns subscribe \\                                                  |
|                                                                       |
| \--topic-arn arn:aws:sns:\...:pipeline-alerts \\                      |
|                                                                       |
| \--protocol https \\                                                  |
|                                                                       |
| \--notification-endpoint                                              |
| https://events.pagerduty.com/integration/YOUR_KEY/enqueue             |
|                                                                       |
| \# Slack via a small Lambda that reformats SNS JSON and posts to a    |
| channel                                                               |
|                                                                       |
| aws sns subscribe \\                                                  |
|                                                                       |
| \--topic-arn arn:aws:sns:\...:pipeline-alerts \\                      |
|                                                                       |
| \--protocol lambda \\                                                 |
|                                                                       |
| \--notification-endpoint arn:aws:lambda:\...:slack-notifier           |
+-----------------------------------------------------------------------+

**Step 7 --- Build a CloudWatch Dashboard**

The dashboard is not needed for alerting --- alarms handle that. Its
purpose is operational visibility when you are paged and need to
diagnose fast. It pulls metrics from all services into one view
regardless of whether they came from log groups or native AWS metrics.

+-----------------------------------------------------------------------+
| aws cloudwatch put-dashboard \\                                       |
|                                                                       |
| \--dashboard-name IngestionPipeline \\                                |
|                                                                       |
| \--dashboard-body \'{                                                 |
|                                                                       |
| \"widgets\": \[                                                       |
|                                                                       |
| {                                                                     |
|                                                                       |
| \"type\": \"alarm\",                                                  |
|                                                                       |
| \"properties\": {                                                     |
|                                                                       |
| \"title\": \"Active alarms\",                                         |
|                                                                       |
| \"alarms\": \[                                                        |
|                                                                       |
| \"arn:aws:\...:alarm:IngestLambda-Errors\",                           |
|                                                                       |
| \"arn:aws:\...:alarm:SQS-DLQ-HasMessages\",                           |
|                                                                       |
| \"arn:aws:\...:alarm:SQS-MessageAge-High\",                           |
|                                                                       |
| \"arn:aws:\...:alarm:SNS-DeliveryFailures\"                           |
|                                                                       |
| \]                                                                    |
|                                                                       |
| }                                                                     |
|                                                                       |
| },                                                                    |
|                                                                       |
| {                                                                     |
|                                                                       |
| \"type\": \"metric\",                                                 |
|                                                                       |
| \"properties\": {                                                     |
|                                                                       |
| \"title\": \"Lambda errors\",                                         |
|                                                                       |
| \"metrics\": \[                                                       |
|                                                                       |
| \[\"                                                                  |
| AWS/Lambda\",\"Errors\",\"FunctionName\",\"ingest-trigger-lambda\"\], |
|                                                                       |
| \                                                                     |
| [\"AWS/Lambda\",\"Errors\",\"FunctionName\",\"job-trigger-lambda\"\], |
|                                                                       |
| \[\"YourPipeline\",\"IngestTriggerErrors\"\],                         |
|                                                                       |
| \[\"YourPipeline\",\"JobTriggerErrors\"\]                             |
|                                                                       |
| \],                                                                   |
|                                                                       |
| \"stat\": \"Sum\", \"period\": 60                                     |
|                                                                       |
| }                                                                     |
|                                                                       |
| },                                                                    |
|                                                                       |
| {                                                                     |
|                                                                       |
| \"type\": \"metric\",                                                 |
|                                                                       |
| \"properties\": {                                                     |
|                                                                       |
| \"title\": \"SQS queue health\",                                      |
|                                                                       |
| \"metrics\": \[                                                       |
|                                                                       |
| \[\"AWS/SQS\",\                                                       |
| "ApproximateNumberOfMessagesVisible\",\"QueueName\",\"your-queue\"\], |
|                                                                       |
| \[\"AWS/SQ                                                            |
| S\",\"ApproximateAgeOfOldestMessage\",\"QueueName\",\"your-queue\"\], |
|                                                                       |
| \[\"AWS/SQS\                                                          |
| ",\"ApproximateNumberOfMessagesVisible\",\"QueueName\",\"your-dlq\"\] |
|                                                                       |
| \],                                                                   |
|                                                                       |
| \"stat\": \"Maximum\", \"period\": 60                                 |
|                                                                       |
| }                                                                     |
|                                                                       |
| }                                                                     |
|                                                                       |
| \]                                                                    |
|                                                                       |
| }\'                                                                   |
+-----------------------------------------------------------------------+

  ------------- -------------------------------------------------------------
  **Dashboard   The dashboard does not combine log groups. It combines
  vs log        CloudWatch Metrics --- which come from two sources: your
  groups**      Lambda log groups (via metric filters) and native metrics
                from SNS/SQS/S3. All of these are just metrics by the time
                the dashboard sees them.

  ------------- -------------------------------------------------------------

**End-to-End Alert Flow**

When a file lands in S3 and the pipeline fails, this is the exact
sequence from failure to notification:

  -------- ------------------------------------------------------------------
  **\#**   **What happens**

  1        File lands in S3

  2        S3 triggers ingest-trigger-lambda

  3        Lambda fails → writes {\"status\":\"error\",\...} to
           /aws/lambda/ingest-trigger-lambda log group

  4        Lambda re-raises → AWS/Lambda Errors metric increments by 1

  5        Metric filter (Step 3) sees \'ERROR\' in log → increments
           IngestTriggerErrors custom metric

  6        CW Alarm A (AWS/Lambda Errors ≥ 1) transitions to ALARM state

  7        CW Alarm B (IngestTriggerErrors ≥ 1) transitions to ALARM state

  8        Both alarms publish to arn:aws:sns:\...:pipeline-alerts (Step 6
           topic)

  9        SNS fans out: email to oncall@, PagerDuty incident created, Slack
           message posted

  10       Engineer opens the CloudWatch Dashboard --- sees error spike
           alongside SQS depth and invocation volume

  11       Engineer queries CloudWatch Logs Insights on the Lambda log group
           to find the exact file key that failed and the error message
  -------- ------------------------------------------------------------------

**Alarm Priority Reference**

Ranked by urgency --- implement in this order:

  ------- ------------------ --------------- ---------------------------------
  **P**   **Alarm**          **Source**      **Why it matters**

  1       SQS DLQ depth \> 0 AWS/SQS native  File permanently abandoned. Needs
                                             immediate human intervention.

  2       SQS message age \> AWS/SQS native  Pipeline is stuck. Catches it
          5 min                              before DLQ fills.

  3       SNS delivery       AWS/SNS native  Files silently dropped --- no
          failures                           Lambda error will fire.

  4       Lambda Errors      AWS/Lambda      Unhandled crashes in either
          (native)           native          Lambda.

  5       Lambda log errors  Log group +     Caught errors explicitly logged
          (custom)           metric filter   by your code.

  6       S3 5xxErrors       AWS/S3 native   Bucket access issues preventing
                                             files from landing.
  ------- ------------------ --------------- ---------------------------------

**Diagnosing Failures with CloudWatch Logs Insights**

When an alarm fires, use this query in the CloudWatch Logs Insights
console against your Lambda log groups to find the exact files and
errors:

+-----------------------------------------------------------------------+
| fields \@timestamp, status, error, file, pipeline_stage               |
|                                                                       |
| \| filter status = \'error\'                                          |
|                                                                       |
| \| sort \@timestamp desc                                              |
|                                                                       |
| \| limit 20                                                           |
+-----------------------------------------------------------------------+

Run this against /aws/lambda/ingest-trigger-lambda and
/aws/lambda/job-trigger-lambda separately to identify which stage of the
pipeline is failing and which specific files are affected.
