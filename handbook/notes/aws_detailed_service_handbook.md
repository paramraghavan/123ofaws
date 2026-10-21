# AWS Detailed Service Handbook

A structured AWS service handbook for interviews and daily reference. This is more detailed than the quick-prep guide, but still organized for lookup.

## 1. AWS Foundations

### Global Infrastructure

| Concept | Detail |
| --- | --- |
| Region | Geographic area containing multiple Availability Zones. Most services are regional. |
| Availability Zone | Isolated data center group inside a Region. Use multiple AZs for high availability. |
| Edge location | Used by services such as CloudFront and Route 53 for low-latency global delivery. |
| Global service | Service not tied to one Region, such as IAM, Route 53, CloudFront, and Organizations. |

Design rule:

> Deploy critical workloads across multiple AZs. Use multiple Regions only when business requirements justify the complexity.

### Shared Responsibility

AWS secures physical infrastructure and managed service foundations. Customers secure identities, data, network rules, application code, and configuration.

Common interview point:

> In S3, AWS protects the durability of the service. The customer controls bucket policies, encryption settings, object access, lifecycle rules, and data classification.

## 2. Identity and Access Management

### IAM Building Blocks

| Resource | Purpose |
| --- | --- |
| IAM user | Long-term principal. Avoid for application workloads. |
| IAM group | Permission grouping for users. |
| IAM role | Temporary identity assumed by AWS services, users, or other accounts. |
| Policy | JSON permission document. |
| Trust policy | Defines who can assume a role. |
| Permission policy | Defines what actions are allowed or denied. |
| Resource policy | Attached to resources such as S3 buckets, KMS keys, SQS queues, SNS topics. |
| STS | Issues temporary credentials. |
| IAM Identity Center | Workforce SSO across accounts. |

### Policy Evaluation Basics

Request is allowed only if:

1. Authentication succeeds.
2. An identity or resource policy allows the action.
3. No explicit deny applies.
4. SCPs, permission boundaries, session policies, and KMS key policies do not block it.

Troubleshooting `AccessDenied`:

- Check caller identity with `sts get-caller-identity`.
- Check IAM identity policy.
- Check resource policy.
- Check SCP.
- Check permission boundary.
- Check KMS key policy if encrypted.
- Check CloudTrail for denied API event.

### IAM Best Practices

- Prefer roles and temporary credentials.
- Use least privilege.
- Avoid wildcard admin policies for workloads.
- Separate human access and workload access.
- Rotate or remove old access keys.
- Use CloudTrail for audit.

## 3. Networking

### VPC Components

| Component | Purpose |
| --- | --- |
| VPC | Isolated virtual network. |
| Subnet | IP range in one AZ. |
| Route table | Determines traffic path. |
| Internet Gateway | Allows public subnet internet access. |
| NAT Gateway | Allows private subnet outbound internet access. |
| Security group | Stateful firewall attached to ENIs/resources. |
| NACL | Stateless subnet-level firewall. |
| VPC endpoint | Private connection to AWS services. |
| Transit Gateway | Hub for connecting many VPCs and networks. |
| VPC Peering | Direct private routing between two VPCs. |

### Public vs Private Subnets

| Subnet Type | Characteristics |
| --- | --- |
| Public subnet | Route to internet gateway. Resources may have public IPs. |
| Private subnet | No direct route to internet gateway. Outbound internet usually through NAT Gateway. |
| Isolated subnet | No internet route. Used for databases or internal-only services. |

### Security Group vs NACL

| Security Group | NACL |
| --- | --- |
| Stateful | Stateless |
| Attached to resource/ENI | Attached to subnet |
| Allow rules only | Allow and deny rules |
| Return traffic automatically allowed | Return traffic must be explicitly allowed |

## 4. Amazon S3

### What It Is

S3 is object storage for files, logs, backups, static assets, analytics data, and data lakes.

### Key Concepts

| Concept | Detail |
| --- | --- |
| Bucket | Top-level object container. Bucket names are globally unique. |
| Object | Stored data plus metadata. |
| Key | Object name/path. |
| Versioning | Preserves multiple object versions. |
| Lifecycle | Transitions or expires objects over time. |
| Storage class | Cost/performance option such as Standard, IA, Glacier. |
| Presigned URL | Temporary access URL. |
| Multipart upload | Upload large objects in parts. |

### Security

- Block Public Access by default.
- Use IAM and bucket policies.
- Encrypt with SSE-S3 or SSE-KMS.
- Use KMS key policy correctly for SSE-KMS.
- Use CloudTrail data events when object-level audit is required.
- Use S3 server access logs or CloudTrail depending on audit need.

### Monitoring

| Need | Tool |
| --- | --- |
| Bucket size/object count | S3 storage metrics, automatic |
| Request count/errors/latency | S3 request metrics, enable per bucket/prefix |
| Who accessed or deleted objects | CloudTrail data events |

## 5. Compute Services

### Lambda

Use Lambda for event-driven code, lightweight APIs, automation, and file/event processing.

Important concepts:

- Execution role controls AWS permissions.
- Timeout controls max runtime.
- Memory setting affects CPU.
- Concurrency controls parallel execution.
- Cold starts can affect latency.
- CloudWatch Logs receives function logs.
- CloudWatch Metrics includes invocations, errors, duration, throttles.

Best practices:

- Initialize AWS clients outside handler.
- Use idempotency for retries.
- Use DLQ/destinations for async failures.
- Keep deployment packages small.
- Store secrets in Secrets Manager or SSM, not environment variables.

### EC2

Use EC2 when you need full OS control, custom software, persistent processes, or special instance types.

Know:

- AMI, instance type, EBS volume, security group, key pair, user data.
- Auto Scaling Groups maintain desired capacity.
- Load balancers distribute traffic.
- Systems Manager can replace SSH for operations.

### Containers

| Service | Use |
| --- | --- |
| ECS on Fargate | Run containers without managing servers. |
| ECS on EC2 | Containers with more host control. |
| EKS | Managed Kubernetes. |
| ECR | Container image registry. |

### AWS Batch

Use Batch for queued compute jobs, scientific workloads, batch ETL, and large parallel jobs.

## 6. Messaging and Eventing

### SQS

SQS is a durable queue for decoupling producers and consumers.

| Feature | Detail |
| --- | --- |
| Standard queue | High throughput, at-least-once delivery, best-effort order. |
| FIFO queue | Ordering and deduplication. |
| Visibility timeout | Message hidden while consumer processes it. |
| DLQ | Stores repeatedly failed messages. |
| Long polling | Reduces empty receives. |

Design notes:

- Consumers must be idempotent.
- Set visibility timeout longer than processing time.
- Alarm on age of oldest message and DLQ depth.

### SNS

SNS is pub/sub fan-out.

Common subscriptions:

- SQS
- Lambda
- HTTP/S
- Email
- SMS

Use SNS when one event should notify multiple subscribers.

### EventBridge

EventBridge routes events using rules and event patterns.

Use EventBridge for:

- SaaS integration.
- Scheduled rules.
- Cross-account event routing.
- Domain events.
- Filtering and routing beyond simple fan-out.

### Step Functions

Step Functions orchestrates workflows with state, retries, branching, parallel steps, and error handling.

Use it when workflows are more complex than a single Lambda or queue consumer.

## 7. Databases

### DynamoDB

Managed NoSQL database for key-value and document workloads.

Key concepts:

| Concept | Detail |
| --- | --- |
| Partition key | Main key and distribution mechanism. |
| Sort key | Enables ordered/range queries inside a partition. |
| GSI | Alternate query access pattern. |
| LSI | Alternate sort key with same partition key. |
| TTL | Automatic item expiration. |
| Streams | Change stream for table events. |
| Conditional write | Prevents conflicting or duplicate writes. |

Design around access patterns. Avoid hot partitions.

### RDS and Aurora

Managed relational databases.

Use when you need:

- SQL.
- Joins.
- Transactions.
- Relational constraints.
- Existing database compatibility.

Features:

- Multi-AZ for failover.
- Read replicas for scaling reads.
- Backups and point-in-time recovery.
- Security groups for network access.
- Encryption with KMS.

### Redshift

Analytical data warehouse for large-scale SQL analytics.

Use for BI, reporting, and warehouse workloads. Not a replacement for OLTP databases.

## 8. Analytics and Data Engineering

### Glue

Glue provides:

- Data Catalog.
- Crawlers.
- Serverless Spark ETL.
- Schema metadata for Athena/EMR/Redshift Spectrum.

### Athena

Athena runs SQL directly over data in S3 using Glue Catalog metadata.

Best for:

- Ad hoc queries.
- Log analysis.
- Data lake exploration.

Cost tip:

> Athena charges by data scanned. Use columnar formats such as Parquet and partition data.

### EMR

EMR runs Spark, Hadoop, Hive, and related big data frameworks.

Use for:

- Large ETL.
- Spark jobs.
- Custom big data frameworks.
- Long-running clusters or job clusters.

### Lake Formation

Lake Formation manages data lake permissions and governance on top of S3 and Glue.

## 9. Monitoring, Logging, and Audit

### CloudWatch

CloudWatch is for health and operations.

Includes:

- Metrics.
- Logs.
- Alarms.
- Dashboards.
- Logs Insights.

Metrics can be:

| Type | Example |
| --- | --- |
| AWS-native | `AWS/Lambda Errors`, `AWS/SQS ApproximateAgeOfOldestMessage` |
| Custom | `YourPipeline/IngestTriggerErrors`, `Custom/App RecordsProcessed` |

Custom metric paths:

```text
Application -> PutMetricData -> CloudWatch metric -> Alarm
Log line -> Metric filter -> CloudWatch metric -> Alarm
Embedded Metric Format -> CloudWatch metric -> Alarm
```

### CloudTrail

CloudTrail is for audit and accountability.

It answers:

- Who called this API?
- What did they change?
- When did it happen?
- From what identity/source IP?

Event types:

| Type | Example | Enablement |
| --- | --- | --- |
| Management event | `CreateBucket`, `UpdateFunctionConfiguration` | Event History exists; create trails for durable retention |
| Data event | `GetObject`, `PutObject`, Lambda `Invoke` | Enable selectively per resource/resource type |
| Insights event | Unusual API activity | Optional |

### CloudWatch vs CloudTrail

| CloudWatch | CloudTrail |
| --- | --- |
| Is the system healthy? | Who did what? |
| Metrics/logs/alarms | API audit events |
| Operational monitoring | Security and compliance |
| Example: Lambda errors increased | Example: IAM role changed Lambda config |

## 10. Security Services

### KMS

KMS manages encryption keys.

Use for:

- S3 SSE-KMS.
- EBS encryption.
- RDS encryption.
- Secrets Manager encryption.
- Application encryption workflows.

Important:

- IAM policy alone is not always enough.
- KMS key policy must allow use.
- Cross-account KMS requires key policy and IAM permissions.

### Secrets Manager vs SSM Parameter Store

| Service | Best Use |
| --- | --- |
| Secrets Manager | Database credentials, rotation, high-value secrets |
| SSM Parameter Store | Config values, simple secure strings, lower-cost parameters |

### GuardDuty, Security Hub, Config

| Service | Purpose |
| --- | --- |
| GuardDuty | Threat detection using logs and signals |
| Security Hub | Central security findings |
| AWS Config | Resource configuration history and compliance |

## 11. Infrastructure as Code

| Tool | Notes |
| --- | --- |
| CloudFormation | Native AWS IaC |
| CDK | Code that synthesizes CloudFormation |
| Terraform | Multi-cloud IaC, common in industry |
| SAM | Serverless-focused IaC |

Best practices:

- Version infrastructure code.
- Use separate environments.
- Review changes before deploy.
- Tag resources.
- Avoid manual console drift.

## 12. Boto3 Handbook

### Client Creation

```python
import boto3

s3 = boto3.client("s3", region_name="us-east-1")
```

### Sessions

```python
import boto3

session = boto3.Session(profile_name="dev", region_name="us-east-1")
s3 = session.client("s3")
```

### Pagination

```python
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket="my-bucket"):
    for item in page.get("Contents", []):
        print(item["Key"])
```

### Error Handling

```python
from botocore.exceptions import ClientError

try:
    s3.head_object(Bucket="my-bucket", Key="file.csv")
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    if code in ("404", "NoSuchKey"):
        print("not found")
    else:
        raise
```

### Retries and Timeouts

```python
from botocore.config import Config
import boto3

config = Config(
    retries={"max_attempts": 5, "mode": "standard"},
    connect_timeout=3,
    read_timeout=30,
)

s3 = boto3.client("s3", config=config)
```

### Waiters

```python
ec2 = boto3.client("ec2")
waiter = ec2.get_waiter("instance_running")
waiter.wait(InstanceIds=["i-1234567890abcdef0"])
```

## 13. Common Production Patterns

### S3 File Pipeline

```text
Producer -> S3 -> Lambda -> SNS/SQS -> Worker -> S3/DynamoDB/Snowflake/Redshift
```

Production checklist:

- Idempotency key based on bucket/key/version/checksum.
- SQS DLQ.
- Alarm on DLQ depth and message age.
- Structured logs.
- CloudTrail data events for sensitive buckets.
- Quarantine path for bad files.

### Serverless API

```text
API Gateway -> Lambda -> DynamoDB/RDS
```

Checklist:

- Authentication and authorization.
- Input validation.
- Timeout and retry strategy.
- CloudWatch alarms.
- WAF for public APIs when needed.
- Least privilege Lambda role.

### Data Lake

```text
Raw S3 -> Glue Catalog -> ETL -> Curated S3 -> Athena/Redshift/QuickSight
```

Checklist:

- Partition strategy.
- File format: Parquet/ORC for analytics.
- Data quality checks.
- Catalog schema management.
- Lake Formation/IAM access controls.
- Lifecycle policies.

## 14. Troubleshooting Quick Reference

| Symptom | Likely Area | First Checks |
| --- | --- | --- |
| AccessDenied | IAM/resource/KMS/SCP | Caller identity, policies, CloudTrail |
| Lambda timeout | Code/network/downstream | Duration, logs, VPC config, dependencies |
| SQS backlog | Consumer slow/failing | Queue age, Lambda errors, concurrency |
| DLQ messages | Repeated processing failure | Message body, consumer logs, retry count |
| DynamoDB throttling | Hot key or capacity | Consumed capacity, partition key design |
| S3 upload denied | Bucket/IAM/KMS | Bucket policy, IAM, KMS key policy |
| API latency high | App/downstream/network | CloudWatch metrics, X-Ray traces, logs |
| Unexpected deletion | Audit event | CloudTrail lookup |

## 15. Interview Cheat Sheet

Strong answers mention:

- Security: IAM least privilege, encryption, secrets, audit.
- Reliability: multi-AZ, retries, DLQ, idempotency, backups.
- Observability: metrics, logs, alarms, traces, CloudTrail.
- Cost: right-sizing, lifecycle, autoscaling, data transfer, NAT cost.
- Scalability: decoupling, queues, partitioning, caching, async processing.
- Operations: runbooks, dashboards, deployment rollback, incident response.

Use this sentence often:

> I would design it with least privilege, retries with idempotency, DLQs for failed async work, CloudWatch alarms for health, CloudTrail for audit, and IaC for repeatable deployment.
