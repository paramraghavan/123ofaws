# AWS Resource Monitoring & Control-M Integration Guide

This guide covers monitoring patterns and common usage examples for AWS resources with Control-M integration via HTTP Swagger endpoints.

## Table of Contents
- [AWS Transfer/MFT](#aws-transfer-mft)
- [Lambda](#lambda)
- [EC2](#ec2)
- [EMR](#emr)
- [AutoScaling](#autoscaling)
- [CloudFormation](#cloudformation)
- [SQS](#sqs)
- [SNS](#sns)
- [SSM (Systems Manager)](#ssm)
- [IAM](#iam)
- [ELBv2 (Application/Network Load Balancer)](#elbv2)
- [S3](#s3)
- [KMS](#kms)

---

## AWS Transfer/MFT

**Purpose**: Managed file transfer service (SFTP, FTPS, AS2)

### Common Usage Patterns

```python
import boto3

# Initialize client
transfer_client = boto3.client('transfer', region_name='us-east-1')

# 1. List servers
response = transfer_client.list_servers()
for server in response['Servers']:
    print(f"Server: {server['ServerId']}, State: {server['State']}")

# 2. Get server details
server_details = transfer_client.describe_server(ServerId='server-id')
print(f"Status: {server_details['Server']['State']}")
print(f"Endpoint Type: {server_details['Server']['EndpointType']}")

# 3. List users for a server
users = transfer_client.list_users(ServerId='server-id')
for user in users['Users']:
    print(f"User: {user['UserName']}, Status: {user['UserName']}")

# 4. Monitor transfer activity
workflows = transfer_client.list_workflows()
for workflow in workflows['Workflows']:
    print(f"Workflow: {workflow['WorkflowId']}, State: {workflow['WorkflowDetails']}")

# 5. Check if server is online
def is_server_healthy(server_id):
    try:
        response = transfer_client.describe_server(ServerId=server_id)
        return response['Server']['State'] == 'ONLINE'
    except Exception as e:
        print(f"Error checking server health: {e}")
        return False
```

### Monitoring Checkpoints
- Server state (ONLINE/OFFLINE)
- User activity and permissions
- Workflow execution status
- CloudWatch metrics: BytesIn, BytesOut, UserCount
- Connectivity to SFTP/FTPS endpoints

### Control-M Integration
- Trigger transfers via API and wait for completion
- Monitor workflow execution status
- Alert on server state changes

---

## Lambda

**Purpose**: Serverless compute service

### Common Usage Patterns

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# 1. List functions
response = lambda_client.list_functions()
for func in response['Functions']:
    print(f"Function: {func['FunctionName']}, Runtime: {func['Runtime']}")

# 2. Get function configuration
config = lambda_client.get_function_configuration(FunctionName='my-function')
print(f"Timeout: {config['Timeout']}s")
print(f"Memory: {config['MemorySize']}MB")

# 3. Invoke function synchronously
response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='RequestResponse',  # Synchronous
    Payload=json.dumps({'key': 'value'})
)
print(f"Status Code: {response['StatusCode']}")
result = json.loads(response['Payload'].read())
print(f"Result: {result}")

# 4. Invoke asynchronously
response = lambda_client.invoke(
    FunctionName='my-function',
    InvocationType='Event',  # Asynchronous
    Payload=json.dumps({'key': 'value'})
)
print(f"Request ID: {response['ResponseMetadata']['RequestId']}")

# 5. Get function metrics
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/Lambda',
    MetricName='Duration',
    Dimensions=[{'Name': 'FunctionName', 'Value': 'my-function'}],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-01-02T00:00:00Z',
    Period=300,
    Statistics=['Average', 'Sum', 'Maximum']
)
for datapoint in response['Datapoints']:
    print(f"Duration: {datapoint['Average']}ms")

# 6. Check function health
def is_function_healthy(function_name):
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['State'] == 'Active'
    except Exception as e:
        print(f"Error checking function health: {e}")
        return False
```

### Monitoring Checkpoints
- Function state (Active/Inactive)
- Invocation duration
- Error rate and throttling
- Cold start metrics
- Concurrent executions vs reserved concurrency
- CloudWatch Logs for errors

### Control-M Integration
- Synchronously invoke functions and wait for completion
- Check execution status via CloudWatch
- Alert on error rates or throttling

---

## EC2

**Purpose**: Elastic Compute Cloud - Virtual machines

### Common Usage Patterns

```python
import boto3

ec2_client = boto3.client('ec2', region_name='us-east-1')
ec2_resource = boto3.resource('ec2', region_name='us-east-1')

# 1. List instances
response = ec2_client.describe_instances()
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"Instance: {instance['InstanceId']}, State: {instance['State']['Name']}")

# 2. Get instance details
response = ec2_client.describe_instances(InstanceIds=['i-1234567890abcdef0'])
instance = response['Reservations'][0]['Instances'][0]
print(f"Type: {instance['InstanceType']}")
print(f"State: {instance['State']['Name']}")
print(f"Public IP: {instance.get('PublicIpAddress')}")
print(f"Private IP: {instance['PrivateIpAddress']}")

# 3. Start/Stop instance
ec2_client.start_instances(InstanceIds=['i-1234567890abcdef0'])
ec2_client.stop_instances(InstanceIds=['i-1234567890abcdef0'])

# 4. Get instance status checks
response = ec2_client.describe_instance_status(InstanceIds=['i-1234567890abcdef0'])
for status in response['InstanceStatuses']:
    print(f"System Status: {status['SystemStatus']['Status']}")
    print(f"Instance Status: {status['InstanceStatus']['Status']}")

# 5. Monitor instance metrics
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/EC2',
    MetricName='CPUUtilization',
    Dimensions=[{'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-01-02T00:00:00Z',
    Period=300,
    Statistics=['Average', 'Maximum']
)
for datapoint in response['Datapoints']:
    print(f"CPU: {datapoint['Average']}%")

# 6. Check instance health
def is_instance_healthy(instance_id):
    try:
        response = ec2_client.describe_instance_status(
            InstanceIds=[instance_id],
            IncludeAllInstances=True
        )
        if response['InstanceStatuses']:
            status = response['InstanceStatuses'][0]
            return (status['InstanceStatus']['Status'] == 'ok' and
                    status['SystemStatus']['Status'] == 'ok')
        return False
    except Exception as e:
        print(f"Error checking instance health: {e}")
        return False
```

### Monitoring Checkpoints
- Instance state (running/stopped/terminated)
- System Status Checks and Instance Status Checks
- CPU, Memory, Network utilization
- EBS volume status
- Security group and network ACL compliance

### Control-M Integration
- Start/stop instances as job triggers
- Wait for status checks to pass
- Monitor instance metrics and alert on thresholds

---

## EMR

**Purpose**: Elastic MapReduce - Big data processing with Hadoop/Spark

### Common Usage Patterns

```python
import boto3

emr_client = boto3.client('emr', region_name='us-east-1')

# 1. List clusters
response = emr_client.list_clusters()
for cluster in response['Clusters']:
    print(f"Cluster: {cluster['Id']}, Name: {cluster['Name']}, Status: {cluster['Status']['State']}")

# 2. Get cluster details
response = emr_client.describe_cluster(ClusterId='j-1ABCDEFGHIJ2K')
cluster = response['Cluster']
print(f"Status: {cluster['Status']['State']}")
print(f"Running Applications: {[app['Name'] for app in cluster.get('Applications', [])]}")
print(f"Master: {cluster['MasterPublicDNSName']}")

# 3. Get cluster status
response = emr_client.describe_cluster(ClusterId='j-1ABCDEFGHIJ2K')
status = response['Cluster']['Status']
print(f"State: {status['State']}")
if status.get('StateChangeReason'):
    print(f"Reason: {status['StateChangeReason']['Message']}")

# 4. List steps (jobs) in cluster
response = emr_client.list_steps(ClusterId='j-1ABCDEFGHIJ2K')
for step in response['Steps']:
    print(f"Step: {step['Id']}, Name: {step['Name']}, Status: {step['Status']['State']}")

# 5. Get step details
response = emr_client.describe_step(ClusterId='j-1ABCDEFGHIJ2K', StepId='s-1ABCDEFGHIJ2K')
step = response['Step']
print(f"Status: {step['Status']['State']}")
print(f"Start Time: {step['Status']['Timeline']['CreationDateTime']}")

# 6. Add a step to cluster
response = emr_client.add_steps(
    ClusterId='j-1ABCDEFGHIJ2K',
    Steps=[{
        'Name': 'My Spark Job',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': ['spark-submit', '--class', 'com.example.Main', 's3://bucket/app.jar']
        }
    }]
)
step_id = response['StepIds'][0]
print(f"Step ID: {step_id}")

# 7. Monitor cluster health
def is_cluster_healthy(cluster_id):
    try:
        response = emr_client.describe_cluster(ClusterId=cluster_id)
        state = response['Cluster']['Status']['State']
        return state in ['RUNNING', 'WAITING']
    except Exception as e:
        print(f"Error checking cluster health: {e}")
        return False

# 8. Wait for step completion
def wait_for_step(cluster_id, step_id, max_wait=3600):
    import time
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = emr_client.describe_step(ClusterId=cluster_id, StepId=step_id)
        state = response['Step']['Status']['State']
        if state == 'COMPLETED':
            return True
        elif state in ['FAILED', 'CANCELLED']:
            return False
        time.sleep(10)
    return False
```

### Monitoring Checkpoints
- Cluster state (RUNNING/WAITING/TERMINATING)
- Step status (PENDING/RUNNING/COMPLETED/FAILED)
- Node count and instance health
- YARN and Hadoop metrics
- Logs in S3 for debugging

### Control-M Integration
- Submit steps to running clusters
- Poll step status until completion
- Trigger failover to new cluster if primary fails

---

## AutoScaling

**Purpose**: Automatically scale EC2/RDS resources based on demand

### Common Usage Patterns

```python
import boto3

asg_client = boto3.client('autoscaling', region_name='us-east-1')

# 1. List Auto Scaling Groups
response = asg_client.describe_auto_scaling_groups()
for asg in response['AutoScalingGroups']:
    print(f"ASG: {asg['AutoScalingGroupName']}")
    print(f"Desired: {asg['DesiredCapacity']}, Current: {len(asg['Instances'])}")
    print(f"Min: {asg['MinSize']}, Max: {asg['MaxSize']}")

# 2. Get specific ASG details
response = asg_client.describe_auto_scaling_groups(
    AutoScalingGroupNames=['my-asg']
)
asg = response['AutoScalingGroups'][0]
print(f"Status: {asg['CreatedTime']}")
print(f"Instances: {[i['InstanceId'] for i in asg['Instances']]}")

# 3. Get scaling activities
response = asg_client.describe_scaling_activities(
    AutoScalingGroupName='my-asg'
)
for activity in response['Activities']:
    print(f"Activity: {activity['Description']}")
    print(f"Status: {activity['StatusCode']} - {activity.get('StatusMessage', '')}")
    print(f"Time: {activity['StartTime']}")

# 4. Get instance protection status
response = asg_client.describe_auto_scaling_groups(
    AutoScalingGroupNames=['my-asg']
)
asg = response['AutoScalingGroups'][0]
for instance in asg['Instances']:
    print(f"Instance: {instance['InstanceId']}, Protected: {instance['ProtectedFromScaleIn']}")

# 5. Get scaling policies
response = asg_client.describe_policies(
    AutoScalingGroupName='my-asg'
)
for policy in response['ScalingPolicies']:
    print(f"Policy: {policy['PolicyName']}")
    print(f"Type: {policy.get('PolicyType')}")
    if 'TargetTrackingConfiguration' in policy:
        target = policy['TargetTrackingConfiguration']
        print(f"Target: {target['TargetValue']}")

# 6. Manually set desired capacity
asg_client.set_desired_capacity(
    AutoScalingGroupName='my-asg',
    DesiredCapacity=5
)

# 7. Check ASG health
def is_asg_healthy(asg_name):
    try:
        response = asg_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        if not response['AutoScalingGroups']:
            return False
        asg = response['AutoScalingGroups'][0]
        # Check if all instances are healthy
        healthy_instances = sum(1 for i in asg['Instances'] if i['HealthStatus'] == 'Healthy')
        return healthy_instances == len(asg['Instances'])
    except Exception as e:
        print(f"Error checking ASG health: {e}")
        return False
```

### Monitoring Checkpoints
- Current capacity vs desired capacity
- Instance health status
- Scaling activity history and success rate
- Scaling policy effectiveness
- Cooldown periods preventing scaling

### Control-M Integration
- Adjust capacity before running workloads
- Monitor scaling activities
- Alert if instances fail to scale up/down

---

## CloudFormation

**Purpose**: Infrastructure as Code - Manage AWS resources via templates

### Common Usage Patterns

```python
import boto3
import json

cf_client = boto3.client('cloudformation', region_name='us-east-1')

# 1. List stacks
response = cf_client.list_stacks(
    StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
)
for stack in response['StackSummaries']:
    print(f"Stack: {stack['StackName']}, Status: {stack['StackStatus']}")

# 2. Get stack details
response = cf_client.describe_stacks(StackName='my-stack')
stack = response['Stacks'][0]
print(f"Status: {stack['StackStatus']}")
print(f"Created: {stack['CreationTime']}")
if 'StackStatusReason' in stack:
    print(f"Reason: {stack['StackStatusReason']}")

# 3. Get stack resources
response = cf_client.list_stack_resources(StackName='my-stack')
for resource in response['StackResourceSummaries']:
    print(f"Resource: {resource['LogicalResourceId']}")
    print(f"Type: {resource['ResourceType']}")
    print(f"Status: {resource['ResourceStatus']}")

# 4. Get stack outputs
response = cf_client.describe_stacks(StackName='my-stack')
stack = response['Stacks'][0]
for output in stack.get('Outputs', []):
    print(f"{output['OutputKey']}: {output['OutputValue']}")

# 5. Create a stack
template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {
        "MyBucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": "my-unique-bucket"
            }
        }
    }
}

response = cf_client.create_stack(
    StackName='my-new-stack',
    TemplateBody=json.dumps(template)
)
print(f"Stack ID: {response['StackId']}")

# 6. Describe stack events
response = cf_client.describe_stack_events(StackName='my-stack')
for event in response['StackEvents'][:10]:
    print(f"Event: {event['EventId']}")
    print(f"Status: {event['ResourceStatus']}")
    if 'ResourceStatusReason' in event:
        print(f"Reason: {event['ResourceStatusReason']}")

# 7. Check stack health
def is_stack_healthy(stack_name):
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        status = response['Stacks'][0]['StackStatus']
        return status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']
    except Exception as e:
        print(f"Error checking stack health: {e}")
        return False

# 8. Wait for stack update
def wait_for_stack_update(stack_name, max_wait=3600):
    import time
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = cf_client.describe_stacks(StackName=stack_name)
        status = response['Stacks'][0]['StackStatus']
        if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return True
        elif 'FAILED' in status:
            return False
        time.sleep(10)
    return False
```

### Monitoring Checkpoints
- Stack status (CREATE_COMPLETE, UPDATE_COMPLETE, etc.)
- Resource creation/deletion status
- Stack events and errors
- Drift detection (actual vs template)
- Outputs and parameter values

### Control-M Integration
- Create/update stacks before workloads
- Monitor stack events until complete
- Validate stack health before dependent jobs

---

## SQS

**Purpose**: Simple Queue Service - Decouple applications via messaging

### Common Usage Patterns

```python
import boto3
import json

sqs_client = boto3.client('sqs', region_name='us-east-1')

# 1. List queues
response = sqs_client.list_queues()
for queue_url in response.get('QueueUrls', []):
    print(f"Queue: {queue_url}")

# 2. Get queue attributes
response = sqs_client.get_queue_attributes(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/my-queue',
    AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfNotVisibleMessages']
)
attributes = response['Attributes']
print(f"Messages: {attributes['ApproximateNumberOfMessages']}")
print(f"In-flight: {attributes['ApproximateNumberOfNotVisibleMessages']}")

# 3. Send message
response = sqs_client.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/my-queue',
    MessageBody=json.dumps({'key': 'value'})
)
print(f"Message ID: {response['MessageId']}")

# 4. Receive messages
response = sqs_client.receive_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/my-queue',
    MaxNumberOfMessages=10,
    WaitTimeSeconds=10
)
for message in response.get('Messages', []):
    print(f"Message ID: {message['MessageId']}")
    print(f"Body: {message['Body']}")
    # Process message...
    # Delete after processing
    sqs_client.delete_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/my-queue',
        ReceiptHandle=message['ReceiptHandle']
    )

# 5. Get queue metrics
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/SQS',
    MetricName='ApproximateNumberOfMessagesVisible',
    Dimensions=[{'Name': 'QueueName', 'Value': 'my-queue'}],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-01-02T00:00:00Z',
    Period=300,
    Statistics=['Average', 'Maximum']
)
for datapoint in response['Datapoints']:
    print(f"Messages: {datapoint['Average']}")

# 6. Monitor queue health
def is_queue_healthy(queue_url):
    try:
        response = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        # Queue is healthy if it exists and is accessible
        return True
    except Exception as e:
        print(f"Error checking queue health: {e}")
        return False
```

### Monitoring Checkpoints
- Approximate message count
- In-flight messages
- Message age
- Queue deadletter queue size
- Throughput (messages sent/received per minute)

### Control-M Integration
- Send messages to trigger downstream processes
- Monitor message count thresholds
- Alert if messages accumulate (processor failures)

---

## SNS

**Purpose**: Simple Notification Service - Publish/Subscribe messaging

### Common Usage Patterns

```python
import boto3
import json

sns_client = boto3.client('sns', region_name='us-east-1')

# 1. List topics
response = sns_client.list_topics()
for topic in response['Topics']:
    print(f"Topic: {topic['TopicArn']}")

# 2. Get topic attributes
response = sns_client.get_topic_attributes(
    TopicArn='arn:aws:sns:us-east-1:123456789:my-topic'
)
attributes = response['Attributes']
print(f"Display Name: {attributes.get('DisplayName')}")
print(f"Subscriptions Count: {attributes.get('SubscriptionsConfirmed')}")

# 3. Publish message
response = sns_client.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789:my-topic',
    Message=json.dumps({'alert': 'System failure detected'}),
    Subject='Alert from AWS'
)
print(f"Message ID: {response['MessageId']}")

# 4. List subscriptions
response = sns_client.list_subscriptions_by_topic(
    TopicArn='arn:aws:sns:us-east-1:123456789:my-topic'
)
for sub in response['Subscriptions']:
    print(f"Subscription: {sub['SubscriptionArn']}")
    print(f"Protocol: {sub['Protocol']}, Endpoint: {sub['Endpoint']}")

# 5. Subscribe to topic (email example)
response = sns_client.subscribe(
    TopicArn='arn:aws:sns:us-east-1:123456789:my-topic',
    Protocol='email',
    Endpoint='admin@example.com'
)
print(f"Subscription ARN: {response['SubscriptionArn']}")

# 6. Send message with filter policy (SQS/Lambda subscriptions)
response = sns_client.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789:my-topic',
    Message=json.dumps({'level': 'CRITICAL', 'service': 'billing'}),
    Subject='Critical Alert'
)

# 7. Monitor topic health
def is_topic_healthy(topic_arn):
    try:
        response = sns_client.get_topic_attributes(TopicArn=topic_arn)
        return True
    except Exception as e:
        print(f"Error checking topic health: {e}")
        return False
```

### Monitoring Checkpoints
- Topic existence and accessibility
- Subscription count and confirmation status
- Message delivery success rate
- Dead letter queue size (if configured)
- Notification latency

### Control-M Integration
- Publish alerts to SNS topic on job failures
- Configure email subscriptions for notifications
- Route alerts based on message attributes

---

## SSM

**Purpose**: Systems Manager - Run commands, maintain patch compliance, parameter store

### Common Usage Patterns

```python
import boto3
import time

ssm_client = boto3.client('ssm', region_name='us-east-1')

# 1. Send command to instances
response = ssm_client.send_command(
    DocumentName='AWS-RunShellScript',
    Parameters={'command': ['echo "Hello from AWS Systems Manager"']},
    InstanceIds=['i-1234567890abcdef0']
)
command_id = response['Command']['CommandId']
print(f"Command ID: {command_id}")

# 2. Get command invocation status
response = ssm_client.get_command_invocation(
    CommandId=command_id,
    InstanceId='i-1234567890abcdef0'
)
print(f"Status: {response['Status']}")
print(f"Output: {response.get('StandardOutputContent', '')}")

# 3. Get parameter from Parameter Store
response = ssm_client.get_parameter(Name='/app/database/host')
value = response['Parameter']['Value']
print(f"Database Host: {value}")

# 4. Put parameter to Parameter Store
ssm_client.put_parameter(
    Name='/app/config/timeout',
    Value='30',
    Type='String',
    Overwrite=True
)

# 5. Get secure parameter (encrypted)
response = ssm_client.get_parameter(
    Name='/app/secrets/api-key',
    WithDecryption=True
)
api_key = response['Parameter']['Value']

# 6. List document details
response = ssm_client.describe_document(Name='AWS-RunShellScript')
document = response['Document']
print(f"Name: {document['Name']}")
print(f"DocumentType: {document['DocumentType']}")

# 7. Run automation document
response = ssm_client.start_automation_execution(
    DocumentName='AWS-ChangeDBPortNumber',
    Parameters={
        'InstanceId': ['i-1234567890abcdef0'],
        'AutomationAssumeRole': ['arn:aws:iam::123456789:role/AutomationRole']
    }
)
execution_id = response['AutomationExecutionId']

# 8. Get automation execution status
response = ssm_client.get_automation_execution(AutomationExecutionId=execution_id)
execution = response['AutomationExecution']
print(f"Status: {execution['AutomationExecutionStatus']}")

# 9. Check compliance
response = ssm_client.list_compliance_items(
    Filters=[{
        'Key': 'Status',
        'Values': ['COMPLIANT', 'NON_COMPLIANT']
    }]
)
for item in response['ComplianceItems']:
    print(f"Resource: {item['ResourceId']}, Status: {item['Status']}")

# 10. Monitor command health
def is_command_successful(command_id, instance_id, max_wait=300):
    import time
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        status = response['Status']
        if status in ['Success', 'Failed', 'Cancelled']:
            return status == 'Success'
        time.sleep(5)
    return False
```

### Monitoring Checkpoints
- Command execution status
- Command output and errors
- Instance compliance status
- Parameter changes and versions
- Automation document execution status

### Control-M Integration
- Execute commands on instances before workloads
- Wait for command completion
- Alert on command failures

---

## IAM

**Purpose**: Identity and Access Management - Users, roles, permissions

### Common Usage Patterns

```python
import boto3

iam_client = boto3.client('iam')

# 1. List users
response = iam_client.list_users()
for user in response['Users']:
    print(f"User: {user['UserName']}, Created: {user['CreateDate']}")

# 2. Get user details
response = iam_client.get_user(UserName='john-doe')
user = response['User']
print(f"UserName: {user['UserName']}")
print(f"ARN: {user['Arn']}")
print(f"Last Password Change: {user.get('PasswordLastUsed', 'Never')}")

# 3. Get user access keys
response = iam_client.list_access_keys(UserName='john-doe')
for key in response['AccessKeyMetadata']:
    print(f"Access Key ID: {key['AccessKeyId']}")
    print(f"Status: {key['Status']}")
    print(f"Created: {key['CreateDate']}")

# 4. Check access key age
response = iam_client.list_access_keys(UserName='john-doe')
for key in response['AccessKeyMetadata']:
    from datetime import datetime, timezone
    created = key['CreateDate'].replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - created).days
    if age_days > 90:
        print(f"OLD KEY: {key['AccessKeyId']} is {age_days} days old")

# 5. List IAM roles
response = iam_client.list_roles()
for role in response['Roles']:
    print(f"Role: {role['RoleName']}, Created: {role['CreateDate']}")

# 6. Get role details
response = iam_client.get_role(RoleName='lambda-execution-role')
role = response['Role']
print(f"RoleName: {role['RoleName']}")
print(f"Arn: {role['Arn']}")

# 7. Get attached policies
response = iam_client.list_attached_role_policies(RoleName='lambda-execution-role')
for policy in response['AttachedPolicies']:
    print(f"Policy: {policy['PolicyName']}")

# 8. Check policy for specific permissions
response = iam_client.get_role_policy(
    RoleName='lambda-execution-role',
    PolicyName='inline-policy'
)
policy = response['RolePolicyDocument']
print(f"Permissions: {policy['Statement']}")

# 9. List account password policy
response = iam_client.get_account_password_policy()
policy = response['PasswordPolicy']
print(f"Minimum Length: {policy['MinimumPasswordLength']}")
print(f"Require Symbols: {policy.get('RequireSymbols')}")

# 10. Verify credentials/role health
def is_role_healthy(role_name):
    try:
        response = iam_client.get_role(RoleName=role_name)
        return True
    except Exception as e:
        print(f"Error checking role health: {e}")
        return False
```

### Monitoring Checkpoints
- User access key age (should rotate every 90 days)
- Password age and policy compliance
- Unused users or roles
- Excessive permissions
- MFA enablement
- Root account activity

### Control-M Integration
- Check role availability before job execution
- Verify credentials are valid
- Alert on permission changes

---

## ELBv2

**Purpose**: Application/Network Load Balancers - Distribute traffic

### Common Usage Patterns

```python
import boto3

elbv2_client = boto3.client('elbv2', region_name='us-east-1')

# 1. List load balancers
response = elbv2_client.describe_load_balancers()
for lb in response['LoadBalancers']:
    print(f"LB: {lb['LoadBalancerName']}, State: {lb['State']['Code']}")
    print(f"DNS: {lb['DNSName']}")
    print(f"Scheme: {lb['Scheme']}")

# 2. Get load balancer details
response = elbv2_client.describe_load_balancers(
    LoadBalancerArns=['arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/my-lb/1234567890']
)
lb = response['LoadBalancers'][0]
print(f"VPC: {lb['VpcId']}")
print(f"Subnets: {lb['AvailabilityZones']}")

# 3. List target groups
response = elbv2_client.describe_target_groups()
for tg in response['TargetGroups']:
    print(f"Target Group: {tg['TargetGroupName']}")
    print(f"Port: {tg['Port']}, Protocol: {tg['Protocol']}")

# 4. Get target health
response = elbv2_client.describe_target_health(
    TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/my-targets/abc123'
)
for target in response['TargetHealthDescriptions']:
    print(f"Target: {target['Target']['Id']}")
    print(f"Health: {target['TargetHealth']['State']}")
    if target['TargetHealth']['State'] == 'unhealthy':
        print(f"Reason: {target['TargetHealth'].get('Reason')}")
        print(f"Description: {target['TargetHealth'].get('Description')}")

# 5. Get load balancer metrics
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/ApplicationELB',
    MetricName='TargetResponseTime',
    Dimensions=[{'Name': 'LoadBalancer', 'Value': 'app/my-lb/1234567890'}],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-01-02T00:00:00Z',
    Period=300,
    Statistics=['Average', 'Maximum']
)
for datapoint in response['Datapoints']:
    print(f"Response Time: {datapoint['Average']}s")

# 6. Describe listeners
response = elbv2_client.describe_listeners(
    LoadBalancerArn='arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/my-lb/1234567890'
)
for listener in response['Listeners']:
    print(f"Port: {listener['Port']}, Protocol: {listener['Protocol']}")

# 7. Monitor load balancer health
def is_load_balancer_healthy(lb_arn):
    try:
        response = elbv2_client.describe_load_balancers(LoadBalancerArns=[lb_arn])
        if response['LoadBalancers']:
            state = response['LoadBalancers'][0]['State']['Code']
            return state == 'active'
        return False
    except Exception as e:
        print(f"Error checking LB health: {e}")
        return False

# 8. Monitor target health
def get_unhealthy_targets(target_group_arn):
    try:
        response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
        unhealthy = [
            t for t in response['TargetHealthDescriptions']
            if t['TargetHealth']['State'] != 'healthy'
        ]
        return unhealthy
    except Exception as e:
        print(f"Error getting target health: {e}")
        return []
```

### Monitoring Checkpoints
- Load balancer state (active/provisioning)
- Target health (healthy/unhealthy)
- Response time and latency
- Request count and error rates (4xx, 5xx)
- Connection count
- Active connection count

### Control-M Integration
- Verify load balancer and targets are healthy before routing traffic
- Alert on target failures or high error rates

---

## S3

**Purpose**: Simple Storage Service - Object storage

### Common Usage Patterns

```python
import boto3
import json

s3_client = boto3.client('s3', region_name='us-east-1')
s3_resource = boto3.resource('s3', region_name='us-east-1')

# 1. List buckets
response = s3_client.list_buckets()
for bucket in response['Buckets']:
    print(f"Bucket: {bucket['Name']}, Created: {bucket['CreationDate']}")

# 2. Get bucket details
response = s3_client.head_bucket(Bucket='my-bucket')
print(f"Status: Bucket exists")

# 3. List objects in bucket
response = s3_client.list_objects_v2(Bucket='my-bucket', MaxKeys=100)
for obj in response.get('Contents', []):
    print(f"Object: {obj['Key']}, Size: {obj['Size']}, Modified: {obj['LastModified']}")

# 4. Upload file to S3
s3_client.upload_file(
    '/local/path/file.txt',
    'my-bucket',
    'remote/path/file.txt'
)

# 5. Download file from S3
s3_client.download_file('my-bucket', 'remote/path/file.txt', '/local/path/file.txt')

# 6. Get object metadata
response = s3_client.head_object(Bucket='my-bucket', Key='remote/path/file.txt')
print(f"Size: {response['ContentLength']}")
print(f"Modified: {response['LastModified']}")
print(f"Metadata: {response.get('Metadata', {})}")

# 7. Check bucket versioning
response = s3_client.get_bucket_versioning(Bucket='my-bucket')
print(f"Versioning: {response.get('Status', 'Disabled')}")

# 8. Get bucket encryption
response = s3_client.get_bucket_encryption(Bucket='my-bucket')
rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
for rule in rules:
    print(f"Encryption: {rule['ApplyServerSideEncryptionByDefault']}")

# 9. List bucket's lifecycle policies
response = s3_client.get_bucket_lifecycle_configuration(Bucket='my-bucket')
for rule in response.get('Rules', []):
    print(f"Rule ID: {rule['ID']}, Status: {rule['Status']}")

# 10. Get bucket size
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/S3',
    MetricName='BucketSizeBytes',
    Dimensions=[
        {'Name': 'BucketName', 'Value': 'my-bucket'},
        {'Name': 'StorageType', 'Value': 'StandardStorage'}
    ],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-01-02T00:00:00Z',
    Period=86400,  # 1 day
    Statistics=['Average']
)
for datapoint in response['Datapoints']:
    size_gb = datapoint['Average'] / (1024**3)
    print(f"Bucket Size: {size_gb:.2f} GB")

# 11. Monitor bucket health
def is_bucket_healthy(bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except Exception as e:
        print(f"Error checking bucket health: {e}")
        return False

# 12. Check object existence
def object_exists(bucket_name, key):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except s3_client.exceptions.NoSuchKey:
        return False
```

### Monitoring Checkpoints
- Bucket existence and accessibility
- Object count and total size
- Replication status (if multi-region)
- Versioning and lifecycle policies
- Encryption status
- Access logging enabled

### Control-M Integration
- Upload files to S3 and verify completion
- Check for file existence before downstream processing
- Alert on bucket access failures

---

## KMS

**Purpose**: Key Management Service - Encryption key management

### Common Usage Patterns

```python
import boto3
import base64

kms_client = boto3.client('kms', region_name='us-east-1')

# 1. List keys
response = kms_client.list_keys()
for key in response['Keys']:
    print(f"Key ID: {key['KeyId']}")

# 2. Get key details
response = kms_client.describe_key(KeyId='arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012')
key_metadata = response['KeyMetadata']
print(f"Key ID: {key_metadata['KeyId']}")
print(f"Description: {key_metadata.get('Description')}")
print(f"Key State: {key_metadata['KeyState']}")
print(f"Key Usage: {key_metadata['KeyUsage']}")

# 3. List key aliases
response = kms_client.list_aliases()
for alias in response['Aliases']:
    if 'TargetKeyId' in alias:
        print(f"Alias: {alias['AliasName']}, Target: {alias['TargetKeyId']}")

# 4. Encrypt data
plaintext = b'Secret data'
response = kms_client.encrypt(
    KeyId='arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012',
    Plaintext=plaintext
)
ciphertext = response['CiphertextBlob']
print(f"Encrypted: {base64.b64encode(ciphertext).decode()}")

# 5. Decrypt data
response = kms_client.decrypt(CiphertextBlob=ciphertext)
decrypted = response['Plaintext']
print(f"Decrypted: {decrypted.decode()}")

# 6. Generate data key
response = kms_client.generate_data_key(
    KeyId='arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012',
    KeySpec='AES_256'
)
plaintext_key = response['Plaintext']
encrypted_key = response['CiphertextBlob']
print(f"Data Key created (encrypted copy available for storage)")

# 7. Get key rotation status
response = kms_client.get_key_rotation_status(
    KeyId='arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012'
)
print(f"Key Rotation Enabled: {response['KeyRotationEnabled']}")

# 8. Get key policy
response = kms_client.get_key_policy(
    KeyId='arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012',
    PolicyName='default'
)
import json
policy = json.loads(response['Policy'])
print(f"Policy: {json.dumps(policy, indent=2)}")

# 9. Monitor key usage
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/KMS',
    MetricName='UserErrorCount',
    Dimensions=[{'Name': 'KeyId', 'Value': '12345678-1234-1234-1234-123456789012'}],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-01-02T00:00:00Z',
    Period=300,
    Statistics=['Sum']
)
for datapoint in response['Datapoints']:
    if datapoint['Sum'] > 0:
        print(f"Errors: {datapoint['Sum']}")

# 10. Check key health
def is_key_healthy(key_id):
    try:
        response = kms_client.describe_key(KeyId=key_id)
        key_state = response['KeyMetadata']['KeyState']
        return key_state in ['Enabled', 'PendingDeletion']
    except Exception as e:
        print(f"Error checking key health: {e}")
        return False
```

### Monitoring Checkpoints
- Key state (Enabled/Disabled/PendingDeletion)
- Key rotation status
- Key usage metrics
- Decryption errors
- Key policy compliance

### Control-M Integration
- Verify encryption key is available before using encrypted resources
- Alert on key rotation or expiration

---

## Monitoring & Alerting Framework

### Email Alert Configuration

```python
import boto3
import json
from datetime import datetime

sns_client = boto3.client('sns')

def send_alert_email(topic_arn, subject, message_body, severity='WARNING'):
    """
    Send alert email via SNS

    Args:
        topic_arn: SNS topic ARN
        subject: Email subject
        message_body: Email body
        severity: CRITICAL, WARNING, INFO
    """
    try:
        message = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'subject': subject,
            'body': message_body
        }

        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=f"[{severity}] {subject}",
            Message=json.dumps(message, indent=2)
        )
        print(f"Alert sent: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

# Example usage:
# send_alert_email(
#     'arn:aws:sns:us-east-1:123456789:alerts',
#     'Lambda Function Failure',
#     'Function my-function failed with error: timeout',
#     'CRITICAL'
# )
```

### Health Check Implementation

```python
def perform_health_checks(region='us-east-1'):
    """
    Perform comprehensive health checks across AWS resources
    """
    health_status = {}

    # Check each service
    checks = {
        'EC2': check_ec2_health,
        'Lambda': check_lambda_health,
        'RDS': check_rds_health,
        'S3': check_s3_health,
        'SQS': check_sqs_health,
        'ELB': check_elb_health,
    }

    for service, check_fn in checks.items():
        try:
            health_status[service] = check_fn(region)
        except Exception as e:
            health_status[service] = {'status': 'ERROR', 'error': str(e)}

    return health_status
```

---

## Control-M Integration Points

### HTTP REST API Pattern

```python
import requests
import json

class ControlMIntegration:
    """
    Integration with Control-M via HTTP REST API
    """

    def __init__(self, control_m_url, username, password):
        self.base_url = control_m_url
        self.session = requests.Session()
        self.authenticate(username, password)

    def authenticate(self, username, password):
        """Authenticate with Control-M API"""
        auth_url = f"{self.base_url}/api/v2/login"
        response = self.session.post(auth_url, json={
            'username': username,
            'password': password
        })
        response.raise_for_status()
        self.session.headers['Authorization'] = f"Bearer {response.json()['token']}"

    def submit_job(self, job_data):
        """Submit job to Control-M"""
        url = f"{self.base_url}/api/v2/jobs"
        response = self.session.post(url, json=job_data)
        response.raise_for_status()
        return response.json()

    def get_job_status(self, job_id):
        """Get job execution status"""
        url = f"{self.base_url}/api/v2/jobs/{job_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def send_event(self, event_name, parameters=None):
        """Send event to Control-M"""
        url = f"{self.base_url}/api/v2/events"
        payload = {
            'name': event_name,
            'parameters': parameters or {}
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

# Example usage:
# ctm = ControlMIntegration('http://control-m.example.com', 'user', 'pass')
# result = ctm.submit_job({
#     'jobName': 'aws-monitoring-job',
#     'description': 'Monitor AWS resources'
# })
```

---

## Next Steps

1. **Monitoring Implementation**: Create Python scripts for continuous monitoring
2. **Alert System**: Configure SNS topics and email subscriptions
3. **Failover Framework**: Implement automated region failover logic
4. **Control-M Webhooks**: Set up webhook receivers for Control-M events
5. **Dashboard**: Create dashboard to visualize resource health

