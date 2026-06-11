# NACL vs Security Groups: Comprehensive Tutoring Guide

> **Master Network Security**: Learn when and how to use Network Access Control Lists (NACLs) and Security Groups to secure your AWS infrastructure. This guide covers fundamentals through advanced scenarios.

---

## Table of Contents

1. [Quick Comparison](#quick-comparison)
2. [Detailed Explanation](#detailed-explanation)
3. [When to Use Each](#when-to-use-each)
4. [Decision Tree](#decision-tree)
5. [Practical Examples](#practical-examples)
6. [Common Mistakes](#common-mistakes)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Comparison

### Side-by-Side Overview

| Feature | Security Group | NACL |
|---------|---|---|
| **Scope** | Instance-level | Subnet-level |
| **Applies to** | Individual EC2, RDS, ALB | All instances in subnet |
| **Stateful?** | ✅ Yes | ❌ No (stateless) |
| **Allow/Deny** | Allow only | Allow & Deny |
| **Rule Processing** | All evaluated | Processed in order |
| **Rule Priority** | Not numbered | Numbered (10, 20, 30...) |
| **Default Action** | Implicit deny all | Allow all (default) |
| **Instances per resource** | Multiple | N/A |
| **Performance Impact** | Minimal | Minimal |
| **Ease of Use** | ⭐⭐⭐⭐⭐ Easier | ⭐⭐⭐ Moderate |

### Traffic Flow

```
Incoming Internet Traffic
    ↓
NACL (subnet-level filter)
    ↓
Security Group (instance-level filter)
    ↓
Instance

If either NACL or SG blocks → Traffic DENIED
Both must allow for traffic to pass
```

---

## Detailed Explanation

### Security Group (Instance-Level Firewall)

#### What is a Security Group?

A **Security Group** is like a firewall attached to an **individual instance**. It controls who can:
- Send traffic TO the instance (inbound)
- Send traffic FROM the instance (outbound)

#### Key Characteristics

**1. Stateful** - Most Important!

**What does "Stateful" mean?**

Stateful means the security group **remembers connections**. If you allow traffic IN, responses automatically go OUT without needing a rule.

**Real-World Analogy:**
```
You're at home (EC2 instance):
├─ Inbound rule: Allow visitors during business hours (9am-5pm)
└─ Stateful behavior: When visitor leaves, door automatically unlocks for them
                      (You don't need a separate "exit rule")

Phone Call Analogy:
├─ You allow incoming calls (inbound rule)
├─ When caller talks, their response comes back automatically
└─ You don't need separate rule for their voice returning to you
```

**Technical Example:**
```
Client Request (port 80):
Client:1234 → Server:80
    ↓
Server receives request
    ↓
Server sends response back:
Server:80 → Client:1234
    ↓
Response goes through AUTOMATICALLY
(No outbound rule needed for response!)

Why? Because SG is STATEFUL:
├─ It remembers: "Client opened connection on port 80"
└─ It allows response back automatically
```

**2. Only Allow Rules (Implicit Deny)**

**What does "Allow Only" mean?**

Security Groups can ONLY explicitly allow traffic. If something is not allowed, it's automatically denied.

```
Security Group:
├─ Inbound: HTTP (80) from 0.0.0.0/0 → ALLOW ✅
├─ Inbound: HTTPS (443) from 0.0.0.0/0 → ALLOW ✅
├─ Inbound: SSH (22) from 10.0.0.0/8 → ALLOW ✅
├─ Outbound: All traffic (default) → ALLOW ✅
└─ Everything else → Implicit DENY ❌ (can't be changed)

❌ You CANNOT explicitly deny:
   "DENY port 22 from 192.168.1.0/24"
   (This is NOT supported in Security Groups!)

If something is not explicitly allowed → It's denied
```

**Why this limitation?**
```
SG design philosophy:
├─ Simplicity: Only specify what you WANT
├─ Security: Default is deny (whitelist approach)
└─ Use NACL if you need explicit deny at subnet level
```

**3. Multiple Per Instance**

```
Single EC2 Instance
    ├─ Security Group 1: HTTP/HTTPS (web traffic)
    ├─ Security Group 2: SSH (management)
    └─ Security Group 3: Database (port 3306)

All rules from all SGs are evaluated together (OR logic)
```

#### Example: Web Server Security Group

```json
Inbound Rules:
[
  {
    "IpProtocol": "tcp",
    "FromPort": 80,
    "ToPort": 80,
    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]  // HTTP from internet
  },
  {
    "IpProtocol": "tcp",
    "FromPort": 443,
    "ToPort": 443,
    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]  // HTTPS from internet
  },
  {
    "IpProtocol": "tcp",
    "FromPort": 22,
    "ToPort": 22,
    "IpRanges": [{"CidrIp": "10.0.0.0/8"}]  // SSH from office
  }
]

Outbound Rules:
[
  {
    "IpProtocol": "-1",  // All protocols
    "CidrIp": "0.0.0.0/0"  // To anywhere
  }
]
```

---

### NACL (Subnet-Level Firewall)

#### What is a NACL?

A **NACL (Network Access Control List)** is a firewall at the **subnet level**. It controls traffic for **all instances** in that subnet.

#### Key Characteristics

**1. Stateless** - Most Important!

**What does "Stateless" mean?**

Stateless means NACL **doesn't remember connections**. Every packet is treated independently. You must explicitly allow BOTH incoming AND outgoing traffic.

**Real-World Analogy:**
```
Government checkpoint (NACL):
├─ Guard checks: Are you allowed to enter? Check entry list.
├─ You enter ✓
├─ Later: Can you leave? Check exit list separately!
├─ Guard doesn't remember you came in
└─ Must check exit rules again (even though you have entry permission)

Security Guard without memory:
├─ Person arrives: Check rule #100 "Allow entry 9am-5pm" ✓
├─ Person tries to leave: Guard checks rules again
├─ Rule #100 only covers entry, not exit!
├─ Need separate Rule #110 "Allow exit 9am-5pm"
└─ Guard doesn't remember they entered
```

**Technical Example:**
```
Client wants to connect to web server on port 80:

NACL Inbound Rules (Entry checkpoint):
├─ Rule #100: Allow port 80 TCP from 0.0.0.0/0 ✓
└─ Rule #32767: Deny all (implicit)

NACL Outbound Rules (Exit checkpoint - separate!):
├─ Rule #100: Allow port 80 TCP to 0.0.0.0/0 ✓
├─ Rule #110: Allow ephemeral (1024-65535) TCP to 0.0.0.0/0 ✓
└─ Rule #32767: Deny all (implicit)

Why 3 rules?
├─ Rule #100 In: Client sends HTTP request (port 80)
├─ Rule #100 Out: Server sends response back (port 80)
└─ Rule #110 Out: Client sends ACK for response (ephemeral port)

NACL doesn't connect these together—each is evaluated separately!
```

**2. Both Allow and Deny Rules**

**What does "Allow + Deny" mean?**

Unlike Security Groups (allow only), NACLs can BOTH explicitly allow AND explicitly deny traffic.

```
NACL Rules (Allow + Deny):
├─ Rule #100: Allow port 80 from 0.0.0.0/0
├─ Rule #110: DENY port 80 from 192.168.1.0/24 (malicious IPs)
├─ Rule #120: Allow port 443 from 0.0.0.0/0
└─ Rule #32767: DENY all (implicit catch-all)

✅ You CAN explicitly block specific sources!
   (NACL supports both ALLOW and DENY)
```

**Use Case: Block Malicious IPs at Subnet Level**
```
Scenario: Malicious botnet attacking port 80

NACL for Web Subnet:
├─ Rule #100: Allow port 80 from 0.0.0.0/0 (most traffic)
├─ Rule #110: DENY port 80 from 192.0.2.0/24 (botnet IPs)
│            └─ STOP HERE! This rule matches first, traffic blocked
├─ Rule #120: Allow port 80 from 10.0.0.0/16 (internal)
└─ Rule #32767: DENY all (implicit)

How it works:
├─ Normal traffic from 1.2.3.4 → Matches rule #100 → ALLOW ✓
├─ Attack traffic from 192.0.2.5 → Matches rule #110 → DENY ✗
└─ Internal traffic from 10.0.0.5 → Matches rule #120 → ALLOW ✓
```

**3. First Rule Match Wins**

**What does "First Rule Match Wins" mean?**

NACL evaluates rules IN ORDER by rule number. As soon as a rule matches, it stops checking—that rule's action (ALLOW or DENY) is applied.

```
Traffic arrives: Source 192.0.2.5, Port 80

Check rules in order:
├─ Rule #100: Allow 80 from 0.0.0.0/0
│  Does 192.0.2.5 match 0.0.0.0/0? YES
│  But wait... check if more specific rule exists
│
├─ Rule #110: DENY 80 from 192.0.2.0/24
│  Does 192.0.2.5 match 192.0.2.0/24? YES
│  MORE SPECIFIC MATCH! → Use this rule → DENY ✗
│  STOP! Don't check other rules
│
└─ Rule #120, #32767: Never reached
```

**Critical: Rule Number Order Matters!**
```
❌ WRONG ORDER (rule 110 won't work):
├─ Rule #100: Allow port 80 from 0.0.0.0/0
│  (This matches everything, rule 110 never used!)
├─ Rule #110: DENY port 80 from 192.0.2.0/24
│  (Never reached because rule 100 already matched!)
└─ Result: Malicious traffic ALLOWED ✗

✅ CORRECT ORDER (specific first, general later):
├─ Rule #100: DENY port 80 from 192.0.2.0/24
│  (Check malicious IPs first)
├─ Rule #110: Allow port 80 from 0.0.0.0/0
│  (Allow everyone else)
└─ Result: Malicious traffic DENIED ✓
```

**4. One NACL Per Subnet (but can share)**

```
Subnet-1 ← NACL-A
Subnet-2 ← NACL-A (same NACL)
Subnet-3 ← NACL-B (different NACL)
```

#### Example: Web Server NACL

```
Inbound Rules:
├─ Rule #100: Allow HTTP (80) TCP from 0.0.0.0/0
├─ Rule #110: Allow HTTPS (443) TCP from 0.0.0.0/0
├─ Rule #120: Allow SSH (22) TCP from 10.0.0.0/8
├─ Rule #130: Allow ephemeral (1024-65535) TCP from 0.0.0.0/0
└─ Rule #32767: Deny all (implicit)

Outbound Rules:
├─ Rule #100: Allow HTTP (80) TCP to 0.0.0.0/0
├─ Rule #110: Allow HTTPS (443) TCP to 0.0.0.0/0
├─ Rule #120: Allow ephemeral (1024-65535) TCP to 0.0.0.0/0
└─ Rule #32767: Deny all (implicit)
```

---

## Comprehensive Comparison Table

```
┌─────────────────────────────────────────────────────────────────────┐
│ FEATURE               SECURITY GROUP    NACL                        │
├─────────────────────────────────────────────────────────────────────┤
│ Scope                 Instance-level    Subnet-level                │
│                                                                     │
│ Stateful/Stateless    STATEFUL          STATELESS                  │
│ • Remember connections ✅ Yes           ❌ No                       │
│ • Response auto-allowed ✅ Yes          ❌ No                       │
│ • Need return rule?   ❌ No             ✅ Yes                      │
│                                                                     │
│ Rules:                ALLOW ONLY        ALLOW + DENY                │
│ • Can explicitly allow ✅ Yes           ✅ Yes                      │
│ • Can explicitly deny  ❌ No            ✅ Yes                      │
│ • Default (no rules)   ❌ Deny all      ✅ Allow all               │
│                                                                     │
│ Rule Processing:      ALL EVALUATED     FIRST MATCH WINS            │
│ • How rules applied    All rules        Stop at first match         │
│ • Rule order matters   ❌ No            ✅ Yes (100,110,120)        │
│ • Rule numbering      ❌ No numbers    ✅ Yes (numbered)           │
│                                                                     │
│ Ease of Use           ⭐⭐⭐⭐⭐ Easier    ⭐⭐⭐ Moderate              │
│ Best For              Instance control  Subnet protection           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## When to Use Each

### Use Security Group When

✅ **Instance-level control needed**
✅ **Managing individual services** (web server, database, cache)
✅ **Need instance-specific rules**
✅ **Multiple applications on same subnet**
✅ **Most common use case**
✅ **Simple "allow" rules**
✅ **Benefit from stateful nature**
✅ **Application-level access control**

**Example**: Three web servers on same subnet, each needing different ports

### Use NACL When

✅ **Subnet-wide protection needed**
✅ **Need to explicitly DENY certain traffic**
✅ **Blocking malicious IPs at subnet boundary**
✅ **Additional security layer** (defense in depth)
✅ **Compliance requirements**
✅ **Complex network filtering**
✅ **Performance optimization** (filter at subnet level)
✅ **Want to block specific traffic patterns**

**Example**: Block known malicious IP range from entire subnet

### Use BOTH Together (Recommended)

```
Defense in Depth Approach:

┌─────────────────────────────┐
│ Subnet (with NACL)          │
│ ├─ First line of defense    │
│ │                           │
│ ├─ Instance 1 (SG-1)        │
│ │  └─ Second line           │
│ │                           │
│ ├─ Instance 2 (SG-2)        │
│ │  └─ Second line           │
│ │                           │
│ └─ Blocked IP space here    │
│    (denied at NACL level)   │
│                             │
└─────────────────────────────┘

Benefits:
- Bad traffic blocked at subnet boundary (NACL)
- Application-level control (SG)
- Multiple layers = more secure
```

---

## Decision Tree

```
Question: What level of control do you need?

┌─ Instance-level?
│  └─ USE SECURITY GROUP
│     (control individual resources)
│
└─ Subnet-level?
   └─ Need to explicitly DENY?
      ├─ YES → USE NACL (with SG)
      │        (both layers of defense)
      │
      └─ NO → Just use SG
               (stateful is easier)

Common Pattern:
├─ DEFAULT: Security Group only
├─ PRODUCTION: Security Group + NACL
├─ COMPLIANCE: Security Group + NACL + WAF
└─ HIGHLY SENSITIVE: All above + VPC Flow Logs + Monitoring
```

---

## Practical Examples

### Example 1: Simple Web Application (Dev)

```
Requirements:
- Web server needs HTTP/HTTPS
- Developers need SSH
- No need for subnet-level filtering

Solution: Security Group Only

Web Server Security Group:
├─ Inbound:
│  ├─ HTTP (80) from 0.0.0.0/0
│  ├─ HTTPS (443) from 0.0.0.0/0
│  └─ SSH (22) from 203.0.113.0/32  (dev office)
└─ Outbound:
   └─ All traffic (default)

Use NACL: Default (allow all)
```

### Example 2: E-Commerce Production (Multi-Tier)

```
Requirements:
- Public subnet: web servers only
- Private subnet: database only
- Block known malicious IPs
- Prevent east-west traffic between tiers
- Audit-ready

Solution: Security Group + Custom NACL (both)

PUBLIC SUBNET (Web Tier):

  NACL:
  ├─ Allow HTTP (80) from 0.0.0.0/0
  ├─ Allow HTTPS (443) from 0.0.0.0/0
  ├─ Allow SSH (22) from 10.0.0.0/8 (internal only)
  ├─ Allow ephemeral (1024-65535) from 0.0.0.0/0
  ├─ DENY from 192.0.2.0/24 (malicious IPs)
  └─ Deny all (implicit)

  SG (Web Servers):
  ├─ HTTP (80) from 0.0.0.0/0
  ├─ HTTPS (443) from 0.0.0.0/0
  └─ SSH (22) from 10.0.0.0/8

PRIVATE SUBNET (Database Tier):

  NACL:
  ├─ Allow MySQL (3306) from 10.0.1.0/24 (app subnet only)
  ├─ Allow ephemeral (1024-65535) from 0.0.0.0/0
  └─ Deny all (implicit)

  SG (Database):
  ├─ MySQL (3306) from sg-web (web SG, by reference)
  └─ Deny SSH (no SSH to databases!)
```

### Example 3: On-Premises + AWS Hybrid

```
Requirements:
- Office network needs access to private subnet
- Use VPN instead of internet
- Secure tunnel encryption
- No bastion host needed

Solution: Security Group + NACL + VPN Gateway

NACL (Private Subnet):
├─ Allow TCP from 10.0.0.0/8 (from public subnet)
├─ Allow TCP 500/4500 (VPN) from 192.0.2.0/24 (office)
├─ Allow ephemeral responses
└─ Deny all (implicit)

SG (Private Servers):
├─ MySQL (3306) from 10.0.1.0/24 (app tier)
├─ Allow responses (stateful)
└─ NO inbound from internet (secure!)

Result: Secure tunnel, no internet exposure
```

### Example 4: Deep Dive - How NACL Rules Actually Work

**Understanding Rule Flow with Real Traffic**

```
Inbound Rules:
#100: Allow TCP port 80    from 0.0.0.0/0 (HTTP)
#110: Allow TCP port 443   from 0.0.0.0/0 (HTTPS)
#120: Allow TCP port 22    from 10.0.0.0/8 (SSH)
#130: Allow TCP 1024-65535 from 0.0.0.0/0 (ephemeral)
#32767: DENY all (implicit, catch-all)

Outbound Rules:
#100: Allow TCP 1-65535 to 0.0.0.0/0 (all responses)
#32767: DENY all (implicit)
```

#### Breaking Down Each Rule:

**Inbound Rules** (Traffic coming INTO subnet):

```
Rule #100 (HTTP - First Match Wins):
├─ Traffic: Source IP, Port 80
├─ Matches rule #100? → YES → ALLOW ✓
├─ Stops checking here (first match wins!)
└─ Client can reach web server on port 80

Rule #110 (HTTPS):
├─ Traffic: Source IP, Port 443
├─ Doesn't match rule #100 (port is 443, not 80)
├─ Matches rule #110 → ALLOW ✓
└─ Client can reach HTTPS server on port 443

Rule #120 (SSH):
├─ Traffic: Source IP, Port 22
├─ Doesn't match rules 100-110 (port is 22)
├─ Matches rule #120 → ALLOW ✓
├─ BUT: Source MUST be from 10.0.0.0/8 (internal only)
├─ External SSH requests → NOT ALLOWED ✗
└─ Only internal networks can SSH

Rule #130 (Ephemeral):
├─ Traffic: Response packets from port 1024-65535
├─ Matches rule #130 → ALLOW ✓
├─ Why? Server sends responses back on random ports
├─ Example: Client connects to port 80
│          Server responds from port 34567
│          This matches rule #130 → ALLOWED ✓
└─ CRITICAL: This enables stateless responses!

Rule #32767 (Catch-All):
├─ Anything not matched by #100-130 → DENY ✗
├─ Example: Port 3306 (MySQL) from anywhere → DENIED
├─ Example: Port 9200 (Elasticsearch) → DENIED
└─ Default: Block everything not explicitly allowed
```

**Outbound Rules** (Traffic leaving subnet):

```
Rule #100 (All TCP responses):
├─ Allows: Any TCP port (1-65535) TO anywhere (0.0.0.0/0)
├─ Purpose: Let responses from inbound connections go out
├─ Example: Client → Port 80 → Server → Response to port 34567 ✓
├─ Example: Server → Port 80 → Client's browser ✓
└─ Connects with inbound rule #130!

Rule #32767 (Catch-All):
├─ Block everything not allowed
├─ Example: Server can't initiate outbound to port 3306 ❌
├─ Example: Server can't reach external database ❌
└─ Unless you add explicit outbound rule
```

#### Real Request Flow:

```
Client makes HTTP request from 203.0.113.5:54321 → Server on port 80

STEP 1: INBOUND (Client → Server on port 80):
├─ Rule #100 check: Port 80, source 0.0.0.0/0
├─ Does 203.0.113.5:54321 match? YES! → ALLOW ✓
└─ Request passes through to EC2 instance

STEP 2: SERVER PROCESSES REQUEST:
└─ Application generates response

STEP 3: OUTBOUND (Server → Client):
├─ Server responds from 172.31.1.10:80 → Client on port 54321
├─ Rule #100 check: Allow TCP 1-65535 to 0.0.0.0/0
├─ Does outbound match? YES! → ALLOW ✓
└─ Response passes back to client ✓

RESULT: Client gets response ✓
```

#### Why Both Inbound AND Outbound Rules?

```
NACL is STATELESS (no memory):

❌ WITHOUT outbound rules:
├─ Client request → Inbound rule #100 → ALLOWED ✓
├─ Server response → Outbound rule #32767 → DENIED ❌
└─ Client never gets response (broken connection!)

✅ WITH outbound rules:
├─ Client request → Inbound rule #100 → ALLOWED ✓
├─ Server response → Outbound rule #100 → ALLOWED ✓
└─ Client gets response (working connection!)
```

#### Key Insight: Complete Conversation Path

```
These rules create a complete 2-way conversation:

Inbound #100:
└─ Let HTTP requests IN (port 80) ←

Inbound #130:
└─ Let response packets IN (ephemeral ports 1024-65535) ←

Outbound #100:
└─ Let response packets OUT (all TCP ports 1-65535) →

Without this complete path:
├─ Missing inbound #100? → Request blocked ✗
├─ Missing inbound #130? → Response blocked ✗
└─ Missing outbound #100? → Response blocked ✗

Stateless = Must explicitly allow BOTH directions!
```

---

## Common Mistakes

### ❌ Mistake 1: Opening SSH to Entire Internet

```
DANGEROUS:
┌─────────────────────────────────┐
│ Security Group                  │
│ Inbound: SSH (22)               │
│ Source: 0.0.0.0/0 (EVERYONE!)   │
└─────────────────────────────────┘

Risk: Brute force attacks, unauthorized access

CORRECT:
┌─────────────────────────────────┐
│ Security Group                  │
│ Inbound: SSH (22)               │
│ Source: 203.0.113.128/32        │
│         (your office only)      │
└─────────────────────────────────┘
```

### ❌ Mistake 2: Forgetting Outbound Rules in NACL

```
BROKEN:
NACL Inbound Rules:
├─ Rule #100: Allow port 80 TCP from 0.0.0.0/0 ✓
└─ Rule #32767: Deny all (implicit)

NACL Outbound Rules:
├─ Rule #32767: Deny all (implicit) ✗
    (No explicit allow!)

Problem: Responses can't go back to client!

CORRECT (COMPLETE NACL RULES):
NACL Ingress (Inbound) Rules:
├─ Rule #100: Allow TCP port 80 from 0.0.0.0/0 (requests) ✓
├─ Rule #110: Allow TCP 1024-65535 from 0.0.0.0/0 (client ACKs/responses) ✓
└─ Rule #32767: DENY all (implicit catch-all)

NACL Egress (Outbound) Rules:
├─ Rule #100: Allow TCP port 80 to 0.0.0.0/0 (responses) ✓
├─ Rule #110: Allow TCP 1024-65535 to 0.0.0.0/0 (server responses on ephemeral) ✓
└─ Rule #32767: DENY all (implicit catch-all)

Why both directions?
├─ NACL is STATELESS (no memory!)
├─ Ingress #100: Client request comes IN on port 80
├─ Egress #100: Server response goes OUT on port 80
├─ Ingress #110: Client sends ACK back on ephemeral port
└─ Egress #110: Server responds on ephemeral port
```

### ❌ Mistake 3: Forgetting Ephemeral Ports

**What Are Ephemeral Ports?**

Ephemeral = "Temporary" or "Short-lived"

**Definition**: Ephemeral ports are temporary, high-numbered ports (1024-65535) that operating systems automatically assign to client connections.

```
OS assigns ephemeral port automatically:

Client Connection Process:

Step 1: Client wants to connect to port 80
  └─ OS assigns random port to client (e.g., 54321)

Step 2: Client makes request
  └─ Source: ClientIP:54321 → Destination: ServerIP:80

Step 3: Server responds
  └─ Source: ServerIP:80 → Destination: ClientIP:54321
  └─ NACL must allow this return port!

Why random high ports?
├─ Avoid conflicts (multiple connections same client)
├─ Automatically managed by OS (not in app code)
└─ Range 1024-65535 reserved for this (1-1023 reserved)
```

**The Problem (Without Ephemeral Port Rule):**

```
Client makes HTTP request:
Client IP:54321 → Server IP:80
       ↑                 ↓
  (Ephemeral)      (Well-known)

Server responds:
Server IP:80 → Client IP:54321
               ↑
         (BLOCKED by NACL! - Not allowed!)

Result: Client gets no response! ❌
```

**The Solution (With Ephemeral Port Rule):**

```
NACL Outbound Rule: Allow TCP 1024-65535 to 0.0.0.0/0

Server can now respond:
Server IP:80 → Client IP:54321 ✅
               (This port range is allowed!)

Result: Client gets response! ✅
```

**Real-World Analogy:**

```
Phone System Analogy:

Traditional Phone (port 80):
├─ Main switchboard: Phone #80 (well-known, published)
└─ Caller dials: 1-800-COMPANY

Return Path (Ephemeral):
├─ Receptionist uses random extension: 54321
├─ Caller's phone rings on 54321
└─ Must ALLOW return calls on this extension!

Without allowing 1024-65535:
├─ Receptionist tries to call back
├─ Extension blocked by rules
└─ Caller never receives response
```

**Complete NACL Rules for HTTP:**

```
To handle HTTP request/response with stateless NACL:

Inbound Rules (Internet → Server):
├─ Rule #100: Allow TCP 80 (HTTP requests coming in)
└─ Rule #110: Allow TCP 1024-65535 (responses might arrive on any port)
   Why #110? Client might send data back on ephemeral port

Outbound Rules (Server → Internet):
├─ Rule #100: Allow TCP 80 (responses going out on port 80)
└─ Rule #110: Allow TCP 1024-65535 (must respond to client's random port)
   Why #110? Server must respond to client's ephemeral port
```

**Practical Timeline:**

```
1:00:00 - Client: 203.0.113.5:54321 → Server:80
         (Client OS picks random port 54321)
         ├─ NACL Inbound Rule #100 matches (port 80)
         └─ Request allowed ✓

1:00:01 - Server: 172.31.1.10:80 → Client:203.0.113.5:54321
         (Server responds on port 80 to client's port 54321)
         ├─ NACL Outbound Rule #110 matches (1024-65535)
         └─ Response allowed ✓

1:00:02 - Client receives HTTP response
         └─ Success! ✅


WITHOUT Rule #110:

1:00:00 - Client: 203.0.113.5:54321 → Server:80
         ├─ NACL Inbound Rule #100 matches
         └─ Request allowed ✓

1:00:01 - Server: 172.31.1.10:80 → Client:203.0.113.5:54321
         ├─ Checks NACL Outbound rules
         ├─ Doesn't match rule #100 (port 80, but direction is OUT)
         ├─ Matches rule #32767 (DENY all - catch-all)
         └─ Response BLOCKED ❌

1:00:02 - Client: Still waiting for response
         └─ Timeout / Connection hangs ❌
```

**The Correct Way:**

```
❌ WRONG:
NACL Outbound: Allow port 80 only
(return traffic on port 54321 is BLOCKED!)

✅ CORRECT:
NACL Inbound:
├─ Rule #100: Allow TCP 80 from 0.0.0.0/0
└─ Rule #110: Allow TCP 1024-65535 from 0.0.0.0/0

NACL Outbound:
├─ Rule #100: Allow TCP 80 to 0.0.0.0/0
└─ Rule #110: Allow TCP 1024-65535 to 0.0.0.0/0
```

**Key Insight: Stateless = Must Explicitly Allow Both Directions**

```
Security Group (Stateful):
├─ Inbound: Allow port 80
└─ Outbound: Automatic! (response auto-allowed)

NACL (Stateless):
├─ Inbound: Allow port 80 + Allow ephemeral ports
└─ Outbound: Allow port 80 + Allow ephemeral ports
   (Every direction must be explicit!)
```

### ❌ Mistake 4: Too Restrictive NACL (Performance)

```
NACL Rules: 1000+ rules, checking each...

Overhead: Every packet checked against 1000 rules!

Better Approach:
├─ Keep NACL simple (5-10 rules)
├─ Use SG for detailed control
└─ Only block specific IPs in NACL
```

### ❌ Mistake 5: Duplicating Control

```
REDUNDANT:
┌─ NACL: Deny 192.0.2.0/24
├─ SG: Deny 192.0.2.0/24
└─ Result: Works, but redundant

BETTER:
┌─ NACL: Deny 192.0.2.0/24 (layer 1)
├─ SG: Allow specific ports (layer 2, simpler)
└─ Result: Cleaner, easier to maintain
```

---

## Troubleshooting

### Problem: "Connection Timed Out"

**Cause**: Traffic blocked somewhere

**Diagnostic steps**:

```bash
# 1. Check Security Group
aws ec2 describe-security-groups --group-ids sg-xxx

# 2. Check NACL
aws ec2 describe-network-acls --filters \
  Name=association.subnet-id,Values=subnet-xxx

# 3. Check route table
aws ec2 describe-route-tables --filters \
  Name=association.subnet-id,Values=subnet-xxx

# 4. Test with VPC Flow Logs
aws ec2 describe-flow-logs --filters Name=resource-id,Values=eni-xxx

# 5. Try different IP/port
# If different IP works, it's NACL
# If same source IP always fails, it's SG
```

### Problem: Rule Not Working

```
You created a rule but it's not taking effect

Causes:
1. Rule number too high (evaluated after DENY)
   ├─ Rule #100: DENY all from 0.0.0.0/0
   └─ Rule #200: ALLOW from 10.0.0.0/8
   Problem: Rule 100 matches first!

2. SG/NACL attached to wrong resource
   ├─ NACL attached to wrong subnet?
   └─ SG attached to wrong instance?

3. Rule syntax error
   ├─ Wrong protocol (-1 vs tcp)
   └─ Wrong port range

Solution:
├─ Verify rule numbers (deny after allow)
├─ Verify attachments
├─ Test with VPC Flow Logs
└─ Check AWS console rule details
```

### Problem: "Too Many Requests" / Throttling

```
NACL Rules: 300+

Solution:
├─ Consolidate rules (use CIDR ranges)
├─ Limit to 100 rules per NACL
├─ Use SG for detailed control
└─ Consider using AWS Network Firewall
```

---

## Best Practices

### Security Best Practices

```
SECURITY GROUPS:
☐ Default: Deny all inbound, allow needed traffic only
☐ SSH: Restrict to office IP (not 0.0.0.0/0)
☐ Use SG references (sg-xxx) instead of IPs when possible
☐ Database: Only allow from app tier SG
☐ Regular audit: Remove unused SG rules
☐ Name your SGs clearly (e.g., "web-tier-sg")
☐ Use descriptions for each rule (why allow this?)

NACLs:
☐ Keep simple: 5-10 rules max (easier to maintain)
☐ Use only for subnet-level blocking
☐ Numbers: 100, 110, 120... (space between for inserts)
☐ Last rule: always explicit deny (#32767)
☐ Document rule purpose
☐ Test deny rules thoroughly
☐ Review monthly for unused rules

COMBINED:
☐ SG = primary control (stateful, easier)
☐ NACL = secondary layer (defense in depth)
☐ Never rely on only one
☐ Audit both monthly
☐ Document traffic flow diagram
```

### Operational Best Practices

```
NACL NUMBERING:
Bad:  Rules 1, 2, 3, 4, 5 (no room to insert)
Good: Rules 100, 110, 120, 130, 140

Why? Easier to insert new rules:
├─ Need rule between 100 and 110?
├─ Can use 105!
└─ Avoids renumbering all rules

RULE ORDERING:
☐ Place specific rules first (higher priority)
├─ Rule #100: Allow 192.0.2.5/32 (specific)
├─ Rule #110: Allow 192.0.2.0/24 (general)
└─ Rule #32767: Deny all (catch-all)

DOCUMENTATION:
☐ Add "Sid" (statements ID) to explain rules
☐ Keep change log
☐ Diagram your network
☐ Document rule priorities
☐ Maintain a "Runbook" for common changes

MONITORING:
☐ Enable VPC Flow Logs
☐ Set CloudWatch alarms for denied traffic
☐ Review logs weekly
☐ Investigate sudden spikes
```

### Cost Optimization

```
☐ Don't use NACL for temporary blocks (use SG)
☐ Don't create multiple NACLs per subnet (consolidate)
☐ Remove unused rules
☐ Simplify complex rules
☐ Review rules quarterly
☐ Use SG for most control (no additional cost)
```

---

## Making Your Webserver Accessible

### Scenario A: From Your On-Premise PC

```plaintext
Network Diagram:
Your PC (192.0.2.1)
    ↓ (internet)
AWS VPC (10.0.0.0/16)
    ├─ Public Subnet (10.0.1.0/24)
    └─ Web Server (10.0.1.10, port 5000)

Configuration:
1. Security Group Configuration:
   ├─ Inbound rule:
   │  ├─ Type: Custom TCP
   │  ├─ Port: 5000
   │  └─ Source: YOUR_IP/32  (e.g., 192.0.2.1/32)
   └─ Outbound: Allow all (default)

2. NACL Configuration (if using custom NACL):
   ├─ Inbound rule:
   │  ├─ Rule #: 100
   │  ├─ Type: Custom TCP
   │  ├─ Port: 5000
   │  ├─ Source: YOUR_IP/32
   │  └─ Allow/Deny: ALLOW
   ├─ Outbound rule:
   │  ├─ Rule #: 100
   │  ├─ Type: Custom TCP
   │  ├─ Port: ephemeral (32768-65535)
   │  ├─ Destination: YOUR_IP/32
   │  └─ Allow/Deny: ALLOW
   └─ Last: Rule #32767 Deny all
```

### Scenario B: From the Internet (Everyone)

```plaintext
Network Diagram:
Internet (0.0.0.0/0, anyone)
    ↓
AWS VPC (10.0.0.0/16)
    ├─ Public Subnet (10.0.1.0/24)
    └─ Web Server (10.0.1.10, port 5000)

Configuration:
1. Security Group Configuration:
   ├─ Inbound rule:
   │  ├─ Type: Custom TCP
   │  ├─ Port: 5000
   │  └─ Source: 0.0.0.0/0 (everyone)
   └─ Outbound: Allow all (default)

2. NACL Configuration (if using custom NACL):
   ├─ Inbound rule:
   │  ├─ Rule #: 100
   │  ├─ Type: Custom TCP
   │  ├─ Port: 5000
   │  ├─ Source: 0.0.0.0/0
   │  └─ Allow/Deny: ALLOW
   ├─ Outbound rule:
   │  ├─ Rule #: 100
   │  ├─ Type: Custom TCP
   │  ├─ Port: ephemeral (32768-65535)
   │  ├─ Destination: 0.0.0.0/0
   │  └─ Allow/Deny: ALLOW
   └─ Last: Rule #32767 Deny all

⚠️ WARNING: Opening to 0.0.0.0/0 means:
   - Attackers can access your server
   - Consider firewall rules (WAF)
   - Use HTTPS not HTTP
   - Rate limit connections
```

### Scenario C: Advanced - SSH Port Forwarding

See the separate guide: `How-to-make-webserver-on-edge-node-avaialble-on-myon-premise-pc.md`

---

## Summary Table

### Quick Reference: SG vs NACL

```
┌────────────────────────────────────────────────────────┐
│ WHEN...                          USE...    REASON       │
├────────────────────────────────────────────────────────┤
│ Need instance-level control      SG        Instance     │
│ Need subnet-level control        NACL      All subnet   │
│ Need to explicitly DENY          NACL      Allow/Deny   │
│ Need simplicity                  SG        Stateful     │
│ Multiple apps on same subnet     SG        Per instance │
│ Block malicious IP               NACL      Layer 1      │
│ Need both security + simplicity  Both      Defense      │
└────────────────────────────────────────────────────────┘
```

---

## Best Practices

1. For internet-facing applications, always use both NACL and Security Groups
2. Use Security Groups as your primary access control
3. Use NACLs as a backup security layer
4. Always follow the principle of least privilege
5. For internet access, consider using AWS ALB/NLB instead of direct access
6. Regularly audit and update your rules

```plaintext
1. Security Group Configuration:
- Add inbound rule:
  Type: Custom TCP
  Port: 5000
  Source: Your on-premise IP address

2. NACL Configuration (if using custom NACL):
- Add inbound rule:
  Rule #: 100 (or any number)
  Type: Custom TCP
  Port: 5000
  Source: Your on-premise IP address
  Allow/Deny: ALLOW
- Add outbound rule:
  Rule #: 100
  Type: Custom TCP
  Port: ephemeral (32768-65535)
  Destination: Your on-premise IP address
  Allow/Deny: ALLOW
```

B) From the Internet:

```plaintext
1. Security Group Configuration:
- Add inbound rule:
  Type: Custom TCP
  Port: 5000
  Source: 0.0.0.0/0 (all IPs)

2. NACL Configuration (if using custom NACL):
- Add inbound rule:
  Rule #: 100
  Type: Custom TCP
  Port: 5000
  Source: 0.0.0.0/0
  Allow/Deny: ALLOW
- Add outbound rule:
  Rule #: 100
  Type: Custom TCP
  Port: ephemeral (32768-65535)
  Destination: 0.0.0.0/0
  Allow/Deny: ALLOW
```

Best Practices:

1. For internet-facing applications, always use both NACL and Security Groups
2. Use Security Groups as your primary access control
3. Use NACLs as a backup security layer
4. Always follow the principle of least privilege
5. For internet access, consider using AWS ALB/NLB instead of direct access
6. Regularly audit and update your rules
