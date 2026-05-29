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

What does "stateful" mean?

```
Scenario: Client connects to web server on port 80

Outbound Rule: Allow traffic to port 80
Inbound Rule: Allow responses back

Stateful SG (Security Group):
  Client → (outbound port 80) → Server
  Server → (response automatically allowed back) ✅
  No inbound rule needed for responses!

Stateless (NACL):
  Client → (outbound port 80) → Server
  Server → Must have explicit rule for response
  Response port 1024-65535 (ephemeral) must be allowed
```

**2. Only Allow Rules (Implicit Deny)**

```
Security Group:
├─ Inbound: HTTP (80) from 0.0.0.0/0
├─ Inbound: HTTPS (443) from 0.0.0.0/0
├─ Inbound: SSH (22) from 10.0.0.0/8
├─ Outbound: All traffic (default)
└─ Implicit Deny: Everything else

You cannot explicitly deny in a Security Group!
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

```
Inbound and Outbound are completely separate!

Client wants to connect to web server on port 80:

NACL Inbound Rules:
├─ Rule #100: Allow port 80 TCP from 0.0.0.0/0
└─ Rule #32767: Deny all (implicit)

NACL Outbound Rules:
├─ Rule #100: Allow port 80 TCP to 0.0.0.0/0
├─ Rule #110: Allow ephemeral (1024-65535) TCP to 0.0.0.0/0
└─ Rule #32767: Deny all (implicit)

Both must be explicitly allowed!
```

**2. Both Allow and Deny Rules**

Unlike Security Groups, NACLs can **explicitly deny**:

```
NACL Rules:
├─ Rule #100: Allow port 80 from 0.0.0.0/0
├─ Rule #110: DENY port 80 from 192.168.1.0/24 ← Explicit deny!
├─ Rule #120: Allow HTTPS from 0.0.0.0/0
└─ Rule #32767: Deny all (implicit)

First matching rule wins!
If traffic matches rule 110 (deny), it's blocked immediately
```

**3. First Rule Match Wins**

```
Traffic arrives: Source 192.168.1.5, port 80

Check rules in order:
Rule #100: Allow port 80 from 0.0.0.0/0
  → MATCHES! Allowed ✓

Rule #110: DENY port 80 from 192.168.1.0/24
  → Never reaches here (already matched rule 100)

This is why rule numbers matter!
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

CORRECT:
NACL Inbound Rules:
├─ Rule #100: Allow port 80 TCP from 0.0.0.0/0 ✓

NACL Outbound Rules:
├─ Rule #100: Allow port 80 TCP to 0.0.0.0/0 ✓
├─ Rule #110: Allow ephemeral (1024-65535) TCP ✓
└─ Rule #32767: Deny all (implicit)
```

### ❌ Mistake 3: Forgetting Ephemeral Ports

```
Client connects to web server (port 80):
Client port 1234 → Server port 80

Server response comes back:
Server port 80 → Client port 1234

In NACL, you must ALLOW this return traffic:

❌ WRONG:
NACL Outbound: Allow port 80 only
(return traffic on port 1234 is BLOCKED!)

✅ CORRECT:
NACL Outbound: Allow port 80 TCP
NACL Outbound: Allow ephemeral (1024-65535) TCP
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
