#!/usr/bin/env python3
"""
AWS Cost Calculator Tool
A Python tool to compute AWS service costs for a given date range.
"""

import boto3
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError


class AWSCostCalculator:
    def __init__(self, profile_name: Optional[str] = None, region: str = 'us-east-1'):
        """
        Initialize the AWS Cost Calculator.

        Args:
            profile_name: AWS profile name (optional)
            region: AWS region (default: us-east-1)
        """
        try:
            if profile_name:
                session = boto3.Session(profile_name=profile_name)
                self.ce_client = session.client('ce', region_name=region)
            else:
                self.ce_client = boto3.client('ce', region_name=region)
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please configure your credentials.")

    def validate_date_format(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def get_cost_by_service(self, start_date: str, end_date: str,
                            granularity: str = 'MONTHLY') -> Dict:
        """
        Get AWS costs grouped by service for the specified date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Time granularity (DAILY, MONTHLY, YEARLY)

        Returns:
            Dictionary containing cost data by service
        """
        if not self.validate_date_format(start_date) or not self.validate_date_format(end_date):
            raise ValueError("Invalid date format. Use YYYY-MM-DD format.")

        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            return response
        except ClientError as e:
            raise Exception(f"Error fetching cost data: {e}")

    def get_cost_by_region(self, start_date: str, end_date: str,
                           granularity: str = 'MONTHLY') -> Dict:
        """
        Get AWS costs grouped by region for the specified date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Time granularity (DAILY, MONTHLY, YEARLY)

        Returns:
            Dictionary containing cost data by region
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ]
            )
            return response
        except ClientError as e:
            raise Exception(f"Error fetching cost data: {e}")

    def get_total_cost(self, start_date: str, end_date: str,
                       granularity: str = 'MONTHLY') -> Dict:
        """
        Get total AWS costs for the specified date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Time granularity (DAILY, MONTHLY, YEARLY)

        Returns:
            Dictionary containing total cost data
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UnblendedCost']
            )
            return response
        except ClientError as e:
            raise Exception(f"Error fetching cost data: {e}")

    def format_cost_data(self, cost_data: Dict, group_by: str = 'service') -> List[Dict]:
        """
        Format cost data for better readability.

        Args:
            cost_data: Raw cost data from AWS API
            group_by: Grouping type ('service', 'region', 'total')

        Returns:
            List of formatted cost records
        """
        formatted_data = []

        for result in cost_data['ResultsByTime']:
            time_period = result['TimePeriod']

            if group_by == 'total':
                # Handle total cost data (no grouping)
                total_cost = float(result['Total']['BlendedCost']['Amount'])
                formatted_data.append({
                    'Period': f"{time_period['Start']} to {time_period['End']}",
                    'Total_Cost': f"${total_cost:.2f}",
                    'Currency': result['Total']['BlendedCost']['Unit']
                })
            else:
                # Handle grouped data (by service or region)
                for group in result['Groups']:
                    group_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                    blended_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    unblended_cost = float(group['Metrics']['UnblendedCost']['Amount'])

                    formatted_data.append({
                        'Period': f"{time_period['Start']} to {time_period['End']}",
                        f'{group_by.title()}': group_name,
                        'Blended_Cost': f"${blended_cost:.2f}",
                        'Unblended_Cost': f"${unblended_cost:.2f}",
                        'Currency': group['Metrics']['BlendedCost']['Unit']
                    })

        return formatted_data

    def generate_cost_report(self, start_date: str, end_date: str,
                             granularity: str = 'MONTHLY',
                             output_format: str = 'json') -> str:
        """
        Generate a comprehensive cost report.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Time granularity (DAILY, MONTHLY, YEARLY)
            output_format: Output format ('json', 'csv', 'console')

        Returns:
            Formatted cost report
        """
        print(f"Generating cost report for {start_date} to {end_date}...")

        # Get cost data
        total_cost_data = self.get_total_cost(start_date, end_date, granularity)
        service_cost_data = self.get_cost_by_service(start_date, end_date, granularity)
        region_cost_data = self.get_cost_by_region(start_date, end_date, granularity)

        # Format data
        total_costs = self.format_cost_data(total_cost_data, 'total')
        service_costs = self.format_cost_data(service_cost_data, 'service')
        region_costs = self.format_cost_data(region_cost_data, 'region')

        report = {
            'report_period': f"{start_date} to {end_date}",
            'granularity': granularity,
            'total_costs': total_costs,
            'costs_by_service': service_costs,
            'costs_by_region': region_costs,
            'generated_at': datetime.now().isoformat()
        }

        if output_format == 'json':
            return json.dumps(report, indent=2)
        elif output_format == 'csv':
            return self._generate_csv_report(report)
        elif output_format == 'console':
            return self._generate_console_report(report)
        else:
            raise ValueError("Invalid output format. Use 'json', 'csv', or 'console'.")

    def _generate_csv_report(self, report: Dict) -> str:
        """Generate CSV format report."""
        csv_output = []

        # Total costs
        csv_output.append("TOTAL COSTS")
        csv_output.append("Period,Total_Cost,Currency")
        for cost in report['total_costs']:
            csv_output.append(f"{cost['Period']},{cost['Total_Cost']},{cost['Currency']}")

        csv_output.append("")

        # Service costs
        csv_output.append("COSTS BY SERVICE")
        csv_output.append("Period,Service,Blended_Cost,Unblended_Cost,Currency")
        for cost in report['costs_by_service']:
            csv_output.append(
                f"{cost['Period']},{cost['Service']},{cost['Blended_Cost']},{cost['Unblended_Cost']},{cost['Currency']}")

        return "\n".join(csv_output)

    def _generate_console_report(self, report: Dict) -> str:
        """Generate console-friendly report."""
        output = []
        output.append("=" * 60)
        output.append(f"AWS COST REPORT: {report['report_period']}")
        output.append("=" * 60)

        # Total costs
        output.append("\nTOTAL COSTS:")
        output.append("-" * 40)
        for cost in report['total_costs']:
            output.append(f"Period: {cost['Period']}")
            output.append(f"Total Cost: {cost['Total_Cost']} {cost['Currency']}")

        # Top services by cost
        output.append("\nTOP SERVICES BY COST:")
        output.append("-" * 40)
        service_costs = sorted(report['costs_by_service'],
                               key=lambda x: float(x['Blended_Cost'].replace('$', '')),
                               reverse=True)[:10]

        for i, cost in enumerate(service_costs, 1):
            output.append(f"{i:2d}. {cost['Service']}: {cost['Blended_Cost']}")

        return "\n".join(output)

    def save_report(self, report: str, filename: str):
        """Save report to file."""
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Report saved to {filename}")


def main():
    """Main function to run the cost calculator from command line."""
    parser = argparse.ArgumentParser(description='AWS Cost Calculator Tool')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--granularity', default='MONTHLY',
                        choices=['DAILY', 'MONTHLY', 'YEARLY'],
                        help='Time granularity')
    parser.add_argument('--format', default='console',
                        choices=['json', 'csv', 'console'],
                        help='Output format')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--region', default='us-east-1', help='AWS region')

    args = parser.parse_args()

    try:
        # Initialize calculator
        calculator = AWSCostCalculator(profile_name=args.profile, region=args.region)

        # Generate report
        report = calculator.generate_cost_report(
            start_date=args.start_date,
            end_date=args.end_date,
            granularity=args.granularity,
            output_format=args.format
        )

        # Output report
        if args.output:
            calculator.save_report(report, args.output)
        else:
            print(report)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())