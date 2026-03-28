#!/usr/bin/env python3
"""
CLI Application - Command-line interface for record processing.

Simple example showing how to:
1. Parse command-line arguments
2. Call shared business logic
3. Output results as JSON

Usage:
    python cli_app.py --operation transform --records '[{"Name":"Alice"}]'
    python cli_app.py --operation validate --records '[{"id":1,"name":"Bob","email":"bob@test.com"}]'
    python cli_app.py --operation aggregate --records '[{"category":"A","id":1}]'
"""

import argparse
import json
import sys
from shared_lib.processor import process_records, parse_records_from_json


def main():
    """Parse CLI arguments and process records."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Process records with different operations'
    )
    parser.add_argument(
        '--operation',
        required=True,
        choices=['transform', 'validate', 'aggregate'],
        help='Operation: transform (lowercase), validate (check fields), or aggregate (group)'
    )
    parser.add_argument(
        '--records',
        required=True,
        help='JSON string with records: [{"key":"value"}] or {"records":[...]}'
    )
    parser.add_argument(
        '--format',
        default='json',
        choices=['json', 'csv'],
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making changes'
    )

    args = parser.parse_args()

    try:
        # Parse records from JSON string
        records = parse_records_from_json(args.records)
        print(f"Processing {len(records)} records with operation: {args.operation}")

        # Call the shared business logic
        result = process_records(
            records=records,
            operation=args.operation,
            format_type=args.format,
            dry_run=args.dry_run
        )

        # Output result as JSON
        print(json.dumps(result, indent=2))

        # Exit with success (0) or failure (1) based on result
        exit_code = 0 if result.get('success', True) else 1
        sys.exit(exit_code)

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in records: {e}", file=sys.stderr)
        print(json.dumps({'success': False, 'error': f'JSON parse error: {str(e)}'}))
        sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
