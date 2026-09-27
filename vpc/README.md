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
     └─ Security Groups = Door locks on each server inside the room (instance-level)
     └─ Internet Gateway = Entrance to the compound from outside
     └─ NAT Gateway = One-way exit door (private rooms to outside)
```

This is the mental model that makes VPC click. Let's break it down:

- **AWS Account** = Your secured property / compound
- **VPC** = Your own building (completely isolated from other buildings)
- **Subnets** = Rooms in your building (each with separate security)
- **Route Table** = Signs directing traffic to right rooms
- **NACL** = Security checkpoint at the room/subnet entrance (checks traffic for the whole subnet)
- **Security Group** = Lock on each server instance inside the room (checks traffic per instance)
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

### Big Picture: VPC Across Availability Zones

This diagram shows the big picture: a VPC spans a Region and can contain multiple public and private subnets across multiple Availability Zones. That is the foundation for high availability and public/private separation.

<img src="https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png" alt="Default VPC across multiple Availability Zones" width="1080">

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

### VPC Resources in This Setup

These are all AWS resources, but they are not all servers:

| Resource | What It Is | Do You Manage a Server? | Where It Attaches or Lives |
|----------|------------|--------------------------|-----------------------------|
| EC2 instance | Virtual server | Yes | In a subnet |
| Internet Gateway | Managed gateway between a VPC and the internet | No | Attached to the VPC |
| NAT Gateway | Managed outbound internet gateway for private subnets | No | Created in a public subnet |
| Route Table | Routing rules for subnet traffic | No | Associated with one or more subnets |
| Security Group | Stateful firewall for an instance/network interface | No | Attached to EC2, ENI, load balancer, RDS, etc. |
| NACL | Stateless firewall for a subnet | No | Associated with one or more subnets |

Important: Internet Gateway and NAT Gateway are AWS-managed networking resources. They are not EC2 instances, and you do not SSH into them or patch them.

### The Simplest Possible VPC

A minimal VPC needs:

1. **VPC itself** - Define IP range (e.g., `172.31.0.0/16`)
2. **Subnet** - Define where instances live (e.g., `172.31.0.0/20`)
3. **Internet Gateway** - Gateway that lets public resources communicate with the internet
4. **Route Table** - Rules that tell subnet traffic where to go
5. **Security Group** - Instance-level firewall for EC2
6. **Public IP or Elastic IP** - Public address for internet-reachable EC2 instances
7. **NAT Gateway** - Optional; lets private subnet instances reach the internet for outbound traffic

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

**Result**: A basic VPC with a public subnet. An EC2 instance in this subnet becomes reachable from the internet only if it also has a public IPv4 address or Elastic IP and its security group/NACL allow the traffic.

### Optional: Add a NAT Gateway for Private Subnets

A NAT Gateway is not needed for a simple public web server. Add it when you also have private subnets and those private resources need outbound internet access for tasks like software updates, package downloads, or calling external APIs.

NAT Gateway requirements:

```text
NAT Gateway must live in a public subnet
+ NAT Gateway must have an Elastic IP
+ public subnet route table must have 0.0.0.0/0 -> Internet Gateway
+ private subnet route table must have 0.0.0.0/0 -> NAT Gateway
= private subnet instances can start outbound internet connections
```

Important: NAT Gateway is outbound-only for private subnets. It does not let internet users start inbound connections to private EC2 instances.

```
Step 7: Create a Private Subnet
   aws ec2 create-subnet --vpc-id vpc-xxxxx \
     --cidr-block 172.31.16.0/20 \
     --availability-zone us-east-1a
   ✓ Private subnet created

Step 8: Allocate an Elastic IP for the NAT Gateway
   aws ec2 allocate-address --domain vpc
   ✓ Elastic IP allocated

Step 9: Create NAT Gateway in the PUBLIC subnet
   aws ec2 create-nat-gateway \
     --subnet-id subnet-public-xxxxx \
     --allocation-id eipalloc-xxxxx
   ✓ NAT Gateway created in public subnet

Step 10: Create Private Route Table
   aws ec2 create-route-table --vpc-id vpc-xxxxx
   ✓ Private route table created

Step 11: Add Route from Private Subnet to NAT Gateway
   aws ec2 create-route --route-table-id rtb-private-xxxxx \
     --destination-cidr-block 0.0.0.0/0 \
     --nat-gateway-id nat-xxxxx
   ✓ Private subnet sends internet-bound traffic to NAT Gateway

Step 12: Associate Private Route Table with Private Subnet
   aws ec2 associate-route-table \
     --subnet-id subnet-private-xxxxx \
     --route-table-id rtb-private-xxxxx
   ✓ Private subnet now uses NAT for outbound internet access
```

Elastic IP note:

```text
aws ec2 allocate-address --domain vpc
```

allocates a static public IPv4 address and returns an `AllocationId`, such as `eipalloc-xxxxx`. The NAT Gateway uses that Elastic IP when you pass it here:

```text
aws ec2 create-nat-gateway --allocation-id eipalloc-xxxxx
```

For a public NAT Gateway, the Elastic IP is the public source IP that the internet sees. Private EC2 instances do not get that Elastic IP directly.

```text
Private EC2 private IP -> NAT Gateway -> NAT Gateway Elastic IP -> Internet
```

Important nuance: AWS also supports private NAT Gateways for private routing use cases. The NAT Gateway in this beginner example is a public NAT Gateway for outbound internet access, so it requires an Elastic IP.

Final layout:

```text
Public subnet:
  EC2 web server or NAT Gateway
  Route: 0.0.0.0/0 -> Internet Gateway

Private subnet:
  App server or database
  Route: 0.0.0.0/0 -> NAT Gateway
```

### How an EC2 Web Server Becomes Public

Putting EC2 in a subnet is not enough by itself. For a public web server, you need all of these:

```text
VPC has Internet Gateway attached
+ subnet route table has 0.0.0.0/0 -> Internet Gateway
+ EC2 has public IPv4 address or Elastic IP
+ EC2 security group allows inbound HTTP/HTTPS
+ subnet NACL allows inbound and outbound traffic
= public web server
```

Example web-server setup:

| Requirement | Example |
|-------------|---------|
| Subnet route | `0.0.0.0/0 -> igw-...` |
| EC2 address | Auto-assigned public IPv4 or Elastic IP |
| Security group inbound | TCP `80` and `443` from `0.0.0.0/0` |
| Security group SSH | TCP `22` only from your IP, or use Session Manager |
| NACL | Allow TCP `80`/`443` inbound and ephemeral ports outbound |

Simple mental model:

```text
Route table gives the subnet a road to the internet.
Public IP gives the EC2 instance a reachable internet address.
Security group opens the EC2 instance door.
NACL opens the subnet checkpoint.
```

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
- Each subnet has its own security checkpoint (NACL) at the room level, while Security Groups are locks on the individual server instances inside that room.

### Public Subnet (Internet-Facing)

A subnet where instances **can reach the internet AND can be reached from the internet if they are given public addresses and security rules allow it**.

**Building analogy**: It's like a **room that faces the street**. Anyone walking by (internet users) can see the window and knock on the door. Your web servers sit in this room to greet visitors.

**What makes it public?**
1. The subnet's route table has a route to an Internet Gateway for `0.0.0.0/0` (doors/windows face the street).
2. The EC2 instance has a public IPv4 address or Elastic IP (everyone knows the street address).
3. The security group allows the needed inbound traffic, such as HTTP `80`, HTTPS `443`, or SSH `22` from an approved source.
4. The subnet NACL allows the traffic in both directions.

**Example**: Your web servers live here (they WANT to talk to internet users).

Important: **a subnet is not public just because an EC2 instance has a public IP**, and an EC2 instance is not reachable just because it is in a public subnet. You need both:

```text
Internet Gateway route in subnet route table
+ public IPv4 or Elastic IP on the EC2 instance
+ security group/NACL rules that allow the traffic
= internet-reachable EC2 instance
```

To launch a web server in a public subnet:

1. Create or choose a subnet whose route table has `0.0.0.0/0 -> Internet Gateway`.
2. Launch the EC2 instance into that subnet.
3. Enable `Auto-assign public IPv4 address` at launch, or attach an Elastic IP after launch.
4. Attach a security group that allows inbound `80`/`443` from `0.0.0.0/0` for a public website.
5. Allow SSH `22` only from your IP, or use AWS Systems Manager Session Manager instead of SSH.

How the EC2 gets a public IP:

- **Auto-assigned public IPv4**: AWS gives the instance a temporary public IP when it launches. It can change when the instance stops and starts.
- **Elastic IP**: You allocate a stable public IP and associate it with the instance or network interface. It stays the same until you release it.

Important public IP detail:

```text
Inside the EC2 operating system, the instance usually sees only its private IP.
AWS maps the public IPv4 address to the instance's network interface through the Internet Gateway path.
```

So yes, the instance gets internet reachability because of the combination of:

```text
public IP + public subnet route table + Internet Gateway + allowed firewall rules
```

It is not just "because it has a public IP." A public IP without a route to an Internet Gateway will not make the instance reachable.

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

A subnet where instances **do not have a direct public internet path**. They can still reach the internet for outbound tasks if their route table points to a NAT Gateway, but the internet cannot start connections directly to them.

**Building analogy**: It's like a **room hidden in the back of the building**, away from the street. There are no visible windows or doors from outside. If someone inside needs to go out (order supplies), they use a secret side door (NAT Gateway) that hides their identity. Strangers from the street can NEVER find this room.

**What makes it private?**
1. The subnet route table does NOT route `0.0.0.0/0` directly to an Internet Gateway.
2. Instances usually do NOT have public IPs.
3. Outbound internet traffic goes through a NAT Gateway in a public subnet when needed.
4. Inbound access comes from internal sources only, such as a public web/app tier, VPN, Direct Connect, bastion host, or Systems Manager.

**Example**: Your databases live here (they DON'T want to talk to internet users, for security).

How private subnet outbound internet works:

```text
Private EC2
  -> private subnet route table
  -> 0.0.0.0/0 route to NAT Gateway
  -> NAT Gateway in a public subnet
  -> Internet Gateway
  -> internet
```

The return response comes back through the same NAT Gateway to the private EC2. However, a random internet user cannot initiate a new connection to the private EC2 because:

- the private EC2 has no public IP,
- the private subnet does not route directly to the Internet Gateway,
- the NAT Gateway only supports outbound-initiated connections,
- security groups should not allow direct public inbound traffic.

Important NAT detail:

```text
NAT Gateway allows outbound-initiated traffic from private subnets.
It does not allow the internet to start new inbound connections to private EC2 instances.
```

Example: a private EC2 can run `yum update` or call an external API through NAT. But an internet user cannot browse directly to that private EC2 because it has no public address and no direct Internet Gateway route.

For databases, the normal access path is internal:

```text
Internet user
  -> public load balancer or public web server
  -> private app server or database over private IP
```

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

NAT Gateway placement:

```text
┌─────────────────────────────────────────────────────────────────────┐
│  VPC (172.31.0.0/16)                                                │
│                                                                     │
│  ┌───────────────────────────────────┐                              │
│  │ Public Subnet (172.31.0.0/20)     │                              │
│  │                                   │                              │
│  │ Route Table:                      │                              │
│  │ ├─ 172.31.0.0/16 → Local         │                              │
│  │ └─ 0.0.0.0/0 → Internet Gateway  │                              │
│  │                                   │                              │
│  │ NAT Gateway lives here ✓          │                              │
│  │ Elastic IP: required              │                              │
│  └───────────────▲───────────────────┘                              │
│                  │                                                  │
│                  │ outbound internet traffic                        │
│                  │ private subnet -> NAT Gateway                    │
│  ┌───────────────┴───────────────────┐                              │
│  │ Private Subnet (172.31.16.0/20)   │                              │
│  │                                   │                              │
│  │ Route Table:                      │                              │
│  │ ├─ 172.31.0.0/16 → Local         │                              │
│  │ └─ 0.0.0.0/0 → NAT Gateway       │                              │
│  │                                   │                              │
│  │ Private EC2 / App / Database      │                              │
│  │ Public IP: none                   │                              │
│  └───────────────────────────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Note: **NAT Gateway resides in a public subnet**, not in the private subnet. Private subnets route outbound internet traffic to the NAT Gateway, and the NAT Gateway uses the Internet Gateway to reach the internet.

### Public vs Private Comparison

| Feature | Public | Private |
|---------|--------|---------|
| **Route table default route** | `0.0.0.0/0 -> Internet Gateway` | Usually `0.0.0.0/0 -> NAT Gateway`, or no internet route |
| **Public IP on instances** | Required for direct internet reachability | Usually none |
| **Internet can start inbound connection** | Yes, only if public IP and SG/NACL allow it | No |
| **Instance can reach internet** | Yes, through IGW | Yes, through NAT if configured |
| **Use case** | Load balancers, bastion hosts, public web servers | App servers, databases, internal workers |

---

## Network Traffic Flow

### Public Subnet Flow: User → Web Server

Here's exactly what happens when someone visits your website:

```
1. USER INITIATES REQUEST
   └─ Browser: curl http://18.207.142.45

2. TRAFFIC REACHES AWS
   └─ Internet → AWS Region

3. INTERNET GATEWAY PUBLIC-IP MAPPING
   └─ Public IP 18.207.142.45 maps to EC2 private IP 172.31.1.50
   └─ The subnet is considered public because its route table has 0.0.0.0/0 → Internet Gateway

4. IGW TRANSLATION / DELIVERY
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
   └─ Route table: 0.0.0.0/0 → Internet Gateway
   └─ IGW: Translates 172.31.1.50 → 18.207.142.45
   └─ User receives web page
```

Key point: route tables apply to traffic leaving a subnet. For the web server response, the subnet route table sends internet-bound traffic to the Internet Gateway.

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

**NACL = Security checkpoint at the room entrance** (subnet-level)
- Checks ALL traffic entering/leaving the room
- Stateless (must check both directions explicitly)
- Applies to entire subnet

**Security Group = Door lock on each server instance inside the room** (instance-level)
- Checks traffic for that specific server instance
- Stateful (remembers your conversation)
- Applies to individual instances, not the whole subnet

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
- **Stateful**: Remembers conversations. If you allow an inbound request on port `80` or `443`, the return response traffic is automatically allowed.
- **Allow only**: You specify what's ALLOWED. Everything else is blocked.
- **Instance-level**: Each instance has its own security group (each room has its own lock)

Important nuance:

```text
Security Group inbound rules do not become general outbound rules.
They only allow return traffic for a connection that was already allowed.
```

Example:

```text
Internet client -> EC2 web server on port 443
```

If the security group allows inbound `443`, the response from EC2 back to that client is automatically allowed because the security group is stateful.

But if the EC2 instance starts a new outbound connection, outbound security group rules still matter:

```text
EC2 -> external API on port 443
```

That requires an outbound rule allowing HTTPS out. The default security group behavior usually allows all outbound traffic, which is why this often works without extra changes.

**Example: Web Server Security Group**

```
Web-SG (Inbound Rules)
├─ Port 80 (HTTP)    from 0.0.0.0/0    (anyone on internet)
├─ Port 443 (HTTPS)  from 0.0.0.0/0    (anyone on internet)
├─ Port 22 (SSH)     from YOUR_IP/32    (your workstation only)
└─ All responses     (automatic - SG is stateful)
```

For private resources, security groups should usually reference another security group instead of public CIDR ranges:

```
App-SG (Inbound Rules)
└─ Port 8080 from Web-SG

DB-SG (Inbound Rules)
└─ Port 3306 from App-SG
```

This means:

```text
Only instances with Web-SG can call the app tier.
Only instances with App-SG can call the database.
```

### NACL (Subnet Protection)

Protects all instances in a subnet. Think of it as a **security checkpoint at the room entrance** where EVERYONE must pass through.

**Building analogy**: Before anyone (traffic) can enter the room (subnet), they must pass through a security checkpoint. The checkpoint checks BOTH coming in AND going out. It doesn't remember people (stateless) - every trip requires a new check.

**Key features**:
- **Stateless**: Must explicitly allow both inbound AND outbound. Doesn't remember past conversations.
- **Allow + Deny**: Can explicitly deny rules (useful for blocking bad actors - "deny this person entry")
- **Subnet-level**: Applies to entire subnet (everyone entering/leaving the room passes through)

Important rule:

```text
NACLs do not remember connections.
If traffic must go in and return out, both directions must be allowed.
```

**Example: Web Server Subnet NACL**

```
Inbound Rules (requests coming IN to web server):
  Rule 100: Allow port 80 from 0.0.0.0/0      ✓ HTTP
  Rule 110: Allow port 443 from 0.0.0.0/0     ✓ HTTPS
  Rule 120: Allow port 22 from YOUR_IP/32     ✓ SSH, if SSH is used
  Rule 130: Deny all from known bad CIDR       Optional explicit block

Outbound Rules (responses going OUT to internet clients):
  Rule 100: Allow 1024-65535 to 0.0.0.0/0      ✓ Return traffic to client ephemeral ports
  Rule 110: Allow port 80 to 0.0.0.0/0         Optional, if server makes HTTP calls out
  Rule 120: Allow port 443 to 0.0.0.0/0        Optional, if server makes HTTPS calls out
```

**Why the 1024-65535 rule?** NACLs are stateless. When an internet client connects to your web server on port `443`, the client's source port is usually a random ephemeral port such as `51734`. Your web server responds back to that client ephemeral port, so the outbound NACL must allow ephemeral destination ports.

For traffic initiated by an EC2 instance to the internet, the reverse is true:

```text
Outbound NACL: allow destination 80/443
Inbound NACL: allow ephemeral ports 1024-65535 for the return response
```

### Public vs Private Security Rules

Typical public web subnet:

| Layer | Inbound | Outbound |
|-------|---------|----------|
| Security group | Allow `80/443` from internet; SSH only from admin IP | Usually allow all, or restrict as needed |
| NACL | Allow `80/443` from internet; SSH only from admin IP | Allow ephemeral ports back to clients |

Typical private app subnet:

| Layer | Inbound | Outbound |
|-------|---------|----------|
| Security group | Allow app port only from Web-SG or Load-Balancer-SG | Allow DB/API/NAT destinations as needed |
| NACL | Allow app port from public/app tier CIDR | Allow ephemeral return traffic and needed outbound ports |

Typical private database subnet:

| Layer | Inbound | Outbound |
|-------|---------|----------|
| Security group | Allow DB port only from App-SG | Usually limited to required destinations |
| NACL | Allow DB port only from app subnet CIDR | Allow ephemeral return traffic to app subnet |

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

### Site-to-Site VPN (Connect On-Premises Over Encrypted Internet)

Site-to-Site VPN connects an on-premises network to AWS using encrypted IPsec tunnels. It normally uses the public internet as the transport, but the traffic inside the tunnel is encrypted.

```
Office Network (10.0.0.0/16)
    ↕ encrypted IPsec tunnel over public internet
AWS Virtual Private Gateway or Transit Gateway
    ↕
AWS VPC (172.31.0.0/16)
```

**Use case**: Securely access private AWS resources from your office or data center without exposing those resources to the public internet.

Important distinction:

```text
Site-to-Site VPN = encrypted tunnel over the internet
Direct Connect = dedicated private network connection to AWS
```

### Direct Connect (Dedicated Private Connection)

AWS Direct Connect provides a dedicated private network connection from your data center, office, or colocation provider to AWS. It does not use the public internet as the normal transport path.

```
On-Premises Network
    ↕ dedicated private circuit
AWS Direct Connect Location
    ↕
AWS VPC through Virtual Interface / Direct Connect Gateway
```

**Use case**: Predictable bandwidth, lower latency, private connectivity, and large data transfer between on-premises and AWS.

Security note: Direct Connect is private, but not automatically encrypted end to end. Add VPN over Direct Connect or MACsec where encryption is required.

### VPC Peering (Connect to Other VPCs)

VPC peering connects two VPCs privately using AWS networking. Traffic does not traverse the public internet.

```
VPC-A (172.31.0.0/16)  ←→  VPC-B (10.0.0.0/16)
```

**Use case**: Private communication between two VPCs, such as app services in one VPC calling shared services in another.

Important limits:

- VPC CIDR ranges must not overlap.
- VPC peering is not transitive. If VPC-A peers with VPC-B and VPC-B peers with VPC-C, VPC-A cannot automatically reach VPC-C through VPC-B.

### Transit Gateway (Hub for Many Networks)

Transit Gateway acts like a central router for many VPCs, VPNs, and Direct Connect connections.

```
        VPC-A
          │
VPC-B ─ Transit Gateway ─ Site-to-Site VPN / Direct Connect
          │
        VPC-C
```

**Use case**: Larger environments where many VPCs and on-premises networks need controlled connectivity through a central hub.

### VPC Endpoints (Access AWS Services Privately)

VPC endpoints let resources in a VPC reach supported AWS services privately without using an Internet Gateway or NAT Gateway.

```
Private Subnet
    │
    └─→ S3 (via Gateway VPC Endpoint)
        └─ No internet required
        └─ No NAT Gateway costs
```

**Use case**: Download files from S3 in a private subnet without NAT costs.

Two common endpoint types:

| Endpoint Type | Common Services | How It Works |
|---------------|-----------------|--------------|
| Gateway endpoint | S3, DynamoDB | Adds a route-table target for the AWS service |
| Interface endpoint | Lambda API, Secrets Manager, SQS, SNS, KMS, CloudWatch Logs, many others | Creates private ENIs in your subnets using AWS PrivateLink |

Important: S3 and DynamoDB are not moved into your VPC. They remain regional AWS services. The gateway endpoint creates a private route from your VPC to those services.

S3/DynamoDB examples:

```text
Private EC2 -> S3 Gateway Endpoint -> S3
No public IP, no NAT Gateway, no Internet Gateway required.

Private EC2 -> DynamoDB Gateway Endpoint -> DynamoDB
No public IP, no NAT Gateway, no Internet Gateway required.
```

Lambda is different:

```text
Private EC2 -> Lambda Interface Endpoint -> Lambda API
```

Use a **Lambda interface endpoint** when something inside a private subnet needs to call the Lambda service API privately, such as:

```bash
aws lambda invoke ...
```

That endpoint service name looks like:

```text
com.amazonaws.<region>.lambda
```

If private DNS is enabled, your app can keep using the normal Lambda regional endpoint and DNS resolves it to the private endpoint IPs.

#### Lambda Function with VPC Access

This is a separate concept from a Lambda interface endpoint.

When you configure a Lambda function with VPC access, Lambda can reach private resources in your VPC, such as RDS, private EC2, ElastiCache, or an internal load balancer.

```text
Lambda function configured with VPC subnets + security group
  -> VPC local route
  -> private RDS / private EC2 / ElastiCache
```

For private resources in the same VPC, Lambda does not need an Internet Gateway or NAT Gateway:

```text
Lambda private network path -> RDS private IP
```

NAT or endpoints are needed only when the VPC-connected Lambda must reach outside the VPC or reach public AWS service endpoints:

| Lambda Needs To Reach | Path |
|-----------------------|------|
| Private RDS or private EC2 in same VPC | VPC local route |
| Public internet or external API | NAT Gateway -> Internet Gateway |
| S3 or DynamoDB | Gateway endpoint, or NAT Gateway |
| Lambda API, Secrets Manager, SQS, SNS, KMS, CloudWatch Logs | Interface endpoint, or NAT Gateway |

Lambda VPC IP note:

```text
Lambda does not create a brand-new EC2-style network interface for every single invocation.
AWS uses managed Hyperplane ENIs in your selected subnets.
Those ENIs have private IPs from your subnet CIDR and can be reused across invocations.
```

Practical meaning:

- Your Lambda consumes private IP capacity in the selected subnets.
- Lambda traffic appears from private IPs associated with AWS-managed Lambda ENIs.
- Do not design around one fixed Lambda IP per invocation.
- If a stable outbound public IP is required, route Lambda through a NAT Gateway with an Elastic IP.

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
