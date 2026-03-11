# Quick Start Guide

Get up and running with the AWS Failover System in 5 minutes!

## 📋 Prerequisites

- Python 3.8+
- AWS CLI configured
- Git (for EMR bootstrap scripts)

## 🚀 Installation (30 seconds)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create configuration
python utils.py

# 3. Edit config.json with your settings
nano config.json  # or your preferred editor
```

## ⚡ Quick Run

### Option 1: Using Config File (Recommended)

```bash
# 1. Edit config.json with your settings
nano config.json

# 2. Run with defaults from config
python failover_main.py

# Or specify mode
python failover_main.py --mode monitor
```

### Option 2: Command Line Override

```bash
# Override config settings
python failover_main.py --profile prod --tag-name production --mode both

# View web dashboard
python webapp.py
# Then open: http://localhost:5000
```

### Option 3: Interactive Menu (Easiest)

```bash
chmod +x run.sh
./run.sh
```

Follow the prompts!

## 📊 View Results

After running, access the web dashboard:

```bash
python webapp.py
```

Navigate to `http://localhost:5000` and see:
- 📈 Summary statistics
- 📋 Filterable resource table
- 📝 Detailed logs
- 🔄 Failover results

## 🏷️ Tag Your Resources

The system finds resources by AWS tag. Ensure your resources have a `Name` tag:

```bash
# Tag an EC2 instance
aws ec2 create-tags --resources i-1234567890abcdef0 \
    --tags Key=Name,Value=production

# Tag an EMR cluster
aws emr add-tags --resource-id j-XXXXXXXXXXXXX \
    --tags Key=Name,Value=production
```

## 🎯 Common Use Cases

### Case 1: Daily Health Check

```bash
# Run every morning to check resource health
python failover_main.py --profile prod --tag-name production --mode monitor
```

### Case 2: Auto-Recovery

```bash
# Monitor and automatically recover failed resources
python failover_main.py --profile prod --tag-name production --mode both
```

### Case 3: EMR Cluster Recreation

When an EMR cluster terminates:
1. System detects termination
2. Retrieves original configuration
3. Clones bootstrap scripts from your GitHub repo
4. Recreates cluster with exact same settings (core/task nodes, spot/on-demand)

## ⚙️ Minimal Configuration

Edit `config.json` - only 4 lines needed:

```json
{
  "aws_profile": "your-profile-name",
  "aws_region": "us-east-1",
  "tag_name": "production",
  "emr": {
    "bootstrap_repo": "https://github.com/your-org/bootstrap-scripts.git",
    "bootstrap_branch": "main"
  }
}
```

**All other configurations are auto-discovered from your AWS resources!**

The system automatically figures out:
- ✅ EC2 instance types, AMIs, security groups
- ✅ EMR cluster sizes, applications, node configurations
- ✅ Lambda runtimes, memory, timeout
- ✅ Auto Scaling min/max/desired capacity
- ✅ All IAM roles and policies

## 🔍 Verify Setup

```bash
# Test AWS credentials
aws sts get-caller-identity --profile your-profile

# Test resource detection
python failover_main.py --profile your-profile --tag-name your-tag --mode monitor
```

## 📁 File Structure

After setup, you'll have:

```
.
├── failover_main.py      # Main script
├── monitors.py           # Resource monitors
├── failover.py           # Failover handlers
├── utils.py              # Utilities
├── webapp.py             # Web dashboard
├── config.json           # Your configuration
├── requirements.txt      # Dependencies
├── run.sh               # Quick launcher
└── logs/                # Auto-created log directory
```

## 🆘 Troubleshooting

### "No resources found"
- ✅ Check tag name matches exactly (case-sensitive)
- ✅ Verify AWS profile has correct permissions
- ✅ Ensure you're in the correct region

### "Permission denied"
- ✅ Run `chmod +x run.sh`
- ✅ Check IAM permissions (see README)

### "Module not found"
- ✅ Install dependencies: `pip install -r requirements.txt`
- ✅ Use virtual environment: `python -m venv venv && source venv/bin/activate`

## 📚 Next Steps

1. ✅ Review the full [README.md](README.md) for advanced features
2. ✅ Customize [config.json](config.example.json) for your needs
3. ✅ Set up scheduled monitoring (cron/Lambda)
4. ✅ Configure notifications (email/Slack)
5. ✅ Add custom resource types

## 💡 Pro Tips

- **Start with monitor mode** to verify detection before enabling failover
- **Use specific tags** to avoid monitoring unintended resources
- **Check the web dashboard** regularly for insights
- **Keep EMR bootstrap scripts** in version control
- **Test in dev/staging** before production use

## 🎉 You're Ready!

Run the system and watch it automatically monitor and recover your AWS infrastructure!

```bash
./run.sh
```

For detailed documentation, see [README.md](README.md)