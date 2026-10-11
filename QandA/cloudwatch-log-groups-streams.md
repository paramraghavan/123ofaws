# CloudWatch Metrics, CloudWatch Logs, EventBridge, and CloudTrail

## Big picture

| Thing | What it stores | Example |
| --- | --- | --- |
| **CloudWatch Metrics** | Numbers over time | CPU = 70%, Lambda errors = 5 |
| **CloudWatch Logs** | Text log lines | `[ERROR] Database connection timeout` |
| **CloudWatch Alarm** | Rule on a metric | Alert if errors > 5 in 5 minutes |
| **EventBridge** | Events and schedules | Run Lambda every 5 minutes |
| **CloudTrail** | AWS audit activity | User changed a security group |

Simple rule:

```text
Metrics are numbers.
Logs are text.
Alarms watch metrics, not raw log text.
```

## How metrics and logs are created

| Data | How it is created |
| --- | --- |
| AWS service metrics | Many AWS services automatically publish metrics to CloudWatch Metrics |
| Custom metrics | Your app, CloudWatch agent, or AWS CLI/API publishes numeric values |
| Application logs | Your app/runtime/agent/log driver sends text logs to CloudWatch Logs |
| Metrics from logs | A CloudWatch Logs metric filter converts matching log lines into metrics |

Example flow:

```text
Application writes log line
-> CloudWatch Logs stores the text
-> Metric filter counts matching log lines
-> CloudWatch Metrics stores the count
-> CloudWatch Alarm alerts on the count
```

## CloudWatch Logs concepts

| Concept | Meaning |
| --- | --- |
| **Log group** | Container for related logs, such as `/myapp/application` |
| **Log stream** | Logs from one source, such as one Lambda runtime, EC2 instance, container, or process |
| **Log event** | One timestamped log line |
| **Metric filter** | Pattern that turns matching log events into a metric |
| **Subscription filter** | Sends logs to Lambda, Kinesis Data Streams, Firehose, or another destination |

## What is automatic by default?

Many AWS services send **CloudWatch Metrics** by default. **CloudWatch Logs** usually needs logging to be enabled or configured.

| Service | CloudWatch Metrics | CloudWatch Logs |
| --- | --- | --- |
| EC2 | CPU, network, disk read/write, status checks by default | App logs require CloudWatch agent |
| Lambda | Invocations, duration, errors, throttles by default | `print()`, `console.log()`, stdout/stderr, and logger output go to `/aws/lambda/<function-name>` |
| RDS | CPU, connections, storage, IOPS, latency by default | Engine logs/audit logs must be enabled |
| ECS | CPU/memory metrics for services/tasks | Container logs require `awslogs` log driver or FireLens |
| EKS | Limited service metrics | Pod/container logs require Fluent Bit, CloudWatch agent, or another collector |
| S3 | Storage metrics by default | Request metrics, access logs, and object-level data events need configuration |
| API Gateway | Basic API metrics | Access logs and execution logs must be enabled |
| EMR on EC2 | Some service/cluster metrics | Spark/YARN logs are usually on nodes or S3 unless CloudWatch logging is configured |
| SSM Run Command | Not mainly a CloudWatch Metrics source | Command stdout/stderr goes to CloudWatch Logs only if CloudWatch output is enabled |
| CloudTrail | Not an app metric service | Sends to CloudWatch Logs only if a trail is configured for CloudWatch Logs |

Key point:

```text
Do not assume text logs exist in CloudWatch Logs just because metrics exist in CloudWatch Metrics.
```

## CloudWatch agent

The CloudWatch agent is installed on EC2, on-prem servers, or some container environments when AWS does not collect the data automatically.

Use it to send:

- Memory and disk space metrics.
- Process-level metrics.
- Custom StatsD or collectd metrics.
- Log files such as `/var/log/myapp/app.log`.

Example:

```text
EC2 app writes /var/log/myapp/app.log
-> CloudWatch agent reads the file
-> CloudWatch Logs stores the log events
```

## EventBridge and CloudWatch Events

CloudWatch Events is the old name. EventBridge is the current and expanded service.

```text
CloudWatch Events ~= Amazon EventBridge
```

Use EventBridge for schedules, AWS service events, CloudWatch alarm state changes, and custom application events.

Old names still appear in CLI/API/IAM/Terraform, such as:

- `aws events put-rule`
- `aws_cloudwatch_event_rule`

## CloudTrail logs

CloudTrail is AWS audit logging. It answers:

```text
Who did what, on which AWS resource, from where, and when?
```

CloudTrail is not application logging.

| Example | Log type |
| --- | --- |
| Lambda prints `Database timeout` | Application log in CloudWatch Logs |
| User changes Lambda configuration | CloudTrail audit event |

CloudTrail defaults:

| CloudTrail capability | Enabled automatically? |
| --- | --- |
| 90-day Event history | Yes |
| Management events in Event history | Yes |
| Trail delivery to S3 | No |
| Trail delivery to CloudWatch Logs | No |
| Data events, such as S3 object access | No |
| Insights events | No |

For production, create an organization trail to a central S3 bucket. Optionally send CloudTrail events to CloudWatch Logs or a SIEM.

## SSM Run Command logs

AWS Systems Manager Run Command runs commands on EC2 through the SSM Agent.

Do not confuse:

- **SSM Agent**: runs commands on EC2.
- **SSM command output**: stdout/stderr from one command run.
- **CloudWatch agent**: continuously ships app log files from EC2.

To send SSM command output to CloudWatch Logs:

```bash
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=instanceIds,Values=i-1234567890abcdef0" \
  --parameters 'commands=["echo hello from ssm"]' \
  --cloud-watch-output-config "CloudWatchOutputEnabled=true,CloudWatchLogGroupName=/aws/ssm/run-command"
```

## Metric filter example

Application log:

```text
[ERROR] 2024-01-23 10:15:32 - Database connection timeout
[INFO] 2024-01-23 10:15:35 - Connection restored
[ERROR] 2024-01-23 10:20:45 - Database connection timeout
```

This filter counts all uppercase errors:

```text
"[ERROR]"
```

Name that metric `ApplicationErrors`, not `DatabaseErrors`.

This filter is database-specific:

```text
"[ERROR]" "Database connection timeout"
```

Create the metric filter:

```bash
aws logs put-metric-filter \
  --log-group-name /myapp/application \
  --filter-name DatabaseErrors \
  --filter-pattern '"[ERROR]" "Database connection timeout"' \
  --metric-transformations \
      metricName=DatabaseErrors,metricNamespace=MyApplication,metricValue=1
```

Create an alarm on the metric:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name DatabaseErrorsAlarm \
  --metric-name DatabaseErrors \
  --namespace MyApplication \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:region:account-id:topic-name
```

## Key takeaway

CloudWatch Metrics stores numbers. CloudWatch Logs stores text. Metric filters can turn selected log text into metrics. Alarms watch metrics. EventBridge handles events and schedules. CloudTrail records AWS audit activity.
