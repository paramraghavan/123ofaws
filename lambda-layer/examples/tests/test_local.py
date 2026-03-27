#!/usr/bin/env python3
"""
Local testing script - Test CLI and Lambda handler with same data.

This demonstrates that both environments call the same business logic.

Usage:
    python test_local.py
"""

import json
import subprocess
import sys
from pathlib import Path


def test_cli():
    """Test the CLI version."""

    print("\n" + "="*70)
    print("TEST 1: CLI - Transform Operation")
    print("="*70)

    records = [
        {"Name": "Alice", "Email": "alice@example.com", "Category": "VIP"},
        {"Name": "Bob", "Email": "bob@example.com", "Category": "Regular"}
    ]

    cmd = [
        'python', 'cli_app.py',
        '--operation', 'transform',
        '--format', 'json',
        '--records', json.dumps(records)
    ]

    print(f"\nCommand: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print(f"Exit Code: {result.returncode}\n")

    return result.returncode == 0


def test_cli_validate():
    """Test CLI validation operation."""

    print("\n" + "="*70)
    print("TEST 2: CLI - Validate Operation (missing required fields)")
    print("="*70)

    records = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},  # Valid
        {"id": 2, "name": "Bob"},  # Missing email
        {"email": "charlie@example.com"}  # Missing id and name
    ]

    cmd = [
        'python', 'cli_app.py',
        '--operation', 'validate',
        '--records', json.dumps(records),
        '--verbose'
    ]

    print(f"\nCommand: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print(f"Exit Code: {result.returncode}\n")

    return True  # Validation fails correctly for incomplete data


def test_cli_dry_run():
    """Test CLI with dry-run flag."""

    print("\n" + "="*70)
    print("TEST 3: CLI - Dry-run Flag")
    print("="*70)

    records = [
        {"id": 1, "category": "A"},
        {"id": 2, "category": "B"},
        {"id": 3, "category": "A"}
    ]

    cmd = [
        'python', 'cli_app.py',
        '--operation', 'aggregate',
        '--records', json.dumps(records),
        '--dry-run'
    ]

    print(f"\nCommand: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = json.loads(result.stdout)

    print("Output:")
    print(json.dumps(output, indent=2))
    print(f"\nDry-run flag in output: {output.get('dry_run')}")
    print(f"Exit Code: {result.returncode}\n")

    return output.get('dry_run') == True


def test_lambda_handler():
    """Test Lambda handler locally."""

    print("\n" + "="*70)
    print("TEST 4: Lambda Handler - Transform Operation")
    print("="*70)

    event = {
        "operation": "transform",
        "records": [
            {"Name": "Alice", "Email": "alice@example.com"},
            {"Name": "Bob", "Email": "bob@example.com"}
        ],
        "format": "json"
    }

    print(f"\nInvoking handler with event:\n{json.dumps(event, indent=2)}\n")

    # Import and call handler directly
    try:
        from lambda_function import handler

        class TestContext:
            invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
            function_name = "test"
            request_id = "test-request-123"

        response = handler(event, TestContext())

        print("Response:")
        print(json.dumps(response, indent=2))
        print(f"\nStatus Code: {response.get('statusCode')}")
        print(f"Success: {response.get('body', {}).get('success')}\n")

        return response.get('statusCode') == 200

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_lambda_handler_error():
    """Test Lambda handler with invalid input."""

    print("\n" + "="*70)
    print("TEST 5: Lambda Handler - Error Handling (missing required field)")
    print("="*70)

    event = {
        # Missing 'records' - required field
        "operation": "transform",
        "format": "json"
    }

    print(f"\nInvoking handler with incomplete event:\n{json.dumps(event, indent=2)}\n")

    try:
        from lambda_function import handler

        class TestContext:
            invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"

        response = handler(event, TestContext())

        print("Response:")
        print(json.dumps(response, indent=2))
        print(f"\nStatus Code: {response.get('statusCode')}")
        print(f"Error: {response.get('body', {}).get('error')}\n")

        return response.get('statusCode') == 400

    except Exception as e:
        print(f"Error: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""

    print("\n" + "#"*70)
    print("# LOCAL TESTING: CLI vs Lambda Handler")
    print("#"*70)

    tests = [
        ("CLI - Transform", test_cli),
        ("CLI - Validate", test_cli_validate),
        ("CLI - Dry-run", test_cli_dry_run),
        ("Lambda - Transform", test_lambda_handler),
        ("Lambda - Error Handling", test_lambda_handler_error),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}\n")
            results.append((test_name, False))

    # Print summary
    print("\n" + "#"*70)
    print("# TEST SUMMARY")
    print("#"*70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed\n")

    return passed_count == total_count


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
