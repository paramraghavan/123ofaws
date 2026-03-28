#!/usr/bin/env python3
"""
Local testing script - Test CLI and Lambda handler.

Simple tests to verify both work with the same business logic.

Usage:
    python tests/test_local.py
"""

import json
import subprocess
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_cli_transform():
    """Test CLI with transform operation."""

    print("\n" + "="*70)
    print("TEST 1: CLI - Transform Operation")
    print("="*70)

    records = [
        {"Name": "Alice", "Email": "alice@example.com"},
        {"Name": "Bob", "Email": "bob@example.com"}
    ]

    cmd = [
        'python', 'cli_app.py',
        '--operation', 'transform',
        '--records', json.dumps(records)
    ]

    print(f"Command: python cli_app.py --operation transform --records '[...]'\n")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    print(result.stdout)

    if result.stderr and "Processing" not in result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


def test_cli_validate():
    """Test CLI with validate operation."""

    print("\n" + "="*70)
    print("TEST 2: CLI - Validate Operation")
    print("="*70)

    records = [
        {"id": 1, "name": "Alice", "email": "alice@test.com"},  # Valid
        {"id": 2, "name": "Bob"},  # Invalid (missing email)
    ]

    cmd = [
        'python', 'cli_app.py',
        '--operation', 'validate',
        '--records', json.dumps(records)
    ]

    print(f"Command: python cli_app.py --operation validate --records '[...]'\n")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    print(result.stdout)

    # Validate should detect the invalid record and exit with code 1
    # (success=false because one record is invalid)
    return result.returncode == 1


def test_cli_aggregate():
    """Test CLI with aggregate operation."""

    print("\n" + "="*70)
    print("TEST 3: CLI - Aggregate Operation")
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

    print(f"Command: python cli_app.py --operation aggregate --records '[...]' --dry-run\n")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    print(result.stdout)

    return result.returncode == 0


def test_lambda_handler():
    """Test Lambda handler directly."""

    print("\n" + "="*70)
    print("TEST 4: Lambda Handler - Transform Operation")
    print("="*70)

    try:
        from lambda_function import handler

        class TestContext:
            invoked_function_arn = 'arn:aws:lambda:test'

        event = {
            "operation": "transform",
            "records": [
                {"Name": "Alice", "Email": "alice@test.com"},
                {"Name": "Bob", "Email": "bob@test.com"}
            ]
        }

        print(f"Event: {json.dumps(event, indent=2)}\n")

        response = handler(event, TestContext())
        print("Response:")
        print(json.dumps(response, indent=2))

        return response.get('statusCode') == 200

    except Exception as e:
        print(f"ERROR: {e}\n")
        return False


def test_lambda_error_handling():
    """Test Lambda error handling."""

    print("\n" + "="*70)
    print("TEST 5: Lambda Handler - Error Handling")
    print("="*70)

    try:
        from lambda_function import handler

        class TestContext:
            invoked_function_arn = 'arn:aws:lambda:test'

        # Missing 'records' parameter
        event = {"operation": "transform"}

        print(f"Event (missing records): {json.dumps(event)}\n")

        response = handler(event, TestContext())
        print("Response:")
        print(json.dumps(response, indent=2))

        # Should return 400 error
        return response.get('statusCode') == 400

    except Exception as e:
        print(f"ERROR: {e}\n")
        return False


def run_all_tests():
    """Run all tests and report results."""

    print("\n" + "#"*70)
    print("# LOCAL TESTING: CLI vs Lambda Handler")
    print("#"*70)

    tests = [
        ("CLI - Transform", test_cli_transform),
        ("CLI - Validate", test_cli_validate),
        ("CLI - Aggregate", test_cli_aggregate),
        ("Lambda - Transform", test_lambda_handler),
        ("Lambda - Error Handling", test_lambda_error_handling),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed: {e}\n")
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
