# Configuration Reference

Complete guide to configuring **aws-lambda-monitoring** and understanding how it compares to **failover_ver3**.

## Configuration Approaches

### This System: aws-lambda-monitoring (Environment Variables)

No separate `config.json` file. Configuration is done via:

1. **serverless.yml** (for Serverless Framework deployment)
2. **CloudFormation parameters** (for CloudFormation deployment)
3. **Environment variables** (for local testing)

### Other System: failover_ver3 (config.json)

Uses a simple JSON config file checked into version control.

## Environment Variables (aws-lambda-monitoring)

### Available Variables

```python
# Required
TAG_NAME              # Tag value to monitor (e.g., "production")
LOG_BUCKET           # S3 bucket for logs
SNS_TOPIC_ARN        # SNS topic for alerts

# Optional
S3_REPLICA_REGION    # Region for S3 failover (default: us-west-2)
```

### Set via serverless.yml

```yaml
provider:
  environment:
    TAG_NAME: production
    LOG_BUCKET: simple-aws-monitoring-logs-${aws:accountId}
    SNS_TOPIC_ARN: !Ref AlertTopic
    S3_REPLICA_REGION: us-west-2
```

### Set via Shell Variables

```bash
export TAG_NAME=production
export LOG_BUCKET=simple-aws-monitoring-logs-123456789
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:alerts
serverless deploy
```

### Set via CloudFormation

```json
[
  {"ParameterKey": "TagName", "ParameterValue": "production"},
  {"ParameterKey": "CodeBucketName", "ParameterValue": "deployment-bucket"}
]
```

Deploy with:
```bash
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters file://params.json \
  --capabilities CAPABILITY_NAMED_IAM
```

## failover_ver3 Config File

### config.json Structure

```json
{
  "aws_profile": "default",
  "aws_region": "us-east-1",
  "tag_name": "production",
  "emr": {
    "bootstrap_repo": "https://github.com/your-org/emr-bootstrap.git",
    "bootstrap_branch": "main"
  }
}
```

### Config Fields Explained

| Field | Purpose | Example |
|-------|---------|---------|
| `aws_profile` | AWS CLI profile to use | `"default"`, `"prod"`, `"uat"` |
| `aws_region` | AWS region for resources | `"us-east-1"` |
| `tag_name` | Tag value to monitor (must match exactly) | `"production"` |
| `emr.bootstrap_repo` | Git repo with EMR bootstrap scripts | `"https://github.com/org/emr-scripts.git"` |
| `emr.bootstrap_branch` | Git branch for bootstrap scripts | `"main"`, `"dev"` |

### Multi-Environment config.json Files

Create multiple config files for different environments:

```bash
# Production
cat > config-prod.json << 'EOF'
{
  "aws_profile": "prod",
  "aws_region": "us-east-1",
  "tag_name": "production",
  "emr": {
    "bootstrap_repo": "https://github.com/org/emr-prod.git",
    "bootstrap_branch": "main"
  }
}
EOF

# UAT
cat > config-uat.json << 'EOF'
{
  "aws_profile": "uat",
  "aws_region": "us-east-1",
  "tag_name": "uat",
  "emr": {
    "bootstrap_repo": "https://github.com/org/emr-uat.git",
    "bootstrap_branch": "develop"
  }
}
EOF

# Development
cat > config-dev.json << 'EOF'
{
  "aws_profile": "dev",
  "aws_region": "us-west-2",
  "tag_name": "dev",
  "emr": {
    "bootstrap_repo": "https://github.com/org/emr-dev.git",
    "bootstrap_branch": "develop"
  }
}
EOF
```

Use them:
```bash
python failover_main.py --config config-prod.json --mode both
python failover_main.py --config config-uat.json --mode monitor
python failover_main.py --config config-dev.json --mode failover
```

## Quick Configuration Table

| Need | Use This | Location |
|------|----------|----------|
| **Single environment, serverless** | serverless.yml | `aws-lambda-monitoring/serverless.yml` |
| **Single environment, CloudFormation** | CloudFormation template | `aws-lambda-monitoring/cloudformation-template.yaml` |
| **Multiple environments, local** | config.json files | `failover_ver3/config-*.json` |
| **Quick test** | Environment variables | `export TAG_NAME=...` |
| **Production deployment** | CloudFormation + Parameters | `.json` parameter file |

## Migration Guide: config.json → Environment Variables

If you're moving from config.json-style configuration:

### Before (failover_ver3)
```json
{
  "aws_profile": "prod",
  "aws_region": "us-east-1",
  "tag_name": "production"
}
```

### After (aws-lambda-monitoring)
```yaml
# In serverless.yml
provider:
  environment:
    TAG_NAME: production

# Or environment variables
export TAG_NAME=production
export LOG_BUCKET=simple-aws-monitoring-logs-123456789
```

## Advanced Configuration

### Using AWS Secrets Manager

For sensitive configuration (API keys, passwords):

```python
# In monitor_lambda.py
import json
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Use in function
secret = get_secret('my-app/s3-failover-config')
replica_bucket = secret['replica_bucket']
```

### Using Parameter Store

For application configuration:

```python
import boto3

ssm = boto3.client('ssm')

# Get parameter
response = ssm.get_parameter(Name='/myapp/tag-name')
tag_name = response['Parameter']['Value']

# Update parameter (e.g., during failover)
ssm.put_parameter(
    Name='/myapp/s3-bucket',
    Value='new-bucket-name',
    Overwrite=True
)
```

### Using Environment-Specific serverless.yml

```yaml
# serverless-prod.yml
provider:
  environment:
    TAG_NAME: production
    LOG_BUCKET: monitoring-logs-prod

# serverless-dev.yml
provider:
  environment:
    TAG_NAME: development
    LOG_BUCKET: monitoring-logs-dev
```

Deploy environment-specific:
```bash
serverless deploy -c serverless-prod.yml
serverless deploy -c serverless-dev.yml
```

## Configuration Best Practices

### 1. Use Consistent Naming

```
✅ GOOD:
  TAG_NAME: production
  TAG_NAME: uat
  TAG_NAME: development

❌ BAD:
  TAG_NAME: prod
  TAG_NAME: testing
  TAG_NAME: dev
```

### 2. Document Your Choices

```yaml
# serverless.yml
provider:
  environment:
    # Resource tag to monitor - must match AWS resource tags exactly
    TAG_NAME: production

    # S3 bucket for monitoring logs and dashboard
    LOG_BUCKET: simple-aws-monitoring-logs-${aws:accountId}

    # Region for S3 failover replica bucket
    # Must have replica bucket pre-created in this region
    S3_REPLICA_REGION: us-west-2
```

### 3. Version Control Guidelines

**DO commit to git:**
- serverless.yml (with placeholder values)
- config.json (with example values)
- Configuration documentation

**DON'T commit to git:**
- AWS credentials
- API keys or secrets
- Account IDs (use CloudFormation intrinsics like `${aws:accountId}`)
- Personal information

### 4. Environment Separation

```bash
# Use CloudFormation stacks for environment separation
aws cloudformation create-stack \
  --stack-name monitoring-prod \
  --template-body file://cloudformation-template.yaml \
  --parameters file://params-prod.json

aws cloudformation create-stack \
  --stack-name monitoring-dev \
  --template-body file://cloudformation-template.yaml \
  --parameters file://params-dev.json
```

### 5. Testing Configuration

```bash
# 1. Validate serverless config
serverless validate

# 2. Test environment variables locally
export TAG_NAME=test
export LOG_BUCKET=test-logs
python monitor_lambda.py

# 3. Validate CloudFormation
aws cloudformation validate-template \
  --template-body file://cloudformation-template.yaml
```

## Configuration Checklist

### Before Deployment

- [ ] AWS CLI configured with credentials
- [ ] AWS account has required permissions
- [ ] S3 buckets for logs created
- [ ] S3 replica bucket created (for failover)
- [ ] SNS topic created or will be auto-created
- [ ] Resource tags created on EC2/EMR/S3
- [ ] TAG_NAME matches resource tags (case-sensitive)
- [ ] LOG_BUCKET name is globally unique
- [ ] S3_REPLICA_REGION is different from primary region

### After Deployment

- [ ] Lambda functions created successfully
- [ ] EventBridge rules enabled
- [ ] CloudWatch alarms created
- [ ] SNS subscriptions configured
- [ ] CloudWatch logs showing Lambda runs
- [ ] Dashboard accessible
- [ ] First monitoring run completed successfully
- [ ] Failover tested in non-production environment

## Troubleshooting Configuration Issues

### "No resources found"

**Cause:** TAG_NAME doesn't match resource tags

```bash
# Check what tags exist
aws ec2 describe-tags --filters Name=resource-type,Values=instance

# Verify exact spelling and case
aws s3api get-bucket-tagging --bucket my-bucket

# Update serverless.yml or environment variable to match exactly
```

### "Permission denied" errors

**Cause:** IAM role missing permissions

```bash
# Check Lambda role permissions
aws iam get-role-policy \
  --role-name simple-aws-monitoring-us-east-1-lambdaRole \
  --policy-name simple-aws-monitoring-us-east-1-policy

# Add missing permissions in serverless.yml iam.role.statements
```

### "Bucket not found" errors

**Cause:** LOG_BUCKET doesn't exist or wrong account

```bash
# Verify bucket exists
aws s3 ls s3://simple-aws-monitoring-logs-ACCOUNT_ID/

# Create if missing
aws s3api create-bucket --bucket simple-aws-monitoring-logs-ACCOUNT_ID
```

### CloudFormation parameter errors

**Cause:** Missing required parameters

```bash
# Validate template first
aws cloudformation validate-template \
  --template-body file://cloudformation-template.yaml

# Ensure all parameters provided
aws cloudformation create-stack \
  --stack-name simple-aws-monitoring \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=CodeBucketName,ParameterValue=my-bucket \
  --capabilities CAPABILITY_NAMED_IAM
```

## See Also

- [Main README.md](README.md) - Complete documentation
- [FAILOVER_GUIDE.md](FAILOVER_GUIDE.md) - S3 failover setup
- [failover_ver3/README.md](../failover_monitoring_cron/README.md) - failover_ver3 documentation
- [failover_ver3/config.json](../failover_monitoring_cron/config.json) - Example failover_ver3 config
