# AWS Monitoring System - Quick Start Guide

Get the monitoring system running in 5 minutes.

## Step 1: Setup Configuration

```bash
cd aws-monitoring

# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit config.yaml with your settings
# - Set AWS profile (optional)
# - Set primary and secondary regions
# - Set SNS topic ARN for alerts (optional)
# - Enable desired services
```

Key configuration items:
```yaml
aws:
  profile: my-profile          # Your AWS profile
  primary_region: us-east-1

cloudformation:
  # Option 1: Single prefix
  stack_prefix: uat-

  # Option 2: Multiple prefixes (uncomment one)
  # stack_prefixes:
  #   - uat-top
  #   - uat-bot

  # Or as comma-separated string:
  # stack_prefixes: uat-top, uat-bot, prod-

alerts:
  # Option 1: Direct email (preferred)
  email_enabled: true
  email: ops-team@example.com

  # Option 2: SNS to email (alternative)
  # sns_enabled: true
  # sns_topic_arn: arn:aws:sns:us-east-1:123456789012:monitoring-alerts

  # Option 3: SNS FIFO queue (for ordered alerts with deduplication)
  # sns_enabled: true
  # sns_topic_arn: arn:aws:sns:us-east-1:123456789012:monitoring-alerts.fifo
  # ^^ Note: .fifo suffix routes to SQS FIFO queue instead of email
```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Verify AWS Credentials

```bash
# Test AWS access
aws sts get-caller-identity --profile my-profile

# Or use environment variables
export AWS_PROFILE=my-profile
aws sts get-caller-identity
```

## Step 4: Start the System

### Option A: Using the startup script

```bash
./scripts/run.sh config/config.yaml uat-top 5000
```

### Option B: Direct Python

```bash
python src/main.py --config config/config.yaml --prefix uat-top --port 5000
```

### Option C: Monitor MULTIPLE prefixes

```bash
# Monitor both uat-top and uat-bot simultaneously
python src/main.py \
  --config config/config.yaml \
  --prefixes uat-top,uat-bot,prod- \
  --port 5000
```

### Option D: With custom parameters

```bash
python src/main.py \
  --config config/config.yaml \
  --prefix uat-bot \
  --port 8080 \
  --host 127.0.0.1 \
  --debug
```

## Step 5: Access Dashboard

Open browser to: `http://localhost:5000`

You should see:
- Service status cards with health counts
- Real-time resource list
- Auto-refresh every 30 seconds

## Expected Flow

1. **Startup**: System reads config and discovers CloudFormation stacks
2. **Discovery**: Resources matching your prefix are identified
3. **Initial Check**: First health check runs (30-60 seconds)
4. **Periodic Checks**: Health checks run every 5 minutes (configurable)
5. **Alerts**: If enabled, SNS alerts sent on status changes
6. **Dashboard**: Real-time display of all resource health

## Troubleshooting Quick Fixes

### No resources found
```bash
# Check CloudFormation stacks exist
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName, 'uat-')].StackName" \
  --region us-east-1
```

### Can't connect to AWS
```bash
# Verify credentials
aws sts get-caller-identity

# Try with explicit profile
export AWS_PROFILE=your-profile
python src/main.py --config config/config.yaml --prefix uat-top
```

### Services not showing up
```bash
# Check enabled services in config.yaml
# Services must have: enabled: true

# Check logs for errors (first 50 lines)
# Should see: "Created monitor for: lambda", "Created monitor for: ec2", etc.
```

### Dashboard not updating
```bash
# Check daemon is running (logs should show periodic checks)
# Check state file is being created:
ls -la /tmp/monitoring-state.json

# Try shorter check interval for faster testing:
# monitoring:
#   check_interval: 60
```

## Local Testing with LocalStack

For development without AWS account:

```bash
# Terminal 1: Start LocalStack
cd ../simulate_aws
docker-compose up

# Terminal 2: Run monitoring with LocalStack config
cd ../aws-monitoring
python src/main.py --config config/localstack-config.yaml --prefix test-
```

## Next Steps

1. **Configure Services**: Edit `config/config.yaml` to enable specific services
2. **Set Alert Thresholds**: Adjust `thresholds` for each service
3. **Enable Alerts**: Choose from:
   - Direct email: `alerts.email_enabled: true` (see [email-alerting.md](email-alerting.md))
   - SNS to email: `alerts.sns_enabled: true`
   - **SNS FIFO queue** (new): Use topic ARN ending in `.fifo` (see [fifo-queue-alerting.md](../docs/fifo-queue-alerting.md))
4. **Customize Interval**: Change `monitoring.check_interval` (in seconds)
5. **Test Failover**: Configure secondary region for manual failover

## API Endpoints

Test the API while system is running:

```bash
# Get overall status
curl http://localhost:5000/api/status | jq

# Get specific service
curl http://localhost:5000/api/service/lambda | jq

# Get specific resource
curl http://localhost:5000/api/resource/lambda/my-function | jq

# Check daemon
curl http://localhost:5000/api/daemon/status | jq

# Control-M webhook test
curl -X POST http://localhost:5000/webhook/controlm \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'
```

## Common Operations

### Change stack prefix
```bash
# Monitor different CloudFormation prefix
python src/main.py --config config/config.yaml --prefix uat-bot
```

### Enable more services
1. Edit `config/config.yaml`
2. Change `enabled: false` → `enabled: true` for desired services
3. Restart the system

### Adjust check interval
```yaml
monitoring:
  check_interval: 60  # Check every 60 seconds instead of 300
```

### Run on different port
```bash
python src/main.py --config config/config.yaml --prefix uat-top --port 8080
```

## Stop the System

Press `Ctrl+C` in the terminal running the system. It will gracefully shut down the daemon and save state.

## Next: Production Deployment

- [ ] Use DynamoDB instead of file storage
- [ ] Add reverse proxy (nginx) with authentication
- [ ] Configure CloudWatch logs
- [ ] Set up Auto Scaling for web server
- [ ] Add S3 bucket for state backups
- [ ] Configure VPC endpoint for private access
- [ ] Set up monitoring dashboards in CloudWatch

For more details, see README.md
