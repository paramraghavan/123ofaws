# Brownfield vs Edge Node: Assuming Roles Guide

> **AWS IAM role assumption on brownfield servers vs AWS edge nodes**: Complete guide covering practical implementation, best practices, and decision matrices for different deployment scenarios.

---

## Table of Contents

1. [Quick Decision Matrix](#quick-decision-matrix)
2. [Brownfield Servers](#brownfield-servers)
3. [AWS Edge Nodes](#aws-edge-nodes)
4. [Practical Implementations](#practical-implementations)
5. [IAM Setup Required](#iam-setup-required)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Quick Decision Matrix

```
┌─────────────────────────────────────────────────────────────┐
│ WHERE AM I RUNNING?          │ APPROACH                    │
├──────────────────────────────┼─────────────────────────────┤
│ Brownfield (On-Prem)         │ → STS AssumeRole            │
│ Brownfield → Different Acct  │ → STS AssumeRole            │
│                              │                             │
│ Outpost (EC2-like)           │ → Service Role (auto)       │
│ Wavelength Zone              │ → Service Role (auto)       │
│ Local Zone                   │ → Service Role (auto)       │
│                              │                             │
│ Edge → Different Account     │ → Service Role + AssumeRole │
│ Edge → Same Account          │ → Service Role (only)       │
└─────────────────────────────────────────────────────────────┘
```

---

# Brownfield Servers (On-Premises/Non-AWS)

## Overview

A **brownfield server** is an existing, non-AWS server (on-premises or hosted elsewhere) that needs to access AWS resources. These servers cannot use EC2 instance profiles or IAM roles automatically.

## Option 1: STS AssumeRole (Recommended)

You **DO need to assume a role** using long-term credentials:

```python
import boto3

# 1. Use long-term credentials (stored securely)
sts = boto3.client('sts')

# 2. Assume the role
response = sts.assume_role(
    RoleArn='arn:aws:iam::ACCOUNT:role/BrownfieldServerRole',
    RoleSessionName='brownfield-server-session',
    DurationSeconds=3600
)

# 3. Use temporary credentials
creds = response['Credentials']
s3 = boto3.client(
    's3',
    aws_access_key_id=creds['AccessKeyId'],
    aws_secret_access_key=creds['SecretAccessKey'],
    aws_session_token=creds['SessionToken']
)
```

### Why Assume a Role?

| Benefit | Details |
|---------|---------|
| **Short-lived credentials** | Max 1 hour (default), auto-expire |
| **Audit trail** | All calls logged in CloudTrail |
| **Instant revocation** | Can be revoked without key rotation |
| **Least privilege** | Separate roles for different purposes |
| **Security best practice** | Industry standard for cross-service access |

## Option 2: Long-Term Credentials (Not Recommended)

Only use as a fallback for legacy systems:

```python
# ❌ Less secure - keys don't expire
import os
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)
```

**Drawbacks:**
- ❌ Keys never expire
- ❌ Difficult to rotate
- ❌ Higher compromise risk
- ❌ Audit trail less clear
- ❌ Cannot be instantly revoked

---

# AWS Edge Nodes

## What Are AWS Edge Nodes?

AWS edge nodes include:
- **AWS Outposts** - On-premises AWS compute/storage
- **Wavelength** - AWS infrastructure at 5G edges
- **Local Zones** - AWS closer to major cities
- **Snow devices** - Portable AWS computing

## Can You Use Service Roles? ✅ YES!

**If the edge node is AWS-managed** (Outposts, Wavelength, Local Zones):

```python
# Edge node automatically has IAM role attached
# No need to assume - just use it!

import boto3

# On the edge node, boto3 auto-detects the role
s3 = boto3.client('s3')  # Uses the attached service role
ec2 = boto3.client('ec2')  # Same role

# This works because edge nodes support EC2 instance profiles
bucket_list = s3.list_buckets()
```

## Service Role vs AssumeRole on Edge

| Scenario | Use Service Role? | Use AssumeRole? | Details |
|----------|------------------|-----------------|---------|
| **Edge node (EC2-like)** | ✅ YES | ❌ Optional | Auto-assigned by AWS |
| **Outposts with instance profiles** | ✅ YES | ❌ No need | Works like EC2 |
| **Edge node → different account** | ❌ NO | ✅ YES | Must assume target role |
| **Brownfield server** | ❌ NO | ✅ YES | No auto role available |
| **Lambda on edge** | ✅ YES | ❌ No need | Auto role from definition |

---

# Practical Implementations

## Scenario 1: Brownfield Server → AWS S3

**Use case**: On-premises data center uploading files to AWS S3

```python
from boto3 import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BrownfieldAWSAccess:
    """Secure AWS access from on-premises servers"""

    def __init__(self, access_key, secret_key, role_arn, duration=3600):
        """
        Initialize brownfield AWS access.

        Args:
            access_key: Long-term AWS access key (from IAM user)
            secret_key: Long-term AWS secret key
            role_arn: ARN of role to assume
            duration: Credential duration in seconds (900-3600)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.role_arn = role_arn
        self.duration = duration
        self._credentials_cache = {}

    def get_temporary_credentials(self):
        """Get temporary credentials via AssumeRole"""
        try:
            sts = Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ).client('sts')

            response = sts.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName='brownfield-session',
                DurationSeconds=self.duration
            )

            creds = response['Credentials']
            logger.info(f"Successfully assumed role {self.role_arn}")

            return {
                'AccessKeyId': creds['AccessKeyId'],
                'SecretAccessKey': creds['SecretAccessKey'],
                'SessionToken': creds['SessionToken'],
                'Expiration': creds['Expiration']
            }

        except Exception as e:
            logger.error(f"Failed to assume role: {e}")
            raise

    def get_s3_client(self):
        """Get S3 client with temporary credentials"""
        creds = self.get_temporary_credentials()

        return Session(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        ).client('s3')

    def upload_file(self, local_path, bucket, s3_key):
        """Upload file from brownfield server to S3"""
        s3 = self.get_s3_client()

        try:
            s3.upload_file(local_path, bucket, s3_key)
            logger.info(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

# Usage on brownfield server
if __name__ == '__main__':
    accessor = BrownfieldAWSAccess(
        access_key='AKIAIOSFODNN7EXAMPLE',
        secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        role_arn='arn:aws:iam::123456789:role/BrownfieldAccess',
        duration=3600
    )

    # Upload file
    accessor.upload_file(
        local_path='/data/customers.csv',
        bucket='my-data-bucket',
        s3_key='incoming/customers.csv'
    )
```

## Scenario 2: AWS Outpost/Edge Node with Service Role

**Use case**: Edge node automatically accessing AWS services

```python
import boto3

# Edge node already has service role attached
# No credentials needed!

# This just works:
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

# All use the attached service role automatically
bucket_list = s3.list_buckets()

# Process data in S3
s3.upload_file(
    'local_file.parquet',
    'bucket-name',
    'data/file.parquet'
)

# Query DynamoDB
response = dynamodb.get_item(
    TableName='edge-data',
    Key={'id': {'S': 'record-1'}}
)

# Invoke Lambda on edge
result = lambda_client.invoke(
    FunctionName='edge-processor',
    InvocationType='RequestResponse',
    Payload=b'{"data": "test"}'
)

print("All operations successful - service role handles credentials!")
```

## Scenario 3: Edge Node → Different AWS Account (AssumeRole)

**Use case**: Edge node in Account A accessing resources in Account B

```python
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class EdgeNodeCrossAccount:
    """Access other AWS accounts from edge node"""

    def __init__(self, target_account, role_name, region='us-east-1'):
        """
        Initialize cross-account access from edge node.

        Args:
            target_account: Target AWS account ID
            role_name: Role name in target account
            region: AWS region
        """
        self.target_account = target_account
        self.role_name = role_name
        self.region = region
        self.target_role_arn = f'arn:aws:iam::{target_account}:role/{role_name}'
        self._credentials_cache = {}
        self._cache_expiry = None

    def assume_role_in_target_account(self):
        """Assume role using edge node's service role"""
        try:
            sts = boto3.client('sts', region_name=self.region)

            response = sts.assume_role(
                RoleArn=self.target_role_arn,
                RoleSessionName='edge-to-target-account',
                DurationSeconds=3600
            )

            creds = response['Credentials']
            logger.info(f"Successfully assumed role in account {self.target_account}")

            return {
                'access_key': creds['AccessKeyId'],
                'secret_key': creds['SecretAccessKey'],
                'token': creds['SessionToken'],
                'expiration': creds['Expiration']
            }

        except ClientError as e:
            logger.error(f"Failed to assume role: {e}")
            raise

    def get_s3_client_in_target(self):
        """Get S3 client in target account"""
        creds = self.assume_role_in_target_account()

        return boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds['token']
        )

    def get_dynamodb_client_in_target(self):
        """Get DynamoDB client in target account"""
        creds = self.assume_role_in_target_account()

        return boto3.client(
            'dynamodb',
            region_name=self.region,
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds['token']
        )

    def get_generic_client(self, service_name):
        """Get any AWS service client in target account"""
        creds = self.assume_role_in_target_account()

        return boto3.client(
            service_name,
            region_name=self.region,
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds['token']
        )

# Usage on edge node
if __name__ == '__main__':
    cross_account = EdgeNodeCrossAccount(
        target_account='999999999999',
        role_name='EdgeNodeTargetRole',
        region='us-east-1'
    )

    # Access S3 in target account
    s3_target = cross_account.get_s3_client_in_target()
    response = s3_target.list_objects_v2(
        Bucket='target-account-bucket'
    )
    print(f"Found {len(response.get('Contents', []))} objects in target bucket")

    # Access DynamoDB in target account
    ddb_target = cross_account.get_dynamodb_client_in_target()
    response = ddb_target.list_tables()
    print(f"Tables in target account: {response['TableNames']}")

    # Access any service
    lambda_target = cross_account.get_generic_client('lambda')
    response = lambda_target.list_functions()
    print(f"Functions in target account: {len(response['Functions'])}")
```

---

# IAM Setup Required

## For Brownfield Servers

### Step 1: Create IAM User with Long-Term Credentials

```bash
# Create user
aws iam create-user --user-name brownfield-server-user

# Create access key
aws iam create-access-key --user-name brownfield-server-user
```

### Step 2: Attach AssumeRole Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::123456789:role/BrownfieldServerRole"
        }
    ]
}
```

```bash
# Attach policy
aws iam put-user-policy \
    --user-name brownfield-server-user \
    --policy-name BrownfieldAssumeRole \
    --policy-document file://policy.json
```

### Step 3: Create Role for Brownfield Server

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789:user/brownfield-server-user"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

```bash
# Create role with trust policy
aws iam create-role \
    --role-name BrownfieldServerRole \
    --assume-role-policy-document file://trust-policy.json
```

### Step 4: Attach Permissions to Role

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        }
    ]
}
```

```bash
# Attach permissions
aws iam put-role-policy \
    --role-name BrownfieldServerRole \
    --policy-name S3Access \
    --policy-document file://permissions.json
```

## For AWS Edge Nodes

### Automatic Setup

**AWS handles this automatically!** When you:

1. Create an Outpost/Wavelength/Local Zone instance
2. AWS automatically assigns a service role
3. No manual setup needed - boto3 auto-detects it

### For Cross-Account Access from Edge

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT-A:role/EdgeNodeServiceRole"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Place this trust policy on the role in Account B that the edge node should access.

---

# Best Practices

## For Brownfield Servers

| Practice | Details |
|----------|---------|
| **Store credentials securely** | Use AWS Secrets Manager or HashiCorp Vault |
| **Rotate keys regularly** | Every 90 days minimum |
| **Use shortest duration** | Set DurationSeconds to minimum needed (default 1 hour) |
| **Enable CloudTrail** | Log all AssumeRole calls for audit |
| **Least privilege** | Only grant necessary permissions in role |
| **Session naming** | Use descriptive RoleSessionName for audit trail |
| **Encrypt credentials in transit** | Use TLS/HTTPS only |

### Credential Storage Example

```python
import boto3
import json

def get_credentials_from_secrets_manager(secret_name):
    """Retrieve brownfield credentials securely"""
    secrets = boto3.client('secretsmanager')

    response = secrets.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    return secret['access_key'], secret['secret_key']

# Usage
access_key, secret_key = get_credentials_from_secrets_manager(
    'brownfield/aws-credentials'
)

accessor = BrownfieldAWSAccess(
    access_key=access_key,
    secret_key=secret_key,
    role_arn='arn:aws:iam::123456789:role/BrownfieldServerRole'
)
```

## For AWS Edge Nodes

| Practice | Details |
|----------|---------|
| **Use service roles** | Never hardcode credentials on edge nodes |
| **Verify instance profile** | Confirm service role is attached on launch |
| **Monitor AssumeRole calls** | Log cross-account access in CloudTrail |
| **Use EC2 instance tags** | Tag edge nodes for tracking and policies |
| **Implement least privilege** | Separate roles for different edge node types |
| **Test on launch** | Verify role works immediately after startup |

## For Both

| Practice | Details |
|----------|---------|
| **Enable CloudTrail** | Log all AssumeRole calls: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole` |
| **Set up alarms** | CloudWatch alarms on failed AssumeRole attempts |
| **Document role purposes** | Add descriptions to all roles |
| **Use resource tags** | Tag all roles with environment, team, purpose |
| **Regularly audit** | Review who can assume which roles quarterly |

---

# Troubleshooting

## Common Issues

### "User is not authorized to perform: sts:AssumeRole"

**Cause**: IAM user doesn't have AssumeRole permission

**Solution**:
```bash
# Check user's attached policies
aws iam list-attached-user-policies --user-name brownfield-server-user

# Attach AssumeRole policy
aws iam put-user-policy \
    --user-name brownfield-server-user \
    --policy-name AssumeRole \
    --policy-document file://assume-role-policy.json
```

### "The role does not have a trust relationship with the principal"

**Cause**: Role's trust policy doesn't include the user/role

**Solution**:
```bash
# Check current trust policy
aws iam get-role --role-name BrownfieldServerRole

# Update trust policy to include the user
# Edit trust-policy.json and update role
aws iam update-assume-role-policy-document \
    --role-name BrownfieldServerRole \
    --policy-document file://trust-policy.json
```

### "Credentials have expired"

**Cause**: Session credentials older than max duration

**Solution**:
```python
# Always request fresh credentials
credentials = accessor.get_temporary_credentials()

# Check expiration
from datetime import datetime
if credentials['Expiration'] < datetime.utcnow():
    credentials = accessor.get_temporary_credentials()  # Get new ones
```

### "AccessDenied on S3 operation"

**Cause**: Role doesn't have required S3 permissions

**Solution**:
```bash
# Check role permissions
aws iam get-role-policy --role-name BrownfieldServerRole --policy-name S3Access

# Update with required permissions
aws iam put-role-policy \
    --role-name BrownfieldServerRole \
    --policy-name S3Access \
    --policy-document file://s3-permissions.json
```

## Debugging Commands

```bash
# Test credentials
aws sts get-caller-identity \
    --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
    --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Simulate AssumeRole
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::123456789:user/brownfield-server-user \
    --action-names sts:AssumeRole \
    --resource-arns arn:aws:iam::123456789:role/BrownfieldServerRole

# Check CloudTrail for failures
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
    --max-results 10
```

---

# Summary

| Deployment Type | Role Type | How to Get | Duration | Notes |
|-----------------|-----------|-----------|----------|-------|
| **Brownfield** | User-assumed | STS AssumeRole | 1 hour max | Must store long-term credentials securely |
| **Outpost** | Service role | Auto-assigned | N/A (role-based) | No manual credential handling |
| **Wavelength** | Service role | Auto-assigned | N/A (role-based) | Works like EC2 instances |
| **Local Zone** | Service role | Auto-assigned | N/A (role-based) | Works like regular EC2 |
| **Edge→Account B** | Service role + AssumeRole | Service role + STS | 1 hour | Combine both approaches |

---

## Key Takeaways

✅ **Brownfield servers**: Always use STS AssumeRole with short duration
✅ **Edge nodes**: Use auto-assigned service roles (no credentials needed)
✅ **Cross-account**: Combine service role + AssumeRole
✅ **Security**: Store brownfield credentials in Secrets Manager
✅ **Audit**: Enable CloudTrail on all AssumeRole calls
✅ **Rotation**: Rotate brownfield credentials every 90 days

