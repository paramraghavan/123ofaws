# AWS & Boto3 Troubleshooting Guide
## Fix Common Errors Fast

### Table of Contents
1. **Part 1: Common Errors** - Fix the most frequent problems
2. **Part 2: Service-Specific Issues** - Troubleshoot by AWS service
3. **Part 3: Debugging Techniques** - Find and fix hidden issues
4. **Part 4: Quick Reference** - Error codes and solutions

---

## PART 1: COMMON ERRORS

### NoCredentialsError

**Error Message**:
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**What It Means**: Boto3 can't find your AWS credentials.

**Solutions** (in order of preference):

#### Solution 1: Check Environment Variables
```bash
# On Mac/Linux
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# On Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY
```

If empty, set them:
```bash
# Mac/Linux
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="your-access-key"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key"
```

#### Solution 2: Check AWS Credentials File
```bash
# Credentials should be at:
# Mac/Linux: ~/.aws/credentials
# Windows: %USERPROFILE%\.aws\credentials

cat ~/.aws/credentials  # Mac/Linux
type %USERPROFILE%\.aws\credentials  # Windows
```

**File Format**:
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[production]
aws_access_key_id = PROD_ACCESS_KEY
aws_secret_access_key = PROD_SECRET_KEY
```

#### Solution 3: Create Credentials File
```bash
mkdir -p ~/.aws

cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
EOF

chmod 600 ~/.aws/credentials  # Secure file permissions
```

#### Solution 4: Use AWS CLI to Configure
```bash
aws configure

# Or configure specific profile
aws configure --profile production
```

#### Solution 5: Explicitly Pass Credentials
```python
import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='your-access-key',
    aws_secret_access_key='your-secret-key',
    region_name='us-east-1'
)
```

**⚠️ WARNING**: Never hardcode credentials in code. Use environment variables or credential files.

#### Solution 6: Check IAM Role (if on EC2/Lambda/ECS)
```python
import boto3
from botocore.exceptions import ClientError

# If you're on EC2, Lambda, or ECS, credentials come from IAM role
# Check the role is attached:

iam = boto3.client('iam')
try:
    # This will fail if no credentials at all
    response = iam.get_user()
    print(f"Current user: {response['User']['UserName']}")
except ClientError as e:
    print(f"Error: {e}")
```

**Verification Script**:
```python
import boto3

def check_credentials():
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"Account: {identity['Account']}")
        print(f"User/Role: {identity['Arn']}")
        print("✓ Credentials are valid")
        return True
    except Exception as e:
        print(f"✗ Credentials error: {e}")
        return False

check_credentials()
```

---

### AccessDenied

**Error Message**:
```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the GetObject operation: Access Denied
```

**What It Means**: Your credentials are valid, but you don't have permission for this operation.

**Root Cause**: IAM policy issue.

#### Debugging Steps

**Step 1: Verify You Can Access AWS**
```python
import boto3
from botocore.exceptions import ClientError

sts = boto3.client('sts')
try:
    identity = sts.get_caller_identity()
    print(f"You are: {identity['Arn']}")
except ClientError as e:
    print(f"Can't access AWS: {e}")
```

**Step 2: Check Specific Permission**
```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
try:
    # Try a simple operation
    response = s3.list_buckets()
    print(f"Can list buckets: {len(response['Buckets'])} found")
except ClientError as e:
    if e.response['Error']['Code'] == 'AccessDenied':
        print("Missing s3:ListAllMyBuckets permission")
    else:
        print(f"Error: {e}")
```

**Step 3: Use IAM Policy Simulator** (Web Console)
1. Go to [IAM Policy Simulator](https://policysim.aws.amazon.com/)
2. Enter your user/role ARN
3. Select service and action
4. See if it's allowed or denied

**Step 4: Check the Resource**
```python
# Sometimes the resource exists but you can't access it
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

try:
    # Try to access specific bucket
    response = s3.head_bucket(Bucket='someone-elses-bucket')
    print("Can access bucket")
except ClientError as e:
    error = e.response['Error']['Code']
    if error == 'AccessDenied':
        print("You don't have permission to access this bucket")
    elif error == '404':
        print("Bucket doesn't exist or is in another account")
except Exception as e:
    print(f"Unexpected error: {e}")
```

#### Common IAM Policy Gaps

**S3 Bucket Access Denied**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::my-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::my-bucket"
        }
    ]
}
```

**EC2 DescribeInstances Access Denied**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeImages",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeNetworkInterfaces"
            ],
            "Resource": "*"
        }
    ]
}
```

**Lambda InvokeFunction Access Denied**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:lambda:us-east-1:123456789:function:my-function"
        }
    ]
}
```

---

### ThrottlingException

**Error Message**:
```
botocore.exceptions.ClientError: An error occurred (ThrottlingException) when calling the PutMetricData operation: Rate exceeded
```

**What It Means**: You're making too many requests to AWS. The service limited you.

**Solutions**:

#### Solution 1: Enable Automatic Retries (Recommended)
```python
import boto3
from botocore.config import Config

# Let Boto3 handle retries automatically
config = Config(retries={'max_attempts': 3, 'mode': 'adaptive'})
cloudwatch = boto3.client('cloudwatch', config=config)

# Now automatic retries happen internally
cloudwatch.put_metric_data(Namespace='MyApp', MetricData=[...])
```

#### Solution 2: Manual Exponential Backoff
```python
import time
from botocore.exceptions import ClientError

def put_metric_with_backoff(cloudwatch, metric_data, max_retries=5):
    for attempt in range(max_retries):
        try:
            cloudwatch.put_metric_data(
                Namespace='MyApp',
                MetricData=metric_data
            )
            return  # Success
        except ClientError as e:
            if e.response['Error']['Code'] != 'ThrottlingException':
                raise  # Different error, re-raise

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                print(f"Throttled. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise  # Max retries exceeded

# Usage
try:
    put_metric_with_backoff(cloudwatch, [...])
except ClientError as e:
    print(f"Failed after all retries: {e}")
```

#### Solution 3: Add Delays Between Requests
```python
import time
import boto3

cloudwatch = boto3.client('cloudwatch')

metrics = [
    # ... your metrics ...
]

for metric in metrics:
    cloudwatch.put_metric_data(Namespace='MyApp', MetricData=[metric])
    time.sleep(0.1)  # 100ms between requests
```

#### Solution 4: Batch Requests
```python
# CloudWatch allows up to 20 metrics per request
# Don't make 100 requests for 100 metrics, make 5 requests for 20 each

import boto3

cloudwatch = boto3.client('cloudwatch')
metrics = [...]  # 100 metrics

# Batch into groups of 20
for i in range(0, len(metrics), 20):
    batch = metrics[i:i+20]
    cloudwatch.put_metric_data(Namespace='MyApp', MetricData=batch)
    print(f"Sent metrics {i} to {i+len(batch)}")
```

#### Solution 5: Use SQS for Async Batching
```python
import boto3
import json
from concurrent.futures import ThreadPoolExecutor

# Queue metrics for async processing
sqs = boto3.client('sqs')
cloudwatch = boto3.client('cloudwatch')

# Send messages to queue
for metric in metrics:
    sqs.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123/metrics-queue',
        MessageBody=json.dumps(metric)
    )

# Process queue with rate limiting
def process_metrics_batch():
    while True:
        response = sqs.receive_message(MaxNumberOfMessages=10)
        if 'Messages' not in response:
            break

        batch = []
        for msg in response['Messages']:
            metric = json.loads(msg['Body'])
            batch.append(metric)
            sqs.delete_message(
                QueueUrl='https://sqs.us-east-1.amazonaws.com/123/metrics-queue',
                ReceiptHandle=msg['ReceiptHandle']
            )

        if batch:
            cloudwatch.put_metric_data(Namespace='MyApp', MetricData=batch)
            time.sleep(1)  # Pause between batches
```

---

### NoSuchBucket (S3)

**Error Message**:
```
botocore.exceptions.ClientError: An error occurred (NoSuchBucket) when calling the GetObject operation
```

**What It Means**: The S3 bucket doesn't exist, or you're looking in the wrong region.

**Solutions**:

#### Solution 1: Verify Bucket Exists
```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

try:
    s3.head_bucket(Bucket='my-bucket')
    print("✓ Bucket exists")
except ClientError as e:
    error = e.response['Error']['Code']
    if error == '404':
        print("✗ Bucket doesn't exist")
    elif error == '403':
        print("✗ Bucket exists but you don't have permission")
    else:
        print(f"✗ Error: {error}")
```

#### Solution 2: List All Your Buckets
```python
s3 = boto3.client('s3')
response = s3.list_buckets()

print("Your buckets:")
for bucket in response['Buckets']:
    print(f"  - {bucket['Name']}")
```

#### Solution 3: Check Bucket Region
```python
import boto3
from botocore.exceptions import ClientError

s3_us_east = boto3.client('s3', region_name='us-east-1')
s3_eu = boto3.client('s3', region_name='eu-west-1')

bucket_name = 'my-bucket'

# Try different regions
for region in ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']:
    try:
        client = boto3.client('s3', region_name=region)
        client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket found in {region}")
        break
    except ClientError as e:
        if e.response['Error']['Code'] != '404':
            continue

# Or check bucket location directly
s3 = boto3.client('s3', region_name='us-east-1')
try:
    response = s3.get_bucket_location(Bucket=bucket_name)
    region = response['LocationConstraint'] or 'us-east-1'
    print(f"Bucket is in: {region}")
except ClientError as e:
    print(f"Can't find bucket: {e}")
```

#### Solution 4: Create Missing Bucket
```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3', region_name='us-east-1')

try:
    if s3.list_buckets()['Buckets']:
        # Check if our bucket exists
        bucket_exists = any(b['Name'] == 'my-bucket' for b in response['Buckets'])

    if not bucket_exists:
        s3.create_bucket(Bucket='my-bucket')
        print("✓ Bucket created")
except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
        print("Bucket already exists")
    else:
        print(f"Error: {e}")
```

---

### InvalidParameterValue

**Error Message**:
```
botocore.exceptions.ClientError: An error occurred (InvalidParameterValue) when calling the RunInstances operation: Invalid id: 'ami-invalid'
```

**What It Means**: A parameter value doesn't match AWS requirements.

**Common Parameter Issues**:

#### Wrong AMI ID
```python
import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')

# WRONG: Invalid format
try:
    response = ec2.run_instances(ImageId='my-image', MinCount=1, MaxCount=1)
except ClientError as e:
    print(f"✗ Error: {e}")

# RIGHT: Valid AMI format
try:
    response = ec2.run_instances(
        ImageId='ami-0c55b159cbfafe1f0',  # Correct format: ami-xxxxxxxxx
        MinCount=1,
        MaxCount=1
    )
except ClientError as e:
    # Check if AMI exists in this region
    print(f"Error: {e}")
```

#### Invalid Instance Type
```python
# WRONG
response = ec2.run_instances(
    ImageId='ami-12345',
    InstanceType='t2.huge'  # ❌ Invalid instance type
)

# RIGHT
response = ec2.run_instances(
    ImageId='ami-12345',
    InstanceType='t2.micro'  # ✓ Valid: micro, small, medium, large, xlarge
)
```

#### Invalid CIDR Block
```python
# WRONG
ec2.authorize_security_group_ingress(
    GroupId='sg-123',
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '192.168.1'}]  # ❌ Missing /24 notation
    }]
)

# RIGHT
ec2.authorize_security_group_ingress(
    GroupId='sg-123',
    IpPermissions=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '192.168.1.0/24'}]  # ✓ Valid CIDR
    }]
)
```

**Validation Script**:
```python
import re

def validate_ami_id(ami_id):
    if re.match(r'^ami-[a-z0-9]{8}$', ami_id) or re.match(r'^ami-[a-z0-9]{17}$', ami_id):
        return True
    return False

def validate_cidr(cidr):
    try:
        import ipaddress
        ipaddress.IPv4Network(cidr, strict=False)
        return True
    except:
        return False

def validate_instance_type(instance_type):
    valid_types = ['t2.micro', 't2.small', 't2.medium', 't2.large', 't3.micro', 't3.small']
    return instance_type in valid_types

# Test
print(validate_ami_id('ami-0c55b159cbfafe1f0'))  # True
print(validate_ami_id('ami-invalid'))            # False
print(validate_cidr('192.168.1.0/24'))           # True
print(validate_cidr('192.168.1'))                # False
print(validate_instance_type('t2.micro'))        # True
```

---

## PART 2: SERVICE-SPECIFIC ISSUES

### S3 Issues

#### Bucket Access Denied
```
AccessDenied: Access Denied
```

**Check IAM Policy**:
```python
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

# Step 1: Can you list buckets?
try:
    s3.list_buckets()
    print("✓ Can list buckets")
except ClientError as e:
    print(f"✗ Can't list buckets: {e}")

# Step 2: Can you access this specific bucket?
try:
    s3.head_bucket(Bucket='my-bucket')
    print("✓ Can access bucket")
except ClientError as e:
    print(f"✗ Can't access bucket: {e}")

# Step 3: Can you list bucket contents?
try:
    s3.list_objects_v2(Bucket='my-bucket')
    print("✓ Can list bucket contents")
except ClientError as e:
    print(f"✗ Can't list bucket: {e}")
```

**Required IAM Permissions**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::my-bucket"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::my-bucket/*"
        }
    ]
}
```

#### Multipart Upload Aborted
```
MultipartUploadError: Error uploading object
```

```python
import boto3

s3 = boto3.client('s3')

# Check for incomplete uploads
response = s3.list_multipart_uploads(Bucket='my-bucket')

if 'Uploads' in response:
    print(f"Found {len(response['Uploads'])} incomplete uploads:")
    for upload in response['Uploads']:
        print(f"  - {upload['Key']} (ID: {upload['UploadId']})")

    # Abort them to free up storage
    for upload in response['Uploads']:
        s3.abort_multipart_upload(
            Bucket='my-bucket',
            Key=upload['Key'],
            UploadId=upload['UploadId']
        )
        print(f"  Aborted: {upload['Key']}")
```

#### Large File Upload Failing
```python
# If you're uploading large files and getting errors:

import boto3
from botocore.config import Config

# Increase timeouts
config = Config(
    connect_timeout=60,
    read_timeout=60,
    retries={'max_attempts': 3, 'mode': 'adaptive'}
)

s3 = boto3.client('s3', config=config)

# Use multipart upload for files > 5GB
with open('/path/to/large/file', 'rb') as f:
    s3.upload_fileobj(f, 'my-bucket', 'large-file.zip')
```

### Lambda Issues

#### Function Not Found
```
ResourceNotFoundException: Function not found
```

```python
import boto3
from botocore.exceptions import ClientError

lambda_client = boto3.client('lambda')

# Check if function exists
try:
    response = lambda_client.get_function(FunctionName='my-function')
    print(f"✓ Function found: {response['Configuration']['FunctionName']}")
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print("✗ Function doesn't exist")
    else:
        print(f"✗ Error: {e}")

# List all functions
response = lambda_client.list_functions()
print("\nYour functions:")
for func in response['Functions']:
    print(f"  - {func['FunctionName']}")
```

#### Timeout Error
```
Lambda function timeout: Your Lambda function has timed out
```

```python
import boto3
from botocore.exceptions import ClientError

lambda_client = boto3.client('lambda')

# Check timeout setting
response = lambda_client.get_function(FunctionName='my-function')
timeout = response['Configuration']['Timeout']
print(f"Current timeout: {timeout} seconds")

# Increase timeout
lambda_client.update_function_configuration(
    FunctionName='my-function',
    Timeout=60  # Increase from default 3 seconds
)
print("Timeout increased to 60 seconds")

# Check memory (memory affects execution speed)
memory = response['Configuration']['MemorySize']
print(f"Current memory: {memory} MB")

# Increase memory (gets more CPU too)
lambda_client.update_function_configuration(
    FunctionName='my-function',
    MemorySize=512  # Increase from default 128
)
```

#### Permission Denied on Invoke
```
User: arn:aws:iam::xxx is not authorized to perform: lambda:InvokeFunction
```

**Add Permission**:
```python
lambda_client = boto3.client('lambda')

# Add permission for another AWS service to invoke
lambda_client.add_permission(
    FunctionName='my-function',
    StatementId='allow-s3-invoke',
    Action='lambda:InvokeFunction',
    Principal='s3.amazonaws.com',
    SourceArn='arn:aws:s3:::my-bucket'
)

# Add permission for another account
lambda_client.add_permission(
    FunctionName='my-function',
    StatementId='allow-cross-account',
    Action='lambda:InvokeFunction',
    Principal='arn:aws:iam::123456789:role/RemoteRole'
)
```

### EC2 Issues

#### Instance Fails to Launch
```
Failed to run instances
```

**Diagnostic Steps**:
```python
import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')

# Step 1: Verify AMI exists in this region
try:
    response = ec2.describe_images(ImageIds=['ami-123456'])
    if response['Images']:
        print(f"✓ AMI found: {response['Images'][0]['Name']}")
    else:
        print("✗ AMI not found in this region")
except ClientError as e:
    print(f"✗ AMI error: {e}")

# Step 2: Verify VPC and subnet exist
try:
    response = ec2.describe_subnets(SubnetIds=['subnet-123'])
    print(f"✓ Subnet found: {response['Subnets'][0]['SubnetId']}")
except ClientError as e:
    print(f"✗ Subnet error: {e}")

# Step 3: Verify security group exists
try:
    response = ec2.describe_security_groups(GroupIds=['sg-123'])
    print(f"✓ Security group found: {response['SecurityGroups'][0]['GroupId']}")
except ClientError as e:
    print(f"✗ Security group error: {e}")

# Step 4: Verify instance type is available
try:
    response = ec2.describe_instance_types(InstanceTypes=['t2.micro'])
    print(f"✓ Instance type available")
except ClientError as e:
    print(f"✗ Instance type error: {e}")
```

### RDS Issues

#### Can't Connect to Database
```
OperationalError: can't establish a connection
```

**Check Database Status**:
```python
import boto3
from botocore.exceptions import ClientError

rds = boto3.client('rds')

response = rds.describe_db_instances(DBInstanceIdentifier='my-db')
db = response['DBInstances'][0]

print(f"Status: {db['DBInstanceStatus']}")
print(f"Endpoint: {db['Endpoint']['Address']}")
print(f"Port: {db['Endpoint']['Port']}")

if db['DBInstanceStatus'] != 'available':
    print(f"⚠️  Database is {db['DBInstanceStatus']}, not available")

# Check security group
for sg in db['VpcSecurityGroups']:
    print(f"Security Group: {sg['VpcSecurityGroupId']} ({sg['Status']})")
```

**Test Connection with Proper Credentials**:
```bash
# For PostgreSQL
psql -h my-db.xxx.us-east-1.rds.amazonaws.com -p 5432 -U admin -d postgres

# For MySQL
mysql -h my-db.xxx.us-east-1.rds.amazonaws.com -u admin -p

# For Connection issues, check:
# 1. Database is in "available" state
# 2. Security group allows your IP on the port
# 3. Database username and password are correct
# 4. Database name exists (don't forget to create it)
```

---

## PART 3: DEBUGGING TECHNIQUES

### Enable Verbose Logging

#### Basic Logging
```python
import logging
import boto3

# Enable INFO level logging
logging.basicConfig(level=logging.INFO)

# Now all Boto3 calls show request/response info
s3 = boto3.client('s3')
response = s3.list_buckets()
```

#### Deep Debug Logging
```python
import logging
import boto3

# Enable DEBUG level (very verbose)
logging.basicConfig(level=logging.DEBUG)

# Or just for Boto3
logging.getLogger('boto3').setLevel(logging.DEBUG)
logging.getLogger('botocore').setLevel(logging.DEBUG)

s3 = boto3.client('s3')
response = s3.list_buckets()
# Now you see full HTTP requests/responses
```

**Output Example**:
```
DEBUG:botocore.endpoint:Response headers: {'x-amz-id-2': '...', 'x-amz-request-id': 'ABC123'}
DEBUG:botocore.parsers:Response body: b'<?xml version="1.0" encoding="UTF-8"?>\n<ListAllMyBucketsResult>...'
```

### CloudTrail Investigation

Track who did what and when:

```python
import boto3
from datetime import datetime, timedelta

cloudtrail = boto3.client('cloudtrail')

# Look up API calls from last hour
response = cloudtrail.lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'EventName',
            'AttributeValue': 'PutObject'  # Find all S3 uploads
        }
    ],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    MaxResults=50
)

print("Recent S3 uploads:")
for event in response['Events']:
    print(f"  - {event['EventName']} by {event['Username']}")
    print(f"    Time: {event['EventTime']}")
    print(f"    Resource: {event['Resources']}")
```

### IAM Policy Simulator

Test if a policy allows an action:

```python
import boto3

iam = boto3.client('iam')

# Simulate whether user can perform action
response = iam.simulate_principal_policy(
    PolicySourceArn='arn:aws:iam::123456789:user/my-user',
    ActionNames=['s3:GetObject', 's3:PutObject'],
    ResourceArns=['arn:aws:s3:::my-bucket/file.txt']
)

for result in response['EvaluationResults']:
    action = result['EvalActionName']
    verdict = result['EvalDecision']
    print(f"  {action}: {verdict}")
    if 'EvalResourceName' in result:
        print(f"    Resource: {result['EvalResourceName']}")
```

### AWS CLI Testing

Sometimes easier than Python:

```bash
# Test S3 access
aws s3 ls --debug 2>&1 | grep "Error\|response"

# Test Lambda invocation
aws lambda invoke --function-name my-function response.json --debug

# Test IAM permissions
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::123456789:user/myuser \
    --action-names s3:GetObject \
    --resource-arns arn:aws:s3:::my-bucket/*

# Test EC2 access
aws ec2 describe-instances --debug 2>&1 | head -20
```

### Use LocalStack for Local Testing

Test without hitting real AWS:

```bash
# Install LocalStack
pip install localstack

# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Use LocalStack endpoint
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Now test locally
aws s3 mb s3://my-bucket
```

```python
import boto3

# Test with LocalStack
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

# Create bucket in LocalStack (not real AWS!)
s3.create_bucket(Bucket='test-bucket')
response = s3.list_buckets()
print(f"LocalStack buckets: {response['Buckets']}")
```

---

## PART 4: QUICK REFERENCE

### Error Code to Solution Map

| Error Code | Service | Cause | Solution |
|-----------|---------|-------|----------|
| NoCredentialsError | All | Credentials not found | Check AWS_ACCESS_KEY_ID, ~/.aws/credentials |
| AccessDenied | All | No permission | Check IAM policy, use IAM simulator |
| ThrottlingException | All | Too many requests | Enable auto-retries, add delays, batch requests |
| InvalidParameterValue | All | Bad parameter | Check AWS docs, validate parameter format |
| NoSuchBucket | S3 | Bucket doesn't exist | Verify bucket name, check region, list buckets |
| NoSuchKey | S3 | Object doesn't exist | Check object path, list bucket contents |
| BucketAlreadyExists | S3 | Can't create bucket | Use different name, bucket names are global |
| InvalidBucketName | S3 | Invalid bucket name | Use lowercase, alphanumeric + hyphens only |
| EntityAlreadyExists | IAM | Resource exists | Delete first or choose different name |
| NoSuchEntity | IAM | Resource not found | Verify ARN, list resources, check region |
| InvalidInstanceID.NotFound | EC2 | Instance doesn't exist | Check instance ID, verify region |
| InvalidParameterValue | EC2 | Invalid parameter | Check instance type, AMI ID, CIDR format |
| SecurityGroupLimitExceeded | EC2 | Too many security groups | Delete unused groups |
| InsufficientInstanceCapacity | EC2 | Can't launch instance | Try different AZ, instance type, or retry |
| DBInstanceNotFound | RDS | Database doesn't exist | Check database name, verify region |
| DBInstanceAlreadyExists | RDS | Can't create database | Delete first or choose different name |
| InvalidDBInstanceIdentifier | RDS | Invalid database name | Use alphanumeric + hyphens, 1-63 characters |
| ResourceNotFoundException | Lambda | Function not found | Check function name, list functions, verify region |
| InvalidParameterValueException | Lambda | Invalid parameter | Check timeout (1-900), memory (128-10240) |
| CodeVerificationFailed | Lambda | Code invalid | Check ZIP format, handler exists |
| InvalidFunctionNameException | Lambda | Invalid function name | Use alphanumeric + hyphens, 1-64 characters |

### Quick Debugging Checklist

```
[ ] 1. Verify AWS credentials
      - export AWS_ACCESS_KEY_ID
      - export AWS_SECRET_ACCESS_KEY
      - Check ~/.aws/credentials

[ ] 2. Verify AWS region
      - export AWS_DEFAULT_REGION=us-east-1
      - Check resource is in same region

[ ] 3. Verify IAM permissions
      - Use IAM policy simulator
      - Check IAM policy attached to user/role
      - Verify resource ARN in policy

[ ] 4. Verify resource exists
      - List resources (list_buckets, describe_instances, etc.)
      - Check resource name and ID
      - Verify resource in correct region

[ ] 5. Verify parameters
      - Check parameter format (AMI ID, CIDR, etc.)
      - Check parameter values match AWS requirements
      - Consult AWS documentation

[ ] 6. Enable logging
      - Set logging.basicConfig(level=logging.DEBUG)
      - Check Boto3 debug output
      - Check CloudTrail logs

[ ] 7. Check service status
      - Verify resource status (available, running, etc.)
      - Check CloudWatch alarms
      - Check CloudTrail for errors
```

---

## Key Takeaways

1. **Credentials**: 99% of errors start here. Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY first.
2. **IAM**: If credentials are valid but access denied, check IAM policy.
3. **Region**: Resource not found? Maybe it's in a different region.
4. **Parameters**: Invalid parameter? Check AWS documentation for exact format.
5. **Logging**: Enable debug logging to see actual HTTP requests/responses.
6. **Testing**: Use LocalStack to test locally before deploying.
7. **Patterns**: Enable auto-retries, batch requests, add delays for throttling.

---

**Last Updated**: 2024
**Target Audience**: AWS developers debugging issues
**Estimated Reading Time**: 1-2 hours reference guide
