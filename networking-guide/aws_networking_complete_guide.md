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

Think of AWS networking like **building a city**:

```
PHYSICAL CITY ANALOGY
├─ City Planning Department = AWS Account
│  └─ Manages all cities
│
├─ Your City = VPC
│  └─ Your isolated region (10.0.0.0/16)
│
├─ Neighborhoods = Subnets
│  ├─ North Side (Public) - 10.0.1.0/24
│  │  └─ Faces the highway (internet)
│  │  └─ Houses have address signs (public IPs)
│  │
│  └─ South Side (Private) - 10.0.2.0/24
│     └─ Hidden from highway
│     └─ No address signs visible (no public IPs)
│
├─ Security Guard at Each House = Security Group
│  └─ "Only let in people from 0.0.0.0/0 on port 80"
│  └─ "No port 3306 allowed"
│
├─ City Gates = NACLs
│  └─ "Check everyone entering the North Side neighborhood"
│  └─ Stateless (check both directions)
│
├─ Highway Entrance = Internet Gateway
│  └─ Main road into your city
│
├─ Back Door = NAT Gateway
│  └─ Private residents can leave, but no one can find them
│
└─ Secret Tunnels = VPC Endpoints
   └─ Direct private pipes to AWS services (S3, DynamoDB)
```

**Key Mental Model:**
- AWS Account = City planning (owns multiple cities)
- VPC = Your city (isolated, controlled)
- Subnets = Neighborhoods (public-facing or hidden)
- Security Groups = House bouncers (per-instance control)
- NACLs = Neighborhood gates (per-subnet control)
- IGW = Highway to world
- NAT = Private exit door
- VPC Endpoints = Direct tunnels to AWS services

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

### 4. VPC Endpoints

**Purpose:** Private connection to AWS services (no internet)

**Two types:**

**Gateway Endpoints** (S3, DynamoDB):
```
EC2 → S3 (no internet needed)
├─ ✓ FREE
├─ ✓ No NAT costs
└─ ✓ Faster
```

**Interface Endpoints** (100+ services):
```
EC2 → Lambda (via ENI)
├─ ✓ Works for any service
├─ ✓ Private connection
├─ ✗ Small cost
└─ ✓ More flexible
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
