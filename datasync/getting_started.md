# Getting Started - 5 Minute Quick Start

**For experienced developers who just need to get running fast.**

## Prerequisites

- Python 3.9+
- AWS account with DataSync set up
- AWS CLI configured (`aws configure`)
- Git (optional)

## 1. Clone/Download (30 seconds)

```bash
cd /Users/paramraghavan/dev/123ofaws/datasync
```

## 2. Install (1 minute)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure (2 minutes)

```bash
cp .env.example .env
# Edit .env with your values:
# - DATASYNC_NFS_LOCATION_ARN
# - DATASYNC_S3_LOCATION_ARN
# - NAS_BASE_PATH
# - S3_BUCKET
```

Or set environment variables:

```bash
export DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:region:account:location/nfs/xxxxx
export DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:region:account:location/s3/yyyyy
export NAS_BASE_PATH=/mydata/prod/icm/datain/poolData
export S3_BUCKET=my-datasync-bucket
export DATATYPES=datatype1,datatype2
```

## 4. Test Locally (1 minute)

```bash
# Verify configuration
python -c "from config import get_config; c=get_config(); print('✓ Config loaded')"

# Test date logic
python -c "from date_logic import DateLogic; print('Today:', DateLogic.get_today())"

# Run tests
pytest test_date_logic.py -v

# Try a scenario (requires AWS credentials)
python lambda_function.py daily
```

## 5. Deploy to Lambda (5-10 minutes)

```bash
# See deployment_guide.md for detailed steps, or quick version:

# Package
pip install -r requirements.txt -t lambda_package/
cp lambda_function.py config.py date_logic.py datasync_manager.py lambda_package/
cd lambda_package && zip -r ../datasync-orchestrator.zip . && cd ..

# Deploy
aws lambda create-function \
  --function-name datasync-orchestrator \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-datasync-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://datasync-orchestrator.zip \
  --environment Variables={DATASYNC_NFS_LOCATION_ARN=arn:aws:...,DATASYNC_S3_LOCATION_ARN=arn:aws:...}

# Set up scheduling (EventBridge)
aws events put-rule --name datasync-daily --schedule-expression "cron(30 0 * * ? *)"
aws events put-targets --rule datasync-daily --targets Id=1,Arn=arn:aws:lambda:region:account:function:datasync-orchestrator
```

## Next Steps

- **Understand architecture**: Read [datasync_overview.md](datasync_overview.md)
- **Detailed setup**: See [setup_guide.md](setup_guide.md)
- **Production deployment**: Follow [deployment_guide.md](deployment_guide.md)
- **Troubleshooting**: Check [troubleshooting.md](troubleshooting.md)
- **API details**: See [api_reference.md](api_reference.md)

## Quick Reference

**Local Testing:**
```bash
python lambda_function.py daily                    # Copy today
python lambda_function.py backdated 2024/0721      # Copy specific date
python lambda_function.py range 7                  # Copy last 7 days
```

**AWS Commands:**
```bash
aws logs tail /aws/lambda/datasync-orchestrator --follow
aws datasync list-tasks
aws lambda invoke --function-name datasync-orchestrator --payload '{"scenario":"daily"}' response.json
```

**File Locations:**
```
Core Code:     config.py, date_logic.py, datasync_manager.py, lambda_function.py
Tests:         test_date_logic.py
Examples:      example_*.py
Documentation: README.md, developer_guide.md, api_reference.md, deployment_guide.md
```

## Common Issues

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `source venv/bin/activate` |
| AWS credentials error | `aws configure` |
| Config missing required values | `cp .env.example .env && nano .env` |
| Lambda timeout | Increase timeout in deployment_guide.md |
| No files copied | Check NAS path exists and date format is YYYY/MMDD |

---

**Need more help?** → See [developer_guide.md](developer_guide.md)

