# Monitoring External Services: Snowflake & Control-M

The AWS Monitoring System now supports monitoring external services like Snowflake and Control-M to ensure they're up and running.

## Snowflake Monitoring

Monitor Snowflake data warehouse availability and warehouse/database health.

### Setup

#### 1. Install Snowflake Connector

```bash
pip install snowflake-connector-python
```

#### 2. Configure in `config/config.yaml`

```yaml
services:
  snowflake:
    enabled: true
    snowflake_account: xy12345.us-east-1     # Your account
    snowflake_warehouse: COMPUTE_WH            # Default warehouse
    snowflake_database: ANALYTICS              # Optional
    # Credentials via environment variables (recommended for security)
    # snowflake_user: ${SNOWFLAKE_USER}
    # snowflake_password: ${SNOWFLAKE_PASSWORD}
    thresholds: {}
```

#### 3. Set Credentials

**Option A: Environment Variables (Recommended)**
```bash
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_PASSWORD=your_password

python src/main.py --config config/config.yaml --prefix uat-
```

**Option B: In Config File**
```yaml
services:
  snowflake:
    enabled: true
    snowflake_user: your_username
    snowflake_password: your_password  # NOT recommended in version control
```

#### 4. Specify Resources to Monitor

In CloudFormation stacks or via command line:

```yaml
# In CloudFormation, tag Snowflake resources with monitoring prefix
# Or specify in config discovery

# Resources can be warehouse names or database names:
# - COMPUTE_WH
# - ANALYTICS
# - REPORTING_WH
```

### What It Monitors

✅ **Warehouse Health**
  - Warehouse state (AVAILABLE, SUSPENDED, etc.)
  - Ability to connect and execute queries
  - Resource accessibility

✅ **Database Health**
  - Database accessibility
  - Connection validation
  - Schema availability

### Health Status Mapping

- **HEALTHY**: Warehouse is AVAILABLE or database is accessible
- **DEGRADED**: Warehouse is SUSPENDED
- **UNHEALTHY**: Cannot connect, warehouse doesn't exist, connection failed
- **UNKNOWN**: Connector not installed, account not configured

### Example Configuration

```yaml
# config/snowflake-monitoring.yaml
aws:
  primary_region: us-east-1

services:
  snowflake:
    enabled: true
    snowflake_account: xy12345.us-east-1
    snowflake_warehouse: COMPUTE_WH
    snowflake_database: ANALYTICS
    # Credentials from environment variables
    thresholds: {}

monitoring:
  check_interval: 300  # Check every 5 minutes

alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789:monitoring
```

### Usage

```bash
# Set credentials
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_PASSWORD=your_password

# Monitor Snowflake
python src/main.py --config config/snowflake-monitoring.yaml
```

### API Examples

```bash
# Get Snowflake status
curl http://localhost:5000/api/service/snowflake | jq

# Response
{
  "service": "snowflake",
  "resources": [
    {
      "resource_id": "COMPUTE_WH",
      "resource_name": "COMPUTE_WH",
      "resource_type": "Snowflake",
      "status": "healthy",
      "message": "Warehouse COMPUTE_WH is AVAILABLE",
      "metrics": {
        "warehouse": "COMPUTE_WH",
        "state": "AVAILABLE"
      }
    }
  ]
}
```

---

## Control-M Monitoring

Monitor Control-M service availability and job health.

### Setup

#### 1. Install Required Library

```bash
pip install requests
```

#### 2. Configure in `config/config.yaml`

```yaml
services:
  controlm:
    enabled: true
    controlm_endpoint: http://controlm-server:8080/ctm  # Control-M API endpoint
    # Credentials via environment variables (recommended)
    # controlm_user: ${CONTROLM_USER}
    # controlm_password: ${CONTROLM_PASSWORD}
    verify_ssl: true  # Set to false for self-signed certificates
    thresholds: {}
```

#### 3. Set Credentials

**Option A: Environment Variables (Recommended)**
```bash
export CONTROLM_USER=your_username
export CONTROLM_PASSWORD=your_password

python src/main.py --config config/config.yaml --prefix uat-
```

**Option B: In Config File**
```yaml
services:
  controlm:
    enabled: true
    controlm_endpoint: http://controlm-server:8080/ctm
    controlm_user: your_username
    controlm_password: your_password  # NOT recommended
```

#### 4. Specify Resources to Monitor

Monitor specific Control-M jobs:

```yaml
# Resources are Control-M job names:
# - DAILY_BATCH_JOB
# - ETL_PROCESS
# - DATA_VALIDATION
```

### What It Monitors

✅ **Control-M Service**
  - Service health/availability
  - API endpoint accessibility
  - Service status

✅ **Jobs**
  - Job execution status
  - Job state (Ready, Executing, Failed, etc.)
  - Job health

✅ **Agents**
  - Agent availability
  - Agent status

### Health Status Mapping

**Service Health:**
- **HEALTHY**: Service is operational
- **DEGRADED**: Service has issues but responding
- **UNHEALTHY**: Service is down or unreachable
- **UNKNOWN**: Cannot connect to API

**Job Health:**
- **HEALTHY**: Executing, Scheduled, or Ready
- **DEGRADED**: On Hold or Suspended
- **UNHEALTHY**: Failed, Aborted, or Ended Not Ok
- **UNKNOWN**: Unknown status

### Example Configuration

```yaml
# config/controlm-monitoring.yaml
aws:
  primary_region: us-east-1

services:
  controlm:
    enabled: true
    controlm_endpoint: http://controlm-server:8080/ctm
    verify_ssl: true
    thresholds: {}

monitoring:
  check_interval: 300  # Check every 5 minutes

alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789:monitoring
```

### Usage

```bash
# Set credentials
export CONTROLM_USER=your_username
export CONTROLM_PASSWORD=your_password

# Monitor Control-M
python src/main.py --config config/controlm-monitoring.yaml
```

### API Examples

```bash
# Get Control-M status
curl http://localhost:5000/api/service/controlm | jq

# Response
{
  "service": "controlm",
  "resources": [
    {
      "resource_id": "controlm-service",
      "resource_name": "Control-M Service",
      "resource_type": "Control-M",
      "status": "healthy",
      "message": "Control-M service is operational",
      "metrics": {
        "status": "healthy"
      }
    },
    {
      "resource_id": "DAILY_BATCH_JOB",
      "resource_name": "DAILY_BATCH_JOB",
      "resource_type": "Control-M",
      "status": "healthy",
      "message": "Job DAILY_BATCH_JOB status: Executing",
      "metrics": {
        "status": "Executing",
        "type": "job"
      }
    }
  ]
}
```

---

## Monitoring Both Services

Monitor Snowflake AND Control-M together:

```yaml
# config/unified-monitoring.yaml
services:
  # AWS Services
  lambda:
    enabled: true
  ec2:
    enabled: true
  s3:
    enabled: true

  # External Services
  snowflake:
    enabled: true
    snowflake_account: xy12345.us-east-1
    snowflake_warehouse: COMPUTE_WH

  controlm:
    enabled: true
    controlm_endpoint: http://controlm-server:8080/ctm
```

Run it:
```bash
export SNOWFLAKE_USER=sf_user SNOWFLAKE_PASSWORD=sf_pass
export CONTROLM_USER=ctm_user CONTROLM_PASSWORD=ctm_pass

python src/main.py --config config/unified-monitoring.yaml
```

**Dashboard shows:**
- AWS resources (Lambda, EC2, S3, etc.)
- Snowflake warehouses
- Control-M service + jobs
- All in one unified status view

---

## Alerts

SNS alerts are sent when services become unhealthy:

```
[SNOWFLAKE] COMPUTE_WH is unhealthy - Cannot connect to Snowflake

[CONTROLM] DAILY_BATCH_JOB is unhealthy - Job Failed

[CONTROLM] Control-M Service is unhealthy - Cannot connect to Control-M API
```

Configure in config.yaml:
```yaml
alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:region:account:monitoring-alerts
  email: ops@example.com
```

---

## Security Best Practices

### 1. Use Environment Variables for Credentials

```bash
# Good - credentials in environment
export SNOWFLAKE_PASSWORD=your_password
export CONTROLM_PASSWORD=your_password

python src/main.py --config config/config.yaml
```

**Never commit credentials to version control!**

### 2. Use IAM Roles for AWS Access

The AWS Monitoring System uses boto3, which automatically picks up:
- IAM instance roles (EC2)
- ECS task roles
- Lambda execution roles
- AWS credentials from `~/.aws/credentials`

### 3. Rotate Credentials Regularly

```bash
# Update Snowflake password in Snowflake console
# Update Control-M password in Control-M console
# Update environment variables in deployment
```

### 4. Restrict Access

```bash
# Use security groups to restrict Control-M API access
# Use VPC endpoints for Snowflake (if supported)
# Use private endpoints instead of public URLs
```

---

## Troubleshooting

### Snowflake Connection Issues

```bash
# Check credentials
python -c "
import snowflake.connector
ctx = snowflake.connector.connect(
    user='$SNOWFLAKE_USER',
    password='$SNOWFLAKE_PASSWORD',
    account='xy12345.us-east-1'
)
print('Connected!')
ctx.close()
"

# Check if connector is installed
pip list | grep snowflake

# Verify account ID format
# Should be like: xy12345.us-east-1 (not just xy12345)
```

### Control-M Connection Issues

```bash
# Check API endpoint
curl -u username:password http://controlm-server:8080/ctm/api/v2/monitoring/health

# Check credentials
curl -u username:password http://controlm-server:8080/ctm/api/v2/jobs/test

# Check firewall/network access
ping controlm-server
telnet controlm-server 8080
```

### Common Errors

**"snowflake-connector-python not installed"**
```bash
pip install snowflake-connector-python
```

**"Control-M endpoint not configured"**
```bash
# Set in config or environment
export CONTROLM_ENDPOINT=http://controlm-server:8080/ctm
```

**"Cannot connect to Snowflake"**
- Check credentials (user, password, account ID)
- Check network connectivity
- Verify account ID format (should include region)

**"Control-M API returned 401"**
- Check username/password
- Verify user has API access permissions

---

## Examples

### Monitor Everything (AWS + External Services)

```yaml
# config/full-monitoring.yaml
aws:
  profile: default
  primary_region: us-east-1

cloudformation:
  enabled: true
  stack_prefixes:
    - uat-top
    - uat-bot
    - prod-

services:
  # AWS Services (13)
  lambda:
    enabled: true
  ec2:
    enabled: true
  s3:
    enabled: true
  sqs:
    enabled: true
  sns:
    enabled: true
  emr:
    enabled: true
  asg:
    enabled: true
  cfn:
    enabled: true
  ssm:
    enabled: true
  iam:
    enabled: true
  elbv2:
    enabled: true
  kms:
    enabled: true
  transfer:
    enabled: true

  # External Services (2)
  snowflake:
    enabled: true
    snowflake_account: xy12345.us-east-1
    snowflake_warehouse: COMPUTE_WH
    snowflake_database: ANALYTICS

  controlm:
    enabled: true
    controlm_endpoint: http://controlm-server:8080/ctm
    verify_ssl: true

monitoring:
  check_interval: 300

alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789:monitoring
  email: ops@example.com
```

Run:
```bash
export SNOWFLAKE_USER=admin SNOWFLAKE_PASSWORD=...
export CONTROLM_USER=admin CONTROLM_PASSWORD=...

python src/main.py --config config/full-monitoring.yaml
```

**Result:** Single dashboard monitoring 15 services + 13 AWS services!

---

## Summary

✅ **Snowflake Monitor**
- Check warehouse availability
- Validate database accessibility
- Monitor Snowflake connectivity

✅ **Control-M Monitor**
- Verify Control-M service health
- Monitor job execution status
- Track job failures

✅ **Features**
- Integrated with existing dashboard
- SNS alerts on failures
- REST API for integration
- Environment variable support for credentials
- SSL certificate validation options

✅ **Security**
- No credentials in code
- Environment variable support
- SSL/TLS validation
- Works with any Control-M/Snowflake deployment
