# Resource Tagging Strategy & Adding New Resources

Complete guide for tagging AWS resources and extending the monitoring system to new resource types.

## Table of Contents

1. [Tagging Fundamentals](#tagging-fundamentals)
2. [Naming Conventions](#naming-conventions)
3. [Tagging by Resource Type](#tagging-by-resource-type)
4. [Real-World Examples](#real-world-examples)
5. [Adding New Resource Types](#adding-new-resource-types)
6. [Best Practices](#best-practices)

---

## Tagging Fundamentals

### What is a Tag?

A tag is a **key-value pair** that you assign to AWS resources:

```
Key:   "Name"
Value: "production"

Key:   "Environment"
Value: "prod"

Key:   "CostCenter"
Value: "engineering"
```

### Why Tag?

- **Organization:** Organize resources by environment, project, owner
- **Monitoring:** Filter resources to monitor
- **Cost Allocation:** Track spending by department or project
- **Automation:** Trigger automated actions based on tags
- **Access Control:** Limit who can access tagged resources
- **Compliance:** Enforce resource naming policies

### Core Monitoring Tag

The monitoring system uses **one primary tag**:

```
Key:   "Name"
Value: "production"  (or "uat", "dev", etc.)
```

This is set in `serverless.yml`:
```yaml
environment:
  TAG_NAME: production  # Match this exactly
```

---

## Naming Conventions

### Recommended Convention

Use **environment-based naming** for simplicity:

```
Production:  Name = "production"
UAT:         Name = "uat"
Development: Name = "dev"
Staging:     Name = "staging"
Testing:     Name = "test"
```

### Alternative: Descriptive Naming

If you prefer more details:

```
Name = "web-server-prod"
Name = "database-prod"
Name = "api-gateway-uat"
```

**When using descriptive names, update TAG_NAME in serverless.yml:**

```yaml
environment:
  TAG_NAME: web-server-prod  # Now matches this specific resource group
```

### Enterprise Convention (Advanced)

Large organizations often use multiple tags:

```
Name:        "production-web-server"
Environment: "production"
Owner:       "platform-team"
CostCenter:  "engineering"
Application: "web"
Tier:        "frontend"
```

**System filters by Name tag only, but other tags help with cost allocation and access control.**

---

## Tagging by Resource Type

### S3 Buckets

```bash
# Tag with Name
aws s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[
    {Key=Name,Value=production},
    {Key=Environment,Value=prod},
    {Key=Owner,Value=data-team}
  ]'

# View tags
aws s3api get-bucket-tagging --bucket my-bucket

# Remove tags
aws s3api delete-bucket-tagging --bucket my-bucket
```

**Best Practice for S3:**
- Tag primary bucket with `Name=production`
- Tag replica bucket with `Name=production-replica` (separate monitoring)
- Also tag with `Purpose=data-storage` for clarity

### EC2 Instances

```bash
# Tag running instance
aws ec2 create-tags \
  --resources i-0123456789abcdef0 \
  --tags \
    Key=Name,Value=production \
    Key=Environment,Value=prod \
    Key=Owner,Value=ops-team

# Tag by filter (all running instances)
aws ec2 create-tags \
  --filters Name=instance-state-name,Values=running \
  --tags Key=Name,Value=production

# View tags
aws ec2 describe-tags \
  --filters Name=resource-id,Values=i-0123456789abcdef0

# Remove specific tag
aws ec2 delete-tags \
  --resources i-0123456789abcdef0 \
  --tags Key=Name
```

**Best Practice for EC2:**
- Use consistent naming across instance types (web, db, cache)
- Tag auto-scaling groups separately
- Document instance purpose in additional tags

### EMR Clusters

```bash
# Tag when creating cluster
aws emr create-cluster \
  --name my-cluster \
  --release-label emr-6.10.0 \
  --applications Name=Spark Name=Hadoop \
  --instance-groups \
    InstanceGroupType=MASTER,InstanceCount=1,InstanceType=m5.xlarge \
    InstanceGroupType=CORE,InstanceCount=3,InstanceType=m5.2xlarge \
  --tags \
    Name=production \
    Environment=prod \
    Owner=data-engineering

# Tag existing cluster
aws emr add-tags \
  --resource-id j-ABC123XYZ \
  --tags \
    Name=production \
    Environment=prod

# View tags
aws emr describe-cluster --cluster-id j-ABC123XYZ

# Remove tags
aws emr remove-tags --resource-id j-ABC123XYZ --tag-keys Name
```

**Best Practice for EMR:**
- Tag at cluster creation time
- Include cluster size in additional tags
- Document bootstrap script version

### RDS (Relational Database Service)

```bash
# Tag RDS instance
aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:my-database \
  --tags \
    Key=Name,Value=production \
    Key=Environment,Value=prod \
    Key=Application,Value=myapp

# View tags
aws rds list-tags-for-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:my-database

# Remove tags
aws rds remove-tags-from-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:my-database \
  --tag-keys Name
```

**Best Practice for RDS:**
- Tag databases by application and environment
- Document backup requirements in tags
- Track multi-AZ status

### DynamoDB Tables

```bash
# Tag DynamoDB table
aws dynamodb tag-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/my-table \
  --tags \
    Key=Name,Value=production \
    Key=Application,Value=myapp \
    Key=CostCenter,Value=engineering

# View tags
aws dynamodb list-tags-of-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/my-table

# Remove tags
aws dynamodb untag-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/my-table \
  --tag-keys Name
```

**Best Practice for DynamoDB:**
- Tag all tables for cost tracking
- Document throughput tier in tags
- Track data sensitivity level

### SNS Topics

```bash
# Tag SNS topic
aws sns tag-resource \
  --resource-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --tags \
    Key=Name,Value=production \
    Key=Application,Value=monitoring \
    Key=Purpose,Value=alerts

# View tags
aws sns list-tags-for-resource \
  --resource-arn arn:aws:sns:us-east-1:123456789012:my-topic

# Remove tags
aws sns untag-resource \
  --resource-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --tag-keys Name
```

**Best Practice for SNS:**
- Tag alert topics with purpose
- Document subscriber info
- Track notification type

### Lambda Functions

```bash
# Tag Lambda function
aws lambda tag-resource \
  --resource arn:aws:lambda:us-east-1:123456789012:function:my-function \
  --tags \
    Name=production \
    Application=monitoring \
    Owner=platform-team

# View tags
aws lambda list-tags \
  --resource arn:aws:lambda:us-east-1:123456789012:function:my-function

# Remove tags
aws lambda untag-resource \
  --resource arn:aws:lambda:us-east-1:123456789012:function:my-function \
  --tag-keys Name
```

**Best Practice for Lambda:**
- Tag production Lambdas consistently
- Document runtime and dependencies
- Track monitoring/logging requirements

### Auto Scaling Groups

```bash
# Tag Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --launch-template LaunchTemplateName=my-template,Version=\$Latest \
  --min-size 1 \
  --max-size 10 \
  --desired-capacity 3 \
  --vpc-zone-identifier subnet-xxx,subnet-yyy \
  --tags \
    Key=Name,Value=production,PropagateAtLaunch=true \
    Key=Environment,Value=prod,PropagateAtLaunch=true

# View tags
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names my-asg

# Update tags
aws autoscaling create-or-update-tags \
  --tags \
    ResourceId=my-asg,ResourceType=auto-scaling-group,Key=Name,Value=production,PropagateAtLaunch=true
```

**Best Practice for ASG:**
- Set `PropagateAtLaunch=true` to apply tags to launched instances
- Keep consistent with instance tags
- Document min/max/desired counts

### VPC Resources

```bash
# Tag VPC
aws ec2 create-tags \
  --resources vpc-12345678 \
  --tags Key=Name,Value=production-vpc

# Tag Subnet
aws ec2 create-tags \
  --resources subnet-12345678 \
  --tags Key=Name,Value=production-subnet-a

# Tag Security Group
aws ec2 create-tags \
  --resources sg-12345678 \
  --tags Key=Name,Value=production-sg

# Tag Route Table
aws ec2 create-tags \
  --resources rtb-12345678 \
  --tags Key=Name,Value=production-routes
```

**Best Practice for VPC:**
- Use consistent naming across network resources
- Tag for network segmentation
- Document security tier

---

## Real-World Examples

### Example 1: Production Web Application

**Resource Group: production-web**

```bash
# EC2 Instances (web servers)
aws ec2 create-tags \
  --resources i-web001 i-web002 i-web003 \
  --tags \
    Key=Name,Value=production-web \
    Key=Environment,Value=prod \
    Key=Tier,Value=frontend \
    Key=Application,Value=web-app \
    Key=Owner,Value=frontend-team

# RDS Database
aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:prod-web-db \
  --tags \
    Key=Name,Value=production-web \
    Key=Environment,Value=prod \
    Key=Tier,Value=backend \
    Key=Application,Value=web-app

# S3 Bucket (static assets)
aws s3api put-bucket-tagging \
  --bucket prod-web-assets \
  --tagging 'TagSet=[
    {Key=Name,Value=production-web},
    {Key=Environment,Value=prod},
    {Key=Purpose,Value=static-assets}
  ]'

# ElastiCache (Redis)
aws elasticache add-tags-to-resource \
  --resource-name arn:aws:elasticache:us-east-1:123456789012:cluster:prod-web-cache \
  --tags \
    Key=Name,Value=production-web \
    Key=Environment,Value=prod \
    Key=Purpose,Value=session-cache
```

### Example 2: Data Processing Pipeline

**Resource Group: production-data**

```bash
# EMR Cluster
aws emr add-tags \
  --resource-id j-PROD123 \
  --tags \
    Name=production-data \
    Environment=prod \
    Owner=data-engineering \
    CostCenter=analytics

# S3 Data Bucket
aws s3api put-bucket-tagging \
  --bucket prod-data-lake \
  --tagging 'TagSet=[
    {Key=Name,Value=production-data},
    {Key=Environment,Value=prod},
    {Key=Purpose,Value=data-lake}
  ]'

# Glue Job
aws glue tag-resource \
  --resource-arn arn:aws:glue:us-east-1:123456789012:job/prod-etl \
  --tags-to-add \
    Name=production-data \
    Environment=prod
```

### Example 3: Multi-Environment Setup

**Development Environment:**
```bash
# All dev resources tagged with Name=dev
aws ec2 create-tags --resources i-dev001 --tags Key=Name,Value=dev
aws rds add-tags-to-resource --resource-name arn:... --tags Key=Name,Value=dev
aws s3api put-bucket-tagging --bucket dev-bucket --tagging 'TagSet=[{Key=Name,Value=dev}]'
```

**UAT Environment:**
```bash
# All UAT resources tagged with Name=uat
aws ec2 create-tags --resources i-uat001 --tags Key=Name,Value=uat
aws rds add-tags-to-resource --resource-name arn:... --tags Key=Name,Value=uat
aws s3api put-bucket-tagging --bucket uat-bucket --tagging 'TagSet=[{Key=Name,Value=uat}]'
```

**Production Environment:**
```bash
# All prod resources tagged with Name=production
aws ec2 create-tags --resources i-prod001 --tags Key=Name,Value=production
aws rds add-tags-to-resource --resource-name arn:... --tags Key=Name,Value=production
aws s3api put-bucket-tagging --bucket prod-bucket --tagging 'TagSet=[{Key=Name,Value=production}]'
```

---

## Adding New Resource Types

### Overview

The monitoring system is designed to be easily extended. Here's how to add support for new AWS services.

### Step 1: Add Check Function to monitor_lambda.py

```python
def check_dynamodb_tables():
    """Check DynamoDB tables with matching tag"""
    dynamodb = boto3.client('dynamodb')
    tables = []

    try:
        # List all tables
        response = dynamodb.list_tables()
        table_names = response.get('TableNames', [])

        for table_name in table_names:
            try:
                # Get table details
                table_details = dynamodb.describe_table(TableName=table_name)
                table = table_details['Table']

                # Get tags
                table_arn = table['TableArn']
                tags_response = dynamodb.list_tags_of_resource(ResourceArn=table_arn)
                tags = tags_response.get('Tags', [])

                # Check if matches tag
                if has_matching_tag(tags, TAG_NAME):
                    tables.append({
                        'name': table_name,
                        'status': table['TableStatus'].lower(),  # active, creating, etc.
                        'region': table_arn.split(':')[3],
                        'size_bytes': table.get('TableSizeBytes', 0)
                    })

            except ClientError as e:
                print(f"Error checking table {table_name}: {str(e)}")

    except Exception as e:
        print(f"Error in check_dynamodb_tables: {str(e)}")

    return tables
```

### Step 2: Call New Function in lambda_handler

```python
def lambda_handler(event, context):
    """Main monitoring function - runs every 10 minutes"""
    try:
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            's3_buckets': check_s3_buckets(),
            'ec2_instances': check_ec2_instances(),
            'emr_clusters': check_emr_clusters(),
            'dynamodb_tables': check_dynamodb_tables(),  # NEW
            'rds_databases': check_rds_databases(),      # NEW
            'sns_topics': check_sns_topics()             # NEW
        }

        # ... rest of function
```

### Step 3: Update Dashboard Template

```html
<h2>DynamoDB Tables</h2>
<table id="dynamodb-table"></table>

<h2>RDS Databases</h2>
<table id="rds-table"></table>

<h2>SNS Topics</h2>
<table id="sns-table"></table>

<script>
    // ... existing code ...

    // Add to renderTable calls:
    renderTable('dynamodb-table', status.dynamodb_tables || [], ['name', 'status', 'region']);
    renderTable('rds-table', status.rds_databases || [], ['name', 'status', 'engine']);
    renderTable('sns-table', status.sns_topics || [], ['name', 'subscriptions', 'status']);
</script>
```

### Step 4: Update Serverless.yml IAM Permissions

```yaml
provider:
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            # ... existing permissions ...
            - dynamodb:ListTables
            - dynamodb:DescribeTable
            - dynamodb:ListTagsOfResource
            - rds:DescribeDBInstances
            - rds:ListTagsForResource
            - sns:ListTopics
            - sns:GetTopicAttributes
            - sns:ListTagsForResource
          Resource: '*'
```

### Step 5: Deploy

```bash
serverless deploy
```

---

## Adding Kubernetes Resources (Future)

When you're ready to add Kubernetes monitoring:

### Monitoring Approach

Kubernetes resources typically run **inside clusters**, not at the AWS resource level. You have two options:

#### Option A: Monitor K8s Clusters via AWS

```python
def check_eks_clusters():
    """Check EKS (Elastic Kubernetes Service) clusters"""
    eks = boto3.client('eks')
    clusters = []

    try:
        response = eks.list_clusters()
        cluster_names = response.get('clusters', [])

        for cluster_name in cluster_names:
            cluster_details = eks.describe_cluster(name=cluster_name)
            cluster = cluster_details['cluster']

            # Check tags
            tags = cluster.get('tags', {})
            if TAG_NAME in str(tags.values()):
                clusters.append({
                    'name': cluster_name,
                    'status': cluster['status'].lower(),  # CREATING, ACTIVE, etc.
                    'version': cluster['version'],
                    'endpoint': cluster['endpoint']
                })

    except Exception as e:
        print(f"Error in check_eks_clusters: {str(e)}")

    return clusters
```

#### Option B: Monitor Inside K8s Cluster

Create a separate monitoring system inside Kubernetes using custom resources:

```python
# Run a monitoring pod/deployment inside K8s
# That reports back to your SNS/S3 infrastructure

def post_k8s_health_to_s3(cluster_name, health_status):
    """Post Kubernetes health status to S3"""
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=f'k8s-status/{cluster_name}.json',
        Body=json.dumps({
            'cluster': cluster_name,
            'timestamp': datetime.utcnow().isoformat(),
            'pods_healthy': health_status['healthy'],
            'pods_total': health_status['total']
        })
    )
```

### Adding SNS, DynamoDB, RDS, Lambda Monitoring

These are simpler since they're AWS-native services:

```python
# SNS Topics
def check_sns_topics():
    sns = boto3.client('sns')
    topics = []
    response = sns.list_topics()
    for topic in response.get('Topics', []):
        tags = sns.list_tags_for_resource(ResourceArn=topic['TopicArn'])
        if has_matching_tag(tags.get('Tags', []), TAG_NAME):
            topics.append({
                'arn': topic['TopicArn'],
                'subscriptions': get_subscription_count(topic['TopicArn']),
                'status': 'active'
            })
    return topics

# RDS Databases
def check_rds_databases():
    rds = boto3.client('rds')
    databases = []
    response = rds.describe_db_instances()
    for db in response.get('DBInstances', []):
        tags = rds.list_tags_for_resource(ResourceName=db['DBResourceId'])
        if has_matching_tag(tags.get('TagList', []), TAG_NAME):
            databases.append({
                'name': db['DBInstanceIdentifier'],
                'engine': db['Engine'],
                'status': db['DBInstanceStatus'],
                'instance_type': db['DBInstanceClass']
            })
    return databases

# Lambda Functions
def check_lambda_functions():
    lambda_client = boto3.client('lambda')
    functions = []
    response = lambda_client.list_functions()
    for func in response.get('Functions', []):
        tags = lambda_client.list_tags(Resource=func['FunctionArn'])
        if has_matching_tag(tags.get('Tags', {}), TAG_NAME):
            functions.append({
                'name': func['FunctionName'],
                'runtime': func['Runtime'],
                'memory': func['MemorySize'],
                'timeout': func['Timeout'],
                'status': 'active'  # Lambda functions don't have status like EC2
            })
    return functions
```

---

## Best Practices

### 1. Standardize Tag Keys

**Standard Tag Set:**
```
Name              → Resource name/identifier (REQUIRED)
Environment       → prod, uat, dev, staging, test
Owner             → Team or person responsible
CostCenter        → For billing allocation
Application       → Application name
Tier              → frontend, backend, data, cache
Purpose           → What it's used for
Backup            → true/false - backup policy
DataClassification → public, internal, confidential, restricted
```

### 2. Enforce Tagging with Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestTag/Name": ["*"]
        }
      }
    }
  ]
}
```

### 3. Tag at Creation Time

**Don't tag later - tag when creating resources:**

```bash
# ✅ GOOD - Tag at creation
aws ec2 run-instances \
  --image-id ami-xxx \
  --instance-type t2.micro \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=production}]'

# ❌ BAD - Tag after creation
aws ec2 run-instances --image-id ami-xxx --instance-type t2.micro
aws ec2 create-tags --resources i-xxx --tags Key=Name,Value=production
```

### 4. Use Consistent Case

```
# ✅ GOOD - Consistent case
Key=Name,Value=production
Key=Environment,Value=prod

# ❌ BAD - Inconsistent case
Key=name,Value=production    # different case
Key=NAME,Value=PRODUCTION    # all caps
Key=Name,Value=Production    # capital P
```

### 5. Document Tag Purposes

Create a tagging policy document:

```markdown
# Tagging Policy

## Required Tags

- **Name**: Resource identifier (REQUIRED)
  - Format: environment-resource-type
  - Examples: production-web-server, uat-db, dev-cache

- **Environment**: Deployment environment
  - Values: production, uat, dev, staging, test

## Optional Tags

- **Owner**: Team/person responsible
- **CostCenter**: For billing
- **Application**: App name
- **Backup**: true/false
```

### 6. Regular Tag Audits

```bash
# Find untagged resources
aws ec2 describe-instances \
  --filters "Name=tag-key,Values=Name" \
  --query 'Reservations[*].Instances[?!Tags[?Key==`Name`]].InstanceId'

# Find misnamed resources
aws ec2 describe-instances \
  --filters "Name=tag-key,Values=Name" \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value]'
```

### 7. Tag Naming Examples by Organization

**Small Startup:**
```
Name=production          # Simple, one environment
Name=staging
Name=development
```

**Mid-Size Company:**
```
Name=production-web      # By application tier
Name=production-data
Environment=prod         # Extra clarity
Owner=frontend-team
```

**Enterprise:**
```
Name=prod-web-server-01                  # Detailed naming
Environment=production
Owner=platform-engineering
CostCenter=eng-prod-001
Application=web-platform
Tier=frontend
DataClassification=internal
BackupPolicy=daily
Compliance=sox
```

---

## Tagging Checklist

Before going to production:

- [ ] All resources tagged with consistent **Name** tag
- [ ] **Name** values match TAG_NAME in serverless.yml exactly (case-sensitive)
- [ ] Replica S3 buckets created and tagged
- [ ] Backup/replica resources tagged differently (e.g., `Name=production-replica`)
- [ ] Tag policy documented for your team
- [ ] IAM users can only create tagged resources
- [ ] Regular tag audits scheduled (weekly/monthly)
- [ ] Dashboard can see all resources
- [ ] SNS alerts configured for tagged resources
- [ ] Cost allocation tags set (Owner, CostCenter)

---

## Quick Reference Commands

### List All Tags on Resource
```bash
# EC2
aws ec2 describe-tags --filters "Name=resource-id,Values=i-xxx"

# S3
aws s3api get-bucket-tagging --bucket my-bucket

# EMR
aws emr describe-cluster --cluster-id j-xxx

# RDS
aws rds list-tags-for-resource --resource-name arn:...

# DynamoDB
aws dynamodb list-tags-of-resource --resource-arn arn:...
```

### Find Resources by Tag
```bash
# EC2 with specific tag value
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=production"

# All EC2 with any Name tag
aws ec2 describe-instances \
  --filters "Name=tag-key,Values=Name"

# S3 buckets (more complex - no direct filter)
aws s3api list-buckets --query 'Buckets[*].Name' | \
  xargs -I {} aws s3api get-bucket-tagging --bucket {} --output text 2>/dev/null | grep -B1 production
```

### Delete Tags
```bash
# EC2
aws ec2 delete-tags --resources i-xxx --tags Key=Name

# S3 (replace all tags, omit the one to delete)
aws s3api put-bucket-tagging --bucket my-bucket --tagging 'TagSet=[{...other tags}]'

# EMR
aws emr remove-tags --resource-id j-xxx --tag-keys Name
```

---

## See Also

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [Resource Groups User Guide](https://docs.aws.amazon.com/ARG/latest/userguide/tagging.html)
- [Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
- [README.md](README.md) - Main documentation
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Configuration options
