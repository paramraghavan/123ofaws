# AWS Monitoring System

Comprehensive monitoring system for AWS resources with CloudFormation auto-discovery, real-time dashboard, email alerts via SNS, and Control-M integration.

## Features

- **13 AWS Services Monitored**: Lambda, EC2, S3, SQS, SNS, EMR, AutoScaling, CloudFormation, SSM, IAM, ELBv2, KMS, Transfer
- **2 External Services**: Snowflake (data warehouse), Control-M (job scheduler)
- **CloudFormation Auto-Discovery**: Automatically discovers resources from CloudFormation stacks using stack name prefix filtering
- **Real-Time Dashboard**: Flask-based web UI showing health status of all resources
- **Direct Email Alerts**: Send alerts via Gmail, Office 365, SendGrid, or custom SMTP
- **Control-M Integration**: Webhook endpoints for Control-M event processing
- **Manual Failover**: Support for manual failover between regions
- **Local Testing**: Full LocalStack support for development and testing
- **Thread-Safe**: Background daemon runs health checks continuously
- **State Persistence**: File-based or DynamoDB state storage

## Quick Start

### Prerequisites

- Python 3.8+
- AWS credentials configured (via `aws configure` or environment variables)
- AWS CLI (optional, for verifying CloudFormation stacks)
- Email service configured (Gmail, Office 365, or custom SMTP server)

### Installation

```bash
cd aws-monitoring
pip install -r requirements.txt
```

### Configuration

1. Copy the example config:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Edit `config/config.yaml`:
   - Set `aws.profile` to your AWS profile name (optional)
   - Set `aws.primary_region` and `aws.secondary_region`
   - Enable desired services in the `services` section
   - **Configure email alerts** (see [EMAIL_ALERTING.md](EMAIL_ALERTING.md) for setup)
   - Configure CloudFormation stack prefix pattern

3. Quick email setup (Gmail example):
```yaml
alerts:
  email_enabled: true
  email: ops-team@example.com
  email_from: monitoring@company.com
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: your-email@gmail.com
  smtp_password: xxxx xxxx xxxx xxxx  # App password from Google
  smtp_tls: true
```

   See [EMAIL_ALERTING.md](EMAIL_ALERTING.md) for Office 365, SendGrid, AWS SES, and other providers.

3. For CloudFormation-based discovery, stacks must follow naming pattern:
   ```
   {stack_prefix}-{service}-{environment}
   Examples: uat-top-lambda, uat-top-ec2, uat-bot-s3
   ```

### Usage

```bash
# Start with default configuration and stack prefix
python src/main.py --config config/config.yaml --prefix uat-top

# Start with custom prefix
python src/main.py --config config/config.yaml --prefix uat-bot

# Monitor MULTIPLE prefixes (NEW!)
python src/main.py --config config/config.yaml --prefixes uat-top,uat-bot,prod-

# Run on custom port
python src/main.py --config config/config.yaml --prefix uat-top --port 8080

# Enable debug mode
python src/main.py --config config/config.yaml --prefix uat-top --debug
```

Access the dashboard at `http://localhost:5000`

## Local Development with LocalStack

### Setup LocalStack

```bash
# Start LocalStack (from /Users/paramraghavan/dev/123ofaws/simulate_aws)
cd ../simulate_aws
./setup.sh
docker-compose up
```

### Run Monitoring with LocalStack

```bash
# In another terminal
cd aws-monitoring
python src/main.py --config config/localstack-config.yaml --prefix test-
```

The system will connect to LocalStack at `http://localhost:4566` and use test resources.

## Architecture

### Core Components

- **`src/main.py`**: Entry point, orchestrates all components
- **`src/daemon.py`**: Background thread running periodic health checks
- **`src/cf_discovery.py`**: CloudFormation resource discovery engine
- **`src/monitors/`**: Service-specific monitor implementations
- **`src/alerts/`**: Alert management and delivery system
- **`src/app.py`**: Flask web application
- **`src/web/`**: Dashboard templates and static files

### Resource Discovery Flow

```
1. Load configuration (config.yaml)
2. Create AWS session with specified profile/region
3. CloudFormation discovery:
   - Query CloudFormation stacks matching prefix
   - Extract resources of monitored types (Lambda, EC2, etc.)
   - Map resources to service monitors
4. Initialize all monitors with discovered resources
5. Start background daemon to run health checks
6. Launch Flask web server for dashboard
```

### Health Check Flow

```
Background Daemon (every 5 minutes):
  1. For each enabled service:
     - Get discovered resources for that service
     - Call monitor.check_health(resource_ids)
     - Collect health status for each resource
     - Check if alert should be sent (status change)
  2. Send alerts via SNS if configured
  3. Update state in state_manager
  4. Make state available to Flask routes

Dashboard:
  - Fetches current state from daemon
  - Auto-refreshes every 30 seconds
  - Shows summary and per-service status
```

## Configuration Reference

### AWS Settings

```yaml
aws:
  primary_region: us-east-1      # Primary AWS region
  secondary_region: us-west-2    # Failover region
  profile: prod                   # AWS profile name (optional)
  localstack: false               # Use LocalStack for testing
```

### Monitoring Settings

```yaml
monitoring:
  check_interval: 300   # Health check interval in seconds
  max_retries: 3        # Retries for transient failures
  retry_delay: 5        # Delay between retries
```

### Service Configuration

Each service can be independently enabled/disabled with thresholds:

```yaml
services:
  lambda:
    enabled: true
    thresholds:
      error_rate: 5.0        # Alarm if error rate > 5%
      duration: 55000        # Alarm if avg duration > 55 seconds
    metrics:
      - Invocations
      - Errors
      - Duration
```

### CloudFormation Discovery

```yaml
cloudformation:
  enabled: true
  stack_prefix: uat-   # Filter stacks by prefix
                       # Finds: uat-lambda-prod, uat-ec2-dev, etc.
```

### Alerts

```yaml
alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789:alerts
  email: ops@example.com  # For SNS email subscriptions
```

## Multiple Stack Prefixes

You can monitor resources from multiple CloudFormation stack prefixes simultaneously:

```bash
# Monitor both UAT environments and production
python src/main.py \
  --config config/config.yaml \
  --prefixes uat-top,uat-bot,prod- \
  --port 5000
```

The system will:
1. Query CloudFormation for stacks matching `uat-top*`
2. Query CloudFormation for stacks matching `uat-bot*`
3. Query CloudFormation for stacks matching `prod-*`
4. Aggregate all resources into a single monitoring dashboard
5. Show combined health status for all environments

**Usage:**
- `--prefix NAME` - Monitor single prefix
- `--prefixes NAME1,NAME2,NAME3` - Monitor multiple prefixes (comma-separated)

## API Endpoints

### Dashboard
- `GET /` - Main dashboard view
- `GET /service/<name>` - Service detail view
- `GET /health` - Health check endpoint

### REST API
- `GET /api/status` - Current status for all services
- `GET /api/service/<name>` - Service resources and status
- `GET /api/resource/<service>/<resource_id>` - Specific resource health
- `GET /api/daemon/status` - Daemon status and last check time

### Webhooks
- `POST /webhook/controlm` - Control-M integration endpoint
- `POST /webhook/health` - Generic health webhook

## Monitoring 13 AWS Services

### Lambda
- Checks function state (Active)
- Monitors error rate, duration, invocation count
- Thresholds: error_rate (%), duration (ms)

### EC2
- Checks instance state (running/pending)
- Verifies status checks (system, instance)
- Monitors CPU utilization
- Thresholds: cpu_utilization (%)

### S3
- Checks bucket access and existence
- Verifies versioning, encryption, public access block
- Thresholds: versioning_enabled, encryption_enabled (boolean)

### SQS
- Checks queue access
- Monitors message count
- Thresholds: message_count

### SNS
- Checks topic existence
- Monitors subscription count
- No thresholds by default

### EMR
- Checks cluster state
- Monitors WAITING, RUNNING, TERMINATED states
- No thresholds by default

### AutoScaling (ASG)
- Checks desired vs current capacity
- Monitors instance health status
- Verifies in-service instance count
- No thresholds by default

### CloudFormation
- Checks stack status
- Monitors CREATE_COMPLETE, UPDATE_COMPLETE, FAILED states
- Alerts on failures and rollbacks

### Systems Manager (SSM)
- Checks document status
- Monitors Active, Draft states
- Verifies document accessibility

### IAM
- Checks role existence
- Monitors attached policies (inline and managed)
- Flags roles with no policies

### Elastic Load Balancer v2 (ELBv2)
- Checks load balancer state (active)
- Monitors target groups
- Verifies target health
- Thresholds: target_health_count

### Key Management Service (KMS)
- Checks key state (Enabled)
- Verifies key rotation status
- Monitors pending deletion keys
- Alerts on disabled keys

### AWS Transfer
- Checks server state (ONLINE/OFFLINE)
- Verifies enabled protocols (SFTP, FTPS, FTP)
- No thresholds by default

## Troubleshooting

### No Resources Discovered
- Verify CloudFormation stacks exist in primary region
- Check stack naming matches prefix pattern
- Confirm AWS credentials and IAM permissions
- Check logs for CloudFormation API errors

### Dashboard Not Updating
- Check daemon is running (should see log messages)
- Verify state file is being written to
- Check logs for health check errors
- Ensure services are configured as enabled

### SNS Alerts Not Sent
- Verify SNS topic ARN is correct
- Confirm IAM permissions for SNS:Publish
- Check topic subscription (especially email confirms)
- Verify alert_manager is initialized

### LocalStack Connection Failed
- Ensure LocalStack container is running
- Check endpoint URL is `http://localhost:4566`
- Verify `localstack: true` in configuration
- Check Docker networking

## Performance Considerations

- **Check Interval**: Default 300 seconds (5 minutes). Lower for faster updates, higher for less API calls.
- **State Storage**: File-based is fast, DynamoDB for distributed deployments.
- **Concurrent Checks**: Services are checked sequentially; can be parallelized if needed.
- **CloudWatch Metrics**: Retrieved for last 5 minutes with 60-second granularity.

## Security Notes

- **Credentials**: Uses AWS profiles/environment variables, never logs credentials
- **State File**: Contains only health status, no sensitive data
- **SNS**: Topic ARN should be restricted to monitoring system
- **Flask**: Runs with `use_reloader=False` for production
- **No Authentication**: Add reverse proxy (nginx) with auth for production

## Future Enhancements

- [ ] DynamoDB state storage backend
- [ ] Automatic failover (not just manual)
- [ ] Slack/PagerDuty integrations
- [ ] Custom metrics from CloudWatch
- [ ] Resource cost tracking
- [ ] Scheduled reports
- [ ] Parallel health check execution
- [ ] Web UI for configuration management

## Support

For issues, questions, or contributions:
1. Check logs in daemon output
2. Verify AWS credentials and permissions
3. Test with LocalStack first
4. Review configuration against examples

## License

Part of 123ofaws educational AWS learning repository.
