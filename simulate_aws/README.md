# LocalStack - Local AWS Cloud Simulation

This setup provides a complete local AWS cloud simulation using LocalStack, allowing you to develop and test AWS applications without connecting to the real AWS cloud.

## Supported Services

| Service | Description | Status |
|---------|-------------|--------|
| S3 | Object Storage | ✅ Full |
| SQS | Message Queuing | ✅ Full |
| SNS | Pub/Sub Messaging | ✅ Full |
| Lambda | Serverless Functions | ✅ Full |
| EC2 | Virtual Machines | ⚠️ Mocked |
| RDS | Relational Databases | ⚠️ Mocked |
| EMR | Big Data Processing | ⚠️ Mocked |
| IAM | Identity Management | ✅ Full |
| STS | Security Token Service | ✅ Full |
| CloudWatch | Monitoring | ✅ Full |

> **Note**: "Mocked" means the API works but doesn't provision actual resources.

## Prerequisites

- Docker Desktop installed and running
- Python 3.8+ (for boto3)
- AWS CLI (optional, for command-line access)

## docker desktop install
```shell
# 1. Install Docker Desktop
brew install --cask docker

# 2. Launch Docker Desktop (required before using docker commands)
open /Applications/Docker.app

# 3. Verify installation
docker --version
```

## Quick Start

### Step 1: Configure AWS Credentials

Create or update your AWS credentials file:

```bash
# Create AWS directory if it doesn't exist
mkdir -p ~/.aws

# Create credentials file
cat > ~/.aws/credentials << 'EOF'
[default]
aws_access_key_id = test
aws_secret_access_key = test
EOF

# Create config file
cat > ~/.aws/config << 'EOF'
[default]
region = us-east-1
output = json
EOF
```

### Step 2: Start LocalStack

```bash
# Navigate to this directory
cd localstack-aws

# Start LocalStack
docker-compose up -d

# Check status
docker-compose ps

# View logs (optional)
docker-compose logs -f
```

### Step 3: Verify LocalStack is Running

```bash
# Check health endpoint
curl http://localhost:4566/_localstack/health
```

### Step 4: Install Python Dependencies

```bash
pip install boto3
```

### Step 5: Test the Connection

```bash
python test_localstack.py
```

## Using with boto3 (Python)

### Option 1: Using endpoint_url (Recommended)

```python
import boto3

# Create client with LocalStack endpoint
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    # Uses default profile credentials automatically
)

# Use normally
s3.create_bucket(Bucket='my-bucket')
```

### Option 2: Using Environment Variables

Set these environment variables before running your code:

```bash
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

Then use boto3 normally:

```python
import boto3
s3 = boto3.client('s3')  # Will use environment variables
```

### Option 3: Create a Helper Module

Create `localstack_client.py`:

```python
import boto3
import os

LOCALSTACK_ENDPOINT = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')

def get_client(service_name, **kwargs):
    return boto3.client(
        service_name,
        endpoint_url=LOCALSTACK_ENDPOINT,
        **kwargs
    )

def get_resource(service_name, **kwargs):
    return boto3.resource(
        service_name,
        endpoint_url=LOCALSTACK_ENDPOINT,
        **kwargs
    )

# Usage:
# from localstack_client import get_client
# s3 = get_client('s3')
```

## Using AWS CLI with LocalStack

Install the AWS CLI LocalStack wrapper:

```bash
pip install awscli-local
```

Then use `awslocal` instead of `aws`:

```bash
# List S3 buckets
awslocal s3 ls

# Create a bucket
awslocal s3 mb s3://my-bucket

# Create SQS queue
awslocal sqs create-queue --queue-name my-queue

# List Lambda functions
awslocal lambda list-functions
```

Or use the standard AWS CLI with `--endpoint-url`:

```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Service Examples

### S3 Example

```python
import boto3

s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

# Create bucket
s3.create_bucket(Bucket='my-bucket')

# Upload file
s3.put_object(Bucket='my-bucket', Key='hello.txt', Body='Hello World!')

# Download file
response = s3.get_object(Bucket='my-bucket', Key='hello.txt')
print(response['Body'].read().decode())
```

### Lambda Example

```python
import boto3
import zipfile
import io

lambda_client = boto3.client('lambda', endpoint_url='http://localhost:4566')

# Create function code
code = '''
def handler(event, context):
    return {"message": "Hello from Lambda!"}
'''

# Package as zip
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w') as zf:
    zf.writestr('lambda_function.py', code)
zip_buffer.seek(0)

# Create function
lambda_client.create_function(
    FunctionName='my-function',
    Runtime='python3.9',
    Role='arn:aws:iam::000000000000:role/lambda-role',
    Handler='lambda_function.handler',
    Code={'ZipFile': zip_buffer.read()}
)

# Invoke function
response = lambda_client.invoke(FunctionName='my-function')
print(response['Payload'].read())
```

### SQS Example

```python
import boto3

sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')

# Create queue
response = sqs.create_queue(QueueName='my-queue')
queue_url = response['QueueUrl']

# Send message
sqs.send_message(QueueUrl=queue_url, MessageBody='Hello SQS!')

# Receive message
response = sqs.receive_message(QueueUrl=queue_url)
print(response['Messages'][0]['Body'])
```

## Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (reset all data)
docker-compose down -v

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Check status
docker-compose ps
```

## Troubleshooting

### LocalStack not starting

```bash
# Check Docker is running
docker ps

# Check LocalStack logs
docker-compose logs localstack

# Restart Docker Desktop and try again
```

### Connection refused errors

```bash
# Verify LocalStack is running
curl http://localhost:4566/_localstack/health

# Check if port 4566 is in use
lsof -i :4566
```

### Lambda functions not working

Make sure Docker socket is mounted correctly in docker-compose.yml:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### Reset everything

```bash
docker-compose down -v
docker-compose up -d
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICES` | Comma-separated list of services to enable | All |
| `DEBUG` | Enable debug logging (0 or 1) | 0 |
| `PERSISTENCE` | Persist data between restarts | 1 |
| `DEFAULT_REGION` | Default AWS region | us-east-1 |

## File Structure

```
localstack-aws/
├── docker-compose.yml      # Docker configuration
├── aws-credentials         # Template for ~/.aws/credentials
├── aws-config             # Template for ~/.aws/config
├── test_localstack.py     # Test script
├── init-scripts/          # Initialization scripts
│   └── init-resources.sh  # Creates default resources
└── README.md              # This file
```

## Useful Links

- [LocalStack Documentation](https://docs.localstack.cloud/)
- [LocalStack GitHub](https://github.com/localstack/localstack)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS CLI LocalStack](https://github.com/localstack/awscli-local)
