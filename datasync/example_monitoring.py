"""
Example 3: Monitoring DataSync Tasks
Check task status, view execution details, and generate reports
"""

import boto3
import logging
from datetime import datetime, timedelta
from config import get_config
from datasync_manager import DataSyncManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSyncMonitor:
    """Monitor and report on DataSync tasks"""

    def __init__(self):
        self.config = get_config()
        self.manager = DataSyncManager(self.config)
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.config.AWS_REGION)

    def list_recent_executions(self, hours: int = 24):
        """
        List all task executions from the last N hours

        Args:
            hours: Number of hours to look back
        """
        tasks = self.manager.list_tasks()

        print(f"\n{'='*80}")
        print(f"Recent Task Executions (Last {hours} Hours)")
        print(f"{'='*80}\n")

        cutoff_time = datetime.now() - timedelta(hours=hours)

        for task in tasks:
            task_name = task.get('Name', 'Unknown')
            task_arn = task.get('TaskArn', '')

            try:
                executions_response = self.manager.client.list_task_executions(
                    TaskArn=task_arn
                )

                executions = executions_response.get('TaskExecutions', [])

                for execution in executions:
                    status = execution.get('Status')
                    start_time = execution.get('StartTime')

                    if start_time and start_time > cutoff_time:
                        print(f"Task: {task_name}")
                        print(f"  Status: {status}")
                        print(f"  Started: {start_time}")

                        if status == 'SUCCESS':
                            details = self.manager.get_task_execution_details(
                                execution.get('TaskExecutionArn')
                            )
                            print(f"  Files: {details.get('FilesTransferred', 0)}")
                            print(f"  Bytes: {details.get('BytesCopied', 0):,}")
                        elif status == 'FAILED':
                            print(f"  Error: {execution.get('ErrorCode', 'Unknown')}")

                        print()

            except Exception as e:
                logger.warning(f"Failed to get executions for {task_name}: {str(e)}")

    def get_task_statistics(self):
        """
        Get overall statistics for all tasks

        Returns:
            Dict with task statistics
        """
        tasks = self.manager.list_tasks()

        stats = {
            'total_tasks': len(tasks),
            'by_status': {},
            'total_files': 0,
            'total_bytes': 0,
        }

        print(f"\n{'='*80}")
        print(f"DataSync Task Statistics")
        print(f"{'='*80}\n")

        print(f"Total Tasks: {len(tasks)}\n")

        for task in tasks:
            task_name = task.get('Name', 'Unknown')
            task_arn = task.get('TaskArn', '')

            try:
                executions_response = self.manager.client.list_task_executions(
                    TaskArn=task_arn
                )

                executions = executions_response.get('TaskExecutions', [])

                if executions:
                    latest = executions[0]  # Most recent
                    status = latest.get('Status')

                    # Count by status
                    if status not in stats['by_status']:
                        stats['by_status'][status] = 0
                    stats['by_status'][status] += 1

                    # Get details
                    if status == 'SUCCESS':
                        details = self.manager.get_task_execution_details(
                            latest.get('TaskExecutionArn')
                        )
                        files = details.get('FilesTransferred', 0)
                        bytes_copied = details.get('BytesCopied', 0)

                        stats['total_files'] += files
                        stats['total_bytes'] += bytes_copied

                        print(f"✓ {task_name}")
                        print(f"  Files: {files} | Bytes: {bytes_copied:,}")
                    else:
                        print(f"✗ {task_name}")
                        print(f"  Status: {status}")

                    print()

            except Exception as e:
                logger.warning(f"Failed to get stats for {task_name}: {str(e)}")

        # Summary
        print(f"\n{'-'*80}")
        print(f"Summary:")
        print(f"  Total Files Transferred: {stats['total_files']:,}")
        print(f"  Total Bytes Transferred: {stats['total_bytes']:,}")
        print(f"  Total GB: {stats['total_bytes'] / (1024**3):.2f}")
        print(f"  By Status: {stats['by_status']}")
        print(f"{'-'*80}\n")

        return stats

    def check_task_by_name(self, task_name: str):
        """
        Get details for a specific task by name

        Args:
            task_name: Name of the task to check

        Returns:
            Dict with task details
        """
        print(f"\n{'='*80}")
        print(f"Task Details: {task_name}")
        print(f"{'='*80}\n")

        task_arn = self.manager.find_task_by_name(task_name)

        if not task_arn:
            print(f"✗ Task '{task_name}' not found")
            return None

        print(f"Task ARN: {task_arn}\n")

        # Get executions
        try:
            executions_response = self.manager.client.list_task_executions(
                TaskArn=task_arn
            )

            executions = executions_response.get('TaskExecutions', [])

            if not executions:
                print("No executions found")
                return None

            # Show recent executions (limit to 5)
            for i, execution in enumerate(executions[:5], 1):
                status = execution.get('Status')
                start_time = execution.get('StartTime')
                execution_arn = execution.get('TaskExecutionArn')

                print(f"Execution {i}:")
                print(f"  Status: {status}")
                print(f"  Started: {start_time}")

                if status == 'SUCCESS':
                    details = self.manager.get_task_execution_details(execution_arn)
                    print(f"  Files: {details.get('FilesTransferred', 0)}")
                    print(f"  Bytes: {details.get('BytesCopied', 0):,}")
                    print(f"  Verified: {details.get('BytesVerified', 0):,}")
                elif status == 'FAILED':
                    print(f"  Error: {execution.get('ErrorCode', 'Unknown')}")

                print()

        except Exception as e:
            logger.error(f"Failed to get executions: {str(e)}")

    def generate_daily_report(self):
        """
        Generate a summary report of yesterday's tasks

        Useful for daily operational reviews
        """
        tasks = self.manager.list_tasks()
        yesterday = datetime.now() - timedelta(days=1)

        print(f"\n{'='*80}")
        print(f"Daily Report - {yesterday.strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")

        successful = 0
        failed = 0
        total_files = 0
        total_bytes = 0

        for task in tasks:
            task_name = task.get('Name', '')

            try:
                executions_response = self.manager.client.list_task_executions(
                    TaskArn=task.get('TaskArn')
                )

                executions = executions_response.get('TaskExecutions', [])

                for execution in executions:
                    start_time = execution.get('StartTime')

                    # Filter for yesterday's executions
                    if start_time and start_time.date() == yesterday.date():
                        status = execution.get('Status')

                        if status == 'SUCCESS':
                            successful += 1
                            details = self.manager.get_task_execution_details(
                                execution.get('TaskExecutionArn')
                            )
                            total_files += details.get('FilesTransferred', 0)
                            total_bytes += details.get('BytesCopied', 0)

                            print(f"✓ {task_name}")
                            print(f"  Files: {details.get('FilesTransferred', 0)}")
                            print(f"  Bytes: {details.get('BytesCopied', 0):,}\n")

                        elif status == 'FAILED':
                            failed += 1
                            print(f"✗ {task_name}")
                            print(f"  Error: {execution.get('ErrorCode', 'Unknown')}\n")

            except Exception as e:
                logger.warning(f"Failed to get report for {task_name}: {str(e)}")

        # Summary
        print(f"\n{'-'*80}")
        print(f"Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total Files: {total_files:,}")
        print(f"  Total Bytes: {total_bytes:,} ({total_bytes / (1024**3):.2f} GB)")
        print(f"{'-'*80}\n")


if __name__ == '__main__':
    monitor = DataSyncMonitor()

    print("DataSync Monitoring Examples\n")
    print("1. Recent executions (last 24 hours)")
    monitor.list_recent_executions(hours=24)

    print("\n2. Task statistics")
    monitor.get_task_statistics()

    print("\n3. Daily report")
    monitor.generate_daily_report()

    # Uncomment to check specific task
    # print("\n4. Check specific task")
    # monitor.check_task_by_name("datasync-nas-to-s3-prod-inventory-2024/0804")
