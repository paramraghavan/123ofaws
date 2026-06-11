# AWS Networking Complete Guide

> **Master AWS Network Architecture**: Build secure, scalable networks from beginner through advanced patterns.

---

## Table of Contents

1. [The Mental Model](#the-mental-model-sticks-in-your-mind)
2. [Quick Reference](#quick-reference)
3. [VPC Fundamentals](#vpc-fundamentals)
4. [Subnets: Public vs Private](#subnets-public-vs-private)
5. [Security: Groups & NACLs](#security-groups--nacls)
6. [Network Components](#network-components)
7. [Architecture Patterns](#architecture-patterns)
8. [Hands-On Exercises](#hands-on-exercises)
9. [Troubleshooting](#troubleshooting)

---

## The Mental Model (Sticks in Your Mind!)

Think of AWS networking like **securing a building**:

```
THE BUILDING ANALOGY
│
├─ AWS Account = Secure Compound
│  └─ Your own property you control
│
├─ VPC = Your Building Within the Compound
│  └─ Your isolated private network (10.0.0.0/16)
│  └─ No one else can enter
│
├─ Subnets = Rooms in Your Building
│  ├─ Public Room (Front Lobby) - 10.0.1.0/24
│  │  └─ Visible from outside (has windows/doors)
│  │  └─ Receives visitors (public IPs)
│  │  └─ Examples: web servers, load balancers
│  │
│  └─ Private Room (Vault) - 10.0.2.0/24
│     └─ Hidden from outside view
│     └─ No direct access from visitors
│     └─ Examples: databases, app servers
│
├─ NACL = Security Checkpoint at Each Room Entrance
│  └─ (Subnet-level control)
│  └─ Checks everyone entering/leaving the room
│  └─ Stateless (checks both directions explicitly)
│
├─ Security Group = Door Locks on Each Room
│  └─ (Instance-level control)
│  └─ Protects individual machines inside
│  └─ Stateful (remembers who's allowed in)
│
├─ Internet Gateway (IGW) = Entrance to the Compound from Outside
│  └─ Main door/gate connecting to the outside world
│  └─ Handles translation between outside visitors and internal rooms
│
├─ NAT Gateway = One-Way Exit Door (Private Rooms Only)
│  └─ Private rooms can leave through this door
│  └─ But outside people cannot find/enter through it
│  └─ They see the NAT's public address, not the private room's
│
└─ VPC Endpoints = Secret Tunnels to AWS Services
   └─ Direct private connections (no need to go outside)
   └─ Private rooms can reach AWS services without exposure
   └─ Examples: S3, Lambda, DynamoDB
```

**Key Mental Model Summary:**
- **AWS Account** = Secure compound (your property)
- **VPC** = Building within compound (isolated network)
- **Subnets** = Rooms (public or private)
- **Security Groups** = Door locks per room (instance-level)
- **NACLs** = Checkpoints at room entrances (subnet-level)
- **IGW** = Main entrance to outside world
- **NAT** = One-way exit door for private rooms
- **VPC Endpoints** = Secret tunnels to AWS services

---

## Quick Reference

### Decision Tables

#### Choose Public or Private Subnet?

| Your Need | Choose | Why |
|-----------|--------|-----|
| **Web servers** | Public | Need internet access |
| **Databases** | Private | Hidden from internet |
| **App servers** | Private | Don't need direct internet access |
| **Load balancers** | Public | Receive traffic from internet |
| **Lambda** | Either | Depends on what it accesses |

---

#### Network Component Quick Lookup

| Component | Purpose | Cost | Notes |
|-----------|---------|------|-------|
| **VPC** | Isolated network | FREE | Default VPC included |
| **Subnet** | Network segment | FREE | Choose AZ wisely |
| **IGW** | Internet gateway | FREE | Only 1 per VPC |
| **NAT Gateway** | Private exit | ~$32/month | One per AZ recommended |
| **VPC Endpoint (Gateway)** | Private S3/DynamoDB access | FREE | S3, DynamoDB only |
| **VPC Endpoint (Interface)** | Private service access | ~$7/month | 100+ AWS services |
| **Security Group** | Instance firewall | FREE | Stateful |
| **NACL** | Subnet firewall | FREE | Stateless |
| **Route Table** | Traffic routing | FREE | Multiple allowed |
| **Elastic IP** | Static public IP | ~$3.50/month if unused | Use wisely |

---

## VPC Fundamentals

### What is a VPC?

A **VPC** is your own isolated network in AWS. Think of it as renting a private city where you control everything.

```
Without VPC:
└─ All AWS users in one shared network (dangerous!)

With VPC:
└─ Your private isolated network (safe!)
   ├─ No one else can access your resources
   └─ You control all security
```

### VPC CIDR Block

The **CIDR block** defines your IP address range:

```
VPC CIDR: 10.0.0.0/16

Breakdown:
├─ First part (10.0) = Fixed (network)
├─ Last part (0.0) = Variable (devices)
├─ /16 = Allows 65,536 IP addresses
│
└─ Example addresses:
   ├─ 10.0.0.0      → Network address (reserved)
   ├─ 10.0.0.1      → VPC router (reserved)
   ├─ 10.0.0.2-3    → DNS/reserved
   ├─ 10.0.0.4+     → Available for devices
   └─ 10.0.255.255  → Broadcast (reserved)
```

### Common CIDR Sizes

```
/16 = 65,536 addresses  ← Standard for VPC
/20 = 4,096 addresses   ← For subnets
/24 = 256 addresses     ← For small subnets
/28 = 16 addresses      ← For very specific use
```

---

## Subnets: Public vs Private

### What is a Subnet?

A **subnet** is a smaller network inside your VPC. Each subnet belongs to ONE availability zone.

```
VPC: 10.0.0.0/16
│
├─ us-east-1a
│  ├─ Public Subnet:  10.0.1.0/24  (256 addresses)
│  └─ Private Subnet: 10.0.11.0/24 (256 addresses)
│
└─ us-east-1b
   ├─ Public Subnet:  10.0.2.0/24  (256 addresses)
   └─ Private Subnet: 10.0.12.0/24 (256 addresses)
```

### Public Subnet (Internet-Facing)

**Characteristics:**
- ✅ Route table points to Internet Gateway
- ✅ Instances get public IP addresses
- ✅ Accessible from the internet

**Traffic flow (with Route Table):**
```
OUTBOUND (EC2 to Internet):
EC2 Instance (10.0.1.5)
    ↓ (destination: 8.8.8.8 - external IP)
Route Table (subnet 10.0.1.0/24):
├─ 0.0.0.0/0 → igw-xxxxx          ← Matches! Send to IGW
└─ 10.0.0.0/16 → local
    ↓
    IGW (Internet Gateway)
    ↓
    Internet

INBOUND (Internet to EC2):
Internet (source: 8.8.8.8)
    ↓
    IGW (Internet Gateway - entry point)
    ↓
Route Table lookup (which subnet?):
    ↓
Public Subnet (10.0.1.0/24)
    ↓
EC2 Instance
```

**Route Table Purpose:**
- Decides WHERE traffic goes based on destination IP
- For public subnets: sends internet traffic (0.0.0.0/0) to IGW
- For private subnets: sends internet traffic to NAT Gateway
- Without correct route table = traffic doesn't know where to go!

**Use for:**
- Web servers (nginx, Apache)
- Load balancers
- Bastion hosts (SSH gateways)

**Example:**
```bash
# Public subnet route table (sends internet traffic to IGW)
Destination      Target
0.0.0.0/0    →   igw-xxxxx     (Internet traffic goes to IGW)
10.0.0.0/16  →   local          (Internal VPC traffic stays local)
```

---

### Private Subnet (Hidden from Internet)

**Characteristics:**
- ✅ Route table points to NAT Gateway
- ❌ Instances do NOT have public IPs
- ❌ NOT accessible from internet (inbound blocked)

**Traffic flow (outbound only - Route Table directs to NAT):**
```
OUTBOUND (EC2 to Internet):
EC2 Instance (10.0.2.5)
    ↓ (destination: 8.8.8.8 - external IP)
Route Table (subnet 10.0.2.0/24):
├─ 0.0.0.0/0 → nat-xxxxx          ← Matches! Send to NAT
└─ 10.0.0.0/16 → local
    ↓
    NAT Gateway (hides private IP, uses public IP)
    ↓
    IGW (Internet Gateway)
    ↓
    Internet (response comes back same way)

INBOUND: ✗ Cannot happen
Reason: NAT is one-way. Internet doesn't know private IP exists.
```

**Use for:**
- Databases (RDS, DynamoDB)
- Application servers
- Sensitive workloads

**Example:**
```bash
# Private subnet route table (sends internet traffic to NAT, not IGW)
Destination      Target
0.0.0.0/0    →   nat-xxxxx     (Internet traffic goes to NAT, not IGW!)
10.0.0.0/16  →   local         (Internal VPC traffic stays local)
```

---

### Comparison Table

| Feature | Public | Private |
|---------|--------|---------|
| **Public IP** | ✓ Yes | ❌ No |
| **Internet accesses it** | ✓ Yes | ❌ No |
| **It accesses internet** | ✓ Yes (IGW) | ✓ Yes (NAT) |
| **Route to IGW** | ✓ Yes | ❌ No |
| **Route to NAT** | ❌ No | ✓ Yes |
| **Use for** | Web servers | Databases |

---

## Security: Groups & NACLs

### Understanding CIDR Notation & 0.0.0.0/0

**CIDR (Classless Inter-Domain Routing)** is how you specify IP address ranges.

**Common CIDR blocks:**
| CIDR | Means | Example Use |
|------|-------|------------|
| `0.0.0.0/0` | **ALL IP addresses** (anywhere on internet) | Public web (HTTP/443) |
| `10.0.0.0/16` | Private VPC (10.0.0.0 - 10.0.255.255) | Internal traffic |
| `192.168.1.0/24` | Specific subnet (256 IPs) | Your office |
| `203.0.113.42/32` | Single IP address | Your home IP |

**What is 0.0.0.0/0?**
- The `/0` means "zero bits matter for matching" → matches ALL IPs
- Real meaning: "Anyone on the internet"
- ✓ Use for: HTTP (80), HTTPS (443) - public web traffic
- ❌ Avoid for: SSH (22), RDS (3306), RDP (3389) - management access

**Example:**
```bash
# Good: Web server open to internet
Port 443 from 0.0.0.0/0 ✓

# Bad: SSH open to internet (security risk!)
Port 22 from 0.0.0.0/0 ❌

# Better: SSH from your office only
Port 22 from 203.0.113.0/24 ✓
```

**IPv6 equivalent:** `::/0` (all IPv6 addresses)

---

### Quick Comparison

```
Two layers of security:

NACL (Subnet-Level)           Security Group (Instance-Level)
├─ Stateless                  ├─ Stateful
├─ Checks both directions     ├─ Remembers conversations
├─ Allow + Deny rules         ├─ Allow only
├─ Applied to entire subnet   └─ Applied to instances
└─ Like a gate at entrance
```

---

### Security Groups (Instance Firewall)

**What it does:**
- Controls which traffic can reach an EC2 instance
- Stateful: remembers return traffic
- Default: DENY all inbound, ALLOW all outbound

**Mental model:**
```
EC2 Instance
├─ Security Group = Bouncer
│  ├─ "Port 80 from anywhere? OK"
│  ├─ "Port 22 from 10.0.0.0/16? OK"
│  ├─ "Port 3306 from anywhere? NO"
│  └─ Return traffic automatic
```

**Example rules:**

```bash
# Web server security group
Inbound:
├─ HTTP (80) from 0.0.0.0/0      ✓
├─ HTTPS (443) from 0.0.0.0/0     ✓
├─ SSH (22) from 10.0.0.0/16      ✓
└─ Everything else                ✗ (blocked)

Outbound:
└─ All traffic allowed (default)
```

---

### NACLs (Subnet Firewall)

**What it does:**
- Controls all traffic entering/leaving a subnet
- Stateless: must explicitly allow both directions
- Default: ALLOW all (but custom ones are restrictive)

**Mental model:**
```
Subnet Entrance
├─ NACL = Security checkpoint
│  ├─ "Everyone check in"
│  ├─ "Inbound: Check document"
│  ├─ "Outbound: Check document again"
│  └─ Doesn't remember who came in
```

**Example rules:**

```bash
# Web server subnet NACL
Inbound:
├─ Rule 100: HTTP (80) from 0.0.0.0/0
├─ Rule 110: HTTPS (443) from 0.0.0.0/0
├─ Rule 120: SSH (22) from 10.0.0.0/16
├─ Rule 130: Ephemeral (1024-65535) from 0.0.0.0/0
└─ Rule 32767: Deny all else (implicit)

Outbound:
├─ Rule 100: All traffic to 0.0.0.0/0
└─ Rule 32767: Deny all else (implicit)
```

**Why ephemeral ports?** Server responses come back on random high ports (1024-65535).

---

### How They Work Together

```
Request enters subnet:

1. NACL checkpoint
   ├─ Check inbound rules
   └─ "Port 80 allowed?" YES → Pass

2. Security Group
   ├─ Check instance rules
   └─ "Port 80 allowed?" YES → Pass

3. EC2 receives request
   └─ Application processes

4. Response goes out

5. Security Group (automatic)
   └─ "Return traffic? YES" (stateful)

6. NACL checkpoint (again)
   ├─ Check outbound rules
   └─ "Ephemeral port allowed?" YES → Pass

Response leaves successfully!
```

---

## Network Components

### 1. Internet Gateway (IGW)

**Purpose:** Connect VPC to the internet

**How it works:**
```
Translates public IPs ↔ private IPs
├─ Inbound: 203.0.113.45 → 10.0.1.50
└─ Outbound: 10.0.1.50 → 203.0.113.45
```

**Key facts:**
- ✓ Only 1 per VPC
- ✓ Attach to VPC explicitly
- ✓ FREE
- ✓ Highly available (no SPOF)

---

### 2. NAT Gateway (NAT)

**Purpose:** Allow private instances to reach internet (one-way)

**How it works:**
```
Private EC2 → NAT Gateway → IGW → Internet
(10.0.2.50)  (public IP)          (response back)

Internet cannot reach private EC2!
```

**Key facts:**
- ✓ One per AZ recommended
- ✓ Costs ~$32/month + data transfer
- ✓ High availability (single point of failure if only one)
- ✓ Requires Elastic IP

**Comparison: NAT Gateway vs NAT Instance**
```
NAT Gateway (AWS Managed):
├─ ✓ Easier to set up
├─ ✓ Faster (5 Gbps)
├─ ✓ AWS manages it
└─ ✗ Costs money

NAT Instance (Self-Managed):
├─ ✓ Cheaper
├─ ✗ Must manage yourself
├─ ✗ Slower
└─ ✗ Single point of failure
```

---

### 3. Route Tables

**Purpose:** Define traffic routing rules for a subnet

**How it works:**
```
Packet destination: 8.8.8.8

Route table:
├─ 10.0.0.0/16 → Local (internal)
└─ 0.0.0.0/0 → igw-xxxxx (send to IGW)

Decision: "Send to IGW"
```

**Default routes:**
```
10.0.0.0/16 → Local (always present)
```

**Added routes:**
```
0.0.0.0/0 → igw-xxxxx     (Internet traffic)
0.0.0.0/0 → nat-xxxxx     (Via NAT)
10.1.0.0/16 → pcx-xxxxx   (Peering)
192.168.0.0/16 → vpn-xxxx (VPN)
```

---

### 4. VPC Endpoints (Private Endpoints)

**Purpose:** Access AWS services WITHOUT going through the internet

**Mental Model:** Secret tunnels from your VPC directly to AWS services

```
BEFORE VPC Endpoint (risky & expensive):
EC2 (private) → NAT Gateway → IGW → Internet → S3
                  ~$32/month    ✗ Exposed to internet
                  ✗ Slower      ✗ Network hops

AFTER VPC Endpoint (secure & free):
EC2 (private) ──────────────→ S3 (direct tunnel)
                 ✓ FREE        ✓ Private
                 ✓ Fast        ✓ AWS managed
```

**Terminology Note:**
- "VPC Endpoint" = "Private Endpoint" (same thing)
- Both terms refer to private connections to AWS services
- The term "Private Endpoint" is just a more descriptive name

---

#### Gateway Endpoints (FREE)

**What it is:** A route table entry that redirects traffic to AWS services

**Services:** S3, DynamoDB

**How it works:**
```
When EC2 tries to reach S3:
1. Route table sees: destination = S3
2. Route table rule: S3 → Gateway Endpoint
3. Traffic goes directly to S3 (no internet)
4. Returns through same private tunnel
```

**Route table looks like:**
```
Destination              Target
10.0.0.0/16         →   Local
0.0.0.0/0           →   igw-xxxxx (internet)
pl-1234567890abcdef →   vpce-1234567 (S3 endpoint)
```

**Characteristics:**
| Feature | Detail |
|---------|--------|
| **Cost** | FREE |
| **Setup** | Easy (2 clicks in console) |
| **Services** | Only S3, DynamoDB |
| **Performance** | Fast (same region) |
| **Security** | Private (no internet exposure) |
| **Availability** | High (AWS managed) |

**When to use:**
- ✓ Private EC2 accessing S3 (common!)
- ✓ Lambda accessing DynamoDB
- ✓ Cost optimization (no NAT charges)
- ✓ Security (avoid internet exposure)

**Example: S3 Gateway Endpoint**
```bash
# Create S3 gateway endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-xxxxx

# Now EC2 in private subnet can access S3 directly
# Private EC2 → S3 (direct, free, secure)
```

---

#### Interface Endpoints (VPCE - small cost)

**What it is:** A network interface (ENI) inside your subnet that acts as a proxy

**Services:** 100+ AWS services
- Lambda, SNS, SQS, Kinesis, Athena
- Secrets Manager, Systems Manager, DynamoDB
- RDS, Redshift, AppConfig, and 90+ more

**How it works:**
```
EC2 needs to call Lambda:
1. EC2 talks to interface endpoint (private IP: 10.0.1.50)
2. Interface endpoint has DNS name: vpce-1234567-xxxxxxx.us-east-1.vpce.amazonaws.com
3. Behind the scenes: AWS routes to Lambda service
4. Response comes back through same interface
```

**Characteristics:**
| Feature | Detail |
|---------|--------|
| **Cost** | ~$7/month per endpoint + data processing |
| **Setup** | Moderate (create in console, add security group) |
| **Services** | 100+ AWS services |
| **Performance** | Fast (same region) |
| **Availability** | High (can span multiple AZs) |
| **Location** | Lives in your subnet as ENI |

**Architecture:**
```
Your VPC:
┌──────────────────────────────────┐
│  Private Subnet (10.0.2.0/24)    │
│                                  │
│  EC2 Instance (10.0.2.10)        │
│      ↓                           │
│  Interface Endpoint ENI          │
│  (10.0.2.20) - vpce-xxxxx        │
│      ↓ (private tunnel)          │
│  AWS Service (Lambda, SNS, etc)  │
└──────────────────────────────────┘
      No internet access needed!
```

**When to use:**
- ✓ Private EC2 calling Lambda functions
- ✓ Lambda calling SNS/SQS
- ✓ EC2 accessing Secrets Manager (passwords, API keys)
- ✓ RDS proxy for database connections
- ✓ Any AWS service NOT in gateway endpoints

**Example: SNS Interface Endpoint**
```bash
# Create SNS interface endpoint
aws ec2 create-vpc-endpoint \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.sns \
  --subnet-ids subnet-xxxxx \
  --security-group-ids sg-xxxxx

# Now get the endpoint DNS name
# Use in code: sns://vpce-1234567-xxxxxxx.us-east-1.vpce.amazonaws.com
```

---

#### Decision Matrix: Gateway vs Interface

| Need | Gateway | Interface |
|------|---------|-----------|
| **Access S3** | ✓ Best choice | ❌ Overkill |
| **Access DynamoDB** | ✓ Best choice | ❌ Overkill |
| **Access Lambda** | ❌ Not available | ✓ Required |
| **Access SNS/SQS** | ❌ Not available | ✓ Required |
| **Cost sensitive** | ✓ FREE | ❌ $7/month |
| **Just learning** | ✓ Start here | - |

---

#### Common Architecture: S3 + Lambda (Private)

```
Scenario: Private Lambda needs to read S3 files

VPC Setup:
┌────────────────────────────────────┐
│  Private Subnet                    │
│                                    │
│  Lambda Function                   │
│    ↓ (need to read S3)            │
│    └─→ S3 Gateway Endpoint        │
│         (FREE, direct access)      │
│                                    │
│  (NO NAT Gateway needed!)          │
└────────────────────────────────────┘

Cost Savings:
- Without endpoint: ~$32/month NAT + data costs
- With endpoint: FREE
- Savings: 100%
```

---

#### Endpoint Policies: Control Access

VPC endpoints can have policies to restrict which services/resources are accessible:

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-xxxxxxxxxx"
        }
      }
    }
  ]
}
```

**Meaning:** Only allow GetObject from S3, and only from your AWS Organization

---

#### Troubleshooting VPC Endpoints

**Issue: "Service not reachable through endpoint"**
```
✓ Check security group on interface endpoint
✓ Check endpoint policy (allows your action?)
✓ Check route table (routes to endpoint?)
✓ Check network ACLs (allow port 443?)
✓ Check DNS resolution (is it resolving?)
```

**Issue: "Still charges NAT Gateway fees"**
```
Reason: Old route still going to NAT
Solution: Update route table to use endpoint instead
```

**Test connectivity:**
```bash
# From EC2 in private subnet
# Check if you can reach S3 through endpoint
aws s3 ls s3://my-bucket/ \
  --endpoint-url https://vpce-1234567.s3.us-east-1.vpce.amazonaws.com
```

---

#### Service-Specific VPC Endpoint Guide

**When to use VPC Endpoints with different AWS services:**

##### 🪣 **S3 (Simple Storage Service)**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 uploading files | ✅ Use Gateway Endpoint (FREE) | ❌ NAT → IGW → S3 (~$32/month) |
| Lambda reading from S3 | ✅ Use Gateway Endpoint (FREE) | ❌ Uses NAT (costs) |
| Public EC2 accessing S3 | ❓ Optional (direct access already) | ✓ Works fine |
| ECS/Fargate pulling images | ✅ Use Gateway Endpoint (FREE) | ❌ Costs, slower |

**Decision:** Private workloads = **Gateway Endpoint (FREE)**

**Example: Private EC2 → S3**
```bash
# 1. Create S3 Gateway Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-xxxxx

# 2. Private EC2 can now access S3 directly (no NAT needed!)
# No code changes required - works automatically
aws s3 ls s3://my-bucket/

# Cost: $0/month (vs $32+/month with NAT)
```

---

##### ⚡ **Lambda**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Lambda in private subnet calling S3 | ✅ S3 Gateway Endpoint (FREE) | ❌ NAT → IGW → S3 |
| Lambda calling SNS/SQS | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW → SNS/SQS |
| Lambda accessing RDS in private subnet | ✅ Direct (same VPC) | ✓ Direct access (no internet needed) |
| Lambda in VPC pulling secrets from Secrets Manager | ✅ Interface Endpoint (~$7/month) | ❌ NAT costs |

**Decision:**
- S3 access = **Gateway Endpoint (FREE)**
- Other services = **Interface Endpoint (~$7/month)**

**Example: Private Lambda → S3**
```python
# Lambda in VPC with S3 Gateway Endpoint
import boto3
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # This automatically uses the S3 Gateway Endpoint
    # No internet exposure, no NAT costs
    response = s3.get_object(Bucket='my-bucket', Key='data.json')

    return {
        'statusCode': 200,
        'body': response['Body'].read()
    }

# Cost breakdown:
# - Lambda execution: normal price
# - S3 access: FREE (through endpoint)
# - NAT Gateway: $0 (not needed!)
```

---

##### 📊 **DynamoDB**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 reading/writing to DynamoDB | ✅ Gateway Endpoint (FREE) | ❌ NAT → IGW → DynamoDB |
| Lambda accessing DynamoDB | ✅ Gateway Endpoint (FREE) | ❌ NAT costs if in VPC |
| ECS task querying DynamoDB | ✅ Gateway Endpoint (FREE) | ❌ NAT → IGW |
| Public app → DynamoDB | ✓ Direct access (no VPC needed) | ✓ Works fine |

**Decision:** Private workloads = **Gateway Endpoint (FREE)**

**Example: Private EC2 → DynamoDB**
```python
import boto3

# Creates DynamoDB Gateway Endpoint
# No code changes needed - works transparently
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Users')

# This automatically uses the endpoint
response = table.get_item(Key={'UserID': '123'})

# Cost: $0/month for endpoint access
# (DynamoDB reads/writes charged normally)
```

---

##### 📢 **SNS (Simple Notification Service)**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 publishing to SNS | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW → SNS (~$32/month) |
| Lambda in VPC → SNS | ✅ Interface Endpoint (~$7/month) | ❌ NAT costs |
| ECS task sending SNS notifications | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW |
| Public API → SNS | ✓ Direct (no VPC) | ✓ Works fine |

**Decision:** Private workloads = **Interface Endpoint (~$7/month)**

**Example: Private Lambda → SNS**
```python
import boto3

# With SNS Interface Endpoint
sns = boto3.client('sns')

def lambda_handler(event, context):
    # This uses the SNS Interface Endpoint
    # Private connection, no internet exposure
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:123456789:alerts',
        Message='Alert: High CPU usage detected'
    )

    return {'statusCode': 200}

# Cost comparison:
# Without endpoint: ~$32/month NAT + SNS
# With endpoint: ~$7/month endpoint + SNS
# Savings: ~$25/month
```

---

##### 📨 **SQS (Simple Queue Service)**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 writing messages to SQS | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW → SQS |
| Lambda reading from SQS queue | ✅ Interface Endpoint (~$7/month) | ❌ NAT costs |
| ECS workers consuming SQS messages | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW |
| Public web app → SQS | ✓ Direct (no VPC) | ✓ Works fine |

**Decision:** Private workloads = **Interface Endpoint (~$7/month)**

---

##### 🔐 **Secrets Manager**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 retrieving database passwords | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW → Secrets |
| Lambda getting API keys | ✅ Interface Endpoint (~$7/month) | ❌ NAT costs |
| ECS task retrieving Docker credentials | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW |
| Public web app → Secrets Manager | ❌ Not recommended (security) | ❌ Not recommended |

**Decision:** **ALWAYS use Interface Endpoint** for private workloads

**Example: Private EC2 → Secrets Manager**
```python
import boto3
import json

# With Secrets Manager Interface Endpoint
secrets = boto3.client('secretsmanager', region_name='us-east-1')

def get_db_password():
    # Secure retrieval through private endpoint
    response = secrets.get_secret_value(
        SecretId='prod/db/password'
    )

    secret = json.loads(response['SecretString'])
    return secret['password']

# Cost: ~$7/month endpoint + normal Secrets Manager API calls
# Security: Credentials never exposed to internet
```

---

##### 📈 **CloudWatch Logs**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 writing logs | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW → CloudWatch |
| Lambda logging metrics | ✅ Interface Endpoint (~$7/month) | ❌ NAT costs |
| ECS container logs | ✅ Interface Endpoint (~$7/month) | ❌ NAT → IGW |

**Decision:** **Use Interface Endpoint** for consistent logging from private workloads

---

##### 🗄️ **RDS (Relational Database Service)**

| Scenario | With Endpoint | Without Endpoint |
|----------|---------------|------------------|
| Private EC2 → RDS (same VPC) | ✓ Direct (no endpoint needed) | ✓ Direct access |
| Private EC2 → RDS (different VPC) | ✅ VPC Peering OR Interface Endpoint | ❌ NAT → IGW → Internet |
| Lambda in VPC → RDS | ✓ Direct (same VPC) | ✓ Direct access |
| Publicly accessible RDS → Internet | ❌ Don't do this | ❌ Dangerous |

**Decision:** RDS in **same VPC = Direct** (no endpoint needed)

---

#### VPC Endpoint ROI (Return on Investment)

**Cost Comparison: NAT Gateway vs VPC Endpoints**

```
NAT Gateway (for internet access):
├─ Cost: $32/month + data transfer
├─ Supports: Any AWS service + internet
└─ Use case: Private instances need internet

VPC Endpoints (for AWS service access):
├─ Gateway (S3/DynamoDB): FREE
├─ Interface (others): ~$7/month each
└─ Use case: Private → AWS services only

Example Savings:
┌─────────────────────────────────────────┐
│ Scenario: Private Lambda + S3 + SNS     │
├─────────────────────────────────────────┤
│ Without Endpoint:                       │
│  - NAT Gateway: $32/month               │
│  - Typical usage: $50-100/month data    │
│  - Total: $82-132/month                 │
│                                         │
│ With Endpoints:                         │
│  - S3 Gateway Endpoint: $0 (FREE)       │
│  - SNS Interface Endpoint: $7/month     │
│  - Total: $7/month                      │
│                                         │
│ Monthly Savings: $75-125/month          │
│ Annual Savings: $900-1,500/year         │
└─────────────────────────────────────────┘
```

---

#### Quick Decision Tree: Should I Use VPC Endpoint?

```
Does your private workload need AWS service access?
  ├─ YES: Accessing S3 or DynamoDB?
  │   ├─ YES → Use Gateway Endpoint (FREE) ✓
  │   └─ NO → Go to next question
  │
  ├─ Accessing SNS, SQS, Lambda, Secrets Manager, CloudWatch?
  │   ├─ YES → Use Interface Endpoint (~$7/month) ✓
  │   └─ NO → Go to next question
  │
  ├─ Accessing RDS (same VPC)?
  │   ├─ YES → Use Direct Connection (FREE) ✓
  │   └─ NO → Use VPC Peering or Interface Endpoint
  │
  └─ Needs internet access beyond AWS?
      ├─ YES → Keep NAT Gateway (necessary)
      └─ NO → Replace with VPC Endpoints (cheaper!)
```

---

## Architecture Patterns

### Pattern 1: Simple Public VPC

```
┌─── Public Subnet ───┐
│                     │
│  EC2 Instance ◄─────┼──── Internet
│  (Public IP)        │
│                     │
└─────────────────────┘
        ▲
        │
   [IGW]
```

**Use:** Learning, testing, simple web servers

**Route table:**
```
0.0.0.0/0 → IGW
```

---

### Pattern 2: Public + Private (Standard)

```
┌───────────────────────┐
│   Public Subnet       │
│                       │
│  Web Server ◄────────┼──── Internet
│  (Public IP)          │
│                       │
└───────────┬───────────┘
            │ [IGW]

┌───────────┼───────────┐
│           │           │
│   Private Subnet      │
│                       │
│  Database EC2         │
│  (No Public IP)       │
│                       │
└───────────────────────┘

Private EC2 can reach:
├─ Web server (same VPC)
└─ Internet (via NAT in public subnet)
```

---

### Pattern 3: Multi-AZ HA

```
us-east-1a:
├─ Public:  10.0.1.0/24 → IGW
├─ Private: 10.0.11.0/24 → NAT

us-east-1b:
├─ Public:  10.0.2.0/24 → IGW
├─ Private: 10.0.12.0/24 → NAT

Load Balancer distributes across AZs
```

**Benefits:**
- ✓ High availability
- ✓ Automatic failover
- ✗ More complex
- ✗ NAT costs × 2

---

## Hands-On Exercises

### Exercise 1: Create a Public VPC

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create public subnet
aws ec2 create-subnet --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

# Create IGW
aws ec2 create-internet-gateway

# Attach IGW
aws ec2 attach-internet-gateway --vpc-id vpc-xxxxx \
  --internet-gateway-id igw-xxxxx

# Create route table
aws ec2 create-route-table --vpc-id vpc-xxxxx

# Add internet route
aws ec2 create-route --route-table-id rtb-xxxxx \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-xxxxx

# Associate route table
aws ec2 associate-route-table --subnet-id subnet-xxxxx \
  --route-table-id rtb-xxxxx
```

---

## Troubleshooting

### Problem: "Cannot reach my EC2"

**Checklist:**
```
1. ✓ Is EC2 in public subnet?
2. ✓ Does subnet have route to IGW?
3. ✓ Does EC2 have public IP?
4. ✓ Does security group allow inbound?
5. ✓ Does NACL allow inbound?
```

### Problem: "Private EC2 cannot reach internet"

**Checklist:**
```
1. ✓ Is NAT Gateway created?
2. ✓ Is route pointing to NAT?
3. ✓ Is NAT in public subnet?
4. ✓ Does security group allow outbound?
5. ✓ Does NACL allow outbound?
```

### Problem: "Two subnets cannot communicate"

**Checklist:**
```
1. ✓ Are they in same VPC?
2. ✓ Do route tables have "Local" route for VPC CIDR?
3. ✓ Do security groups allow traffic?
4. ✓ Do NACLs allow traffic both ways?
```

---

## Key Takeaways

| Concept | Remember |
|---------|----------|
| **VPC** | Your isolated network (10.0.0.0/16) |
| **Subnet** | Part of VPC in ONE AZ (10.0.1.0/24) |
| **Public** | Has route to IGW, can access internet |
| **Private** | Has route to NAT, hidden from internet |
| **Security Group** | Instance-level firewall (stateful) |
| **NACL** | Subnet-level firewall (stateless) |
| **IGW** | Gateway to internet (public only) |
| **NAT** | One-way exit door (private only) |

---

**Last Updated:** 2026-05-28
**Level:** Beginner to Intermediate
