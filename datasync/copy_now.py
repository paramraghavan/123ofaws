#!/usr/bin/env python3
"""
Simple one-time copy from NFS to S3 using DataSync
Just run: python copy_now.py
"""

import boto3
import time
import sys

# Configuration - Update these with your ARNs
NFS_LOCATION_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123'
S3_LOCATION_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789'
AWS_REGION = 'us-east-1'

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def main():
    print(f"{YELLOW}AWS DataSync NFS to S3 Copy{RESET}")
    print("=" * 50)

    # Create DataSync client
    datasync = boto3.client('datasync', region_name=AWS_REGION)

    # Check if ARNs are configured
    if 'abc123' in NFS_LOCATION_ARN:
        print(f"{RED}ERROR: Update NFS_LOCATION_ARN and S3_LOCATION_ARN in the script{RESET}")
        sys.exit(1)

    # Create task
    print(f"\n{YELLOW}Creating DataSync task...{RESET}")
    try:
        task_response = datasync.create_task(
            SourceLocationArn=NFS_LOCATION_ARN,
            DestinationLocationArn=S3_LOCATION_ARN,
            Name=f'NFS-to-S3-Copy-{int(time.time())}',
            Options={
                'VerifyMode': 'POINT_IN_TIME_CONSISTENT',
                'OverwriteMode': 'ALWAYS',
                'TransferMode': 'CHANGED',  # Only copy new/changed files
            }
        )
        task_arn = task_response['TaskArn']
        print(f"{GREEN}✓ Task created: {task_arn}{RESET}")
    except Exception as e:
        print(f"{RED}ERROR creating task: {str(e)}{RESET}")
        sys.exit(1)

    # Start task execution
    print(f"\n{YELLOW}Starting copy...{RESET}")
    try:
        exec_response = datasync.start_task_execution(TaskArn=task_arn)
        execution_arn = exec_response['TaskExecutionArn']
        print(f"{GREEN}✓ Copy started: {execution_arn}{RESET}")
    except Exception as e:
        print(f"{RED}ERROR starting task: {str(e)}{RESET}")
        sys.exit(1)

    # Monitor progress
    print(f"\n{YELLOW}Monitoring progress...{RESET}")
    print("(This may take a while depending on file size)")

    start_time = time.time()
    while True:
        try:
            status_response = datasync.describe_task_execution(TaskExecutionArn=execution_arn)
            status = status_response['Status']

            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60

            print(f"\rStatus: {status} | Elapsed: {minutes}m {seconds}s", end='', flush=True)

            if status == 'SUCCESS':
                files = status_response.get('FilesTransferred', 0)
                bytes_copied = status_response.get('BytesCopied', 0)
                mb = bytes_copied / (1024 * 1024)
                print(f"\n\n{GREEN}✓ Copy successful!{RESET}")
                print(f"  Files transferred: {files}")
                print(f"  Data copied: {mb:.2f} MB")
                break

            elif status == 'FAILED':
                error = status_response.get('ErrorCode', 'Unknown error')
                print(f"\n\n{RED}✗ Copy failed: {error}{RESET}")
                sys.exit(1)

            time.sleep(5)

        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Copy cancelled by user{RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{RED}Error checking status: {str(e)}{RESET}")
            sys.exit(1)

if __name__ == '__main__':
    main()
