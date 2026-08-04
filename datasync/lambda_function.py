"""
AWS Lambda handler for DataSync orchestration
Triggered daily by CloudWatch Events or EventBridge
"""

import json
import logging
import sys
from typing import Dict, Any, Optional, List

from config import get_config
from date_logic import DataSyncDateCalculator, DateLogic
from datasync_manager import DataSyncOrchestrator

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for DataSync orchestration

    Expected event format:
    {
        "scenario": "daily",  # Options: daily, backdated, range, weekly, monthly, custom
        "custom_date": "2024/0804",  # Required for backdated/custom scenarios
        "days_back": 7,  # Required for range scenario
        "datatypes": ["datatype1", "datatype2"],  # Optional, uses config default if not provided
        "wait_for_completion": true  # Whether to wait for tasks to complete
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "message": "...",
            "dates_copied": ["2024/0804"],
            "results": [...]
        }
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Parse configuration
        config = get_config()
        logger.info(f"Environment: {config.ENVIRONMENT}")

        # Parse event parameters
        scenario = event.get('scenario', 'daily')
        custom_date = event.get('custom_date')
        days_back = event.get('days_back', 1)
        datatypes = event.get('datatypes')
        wait_for_completion = event.get('wait_for_completion', True)

        logger.info(f"Scenario: {scenario}")
        logger.info(f"Days back: {days_back}")

        # Calculate dates to copy
        calculator = DataSyncDateCalculator()
        dates_to_copy = calculator.calculate_dates_to_copy(
            scenario=scenario,
            custom_date=custom_date,
            days_back=days_back
        )

        logger.info(f"Dates to copy: {dates_to_copy}")
        logger.info(calculator.get_summary(dates_to_copy))

        # Initialize orchestrator
        orchestrator = DataSyncOrchestrator(config)

        # Execute batch copy
        results = orchestrator.execute_batch_copy(
            dates=dates_to_copy,
            datatypes=datatypes,
            wait_for_completion=wait_for_completion
        )

        # Summary
        successful = sum(1 for r in results if r.get('status') in ['SUCCESS', 'STARTED'])
        failed = sum(1 for r in results if r.get('status') == 'FAILED')

        summary = {
            "message": f"DataSync orchestration completed",
            "scenario": scenario,
            "dates_copied": dates_to_copy,
            "total_tasks": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }

        logger.info(f"Summary: {json.dumps(summary)}")

        return {
            "statusCode": 200 if failed == 0 else 206,
            "body": summary
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)

        error_response = {
            "statusCode": 500,
            "body": {
                "error": str(e),
                "message": "DataSync orchestration failed"
            }
        }

        return error_response


def lambda_handler_simple(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simplified handler that just copies today's date
    Use this if you don't need complex scenarios
    """
    try:
        logger.info("Starting daily DataSync copy")

        config = get_config()
        orchestrator = DataSyncOrchestrator(config)

        # Copy today's files
        today = DateLogic.get_today()
        logger.info(f"Copying files for: {today}")

        results = orchestrator.execute_batch_copy(
            dates=[today],
            wait_for_completion=True
        )

        successful = sum(1 for r in results if r.get('status') == 'SUCCESS')

        return {
            "statusCode": 200,
            "body": {
                "message": f"Successfully copied files for {today}",
                "date": today,
                "tasks_completed": successful,
                "results": results
            }
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": {"error": str(e)}
        }


# CLI/Testing helper
if __name__ == '__main__':
    """
    For local testing:
    python lambda_function.py daily
    python lambda_function.py backdated 2024/0721
    python lambda_function.py range 7
    """

    # Setup console logging for local testing
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if len(sys.argv) < 2:
        print("Usage: python lambda_function.py [scenario] [args]")
        print("  daily                    - Copy today's files")
        print("  backdated <date>        - Copy specific date (YYYY/MMDD)")
        print("  range <days>            - Copy last N days")
        print("  weekly                  - Copy last 7 days")
        sys.exit(1)

    scenario = sys.argv[1]
    event = {"scenario": scenario}

    if scenario == 'backdated' and len(sys.argv) > 2:
        event["custom_date"] = sys.argv[2]
    elif scenario == 'range' and len(sys.argv) > 2:
        event["days_back"] = int(sys.argv[2])

    result = lambda_handler(event, None)
    print(json.dumps(result, indent=2))
