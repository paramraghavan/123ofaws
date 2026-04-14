# AWS Networking - Visual Diagrams & Illustrations

**ASCII art diagrams for AWS network concepts**

---

## 1. Basic VPC Architecture

### Simple Single-AZ VPC

```
┌────────────────────────────────────────────────────────────┐
│                        AWS REGION                          │
│                       (us-east-1)                          │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              YOUR VPC (10.0.0.0/16)                  │ │
│  │                                                      │ │
│  │  ┌─────────────────────────────────────────────┐   │ │
│  │  │ Availability Zone: us-east-1a              │   │ │
│  │  │                                             │   │ │
│  │  │  ┌───────────────────────────────────────┐ │   │ │
│  │  │  │ PUBLIC SUBNET (10.0.1.0/24)          │ │   │ │
│  │  │  │                                       │ │   │ │
│  │  │  │ Route Table:                          │ │   │ │
│  │  │  │ • 10.0.0.0/16 → Local                │ │   │ │
│  │  │  │ • 0.0.0.0/0 → igw-123               │ │   │ │
│  │  │  │                                       │ │   │ │
│  │  │  │ ┌─────────────────────────────────┐ │ │   │ │
│  │  │  │ │ EC2 Web Server                  │ │ │   │ │
│  │  │  │ │ IP: 10.0.1.100                  │ │ │   │ │
│  │  │  │ │ Public IP: 54.123.45.67         │ │ │   │ │
│  │  │  │ │ Security Group: Allow 80,443    │ │ │   │ │
│  │  │  │ └─────────────────────────────────┘ │ │   │ │
│  │  │  └───────────────────────────────────────┘ │   │ │
│  │  │                   ▲                         │   │ │
│  │  │                   │ (connects to internet) │   │ │
│  │  │              IGW-123                       │   │ │
│  │  │                   │                        │   │ │
│  │  │  ┌───────────────────────────────────────┐ │   │ │
│  │  │  │ PRIVATE SUBNET (10.0.2.0/24)         │ │   │ │
│  │  │  │                                       │ │   │ │
│  │  │  │ Route Table:                          │ │   │ │
│  │  │  │ • 10.0.0.0/16 → Local                │ │   │ │
│  │  │  │ • 0.0.0.0/0 → nat-456               │ │   │ │
│  │  │  │                                       │ │   │ │
│  │  │  │ ┌─────────────────────────────────┐ │ │   │ │
│  │  │  │ │ EC2 App Server                  │ │ │   │ │
│  │  │  │ │ IP: 10.0.2.50                   │ │ │   │ │
│  │  │  │ │ Public IP: NONE (private only)  │ │ │   │ │
│  │  │  │ │ SG: Allow 8080 from web server  │ │ │   │ │
│  │  │  │ └─────────────────────────────────┘ │ │   │ │
│  │  │  │                                       │ │   │ │
│  │  │  │ ┌─────────────────────────────────┐ │ │   │ │
│  │  │  │ │ RDS Database                    │ │ │   │ │
│  │  │  │ │ IP: 10.0.2.100                  │ │ │   │ │
│  │  │  │ │ SG: Allow 3306 from app server  │ │ │   │ │
│  │  │  │ │        Allow 22 from admin      │ │ │   │ │
│  │  │  │ └─────────────────────────────────┘ │ │   │ │
│  │  │  └───────────────────────────────────────┘ │   │ │
│  │  └─────────────────────────────────────────────┘   │ │
│  │                                                      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-AZ Architecture (Highly Available)

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS REGION (us-east-1)                      │
│                                                                 │
│    ┌────────────────────────────────────────────────────────┐  │
│    │              YOUR VPC (10.0.0.0/16)                    │  │
│    │                                                        │  │
│    │  AZ: us-east-1a                AZ: us-east-1b        │  │
│    │  ┌──────────────────┐  ┌──────────────────┐         │  │
│    │  │ Public Subnet 1  │  │ Public Subnet 2  │         │  │
│    │  │ 10.0.1.0/24      │  │ 10.0.2.0/24      │         │  │
│    │  │                  │  │                  │         │  │
│    │  │ ┌──────────────┐ │  │ ┌──────────────┐ │         │  │
│    │  │ │  EC2 Web #1  │ │  │ │  EC2 Web #2  │ │         │  │
│    │  │ │  10.0.1.10   │ │  │ │  10.0.2.10   │ │         │  │
│    │  │ └──────┬───────┘ │  │ └──────┬───────┘ │         │  │
│    │  └────────┼──────────┘  └────────┼─────────┘         │  │
│    │           │                      │                   │  │
│    │           └──────────┬───────────┘                   │  │
│    │                      │                               │  │
│    │           ┌──────────▼──────────┐                   │  │
│    │           │ Application Load    │                   │  │
│    │           │ Balancer (ALB)      │                   │  │
│    │           │ 10.0.1.5            │                   │  │
│    │           │ 10.0.2.5            │                   │  │
│    │           │ Health Checks: ✓    │                   │  │
│    │           └──────────┬──────────┘                   │  │
│    │                      │                               │  │
│    │  ┌──────────────────┐│ ┌──────────────────┐         │  │
│    │  │ Private Subnet 1 │└─│ Private Subnet 2 │         │  │
│    │  │ 10.0.11.0/24     │  │ 10.0.12.0/24     │         │  │
│    │  │                  │  │                  │         │  │
│    │  │ ┌──────────────┐ │  │ ┌──────────────┐ │         │  │
│    │  │ │ EC2 App #1   │ │  │ │ EC2 App #2   │ │         │  │
│    │  │ │ 10.0.11.50   │ │  │ │ 10.0.12.50   │ │         │  │
│    │  │ └──────────────┘ │  │ └──────────────┘ │         │  │
│    │  │                  │  │                  │         │  │
│    │  │ ┌──────────────┐ │  │ ┌──────────────┐ │         │  │
│    │  │ │ RDS Primary  │ │  │ │RDS Standby   │ │         │  │
│    │  │ │ 10.0.11.100  │ │  │ │10.0.12.100   │ │         │  │
│    │  │ │ (Master)     │ │  │ │(Replica)     │ │         │  │
│    │  │ └──────────────┘ │  │ └──────────────┘ │         │  │
│    │  └──────────────────┘  └──────────────────┘         │  │
│    │           ▲  Failover Active-Passive               │  │
│    │           │                                         │  │
│    └────────────┼─────────────────────────────────────────┘  │
│                 │                                             │
│                 ▼ (routes through IGW)                        │
│          INTERNET GATEWAY                                     │
│                 │                                             │
└─────────────────┼──────────────────────────────────────────────┘
                  ▼
            Internet Traffic
```

---

## 3. Traffic Flow Visualization

### Request from Internet to Private Database

```
STEP 1: User Request
┌──────────────────┐
│ External User    │
│ IP: 8.8.8.8:1234 │
└────────┬─────────┘
         │
         │ HTTP Request (Port 80)
         ▼
STEP 2: Internet Gateway
┌──────────────────────────┐
│ AWS Internet Gateway      │
│ Destination: Web Server  │
│ Action: ALLOW            │
└────────┬─────────────────┘
         │
         ▼
STEP 3: Route Table (Public)
┌──────────────────────────┐
│ Check routing rules:     │
│ Dest: 0.0.0.0/0          │
│ Target: igw-123          │
│ Match: YES               │
│ Action: Forward to igw   │
└────────┬─────────────────┘
         │
         ▼
STEP 4: Public Subnet
┌────────────────────────────┐
│ Check NACL rules:          │
│ Port 80 allowed? YES       │
│ Source allowed? YES        │
│ Action: PASS               │
└────────┬───────────────────┘
         │
         ▼
STEP 5: EC2 Instance (Public Subnet)
┌────────────────────────────┐
│ IP: 10.0.1.100             │
│ Check Security Group rules:│
│ Port 80 from 0.0.0.0/0?    │
│ YES ✓                       │
│ Action: PASS               │
└────────┬───────────────────┘
         │
         │ Web server receives request
         │ Connects to backend app
         │
         ▼
STEP 6: Route to Private Subnet (App)
┌────────────────────────────────┐
│ Check Route Table (Private):   │
│ Dest: 10.0.0.0/16 (VPC CIDR)  │
│ Target: Local (stay in VPC)    │
│ Match: YES                      │
│ Action: Send to private subnet  │
└────────┬───────────────────────┘
         │
         ▼
STEP 7: Private Subnet
┌────────────────────────────┐
│ Check NACL rules:          │
│ Port 8080 allowed? YES     │
│ Source allowed? YES        │
│ Action: PASS               │
└────────┬───────────────────┘
         │
         ▼
STEP 8: App Server (Private)
┌──────────────────────────────┐
│ IP: 10.0.2.50                │
│ Check Security Group rules:  │
│ Port 8080 from 10.0.1.0/24? │
│ YES ✓                         │
│ Action: ALLOW                 │
└────────┬──────────────────────┘
         │
         │ App connects to database
         │
         ▼
STEP 9: Route to Database (Private)
┌────────────────────────────────┐
│ Check Route Table (Private):   │
│ Dest: 10.0.0.0/16 (VPC CIDR)  │
│ Target: Local                  │
│ Match: YES                     │
│ Action: Send to database       │
└────────┬───────────────────────┘
         │
         ▼
STEP 10: Database Server
┌──────────────────────────────┐
│ IP: 10.0.2.100               │
│ Port: 3306 (MySQL)           │
│ Check Security Group:        │
│ Port 3306 from 10.0.2.0/24?  │
│ YES ✓                         │
│ Action: ALLOW                 │
└──────────────────────────────┘

SUCCESS! Database received query.

RESPONSE travels same path back:
Database → App Server → Web Server → IGW → User
```

---

## 4. Security Group Filtering Example

```
Traffic Checkpoint: Security Group

INBOUND TRAFFIC:

User from 8.8.8.8 sends HTTP (port 80):

     8.8.8.8:54321 ──HTTP──► 54.123.45.67:80
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Security Group Rules  │
                    │ (for EC2 instance)    │
                    └───────────────────────┘
                                │
                Check Rule #1: │
                Protocol: TCP  │ ✓ Match
                Port: 80       │ ✓ Match
                Source: 0.0.0.0│ ✓ Match
                               │
                               ▼
                        ✓ ALLOW ─────► EC2 gets traffic


User from 192.168.1.1 sends MySQL (port 3306):

     192.168.1.1:54321 ──MySQL──► 54.123.45.67:3306
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │ Security Group Rules  │
                            │ (for EC2 instance)    │
                            └───────────────────────┘
                                        │
                    Check Rule #1: ─────┘
                    Protocol: TCP
                    Port: 80
                    Source: 0.0.0.0/0

                    Does NOT match (port 3306)
                                        │
                    Check Rule #2: ─────┼──► Does NOT exist
                                        │
                    Check Rule #*: ─────┼──► Default: DENY
                                        │
                                        ▼
                        ✗ DENY ─────► Traffic blocked
```

---

## 5. NACL Processing Order

```
NACL Ruleset Example:

┌─────┬──────────┬─────┬──────────┬──────────┐
│ # │ Proto │ Port │ Source     │ Action │
├─────┼──────────┼─────┼──────────┼──────────┤
│ 100 │ TCP   │ 80  │ 0.0.0.0/0 │ ALLOW  │
│ 110 │ TCP   │ 443 │ 0.0.0.0/0 │ ALLOW  │
│ 120 │ TCP   │ 22  │ 10.0.0/16 │ ALLOW  │
│ 130 │ TCP   │ 3306│ 10.0.0/16 │ ALLOW  │
│ 140 │ TCP   │1024-│ 0.0.0.0/0 │ ALLOW  │
│     │       │65535│           │        │
│ 32767│ All │ All │ 0.0.0.0/0 │ DENY   │ (default)
└─────┴──────────┴─────┴──────────┴──────────┘

INCOMING HTTP REQUEST (80):

1. Check Rule #100:
   Protocol: TCP ✓
   Port: 80 ✓
   Source: 0.0.0.0/0 ✓
   Action: ✓ ALLOW

   → Stop processing, TRAFFIC PASSES

INCOMING SSH REQUEST (22) from 192.168.1.1:

1. Check Rule #100:
   Port: 80 (not 22) ✗
   → Continue to next rule

2. Check Rule #110:
   Port: 443 (not 22) ✗
   → Continue to next rule

3. Check Rule #120:
   Protocol: TCP ✓
   Port: 22 ✓
   Source: 10.0.0/16 (not 192.168.1.1) ✗
   → Continue to next rule

4. Check Rule #130:
   Port: 3306 (not 22) ✗
   → Continue to next rule

5. Check Rule #140:
   Port: 1024-65535 (not 22) ✗
   → Continue to next rule

6. Check Rule #32767:
   All Protocols, All Ports
   Action: DENY

   → TRAFFIC BLOCKED
```

---

## 6. VPC Endpoint Architecture

### Before VPC Endpoint (expensive!)

```
PRIVATE EC2 accessing S3 (without endpoint):

Private EC2
10.0.11.50
    │
    │ Need S3 access
    │ but no public IP
    │
    ▼
Must route through NAT Gateway

NAT Gateway
(in public subnet)
    │
    │ $0.045/hour + data charges
    │ Every request costs money
    │
    ▼
Internet Gateway
    │
    │ Data exposed to internet path
    │
    ▼
S3 Public Endpoint
(Over the internet!)

Problems:
✗ Expensive (NAT charges)
✗ Slow (goes through internet)
✗ Not private (internet exposure)
✗ Overkill if just need AWS services
```

### After VPC Endpoint (fast & cheap!)

```
PRIVATE EC2 accessing S3 (with endpoint):

Private EC2
10.0.11.50
    │
    │ Need S3 access
    │ Create VPC Endpoint for S3
    │
    ▼
VPC Endpoint (S3)
└─ Created automatically in private subnet
└─ Private DNS: s3.us-east-1.amazonaws.com
└─ Access like normal S3, but through AWS network
    │
    │ Direct AWS network path
    │ No internet gateway needed
    │ No NAT gateway needed
    │
    ▼
S3 Service
(Via private AWS network!)

Benefits:
✓ FREE (gateway endpoints are free)
✓ Fast (AWS network, lower latency)
✓ Private (no internet exposure)
✓ Simple (update route table or DNS)

What route table looks like:
Destination: pl-12345678 (S3 prefix list)
Target: vpce-s3-xxxxx (VPC Endpoint)
```

---

## 7. NAT Gateway vs Private Endpoint

```
SCENARIO: Private EC2 needs internet access

┌─────────────────────────────────────────────────────────┐
│ OPTION A: NAT GATEWAY                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Private EC2                                             │
│ 10.0.11.50                                              │
│     │                                                   │
│     ├─ Make request to yum.amazonaws.com                │
│     │                                                   │
│     ▼                                                   │
│ Route Table: 0.0.0.0/0 → nat-xxx                       │
│ (Send all internet traffic through NAT)                │
│     │                                                   │
│     ▼                                                   │
│ NAT Gateway (in public subnet)                          │
│ • Hides private IP (translates to NAT IP)              │
│ • Processes request                                    │
│ • Sends to Internet Gateway                            │
│     │                                                   │
│     ▼                                                   │
│ Internet Gateway                                       │
│ (Request goes OUT to internet)                         │
│     │                                                   │
│     ▼                                                   │
│ Internet                                               │
│     │                                                   │
│     ▼ (response comes back)                            │
│ Internet Gateway → NAT → EC2                           │
│                                                         │
│ COST: $0.045/hour + $0.045/GB processed               │
│ For 1TB: $0.045 + (1000 × 0.045) = ~$45/month        │
│                                                         │
└─────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────┐
│ OPTION B: VPC ENDPOINT (Recommended!)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Private EC2                                             │
│ 10.0.11.50                                              │
│     │                                                   │
│     ├─ Make request to s3.amazonaws.com                │
│     │                                                   │
│     ▼                                                   │
│ Route Table: pl-s3 → vpce-s3-xxxxx                    │
│ (S3 requests go directly to VPC endpoint)              │
│     │                                                   │
│     ▼                                                   │
│ VPC Endpoint (S3)                                      │
│ • Stays in AWS network                                │
│ • Elastic IP in VPC                                    │
│ • Direct connection to S3                              │
│     │                                                   │
│     ▼ (stays internal)                                 │
│ S3 Service                                             │
│ (Request never leaves AWS!)                            │
│                                                         │
│ COST: FREE (or $7.20/month for Interface endpoints)   │
│ Savings: ~$38/month vs NAT                            │
│                                                         │
└─────────────────────────────────────────────────────────┘

CONCLUSION: Use VPC Endpoints whenever possible!
```

---

## 8. Subnet IP Distribution

```
Subnet: 10.0.1.0/24 (Total: 256 addresses)

RESERVED ADDRESSES (Not usable):

10.0.1.0
└─► Network address (AWS reserved)

10.0.1.1
└─► VPC Router (AWS reserved)

10.0.1.2
└─► DNS Server (AWS reserved)

10.0.1.3
└─► Reserved for future use (AWS reserved)

10.0.1.4 to 10.0.1.250
└─► AVAILABLE FOR USE (247 usable addresses)
    └─► Typically assign first 5-10 for NICs
    └─► Rest for EC2 instances, RDS, etc.

10.0.1.251 to 10.0.1.255
└─► Reserved (AWS reserved for future use)

10.0.1.255
└─► Broadcast address (AWS reserved)


VISUALIZATION:

10.0.1.0   ██ Reserved
10.0.1.1   ██ Reserved
10.0.1.2   ██ Reserved
10.0.1.3   ██ Reserved
10.0.1.4   ▓▓ Available (EC2 1)
10.0.1.5   ▓▓ Available (RDS)
...
10.0.1.250 ▓▓ Available (EC2 N)
10.0.1.251 ██ Reserved
10.0.1.252 ██ Reserved
10.0.1.253 ██ Reserved
10.0.1.254 ██ Reserved
10.0.1.255 ██ Broadcast

██ = Reserved (5 addresses)
▓▓ = Available (247 addresses)
```

---

## 9. High Availability Setup

```
SINGLE AZ (NOT HA - RISKY!):

┌──────────────────────────────────┐
│ Availability Zone us-east-1a    │
│                                  │
│ ┌────────────────────────────┐  │
│ │ Public Subnet              │  │
│ │ ┌──────────────────────┐   │  │
│ │ │ Web Server           │   │  │
│ │ └──────────────────────┘   │  │
│ └────────────────────────────┘  │
│                                  │
│ ┌────────────────────────────┐  │
│ │ Private Subnet             │  │
│ │ ┌──────────────────────┐   │  │
│ │ │ Database             │   │  │
│ │ │ (SINGLE POINT OF     │   │  │
│ │ │  FAILURE!)           │   │  │
│ │ └──────────────────────┘   │  │
│ └────────────────────────────┘  │
│                                  │
└──────────────────────────────────┘

Problem: If AZ goes down, everything goes down!


MULTI-AZ HA (RECOMMENDED):

┌──────────────────────────┬──────────────────────────┐
│ AZ: us-east-1a          │ AZ: us-east-1b          │
├──────────────────────────┼──────────────────────────┤
│ ┌────────────────────┐   │ ┌────────────────────┐  │
│ │ Public Subnet      │   │ │ Public Subnet      │  │
│ │ ┌──────────────┐   │   │ │ ┌──────────────┐   │  │
│ │ │ Web Server 1 │───┼───┼─┤─│ Web Server 2 │   │  │
│ │ └──────────────┘   │   │ │ └──────────────┘   │  │
│ └─────────┬──────────┘   │ └────────┬────────────┘  │
│           │              │         │               │
│ ┌─────────▼──────────┐   │ ┌───────▼──────────┐    │
│ │ Private Subnet     │   │ │ Private Subnet   │    │
│ │ ┌──────────────┐   │   │ │ ┌──────────────┐ │    │
│ │ │ RDS Primary  │───┼───┼─┤─│RDS Standby   │ │    │
│ │ │ (Master)     │   │   │ │ │(Replica)     │ │    │
│ │ └──────────────┘   │   │ │ └──────────────┘ │    │
│ └────────────────────┘   │ └──────────────────┘    │
└──────────────────────────┴──────────────────────────┘

      Auto Failover
         ▲ (If AZ-a fails)
         │
    Data replicated
    in real-time

Benefits:
✓ AZ failure: Automatic failover
✓ App continues running
✓ No data loss
✓ RDS Multi-AZ handles failover automatically
```

---

## 10. Internet Gateway Connection Path

```
HOW INTERNET GATEWAY WORKS:

External Internet (8.8.8.8)
         │
         │ (packet destined for EC2)
         │
         ▼
┌─────────────────────────────────┐
│ AWS Edge Location               │
│ (entry point to AWS network)    │
└──────────────┬──────────────────┘
               │
         (looks up routing)
               │
               ▼
┌─────────────────────────────────┐
│ Internet Gateway (IGW)          │
│ • Performs NAT translation      │
│ • Maps public IP to private IP  │
│ • Routes to appropriate subnet  │
│                                 │
│ 54.123.45.67 ←→ 10.0.1.100     │
│ (public)        (private)       │
└──────────────┬──────────────────┘
               │
         (within VPC)
               │
               ▼
┌─────────────────────────────────┐
│ Public Subnet                   │
│                                 │
│ ┌──────────────────────────┐   │
│ │ EC2 Instance             │   │
│ │ Private: 10.0.1.100      │   │
│ │ Public:  54.123.45.67    │   │
│ └──────────────────────────┘   │
└─────────────────────────────────┘

Return Path (Response):

EC2 (10.0.1.100) sends response
         │
         ▼
Route table: Check destination
"Packet going to 8.8.8.8? → Send to IGW"
         │
         ▼
IGW reverses NAT
(10.0.1.100 → 54.123.45.67)
         │
         ▼
Sends through AWS network to Internet
         │
         ▼
Reaches user at 8.8.8.8

This all happens in milliseconds!
```

---

**These visual diagrams should help you understand AWS networking at a glance!**

Print them, study them, refer back to them when building your own VPCs.

