"""
Utility Functions
Helper functions for logging, configuration, and file management
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Setup logging configuration"""

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create log filename with timestamp
    log_file = log_dir / f'failover_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger('FailoverSystem')
    logger.info(f"Logging initialized. Log file: {log_file}")

    return logger


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""

    with open(config_path, 'r') as f:
        config = json.load(f)

    return config


def save_log_entry(entry: Dict[str, Any], log_type: str):
    """Save log entry to JSON file"""

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Determine log file based on type
    if log_type == 'monitor':
        log_file = log_dir / 'monitor_log.jsonl'
    elif log_type == 'failover':
        log_file = log_dir / 'failover_log.jsonl'
    else:
        log_file = log_dir / 'system_log.jsonl'

    # Append to JSONL file
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def read_log_file(log_type: str) -> list:
    """Read log entries from JSON file"""

    log_dir = Path('logs')

    if log_type == 'monitor':
        log_file = log_dir / 'monitor_log.jsonl'
    elif log_type == 'failover':
        log_file = log_dir / 'failover_log.jsonl'
    else:
        log_file = log_dir / 'system_log.jsonl'

    if not log_file.exists():
        return []

    entries = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    return entries


def get_all_logs() -> Dict[str, list]:
    """Get all log types"""

    return {
        'monitor': read_log_file('monitor'),
        'failover': read_log_file('failover'),
        'system': read_log_file('system')
    }


def create_sample_config():
    """Create a sample configuration file"""

    sample_config = {
        "_comment": "AWS Failover System - Simple Configuration",
        "aws_profile": "default",
        "aws_region": "us-east-1",
        "tag_name": "production",
        "emr": {
            "bootstrap_repo": "https://github.com/your-org/emr-bootstrap-scripts.git",
            "bootstrap_branch": "main"
        }
    }

    with open('config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)

    print("Sample config.json created. Please update with your settings.")
    print("\nRequired settings:")
    print("  - aws_profile: Your AWS CLI profile name")
    print("  - aws_region: AWS region (e.g., us-east-1)")
    print("  - tag_name: Resource tag Name value to monitor")
    print("  - emr.bootstrap_repo: GitHub repo URL for EMR bootstrap scripts")
    print("\nAll other configurations are auto-discovered from your AWS resources!")


if __name__ == '__main__':
    # Create sample config if run directly
    create_sample_config()