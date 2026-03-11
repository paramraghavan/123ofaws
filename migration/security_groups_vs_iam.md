# Security Groups vs IAM for Failover Scripts

**Do you really need to create security groups if your EC2 has an IAM service role with full AWS permissions?**

---

## TL;DR

- **IAM Service Role** = What API calls you can make (boto3, AWS SDK)
- **Security Groups** = What network traffic can physically flow in/out

You don't need security groups **only if your failover script** calls AWS APIs and doesn't directly connect to:
- RDS/Databases
- ElastiCache/Redis
- Other EC2 instances (SSH)
- Internal webhooks/APIs

---

## The Core Difference Explained

### Example: Checking EC2 Status

```python
import boto3

ec2 = boto3.client('ec2')

# This call works WITHOUT any security group rules
instances = ec2.describe_instances(InstanceIds=['i-primary'])
primary_status = instances['Reservations'][0]['Instances'][0]['State']['Name']
```

**Why it works:**
- You're calling AWS public API endpoint
- Traffic goes: EC2 → Internet → AWS API Gateway
- No security group needed (public internet)
- IAM role is what authorizes the call

### Example: SSH to Another EC2

```python
import paramiko

ssh = paramiko.SSHClient()
ssh.connect('10.0.2.20', username='ec2-user', port=22)
# This times out without security group!
```

**Why it fails:**
- You're making a network connection on port 22
- Traffic tries to go: EC2 (10.0.1.10) → Internal network → EC2 (10.0.2.20):22
- Security group on target EC2 blocks this
- IAM role doesn't help with network blocking

---

## When You DON'T Need Security Groups

### ✅ Case 1: Using Only AWS APIs (RECOMMENDED)

Your failover script only calls boto3:

```python
import boto3

def failover_script():
    # AWS API calls - NO security groups needed
    ec2 = boto3.client('ec2')
    route53 = boto3.client('route53')
    sns = boto3.client('sns')
    ssm = boto3.client('ssm')
    cloudwatch = boto3.client('cloudwatch')

    # Check primary EC2 status
    instances = ec2.describe_instances(InstanceIds=['i-primary'])
    state = instances['Reservations'][0]['Instances'][0]['State']['Name']

    if state != 'running':
        # Start backup EC2
        ec2.start_instances(InstanceIds=['i-backup'])

        # Execute command on backup via Systems Manager
        # (not SSH - no port 22 needed)
        ssm.send_command(
            InstanceIds=['i-backup'],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': ['systemctl restart myapp']}
        )

        # Update DNS in Route 53
        route53.change_resource_record_sets(
            HostedZoneId='Z1234567890ABC',
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'app.example.com',
                        'Type': 'A',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': '10.0.3.10'}]
                    }
                }]
            }
        )

        # Send alert
        sns.publish(
            TopicArn='arn:aws:sns:region:account:alerts',
            Subject='Failover Executed',
            Message='Primary is down, backup activated'
        )

        # Log to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='CustomMonitoring',
            MetricData=[{
                'MetricName': 'FailoverExecuted',
                'Value': 1,
                'Unit': 'Count'
            }]
        )

# Security groups needed: NONE (only AWS public APIs)
```

**What your monitoring EC2 needs:**
- ✅ IAM service role with EC2, Route 53, SNS, SSM, CloudWatch permissions
- ✅ VPC with internet access (NAT Gateway or public IP)
- ✅ Network ACLs allowing outbound 443 (HTTPS)
- ❌ **No special security groups**

---

### ✅ Case 2: Using Systems Manager Instead of SSH

```python
import boto3

def restart_app_on_backup():
    """Restart app without SSH"""
    ssm = boto3.client('ssm')

    # Execute command on remote EC2
    # Uses Systems Manager - NO SSH needed
    response = ssm.send_command(
        InstanceIds=['i-backup'],
        DocumentName='AWS-RunShellScript',
        Parameters={
            'commands': [
                'systemctl stop myapp',
                'systemctl start myapp'
            ]
        }
    )

    # Check command status
    command_id = response['Command']['CommandId']
    command_output = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId='i-backup'
    )

    return command_output['StandardOutputContent']

# Security groups needed: NONE
# Why? Systems Manager uses AWS APIs, not SSH
```

**Bonus: Systems Manager advantages:**
- No SSH keys needed
- No port 22 to manage
- Logging built into CloudWatch
- Works across regions
- No bastion host needed

---

## When You DO Need Security Groups

### ❌ Case 1: Directly Connecting to RDS

```python
import pymysql

def check_database_health():
    """Direct connection to RDS"""
    connection = pymysql.connect(
        host='mydb.c9akciq32.us-east-1.rds.amazonaws.com',
        port=3306,
        user='admin',
        password='password',
        database='mydb'
    )
    # ❌ TIMES OUT without security group rule!
```

**What's blocking you:**
- Not IAM (you have permission)
- Network traffic on port 3306 is blocked
- RDS security group blocks inbound from your EC2

**Fix:**
```bash
# Add inbound rule to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds \
  --protocol tcp \
  --port 3306 \
  --source-security-group-id sg-monitoring-ec2

# Or allow all traffic from monitoring EC2
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds \
  --protocol all \
  --source-security-group-id sg-monitoring-ec2
```

**Better approach:** Don't directly connect to RDS
```python
import boto3

def check_database_health_via_api():
    """Use RDS API instead of direct connection"""
    rds = boto3.client('rds')

    # Check RDS status via API (no direct connection needed)
    databases = rds.describe_db_instances(
        DBInstanceIdentifier='mydb'
    )

    db_status = databases['DBInstances'][0]['DBInstanceStatus']
    # Returns: 'available', 'backing-up', 'failed', etc.

    return db_status

# No security group needed!
```

---

### ❌ Case 2: SSH to Another EC2

```python
import paramiko

def check_primary_app_directly():
    """SSH to primary EC2"""
    ssh = paramiko.SSHClient()
    ssh.connect(
        '10.0.2.20',  # Primary EC2 private IP
        username='ec2-user',
        key_filename='/home/ec2-user/.ssh/key.pem',
        port=22
    )
    # ❌ CONNECTION REFUSED without security group!
```

**What's blocking you:**
- Primary EC2's security group doesn't allow port 22 from monitoring EC2
- IAM role doesn't help with network access

**Fix:**
```bash
# Add SSH access from monitoring EC2
aws ec2 authorize-security-group-ingress \
  --group-id sg-primary \
  --protocol tcp \
  --port 22 \
  --source-security-group-id sg-monitoring-ec2
```

**Better approach:** Use Systems Manager instead
```python
import boto3

def check_primary_app_via_ssm():
    """Use Systems Manager instead of SSH"""
    ssm = boto3.client('ssm')

    # Execute command on primary EC2
    response = ssm.send_command(
        InstanceIds=['i-primary'],
        DocumentName='AWS-RunShellScript',
        Parameters={
            'commands': [
                'systemctl is-active myapp',
                'curl localhost:8080/health'
            ]
        }
    )

    command_id = response['Command']['CommandId']

    # Get output
    output = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId='i-primary'
    )

    return output['StandardOutputContent']

# No security group needed!
# Why? Uses AWS API + IAM, not SSH
```

---

### ❌ Case 3: Calling Internal Webhook/API

```python
import requests

def check_app_health():
    """Call health endpoint on another EC2"""
    response = requests.get(
        'http://10.0.2.20:5000/health',
        timeout=5
    )
    # ❌ CONNECTION TIMEOUT without security group!
```

**What's blocking you:**
- Application EC2's security group doesn't allow port 5000
- IAM role doesn't control port access

**Fix:**
```bash
# Allow application port from monitoring EC2
aws ec2 authorize-security-group-ingress \
  --group-id sg-application \
  --protocol tcp \
  --port 5000 \
  --source-security-group-id sg-monitoring-ec2
```

**Better approach:** Expose via AWS API Gateway
```python
import boto3

def check_app_health_via_api():
    """Call health endpoint via API Gateway (not direct)"""
    apigateway = boto3.client('apigateway')

    # Get stage URL
    stage = apigateway.get_stage(
        restApiId='abc123',
        stageName='prod'
    )

    # Call via API Gateway endpoint (public internet)
    import requests
    response = requests.get(
        f"{stage['variables']['endpoint']}/health"
    )

    return response.json()

# No security group needed!
```

---

### ❌ Case 4: Direct ElastiCache/Redis Connection

```python
import redis

def check_cache_health():
    """Direct connection to ElastiCache"""
    r = redis.Redis(
        host='myredis.us-east-1.cache.amazonaws.com',
        port=6379,
        db=0
    )
    # ❌ CONNECTION TIMEOUT without security group!
```

**Fix:**
```bash
# Add inbound rule to ElastiCache security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-elasticache \
  --protocol tcp \
  --port 6379 \
  --source-security-group-id sg-monitoring-ec2
```

**Better approach:** Don't connect directly to ElastiCache
```python
import boto3

def check_cache_health_via_api():
    """Monitor ElastiCache via CloudWatch instead"""
    cloudwatch = boto3.client('cloudwatch')

    # Check cache metrics
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/ElastiCache',
        MetricName='EvictionsPersec',
        Dimensions=[{
            'Name': 'CacheClusterId',
            'Value': 'myredis'
        }],
        StartTime=datetime.utcnow() - timedelta(minutes=5),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average']
    )

    return metrics

# No security group needed!
```

---

## Decision Tree: Do I Need Security Groups?

```
Does your failover script...
│
├─ Call AWS APIs (boto3) only?
│  ├─ Yes → ✅ NO SECURITY GROUPS NEEDED
│  └─ No → Continue...
│
├─ SSH to other EC2s?
│  ├─ Yes → ❌ NEED SECURITY GROUP (port 22)
│  ├─ Use Systems Manager instead? → ✅ NO SG NEEDED
│  └─ No → Continue...
│
├─ Connect directly to RDS/Aurora?
│  ├─ Yes → ❌ NEED SECURITY GROUP (port 3306/5432)
│  ├─ Use RDS API instead? → ✅ NO SG NEEDED
│  └─ No → Continue...
│
├─ Connect directly to ElastiCache/Redis?
│  ├─ Yes → ❌ NEED SECURITY GROUP (port 6379)
│  ├─ Use CloudWatch metrics instead? → ✅ NO SG NEEDED
│  └─ No → Continue...
│
└─ Call internal webhooks/APIs?
   ├─ Yes → ❌ NEED SECURITY GROUP (app port)
   ├─ Expose via API Gateway instead? → ✅ NO SG NEEDED
   └─ No → ✅ NO SECURITY GROUPS NEEDED
```

---

## Recommended Architecture (No Security Groups Needed)

```python
import boto3
import json
from datetime import datetime

def production_failover_script():
    """
    Failover script that needs NO security groups
    Only uses boto3 (AWS APIs)
    """

    ec2 = boto3.client('ec2')
    route53 = boto3.client('route53')
    sns = boto3.client('sns')
    ssm = boto3.client('ssm')
    cloudwatch = boto3.client('cloudwatch')
    rds = boto3.client('rds')

    # 1. Check primary EC2 via API (no SSH needed)
    primary = ec2.describe_instances(
        InstanceIds=['i-primary'],
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    if not primary['Reservations']:
        print("Primary EC2 is not running - failover needed")
        failover_executed = True
    else:
        failover_executed = False

    # 2. Check primary RDS via API (no direct connection)
    try:
        rds_instance = rds.describe_db_instances(
            DBInstanceIdentifier='primary-db'
        )
        db_status = rds_instance['DBInstances'][0]['DBInstanceStatus']
        if db_status != 'available':
            print("Primary RDS is not available - failover needed")
            failover_executed = True
    except Exception as e:
        print(f"RDS check failed: {e}")
        failover_executed = True

    if failover_executed:
        # 3. Start backup EC2
        ec2.start_instances(InstanceIds=['i-backup'])

        # 4. Run failover script on backup via Systems Manager
        # (not SSH - no port 22 needed)
        ssm.send_command(
            InstanceIds=['i-backup'],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [
                    'cd /opt/failover && python3 activate_backup.py'
                ]
            }
        )

        # 5. Update DNS
        route53.change_resource_record_sets(
            HostedZoneId='Z1234567890ABC',
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': 'app.example.com',
                        'Type': 'A',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': '10.0.3.10'}]
                    }
                }]
            }
        )

        # 6. Send alert
        sns.publish(
            TopicArn='arn:aws:sns:region:account:alerts',
            Subject='🚨 Failover Executed',
            Message=json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'primary_ec2': 'i-primary',
                'backup_ec2': 'i-backup',
                'action': 'Failover activated'
            }, indent=2)
        )

        # 7. Log metrics
        cloudwatch.put_metric_data(
            Namespace='FailoverMonitoring',
            MetricData=[{
                'MetricName': 'FailoverExecuted',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            }]
        )

    return {
        'status': 'success',
        'failover_executed': failover_executed
    }

# SECURITY GROUPS NEEDED:
# - None! Only AWS APIs are called
#
# IAM ROLE NEEDED with permissions for:
# - ec2:DescribeInstances
# - rds:DescribeDBInstances
# - route53:ChangeResourceRecordSets
# - sns:Publish
# - ssm:SendCommand
# - cloudwatch:PutMetricData
```

---

## Minimal Security Group Configuration (If Needed)

If you MUST use SSH or direct database connections:

```bash
# Create security group for monitoring EC2
aws ec2 create-security-group \
  --group-name monitoring-failover-sg \
  --description "Security group for failover monitoring EC2"

SG_ID="sg-xxxxxxxx"

# Outbound rules (what monitoring EC2 can initiate)
# HTTPS to AWS APIs
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# SSH to other EC2s (if needed)
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --source-security-group-id sg-production

# MySQL/RDS (if direct connection needed)
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 3306 \
  --source-security-group-id sg-rds

# Add corresponding inbound rules to TARGET security groups
# (primary EC2, RDS, etc.)
```

---

## Summary Table

| Approach | Security Groups | SSH Key | IAM Role | Best For |
|----------|-----------------|---------|----------|----------|
| **AWS APIs only** | ❌ None | ❌ No | ✅ Yes | Modern, recommended |
| **Systems Manager** | ❌ None | ❌ No | ✅ Yes | Execution on remote EC2 |
| **API Gateway** | ❌ None | ❌ No | ✅ Yes | Health checks |
| **CloudWatch metrics** | ❌ None | ❌ No | ✅ Yes | Monitoring |
| **SSH** | ✅ Port 22 | ✅ Yes | ✅ Yes | Legacy, harder to scale |
| **Direct RDS connection** | ✅ Port 3306 | ❌ No | ✅ Yes | Legacy, use RDS API instead |

---

## Bottom Line for Your Brownfield Migration

**When migrating your failover script to AWS EC2 or Lambda:**

✅ **DO:**
- Use boto3 for all resource checks
- Use Systems Manager for remote execution
- Use CloudWatch for metrics
- Use Route 53 API for DNS changes
- Create IAM role with permissions
- Allow outbound HTTPS traffic

❌ **DON'T:**
- SSH to other EC2s (use Systems Manager)
- Connect directly to RDS (use RDS API)
- Connect directly to ElastiCache (use CloudWatch)
- Create complex security group rules
- Manage SSH keys

**Result:** Fewer security groups, simpler configuration, more secure, easier to manage

