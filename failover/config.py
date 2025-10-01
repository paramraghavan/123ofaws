import os


class Config:
    """Configuration settings for AWS Failover Manager"""

    # AWS Settings
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    # Logging Settings
    LOG_DIR = 'logs'
    LOG_FILE = os.path.join(LOG_DIR, 'failover.log')
    STATUS_LOG_FILE = os.path.join(LOG_DIR, 'status.jsonl')
    FAILOVER_LOG_FILE = os.path.join(LOG_DIR, 'failover.jsonl')

    # Flask Settings
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    DEBUG = True

    # Pagination
    LOGS_PER_PAGE = 50

    @staticmethod
    def init_app():
        """Initialize application directories"""
        os.makedirs(Config.LOG_DIR, exist_ok=True)