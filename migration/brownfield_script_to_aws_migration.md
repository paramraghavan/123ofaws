# Brownfield Failover Script to AWS Migration

**Complete guide for migrating your on-premises failover script to AWS EC2 or Lambda**

---

## Table of Contents

1. [Quick Decision: EC2 vs Lambda](#quick-decision-ec2-vs-lambda)
2. [Pre-Migration Setup](#pre-migration-setup)
3. [Option A: Migrate to EC2 Instance](#option-a-migrate-to-ec2-instance)
4. [Option B: Migrate to AWS Lambda](#option-b-migrate-to-aws-lambda)
5. [Code Migration Checklist](#code-migration-checklist)
6. [Testing & Validation](#testing--validation)
7. [Deployment Steps](#deployment-steps)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Rollback Procedures](#rollback-procedures)

---

## Quick Decision: EC2 vs Lambda

### Your Current Situation
- ✅ Failover script running on on-premises brownfield
- ✅ Can access all AWS resources from there
- ✅ Script works reliably
- ✅ Need to move to AWS

### Decision Matrix

| Factor | EC2 Instance | AWS Lambda |
|--------|--------------|-----------|
| **Complexity of script** | Any size | Simple to moderate |
| **Execution time** | Any length | Max 15 minutes |
| **Memory needed** | Flexible | Max 10 GB |
| **State management** | Local files OK | Must use external storage |
| **Cost** | Fixed hourly (~$10-30/month) | Pay per execution (~$1-5/month) |
| **Management** | You manage OS/patches | AWS managed |
| **Monitoring** | CloudWatch + custom | CloudWatch built-in |
| **Dependencies** | All supported | Limited |
| **Network** | Full VPC access | Limited |
| **Control** | Maximum | Constrained |
| **Setup complexity** | Medium | Low |
| **Operational overhead** | Medium | Low |

### Choose EC2 If Your Script:
```
✅ Runs for > 5 minutes
✅ Needs complex file operations
✅ Has many external dependencies
✅ Needs constant/background execution
✅ Uses system-level features
✅ Cost is not primary concern
✅ Team prefers traditional servers
```

### Choose Lambda If Your Script:
```
✅ Runs for < 5 minutes
✅ Triggered on schedule (every 5-60 min)
✅ Simple logic (monitor + action)
✅ Can be stateless
✅ Cost is important
✅ Team wants serverless
✅ Minimal operational overhead desired
```

### **RECOMMENDATION FOR YOUR CASE**

**Most likely: Start with EC2**

Why?
- Your brownfield script is complex (it's a production failover system)
- Likely has multiple dependencies and file operations
- May need to run frequently with low latency
- EC2 gives you flexibility to migrate with minimal changes
- Can later optimize with Lambda if simple enough

---

## Pre-Migration Setup

### ☑️ 1. Create AWS VPC & Networking Infrastructure

**Checklist:**

- [ ] Create or identify VPC
  ```bash
  aws ec2 describe-vpcs
  # Note the VPC ID
  ```

- [ ] Identify subnets for your EC2 instance
  ```bash
  aws ec2 describe-subnets --vpc-ids vpc-xxxxx
  # Choose private subnet in a specific AZ
  ```

- [ ] Create security group for failover script instance
  ```bash
  aws ec2 create-security-group \
    --group-name failover-script-sg \
    --description "Security group for failover script" \
    --vpc-id vpc-xxxxx

  # Save the security group ID (sg-xxxxx)
  ```

- [ ] Configure security group rules
  ```bash
  # Allow SSH from your location (for management)
  aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32

  # Allow outbound to AWS APIs (usually default)
  # Allow outbound to on-premises if needed (cross-datacenter calls)
  ```

- [ ] Plan IP addressing
  ```
  EC2 instance IP: 10.0.X.X (from private subnet)
  DNS name: failover-script.internal (optional)
  Elastic IP: Not needed (stays within VPC)
  ```

### ☑️ 2. Create IAM Role for EC2 Instance

**Create role with minimal permissions:**

- [ ] Create IAM role
  ```bash
  aws iam create-role \
    --role-name failover-script-ec2-role \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'
  ```

- [ ] Create IAM policy with your script's permissions
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "EC2Management",
        "Effect": "Allow",
        "Action": [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ec2:RebootInstances"
        ],
        "Resource": "*"
      },
      {
        "Sid": "Route53Updates",
        "Effect": "Allow",
        "Action": [
          "route53:ChangeResourceRecordSets",
          "route53:ListResourceRecordSets"
        ],
        "Resource": "arn:aws:route53:::hostedzone/Z1234567890ABC"
      },
      {
        "Sid": "RDSFailover",
        "Effect": "Allow",
        "Action": [
          "rds:DescribeDBInstances",
          "rds:FailoverDBCluster"
        ],
        "Resource": "*"
      },
      {
        "Sid": "SNSNotifications",
        "Effect": "Allow",
        "Action": ["sns:Publish"],
        "Resource": "arn:aws:sns:us-east-1:123456789012:failover-alerts"
      },
      {
        "Sid": "CloudWatchLogs",
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:us-east-1:123456789012:log-group:/failover/*"
      },
      {
        "Sid": "SSMCommand",
        "Effect": "Allow",
        "Action": [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation"
        ],
        "Resource": "*"
      },
      {
        "Sid": "DynamoDBState",
        "Effect": "Allow",
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ],
        "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/failover-state"
      },
      {
        "Sid": "SecretsManager",
        "Effect": "Allow",
        "Action": ["secretsmanager:GetSecretValue"],
        "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:failover/*"
      }
    ]
  }
  ```

- [ ] Attach policy to role
  ```bash
  aws iam put-role-policy \
    --role-name failover-script-ec2-role \
    --policy-name failover-script-policy \
    --policy-document file://policy.json
  ```

- [ ] Create instance profile
  ```bash
  aws iam create-instance-profile \
    --instance-profile-name failover-script-profile

  aws iam add-role-to-instance-profile \
    --instance-profile-name failover-script-profile \
    --role-name failover-script-ec2-role
  ```

### ☑️ 3. Create AWS Resources (DynamoDB, S3, etc.)

**Create state storage:**

- [ ] Create DynamoDB table for state
  ```bash
  aws dynamodb create-table \
    --table-name failover-state \
    --attribute-definitions AttributeName=resource_id,AttributeType=S \
    --key-schema AttributeName=resource_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

  # Add TTL for auto-cleanup
  aws dynamodb update-time-to-live \
    --table-name failover-state \
    --time-to-live-specification "AttributeName=expiration,Enabled=true"
  ```

- [ ] Create S3 bucket for logs (if needed)
  ```bash
  aws s3api create-bucket \
    --bucket failover-script-logs-$(date +%s) \
    --region us-east-1
  ```

- [ ] Create SNS topic for alerts
  ```bash
  aws sns create-topic --name failover-alerts
  # Subscribe to email/SMS
  ```

- [ ] Create CloudWatch Log Group
  ```bash
  aws logs create-log-group --log-group-name /failover/script
  ```

---

## Option A: Migrate to EC2 Instance

### ☑️ 4A. Launch EC2 Instance

**Choose the right instance type:**

```bash
# For most failover scripts: t3.small or t3.medium
# t3.small:   1 vCPU, 2 GB memory, ~$10/month
# t3.medium:  2 vCPU, 4 GB memory, ~$20/month
# t3.large:   2 vCPU, 8 GB memory, ~$40/month

# Choose Amazon Linux 2 or Ubuntu 22.04 LTS
# Both are well-supported and lightweight
```

- [ ] Get latest AMI ID
  ```bash
  # Amazon Linux 2
  aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text

  # Ubuntu 22.04 LTS
  aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text
  ```

- [ ] Launch EC2 instance
  ```bash
  aws ec2 run-instances \
    --image-id ami-xxxxxxxxx \
    --instance-type t3.small \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxx \
    --subnet-id subnet-xxxxx \
    --iam-instance-profile Name=failover-script-profile \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=failover-script},{Key=Environment,Value=production}]' \
    --monitoring Enabled=true

  # Save the instance ID (i-xxxxxxxxxxxxx)
  ```

- [ ] Wait for instance to start
  ```bash
  aws ec2 wait instance-running --instance-ids i-xxxxx

  # Get instance details
  aws ec2 describe-instances --instance-ids i-xxxxx
  ```

- [ ] Assign Elastic IP (optional, if you need fixed IP)
  ```bash
  aws ec2 allocate-address --domain vpc
  aws ec2 associate-address \
    --instance-id i-xxxxx \
    --allocation-id eipalloc-xxxxx
  ```

### ☑️ 5A. Set Up EC2 Instance

**SSH into instance and prepare it:**

- [ ] SSH into instance
  ```bash
  # Get instance IP
  INSTANCE_IP=$(aws ec2 describe-instances \
    --instance-ids i-xxxxx \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
    --output text)

  ssh -i your-key.pem ec2-user@$INSTANCE_IP  # Amazon Linux 2
  # or
  ssh -i your-key.pem ubuntu@$INSTANCE_IP    # Ubuntu
  ```

- [ ] Update system packages
  ```bash
  # Amazon Linux 2
  sudo yum update -y
  sudo yum install -y python3 python3-pip git

  # Ubuntu
  sudo apt-get update
  sudo apt-get upgrade -y
  sudo apt-get install -y python3 python3-pip git
  ```

- [ ] Install Python dependencies
  ```bash
  # Install boto3 and other dependencies
  sudo pip3 install boto3 paramiko requests PyYAML
  ```

- [ ] Create directory for failover script
  ```bash
  sudo mkdir -p /opt/failover-script
  sudo chown ec2-user:ec2-user /opt/failover-script
  ```

- [ ] Create log directory
  ```bash
  sudo mkdir -p /var/log/failover
  sudo chown ec2-user:ec2-user /var/log/failover
  ```

- [ ] Install CloudWatch agent (optional)
  ```bash
  # Download agent
  wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm

  # Amazon Linux 2
  sudo rpm -U ./amazon-cloudwatch-agent.rpm

  # Ubuntu
  # wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
  # sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
  ```

### ☑️ 6A. Migrate Script to EC2

**Copy script and update for AWS environment:**

- [ ] Copy script to EC2
  ```bash
  # From your local machine
  scp -i your-key.pem /path/to/failover_script.py \
    ec2-user@$INSTANCE_IP:/opt/failover-script/

  # Or from EC2, clone from Git
  cd /opt/failover-script
  git clone https://your-repo/failover-script.git .
  ```

- [ ] Update script for AWS (see Code Migration Checklist below)

- [ ] Create config file for AWS environment
  ```bash
  cat > /opt/failover-script/config.aws.yaml << 'EOF'
  # AWS Configuration
  aws:
    region: us-east-1
    profile: default  # Uses IAM instance profile

  # Resources to monitor
  resources:
    primary:
      type: ec2
      instance_id: i-primary123
    backup:
      type: ec2
      instance_id: i-backup456

  # Route53 DNS update
  route53:
    hosted_zone_id: Z1234567890ABC
    record_name: myapp.example.com
    ttl: 60

  # SNS alerts
  sns:
    topic_arn: arn:aws:sns:us-east-1:123456789012:failover-alerts

  # Monitoring
  monitoring:
    health_check_interval: 60  # seconds
    failure_threshold: 3        # fail after 3 checks
    log_level: INFO
    log_file: /var/log/failover/script.log

  # State storage
  state:
    backend: dynamodb
    table_name: failover-state
  EOF
  ```

- [ ] Test script runs without errors
  ```bash
  cd /opt/failover-script
  python3 failover_script.py --config config.aws.yaml --dry-run
  # Should complete without errors
  ```

### ☑️ 7A. Set Up Systemd Service

**Make script run as system service:**

- [ ] Create systemd service file
  ```bash
  sudo cat > /etc/systemd/system/failover-script.service << 'EOF'
  [Unit]
  Description=AWS Failover Script
  After=network.target
  StartLimitInterval=600
  StartLimitBurst=3

  [Service]
  Type=simple
  User=ec2-user
  WorkingDirectory=/opt/failover-script
  ExecStart=/usr/bin/python3 /opt/failover-script/failover_script.py --config /opt/failover-script/config.aws.yaml

  # Restart on failure
  Restart=on-failure
  RestartSec=30

  # Environment
  Environment="PATH=/usr/local/bin:/usr/bin:/bin"
  Environment="AWS_DEFAULT_REGION=us-east-1"

  # Logging
  StandardOutput=journal
  StandardError=journal
  SyslogIdentifier=failover-script

  # Resource limits
  MemoryLimit=512M
  CPUQuota=50%

  [Install]
  WantedBy=multi-user.target
  EOF
  ```

- [ ] Enable and start service
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable failover-script
  sudo systemctl start failover-script
  ```

- [ ] Verify service is running
  ```bash
  sudo systemctl status failover-script

  # View logs
  sudo journalctl -u failover-script -f
  ```

### ☑️ 8A. Set Up Monitoring & Log Streaming

**Configure CloudWatch monitoring:**

- [ ] Create CloudWatch agent config
  ```bash
  cat > /opt/aws-cloudwatch-agent.json << 'EOF'
  {
    "metrics": {
      "namespace": "FailoverScript",
      "metrics_collected": {
        "cpu": {
          "measurement": [
            {
              "name": "cpu_usage_idle",
              "rename": "CPU_IDLE",
              "unit": "Percent"
            }
          ],
          "totalcpu": false
        },
        "mem": {
          "measurement": [
            {
              "name": "mem_used_percent",
              "rename": "MEM_USED",
              "unit": "Percent"
            }
          ]
        },
        "disk": {
          "measurement": [
            {
              "name": "used_percent",
              "rename": "DISK_USED",
              "unit": "Percent"
            }
          ],
          "resources": ["/"]
        }
      }
    },
    "logs": {
      "logs_collected": {
        "files": {
          "collect_list": [
            {
              "file_path": "/var/log/failover/script.log",
              "log_group_name": "/failover/script",
              "log_stream_name": "{instance_id}"
            }
          ]
        }
      }
    }
  }
  EOF
  ```

- [ ] Start CloudWatch agent
  ```bash
  /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws-cloudwatch-agent.json
  ```

- [ ] Create CloudWatch alarms
  ```bash
  # Alarm if script stops writing logs
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-script-heartbeat \
    --alarm-description "Alert if failover script stops" \
    --metric-name IncomingLogEvents \
    --namespace AWS/Logs \
    --statistic Sum \
    --period 600 \
    --threshold 1 \
    --comparison-operator LessThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:failover-alerts

  # Alarm if CPU usage high
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-script-high-cpu \
    --alarm-description "Alert if script using too much CPU" \
    --metric-name CPU_IDLE \
    --namespace FailoverScript \
    --statistic Average \
    --period 300 \
    --threshold 20 \
    --comparison-operator LessThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:failover-alerts
  ```

---

## Option B: Migrate to AWS Lambda

### ☑️ 4B. Assess Script for Lambda Compatibility

**Check if your script can run on Lambda:**

- [ ] Verify execution time < 15 minutes
  ```bash
  # Time your script
  time python3 /opt/failover-script/failover_script.py

  # If takes > 10 min, use EC2 instead
  # Lambda has 15 min timeout, but leave buffer
  ```

- [ ] Verify memory usage < 3 GB
  ```bash
  # Monitor memory during execution
  ps aux | grep failover_script

  # Or use memory profiler
  pip install memory_profiler
  python3 -m memory_profiler failover_script.py
  ```

- [ ] Check for incompatible dependencies
  ```bash
  # Lambda supports these libraries:
  ✅ boto3
  ✅ requests
  ✅ paramiko
  ✅ PyYAML
  ✅ psycopg2
  ✅ Most common packages

  # Lambda does NOT support:
  ❌ GUI libraries (Qt, Tkinter)
  ❌ Large compiled packages
  ❌ Custom system libraries
  ```

- [ ] Verify no persistent state needed
  ```bash
  # Check if script uses:
  # /var/lib/failover/state.txt - NO! Use DynamoDB instead
  # /var/log/failover.log - NO! Use CloudWatch Logs instead
  # /etc/failover/config - NO! Use Parameter Store instead
  ```

### ☑️ 5B. Refactor Script for Lambda

**Make script Lambda-compatible:**

- [ ] Create Lambda handler function
  ```python
  # failover_lambda.py

  import boto3
  import json
  import logging
  from datetime import datetime

  # Set up logging
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  # AWS clients (reuse connections)
  ec2 = boto3.client('ec2')
  route53 = boto3.client('route53')
  sns = boto3.client('sns')
  dynamodb = boto3.resource('dynamodb')

  def lambda_handler(event, context):
      """
      Lambda handler - entry point for function

      Args:
          event: Trigger event (from EventBridge or manual invoke)
          context: Lambda context object

      Returns:
          Response dict with statusCode and body
      """

      try:
          logger.info(f"Starting failover check at {datetime.utcnow()}")

          # Get configuration from environment variables
          primary_instance_id = os.environ['PRIMARY_INSTANCE_ID']
          backup_instance_id = os.environ['BACKUP_INSTANCE_ID']
          hosted_zone_id = os.environ['ROUTE53_ZONE_ID']
          sns_topic_arn = os.environ['SNS_TOPIC_ARN']

          # Check primary status
          is_primary_healthy = check_primary_status(primary_instance_id)
          logger.info(f"Primary healthy: {is_primary_healthy}")

          if not is_primary_healthy:
              # Execute failover
              result = execute_failover(
                  primary_instance_id,
                  backup_instance_id,
                  hosted_zone_id,
                  sns_topic_arn
              )

              return {
                  'statusCode': 200,
                  'body': json.dumps({
                      'status': 'failover_executed',
                      'result': result
                  })
              }
          else:
              # Primary is healthy
              return {
                  'statusCode': 200,
                  'body': json.dumps({
                      'status': 'healthy',
                      'message': 'Primary is healthy'
                  })
              }

      except Exception as e:
          logger.error(f"Error in failover check: {str(e)}", exc_info=True)

          # Send alert on error
          send_sns_alert(
              topic_arn=os.environ['SNS_TOPIC_ARN'],
              subject='Failover Script Error',
              message=f"Error: {str(e)}"
          )

          return {
              'statusCode': 500,
              'body': json.dumps({
                  'error': str(e)
              })
          }

  def check_primary_status(instance_id):
      """Check if primary EC2 instance is healthy"""

      try:
          response = ec2.describe_instance_status(
              InstanceIds=[instance_id],
              IncludeAllInstances=False
          )

          if not response['InstanceStatuses']:
              return False

          status = response['InstanceStatuses'][0]

          # Check both system status and instance status
          system_ok = status['SystemStatus']['Status'] == 'ok'
          instance_ok = status['InstanceStatus']['Status'] == 'ok'

          return system_ok and instance_ok

      except Exception as e:
          logger.error(f"Error checking primary: {str(e)}")
          return False

  def execute_failover(primary_id, backup_id, zone_id, topic_arn):
      """Execute failover to backup instance"""

      try:
          # 1. Start backup instance if not running
          logger.info(f"Starting backup instance {backup_id}")
          ec2.start_instances(InstanceIds=[backup_id])

          # 2. Get backup instance details
          response = ec2.describe_instances(InstanceIds=[backup_id])
          backup_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']

          # 3. Update Route53 DNS
          logger.info(f"Updating DNS to {backup_ip}")
          update_route53(zone_id, 'myapp.example.com', backup_ip)

          # 4. Send SNS alert
          send_sns_alert(
              topic_arn=topic_arn,
              subject='Failover Executed',
              message=f'Failover from {primary_id} to {backup_id}'
          )

          # 5. Store failover event in DynamoDB
          store_failover_event(primary_id, backup_id)

          return {
              'primary': primary_id,
              'backup': backup_id,
              'backup_ip': backup_ip,
              'timestamp': datetime.utcnow().isoformat()
          }

      except Exception as e:
          logger.error(f"Error during failover: {str(e)}", exc_info=True)
          raise

  def update_route53(zone_id, record_name, ip_address):
      """Update Route53 DNS record"""

      route53.change_resource_record_sets(
          HostedZoneId=zone_id,
          ChangeBatch={
              'Changes': [{
                  'Action': 'UPSERT',
                  'ResourceRecordSet': {
                      'Name': record_name,
                      'Type': 'A',
                      'TTL': 60,
                      'ResourceRecords': [{'Value': ip_address}]
                  }
              }]
          }
      )
      logger.info(f"Updated {record_name} to {ip_address}")

  def send_sns_alert(topic_arn, subject, message):
      """Send SNS alert"""

      sns.publish(
          TopicArn=topic_arn,
          Subject=subject,
          Message=message
      )
      logger.info(f"Sent alert: {subject}")

  def store_failover_event(primary_id, backup_id):
      """Store failover event in DynamoDB"""

      table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'failover-events'))

      table.put_item(
          Item={
              'event_id': f"{datetime.utcnow().isoformat()}_{primary_id}",
              'timestamp': datetime.utcnow().isoformat(),
              'primary_instance': primary_id,
              'backup_instance': backup_id,
              'status': 'success'
          }
      )
      logger.info("Failover event stored")
  ```

- [ ] Move configuration to environment variables
  ```bash
  # Instead of config file, use Lambda environment variables

  Environment variables in Lambda:
  - PRIMARY_INSTANCE_ID: i-primary123
  - BACKUP_INSTANCE_ID: i-backup456
  - ROUTE53_ZONE_ID: Z1234567890ABC
  - SNS_TOPIC_ARN: arn:aws:sns:us-east-1:123456789012:alerts
  - DYNAMODB_TABLE: failover-events
  - LOG_LEVEL: INFO
  ```

### ☑️ 6B. Create Lambda Deployment Package

**Package script for Lambda:**

- [ ] Create deployment directory
  ```bash
  mkdir lambda-deployment
  cd lambda-deployment
  ```

- [ ] Copy script and dependencies
  ```bash
  # Copy handler function
  cp failover_lambda.py .

  # Install dependencies to package
  pip install -r requirements.txt -t .
  # (requirements.txt contains: boto3, paramiko, requests, pyyaml)
  ```

- [ ] Create deployment ZIP
  ```bash
  zip -r failover-lambda.zip .
  # Should be < 50 MB (Lambda limit 250 MB)

  ls -lh failover-lambda.zip
  ```

- [ ] Upload to S3 (optional, for large packages)
  ```bash
  # Only needed if > 50 MB
  aws s3 cp failover-lambda.zip s3://your-bucket/
  ```

### ☑️ 7B. Create Lambda Function

**Deploy function to AWS:**

- [ ] Create Lambda function
  ```bash
  aws lambda create-function \
    --function-name failover-script \
    --runtime python3.11 \
    --role arn:aws:iam::123456789012:role/lambda-failover-role \
    --handler failover_lambda.lambda_handler \
    --zip-file fileb://failover-lambda.zip \
    --timeout 300 \
    --memory-size 256 \
    --environment Variables='{
      PRIMARY_INSTANCE_ID=i-primary123,
      BACKUP_INSTANCE_ID=i-backup456,
      ROUTE53_ZONE_ID=Z1234567890ABC,
      SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:alerts,
      DYNAMODB_TABLE=failover-events,
      LOG_LEVEL=INFO
    }'
  ```

- [ ] Create EventBridge trigger (for periodic execution)
  ```bash
  # Create EventBridge rule
  aws events put-rule \
    --name failover-script-trigger \
    --schedule-expression "rate(5 minutes)" \
    --state ENABLED \
    --description "Trigger failover script every 5 minutes"

  # Add Lambda as target
  aws events put-targets \
    --rule failover-script-trigger \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:failover-script","RoleArn"="arn:aws:iam::123456789012:role/eventbridge-role"

  # Grant Lambda permission
  aws lambda add-permission \
    --function-name failover-script \
    --statement-id AllowEventBridge \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:123456789012:rule/failover-script-trigger
  ```

### ☑️ 8B. Set Up Lambda Monitoring

**Configure CloudWatch alarms:**

- [ ] Create Lambda error alarm
  ```bash
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-lambda-errors \
    --alarm-description "Alert if Lambda function errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --dimensions Name=FunctionName,Value=failover-script \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:failover-alerts
  ```

- [ ] Create invocation timeout alarm
  ```bash
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-lambda-timeout \
    --alarm-description "Alert if Lambda times out" \
    --metric-name Duration \
    --namespace AWS/Lambda \
    --dimensions Name=FunctionName,Value=failover-script \
    --statistic Maximum \
    --period 300 \
    --threshold 280000 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:failover-alerts
  ```

- [ ] Create missing invocation alarm
  ```bash
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-lambda-missing-invocation \
    --alarm-description "Alert if Lambda doesn't run" \
    --metric-name Invocations \
    --namespace AWS/Lambda \
    --dimensions Name=FunctionName,Value=failover-script \
    --statistic Sum \
    --period 600 \
    --threshold 0 \
    --comparison-operator LessThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:failover-alerts
  ```

---

## Code Migration Checklist

### ☑️ 9. Update Python Code for AWS

**Modify your brownfield script:**

**Changes Needed:**

| On-Premises | AWS (EC2) | AWS (Lambda) |
|-------------|-----------|--------------|
| `import paramiko` | Keep (SSH) | Keep (SSM instead) |
| Direct file I/O | Keep | Use DynamoDB/S3 |
| System commands | Keep | Use Systems Manager |
| Local logging | CloudWatch Logs | CloudWatch Logs |
| Environment files | Config file (YAML) | Environment variables |
| Direct server access | AWS API (boto3) | AWS API (boto3) |
| Email alerts | SNS | SNS |
| State files | DynamoDB/Parameter Store | DynamoDB |
| Continuous loop | While True | Lambda handler |
| Sleep intervals | time.sleep(60) | EventBridge schedule |

**Code Diff - Key Changes:**

```python
# BEFORE (On-Premises)
import paramiko
import subprocess
import os

def monitor_primary():
    """Check on-premises primary via ping"""
    result = subprocess.run(['ping', '-c', '1', '192.168.1.10'],
                          capture_output=True, timeout=5)
    return result.returncode == 0

def failover():
    """SSH to backup and restart service"""
    ssh = paramiko.SSHClient()
    ssh.connect('backup.local')
    ssh.exec_command('systemctl restart myapp')
    ssh.close()

# Main loop
while True:
    if not monitor_primary():
        failover()
        send_email_alert('Failover executed')
    time.sleep(60)

# AFTER (AWS EC2)
import boto3
import logging

ec2 = boto3.client('ec2')
route53 = boto3.client('route53')
sns = boto3.client('sns')
logger = logging.getLogger(__name__)

def monitor_primary():
    """Check AWS primary EC2 status"""
    response = ec2.describe_instance_status(
        InstanceIds=[os.environ['PRIMARY_INSTANCE_ID']],
        IncludeAllInstances=False
    )

    if not response['InstanceStatuses']:
        return False

    status = response['InstanceStatuses'][0]
    return (status['SystemStatus']['Status'] == 'ok' and
            status['InstanceStatus']['Status'] == 'ok')

def failover():
    """Failover to AWS backup instance"""
    # Start backup
    ec2.start_instances(InstanceIds=[os.environ['BACKUP_INSTANCE_ID']])

    # Update Route53
    route53.change_resource_record_sets(
        HostedZoneId=os.environ['ROUTE53_ZONE_ID'],
        ChangeBatch={'Changes': [{
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': 'myapp.example.com',
                'Type': 'A',
                'TTL': 60,
                'ResourceRecords': [{'Value': os.environ['BACKUP_IP']}]
            }
        }]}
    )

    # Send alert
    sns.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Subject='Failover Executed',
        Message='Failover to backup'
    )

# Main loop (for EC2)
import time
while True:
    if not monitor_primary():
        logger.warning('Primary down, executing failover')
        failover()
    time.sleep(60)

# Handler (for Lambda)
def lambda_handler(event, context):
    if not monitor_primary():
        failover()
    return {'statusCode': 200, 'body': 'Check complete'}
```

### ☑️ 10. Handle Configuration & Secrets

**Move from config files to AWS services:**

```python
# BEFORE (On-Premises - bad practice)
CONFIG = {
    'primary_ip': '192.168.1.10',
    'backup_ip': '192.168.1.20',
    'db_password': 'mypassword123',  # ❌ BAD
}

# AFTER (AWS - best practice)
import os
from botocore.exceptions import ClientError

def get_config():
    """Load config from environment variables"""
    return {
        'primary_instance_id': os.environ['PRIMARY_INSTANCE_ID'],
        'backup_instance_id': os.environ['BACKUP_INSTANCE_ID'],
        'route53_zone_id': os.environ['ROUTE53_ZONE_ID'],
        'sns_topic_arn': os.environ['SNS_TOPIC_ARN'],
    }

def get_secret(secret_name):
    """Get secret from AWS Secrets Manager"""
    secrets_client = boto3.client('secretsmanager')

    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise

# Use it
db_credentials = get_secret('myapp/db-password')
db_password = db_credentials['password']
```

---

## Testing & Validation

### ☑️ 11. Test Script Before Production

**For EC2:**

- [ ] Test script runs locally
  ```bash
  python3 failover_script.py --config config.aws.yaml --dry-run
  ```

- [ ] Test systemd service
  ```bash
  sudo systemctl start failover-script
  sudo systemctl status failover-script
  sudo journalctl -u failover-script -n 50
  ```

- [ ] Test failover logic
  ```bash
  # Simulate primary failure
  # Stop primary EC2 instance
  aws ec2 stop-instances --instance-ids i-primary123

  # Wait for script to detect and failover
  # Verify backup instance starts
  # Verify DNS updated
  # Verify alert sent
  ```

**For Lambda:**

- [ ] Test handler locally
  ```bash
  # Create test event
  cat > test-event.json << 'EOF'
  {
    "detail-type": "Scheduled Event",
    "source": "aws.events"
  }
  EOF

  # Invoke locally (requires SAM CLI)
  sam local invoke failover-script -e test-event.json
  ```

- [ ] Test in AWS Lambda console
  ```bash
  # Go to Lambda console
  # Click Test tab
  # Create test event
  # Click Test
  # View logs
  ```

- [ ] Test EventBridge trigger
  ```bash
  # Check CloudWatch Logs
  aws logs tail /aws/lambda/failover-script --follow

  # Should see invocations every 5 minutes
  ```

---

## Deployment Steps

### ☑️ 12. Deploy to Production

**Blue-Green Deployment (Recommended):**

**Week 1: Parallel Run**
```
On-Premises (Green)  ← Active
    ↓
Monitoring both resources

AWS (Blue)           ← New
    ↓
Passive (monitoring only, not triggering failover)
```

- [ ] Deploy to AWS (EC2 or Lambda)
- [ ] Verify it's monitoring correctly
- [ ] Let it run for 1 week without executing failover
- [ ] Monitor logs for errors

**Week 2: Gradual Activation**
```
On-Premises (Green)  ← Still active
    ↓
Both monitoring and can trigger failover

AWS (Blue)           ← Gradually active
    ↓
Monitoring and starting to trigger failover
```

- [ ] Enable failover execution on AWS
- [ ] Test failover scenarios
- [ ] Verify it executes correctly

**Week 3+: Switch to AWS**
```
On-Premises (Green)  ← Backup only
    ↓
Monitoring only (no failover execution)

AWS (Blue)           ← Active
    ↓
Monitoring and triggering failover
```

- [ ] Disable failover on on-premises
- [ ] Monitor AWS version for 1+ weeks
- [ ] Keep on-premises running as backup

**Weeks 4+: Retire On-Premises**
```
AWS (Blue)  ← Only version running
    ↓
Full responsibility
```

- [ ] Stop on-premises failover script
- [ ] Archive on-premises setup
- [ ] Document migration

---

## Monitoring & Troubleshooting

### ☑️ 13. Monitor in Production

**EC2 Monitoring:**

```bash
# View logs
sudo journalctl -u failover-script -f

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --metric-name CPU_IDLE \
  --namespace FailoverScript \
  --dimensions Name=InstanceId,Value=i-xxxxx \
  --start-time 2024-03-09T00:00:00Z \
  --end-time 2024-03-10T00:00:00Z \
  --period 300 \
  --statistics Average
```

**Lambda Monitoring:**

```bash
# View logs
aws logs tail /aws/lambda/failover-script --follow

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=failover-script \
  --start-time 2024-03-09T00:00:00Z \
  --end-time 2024-03-10T00:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

**Common Issues:**

| Issue | EC2 Solution | Lambda Solution |
|-------|------------|-----------------|
| **Script not running** | `sudo systemctl start failover-script` | Check EventBridge rule enabled |
| **No logs** | Check `/var/log/failover/` | Check CloudWatch Logs |
| **High latency** | Check CloudWatch metrics | Check function duration |
| **Permission denied** | Check IAM role attached | Check Lambda execution role |
| **Memory error** | Increase instance size | Increase Lambda memory |
| **Timeout** | Increase timeout in systemd | Increase Lambda timeout |

---

## Rollback Procedures

### ☑️ 14. Rollback to On-Premises

**If AWS deployment fails:**

**For EC2:**

```bash
# 1. Stop failover on AWS
ssh ec2-user@failover-instance
sudo systemctl stop failover-script

# 2. Re-enable on-premises
ssh on-prem-server
sudo systemctl start failover-script

# 3. Verify on-premises is handling failover
tail -f /var/log/failover.log
# Should see monitoring messages

# 4. Restore DNS (if changed)
# Update Route53 to point back to on-premises

# 5. Investigate issue
# Review AWS logs and on-premises logs
```

**For Lambda:**

```bash
# 1. Disable Lambda trigger
aws events disable-rule --name failover-script-trigger

# 2. Enable on-premises
ssh on-prem-server
sudo systemctl start failover-script

# 3. Verify on-premises is active
tail -f /var/log/failover.log

# 4. Once stable, investigate Lambda issue
aws logs tail /aws/lambda/failover-script --follow
```

---

## Quick Comparison Table

### Decision Helper

```
┌─────────────────────────┬──────────────────────┬──────────────────────┐
│ Factor                  │ EC2 Instance         │ AWS Lambda           │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ Setup Complexity        │ Medium               │ Low                  │
│ Operational Overhead    │ Medium               │ Low                  │
│ Cost per Month          │ $10-30 (fixed)       │ $1-5 (pay-per-call)  │
│ Execution Time          │ Any length           │ Max 15 minutes       │
│ Configuration           │ Config file + env    │ Environment vars     │
│ Monitoring              │ CloudWatch + logs    │ CloudWatch (built-in)│
│ Failover Latency        │ 5-10 seconds         │ 30-60 seconds        │
│ State Management        │ Local files OK       │ DynamoDB required    │
│ Logging                 │ Local + CloudWatch   │ CloudWatch only      │
│ Your Script Complexity  │ Any                  │ Simple to moderate   │
│ Team Preference         │ Traditional servers  │ Serverless           │
│ Ready for Production    │ Now                  │ After refactoring    │
└─────────────────────────┴──────────────────────┴──────────────────────┘
```

### Recommendation

**Choose EC2 if:**
- Your script is complex
- Execution time varies widely
- You prefer traditional operations
- You want minimal code changes
- Cost is not a major concern

**Choose Lambda if:**
- Your script is simple (monitor + action)
- Execution time is consistent < 5 min
- You want minimal operational overhead
- You prefer pay-per-use pricing
- Your team is serverless-oriented

---

## Next Steps

1. **Decision:** EC2 or Lambda? (See comparison above)
2. **For EC2:**
   - Follow sections 4A-8A
   - Deploy to production using blue-green strategy

3. **For Lambda:**
   - Follow sections 4B-8B
   - Refactor script first
   - Deploy function and trigger

4. **Testing:** Section 11 (test before production)
5. **Deployment:** Section 12 (blue-green, 3-4 weeks)
6. **Monitoring:** Section 13 (ongoing)
7. **Rollback:** Section 14 (if needed)

---

**Good luck with your migration!** 🚀
