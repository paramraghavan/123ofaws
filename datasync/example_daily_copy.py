"""
Example 1: Daily Copy of Today's Files
Simple use case for daily scheduled execution
"""

from datasync_manager import DataSyncOrchestrator
from date_logic import DateLogic
from config import get_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def copy_todays_files():
    """
    Copy all files from today for configured datatypes to S3

    This is the simplest use case - run once daily via EventBridge
    """
    config = get_config()
    orchestrator = DataSyncOrchestrator(config)

    # Get today's date in NAS format (YYYY/MMDD)
    today = DateLogic.get_today()
    logger.info(f"Starting daily copy for: {today}")

    # Execute copy for all configured datatypes
    results = orchestrator.execute_batch_copy(
        dates=[today],
        wait_for_completion=True
    )

    # Print results
    print(f"\n{'='*60}")
    print(f"Daily Copy Results for {today}")
    print(f"{'='*60}\n")

    for result in results:
        datatype = result.get('datatype', 'N/A')
        status = result.get('status', 'N/A')
        date = result.get('date', 'N/A')

        if status == 'SUCCESS':
            details = result.get('details', {})
            files = details.get('FilesTransferred', 0)
            bytes_copied = details.get('BytesCopied', 0)
            print(f"✓ {datatype}/{date}")
            print(f"  Status: {status}")
            print(f"  Files: {files}")
            print(f"  Bytes: {bytes_copied:,}")
        else:
            print(f"✗ {datatype}/{date}")
            print(f"  Status: {status}")
            if 'error' in result:
                print(f"  Error: {result['error']}")

        print()

    # Summary
    successful = sum(1 for r in results if r.get('status') == 'SUCCESS')
    total = len(results)
    print(f"Summary: {successful}/{total} tasks completed successfully")

    return results


if __name__ == '__main__':
    copy_todays_files()
