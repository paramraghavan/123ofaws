"""
Daily NFS to S3 Sync via DataSync
Runs every day at 6 PM
Copies files from /yyyy/mmdd/ folder to S3
"""

import boto3
import time
from datetime import datetime

# UPDATE THESE WITH YOUR ARNS
NFS_LOCATION_ARN = 'arn:aws:datasync:us-east-1:YOUR_ACCOUNT:location/nfs/YOUR_NFS_ID'
S3_LOCATION_ARN = 'arn:aws:datasync:us-east-1:YOUR_ACCOUNT:location/s3/YOUR_S3_ID'

datasync = boto3.client('datasync')


def lambda_handler(event, context):
    """
    Runs daily at 6 PM
    Checks /yyyy/mmdd/ folder and copies new files to S3
    """

    today = datetime.now()
    year = today.strftime('%Y')
    month_day = today.strftime('%m%d')

    print(f"Starting daily sync at {today}")
    print(f"Checking folder: /{year}/{month_day}/")

    try:
        # Step 1: Find or create task for today's folder
        task_arn = find_or_create_task(year, month_day)
        print(f"Using task: {task_arn}")

        # Step 2: Start copying
        execution_arn = start_copy(task_arn)
        print(f"Started copying: {execution_arn}")

        # Step 3: Wait for completion
        result = wait_for_copy(execution_arn)

        print(f"✓ Success! Files copied: {result['files']}, Bytes: {result['bytes']}")

        return {
            'statusCode': 200,
            'message': f"Copied {result['files']} files ({result['bytes']} bytes)",
            'date': f"{year}/{month_day}"
        }

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }


def find_or_create_task(year, month_day):
    """Find existing task or create new one for today's folder"""

    task_name = f"sync-{year}-{month_day}"

    # Check if task already exists
    tasks = datasync.list_tasks()['Tasks']
    for task in tasks:
        if task['Name'] == task_name:
            return task['TaskArn']

    # Create new task for today's folder
    print(f"Creating task for /{year}/{month_day}/")

    response = datasync.create_task(
        SourceLocationArn=NFS_LOCATION_ARN,
        DestinationLocationArn=S3_LOCATION_ARN,
        Name=task_name,
        Options={
            'VerifyMode': 'POINT_IN_TIME_CONSISTENT',
            'OverwriteMode': 'ALWAYS',
            'TransferMode': 'CHANGED',  # Only copy new/changed files
        }
    )

    return response['TaskArn']


def start_copy(task_arn):
    """Start the copy task"""
    response = datasync.start_task_execution(TaskArn=task_arn)
    return response['TaskExecutionArn']


def wait_for_copy(execution_arn, max_wait=900):
    """Wait for copy to complete (up to 15 minutes)"""

    start = time.time()

    while True:
        elapsed = time.time() - start

        if elapsed > max_wait:
            raise TimeoutError(f"Copy timed out after {max_wait} seconds")

        # Check status
        response = datasync.describe_task_execution(TaskExecutionArn=execution_arn)
        status = response['Status']

        print(f"  Status: {status} (elapsed: {int(elapsed)}s)")

        if status == 'SUCCESS':
            return {
                'files': response.get('FilesTransferred', 0),
                'bytes': response.get('BytesCopied', 0)
            }

        if status == 'FAILED':
            raise Exception(f"Copy failed: {response.get('ErrorCode')}")

        time.sleep(5)
