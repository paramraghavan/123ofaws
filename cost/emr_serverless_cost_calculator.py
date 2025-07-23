#!/usr/bin/env python3
"""
AWS EMR Serverless Cost Calculator

This script calculates the cost of running EMR Serverless jobs using AWS Cost Explorer API.
It can filter costs by application ID, job name, or both.

Requirements:
- boto3
- AWS credentials configured (via AWS CLI, IAM role, or environment variables)
- Cost Explorer API access (may require enabling in AWS Console)

Usage:
    python emr_serverless_cost_calculator.py --job-name "data-processing" --days 30
    python emr_serverless_cost_calculator.py --application-id "00f1r2p0123456789" --start-date "2024-01-01" --end-date "2024-01-31"
    python emr_serverless_cost_calculator.py --job-name "ml-training" --application-id "00f1r2p0123456789"
"""

import boto3
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys


class EMRServerlessCostCalculator:
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize the EMR Serverless Cost Calculator

        Args:
            region_name: AWS region name
        """
        try:
            self.cost_explorer = boto3.client('ce', region_name=region_name)
            self.emr_serverless = boto3.client('emr-serverless', region_name=region_name)
            self.region = region_name
        except Exception as e:
            print(f"Error initializing AWS clients: {e}")
            sys.exit(1)

    def get_applications(self, application_id: Optional[str] = None) -> List[Dict]:
        """
        Get EMR Serverless applications

        Args:
            application_id: Optional specific application ID

        Returns:
            List of application information dictionaries
        """
        applications = []

        try:
            if application_id:
                # Get specific application
                response = self.emr_serverless.get_application(applicationId=application_id)
                app = response['application']
                applications.append({
                    'Id': app['id'],
                    'Name': app['name'],
                    'Type': app['type'],
                    'State': app['state'],
                    'CreatedAt': app['createdAt'],
                    'UpdatedAt': app['updatedAt'],
                    'ReleaseLabel': app['releaseLabel']
                })
            else:
                # List all applications
                paginator = self.emr_serverless.get_paginator('list_applications')
                for page in paginator.paginate():
                    for app in page['applications']:
                        applications.append({
                            'Id': app['id'],
                            'Name': app['name'],
                            'Type': app['type'],
                            'State': app['state'],
                            'CreatedAt': app['createdAt'],
                            'UpdatedAt': app['updatedAt'],
                            'ReleaseLabel': app['releaseLabel']
                        })

            return applications

        except Exception as e:
            print(f"Error getting application information: {e}")
            return []

    def get_job_runs(self, application_id: Optional[str] = None,
                     job_name: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> List[Dict]:
        """
        Get EMR Serverless job runs

        Args:
            application_id: Optional application ID to filter by
            job_name: Optional job name to filter by
            start_date: Optional start date for filtering job runs
            end_date: Optional end date for filtering job runs

        Returns:
            List of job run information dictionaries
        """
        job_runs = []
        applications_to_search = []

        try:
            # Determine which applications to search
            if application_id:
                applications_to_search = [application_id]
            else:
                # Get all applications if none specified
                apps = self.get_applications()
                applications_to_search = [app['Id'] for app in apps]

            # Convert date strings to datetime objects for filtering
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            # Search job runs in each application
            for app_id in applications_to_search:
                try:
                    paginator = self.emr_serverless.get_paginator('list_job_runs')

                    # Set up pagination parameters
                    paginate_kwargs = {'applicationId': app_id}
                    if start_dt:
                        paginate_kwargs['createdAtAfter'] = start_dt
                    if end_dt:
                        paginate_kwargs['createdAtBefore'] = end_dt

                    for page in paginator.paginate(**paginate_kwargs):
                        for job_run in page['jobRuns']:
                            # Filter by job name if specified
                            if job_name and job_name.lower() not in job_run['name'].lower():
                                continue

                            # Get detailed job run information
                            try:
                                job_detail = self.emr_serverless.get_job_run(
                                    applicationId=app_id,
                                    jobRunId=job_run['id']
                                )

                                job_info = job_detail['jobRun']
                                job_runs.append({
                                    'ApplicationId': app_id,
                                    'JobRunId': job_info['id'],
                                    'Name': job_info['name'],
                                    'State': job_info['state'],
                                    'CreatedAt': job_info['createdAt'],
                                    'UpdatedAt': job_info['updatedAt'],
                                    'StartedAt': job_info.get('stateDetails', {}).get('startedAt'),
                                    'EndedAt': job_info.get('stateDetails', {}).get('endedAt'),
                                    'ExecutionRole': job_info['executionRoleArn'],
                                    'JobDriver': job_info.get('jobDriver', {}),
                                    'ConfigurationOverrides': job_info.get('configurationOverrides', {}),
                                    'TotalResourceUtilization': job_info.get('totalResourceUtilization', {}),
                                    'TotalExecutionDurationSeconds': job_info.get('totalExecutionDurationSeconds'),
                                    'BilledResourceUtilization': job_info.get('billedResourceUtilization', {})
                                })
                            except Exception as e:
                                # Skip job runs that can't be accessed
                                continue

                except Exception as e:
                    # Skip applications that can't be accessed
                    continue

            return job_runs

        except Exception as e:
            print(f"Error getting job run information: {e}")
            return []

    def get_emr_serverless_costs(self, start_date: str, end_date: str,
                                 application_id: Optional[str] = None,
                                 job_name: Optional[str] = None) -> Dict:
        """
        Get EMR Serverless costs from Cost Explorer API

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            application_id: Optional EMR Serverless application ID
            job_name: Optional job name for filtering

        Returns:
            Dictionary containing cost information
        """
        try:
            # Base filter for EMR Serverless
            filters = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['EMR Serverless']
                }
            }

            # Get application IDs to filter by if job name is specified
            application_ids_to_filter = []

            if job_name:
                # Find applications that ran jobs with this name
                job_runs = self.get_job_runs(application_id, job_name, start_date, end_date)
                application_ids_to_filter = list(set([job['ApplicationId'] for job in job_runs]))
                print(
                    f"Found {len(job_runs)} job runs matching '{job_name}' across {len(application_ids_to_filter)} applications")
            elif application_id:
                application_ids_to_filter = [application_id]

            # Add application-specific filters if we have application IDs
            if application_ids_to_filter:
                app_filters = []

                for app_id in application_ids_to_filter:
                    app_filters.append({
                        'Dimensions': {
                            'Key': 'RESOURCE_ID',
                            'Values': [app_id],
                            'MatchOptions': ['CONTAINS']
                        }
                    })

                if app_filters:
                    if len(app_filters) == 1:
                        filters = {
                            'And': [filters, app_filters[0]]
                        }
                    else:
                        filters = {
                            'And': [filters, {'Or': app_filters}]
                        }

            # Query Cost Explorer
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'RESOURCE_ID'
                    }
                ],
                Filter=filters
            )

            return response

        except Exception as e:
            print(f"Error querying Cost Explorer: {e}")
            return {}

    def calculate_total_cost(self, cost_data: Dict) -> Tuple[float, float]:
        """
        Calculate total costs from Cost Explorer response

        Args:
            cost_data: Cost Explorer API response

        Returns:
            Tuple of (blended_cost, unblended_cost)
        """
        total_blended = 0.0
        total_unblended = 0.0

        if 'ResultsByTime' in cost_data:
            for result in cost_data['ResultsByTime']:
                for group in result.get('Groups', []):
                    metrics = group.get('Metrics', {})

                    blended = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                    unblended = float(metrics.get('UnblendedCost', {}).get('Amount', 0))

                    total_blended += blended
                    total_unblended += unblended

        return total_blended, total_unblended

    def format_cost_breakdown(self, cost_data: Dict) -> str:
        """
        Format cost data into a readable breakdown

        Args:
            cost_data: Cost Explorer API response

        Returns:
            Formatted string with cost breakdown
        """
        breakdown = []
        daily_costs = {}
        usage_type_costs = {}
        resource_costs = {}

        if 'ResultsByTime' in cost_data:
            for result in cost_data['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_total = 0.0

                for group in result.get('Groups', []):
                    service = group['Keys'][0] if len(group['Keys']) > 0 else 'Unknown'
                    usage_type = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'
                    resource_id = group['Keys'][2] if len(group['Keys']) > 2 else 'Unknown'

                    metrics = group.get('Metrics', {})
                    cost = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                    usage = float(metrics.get('UsageQuantity', {}).get('Amount', 0))

                    daily_total += cost

                    # Track usage type costs
                    if usage_type not in usage_type_costs:
                        usage_type_costs[usage_type] = 0.0
                    usage_type_costs[usage_type] += cost

                    # Track resource costs (applications)
                    if resource_id not in resource_costs and resource_id != 'Unknown':
                        resource_costs[resource_id] = 0.0
                    if resource_id != 'Unknown':
                        resource_costs[resource_id] += cost

                if daily_total > 0:
                    daily_costs[date] = daily_total

        # Format daily breakdown
        if daily_costs:
            breakdown.append("\n=== Daily Cost Breakdown ===")
            for date, cost in sorted(daily_costs.items()):
                breakdown.append(f"{date}: ${cost:.2f}")

        # Format usage type breakdown
        if usage_type_costs:
            breakdown.append("\n=== Cost by Usage Type ===")
            for usage_type, cost in sorted(usage_type_costs.items(),
                                           key=lambda x: x[1], reverse=True):
                if cost > 0:
                    breakdown.append(f"{usage_type}: ${cost:.2f}")

        # Format resource/application breakdown
        if resource_costs:
            breakdown.append("\n=== Cost by Application ===")
            for resource_id, cost in sorted(resource_costs.items(),
                                            key=lambda x: x[1], reverse=True):
                if cost > 0:
                    breakdown.append(f"{resource_id}: ${cost:.2f}")

        return '\n'.join(breakdown)

    def format_job_runs_summary(self, job_runs: List[Dict]) -> str:
        """
        Format job runs into a summary

        Args:
            job_runs: List of job run dictionaries

        Returns:
            Formatted string with job runs summary
        """
        if not job_runs:
            return "No job runs found"

        summary = []
        total_duration = 0
        state_counts = {}

        for job in job_runs:
            state = job['State']
            if state not in state_counts:
                state_counts[state] = 0
            state_counts[state] += 1

            if job.get('TotalExecutionDurationSeconds'):
                total_duration += job['TotalExecutionDurationSeconds']

        summary.append(f"\n=== Job Runs Summary ===")
        summary.append(f"Total Job Runs: {len(job_runs)}")

        if state_counts:
            summary.append("Job States:")
            for state, count in sorted(state_counts.items()):
                summary.append(f"  {state}: {count}")

        if total_duration > 0:
            hours = total_duration / 3600
            summary.append(f"Total Execution Time: {hours:.2f} hours")

        return '\n'.join(summary)

    def run_cost_analysis(self, application_id: Optional[str] = None,
                          job_name: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          days: int = 30) -> None:
        """
        Run complete cost analysis for EMR Serverless

        Args:
            application_id: EMR Serverless application ID
            job_name: Job name to filter by
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            days: Number of days to look back if dates not provided
        """
        # Set date range
        if not start_date or not end_date:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days)
            start_date = start_dt.strftime('%Y-%m-%d')
            end_date = end_dt.strftime('%Y-%m-%d')

        print(f"\n=== EMR Serverless Cost Analysis ===")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Region: {self.region}")

        # Get application information
        if application_id:
            print(f"\n=== Application Information ===")
            applications = self.get_applications(application_id)

            if applications:
                for app in applications:
                    print(f"Application ID: {app['Id']}")
                    print(f"Application Name: {app['Name']}")
                    print(f"Type: {app['Type']}")
                    print(f"State: {app['State']}")
                    print(f"Release Label: {app['ReleaseLabel']}")
                    print(f"Created: {app['CreatedAt']}")
                    print()
            else:
                print("Application not found")
                return

        # Get job run information
        if job_name or application_id:
            print("Fetching job run information...")
            job_runs = self.get_job_runs(application_id, job_name, start_date, end_date)

            if job_runs:
                print(f"\n=== Job Run Details ===")
                for job in job_runs[:10]:  # Show first 10 jobs
                    print(f"Job Name: {job['Name']}")
                    print(f"Job Run ID: {job['JobRunId']}")
                    print(f"Application ID: {job['ApplicationId']}")
                    print(f"State: {job['State']}")
                    print(f"Created: {job['CreatedAt']}")
                    if job.get('StartedAt'):
                        print(f"Started: {job['StartedAt']}")
                    if job.get('EndedAt'):
                        print(f"Ended: {job['EndedAt']}")
                    if job.get('TotalExecutionDurationSeconds'):
                        hours = job['TotalExecutionDurationSeconds'] / 3600
                        print(f"Duration: {hours:.2f} hours")
                    print("-" * 50)

                if len(job_runs) > 10:
                    print(f"... and {len(job_runs) - 10} more job runs")

                # Show job runs summary
                summary = self.format_job_runs_summary(job_runs)
                print(summary)

        # Get cost data
        print("\nFetching cost data...")
        cost_data = self.get_emr_serverless_costs(start_date, end_date, application_id, job_name)

        if not cost_data:
            print("No cost data retrieved")
            return

        # Calculate and display costs
        blended_cost, unblended_cost = self.calculate_total_cost(cost_data)

        print(f"\n=== Cost Summary ===")
        print(f"Total Blended Cost: ${blended_cost:.2f}")
        print(f"Total Unblended Cost: ${unblended_cost:.2f}")

        # Display detailed breakdown
        breakdown = self.format_cost_breakdown(cost_data)
        if breakdown:
            print(breakdown)

        # Save raw data if requested
        if args.save_raw:
            filename = f"emr_serverless_costs_{start_date}_{end_date}.json"
            with open(filename, 'w') as f:
                json.dump(cost_data, f, indent=2, default=str)
            print(f"\nRaw cost data saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate AWS EMR Serverless costs using Cost Explorer API'
    )

    # Filtering options
    parser.add_argument('--application-id', type=str,
                        help='EMR Serverless application ID to filter costs')
    parser.add_argument('--job-name', type=str,
                        help='Job name to filter costs (can be combined with application-id)')

    # Date range options
    parser.add_argument('--start-date', type=str,
                        help='Start date for cost analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='End date for cost analysis (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to look back (default: 30)')

    # Other options
    parser.add_argument('--region', type=str, default='us-east-1',
                        help='AWS region (default: us-east-1)')
    parser.add_argument('--save-raw', action='store_true',
                        help='Save raw cost data to JSON file')

    global args
    args = parser.parse_args()

    # Validate date format if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print("Error: start-date must be in YYYY-MM-DD format")
            sys.exit(1)

    if args.end_date:
        try:
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print("Error: end-date must be in YYYY-MM-DD format")
            sys.exit(1)

    # Initialize calculator and run analysis
    calculator = EMRServerlessCostCalculator(region_name=args.region)
    calculator.run_cost_analysis(
        application_id=args.application_id,
        job_name=args.job_name,
        start_date=args.start_date,
        end_date=args.end_date,
        days=args.days
    )

"""
Key Differences from Traditional EMR:

    Applications vs Clusters: EMR Serverless uses applications instead of clusters
    Job Runs: Individual job executions within applications
    Serverless Billing: Pay-per-use model with different cost attribution
    Resource Utilization: Tracks actual vs billed resource usage
    
    # Find costs for all EMR Serverless usage (last 30 days)
    python emr_serverless_cost_calculator.py
    
    # Filter by specific application
    python emr_serverless_cost_calculator.py --application-id "00f1r2p0123456789"
    
    # Filter by job name (searches all applications)
    python emr_serverless_cost_calculator.py --job-name "data-processing"
    
    # Combined filtering - specific job in specific application
    python emr_serverless_cost_calculator.py --application-id "00f1r2p0123456789" --job-name "ml-training"
    
    # Custom date range
    python emr_serverless_cost_calculator.py --job-name "etl-pipeline" --start-date "2024-01-01" --end-date "2024-01-31"
    
    # Last 7 days in specific region
    python emr_serverless_cost_calculator.py --job-name "analytics" --days 7 --region "us-west-2"

"""

if __name__ == '__main__':
    main()