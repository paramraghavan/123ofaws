"""
Simple logging utility for CLI and Lambda.

This is a minimal wrapper around Python's standard logging.
Both CLI and Lambda use this - no environment detection needed.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        A configured logging.Logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("This works in CLI and Lambda")
    """

    logger = logging.getLogger(name)

    # Only configure if not already done
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
