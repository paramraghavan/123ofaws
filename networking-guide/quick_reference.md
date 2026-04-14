# AWS Networking - Quick Reference Guide

**Fast lookup for AWS networking concepts**

---

## VPC Comparison

```
╔═══════════════════════════════════════════════════════════════════╗
║                          VPC CHECKLIST                            ║
╠═══════════════════════════════════════════════════════════════════╣
║ ✓ Choose CIDR block (usually 10.0.0.0/16 for production)         ║
║ ✓ Create subnets in multiple AZs                                 ║
║ ✓ Attach Internet Gateway                                         ║
║ ✓ Create route tables (public and private)                        ║
║ ✓ Create security groups                                          ║
║ ✓ Create NACLs if restrictive security needed                     ║
║ ✓ Launch resources in appropriate subnets                         ║
║ ✓ Test connectivity                                               ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## Subnet CIDR Calculation

```
Quick Subnet Math:

/24 = 256 addresses
/25 = 128 addresses
/26 = 64 addresses
/27 = 32 addresses
/28 = 16 addresses
/29 = 8 addresses
/30 = 4 addresses

Example: VPC 10.0.0.0/16 (65,536 addresses)

Divide into /24 subnets:
10.0.0.0/24   (10.0.0.0   - 10.0.0.255)
10.0.1.0/24   (10.0.1.0   - 10.0.1.255)
10.0.2.0/24   (10.0.2.0   - 10.0.2.255)
10.0.3.0/24   (10.0.3.0   - 10.0.3.255)
...
10.0.255.0/24 (10.0.255.0 - 10.0.255.255)

This gives you 256 subnets of 256 addresses each!
```

---

## Security Group vs NACL

```
┌────────────────────┬──────────────────┬──────────────────┐
│ Feature            │ Security Group   │ NACL             │
├────────────────────┼──────────────────┼──────────────────┤
│ Scope              │ Instance (ENI)   │ Subnet           │
│ Rules              │ Allow only       │ Allow + Deny     │
│ Stateful           │ YES              │ NO               │
│ Applied Order      │ All rules        │ Rule # order     │
│ Default            │ Deny inbound     │ Allow all        │
│ Performance Impact │ Minimal          │ Minimal          │
│ Change takes       │ Immediate        │ Immediate        │
└────────────────────┴──────────────────┴──────────────────┘
```

---

## Common Port Numbers

```
Service                Protocol    Port
─────────────────────────────────────────
SSH                    TCP         22
RDP (Remote Desktop)   TCP         3389
HTTP                   TCP         80
HTTPS                  TCP         443
MySQL/Aurora           TCP         3306
PostgreSQL/Aurora      TCP         5432
Oracle                 TCP         1521
SQL Server             TCP         1433
MongoDB                TCP         27017
Redis                  TCP         6379
ElastiCache Memcached  TCP         11211
Elasticsearch          TCP         9200
RabbitMQ               TCP         5672
SMTP                   TCP         25
DNS                    UDP         53
NTP                    UDP         123
DHCP                   UDP         67-68
```

---

## Route Table Destinations

```
COMMON ROUTE DESTINATIONS:

0.0.0.0/0
  ├─► Internet (all IPv4)
  └─► Used for: "Route to internet"

10.0.0.0/16
  └─► VPC CIDR (stay within VPC)

10.0.1.0/24
  └─► Specific subnet

pl-12345678
  └─► S3 prefix list (for gateway endpoint)

vpce-1a2b3c4d
  └─► VPC endpoint ID

nat-12345678
  └─► NAT gateway ID

igw-12345678
  └─► Internet gateway ID

tgw-12345678
  └─► Transit gateway ID
```

---

## Public Subnet Checklist

```
Public Subnet Requirements:

☑ VPC has Internet Gateway
☑ Subnet route table has route:
   Destination: 0.0.0.0/0
   Target: Internet Gateway (igw-xxx)
☑ EC2 instance has public IP or Elastic IP
☑ Security Group allows inbound traffic
☑ NACL allows inbound traffic
☑ EC2 OS firewall allows traffic

If any step missing → Not publicly accessible!
```

---

## Private Subnet Checklist

```
Private Subnet for Outbound Internet:

☑ VPC has NAT Gateway (in public subnet)
☑ Subnet route table has route:
   Destination: 0.0.0.0/0
   Target: NAT Gateway (nat-xxx)
☑ EC2 instance doesn't need public IP
☑ Security Group allows outbound

For AWS Services (No Internet):

☑ Use VPC Endpoint (S3, DynamoDB, others)
☑ Endpoint policy allows service access
☑ Route table updated for gateway endpoints
✓ Saves cost (no NAT gateway charges)
```

---

## VPC Endpoint Quick Start

```
Gateway Endpoints (FREE):
✓ S3
✓ DynamoDB

Interface Endpoints (Paid, ~$7/month):
✓ EC2
✓ Lambda
✓ SNS, SQS, Kinesis
✓ Athena
✓ CloudWatch
✓ CodeBuild
✓ and many more...

Setup Steps:
1. Go to VPC → Endpoints
2. Create endpoint
3. Choose service
4. Select VPC and subnets
5. Select route tables (for gateway type)
6. Select security group (for interface type)
7. Create

Testing from EC2:
aws s3 ls                    (S3 endpoint)
aws sns list-topics          (SNS endpoint)
aws lambda list-functions    (Lambda endpoint)
```

---

## Internet Gateway vs NAT Gateway

```
INTERNET GATEWAY (IGW):
┌──────────────────────────────────────┐
│ Allows bi-directional communication  │
│ EC2 <──────────► Internet            │
│                                      │
│ Cost: FREE                           │
│ Use for: Public subnets              │
│ Setup: Attach to VPC + add route     │
└──────────────────────────────────────┘


NAT GATEWAY:
┌──────────────────────────────────────┐
│ Allows private EC2 outbound only     │
│ EC2 ──────►  Internet (one-way)      │
│              ◄────── (response)      │
│                                      │
│ Cost: $0.045/hour + data transfer    │
│ Use for: Private subnets outbound    │
│ Setup: Create in PUBLIC subnet       │
│        Add route in PRIVATE table    │
└──────────────────────────────────────┘


When to use what:
Private subnet needs internet? → NAT Gateway
Private subnet needs AWS service? → VPC Endpoint
Don't need either? → Neither (save cost!)
```

---

## Common Architectures

### Web Server (Public)

```
SG Rules:
✓ Allow HTTP (80) from 0.0.0.0/0
✓ Allow HTTPS (443) from 0.0.0.0/0
✓ Allow SSH (22) from your IP
✗ Block everything else

NACL Rules:
✓ Allow HTTP/HTTPS inbound
✓ Allow ephemeral ports (1024-65535) for responses
✗ Block everything else

Route Table:
Destination: 0.0.0.0/0 → Internet Gateway
```

### App Server (Private)

```
SG Rules:
✓ Allow APP_PORT from LOAD_BALANCER_SG
✓ Allow SSH (22) from BASTION_SG
✗ Block HTTP/HTTPS from internet

NACL Rules:
✓ Allow APP_PORT from load balancer subnet
✓ Allow SSH from bastion subnet
✓ Allow ephemeral ports outbound
✗ Block internet directly

Route Table:
Destination: 0.0.0.0/0 → NAT Gateway OR VPC Endpoint
(depending on needs)
```

### Database (Private, Locked Down)

```
SG Rules:
✓ Allow MySQL (3306) from APP_SERVER_SG ONLY
✓ SSH (22) from ADMIN_SG ONLY
✗ Nothing from internet

NACL Rules:
✓ Allow 3306 from app server subnet
✓ Allow 22 from admin subnet
✓ Allow ephemeral responses
✗ Block everything else

Route Table:
Destination: No 0.0.0.0/0 route at all!
(Database never needs internet)
```

---

## Troubleshooting Steps

```
EC2 CAN'T REACH INTERNET:

1. Check EC2 public IP
   aws ec2 describe-instances --query 'Reservations[0].Instances[0]'
   Look for: PublicIpAddress

2. Check route table
   aws ec2 describe-route-tables --query 'RouteTables[0]'
   Should have: 0.0.0.0/0 → igw-xxx

3. Check security group
   aws ec2 describe-security-groups --group-ids sg-xxx
   Should have: Port 80/443 allowed inbound

4. Check NACL
   aws ec2 describe-network-acls --query 'NetworkAcls[0]'
   Should have: Port 80/443 allowed inbound
   Should have: Ephemeral (1024-65535) allowed inbound

5. Check IGW attached
   aws ec2 describe-internet-gateways
   Should show: AttachmentSet with VpcId


EC2 CAN REACH INTERNET BUT SLOW:

Check if using NAT Gateway:
aws ec2 describe-route-tables --query 'RouteTables[0].Routes'
Look for: nat-xxx

NAT Gateway performance depends on:
- Instance size (larger = better bandwidth)
- Available bandwidth (shared resource)
- Data transfer size

Solution: Use VPC Endpoint instead!
(Better performance, lower cost)


EC2 IN PRIVATE SUBNET CAN'T ACCESS S3:

Option 1: Check NAT Gateway
aws ec2 describe-nat-gateways
Should show: State: available

Option 2: Better - Use VPC Endpoint
aws ec2 describe-vpc-endpoints
Should show: S3 endpoint

Set up S3 endpoint:
1. Go to VPC → Endpoints
2. Create endpoint for S3
3. Select VPC and route tables
4. Create
5. Test: aws s3 ls
```

---

## Cost Optimization

```
╔══════════════════════════════════════════════════════╗
║ SAVE MONEY ON AWS NETWORKING                        ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║ 1. Use VPC Endpoints instead of NAT Gateway         ║
║    NAT: $0.045/hour + $0.045/GB processed           ║
║    Endpoint: $7.20/month flat                       ║
║    Saves: ~$32/month for light usage                ║
║                                                      ║
║ 2. Use Gateway Endpoints for S3/DDB                 ║
║    Gateway endpoints are FREE                       ║
║    Interface endpoints cost $7.20/month             ║
║    Use Gateway whenever possible                    ║
║                                                      ║
║ 3. Consolidate NACLs                                ║
║    Don't create unnecessary NACLs                   ║
║    Default NACL + Security Groups = usually enough  ║
║                                                      ║
║ 4. Use one NAT Gateway if possible                  ║
║    One per AZ is standard HA                        ║
║    But evaluate if you really need HA               ║
║                                                      ║
║ 5. Monitor data transfer                            ║
║    NAT outbound: $0.045/GB                          ║
║    CloudFront: Much cheaper for static content      ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```

---

## AWS CLI Commands Reference

```
# List all VPCs
aws ec2 describe-vpcs

# Get VPC details
aws ec2 describe-vpcs --vpc-ids vpc-xxxxx

# List subnets
aws ec2 describe-subnets --filters Name=vpc-id,Values=vpc-xxxxx

# Get subnet details
aws ec2 describe-subnets --subnet-ids subnet-xxxxx

# List security groups
aws ec2 describe-security-groups --filters Name=vpc-id,Values=vpc-xxxxx

# Get security group details
aws ec2 describe-security-groups --group-ids sg-xxxxx

# List NACLs
aws ec2 describe-network-acls --filters Name=vpc-id,Values=vpc-xxxxx

# List route tables
aws ec2 describe-route-tables --filters Name=vpc-id,Values=vpc-xxxxx

# List internet gateways
aws ec2 describe-internet-gateways --filters Name=vpc-id,Values=vpc-xxxxx

# List NAT gateways
aws ec2 describe-nat-gateways

# List VPC endpoints
aws ec2 describe-vpc-endpoints

# List VPC Flow Logs (debugging)
aws ec2 describe-flow-logs

# Create flow logs for troubleshooting
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs

# Test connectivity (from EC2)
ping 8.8.8.8                    # Test internet
tracert google.com              # Windows
traceroute google.com           # Linux
aws s3 ls                       # Test S3 access
```

---

## Common Mistakes to Avoid

```
❌ MISTAKE 1: Overlapping subnets
   10.0.1.0/24 and 10.0.1.0/24 (same range)
   ✓ Fix: Use non-overlapping ranges
   ✓ Use: 10.0.1.0/24 and 10.0.2.0/24

❌ MISTAKE 2: No route to internet
   Subnet in public subnet but no IGW route
   ✓ Fix: Add route 0.0.0.0/0 → IGW

❌ MISTAKE 3: SG rule too broad
   Allow 0.0.0.0/0 on port 3306 (MySQL)
   ✓ Fix: Allow only from app server SG

❌ MISTAKE 4: NACL blocking responses
   Allow HTTP inbound (80) but not ephemeral (1024-65535)
   ✓ Fix: Allow 1024-65535 for responses

❌ MISTAKE 5: Database accessible from internet
   DB SG allows 0.0.0.0/0 inbound
   ✓ Fix: Allow only from app server SG
   ✓ Place DB in private subnet

❌ MISTAKE 6: NAT gateway in wrong subnet
   NAT gateway must be in PUBLIC subnet
   ✓ Fix: Move to public subnet

❌ MISTAKE 7: No HA for NAT gateway
   Single NAT = single point of failure
   ✓ Fix: One NAT per AZ for failover

❌ MISTAKE 8: Ignoring NACL completely
   NACL allows all, thinking SG is enough
   ✓ Do: Use both for defense in depth
```

---

## Quick Lookup: AWS Services and Endpoints

```
SERVICE NAME                 INTERFACE?  GATEWAY?
─────────────────────────────────────────────────
EC2                          Yes         No
ECS                          Yes         No
Lambda                       Yes         No
RDS                          Yes         No
ElastiCache                  Yes         No
DynamoDB                     Yes         Yes ✓
S3                           Yes         Yes ✓
Kinesis                      Yes         No
SQS                          Yes         No
SNS                          Yes         No
CloudWatch                   Yes         No
CloudWatch Logs              Yes         No
CloudTrail                   Yes         No
Secrets Manager              Yes         No
Systems Manager              Yes         No
CodeBuild                    Yes         No
CodePipeline                 Yes         No
Athena                       Yes         No
EventBridge                  Yes         No
API Gateway                  Yes         No
Glue                         Yes         No
Marketplace                  Yes         No

✓ = Gateway endpoint (FREE!)
Yes = Interface endpoint (Paid, ~$7/month)
```

---

## Memory Aid: The 3 Security Layers

```
LAYER 1: VPC
         What network am I in?
         IP range: 10.0.0.0/16

LAYER 2: NACL
         What subnet am I in?
         Can this packet enter the subnet?

LAYER 3: Security Group
         What instance am I on?
         Can this traffic reach the instance?

        All 3 must allow traffic for connection!

     Request
       ↓
    [VPC allowed?]
       ↓
    [NACL allowed?]
       ↓
    [SG allowed?]
       ↓
    Connected! ✓
```

---

**Print this guide and keep it handy!**

Last Updated: April 3, 2026
AWS Region: All regions apply (examples: us-east-1)
