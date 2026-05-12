# AWS Quick Reference for Interviews
## Senior Data Engineer Cheat Sheet

---

## 60-Second Service Comparison

| Service | When to Use | Cost | Your Experience |
|---------|------------|------|-----------------|
| **Glue** | Scheduled ETL, data discovery | $0.44/DPU-hr + storage | Freddie Mac lineage tracking |
| **EMR** | Spark jobs, sustained compute | $0.50-2/hr + EC2 | MessageBird, Fannie Mae |
| **Lambda** | Event-driven, sub-1min | $0.20M invocations + GB-s | Serverless, S3 triggers |
| **Step Functions** | Orchestration, error handling | $0.000025/state transition | Data pipeline coordination |
| **Kinesis** | Real-time streaming | $0.065/shard-hr | MessageBird event processing |
| **Athena** | Ad-hoc SQL queries | $5/TB scanned | Spectrum queries |
| **Redshift** | Analytics warehouse | $1.5/hour (ra3.xl+) | BI dashboards, aggregations |
| **DynamoDB** | NoSQL, sub-ms latency | $1.25/M writes (on-demand) | Metadata, hot data |
| **RDS/Aurora** | SQL OLTP, multi-AZ | $0.5-5/hr + storage | Metadata, source systems |
| **S3** | Object storage, data lake | $0.023/GB stored | Everything - foundational |

---

## Architecture Decision Trees

### "What tool for batch ETL?"
```
Size < 100 GB?  → Glue (simple, no ops)
Size 100GB-1TB? → Glue or small EMR cluster
Size > 1TB?     → EMR (cost-effective at scale)
Daily job?      → Glue (schedule-friendly)
Ad-hoc queries? → Athena (pay per scan)
Real-time?      → Kinesis + Lambda (100ms) or Flink (seconds)
```

### "How to handle failures?"
```
Transient (timeout)?      → Exponential backoff retry
Data quality issue?       → DLQ + manual review
Service quota exceeded?   → Wait before retry (2^attempt seconds)
Permanent error (bad input)?  → Catch + log + alert
Missing dependency?       → Block in Step Functions with Catch
```

### "Optimize this job?"
```
1. Profile first!
   - Spark UI for stage times
   - CloudWatch for memory/CPU
   - Check data volume (is it growing?)

2. Common fixes:
   - Too many partitions? → Coalesce
   - Too few partitions? → Repartition
   - Join skewed? → Enable adaptive.skewJoin
   - Too many small files? → Compaction
   - Memory pressure? → Increase executor memory
   - Shuffle bottleneck? → Increase shuffle partitions
```

---

## Code Snippets - Quick Copy-Paste

### Glue Job with Optimization
```python
from awsglue.context import GlueContext
from awsglue.job import Job

glueContext = GlueContext(SparkContext.getOrCreate())
job = Job(glueContext)
job.init('my-job', {"TempDir": "s3://bucket/temp"})

# Read with partition pruning
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="mydb", table_name="mytable",
    push_down_predicate="year >= 2024"  # ← Pushes filter to catalog
)

# Transform and write
df = dyf.toDF()
df.filter(df.status == "active") \
  .write.mode("overwrite") \
  .parquet("s3://bucket/output")

job.commit()
```

### Lambda with S3 Trigger
```python
import json, boto3

s3 = boto3.client('s3')
stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    try:
        # Async processing via Step Functions
        stepfunctions.start_execution(
            stateMachineArn=f"arn:aws:states:...:{STATE_MACHINE}",
            input=json.dumps({"bucket": bucket, "key": key})
        )
        return {'statusCode': 202}
    except Exception as e:
        print(f"Error: {e}")
        raise  # Let SQS/DLQ handle retry
```

### EMR Spark Tuning
```python
spark = SparkSession.builder \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.skewJoin.enabled", "true") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .config("spark.dynamicAllocation.minExecutors", "4") \
    .config("spark.dynamicAllocation.maxExecutors", "100") \
    .config("spark.sql.shuffle.partitions", "500") \
    .getOrCreate()

# Use partitioning for 100GB+ datasets
df = spark.read \
    .parquet("s3://bucket/data/year=2024/month=01/*") \
    .where("value > 100")  # Predicate pushdown

# Bucketing for frequent joins (MUST have same bucket count in both tables)
df.write \
    .bucketBy(100, "user_id") \
    .mode("overwrite") \
    .parquet("s3://bucket/bucketed")
```

### Step Functions with Error Handling
```json
{
  "StartAt": "ExtractData",
  "States": {
    "ExtractData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:extract",
      "Retry": [{
        "ErrorEquals": ["ServiceUnavailable"],
        "BackoffRate": 2.0,
        "MaxAttempts": 3,
        "IntervalSeconds": 2
      }],
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "NotifyFailure"
      }],
      "Next": "TransformData"
    },
    "TransformData": {
      "Type": "Task",
      "Resource": "arn:aws:emr:...",
      "Next": "NotifySuccess"
    },
    "NotifySuccess": {
      "Type": "Task",
      "Resource": "arn:aws:sns:...",
      "End": true
    },
    "NotifyFailure": {
      "Type": "Task",
      "Resource": "arn:aws:sns:...",
      "End": true
    }
  }
}
```

### Configuration-Driven ETL
```python
import json, boto3

class ConfigETL:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = json.load(f)

    def execute(self, pipeline_name):
        pipeline = next(p for p in self.config['pipelines']
                       if p['name'] == pipeline_name)

        for stage in pipeline['stages']:
            try:
                self.execute_stage(stage)
            except Exception as e:
                self.handle_error(e, pipeline.get('errorHandling'))
                raise

    def execute_stage(self, stage):
        if stage['type'] == 'extract':
            # Read from RDS/S3/API
            pass
        elif stage['type'] == 'transform':
            # PySpark or Pandas
            pass
        elif stage['type'] == 'load':
            # Write to S3/Redshift/DynamoDB
            pass

# Use case: 200+ data sources, self-service, auditable
```

---

## Key Interview Stories (Yours!)

### Story 1: Real-Time Streaming at MessageBird
**Setup:** "We needed to process 1M+ events/day across SMS, WhatsApp, voice in real-time"

**Challenge:** Latency, data quality, multi-channel consistency

**Solution:**
- Kinesis Data Streams for buffering
- Lambda + Firehose for ingestion
- Apache Flink for stateful processing
- Datadog dashboards for monitoring

**Result:** 100ms latency, 99.99% availability

**Interview Angle:** Shows you can design for scale, real-time requirements, complex orchestration

---

### Story 2: Configuration-Driven ETL at Freddie Mac
**Setup:** "100+ data pipelines, 200+ data sources, compliance requirements"

**Challenge:** Ops burden, audit trail, non-technical user needs

**Solution:**
- Configuration-driven framework
- Glue Catalog for metadata
- Neptune for data lineage
- Self-service dashboards

**Result:** 60% reduction in pipeline development time, full compliance audit trail

**Interview Angle:** Shows architecture thinking, governance, scalability

---

### Story 3: Performance Optimization at Fannie Mae
**Setup:** "Spark job processing 2TB+ financial data taking 8 hours"

**Challenge:** Cost, latency, cluster sizing

**Solution:**
- Enabled Adaptive Query Execution
- Implemented bucketing for joins
- Optimized partition strategy
- Added monitoring/alerting

**Result:** Reduced runtime to 2 hours (4x improvement), 70% cost reduction

**Interview Angle:** Shows systematic debugging, deep technical knowledge

---

## Common "Gotchas" to Avoid

### S3 Eventual Consistency
❌ Don't: "S3 is eventually consistent so we'll wait"
✅ Do: "We track processed files in DynamoDB with TTL for idempotency"

### Lambda Cold Starts
❌ Don't: "Cold starts are unavoidable"
✅ Do: "We use Provisioned Concurrency for critical paths, SQS for async non-critical"

### Spark Join Failures
❌ Don't: "Just increase memory"
✅ Do: "We check data skew in explain plan, use adaptive skew join, then memory"

### Cost Overruns
❌ Don't: "We monitor costs after the fact"
✅ Do: "We set CloudWatch alarms on daily spend, use Glue Studio for cost estimation"

### Data Quality
❌ Don't: "We validate after load"
✅ Do: "We validate during extraction with DQ rules, fail fast with DLQ"

---

## What NOT to Say in Interviews

| ❌ Avoid | ✅ Say Instead |
|---------|---------------|
| "EMR is expensive" | "EMR is cost-effective for workloads > 2 hours, we use Spot instances" |
| "Spark runs out of memory" | "We had OOM due to shuffle size; we reduced partitions and enabled AQE" |
| "We'll optimize later" | "We measure baseline performance, profile regularly, optimize systematically" |
| "AWS is slow" | "We reduced latency from 1h to 10m by using Redshift Spectrum filters" |
| "We don't have good monitoring" | "We use CloudWatch for infrastructure, Datadog for app-level metrics" |

---

## Pre-Interview Checklist

- [ ] Review your resume (know your numbers!)
- [ ] Prepare 5-7 concrete stories with metrics
- [ ] Draw EMR/Glue/Lambda architecture on whiteboard 2-3 times
- [ ] Answer "Why did you choose X over Y?" for your 3 latest projects
- [ ] Know your failure story (what didn't work and why)
- [ ] Practice explaining Spark optimization without getting lost
- [ ] Prepare 2-3 good questions about the role/company
- [ ] Test your whiteboard/drawing tool before interview

---

## Terraform & Infrastructure as Code Essentials

### Quick Terraform Pattern
```hcl
# VPC with private/public subnets
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
}

# Private subnet (for EMR, RDS)
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

# Security group with minimal permissions
resource "aws_security_group" "emr" {
  vpc_id = aws_vpc.main.id
  name   = "emr-sg"

  # SSH from VPC only
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # YARN UI from VPC only
  ingress {
    from_port   = 8088
    to_port     = 8088
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # All outbound
  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### IAM Least Privilege Pattern
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3SpecificPath",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::mybucket/data/*",
      "Condition": {
        "StringLike": {"s3:key": "data/*"}
      }
    },
    {
      "Sid": "DenyPublicBuckets",
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::public-*"
    },
    {
      "Sid": "DenyIAMChanges",
      "Effect": "Deny",
      "Action": ["iam:*", "ec2:TerminateInstances"],
      "Resource": "*"
    }
  ]
}
```

### Security Groups Interview Tips
**Q: EMR needs to read from RDS. How do you configure security groups?**
```
1. RDS-SG: Inbound port 5432 ONLY from EMR-SG
2. EMR-SG: Outbound port 5432 to RDS-SG
3. Never use 0.0.0.0/0 for database access
4. Use service-linked security group rules (reference by ID, not CIDR)
```

---

## Cross-Account & Cross-Region Access Patterns

### Cross-Account S3 Access (Prod→Dev)

**Prod Account (222...) - S3 Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDevAccountRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/dev-emr-role"
      },
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::prod-datalake/*"
      ],
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-secret-xyz"
        }
      }
    }
  ]
}
```

**Prod Account (222...) - KMS Key Policy:**
```json
{
  "Sid": "AllowDevAccountDecrypt",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::111111111111:role/dev-emr-role"
  },
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*"
}
```

**Dev Account (111...) - AssumeRole Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::222222222222:role/prod-data-access",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-secret-xyz"
        }
      }
    }
  ]
}
```

**Python - Assume Cross-Account Role:**
```python
import boto3

sts = boto3.client('sts')
assumed_role = sts.assume_role(
    RoleArn='arn:aws:iam::222222222222:role/prod-data-access',
    RoleSessionName='dev-session',
    ExternalId='unique-secret-xyz',
    DurationSeconds=3600
)

credentials = assumed_role['Credentials']
s3 = boto3.client(
    's3',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)

# Now read from prod bucket
obj = s3.get_object(Bucket='prod-datalake', Key='data/file.parquet')
```

### Cross-Region S3 Replication

**Terraform - S3 Replication Configuration:**
```hcl
# Enable versioning (required)
resource "aws_s3_bucket_versioning" "primary" {
  bucket = aws_s3_bucket.prod_primary.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Replication rule
resource "aws_s3_bucket_replication_configuration" "replication" {
  role   = aws_iam_role.replication_role.arn
  bucket = aws_s3_bucket.prod_primary.id

  rule {
    id     = "replicate-to-west"
    status = "Enabled"
    filter {
      prefix = "data/processed/"
    }
    destination {
      bucket = aws_s3_bucket.prod_replica_west.arn
      replication_time {
        status = "Enabled"
        time {
          minutes = 15  # RTC - replication within 15 minutes
        }
      }
    }
  }
}
```

### Cross-Region IAM Policy

**Analytics team accessing data across regions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadCrossRegionData",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::prod-replica-eu/*",
        "arn:aws:s3:::prod-replica-eu",
        "arn:aws:s3:::prod-replica-west/*",
        "arn:aws:s3:::prod-replica-west"
      ]
    },
    {
      "Sid": "AthenaQueries",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryResults"
      ],
      "Resource": "*"
    }
  ]
}
```

### "Confused Deputy" Prevention

**Always include External ID in cross-account assume role:**
```hcl
# In Prod account - Assume role condition
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::111111111111:role/dev-role"
  },
  "Action": "sts:AssumeRole",
  "Condition": {
    "StringEquals": {
      "sts:ExternalId": "unique-secret-12345"  # ← Required!
    }
  }
}
```

**Why?** Prevents confused deputy attack where attacker tricks you into assuming wrong role.

---

## AWS Systems Manager (SSM) Quick Reference

### Store Configuration
```python
import boto3

ssm = boto3.client('ssm')

# Store securely (encrypted)
ssm.put_parameter(
    Name='/myapp/database/password',
    Value='secret123',
    Type='SecureString'  # Encrypted
)

# Store as JSON
ssm.put_parameter(
    Name='/myapp/config',
    Value='{"batch_size": 5000}',
    Type='String'
)
```

### Retrieve Configuration
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_param(name):
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']

# Use in Lambda
password = get_param('/myapp/database/password')
config = json.loads(get_param('/myapp/config'))
```

### Parameter Store vs Secrets Manager
| Use Case | Service |
|----------|---------|
| Database password | Secrets Manager (auto-rotate) |
| API keys | Parameter Store (SecureString) |
| S3 bucket names | Parameter Store (String) |
| Config values | Parameter Store (String) |
| Rotating RDS password | Secrets Manager |

### Best Practices
```
✅ Use SecureString for sensitive data
✅ Cache parameters in memory (@lru_cache)
✅ Use path hierarchy: /prod/db/password
✅ Tag parameters by environment
✅ Restrict IAM permissions

❌ Don't hard-code secrets
❌ Don't use environment variables for secrets
❌ Don't grant everyone SSM access
```

---

## 30-Minute Interview Prep

**If you have only 30 minutes before interview:**

1. **Read your 3 most recent job roles** (5 min)
   - What was the scale? (1TB? 10TB?)
   - What was the challenge?
   - What did you solve?

2. **Review AWS services you used** (10 min)
   - Glue patterns (Freddie Mac)
   - Kinesis patterns (MessageBird)
   - EMR tuning (Fannie Mae)

3. **Draw one architecture** (10 min)
   - Data pipeline: Ingestion → Processing → Storage
   - Label: Kinesis → Lambda → S3, or Glue → Redshift

4. **Know your best story** (5 min)
   - 2TB job optimization
   - Real-time lineage system
   - Configuration-driven ETL

---

## Interview Response Templates

### "Walk us through your most complex project"
Template:
```
1. Scale: "We processed X TB/day across Y systems"
2. Challenge: "The challenge was [latency/governance/cost]"
3. Solution: "We chose [service] because [reasoning], implemented [pattern]"
4. Result: "We achieved [metric] - reduced latency by X% / reduced cost by Y%"
5. Learnings: "Going forward, we learned to [insight]"

Make it under 3 minutes total.
```

### "How would you optimize this?"
Template:
```
1. Clarify: "Let me understand - is this Spark job? What's the current runtime?"
2. Profile: "First I'd check the Spark UI for [stage times/shuffle/memory]"
3. Hypothesis: "I suspect the issue is [join? aggregation? I/O?]"
4. Solution: "We'd try [specific config change or code refactor]"
5. Measure: "We'd measure the improvement and document the change"

Show systematic thinking, not random guessing.
```

### "Tell us about a failure"
Template:
```
1. Situation: "We deployed a new Spark config that looked good in testing"
2. Problem: "In production, we got OutOfMemory errors on 100GB dataset"
3. Root cause: "We had 10M unique values in groupBy, causing huge shuffle"
4. Resolution: "We added data profiling to test suite, limited group by cardinality"
5. Learning: "Now we always profile production data shape before config changes"

Show you learn from failures, not that you're perfect.
```

---

## Salary Negotiation Tips

**Know your value:**
- 18 years experience, 9+ years AWS → Senior level ($180K-220K)
- Your Freddie Mac/MessageBird experience → Enterprise scale credibility
- Configuration-driven design, real-time systems → Specialized skills

**During negotiation:**
- "Based on [years experience] and [specific projects], I'm looking for $X"
- Don't give first number
- Use Glassdoor/Blind/Levels data as reference
- Negotiate total comp, not just base (stock, bonus, signing)

---

## Final Mindset

**Remember:**
- You have 18 years of experience, they're interviewing YOU
- Production problems you solved are real, their questions are academic
- You can design systems, they're asking about systems
- Be confident, not arrogant
- Show humility: "I don't know that, but here's how I'd approach it"

**Your unfair advantages:**
1. Real Freddie Mac experience (financial services, scale)
2. Real MessageBird experience (real-time, multi-channel)
3. Real Fannie Mae experience (big data, compliance)
4. Configuration-driven architecture (production-proven)
5. 9+ years hands-on AWS (not just certification knowledge)

Use them confidently!

---

**Last Updated:** May 2024
**Version:** 1.0 - Quick Reference
