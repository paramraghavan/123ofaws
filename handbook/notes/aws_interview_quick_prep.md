# AWS Interview Quick Prep

Fast review notes for AWS, Python, and Boto3 interviews. This is written for candidates with about one year of experience who need clear concepts, common questions, and practical talking points.

## 1. Core AWS Concepts

| Concept | Simple Meaning | Interview Tip |
| --- | --- | --- |
| Region | Geographic AWS location, such as `us-east-1` | Most resources are regional. |
| Availability Zone | Isolated data center group inside a Region | Use multiple AZs for high availability. |
| VPC | Private network boundary in AWS | Subnets, route tables, security groups live here. |
| Subnet | IP range inside one AZ | Public subnet has route to internet gateway; private subnet usually does not. |
| IAM | Identity and access control | Always mention least privilege. |
| ARN | Unique AWS resource identifier | Used in IAM policies and resource references. |
| Tag | Key-value metadata | Used for cost, ownership, automation, and access control. |
| Control plane | APIs that create/configure resources | Example: `CreateBucket`, `UpdateFunctionConfiguration`. |
| Data plane | APIs that read/write application data | Example: `GetObject`, `PutItem`, `Invoke`. |

## 2. Shared Responsibility Model

AWS secures the cloud. You secure what you put in the cloud.

| AWS Handles | Customer Handles |
| --- | --- |
| Data centers, hardware, managed service infrastructure | IAM, data, encryption choices, network rules, app code |
| Physical security | Least privilege, patching EC2, secure configs |
| Managed service availability | Backups, monitoring, recovery design |

Interview answer:

> AWS manages the infrastructure. The customer manages identity, data protection, network access, application code, and configuration.

## 3. IAM Must-Know

| Term | Meaning |
| --- | --- |
| IAM user | Long-term identity, usually avoid for apps |
| IAM role | Temporary credentials assumed by AWS services, users, or accounts |
| Policy | JSON permissions document |
| Trust policy | Who can assume a role |
| Permission policy | What actions are allowed or denied |
| Resource policy | Policy attached to a resource, such as S3 bucket policy |
| SCP | Organization-level guardrail |
| Permission boundary | Maximum permissions an identity can receive |

Best practices:

- Prefer IAM roles over access keys.
- Use least privilege.
- Use temporary credentials with STS.
- Never store secrets in code.
- Use CloudTrail to audit API activity.

Common question:

**Q: Role vs user?**  
An IAM user is a long-term identity. An IAM role is assumed temporarily and is better for AWS services, cross-account access, and automation.

## 4. S3

S3 is durable object storage for files, backups, logs, static assets, and data lakes.

Important concepts:

| Concept | Meaning |
| --- | --- |
| Bucket | Top-level container |
| Object | File plus metadata |
| Key | Object path/name |
| Versioning | Keeps multiple versions of objects |
| Lifecycle policy | Moves or deletes objects over time |
| SSE-S3 | S3-managed encryption |
| SSE-KMS | KMS-managed encryption with key control |
| Presigned URL | Temporary URL for upload/download |

Common question:

**Q: S3 vs EBS vs EFS?**

| Service | Use |
| --- | --- |
| S3 | Object storage, data lake, backups |
| EBS | Block disk attached to one EC2 instance |
| EFS | Shared POSIX file system across many compute resources |

## 5. Lambda

Lambda runs code without managing servers. It is good for event-driven tasks, APIs, automation, and file processing.

Know these:

- Max runtime is limited, so not ideal for very long jobs.
- Cold starts can affect latency.
- Memory setting also affects CPU.
- Use environment variables for config, not secrets.
- Use IAM execution role for permissions.
- Use DLQs or destinations for async failure handling.
- Log to CloudWatch Logs.

Common question:

**Q: What happens when Lambda fails with SQS?**  
The message becomes visible again after the visibility timeout. After repeated failures, it can move to a DLQ if configured.

## 6. SQS

SQS is a managed queue for decoupling systems.

| Feature | Meaning |
| --- | --- |
| Standard queue | High throughput, at-least-once delivery, best-effort ordering |
| FIFO queue | Ordered, exactly-once processing support with deduplication |
| Visibility timeout | Time a message is hidden after a consumer receives it |
| DLQ | Stores messages that failed too many times |
| Long polling | Reduces empty receives and cost |

Interview answer:

> SQS decouples producers and consumers. It improves reliability because producers can continue sending even if consumers are slow. Consumers must be idempotent because messages can be delivered more than once.

## 7. SNS and EventBridge

| Service | Use |
| --- | --- |
| SNS | Pub/sub fan-out to SQS, Lambda, HTTP, email, SMS |
| EventBridge | Event routing, SaaS integration, rules, event buses |

Common pattern:

```text
S3 upload -> Lambda -> SNS -> SQS queues -> worker Lambdas
```

Use SNS for simple fan-out. Use EventBridge for event routing, filtering, and integration patterns.

## 8. DynamoDB

DynamoDB is a managed NoSQL key-value/document database.

Know these:

- Partition key chooses data distribution.
- Sort key enables range queries within a partition.
- Design tables around access patterns.
- Avoid hot partitions.
- Use GSIs for alternate query patterns.
- Conditional writes help with idempotency.
- TTL can expire old items.

Common question:

**Q: DynamoDB vs RDS?**  
DynamoDB is NoSQL and scales horizontally for key-based access. RDS is relational SQL and better for joins, transactions, and relational data models.

## 9. RDS and Aurora

RDS is managed relational database service. Aurora is AWS-optimized MySQL/PostgreSQL-compatible database.

Important terms:

- Multi-AZ: high availability failover.
- Read replica: read scaling.
- Backup: point-in-time recovery.
- Subnet group: controls where DB instances run.
- Security group: controls network access.

Interview answer:

> Use RDS/Aurora when you need SQL, joins, transactions, and relational constraints. Use DynamoDB when you need massive scale with predictable key-based access.

## 10. EC2, ECS, EKS, and Batch

| Service | Use |
| --- | --- |
| EC2 | Full VM control |
| Auto Scaling Group | Maintain desired number of EC2 instances |
| ECS/Fargate | Run containers without managing servers |
| EKS | Managed Kubernetes |
| AWS Batch | Queued batch jobs |

Simple answer:

> Use Lambda for event-driven code, ECS/Fargate for containers, EC2 for full OS control, and Batch for scheduled or queued compute-heavy jobs.

## 11. VPC Networking

Must-know:

| Component | Meaning |
| --- | --- |
| VPC | Private network |
| Subnet | IP range in one AZ |
| Route table | Controls where traffic goes |
| Internet Gateway | Internet access for public subnet |
| NAT Gateway | Private subnet outbound internet |
| Security group | Stateful firewall on resource |
| NACL | Stateless firewall on subnet |
| VPC endpoint | Private access to AWS services |

Common question:

**Q: Security group vs NACL?**

| Security Group | NACL |
| --- | --- |
| Stateful | Stateless |
| Attached to ENI/resource | Attached to subnet |
| Allow rules only | Allow and deny rules |
| Return traffic automatically allowed | Return traffic must be allowed |

## 12. CloudWatch vs CloudTrail

| Topic | CloudWatch | CloudTrail |
| --- | --- | --- |
| Purpose | Health and operations | Audit and accountability |
| Data | Metrics, logs, alarms, dashboards | API event history |
| Question | Is the system failing? | Who did what and when? |
| Example | `Lambda Errors = 5` | `UpdateFunctionConfiguration` by an IAM role |

CloudWatch metrics can be:

- AWS-native metrics, such as `AWS/Lambda Errors`.
- Custom metrics, such as `YourPipeline/IngestTriggerErrors`.

CloudTrail can record:

- Management events, such as creating or changing resources.
- Data events, such as S3 object reads/writes, if enabled.

Simple example:

```text
CloudWatch says Lambda errors increased.
CloudTrail shows someone changed the Lambda environment variables earlier.
```

## 13. Boto3 Basics

Boto3 is the AWS SDK for Python.

```python
import boto3

s3 = boto3.client("s3")
response = s3.list_buckets()
for bucket in response["Buckets"]:
    print(bucket["Name"])
```

Client vs resource:

| Type | Meaning |
| --- | --- |
| Client | Low-level API mapping, available for all services |
| Resource | Higher-level object abstraction, not available for all services |

Use clients in interviews and production automation unless the resource API is clearly useful.

## 14. Boto3 Production Tips

- Create clients outside Lambda handler for connection reuse.
- Use paginators for list APIs.
- Handle `ClientError`.
- Configure retries and timeouts with botocore `Config`.
- Use waiters for async state changes.
- Use idempotency tokens where supported.
- Avoid hardcoded credentials.
- Validate Region and account before destructive actions.

Example error handling:

```python
from botocore.exceptions import ClientError

try:
    s3.head_object(Bucket="my-bucket", Key="file.csv")
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    if code == "404":
        print("not found")
    else:
        raise
```

## 15. Most Common Architecture Patterns

### File Ingestion Pipeline

```text
S3 -> Lambda -> SNS/SQS -> worker Lambda/Glue/EMR -> S3/Snowflake/Redshift
```

Mention:

- S3 event triggers.
- SQS buffers and retries.
- DLQ captures failures.
- CloudWatch alarms monitor errors and backlog.
- CloudTrail audits changes/access.
- Idempotency prevents duplicate processing.

### Serverless API

```text
API Gateway -> Lambda -> DynamoDB
```

Mention:

- IAM/Cognito authorizer.
- Lambda logs and metrics.
- DynamoDB access pattern design.
- DLQ or retries for async work.

### Data Lake

```text
S3 -> Glue Data Catalog -> Athena/Glue/EMR -> QuickSight/Redshift
```

Mention:

- S3 zones: raw, trusted, curated.
- Glue catalog stores table metadata.
- Athena queries files in S3.
- Lake Formation can govern access.

## 16. Common Interview Questions

**Q: What is high availability?**  
Running across multiple failure domains so the system can continue if one component fails.

**Q: What is fault tolerance?**  
The system keeps working with little or no interruption after failure.

**Q: How do you secure S3?**  
Block public access, least privilege IAM/bucket policies, encryption, versioning, logging/auditing, and lifecycle controls.

**Q: How do you monitor a Lambda pipeline?**  
Use CloudWatch metrics for errors, duration, throttles; CloudWatch Logs for application logs; SQS metrics for queue age and DLQ depth; alarms to SNS; CloudTrail for audit.

**Q: What is idempotency?**  
Running the same operation more than once produces the same final result. It is critical for retries and at-least-once delivery.

**Q: How do you troubleshoot AccessDenied?**  
Check IAM identity policy, resource policy, SCP, permission boundary, session policy, KMS key policy, and CloudTrail.

**Q: What is the difference between SNS and SQS?**  
SNS pushes one message to many subscribers. SQS stores messages for consumers to pull.

**Q: What is a DLQ?**  
A dead-letter queue stores messages that failed repeatedly so they can be inspected or replayed.

**Q: When use Step Functions?**  
When a workflow has multiple steps, retries, branching, human approval, or needs visible orchestration state.

**Q: How do you reduce AWS cost?**  
Right-size resources, use lifecycle policies, autoscaling, reserved/savings plans where appropriate, reduce NAT/data transfer, delete unused resources, and monitor with budgets.

## 17. Final Rapid Review

Remember these one-liners:

- IAM controls who can do what.
- VPC controls network boundaries.
- S3 stores objects.
- Lambda runs event-driven code.
- SQS buffers work.
- SNS fans out messages.
- EventBridge routes events.
- DynamoDB is scalable NoSQL.
- RDS/Aurora is relational SQL.
- CloudWatch monitors health.
- CloudTrail audits API activity.
- KMS manages encryption keys.
- Secrets Manager stores and rotates secrets.
- Glue catalogs and runs ETL.
- Athena queries S3 with SQL.
- EMR runs Spark/Hadoop.
- Step Functions orchestrates workflows.
