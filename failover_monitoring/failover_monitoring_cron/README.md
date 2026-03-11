# AWS Failover Monitoring System - Complete Guide

## 🚀 Quick Start (5 Minutes)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Create config.json
```json
{
  "aws_profile": "default",
  "aws_region": "us-east-1",
  "tag_name": "production",
  "emr": {
    "bootstrap_repo": "https://github.com/your-org/emr-bootstrap.git",
    "bootstrap_branch": "main"
  }
}
```

### 3. Run
```bash
# Interactive mode
./run.sh

# Or directly
python failover_main.py

# View dashboard
python webapp.py  # Access at http://localhost:5000
```

---

## 🌟 Key Features

### Auto-Discovery - Zero Configuration!
The system **automatically discovers ALL configurations** from AWS:
- ✅ EC2: Instance types, AMIs, security groups, subnets, IAM roles, launch templates
- ✅ EMR: Cluster sizes, applications, node configs, spot/on-demand settings, everything!
- ✅ Lambda: Runtimes, memory, timeout
- ✅ Auto Scaling: Min/max/desired capacity

**You only configure 4 things:**
1. AWS profile name
2. AWS region
3. Resource tag to monitor
4. EMR bootstrap repo (if using EMR)

### Supported Resources
- EC2 Instances (start stopped, recreate terminated)
- EMR Clusters (exact clone with auto-discovered config, **scaling issue detection**)
- Lambda Functions
- Auto Scaling Groups
- Snowflake (optional)
- API Tokens (optional)

### EMR Scaling Detection
The system automatically detects and reports:
- ✅ Instance count mismatches (requested vs running)
- ✅ Spot instance interruptions
- ✅ Fleet capacity issues (on-demand and spot)
- ✅ Instance group resizing problems
- ✅ Autoscaling policy failures
- ✅ Capacity provisioning failures

When scaling issues are detected, status shows as `SCALING_ISSUE` with detailed problem descriptions.

### Web Dashboard
- Real-time monitoring
- Filterable logs (by time, instance, tag, status, type, **AWS profile**)
- Summary statistics (overall and **per-profile**)
- Failover results tracking
- **Multi-environment support** - filter by UAT, DEV, PROD profiles

---

## 📋 Files You Need

**Core Files (Required):**
1. `failover_main.py` - Main orchestrator
2. `monitors.py` - Resource monitors
3. `failover.py` - Failover handlers
4. `utils.py` - Utilities
5. `webapp.py` - Web dashboard
6. `requirements.txt` - Dependencies
7. `config.json` - Your simple config

**Optional:**
8. `run.sh` - Interactive launcher

---

## 💡 Usage Examples

### Using config.json defaults
```bash
python failover_main.py --mode both
python failover_main.py --mode monitor
python failover_main.py --mode failover
```

### Override config settings
```bash
python failover_main.py --profile dev --tag-name staging --region us-west-2
```

### Interactive mode
```bash
./run.sh
# Automatically detects and offers to use config.json defaults
```

---

## 🏷️ Tag Your Resources

Tag resources you want to monitor:

```bash
# EC2
aws ec2 create-tags --resources i-1234567890abcdef0 \
    --tags Key=Name,Value=production

# EMR
aws emr add-tags --resource-id j-XXXXXXXXXXXXX \
    --tags Key=Name,Value=production
```

---

## 🔄 How EMR Failover Works

**Your terminated cluster:**
- 1 master (m5.xlarge on-demand)
- 3 core (m5.2xlarge on-demand)
- 5 task (m5.xlarge spot @ $0.50/hr)
- Apps: Spark 3.3.0, Hive 3.1.3
- Custom bootstrap scripts

**System automatically:**
1. Detects termination
2. Reads full config from AWS API
3. Clones bootstrap scripts from GitHub
4. Recreates cluster **exactly as it was**

**No manual config needed!** Everything auto-discovered from AWS.

---

## 📊 Web Dashboard Features

Access at `http://localhost:5000`

**Summary Tab:**
- Filterable resource table
- Filter by: start time, instance ID, tag, status, resource type, **AWS profile**
- Real-time statistics

**Detailed Logs Tab:**
- Complete log entries in JSON format
- All resource metadata

**Failover Logs Tab:**
- Failover execution results
- System logs

### Multi-Environment Support

The dashboard supports filtering by AWS profile, perfect for managing multiple environments from one machine:

**Global Profile Filter (Header):**
- Dropdown to select specific profile (UAT, DEV, PROD, etc.)
- Filters ALL stats and logs across all tabs
- Shows only data for selected environment

**Granular Profile Filter (Summary Tab):**
- Additional text filter in the filters section
- Combine with other filters for precise queries
- Example: "Show all stopped EC2 instances in UAT profile"

**Use Cases:**
```bash
# Run for production
python failover_main.py --profile prod --tag-name production

# Run for UAT  
python failover_main.py --profile uat --tag-name uat

# Run for dev
python failover_main.py --profile dev --tag-name dev

# All logs saved to same files, filtered by profile in dashboard
```

---

## 🔧 Adding New Resource Types

The system is designed for easy extension:

```python
# 1. In monitors.py
class RDSMonitor(BaseMonitor):
    def check_status(self) -> List[Dict[str, Any]]:
        # Your monitoring logic
        return statuses

# 2. In failover.py
class RDSFailover(BaseFailover):
    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        # Your failover logic
        return result

# 3. In failover_main.py __init__
self.monitors['rds'] = RDSMonitor(self.session, tag_name)
self.failover_handlers['rds'] = RDSFailover(self.session, config)
```

Done! Your new resource is now monitored.

---

## 🔐 Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "ec2:DescribeInstances",
      "ec2:StartInstances",
      "ec2:RunInstances",
      "emr:ListClusters",
      "emr:DescribeCluster",
      "emr:ListInstanceFleets",
      "emr:ListInstanceGroups",
      "emr:RunJobFlow",
      "lambda:ListFunctions",
      "lambda:GetFunction",
      "lambda:ListTags",
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:SetDesiredCapacity"
    ],
    "Resource": "*"
  }]
}
```

---

## 📝 Log Format

**Monitor Logs (monitor_log.jsonl):**
```json
{
  "script_start_time": "2025-10-03T10:30:00",
  "resource_id": "i-1234567890abcdef0",
  "tag_name": "production-web",
  "status": "running",
  "resource_type": "ec2",
  "instance_type": "t3.large",
  "aws_profile": "production",
  "aws_region": "us-east-1",
  "timestamp": "2025-10-03T10:30:15"
}
```

**Failover Logs (failover_log.jsonl):**
```json
{
  "resource_id": "i-1234567890abcdef0",
  "resource_type": "ec2",
  "original_status": "stopped",
  "action": "start",
  "result": "SUCCESS",
  "message": "Started instance i-1234567890abcdef0",
  "aws_profile": "production",
  "aws_region": "us-east-1",
  "timestamp": "2025-10-03T10:30:30"
}
```

**All logs include `aws_profile` and `aws_region` fields for multi-environment tracking.**

---

## 🔍 EMR Scaling Issue Detection

The system monitors running EMR clusters for scaling problems:

### What Gets Detected

**Instance Count Mismatches:**
```
Core group: Requested 5 instances, Running 3 instances
Task group: Requested 10 instances, Running 7 instances
```

**Spot Instance Issues:**
```
Task fleet: Spot capacity mismatch (Target: 10, Provisioned: 6)
Task group: 3 spot instances terminated
```

**Fleet/Group State Problems:**
```
Core fleet in RESIZING state
Task group in ARRESTED state
```

**Autoscaling Policy Failures:**
```
Task group autoscaling policy in FAILED state
```

### Example Log Entry with Scaling Issues

```json
{
  "resource_id": "j-ABC123XYZ",
  "status": "SCALING_ISSUE",
  "cluster_state": "RUNNING",
  "scaling_issues": [
    "CORE group: Instance count mismatch (Requested: 5, Running: 3)",
    "TASK fleet: Spot capacity mismatch (Target: 10, Provisioned: 7)",
    "TASK group autoscaling policy in FAILED state"
  ],
  "aws_profile": "production",
  "timestamp": "2025-10-04T10:30:00"
}
```

### Automatic Remediation

When `--mode failover` is used, the system attempts to:
1. Trigger resize operations for instance groups with capacity mismatches
2. Re-apply requested instance counts
3. Log all actions taken

```bash
# Monitor detects scaling issues
python failover_main.py --profile prod --tag-name production --mode monitor

# Auto-remediate detected issues
python failover_main.py --profile prod --tag-name production --mode failover
```

---

## 🐛 Troubleshooting

**No resources found:**
- ✅ Check tag name matches exactly (case-sensitive)
- ✅ Verify AWS profile permissions
- ✅ Ensure correct region

**EMR failover fails:**
- ✅ Verify bootstrap repo is accessible
- ✅ Check IAM roles exist
- ✅ Ensure EC2 capacity available

**Web dashboard not loading:**
- ✅ Run `python webapp.py`
- ✅ Check port 5000 is not in use
- ✅ Verify logs directory exists

---

## ✨ Configuration Philosophy

> **"The best config is no config."**

This system uses **infrastructure-as-code principles**: your AWS resources ARE your configuration.

The system reads what you already have and recreates it exactly when needed. No maintaining parallel config files. No config drift. Just tag your resources and let the system handle the rest!

---

## 🎯 Best Practices

1. **Tag Consistently** - Use consistent `Name` tags
2. **Test First** - Use monitor mode before enabling failover
3. **Version Control** - Keep EMR bootstrap scripts in Git
4. **Review Logs** - Check dashboard regularly
5. **Start Simple** - Begin with one resource type

---

## 📦 Complete File List

```
.
├── failover_main.py      # Main orchestrator
├── monitors.py           # Resource monitors  
├── failover.py           # Failover handlers
├── utils.py              # Utilities
├── webapp.py             # Web dashboard
├── requirements.txt      # Python dependencies
├── run.sh               # Interactive launcher (optional)
├── config.json           # Your config (4 lines!)
└── logs/                # Auto-created logs
    ├── monitor_log.jsonl
    ├── failover_log.jsonl
    └── failover_*.log
```

---

## 🚀 You're Ready!

```bash
# Quick test
python failover_main.py --mode monitor

# Full run
python failover_main.py --mode both

# Dashboard
python webapp.py
```

The system will auto-discover all your AWS resource configurations. Just tag and go! 🎉
# AWS Failover Monitoring and Recovery System

A comprehensive, extensible system for monitoring AWS resources and automatically recovering from failures.

## 🌟 Key Feature: Auto-Discovery

**Zero configuration needed!** The system automatically discovers all resource configurations from AWS:

- ✅ **EC2**: Instance types, AMIs, security groups, subnets, IAM roles - all auto-discovered
- ✅ **EMR**: Cluster sizes, applications, node configs, spot/on-demand settings - all auto-discovered  
- ✅ **Lambda**: Runtimes, memory, timeout - all auto-discovered
- ✅ **Auto Scaling**: Min/max/desired capacity - all auto-discovered

**You only configure 4 things:**
1. AWS profile name
2. AWS region  
3. Resource tag to monitor
4. EMR bootstrap repo URL (if using EMR)

Everything else is read directly from your existing AWS infrastructure!

## Features

- **Multi-Resource Monitoring**: EC2, EMR, Lambda, Auto Scaling Groups
- **Non-AWS Service Support**: Token renewal, Snowflake monitoring
- **Automatic Failover**: Restart stopped instances, recreate terminated resources
- **EMR Clone**: Exact recreation of EMR clusters with same configuration (auto-discovered from AWS!)
- **Web Dashboard**: Flask-based HTML5 viewer with filtering and analytics
- **Extensible Design**: Easy to add new resource types
- **Comprehensive Logging**: Monitor, failover, and system logs

## Architecture

```
├── failover_main.py          # Main orchestrator script
├── monitors.py               # Resource monitoring modules
├── failover.py               # Failover handlers
├── utils.py                  # Utility functions
├── webapp.py                 # Flask web application
├── config.json               # Configuration file
├── logs/                     # Log directory
│   ├── monitor_log.jsonl     # Monitoring logs
│   ├── failover_log.jsonl    # Failover logs
│   └── failover_*.log        # System logs
└── templates/
    └── index.html            # Auto-generated web UI
```

## Installation

### Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate profile
- Git (for EMR bootstrap script cloning)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure AWS Credentials

```bash
aws configure --profile your-profile-name
```

### Create Configuration File

```bash
python utils.py
```

This creates a simple `config.json`. Edit it with your settings:

```json
{
  "aws_profile": "default",
  "aws_region": "us-east-1",
  "tag_name": "production",
  "emr": {
    "bootstrap_repo": "https://github.com/your-org/emr-bootstrap-scripts.git",
    "bootstrap_branch": "main"
  }
}
```

**That's it!** The system auto-discovers all other configurations from your AWS resources.

## Usage

### Using Config File (Recommended)

Set `aws_profile`, `aws_region`, and `tag_name` in `config.json`, then run:

```bash
# Monitor + Failover (uses config.json defaults)
python failover_main.py --mode both

# Monitor only
python failover_main.py --mode monitor

# Failover only  
python failover_main.py --mode failover
```

### Using Command Line (Override Config)

```bash
# Override profile and tag from command line
python failover_main.py --profile prod --tag-name production --mode both

# Override all settings
python failover_main.py --profile dev --tag-name staging --region us-west-2 --mode monitor
```

### With Custom Config File

```bash
python failover_main.py --config config-dev.json
```

### Set Log Level

```bash
python failover_main.py --log-level DEBUG
```

## Web Dashboard

Start the web viewer:

```bash
python webapp.py
```

Access at: `http://localhost:5000`

### Features

**Summary Tab**
- Filterable table of all resources
- Filter by: start time, instance ID, tag name, status, resource type
- Real-time status updates

**Detailed Logs Tab**
- Complete log entries in JSON format
- All monitored resources with full metadata

**Failover Logs Tab**
- Failover execution results
- System logs from all operations

## Adding New Resource Types

The system is designed to be easily extensible. To add a new AWS resource:

### 1. Create Monitor Class

In `monitors.py`:

```python
class RDSMonitor(BaseMonitor):
    """Monitor RDS instances"""
    
    def __init__(self, session, tag_name: str):
        super().__init__(tag_name)
        self.rds = session.client('rds')
    
    def check_status(self) -> List[Dict[str, Any]]:
        statuses = []
        # Implement your monitoring logic
        return statuses
```

### 2. Create Failover Handler

In `failover.py`:

```python
class RDSFailover(BaseFailover):
    """Failover handler for RDS"""
    
    def __init__(self, session, config: Dict[str, Any]):
        super().__init__(config)
        self.rds = session.client('rds')
    
    def execute(self, resource_info: Dict[str, Any]) -> Dict[str, Any]:
        # Implement your failover logic
        pass
```

### 3. Register in Orchestrator

In `failover_main.py`, add to `__init__`:

```python
self.monitors['rds'] = RDSMonitor(self.session, tag_name)
self.failover_handlers['rds'] = RDSFailover(self.session, config)
```

That's it! Your new resource type is now monitored and failover-enabled.

## EMR Failover Details

When an EMR cluster is terminated, the system automatically:

1. **Auto-discovers the complete cluster configuration from AWS** - no need to specify instance types, sizes, or applications in config
2. Retrieves instance groups (core and task nodes) with exact counts
3. Preserves spot vs on-demand instance settings
4. Maintains all applications (Spark, Hive, etc.)
5. Preserves all security groups, subnets, and IAM roles
6. Clones bootstrap scripts from your configured GitHub repo
7. Applies all original tags
8. Recreates with identical configuration

**Example**: If your terminated cluster had:
- 1 master (m5.xlarge on-demand)
- 3 core nodes (m5.2xlarge on-demand)  
- 5 task nodes (m5.xlarge spot)
- Applications: Spark 3.3.0, Hive 3.1.3
- Custom bootstrap scripts

The new cluster will be **exactly the same** - all settings auto-discovered from AWS!

## Log Format

### Monitor Logs (monitor_log.jsonl)

```json
{
  "script_start_time": "2025-10-03T10:30:00",
  "resource_id": "i-1234567890abcdef0",
  "tag_name": "production-web",
  "status": "running",
  "resource_type": "ec2",
  "instance_type": "t3.large",
  "timestamp": "2025-10-03T10:30:15"
}
```

### Failover Logs (failover_log.jsonl)

```json
{
  "script_start_time": "2025-10-03T10:30:00",
  "resource_id": "i-1234567890abcdef0",
  "resource_type": "ec2",
  "original_status": "stopped",
  "action": "start",
  "result": "SUCCESS",
  "message": "Started instance i-1234567890abcdef0",
  "timestamp": "2025-10-03T10:30:30"
}
```

## Best Practices

1. **Tag Consistently**: Use consistent naming for the `Name` tag across resources
2. **Test Failover**: Test in dev/staging before production use
3. **Review Logs**: Regularly check the web dashboard for issues
4. **Bootstrap Scripts**: Keep EMR bootstrap scripts in version control
5. **Dry Run**: Use monitor mode first to verify detection

The system auto-discovers all AWS configurations, so you don't need to maintain complex config files!

## Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:RunInstances",
        "emr:ListClusters",
        "emr:DescribeCluster",
        "emr:ListInstanceFleets",
        "emr:ListInstanceGroups",
        "emr:RunJobFlow",
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:ListTags",
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:SetDesiredCapacity"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

### No resources found
- Verify the tag name matches exactly (case-sensitive)
- Check AWS profile has correct permissions
- Ensure resources are in the correct region

### EMR failover fails
- Verify bootstrap repo URL is accessible
- Check IAM roles exist for EMR
- Ensure sufficient EC2 capacity for instance types

### Web dashboard not loading
- Check Flask is running: `python webapp.py`
- Verify logs directory exists
- Check for log file permissions

## Extending to Non-AWS Services

Example for adding Snowflake monitoring:

1. Install connector: `pip install snowflake-connector-python`
2. Implement in `monitors.py`:

```python
import snowflake.connector

def check_status(self) -> List[Dict[str, Any]]:
    conn = snowflake.connector.connect(
        user=self.config['user'],
        password=self.config['password'],
        account=self.config['account']
    )
    # Check connection and warehouse status
    return statuses
```
