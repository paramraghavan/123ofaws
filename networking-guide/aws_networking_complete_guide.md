# AWS Networking Complete Guide

**A Comprehensive Educational Resource for Learning AWS Network Architecture**

---

## Table of Contents

1. [Introduction](#introduction)
2. [VPC Basics](#vpc-basics)
3. [Subnets](#subnets)
4. [Security Groups](#security-groups)
5. [Network ACLs (NACLs)](#network-acls)
6. [Private Endpoints](#private-endpoints)
7. [Complete Architecture](#complete-architecture)
8. [Hands-On Exercises](#hands-on-exercises)
9. [Common Patterns](#common-patterns)

---

## Introduction

### What is AWS Networking?

AWS Networking allows you to:
- Create isolated networks (VPCs)
- Control network traffic
- Secure your resources
- Connect different parts of your infrastructure

Think of it like building a city:
- **VPC** = The entire city
- **Subnets** = Neighborhoods in the city
- **Security Groups** = Locks on individual houses
- **NACLs** = Gates that control who can enter neighborhoods
- **Private Endpoints** = Secret tunnels for private communication

---

## VPC Basics

### What is a VPC?

A **Virtual Private Cloud (VPC)** is your own isolated network in AWS. It's like renting a private apartment building in AWS where you control everything.

```
┌─────────────────────────────────────────────────────────────┐
│                          AWS REGION                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                        YOUR VPC                          ││
│  │  10.0.0.0/16 (65,536 IP addresses)                      ││
│  │                                                           ││
│  │  ┌──────────────────────┐  ┌──────────────────────┐    ││
│  │  │    Public Subnet     │  │   Private Subnet     │    ││
│  │  │   10.0.1.0/24        │  │   10.0.2.0/24        │    ││
│  │  │  (256 addresses)     │  │  (256 addresses)     │    ││
│  │  │                      │  │                      │    ││
│  │  │  ┌──────────────┐   │  │  ┌──────────────┐   │    ││
│  │  │  │  EC2 Instance│   │  │  │  EC2 Instance│   │    ││
│  │  │  │  (Has Public)│   │  │  │(No Public IP)│   │    ││
│  │  │  └──────────────┘   │  │  └──────────────┘   │    ││
│  │  │                      │  │                      │    ││
│  │  └──────────────────────┘  └──────────────────────┘    ││
│  │                                                           ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### VPC Key Concepts

| Concept | What It Does | Example |
|---------|-------------|---------|
| **CIDR Block** | Defines IP address range | 10.0.0.0/16 = 65,536 addresses |
| **Internet Gateway** | Connects VPC to internet | Allows EC2 to access Google.com |
| **Route Table** | Directs traffic to destinations | "Send traffic to 10.0.0.0/16 internally" |
| **NAT Gateway** | Hides private IPs from internet | Private EC2 can download updates |

### VPC IP Addresses Explained

```
VPC CIDR: 10.0.0.0/16

The "/16" means:
- First 16 bits are fixed: 10.0
- Last 16 bits can vary: 0.0 to 255.255
- Total addresses: 2^16 = 65,536

Example addresses in this VPC:
10.0.0.0     (Network address - reserved)
10.0.0.1     (VPC router - reserved)
10.0.0.2     (DNS server - reserved)
10.0.0.3     (Reserved for future use)
10.0.0.4     (First available for EC2)
...
10.0.1.100   (Public subnet - can have public IP)
10.0.2.50    (Private subnet - no public IP)
...
10.0.255.255 (Broadcast - reserved)
```

---

## Subnets

### What is a Subnet?

A **Subnet** is a smaller network inside your VPC. Like dividing your city into neighborhoods.

```
                    VPC: 10.0.0.0/16
        ┌───────────────────────────────────┐
        │                                   │
        │    ┌──────────────────────────┐   │
        │    │  Public Subnet 1         │   │
        │    │  10.0.1.0/24             │   │
        │    │  Availability Zone: us-  │   │
        │    │  east-1a                 │   │
        │    │  256 addresses           │   │
        │    │  (10.0.1.0 - 10.0.1.255)│   │
        │    └──────────────────────────┘   │
        │                                   │
        │    ┌──────────────────────────┐   │
        │    │  Public Subnet 2         │   │
        │    │  10.0.2.0/24             │   │
        │    │  Availability Zone: us-  │   │
        │    │  east-1b                 │   │
        │    │  256 addresses           │   │
        │    │  (10.0.2.0 - 10.0.2.255) │   │
        │    └──────────────────────────┘   │
        │                                   │
        │    ┌──────────────────────────┐   │
        │    │  Private Subnet 1        │   │
        │    │  10.0.11.0/24            │   │
        │    │  Availability Zone: us-  │   │
        │    │  east-1a                 │   │
        │    │  256 addresses           │   │
        │    │  (10.0.11.0 -10.0.11.255)│   │
        │    └──────────────────────────┘   │
        │                                   │
        │    ┌──────────────────────────┐   │
        │    │  Private Subnet 2        │   │
        │    │  10.0.12.0/24            │   │
        │    │  Availability Zone: us-  │   │
        │    │  east-1b                 │   │
        │    │  256 addresses           │   │
        │    │  (10.0.12.0 -10.0.12.255)│   │
        │    └──────────────────────────┘   │
        │                                   │
        └───────────────────────────────────┘
```

### Public vs Private Subnets

#### Public Subnet
- **Connected to Internet Gateway**
- **EC2 instances have public IP addresses**
- **Accessible from the internet**
- **Use for**: Web servers, bastion hosts, load balancers

```
PUBLIC SUBNET FLOW:

User (8.8.8.8)
    │
    ▼
Internet (outside AWS)
    │
    ▼
Internet Gateway (IGW)
    │
    ▼
Public Subnet EC2 (10.0.1.100)
    │
    ▼ (has public IP: 54.123.45.67)
Accessible!
```

#### Private Subnet
- **No direct connection to Internet Gateway**
- **EC2 instances have NO public IP addresses**
- **NOT accessible from the internet (inbound)**
- **Use for**: Databases, private servers, sensitive workloads

```
PRIVATE SUBNET FLOW:

User (8.8.8.8)
    │
    ▼
Internet
    │
    ✗ Cannot reach private EC2 directly


Private EC2 (10.0.11.50) outbound flow:
    │
    ▼
NAT Gateway
    │
    ▼
Internet Gateway
    │
    ▼
Internet
    │
    ▼ (response comes back)
Private EC2 receives data
(But cannot be reached from outside)
```

### Subnet Sizing Guide

```
/24 Subnet = 256 total addresses

10.0.1.0/24 breakdown:
┌─────────────────────────────────────────┐
│  Subnet: 10.0.1.0 - 10.0.1.255         │
│  Total:  256 addresses                  │
├─────────────────────────────────────────┤
│  10.0.1.0      → Network address        │
│  10.0.1.1      → VPC Router (reserved)  │
│  10.0.1.2      → DNS Server (reserved)  │
│  10.0.1.3      → Reserved               │
│  10.0.1.4-250  → Available (247 usable) │
│  10.0.1.255    → Broadcast (reserved)   │
└─────────────────────────────────────────┘

Common CIDR sizes:
/24 = 256 addresses (best for most cases)
/25 = 128 addresses (small networks)
/22 = 1,024 addresses (large networks)
/20 = 4,096 addresses (very large)
```

### Subnet Rules

```
Rule 1: Subnets belong to ONE AZ (Availability Zone)
┌──────────────────────────────┐
│  us-east-1a (AZ)            │
│  ┌──────────────────────────┤
│  │ Public Subnet 1          │
│  │ 10.0.1.0/24              │
│  └──────────────────────────┘
└──────────────────────────────┘

┌──────────────────────────────┐
│  us-east-1b (AZ)            │
│  ┌──────────────────────────┤
│  │ Public Subnet 2          │
│  │ 10.0.2.0/24              │
│  └──────────────────────────┘
└──────────────────────────────┘

Rule 2: IP ranges must not overlap
✓ Valid:  10.0.1.0/24 and 10.0.2.0/24
✗ Invalid: 10.0.1.0/24 and 10.0.1.0/24 (same!)

Rule 3: Each subnet can have different rules
Public Subnet:  Has Internet Gateway route
Private Subnet: Connects via NAT Gateway
```

---

## Security Groups

### What is a Security Group?

A **Security Group** is like a firewall for individual resources. It controls what traffic can reach your EC2 instances.

```
Security Group = Bouncer at a nightclub

Think of it this way:

┌─────────────────────────────────────────────────┐
│  EC2 Instance                                   │
│  (Protected by Security Group)                  │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ SECURITY GROUP (Acts like a bouncer)      │ │
│  │                                           │ │
│  │ INBOUND RULES:                           │ │
│  │ ✓ Allow SSH (port 22) from 0.0.0.0/0     │ │
│  │ ✓ Allow HTTP (port 80) from 0.0.0.0/0    │ │
│  │ ✓ Allow HTTPS (port 443) from 0.0.0.0/0  │ │
│  │ ✗ Block everything else                  │ │
│  │                                           │ │
│  │ OUTBOUND RULES:                          │ │
│  │ ✓ Allow all traffic out                  │ │
│  │                                           │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Security Group Traffic Flow

```
INBOUND: Traffic coming TO your EC2

Internet                Security Group              EC2
User at 8.8.8.8                                   Instance
   │                     ┌──────────────┐           │
   ├──SSH (22)──────────►│ Check rules  │──────────►│
   │                     │              │           │
   │                     │ Allow? ✓     │           │
   │                     └──────────────┘           │
   │
   ├──MySQL (3306)──────►│ Check rules  │──────────X
   │                     │              │
   │                     │ Allow? ✗     │
   │                     └──────────────┘
   │
   └──HTTP (80)────────►│ Check rules  │──────────►│
                        │              │           │
                        │ Allow? ✓     │           │
                        └──────────────┘


OUTBOUND: Traffic leaving your EC2

EC2                   Security Group            Internet
Instance                                        Outside
   │                  ┌──────────────┐           │
   ├──HTTPS (443)────►│ Check rules  │──────────►│
   │                  │              │           │
   │                  │ Allow? ✓     │           │
   │                  └──────────────┘           │
   │
   └──All traffic────►│ Check rules  │──────────►│
                      │              │           │
                      │ Allow? ✓     │           │
                      └──────────────┘
```

### Common Security Group Rules

```
WEB SERVER Security Group:

┌─────────────────────────────────────────────┐
│ INBOUND RULES                               │
├──────────┬──────────┬───────────┬───────────┤
│ Protocol │ Port     │ Source    │ Purpose   │
├──────────┼──────────┼───────────┼───────────┤
│ TCP      │ 80       │ 0.0.0.0/0 │ HTTP      │
│ TCP      │ 443      │ 0.0.0.0/0 │ HTTPS     │
│ TCP      │ 22       │ 10.0.0.0/8│ SSH (admin)
└──────────┴──────────┴───────────┴───────────┘

│ OUTBOUND RULES (Usually allow all)          │
├──────────┬──────────┬───────────┬───────────┤
│ Protocol │ Port     │ Dest      │ Purpose   │
├──────────┼──────────┼───────────┼───────────┤
│ All      │ All      │ 0.0.0.0/0 │ Allow all │
└──────────┴──────────┴───────────┴───────────┘


DATABASE Security Group:

┌─────────────────────────────────────────────┐
│ INBOUND RULES                               │
├──────────┬──────────┬───────────┬───────────┤
│ Protocol │ Port     │ Source    │ Purpose   │
├──────────┼──────────┼───────────┼───────────┤
│ TCP      │ 3306     │ App SG    │ MySQL from app
│ TCP      │ 5432     │ App SG    │ PostgreSQL
└──────────┴──────────┴───────────┴───────────┘

│ OUTBOUND RULES                              │
├──────────┬──────────┬───────────┬───────────┤
│ Protocol │ Port     │ Dest      │ Purpose   │
├──────────┼──────────┼───────────┼───────────┤
│ TCP      │ 443      │ 0.0.0.0/0 │ HTTPS out |
└──────────┴──────────┴───────────┴───────────┘
```

### Security Group Chaining

Security Groups can reference each other!

```
┌──────────────────────────────────────────────┐
│                    VPC                        │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │ WEB SERVER SECURITY GROUP           │   │
│  │                                     │   │
│  │ INBOUND:                            │   │
│  │ ✓ Port 80 from 0.0.0.0/0           │   │
│  │ ✓ Port 443 from 0.0.0.0/0          │   │
│  │ ✓ Port 22 from ADMIN_SG            │   │
│  │                                     │   │
│  │ ┌──────────────────────────────┐   │   │
│  │ │ EC2 Instance - Web Server    │   │   │
│  │ └──────────────────────────────┘   │   │
│  └─────────────────────────────────────┘   │
│            ▲                                │
│            │ Can access DB on             │
│            │ port 3306                    │
│            │                              │
│  ┌─────────────────────────────────────┐   │
│  │ DATABASE SECURITY GROUP             │   │
│  │                                     │   │
│  │ INBOUND:                            │   │
│  │ ✓ Port 3306 from WEB_SG             │   │
│  │   (allows traffic from web SG)      │   │
│  │ ✗ Port 3306 from anywhere else      │   │
│  │                                     │   │
│  │ ┌──────────────────────────────┐   │   │
│  │ │ RDS Database Instance        │   │   │
│  │ └──────────────────────────────┘   │   │
│  └─────────────────────────────────────┘   │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Network ACLs

### What is a NACL?

A **Network Access Control List (NACL)** is a layer of security at the SUBNET level. It's like a security checkpoint at the entrance to a neighborhood.

```
SECURITY GROUP vs NACL:

Security Group = Door lock on individual house
                 (Instance level)

NACL          = Neighborhood gates
                (Subnet level)

┌─────────────────────────────────────────┐
│         SUBNET                          │
│  (Protected by NACL)                    │
│                                         │
│  ┌────────────────────────────────┐   │
│  │ EC2 Instance 1                 │   │
│  │ ┌─────────────────────────┐   │   │
│  │ │ Security Group (locked) │   │   │
│  │ └─────────────────────────┘   │   │
│  └────────────────────────────────┘   │
│                                         │
│  ┌────────────────────────────────┐   │
│  │ EC2 Instance 2                 │   │
│  │ ┌─────────────────────────┐   │   │
│  │ │ Security Group (locked) │   │   │
│  │ └─────────────────────────┘   │   │
│  └────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
       ▲
       │ NACL Gate
       │ (Checks all traffic)
       │
    Internet
```

### NACL Rules

```
DEFAULT NACL (Allows all traffic):

┌────────┬──────────┬──────────┬─────────┬─────────────┐
│ Rule # │ Protocol │ Port     │ Source  │ Allow/Deny  │
├────────┼──────────┼──────────┼─────────┼─────────────┤
│ 100    │ All      │ All      │ 0.0.0.0 │ ALLOW       │
│ *      │ All      │ All      │ 0.0.0.0 │ DENY        │
└────────┴──────────┴──────────┴─────────┴─────────────┘
(* = catch all)


CUSTOM NACL (Restrictive - Real World):

┌────────┬──────────┬──────────┬─────────┬─────────────┐
│ Rule # │ Protocol │ Port     │ Source  │ Allow/Deny  │
├────────┼──────────┼──────────┼─────────┼─────────────┤
│ 100    │ TCP      │ 80       │ 0.0.0.0 │ ALLOW       │
│ 110    │ TCP      │ 443      │ 0.0.0.0 │ ALLOW       │
│ 120    │ TCP      │ 22       │ 10.0.0.0│ ALLOW       │
│ 1024-  │ TCP      │ 1024-    │ 0.0.0.0 │ ALLOW       │
│        │          │ 65535    │         │ (ephemeral) │
│ *      │ All      │ All      │ 0.0.0.0 │ DENY        │
└────────┴──────────┴──────────┴─────────┴─────────────┘
```

### NACL Processing Order

```
INBOUND TRAFFIC arrives:

1. Check rule #100: Protocol? ✓ TCP
                    Port?     ✓ 80
                    Source?   ✓ 0.0.0.0/0
                    → ALLOW! (Stop checking)

Traffic passes through


2. Check rule #100: Protocol? ✓ TCP
                    Port?     ✗ 22 (wrong port)
                    → Continue to next rule

3. Check rule #110: Protocol? ✓ TCP
                    Port?     ✗ 443 (wrong port)
                    → Continue to next rule

4. Check rule #120: Protocol? ✓ TCP
                    Port?     ✓ 22
                    Source?   ✗ 10.0.0.0 (wrong source)
                    → Continue to next rule

5. Check rule *:    Default DENY → Block traffic
```

### NACL vs Security Group

```
╔════════════════════════════════════════════════════════╗
║                  COMPARISON TABLE                      ║
╠════════════════════════════════════════════════════════╣
║ Feature          │ Security Group  │ NACL             ║
╠──────────────────┼─────────────────┼──────────────────╣
║ Scope            │ Instance        │ Subnet           ║
║ Applied at       │ ENI level       │ Subnet level     ║
║ Rules            │ Allow + Implicit│ Allow + Deny     ║
║ Default          │ Deny inbound    │ Allow all        ║
║ Stateful?        │ Yes (bidirect.) │ No (stateless)   ║
║ How to block     │ Remove rule     │ Add DENY rule    ║
╚════════════════════════════════════════════════════════╝

STATEFUL vs STATELESS:

Security Group (Stateful):
  Request out ──────────►
  Response automatically allowed in
  (Doesn't need to be in rules)

NACL (Stateless):
  Request out ──────────►
  Response MUST match INBOUND rules
  (Must explicitly allow responses)

This is why NACLs need ephemeral port range (1024-65535)
```

---

## Private Endpoints

### What is a Private Endpoint?

A **Private Endpoint** lets your private resources access AWS services WITHOUT going through the internet.

```
BEFORE Private Endpoint:
(Traffic goes through Internet Gateway)

┌──────────────────┐
│ Private EC2      │
│ 10.0.11.50       │
└─────────┬────────┘
          │
          ▼
┌──────────────────────────────────┐
│ NAT Gateway (costs money!)       │
└─────────────┬────────────────────┘
              │
              ▼
┌──────────────────────────────────┐
│ Internet Gateway                 │
│ (Traffic exposed to internet)    │
└─────────────┬────────────────────┘
              │
              ▼
┌──────────────────────────────────┐
│ S3 Service (Public endpoint)     │
└──────────────────────────────────┘


AFTER Private Endpoint:
(Stays within AWS network)

┌──────────────────┐
│ Private EC2      │
│ 10.0.11.50       │
└─────────┬────────┘
          │
          ▼
┌──────────────────────────────┐
│ VPC Endpoint                 │
│ (Private tunnel)             │
│ 10.0.11.xxx (elastic IP)     │
└─────────────┬────────────────┘
              │ (stays in AWS network)
              ▼
┌──────────────────────────────┐
│ S3 Service (Private access)  │
└──────────────────────────────┘
```

### Types of Private Endpoints

#### 1. Gateway Endpoints (S3 and DynamoDB)

```
VPC with Gateway Endpoint:

┌─────────────────────────────────────────────┐
│ VPC                                         │
│                                             │
│ Route Table Entry:                          │
│ Destination: S3 prefix list                 │
│ Target: pl-1a2b3c4d (S3 endpoint)          │
│                                             │
│ ┌────────────────────────┐                 │
│ │ Private EC2            │                 │
│ └────────┬───────────────┘                 │
│          │                                  │
│          ▼ (sends request to S3)           │
│ ┌────────────────────────┐                 │
│ │ S3 Gateway Endpoint    │                 │
│ │ (Route table handles) │                 │
│ └────────┬───────────────┘                 │
│          │                                  │
│          ▼ (private tunnel to S3)          │
│ ┌────────────────────────┐                 │
│ │ Amazon S3              │                 │
│ └────────────────────────┘                 │
│                                             │
└─────────────────────────────────────────────┘

No: Internet Gateway
No: NAT Gateway
No: Internet exposure
✓ Automatic DNS resolution
✓ Free to use
```

#### 2. Interface Endpoints (Most AWS Services)

```
VPC with Interface Endpoint:

┌─────────────────────────────────────────────┐
│ VPC                                         │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ Private Subnet                      │   │
│ │ (Running private EC2)               │   │
│ │                                     │   │
│ │ ┌────────────────────┐             │   │
│ │ │ Private EC2        │             │   │
│ │ │ 10.0.11.50         │             │   │
│ │ └────────┬───────────┘             │   │
│ │          │                          │   │
│ │          ▼                          │   │
│ │ ┌────────────────────┐             │   │
│ │ │ Interface Endpoint │             │   │
│ │ │ (Elastic IP in VPC)│             │   │
│ │ │ 10.0.11.123        │             │   │
│ │ │                    │             │   │
│ │ │ Creates:           │             │   │
│ │ │ • ENI (Network Int)│             │   │
│ │ │ • Private DNS name │             │   │
│ │ │ • Service endpoint │             │   │
│ │ └────────┬───────────┘             │   │
│ │          │                          │   │
│ │          │ Private connection      │   │
│ │          ▼                          │   │
│ │ AWS Service                         │   │
│ │ (EC2, SNS, SQS, etc)               │   │
│ │                                     │   │
│ └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Private Endpoint Benefits

```
┌─────────────────────────────────────────────────┐
│        PRIVATE ENDPOINT BENEFITS                │
├─────────────────────────────────────────────────┤
│                                                 │
│ 1. SECURITY                                     │
│    • No internet exposure                       │
│    • No NAT gateway costs                       │
│    • Encrypted in transit                       │
│    • Can restrict via NACL/SG                   │
│                                                 │
│ 2. PERFORMANCE                                  │
│    • Lower latency (no internet path)           │
│    • More reliable (AWS internal network)       │
│    • Dedicated bandwidth                        │
│                                                 │
│ 3. COST SAVINGS                                 │
│    • No NAT gateway charges                     │
│    • Gateway endpoints (S3, DDB) are free       │
│    • Interface endpoints: ~$7/month             │
│                                                 │
│ 4. COMPLIANCE                                   │
│    • Data never leaves AWS network              │
│    • No PII transmitted over internet           │
│    • Meet regulatory requirements               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Common Private Endpoints

```
SERVICE TYPE          EXAMPLE SERVICES         ENDPOINT TYPE
─────────────────────────────────────────────────────────────
Compute              EC2, Lambda, ECS          Interface

Storage              S3, EBS, EFS              Gateway (S3)
                                              Interface (EFS)

Database             RDS, DynamoDB, Redshift  Interface/Gateway

Messaging            SNS, SQS, Kinesis        Interface

Analytics            Athena, CloudWatch       Interface

Machine Learning     SageMaker                Interface

Development          CodeBuild, CodePipeline  Interface
```

---

## Complete Architecture

### Three-Tier Application Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                          INTERNET                              │
│                       (Users/Clients)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  Internet Gateway (IGW)      │
          │  Route to 0.0.0.0/0 traffic  │
          └──────────────┬───────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────────┐         ┌──────────────────────┐
│ PUBLIC SUBNET        │         │ PUBLIC SUBNET        │
│ AZ: us-east-1a      │         │ AZ: us-east-1b      │
│ 10.0.1.0/24         │         │ 10.0.2.0/24         │
│                      │         │                      │
│ ┌──────────────────┐ │         │ ┌──────────────────┐ │
│ │ ALB/NLB          │ │         │ │ ALB/NLB          │ │
│ │ (Load Balancer)  │ │         │ │ (Load Balancer)  │ │
│ │ 10.0.1.10        │ │         │ │ 10.0.2.10        │ │
│ │                  │ │         │ │                  │ │
│ │ SG: Allow 80,443 │ │         │ │ SG: Allow 80,443 │ │
│ └────────┬─────────┘ │         │ └────────┬─────────┘ │
│          │           │         │          │           │
└──────────┼───────────┘         └──────────┼───────────┘
           │                                │
           └────────────────┬───────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────┐             ┌──────────────────────┐
│ PRIVATE SUBNET       │             │ PRIVATE SUBNET       │
│ AZ: us-east-1a      │             │ AZ: us-east-1b      │
│ 10.0.11.0/24        │             │ 10.0.12.0/24        │
│                      │             │                      │
│ ┌──────────────────┐ │             │ ┌──────────────────┐ │
│ │ App Server (EC2) │ │             │ │ App Server (EC2) │ │
│ │ 10.0.11.50       │ │             │ │ 10.0.12.50       │ │
│ │                  │ │             │ │                  │ │
│ │ SG: Allow port   │ │             │ │ SG: Allow port   │ │
│ │ 8080 from ALB    │ │             │ │ 8080 from ALB    │ │
│ └────────┬─────────┘ │             │ └────────┬─────────┘ │
│          │           │             │          │           │
└──────────┼───────────┘             └──────────┼───────────┘
           │                                    │
           └────────────────┬───────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────┐             ┌──────────────────────┐
│ PRIVATE SUBNET       │             │ PRIVATE SUBNET       │
│ AZ: us-east-1a      │             │ AZ: us-east-1b      │
│ 10.0.21.0/24        │             │ 10.0.22.0/24        │
│                      │             │                      │
│ ┌──────────────────┐ │             │ ┌──────────────────┐ │
│ │ RDS Database     │ │             │ │ RDS Replica      │ │
│ │ (Primary)        │ │             │ │ (Standby)        │ │
│ │ 10.0.21.100      │ │             │ │ 10.0.22.100      │ │
│ │                  │ │             │ │                  │ │
│ │ SG: Allow 3306   │ │             │ │ SG: Allow 3306   │ │
│ │ from App SG      │ │             │ │ from App SG      │ │
│ └──────────────────┘ │             │ └──────────────────┘ │
│                      │             │                      │
└──────────────────────┘             └──────────────────────┘
           │                                    │
           └────────────────┬───────────────────┘
                            │
                    ┌───────▼────────┐
                    │ VPC Endpoint   │
                    │ for S3         │
                    │ (Private)      │
                    │ Route via route│
                    │ table          │
                    └────────┬───────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ S3 Bucket        │
                    │ (Backups, logs)  │
                    │ Private access   │
                    └──────────────────┘
```

### Traffic Flow Example

```
REQUEST: User uploads file to web server

1. User sends HTTP request from 8.8.8.8
   ▼
2. Internet Gateway routes to ALB (public subnet)
   ▼
3. ALB Security Group checks:
   ✓ Protocol: TCP ✓ Port: 443 ✓ Source: 0.0.0.0/0
   → ALLOW
   ▼
4. ALB routes to App Server (private subnet)
   ▼
5. App Server Security Group checks:
   ✓ Protocol: TCP ✓ Port: 8080 ✓ Source: ALB SG
   → ALLOW
   ▼
6. App Server saves file to S3
   ▼
7. VPC Endpoint for S3:
   ✓ Private connection (no NAT needed)
   → File saved to S3
   ▼
8. Response sent back through same path
   ▼
9. User receives response
```

---

## Hands-On Exercises

### Exercise 1: Create a VPC

**Objective**: Build your first VPC with public and private subnets

**Steps**:
1. Create VPC with CIDR 10.0.0.0/16
2. Create 2 public subnets
   - us-east-1a: 10.0.1.0/24
   - us-east-1b: 10.0.2.0/24
3. Create 2 private subnets
   - us-east-1a: 10.0.11.0/24
   - us-east-1b: 10.0.12.0/24
4. Create Internet Gateway
5. Create and configure route tables

**Verification**:
- [ ] VPC shows 10.0.0.0/16
- [ ] 4 subnets in correct AZs
- [ ] IGW attached to VPC
- [ ] Public subnet route table has route to IGW
- [ ] Private subnet route table has no IGW route

---

### Exercise 2: Create Security Groups

**Objective**: Implement security controls for web servers

**Rules to create**:
```
WEB_SG:
  INBOUND:
  - HTTP (80) from 0.0.0.0/0
  - HTTPS (443) from 0.0.0.0/0
  - SSH (22) from 10.0.0.0/8

DB_SG:
  INBOUND:
  - MySQL (3306) from WEB_SG

OUTBOUND:
  - HTTPS (443) to 0.0.0.0/0 (for updates)
```

**Verification**:
- [ ] WEB_SG allows HTTP/HTTPS from internet
- [ ] DB_SG allows MySQL only from WEB_SG
- [ ] Can't access DB directly from internet
- [ ] Web servers can still update packages

---

### Exercise 3: Configure NACLs

**Objective**: Implement subnet-level security

```
PUBLIC_NACL:
┌────┬──────────┬──────┬─────────────┬──────┐
│ Rule│ Protocol │ Port │ Source      │Allow ││
├────┼──────────┼──────┼─────────────┼──────┤
│100 │ TCP      │ 80   │ 0.0.0.0/0   │ALLOW ││
│110 │ TCP      │ 443  │ 0.0.0.0/0   │ALLOW ││
│120 │ TCP      │ 22   │ 10.0.0.0/8  │ALLOW ││
│130 │ TCP      │1024- │ 0.0.0.0/0   │ALLOW ││
│    │          │65535 │             │      ││
│ *  │ All      │ All  │ 0.0.0.0/0   │DENY  ││
└────┴──────────┴──────┴─────────────┴──────┘

PRIVATE_NACL:
┌────┬──────────┬──────┬──────────────┬──────┐
│ Rule│ Protocol │ Port │ Source       │Allow ││
├────┼──────────┼──────┼──────────────┼──────┤
│100 │ TCP      │ 3306 │ 10.0.1.0/24 │ALLOW ││
│110 │ TCP      │ 3306 │ 10.0.2.0/24 │ALLOW ││
│120 │ TCP      │1024- │ 0.0.0.0/0    │ALLOW ││
│    │          │65535 │              │      ││
│130 │ TCP      │ 443  │ 0.0.0.0/0    │ALLOW ││
│ *  │ All      │ All  │ 0.0.0.0/0    │DENY  ││
└────┴──────────┴──────┴──────────────┴──────┘
```

---

### Exercise 4: Set Up Private Endpoints

**Objective**: Create secure access to S3 without NAT Gateway

**Steps**:
1. Create VPC Endpoint for S3 (Gateway type)
2. Update private subnet route table to use endpoint
3. Create endpoint policy allowing S3 access
4. Test access from private EC2

**Verification**:
```bash
# From private EC2 (no public IP):
$ aws s3 ls s3://my-bucket

# Should work without going through NAT Gateway
# Cost savings: No NAT data transfer charges
```

---

## Common Patterns

### Pattern 1: Highly Available Web Application

```
┌──────────────────────────────────────┐
│ VPC: 10.0.0.0/16                     │
│                                      │
│ ┌──────────────────────────────────┐│
│ │ Public Subnets (ALB)             ││
│ │ 10.0.1.0/24 (AZ-a)               ││
│ │ 10.0.2.0/24 (AZ-b)               ││
│ │                                  ││
│ │ ┌────────────────────────────┐  ││
│ │ │ Application Load Balancer  │  ││
│ │ │ Listens on 80, 443         │  ││
│ │ └────────────────────────────┘  ││
│ └──────────────┬───────────────────┘│
│                │                    │
│ ┌──────────────┴────────────────┐  │
│ │ Private Subnets (App Servers) │  │
│ │ 10.0.11.0/24 (AZ-a)           │  │
│ │ 10.0.12.0/24 (AZ-b)           │  │
│ │                               │  │
│ │ ┌────────┐      ┌────────┐   │  │
│ │ │EC2 App │      │EC2 App │   │  │
│ │ │Server 1│      │Server 2│   │  │
│ │ └────────┘      └────────┘   │  │
│ └──────────────┬────────────────┘  │
│                │                    │
│ ┌──────────────┴────────────────┐  │
│ │ Database Subnets             │  │
│ │ 10.0.21.0/24 (AZ-a)          │  │
│ │ 10.0.22.0/24 (AZ-b)          │  │
│ │                              │  │
│ │ ┌────────┐      ┌────────┐  │  │
│ │ │RDS Prim│      │RDS Std │  │  │
│ │ │ary     │      │by (HA) │  │  │
│ │ └────────┘      └────────┘  │  │
│ └──────────────────────────────┘  │
│                                    │
└──────────────────────────────────────┘

Benefits:
✓ Load balanced across 2 AZs
✓ Auto-scaling group for elasticity
✓ RDS Multi-AZ for HA
✓ No single point of failure
```

### Pattern 2: Isolated Development Environment

```
┌────────────────────────────────────┐
│ Dev VPC: 10.1.0.0/16               │
│                                    │
│ ┌────────────────────────────────┐│
│ │ Dev Subnet (Single AZ)         ││
│ │ 10.1.1.0/24                    ││
│ │                                ││
│ │ ┌──────────────────────────┐  ││
│ │ │ EC2 Dev Instance         │  ││
│ │ │ Database (Same EC2)      │  ││
│ │ │ App Server (Same EC2)    │  ││
│ │ │ (All in one for simplicity)  ││
│ │ └──────────────────────────┘  ││
│ │ SG: Allow all traffic         ││
│ └────────────────────────────────┘│
│                                    │
└────────────────────────────────────┘

Benefits:
✓ Single instance = low cost
✓ Relaxed security (dev only!)
✓ Easy to reset/recreate
✓ Perfect for learning
```

### Pattern 3: Hybrid Cloud (VPN)

```
┌──────────────────────────────────────┐
│ AWS VPC: 10.0.0.0/16                 │
│                                      │
│ ┌────────────────────────────────┐  │
│ │ Private Subnet: 10.0.1.0/24    │  │
│ │                                │  │
│ │ ┌──────────────────────────┐   │  │
│ │ │ EC2 Instance            │   │  │
│ │ └──────────────────────────┘   │  │
│ └────────────┬────────────────────┘  │
│              │                       │
│              ▼                       │
│  ┌──────────────────────────────┐   │
│  │ Virtual Private Gateway      │   │
│  │ (VPN Endpoint)              │   │
│  └──────────────┬───────────────┘   │
│                 │ (Encrypted tunnel)│
│                 │                   │
└─────────────────┼───────────────────┘
                  │
                  ▼ (VPN Connection)
┌──────────────────────────────────────┐
│ On-Premises Data Center              │
│ 192.168.0.0/16                       │
│                                      │
│ ┌────────────────────────────────┐  │
│ │ Corporate Network              │  │
│ │ Servers, Databases             │  │
│ └────────────────────────────────┘  │
│                                      │
└──────────────────────────────────────┘

Benefits:
✓ Secure encrypted connection
✓ Access on-prem from AWS
✓ Access AWS from on-prem
✓ No internet exposure
```

---

## Key Takeaways

### The 7 Layers of AWS Networking Security

```
Layer 1: VPC Selection
         ┌─────────────────┐
         │ Choose VPC size │
         └────────┬────────┘
                  │
Layer 2: Subnet Selection
         ┌─────────────────────────┐
         │ Public or Private       │
         │ Which AZ                │
         └────────┬────────────────┘
                  │
Layer 3: Internet Gateway
         ┌─────────────────────────┐
         │ Route to IGW or NAT GW  │
         └────────┬────────────────┘
                  │
Layer 4: NACL (Subnet-level firewall)
         ┌─────────────────────────┐
         │ Stateless rules         │
         │ Allow/Deny specific     │
         │ protocols/ports         │
         └────────┬────────────────┘
                  │
Layer 5: Security Group (Instance-level firewall)
         ┌─────────────────────────┐
         │ Stateful rules          │
         │ Allow specific ports    │
         │ and protocols           │
         └────────┬────────────────┘
                  │
Layer 6: OS-level Firewall
         ┌─────────────────────────┐
         │ iptables / Windows FW   │
         │ Software firewall       │
         └────────┬────────────────┘
                  │
Layer 7: Application-level Controls
         ┌─────────────────────────┐
         │ Authentication          │
         │ Authorization           │
         │ Encryption              │
         └─────────────────────────┘
```

### Quick Decision Tree

```
Do you need internet access?
│
├─ YES ─► Place in Public Subnet
│         Attach IGW to VPC
│         Route to IGW
│         Allow port 80/443 in SG
│
└─ NO ──► Place in Private Subnet
          (If need updates: NAT Gateway)
          (If need AWS service: Private Endpoint)
          No public IP needed
          More secure
```

---

## Additional Resources

### Important AWS Networking Limits

```
╔════════════════════════════════════════╗
║ Default AWS Networking Limits          ║
╠════════════════════════════════════════╣
║ VPCs per region: 5 (can increase)      ║
║ Subnets per VPC: 200                   ║
║ Route tables per VPC: 200              ║
║ Security groups per VPC: 500           ║
║ Rules per SG: 60 (inbound + outbound)  ║
║ NACLs per VPC: 200                     ║
║ ENIs per instance: 1-8 (instance type) ║
║ Private IPs per ENI: 6-32              ║
╚════════════════════════════════════════╝
```

### Common Debugging Tips

```
"Can't connect to EC2?"
→ Check: Security Group rules
→ Check: NACL rules
→ Check: Route table has route
→ Check: Instance has correct ENI
→ Check: OS firewall allows traffic

"High NAT Gateway costs?"
→ Use: VPC Endpoints for S3/DynamoDB
→ Use: CloudFront for static content
→ Monitor: NAT Gateway metrics

"Private instance can't reach internet?"
→ Add: NAT Gateway to public subnet
→ Update: Private route table
→ OR: Use: VPC Endpoint (preferred)
```

---

## Summary

### What You've Learned

✅ **VPC**: Your isolated network in AWS
✅ **Subnets**: Smaller networks for organization
✅ **Public Subnets**: Internet-facing resources
✅ **Private Subnets**: Internal resources only
✅ **Security Groups**: Instance-level firewall
✅ **NACLs**: Subnet-level firewall
✅ **Private Endpoints**: Secure AWS service access
✅ **Architecture Patterns**: How to design real applications
✅ **Security Layers**: Defense in depth

### Next Steps

1. **Practice Building**: Create VPCs with AWS Console
2. **Terraform/CloudFormation**: Infrastructure as Code
3. **Advanced Topics**: VPC Peering, Transit Gateways
4. **Monitoring**: VPC Flow Logs, CloudWatch
5. **Cost Optimization**: NAT Gateway alternatives
6. **Compliance**: Security group best practices

---

**This guide is designed for learning and practice. Use it with AWS Free Tier for hands-on experience!**

**Last Updated**: April 3, 2026
**AWS Region Used**: us-east-1 (examples)
**Difficulty**: Beginner to Intermediate
