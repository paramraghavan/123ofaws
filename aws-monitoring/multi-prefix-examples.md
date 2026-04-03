# Multiple Stack Prefix Examples

The monitoring system now supports monitoring resources from multiple CloudFormation stack prefixes simultaneously.

## Overview

Instead of running separate instances for different environments, you can monitor multiple stack prefixes in a single instance:

```bash
# Monitor both UAT and production stacks
python src/main.py --config config/config.yaml --prefixes uat-top,uat-bot,prod-

# Dashboard shows resources from all specified prefixes
# API aggregates data across all prefixes
# Single SNS topic receives alerts from all environments
```

## Configuration Methods

### Method 1: Config File (Recommended for Static Setup)

Edit `config/config.yaml`:

```yaml
cloudformation:
  enabled: true

  # Option A: YAML List format
  stack_prefixes:
    - uat-top
    - uat-bot
    - prod-
```

Or:

```yaml
cloudformation:
  enabled: true

  # Option B: Comma-separated string
  stack_prefixes: uat-top, uat-bot, prod-
```

Then run normally:
```bash
python src/main.py --config config/config.yaml
# Automatically uses prefixes from config file
```

### Method 2: Command-Line (For Dynamic/Testing)

```bash
# Single prefix
python src/main.py --config config/config.yaml --prefix uat-top

# Multiple prefixes
python src/main.py --config config/config.yaml --prefixes uat-top,uat-bot,prod-
```

**Priority** (highest to lowest):
1. CLI `--prefixes` argument
2. CLI `--prefix` argument
3. Config file `stack_prefixes` setting
4. Config file `stack_prefix` setting (default)

---

## Usage Examples

### Example 1: Monitor Two UAT Environments

```bash
python src/main.py \
  --config config/config.yaml \
  --prefixes uat-top,uat-bot \
  --port 5000
```

This discovers resources from:
- CloudFormation stacks starting with `uat-top`
- CloudFormation stacks starting with `uat-bot`

**Result**: Single dashboard shows all resources from both UAT environments

### Example 2: Monitor All Environments

```bash
python src/main.py \
  --config config/config.yaml \
  --prefixes uat-top,uat-bot,staging-,prod- \
  --port 5000
```

This discovers resources from all four environment prefixes:
- `uat-top*` - UAT Top resources
- `uat-bot*` - UAT Bot resources
- `staging-*` - Staging resources
- `prod-*` - Production resources

### Example 3: Config File with YAML List

Create `config/uat-config.yaml`:
```yaml
aws:
  profile: default
  primary_region: us-east-1

monitoring:
  check_interval: 300

cloudformation:
  enabled: true
  stack_prefixes:
    - uat-top
    - uat-bot

services:
  lambda:
    enabled: true
  ec2:
    enabled: true
  s3:
    enabled: true
  # ... other services

alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:us-east-1:123456789:monitoring
```

Run it:
```bash
python src/main.py --config config/uat-config.yaml
# Automatically monitors both uat-top and uat-bot stacks
```

### Example 4: Config File with Comma-Separated String

Create `config/all-env-config.yaml`:
```yaml
cloudformation:
  enabled: true
  stack_prefixes: uat-top, uat-bot, staging-, prod-

# ... rest of config
```

Run it:
```bash
python src/main.py --config config/all-env-config.yaml
# Monitors all four environment prefixes
```

### Example 5: Using the Startup Script

```bash
# Single prefix from config file
./scripts/run.sh config/config.yaml uat-top 5000

# Multiple prefixes from command line
./scripts/run.sh config/config.yaml "uat-top,uat-bot" 5000

# Multiple prefixes from config file (auto-detected)
./scripts/run.sh config/uat-config.yaml "" 5000
```

### Example 4: Development vs Production Config

Create separate configurations:

```bash
# config/dev-config.yaml - monitors dev stacks only
cloudformation:
  stack_prefix: dev-

# config/prod-config.yaml - monitors all prod/staging stacks
cloudformation:
  stack_prefix: prod-  # fallback if --prefixes not used
```

Then run:
```bash
# Monitor development
python src/main.py --config config/dev-config.yaml --prefix dev-

# Monitor production + staging
python src/main.py --config config/prod-config.yaml --prefixes prod-,staging-
```

## API Usage

All API endpoints automatically aggregate data across all monitored prefixes:

```bash
# Get status for all monitored environments
curl http://localhost:5000/api/status | jq

# Get Lambda resources from all prefixes
curl http://localhost:5000/api/service/lambda | jq

# Example response shows resources from all prefixes:
{
  "lambda": [
    {
      "resource_id": "uat-top-function-1",
      "status": "healthy",
      ...
    },
    {
      "resource_id": "uat-bot-function-2",
      "status": "degraded",
      ...
    },
    {
      "resource_id": "prod-function-1",
      "status": "healthy",
      ...
    }
  ]
}
```

## Dashboard

The dashboard automatically shows:

- **Summary Cards**: Total counts across all prefixes
  - Healthy resources (green)
  - Degraded resources (yellow)
  - Unhealthy resources (red)
  - Unknown status (gray)

- **Service Cards**: Per-service breakdowns
  - Shows resource counts for each service
  - Progress bars with status distribution

- **Resource Details**: Click into each service to see individual resources
  - Resource name/ID
  - Current status
  - Last update time
  - Metrics

## Alerts

SNS alerts are sent for resources across all prefixes:

```
[UAT-TOP] Lambda my-function is unhealthy
[UAT-BOT] EC2 i-12345678 is degraded
[PROD] S3 critical-bucket is unhealthy
```

Configure in `config.yaml`:
```yaml
alerts:
  sns_enabled: true
  sns_topic_arn: arn:aws:sns:region:account:monitoring-alerts
  email: ops@example.com
```

## Best Practices

### 1. Naming Convention

Use consistent stack naming across environments:
```
{environment}-{service}-{component}
```

Examples:
- `uat-top-lambda-processor`
- `uat-bot-s3-backup`
- `staging-ec2-web-server`
- `prod-lambda-api`

Then filter by prefix:
- `--prefix uat-top` → all UAT Top resources
- `--prefixes uat-top,uat-bot` → all UAT resources
- `--prefixes prod-,staging-` → production and staging

### 2. Separate Monitoring Instances

For large deployments, consider running separate instances:

```bash
# Terminal 1: Monitor UAT
python src/main.py --config config/config.yaml --prefixes uat-top,uat-bot --port 5001

# Terminal 2: Monitor Production
python src/main.py --config config/config.yaml --prefixes prod-,staging- --port 5002

# Terminal 3: Monitor Development
python src/main.py --config config/config.yaml --prefix dev- --port 5003
```

### 3. Different Check Intervals

Use different check intervals for different environments:

```yaml
# config/uat-config.yaml
monitoring:
  check_interval: 300  # Check every 5 minutes

# config/prod-config.yaml
monitoring:
  check_interval: 60   # Check every minute (more frequent)
```

```bash
python src/main.py --config config/uat-config.yaml --prefixes uat-top,uat-bot
python src/main.py --config config/prod-config.yaml --prefix prod-
```

### 4. Service Filtering

Different configurations for different services:

```yaml
# config/critical-services.yaml
services:
  lambda:
    enabled: true
    thresholds:
      error_rate: 1.0  # Strict threshold
  ec2:
    enabled: true
  s3:
    enabled: true
  # Other services disabled

# config/all-services.yaml
services:
  # All services enabled with standard thresholds
```

## Troubleshooting Multiple Prefixes

### No resources found
```bash
# Check if stacks exist with specified prefixes
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName, 'uat-')].StackName"
```

### Verify prefix syntax
```bash
# Correct: comma-separated, no spaces
--prefixes uat-top,uat-bot,prod-

# Incorrect: spaces around commas
--prefixes "uat-top, uat-bot, prod-"  # Will only match exact "uat-bot, " prefix!

# Also incorrect: single string
--prefixes "uat-top uat-bot prod-"
```

### Debug resource discovery
```bash
# Enable debug logging
python src/main.py \
  --config config/config.yaml \
  --prefixes uat-top,uat-bot \
  --debug

# Watch logs for "Discovering resources with prefix: uat-top"
```

## Performance Notes

- **Multiple prefixes have minimal performance impact**: CloudFormation queries are batched
- **Resource count**: System handles 100s of resources across multiple prefixes
- **Dashboard refresh**: Still happens every 30 seconds regardless of prefix count
- **Check interval**: Applies to all prefixes (all checked within same cycle)

Example with 3 prefixes and 300 resources total:
- 1 API call to list stacks (all prefixes)
- ~10-20 API calls to get resource details
- ~50 API calls for CloudWatch metrics
- Total time: ~30-45 seconds per check cycle
- Memory usage: ~50-100 MB

## Migration Guide

If you were running separate instances:

**Before (separate instances):**
```bash
# Terminal 1
python src/main.py --config config/config.yaml --prefix uat-top

# Terminal 2
python src/main.py --config config/config.yaml --prefix uat-bot
```

**After (single instance):**
```bash
python src/main.py --config config/config.yaml --prefixes uat-top,uat-bot
```

Benefits:
- Single dashboard for all prefixes
- One alert system
- Unified state management
- Simplified deployment

## Examples with Your Naming

If your stacks follow the pattern `{prefix}-{service}-{component}`:

```
uat-top-lambda-processor
uat-top-s3-data
uat-top-ec2-web
uat-bot-lambda-processor
uat-bot-s3-data
uat-bot-ec2-web
```

Monitor them all:
```bash
python src/main.py \
  --config config/config.yaml \
  --prefixes uat-top,uat-bot \
  --port 5000

# Result: Single dashboard with all 6 resources
# Status summary: X healthy, Y degraded, Z unhealthy
# Can drill down by service or prefix
```

---

**Notes:**
- Prefix matching is prefix-based (starts with), not exact match
- Resource names are preserved in the dashboard (you see full stack names)
- All services work with multiple prefixes (Lambda, EC2, S3, etc.)
- No additional configuration needed per prefix
