# VPC (Virtual Private Cloud): Comprehensive Tutoring Guide

> **Master AWS VPC**: Learn to design and manage your own isolated network within AWS. This guide covers everything from
> fundamentals to advanced architectures, with practical examples for beginners, intermediate, and advanced users.

---

## Table of Contents

1. [What is VPC? (Fundamentals)](#what-is-vpc-fundamentals)
2. [Core Concepts](#core-concepts)
3. [Default VPC vs Custom VPC](#default-vpc-vs-custom-vpc)
4. [Subnets: Public vs Private](#subnets-public-vs-private)
5. [VPC Architecture Patterns](#vpc-architecture-patterns)
6. [Network Components](#network-components)
7. [Security: NACL and Security Groups](#security-nacl-and-security-groups)
8. [Advanced Scenarios](#advanced-scenarios)
9. [AWS Services and VPC](#aws-services-and-vpc)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Real-World Scenarios](#real-world-scenarios)

---

## What is VPC? (Fundamentals)

### Simple Explanation

A **VPC (Virtual Private Cloud)** is your own **isolated private network inside AWS**. Think of it like this:

```
Without VPC:
  AWS Account = Shared building (dangerous!)

With VPC:
  AWS Account = Secure compound
  VPC = Your building within the compound
  Subnets = Rooms in your building
  NACL = Security checkpoint at each room entrance (subnet-level)
  Security Groups = Door locks on each room (instance-level)
  Internet Gateway = Entrance to the compound from outside
  NAT Gateway = One-way exit door (private rooms to outside)
```

**How they work together:**

```
Internet Traffic
    ↓
Internet Gateway
    ↓
NACL (subnet firewall) ← Checks all traffic entering subnet
    ↓
Security Group (instance firewall) ← Checks traffic for specific instance
    ↓
Instance (EC2, RDS, etc.)
```

**Key difference:**

- **NACL** = Subnet-level (protects all instances in the room)
- **Security Group** = Instance-level (protects specific door)


### Key Ideas for Beginners

- **Private**: Your VPC is isolated from other AWS customers' VPCs
- **Configurable**: You control the network structure (IP ranges, subnets, routing)
- **Global-Ready**: You can have VPCs across different AWS regions
- **Default Available**: Every AWS account gets a default VPC ready to use immediately

### Important Fact

Every AWS account automatically gets a **default VPC** in each region. This default VPC is pre-configured and ready for you to launch EC2 instances immediately—no setup needed!

```

AWS Account Created
↓
Every Region gets a Default VPC
↓
Each Default VPC has:

- CIDR block: 172.31.0.0/16 (65,536 IP addresses)
- 1 subnet per Availability Zone
- Internet Gateway (automatically attached)
- Default Security Group
- Default NACL

```

---

## Core Concepts

### AWS Regions and Availability Zones (AZs)

#### What is a Region?

**Definition**: A **Region** is a completely independent geographic area where AWS operates a cluster of data centers.

**Key Characteristics**:
- **Geographic**: Each region is in a different part of the world
- **Independent**: Regions are isolated—if one fails, others are unaffected
- **Complete**: Each region has its own VPCs, EC2, databases, everything
- **30+ Regions**: AWS operates 30+ regions globally
- **Compliance**: Choose regions based on data residency requirements (GDPR, etc.)

**Common Regions**:
```
us-east-1      = Northern Virginia (largest, most services)
us-west-2      = Oregon
eu-west-1      = Ireland
ap-southeast-1 = Singapore
ap-northeast-1 = Tokyo
```

**Why use multiple regions?**
```
✅ Disaster recovery (if one region fails, use another)
✅ Low latency (serve users from nearby region)
✅ Compliance (store data in specific countries)
✅ Service availability (not all services in all regions)
```

#### What is an Availability Zone (AZ)?

**Definition**: An **Availability Zone (AZ)** is a physically separate data center (or logical grouping of data centers) within a region.

**Key Characteristics**:
- **Minimum 2 per Region**: AWS regions have at least 2 AZs for redundancy
- **Typically 3+ AZs**: Most regions have 3-6 AZs
- **Multiple Physical Data Centers per AZ**: Each AZ typically contains 1-5 physical data centers
- **Treated as Single Logical Unit**: Multiple data centers in same AZ share infrastructure for redundancy
- **Physically Isolated from Other AZs**: Separate buildings, power supplies, cooling, networks from other AZs
- **Low Latency Connection**: Connected with high-speed fiber within AZ and between AZs (microseconds)
- **Named Sequentially**: us-east-1a, us-east-1b, us-east-1c, etc.
- **Failure Isolation**: If one AZ fails, others continue operating unaffected

**AWS Requirement**:
```
Minimum: 2 AZs per region (for redundancy)
Typical: 3-4 AZs per region
Maximum: Can go up to 6 AZs in large regions
Goal: Ensure you can survive failure of 1 data center
```

**Real Example: Northern Virginia (us-east-1) has 6 AZs**:
```
Region: us-east-1 (Northern Virginia)
├─ us-east-1a (Availability Zone A)
│  ├─ Physical Data Center 1 (Building A1)
│  ├─ Physical Data Center 2 (Building A2)
│  └─ Connected by high-speed fiber, shared power, cooling
│     (Treated as ONE logical failure domain)
│
├─ us-east-1b (Availability Zone B)
│  ├─ Physical Data Center 3 (Building B1)
│  ├─ Physical Data Center 4 (Building B2)
│  └─ Independent power grid, network, cooling from AZ-A
│
├─ us-east-1c (Availability Zone C)
│  ├─ Physical Data Center 5 (Building C1)
│  ├─ Physical Data Center 6 (Building C2)
│  └─ Independent from AZ-A and AZ-B
│
├─ us-east-1d (Availability Zone D)
│  ├─ Physical Data Center 7
│  ├─ Physical Data Center 8
│  └─ Independent from all other AZs
│
├─ us-east-1e (Availability Zone E)
│  └─ Multiple physical data centers
│
└─ us-east-1f (Availability Zone F)
   └─ Multiple physical data centers

Total: 6 Availability Zones, each containing 1-5 physical data centers
```

**Key Clarification: AZ vs Physical Data Centers**
```
✅ CORRECT Understanding:

One AZ (Logical Unit):
├─ Contains 1-5 physical data centers
├─ Data centers connected by high-speed fiber (microseconds)
├─ Shared infrastructure within AZ (for redundancy)
├─ Isolated from other AZs (separate power, cooling, networks)
└─ Treated as ONE failure domain by AWS

From AWS User perspective:
- Deploy resources to an AZ (us-east-1a)
- AWS handles physical data center placement internally
- If one AZ fails, others are unaffected
- You don't control which physical data center, just the AZ
```

**Why use multiple AZs?**
```
✅ High availability (survives data center outages)
✅ Redundancy (AWS automatically replicates across AZs)
✅ Performance (choose nearest AZ for lowest latency)
✅ Resilience (architectures spread across AZs)
```

#### Hierarchy: How They Relate

```
Region (Geographic Area)
    │
    ├─ Availability Zone A (Data Center 1)
    │  └─ VPC Subnets can be in this AZ
    │
    ├─ Availability Zone B (Data Center 2)
    │  └─ VPC Subnets can be in this AZ
    │
    └─ Availability Zone C (Data Center 3)
       └─ VPC Subnets can be in this AZ

Example: Your VPC in us-east-1
├─ Subnet-A in us-east-1a
├─ Subnet-B in us-east-1b
└─ Subnet-C in us-east-1c
   (All in same VPC, different AZs for high availability)
```

#### Practical Example: Building HA Application

```
Scenario: Deploy a web application with high availability

Step 1: Choose Region
├─ Users in US? → us-east-1
└─ Users in Europe? → eu-west-1

Step 2: Create VPC in region
├─ VPC automatically spans all AZs
└─ You can launch resources in any AZ

Step 3: Create subnets in multiple AZs
├─ Subnet-1a (us-east-1a) - Public
├─ Subnet-1b (us-east-1b) - Public
└─ Subnet-1c (us-east-1c) - Public

Step 4: Launch instances across AZs
├─ Web Server 1 in Subnet-1a
├─ Web Server 2 in Subnet-1b
└─ Web Server 3 in Subnet-1c

Step 5: Use Load Balancer across AZs
├─ Routes traffic to all 3 servers
├─ Automatic failover if one AZ fails
└─ Users experience no downtime!
```

#### Advanced: Latency Considerations

```
Within same region (cross-AZ):
├─ Typical latency: 1-5 milliseconds
├─ Uses AWS private network backbone
├─ Safe for synchronous database replication
├─ Minimal data transfer charges
└─ Recommended for most HA setups

Between regions:
├─ Typical latency: 50-200+ milliseconds
├─ Goes through public internet or AWS backbone
├─ Higher data transfer charges
├─ Better for asynchronous replication
└─ Use only for disaster recovery
```

#### Advanced: AZ Mapping Randomization

**Important**: AWS randomizes AZ names per account for load distribution!

```
Your Account:
├─ us-east-1a → Physical Data Center #1

Your Colleague's Account:
├─ us-east-1a → Physical Data Center #3

Same name, different physical location!

Solution: Use AZ IDs (more reliable)
├─ Your account: use1-az1 → same physical location
├─ Colleague's account: use1-az1 → same physical location
```

### Visual: How Regions, Availability Zones, and VPCs Relate

![image (2)](https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png)

**Example**: Northern Virginia (`us-east-1`) has 6 Availability Zones:
- us-east-1a, us-east-1b, us-east-1c, us-east-1d, us-east-1e, us-east-1f

When you create an AWS account:

```
For each region:
✓ 1 default VPC is created
✓ 1 subnet is created in each AZ
✓ You can immediately launch EC2 instances

```

---

## Default VPC vs Custom VPC

### Default VPC (Pre-Configured)

When you create an AWS account, you automatically get a **default VPC** in each region. Here's what it includes:

| Feature | Default VPC |
|---------|------------|
| **CIDR Block** | 172.31.0.0/16 (65,536 IP addresses) |
| **Subnets** | 1 public subnet per AZ (/20 CIDR = 4,096+ addresses each) |
| **Internet Gateway** | ✅ Attached automatically |
| **Public IPs** | ✅ All instances get both private AND public IPs |
| **Default Security Group** | ✅ Allows all outbound, denies all inbound |
| **Default NACL** | ✅ Allows all inbound and outbound |
| **Route Table** | ✅ Routes 0.0.0.0/0 to Internet Gateway |
| **DHCP Options** | ✅ Set up automatically |

### Default VPC: Key Facts

✅ **Ready to use immediately** - Just launch instances
✅ **Can be deleted** - But you can recreate it from AWS console
✅ **Per-region** - Each region has its own default VPC
✅ **Internet accessible** - All instances can reach the internet

### When to Use Default VPC

**Use default VPC for:**
- Learning and testing
- Development environments
- Quick prototypes
- Non-production workloads

### When to Create Custom VPC

**Create custom VPC for:**
- Production applications
- Multi-tier architecture (public/private subnets)
- Enhanced security requirements
- Cross-account deployments
- Applications needing isolation

---

## Subnets: Public vs Private

### What is a Subnet?

A **subnet** is a smaller network within your VPC. Think of it as:
```

VPC = Your building
Subnet = A floor in your building
Resources (EC2, RDS) = Rooms on that floor

```

### Public Subnet (Internet Accessible)

**Definition**: A subnet where instances **can** reach the internet and vice versa.

```

┌─────────────────────────────────────┐
│ VPC (172.31.0.0/16)                 │
│ │
│ Public Subnet (172.31.0.0/20)       │
│ ├─ Route to Internet Gateway │
│ ├─ Instances get public IPs │
│ └─ Can send/receive internet traffic│
│ │
│ Internet Gateway (IGW)              │
│ ↓ │
│ Internet (0.0.0.0/0)             │
│ │
└─────────────────────────────────────┘

```

**Requirements for public subnet:**
1. Route table with route to Internet Gateway
2. Internet Gateway attached to VPC
3. Instances need public IP (Elastic IP or auto-assigned)
4. Security Group allows inbound traffic
5. NACL allows traffic

### Private Subnet (Internet Hidden)

**Definition**: A subnet where instances **cannot** receive traffic from the internet.

```

┌─────────────────────────────────────┐
│ VPC (172.31.0.0/16)                 │
│ │
│ Private Subnet (172.31.16.0/20)     │
│ ├─ NO route to Internet Gateway │
│ ├─ Instances have NO public IP │
│ ├─ Cannot receive internet traffic │
│ └─ Protected from internet access │
│ │
│ Can only communicate within VPC │
│ (or via NAT Gateway for outbound)   │
│ │
└─────────────────────────────────────┘

```
> Databases need outbound access for operational necessities (patches, time, DNS), but NAT Gateway ensures they can't be accessed FROM the internet—maintaining security while enabling functionality! 🔒


**When to use private subnet:**
- Database servers (RDS)
- Application servers not needing internet access
- Internal APIs
- Backend services
- Sensitive workloads

---

## VPC Architecture Patterns

### Pattern 1: Simple Public VPC (Learning/Dev)

**Use case**: Testing, learning, development

```

Public Subnet (web servers)
↑
↓ (can reach internet)
Internet Gateway
↑
↓
Internet

```

**Pros:**
- Simple to set up
- All resources internet-accessible
- Good for learning

**Cons:**
- Less secure
- Not suitable for production
- All resources exposed to internet

---

### Pattern 2: Public + Private (Standard Production)

**Use case**: Production applications with multiple tiers

```

┌─────────────────────────────────┐
│ VPC │
├─────────────────────────────────┤
│ Public Subnet (Web tier)        │
│ - Web servers/ALB │
│ - Internet Gateway │
│ ↕ │
├─────────────────────────────────┤
│ Private Subnet (App tier)       │
│ - Application servers │
│ - Bastion host for access │
│ ↕ │
├─────────────────────────────────┤
│ Private Subnet (DB tier)        │
│ - Database servers │
│ - NAT Gateway for outbound │
│ │
└─────────────────────────────────┘

```

**Traffic flow:**
1. Internet → Web tier (public subnet)
2. Web tier → App tier (within VPC)
3. App tier → DB tier (within VPC)
4. Outbound traffic → NAT Gateway → Internet

**Security benefits:**
- ✅ Databases are hidden from internet
- ✅ Only web servers exposed
- ✅ Extra layer of protection
- ✅ Least privilege access

### Pattern 3: Multi-AZ Production (High Availability)

```

AZ-1:                          AZ-2:
┌────────────────────┐ ┌────────────────────┐
│ Public Subnet 1 │ │ Public Subnet 2 │
│ - Web Server 1 │ │ - Web Server 2 │
│ - Bastion Host │ │ │
└────────────────────┘ └────────────────────┘
↓ ↓
Internet Gateway Internet Gateway
↓ ↓
Internet Router Internet Router

┌────────────────────┐ ┌────────────────────┐
│ Private Subnet 1 │ │ Private Subnet 2 │
│ - App Server 1 │ │ - App Server 2 │
└────────────────────┘ └────────────────────┘
↓ ↓
NAT Gateway 1 NAT Gateway 2

┌────────────────────┐ ┌────────────────────┐
│ Private DB Subnet 1│ │ Private DB Subnet 2│
│ - RDS Primary │ │ - RDS Replica │
└────────────────────┘ └────────────────────┘
↓ ↓
Multi-AZ RDS (Automatic failover)

```

**Benefits:**
- ✅ Survives AZ failure
- ✅ High availability
- ✅ Load balancing across AZs
- ✅ Automatic failover

---

## Network Components

### 1. Internet Gateway (IGW)

**Purpose**: Allows communication between VPC and the internet

```

Your VPC ←→ Internet Gateway ←→ Internet

```

**Key facts:**
- Only allows traffic TO resources with public IPs
- Stateless (doesn't track connections)
- One IGW per VPC (maximum)
- Must be explicitly attached to VPC

---

### 2. NAT Gateway (Network Address Translation)

**Purpose**: Allows private subnet resources to reach the internet (outbound only)

```

Private Subnet → NAT Gateway → Internet
(translates source IP)

BUT:
Internet → ✗ NAT Gateway (blocked)

```

**Use case**: Private database servers need to download patches from the internet

**Key facts:**
- Only allows outbound traffic
- Blocks unsolicited inbound traffic (secure)
- Uses an Elastic IP
- Should be in public subnet
- Pay per data processed

---

### 3. VPN Gateway

**Purpose**: Connects on-premises network to AWS VPC securely

```

On-Premises ←→ VPN Connection ←→ VPN Gateway ←→ VPC
Network Private Subnets

```

**Use case**: Company wants employees to access VPC as if they're in the office

**Key facts:**
- Encrypted tunnel
- Uses customer gateway (on-premises)
- Maintains privacy
- Reduces need for Bastion hosts

---

### 4. Bastion Host (Jump Box)

**Purpose**: Secure gateway to access private subnet resources from internet

```

Internet ← SSH → Bastion Host (public) ← SSH → Private Server

```

**Setup:**
1. Launch small EC2 in public subnet
2. Open SSH (port 22) to your IP in security group
3. SSH to Bastion host
4. From Bastion, SSH to private instances

**Benefits:**
- Single point of access to monitor
- Reduces attack surface
- Easy to add MFA
- Audit trail available

---

## Security: NACL and Security Groups

### Quick Comparison

| Feature | Security Group | NACL |
|---------|----------------|------|
| **Level** | Instance | Subnet |
| **Stateful?** | ✅ Yes | ❌ No (stateless) |
| **Allow/Deny** | Allow only | Allow & Deny |
| **Processing** | All rules evaluated | Rules in order (first match wins) |
| **Attached to** | Instances | Subnets |
| **How many** | Multiple per instance | One per subnet |

### Security Group (Instance-Level)

**Purpose**: Firewall for individual instances

```

Security Group Rules:
├─ Inbound: Who can connect TO this instance?
├─ Outbound: What can this instance connect to?
└─ Stateful: If inbound allowed, response automatically goes out

```

**Example: Web Server Security Group**

```
Inbound Rules:
├─ Port 80 (HTTP): Source 0.0.0.0/0
├─ Port 443 (HTTPS): Source 0.0.0.0/0
└─ Port 22 (SSH): Source YOUR_IP/32

Outbound Rules:
└─ All traffic allowed (default)
```

**Common mistake**: Opening port 22 (SSH) to 0.0.0.0/0 (the whole internet) = dangerous!

### NACL (Subnet-Level)

**Purpose**: Subnet-level firewall

**Critical Concept**: NACLs are **STATELESS** - you MUST define BOTH INGRESS (inbound) AND EGRESS (outbound) rules separately!

#### Why Both Ingress AND Egress Rules?

Because NACLs don't remember connections (stateless), every traffic direction needs explicit rules:

```
Client Request/Response Flow (HTTP):

Client (203.0.113.45:54321)
    │
    ├─ Sends HTTP request on port 80
    │  → Check INGRESS Rule #100: Allow TCP 80 from 0.0.0.0/0? ✅ YES
    │  → Request enters subnet
    │
    ├─ Server processes request
    │
    ├─ Server sends response back on port 80
    │  → Check EGRESS Rule #100: Allow TCP 80 to 0.0.0.0/0? ✅ YES
    │  → Response leaves subnet
    │
    └─ Client receives response ✅

WITHOUT EGRESS RULE: Response gets blocked! ❌
```

#### Complete NACL Example: Web Server Subnet

```
VPC: 10.0.0.0/16
Public Subnet: 10.0.1.0/24 (Web servers)

═══════════════════════════════════════════════════════════

INGRESS RULES (Traffic Coming INTO the subnet):

Rule #100: Allow HTTP (port 80)
├─ Protocol: TCP
├─ Port Range: 80-80
├─ Source: 0.0.0.0/0 (from anywhere)
└─ Action: ALLOW

Rule #110: Allow HTTPS (port 443)
├─ Protocol: TCP
├─ Port Range: 443-443
├─ Source: 0.0.0.0/0 (from anywhere)
└─ Action: ALLOW

Rule #120: Allow SSH (port 22)
├─ Protocol: TCP
├─ Port Range: 22-22
├─ Source: 10.0.0.0/16 (from VPC only - bastion)
└─ Action: ALLOW

Rule #130: Allow Ephemeral Responses (1024-65535)
├─ Protocol: TCP
├─ Port Range: 1024-65535
├─ Source: 0.0.0.0/0 (from anywhere)
└─ Action: ALLOW
   Note: Clients connect FROM random high ports

Rule #32767: Deny All (catch-all default)
├─ Protocol: All
├─ Port: All
└─ Action: DENY

═══════════════════════════════════════════════════════════

EGRESS RULES (Traffic Going OUT of the subnet):

Rule #100: Allow HTTP (port 80)
├─ Protocol: TCP
├─ Port Range: 80-80
├─ Destination: 0.0.0.0/0 (to anywhere)
└─ Action: ALLOW

Rule #110: Allow HTTPS (port 443)
├─ Protocol: TCP
├─ Port Range: 443-443
├─ Destination: 0.0.0.0/0 (to anywhere)
└─ Action: ALLOW

Rule #120: Allow SSH (port 22)
├─ Protocol: TCP
├─ Port Range: 22-22
├─ Destination: 10.0.0.0/16 (to VPC only - bastion)
└─ Action: ALLOW

Rule #130: Allow Ephemeral Responses (1024-65535)
├─ Protocol: TCP
├─ Port Range: 1024-65535
├─ Destination: 0.0.0.0/0 (to anywhere)
└─ Action: ALLOW
   Note: Servers respond ON random high ports

Rule #32767: Deny All (catch-all default)
├─ Protocol: All
├─ Port: All
└─ Action: DENY
```

#### Why You Need All 4 Rules (Not Just 2)

```
Misconception: "Just allow port 80, that's it!"

❌ WRONG - Only 2 rules (incomplete):
├─ INGRESS #100: Allow TCP 80 from 0.0.0.0/0
└─ EGRESS #100: Allow TCP 80 to 0.0.0.0/0
   Problem: Clients can't receive responses on ephemeral ports!

✅ CORRECT - 4 rules (complete):
├─ INGRESS #100: Allow TCP 80 (requests come in)
├─ INGRESS #130: Allow TCP 1024-65535 (client ACKs/responses)
├─ EGRESS #100: Allow TCP 80 (server responds to port 80)
└─ EGRESS #130: Allow TCP 1024-65535 (server responses on ephemeral)

Why? Because of stateless traffic flow:

Request: Client:54321 → Server:80 (uses high port on client side)
         INGRESS #100 allows this ✅

Response: Server:80 → Client:54321 (goes back to high port)
          EGRESS #130 allows this ✅

ACK from Client: Client:54321 → Server:80 (sends ACK on high port)
                 INGRESS #130 allows this ✅
```

#### Real-World Scenario: Why Databases Need Both Directions

```
Example: Web Server (10.0.1.0/24) needs to connect to Database (10.0.3.0/24)

Web Server needs BOTH:

EGRESS (Web Server sending):
├─ Rule #100: Allow TCP 5432 TO 10.0.3.0/24
│  └─ Web server initiates connection to database
│
└─ Rule #110: Allow TCP 1024-65535 TO 10.0.3.0/24
   └─ Web server uses random high port for connection

INGRESS (Web Server receiving):
├─ Rule #100: Allow TCP 5432 FROM 10.0.3.0/24
│  └─ Database responses on port 5432
│
└─ Rule #110: Allow TCP 1024-65535 FROM 10.0.3.0/24
   └─ Database responses on web server's high port

All 4 rules REQUIRED!
Without them, database connection fails.
```

#### NACL Rules Summary (Always 4 for bidirectional traffic)

| Direction | Port | Rule Type | Source/Dest | Purpose |
|-----------|------|-----------|---|---|
| **Inbound** | 80 | INGRESS | 0.0.0.0/0 | Client request comes IN on port 80 |
| **Inbound** | 1024-65535 | INGRESS | 0.0.0.0/0 | Client response comes IN on high port |
| **Outbound** | 80 | EGRESS | 0.0.0.0/0 | Server response goes OUT on port 80 |
| **Outbound** | 1024-65535 | EGRESS | 0.0.0.0/0 | Server response goes OUT on high port |

---

### Multiple NACLs Per VPC (Advanced)

**Key Concept**: You can have **many NACLs in one VPC**. Each subnet associates with ONE NACL, but multiple subnets can
share the same NACL.

```
VPC with 10 subnets = Can have 1-10 NACLs

Option A: Single NACL (Simple)
└─ All 10 subnets → 1 NACL (default behavior)

Option B: Multiple NACLs (Recommended for Production)
├─ NACL-Web (web tier rules)
│  ├─ Public Subnet-1 → NACL-Web
│  ├─ Public Subnet-2 → NACL-Web
│  └─ Public Subnet-3 → NACL-Web
│
└─ NACL-Database (database tier rules)
   ├─ Private Subnet-1 → NACL-Database
   ├─ Private Subnet-2 → NACL-Database
   ├─ Private Subnet-3 → NACL-Database
   ├─ Private Subnet-4 → NACL-Database
   ├─ Private Subnet-5 → NACL-Database
   ├─ Private Subnet-6 → NACL-Database
   └─ Private Subnet-7 → NACL-Database
```

### Why Use Multiple NACLs?

**Reason 1: Different Security Requirements**

```
Web Tier (Public):
├─ Allow: HTTP (80), HTTPS (443) from internet
├─ Allow: SSH (22) from office IP
└─ Allow: ephemeral responses

Database Tier (Private):
├─ Allow: MySQL (3306) from web tier only
├─ DENY: SSH (no direct access)
├─ DENY: HTTP/HTTPS (not a web server)
└─ Deny: from internet (completely private)
```

**Reason 2: Easier Maintenance**

```
❌ One NACL with 20 rules (confusing):
├─ Rule #100: Allow port 80 (web)
├─ Rule #110: Allow port 443 (web)
├─ Rule #120: Allow port 22 (web SSH)
├─ Rule #130: Allow port 3306 (database MySQL)
├─ Rule #140: Allow port 6379 (cache Redis)
├─ ... 15 more rules jumbled together

✅ Two NACLs (clear separation):

NACL-Web:
├─ Rule #100: Allow port 80
├─ Rule #110: Allow port 443
└─ Rule #120: Allow port 22

NACL-Database:
├─ Rule #100: Allow port 3306
└─ Rule #110: Allow port 6379
```

### Example: 3 Web + 7 Database Subnets

**Visual: Your Building with Two NACL Security Checkpoints**

```
                    AWS Compound
                         │
                         ↓
        ┌────────────────────────────┐
        │      VPC Building           │
        │      (10.0.0.0/16)          │
        │                            │
        │  ┌──────────────────────┐  │
        │  │  BUILDING SECTION 1  │  │
        │  │  *** NACL-Web ***    │  │
        │  │ Security Checkpoint  │  │
        │  │ (Allows public)       │  │
        │  │                      │  │
        │  │ Room 1: Public S1    │  │
        │  │ └─ Web Server-1      │  │
        │  │   • Allows HTTP(80)  │  │
        │  │   • Allows HTTPS(443)│  │
        │  │   • Allows SSH(22)   │  │
        │  │   • SG: Web-SG       │  │
        │  │                      │  │
        │  │ Room 2: Public S2    │  │
        │  │ └─ Web Server-2      │  │
        │  │   • Same rules       │  │
        │  │   • SG: Web-SG       │  │
        │  │                      │  │
        │  │ Room 3: Public S3    │  │
        │  │ └─ Load Balancer     │  │
        │  │   • Same rules       │  │
        │  │   • SG: Web-SG       │  │
        │  │                      │  │
        │  └──────────────────────┘  │
        │           ↓ (internal)      │
        │  ┌──────────────────────┐  │
        │  │  BUILDING SECTION 2  │  │
        │  │  *** NACL-Database **│  │
        │  │ Security Checkpoint  │  │
        │  │ (Allows DB tier only)│  │
        │  │                      │  │
        │  │ Room 4: Private S1   │  │
        │  │ └─ RDS MySQL (Master)│  │
        │  │   • Allows MySQL(3306)  │
        │  │   • From 10.0.1-3 only  │
        │  │   • SG: DB-SG        │  │
        │  │                      │  │
        │  │ Room 5: Private S2   │  │
        │  │ └─ RDS MySQL (Replica) │
        │  │   • Same rules       │  │
        │  │   • SG: DB-SG        │  │
        │  │                      │  │
        │  │ Room 6: Private S3   │  │
        │  │ └─ ElastiCache Redis │  │
        │  │   • Allows Redis(6379)  │
        │  │   • From web tier only  │
        │  │   • SG: Cache-SG     │  │
        │  │                      │  │
        │  │ Room 7-10: Private S4-7 │
        │  │ └─ App Servers, EFS  │  │
        │  │   • Internal traffic │  │
        │  │   • SG: App-SG       │  │
        │  │                      │  │
        │  └──────────────────────┘  │
        │                            │
        └────────────────────────────┘
```

**Real VPC Architecture (with IP ranges):**

```
                        INTERNET
                             │
                             ↓
                    ┌─────────────────┐
                    │ Internet Gateway │
                    └─────────────────┘
                             │
                    ┌────────┴────────┐
                    ↓                 ↓
            ┌──────────────┐   ┌──────────────┐
            │  NACL-Web    │   │ NACL-Web     │
            │  Checkpoint  │   │ Checkpoint   │
            └──────┬───────┘   └──────┬───────┘
                   ↓                  ↓
        ┌──────────────────────────────────────┐
        │ Public Subnet-1     Public Subnet-2  │
        │ 10.0.1.0/24         10.0.2.0/24      │
        │ ┌──────────────┐   ┌──────────────┐  │
        │ │ Web-SG:      │   │ Web-SG:      │  │
        │ │ - HTTP (80)  │   │ - HTTP (80)  │  │
        │ │ - HTTPS(443) │   │ - HTTPS(443) │  │
        │ │ - SSH (22)   │   │ - SSH (22)   │  │
        │ │              │   │              │  │
        │ │ EC2-1        │   │ EC2-2        │  │
        │ └──────────────┘   └──────────────┘  │
        └──────────────────────────────────────┘
                             │
                             ↓ (VPC internal traffic)
        ┌──────────────────────────────────────┐
        │         NACL-Database Checkpoint      │
        │    (Allows DB tier traffic only)      │
        └──────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ Private S-1 │   │ Private S-2 │   │ Private S-3 │
   │ 10.0.10/24  │   │ 10.0.11/24  │   │ 10.0.12/24  │
   │ ┌─────────┐ │   │ ┌─────────┐ │   │ ┌─────────┐ │
   │ │ DB-SG:  │ │   │ │ DB-SG:  │ │   │ │Cache-SG:│ │
   │ │ MySQL   │ │   │ │ MySQL   │ │   │ │ Redis   │ │
   │ │ 3306    │ │   │ │ 3306    │ │   │ │ 6379    │ │
   │ │         │ │   │ │         │ │   │ │         │ │
   │ │RDS-M    │ │   │ │RDS-R    │ │   │ │Redis    │ │
   │ └─────────┘ │   │ └─────────┘ │   │ └─────────┘ │
   └─────────────┘   └─────────────┘   └─────────────┘
        │                   │                  │
        │                   │    ┌─────────────┘
        │                   ↓    ↓
        │           ┌──────────────────┐
        │           │ Private S-4      │
        │           │ 10.0.13/24       │
        │           │ ┌──────────────┐ │
        │           │ │ App-SG:      │ │
        │           │ │ Internal     │ │
        │           │ │ traffic only │ │
        │           │ │              │ │
        │           │ │App Server    │ │
        │           │ └──────────────┘ │
        │           └──────────────────┘
        │
        └─────────────────────────────────────────────────────────┐
                                                                  │
    [Private S-5, S-6, S-7 with same NACL-Database rules]        │
                                                                  │
                  (All have same NACL-Database)                   │
                  (All have different SGs for their purpose)      │
```

**Key Rules for Each NACL:**

```
┌─────────────────────────────────────────────────────────┐
│ NACL-Web (3 Public Subnets)                             │
├─────────────────────────────────────────────────────────┤
│ Inbound Rules:                                          │
│ #100: Allow TCP port 80    from 0.0.0.0/0 (HTTP)      │
│ #110: Allow TCP port 443   from 0.0.0.0/0 (HTTPS)     │
│ #120: Allow TCP port 22    from 10.0.0.0/8 (SSH)      │
│ #130: Allow TCP 1024-65535 from 0.0.0.0/0 (ephemeral) │
│ #32767: DENY all (implicit, catch-all)                 │
│                                                         │
│ Outbound Rules:                                         │
│ #100: Allow TCP 1-65535 to 0.0.0.0/0 (all responses)  │
│ #32767: DENY all (implicit)                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ NACL-Database (7 Private Subnets)                       │
├─────────────────────────────────────────────────────────┤
│ Inbound Rules:                                          │
│ #100: Allow TCP 3306      from 10.0.1.0/24 (MySQL)    │
│ #110: Allow TCP 3306      from 10.0.2.0/24 (MySQL)    │
│ #120: Allow TCP 3306      from 10.0.3.0/24 (MySQL)    │
│ #130: Allow TCP 6379      from 10.0.1.0/24 (Redis)    │
│ #140: Allow TCP 1024-65535 from 10.0.0.0/16 (respons) │
│ #32767: DENY all (implicit, catch-all)                 │
│                                                         │
│ Outbound Rules:                                         │
│ #100: Allow TCP 1-65535 to 10.0.0.0/16 (to web tier)  │
│ #32767: DENY all (implicit)                            │
└─────────────────────────────────────────────────────────┘
```

**Architecture:**

### How to Create Multiple NACLs

**Step 1: Create NACL-Web**

```bash
aws ec2 create-network-acl --vpc-id vpc-0123456789abcdef0
# Returns: nacl-web000000000

# Add inbound rules
aws ec2 create-network-acl-entry \
  --network-acl-id nacl-web000000000 \
  --rule-number 100 \
  --protocol tcp \
  --port-range FromPort=80,ToPort=80 \
  --cidr-block 0.0.0.0/0 \
  --ingress

aws ec2 create-network-acl-entry \
  --network-acl-id nacl-web000000000 \
  --rule-number 110 \
  --protocol tcp \
  --port-range FromPort=443,ToPort=443 \
  --cidr-block 0.0.0.0/0 \
  --ingress
```

**Step 2: Associate NACL-Web with 3 Public Subnets**

```bash
aws ec2 associate-network-acl \
  --network-acl-id nacl-web000000000 \
  --subnet-id subnet-public-1

aws ec2 associate-network-acl \
  --network-acl-id nacl-web000000000 \
  --subnet-id subnet-public-2

aws ec2 associate-network-acl \
  --network-acl-id nacl-web000000000 \
  --subnet-id subnet-public-3
```

**Step 3: Create NACL-Database**

```bash
aws ec2 create-network-acl --vpc-id vpc-0123456789abcdef0
# Returns: nacl-db0000000000

# Allow MySQL from web tier only
aws ec2 create-network-acl-entry \
  --network-acl-id nacl-db0000000000 \
  --rule-number 100 \
  --protocol tcp \
  --port-range FromPort=3306,ToPort=3306 \
  --cidr-block 10.0.1.0/24 \
  --ingress
```

**Step 4: Associate NACL-Database with 7 Private Subnets**

```bash
aws ec2 associate-network-acl \
  --network-acl-id nacl-db0000000000 \
  --subnet-id subnet-private-1

# ... repeat for remaining 6 private subnets
```

### Traffic Flow with Multiple NACLs

```
Client Request (port 80)
    ↓
Internet Gateway
    ↓
NACL-Web (Allows port 80) ✅ Passes
    ↓
Security Group (Allows port 80) ✅ Passes
    ↓
Web Server (EC2)
    ↓
Wants to query database (port 3306)
    ↓
Traffic stays within VPC
    ↓
NACL-Database (Allows 3306 from 10.0.1.0/24) ✅ Passes
    ↓
Security Group (Allows 3306 from web SG) ✅ Passes
    ↓
Database (RDS MySQL)
```

### Best Practices for Multiple NACLs

```
✅ DO:
☐ Create separate NACLs per tier (web, app, database, cache)
☐ Name them clearly: NACL-Web, NACL-AppServer, NACL-Database
☐ Use consistent rule numbering: 100, 110, 120, 130...
☐ Document each NACL's purpose
☐ Keep rules simple (5-15 per NACL)
☐ Group related subnets in same NACL
☐ Tag NACLs for easy identification

❌ DON'T:
☐ Create one NACL per subnet (unmanageable)
☐ Mix web + database rules in same NACL
☐ Have more than 5 NACLs per VPC (overcomplicated)
☐ Leave default NACL "allow all" if not used
☐ Forget outbound rules (stateless!)
☐ Use overlapping rule numbers
```

---

## Advanced Scenarios

### Traffic Flow Through VPC

When traffic enters your VPC, it follows this path:

```
Internet Traffic
      ↓
Internet Gateway
      ↓
Route Table (decides where to send traffic)
      ↓
Network ACL (subnet-level firewall)
      ↓
Security Group (instance-level firewall)
      ↓
Instance
```

**Each step must allow traffic or it stops!**

---

## VPC with Public Subnet (Internet-Accessible)

### Use Case

Web servers that need to be accessible from the internet

### Architecture

![image](https://user-images.githubusercontent.com/52529498/125168074-9dcddb00-e171-11eb-8e92-4c8f0a7ef92b.png)

### Key Components

1. **Internet Gateway (IGW)**
    - Attached to VPC
    - Enables communication between VPC and internet

2. **Public Subnet**
    - Instances get public IP addresses
    - Route table includes route to IGW (0.0.0.0/0 → IGW)

3. **Security Group**
    - Inbound rules allow HTTP (80), HTTPS (443)
    - SSH (22) restricted to your IP (not 0.0.0.0/0!)

4. **NACL**
    - Default allows all traffic (if using default NACL)
    - Custom NACL: explicitly allow needed ports

### Setup Steps (Beginner)

```bash
# 1. Create VPC with public subnet
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# 2. Create subnet
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24

# 3. Create and attach Internet Gateway
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --internet-gateway-id igw-xxx --vpc-id vpc-xxx

# 4. Create route table
aws ec2 create-route-table --vpc-id vpc-xxx

# 5. Add route to IGW
aws ec2 create-route --route-table-id rtb-xxx \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-xxx

# 6. Associate subnet with route table
aws ec2 associate-route-table --subnet-id subnet-xxx --route-table-id rtb-xxx
```

### Security Considerations

⚠️ **Danger**: Don't open SSH to 0.0.0.0/0 (the entire internet)

```
❌ DON'T:
Port 22 (SSH): Source 0.0.0.0/0

✅ DO:
Port 22 (SSH): Source YOUR_IP/32
```

---

## VPC with Public AND Private Subnets (Standard Production)

### Use Case

Real-world applications with multiple tiers

- **Public subnet**: Web servers (ALB)
- **Private subnet**: Application servers + Databases

### Architecture

![image](https://user-images.githubusercontent.com/52529498/125170306-7e887b00-e17c-11eb-94ba-81134d2cee4a.png)

### Key Components

**Public Subnet**

- Route table with route to Internet Gateway
- Instances can receive traffic from internet
- Bastion host for SSH access to private instances

**Private Subnet**

- NO route to Internet Gateway (isolated from internet)
- Instances have only private IPs
- Cannot be accessed directly from internet
- **Protected**: no direct internet access = no direct attack vector

### How to Access Private Instances

**Option 1: Bastion Host (Jump Box)**

```
You (on internet)
    ↓ SSH to Bastion (public)
Bastion Host
    ↓ SSH to Private Server
Private Server (database, app)
```

**Setup**:

```bash
# 1. SSH to Bastion with your SSH key
ssh -i mykey.pem ec2-user@bastion-public-ip

# 2. From Bastion, SSH to private instance
ssh -i mykey.pem ec2-user@private-instance-private-ip
```

**Option 2: AWS Systems Manager Session Manager (Easier)**

```bash
# No need for SSH keys or Bastion!
aws ssm start-session --target i-1234567890abcdef0
```

### Accessing Internet from Private Subnet

**Problem**: Private instances need to download patches/software

**Solution: NAT Gateway**

```
Private Instance
    ↓
NAT Gateway (in public subnet)
    ↓ (translates source IP)
Internet
    ↓ (response returns to NAT Gateway)
NAT Gateway
    ↓
Private Instance
```

**Key fact**: NAT Gateway is **one-way**:

- ✅ Private instances CAN reach internet
- ❌ Internet CANNOT reach private instances

**Cost**: You pay per data processed (not included in free tier)

### Setup (Intermediate)

```bash
# 1. Allocate Elastic IP (needed for NAT Gateway)
aws ec2 allocate-address --domain vpc

# 2. Create NAT Gateway in public subnet
aws ec2 create-nat-gateway \
  --subnet-id subnet-public \
  --allocation-id eipalloc-xxx

# 3. Create route in private subnet's route table
aws ec2 create-route --route-table-id rtb-private \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id nat-xxx
```

### Private Subnet Traffic Flow

```
Private Instance wants to reach internet
    ↓
Checks local route table
    ↓
Finds route: 0.0.0.0/0 → NAT Gateway
    ↓
Sends to NAT Gateway (public subnet)
    ↓
NAT translates source IP
    ↓
Sends to Internet Gateway
    ↓
Reaches internet
```

### Security Benefits

✅ Database servers are completely hidden
✅ Only web servers exposed to internet
✅ Additional layer of protection
✅ Follows principle of least privilege
✅ Application servers protected from direct attacks

---

## Advanced Scenarios

### Scenario 1: On-Premises Connection (VPN)

**Use case**: Company wants to extend office network to AWS

```
On-Premises Office Network
    ↓
Customer Gateway (your side)
    ↓ VPN Connection (encrypted tunnel)
VPN Gateway (AWS side)
    ↓
Private Subnet in AWS

Result: AWS looks like another office building!
```

**Benefits:**

- ✅ Access private instances with internal IPs
- ✅ No Bastion host needed
- ✅ Encrypted tunnel
- ✅ More convenient than internet access

### Scenario 2: Multi-Region Deployment

**Use case**: Disaster recovery, high availability across regions

```
Region us-east-1:
├─ VPC-1 with subnets
├─ EC2 instances, RDS database
└─ Route53 health check

        ↕ (replication)

Region us-west-2:
├─ VPC-2 with subnets
├─ EC2 instances, RDS replica
└─ Route53 failover

If us-east-1 fails → Traffic routes to us-west-2
```

### Scenario 3: VPC Peering

**Use case**: Two VPCs need to communicate privately

```
VPC-A (172.31.0.0/16)
    ↓
VPC Peering Connection
    ↓
VPC-B (10.0.0.0/16)

Now instances in VPC-A can reach instances in VPC-B using private IPs!
``` 

---

## Default VPC Deep Dive

### Default VPC Configuration

**CIDR Block: 172.31.0.0/16**

This provides:

- 65,536 total IP addresses
- Subnets: 172.31.0.0/20, 172.31.16.0/20, 172.31.32.0/20, etc.
- Each subnet: 4,096+ addresses

### Visual: Default VPC Structure

![image](https://user-images.githubusercontent.com/52529498/137606958-956256de-0ccc-410b-82d7-e3ec6ae49b3b.png)

### Default VPC Across All Availability Zones

![image](https://user-images.githubusercontent.com/52529498/137607039-4ec285b8-0ef7-4841-8241-3c8e6f73418a.png)

### Key Points About Default VPC

**One subnet per AZ**:

- If region has 6 AZs, default VPC gets 6 subnets
- Each in different AZ (for high availability)

**Same Route Table ID as VPC ID**: (visible in AWS console - AWS optimization)

**Pre-configured for internet access**:

- ✅ Internet Gateway attached
- ✅ Route table points to IGW
- ✅ All subnets are public
- ✅ DHCP enabled

### When to Delete Default VPC

**Delete it if:**

- You need custom network ranges
- You need private subnets in your VPC
- You want specific security controls
- Building production infrastructure

**How to recreate:**

```bash
# AWS console: VPC → Actions → Create default VPC
# OR use AWS CLI:
aws ec2 create-default-vpc
```

---


---

## AWS Services and VPC

### Services That Require VPC

Some AWS services **MUST be launched in a VPC** (no choice):

| Service                       | Must be in VPC            | Notes                  |
|-------------------------------|---------------------------|------------------------|
| **EC2 instances**             | ✅ Yes                     | Always launched in VPC |
| **RDS databases**             | ✅ Yes (for best practice) | Multi-AZ needs subnets |
| **ElastiCache**               | ✅ Yes                     | In-memory database     |
| **Elastic File System (EFS)** | ✅ Yes                     | Shared storage         |
| **Internal Load Balancers**   | ✅ Yes                     | For internal routing   |
| **Network Load Balancer**     | ✅ Yes                     | For Layer 4 routing    |

### Services That Are Internet-Accessible by Default

These services are public-facing and accessible from internet:

- S3 (but can restrict to VPC endpoints)
- CloudFront (CDN)
- API Gateway (but can add VPC endpoints)
- Cognito
- Route53

### Lambda and VPC (Important!)

**By default**: Lambda functions are **NOT in a VPC**

- ✅ Can reach internet
- ❌ Cannot reach private RDS, ElastiCache, private subnets
- This is intentional (simplicity)

**When Lambda needs VPC access**:

```
Database or service is in private subnet
    ↓
Lambda needs to reach it
    ↓
Must configure Lambda for VPC:
  1. Assign VPC
  2. Select subnets (private)
  3. Assign security group
    ↓
Now Lambda can reach private services!
```

**Tradeoff**: Lambda in VPC has:

- ✅ Access to private resources
- ❌ Slower cold start
- ❌ Needs NAT Gateway to reach internet
- ❌ More configuration

### VPC Endpoints (Advanced)

**Use case**: Access AWS services from private subnets without NAT Gateway

```
Private Subnet
    ↓
VPC Endpoint (gateway endpoint)
    ↓
S3 / DynamoDB
```

**Benefits**:

- ✅ No NAT Gateway cost
- ✅ No internet traffic
- ✅ Private access to AWS services
- ✅ Better security

**Services supporting VPC endpoints**:

- S3 (gateway endpoint)
- DynamoDB (gateway endpoint)
- API Gateway (interface endpoint)
- Athena
- CodeBuild
- CodePipeline
- SNS, SQS
- And many more...

**Cost**: Usually free for gateway endpoints, small charge for interface endpoints

---

## Best Practices

### 1. Security Best Practices

```
☐ Use custom VPCs for production
☐ Never use default VPC for sensitive data
☐ Public subnets: only web tier
☐ Private subnets: database, cache, internal services
☐ Enable VPC Flow Logs (for auditing)
☐ Use security groups restrictively
☐ Review NACL rules regularly
☐ Use Network Firewall for advanced threat protection
☐ Implement least privilege principle
☐ Use AWS Config to monitor compliance
```

### 2. Network Architecture Best Practices

```
☐ Use multi-AZ subnets (high availability)
☐ Use appropriate subnet sizes (don't run out of IPs)
☐ Document CIDR blocks clearly
☐ Avoid overlapping CIDR blocks (important for VPC peering)
☐ Use VPC peering or AWS Transit Gateway for multi-VPC
☐ Segregate tiers (web/app/db)
☐ Use NAT Gateways in public subnets (not EC2)
☐ Enable DHCP option sets
☐ Monitor NAT Gateway data processing (costs!)
```

### 3. Operational Best Practices

```
☐ Use CloudWatch for VPC Flow Logs
☐ Monitor VPC peering connections
☐ Use VPC console for visualization
☐ Tag all resources (for cost allocation)
☐ Use route tables naming conventions
☐ Document network diagram
☐ Plan for growth (CIDR expansion)
☐ Regular security audits
☐ Use Systems Manager to access private instances
☐ Enable enhanced monitoring
```

### 4. Cost Optimization

```
☐ Use NAT Gateway only when needed
☐ Consider VPC endpoints instead of NAT (for S3/DynamoDB)
☐ Right-size NAT Gateway (consider availability vs cost)
☐ Use free tier default VPC for dev/test
☐ Monitor data transfer costs
☐ Delete unused resources
☐ Use CloudFormation for infrastructure as code
☐ Monitor reserved capacity
```

---

## Troubleshooting

### Problem: EC2 Can't Reach Internet

**Check list:**

```
1. Does instance have public IP?
   aws ec2 describe-instances --instance-ids i-xxx
   → Look for PublicIpAddress

2. Is subnet public?
   aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-xxx
   → Should have route: 0.0.0.0/0 to Internet Gateway

3. Is Internet Gateway attached to VPC?
   aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=vpc-xxx
   → Should show attached status

4. Is Security Group allowing outbound?
   aws ec2 describe-security-groups --group-ids sg-xxx
   → Check egress rules (should have 0.0.0.0/0 by default)

5. Is NACL allowing traffic?
   aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-xxx
   → Check inbound/outbound rules
```

### Problem: Can't SSH to EC2 in Private Subnet

**Solution 1: Use Bastion Host**

```bash
# SSH to Bastion first
ssh -i key.pem ec2-user@bastion-public-ip

# From Bastion, SSH to private instance
ssh -i key.pem ec2-user@private-instance-ip
```

**Solution 2: Use AWS Systems Manager**

```bash
# Requires: IAM role with SSM permissions
aws ssm start-session --target i-xxxxx
# No key needed!
```

**Solution 3: Add public IP**

```bash
# Stop instance, detach primary ENI
# Attach to public subnet, then reconnect
# (temporary, not recommended)
```

### Problem: Private Subnet Can't Access Internet

**Check list:**

```
1. Does private route table have NAT Gateway route?
   Route: 0.0.0.0/0 → NAT Gateway

2. Is NAT Gateway in public subnet?
   (Must be in public subnet to work!)

3. Does NAT Gateway have Elastic IP?
   aws ec2 describe-nat-gateways --nat-gateway-ids nat-xxx

4. Is instance's security group allowing outbound?
   Check egress rules

5. Check VPC Flow Logs for traffic:
   aws ec2 describe-flow-logs
```

### Problem: VPC Peering Not Working

**Check list:**

```
1. Is peering connection accepted?
   aws ec2 describe-vpc-peering-connections
   → Status should be "active"

2. Are route tables configured?
   VPC-A route table: 10.0.0.0/16 → peering connection
   VPC-B route table: 172.31.0.0/16 → peering connection

3. Are security groups allowing traffic?
   Source/destination security groups must allow

4. Are CIDR blocks overlapping?
   If yes, peering won't work

5. Are subnets associated correctly?
   Use describe-route-table-associations
```

### Problem: DNS Names Not Resolving in VPC

**Causes:**

- DNS resolution disabled in VPC
- DHCP options set not configured
- Route53 private hosted zone not set up

**Fix:**

```bash
# 1. Enable DNS in VPC
aws ec2 modify-vpc-attribute --vpc-id vpc-xxx \
  --enable-dns-hostnames

# 2. Check DHCP options set
aws ec2 describe-dhcp-options-sets

# 3. Use Route53 private hosted zone (advanced)
```

---

## Real-World Scenarios

### Scenario 1: E-Commerce Application

```
Web Tier (Public Subnets - Multi-AZ):
├─ Application Load Balancer
├─ EC2 web servers (auto-scaling)
└─ Route53 for DNS

App Tier (Private Subnets - Multi-AZ):
├─ EC2 application servers
├─ NAT Gateway for outbound internet
└─ CloudWatch monitoring

Database Tier (Private Subnets - Multi-AZ):
├─ RDS MySQL (multi-AZ)
├─ ElastiCache Redis
└─ EFS for shared files

Security:
├─ Security Groups: ALB → Web → App → DB
├─ NACLs: Deny suspicious IPs at subnet level
├─ VPC Flow Logs: Monitor all traffic
└─ CloudTrail: API audit trail
```

### Scenario 2: Hybrid Cloud (On-Premises + AWS)

```
On-Premises Data Center
├─ Employees
├─ Databases (legacy)
└─ Internal services
    ↓ (VPN Connection)
AWS VPC (Private Subnets)
├─ Application servers
├─ Can access on-prem databases
└─ Secure tunnel (encrypted)

Result: Seamless integration!
```

### Scenario 3: Multi-Environment Setup

```
Dev Environment (Single AZ):
├─ VPC: 10.1.0.0/16
├─ Public subnet: 10.1.1.0/24
├─ Private subnet: 10.1.2.0/24
└─ Cost optimized

Staging Environment (Multi-AZ):
├─ VPC: 10.2.0.0/16
├─ Public subnets: 10.2.1.0/24, 10.2.2.0/24
├─ Private subnets: 10.2.3.0/24, 10.2.4.0/24
└─ HA configured

Production Environment (Multi-AZ + Multi-Region):
├─ VPC: 10.3.0.0/16
├─ Multiple AZs per region
├─ RDS multi-AZ
├─ Backup region VPC: 10.3.0.0/16 (different region)
└─ Maximum resilience

VPC Peering: Dev ↔ Staging ↔ Production (controlled)
```

---

## Key Takeaways

✅ **VPC is your network foundation** - Master it for AWS success
✅ **Defaults work, but customize for production**
✅ **Public + Private = industry standard**
✅ **Multi-AZ = high availability**
✅ **Security Groups + NACL = defense in depth**
✅ **NAT Gateway = private internet access**
✅ **VPC Endpoints = cheaper than NAT**
✅ **Always: least privilege principle**
✅ **Monitor: VPC Flow Logs**
✅ **Document: network architecture**

---

## References and Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [VPC Subnets Guide](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html)
- [NACL vs Security Groups](https://www.knowledgehut.com/tutorials/aws/nacl-vs-security-groups)
- [VPC Endpoints](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/centralized-access-to-vpc-private-endpoints.html)
- [AWS VPC FAQs](https://aws.amazon.com/vpc/faqs/)
- [CIDR Notation Explained](http://cidr.xyz)
- [Regions and Availability Zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones)
- [Default VPC Details](https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html)

---

**Last Updated**: 2024

**Notes**

- https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
- https://aws.amazon.com/vpc/faqs/
- http://cidr.xyz
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones
- https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html





