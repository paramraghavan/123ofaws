#!/usr/bin/env python3
"""
AWS EMR Cost Calculator

This script calculates the cost of running EMR jobs using AWS Cost Explorer API.
It can filter costs by EMR cluster name, cluster ID, or both.

Requirements:
- boto3
- AWS credentials configured (via AWS CLI, IAM role, or environment variables)
- Cost Explorer API access (may require enabling in AWS Console)

Usage:
    python emr_cost_calculator.py --cluster-name "my-emr-cluster" --days 30
    python emr_cost_calculator.py --cluster-id "j-1234567890ABC" --start-date "2024-01-01" --end-date "2024-01-31"
"""

import boto3
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys


class EMRCostCalculator:
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize the EMR Cost Calculator

        Args:
            region_name: AWS region name
        """
        try:
            self.cost_explorer = boto3.client('ce', region_name=region_name)
            self.emr_client = boto3.client('emr', region_name=region_name)
            self.region = region_name
        except Exception as e:
            print(f"Error initializing AWS clients: {e}")
            sys.exit(1)

    def get_cluster_info(self, cluster_id: Optional[str] = None,
                         cluster_name: Optional[str] = None) -> List[Dict]:
        """
        Get EMR cluster information by ID or name

        Args:
            cluster_id: EMR cluster ID
            cluster_name: EMR cluster name

        Returns:
            List of cluster information dictionaries
        """
        clusters = []

        try:
            if cluster_id:
                # Get specific cluster by ID
                response = self.emr_client.describe_cluster(ClusterId=cluster_id)
                clusters.append({
                    'Id': response['Cluster']['Id'],
                    'Name': response['Cluster']['Name'],
                    'Status': response['Cluster']['Status']['State'],
                    'CreationDateTime': response['Cluster']['Status']['Timeline'].get('CreationDateTime'),
                    'EndDateTime': response['Cluster']['Status']['Timeline'].get('EndDateTime')
                })
            elif cluster_name:
                # List clusters and filter by name
                paginator = self.emr_client.get_paginator('list_clusters')

                for page in paginator.paginate():
                    for cluster in page['Clusters']:
                        if cluster['Name'] == cluster_name:
                            clusters.append({
                                'Id': cluster['Id'],
                                'Name': cluster['Name'],
                                'Status': cluster['Status']['State'],
                                'CreationDateTime': cluster['Status']['Timeline'].get('CreationDateTime'),
                                'EndDateTime': cluster['Status']['Timeline'].get('EndDateTime')
                            })

            return clusters

        except Exception as e:
            print(f"Error getting cluster information: {e}")
            return []

    def get_job_info(self, job_name: str, cluster_id: Optional[str] = None) -> List[Dict]:
        """
        Get EMR job/step information by name

        Args:
            job_name: EMR job/step name to search for
            cluster_id: Optional cluster ID to limit search scope

        Returns:
            List of job information dictionaries
        """
        jobs = []
        clusters_to_search = []

        try:
            if cluster_id:
                clusters_to_search = [cluster_id]
            else:
                # Get all clusters if no specific cluster provided
                paginator = self.emr_client.get_paginator('list_clusters')
                for page in paginator.paginate():
                    for cluster in page['Clusters']:
                        clusters_to_search.append(cluster['Id'])

            # Search for jobs/steps in clusters
            for cid in clusters_to_search:
                try:
                    # List steps for this cluster
                    step_paginator = self.emr_client.get_paginator('list_steps')
                    for page in step_paginator.paginate(ClusterId=cid):
                        for step in page['Steps']:
                            if job_name.lower() in step['Name'].lower():
                                # Get detailed step information
                                step_detail = self.emr_client.describe_step(
                                    ClusterId=cid,
                                    StepId=step['Id']
                                )

                                jobs.append({
                                    'ClusterId': cid,
                                    'StepId': step['Id'],
                                    'StepName': step['Name'],
                                    'Status': step['Status']['State'],
                                    'CreationDateTime': step['Status']['Timeline'].get('CreationDateTime'),
                                    'StartDateTime': step['Status']['Timeline'].get('StartDateTime'),
                                    'EndDateTime': step['Status']['Timeline'].get('EndDateTime'),
                                    'Config': step_detail['Step']['Config']
                                })
                except Exception as e:
                    # Skip clusters that can't be accessed or have no steps
                    continue

            return jobs

        except Exception as e:
            print(f"Error getting job information: {e}")
            return []

    def get_emr_costs(self, start_date: str, end_date: str,
                      cluster_id: Optional[str] = None,
                      cluster_name: Optional[str] = None,
                      job_name: Optional[str] = None) -> Dict:
        """
        Get EMR costs from Cost Explorer API

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            cluster_id: Optional EMR cluster ID for filtering
            cluster_name: Optional EMR cluster name for filtering
            job_name: Optional EMR job/step name for filtering

        Returns:
            Dictionary containing cost information
        """
        try:
            # Base filter for EMR service
            filters = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Elastic MapReduce']
                }
            }

            # Determine cluster IDs to filter by
            cluster_ids_to_filter = []

            # Start with cluster filtering if provided
            if cluster_id:
                cluster_ids_to_filter = [cluster_id]
            elif cluster_name:
                clusters = self.get_cluster_info(cluster_name=cluster_name)
                cluster_ids_to_filter = [cluster['Id'] for cluster in clusters]

            # If job name is provided, further filter or find clusters
            if job_name:
                if cluster_ids_to_filter:
                    # Job filtering within already identified clusters
                    job_cluster_ids = []
                    for cid in cluster_ids_to_filter:
                        jobs = self.get_job_info(job_name, cid)
                        if jobs:  # Only include clusters that actually ran this job
                            job_cluster_ids.append(cid)
                    cluster_ids_to_filter = job_cluster_ids
                    print(f"Found job '{job_name}' in {len(cluster_ids_to_filter)} of the specified clusters")
                else:
                    # Job filtering across all clusters
                    jobs = self.get_job_info(job_name)
                    cluster_ids_to_filter = list(set([job['ClusterId'] for job in jobs]))
                    print(f"Found {len(jobs)} jobs matching '{job_name}' across {len(cluster_ids_to_filter)} clusters")

            # Add cluster-specific filters if we have cluster IDs
            if cluster_ids_to_filter:
                cluster_filters = []

                for cid in cluster_ids_to_filter:
                    # Try multiple filter approaches for better coverage
                    cluster_filters.extend([
                        {
                            'Dimensions': {
                                'Key': 'RESOURCE_ID',
                                'Values': [cid],
                                'MatchOptions': ['EQUALS']
                            }
                        },
                        {
                            'Dimensions': {
                                'Key': 'USAGE_TYPE',
                                'Values': [cid],
                                'MatchOptions': ['CONTAINS']
                            }
                        }
                    ])

                if cluster_filters:
                    filters = {
                        'And': [
                            filters,
                            {'Or': cluster_filters}
                        ]
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

        if 'ResultsByTime' in cost_data:
            for result in cost_data['ResultsByTime']:
                date = result['TimePeriod']['Start']
                daily_total = 0.0

                for group in result.get('Groups', []):
                    service = group['Keys'][0] if len(group['Keys']) > 0 else 'Unknown'
                    usage_type = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'

                    metrics = group.get('Metrics', {})
                    cost = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                    usage = float(metrics.get('UsageQuantity', {}).get('Amount', 0))

                    daily_total += cost

                    # Track usage type costs
                    if usage_type not in usage_type_costs:
                        usage_type_costs[usage_type] = 0.0
                    usage_type_costs[usage_type] += cost

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

        return '\n'.join(breakdown)

    def run_cost_analysis(self, cluster_name: Optional[str] = None,
                          cluster_id: Optional[str] = None,
                          job_name: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          days: int = 30) -> None:
        """
        Run complete cost analysis for EMR cluster or job

        Args:
            cluster_name: EMR cluster name
            cluster_id: EMR cluster ID
            job_name: EMR job/step name
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

        print(f"\n=== EMR Cost Analysis ===")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Region: {self.region}")

        # Get job information if job name provided
        if job_name:
            print(f"\n=== Job Information ===")
            jobs = self.get_job_info(job_name, cluster_id)

            if jobs:
                for job in jobs:
                    print(f"Job Name: {job['StepName']}")
                    print(f"Step ID: {job['StepId']}")
                    print(f"Cluster ID: {job['ClusterId']}")
                    print(f"Status: {job['Status']}")
                    if job.get('CreationDateTime'):
                        print(f"Created: {job['CreationDateTime']}")
                    if job.get('StartDateTime'):
                        print(f"Started: {job['StartDateTime']}")
                    if job.get('EndDateTime'):
                        print(f"Ended: {job['EndDateTime']}")
                    print(f"Job Type: {job['Config'].get('Jar', 'N/A')}")
                    print("-" * 50)
            else:
                print(f"No jobs found matching '{job_name}'")
                return

        # Get cluster information if specified
        elif cluster_name or cluster_id:
            print(f"\n=== Cluster Information ===")
            clusters = self.get_cluster_info(cluster_id, cluster_name)

            if clusters:
                for cluster in clusters:
                    print(f"Cluster ID: {cluster['Id']}")
                    print(f"Cluster Name: {cluster['Name']}")
                    print(f"Status: {cluster['Status']}")
                    if cluster.get('CreationDateTime'):
                        print(f"Created: {cluster['CreationDateTime']}")
                    if cluster.get('EndDateTime'):
                        print(f"Ended: {cluster['EndDateTime']}")
                    print()
            else:
                print("No clusters found matching the criteria")
                return

        # Get cost data
        print("Fetching cost data...")
        cost_data = self.get_emr_costs(start_date, end_date, cluster_id, cluster_name, job_name)

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
            filename = f"emr_costs_{start_date}_{end_date}.json"
            with open(filename, 'w') as f:
                json.dump(cost_data, f, indent=2, default=str)
            print(f"\nRaw cost data saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate AWS EMR costs using Cost Explorer API'
    )

    # Cluster filtering (mutually exclusive)
    cluster_group = parser.add_mutually_exclusive_group()
    cluster_group.add_argument('--cluster-name', type=str,
                               help='EMR cluster name to filter costs')
    cluster_group.add_argument('--cluster-id', type=str,
                               help='EMR cluster ID to filter costs')

    # Job filtering (optional, can be combined with cluster filters)
    parser.add_argument('--job-name', type=str,
                        help='EMR job/step name to filter costs (can be combined with cluster filters)')

    parser.add_argument('--start-date', type=str,
                        help='Start date for cost analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='End date for cost analysis (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to look back (default: 30)')
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
    calculator = EMRCostCalculator(region_name=args.region)
    calculator.run_cost_analysis(
        cluster_name=args.cluster_name,
        cluster_id=args.cluster_id,
        job_name=args.job_name,
        start_date=args.start_date,
        end_date=args.end_date,
        days=args.days
    )


if __name__ == '__main__':
    """
        # 1. Cluster only (original functionality)
        python emr_cost_calculator.py --cluster-name "analytics-cluster"
        python emr_cost_calculator.py --cluster-id "j-1234567890ABC"
        
        # 2. Job only (searches all clusters)
        python emr_cost_calculator.py --job-name "data-processing"
        
        # 3. Cluster + Job (NEW - most precise filtering)
        python emr_cost_calculator.py --cluster-name "analytics-cluster" --job-name "data-processing"
        python emr_cost_calculator.py --cluster-id "j-1234567890ABC" --job-name "etl-pipeline"
        
        # 4. All EMR costs (no filters)
        python emr_cost_calculator.py --days 30
    
    """
    main()