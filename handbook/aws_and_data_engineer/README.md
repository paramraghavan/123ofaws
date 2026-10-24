# AWS Data Engineering: Mac And Remote Jupyter Lab

Run Docker Desktop, LocalStack, Python, and Jupyter on your Mac; work in a browser on another computer on your LAN.
Notebook code and files stay on the Mac. The notebook's LocalStack endpoint is `http://localhost:4566`.

## Reading Order

| Guide | Purpose |
|---|---|
| [setup.md](setup.md) | One-time Mac installation, local credentials, and S3 smoke test |
| [jupyter-lan-setup.md](jupyter-lan-setup.md) | Remote browser access, notebook commands, optional PySpark, and daily workflow |
| [learn.md](learn.md) | Local S3, Lambda, SNS, SQS, Step Functions, and small-file pipeline labs |
| [complete-aws-data-engineering-handbook.md](complete-aws-data-engineering-handbook.md) | AWS concepts and reference examples for Glue, Spark, EMR, governance, streaming, and SSM |
| [localstack-docker-setup.md](localstack-docker-setup.md) | Optional Compose configuration, persistence, endpoints, and container troubleshooting |

## Choose The Right Environment

- **Local API labs:** use `lstk aws` or explicitly configured Boto3 clients. Check your LocalStack service entitlements.
- **Local Spark:** runs on the Mac and needs Hadoop S3A libraries/settings for LocalStack storage.
- **Managed Glue/EMR:** use an AWS sandbox with suitable roles, resources, runtime versions, and billing controls.
  LocalStack API emulation does not provide a production managed Spark cluster.
- **Introductory pipeline:** calls Python handlers on the Mac. It does not deploy Lambda functions or automatic triggers.

Keep local endpoint/test-credential settings separate from real AWS sessions. Examples require adaptation and validation
before production use. See [Boto3 patterns](../boto3-complete-guide.md) and [troubleshooting](../troubleshooting-guide.md)
for additional detail.

## How The Pieces Fit

```text
Small-file lab:
CSV -> LocalStack S3 -> Python validator -> SNS -> SQS -> Python processor -> S3 output

Distributed data platform:
Sources -> S3 raw -> Glue/EMR Spark -> Curated data -> Catalog + query engine
                          |
                    Logs and metrics
```

The small-file lab runs its handlers on the Mac. A deployed Lambda pipeline also needs packaging, execution roles,
permissions, and event-source configuration. Large transformations belong in distributed processing rather than
loading entire files into a Python list.

## Services To Know

| Service | Role | Read next |
|---|---|---|
| S3 | Object storage for inputs, outputs, and data lakes | [S3 lab](learn.md#s3-cloud-storage) |
| SNS | Publish notifications to subscribers | [SNS lab](learn.md#sns-notifications) |
| SQS | Buffer messages until a consumer processes them | [SQS lab](learn.md#sqs-message-queues) |
| Lambda | Execute short event-driven functions | [Lambda lab](learn.md#lambda-serverless-functions) |
| Step Functions | Coordinate steps, retries, and failures | [Workflow lab](learn.md#step-functions-orchestration) |
| Glue Data Catalog | Describe tables and partitions over stored data | Reference Chapter 6 |
| Glue / EMR | Run managed distributed data processing | Reference Chapters 8 and 11 |
| Kinesis | Ingest and consume continuous event streams | Reference Chapter 14 |
| SSM Parameter Store | Retrieve runtime configuration and encrypted parameters | Reference Chapter 16 |

The [full reference](complete-aws-data-engineering-handbook.md) also covers IAM, Spark tuning, governance, and
cross-account access. A catalog describes data; it does not move or transform the files.

## If You Know Azure Or SQL

| Familiar concept | AWS comparison |
|---|---|
| Blob storage | S3 |
| Managed Spark | Glue or EMR, depending on runtime and operational needs |
| Workflow orchestration | Step Functions; use a scheduling service for scheduled starts |
| Event-driven functions | Lambda |
| Event streaming | Kinesis; SNS and SQS serve different messaging needs |

The concepts transfer, but SQL dialects, credentials, connectors, and deployment settings differ. Choose Glue versus EMR
from integrations, runtime control, operational effort, and benchmarks rather than a fixed dataset-size cutoff.
