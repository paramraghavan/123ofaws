"""
AWS Lambda Handler - Process records via AWS Lambda.

This shows how to:
1. Receive parameters from Lambda event JSON
2. Call the same shared business logic as CLI
3. Return properly formatted Lambda response

Expected event:
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
        ...
    }
}
"""

import json
from shared_lib.processor import process_records, parse_records_from_json


def handler(event: dict, context) -> dict:
    """
    AWS Lambda handler function.

    Args:
        event: Dictionary with operation, records, format, dry_run
        context: Lambda context (function name, request ID, etc.)

    Returns:
        Dict with statusCode and body
    """

    print(f"Event received: {json.dumps(event)}")

    try:
        # Extract parameters from event dict
        operation = event.get('operation')
        records_input = event.get('records')
        format_type = event.get('format', 'json')
        dry_run = event.get('dry_run', False)

        # Validate required parameters
        if not operation:
            return {
                'statusCode': 400,
                'body': {'success': False, 'error': 'Missing: operation'}
            }

        if records_input is None:
            return {
                'statusCode': 400,
                'body': {'success': False, 'error': 'Missing: records'}
            }

        # Parse records (handle both JSON strings and lists)
        if isinstance(records_input, str):
            records = parse_records_from_json(records_input)
        elif isinstance(records_input, list):
            records = records_input
        else:
            return {
                'statusCode': 400,
                'body': {'success': False, 'error': 'records must be a list or JSON string'}
            }

        # Call shared business logic
        result = process_records(
            records=records,
            operation=operation,
            format_type=format_type,
            dry_run=dry_run
        )

        # Return successful response
        return {
            'statusCode': 200,
            'body': result
        }

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return {
            'statusCode': 400,
            'body': {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': {'success': False, 'error': f'Internal error: {str(e)}'}
        }


# For local testing without AWS
if __name__ == '__main__':
    class TestContext:
        invoked_function_arn = 'arn:aws:lambda:test'

    test_event = {
        "operation": "transform",
        "records": [
            {"Name": "Alice", "Email": "alice@test.com"},
            {"Name": "Bob", "Email": "bob@test.com"}
        ]
    }

    response = handler(test_event, TestContext())
    print("\nResponse:")
    print(json.dumps(response, indent=2))
