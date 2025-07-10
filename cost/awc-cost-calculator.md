Using the AWS Cost Explorer API to retrieve billing data.

## Key Features:

1. **Cost Analysis by Service**: Groups costs by AWS service
2. **Cost Analysis by Region**: Groups costs by AWS region
3. **Total Cost Calculation**: Provides overall spending summaries
4. **Multiple Output Formats**: JSON, CSV, and console-friendly formats
5. **Flexible Time Granularity**: Daily, monthly, or yearly breakdowns
6. **Command-line Interface**: Easy to use from terminal

## Prerequisites:

```bash
# Install required packages
pip install boto3 pandas

# Configure AWS credentials (choose one method):
# 1. AWS CLI
aws configure

# 2. Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# 3. IAM roles (if running on EC2)
```

## Required AWS Permissions:

Your AWS account needs the following IAM permissions:

- `ce:GetCostAndUsage`
- `ce:GetUsageReport`

## Usage Examples:

```bash
# Basic usage - last 30 days
python aws_cost_calculator.py --start-date 2025-06-01 --end-date 2025-07-01

# With specific AWS profile
python aws_cost_calculator.py --start-date 2025-06-01 --end-date 2025-07-01 --profile my-profile

# Daily granularity with JSON output
python aws_cost_calculator.py --start-date 2025-06-01 --end-date 2025-07-01 --granularity DAILY --format json

# Save to file
python aws_cost_calculator.py --start-date 2025-06-01 --end-date 2025-07-01 --format csv --output costs.csv
```

## Programmatic Usage:

```python
from aws_cost_calculator import AWSCostCalculator

# Initialize
calculator = AWSCostCalculator(profile_name='default')

# Generate report
report = calculator.generate_cost_report(
    start_date='2025-06-01',
    end_date='2025-07-01',
    granularity='MONTHLY',
    output_format='json'
)

print(report)
```

## Features:

- **Error Handling**: Comprehensive error handling for API calls and authentication
- **Date Validation**: Ensures proper date format (YYYY-MM-DD)
- **Flexible Reporting**: Multiple output formats for different use cases
- **Top Services**: Automatically shows top 10 services by cost
- **Time Period Analysis**: Supports different time granularities

The tool uses the AWS Cost Explorer API to fetch accurate billing data and provides detailed breakdowns by service,
region, and time period. Make sure your AWS account has billing data available (costs are typically available 24-48
hours after usage).

## IAM Role for account used to run the script
Required IAM Permissions
**Basic Cost Explorer Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetUsageReport",
                "ce:GetCostCategories",
                "ce:GetReservationCoverage",
                "ce:GetReservationPurchaseRecommendation",
                "ce:GetReservationUtilization",
                "ce:GetSavingsPlansUtilization",
                "ce:GetSavingsPlansCoverage",
                "ce:ListCostCategoryDefinitions",
                "ce:GetCostAndUsageWithResources"
            ],
            "Resource": "*"
        }
    ]
}
```

**Minimal Permissions (for basic cost reporting):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetUsageReport"
            ],
            "Resource": "*"
        }
    ]
}
```

