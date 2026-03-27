"""
Logging utility for both CLI and Lambda.

Returns a configured logger that works in both environments.
"""

import logging
import os
import json
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for CLI or Lambda.

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
               If None, reads from LOG_LEVEL env var or defaults to INFO

    Returns:
        Configured logging.Logger instance
    """

    logger = logging.getLogger(name)

    # Determine log level
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO')

    logger.setLevel(getattr(logging, level.upper()))

    # Check if we're in Lambda
    in_lambda = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

    # Only add handler if not already configured
    if not logger.handlers:
        if in_lambda:
            # Lambda: use JSON structured logging
            handler = logging.StreamHandler()
            formatter = LambdaJsonFormatter()
        else:
            # CLI: use human-readable format
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class LambdaJsonFormatter(logging.Formatter):
    """
    Log formatter for Lambda that outputs JSON.

    CloudWatch Logs can parse JSON structured logs for better filtering/searching.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)
