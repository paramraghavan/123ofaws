# Documentation Index

Quick navigation guide for all documentation files.

## Start Here

**New to this system?** Start with: [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md)
- High-level overview of what the system does
- Quick start (5 minutes)
- Architecture diagram
- Key features

## Main Documentation

### Complete Reference
📖 **[README.md](README.md)** (1000+ lines)
- Full feature documentation
- Installation & deployment (both Serverless and CloudFormation)
- All configuration options
- Resource monitoring details (S3, EC2, EMR)
- Testing & verification procedures
- Troubleshooting guide
- Security considerations

### S3 Failover Setup
🚀 **[FAILOVER_GUIDE.md](FAILOVER_GUIDE.md)** (400+ lines)
- How S3 failover works
- Step-by-step setup instructions
- 3 failover implementation examples:
  - Copy objects to replica
  - Update Route53 DNS
  - Update Parameter Store
- Complete testing procedures
- Integration with failover_ver3
- Troubleshooting

### Configuration Reference
⚙️ **[CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)** (500+ lines)
- Environment variables explained
- serverless.yml configuration
- CloudFormation parameters
- failover_ver3 config.json comparison
- Multi-environment setup
- Advanced configuration patterns
- Configuration checklist
- Troubleshooting config issues

### System Overview
🎯 **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)** (This file explains everything)
- What was created
- What the system does
- Architecture overview
- Quick start guide
- Deployment options
- Cost breakdown
- Integration with failover_ver3
- Feature summary

## Code Files

### Lambda Functions

**[monitor_lambda.py](monitor_lambda.py)**
- Main monitoring function (220 lines)
- Checks S3, EC2, EMR every 10 minutes
- Triggers S3 failover
- Sends SNS alerts
- Writes status and heartbeat to S3

**[generate_dashboard.py](generate_dashboard.py)**
- Dashboard generator (110 lines)
- Reads latest status from S3
- Generates static HTML
- Uploads to S3 for web access

### Configuration & Deployment

**[serverless.yml](serverless.yml)**
- Serverless Framework deployment config
- Lambda function definitions
- EventBridge scheduler configuration
- S3 bucket setup
- SNS topic creation
- CloudWatch alarms
- Recommended deployment method

**[cloudformation-template.yaml](cloudformation-template.yaml)**
- CloudFormation deployment (in README.md)
- Pure AWS-native deployment
- Alternative to Serverless Framework

**[requirements.txt](requirements.txt)**
- Python dependencies (just boto3)

### User Interface

**[dashboard_template.html](dashboard_template.html)**
- Responsive web dashboard template
- Real-time resource status
- Color-coded health indicators
- Mobile-friendly design
- Auto-refresh every 60 seconds

## Quick Decision Tree

```
I want to...

1. Understand what this system does
   → SYSTEM_OVERVIEW.md

2. Deploy and get started quickly
   → SYSTEM_OVERVIEW.md (Quick Start section)
   → Then serverless deploy

3. Set up S3 failover
   → FAILOVER_GUIDE.md

4. Configure for my environment
   → CONFIGURATION_REFERENCE.md
   → Then edit serverless.yml

5. Deploy with CloudFormation
   → README.md (CloudFormation section)
   → Use cloudformation-template.yaml in README

6. Understand the code
   → README.md (Resource Monitoring Details)
   → Then read monitor_lambda.py

7. Integrate with failover_ver3
   → FAILOVER_GUIDE.md (Integration section)
   → Then ../failover_ver3/README.md

8. Troubleshoot an issue
   → README.md (Troubleshooting)
   → Or FAILOVER_GUIDE.md (Troubleshooting)
   → Or CONFIGURATION_REFERENCE.md (Troubleshooting)

9. Test before production
   → README.md (Testing & Verification)
   → FAILOVER_GUIDE.md (Testing S3 Failover)
```

## File Sizes & Complexity

| Document | Size | Complexity | Time |
|----------|------|-----------|------|
| SYSTEM_OVERVIEW.md | 14 KB | Low | 10 min |
| README.md | 35 KB | Medium | 30 min |
| FAILOVER_GUIDE.md | 11 KB | Medium | 20 min |
| CONFIGURATION_REFERENCE.md | 9.8 KB | Medium | 20 min |
| monitor_lambda.py | 8.4 KB | Medium | 15 min |
| generate_dashboard.py | 6.7 KB | Low | 10 min |
| serverless.yml | 5.3 KB | Low | 10 min |

## Key Sections by Use Case

### I'm a Developer
1. SYSTEM_OVERVIEW.md - Understand the system
2. README.md - Complete reference
3. monitor_lambda.py - Read the code
4. Test in development environment

### I'm a DevOps Engineer
1. README.md - Deployment options
2. serverless.yml - Review deployment config
3. CONFIGURATION_REFERENCE.md - Setup for multiple environments
4. FAILOVER_GUIDE.md - Test S3 failover strategy

### I'm a System Administrator
1. SYSTEM_OVERVIEW.md - High-level overview
2. FAILOVER_GUIDE.md - Understand failover capabilities
3. README.md - Setup monitoring and alerting
4. Create runbooks for failure scenarios

### I'm Integrating with failover_ver3
1. FAILOVER_GUIDE.md - Integration section
2. SYSTEM_OVERVIEW.md - See comparison table
3. README.md - Comparison with failover_ver3
4. ../failover_ver3/README.md - Comprehensive failover system

## Topic-Based Index

### Deployment
- SYSTEM_OVERVIEW.md - Quick start (5 min)
- README.md - Installation & Deployment section
- README.md - Deployment Methods section
- serverless.yml - Serverless Framework
- README.md - CloudFormation Approach (code in README)

### Configuration
- CONFIGURATION_REFERENCE.md - Complete guide
- serverless.yml - Environment variables
- README.md - Configuration section

### S3 Failover
- FAILOVER_GUIDE.md - Complete S3 failover guide
- README.md - S3 Buckets section (Resource Monitoring)
- SYSTEM_OVERVIEW.md - S3 Failover Customization

### Monitoring & Alerts
- README.md - Monitoring & Alerts section
- SYSTEM_OVERVIEW.md - What This System Does
- README.md - Resource Monitoring Details

### Dashboard
- README.md - View Dashboard section
- SYSTEM_OVERVIEW.md - Visual Dashboard
- dashboard_template.html - HTML template

### Testing
- README.md - Testing & Verification section
- FAILOVER_GUIDE.md - Testing S3 Failover section
- SYSTEM_OVERVIEW.md - Verification

### Troubleshooting
- README.md - Troubleshooting section
- FAILOVER_GUIDE.md - Troubleshooting section
- CONFIGURATION_REFERENCE.md - Troubleshooting section

### Cost
- README.md - Cost Estimate section
- SYSTEM_OVERVIEW.md - Cost breakdown

## Architecture Diagrams

### System Architecture
See: SYSTEM_OVERVIEW.md - Architecture Overview section

### S3 Failover Flow
See: FAILOVER_GUIDE.md - S3 Failover Architecture section

### Integration with failover_ver3
See: FAILOVER_GUIDE.md - Integration with failover_ver3 section

## External References

### Related Systems
- **failover_ver3** - Comprehensive failover system
  - Location: `../failover_ver3/`
  - Read: `../failover_ver3/README.md`
  - Config: `../failover_ver3/config.json`

### AWS Services Used
- Lambda - Serverless compute
- EventBridge - Scheduling
- S3 - Logging and dashboard hosting
- SNS - Alerts
- CloudWatch - Monitoring and alarms
- IAM - Permissions
- EC2 - Monitored resource
- EMR - Monitored resource

## Recommended Reading Order

### For Quick Start (30 minutes)
1. SYSTEM_OVERVIEW.md (10 min)
2. README.md - Installation & Deployment (10 min)
3. serverless deploy (5 min)
4. Access dashboard (5 min)

### For Complete Understanding (2 hours)
1. SYSTEM_OVERVIEW.md (10 min)
2. README.md (45 min)
3. CONFIGURATION_REFERENCE.md (20 min)
4. FAILOVER_GUIDE.md (20 min)
5. Review code files (15 min)
6. Practice deployment (10 min)

### For S3 Failover Setup (1 hour)
1. FAILOVER_GUIDE.md (30 min)
2. README.md - S3 Buckets section (10 min)
3. Implement and test (20 min)

## Getting Help

**If you're stuck on:**

- **"What is this system?"** → SYSTEM_OVERVIEW.md
- **"How do I deploy it?"** → README.md Installation section
- **"How do I configure it?"** → CONFIGURATION_REFERENCE.md
- **"How does S3 failover work?"** → FAILOVER_GUIDE.md
- **"What does this code do?"** → README.md Resource Monitoring Details
- **"I got an error"** → Troubleshooting in relevant document
- **"How does it integrate with failover_ver3?"** → FAILOVER_GUIDE.md Integration section

## File Manifest

```
aws-lambda-monitoring/
├── Documentation/
│   ├── INDEX.md                     # You are here!
│   ├── SYSTEM_OVERVIEW.md           # High-level overview
│   ├── README.md                    # Complete reference
│   ├── FAILOVER_GUIDE.md           # S3 failover setup
│   └── CONFIGURATION_REFERENCE.md  # Configuration options
│
├── Code/
│   ├── monitor_lambda.py            # Main Lambda function
│   ├── generate_dashboard.py        # Dashboard generator
│   └── dashboard_template.html      # Web UI template
│
├── Deployment/
│   ├── serverless.yml               # Serverless config
│   ├── requirements.txt             # Dependencies
│   └── cloudformation-template.yaml # (in README.md)
│
└── Output/
    └── logs/                        # Created by Lambda
        ├── status/latest.json
        ├── heartbeat.json
        └── failover_logs/
```

---

**Start reading:** [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)

**Then deploy:** `serverless deploy`

**Then monitor:** Check your dashboard!

Good luck! 🚀
