#!/usr/bin/env python3
"""
AWS Failover Monitoring and Recovery System
Main entry point for monitoring and failover operations
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import boto3
from monitors import (
    EC2Monitor, EMRMonitor, LambdaMonitor,
    AutoScalingMonitor, SnowflakeMonitor, TokenMonitor
)
from failover import (
    EC2Failover, EMRFailover, LambdaFailover,
    AutoScalingFailover, TokenFailover
)
from utils import setup_logging, load_config, save_log_entry, create_sample_config

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class FailoverOrchestrator:
    """Orchestrates monitoring and failover operations"""

    def __init__(self, profile_name: str, tag_name: str, region: str, config: Dict[str, Any]):
        self.profile_name = profile_name
        self.tag_name = tag_name
        self.region = region
        self.config = config

        # Create session with region if specified
        session_params = {'profile_name': profile_name}
        if region:
            session_params['region_name'] = region

        self.session = boto3.Session(**session_params)
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.now()

        # Initialize monitors
        self.monitors = {
            'ec2': EC2Monitor(self.session, tag_name),
            'emr': EMRMonitor(self.session, tag_name),
            'lambda': LambdaMonitor(self.session, tag_name),
            'autoscaling': AutoScalingMonitor(self.session, tag_name),
            'snowflake': SnowflakeMonitor(config.get('snowflake', {})),
            'token': TokenMonitor(config.get('token', {}))
        }

        # Initialize failover handlers
        self.failover_handlers = {
            'ec2': EC2Failover(self.session, config),
            'emr': EMRFailover(self.session, config),
            'lambda': LambdaFailover(self.session, config),
            'autoscaling': AutoScalingFailover(self.session, config),
            'token': TokenFailover(config.get('token', {}))
        }

    def monitor(self) -> List[Dict[str, Any]]:
        """Monitor all configured resources"""
        self.logger.info("Starting monitoring phase...")
        all_statuses = []

        for resource_type, monitor in self.monitors.items():
            try:
                self.logger.info(f"Monitoring {resource_type}...")
                statuses = monitor.check_status()

                for status in statuses:
                    status['script_start_time'] = self.start_time.isoformat()
                    status['resource_type'] = resource_type
                    status['aws_profile'] = self.profile_name
                    status['aws_region'] = self.region or 'default'
                    all_statuses.append(status)

                    # Save to log file
                    save_log_entry(status, 'monitor')

                    # Log to console
                    self.logger.info(
                        f"{resource_type.upper()}: {status.get('resource_id', 'N/A')} "
                        f"({status.get('tag_name', 'N/A')}) - Status: {status.get('status', 'UNKNOWN')}"
                    )

            except Exception as e:
                self.logger.error(f"Error monitoring {resource_type}: {str(e)}", exc_info=True)
                error_status = {
                    'script_start_time': self.start_time.isoformat(),
                    'resource_type': resource_type,
                    'resource_id': 'ERROR',
                    'tag_name': self.tag_name,
                    'status': 'ERROR',
                    'error': str(e),
                    'aws_profile': self.profile_name,
                    'aws_region': self.region or 'default'
                }
                all_statuses.append(error_status)
                save_log_entry(error_status, 'monitor')

        self.logger.info(f"Monitoring completed. Found {len(all_statuses)} resources.")
        return all_statuses

    def failover(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute failover for stopped/terminated resources"""
        self.logger.info("Starting failover phase...")
        failover_results = []

        # Filter resources that need failover
        needs_failover = [
            r for r in resources
            if r.get('status') in ['stopped', 'terminated', 'INVALID', 'DOWN', 'FAILED', 'SCALING_ISSUE']
        ]

        self.logger.info(f"Found {len(needs_failover)} resources needing failover")

        for resource in needs_failover:
            resource_type = resource['resource_type']

            try:
                if resource_type in self.failover_handlers:
                    self.logger.info(
                        f"Executing failover for {resource_type}: {resource.get('resource_id')}"
                    )

                    handler = self.failover_handlers[resource_type]
                    result = handler.execute(resource)

                    result['script_start_time'] = self.start_time.isoformat()
                    result['aws_profile'] = self.profile_name
                    result['aws_region'] = self.region or 'default'
                    failover_results.append(result)

                    # Save to log file
                    save_log_entry(result, 'failover')

                    # Log result
                    self.logger.info(
                        f"Failover result for {resource_type} "
                        f"{resource.get('resource_id')}: {result.get('result', 'UNKNOWN')}"
                    )
                else:
                    self.logger.warning(
                        f"No failover handler for {resource_type}: {resource.get('resource_id')}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error during failover for {resource_type} "
                    f"{resource.get('resource_id')}: {str(e)}",
                    exc_info=True
                )
                error_result = {
                    'script_start_time': self.start_time.isoformat(),
                    'resource_type': resource_type,
                    'resource_id': resource.get('resource_id'),
                    'result': 'ERROR',
                    'error': str(e),
                    'aws_profile': self.profile_name,
                    'aws_region': self.region or 'default'
                }
                failover_results.append(error_result)
                save_log_entry(error_result, 'failover')

        self.logger.info(f"Failover completed. Processed {len(failover_results)} resources.")
        return failover_results


def main():
    parser = argparse.ArgumentParser(
        description='AWS Resource Monitoring and Failover System'
    )
    parser.add_argument(
        '--profile',
        help='AWS profile name (overrides config file)'
    )
    parser.add_argument(
        '--tag-name',
        help='Resource tag Name to filter resources (overrides config file)'
    )
    parser.add_argument(
        '--region',
        help='AWS region (overrides config file)'
    )
    parser.add_argument(
        '--mode',
        choices=['monitor', 'failover', 'both'],
        default='both',
        help='Operation mode: monitor only, failover only, or both'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger = logging.getLogger(__name__)
        logger.warning(f"Config file {args.config} not found. Creating default config...")
        create_sample_config()
        logger.info("Please edit config.json and run again.")
        sys.exit(0)

    # Get profile, region, and tag_name from args or config
    profile = args.profile or config.get('aws_profile')
    tag_name = args.tag_name or config.get('tag_name')
    region = args.region or config.get('aws_region')

    if not profile or not tag_name:
        print("Error: AWS profile and tag name are required.")
        print("Either provide them via command line or set them in config.json:")
        print("  --profile <profile> --tag-name <tag>")
        print("  OR edit config.json with 'aws_profile' and 'tag_name'")
        sys.exit(1)

    # Setup logging
    logger = setup_logging(args.log_level)
    logger.info("=" * 80)
    logger.info(f"AWS Failover System started at {datetime.now()}")
    logger.info(f"Profile: {profile}, Tag: {tag_name}, Region: {region or 'default'}, Mode: {args.mode}")
    logger.info("=" * 80)

    # Initialize orchestrator
    orchestrator = FailoverOrchestrator(profile, tag_name, region, config)

    # Execute based on mode
    try:
        if args.mode in ['monitor', 'both']:
            monitor_results = orchestrator.monitor()

            if args.mode == 'both':
                logger.info("\n" + "=" * 80)
                orchestrator.failover(monitor_results)

        elif args.mode == 'failover':
            # In failover-only mode, we still need to monitor first to know what to failover
            logger.info("Running monitor to identify resources for failover...")
            monitor_results = orchestrator.monitor()
            logger.info("\n" + "=" * 80)
            orchestrator.failover(monitor_results)

        logger.info("=" * 80)
        logger.info("Operation completed successfully")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()