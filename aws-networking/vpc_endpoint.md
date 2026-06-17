# VPC Endpoints and Services Inside VPC - Complete Guide

---

## Quick Answer: Three Different Concepts

| Concept | What It Means | Network Initialization | Use Case |
|---------|--------------|----------------------|----------|
| **Service INSIDE VPC** | Service runs with ENI in your VPC | YES - needs ENI, security groups, IAM roles | RDS, EC2, ECS (Fargate in VPC) |
| **VPC ENDPOINT** | Private link to reach EXTERNAL services | YES - setup once, NO code init | Access S3, DynamoDB, Lambda API from inside VPC |
| **NAT/Public Route** | Go through internet to reach services | NO special init - traffic routes out | Access public services via NAT Gateway |

---

## Part 1: Lambda INSIDE VPC vs Lambda VPC ENDPOINT (KEY DIFFERENCE)

### Lambda INSIDE VPC (Lambda Function Runs in VPC)

**What it means:**
- Lambda execution environment gets an ENI (Elastic Network Interface) in your VPC
- Lambda can directly access resources in VPC (RDS, ElastiCache, private databases)
- Lambda CANNOT access internet unless configured with NAT Gateway
- Cold starts are ~1-2 seconds longer

**Network Initialization - YES, Required:**

**AWS Console Setup:**
1. Go to Lambda function
2. VPC section → Edit
3. Select 2+ Subnets (for HA)
4. Select Security Group
5. Save

**CloudFormation:**
```yaml
MyFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: my-function
    VpcConfig:
      SecurityGroupIds:
        - !Ref LambdaSecurityGroup
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
```

**Boto3:**
```python
client = boto3.client('lambda')
client.create_function(
    FunctionName='my-function',
    Runtime='python3.9',
    Role='arn:aws:iam::123456789012:role/lambda-role',
    Handler='index.handler',
    Code={'ZipFile': b'code'},
    VpcConfig={
        'SubnetIds': ['subnet-12345', 'subnet-67890'],
        'SecurityGroupIds': ['sg-abcdef']
    }
)
```

**Security Group Rules Required:**
```
Outbound:
  - HTTPS (443) to 0.0.0.0/0 (for AWS API calls to S3, DynamoDB)
  - All traffic to VPC CIDR (for internal resources)

Inbound:
  - If other VPC resources need to reach Lambda
```

**Network diagram:**
```
Lambda in VPC → ENI in Subnet → Can access VPC resources (RDS, etc)
                             → Can access AWS services (if VPC endpoint or NAT)
                             → Cannot access internet (without NAT)
```

**Code example:**
```python
import boto3
import pymysql

# This works (RDS in VPC - direct access via ENI)
connection = pymysql.connect(
    host='rds-instance.internal',  # VPC DNS
    user='admin'
)

# This works IF VPC endpoint configured for S3
s3 = boto3.client('s3')
s3.put_object(Bucket='bucket', Key='data.txt', Body=b'data')

# This FAILS (no internet) - unless NAT Gateway exists
import requests
response = requests.get('https://api.external.com')  # ❌ Error
```

**Benefits:**
✅ Access to VPC resources (RDS, databases, private services)
✅ Security - stays private within VPC

**Drawbacks:**
❌ Cold starts ~1-2 seconds longer
❌ Requires NAT Gateway for internet access
❌ More complex network setup

---

### Lambda VPC ENDPOINT (Access Lambda Service from Inside VPC)

**What it means:**
- Resources INSIDE your VPC (EC2, container, etc) can call the Lambda service API privately
- Lambda service itself is still OUTSIDE your VPC (managed service)
- NOT about where Lambda runs, but how to CALL Lambda from inside VPC
- Private link from VPC resources to Lambda service

**Network Initialization - YES, Setup Once:**

**AWS CLI Setup:**
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.lambda \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-12345 subnet-67890 \
  --security-group-ids sg-abcdef
```

**CloudFormation:**
```yaml
LambdaEndpoint:
  Type: AWS::EC2::VPCEndpoint
  Properties:
    VpcId: !Ref MyVPC
    ServiceName: !Sub com.amazonaws.${AWS::Region}.lambda
    VpcEndpointType: Interface
    SubnetIds:
      - !Ref PrivateSubnet1
      - !Ref PrivateSubnet2
    SecurityGroupIds:
      - !Ref EndpointSecurityGroup
```

**Network diagram:**
```
EC2 in VPC → VPC Endpoint ENI → Lambda Service (outside VPC)
            (private link, no internet)
```

**Code to invoke Lambda from EC2:**
```python
import boto3

# EC2 instance inside VPC calling Lambda function
lambda_client = boto3.client('lambda')

# With VPC Endpoint: This call goes through private link
# Without VPC Endpoint: This call goes through NAT → Internet → Lambda
response = lambda_client.invoke(
    FunctionName='my-function',
    Payload='{"key": "value"}'
)
```

**NO special code initialization needed** - boto3 automatically detects and uses endpoint

**Benefits:**
✅ Private connectivity from VPC to Lambda service
✅ No data leaves AWS network
✅ Faster than going through internet
✅ No NAT Gateway charges for Lambda calls

**Drawbacks:**
❌ Additional cost (~$7-14/month + $0.01/GB data)
❌ Additional setup required

---

## Part 2: S3 and DynamoDB (CANNOT Be "Inside VPC")

### Key Point: S3 and DynamoDB are Managed Services OUTSIDE VPC

**You CANNOT put S3 or DynamoDB "inside VPC" like you can with RDS or Lambda.**

### S3 - Without VPC Endpoint

**Network Initialization - Not required, but expensive:**

```
Lambda in VPC (10.0.1.10)
    ↓
  NAT Gateway
    ↓ (goes to INTERNET)
  S3 Service (outside VPC)
```

**Code:**
```python
import boto3

s3 = boto3.client('s3')
s3.put_object(Bucket='my-bucket', Key='data.txt', Body=b'data')
# Route: Lambda → NAT Gateway → Internet → S3
# Cost: NAT Gateway charges + data transfer charges
```

**Cost Impact:**
- NAT Gateway: ~$32/month + $0.045/GB data
- S3 calls go through NAT = additional costs

---

### S3 - With VPC Gateway Endpoint

**Network Initialization - YES, Setup Once:**

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345
```

**Route table entry added automatically:**
```
Destination: S3 CIDR Range (e.g., 52.94.0.0/16)
Target: VPC Endpoint ID
Action: Auto-applied when endpoint created
```

**Network diagram:**
```
Lambda in VPC (10.0.1.10)
    ↓ (private link)
VPC Endpoint Gateway
    ↓ (private AWS network)
S3 Service (outside VPC, accessed privately)
```

**Code:**
```python
import boto3

s3 = boto3.client('s3')
s3.put_object(Bucket='my-bucket', Key='data.txt', Body=b'data')
# Route: Lambda → VPC Endpoint → S3 (PRIVATE)
# NO CODE CHANGES - boto3 automatically uses endpoint!
```

**NO code initialization needed** - boto3 detects endpoint automatically

**Benefits:**
✅ FREE (no cost)
✅ Private connectivity
✅ No NAT Gateway charges
✅ Lower latency
✅ No code changes

**Cost savings:**
- Without endpoint: ~$32/month (NAT) + data charges
- With endpoint: FREE
- **Savings: ~$32/month per region**

---

### DynamoDB - Without VPC Endpoint

**Network Initialization - Not required, but expensive:**

```
Lambda in VPC (10.0.1.10)
    ↓
  NAT Gateway
    ↓ (INTERNET)
  DynamoDB Service (outside VPC)
```

**Code:**
```python
import boto3

dynamodb = boto3.client('dynamodb')
dynamodb.get_item(TableName='users', Key={'id': {'S': 'user1'}})
# Route: Lambda → NAT → Internet → DynamoDB
# Cost: NAT Gateway charges
```

---

### DynamoDB - With VPC Gateway Endpoint

**Network Initialization - YES, Setup Once:**

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345
```

**Network diagram:**
```
Lambda in VPC (10.0.1.10)
    ↓ (private link)
VPC Endpoint Gateway
    ↓ (private AWS network)
DynamoDB Service (outside VPC, accessed privately)
```

**Code:**
```python
import boto3

dynamodb = boto3.client('dynamodb')
dynamodb.get_item(TableName='users', Key={'id': {'S': 'user1'}})
# Route: Lambda → VPC Endpoint → DynamoDB (PRIVATE)
# NO CODE CHANGES - boto3 automatically uses endpoint!
```

**NO code initialization needed** - boto3 detects endpoint automatically

**Benefits:**
✅ FREE (Gateway endpoint)
✅ Private connectivity
✅ No NAT Gateway charges
✅ Lower latency

---

## Part 3: Network Initialization Summary

### Services That NEED Network Initialization When "Inside VPC"

| Service | Type | Network Init Required? | What You Need |
|---------|------|----------------------|--------------|
| **RDS** | Inside VPC | YES | DB Subnet Group, Security Groups, connection strings |
| **EC2** | Inside VPC | YES | Subnet, Security Groups, routing |
| **ECS Fargate** | Inside VPC | YES | VPC, Subnets, Security Groups |
| **ElastiCache** | Inside VPC | YES | Subnet Group, Security Groups, endpoint addresses |
| **Lambda** | Inside VPC (optional) | YES | VpcConfig (subnets + SG), IAM role, timeout increase |

---

### Services That DON'T Need Code Initialization (Use VPC Endpoints)

| Service | Endpoint Type | Network Init? | Code Init? | Cost |
|---------|---------------|--------------|-----------|------|
| **S3** | Gateway | YES (once) | NO | FREE |
| **DynamoDB** | Gateway | YES (once) | NO | FREE |
| **SNS** | Interface | YES (once) | NO | $7-14/mo |
| **SQS** | Interface | YES (once) | NO | $7-14/mo |
| **Lambda API** | Interface | YES (once) | NO | $7-14/mo |
| **Secrets Manager** | Interface | YES (once) | NO | $7-14/mo |
| **CloudWatch Logs** | Interface | YES (once) | NO | $7-14/mo |

**Key Point:** After VPC endpoint setup, boto3 code works unchanged - no special initialization code needed!

---

## Part 4: Real-World Scenario - Your Region Failover Setup

### Architecture with VPC Endpoints (Recommended)

```
┌─────────────────────────────────────────┐
│     VPC East-1 (10.0.0.0/16)            │
│  ┌──────────────────────────────────┐   │
│  │  Lambda (in VPC)                 │   │
│  │  - Subnets: subnet-1, subnet-2   │   │
│  │  - SecurityGroup: sg-lambda      │   │
│  └──────────────────────────────────┘   │
│              │                           │
│              ├─ S3 Gateway Endpoint ────→ S3
│              │  (FREE, private)         │
│              │                          │
│              ├─ DynamoDB Gateway ──────→ DynamoDB Global Table
│              │  (FREE, private)         │
│              │                          │
│              └─ NAT Gateway ───────────→ Snowflake
│                 (for external access)   │
│                 Cost: ~$32/mo           │
└─────────────────────────────────────────┘

Same setup for East-2 VPC
```

### Code Works Unchanged in Both Regions

```python
# Lambda code - SAME for both regions
import boto3

# Network initialization: NONE NEEDED
# Boto3 automatically detects VPC endpoints

# Access S3 (via Gateway endpoint)
s3 = boto3.client('s3')
s3.put_object(Bucket='data-bucket', Key='file.txt', Body=b'data')

# Access DynamoDB (via Gateway endpoint)
dynamodb = boto3.client('dynamodb')
dynamodb.put_item(TableName='config', Item={'region': {'S': 'east-2'}})

# Access external (via NAT Gateway)
import requests
response = requests.get('https://snowflake.example.com')
```

**Regional Failover Steps:**
```
1. Update ACTIVE_REGION in DynamoDB Global Table: "us-east-2"
2. Lambda picks up new region automatically
3. All S3/DynamoDB calls route through East-2 VPC endpoints
4. NO CODE CHANGES NEEDED
5. NO LAMBDA REDEPLOYMENT NEEDED
```

---

## Part 5: Detailed Comparison - All AWS Services

| Service | Inside VPC? | VPC Endpoint? | Network Init? | Code Init? | Cost |
|---------|------------|--------------|--------------|-----------|------|
| **RDS** | ✅ YES | ❌ NO (in VPC) | ✅ YES | ✅ YES | Service charges |
| **EC2** | ✅ YES | ❌ NO (in VPC) | ✅ YES | ✅ YES | Instance charges |
| **ECS Fargate** | ✅ YES | ❌ NO (in VPC) | ✅ YES | ✅ YES | Task charges |
| **ElastiCache** | ✅ YES | ❌ NO (in VPC) | ✅ YES | ✅ YES | Cluster charges |
| **Lambda** | ✅ OPTIONAL | ✅ YES (for API) | ✅ IF in VPC | ❌ NO | Free (endpoint) |
| **S3** | ❌ NO | ✅ YES (Gateway) | ✅ ONCE | ❌ NO | FREE |
| **DynamoDB** | ❌ NO | ✅ YES (Gateway) | ✅ ONCE | ❌ NO | FREE |
| **SNS** | ❌ NO | ✅ YES (Interface) | ✅ ONCE | ❌ NO | $7-14/mo |
| **SQS** | ❌ NO | ✅ YES (Interface) | ✅ ONCE | ❌ NO | $7-14/mo |
| **Kinesis** | ❌ NO | ✅ YES (Interface) | ✅ ONCE | ❌ NO | $7-14/mo |
| **Secrets Manager** | ❌ NO | ✅ YES (Interface) | ✅ ONCE | ❌ NO | $7-14/mo |
| **CloudWatch Logs** | ❌ NO | ✅ YES (Interface) | ✅ ONCE | ❌ NO | $7-14/mo |

---

## Part 6: Decision Tree

```
Question 1: Is service a managed service (S3, DynamoDB, SNS)?
│
├─ YES → Use VPC ENDPOINT
│        (Setup once, no code changes, boto3 automatic)
│
└─ NO → Is it a database or compute service (RDS, EC2, ECS)?
       │
       ├─ YES → Can be INSIDE VPC
       │        (Network init required: subnets, SG)
       │
       └─ NO → Lambda?
              │
              ├─ In VPC? → Network init (subnets, SG, timeout)
              └─ For API access? → Use Lambda VPC ENDPOINT
```

---

## Part 7: Cost Comparison for Your Setup

### Option 1: Without VPC Endpoints (More Expensive)

```
Lambda in VPC (East-1):
├─ NAT Gateway for S3/DynamoDB: $32.40/month
├─ Data transfer (1GB/day avg): $0.045 × 30 = $1.35/month
└─ Subtotal East-1: ~$34/month

Lambda in VPC (East-2):
├─ NAT Gateway for S3/DynamoDB: $32.40/month
├─ Data transfer (1GB/day avg): $0.045 × 30 = $1.35/month
└─ Subtotal East-2: ~$34/month

TOTAL: ~$68/month for 2 regions
```

### Option 2: With VPC Gateway Endpoints (Recommended)

```
Lambda in VPC (East-1):
├─ S3 Gateway Endpoint: FREE
├─ DynamoDB Gateway Endpoint: FREE
└─ Subtotal East-1: $0/month

Lambda in VPC (East-2):
├─ S3 Gateway Endpoint: FREE
├─ DynamoDB Gateway Endpoint: FREE
└─ Subtotal East-2: $0/month

TOTAL: $0/month for 2 regions
```

**Savings: $68/month (~$816/year) for 2 regions**

---

## Part 8: Quick Setup for Your Failover

### Step 1: Create S3 Gateway Endpoint in East-1
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-east1-id \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-east1-id
```

### Step 2: Create DynamoDB Gateway Endpoint in East-1
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-east1-id \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-east1-id
```

### Step 3: Repeat for East-2 (with us-east-2 service names)
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-east2-id \
  --service-name com.amazonaws.us-east-2.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-east2-id

aws ec2 create-vpc-endpoint \
  --vpc-id vpc-east2-id \
  --service-name com.amazonaws.us-east-2.dynamodb \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-east2-id
```

### Step 4: Verify Endpoints Created
```bash
# East-1
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=vpc-east1-id

# East-2
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=vpc-east2-id
```

### Step 5: No Code Changes!
Your existing Lambda code works in both regions automatically.

---

## Part 9: When to Use Each Approach - Decision Guide

### Scenario 1: Lambda Needs to Access VPC Resources
**Use: Lambda INSIDE VPC**

Examples:
- Lambda → Query RDS database
- Lambda → Write to ElastiCache
- Lambda → SSH to EC2 instance
- Lambda → Call private microservice
- Lambda → Access private API Gateway

```
Lambda (IN VPC)
  └─ Direct access to RDS, ElastiCache, etc (same VPC)
```

**Setup:**
```python
# In Lambda console or IaC:
VpcConfig = {
    'SubnetIds': ['subnet-12345', 'subnet-67890'],
    'SecurityGroupIds': ['sg-lambda-sg']
}
```

**Code example:**
```python
import pymysql

# Direct access to private RDS
connection = pymysql.connect(
    host='rds-instance.c123456.us-east-1.rds.amazonaws.com',  # Private RDS
    user='admin',
    password='password'
)
cursor = connection.cursor()
cursor.execute("SELECT * FROM users")
```

**Trade-offs:**
✅ Direct access to VPC resources
✅ Secure (no internet exposure)
❌ Cold starts ~1-2 seconds longer
❌ Requires NAT Gateway if needs internet
❌ More complex setup

---

### Scenario 2: EC2/Container in VPC Needs to Call Lambda
**Use: Lambda VPC ENDPOINT**

Examples:
- EC2 instance invoking Lambda function
- ECS container invoking Lambda
- Other VPC resources triggering Lambda
- Step Functions in VPC calling Lambda

```
EC2 in VPC
  └─ Calls Lambda via VPC Endpoint
       └─ Lambda (can be in VPC or not)
```

**Setup (one time):**
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.lambda \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-12345 subnet-67890 \
  --security-group-ids sg-abcdef
```

**Code example (EC2 calling Lambda):**
```python
import boto3

# On EC2 inside VPC
lambda_client = boto3.client('lambda')

# This call goes through VPC Endpoint (private)
# Instead of NAT → Internet → Lambda
response = lambda_client.invoke(
    FunctionName='process-data',
    InvocationType='RequestResponse',
    Payload='{"data": "value"}'
)
```

**Trade-offs:**
✅ Private connectivity from VPC to Lambda service
✅ No NAT Gateway charges for Lambda calls
✅ Lambda can stay outside VPC (better performance)
❌ Additional setup (~$7-14/month)
❌ EC2/container specific (not for Lambda-to-Lambda)

---

### Scenario 3: Lambda Calls AWS Services (S3, DynamoDB)
**Use: VPC GATEWAY ENDPOINTS (NOT Lambda VPC ENDPOINT)**

Examples:
- Lambda (in VPC) → S3
- Lambda (in VPC) → DynamoDB
- Lambda (in VPC) → CloudWatch

```
Lambda in VPC
  └─ Calls S3/DynamoDB via Gateway Endpoint (private, FREE)
```

**Setup (one time):**
```bash
# S3 Gateway Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345

# DynamoDB Gateway Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-12345
```

**Code example:**
```python
import boto3

# Lambda in VPC
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

# These automatically use Gateway Endpoints (private)
# NO code changes needed!
s3.put_object(Bucket='bucket', Key='file', Body=b'data')
dynamodb.get_item(TableName='table', Key={'id': {'S': 'value'}})
```

**Trade-offs:**
✅ FREE (no cost!)
✅ Private connectivity
✅ No code changes
✅ Lower latency
❌ One-time setup
❌ Only works for managed services (S3, DynamoDB, SNS, SQS, etc)

---

## Decision Matrix: Which Option to Use?

```
Question 1: Lambda needs to ACCESS something?
│
├─ YES → Question 2: What does it access?
│        │
│        ├─ VPC resource (RDS, EC2, ElastiCache, private service)?
│        │  └─ USE: Lambda INSIDE VPC
│        │
│        ├─ AWS managed service (S3, DynamoDB, SNS, SQS, CloudWatch)?
│        │  └─ USE: VPC GATEWAY ENDPOINT (with Lambda in VPC)
│        │
│        └─ External internet?
│           └─ USE: Lambda OUTSIDE VPC + NAT Gateway (if in VPC)
│
└─ NO → Question 2: Does something in VPC CALL Lambda?
       │
       ├─ YES → EC2, container, or other VPC compute needs to invoke Lambda?
       │  └─ USE: Lambda VPC ENDPOINT
       │
       └─ NO → Standard Lambda (S3 trigger, API Gateway, scheduled)?
          └─ USE: Lambda OUTSIDE VPC (default, best performance)
```

---

## Real-World Example: Your Region Failover Setup

### Your Current Architecture

```
VPC East-1
├─ Lambda function
├─ S3 bucket (outside VPC)
├─ DynamoDB table (outside VPC)
└─ Snowflake (external internet)
```

### Decision: What Should You Use?

**Q1: Does Lambda need to access S3/DynamoDB?**
- A: YES → Use VPC Gateway Endpoints (S3, DynamoDB)

**Q2: Does Lambda need to access VPC resources?**
- A: NO → Don't put Lambda in VPC

**Q3: Does something in VPC call Lambda?**
- A: NO → Don't need Lambda VPC Endpoint

### Recommended Setup for Your Failover

```
┌─────────────────────────────────┐
│     VPC East-1                  │
│  ┌─────────────────────────┐    │
│  │  Lambda (OUTSIDE VPC)   │    │
│  │  - No VpcConfig         │    │
│  │  - Fast cold starts     │    │
│  │  - Simple setup         │    │
│  └─────────────────────────┘    │
│         │                       │
│         ├─ S3 Gateway Endpoint ─┘ (FREE)
│         │
│         └─ DynamoDB Gateway Endpoint (FREE)
│
│  Route Tables:
│  └─ S3 CIDR → S3 Gateway Endpoint
│  └─ DynamoDB CIDR → DynamoDB Gateway Endpoint
└─────────────────────────────────┘

No Lambda VPC Endpoint needed (nothing calls Lambda from VPC)
```

**Code (same for both regions):**
```python
import boto3

# No special initialization needed
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

# Boto3 automatically uses Gateway Endpoints
s3.put_object(Bucket='data', Key='file', Body=b'data')
dynamodb.put_item(TableName='config', Item={'region': {'S': 'east-2'}})
```

**Failover process:**
1. Update DynamoDB Global Table: `ACTIVE_REGION = "us-east-2"`
2. Lambda automatically uses East-2 Gateway Endpoints
3. No code changes, no Lambda redeployment
4. Cost: $0 (Gateway endpoints are free)

---

## Summary Table

| Use Case | Lambda INSIDE VPC | Lambda VPC ENDPOINT | Gateway Endpoints (S3/DynamoDB) |
|----------|------------------|-------------------|----------------------------------|
| **Lambda needs RDS/private DB** | ✅ USE THIS | ❌ | N/A |
| **Lambda needs S3/DynamoDB** | ✅ Optional | ❌ | ✅ USE THIS (free) |
| **EC2 in VPC calls Lambda** | ❌ | ✅ USE THIS | N/A |
| **Lambda needs internet** | ❌ (needs NAT) | ❌ | N/A |
| **Your failover setup** | ❌ Not needed | ❌ Not needed | ✅ USE THIS |
| **Setup complexity** | High | Medium | Low |
| **Cold start impact** | 1-2 sec longer | None | None |
| **Cost** | Service charges | $7-14/mo | FREE |
| **Code changes** | YES | NO | NO |

---

## Quick Checklist: Which to Choose?

```
Does Lambda need to access VPC resources (RDS, ElastiCache, EC2)?
  YES  → Lambda INSIDE VPC (accept longer cold starts)
  NO   → Go to next question

Does something in VPC CALL Lambda via API?
  YES  → Lambda VPC ENDPOINT (for EC2/container calling Lambda)
  NO   → Go to next question

Does Lambda need private access to S3/DynamoDB from VPC?
  YES  → Gateway VPC Endpoints (FREE, automatic)
  NO   → Lambda OUTSIDE VPC (default, best performance)
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Lambda INSIDE VPC vs Lambda VPC ENDPOINT - Same?** | NO. "Inside VPC" = Lambda runs in VPC. "VPC ENDPOINT" = Access Lambda API from VPC. |
| **Lambda INSIDE VPC - Network init?** | YES - need subnets, security group, longer timeouts |
| **S3 Gateway Endpoint - Network init?** | YES (one-time setup), NO (code changes) |
| **DynamoDB Gateway Endpoint - Network init?** | YES (one-time setup), NO (code changes) |
| **Cost of Gateway Endpoints?** | FREE - saves ~$32/month per region (vs NAT) |
| **Code changes for VPC endpoints?** | NO - boto3 detects automatically |
| **For your failover setup?** | Create Gateway endpoints in both regions, update DynamoDB ACTIVE_REGION, done! |

