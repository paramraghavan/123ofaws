"""
Configuration module for DataSync Orchestrator
Supports both environment variables and AWS Systems Manager Parameter Store
"""

import os
from typing import List


class Config:
    """DataSync orchestrator configuration"""

    # AWS DataSync configuration
    DATASYNC_NFS_LOCATION_ARN = os.getenv(
        'DATASYNC_NFS_LOCATION_ARN',
        'arn:aws:datasync:us-east-1:123456789012:location/nfs/12345678901234567'
    )

    DATASYNC_S3_LOCATION_ARN = os.getenv(
        'DATASYNC_S3_LOCATION_ARN',
        'arn:aws:datasync:us-east-1:123456789012:location/s3/87654321098765432'
    )

    # NAS and S3 paths
    NAS_BASE_PATH = os.getenv(
        'NAS_BASE_PATH',
        '/mydata/prod/icm/datain/poolData'
    )

    S3_BUCKET = os.getenv(
        'S3_BUCKET',
        'my-datasync-bucket'
    )

    S3_PREFIX = os.getenv(
        'S3_PREFIX',
        'poolData'
    )

    # Data types to copy (comma-separated)
    DATATYPES = os.getenv(
        'DATATYPES',
        'datatype1,datatype2,datatype3'
    ).split(',')

    # Environment
    ENVIRONMENT = os.getenv(
        'ENVIRONMENT',
        'prod'
    )

    # SNS topic for notifications
    SNS_TOPIC_ARN = os.getenv(
        'SNS_TOPIC_ARN',
        'arn:aws:sns:us-east-1:123456789012:datasync-notifications'
    )

    # AWS Region
    AWS_REGION = os.getenv(
        'AWS_REGION',
        'us-east-1'
    )

    # DataSync task naming
    TASK_NAME_PREFIX = os.getenv(
        'TASK_NAME_PREFIX',
        f'datasync-nas-to-s3-{ENVIRONMENT}'
    )

    # Logging
    LOG_LEVEL = os.getenv(
        'LOG_LEVEL',
        'INFO'
    )

    # DataSync task options
    DATASYNC_OPTIONS = {
        'VerifyMode': 'POINT_IN_TIME_CONSISTENT',  # Validate after copy
        'OverwriteMode': 'ALWAYS',  # Overwrite existing files
        'Atime': 'BEST_EFFORT',  # Preserve access time
        'Mtime': 'PRESERVE',  # Preserve modification time
        'Uid': 'NONE',  # Don't preserve UID
        'Gid': 'NONE',  # Don't preserve GID
        'PreserveDeletedFiles': False,  # Don't preserve deleted files
        'TransferMode': 'CHANGED',  # Only copy changed files
        'LogLevel': 'TRANSFER',
        'ObjectTags': 'NONE'
    }

    # Task scheduling
    TASK_TIMEOUT_SECONDS = int(os.getenv(
        'TASK_TIMEOUT_SECONDS',
        '3600'  # 1 hour default
    ))

    # Retry configuration
    MAX_RETRIES = int(os.getenv(
        'MAX_RETRIES',
        '3'
    ))

    RETRY_WAIT_SECONDS = int(os.getenv(
        'RETRY_WAIT_SECONDS',
        '30'
    ))

    # Parallel task configuration
    ENABLE_PARALLEL_TASKS = os.getenv(
        'ENABLE_PARALLEL_TASKS',
        'true'
    ).lower() == 'true'

    # Date format
    DATE_FORMAT = 'YYYY/MMDD'  # e.g., 2024/0804

    @classmethod
    def get_datatypes(cls) -> List[str]:
        """Get list of data types to copy"""
        return [dt.strip() for dt in cls.DATATYPES if dt.strip()]

    @classmethod
    def get_task_name(cls, datatype: str, date_str: str) -> str:
        """Generate task name"""
        return f'{cls.TASK_NAME_PREFIX}-{datatype}-{date_str}'

    @classmethod
    def get_nas_source_path(cls, datatype: str, date_str: str) -> str:
        """
        Generate NAS source path

        Example:
            Input: datatype='inventory', date_str='2024/0804'
            Output: '/mydata/prod/icm/datain/poolData/inventory/2024/0804'
        """
        return f'{cls.NAS_BASE_PATH}/{datatype}/{date_str}'

    @classmethod
    def get_s3_destination_path(cls, datatype: str, date_str: str) -> str:
        """
        Generate S3 destination path

        Example:
            Input: datatype='inventory', date_str='2024/0804'
            Output: '/poolData/inventory/2024/0804'
        """
        return f'{cls.S3_PREFIX}/{datatype}/{date_str}'


class LocalConfig(Config):
    """Configuration for local testing"""

    TASK_TIMEOUT_SECONDS = 300  # 5 minutes for testing
    MAX_RETRIES = 2
    RETRY_WAIT_SECONDS = 10


class DevConfig(Config):
    """Configuration for development environment"""

    ENVIRONMENT = 'dev'
    TASK_TIMEOUT_SECONDS = 1800  # 30 minutes
    LOG_LEVEL = 'DEBUG'


class ProdConfig(Config):
    """Configuration for production environment"""

    ENVIRONMENT = 'prod'
    TASK_TIMEOUT_SECONDS = 3600  # 1 hour
    LOG_LEVEL = 'INFO'


def get_config(env: str = None) -> Config:
    """Factory function to get appropriate config"""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'prod').lower()

    config_map = {
        'local': LocalConfig,
        'dev': DevConfig,
        'prod': ProdConfig,
    }

    config_class = config_map.get(env, ProdConfig)
    return config_class()
