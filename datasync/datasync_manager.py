"""
DataSync Manager - Handle DataSync task creation, execution, and monitoring
"""

import json
import logging
import time
from typing import Optional, Dict, List, Any
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from config import Config

logger = logging.getLogger(__name__)


class DataSyncManager:
    """Manages DataSync tasks and execution"""

    def __init__(self, config: Config):
        """
        Initialize DataSync manager

        Args:
            config: Configuration object
        """
        self.config = config
        self.client = boto3.client('datasync', region_name=config.AWS_REGION)
        self.sns_client = boto3.client('sns', region_name=config.AWS_REGION)
        self.logger = logging.getLogger(__name__)

    def create_task(
        self,
        task_name: str,
        source_path: str,
        destination_path: str,
        verify: bool = True
    ) -> str:
        """
        Create a DataSync task

        Args:
            task_name: Name for the task
            source_path: NAS path (e.g., '/mydata/prod/icm/datain/poolData/datatype/2024/0804')
            destination_path: S3 prefix (e.g., '/poolData/datatype/2024/0804')
            verify: Whether to verify data after copy

        Returns:
            str: Task ARN

        Raises:
            ClientError: If task creation fails
        """
        try:
            self.logger.info(f"Creating DataSync task: {task_name}")
            self.logger.info(f"  Source: {source_path}")
            self.logger.info(f"  Destination: {destination_path}")

            # Build task definition
            task_definition = {
                'SourceLocationArn': self.config.DATASYNC_NFS_LOCATION_ARN,
                'DestinationLocationArn': self.config.DATASYNC_S3_LOCATION_ARN,
                'Name': task_name,
                'Options': {
                    'VerifyMode': self.config.DATASYNC_OPTIONS.get('VerifyMode', 'POINT_IN_TIME_CONSISTENT'),
                    'OverwriteMode': self.config.DATASYNC_OPTIONS.get('OverwriteMode', 'ALWAYS'),
                    'Atime': self.config.DATASYNC_OPTIONS.get('Atime', 'BEST_EFFORT'),
                    'Mtime': self.config.DATASYNC_OPTIONS.get('Mtime', 'PRESERVE'),
                    'PreserveDeletedFiles': self.config.DATASYNC_OPTIONS.get('PreserveDeletedFiles', False),
                    'TransferMode': self.config.DATASYNC_OPTIONS.get('TransferMode', 'CHANGED'),
                    'LogLevel': self.config.DATASYNC_OPTIONS.get('LogLevel', 'TRANSFER'),
                },
                'Excludes': [],  # Can add exclude patterns if needed
                'Schedule': {
                    'ScheduleExpression': 'rate(0 minutes)'  # No auto-schedule; we'll start manually
                },
                'Tags': [
                    {
                        'Key': 'Environment',
                        'Value': self.config.ENVIRONMENT
                    },
                    {
                        'Key': 'CreatedBy',
                        'Value': 'datasync-orchestrator'
                    },
                    {
                        'Key': 'CreatedAt',
                        'Value': datetime.now().isoformat()
                    }
                ]
            }

            # Create the task
            response = self.client.create_task(**task_definition)
            task_arn = response['TaskArn']

            self.logger.info(f"Task created successfully: {task_arn}")
            return task_arn

        except ClientError as e:
            self.logger.error(f"Failed to create DataSync task: {str(e)}")
            raise

    def update_task(
        self,
        task_arn: str,
        task_name: Optional[str] = None
    ) -> None:
        """
        Update an existing DataSync task

        Args:
            task_arn: ARN of the task to update
            task_name: New name for the task (optional)

        Raises:
            ClientError: If update fails
        """
        try:
            update_params = {'TaskArn': task_arn}

            if task_name:
                update_params['Name'] = task_name

            self.client.update_task(**update_params)
            self.logger.info(f"Task updated: {task_arn}")

        except ClientError as e:
            self.logger.error(f"Failed to update DataSync task: {str(e)}")
            raise

    def start_task_execution(self, task_arn: str) -> str:
        """
        Start a task execution

        Args:
            task_arn: ARN of the task to execute

        Returns:
            str: Task Execution ARN

        Raises:
            ClientError: If execution fails to start
        """
        try:
            self.logger.info(f"Starting task execution: {task_arn}")

            response = self.client.start_task_execution(TaskArn=task_arn)
            execution_arn = response['TaskExecutionArn']

            self.logger.info(f"Task execution started: {execution_arn}")
            return execution_arn

        except ClientError as e:
            self.logger.error(f"Failed to start task execution: {str(e)}")
            raise

    def wait_for_task_completion(
        self,
        task_execution_arn: str,
        timeout_seconds: int = 3600,
        check_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for a task execution to complete

        Args:
            task_execution_arn: ARN of the execution to monitor
            timeout_seconds: Maximum time to wait in seconds
            check_interval: Interval between status checks in seconds

        Returns:
            Dict: Task execution details

        Raises:
            TimeoutError: If execution doesn't complete within timeout
            Exception: If execution fails
        """
        self.logger.info(f"Waiting for task completion: {task_execution_arn}")

        start_time = time.time()
        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout_seconds:
                raise TimeoutError(
                    f"Task execution did not complete within {timeout_seconds} seconds"
                )

            try:
                response = self.client.describe_task_execution(
                    TaskExecutionArn=task_execution_arn
                )

                status = response['Status']
                self.logger.debug(f"Task status: {status} (elapsed: {int(elapsed)}s)")

                if status == 'SUCCESS':
                    self.logger.info("Task execution completed successfully")
                    return response

                elif status == 'FAILED':
                    error_msg = response.get('ErrorCode', 'Unknown error')
                    self.logger.error(f"Task execution failed: {error_msg}")
                    raise Exception(f"DataSync task failed: {error_msg}")

                elif status in ['CANCELLED', 'CANCELLING']:
                    raise Exception(f"Task execution was cancelled: {status}")

                time.sleep(check_interval)

            except ClientError as e:
                self.logger.error(f"Failed to check task status: {str(e)}")
                raise

    def get_task_execution_details(self, task_execution_arn: str) -> Dict[str, Any]:
        """
        Get detailed information about a task execution

        Args:
            task_execution_arn: ARN of the execution

        Returns:
            Dict: Execution details including:
                - Status
                - BytesCopied
                - BytesVerified
                - ErrorCode
                - etc.
        """
        try:
            response = self.client.describe_task_execution(
                TaskExecutionArn=task_execution_arn
            )
            return response

        except ClientError as e:
            self.logger.error(f"Failed to get task execution details: {str(e)}")
            raise

    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all DataSync tasks

        Returns:
            List[Dict]: List of task information
        """
        try:
            response = self.client.list_tasks()
            return response.get('Tasks', [])

        except ClientError as e:
            self.logger.error(f"Failed to list tasks: {str(e)}")
            raise

    def find_task_by_name(self, task_name: str) -> Optional[str]:
        """
        Find a task ARN by name

        Args:
            task_name: Name of the task to find

        Returns:
            str: Task ARN if found, None otherwise
        """
        try:
            tasks = self.list_tasks()
            for task in tasks:
                if task.get('Name') == task_name:
                    return task['TaskArn']
            return None

        except ClientError as e:
            self.logger.error(f"Failed to find task: {str(e)}")
            raise

    def send_notification(
        self,
        subject: str,
        message: str,
        message_type: str = 'INFO'
    ) -> None:
        """
        Send SNS notification

        Args:
            subject: Notification subject
            message: Notification message
            message_type: Type of message (INFO, SUCCESS, WARNING, ERROR)
        """
        try:
            # Format message
            formatted_message = f"""
[{message_type}] DataSync Orchestrator Notification

{message}

---
Environment: {self.config.ENVIRONMENT}
Timestamp: {datetime.now().isoformat()}
            """

            self.sns_client.publish(
                TopicArn=self.config.SNS_TOPIC_ARN,
                Subject=subject,
                Message=formatted_message
            )

            self.logger.info(f"Notification sent: {subject}")

        except ClientError as e:
            self.logger.warning(f"Failed to send notification: {str(e)}")
            # Don't raise - notification failure shouldn't stop the process


class DataSyncOrchestrator:
    """
    High-level orchestrator combining date logic and DataSync operations
    """

    def __init__(self, config: Config):
        self.config = config
        self.datasync = DataSyncManager(config)
        self.logger = logging.getLogger(__name__)

    def execute_copy_task(
        self,
        datatype: str,
        date_str: str,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a complete copy task for a specific datatype and date

        Args:
            datatype: Data type (e.g., 'inventory')
            date_str: Date in YYYY/MMDD format
            wait_for_completion: Whether to wait for task to complete

        Returns:
            Dict: Result containing:
                - task_arn
                - execution_arn
                - status
                - details (if completed)
        """
        try:
            # Generate paths
            task_name = self.config.get_task_name(datatype, date_str)
            source_path = self.config.get_nas_source_path(datatype, date_str)
            destination_path = self.config.get_s3_destination_path(datatype, date_str)

            self.logger.info(f"Executing copy task: {task_name}")

            # Check if task exists
            existing_task_arn = self.datasync.find_task_by_name(task_name)

            if existing_task_arn:
                self.logger.info(f"Reusing existing task: {existing_task_arn}")
                task_arn = existing_task_arn
            else:
                # Create new task
                task_arn = self.datasync.create_task(
                    task_name=task_name,
                    source_path=source_path,
                    destination_path=destination_path
                )

            # Start execution
            execution_arn = self.datasync.start_task_execution(task_arn)

            result = {
                'task_arn': task_arn,
                'execution_arn': execution_arn,
                'status': 'STARTED',
                'datatype': datatype,
                'date': date_str
            }

            if wait_for_completion:
                self.logger.info("Waiting for task completion...")
                details = self.datasync.wait_for_task_completion(
                    execution_arn,
                    timeout_seconds=self.config.TASK_TIMEOUT_SECONDS
                )

                result['status'] = 'SUCCESS'
                result['details'] = {
                    'BytesCopied': details.get('BytesCopied', 0),
                    'BytesVerified': details.get('BytesVerified', 0),
                    'FilesTransferred': details.get('FilesTransferred', 0),
                    'ErrorCode': details.get('ErrorCode', None)
                }

                self.datasync.send_notification(
                    subject=f"DataSync Task Completed: {datatype} / {date_str}",
                    message=f"Successfully copied {details.get('FilesTransferred', 0)} files "
                            f"({details.get('BytesCopied', 0)} bytes)",
                    message_type='SUCCESS'
                )

            return result

        except Exception as e:
            self.logger.error(f"Failed to execute copy task: {str(e)}")

            self.datasync.send_notification(
                subject=f"DataSync Task Failed: {datatype} / {date_str}",
                message=f"Error: {str(e)}",
                message_type='ERROR'
            )

            raise

    def execute_batch_copy(
        self,
        dates: List[str],
        datatypes: Optional[List[str]] = None,
        wait_for_completion: bool = True,
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute copy tasks for multiple dates and datatypes

        Args:
            dates: List of dates in YYYY/MMDD format
            datatypes: List of datatypes (uses config default if None)
            wait_for_completion: Whether to wait for all tasks
            parallel: Whether to run tasks in parallel (not implemented yet)

        Returns:
            List[Dict]: Results for each task
        """
        if datatypes is None:
            datatypes = self.config.get_datatypes()

        results = []

        self.logger.info(
            f"Starting batch copy: {len(dates)} date(s) × {len(datatypes)} datatype(s)"
        )

        for datatype in datatypes:
            for date_str in dates:
                try:
                    result = self.execute_copy_task(
                        datatype=datatype,
                        date_str=date_str,
                        wait_for_completion=wait_for_completion
                    )
                    results.append(result)

                except Exception as e:
                    self.logger.error(f"Failed to execute task for {datatype}/{date_str}: {str(e)}")
                    results.append({
                        'datatype': datatype,
                        'date': date_str,
                        'status': 'FAILED',
                        'error': str(e)
                    })

        return results
