# AWS Networking & VPC Guides

Complete reference for AWS networking architecture and VPC configuration. Everything you need to design, build, and troubleshoot AWS networks.

## 📁 Directory Organization

This consolidated guide is organized by topic for easy navigation:

### 🏗️ `foundations/` - Start Here
**Learn AWS networking fundamentals:**
- **aws-networking-complete-guide.md** - Comprehensive networking overview
  - VPC, subnets, security groups, NACLs, IGW, NAT
  - Mental models and decision matrices
  - Common CIDR notation, routing, and traffic flow
  - VPC endpoints (Gateway & Interface)

- **quick-reference.md** - Quick lookup tables and commands
  - Common operations cheat sheet
  - Decision tables for architecture choices
  - Service comparison matrix

- **visual-diagrams.md** - Architecture diagrams and visual explanations
  - Network topology diagrams
  - Traffic flow diagrams
  - Visual decision trees

### 🎯 `vpc-guides/` - Deep Dives
**Specific VPC topics and how-to guides:**
- **vpc-nacl-vs-security-groups.md** - Security comparison
  - Detailed comparison: NACLs vs Security Groups
  - When to use each
  - Decision matrix
  - Common mistakes and gotchas

- **vpc-web-server-setup.md** - How-to guide
  - Setting up web servers on edge nodes
  - Making services available on-premise
  - Network configuration examples
  - Real-world scenarios

### 🔬 `hands-on-labs/` - Practical Exercises
**Step-by-step implementation labs:**
- **hands-on-labs.md** - Interactive exercises
  - Create a public VPC from scratch
  - Add private subnets with NAT
  - Configure security groups
  - Set up VPC endpoints
  - Build multi-AZ architectures

---

## 🎓 Quick Start Guide

### **New to AWS Networking?**
Start here (reading order):
1. **aws-networking-complete-guide.md** - Chapters 1-3 (Mental Model, CIDR, VPC Basics)
2. **quick-reference.md** - Decision tables section
3. **hands-on-labs.md** - Exercise 1 (Create Public VPC)

**Time commitment**: ~4 hours

### **Know AWS basics, want to master VPC?**
1. **aws-networking-complete-guide.md** - Focus on Subnets & Security sections
2. **vpc-guides/** - Read relevant how-to guides
3. **hands-on-labs.md** - Complete all exercises

**Time commitment**: ~6-8 hours

### **Need quick answers?**
- Looking for syntax? → **quick-reference.md**
- Need decision help? → **aws-networking-complete-guide.md** → Decision Tables
- Comparing features? → **vpc-nacl-vs-security-groups.md**
- Want visual explanation? → **visual-diagrams.md**

### **Solving a problem?**
1. Check the **Troubleshooting** section in aws-networking-complete-guide.md
2. Review **vpc-guides/** for specific scenarios
3. Follow a **hands-on-lab** exercise to test your understanding

---

## 📚 Topic Finder

Find information by topic:

| Topic | Location | Section |
|-------|----------|---------|
| **VPC Basics** | foundations/ | aws-networking-complete-guide.md → VPC Fundamentals |
| **Subnets (Public/Private)** | foundations/ | aws-networking-complete-guide.md → Subnets Section |
| **Security Groups** | foundations/ | aws-networking-complete-guide.md → Security Groups |
| **NACLs** | foundations/ | aws-networking-complete-guide.md → NACLs |
| **VPC Endpoints** | foundations/ | aws-networking-complete-guide.md → VPC Endpoints (4 subsections) |
| **Internet Gateway** | foundations/ | aws-networking-complete-guide.md → Network Components |
| **NAT Gateway** | foundations/ | aws-networking-complete-guide.md → Network Components |
| **Route Tables** | foundations/ | aws-networking-complete-guide.md → Network Components |
| **NACL vs Security Groups** | vpc-guides/ | vpc-nacl-vs-security-groups.md (full comparison) |
| **Web Server Setup** | vpc-guides/ | vpc-web-server-setup.md (how-to guide) |
| **Hands-On Exercises** | hands-on-labs/ | hands-on-labs.md (all exercises) |
| **Visual Diagrams** | foundations/ | visual-diagrams.md |

---

## 🏗️ Common Architectures

Explore these patterns in **aws-networking-complete-guide.md** → Architecture Patterns:

1. **Simple Public VPC** - Single public subnet with IGW
2. **Public + Private (Standard)** - Web servers + databases
3. **Multi-AZ HA** - High availability across availability zones

---

## 💡 Key Concepts Cheat Sheet

**Mental Models:**
- **VPC** = Your private city in AWS
- **Subnets** = Neighborhoods (public-facing or hidden)
- **Security Groups** = House bouncers at instance level
- **NACLs** = Neighborhood gates at subnet level
- **IGW** = Highway to the internet
- **NAT** = Private exit door (one-way)
- **VPC Endpoints** = Secret tunnels to AWS services

**Network Components Cost:**
- VPC, Subnets, IGW, Security Groups, NACLs, Route Tables = FREE
- NAT Gateway = ~$32/month + data transfer
- VPC Endpoint (Gateway) = FREE
- VPC Endpoint (Interface) = ~$7/month

**Quick Decisions:**
- Public subnet? → Yes if needs direct internet access
- Private subnet? → Yes for databases, sensitive workloads
- NAT or VPC Endpoint? → Use VPC Endpoint (cheaper, secure)
- Security Group or NACL? → Both (layered security)

---

## 📖 Reading Paths

### **Path 1: Complete Beginner (4-6 hours)**
```
aws-networking-complete-guide.md (Ch 1-3: Mental Model, CIDR, VPC)
         ↓
quick-reference.md (Decision tables)
         ↓
aws-networking-complete-guide.md (Ch 4-6: Subnets, Security, Components)
         ↓
hands-on-labs.md (Exercise 1-2)
         ↓
vpc-guides/ (Choose relevant guides)
```

### **Path 2: Intermediate (2-3 hours)**
```
aws-networking-complete-guide.md (skim, focus on Security section)
         ↓
vpc-nacl-vs-security-groups.md (full deep dive)
         ↓
hands-on-labs.md (all exercises)
         ↓
vpc-guides/ (remaining guides)
```

### **Path 3: Architecture Design (3-4 hours)**
```
aws-networking-complete-guide.md (Architecture Patterns section)
         ↓
vpc-guides/ (all how-to guides)
         ↓
hands-on-labs.md (build your own)
         ↓
Combine learnings into custom architecture
```

---

## ✅ Consolidation Status

**Original Directories:**
- ❌ networking-guide/ (consolidated)
- ❌ vpc/ (consolidated)

**New Unified Directory:**
- ✅ aws-networking/ (all content organized by topic)

**Benefits:**
- Single source of truth
- Logical topic-based organization
- Easier to maintain
- Better discoverability
- Clear navigation with this README

---

## 🚀 Next Steps

1. **Choose your learning path** above based on your experience level
2. **Open** the recommended file in your path
3. **Read** the relevant sections
4. **Practice** with hands-on labs
5. **Refer back** to quick-reference.md when needed

---

## 📝 File Statistics

| Directory | Files | Content |
|-----------|-------|---------|
| foundations/ | 3 | 1,600+ lines (comprehensive) |
| vpc-guides/ | 2 | 1,200+ lines (specific topics) |
| hands-on-labs/ | 1 | 400+ lines (practical exercises) |
| **Total** | **6** | **3,200+ lines** |

---

## 💬 Using This Guide

**Best for:**
- Learning AWS networking from basics to advanced
- Making architectural decisions
- Troubleshooting network issues
- Quick reference lookups
- Hands-on practice

**Not a guide for:**
- AWS-specific tools (use AWS documentation)
- Programming in Python/Node.js (use AWS SDKs docs)
- Database administration (use RDS docs)

---

**Last Updated**: June 2024
**Coverage**: AWS VPC, Subnets, Security, Routing, VPC Endpoints, NAT, IGW, NACLs
**Level**: Beginner to Advanced
