# Copy Files from On-Premises NFS to AWS S3 using DataSync

**Simple solution to migrate files from your brownfield server to AWS S3**

## The Problem

You have files on an on-premises NFS mount that you want to copy to AWS S3. Your brownfield server is being retired, so you need an automated solution.

**NFS Location**: `/mydata/prod/icm/datain/poolData/`
**AWS Destination**: `s3://your-bucket/poolData/`
- **Complete error handling** and SNS notifications
- **CloudWatch logging** for monitoring and debugging
- **Simple Python implementation** - easy to understand and modify

## Quick Start

### 1. Prerequisites

- AWS Account with DataSync permissions
- DataSync Agent installed on edge node
- S3 bucket created
- Python 3.9+ (for testing)
- AWS CLI v2 configured

### 2. Deploy in 5 Minutes

```bash
# Clone/download this project
cd /Users/paramraghavan/dev/123ofaws/datasync

# Set environment variables (or edit config.py)
export DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:region:account:location/nfs/xxxxx
export DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:region:account:location/s3/yyyyy
export S3_BUCKET=my-datasync-bucket
export ENVIRONMENT=prod

# Install dependencies
pip install -r requirements.txt

# Test locally
python lambda_function.py daily

# Deploy to Lambda (see deployment_guide.md)
```

### 3. Usage

#### Daily Automatic Copy
EventBridge rule triggers Lambda daily at 00:30 UTC (configurable)

#### Manual Invocation
```bash
# Today's data
aws lambda invoke --function-name datasync-orchestrator \
  --payload '{"scenario":"daily"}' response.json

# Specific date (backdated)
aws lambda invoke --function-name datasync-orchestrator \
  --payload '{"scenario":"backdated","custom_date":"2024/0721"}' response.json

# Last 7 days
aws lambda invoke --function-name datasync-orchestrator \
  --payload '{"scenario":"weekly"}' response.json
```

---

## Architecture

```
┌─────────────────┐
│   NAS Storage   │
│ /vol/xxx/data   │
└────────┬────────┘
         │
         │ (NFS mount)
         │
┌────────▼──────────────┐
│   Edge Node (Agent)   │
│   DataSync Agent      │
└────────┬──────────────┘
         │
         │ (Port 443)
         │
┌────────▼──────────────┐
│  AWS DataSync         │
│  Task Executor        │
└────────┬──────────────┘
         │
         │
┌────────▼──────────────┐
│   S3 Bucket           │
│   Destination         │
└───────────────────────┘

ORCHESTRATION:
┌──────────────────────────┐
│  EventBridge (Cron)      │  Triggers daily
│  or Manual Invocation    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Lambda Function         │
│  1. Calculate date       │
│  2. Create/Find task     │
│  3. Execute task         │
│  4. Monitor completion   │
│  5. Send notification    │
└──────────────────────────┘
```

---

## File Structure

```
datasync/
├── README.md                    # This file
├── datasync_overview.md        # Detailed DataSync explanation
├── setup_guide.md              # Phase-by-phase setup
├── deployment_guide.md         # Complete deployment instructions
├── troubleshooting.md          # Common issues and solutions
│
├── config.py                   # Configuration (environment-based)
├── date_logic.py               # Date calculation logic
├── datasync_manager.py         # DataSync API wrapper
├── lambda_function.py          # Lambda handler (main entry point)
│
├── requirements.txt            # Python dependencies
├── test_date_logic.py          # Unit tests for date logic
│
└── examples/
    ├── daily_scenario.py       # Example: daily copy
    ├── backdated_scenario.py   # Example: backdated copy
    └── monitoring.py           # Example: monitor tasks
```

---

## Core Modules

### config.py
Configuration management with support for environment variables and AWS Systems Manager Parameter Store.

**Key settings:**
- DataSync location ARNs
- NAS and S3 paths
- Data types to copy
- AWS region and environment
- Task options and timeouts

```python
from config import get_config

config = get_config()
print(config.NAS_BASE_PATH)           # /mydata/prod/icm/datain/poolData
print(config.get_datatypes())         # ['datatype1', 'datatype2']
print(config.get_nas_source_path('datatype1', '2024/0804'))
# Output: /mydata/prod/icm/datain/poolData/datatype1/2024/0804
```

### date_logic.py
Calculate which dates to copy based on various scenarios.

**Scenarios:**
- `daily`: Copy today's data (default)
- `backdated`: Copy specific date
- `range`: Copy last N days
- `weekly`: Copy last 7 days
- `monthly`: Copy all days from previous month end

```python
from date_logic import DataSyncDateCalculator

calculator = DataSyncDateCalculator()

# Today
dates = calculator.calculate_dates_to_copy('daily')
# Output: ['2024/0804']

# Last 7 days
dates = calculator.calculate_dates_to_copy('weekly')
# Output: ['2024/0804', '2024/0803', '2024/0802', ...]

# Specific date
dates = calculator.calculate_dates_to_copy('backdated', custom_date='2024/0721')
# Output: ['2024/0721']
```

### datasync_manager.py
Wrapper around AWS DataSync API for task management and execution.

```python
from datasync_manager import DataSyncOrchestrator
from config import get_config

config = get_config()
orchestrator = DataSyncOrchestrator(config)

# Execute copy task
result = orchestrator.execute_copy_task(
    datatype='inventory',
    date_str='2024/0804',
    wait_for_completion=True
)

print(result['status'])  # 'SUCCESS'
print(result['details']['FilesTransferred'])  # Number of files copied
```

### lambda_function.py
Lambda handler for CloudWatch Events/EventBridge trigger.

**Supported event formats:**
```json
{
  "scenario": "daily",
  "custom_date": "2024/0804",
  "days_back": 7,
  "wait_for_completion": true
}
```

---

## Usage Examples

### Example 1: Copy Today's Data (Daily)

```bash
python lambda_function.py daily
```

**Output:**
```json
{
  "statusCode": 200,
  "body": {
    "message": "DataSync orchestration completed",
    "scenario": "daily",
    "dates_copied": ["2024/0804"],
    "successful": 3,
    "failed": 0
  }
}
```

### Example 2: Copy Backdated Data

```bash
python lambda_function.py backdated 2024/0721
```

### Example 3: Copy Last 7 Days

```bash
python lambda_function.py range 7
```

### Example 4: Programmatic Usage

```python
from datasync_manager import DataSyncOrchestrator
from config import get_config

config = get_config()
orchestrator = DataSyncOrchestrator(config)

# Copy multiple dates for multiple datatypes
results = orchestrator.execute_batch_copy(
    dates=['2024/0801', '2024/0802', '2024/0803'],
    datatypes=['inventory', 'orders'],
    wait_for_completion=True
)

for result in results:
    print(f"{result['datatype']}/{result['date']}: {result['status']}")
```

---

## Configuration

### Environment Variables

Required:
```bash
DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:region:account:location/nfs/xxxxx
DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:region:account:location/s3/yyyyy
S3_BUCKET=my-datasync-bucket
NAS_BASE_PATH=/mydata/prod/icm/datain/poolData
```

Optional:
```bash
DATATYPES=datatype1,datatype2,datatype3
ENVIRONMENT=prod
AWS_REGION=us-east-1
SNS_TOPIC_ARN=arn:aws:sns:region:account:datasync-notifications
TASK_TIMEOUT_SECONDS=3600
MAX_RETRIES=3
```

### Path Structure

**NAS Paths:**
```
/mydata/prod/icm/datain/poolData/
├── datatype1/2024/0804/files...
├── datatype2/2024/0804/files...
└── datatype3/2024/0804/files...
```

**S3 Paths:**
```
s3://my-datasync-bucket/
└── poolData/
    ├── datatype1/2024/0804/files...
    ├── datatype2/2024/0804/files...
    └── datatype3/2024/0804/files...
```

---

## Testing

### Unit Tests

```bash
# Run all tests
python -m pytest test_date_logic.py -v

# Run specific test
python -m pytest test_date_logic.py::TestDateLogic::test_today_format -v

# Run with coverage
python -m pytest test_date_logic.py --cov=date_logic
```

### Manual Testing

```bash
# Test date calculation
python -c "
from date_logic import DateLogic
print('Today:', DateLogic.get_today())
print('Last 3 days:', DateLogic.get_last_n_days(3))
"

# Test with event payload
python lambda_function.py daily
python lambda_function.py backdated 2024/0721
python lambda_function.py range 7
```

---

## Deployment

See [deployment_guide.md](deployment_guide.md) for step-by-step deployment instructions.

Quick summary:
1. Create IAM roles and policies
2. Set up S3 bucket and SNS topic
3. Package Lambda function
4. Deploy to Lambda
5. Create EventBridge trigger

---

## Monitoring

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/datasync-orchestrator --follow

# Filter by date
aws logs filter-log-events \
  --log-group-name /aws/lambda/datasync-orchestrator \
  --filter-pattern "2024/0804"
```

### DataSync Metrics

```bash
# List tasks
aws datasync list-tasks

# Get task details
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:region:account:tasexecution/xxxxx
```

### SNS Notifications

Receive email notifications on:
- Task completion
- Task failure
- Validation errors

---

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for:
- Permission errors
- Missing files
- Timeout issues
- Date calculation problems
- Agent connectivity issues

---

## FAQ

**Q: Can I copy files from multiple NAS servers?**
A: Yes, create separate DataSync locations and configure multiple tasks.

**Q: What if a file is being written while DataSync copies it?**
A: DataSync has verification enabled to detect incomplete copies. Consider scheduling after file writes complete.

**Q: Can I run this on a schedule other than daily?**
A: Yes, modify the EventBridge rule cron expression in deployment_guide.md

**Q: How do I handle large file volumes?**
A: Increase Lambda timeout and DataSync task timeout in config.py

**Q: Can I copy files in parallel for multiple datatypes?**
A: Yes, set `ENABLE_PARALLEL_TASKS=true` in config.py (implementation in progress)

---

## Security Best Practices

1. **Encryption in Transit**: DataSync uses TLS 1.2
2. **IAM Roles**: Use least-privilege IAM policies
3. **S3 Encryption**: Enable server-side encryption (AES-256 or KMS)
4. **Bucket Versioning**: Enable to protect against accidental deletes
5. **Access Logging**: Enable S3 access logging
6. **VPC Endpoints**: Consider using for private connectivity

---

## Performance Tuning

- **Parallel Tasks**: Configure for multiple datatypes
- **Bandwidth Throttling**: Set via DataSync options
- **Verification Mode**: POINT_IN_TIME_CONSISTENT (slower but safer)
- **Transfer Mode**: CHANGED (only copies modified files)

---

## Support

- AWS DataSync Documentation: https://docs.aws.amazon.com/datasync/
- Report issues: Create GitHub issue
- AWS Support: Open AWS Support ticket

---

## License

MIT License

---

## Author

Built for AWS brownfield server retirement migration scenarios.

