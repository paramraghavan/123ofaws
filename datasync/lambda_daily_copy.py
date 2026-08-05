"""
AWS Lambda function for daily NFS to S3 copy via DataSync
Deploy to Lambda and trigger with EventBridge cron schedule
"""

import boto3
import time
import json
import os
from datetime import datetime

# Configuration from environment variables
NFS_LOCATION_ARN = os.environ.get('NFS_LOCATION_ARN')
S3_LOCATION_ARN = os.environ.get('S3_LOCATION_ARN')
TASK_NAME = 'Daily-NFS-to-S3-Copy'


def lambda_handler(event, context):
    """
    Main Lambda handler - runs daily via EventBridge
    """
    print(f"Starting daily DataSync copy at {datetime.now()}")

    # Initialize DataSync client
    datasync = boto3.client('datasync')

    # Validate configuration
    if not NFS_LOCATION_ARN or not S3_LOCATION_ARN:
        return error_response('Missing NFS_LOCATION_ARN or S3_LOCATION_ARN environment variables')

    try:
        # Step 1: Find or create task
        print("Step 1: Finding or creating task...")
        task_arn = find_or_create_task(datasync, NFS_LOCATION_ARN, S3_LOCATION_ARN)
        print(f"  Using task: {task_arn}")

        # Step 2: Start task execution
        print("Step 2: Starting task execution...")
        execution_arn = start_copy(datasync, task_arn)
        print(f"  Execution started: {execution_arn}")

        # Step 3: Monitor until complete (with timeout)
        print("Step 3: Monitoring progress...")
        result = monitor_execution(datasync, execution_arn)

        # Step 4: Return success
        return success_response(result)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return error_response(str(e))


def find_or_create_task(datasync, nfs_arn, s3_arn):
    """Find existing task or create a new one"""

    # List existing tasks
    response = datasync.list_tasks()
    tasks = response.get('Tasks', [])

    # Look for existing task with our name
    for task in tasks:
        if task['Name'] == TASK_NAME:
            print(f"  Found existing task: {task['TaskArn']}")
            return task['TaskArn']

    # Create new task if not found
    print(f"  Task not found, creating new task...")
    response = datasync.create_task(
        SourceLocationArn=nfs_arn,
        DestinationLocationArn=s3_arn,
        Name=TASK_NAME,
        Options={
            'VerifyMode': 'POINT_IN_TIME_CONSISTENT',
            'OverwriteMode': 'ALWAYS',
            'TransferMode': 'CHANGED',  # Only copy new/changed files
            'Atime': 'BEST_EFFORT',
            'Mtime': 'PRESERVE',
        }
    )

    task_arn = response['TaskArn']
    print(f"  Created new task: {task_arn}")
    return task_arn


def start_copy(datasync, task_arn):
    """Start a task execution"""
    response = datasync.start_task_execution(TaskArn=task_arn)
    return response['TaskExecutionArn']


def monitor_execution(datasync, execution_arn, max_wait=1800):
    """
    Monitor execution until completion
    max_wait: Maximum seconds to wait (default 30 minutes for Lambda)
    """
    start_time = time.time()
    check_interval = 5

    while True:
        elapsed = time.time() - start_time

        # Timeout check
        if elapsed > max_wait:
            raise TimeoutError(f'Task did not complete within {max_wait} seconds')

        # Get status
        response = datasync.describe_task_execution(TaskExecutionArn=execution_arn)
        status = response['Status']

        print(f"  Status: {status} (elapsed: {int(elapsed)}s)")

        if status == 'SUCCESS':
            return {
                'status': 'SUCCESS',
                'files_transferred': response.get('FilesTransferred', 0),
                'bytes_copied': response.get('BytesCopied', 0),
                'files_skipped': response.get('FilesSkipped', 0),
            }

        elif status == 'FAILED':
            error_code = response.get('ErrorCode', 'Unknown error')
            raise Exception(f'Task failed: {error_code}')

        elif status == 'CANCELLED':
            raise Exception('Task was cancelled')

        # Wait before checking again
        time.sleep(check_interval)


def success_response(result):
    """Format success response"""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Copy completed successfully',
            'timestamp': datetime.now().isoformat(),
            'files_transferred': result['files_transferred'],
            'bytes_copied': result['bytes_copied'],
            'files_skipped': result['files_skipped'],
        })
    }


def error_response(error_message):
    """Format error response"""
    return {
        'statusCode': 500,
        'body': json.dumps({
            'message': 'Copy failed',
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
        })
    }
