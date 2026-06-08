# VPC (Virtual Private Cloud): Beginner to Advanced

> **Your Own Isolated Network in AWS**: Learn to design and manage your private cloud infrastructure. This guide takes you from complete beginner to building production-grade architectures.

---

## Table of Contents

1. [What is VPC? (Start Here)](#what-is-vpc-start-here)
2. [Core Concepts You Need](#core-concepts-you-need)
3. [Creating Your First VPC](#creating-your-first-vpc)
4. [Subnets: Public vs Private](#subnets-public-vs-private)
5. [Network Traffic Flow](#network-traffic-flow)
6. [Security: Groups & NACLs](#security-groups--nacls)
7. [Common Architectures](#common-architectures)
8. [Advanced Scenarios](#advanced-scenarios)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## What is VPC? (Start Here)

### The Building Analogy (Sticks in Your Mind!)

**Without VPC:**
```
AWS Account = Shared building (dangerous!)
└─ Everyone's data in same building
└─ Other customers' code running nearby
└─ Security nightmare
```

**With VPC:**
```
AWS Account = Secure compound (your own property)
  └─ VPC = Your building within the compound
     └─ Subnets = Rooms in your building
     └─ NACL = Security checkpoint at each room entrance (subnet-level)
     └─ Security Groups = Door locks on each room (instance-level)
     └─ Internet Gateway = Entrance to the compound from outside
     └─ NAT Gateway = One-way exit door (private rooms to outside)
```

This is the mental model that makes VPC click. Let's break it down:

- **AWS Account** = Your secured property / compound
- **VPC** = Your own building (completely isolated from other buildings)
- **Subnets** = Rooms in your building (each with separate security)
- **Route Table** = Signs directing traffic to right rooms
- **NACL** = Security checkpoint at room entrance (checks all traffic)
- **Security Group** = Lock on individual door (checks per-instance)
- **Internet Gateway** = Front gate to your compound (how internet accesses you)
- **NAT Gateway** = Side door (how you secretly exit to internet without revealing location)

### Simple Explanation

A **VPC (Virtual Private Cloud)** is your own isolated private network within AWS. Think of it like owning a secure compound with your own building inside it.

```
┌─────────────────────────────────────────┐
│      AWS Account (Your Compound)        │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Your VPC (Your Building)        │  │
│  │  (Completely isolated)           │  │
│  │                                  │  │
│  │   ┌─────────────────────────┐   │  │
│  │   │  Internet Gateway       │   │  │
│  │   │ (Front gate/Entrance)   │   │  │
│  │   └────────────┬────────────┘   │  │
│  │                │                │  │
│  │         ↓      ↓      ↓         │  │
│  │  ┌─────────────┐ ┌────────────┐ │  │
│  │  │  Subnet-1   │ │ Subnet-2   │ │  │
│  │  │  (Rooms)    │ │ (Rooms)    │ │  │
│  │  │  Public     │ │ Private    │ │  │
│  │  └─────────────┘ └────────────┘ │  │
│  │                                  │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

**Key idea**: Your VPC is completely isolated from other AWS customers' networks. Only you control what goes in and out. You have full control over your security, routing, and who can access what.

### Why VPC Matters

- ✅ **Private**: Other AWS customers' buildings are completely separate (security checkpoint at compound entrance)
- ✅ **Configurable**: You control IP ranges, routing, security (your rules for your building)
- ✅ **Scalable**: Grows with your application needs (add more rooms/subnets)
- ✅ **Available by default**: Every AWS account gets a default VPC ready to use immediately

---

## Core Concepts You Need

### Regions and Availability Zones

**Region**: A geographic area where AWS has data centers
- Example: `us-east-1` (N. Virginia), `eu-west-1` (Ireland)
- Each region is completely independent

**Availability Zone (AZ)**: A physically separate data center within a region
- Each region has multiple AZs for redundancy
- Example: `us-east-1a`, `us-east-1b`, `us-east-1c`

```
┌─────────────────────────────────────┐
│     AWS Region: us-east-1           │
│                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────┐│
│  │us-east-1a│ │us-east-1b│ │1a,1c ││
│  │ (AZ 1)   │ │ (AZ 2)   │ │(AZ 3)││
│  │          │ │          │ │      ││
│  │ Data     │ │ Data     │ │Data  ││
│  │ Center   │ │ Center   │ │Ctr   ││
│  └──────────┘ └──────────┘ └──────┘│
│                                     │
└─────────────────────────────────────┘
```

**Why this matters**: Deploy across AZs for high availability. If one AZ has issues, your app keeps running.

### IP Addressing (CIDR Blocks)

A **CIDR block** specifies a range of IP addresses:

```
172.31.0.0/16    = 172.31.0.0 to 172.31.255.255 (65,536 IPs)
                    ↑                              ↑
                    Network                        /16 = size
                    (first 16 bits fixed)

172.31.0.0/20    = 172.31.0.0 to 172.31.15.255 (4,096 IPs)
                    (smaller = fewer IPs)

172.31.16.0/20   = 172.31.16.0 to 172.31.31.255 (4,096 IPs)
```

**Common CIDR blocks**:
- `/16` = 65,536 IPs (typical for a VPC)
- `/20` = 4,096 IPs (typical for a subnet)
- `/24` = 256 IPs (typical for a small subnet)

---

## Creating Your First VPC

### The Simplest Possible VPC

A minimal VPC needs:

1. **VPC itself** - Define IP range (e.g., `172.31.0.0/16`)
2. **Subnet** - Define where instances live (e.g., `172.31.0.0/20`)
3. **Internet Gateway** - Gateway to the internet
4. **Route Table** - Rules for routing traffic

```
Step 1: Create VPC
   aws ec2 create-vpc --cidr-block 172.31.0.0/16
   ✓ You now have 65,536 IP addresses to use

Step 2: Create Subnet
   aws ec2 create-subnet --vpc-id vpc-xxxxx \
     --cidr-block 172.31.0.0/20 \
     --availability-zone us-east-1a
   ✓ You now have 4,096 IPs in one AZ

Step 3: Create Internet Gateway
   aws ec2 create-internet-gateway
   ✓ Gateway created

Step 4: Attach Gateway to VPC
   aws ec2 attach-internet-gateway \
     --internet-gateway-id igw-xxxxx --vpc-id vpc-xxxxx
   ✓ VPC now has internet access

Step 5: Create Route Table
   aws ec2 create-route-table --vpc-id vpc-xxxxx
   ✓ Route table created

Step 6: Add Internet Route
   aws ec2 create-route --route-table-id rtb-xxxxx \
     --destination-cidr-block 0.0.0.0/0 \
     --gateway-id igw-xxxxx
   ✓ Route table now directs internet traffic to IGW
```

**Result**: A basic VPC where you can launch EC2 instances and access the internet.

---

## Subnets: Public vs Private

### What is a Subnet?

A **subnet** is a **room in your building** (VPC) with its own IP range and security rules. You split your VPC into subnets to:
- Deploy instances in different AZs (different rooms on different floors for redundancy)
- Separate web servers from databases (web room vs database room)
- Control which instances touch the internet (some rooms face the street, others are hidden)

**Analogy**:
- VPC = Your building
- Subnets = Rooms in your building
- Each subnet has its own security checkpoint (NACL) and room locks (Security Groups)

### Public Subnet (Internet-Facing)

A subnet where instances **can reach the internet AND the internet can reach them**.

**Building analogy**: It's like a **room that faces the street**. Anyone walking by (internet users) can see the window and knock on the door. Your web servers sit in this room to greet visitors.

**What makes it public?**
1. Route table has a route to Internet Gateway for `0.0.0.0/0` (doors/windows face the street)
2. Instances get public IPs (everyone knows the street address)
3. Security Group allows inbound traffic (doorbell works, visitors can knock)

**Example**: Your web servers live here (they WANT to talk to internet users).

```
┌─────────────────────────────────────────┐
│  Public Subnet (172.31.0.0/20)          │
│                                         │
│  Route Table:                           │
│  ├─ 172.31.0.0/16 → Local (internal)   │
│  └─ 0.0.0.0/0 → Internet Gateway       │
│                                         │
│  ┌────────────────────────────────┐   │
│  │ EC2 Web Server                 │   │
│  │ Private IP: 172.31.1.50        │   │
│  │ Public IP: 18.207.142.45 ✓     │   │
│  │ (Accessible from internet)     │   │
│  └────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### Private Subnet (Hidden from Internet)

A subnet where instances **can reach the internet BUT the internet cannot reach them**.

**Building analogy**: It's like a **room hidden in the back of the building**, away from the street. There are no visible windows or doors from outside. If someone inside needs to go out (order supplies), they use a secret side door (NAT Gateway) that hides their identity. Strangers from the street can NEVER find this room.

**What makes it private?**
1. Route table does NOT have a route to Internet Gateway (no doors/windows facing street)
2. Instances do NOT have public IPs (no street address visible)
3. Traffic to internet goes through NAT Gateway (secret side door with one-way exit)

**Example**: Your databases live here (they DON'T want to talk to internet users, for security).

```
┌─────────────────────────────────────────┐
│  Private Subnet (172.31.16.0/20)        │
│                                         │
│  Route Table:                           │
│  ├─ 172.31.0.0/16 → Local (internal)   │
│  └─ 0.0.0.0/0 → NAT Gateway (outbound) │
│                                         │
│  ┌────────────────────────────────┐   │
│  │ RDS Database                   │   │
│  │ Private IP: 172.31.16.50       │   │
│  │ Public IP: ❌ None             │   │
│  │ (Hidden from internet)         │   │
│  └────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### Public vs Private Comparison

| Feature | Public | Private |
|---------|--------|---------|
| **Public IP** | ✓ Yes | ❌ No |
| **Internet can reach it** | ✓ Yes | ❌ No |
| **Can reach internet** | ✓ Yes (IGW) | ✓ Yes (NAT) |
| **Use case** | Web servers | Databases, app servers |
| **Route table has** | Route to IGW | Route to NAT |

---

## Network Traffic Flow

### Public Subnet Flow: User → Web Server

Here's exactly what happens when someone visits your website:

```
1. USER INITIATES REQUEST
   └─ Browser: curl http://18.207.142.45

2. TRAFFIC REACHES AWS
   └─ Internet → AWS Region

3. ROUTE TABLE DECISION
   └─ Destination: 18.207.142.45:80 (public IP)
   └─ Route table: 0.0.0.0/0 → Internet Gateway
   └─ Decision: Send to IGW

4. IGW TRANSLATION
   └─ Translates 18.207.142.45 → 172.31.1.50 (private IP)

5. NACL CHECK (Stateless - checks both directions)
   └─ Inbound: Is port 80 allowed? ✓ Yes
   └─ Allows traffic in

6. SECURITY GROUP CHECK (Stateful - remembers conversation)
   └─ Is port 80 allowed? ✓ Yes
   └─ Allows traffic in

7. EC2 RECEIVES
   └─ Nginx on port 80 receives request
   └─ Sends response (e.g., HTML page)

8. RETURN PATH (Automatic)
   └─ EC2 sends response
   └─ SG: ✓ Allows (remembers original request)
   └─ NACL: ✓ Allows outbound
   └─ IGW: Translates 172.31.1.50 → 18.207.142.45
   └─ User receives web page
```

### Private Subnet Flow: Database Access

Here's how an app server talks to a database in a private subnet:

```
1. APP SERVER INITIATES
   └─ Address: RDS at 172.31.16.50:3306

2. ROUTE TABLE DECISION
   └─ Destination: 172.31.16.50 (private IP)
   └─ Route table: 172.31.0.0/16 → Local
   └─ Decision: Local delivery (same VPC)

3. NACL CHECK
   └─ Is port 3306 inbound allowed? ✓ Yes

4. SECURITY GROUP CHECK
   └─ Is traffic from App-SG allowed? ✓ Yes (DB-SG allows it)

5. RDS RECEIVES
   └─ MySQL port 3306 receives query
   └─ Sends response

6. RETURN PATH (Automatic)
   └─ All checks pass (same subnet)
   └─ Response reaches app server
```

---

## Security: Groups & NACLs

### Quick Comparison (Building Analogy)

Both protect your instances, but work at different levels:

**NACL = Security checkpoint at room entrance** (subnet-level)
- Checks ALL traffic entering/leaving the room
- Stateless (must check both directions explicitly)
- Applies to entire subnet

**Security Group = Door lock on each room** (instance-level)
- Checks traffic for that specific instance
- Stateful (remembers your conversation)
- Applies to individual instances

| Feature | Security Group | NACL |
|---------|---|---|
| **Level** | Instance (door lock) | Subnet (checkpoint at entrance) |
| **Stateful** | ✓ Yes (remembers) | ❌ No (checks both ways) |
| **Rules** | Allow only | Allow + Deny |
| **Default** | Deny inbound | Allow all |
| **When evaluated** | Applied per instance | Applied per subnet |

### Security Group (Instance Protection)

Protects individual EC2 instances. Think of it as a **door lock on your specific room/instance**.

**Building analogy**: Each room (instance) has its own lock. If the lock says "allow port 80", then anyone knocking on port 80 can enter. Visitors don't need to knock on the way out (stateful - SG remembers the conversation).

**Key features**:
- **Stateful**: Remembers conversations. If you allow inbound on port 80, response traffic automatically goes back.
- **Allow only**: You specify what's ALLOWED. Everything else is blocked.
- **Instance-level**: Each instance has its own security group (each room has its own lock)

**Example: Web Server Security Group**

```
Web-SG (Inbound Rules)
├─ Port 80 (HTTP)    from 0.0.0.0/0    (anyone on internet)
├─ Port 443 (HTTPS)  from 0.0.0.0/0    (anyone on internet)
├─ Port 22 (SSH)     from 10.0.0.0/8   (your office)
└─ All responses     (automatic - SG is stateful)
```

### NACL (Subnet Protection)

Protects all instances in a subnet. Think of it as a **security checkpoint at the room entrance** where EVERYONE must pass through.

**Building analogy**: Before anyone (traffic) can enter the room (subnet), they must pass through a security checkpoint. The checkpoint checks BOTH coming in AND going out. It doesn't remember people (stateless) - every trip requires a new check.

**Key features**:
- **Stateless**: Must explicitly allow both inbound AND outbound. Doesn't remember past conversations.
- **Allow + Deny**: Can explicitly deny rules (useful for blocking bad actors - "deny this person entry")
- **Subnet-level**: Applies to entire subnet (everyone entering/leaving the room passes through)

**Example: Web Server Subnet NACL**

```
Inbound Rules (requests coming IN):
  Rule 100: Allow port 80 from 0.0.0.0/0      ✓ HTTP
  Rule 110: Allow port 443 from 0.0.0.0/0     ✓ HTTPS
  Rule 120: Allow port 22 from 10.0.0.0/8     ✓ SSH
  Rule 130: Allow 1024-65535 from 0.0.0.0/0   ✓ Responses (ephemeral)

Outbound Rules (responses going OUT):
  Rule 100: Allow all to 0.0.0.0/0             ✓ Everything
```

**Why the 1024-65535 rule?** Responses from servers come back on random high ports (ephemeral ports), so you must explicitly allow them in NACL.

### How They Work Together (Building Analogy)

```
VISITOR ARRIVES AT YOUR BUILDING

Step 1: NACL Check (Security checkpoint at room entrance)
   "Is this visitor allowed? (checking port number)"
   ✓ YES → Pass through

Step 2: Security Group Check (Door lock on your instance)
   "Is this visitor allowed? (checking type of knock)"
   ✓ YES → Allow in
   "Remember this visitor so they can leave later"

Step 3: INSTANCE RECEIVES
   EC2 or application processes the request

Step 4: INSTANCE SENDS RESPONSE
   "Visitor is leaving, remember we allowed them?"

Step 5: Security Group Check (automatic)
   "Yes, this is the visitor we allowed in"
   ✓ ALLOW OUT (stateful - remembers)

Step 6: NACL Check (Security checkpoint again)
   "Is outbound port allowed?"
   ✓ YES → Let them leave

VISITOR LEAVES WITH RESPONSE
```

**Key insight**: Two layers of protection:
1. **NACL** = Checkpoint for the entire room (subnet-level)
2. **Security Group** = Lock for each door (instance-level)

---

## Common Architectures

### Architecture 1: Simple Web Server

For learning or small projects:

```
Public VPC (172.31.0.0/16)
│
├─ Subnet-1a (172.31.0.0/20)
│  └─ EC2: Web Server
│     Public IP: 18.207.142.45
│     Listens: Port 80/443
│
└─ Internet Gateway (IGW)
   └─ Allows traffic from internet
```

**Setup**:
1. Create VPC with `172.31.0.0/16`
2. Create subnet with `172.31.0.0/20`
3. Create and attach Internet Gateway
4. Add route: `0.0.0.0/0 → IGW` to route table
5. Launch EC2 with public IP
6. Security Group: Allow port 80/443 from `0.0.0.0/0`

**Good for**: Learning, demos, small websites

### Architecture 2: Public + Private (Production Standard)

For real applications with proper separation.

**Building analogy**:
```
Your Building Layout:
├─ Ground Floor (Public) = Your storefront (web servers)
│  └─ Face the street, talk to customers (internet)
│
├─ Second Floor (Private) = Your office (app servers)
│  └─ Hidden from public, receives orders from storefront
│
└─ Basement (Private) = Your vault (database)
   └─ Locked away, nobody sees it except office staff
```

**Architecture diagram**:

```
VPC (172.31.0.0/16)
│
├─ Public Subnet-1a (172.31.0.0/20) = STOREFRONT FLOOR
│  └─ Web Server (Public IP)
│     ✓ Visible from street (has public IP)
│     ✓ Receives: HTTP/HTTPS from internet customers
│     ✓ Sends: Requests to App tier
│
├─ Private Subnet-1b (172.31.16.0/20) = OFFICE FLOOR
│  └─ App Server (No public IP)
│     ✗ Hidden from street (no public IP)
│     ✓ Receives: Requests from Web tier only
│     ✓ Sends: Queries to DB tier
│
├─ Private Subnet-1c (172.31.32.0/20) = VAULT (BASEMENT)
│  └─ RDS Database (No public IP)
│     ✗ Hidden from street
│     ✗ Hidden from customers
│     ✓ Receives: Queries from App tier ONLY
│     Customers → Storefront → Office → Vault
│     (can't skip steps!)
│
└─ Internet Gateway (IGW)
   └─ Front door of building (public subnet connects here)

└─ NAT Gateway (in public subnet)
   └─ Secret side exit (private subnets use this to reach internet)
```

**Security Benefits**:
- **Web tier can't access database directly** (different floors, no direct stairway)
- **Database hidden from internet** (in vault, not visible from street)
- **If web server compromised, attacker can't reach database** (must go through office, which has its own locks)
- **Defense in depth** (multiple layers of protection)

**Good for**: Production apps with proper security layers

### Architecture 3: Multi-AZ High Availability

For reliability:

```
VPC (172.31.0.0/16)
│
├─ AZ: us-east-1a
│  ├─ Public Subnet (172.31.0.0/20)
│  │  └─ EC2: Web Server #1
│  └─ Private Subnet (172.31.32.0/20)
│     └─ RDS: Database (Primary)
│
├─ AZ: us-east-1b
│  ├─ Public Subnet (172.31.16.0/20)
│  │  └─ EC2: Web Server #2
│  └─ Private Subnet (172.31.48.0/20)
│     └─ RDS: Database (Standby)
│
└─ Load Balancer
   └─ Distributes traffic to both web servers
```

**Benefits**:
- If 1 AZ goes down, 1a continues
- Database replicates across AZs
- No single point of failure

---

## Advanced Scenarios

### VPN Gateway (Connect On-Premises)

Connect your office network to AWS VPC:

```
Office Network (10.0.0.0/16)
    ↕ (Encrypted VPN Tunnel)
AWS VPC (172.31.0.0/16)
```

**Use case**: Access AWS resources from your office securely.

### VPC Peering (Connect to Other VPCs)

Connect one VPC to another VPC:

```
VPC-A (172.31.0.0/16)  ←→  VPC-B (10.0.0.0/16)
```

**Use case**: Share data between VPCs without going through internet.

### VPC Endpoints (Access AWS Services Privately)

Access S3, DynamoDB, etc. without leaving AWS network:

```
Private Subnet
    │
    └─→ S3 (via VPC Endpoint)
        └─ No internet required
        └─ No NAT Gateway costs
```

**Use case**: Download files from S3 in private subnet without NAT costs.

### Default VPC Across Multiple AZs

![image (2)](https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png)

Your default VPC automatically spans multiple AZs for redundancy.

---

## Best Practices

### 1. Security

- ✅ Put databases in private subnets
- ✅ Use security groups to restrict traffic
- ✅ Use NACLs for deny rules (block bad actors)
- ✅ Always separate public and private layers
- ❌ Don't expose RDS to internet
- ❌ Don't open port 22 to `0.0.0.0/0`

### 2. High Availability

- ✅ Deploy across multiple AZs
- ✅ Use auto-scaling groups
- ✅ Use load balancers
- ✓ Use RDS Multi-AZ
- ❌ Don't put all resources in one AZ

### 3. Network Design

- ✅ Plan IP ranges before creating VPC
- ✅ Leave room for growth (use `/16` for large VPCs)
- ✅ Use consistent naming (Public-1a, Private-1a, etc.)
- ✅ Document your architecture
- ❌ Don't use overlapping CIDR blocks

### 4. Cost Optimization

- ✅ Use VPC Endpoints to avoid NAT costs
- ✅ Combine resources when possible
- ✅ Use spot instances in public subnets
- ❌ Don't create unnecessary NAT Gateways
- ❌ Don't leave unused Elastic IPs

---

## Troubleshooting

### Problem: EC2 Can't Reach Internet

**Symptoms**: EC2 instance in public subnet can't reach internet (ping 8.8.8.8 fails)

**Checklist**:
1. ✓ Does subnet have route to IGW? (`aws ec2 describe-route-tables`)
2. ✓ Is route `0.0.0.0/0 → igw-xxxxx`? (If not, add it)
3. ✓ Does instance have public IP? (If not, associate one)
4. ✓ Does security group allow outbound? (Default allows all outbound)
5. ✓ Does NACL allow outbound? (Check ephemeral ports 1024-65535)

**Fix**:
```bash
# Add route if missing
aws ec2 create-route --route-table-id rtb-xxxxx \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-xxxxx
```

### Problem: Private Subnet Can't Reach Internet

**Symptoms**: EC2 in private subnet can't download updates (`apt update` fails)

**Checklist**:
1. ✓ Is there a NAT Gateway? (If not, create one in public subnet)
2. ✓ Does route table have route to NAT? (`0.0.0.0/0 → nat-xxxxx`)
3. ✓ NAT Gateway in same AZ as private subnet? (If not, create NAT in different AZ)
4. ✓ Does security group allow outbound? (Default allows all)

**Fix**:
```bash
# Create NAT Gateway in public subnet
aws ec2 create-nat-gateway --subnet-id subnet-xxxxx \
  --allocation-id eipalloc-xxxxx

# Add route in private subnet route table
aws ec2 create-route --route-table-id rtb-private \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id nat-xxxxx
```

### Problem: Two Subnets Can't Talk to Each Other

**Symptoms**: EC2 in subnet-1 can't reach EC2 in subnet-2 (even in same VPC)

**Checklist**:
1. ✓ Are they in same VPC? (Use same CIDR block?)
2. ✓ Do route tables have "Local" route for VPC CIDR? (Should be automatic)
3. ✓ Do security groups allow traffic? (Add rule: source = other subnet CIDR)

**Fix**:
```bash
# Add security group rule to allow from other subnet
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 3306 \
  --cidr 172.31.16.0/20  # CIDR of other subnet
```

---

## Key Takeaways

| Concept | Remember |
|---------|----------|
| **VPC** | Your isolated network in AWS |
| **Subnet** | Section of VPC with own IP range |
| **Public Subnet** | Accessible from internet (has route to IGW) |
| **Private Subnet** | Hidden from internet (routes through NAT) |
| **Security Group** | Instance-level firewall (stateful) |
| **NACL** | Subnet-level firewall (stateless) |
| **Route Table** | Rules for directing traffic |
| **Internet Gateway** | Gateway to internet (public subnets) |
| **NAT Gateway** | One-way exit for private subnets |

---

## Quick Reference

### Create VPC from Scratch

```bash
# 1. Create VPC
vpc=$(aws ec2 create-vpc --cidr-block 172.31.0.0/16 \
  --query 'Vpc.VpcId' --output text)

# 2. Create subnet
subnet=$(aws ec2 create-subnet --vpc-id $vpc \
  --cidr-block 172.31.0.0/20 --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)

# 3. Create Internet Gateway
igw=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' --output text)

# 4. Attach to VPC
aws ec2 attach-internet-gateway --vpc-id $vpc --internet-gateway-id $igw

# 5. Create route table
rt=$(aws ec2 create-route-table --vpc-id $vpc \
  --query 'RouteTable.RouteTableId' --output text)

# 6. Add internet route
aws ec2 create-route --route-table-id $rt \
  --destination-cidr-block 0.0.0.0/0 --gateway-id $igw

# 7. Associate route table with subnet
aws ec2 associate-route-table --subnet-id $subnet --route-table-id $rt

echo "VPC created: $vpc"
echo "Subnet: $subnet"
```

### Common Security Group Rules

```bash
# Allow HTTP
aws ec2 authorize-security-group-ingress --group-id sg-xxxxx \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress --group-id sg-xxxxx \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress --group-id sg-xxxxx \
  --protocol tcp --port 22 --cidr YOUR_IP/32

# Allow from other security group
aws ec2 authorize-security-group-ingress --group-id sg-db \
  --protocol tcp --port 3306 --source-group sg-app
```

---

## Visual Architecture References

![image](https://user-images.githubusercontent.com/52529498/125168074-9dcddb00-e171-11eb-8e92-4c8f0a7ef92b.png)

![image](https://user-images.githubusercontent.com/52529498/125170306-7e887b00-e17c-11eb-94ba-81134d2cee4a.png)

![image](https://user-images.githubusercontent.com/52529498/137606958-956256de-0ccc-410b-82d7-e3ec6ae49b3b.png)

![image](https://user-images.githubusercontent.com/52529498/137607039-4ec285b8-0ef7-4841-8241-3c8e6f73418a.png)

---

## Next Steps

- **Beginner**: Create a simple VPC and launch an EC2 instance
- **Intermediate**: Add a private subnet with a database
- **Advanced**: Implement multi-AZ with auto-scaling and load balancing

---

**Last Updated**: 2026-05-28
**For Questions**: Refer to AWS VPC documentation
