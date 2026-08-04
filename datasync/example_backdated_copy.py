"""
Example 2: Backdated Copy
Copy files from a specific past date
Useful when initial job run was missed or historical data needs syncing
"""

from datasync_manager import DataSyncOrchestrator
from date_logic import DateLogic, DataSyncDateCalculator
from config import get_config
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def copy_backdated_date(date_str: str, datatypes: list = None):
    """
    Copy files from a specific past date

    Args:
        date_str: Date in YYYY/MMDD format (e.g., '2024/0721')
        datatypes: List of datatypes to copy (uses config default if None)

    Example:
        copy_backdated_date('2024/0721')
        copy_backdated_date('2024/0721', datatypes=['inventory', 'orders'])
    """
    config = get_config()
    orchestrator = DataSyncOrchestrator(config)

    # Validate date format
    if not DateLogic.is_valid_nas_date_format(date_str):
        print(f"Error: Invalid date format '{date_str}'")
        print("Expected format: YYYY/MMDD (e.g., 2024/0721)")
        return None

    logger.info(f"Starting backdated copy for: {date_str}")

    # Execute copy
    results = orchestrator.execute_batch_copy(
        dates=[date_str],
        datatypes=datatypes,
        wait_for_completion=True
    )

    # Print results
    print(f"\n{'='*60}")
    print(f"Backdated Copy Results - {date_str}")
    print(f"{'='*60}\n")

    for result in results:
        datatype = result.get('datatype', 'N/A')
        status = result.get('status', 'N/A')

        if status == 'SUCCESS':
            details = result.get('details', {})
            files = details.get('FilesTransferred', 0)
            bytes_copied = details.get('BytesCopied', 0)
            print(f"✓ {datatype}")
            print(f"  Files transferred: {files}")
            print(f"  Bytes copied: {bytes_copied:,}")
        else:
            print(f"✗ {datatype}")
            print(f"  Status: {status}")
            if 'error' in result:
                print(f"  Error: {result['error']}")

        print()

    return results


def copy_date_range(start_date: str, end_date: str):
    """
    Copy files from a range of dates

    Args:
        start_date: Start date in YYYY/MMDD format
        end_date: End date in YYYY/MMDD format

    Example:
        copy_date_range('2024/0701', '2024/0705')
    """
    # Validate dates
    if not DateLogic.is_valid_nas_date_format(start_date):
        print(f"Error: Invalid start date format '{start_date}'")
        return None

    if not DateLogic.is_valid_nas_date_format(end_date):
        print(f"Error: Invalid end date format '{end_date}'")
        return None

    # Get date range
    dates = DateLogic.get_date_range(start_date, end_date)
    logger.info(f"Copying {len(dates)} dates from {start_date} to {end_date}")

    # Copy all dates
    config = get_config()
    orchestrator = DataSyncOrchestrator(config)

    results = orchestrator.execute_batch_copy(
        dates=dates,
        wait_for_completion=True
    )

    # Summary
    print(f"\n{'='*60}")
    print(f"Date Range Copy Results - {start_date} to {end_date}")
    print(f"{'='*60}\n")

    successful = sum(1 for r in results if r.get('status') == 'SUCCESS')
    failed = sum(1 for r in results if r.get('status') == 'FAILED')

    print(f"Total tasks: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()

    return results


def copy_missing_dates():
    """
    Identify and copy missing dates for today (for retry scenarios)

    This function checks which dates failed and retries them
    """
    config = get_config()
    calculator = DataSyncDateCalculator()

    # Get dates that commonly need retry (last 3 days)
    dates = DateLogic.get_last_n_days(3)
    logger.info(f"Retrying copy for last 3 days: {dates}")

    orchestrator = DataSyncOrchestrator(config)
    results = orchestrator.execute_batch_copy(
        dates=dates,
        wait_for_completion=True
    )

    failed_tasks = [r for r in results if r.get('status') == 'FAILED']

    print(f"\n{'='*60}")
    print(f"Retry Results for Last 3 Days")
    print(f"{'='*60}\n")

    if not failed_tasks:
        print("✓ All tasks completed successfully!")
    else:
        print(f"✗ {len(failed_tasks)} tasks failed:")
        for task in failed_tasks:
            print(f"  - {task['datatype']}/{task['date']}: {task.get('error', 'Unknown error')}")

    print()
    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python example_backdated_copy.py <date>")
        print("  python example_backdated_copy.py <start_date> <end_date>")
        print()
        print("Examples:")
        print("  python example_backdated_copy.py 2024/0721")
        print("  python example_backdated_copy.py 2024/0701 2024/0705")
        print()
        sys.exit(1)

    if len(sys.argv) == 2:
        # Single date
        date = sys.argv[1]
        copy_backdated_date(date)
    elif len(sys.argv) == 3:
        # Date range
        start = sys.argv[1]
        end = sys.argv[2]
        copy_date_range(start, end)
