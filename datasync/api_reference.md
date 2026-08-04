# API Reference - Module Documentation

Complete API documentation for all modules in the DataSync Orchestrator.

---

## Table of Contents

1. [config.py](#configpy) - Configuration management
2. [date_logic.py](#date_logicpy) - Date utilities
3. [datasync_manager.py](#datasync_managerpy) - AWS DataSync integration
4. [lambda_function.py](#lambda_functionpy) - Lambda handler

---

## config.py

Configuration management module. Loads settings from environment variables with sensible defaults.

### Classes

#### `Config`

Base configuration class with all settings.

**Properties:**
```python
# AWS DataSync
DATASYNC_NFS_LOCATION_ARN: str
DATASYNC_S3_LOCATION_ARN: str

# Paths
NAS_BASE_PATH: str
S3_BUCKET: str
S3_PREFIX: str
DATATYPES: List[str]

# AWS
ENVIRONMENT: str  # 'dev', 'staging', 'prod', 'local'
AWS_REGION: str
SNS_TOPIC_ARN: str

# Timeouts
TASK_TIMEOUT_SECONDS: int
MAX_RETRIES: int
RETRY_WAIT_SECONDS: int

# Logging
LOG_LEVEL: str  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'

# Features
ENABLE_PARALLEL_TASKS: bool
TASK_NAME_PREFIX: str

# DataSync Options
DATASYNC_OPTIONS: Dict[str, Any]
```

**Methods:**

```python
@classmethod
def get_datatypes() -> List[str]:
    """Get list of data types to copy.

    Returns:
        List of datatype strings, e.g., ['datatype1', 'datatype2']
    """

@classmethod
def get_task_name(datatype: str, date_str: str) -> str:
    """Generate DataSync task name.

    Args:
        datatype: Data type (e.g., 'inventory')
        date_str: Date in YYYY/MMDD format (e.g., '2024/0804')

    Returns:
        Task name string
        Example: 'datasync-nas-to-s3-prod-inventory-2024/0804'
    """

@classmethod
def get_nas_source_path(datatype: str, date_str: str) -> str:
    """Generate NAS source path.

    Args:
        datatype: Data type
        date_str: Date in YYYY/MMDD format

    Returns:
        Full NAS path
        Example: '/mydata/prod/icm/datain/poolData/inventory/2024/0804'
    """

@classmethod
def get_s3_destination_path(datatype: str, date_str: str) -> str:
    """Generate S3 destination path.

    Args:
        datatype: Data type
        date_str: Date in YYYY/MMDD format

    Returns:
        S3 prefix path
        Example: '/poolData/inventory/2024/0804'
    """
```

#### `LocalConfig`, `DevConfig`, `ProdConfig`

Environment-specific configurations that inherit from `Config`.

```python
class LocalConfig(Config):
    """For local/testing environment"""
    TASK_TIMEOUT_SECONDS = 300
    MAX_RETRIES = 2

class DevConfig(Config):
    """For development environment"""
    ENVIRONMENT = 'dev'
    LOG_LEVEL = 'DEBUG'

class ProdConfig(Config):
    """For production environment"""
    ENVIRONMENT = 'prod'
    LOG_LEVEL = 'INFO'
```

### Functions

```python
def get_config(env: str = None) -> Config:
    """Get configuration for specified environment.

    Args:
        env: Environment name ('local', 'dev', 'prod')
             If None, uses ENVIRONMENT variable (default: 'prod')

    Returns:
        Configuration object for the environment

    Example:
        config = get_config('prod')
        print(config.NAS_BASE_PATH)
    """
```

### Usage Examples

```python
from config import get_config

# Get configuration
config = get_config()

# Access values
nfs_arn = config.DATASYNC_NFS_LOCATION_ARN
datatypes = config.get_datatypes()

# Generate paths
nas_path = config.get_nas_source_path('inventory', '2024/0804')
s3_path = config.get_s3_destination_path('inventory', '2024/0804')

# Get task name
task_name = config.get_task_name('inventory', '2024/0804')
```

---

## date_logic.py

Date calculation utilities for determining which dates to copy.

### Classes

#### `DateLogic`

Static utility class for date operations.

**Static Methods:**

```python
@staticmethod
def get_today() -> str:
    """Get today's date in NAS format (YYYY/MMDD).

    Returns:
        Date string, e.g., '2024/0804'
    """

@staticmethod
def get_date(year: int, month: int, day: int) -> str:
    """Get specific date in NAS format.

    Args:
        year: Year (e.g., 2024)
        month: Month 1-12 (e.g., 8)
        day: Day 1-31 (e.g., 4)

    Returns:
        Date string in format YYYY/MMDD

    Raises:
        ValueError: If date is invalid

    Example:
        date = DateLogic.get_date(2024, 8, 4)  # Returns '2024/0804'
    """

@staticmethod
def get_yesterdays_date() -> str:
    """Get yesterday's date in NAS format.

    Returns:
        Date string, e.g., '2024/0803'
    """

@staticmethod
def get_date_range(start_date: str, end_date: str) -> List[str]:
    """Get all dates between start and end (inclusive).

    Args:
        start_date: Start date in YYYY/MMDD format
        end_date: End date in YYYY/MMDD format

    Returns:
        List of date strings

    Example:
        dates = DateLogic.get_date_range('2024/0801', '2024/0805')
        # Returns: ['2024/0801', '2024/0802', '2024/0803', '2024/0804', '2024/0805']
    """

@staticmethod
def get_last_n_days(n: int) -> List[str]:
    """Get last N days including today.

    Args:
        n: Number of days (e.g., 7 for last week)

    Returns:
        List of dates, most recent first

    Example:
        dates = DateLogic.get_last_n_days(3)
        # Returns: ['2024/0804', '2024/0803', '2024/0802']
    """

@staticmethod
def is_valid_nas_date_format(date_str: str) -> bool:
    """Check if date is in valid NAS format (YYYY/MMDD).

    Args:
        date_str: Date string to validate

    Returns:
        True if valid format, False otherwise

    Example:
        is_valid_nas_date_format('2024/0804')  # True
        is_valid_nas_date_format('2024-08-04')  # False
    """

@staticmethod
def get_last_business_day() -> str:
    """Get last business day (excludes weekends).

    Returns:
        Date string in YYYY/MMDD format
    """

@staticmethod
def get_last_month_end() -> str:
    """Get last day of previous month.

    Returns:
        Date string in YYYY/MMDD format

    Example:
        # If today is 2024-08-15
        date = DateLogic.get_last_month_end()  # Returns '2024/0731'
    """

@staticmethod
def parse_nas_date(date_str: str) -> datetime:
    """Parse NAS date format to datetime object.

    Args:
        date_str: Date in YYYY/MMDD format

    Returns:
        datetime.datetime object

    Example:
        dt = DateLogic.parse_nas_date('2024/0804')
        print(dt.year, dt.month, dt.day)  # 2024, 8, 4
    """
```

#### `DataSyncDateCalculator`

High-level calculator for determining dates based on scenarios.

**Methods:**

```python
def calculate_dates_to_copy(
    scenario: str = 'daily',
    custom_date: Optional[str] = None,
    days_back: int = 0
) -> List[str]:
    """Calculate which dates to copy based on scenario.

    Args:
        scenario: One of:
            - 'daily': Copy today's data (default)
            - 'backdated': Copy specific date
            - 'range': Copy last N days
            - 'weekly': Copy last 7 days
            - 'monthly': Copy previous month's data
            - 'custom': Copy custom date

        custom_date: Required for 'backdated' and 'custom' scenarios
                    Format: YYYY/MMDD (e.g., '2024/0804')

        days_back: Required for 'range' scenario
                  Number of days to include (e.g., 7)

    Returns:
        List of dates to copy in YYYY/MMDD format

    Raises:
        ValueError: If parameters invalid for scenario

    Examples:
        # Daily
        dates = calc.calculate_dates_to_copy('daily')
        # Returns: ['2024/0804']

        # Backdated
        dates = calc.calculate_dates_to_copy('backdated', custom_date='2024/0721')
        # Returns: ['2024/0721']

        # Range
        dates = calc.calculate_dates_to_copy('range', days_back=7)
        # Returns: ['2024/0804', '2024/0803', ..., '2024/0729']
    """

def get_summary(dates: List[str]) -> str:
    """Get human-readable summary of dates.

    Args:
        dates: List of dates in YYYY/MMDD format

    Returns:
        Summary string

    Examples:
        summary = calc.get_summary(['2024/0804'])
        # Returns: 'Copying 1 date: 2024/0804'

        summary = calc.get_summary(['2024/0801', '2024/0802', '2024/0803'])
        # Returns: 'Copying 3 dates: 2024/0801 to 2024/0803'
    """
```

### Usage Examples

```python
from date_logic import DateLogic, DataSyncDateCalculator

# Direct date operations
today = DateLogic.get_today()
yesterday = DateLogic.get_yesterdays_date()
last_7_days = DateLogic.get_last_n_days(7)
date_range = DateLogic.get_date_range('2024/0801', '2024/0805')

# Using calculator for scenarios
calculator = DataSyncDateCalculator()

# Daily scenario
dates = calculator.calculate_dates_to_copy('daily')
print(calculator.get_summary(dates))
# Output: Copying 1 date: 2024/0804

# Backdated scenario
dates = calculator.calculate_dates_to_copy('backdated', custom_date='2024/0721')

# Range scenario
dates = calculator.calculate_dates_to_copy('range', days_back=7)
```

---

## datasync_manager.py

AWS DataSync API integration and orchestration.

### Classes

#### `DataSyncManager`

Low-level DataSync API operations.

**Constructor:**
```python
def __init__(self, config: Config):
    """Initialize DataSync manager.

    Args:
        config: Configuration object
    """
```

**Methods:**

```python
def create_task(
    task_name: str,
    source_path: str,
    destination_path: str,
    verify: bool = True
) -> str:
    """Create a DataSync task.

    Args:
        task_name: Name for the task
        source_path: NAS path (e.g., '/mydata/.../datatype/2024/0804')
        destination_path: S3 prefix (e.g., '/poolData/datatype/2024/0804')
        verify: Whether to verify data after copy

    Returns:
        Task ARN string

    Raises:
        ClientError: If task creation fails
    """

def start_task_execution(task_arn: str) -> str:
    """Start task execution.

    Args:
        task_arn: ARN of task to execute

    Returns:
        Task execution ARN

    Raises:
        ClientError: If execution fails to start
    """

def wait_for_task_completion(
    task_execution_arn: str,
    timeout_seconds: int = 3600,
    check_interval: int = 10
) -> Dict[str, Any]:
    """Wait for task execution to complete.

    Args:
        task_execution_arn: ARN of execution to monitor
        timeout_seconds: Max time to wait (default: 1 hour)
        check_interval: Seconds between status checks (default: 10)

    Returns:
        Dict with execution details:
            - Status: 'SUCCESS' or 'FAILED'
            - BytesCopied: Number of bytes transferred
            - FilesTransferred: Number of files copied
            - etc.

    Raises:
        TimeoutError: If execution doesn't complete in time
        Exception: If execution fails
    """

def get_task_execution_details(task_execution_arn: str) -> Dict[str, Any]:
    """Get detailed execution information.

    Args:
        task_execution_arn: ARN of execution

    Returns:
        Dict with detailed execution info
    """

def find_task_by_name(task_name: str) -> Optional[str]:
    """Find task ARN by name.

    Args:
        task_name: Name to search for

    Returns:
        Task ARN if found, None otherwise
    """

def send_notification(
    subject: str,
    message: str,
    message_type: str = 'INFO'
) -> None:
    """Send SNS notification.

    Args:
        subject: Notification subject
        message: Notification message
        message_type: 'INFO', 'SUCCESS', 'WARNING', 'ERROR'
    """
```

#### `DataSyncOrchestrator`

High-level orchestration combining date logic and DataSync.

**Constructor:**
```python
def __init__(self, config: Config):
    """Initialize orchestrator.

    Args:
        config: Configuration object
    """
```

**Methods:**

```python
def execute_copy_task(
    datatype: str,
    date_str: str,
    wait_for_completion: bool = True
) -> Dict[str, Any]:
    """Execute complete copy task for datatype and date.

    Args:
        datatype: Data type (e.g., 'inventory')
        date_str: Date in YYYY/MMDD format
        wait_for_completion: Whether to wait for completion

    Returns:
        Dict with:
            - task_arn: ARN of task
            - execution_arn: ARN of execution
            - status: 'STARTED', 'SUCCESS', or 'FAILED'
            - datatype: The datatype copied
            - date: The date copied
            - details: (if completed) Execution details
            - error: (if failed) Error message

    Raises:
        Exception: On execution failure
    """

def execute_batch_copy(
    dates: List[str],
    datatypes: Optional[List[str]] = None,
    wait_for_completion: bool = True,
    parallel: bool = False
) -> List[Dict[str, Any]]:
    """Execute copy tasks for multiple dates and datatypes.

    Args:
        dates: List of dates in YYYY/MMDD format
        datatypes: List of datatypes (uses config default if None)
        wait_for_completion: Whether to wait for all tasks
        parallel: Whether to run in parallel (future feature)

    Returns:
        List of result dicts for each task

    Example:
        results = orchestrator.execute_batch_copy(
            dates=['2024/0804', '2024/0805'],
            datatypes=['inventory', 'orders']
        )

        for result in results:
            print(f"{result['datatype']}/{result['date']}: {result['status']}")
    """
```

### Usage Examples

```python
from datasync_manager import DataSyncOrchestrator
from config import get_config

config = get_config()
orchestrator = DataSyncOrchestrator(config)

# Execute single copy task
result = orchestrator.execute_copy_task(
    datatype='inventory',
    date_str='2024/0804',
    wait_for_completion=True
)
print(result['status'])  # 'SUCCESS'
print(result['details']['FilesTransferred'])  # Number of files

# Batch copy
results = orchestrator.execute_batch_copy(
    dates=['2024/0804', '2024/0805'],
    datatypes=['inventory', 'orders'],
    wait_for_completion=True
)

# Process results
successful = sum(1 for r in results if r['status'] == 'SUCCESS')
print(f"Completed: {successful}/{len(results)}")
```

---

## lambda_function.py

AWS Lambda entry point for scheduled and manual execution.

### Functions

#### `lambda_handler`

Main handler for Lambda with full scenario support.

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for DataSync orchestration.

    Args:
        event: Lambda event dict with:
            - scenario: 'daily', 'backdated', 'range', 'weekly', 'monthly', 'custom'
            - custom_date: Required for 'backdated'/'custom' (YYYY/MMDD format)
            - days_back: Required for 'range' (integer)
            - datatypes: Optional list of datatypes (uses config default if not provided)
            - wait_for_completion: Boolean, default True

        context: Lambda context (not used but required by AWS)

    Returns:
        Dict with:
            - statusCode: 200 (success) or 206 (partial) or 500 (failure)
            - body: Dict with results

    Examples:
        # Daily copy
        event = {"scenario": "daily"}
        response = lambda_handler(event, None)

        # Backdated copy
        event = {"scenario": "backdated", "custom_date": "2024/0721"}
        response = lambda_handler(event, None)

        # Range copy
        event = {"scenario": "range", "days_back": 7}
        response = lambda_handler(event, None)
    """
```

#### `lambda_handler_simple`

Simplified handler for daily-only execution.

```python
def lambda_handler_simple(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Simplified handler - copies today's files only.

    Use this if you only need daily automated copying.

    Args:
        event: Lambda event (not used, can be empty dict)
        context: Lambda context (not used)

    Returns:
        Dict with statusCode and results
    """
```

### CLI Testing

When run directly (not via Lambda), supports command-line arguments:

```bash
python lambda_function.py daily
python lambda_function.py backdated 2024/0721
python lambda_function.py range 7
python lambda_function.py weekly
python lambda_function.py monthly
```

### Event Examples

```python
# Daily scenario
{
    "scenario": "daily"
}

# Backdated scenario
{
    "scenario": "backdated",
    "custom_date": "2024/0721"
}

# Range scenario
{
    "scenario": "range",
    "days_back": 7
}

# Custom datatypes
{
    "scenario": "daily",
    "datatypes": ["inventory", "orders"]
}

# Don't wait for completion (async)
{
    "scenario": "daily",
    "wait_for_completion": false
}

# Complete example
{
    "scenario": "backdated",
    "custom_date": "2024/0721",
    "datatypes": ["inventory"],
    "wait_for_completion": true
}
```

### Response Examples

**Success:**
```json
{
    "statusCode": 200,
    "body": {
        "message": "DataSync orchestration completed",
        "scenario": "daily",
        "dates_copied": ["2024/0804"],
        "total_tasks": 3,
        "successful": 3,
        "failed": 0,
        "results": [
            {
                "task_arn": "arn:aws:datasync:...",
                "execution_arn": "arn:aws:datasync:...",
                "status": "SUCCESS",
                "datatype": "inventory",
                "date": "2024/0804",
                "details": {
                    "FilesTransferred": 150,
                    "BytesCopied": 1073741824
                }
            },
            ...
        ]
    }
}
```

**Partial Failure:**
```json
{
    "statusCode": 206,
    "body": {
        "message": "DataSync orchestration completed",
        "total_tasks": 3,
        "successful": 2,
        "failed": 1,
        "results": [
            {"status": "SUCCESS", ...},
            {"status": "SUCCESS", ...},
            {"status": "FAILED", "error": "..."}
        ]
    }
}
```

**Error:**
```json
{
    "statusCode": 500,
    "body": {
        "error": "Error message details",
        "message": "DataSync orchestration failed"
    }
}
```

---

## Integration Examples

### Complete Daily Copy Workflow

```python
from config import get_config
from date_logic import DataSyncDateCalculator
from datasync_manager import DataSyncOrchestrator

# 1. Load configuration
config = get_config()

# 2. Calculate dates to copy
calculator = DataSyncDateCalculator()
dates = calculator.calculate_dates_to_copy('daily')
print(calculator.get_summary(dates))

# 3. Execute copy
orchestrator = DataSyncOrchestrator(config)
results = orchestrator.execute_batch_copy(
    dates=dates,
    wait_for_completion=True
)

# 4. Report results
for result in results:
    if result['status'] == 'SUCCESS':
        print(f"✓ {result['datatype']}: {result['details']['FilesTransferred']} files")
    else:
        print(f"✗ {result['datatype']}: {result.get('error', 'Unknown error')}")
```

### Backdated Retry Workflow

```python
# Retry failed copies for specific dates
calculator = DataSyncDateCalculator()
dates = calculator.calculate_dates_to_copy('range', days_back=3)

orchestrator = DataSyncOrchestrator(config)
results = orchestrator.execute_batch_copy(dates)

# Show what was retried
for result in results:
    status = "✓" if result['status'] == 'SUCCESS' else "✗"
    print(f"{status} {result['datatype']}/{result['date']}")
```

---

## Testing

All modules are testable. See `test_date_logic.py` for examples:

```bash
pytest -v test_date_logic.py
```

For integration testing with AWS, see [developer_guide.md](developer_guide.md#testing-locally-without-aws).

---

## Error Handling

All modules provide comprehensive error handling:

```python
try:
    result = orchestrator.execute_copy_task(
        datatype='inventory',
        date_str='2024/0804'
    )
except Exception as e:
    logger.error(f"Failed: {str(e)}", exc_info=True)
    # Error notification sent via SNS automatically
```

---

## Related Documentation

- [README.md](README.md) - Project overview
- [developer_guide.md](developer_guide.md) - Getting started
- [deployment_guide.md](deployment_guide.md) - Production deployment
- [troubleshooting.md](troubleshooting.md) - Common issues

