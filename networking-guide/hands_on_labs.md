# AWS Networking - Hands-On Labs

**Step-by-step learning exercises for AWS networking concepts**

---

## Lab Setup

### Prerequisites
- AWS Account with free tier access
- AWS Management Console access
- Basic understanding of networking concepts
- About 2-3 hours for all labs

### Important Notes
- All labs use AWS Free Tier eligible resources
- Clean up resources after each lab to avoid charges
- Estimated cost: $0 (if using free tier)

---

## Lab 1: Create Your First VPC

**Time**: 15 minutes
**Objective**: Create a VPC with public and private subnets

### Step 1.1: Create VPC

1. Go to AWS Console → VPC → VPCs
2. Click "Create VPC"
3. Fill in:
   - Name: `learning-vpc`
   - IPv4 CIDR: `10.0.0.0/16`
   - IPv6 CIDR: Leave empty
   - Tenancy: Default
4. Click "Create VPC"

**Verification**:
```bash
aws ec2 describe-vpcs --filters Name=tag:Name,Values=learning-vpc
# Should show CIDR: 10.0.0.0/16
```

### Step 1.2: Create Public Subnet

1. VPC → Subnets → Create subnet
2. Fill in:
   - VPC: `learning-vpc`
   - Subnet name: `public-subnet-1a`
   - Availability Zone: `us-east-1a`
   - IPv4 CIDR: `10.0.1.0/24`
3. Click "Create subnet"

**Repeat** for second public subnet:
- Name: `public-subnet-1b`
- AZ: `us-east-1b`
- CIDR: `10.0.2.0/24`

### Step 1.3: Create Private Subnet

1. Create subnet:
   - Name: `private-subnet-1a`
   - AZ: `us-east-1a`
   - CIDR: `10.0.11.0/24`

2. Create another:
   - Name: `private-subnet-1b`
   - AZ: `us-east-1b`
   - CIDR: `10.0.12.0/24`

**Verification**:
```bash
aws ec2 describe-subnets --filters Name=vpc-id,Values=vpc-xxxxx
# Should show 4 subnets with correct CIDR blocks
```

### Step 1.4: Create Internet Gateway

1. VPC → Internet Gateways → Create Internet Gateway
2. Name: `learning-igw`
3. Click "Create"
4. Attach to VPC:
   - Select the IGW
   - Attachment → Attach to VPC
   - Choose `learning-vpc`
   - Click "Attach"

**Verification**:
```bash
aws ec2 describe-internet-gateways --filters Name=tag:Name,Values=learning-igw
# Should show AttachmentSet with VpcId
```

### Step 1.5: Create Route Tables

1. VPC → Route Tables → Create route table
   - Name: `public-routes`
   - VPC: `learning-vpc`
   - Create

2. Add route:
   - Select the route table
   - Routes tab → Edit routes
   - Add route:
     - Destination: `0.0.0.0/0`
     - Target: Internet Gateway → `learning-igw`
   - Save

3. Associate subnets:
   - Subnet associations → Edit subnet associations
   - Select `public-subnet-1a` and `public-subnet-1b`
   - Save

4. Create private route table:
   - Name: `private-routes`
   - VPC: `learning-vpc`
   - Create
   - Associate with `private-subnet-1a` and `private-subnet-1b`

**Verification**:
```bash
aws ec2 describe-route-tables --filters Name=vpc-id,Values=vpc-xxxxx
# Should see two route tables with different routes
```

### Lab 1 Complete!

You now have:
- ✓ VPC with 10.0.0.0/16 CIDR
- ✓ 2 Public subnets (10.0.1.0/24, 10.0.2.0/24)
- ✓ 2 Private subnets (10.0.11.0/24, 10.0.12.0/24)
- ✓ Internet Gateway attached
- ✓ Route tables configured

---

## Lab 2: Launch EC2 Instances

**Time**: 20 minutes
**Objective**: Launch EC2 instances in public and private subnets

### Step 2.1: Create Security Group for Web Server

1. VPC → Security Groups → Create security group
2. Fill in:
   - Name: `web-server-sg`
   - Description: `Security group for web servers`
   - VPC: `learning-vpc`

3. Add inbound rules:
   - HTTP (80) from 0.0.0.0/0
   - HTTPS (443) from 0.0.0.0/0
   - SSH (22) from your IP (or 0.0.0.0/0 for testing)

4. Outbound rules:
   - Leave default (allow all)

5. Create

### Step 2.2: Launch Public EC2 Instance

1. EC2 → Instances → Launch instances
2. Fill in:
   - Name: `web-server-1`
   - OS: Amazon Linux 2 (free tier eligible)
   - Instance type: t2.micro (free tier)
   - Key pair: Create or select existing
   - VPC: `learning-vpc`
   - Subnet: `public-subnet-1a`
   - Auto-assign public IP: Enable
   - Security group: `web-server-sg`

3. Launch

### Step 2.3: Launch Private EC2 Instance

1. Launch another instance:
   - Name: `app-server-1`
   - OS: Amazon Linux 2
   - Instance type: t2.micro
   - VPC: `learning-vpc`
   - Subnet: `private-subnet-1a`
   - Auto-assign public IP: Disable (important!)
   - Create new security group: `app-server-sg`
     - Allow SSH (22) from `web-server-sg`
     - Allow port 8080 from `web-server-sg`

2. Launch

### Step 2.4: Verify Connectivity

Test from web server:

```bash
# SSH into web server
ssh -i your-key.pem ec2-user@<web-server-public-ip>

# From web server, SSH to app server (private)
ssh -i your-key.pem ec2-user@10.0.11.<private-ip>

# If successful, you can ping the private instance:
ping 10.0.11.<ip>
```

Expected results:
- ✓ Can SSH to public EC2 from internet
- ✓ Can't SSH to private EC2 from internet
- ✓ Can SSH to private EC2 from public EC2

### Lab 2 Complete!

You now have:
- ✓ Security groups with appropriate rules
- ✓ Public EC2 instance (accessible from internet)
- ✓ Private EC2 instance (not accessible from internet)
- ✓ Network connectivity between instances

---

## Lab 3: Explore Network ACLs

**Time**: 15 minutes
**Objective**: Understand and modify Network ACLs

### Step 3.1: View Default NACL

1. VPC → Network ACLs
2. Select the NACL for `learning-vpc`
3. View inbound/outbound rules
4. Notice: Default allows all traffic

### Step 3.2: Create Restrictive NACL

1. Create network ACL:
   - Name: `restrictive-nacl`
   - VPC: `learning-vpc`
   - Create

2. Add inbound rules:
   - Rule 100: HTTP (80) from 0.0.0.0/0 → ALLOW
   - Rule 110: HTTPS (443) from 0.0.0.0/0 → ALLOW
   - Rule 120: SSH (22) from 10.0.0.0/8 → ALLOW
   - Rule 130: Ephemeral ports (1024-65535) from 0.0.0.0/0 → ALLOW
   - Rule * (default): All traffic → DENY

3. Add outbound rules:
   - Rule 100: All traffic to 0.0.0.0/0 → ALLOW

### Step 3.3: Associate NACL

1. Select `restrictive-nacl`
2. Association → Edit
3. Associate with `public-subnet-1a`
4. Save

### Step 3.4: Test Connectivity

```bash
# From web server on public-subnet-1a, try:
ping 8.8.8.8

# Should work (rule 130 allows ephemeral responses)
# Try accessing web:
curl http://google.com

# Should work (rule 100 allows HTTP)
```

### Lab 3 Complete!

You now understand:
- ✓ How NACLs work
- ✓ Rule ordering and processing
- ✓ Ephemeral ports and responses
- ✓ Default vs custom NACLs

---

## Lab 4: Configure Private Subnets for Internet Access

**Time**: 15 minutes
**Objective**: Set up NAT Gateway and VPC Endpoints

### Step 4.1: Create NAT Gateway

1. VPC → NAT Gateways → Create NAT Gateway
2. Fill in:
   - Subnet: `public-subnet-1a`
   - Elastic IP: Allocate Elastic IP
   - Create

**Wait** for NAT to be available (about 1 minute)

### Step 4.2: Update Private Route Table

1. VPC → Route Tables
2. Select `private-routes`
3. Edit routes:
   - Add route:
     - Destination: `0.0.0.0/0`
     - Target: NAT Gateway → (select your NAT)
   - Save

### Step 4.3: Test Private EC2 Internet Access

```bash
# SSH into public EC2
ssh -i key.pem ec2-user@<public-ip>

# From public, SSH to private EC2
ssh -i key.pem ec2-user@10.0.11.<ip>

# From private EC2, test internet access:
ping 8.8.8.8
# Should work now!

curl http://google.com
# Should work!

# Download package
sudo yum update
# Should work!
```

### Step 4.4: Create VPC Endpoint for S3 (Free!)

1. VPC → Endpoints → Create endpoint
2. Fill in:
   - Service category: AWS services
   - Service name: S3 (us-east-1)
   - VPC: `learning-vpc`
   - Route tables: Select `private-routes`
   - Policy: Full access (for testing)

3. Create

### Step 4.5: Test S3 Access from Private EC2

```bash
# From private EC2:
aws s3 ls

# If you have buckets, should see them
# If not, should see empty list (no error)

# This uses VPC Endpoint (not NAT Gateway!)
# Free and more secure!
```

### Lab 4 Complete!

You now have:
- ✓ NAT Gateway for general internet access
- ✓ VPC Endpoint for S3 (free!)
- ✓ Private EC2 can access internet
- ✓ Private EC2 can access AWS services

---

## Lab 5: Security Group Chaining

**Time**: 10 minutes
**Objective**: Reference security groups in rules

### Step 5.1: Create Database Security Group

1. VPC → Security Groups → Create
2. Fill in:
   - Name: `database-sg`
   - VPC: `learning-vpc`

3. Inbound rules:
   - MySQL (3306) from `app-server-sg`

### Step 5.2: Modify App Server SG

1. Select `app-server-sg`
2. Add outbound rule:
   - MySQL (3306) to `database-sg`

### Step 5.3: Verify

From app server, you can now reach any database with `database-sg`:

```bash
# Security group references work like:
# app-server-sg can talk to database-sg
# but only on port 3306
```

This demonstrates:
- ✓ Security group referencing
- ✓ Fine-grained access control
- ✓ Logical grouping of rules

---

## Lab 6: Clean Up

**IMPORTANT**: Avoid unexpected charges by deleting resources!

### Cleanup Checklist

1. **Delete EC2 Instances**
   - EC2 → Instances → Select → Instance State → Terminate

2. **Delete NAT Gateway**
   - VPC → NAT Gateways → Select → Delete

3. **Release Elastic IP**
   - VPC → Elastic IPs → Release address

4. **Delete VPC Endpoints**
   - VPC → Endpoints → Select → Delete

5. **Delete VPC** (automatically deletes subnets/route tables)
   - VPC → Your VPCs → Select → Delete

6. **Delete Security Groups**
   - VPC → Security Groups → Select → Delete

7. **Detach Internet Gateway**
   - VPC → Internet Gateways → Detach from VPC

8. **Delete Internet Gateway**
   - VPC → Internet Gateways → Delete

**Verification**:
```bash
# Check no resources remain
aws ec2 describe-vpcs --filters Name=tag:Name,Values=learning-vpc
# Should return empty

aws ec2 describe-instances
# Should not show your instances

# Delete key pair (optional)
aws ec2 delete-key-pair --key-name your-key-name
```

---

## Lab 7: Advanced - Multi-AZ High Availability

**Time**: 30 minutes
**Objective**: Build a highly available application

### Architecture

```
Public Subnets (ALB)
├─ 10.0.1.0/24 (us-east-1a)
└─ 10.0.2.0/24 (us-east-1b)

Private Subnets (App Servers)
├─ 10.0.11.0/24 (us-east-1a)
└─ 10.0.12.0/24 (us-east-1b)

DB Subnets (RDS)
├─ 10.0.21.0/24 (us-east-1a)
└─ 10.0.22.0/24 (us-east-1b)
```

### Step 7.1-7.5: Repeat VPC Setup

Repeat Labs 1-2 but with:
- Multiple availability zones
- Multiple EC2 instances

### Step 7.6: Create Load Balancer

1. EC2 → Load Balancers → Create Application Load Balancer
2. Fill in:
   - Name: `learning-alb`
   - Scheme: Internet-facing
   - Subnets: Select both public subnets

3. Security group: Create or select `alb-sg`
   - Allow HTTP (80) from 0.0.0.0/0

4. Target group:
   - Protocol: HTTP
   - Targets: Add EC2 instances

5. Create

### Step 7.7: Test Load Balancer

```bash
# Get ALB DNS name
curl <alb-dns-name>

# Should route to one of the target EC2 instances
# If you terminate one instance, traffic routes to the other
```

### Lab 7 Complete!

You now have:
- ✓ Multi-AZ application setup
- ✓ Load balancer distributing traffic
- ✓ High availability (survives AZ failure)
- ✓ Understanding of real-world architectures

---

## Common Lab Issues & Solutions

### Issue 1: Can't SSH to EC2

**Solutions**:
1. Check security group allows SSH (22)
2. Check EC2 has public IP (if public subnet)
3. Check your IP in SSH rule (0.0.0.0/0 for testing)
4. Check key permissions: `chmod 400 key.pem`
5. Check EC2 is running and initialized

### Issue 2: Private EC2 Can't Reach Internet

**Solutions**:
1. Check NAT Gateway exists and is available
2. Check private route table has 0.0.0.0/0 → NAT
3. Check outbound security group rules
4. Check NACL allows traffic out
5. Check NAT Gateway is in public subnet

### Issue 3: VPC Endpoint Not Working

**Solutions**:
1. Check endpoint service name is correct (s3.region, not s3)
2. Check route table associated with endpoint
3. For gateway endpoints: route table should have route
4. For interface endpoints: security group should allow 443
5. Test: `aws s3 ls` should work without errors

### Issue 4: Charges Higher Than Expected

**Solutions**:
1. NAT Gateway costs $0.045/hour + data
2. Delete NAT Gateway if not needed
3. Use VPC Endpoints instead (cheaper)
4. Elastic IPs cost if not attached
5. Clean up resources immediately after labs

---

## Lab Exercises Summary

| Lab | Topic | Time | Difficulty |
|-----|-------|------|-----------|
| 1 | VPC Creation | 15 min | Easy |
| 2 | EC2 Instances | 20 min | Easy |
| 3 | Network ACLs | 15 min | Medium |
| 4 | NAT & Endpoints | 15 min | Medium |
| 5 | SG Chaining | 10 min | Medium |
| 6 | Cleanup | 10 min | Easy |
| 7 | HA Setup | 30 min | Hard |

**Total Time**: 2-3 hours

---

## Next Steps After Labs

### Level 2: Advanced Networking
1. VPC Peering
2. Transit Gateway
3. AWS PrivateLink
4. VPN Connections
5. Direct Connect

### Level 3: Security
1. Security best practices
2. Network segmentation
3. DDoS protection
4. Firewall deployment
5. Zero-trust architecture

### Level 4: Operations
1. Network monitoring
2. VPC Flow Logs
3. CloudWatch metrics
4. AWS Config
5. Network ACL logging

---

## Useful Commands Reference

```bash
# List all VPCs
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock]'

# List subnets in VPC
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=vpc-xxxxx \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone]'

# List security groups
aws ec2 describe-security-groups \
  --filters Name=vpc-id,Values=vpc-xxxxx

# List route tables
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-xxxxx

# List NAT gateways
aws ec2 describe-nat-gateways

# Create security group
aws ec2 create-security-group \
  --group-name test-sg \
  --description "Test SG" \
  --vpc-id vpc-xxxxx

# Add ingress rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Delete security group
aws ec2 delete-security-group --group-id sg-xxxxx
```

---

**Happy Learning! These hands-on labs will give you practical AWS networking experience.**

Last Updated: April 3, 2026
AWS Free Tier: All labs use free tier eligible resources
