# Developer Guide - Getting Started

Welcome! This guide is for developers new to this project. It will help you set up, understand, and contribute to the DataSync Orchestrator.

## 📋 Quick Navigation

- **New to this project?** → Start with [Local Development Setup](#local-development-setup)
- **Need to deploy?** → See [deployment_guide.md](deployment_guide.md)
- **Running into issues?** → Check [troubleshooting.md](troubleshooting.md)
- **Understanding the code?** → Read [CODE_STRUCTURE.md](#code-structure)
- **API reference?** → See [api_reference.md](api_reference.md)

---

## Local Development Setup

### Step 1: Clone and Navigate

```bash
cd /Users/paramraghavan/dev/123ofaws/datasync
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt

# For development (includes test tools)
pip install -r requirements.txt pytest pytest-cov black flake8
```

### Step 4: Set Up Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env

# Or set environment variables directly
export DATASYNC_NFS_LOCATION_ARN=arn:aws:datasync:...
export DATASYNC_S3_LOCATION_ARN=arn:aws:datasync:...
export NAS_BASE_PATH=/mydata/prod/icm/datain/poolData
export S3_BUCKET=my-bucket
export DATATYPES=datatype1,datatype2
```

### Step 5: Verify Installation

```bash
# Test configuration loads
python -c "from config import get_config; print('✓ Config loaded')"

# Run date logic test
python -c "from date_logic import DateLogic; print('Today:', DateLogic.get_today())"

# Run full test suite
pytest test_date_logic.py -v
```

---

## Code Structure

```
datasync/
├── Core Modules (implement the actual logic)
│   ├── config.py              # Configuration management
│   ├── date_logic.py          # Date calculation utilities
│   ├── datasync_manager.py    # AWS DataSync API wrapper
│   └── lambda_function.py     # Lambda entry point
│
├── Examples (learn by doing)
│   ├── example_daily_copy.py
│   ├── example_backdated_copy.py
│   └── example_monitoring.py
│
├── Tests (verify everything works)
│   └── test_date_logic.py
│
└── Documentation (understand the "why")
    ├── README.md              # Start here
    ├── developer_guide.md     # This file
    ├── setup_guide.md         # AWS setup
    ├── deployment_guide.md    # Production deployment
    ├── datasync_overview.md   # Architecture & options
    └── troubleshooting.md     # Issue solutions
```

---

## Understanding the Modules

### config.py
**What it does**: Loads configuration from environment variables
**Key classes**:
- `Config`: Base configuration
- `LocalConfig`, `DevConfig`, `ProdConfig`: Environment-specific
- `get_config()`: Factory function

**Common operations**:
```python
from config import get_config

config = get_config()
print(config.NAS_BASE_PATH)           # Get a value
print(config.get_datatypes())         # Get list of datatypes
print(config.get_nas_source_path(...))  # Generate NAS path
```

### date_logic.py
**What it does**: Calculate which dates to copy
**Key classes**:
- `DateLogic`: Static utility methods for date operations
- `DataSyncDateCalculator`: High-level scenario calculator

**Common operations**:
```python
from date_logic import DateLogic, DataSyncDateCalculator

# Get today's date
today = DateLogic.get_today()  # Returns '2024/0804'

# Get date range
dates = DateLogic.get_date_range('2024/0801', '2024/0805')

# Use calculator for scenarios
calc = DataSyncDateCalculator()
dates = calc.calculate_dates_to_copy('daily')
dates = calc.calculate_dates_to_copy('backdated', custom_date='2024/0721')
```

### datasync_manager.py
**What it does**: Interact with AWS DataSync API
**Key classes**:
- `DataSyncManager`: Low-level API operations
- `DataSyncOrchestrator`: High-level orchestration

**Common operations**:
```python
from datasync_manager import DataSyncOrchestrator
from config import get_config

config = get_config()
orchestrator = DataSyncOrchestrator(config)

# Copy files
results = orchestrator.execute_copy_task(
    datatype='inventory',
    date_str='2024/0804',
    wait_for_completion=True
)

# Batch copy
results = orchestrator.execute_batch_copy(
    dates=['2024/0804', '2024/0805'],
    datatypes=['inventory', 'orders']
)
```

### lambda_function.py
**What it does**: Lambda handler for automated execution
**Key functions**:
- `lambda_handler`: Full-featured handler with scenarios
- `lambda_handler_simple`: Simplified daily-only version

**Local testing**:
```bash
python lambda_function.py daily
python lambda_function.py backdated 2024/0721
python lambda_function.py range 7
```

---

## Common Development Tasks

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test
pytest test_date_logic.py::TestDateLogic::test_today_format -v

# Run with coverage
pytest --cov=date_logic --cov=datasync_manager

# Run and show print statements
pytest -v -s
```

### Testing Locally (Without AWS)

```bash
# Test date logic
python -c "
from date_logic import DateLogic
print('Today:', DateLogic.get_today())
print('Last 7 days:', DateLogic.get_last_n_days(7))
"

# Test configuration
python -c "
from config import get_config
config = get_config()
print('Environment:', config.ENVIRONMENT)
print('Datatypes:', config.get_datatypes())
"

# Test examples
python example_daily_copy.py          # Requires AWS credentials
python example_backdated_copy.py 2024/0721
python example_monitoring.py
```

### Code Quality

```bash
# Format code (install black first)
black *.py

# Check for issues
flake8 *.py

# Check type hints (optional)
mypy *.py
```

### Adding New Scenarios

1. Add method to `DataSyncDateCalculator` in `date_logic.py`
2. Update `calculate_dates_to_copy()` to handle new scenario
3. Add unit test in `test_date_logic.py`
4. Document in README.md

Example:
```python
def calculate_dates_to_copy(self, scenario='daily', ...):
    ...
    elif scenario == 'my_scenario':
        # Your logic here
        return dates
```

---

## Working with AWS

### Prerequisites

```bash
# Install AWS CLI v2
# See: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# Configure AWS credentials
aws configure
# Enter: Access Key, Secret Key, Region, Output format

# Verify credentials
aws sts get-caller-identity
```

### Common AWS Commands for Development

```bash
# List DataSync locations
aws datasync list-locations

# Get specific location details
aws datasync describe-location-nfs \
  --location-arn arn:aws:datasync:region:account:location/nfs/xxxxx

# List existing tasks
aws datasync list-tasks

# Check Lambda function
aws lambda get-function-configuration \
  --function-name datasync-orchestrator

# View Lambda logs
aws logs tail /aws/lambda/datasync-orchestrator --follow

# Test Lambda locally
aws lambda invoke \
  --function-name datasync-orchestrator \
  --payload '{"scenario":"daily"}' \
  response.json
cat response.json | python -m json.tool
```

---

## Understanding Data Flow

```
User/EventBridge
    ↓
Lambda Function (lambda_function.py)
    ↓
DataSyncOrchestrator (datasync_manager.py)
    ├─→ Calculate dates (date_logic.py)
    ├─→ Load config (config.py)
    ├─→ Find or create DataSync task
    ├─→ Start task execution
    ├─→ Monitor completion
    └─→ Send notification (SNS)
    ↓
AWS DataSync Service
    ├─→ NFS Location (NAS mount)
    ├─→ S3 Location (bucket)
    └─→ Task Execution (copy files)
    ↓
S3 Bucket (destination)
```

---

## Configuration Priority

The system loads configuration in this order (highest to lowest priority):

1. **Environment variables** (set in shell or Lambda environment)
   ```bash
   export DATASYNC_NFS_LOCATION_ARN=arn:aws:...
   ```

2. **`.env` file** (local development)
   ```bash
   cp .env.example .env
   # Edit .env
   source .env
   ```

3. **Default values** in `config.py`
   ```python
   DATASYNC_NFS_LOCATION_ARN = os.getenv(
       'DATASYNC_NFS_LOCATION_ARN',
       'arn:aws:datasync:...'  # Default if not set
   )
   ```

**Best practice**: Use environment variables for secrets and configuration.

---

## Debugging Tips

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run with debug output
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from lambda_function import lambda_handler
result = lambda_handler({'scenario': 'daily'}, None)
print(result)
"
```

### Add Print Debugging

```python
# In any module
import logging
logger = logging.getLogger(__name__)

logger.info(f"Debug: {variable}")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### Test Individual Functions

```python
from datasync_manager import DataSyncManager
from config import get_config

config = get_config()
manager = DataSyncManager(config)

# Test finding a task
task_arn = manager.find_task_by_name("my-task-name")
print(f"Found task: {task_arn}")

# Test listing tasks
tasks = manager.list_tasks()
print(f"Total tasks: {len(tasks)}")
```

---

## Common Issues for New Developers

### Issue 1: "ModuleNotFoundError: No module named 'boto3'"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify
python -c "import boto3; print('✓ boto3 installed')"
```

### Issue 2: "Failed to import local modules"

**Solution:** Make sure you're running from the project root:
```bash
cd /Users/paramraghavan/dev/123ofaws/datasync
python lambda_function.py daily
```

### Issue 3: "AWS credentials not found"

**Solution:**
```bash
# Configure AWS credentials
aws configure

# Verify
aws sts get-caller-identity

# For local testing only (not production!)
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### Issue 4: "Invalid configuration - missing required values"

**Solution:**
```bash
# Check configuration
python -c "
from config import get_config
config = get_config()
print('NAS_BASE_PATH:', config.NAS_BASE_PATH)
print('S3_BUCKET:', config.S3_BUCKET)
print('DATATYPES:', config.get_datatypes())
"

# Fill in .env file
cp .env.example .env
nano .env
```

---

## Next Steps

After setting up locally:

1. **Read the README** for project overview
2. **Review datasync_overview.md** to understand architecture
3. **Run the examples** to see code in action
4. **Run tests** to verify everything works
5. **Read setup_guide.md** when ready to set up AWS
6. **Follow deployment_guide.md** when ready to deploy

---

## Getting Help

1. **Check troubleshooting.md** for known issues
2. **Review example files** for usage patterns
3. **Read docstrings** in the code:
   ```python
   from datasync_manager import DataSyncOrchestrator
   help(DataSyncOrchestrator.execute_copy_task)
   ```
4. **Check AWS DataSync docs**: https://docs.aws.amazon.com/datasync/

---

## Contributing

When making changes:

1. Write tests first (test-driven development)
2. Run full test suite: `pytest -v`
3. Format code: `black *.py`
4. Update docstrings and comments
5. Update documentation if behavior changes
6. Create a pull request with clear description

---

## Development Workflow Example

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Load configuration
cp .env.example .env
nano .env  # Fill in your values

# 3. Run tests to verify setup
pytest -v

# 4. Test a specific scenario
python example_daily_copy.py

# 5. Make changes to code
nano date_logic.py

# 6. Add tests for new functionality
nano test_date_logic.py

# 7. Run tests again
pytest -v

# 8. Format code
black *.py

# 9. Commit changes
git add .
git commit -m "Add new feature"
```

---

## File Permissions

For production security:

```bash
# Make scripts executable
chmod +x lambda_function.py example_*.py

# Restrict config files (if they contain secrets)
chmod 600 .env

# Allow others to read documentation
chmod 644 *.md *.txt
```

---

Good luck! If you have questions, check the [documentation index](README.md#documentation) or the [troubleshooting guide](troubleshooting.md).

