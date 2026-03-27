#!/usr/bin/env python3
"""
CLI Application - Command-line interface for record processing.

This script demonstrates how to:
1. Parse command-line arguments
2. Call shared business logic
3. Output results as JSON

Usage:
    python cli_app.py --operation transform --format json --records '[...]'
    python cli_app.py --operation validate --dry-run
"""

import argparse
import json
import sys
import logging
from typing import Dict, Any

# Import shared library
from shared_lib.processor import process_records, parse_records_from_json
from shared_lib.logger import get_logger

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse and return command-line arguments."""

    parser = argparse.ArgumentParser(
        description='Process records with multiple operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Transform records to lowercase keys
  python cli_app.py \\
    --operation transform \\
    --format json \\
    --records '[{"Name":"Alice","Email":"alice@example.com"}]'

  # Validate records (check required fields)
  python cli_app.py \\
    --operation validate \\
    --records '{"records":[{"id":1,"name":"Bob","email":"bob@example.com"}]}'

  # Dry-run (no side effects)
  python cli_app.py \\
    --operation transform \\
    --dry-run \\
    --records '[{"id":1}]'

  # Set log level
  LOG_LEVEL=DEBUG python cli_app.py --operation validate
        '''
    )

    # Required arguments
    parser.add_argument(
        '--operation',
        required=True,
        choices=['transform', 'validate', 'aggregate'],
        help='Operation to perform on records'
    )

    # Records input
    parser.add_argument(
        '--records',
        required=True,
        help='JSON string containing records (list or dict with "records" key)'
    )

    # Optional arguments
    parser.add_argument(
        '--format',
        default='json',
        choices=['json', 'csv'],
        help='Output format (default: json)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without persisting changes'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def main():
    """Main CLI entry point."""

    # Parse arguments
    args = parse_arguments()

    # Configure logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger_instance = get_logger(__name__, level=log_level)
    logger_instance.debug(f"Arguments: {args}")

    try:
        # Parse records from JSON string
        logger_instance.info(f"Parsing records from JSON...")
        records = parse_records_from_json(args.records)
        logger_instance.info(f"Parsed {len(records)} records")

        # Call shared business logic
        logger_instance.info(f"Executing operation: {args.operation}")
        result = process_records(
            records=records,
            operation=args.operation,
            format_type=args.format,
            dry_run=args.dry_run
        )

        # Output result as JSON
        print(json.dumps(result, indent=2))

        # Exit with status based on success
        sys.exit(0 if result.get('success', False) else 1)

    except json.JSONDecodeError as e:
        logger_instance.error(f"Invalid JSON in records: {e}")
        print(json.dumps({
            'success': False,
            'error': f'Invalid JSON: {str(e)}',
            'operation': args.operation
        }), file=sys.stdout)
        sys.exit(1)

    except Exception as e:
        logger_instance.error(f"Unexpected error: {e}", exc_info=True)
        print(json.dumps({
            'success': False,
            'error': str(e),
            'operation': args.operation
        }), file=sys.stdout)
        sys.exit(1)


if __name__ == '__main__':
    main()
