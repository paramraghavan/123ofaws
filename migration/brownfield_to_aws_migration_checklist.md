# Brownfield to AWS EC2 Edge Node Migration Checklist

**Complete guide for migrating on-premises failover scripts to AWS EC2 with edge node considerations.**

---

## Table of Contents

1. [Overview & Key Differences](#overview--key-differences)
2. [Pre-Migration Assessment](#pre-migration-assessment)
3. [Infrastructure & Networking](#infrastructure--networking)
4. [Failover Script Migration](#failover-script-migration)
5. [IAM & Security](#iam--security)
6. [Monitoring & Logging](#monitoring--logging)
7. [Edge Node Specific](#edge-node-specific)
8. [Testing & Validation](#testing--validation)
9. [Deployment Strategy](#deployment-strategy)
10. [Rollback & Contingency](#rollback--contingency)
11. [Post-Migration](#post-migration)

---

## Overview & Key Differences

### On-Premises vs AWS

| Aspect | On-Premises | AWS EC2 |
|--------|-------------|---------|
| **Infrastructure** | Fixed, physical hardware | Elastic, virtual |
| **Networking** | Direct physical connections | VPC, Security Groups, NACLs |
| **Authentication** | Active Directory, LDAP | IAM roles, instance profiles |
| **Monitoring** | Local tools (Nagios, Zabbix) | CloudWatch, CloudTrail |
| **Secrets** | Local files, environment vars | AWS Secrets Manager, Parameter Store |
| **Failover Triggers** | Ping, custom monitors | CloudWatch alarms, SNS, custom agents |
| **Resource Discovery** | Manual configuration | AWS API (auto-discovery) |
| **Time Sync** | Local NTP | AWS NTP service |
| **Logging** | Local syslog, files | CloudWatch Logs, S3 |
| **Reliability** | Manual failover or simple HA | Multi-AZ, Load Balancing, Auto Scaling |

### Why These Differences Matter

On-premises scripts assume:
- Direct access to physical systems
- Persistent local state
- Network topology is fixed
- Credentials are local
- Resources are static

AWS requires:
- API-based resource management
- Stateless design preferred
- Dynamic network topology
- Credential delegation via IAM
- Resources can change frequently

---

## Pre-Migration Assessment

### ☑️ 1. Understand Your Current Failover Script

**Question:** What does your on-premises failover script do?

**Checklist:**
- [ ] Identify all resources it manages (databases, applications, services)
- [ ] Document failure detection mechanism (ping, health checks, monitoring)
- [ ] Map all failover actions (restart, switch IPs, data sync, etc.)
- [ ] List all external dependencies (DNS, load balancers, file systems)
- [ ] Understand state management (configuration files, databases)
- [ ] Identify manual intervention points
- [ ] Document recovery procedures
- [ ] Review historical failover logs and timing

**Example:**
```
Current Script Does:
├─ Monitor primary database server (192.168.1.10)
├─ Check application service health (HTTP status 200)
├─ Monitor disk usage on primary
├─ On failure:
│  ├─ Update DNS (via API call)
│  ├─ Restart backup application server
│  ├─ Sync configuration from shared NFS
│  ├─ Start replication from backup DB
│  └─ Send email alert
└─ Every 60 seconds
```

---

### ☑️ 2. Identify AWS Equivalents

**Question:** What AWS services can replace your on-premises components?

**Mapping:**

| On-Premises | AWS Equivalent | Notes |
|-------------|----------------|-------|
| Primary server | EC2 instance (private subnet) | Use security groups for access control |
| Backup server | EC2 instance (different AZ) | For high availability |
| Shared NFS | EBS snapshots or S3 | For cross-AZ replication |
| Local database | RDS with Multi-AZ or EC2 DB | RDS handles failover automatically |
| DNS update script | Route 53 API | AWS SDK handles updates |
| Email alerts | SNS + email | AWS managed service |
| Monitoring tool | CloudWatch | Native AWS monitoring |
| Health checks | CloudWatch alarms + custom agents | Event-driven |
| Local logging | CloudWatch Logs | Centralized logging |
| NTP server | AWS NTP (169.254.169.123) | Built-in to AWS |

**Decision:**
```
For your failover script:
├─ Stay on EC2 for existing application (familiar, control)
├─ Use RDS if database is relational (AWS manages failover)
├─ Use Route 53 for DNS updates (API-driven)
├─ Use CloudWatch for monitoring (integrated)
├─ Use SNS for alerts (scalable)
└─ Use Systems Manager for agent deployment (secure)
```

---

### ☑️ 3. Assess Script Complexity

**Question:** How complex is your failover logic?

**Complexity Levels:**

**Level 1 - Simple (Easy Migration)**
```
If script only:
☐ Checks service health
☐ Restarts service
☐ Sends email alert
☐ Updates DNS manually
→ Easy to migrate to Lambda or EC2 agent
```

**Level 2 - Moderate (Medium Effort)**
```
If script also:
☐ Manages multiple resources
☐ Performs data synchronization
☐ Has multiple failure scenarios
☐ Requires manual decision points
→ Requires more careful planning
```

**Level 3 - Complex (High Effort)**
```
If script also:
☐ Manages distributed systems
☐ Performs complex state management
☐ Integrates with many external systems
☐ Has custom protocol handling
☐ Requires ultra-low failover time (<1 second)
→ May need complete redesign
```

---

## Infrastructure & Networking

### ☑️ 4. VPC & Subnet Design

**Question:** How will your EC2 instances be networked in AWS?

**Checklist:**

- [ ] Create VPC for your resources
- [ ] Design subnets across multiple AZs (for HA)
- [ ] Plan for private vs public subnets
  - Primary app → Private subnet (security)
  - Failover app → Private subnet (different AZ)
  - Failover script → Can run on either (or separate edge instance)
- [ ] Configure VPC endpoints if needed (S3, Secrets Manager)
- [ ] Plan NAT Gateway for private instances to reach internet
- [ ] Document IP addressing scheme
- [ ] Plan security group rules

**Example Architecture:**
```
VPC: 10.0.0.0/16

┌─────────────────────────────────────────┐
│           AWS Region (us-east-1)        │
├─────────────────────────────────────────┤
│                                         │
│  AZ-1 (us-east-1a)                     │
│  ┌─────────────────────────────────┐   │
│  │ Private Subnet: 10.0.1.0/24    │   │
│  │ ├─ Primary App (10.0.1.10)    │   │
│  │ └─ Primary DB (10.0.1.20)     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  AZ-2 (us-east-1b)                     │
│  ┌─────────────────────────────────┐   │
│  │ Private Subnet: 10.0.2.0/24    │   │
│  │ ├─ Failover App (10.0.2.10)   │   │
│  │ └─ Failover DB (10.0.2.20)    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Edge AZ (AWS Local Zones or EC2)      │
│  ┌─────────────────────────────────┐   │
│  │ Failover Script Node            │   │
│  │ ├─ Monitors both AZ-1 & AZ-2   │   │
│  │ └─ Triggers failover logic      │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### ☑️ 5. Security Groups & Network Access

**Question:** How will your failover script communicate with resources?

**Checklist:**

- [ ] Create security group for primary app
  ```
  Inbound:
  - Port 3306 (MySQL) from failover script
  - Port 8080 (App) from load balancer
  - Port 22 (SSH) from bastion host (optional)

  Outbound:
  - All traffic to internet
  ```

- [ ] Create security group for failover script
  ```
  Inbound:
  - Port 22 (SSH) from admin access
  - Port 443 (HTTPS) for AWS API calls

  Outbound:
  - All TCP to primary app security group
  - All TCP to failover app security group
  - Port 443 to AWS endpoints
  - Port 53 (DNS) for Route 53 updates
  ```

- [ ] Create security group for backup/failover app
  ```
  Inbound:
  - Port 3306 (MySQL) from failover script
  - Port 8080 (App) from load balancer

  Outbound:
  - All traffic to internet
  ```

- [ ] Test connectivity between all instances
  ```bash
  # From failover script to primary app
  ssh ec2-user@10.0.1.10  # Should fail (no SSH)
  mysql -h 10.0.1.20 -u root  # Should work
  curl http://10.0.1.10:8080/health  # Should return 200
  ```

### ☑️ 6. Network Latency & Edge Considerations

**Question:** How does network latency affect your failover?

**Checklist:**

- [ ] Measure current on-premises latency between primary and backup
  ```bash
  # On-premises
  ping primary_server     # Typical: 1-5ms
  ping backup_server      # Typical: 5-20ms
  ```

- [ ] Understand AWS AZ latency
  ```
  Same AZ:        ~1ms
  Different AZ:   ~5-10ms
  Cross-region:   ~50-100ms
  ```

- [ ] Consider AWS Local Zones for ultra-low latency
  - Available in major cities (NYC, LA, Boston, etc.)
  - 1-10ms latency to associated region
  - Cost: Higher than standard EC2
  - Use case: Real-time trading, gaming, etc.

- [ ] Plan failover script placement
  ```
  Option 1: On EC2 instance in VPC (classic)
  - Pro: Easy to manage
  - Con: Depends on network connectivity

  Option 2: On AWS Local Zone edge node
  - Pro: Ultra-low latency to primary
  - Con: More expensive, limited availability

  Option 3: Lambda (if script is simple)
  - Pro: Serverless, no management
  - Con: Limited execution time (15 min), network limitations

  Option 4: EventBridge + Systems Manager
  - Pro: Fully managed failover
  - Con: Less control over logic
  ```

- [ ] Configure VPC Flow Logs to monitor network traffic
  ```bash
  # This helps identify latency bottlenecks
  ```

---

## Failover Script Migration

### ☑️ 7. Rewrite Script for AWS

**Question:** Will your existing script work in AWS?

**Answer: Probably not without changes!** Here's why and how to fix it:

**Common Issues & Solutions:**

| Issue | On-Premises Approach | AWS Approach |
|-------|----------------------|--------------|
| **Detect Primary Down** | Ping 192.168.1.10 | CloudWatch alarm + custom health check |
| **Update Primary IP** | Direct routing change | Route 53 DNS failover |
| **Access DB** | Connect to 10.0.1.20 | Use RDS endpoint or parameter store |
| **Restart service** | ssh + systemctl restart | Systems Manager + EC2 instance metadata |
| **Sync data** | NFS mount + rsync | RDS read replica or S3 sync |
| **Send alerts** | sendmail to local mail server | SNS to email/SMS |
| **Log actions** | syslog to /var/log | CloudWatch Logs |
| **Credentials** | In script or env vars | IAM roles (instance profile) |
| **Resource discovery** | Static config file | AWS SDK + tagging |

### ☑️ 8. Refactor for Statelessness

**Question:** Does your script maintain persistent state?

**On-Premises Pattern (Problematic in AWS):**
```bash
# File: /var/lib/failover/state.txt
# Stores: last_failover_time, failover_count, etc.

if [ -f /var/lib/failover/state.txt ]; then
    source /var/lib/failover/state.txt
fi

# Update state file
echo "last_failover=$(date)" > /var/lib/failover/state.txt
```

**Problem:** If EC2 instance crashes, state is lost!

**AWS Solution: Use DynamoDB or Parameter Store**
```python
import boto3
from datetime import datetime

ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')

# Store failover state
table = dynamodb.Table('failover-state')
table.put_item(Item={
    'resource_id': 'primary-app',
    'last_failover': datetime.utcnow().isoformat(),
    'failover_count': 5,
    'status': 'failed_over'
})

# Retrieve state
response = table.get_item(Key={'resource_id': 'primary-app'})
last_failover = response['Item']['last_failover']
```

**Benefits:**
- ✅ State persists across instance failures
- ✅ Multiple instances can share state
- ✅ Automatic backup and replication
- ✅ Queryable history

### ☑️ 9. Use AWS SDKs Instead of System Commands

**Question:** Does your script use shell commands to manage infrastructure?

**On-Premises Pattern:**
```bash
#!/bin/bash

# Update DNS via CLI tool
/usr/local/bin/dns-update-tool --host primary --ip 10.0.2.10

# SSH to backup and restart
ssh backup-server "systemctl restart myapp"

# Check status via remote command
ssh primary-server "systemctl status myapp"
```

**Problem:**
- Fragile (depends on tools being installed)
- Slow (network round trips)
- Insecure (SSH key management)
- Not idempotent (may fail unpredictably)

**AWS Solution: Use Boto3 SDK**
```python
import boto3

# Initialize AWS clients
route53 = boto3.client('route53')
ssm = boto3.client('ssm')
ec2 = boto3.client('ec2')

# Update DNS via Route 53 API
route53.change_resource_record_sets(
    HostedZoneId='Z1234567890ABC',
    ChangeBatch={
        'Changes': [{
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': 'myapp.example.com',
                'Type': 'A',
                'TTL': 60,
                'ResourceRecords': [{'Value': '10.0.2.10'}]
            }
        }]
    }
)

# Restart service on backup via Systems Manager
ssm.send_command(
    InstanceIds=['i-backup123'],
    DocumentName='AWS-RunShellScript',
    Parameters={
        'command': ['systemctl restart myapp']
    }
)

# Check status via EC2 API
response = ec2.describe_instances(InstanceIds=['i-primary123'])
instance = response['Reservations'][0]['Instances'][0]
status = instance['State']['Name']  # 'running', 'stopped', etc.
```

**Benefits:**
- ✅ Reliable API calls (not shell-dependent)
- ✅ Native error handling
- ✅ Secure credential passing via IAM
- ✅ Idempotent operations
- ✅ Easy to mock for testing

---

## IAM & Security

### ☑️ 10. Create IAM Role for Failover Script

**Question:** How will your failover script authenticate to AWS?

**Never do this:**
```bash
# ❌ WRONG - hardcoded credentials in script
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

**Always do this:**
```bash
# ✅ CORRECT - use IAM instance profile
# AWS automatically provides credentials
```

**Checklist:**

- [ ] Create IAM role for failover EC2 instance
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
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
        "Sid": "SystemsManagerCommand",
        "Effect": "Allow",
        "Action": [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations"
        ],
        "Resource": "*"
      },
      {
        "Sid": "RDSManagement",
        "Effect": "Allow",
        "Action": [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:FailoverDBCluster"
        ],
        "Resource": "*"
      },
      {
        "Sid": "SNSNotifications",
        "Effect": "Allow",
        "Action": [
          "sns:Publish"
        ],
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
        "Action": [
          "secretsmanager:GetSecretValue"
        ],
        "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:myapp/*"
      }
    ]
  }
  ```

- [ ] Attach role to EC2 instance
  ```bash
  aws ec2 associate-iam-instance-profile \
    --instance-id i-failover123 \
    --iam-instance-profile Name=failover-role
  ```

- [ ] Verify instance can access AWS APIs
  ```bash
  # SSH into instance and test
  aws sts get-caller-identity  # Should show role ARN
  aws route53 list-hosted-zones  # Should list zones
  ```

### ☑️ 11. Handle Sensitive Data

**Question:** How will your script access databases, API keys, etc.?

**On-Premises Approach (Bad):**
```bash
# ❌ WRONG
DB_PASSWORD="mypassword123"
API_KEY="secret-key-in-plaintext"

mysql -h db.example.com -u admin -p"$DB_PASSWORD"
curl -H "Authorization: Bearer $API_KEY" https://api.example.com/failover
```

**AWS Solution: Use Secrets Manager**
```python
import boto3
import json

secrets_client = boto3.client('secretsmanager')

# Retrieve secret
response = secrets_client.get_secret_value(SecretId='myapp/db-password')
secret = json.loads(response['SecretString'])
db_password = secret['password']

# Use in connection
import pymysql
conn = pymysql.connect(
    host='db.example.com',
    user='admin',
    password=db_password,
    database='myapp'
)
```

**Checklist:**

- [ ] Store all credentials in AWS Secrets Manager
  ```bash
  aws secretsmanager create-secret \
    --name myapp/db-password \
    --secret-string '{"username":"admin","password":"secure-password"}'
  ```

- [ ] Grant IAM role permission to access secrets
  ```json
  {
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:myapp/*"
  }
  ```

- [ ] Never commit secrets to code repository
  - [ ] Add `*.secrets` to `.gitignore`
  - [ ] Use `git-secrets` hook to prevent accidental commits
  - [ ] Scan repository history: `git log -p | grep -i password`

- [ ] Rotate secrets regularly
  ```bash
  # Enable automatic rotation
  aws secretsmanager rotate-secret \
    --secret-id myapp/db-password \
    --rotation-rules AutomaticallyAfterDays=30
  ```

---

## Monitoring & Logging

### ☑️ 12. Set Up CloudWatch Monitoring

**Question:** How will you monitor your failover script?

**On-Premises Approach:**
```bash
# Monitor via local tools
tail -f /var/log/failover.log
ps aux | grep failover
df -h  # Disk space
free -h  # Memory
```

**AWS Approach: Use CloudWatch**

Checklist:

- [ ] Install CloudWatch agent on EC2 instance
  ```bash
  wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
  rpm -U ./amazon-cloudwatch-agent.rpm
  ```

- [ ] Configure CloudWatch agent
  ```json
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
              "file_path": "/var/log/failover.log",
              "log_group_name": "/failover/script",
              "log_stream_name": "{instance_id}"
            }
          ]
        }
      }
    }
  }
  ```

- [ ] Send custom metrics from your script
  ```python
  import boto3
  from datetime import datetime

  cloudwatch = boto3.client('cloudwatch')

  # Send failover event metric
  cloudwatch.put_metric_data(
      Namespace='FailoverScript',
      MetricData=[
          {
              'MetricName': 'FailoverExecuted',
              'Value': 1,
              'Unit': 'Count',
              'Timestamp': datetime.utcnow()
          },
          {
              'MetricName': 'FailoverDuration',
              'Value': 2.5,
              'Unit': 'Seconds',
              'Timestamp': datetime.utcnow()
          }
      ]
  )
  ```

- [ ] Create CloudWatch alarms
  ```bash
  # Alert if failover script CPU goes high
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-high-cpu \
    --alarm-description "Alert if failover script CPU > 80%" \
    --metric-name CPU_IDLE \
    --namespace FailoverScript \
    --statistic Average \
    --period 300 \
    --threshold 20 \
    --comparison-operator LessThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

  # Alert if failover script stops writing logs
  aws cloudwatch put-metric-alarm \
    --alarm-name failover-heartbeat-missing \
    --alarm-description "Alert if failover logs stop" \
    --metric-name IncomingLogEvents \
    --namespace AWS/Logs \
    --statistic Sum \
    --period 600 \
    --threshold 1 \
    --comparison-operator LessThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
  ```

### ☑️ 13. Centralize Logging

**Question:** Where will your failover logs be stored?

**On-Premises:**
```bash
# Local files
tail -f /var/log/failover.log
tail -f /var/log/syslog | grep failover
```

**AWS Solution: CloudWatch Logs**

- [ ] Configure application to log to CloudWatch
  ```python
  import logging
  import watchtower

  # Python logging to CloudWatch
  logger = logging.getLogger(__name__)
  logger.addHandler(watchtower.CloudWatchLogHandler(
      log_group='/failover/script',
      stream_name=instance_id
  ))

  logger.info('Failover script started')
  logger.error('Primary host unreachable: 10.0.1.10')
  logger.warning('Failover taking longer than expected')
  ```

- [ ] Create log queries for troubleshooting
  ```bash
  # Find all failover events
  aws logs filter-log-events \
    --log-group-name '/failover/script' \
    --filter-pattern '[time, request_id, level = ERROR, ...]'

  # Find slow failovers
  aws logs filter-log-events \
    --log-group-name '/failover/script' \
    --filter-pattern 'DURATION > 5'
  ```

- [ ] Set retention policies
  ```bash
  # Keep logs for 30 days
  aws logs put-retention-policy \
    --log-group-name '/failover/script' \
    --retention-in-days 30
  ```

- [ ] Create CloudWatch Insights queries
  ```
  fields @timestamp, @message, failover_duration
  | filter @message like /Failover/
  | stats avg(failover_duration) as avg_duration by @logStream
  ```

---

## Edge Node Specific

### ☑️ 14. AWS Local Zones (If Using Edge Nodes)

**Question:** Are you deploying failover script on AWS Local Zones edge nodes?

**What are AWS Local Zones?**
- Extensions of AWS Regions closer to end users
- Single digit millisecond latency (1-10ms)
- Available in major cities: NYC, LA, Boston, Dallas, etc.
- Higher cost than standard EC2
- Limited service availability

**Checklist:**

- [ ] Check if Local Zone is available in your location
  ```bash
  aws ec2 describe-availability-zones \
    --query 'AvailabilityZones[?ZoneType==`local-zone`]'
  ```

- [ ] Understand latency vs standard AZ
  ```
  Standard AZ (us-east-1a) to on-premises DC: 40-50ms
  Local Zone (us-east-1-nyc-1) to on-premises DC: 5-10ms
  ```

- [ ] Decide if cost justifies latency benefit
  ```
  Standard EC2 t3.medium: $0.0416/hour
  Local Zone EC2 t3.medium: ~$0.0500/hour (20% premium)

  For 24/7/365:
  Standard: $364/year
  Local Zone: $438/year ($74 extra)

  Worth it if? Failover latency is critical
  ```

- [ ] Plan networking to Local Zone
  ```
  Local Zone instances can communicate with parent region via:
  - VPC peering (not needed, same VPC)
  - Elastic IP for internet access
  - NAT Gateway in parent region

  Note: Latency is ~10ms to parent region, ~1ms within Local Zone
  ```

- [ ] Test connectivity
  ```bash
  # From Local Zone instance
  ping primary-instance-in-standard-az  # ~10ms
  ping backup-instance-in-same-localzone  # ~1ms

  # Primary should be in Local Zone for ultra-low latency
  ```

### ☑️ 15. Outpost & On-Premises Edge Deployments

**Question:** Are you using AWS Outpost or hybrid edge nodes?

**AWS Outpost:**
- AWS infrastructure running in your data center
- Full AWS services locally
- Connects to AWS Region over dedicated link
- High cost, requires significant infrastructure

**Checklist if using Outpost:**

- [ ] Network connectivity between Outpost and AWS Region
  ```bash
  # Dedicated connection (1GB to 100GB)
  # Latency: <5ms typically
  ```

- [ ] IAM authentication works same way (no changes needed)

- [ ] Data sovereignty is maintained (stays in Outpost)

- [ ] Use same Boto3 code (works on Outpost EC2 too)

**For Hybrid Deployments (On-Premises + AWS):**

- [ ] Set up AWS Systems Manager Hybrid Activation
  ```bash
  aws ssm create-activation \
    --default-instance-name on-prem-failover \
    --iam-role service-role/AmazonSSMManagedInstanceCore
  ```

- [ ] Install Systems Manager Agent on on-premises instance
  ```bash
  wget https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
  rpm -U amazon-ssm-agent.rpm
  ```

- [ ] Failover script can manage both AWS EC2 and on-premises
  ```python
  # On-premises resources show up in Systems Manager inventory
  response = ssm.describe_instance_information(
      Filters=[
          {'Key': 'tag:Environment', 'Values': ['production']}
      ]
  )

  # Works for both AWS EC2 and on-premises servers
  for instance in response['InstanceInformationList']:
      print(f"{instance['InstanceId']}: {instance['PlatformType']}")
  ```

---

## Testing & Validation

### ☑️ 16. Test Failover Before Deploying

**Question:** How will you test failover script in AWS?

**Testing Phases:**

**Phase 1: Unit Tests (Test Components)**
```python
import unittest
from unittest.mock import Mock, patch

class TestFailoverScript(unittest.TestCase):

    @patch('boto3.client')
    def test_detect_primary_down(self, mock_boto):
        """Test that script detects primary down"""
        # Mock EC2 client
        ec2_mock = Mock()
        ec2_mock.describe_instance_status.return_value = {
            'InstanceStatuses': [{
                'InstanceId': 'i-primary123',
                'InstanceStatus': {'Status': 'impaired'}  # Down!
            }]
        }

        # Test detection logic
        from failover_script import detect_primary_down
        result = detect_primary_down('i-primary123', ec2_mock)
        self.assertTrue(result)

    @patch('boto3.client')
    def test_route53_update(self, mock_boto):
        """Test Route 53 DNS update"""
        route53_mock = Mock()

        from failover_script import update_dns
        update_dns('myapp.example.com', '10.0.2.10', route53_mock)

        route53_mock.change_resource_record_sets.assert_called_once()
```

**Phase 2: Integration Tests (Test with Real AWS)**
```python
def test_end_to_end_failover():
    """
    Test complete failover flow:
    1. Detect primary down
    2. Start backup instance
    3. Update DNS
    4. Verify traffic goes to backup
    """

    # Use test VPC and instances
    primary_id = 'i-test-primary-123'
    backup_id = 'i-test-backup-456'

    # Step 1: Simulate primary failure
    ec2.stop_instances(InstanceIds=[primary_id])

    # Step 2: Run failover script
    from failover_script import execute_failover
    result = execute_failover(primary_id, backup_id)

    # Step 3: Verify results
    assert result['status'] == 'success'
    assert result['backup_started'] == True
    assert result['dns_updated'] == True

    # Step 4: Test connectivity to backup
    import requests
    response = requests.get('http://myapp.example.com/health')
    assert response.status_code == 200
```

**Phase 3: Chaos Testing (Test Failure Scenarios)**
```python
import random

def test_partial_failure():
    """Test failover when backup is slow"""
    # Slow down network to backup
    # Run failover
    # Verify it still works (maybe takes longer)
    pass

def test_cascade_failure():
    """Test if backup also fails during failover"""
    # Fail primary
    # While failover happening, fail backup
    # Verify script handles gracefully
    pass

def test_dns_propagation_delay():
    """Test if script handles DNS propagation"""
    # Update DNS
    # But some clients still see old IP
    # Verify script doesn't declare success too early
    pass
```

**Phase 4: Load Testing (Test under stress)**
```python
def test_failover_during_high_load():
    """Test failover while primary is under load"""

    # Generate load on primary
    import concurrent.futures

    def make_request():
        requests.get('http://10.0.1.10:8080/data')

    # Hammer primary with 1000 req/sec
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(make_request) for _ in range(10000)]

        # After 30 seconds of load, trigger failover
        time.sleep(30)
        execute_failover()

        # Verify remaining requests complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            assert result is not None
```

### ☑️ 17. Validate Before Production

**Checklist:**

- [ ] Test in dev environment
  - [ ] Script deploys successfully
  - [ ] IAM role permissions work
  - [ ] Security groups allow required traffic
  - [ ] CloudWatch metrics flow correctly

- [ ] Test in staging environment (similar to prod)
  - [ ] Simulate primary failure
  - [ ] Verify failover executes
  - [ ] Check DNS updates
  - [ ] Verify backup starts correctly
  - [ ] Confirm alerts are sent
  - [ ] Review logs for errors

- [ ] Test rollback procedure
  - [ ] After failover, bring primary back online
  - [ ] Failover script detects primary is back
  - [ ] Switch traffic back to primary
  - [ ] Verify no data loss

- [ ] Test failure scenarios
  - [ ] Primary network down (but instance still running)
  - [ ] Primary service crashed (but instance running)
  - [ ] Backup also down during failover
  - [ ] DNS update fails
  - [ ] Alert delivery fails

- [ ] Performance validation
  ```bash
  # Measure failover time
  # On-premises: ?
  # AWS EC2: should be similar or better

  Time to detect failure: 10-60 seconds
  Time to failover: 20-120 seconds
  Total: 30-180 seconds (depending on detection mechanism)
  ```

- [ ] Document test results
  ```
  Test Case: Failover during high load
  Result: PASSED
  Detection Time: 45 seconds
  Failover Time: 78 seconds
  Total: 123 seconds

  Observations:
  - DNS took 45 seconds to propagate
  - Some old requests failed but clients retry
  - No data loss observed
  - Memory on failover instance peaked at 65%
  ```

---

## Deployment Strategy

### ☑️ 18. Plan Deployment Steps

**Question:** How will you safely deploy failover script to AWS?

**Option 1: Blue-Green Deployment (Safe)**

```
Phase 1: Deploy to Blue (New)
- Deploy failover script to new EC2 instance
- Test it works
- Keep it idle (not active)

Phase 2: Monitor Blue
- Run for 1-2 weeks
- Ensure no issues
- Compare metrics with old Green system

Phase 3: Switch to Blue
- Update configuration to use Blue
- Monitor closely
- Keep Green running as fallback

Phase 4: Retire Green
- After 2-4 weeks of stable operation
- Terminate old instance
```

**Option 2: Canary Deployment (Gradual)**

```
Phase 1: Deploy on EC2
- 10% traffic/health checks
- Monitor for errors
- Compare with on-premises

Phase 2: Increase to 50%
- Half requests go to AWS EC2
- Half stay on-premises
- Ensure consistency

Phase 3: Go to 100%
- All traffic to AWS EC2
- Keep on-premises on standby

Phase 4: Retire on-premises
- Only if stable for 30 days
```

**Recommended: Blue-Green**

- [ ] Week 1: Deploy on EC2 (blue), test thoroughly
  ```bash
  # Deploy failover script to EC2
  git clone <failover-repo>
  cd failover-script

  # Install dependencies
  pip install -r requirements.txt

  # Configure for AWS
  cp config.aws.yaml config.yaml

  # Start service
  systemctl start failover-script

  # Verify working
  curl http://10.0.3.10:5000/health  # Check if running
  grep "Started successfully" /var/log/failover.log
  ```

- [ ] Week 1-2: Run parallel to on-premises
  ```
  Failover Script A (On-Premises): Active
  Failover Script B (AWS EC2): Passive, monitoring

  If B detects something wrong, it doesn't act
  If A fails, B is ready to take over
  ```

- [ ] Week 2-3: Switch to AWS (Blue)
  ```bash
  # Update configuration to make AWS EC2 primary
  aws ssm put-parameter \
    --name /failover/active-instance \
    --value "i-ec2-failover-123" \
    --overwrite

  # Both systems now monitoring, AWS is authoritative
  ```

- [ ] Week 3-4: Retire on-premises
  ```bash
  # After 2+ weeks of stable operation
  # Stop on-premises failover script
  systemctl stop failover-script

  # Retire instance
  # Keep as backup for 1 month
  ```

### ☑️ 19. Runbook for Going Live

**Checklist:**

- [ ] Pre-deployment
  - [ ] All tests passed
  - [ ] Code reviewed
  - [ ] Rollback plan documented
  - [ ] Team trained
  - [ ] Alert channels working
  - [ ] Monitoring dashboards created

- [ ] Deployment day
  - [ ] Schedule: Tuesday-Thursday, 9am-12pm (avoid weekends/nights)
  - [ ] Team present: DevOps, DBA, App team, on-call
  - [ ] Start deployment
    ```bash
    # Day 1: Deploy EC2 instance with failover script
    # Day 2: Test with synthetic traffic
    # Day 3: Run parallel to on-premises
    # Day 4-7: Monitor
    # Day 8: Switch primary to EC2
    # Day 15: Retire on-premises
    ```

- [ ] Rollback triggers
  - [ ] Failover not detecting failures: Rollback
  - [ ] Failover taking >5x longer than expected: Investigate
  - [ ] Data loss detected: Rollback immediately
  - [ ] Critical service impact: Rollback
  - [ ] Multiple failover script crashes: Rollback

- [ ] Rollback procedure
  ```bash
  # If things go wrong
  1. Immediately activate on-premises failover script
  2. Update configuration to point to on-premises
  3. Verify on-premises is handling failover correctly
  4. Post incident: Root cause analysis
  5. Fix issues and try again next week
  ```

---

## Hybrid Approach: On-Premises Script Managing AWS

### ☑️ 20A. Run Failover Script from On-Premises (NEW!)

**Question:** Can your on-premises failover script manage AWS resources directly?

**Answer: YES! This is the safest migration path.**

**Benefits of Hybrid Approach:**
```
Phase 1: On-premises script manages AWS resources
├─ Lower risk (familiar infrastructure)
├─ Easy rollback (just restart on-premises)
├─ Parallel testing (without moving script)
├─ Network connectivity already established
└─ Allows gradual validation

Phase 2: Move script to AWS EC2
├─ After validating AWS resource management works
├─ Same failover logic, just different location
├─ Can still fall back to on-premises if needed
└─ Cleaner architecture (everything in AWS)
```

**Setup Checklist:**

- [ ] **Verify network connectivity from on-premises to AWS**
  ```bash
  # From on-premises server
  aws ec2 describe-instances --region us-east-1
  # Should show your AWS instances

  # Test latency to AWS
  ping 10.0.1.10  # Private IP of primary EC2 in AWS
  # Typical latency: 40-50ms over internet, <5ms over dedicated connection
  ```

- [ ] **Verify boto3 is working on on-premises server**
  ```bash
  # On-premises server
  python3 -c "import boto3; print(boto3.__version__)"
  # Should show version like: 1.26.0 or higher

  # Test AWS API call
  python3 -c "
  import boto3
  ec2 = boto3.client('ec2', region_name='us-east-1')
  response = ec2.describe_instances()
  print(f'Found {len(response[\"Reservations\"])} EC2 instances')
  "
  ```

- [ ] **Ensure AWS credentials are available on on-premises server**

  **Option A: AWS CLI Profile (Recommended)**
  ```bash
  # On-premises server already has AWS credentials configured
  aws configure  # If not already done

  # Verify profile works
  aws sts get-caller-identity --profile default
  # Should show your AWS account info
  ```

  **Option B: Export AWS Credentials (Less Secure)**
  ```bash
  # ⚠️ Less secure, but works for testing
  export AWS_ACCESS_KEY_ID="your-access-key"
  export AWS_SECRET_ACCESS_KEY="your-secret-key"
  export AWS_DEFAULT_REGION="us-east-1"

  # Verify
  aws sts get-caller-identity
  ```

  **Option C: IAM User with API Keys (Recommended for On-Premises)**
  ```bash
  # Create IAM user in AWS
  aws iam create-user --user-name on-prem-failover-script

  # Create API keys
  aws iam create-access-key --user-name on-prem-failover-script

  # Attach policy (see section 10 for policy)
  aws iam put-user-policy \
    --user-name on-prem-failover-script \
    --policy-name failover-policy \
    --policy-document file://failover-policy.json

  # Use these keys on on-premises server
  ```

- [ ] **Test failover script can manage AWS resources**
  ```python
  # Test script: test_aws_management.py
  import boto3
  import sys

  def test_aws_connectivity():
      """Test if on-premises script can manage AWS resources"""

      try:
          # Test EC2 management
          ec2 = boto3.client('ec2', region_name='us-east-1')
          instances = ec2.describe_instances()
          print(f"✅ EC2: Found {len(instances['Reservations'])} reservations")

          # Test Route 53 DNS updates
          route53 = boto3.client('route53')
          zones = route53.list_hosted_zones()
          print(f"✅ Route 53: Found {len(zones['HostedZones'])} zones")

          # Test RDS if using
          rds = boto3.client('rds')
          dbs = rds.describe_db_instances()
          print(f"✅ RDS: Found {len(dbs['DBInstances'])} databases")

          # Test SNS for alerts
          sns = boto3.client('sns')
          topics = sns.list_topics()
          print(f"✅ SNS: Found {len(topics['Topics'])} topics")

          # Test Systems Manager for remote commands
          ssm = boto3.client('ssm')
          instances_ssm = ssm.describe_instance_information()
          print(f"✅ Systems Manager: Found {len(instances_ssm['InstanceInformationList'])} managed instances")

          print("\n✅ All AWS services accessible from on-premises!")
          return True

      except Exception as e:
          print(f"❌ Error: {str(e)}")
          return False

  if __name__ == '__main__':
      if test_aws_connectivity():
          sys.exit(0)
      else:
          sys.exit(1)
  ```

  **Run test:**
  ```bash
  # On on-premises server
  python3 test_aws_management.py
  # Should show all ✅ checks
  ```

### ☑️ 20B. Hybrid Failover Architecture

**New Architecture: On-Premises Script + AWS Resources**

```
ON-PREMISES DATA CENTER          AWS CLOUD
────────────────────────         ────────────────

Failover Script (on-prem)         Primary EC2 (us-east-1a)
        │                                │
        ├─ Monitors ─────────────────────┤
        │                                │
        │                         Backup EC2 (us-east-1b)
        │                                │
        ├─ Can restart via ──────────────┤
        │  Systems Manager API           │
        │                                │
        ├─ Can update DNS via ───→ Route 53
        │  Route 53 API
        │
        ├─ Can manage RDS ──────→ RDS Multi-AZ
        │  failover via API
        │
        └─ Sends alerts ────────→ SNS Topic
           via SNS

Benefits:
✅ On-premises has all intelligence
✅ Can manage both on-prem + AWS resources
✅ Easy rollback (just restart on-prem script)
✅ AWS resources are passive (no agents needed initially)
✅ Gradual transition to full AWS
```

### ☑️ 20C. Update Failover Script for Hybrid

**Your current on-premises failover script:**

```bash
# Current: Manages on-premises resources
check_primary() {
    ping primary_server  # 192.168.1.10 (on-prem)
}

failover() {
    ssh backup_server "systemctl restart myapp"  # On-prem
    /usr/local/bin/dns-update-tool --host primary --ip 192.168.1.20
}
```

**Enhanced: Can also manage AWS resources**

```python
# New: Manages both on-premises + AWS resources
import boto3
import paramiko
import os

# Initialize AWS clients
ec2 = boto3.client('ec2', region_name='us-east-1')
route53 = boto3.client('route53')
ssm = boto3.client('ssm')
sns = boto3.client('sns')

def check_primary():
    """Check if primary is available (on-prem or AWS)"""

    # Option 1: Still have on-prem primary
    try:
        # Ping on-prem primary
        import subprocess
        subprocess.run(['ping', '-c', '1', '192.168.1.10'],
                      timeout=5, check=True)
        return True
    except:
        # On-prem primary down
        return False

def check_aws_primary():
    """Check if AWS primary EC2 is available"""

    response = ec2.describe_instances(
        InstanceIds=['i-aws-primary-123']
    )

    instance = response['Reservations'][0]['Instances'][0]

    # Check both running state AND status checks
    if instance['State']['Name'] != 'running':
        return False

    # Check EC2 status checks
    status = ec2.describe_instance_status(
        InstanceIds=['i-aws-primary-123']
    )

    if not status['InstanceStatuses']:
        return False

    instance_status = status['InstanceStatuses'][0]
    return (instance_status['InstanceStatus']['Status'] == 'ok' and
            instance_status['SystemStatus']['Status'] == 'ok')

def failover_to_backup():
    """Failover to backup (on-prem or AWS)"""

    # Check which primary failed
    on_prem_down = not check_primary()
    aws_down = not check_aws_primary()

    if on_prem_down and not aws_down:
        # On-prem primary down, AWS primary is up
        # Keep monitoring, don't fail over yet
        print("On-prem primary down, but AWS primary is up")
        return

    elif aws_down and not on_prem_down:
        # AWS primary down, on-prem primary is up
        # This is handled by on-prem, no need to failover
        print("AWS primary down, but on-prem primary is up")
        return

    elif on_prem_down and aws_down:
        # Both down! Execute failover to backup

        # Determine backup location
        if has_aws_backup:
            failover_to_aws_backup()
        else:
            failover_to_on_prem_backup()

def failover_to_on_prem_backup():
    """Failover to on-premises backup (old way)"""

    ssh = paramiko.SSHClient()
    ssh.connect('backup.on-prem.local')

    # Restart backup service
    ssh.exec_command('systemctl restart myapp')

    # Update DNS
    os.system('/usr/local/bin/dns-update-tool --host primary --ip 192.168.1.20')

    # Send alert
    send_alert('Failover to on-prem backup')

    ssh.close()

def failover_to_aws_backup():
    """Failover to AWS backup (new AWS way)"""

    # 1. Start backup EC2 instance
    ec2.start_instances(InstanceIds=['i-aws-backup-456'])
    print("Started AWS backup instance")

    # 2. Wait for instance to be running
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=['i-aws-backup-456'])
    print("AWS backup instance is running")

    # 3. Restart application on backup via Systems Manager
    response = ssm.send_command(
        InstanceIds=['i-aws-backup-456'],
        DocumentName='AWS-RunShellScript',
        Parameters={'command': ['systemctl restart myapp']}
    )
    print(f"Sent restart command to AWS backup")

    # 4. Wait for command to complete
    command_id = response['Command']['CommandId']
    import time
    time.sleep(5)  # Wait for command execution

    # 5. Update Route 53 DNS to point to AWS backup
    route53.change_resource_record_sets(
        HostedZoneId='Z1234567890ABC',
        ChangeBatch={
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'myapp.example.com',
                    'Type': 'A',
                    'TTL': 60,
                    'ResourceRecords': [{'Value': '10.0.2.10'}]  # AWS backup IP
                }
            }]
        }
    )
    print("Updated DNS to AWS backup")

    # 6. Send alert
    send_alert('Failover to AWS backup EC2 instance')

def send_alert(message):
    """Send alert via SNS"""

    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789012:failover-alerts',
        Subject='Failover Event',
        Message=message
    )

# Main loop (runs on on-premises server)
def main():
    """Main monitoring loop"""

    import time

    while True:
        try:
            # Check both on-prem and AWS primaries
            on_prem_ok = check_primary()
            aws_ok = check_aws_primary()

            if not on_prem_ok or not aws_ok:
                print(f"On-prem: {on_prem_ok}, AWS: {aws_ok}")
                failover_to_backup()

            # Sleep before next check
            time.sleep(60)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
```

**Benefits of this hybrid approach:**

✅ **On-premises script stays as central controller**
✅ **Can manage both on-premises AND AWS resources**
✅ **Easy testing without moving script**
✅ **Network connectivity already proven**
✅ **Boto3 calls already working**
✅ **Gradual transition path to full AWS**
✅ **Easy rollback (just change code)**

### ☑️ 20D. Migration Path with Hybrid Approach

```
PHASE 1: Hybrid (Weeks 1-4)
├─ On-premises script monitors on-premises primary
├─ On-premises script ALSO monitors AWS primary
├─ Failover logic supports both on-premises and AWS backups
├─ Test thoroughly with both scenarios
└─ Run parallel: on-prem and AWS simultaneously

PHASE 2: Transition (Weeks 5-8)
├─ Move primary to AWS
├─ On-premises script still running, managing AWS resources
├─ Test failover with AWS primary down
├─ Build confidence in AWS failover
└─ Keep on-premises as ultimate backup

PHASE 3: Final Migration (Weeks 9-12)
├─ Move failover script itself to AWS EC2
├─ Deploy on AWS using same logic
├─ Run parallel: script on-prem and script on AWS
├─ Verify AWS-based script works
└─ Retire on-premises script

TOTAL: 12 weeks, low risk, proven at each step
```

### ☑️ 20E. Checklist for Hybrid Approach

- [ ] **Week 1: Validate Connectivity**
  - [ ] On-premises server can reach AWS VPC (via VPN or Direct Connect)
  - [ ] Boto3 calls work from on-premises
  - [ ] AWS credentials configured and tested
  - [ ] All AWS APIs accessible (EC2, Route 53, RDS, SNS, SSM)

- [ ] **Week 2: Enhance Failover Script**
  - [ ] Add AWS resource monitoring (EC2 status checks)
  - [ ] Add AWS failover logic (Systems Manager, Route 53)
  - [ ] Test with AWS resources only (primary down simulation)
  - [ ] Test with on-premises resources only
  - [ ] Test with both down (trigger failover)

- [ ] **Week 3: Test Hybrid Failover**
  - [ ] Simulate on-prem primary failure → failover to AWS backup
  - [ ] Simulate AWS primary failure → failover to on-prem backup
  - [ ] Simulate both down → select best backup
  - [ ] Test DNS updates (Route 53 and on-premises)
  - [ ] Verify alerts sent to both on-prem and AWS monitoring

- [ ] **Week 4: Validation & Documentation**
  - [ ] Document all test results
  - [ ] Update runbooks for hybrid setup
  - [ ] Train ops team on new hybrid failover
  - [ ] Get sign-off from stakeholders

- [ ] **Weeks 5-8: Run Hybrid in Production**
  - [ ] Monitor closely (double logging)
  - [ ] Track failover events
  - [ ] Measure failover time
  - [ ] Compare with previous setup
  - [ ] Optimize as needed

- [ ] **Weeks 9-12: Move Script to AWS**
  - [ ] Deploy on AWS EC2 (from section 18)
  - [ ] Run script in on-premises AND AWS simultaneously
  - [ ] Verify both can manage same resources
  - [ ] Test failover from AWS-based script
  - [ ] Retire on-premises script

---

## Rollback & Contingency

### ☑️ 21. Create Rollback Plan

**Question:** What if AWS deployment fails?

**Answer:** With hybrid approach, rollback is trivial! Just update code!

**Hybrid Advantage - Instant Rollback:**
```
If AWS script fails:
  1. Stop AWS script
  2. Start on-premises script (already running!)
  3. On-prem script takes over managing resources
  4. No need to update DNS or restart anything
  5. Total rollback time: < 5 minutes

With pure AWS approach:
  1. Detect failure
  2. Activate on-prem system
  3. Update DNS to on-prem IP
  4. Wait for propagation
  5. Total rollback time: 30+ minutes
```

**Rollback Scenarios:**

| Scenario | Detection | Rollback Time |
|----------|-----------|----------------|
| AWS EC2 failover script crashes | CloudWatch alarm (no heartbeat) | <5 min |
| AWS IAM role denied permissions | Logs show "AccessDenied" | <5 min |
| AWS API rate limited | SNS alerts | <10 min |
| DNS updates fail | Route 53 API errors | <5 min |
| Primary-Backup connectivity lost | Ping failures in logs | <5 min |
| Logic error in failover code | False failovers in logs | <15 min |

**Rollback Procedure:**

```bash
#!/bin/bash
# Rollback from AWS to On-Premises

echo "INITIATING ROLLBACK..."

# Step 1: Activate on-premises failover script
echo "Step 1: Activating on-premises failover script..."
ssh on-prem-failover "systemctl start failover-script"
sleep 10

# Step 2: Verify it's working
echo "Step 2: Verifying on-premises is active..."
ssh on-prem-failover "systemctl status failover-script" | grep "active"
if [ $? -ne 0 ]; then
    echo "ERROR: On-premises failover script not running!"
    exit 1
fi

# Step 3: Update Route 53 to point back to on-premises IP
echo "Step 3: Updating DNS to on-premises..."
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "failover.example.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "203.0.113.10"}]
      }
    }]
  }'

# Step 4: Wait for DNS propagation
echo "Step 4: Waiting for DNS propagation..."
sleep 30

# Step 5: Verify traffic is going to on-premises
echo "Step 5: Verifying traffic routing..."
curl -v https://failover.example.com/health

# Step 6: Disable AWS failover script
echo "Step 6: Disabling AWS failover script..."
aws ssm send-command \
  --instance-ids i-aws-failover-123 \
  --document-name "AWS-RunShellScript" \
  --parameters 'command=["systemctl stop failover-script"]'

# Step 7: Notify team
echo "Step 7: Sending notification..."
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789012:alerts \
  --subject "Failover Script Rolled Back to On-Premises" \
  --message "AWS deployment failed. Rolled back to on-premises failover script."

echo "ROLLBACK COMPLETE"
```

### ☑️ 21. Contingency Scenarios

**Question:** What could go wrong and how do you handle it?

| Issue | Prevention | Detection | Recovery |
|-------|-----------|-----------|----------|
| **EC2 instance fails** | Auto-recover, Multi-AZ backup | CloudWatch alarm | Start backup instance, run failover |
| **IAM role removed** | Change management, approval | DescribeInstances fails | Restore role from backup, redeploy |
| **Security group misconfigured** | Test before deploy | Connection timeouts | Fix SG rules, restart script |
| **Route 53 API throttled** | Implement retry logic | Rate limit errors in logs | Exponential backoff, SNS alert |
| **Backup instance is down** | Regular health checks | Instance status check fails | Start instance, trigger failover |
| **Network partition** | Monitor VPC Flow Logs | Ping fails, latency spikes | Failover script detects and handles |
| **Cascading failure** | Circuit breaker pattern | Multiple components down | Graceful degradation, alert on-call |
| **Data loss** | Automated backups, replication | Sync errors in logs | Restore from RDS snapshot |

**Example: Handle EC2 instance failure**

```python
import boto3
import time

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def monitor_failover_script_health():
    """Monitor if failover script instance is healthy"""

    instance_id = 'i-aws-failover-123'
    backup_instance_id = 'i-aws-failover-backup-456'

    while True:
        # Check if failover script instance is running
        response = ec2.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']

        if state != 'running':
            # Instance crashed! Switch to backup
            print(f"Instance {instance_id} is {state}. Switching to backup...")

            # Start backup instance
            ec2.start_instances(InstanceIds=[backup_instance_id])

            # Wait for backup to start
            time.sleep(30)

            # Send alert
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:alerts',
                Subject='Failover Script Instance Failed - Switched to Backup',
                Message=f'Primary instance {instance_id} crashed. Switched to backup {backup_instance_id}'
            )

            # Restart primary instance
            ec2.start_instances(InstanceIds=[instance_id])

        # Check again every 5 minutes
        time.sleep(300)
```

---

## Post-Migration

### ☑️ 22. Optimize After Migration

**Question:** What can you improve after AWS migration?

**Optimization Opportunities:**

- [ ] **Reduce failover time**
  - On-premises: ~180 seconds (detect + DNS propagation)
  - AWS: Can be ~60 seconds with health checks + Route 53
  - Further improvements:
    - Use shorter Route 53 TTL (60 seconds)
    - Implement CloudWatch alarms for faster detection
    - Use Application Load Balancer with target group health checks (instant failover)

- [ ] **Leverage AWS-native HA**
  - Replace manual failover with RDS Multi-AZ (for databases)
  - Use Application Load Balancer (automatic failover)
  - Use Auto Scaling Groups (automatic recovery)
  - Use Route 53 health checks (built-in failover)

- [ ] **Reduce costs**
  - Shut down on-premises failover hardware (save $XXX/month)
  - Use Spot Instances for non-critical backups
  - Use Reserved Instances for primary app (60% savings)
  - Monitor unused resources with Cost Explorer

- [ ] **Improve reliability**
  - Add multi-region failover (for disaster recovery)
  - Implement backup failover script in another AZ
  - Use EventBridge for event-driven failover (more flexible)
  - Implement canary deployments for safe updates

---

## Comprehensive Migration Checklist

### **Phase 0: Hybrid Setup (NEW!) (Weeks 1-4) ⭐ START HERE**

**✅ YOUR SITUATION: On-premises can access AWS via boto3**

This is the EASIEST and SAFEST path:

- [ ] 20A. Verify on-premises connectivity to AWS
- [ ] 20B. Understand hybrid architecture
- [ ] 20C. Update failover script for hybrid (manage both on-prem + AWS)
- [ ] 20D. Plan hybrid migration path (3 phases)
- [ ] 20E. Test hybrid failover extensively

**Result after Phase 0:**
- ✅ Single script managing both on-premises AND AWS resources
- ✅ Proven AWS connectivity and boto3 calls
- ✅ Low-risk approach with instant rollback capability
- ✅ Running in production simultaneously

### **Phase 1: Assessment (Week 1)**

- [ ] 1. Document current failover script functionality
- [ ] 2. Map on-premises components to AWS services
- [ ] 3. Assess script complexity level
- [ ] 4. Identify technical risks and unknowns

### **Phase 2: Design (Week 2-3)**

- [ ] 5. Design VPC and subnet architecture
- [ ] 6. Plan security groups and network access
- [ ] 7. Consider network latency and edge options
- [ ] 8. Refactor script for statelessness
- [ ] 9. Plan to use AWS SDKs (not shell commands)

### **Phase 3: Setup (Week 4-5)**

- [ ] 10. Create IAM role with proper permissions
- [ ] 11. Set up Secrets Manager for credentials
- [ ] 12. Configure CloudWatch monitoring
- [ ] 13. Set up centralized logging
- [ ] 14. (Optional) Set up Local Zones or Outposts
- [ ] 15. (Optional) Set up hybrid on-premises edge nodes

### **Phase 4: Testing (Week 6-7)**

- [ ] 16. Write unit and integration tests
- [ ] 17. Validate with full end-to-end testing
- [ ] 18. Test failure scenarios
- [ ] 19. Performance testing

### **Phase 5: Deployment (Week 8-12)**

- [ ] 20. Plan deployment strategy (blue-green)
- [ ] 21. Create rollback procedure
- [ ] 22. Deploy to EC2 in AWS
- [ ] 23. Run parallel to on-premises
- [ ] 24. Switch to AWS
- [ ] 25. Retire on-premises

### **Phase 6: Optimization (Ongoing)**

- [ ] 26. Reduce failover time with AWS-native features
- [ ] 27. Optimize costs (shut down redundant systems)
- [ ] 28. Improve reliability with multi-region
- [ ] 29. Document lessons learned
- [ ] 30. Train team on new system

---

## Common Mistakes to Avoid

| ❌ Mistake | ✅ Solution |
|-----------|-----------|
| Hardcoding credentials | Use IAM roles and Secrets Manager |
| Assuming fixed network topology | Use Route 53 for DNS failover, not IP changes |
| Running failover script with sudo | Use IAM role with minimal permissions |
| Not testing failover before production | Implement comprehensive testing |
| Maintaining persistent state in script | Use DynamoDB or Parameter Store |
| Using shell scripts instead of SDKs | Use Boto3 for reliability |
| Ignoring network latency | Account for AWS AZ latency (5-10ms) |
| Not monitoring the monitor | Set up CloudWatch alarms on failover script |
| Single point of failure | Redundant failover script in another AZ |
| Migrating without parallel run | Run both on-premises and AWS simultaneously |
| Not documenting changes | Create runbooks and architecture diagrams |
| Premature retirement of on-premises | Wait 30+ days after successful AWS migration |

---

## Hybrid Approach Advantages

### **Why Hybrid is Best for Your Situation**

You have a rare advantage: **on-premises + AWS connectivity**

| Aspect | Pure AWS Migration | Hybrid Approach (YOUR SITUATION) |
|--------|-------------------|----------------------------------|
| **Risk** | High (big-bang) | Low (gradual, proven step-by-step) |
| **Rollback Time** | 30+ minutes | < 5 minutes (just restart on-prem) |
| **Testing** | Must deploy to AWS first | Test on-prem with AWS resources |
| **Script Location** | Requires moving infrastructure | Start on-prem, move later |
| **Failover Strategy** | Must redesign for AWS | Extend existing logic with AWS SDK |
| **Downtime Risk** | High | Very low |
| **Time to Production** | 8-12 weeks | 4 weeks for hybrid + 8 more for full AWS |
| **Team Training** | Learn new AWS approach | Gradual AWS adoption |
| **Cost** | Immediate AWS costs | Phased (keep on-prem initially) |

**Bottom Line:** Hybrid lets you prove AWS integration BEFORE moving the script!

### **Three-Phase Hybrid Approach Timeline**

```
PHASE 1: HYBRID (Weeks 1-4) - On-prem script, AWS resources
├─ Add AWS SDK calls to existing script
├─ Monitor both on-prem and AWS resources
├─ Test failover between them
├─ Run in production (low risk)
└─ Result: Proven AWS integration

PHASE 2: TRANSITION (Weeks 5-8) - Primary moves to AWS
├─ Move primary workload to AWS
├─ On-prem script still manages it (from on-premises)
├─ Test AWS failure scenarios
├─ Build confidence
└─ Result: Running on AWS, managed from on-premises

PHASE 3: FINAL (Weeks 9-12) - Script moves to AWS
├─ Deploy script to AWS EC2
├─ Run parallel (on-prem + AWS scripts)
├─ Validate AWS-based failover
├─ Retire on-premises
└─ Result: Everything in AWS

Total: 12 weeks, with low risk and instant rollback at each step!
```

### **Comparison: Migration Approaches**

```
APPROACH 1: Pure AWS (Risky)
┌─────────────┐
│ On-Premises │ Delete this when moving to AWS
│   Script    │ If something breaks = downtime!
└─────────────┘
         ↓ RISKY CUTOVER
┌─────────────┐
│ AWS Script  │ New untested script
│  (Day 1)    │ No fallback
└─────────────┘

APPROACH 2: Hybrid (Safe) ← YOUR SITUATION
┌─────────────┐
│ On-Premises │
│   Script    │ Stay here, manage AWS resources
└────────┬────┘
         │ Add boto3 calls
         ↓
    [AWS Resources]
         │ Proven working
         ↓
┌─────────────┐
│ AWS Script  │ Move script only when confident
│  (Week 9)   │ On-prem is backup
└─────────────┘
         │ If fails
         ↓
┌─────────────┐
│ On-Premises │ Always there as fallback!
│   Script    │ < 5 min to activate
└─────────────┘
```

---

## Key Takeaways

### **Essential Differences to Remember**

1. **Infrastructure as Code** - Don't SSH and manually configure; use Terraform or CloudFormation

2. **Statelessness** - Store state in DynamoDB/Parameter Store, not local files

3. **API-Driven** - Use Boto3 SDK, not shell commands

4. **Security** - Use IAM roles, not embedded credentials

5. **Networking** - Understand VPC, security groups, and cross-AZ latency

6. **Monitoring** - CloudWatch is your friend (logs, metrics, alarms)

7. **Testing** - Comprehensive testing before production is non-negotiable

8. **Gradual Migration** - Blue-green or canary deployments, not big-bang

9. **Redundancy** - Multiple AZs, backup instances, failover scripts

10. **Documentation** - Runbooks, architecture diagrams, testing results

---

## Next Steps

1. **Start with Assessment:** Complete sections 1-3 of this checklist
2. **Design Architecture:** Complete sections 4-7
3. **Build & Test:** Complete sections 8-17
4. **Deploy Safely:** Complete sections 18-21
5. **Optimize:** Complete section 22

---

## Resources

- **AWS Documentation:** https://docs.aws.amazon.com/
- **Boto3 Reference:** https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **EC2 Best Practices:** https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-best-practices.html
- **VPC Best Practices:** https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html
- **IAM Best Practices:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- **This Repository:** `/Users/paramraghavan/dev/123ofaws/`
  - Failover Reference: `failover_ver3/README.md`
  - Monitoring Reference: `aws-lambda-monitoring/README.md`
  - Migration Guide: `FAILOVER_AND_MONITORING_GUIDE.md`

---

**Last Updated:** March 2026
**Status:** Production Ready
**Scope:** Brownfield to AWS EC2 Migration
