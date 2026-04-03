#!/usr/bin/env python3
"""
Manual Failover Script - Interactive resource selection and failover.

Run this on the SECONDARY region monitoring system when primary region is down.

Usage:
    python scripts/failover.py --config config/failover-secondary-config.yaml --prefix uat-

Workflow:
    1. Script checks primary region heartbeat
    2. Asks user if they want to failover
    3. Shows all resources in current state
    4. User selects which resources to failover (y/n for each)
    5. Script asks for final confirmation
    6. Script executes failover
    7. Shows results
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config_loader import ConfigLoader
from utils.logger import get_logger
from utils.aws_session import AWSSessionManager
from utils.state_manager import FileStateManager
from daemon import MonitoringDaemon
from failover.failover_manager import FailoverManager
from failover.interactive_failover import InteractiveFailover

# Import all monitors
from monitors.lambda_monitor import LambdaMonitor
from monitors.ec2_monitor import EC2Monitor
from monitors.s3_monitor import S3Monitor
from monitors.sqs_monitor import SQSMonitor
from monitors.sns_monitor import SNSMonitor
from monitors.emr_monitor import EMRMonitor
from monitors.autoscaling_monitor import AutoScalingMonitor
from monitors.cloudformation_monitor import CloudFormationMonitor
from monitors.ssm_monitor import SSMMonitor
from monitors.iam_monitor import IAMMonitor
from monitors.elbv2_monitor import ELBv2Monitor
from monitors.kms_monitor import KMSMonitor
from monitors.transfer_monitor import TransferMonitor
from monitors.snowflake_monitor import SnowflakeMonitor
from monitors.controlm_monitor import ControlMMonitor

logger = get_logger(__name__)

MONITOR_CLASSES = {
    'lambda': LambdaMonitor,
    'ec2': EC2Monitor,
    's3': S3Monitor,
    'sqs': SQSMonitor,
    'sns': SNSMonitor,
    'emr': EMRMonitor,
    'asg': AutoScalingMonitor,
    'cfn': CloudFormationMonitor,
    'ssm': SSMMonitor,
    'iam': IAMMonitor,
    'elbv2': ELBv2Monitor,
    'kms': KMSMonitor,
    'transfer': TransferMonitor,
    'snowflake': SnowflakeMonitor,
    'controlm': ControlMMonitor,
}


def create_monitors(session_manager, config):
    """Create monitor instances for enabled services."""
    monitors = {}

    for service_name, monitor_class in MONITOR_CLASSES.items():
        service_config = config.get_service_config(service_name)
        if service_config.enabled:
            try:
                monitors[service_name] = monitor_class(session_manager, service_config)
            except Exception as e:
                logger.error(f"Failed to create monitor for {service_name}: {e}")

    return monitors


def main():
    """Main failover script entry point."""
    parser = argparse.ArgumentParser(
        description='Manual Failover - Interactive resource selection'
    )
    parser.add_argument(
        '--config',
        default='config/failover-secondary-config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--prefix',
        help='CloudFormation stack name prefix'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("AWS MONITORING SYSTEM - MANUAL FAILOVER")
    print("=" * 70)

    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config = ConfigLoader.load(args.config)

        if config.failover.mode != 'secondary':
            print("\n❌ ERROR: This script must run on SECONDARY region monitoring system!")
            print(f"   Current mode: {config.failover.mode}")
            print(f"   Expected mode: secondary")
            sys.exit(1)

        # Create AWS session
        logger.info("Initializing AWS session")
        session_manager = AWSSessionManager(
            profile_name=config.aws.profile,
            region=config.aws.secondary_region,
            endpoint_url='http://localhost:4566' if config.aws.localstack else None
        )

        # Create state manager
        state_manager = FileStateManager(config.state.file_path)

        # Create monitors
        logger.info("Creating service monitors")
        monitors = create_monitors(session_manager, config)

        if not monitors:
            print("\n❌ ERROR: No monitors configured!")
            sys.exit(1)

        # Create monitoring daemon (for state tracking, not running background)
        daemon = MonitoringDaemon(config.monitoring, monitors, None, state_manager)

        # Run one health check to populate state
        print("\nChecking current resource state...")
        daemon._check_all_services()
        current_state = daemon.get_current_state()

        if not current_state:
            print("\n❌ ERROR: Could not retrieve resource state!")
            sys.exit(1)

        # Create failover manager
        failover_manager = FailoverManager(session_manager, config.failover)

        # Run interactive failover
        interactive = InteractiveFailover(failover_manager, daemon)
        success = interactive.run_interactive_failover()

        if success:
            print("\n✅ Failover completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Failover did not complete successfully")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
