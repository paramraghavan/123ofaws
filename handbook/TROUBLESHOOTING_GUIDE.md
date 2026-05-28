# AWS Boto3 Troubleshooting Guide: Fix Errors Fast

> **Fast solutions to common AWS errors**: This guide covers 25+ error messages with multiple solutions for each. Organized by error type and service.

---

## Table of Contents

### PART 1: AUTHENTICATION & CREDENTIALS (Top 10 Errors)
- NoCredentialsError
- InvalidSignatureException
- AccessDenied
- ExpiredToken
- InvalidClientTokenId

### PART 2: COMMON SERVICE ERRORS (Top 15 Errors)
- S3 Errors
- Lambda Errors
- EC2 Errors
- RDS Errors
- CloudWatch Errors

### PART 3: DEBUGGING TECHNIQUES
- Enable Debug Logging
- Using CloudTrail
- IAM Policy Simulator
- AWS CLI Testing

---

# PART 1: AUTHENTICATION & CREDENTIALS

## Error 1: NoCredentialsError

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

### What it means
Boto3 cannot find AWS credentials to authenticate API calls.

### Root causes
1. No AWS credentials configured
2. Credentials expired
3. Wrong credentials location
4. Environment variables not set
5. IAM role not attached to EC2/Lambda

### Solution 1: Configure AWS CLI (Easiest)

```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure with your credentials
aws configure

# Prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (us-east-1)
# - Default output format (json)

# Verify it works
aws s3 ls
```

### Solution 2: Set Environment Variables

```bash
# Set credentials as environment variables
export AWS_ACCESS_KEY_ID='your_access_key_here'
export AWS_SECRET_ACCESS_KEY='your_secret_key_here'
export AWS_DEFAULT_REGION='us-east-1'

# Verify in Python
import boto3
s3 = boto3.client('s3')
print(s3.list_buckets())
```

### Solution 3: Hardcode in Code (Development Only!)

```python
import boto3

# ⚠️ NEVER DO THIS IN PRODUCTION
# Only for local development and testing
s3 = boto3.client(
    's3',
    aws_access_key_id='your_access_key',
    aws_secret_access_key='your_secret_key',
    region_name='us-east-1'
)

print(s3.list_buckets())
```

### Solution 4: Use IAM Role (Recommended for EC2/Lambda)

```python
import boto3

# When running on EC2 or Lambda, use the attached IAM role
# No credentials needed - AWS SDK auto-detects the role
s3 = boto3.client('s3')  # Just works!

print(s3.list_buckets())

# Or explicitly request credentials from role
sts = boto3.client('sts')
response = sts.get_caller_identity()
print(f"Account: {response['Account']}")
print(f"ARN: {response['Arn']}")
```

### Solution 5: Use Named Profile

```bash
# If you have multiple AWS accounts/profiles
# First, configure profile
aws configure --profile production

# Then use in Python
import boto3
from boto3 import Session

session = Session(profile_name='production')
s3 = session.client('s3')
print(s3.list_buckets())
```

### Verification Checklist

```bash
# 1. Check credentials file exists
cat ~/.aws/credentials

# 2. Check config file exists
cat ~/.aws/config

# 3. Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# 4. Test with AWS CLI
aws sts get-caller-identity

# 5. Test in Python
python3 -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

---

## Error 2: InvalidSignatureException

```
botocore.exceptions.ClientError: An error occurred (InvalidSignature) when calling
the [...] operation: The request signature we calculated does not match the signature
you provided. Check your key and signing method.
```

### What it means
Your credentials are being rejected. Usually wrong credentials or they've changed.

### Root causes
1. Wrong AWS secret access key
2. Credentials were recently rotated
3. Using credentials from wrong account
4. Clock skew (system time is very wrong)
5. Credentials have spaces or special characters

### Solution 1: Rotate Credentials

```bash
# Generate new credentials from AWS Console
# Then update credentials file
aws configure

# Or update environment variables
export AWS_ACCESS_KEY_ID='new_access_key'
export AWS_SECRET_ACCESS_KEY='new_secret_key'

# Test
aws sts get-caller-identity
```

### Solution 2: Check System Time

```bash
# Server time must be within 5 minutes of AWS time
# If off, it will cause signature errors

# Check current time
date

# Mac: Sync time
# Settings > Date & Time > Sync Now

# Linux: Sync time
sudo ntpdate -s time.nist.gov
# or
timedatectl set-ntp on

# Docker: Ensure correct timezone/time
# In docker-compose.yml:
# environment:
#   - TZ=UTC
```

### Solution 3: Verify Credentials Format

```python
import boto3
import os

# Check if credentials have invisible characters
access_key = os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()

print(f"Access Key: '{access_key}' (len={len(access_key)})")
print(f"Secret Key length: {len(secret_key)}")

# Access key should be 20 chars like: AKIAIOSFODNN7EXAMPLE
# Secret key should be 40 chars

if len(access_key) != 20:
    print("⚠️  Access key has wrong length!")
if len(secret_key) != 40:
    print("⚠️  Secret key has wrong length!")
```

### Solution 4: Use Different Account

```python
import boto3

# If you have multiple accounts, ensure you're using correct credentials
sts = boto3.client('sts')

try:
    response = sts.get_caller_identity()
    account_id = response['Account']
    arn = response['Arn']
    print(f"Using account: {account_id}")
    print(f"ARN: {arn}")

    # Check if this is the account you intended
    if account_id != '123456789':  # Your expected account
        print("⚠️  Wrong account!")

except Exception as e:
    print(f"Error: {e}")
```

---

## Error 3: AccessDenied / UnauthorizedOperation

```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling
the [...] operation: User: arn:aws:iam::123456789:user/john is not authorized
to perform: s3:GetObject on resource: arn:aws:s3:::my-bucket/data.csv
```

### What it means
Your credentials are valid, but you don't have permission for this operation.

### Root causes
1. IAM policy doesn't allow this operation
2. Resource-based policy denies access
3. Missing KMS key permissions (for encrypted resources)
4. Bucket policy is too restrictive
5. SCP (Service Control Policy) blocks operation

### Solution 1: Check IAM Policy

```python
import boto3
from botocore.exceptions import ClientError

iam = boto3.client('iam')

# Get current user
sts = boto3.client('sts')
user_arn = sts.get_caller_identity()['Arn']
username = user_arn.split('/')[-1]

print(f"Checking policies for: {username}")

# List attached policies
response = iam.list_attached_user_policies(UserName=username)
print(f"Attached policies:")
for policy in response['AttachedPolicies']:
    print(f"  - {policy['PolicyName']}")

# List inline policies
response = iam.list_user_policies(UserName=username)
print(f"Inline policies:")
for policy in response['PolicyNames']:
    print(f"  - {policy}")
```

### Solution 2: Add Required Permissions

```python
import boto3
import json

iam = boto3.client('iam')

# Define policy with required permissions
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "arn:aws:kms:us-east-1:123456789:key/12345678-1234"
        }
    ]
}

# Attach to user
iam.put_user_policy(
    UserName='john',
    PolicyName='S3Access',
    PolicyDocument=json.dumps(policy_document)
)

print("Policy attached. Changes take effect immediately.")
```

### Solution 3: Use IAM Policy Simulator

```python
import boto3
import json

iam = boto3.client('iam')

# Simulate permission
response = iam.simulate_principal_policy(
    PolicySourceArn='arn:aws:iam::123456789:user/john',
    ActionNames=['s3:GetObject'],
    ResourceArns=['arn:aws:s3:::my-bucket/data.csv']
)

print("Permission simulation results:")
for result in response['EvaluationResults']:
    action = result['EvalActionName']
    decision = result['EvalDecision']  # allowed, implicitDeny, explicitDeny
    print(f"{action}: {decision}")

    if decision != 'allowed':
        print(f"  Reason: {result.get('EvalResourceName', 'N/A')}")
```

### Solution 4: Check S3 Bucket Policy

```python
import boto3
import json

s3 = boto3.client('s3')

# Get bucket policy
try:
    response = s3.get_bucket_policy(Bucket='my-bucket')
    policy = json.loads(response['Policy'])
    print("Bucket policy:")
    print(json.dumps(policy, indent=2))

except s3.exceptions.NoSuchBucketPolicy:
    print("No bucket policy set")

# Check bucket ACL
response = s3.get_bucket_acl(Bucket='my-bucket')
print(f"Owner: {response['Owner']['DisplayName']}")
print(f"Grants: {response['Grants']}")
```

### Solution 5: Check KMS Key Permissions

```python
import boto3

kms = boto3.client('kms')

# List key policies
key_id = 'arn:aws:kms:us-east-1:123456789:key/12345678'

response = kms.get_key_policy(KeyId=key_id, PolicyName='default')
import json
policy = json.loads(response['Policy'])
print("KMS Key policy:")
print(json.dumps(policy, indent=2))
```

---

## Error 4: ExpiredToken

```
botocore.exceptions.ClientError: An error occurred (ExpiredToken) when calling
the [...] operation: The provided token has expired.
```

### What it means
Your temporary credentials (from STS) have expired.

### Root causes
1. STS credentials older than 1 hour
2. AssumeRole credentials exceeded max duration
3. Federation token expired
4. Session token invalid

### Solution 1: Refresh Credentials

```python
import boto3
from boto3 import Session
from datetime import datetime

# Check current credentials
sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(f"Current user: {identity['Arn']}")

# If using temporary credentials from AssumeRole
# they are automatically refreshed by boto3

# If using federation, request new credentials
sts = boto3.client('sts')
response = sts.assume_role(
    RoleArn='arn:aws:iam::123456789:role/MyRole',
    RoleSessionName='session-name'
)

credentials = response['Credentials']
print(f"New credentials valid until: {credentials['Expiration']}")

# Create new session with fresh credentials
session = Session(
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)

s3 = session.client('s3')
```

### Solution 2: Increase Token Duration

```python
import boto3

sts = boto3.client('sts')

# Request longer-lived credentials (max 12 hours)
response = sts.assume_role(
    RoleArn='arn:aws:iam::123456789:role/MyRole',
    RoleSessionName='long-running-job',
    DurationSeconds=43200  # 12 hours (max)
)

credentials = response['Credentials']
expiration = credentials['Expiration']
print(f"Credentials valid until: {expiration}")
```

### Solution 3: Check Credential Expiration

```python
import boto3
from datetime import datetime, timedelta
import os

# Check if environment credentials are about to expire
from botocore.session import get_session

session = get_session()
credentials = session.get_credentials()

if credentials and hasattr(credentials, '_expiry_time'):
    expiry = credentials._expiry_time
    now = datetime.utcnow()
    remaining = expiry - now

    print(f"Credentials expire in: {remaining}")

    if remaining < timedelta(minutes=5):
        print("⚠️  Credentials expiring soon!")
else:
    print("Using long-term credentials (don't expire)")
```

---

# PART 2: COMMON SERVICE ERRORS

## S3 Errors

### Error: NoSuchBucket

```
botocore.exceptions.ClientError: An error occurred (NoSuchBucket) when calling
the HeadBucket operation: The specified bucket does not exist
```

**Solutions:**

```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

# Solution 1: Check if bucket exists
def bucket_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404' or error_code == 'NoSuchBucket':
            return False
        raise

if not bucket_exists('my-bucket'):
    print("Bucket doesn't exist, creating...")
    s3.create_bucket(Bucket='my-bucket')

# Solution 2: List all available buckets
response = s3.list_buckets()
available_buckets = [b['Name'] for b in response['Buckets']]
print(f"Available buckets: {available_buckets}")

# Solution 3: Check bucket name for typos
bucket_to_check = 'my-buckét'  # Wrong
correct_bucket = 'my-bucket'   # Right
```

### Error: NoSuchKey

```
botocore.exceptions.ClientError: An error occurred (NoSuchKey) when calling
the GetObject operation: The specified key does not exist.
```

**Solutions:**

```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

# Solution 1: Check if object exists
def object_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise

if not object_exists('my-bucket', 'file.txt'):
    print("Object doesn't exist")
    # Upload it first
    s3.put_object(Bucket='my-bucket', Key='file.txt', Body=b'content')

# Solution 2: List objects in bucket to find correct key
response = s3.list_objects_v2(Bucket='my-bucket', Prefix='data/')
print("Objects in bucket:")
for obj in response.get('Contents', []):
    print(f"  {obj['Key']}")

# Solution 3: Check key format (case-sensitive!)
wrong_key = 'File.TXT'    # Wrong
correct_key = 'file.txt'  # Right
```

### Error: AccessDenied (S3)

**Solutions:**

```python
import boto3
import json

s3 = boto3.client('s3')

# Solution 1: Check bucket permissions
def check_s3_permissions(bucket):
    try:
        # Try to read bucket
        s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        print("✓ ListBucket permission OK")
    except Exception as e:
        print(f"✗ ListBucket permission denied: {e}")

    try:
        # Try to read an object (any)
        s3.get_object(Bucket=bucket, Key='test.txt')
        print("✓ GetObject permission OK")
    except Exception:
        print("✗ GetObject permission denied")

# Solution 2: Check bucket policy
response = s3.get_bucket_policy(Bucket='my-bucket')
policy = json.loads(response['Policy'])
print(json.dumps(policy, indent=2))

# Solution 3: Check if bucket is encrypted
response = s3.get_bucket_encryption(Bucket='my-bucket')
encryption = response.get('ServerSideEncryptionConfiguration', {})
if encryption:
    print("Bucket is encrypted with:", encryption)
    print("You may need KMS key permissions")
```

---

## Lambda Errors

### Error: InvalidParameterValueException

```
botocore.exceptions.ClientError: An error occurred (InvalidParameterValueException)
when calling the CreateFunction operation: The role defined for the function cannot
be assumed by Lambda.
```

**Solutions:**

```python
import boto3
import json

lambda_client = boto3.client('lambda')
iam = boto3.client('iam')

# Solution 1: Verify IAM role exists and has trust relationship
role_name = 'lambda-execution-role'

try:
    response = iam.get_role(RoleName=role_name)
    role_arn = response['Role']['Arn']
    print(f"Role ARN: {role_arn}")

except iam.exceptions.NoSuchEntityException:
    print(f"Role {role_name} doesn't exist")
    print("Creating role...")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }

    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Execution role for Lambda functions'
    )

    # Attach basic Lambda policy
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )

# Solution 2: Check trust policy
response = iam.get_role(RoleName=role_name)
trust_policy = response['Role']['AssumeRolePolicyDocument']
print("Trust policy:")
print(json.dumps(trust_policy, indent=2))

# Should have: "Service": "lambda.amazonaws.com"
```

### Error: ResourceNotFoundException

```
botocore.exceptions.ClientError: An error occurred (ResourceNotFoundException)
when calling the GetFunction operation: The resource you requested does not exist.
```

**Solutions:**

```python
import boto3

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Solution 1: Check if function exists
def function_exists(function_name):
    try:
        lambda_client.get_function(FunctionName=function_name)
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        return False

if not function_exists('my-function'):
    print("Function doesn't exist")
    print("Creating function...")
    # Create it

# Solution 2: List all Lambda functions
response = lambda_client.list_functions()
functions = [f['FunctionName'] for f in response['Functions']]
print(f"Available functions: {functions}")

# Solution 3: Check if you're in correct region
print(f"Current region: {lambda_client.meta.region_name}")
print("Function might be in a different region")
```

### Error: CodeStorageExceededException

```
botocore.exceptions.ClientError: An error occurred (CodeStorageExceededException)
when calling the CreateFunction operation: An error occurred (CodeStorageExceededException)
when calling the CreateFunction operation: Your total code size is [...] bytes,
which exceeds the account limit of [...]
```

**Solutions:**

```python
import boto3

lambda_client = boto3.client('lambda')

# Solution 1: Check current code storage usage
response = lambda_client.get_account_settings()
code_size_limit = response['AccountUsage']['CodeStorageInBytes']
code_size_used = response['AccountUsage'].get('CodeStorageInBytes', 0)

print(f"Code storage limit: {code_size_limit / 1024 / 1024 / 1024:.2f} GB")
print(f"Code storage used: {code_size_used / 1024 / 1024 / 1024:.2f} GB")

# Solution 2: Delete unused Lambda functions
response = lambda_client.list_functions()
functions = response['Functions']

# Sort by last modified
functions.sort(key=lambda x: x['LastModified'])

print("Functions (oldest first):")
for f in functions:
    size_mb = f['CodeSize'] / 1024 / 1024
    print(f"  {f['FunctionName']}: {size_mb:.2f} MB (Modified: {f['LastModified']})")

# Delete old functions
lambda_client.delete_function(FunctionName='old-function')

# Solution 3: Reduce function package size
# - Remove unnecessary dependencies
# - Use Lambda Layers for shared code
# - Use AWS Lambda extensions for tools
```

---

## EC2 Errors

### Error: InsufficientInstanceCapacity

```
botocore.exceptions.ClientError: An error occurred (InsufficientInstanceCapacity)
when calling the RunInstances operation: We currently do not have sufficient
capacity in the Availability Zone to service your request.
```

**Solutions:**

```python
import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

# Solution 1: Try different availability zone
# Launch in multiple AZs
azs = ['us-east-1a', 'us-east-1b', 'us-east-1c']

for az in azs:
    try:
        response = ec2.run_instances(
            ImageId='ami-0c55b159cbfafe1f0',
            MinCount=1,
            MaxCount=1,
            InstanceType='t3.micro',
            Placement={'AvailabilityZone': az}
        )
        print(f"✓ Launched in {az}")
        break
    except Exception as e:
        print(f"✗ Failed in {az}: {e}")
        continue

# Solution 2: Try different instance type
instance_types = ['t3.micro', 't3.small', 't2.micro', 't2.small']

for inst_type in instance_types:
    try:
        response = ec2.run_instances(
            ImageId='ami-0c55b159cbfafe1f0',
            MinCount=1,
            MaxCount=1,
            InstanceType=inst_type
        )
        print(f"✓ Launched with instance type {inst_type}")
        break
    except Exception as e:
        print(f"✗ Failed with {inst_type}: {e}")
        continue

# Solution 3: Wait and retry
import time
for attempt in range(5):
    try:
        response = ec2.run_instances(
            ImageId='ami-0c55b159cbfafe1f0',
            MinCount=1,
            MaxCount=1,
            InstanceType='t3.micro'
        )
        print("✓ Instance launched")
        break
    except Exception as e:
        wait_time = 2 ** attempt
        print(f"Attempt {attempt + 1} failed, waiting {wait_time}s...")
        time.sleep(wait_time)
```

---

## RDS Errors

### Error: DBInstanceAlreadyExists

```
botocore.exceptions.ClientError: An error occurred (DBInstanceAlreadyExists)
when calling the CreateDBInstance operation: [...]
```

**Solutions:**

```python
import boto3

rds = boto3.client('rds', region_name='us-east-1')

# Solution 1: Check if instance exists
def db_instance_exists(db_instance_id):
    try:
        rds.describe_db_instances(DBInstanceIdentifier=db_instance_id)
        return True
    except rds.exceptions.DBInstanceNotFoundFault:
        return False

if db_instance_exists('mydb'):
    print("Database already exists")
    # Either use it or delete and recreate
    response = rds.describe_db_instances(DBInstanceIdentifier='mydb')
    print(f"Endpoint: {response['DBInstances'][0]['Endpoint']}")
else:
    print("Creating new database...")
    # Create it

# Solution 2: List all databases
response = rds.describe_db_instances()
databases = [db['DBInstanceIdentifier'] for db in response['DBInstances']]
print(f"Existing databases: {databases}")

# Solution 3: Delete old instance first (careful!)
print("Deleting old database...")
rds.delete_db_instance(
    DBInstanceIdentifier='old-db',
    SkipFinalSnapshot=True  # Don't create snapshot
)
```

---

## CloudWatch Errors

### Error: InvalidParameterValue

```
botocore.exceptions.ClientError: An error occurred (InvalidParameterValue)
when calling the PutMetricAlarm operation: [...]
```

**Solutions:**

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Solution 1: Verify all required parameters
try:
    cloudwatch.put_metric_alarm(
        AlarmName='my-alarm',
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Statistic='Average',
        Period=300,
        EvaluationPeriods=2,
        Threshold=80.0,
        ComparisonOperator='GreaterThanThreshold',
        # Missing AlarmActions or TreatMissingData
    )
except Exception as e:
    print(f"Error: {e}")

# Solution 2: Add all required parameters
cloudwatch.put_metric_alarm(
    AlarmName='my-alarm',
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',  # Must be: SampleCount, Average, Sum, Minimum, Maximum
    Period=60,  # Must be multiple of 60
    EvaluationPeriods=1,
    Threshold=80.0,
    ComparisonOperator='GreaterThanThreshold',  # GreaterThan, LessThan, GreaterThanOrEqualTo, etc.
    AlarmActions=['arn:aws:sns:us-east-1:123456789:topic'],
    TreatMissingData='notBreaching'  # breaching, notBreaching, missing
)

print("✓ Alarm created")
```

---

# PART 3: DEBUGGING TECHNIQUES

## Technique 1: Enable Debug Logging

```python
import boto3
import logging

# Enable debug logging for boto3
boto3.set_stream_logger(
    name='botocore',
    level=logging.DEBUG
)

# Now all AWS API calls will be logged with full details
s3 = boto3.client('s3')
response = s3.list_buckets()

# Output will show:
# - Exact API request
# - Request headers
# - Response headers
# - Full response body
```

### Selective Debug Logging

```python
import logging

# Create logger for specific service
logging.basicConfig(level=logging.DEBUG)

# Debug only S3
boto3.set_stream_logger('botocore.s3', logging.DEBUG)

# Debug only EC2
boto3.set_stream_logger('botocore.ec2', logging.DEBUG)

# This is useful when dealing with large responses
```

---

## Technique 2: Test with AWS CLI First

```bash
# Many Boto3 errors can be reproduced with AWS CLI first
# This helps isolate if it's a permission issue vs code issue

# Test S3 access
aws s3 ls

# Test specific operation
aws s3 cp test.txt s3://my-bucket/test.txt

# With debug output
aws s3 ls --debug

# Check credentials being used
aws sts get-caller-identity

# List all resources of a type
aws ec2 describe-instances
aws rds describe-db-instances
```

---

## Technique 3: Use IAM Access Analyzer

```python
import boto3
import json

iam = boto3.client('iam')
access_analyzer = boto3.client('accessanalyzer')

# Find out what permissions you actually have
sts = boto3.client('sts')
user_arn = sts.get_caller_identity()['Arn']

# List all policies
iam = boto3.client('iam')
response = iam.list_attached_user_policies(
    UserName=user_arn.split('/')[-1]
)

print("Attached policies:")
for policy in response['AttachedPolicies']:
    print(f"  - {policy['PolicyName']}")

    # Get policy document
    policy_version = iam.get_policy(PolicyArn=policy['PolicyArn'])
    policy_doc = iam.get_policy_version(
        PolicyArn=policy['PolicyArn'],
        VersionId=policy_version['Policy']['DefaultVersionId']
    )

    statements = policy_doc['PolicyVersion']['Document']['Statement']
    for stmt in statements:
        if stmt['Effect'] == 'Allow':
            actions = stmt.get('Action', [])
            resources = stmt.get('Resource', [])
            print(f"    Actions: {actions}")
            print(f"    Resources: {resources}")
```

---

## Technique 4: Use botocore Event System

```python
import boto3
from botocore.hooks import EventAliasMapping

# Register event handlers to see all API calls
def log_api_call(event_name=None, **kwargs):
    print(f"Event: {event_name}")
    if 'request' in kwargs:
        print(f"  URL: {kwargs['request'].url}")
        print(f"  Method: {kwargs['request'].method}")
        print(f"  Headers: {dict(kwargs['request'].headers)}")

s3 = boto3.client('s3')

# Register before every API call
s3.meta.events.register('before-call', log_api_call)
s3.meta.events.register('after-call', log_api_call)

# Now test
response = s3.list_buckets()
```

---

## Technique 5: Wrap API Calls with Timing

```python
import boto3
import time
from functools import wraps

def time_api_calls(func):
    """Decorator to time AWS API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            print(f"✓ {func.__name__} took {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            print(f"✗ {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Usage
s3 = boto3.client('s3')

@time_api_calls
def list_all_buckets():
    return s3.list_buckets()

@time_api_calls
def list_bucket_objects(bucket):
    return s3.list_objects_v2(Bucket=bucket, MaxKeys=1000)

buckets = list_all_buckets()
for bucket in buckets['Buckets']:
    list_bucket_objects(bucket['Name'])
```

---

## Quick Error Reference Table

| Error | Cause | Fix |
|-------|-------|-----|
| NoCredentialsError | No AWS credentials | Run `aws configure` |
| InvalidSignatureException | Wrong credentials | Check access key/secret key |
| AccessDenied | Missing permissions | Check IAM policy |
| NoSuchBucket | Bucket doesn't exist | Create bucket or check name |
| NoSuchKey | Object doesn't exist | Upload object or check key |
| InsufficientInstanceCapacity | AWS can't provide capacity | Try different AZ or instance type |
| DBInstanceAlreadyExists | DB already exists | Delete first or use different name |
| InvalidParameterValueException | Missing/wrong parameters | Check all required parameters |
| ThrottlingException | Too many API calls | Implement backoff/retry logic |
| RequestLimitExceeded | Rate limit exceeded | Wait and retry with exponential backoff |

---

## Best Practices for Avoiding Errors

1. **Always handle ClientError**
   ```python
   from botocore.exceptions import ClientError
   try:
       # AWS operation
   except ClientError as e:
       # Check error_code and handle appropriately
   ```

2. **Check existence before operations**
   ```python
   if bucket_exists(bucket_name):
       # Proceed
   ```

3. **Use waiters for state changes**
   ```python
   waiter = ec2.get_waiter('instance_running')
   waiter.wait(InstanceIds=['i-1234'])
   ```

4. **Implement retry logic**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential())
   def call_aws():
       # AWS operation
   ```

5. **Log everything in production**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"Starting operation: {operation_name}")
   ```

6. **Test with AWS CLI first**
   ```bash
   aws s3 ls  # Before writing Python code
   ```

