"""
Data processor module - contains pure business logic.

This module is designed to be:
- Used from CLI via arguments
- Used from Lambda via event dict
- Testable in isolation
- Environment-agnostic
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def process_records(
    records: List[Dict[str, Any]],
    operation: str,
    format_type: str = 'json',
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Process a list of records based on operation type.

    Args:
        records: List of record dictionaries
        operation: One of 'transform', 'validate', 'aggregate'
        format_type: Output format ('json' or 'csv')
        dry_run: If True, don't persist changes

    Returns:
        Dictionary with processing results
    """

    logger.info(f"Processing {len(records)} records with operation: {operation}")

    if operation == 'transform':
        return _transform_records(records, format_type, dry_run)
    elif operation == 'validate':
        return _validate_records(records, format_type, dry_run)
    elif operation == 'aggregate':
        return _aggregate_records(records, format_type, dry_run)
    else:
        return {
            'success': False,
            'error': f'Unknown operation: {operation}',
            'operation': operation
        }


def _transform_records(
    records: List[Dict[str, Any]],
    format_type: str,
    dry_run: bool
) -> Dict[str, Any]:
    """Transform records (example: convert field names to lowercase)."""

    transformed = []
    for record in records:
        new_record = {k.lower(): v for k, v in record.items()}
        transformed.append(new_record)

    logger.info(f"Transformed {len(transformed)} records")

    return {
        'success': True,
        'operation': 'transform',
        'count_processed': len(transformed),
        'dry_run': dry_run,
        'format': format_type,
        'timestamp': datetime.utcnow().isoformat(),
        'sample': transformed[:2] if transformed else []
    }


def _validate_records(
    records: List[Dict[str, Any]],
    format_type: str,
    dry_run: bool
) -> Dict[str, Any]:
    """Validate records (example: check required fields)."""

    required_fields = ['id', 'name', 'email']
    valid = []
    invalid = []

    for idx, record in enumerate(records):
        missing = [f for f in required_fields if f not in record]
        if missing:
            invalid.append({
                'index': idx,
                'record': record,
                'missing_fields': missing
            })
        else:
            valid.append(record)

    logger.info(f"Validated: {len(valid)} valid, {len(invalid)} invalid")

    return {
        'success': len(invalid) == 0,
        'operation': 'validate',
        'count_valid': len(valid),
        'count_invalid': len(invalid),
        'dry_run': dry_run,
        'format': format_type,
        'timestamp': datetime.utcnow().isoformat(),
        'invalid_records': invalid[:5]  # Return first 5 for debugging
    }


def _aggregate_records(
    records: List[Dict[str, Any]],
    format_type: str,
    dry_run: bool
) -> Dict[str, Any]:
    """Aggregate records by category."""

    categories = {}
    for record in records:
        category = record.get('category', 'unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(record)

    logger.info(f"Aggregated into {len(categories)} categories")

    return {
        'success': True,
        'operation': 'aggregate',
        'total_records': len(records),
        'categories': {
            cat: len(recs) for cat, recs in categories.items()
        },
        'dry_run': dry_run,
        'format': format_type,
        'timestamp': datetime.utcnow().isoformat()
    }


def parse_records_from_json(json_str: str) -> List[Dict[str, Any]]:
    """Parse records from JSON string."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'records' in data:
            return data['records']
        else:
            raise ValueError("JSON must be a list or have 'records' key")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise
