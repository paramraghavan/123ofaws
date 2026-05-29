# Making Your Webserver Accessible: On-Premise PC to AWS Edge Node

> **Complete Guide**: Learn multiple methods to access web servers running on AWS edge nodes (Outposts, Wavelength, Local Zones) from your on-premises computers. Includes security considerations and step-by-step tutorials for beginners through advanced users.

---

## Table of Contents

1. [Overview: Access Methods](#overview)
2. [Method 1: Direct Network Access (NACL/SG)](#method-1-direct-network-access)
3. [Method 2: SSH Port Forwarding (Recommended)](#method-2-ssh-port-forwarding)
4. [Method 3: VPN Gateway](#method-3-vpn-gateway)
5. [Method 4: AWS Systems Manager](#method-4-aws-systems-manager)
6. [Comparison of Methods](#comparison-of-methods)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### The Problem

Your web server runs on AWS edge node at port 5000:
```
AWS Edge Node (Outposts/Wavelength/Local Zone)
    ├─ Private IP: 10.0.0.50
    ├─ Port: 5000 (web server running)
    └─ Problem: How to access from home/office?
```

### Solutions Available

| Method | Ease | Security | Cost | Setup Time |
|--------|------|----------|------|-----------|
| **Direct Access (NACL/SG)** | ⭐⭐⭐ Easy | ⭐ Low | Free | 5 min |
| **SSH Port Forwarding** | ⭐⭐⭐⭐ Easiest | ⭐⭐⭐⭐⭐ Best | Free | 10 min |
| **VPN Gateway** | ⭐⭐ Complex | ⭐⭐⭐⭐⭐ Best | $$ | 1 hour |
| **AWS Systems Manager** | ⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐⭐ Best | Free | 10 min |

---

## Method 1: Direct Network Access (NACL/SG)

### When to Use
- Quick testing/development
- Single developer access
- Temporary access needed

### Security Level
⚠️ **Lower security** - your IP exposed on internet

### Setup (Beginner)

**Step 1: Find Your Public IP**

```bash
# On your on-premise PC
curl https://ifconfig.me
# Output: 203.0.113.45 (example)
```

**Step 2: Configure Security Group**

```bash
# For AWS edge node
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 5000 \
  --cidr 203.0.113.45/32  # Your IP
```

Or via AWS Console:
```
VPC → Security Groups → Select SG
  → Inbound Rules → Add Rule
    Port: 5000
    Source: 203.0.113.45/32 (your IP)
```

**Step 3: Configure NACL (if custom NACL)**

```bash
aws ec2 create-network-acl-entry \
  --network-acl-id acl-0123456789abcdef0 \
  --rule-number 100 \
  --protocol tcp \
  --port-range FromPort=5000,ToPort=5000 \
  --cidr-block 203.0.113.45/32 \
  --ingress
```

**Step 4: Access the Web Server**

```bash
# From your PC
curl http://edge-node-public-ip:5000

# In browser
http://edge-node-public-ip:5000
```

### Problems with This Method

❌ Your home/office IP exposed on internet
❌ Hard to manage multiple users
❌ Not suitable for production
❌ Security risk if IP becomes known

---

## Method 2: SSH Port Forwarding (Recommended)

### Why This Method is Best

✅ **Secure**: Traffic encrypted in SSH tunnel
✅ **Easy**: No AWS configuration needed
✅ **Flexible**: Works through corporate firewalls
✅ **Free**: No additional AWS costs
✅ **Temporary**: Only while tunnel is active
✅ **Auditable**: SSH logs show all connections

### How SSH Port Forwarding Works

```
Your PC (local port 8080)
    ↓ (SSH tunnel - encrypted)
Edge Node (SSH server on port 22)
    ↓ (local connection - not encrypted)
Web Server (port 5000 - local only)

Result:
  - You access: localhost:8080
  - Reaches: localhost:5000 on edge node
  - Secure: encrypted SSH tunnel
```

### Setup (Beginner - 5 minutes)

**Step 1: Have SSH Key**

```bash
# Check if you have key
ls ~/.ssh/id_rsa

# If not, create one
ssh-keygen -t rsa -b 2048
# Press enter for default location
# Optionally add passphrase
```

**Step 2: Start SSH Port Forwarding**

```bash
# Basic command
ssh -L 8080:localhost:5000 user@edge-node-ip

# With no remote command execution
ssh -L 8080:localhost:5000 user@edge-node-ip -N

# Explanation:
# -L = Local port forwarding
# 8080 = Your local port
# localhost:5000 = Edge node local port
# -N = Don't execute remote commands (just forward)
```

**Step 3: Access Web Server**

```bash
# In another terminal
curl http://localhost:8080

# Or in browser
http://localhost:8080
```

**Step 4: Stop Port Forwarding**

```bash
# Press Ctrl+C in the SSH terminal
```

### Setup (Intermediate - SSH Key-Based Authentication)

**Why**: Avoid password prompts every time

**Step 1: Generate SSH Key Pair**

```bash
# Create RSA key pair
ssh-keygen -t rsa -b 2048 -f ~/.ssh/edge-node-key

# Output:
# ~/.ssh/edge-node-key (private key - keep secret!)
# ~/.ssh/edge-node-key.pub (public key - share)
```

**Step 2: Copy Public Key to Edge Node**

```bash
# Method 1 (Easiest - if ssh-copy-id available)
ssh-copy-id -i ~/.ssh/edge-node-key.pub user@edge-node-ip

# Method 2 (Manual)
cat ~/.ssh/edge-node-key.pub | \
  ssh user@edge-node-ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Result: Public key added to ~/.ssh/authorized_keys on edge node
```

**Step 3: Port Forward with SSH Key**

```bash
ssh -i ~/.ssh/edge-node-key \
  -L 8080:localhost:5000 \
  user@edge-node-ip -N
```

### Setup (Advanced - SSH Config)

**Make it even easier**

**Step 1: Edit SSH Config**

```bash
# Edit ~/.ssh/config
nano ~/.ssh/config
```

**Add this:**

```bash
Host edgenode
    HostName 203.0.113.45          # Edge node IP
    User ec2-user                   # SSH username
    IdentityFile ~/.ssh/edge-node-key
    LocalForward 8080 localhost:5000
    ServerAliveInterval 60          # Keep alive
    ServerAliveCountMax 3
```

**Step 2: Simple Command**

```bash
# Instead of long command
ssh -i ~/.ssh/edge-node-key -L 8080:localhost:5000 user@edge-node-ip -N

# Just use:
ssh edgenode -N
```

**Step 3: One-Line Connection (with everything)**

```bash
# Terminal 1: Port forwarding
ssh edgenode -N

# Terminal 2: Access web server
curl http://localhost:8080

# Or automate it:
(ssh edgenode -N &) && sleep 2 && open http://localhost:8080
```

### Advanced: Avoid Password Prompts Entirely

**Step 1: SSH Config (Already Done)**

```bash
# ~/.ssh/config already has IdentityFile
Host edgenode
    HostName edge-node-ip
    User ec2-user
    IdentityFile ~/.ssh/edge-node-key
```

**Step 2: Test SSH (No Password Needed)**

```bash
ssh edgenode

# Should work without asking for password!
# (If asks for passphrase, you added one to the key)
```

**Step 3: Use in Scripts**

```bash
#!/bin/bash
# Script to start port forwarding

# Start SSH tunnel
ssh edgenode -N -f

# Wait for tunnel to be ready
sleep 2

# Open browser
open http://localhost:8080

# When done, close tunnel:
# pkill -f "ssh edgenode"
```

### Advanced: Security - SSH Agent (No Passphrase in Memory)

```bash
# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent (one-time)
ssh-add ~/.ssh/edge-node-key

# Now SSH uses key from agent (safe, not asking for passphrase each time)
ssh edgenode

# Later, stop agent:
ssh-agent -k
```

---

## Method 3: VPN Gateway

### When to Use
- Permanent network connectivity needed
- Multiple on-premises sites
- Multiple AWS users
- Compliance requirements

### Setup Overview

**Step 1: Create Customer Gateway (On-Premises)**

```bash
# Need public IP of your office/site
# Example: 203.0.113.0 (your office network)

aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.0 \
  --bgp-asn 65000
```

**Step 2: Create VPN Gateway (AWS Side)**

```bash
aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64512
```

**Step 3: Attach to VPC**

```bash
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --vpc-id vpc-0123456789abcdef0
```

**Step 4: Create VPN Connection**

```bash
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-0123456789abcdef0 \
  --vpn-gateway-id vgw-0123456789abcdef0
```

### Advantages

✅ Encrypted tunnel (IPsec)
✅ No public IP exposure
✅ Multiple office connections
✅ Permanent (always-on)
✅ Access private subnets

### Disadvantages

❌ Complex to set up
❌ Requires on-premises VPN equipment
❌ AWS costs ($36/month + data)
❌ Ongoing maintenance

---

## Method 4: AWS Systems Manager

### Why This Method is Excellent

✅ **No SSH keys needed** - Uses IAM
✅ **Auditable** - All sessions logged
✅ **Secure** - No internet exposure
✅ **Easy** - Single command
✅ **Free** - No additional costs
✅ **Works through firewall** - Uses HTTPS

### Requirements

1. **IAM Role** on edge node with SSM permissions
2. **Systems Manager Agent** running (pre-installed on most AMIs)
3. **AWS CLI** on your PC

### Setup (Intermediate)

**Step 1: Verify IAM Role on Edge Node**

```bash
# SSH to edge node and check
aws sts get-caller-identity

# Should show role: EC2-Role-with-SSM-Permissions
```

**Step 2: Start Session Manager**

```bash
# From your PC
aws ssm start-session --target i-0123456789abcdef0

# Result: Shell prompt on edge node
ec2-user@ip-10-0-0-50 $
```

**Step 3: Port Forward Through Session**

```bash
# While in Session Manager session
# Run port forward command
ssh -L 8080:localhost:5000 localhost -N

# Wait for prompt, then in another terminal:
curl http://localhost:8080
```

### Or: Direct Port Forwarding via Session Manager

```bash
# Single command (no intermediate SSH)
aws ssm start-session \
  --target i-0123456789abcdef0 \
  --document-name AWS-StartPortForwardingSession \
  --parameters "localPortNumber=8080,portNumber=5000,host=127.0.0.1"
```

---

## Comparison of Methods

### Decision Matrix

```
Scenario A: Quick Testing
  → SSH Port Forwarding (Method 2)
     ✓ 5-minute setup
     ✓ Most secure
     ✓ No AWS config needed

Scenario B: Development (Multiple Users)
  → SSH Port Forwarding + SSH Config (Method 2 Advanced)
     ✓ Easy for team
     ✓ Key-based auth
     ✓ Automatable

Scenario C: Production (Permanent Access)
  → VPN Gateway (Method 3)
     ✓ Always-on
     ✓ Encrypted
     ✓ Scalable for many sites

Scenario D: Audited Environment
  → AWS Systems Manager (Method 4)
     ✓ All sessions logged
     ✓ Audit trail
     ✓ IAM-based access

Scenario E: Testing Without SSH
  → AWS Systems Manager (Method 4)
     ✓ No keys needed
     ✓ Easier onboarding
     ✓ Built-in AWS auth
```

---

## Security Best Practices

### SSH Port Forwarding Security

```
✓ SECURE:
  - Use SSH keys, not passwords
  - Restrict SSH key file permissions: chmod 600 ~/.ssh/ed-node-key
  - Use -N flag (no remote shell)
  - Limit local port to localhost (don't expose on all IPs)
  - Use passphrases on keys (SSH agent for ease)

✗ INSECURE:
  - SSH from home IP to internet-facing server
  - Sharing SSH keys
  - Key permissions: 644 (readable by others)
  - Allowing -N off (full shell access)
  - No passphrases on keys
```

### General Best Practices

```
ALWAYS:
☐ Use encrypted tunnels (SSH, VPN, TLS)
☐ Restrict access to specific IPs (not 0.0.0.0/0)
☐ Use IAM roles instead of access keys
☐ Enable CloudTrail logging
☐ Monitor failed connection attempts
☐ Rotate credentials regularly
☐ Use MFA for sensitive access
☐ Document your network architecture

NEVER:
☐ Expose port 5000 directly to internet
☐ Use telnet (unencrypted)
☐ Share SSH keys
☐ Hardcode credentials in scripts
☐ Allow SSH from 0.0.0.0/0
☐ Disable logging
```

---

## Troubleshooting

### Problem: "Connection Refused"

```
Symptom:
ssh -L 8080:localhost:5000 user@edge-node-ip -N
Error: Connection refused

Causes:
1. Web server not running on port 5000
2. Wrong port number
3. Firewall blocking port 5000

Solutions:
# SSH to edge node and check
ssh user@edge-node-ip

# Check if web server running
ps aux | grep python
netstat -tulpn | grep 5000

# Check if port is correct
curl http://localhost:5000  # From edge node

# Check security group
aws ec2 describe-security-groups --group-ids sg-xxx
```

### Problem: "Permission Denied (publickey)"

```
Symptom:
ssh -i ~/.ssh/edge-node-key user@edge-node-ip
Error: Permission denied (publickey)

Causes:
1. Public key not on edge node
2. Wrong key file
3. Wrong username
4. Wrong IP address

Solutions:
# Verify key is on edge node
ssh user@edge-node-ip
cat ~/.ssh/authorized_keys  # Should contain your public key

# Check permissions
ls -la ~/.ssh/
# Should be: -rw------- (600)

# Copy key again
ssh-copy-id -i ~/.ssh/edge-node-key.pub user@edge-node-ip

# Test with -v flag for debugging
ssh -v -i ~/.ssh/edge-node-key user@edge-node-ip
```

### Problem: "Timeout" After Connecting

```
Symptom:
SSH connection works, but page won't load at localhost:8080

Causes:
1. Port forwarding not working
2. Web server not accessible
3. Security group blocking traffic

Solutions:
# Check port forwarding (should see output)
ssh -vvv -L 8080:localhost:5000 user@edge-node-ip -N

# From edge node, test web server
ssh user@edge-node-ip
curl http://localhost:5000

# Check security group allows SSH
aws ec2 describe-security-groups --group-ids sg-xxx
```

### Problem: "Permission Denied (password)"

```
Symptom:
ssh user@edge-node-ip
Asks for password (not using key)

Causes:
SSH not using the key file you specified

Solutions:
# Explicitly specify key
ssh -i ~/.ssh/edge-node-key user@edge-node-ip

# Add to SSH config
# (See "Setup - Advanced" section)

# Verify key path is correct
ls -la ~/.ssh/edge-node-key
```

---

## Summary: Quick Reference

### Fastest Method (Development)

```bash
# 1. Copy public key (one time)
ssh-copy-id user@edge-node-ip

# 2. Port forward
ssh -L 8080:localhost:5000 user@edge-node-ip -N

# 3. In another terminal
curl http://localhost:8080
```

### Most Secure Method (Production)

```bash
# 1. Set up VPN or Systems Manager (one time)
aws ec2 create-vpn-connection ...

# 2. Access through VPN
# (Always-on, encrypted, auditable)
```

### Best Balance (Teams)

```bash
# 1. Set up SSH config (one time)
# Edit ~/.ssh/config with Host edgenode

# 2. Port forward
ssh edgenode -N

# 3. Access
curl http://localhost:8080
```

---

## Additional Resources

- [AWS EC2 Key Pairs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html)
- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [AWS Client VPN](https://docs.aws.amazon.com/vpn/latest/clientvpn-user/what-is.html)
- [SSH Port Forwarding](https://en.wikipedia.org/wiki/Port_forwarding)

---

**Last Updated**: 2024

**Note:** Code examples are for AWS edge nodes (Outposts, Wavelength, Local Zones). Traditional VPC EC2 instances use similar concepts but may have different configurations for public/private subnets.

<pre class="code-fence" md-src-pos="1534..2006"><div class="code-fence-highlighter-copy-button" data-fence-content="MS4gU2VjdXJpdHkgR3JvdXAgQ29uZmlndXJhdGlvbjoKLSBBZGQgaW5ib3VuZCBydWxlOgogIFR5cGU6IEN1c3RvbSBUQ1AKICBQb3J0OiA1MDAwCiAgU291cmNlOiBZb3VyIG9uLXByZW1pc2UgSVAgYWRkcmVzcwoKMi4gTkFDTCBDb25maWd1cmF0aW9uIChpZiB1c2luZyBjdXN0b20gTkFDTCk6Ci0gQWRkIGluYm91bmQgcnVsZToKICBSdWxlICM6IDEwMCAob3IgYW55IG51bWJlcikKICBUeXBlOiBDdXN0b20gVENQCiAgUG9ydDogNTAwMAogIFNvdXJjZTogWW91ciBvbi1wcmVtaXNlIElQIGFkZHJlc3MKICBBbGxvdy9EZW55OiBBTExPVwotIEFkZCBvdXRib3VuZCBydWxlOgogIFJ1bGUgIzogMTAwCiAgVHlwZTogQ3VzdG9tIFRDUAogIFBvcnQ6IGVwaGVtZXJhbCAoMzI3NjgtNjU1MzUpCiAgRGVzdGluYXRpb246IFlvdXIgb24tcHJlbWlzZSBJUCBhZGRyZXNzCiAgQWxsb3cvRGVueTogQUxMT1c="><img class="code-fence-highlighter-copy-button-icon" data-original-src="vpc" src="http://localhost:63342/markdownPreview/1139199909/vpc?_ijt=c83u7f0o829dhv46iq2tith5n3"/><span class="tooltiptext"></span></div><code class="language-plaintext" md-src-pos="1534..2006"><span md-src-pos="1534..1547"></span><span md-src-pos="1547..1580">1. Security Group Configuration:
</span><span md-src-pos="1580..1600">- Add inbound rule:
</span><span md-src-pos="1600..1619">  Type: Custom TCP
</span><span md-src-pos="1619..1632">  Port: 5000
</span><span md-src-pos="1632..1669">  Source: Your on-premise IP address
</span><span md-src-pos="1669..1670">
</span><span md-src-pos="1670..1716">2. NACL Configuration (if using custom NACL):
</span><span md-src-pos="1716..1736">- Add inbound rule:
</span><span md-src-pos="1736..1766">  Rule #: 100 (or any number)
</span><span md-src-pos="1766..1785">  Type: Custom TCP
</span><span md-src-pos="1785..1798">  Port: 5000
</span><span md-src-pos="1798..1835">  Source: Your on-premise IP address
</span><span md-src-pos="1835..1855">  Allow/Deny: ALLOW
</span><span md-src-pos="1855..1876">- Add outbound rule:
</span><span md-src-pos="1876..1890">  Rule #: 100
</span><span md-src-pos="1890..1909">  Type: Custom TCP
</span><span md-src-pos="1909..1941">  Port: ephemeral (32768-65535)
</span><span md-src-pos="1941..1983">  Destination: Your on-premise IP address
</span><span md-src-pos="1983..2003">  Allow/Deny: ALLOW</span></code></pre>


B. **Using port forwarding!**

1. SSH Port Forwarding Options:

```bash
# Local port forwarding (most common for your case)
ssh -L 8080:localhost:5000 user@edge-node-ip

# This maps your local port 8080 to edge node's port 5000
# After running this, access the web server via: http://localhost:8080
```

2. Different Types of Port Forwarding:

- Local (-L): Forward local port to remote server

  ```bash
  ssh -L local_port:remote_host:remote_port user@server
  ```
- Remote (-R): Forward remote port to local machine

  ```bash
  ssh -R remote_port:local_host:local_port user@server
  ```
- Dynamic (-D): Creates SOCKS proxy

  ```bash
  ssh -D local_port user@server
  ```

For your specific case (web server on port 5000):

1. Simplest Solution:

```bash
ssh -L 8080:localhost:5000 user@edge-node-ip -N
```

The `-N` flag means "don't execute remote commands" - useful for just port forwarding

Benefits of this approach:

- No need to modify security groups for port 5000
- Traffic is encrypted through SSH tunnel
- Only need SSH port (22) open on AWS
- Can work through corporate firewalls that block other ports

C. **And avoid entering the password by setting up SSH key-based authentication.**

1. Generate SSH key pair on your local machine (if you haven't already):

```bash
# Generate key pair
ssh-keygen -t rsa -b 2048
# Press enter to save in default location (~/.ssh/id_rsa)
# Optionally enter passphrase (or press enter for no passphrase)
```

2. Copy your public key to the edge node:

```bash
# Method 1: Using ssh-copy-id (easiest)
ssh-copy-id user@edge-node-ip

# Method 2: Manual copy (if ssh-copy-id isn't available)
cat ~/.ssh/id_rsa.pub | ssh user@edge-node-ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

3. Now you can use port forwarding without password:

```bash
ssh -L 8080:localhost:5000 user@edge-node-ip -N
```

To make it even more convenient:

4. Add an entry to your SSH config (~/.ssh/config):

```bash
Host edgenode
    HostName edge-node-ip
    User your-username
    IdentityFile ~/.ssh/id_rsa
```

Then you can simply use:

```bash
ssh -L 8080:localhost:5000 edgenode -N
```

Would you like me to explain any of these steps in more detail?
