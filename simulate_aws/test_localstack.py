#!/usr/bin/env python3
"""
Test script for connecting to LocalStack using boto3 with default profile.
This script tests various AWS services running on LocalStack.
"""

import boto3
import json
from botocore.config import Config

# LocalStack endpoint
LOCALSTACK_ENDPOINT = "http://localhost:4566"

def get_client(service_name):
    """Create a boto3 client configured for LocalStack."""
    return boto3.client(
        service_name,
        endpoint_url=LOCALSTACK_ENDPOINT,
        # Uses 'default' profile from ~/.aws/credentials
        # aws_access_key_id and aws_secret_access_key come from profile
    )

def get_resource(service_name):
    """Create a boto3 resource configured for LocalStack."""
    return boto3.resource(
        service_name,
        endpoint_url=LOCALSTACK_ENDPOINT,
    )

def test_s3():
    """Test S3 operations."""
    print("\n" + "="*50)
    print("Testing S3...")
    print("="*50)
    
    s3 = get_client('s3')
    
    # Create bucket
    bucket_name = "my-test-bucket"
    s3.create_bucket(Bucket=bucket_name)
    print(f"✓ Created bucket: {bucket_name}")
    
    # Upload object
    s3.put_object(
        Bucket=bucket_name,
        Key="test-file.txt",
        Body="Hello from LocalStack!"
    )
    print("✓ Uploaded object: test-file.txt")
    
    # List buckets
    response = s3.list_buckets()
    print(f"✓ Buckets: {[b['Name'] for b in response['Buckets']]}")
    
    # Read object
    obj = s3.get_object(Bucket=bucket_name, Key="test-file.txt")
    content = obj['Body'].read().decode('utf-8')
    print(f"✓ Object content: {content}")

def test_sqs():
    """Test SQS operations."""
    print("\n" + "="*50)
    print("Testing SQS...")
    print("="*50)
    
    sqs = get_client('sqs')
    
    # Create queue
    queue_name = "my-test-queue"
    response = sqs.create_queue(QueueName=queue_name)
    queue_url = response['QueueUrl']
    print(f"✓ Created queue: {queue_url}")
    
    # Send message
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody="Hello from LocalStack SQS!"
    )
    print("✓ Sent message to queue")
    
    # Receive message
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    if 'Messages' in response:
        print(f"✓ Received message: {response['Messages'][0]['Body']}")

def test_sns():
    """Test SNS operations."""
    print("\n" + "="*50)
    print("Testing SNS...")
    print("="*50)
    
    sns = get_client('sns')
    
    # Create topic
    topic_name = "my-test-topic"
    response = sns.create_topic(Name=topic_name)
    topic_arn = response['TopicArn']
    print(f"✓ Created topic: {topic_arn}")
    
    # List topics
    response = sns.list_topics()
    print(f"✓ Topics: {[t['TopicArn'].split(':')[-1] for t in response['Topics']]}")

def test_lambda():
    """Test Lambda operations."""
    print("\n" + "="*50)
    print("Testing Lambda...")
    print("="*50)
    
    lambda_client = get_client('lambda')
    
    # Create a simple Lambda function
    import zipfile
    import io
    
    # Create function code
    function_code = """
def handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from LocalStack Lambda!'
    }
"""
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('lambda_function.py', function_code)
    zip_buffer.seek(0)
    
    function_name = "my-test-function"
    
    try:
        # Delete if exists
        lambda_client.delete_function(FunctionName=function_name)
    except:
        pass
    
    # Create function
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.9',
        Role='arn:aws:iam::000000000000:role/lambda-role',
        Handler='lambda_function.handler',
        Code={'ZipFile': zip_buffer.read()},
    )
    print(f"✓ Created Lambda function: {function_name}")
    
    # List functions
    response = lambda_client.list_functions()
    print(f"✓ Functions: {[f['FunctionName'] for f in response['Functions']]}")
    
    # Invoke function
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse'
    )
    result = json.loads(response['Payload'].read())
    print(f"✓ Lambda response: {result}")

def test_ec2():
    """Test EC2 operations."""
    print("\n" + "="*50)
    print("Testing EC2...")
    print("="*50)
    
    ec2 = get_client('ec2')
    
    # Describe instances (will be empty initially)
    response = ec2.describe_instances()
    instance_count = sum(len(r['Instances']) for r in response['Reservations'])
    print(f"✓ Current instances: {instance_count}")
    
    # Create a key pair
    try:
        ec2.delete_key_pair(KeyName='my-test-key')
    except:
        pass
    
    response = ec2.create_key_pair(KeyName='my-test-key')
    print(f"✓ Created key pair: {response['KeyName']}")
    
    # Describe VPCs
    response = ec2.describe_vpcs()
    print(f"✓ VPCs: {len(response['Vpcs'])}")

def test_rds():
    """Test RDS operations."""
    print("\n" + "="*50)
    print("Testing RDS...")
    print("="*50)
    
    rds = get_client('rds')
    
    # List DB instances
    response = rds.describe_db_instances()
    print(f"✓ DB Instances: {len(response['DBInstances'])}")
    
    # Create DB instance (Note: LocalStack simulates metadata, not actual DB)
    db_instance_id = "my-test-db"
    
    try:
        rds.delete_db_instance(
            DBInstanceIdentifier=db_instance_id,
            SkipFinalSnapshot=True
        )
    except:
        pass
    
    try:
        rds.create_db_instance(
            DBInstanceIdentifier=db_instance_id,
            DBInstanceClass='db.t2.micro',
            Engine='mysql',
            MasterUsername='admin',
            MasterUserPassword='password123',
            AllocatedStorage=20
        )
        print(f"✓ Created DB instance: {db_instance_id}")
    except Exception as e:
        print(f"! RDS create note: {str(e)[:50]}...")

def test_emr():
    """Test EMR operations."""
    print("\n" + "="*50)
    print("Testing EMR...")
    print("="*50)
    
    emr = get_client('emr')
    
    # List clusters
    response = emr.list_clusters()
    print(f"✓ EMR Clusters: {len(response.get('Clusters', []))}")

def check_localstack_health():
    """Check if LocalStack is running and healthy."""
    import urllib.request
    import urllib.error
    
    print("="*50)
    print("Checking LocalStack Health...")
    print("="*50)
    
    try:
        with urllib.request.urlopen(f"{LOCALSTACK_ENDPOINT}/_localstack/health", timeout=5) as response:
            health = json.loads(response.read().decode())
            print("✓ LocalStack is running!")
            print(f"  Services: {list(health.get('services', {}).keys())}")
            return True
    except urllib.error.URLError:
        print("✗ LocalStack is not running!")
        print("  Please start it with: docker-compose up -d")
        return False

def main():
    """Run all tests."""
    print("\n" + "#"*50)
    print("# LocalStack AWS Services Test Suite")
    print("#"*50)
    
    if not check_localstack_health():
        return
    
    try:
        test_s3()
        test_sqs()
        test_sns()
        test_lambda()
        test_ec2()
        test_rds()
        test_emr()
        
        print("\n" + "="*50)
        print("All tests completed successfully! ✓")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise

if __name__ == "__main__":
    main()
