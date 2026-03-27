"""
AWS Lambda Handler - Process records via AWS Lambda.

This handler demonstrates how to:
1. Receive parameters from Lambda event JSON
2. Call the same shared business logic as CLI
3. Return properly formatted Lambda response

Expected event format:
{
    "operation": "transform",
    "records": [...],
    "format": "json",
    "dry_run": false
}

Returns:
{
    "statusCode": 200,
    "body": {
        "success": true,
        "operation": "transform",
        ...
    }
}
"""

import json
import logging
from typing import Dict, Any

# Import shared library (will be in Lambda layer)
from shared_lib.processor import process_records, parse_records_from_json
from shared_lib.logger import get_logger

logger = get_logger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: Lambda event containing operation, records, format, dry_run
        context: Lambda context object (function name, request ID, etc.)

    Returns:
        Lambda response with statusCode and body
    """

    logger.info(f"Handler invoked with event: {json.dumps(event)}")
    logger.info(f"Request ID: {context.invoked_function_arn}")

    try:
        # Extract parameters from event
        operation = event.get('operation')
        records_input = event.get('records')
        format_type = event.get('format', 'json')
        dry_run = event.get('dry_run', False)

        # Validate required parameters
        if not operation:
            return _error_response(
                400,
                "Missing required parameter: operation"
            )

        if records_input is None:
            return _error_response(
                400,
                "Missing required parameter: records"
            )

        # Parse records
        logger.info(f"Parsing records (type: {type(records_input).__name__})")

        # Handle both direct list and JSON string
        if isinstance(records_input, str):
            records = parse_records_from_json(records_input)
        elif isinstance(records_input, list):
            records = records_input
        elif isinstance(records_input, dict) and 'records' in records_input:
            records = records_input['records']
        else:
            return _error_response(
                400,
                "Records must be a list, JSON string, or dict with 'records' key"
            )

        logger.info(f"Parsed {len(records)} records")

        # Validate operation
        valid_operations = ['transform', 'validate', 'aggregate']
        if operation not in valid_operations:
            return _error_response(
                400,
                f"Invalid operation: {operation}. Must be one of: {valid_operations}"
            )

        # Call shared business logic
        logger.info(f"Processing with operation: {operation}")
        result = process_records(
            records=records,
            operation=operation,
            format_type=format_type,
            dry_run=dry_run
        )

        # Return success response
        return {
            'statusCode': 200,
            'body': result
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return _error_response(400, f"Invalid JSON: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return _error_response(500, f"Internal error: {str(e)}")


def _error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Helper to return formatted error response."""
    return {
        'statusCode': status_code,
        'body': {
            'success': False,
            'error': message
        }
    }


# For local testing
if __name__ == '__main__':
    # Test context object
    class TestContext:
        invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

    # Test event
    test_event = {
        "operation": "transform",
        "records": [
            {"Name": "Alice", "Email": "alice@example.com", "Category": "A"},
            {"Name": "Bob", "Email": "bob@example.com", "Category": "B"}
        ],
        "format": "json"
    }

    context = TestContext()
    response = handler(test_event, context)
    print(json.dumps(response, indent=2))
