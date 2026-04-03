#!/usr/bin/env python3
"""
AWS Monitoring System - Main Entry Point.

Usage:
    # Single prefix
    python main.py --config config/config.yaml --prefix uat-top
    python main.py --config config/config.yaml --prefix uat-bot

    # Multiple prefixes
    python main.py --config config/config.yaml --prefixes uat-top,uat-bot,prod-

    # Custom port and debug
    python main.py --config config/config.yaml --prefix uat-top --port 8080 --debug
"""

import sys
import signal
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import ConfigLoader
from utils.logger import get_logger
from utils.aws_session import AWSSessionManager
from utils.state_manager import FileStateManager
from cf_discovery import CloudFormationDiscovery
from daemon import MonitoringDaemon
from alerts.alert_manager import AlertManager
from failover.failover_manager import FailoverManager
from app import create_app

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

# Monitor mapping
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
                logger.info(f"Created monitor for: {service_name}")
            except Exception as e:
                logger.error(f"Failed to create monitor for {service_name}: {e}")

    return monitors


def discover_resources_multi(session_manager, config, stack_prefixes):
    """Discover resources from CloudFormation stacks with multiple prefixes."""
    logger.info(f"Discovering resources with stack prefixes: {stack_prefixes}")

    discovery = CloudFormationDiscovery(session_manager)

    # Get list of enabled services
    enabled_services = [
        name for name, monitor in MONITOR_CLASSES.items()
        if config.get_service_config(name).enabled
    ]

    # Aggregate resources from all prefixes
    aggregated_resources = {service: [] for service in enabled_services}

    for prefix in stack_prefixes:
        try:
            logger.info(f"Discovering resources with prefix: {prefix}")
            resources = discovery.discover_resources(prefix, enabled_services)

            # Merge results
            for service, resource_list in resources.items():
                aggregated_resources[service].extend(resource_list)

            logger.info(f"Prefix {prefix}: {sum(len(r) for r in resources.values())} resources")
        except Exception as e:
            logger.error(f"Error discovering resources with prefix {prefix}: {e}")

    # Log summary
    total_resources = sum(len(r) for r in aggregated_resources.values())
    logger.info(f"Total discovered: {total_resources} resources across {len(aggregated_resources)} service(s)")

    for service, resource_list in aggregated_resources.items():
        if resource_list:
            logger.info(f"  {service}: {len(resource_list)} resource(s)")

    return aggregated_resources


def discover_resources(session_manager, config, stack_prefix):
    """Discover resources from CloudFormation stacks (single prefix)."""
    return discover_resources_multi(session_manager, config, [stack_prefix])


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='AWS Monitoring System with CloudFormation Discovery'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--prefix',
        help='CloudFormation stack name prefix (e.g., uat-top, uat-bot)'
    )
    parser.add_argument(
        '--prefixes',
        help='Multiple stack prefixes separated by comma (e.g., uat-top,uat-bot,prod-)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port for Flask web server'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host for Flask web server'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable Flask debug mode'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AWS Monitoring System Starting")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info(f"Loading configuration from: {args.config}")
        config = ConfigLoader.load(args.config)

        # Determine stack prefixes (support multiple from CLI or config)
        if args.prefixes:
            # CLI --prefixes argument takes precedence
            stack_prefixes = [p.strip() for p in args.prefixes.split(',')]
            logger.info(f"Using stack prefixes from CLI: {stack_prefixes}")
        elif args.prefix:
            # CLI --prefix argument
            stack_prefixes = [args.prefix]
            logger.info(f"Using stack prefix from CLI: {args.prefix}")
        else:
            # Use config file settings
            stack_prefixes = config.cloudformation.stack_prefixes
            if len(stack_prefixes) > 1:
                logger.info(f"Using stack prefixes from config: {stack_prefixes}")
            else:
                logger.info(f"Using stack prefix from config: {stack_prefixes[0]}")

        # Create AWS session
        logger.info("Initializing AWS session")
        session_manager = AWSSessionManager(
            profile_name=config.aws.profile,
            region=config.aws.primary_region,
            endpoint_url='http://localhost:4566' if config.aws.localstack else None
        )

        # Create state manager
        state_manager = FileStateManager(config.state.file_path)

        # Create monitors for enabled services
        logger.info("Creating service monitors")
        monitors = create_monitors(session_manager, config)

        if not monitors:
            logger.error("No monitors were created. Check configuration.")
            sys.exit(1)

        # Discover resources from CloudFormation
        resource_map = discover_resources_multi(session_manager, config, stack_prefixes)

        if not resource_map or sum(len(r) for r in resource_map.values()) == 0:
            logger.warning("No resources discovered. Check CloudFormation stacks and permissions.")

        # Create alert manager
        logger.info("Initializing alert system")
        alert_manager = AlertManager(config.alerts, session_manager)

        # Create failover manager
        logger.info("Initializing failover system")
        failover_manager = FailoverManager(session_manager, config.failover)

        # Create and start monitoring daemon
        logger.info("Starting monitoring daemon")
        daemon = MonitoringDaemon(config.monitoring, monitors, alert_manager, state_manager)
        daemon.set_resource_map(resource_map)
        daemon.start()

        # Create Flask app
        logger.info("Creating Flask application")
        app = create_app(daemon, failover_manager)

        # Graceful shutdown handler
        def signal_handler(sig, frame):
            logger.info("\nShutdown signal received")
            daemon.stop()
            logger.info("AWS Monitoring System stopped")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run Flask app
        logger.info("=" * 60)
        logger.info(f"Starting Flask server on http://{args.host}:{args.port}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)

        app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
