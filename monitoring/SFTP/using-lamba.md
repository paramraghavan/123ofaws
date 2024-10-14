To add monitoring to a third-party SFTP servers using AWS, you can set up a solution using AWS Lambda,
Amazon CloudWatch, and AWS Systems Manager Parameter Store. Here's an approach to accomplish this:

1. Set up an AWS Lambda function:

```python
import paramiko
import boto3
from datetime import datetime
import os


def lambda_handler(event, context):
    ssm = boto3.client('ssm')
    cloudwatch = boto3.client('cloudwatch')

    # Retrieve SFTP credentials from Parameter Store
    hostname = ssm.get_parameter(Name='/sftp/hostname', WithDecryption=True)['Parameter']['Value']
    username = ssm.get_parameter(Name='/sftp/username', WithDecryption=True)['Parameter']['Value']
    password = ssm.get_parameter(Name='/sftp/password', WithDecryption=True)['Parameter']['Value']

    try:
        # Attempt to connect to the SFTP server
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=username, password=password)

            # If connection is successful, check for new files
            with ssh.open_sftp() as sftp:
                files = sftp.listdir()
                today = datetime.now().strftime('%Y-%m-%d')
                new_files = [f for f in files if f.startswith(today)]

                if not new_files:
                    # No new files for today, send alert
                    cloudwatch.put_metric_data(
                        Namespace='BlacknightSFTP',
                        MetricData=[
                            {
                                'MetricName': 'NoNewFiles',
                                'Value': 1,
                                'Unit': 'Count'
                            },
                        ]
                    )
                else:
                    # Reset the metric if files are found
                    cloudwatch.put_metric_data(
                        Namespace='BlacknightSFTP',
                        MetricData=[
                            {
                                'MetricName': 'NoNewFiles',
                                'Value': 0,
                                'Unit': 'Count'
                            },
                        ]
                    )

        # If we reach here, connection was successful
        cloudwatch.put_metric_data(
            Namespace='BlacknightSFTP',
            MetricData=[
                {
                    'MetricName': 'ConnectionStatus',
                    'Value': 1,
                    'Unit': 'Count'
                },
            ]
        )

    except Exception as e:
        # If an exception occurs, log it and send an alert
        print(f"Error: {str(e)}")
        cloudwatch.put_metric_data(
            Namespace='BlacknightSFTP',
            MetricData=[
                {
                    'MetricName': 'ConnectionStatus',
                    'Value': 0,
                    'Unit': 'Count'
                },
            ]
        )

    return {
        'statusCode': 200,
        'body': 'Monitoring check completed'
    }

```

This Lambda function does the following:

- Retrieves SFTP credentials from AWS Systems Manager Parameter Store
- Attempts to connect to the SFTP server
- If successful, checks for new files for the current day
- Sends metrics to CloudWatch based on connection status and presence of new files

2. Set up CloudWatch Alarms:

Create two CloudWatch Alarms:

a. For SFTP connection errors:

- Metric: ConnectionStatus
- Condition: ConnectionStatus = 0
- Period: 300 seconds (5 minutes)
- Evaluation periods: 1

b. For no new files:

- Metric: NoNewFiles
- Condition: NoNewFiles = 1
- Period: 86400 seconds (24 hours)
- Evaluation periods: 1

3. Create a CloudWatch Events rule to trigger the Lambda function every 5 minutes.

4. Set up IAM roles and permissions:

- Lambda execution role with permissions to access Systems Manager Parameter Store and publish CloudWatch metrics
- CloudWatch Events permission to invoke the Lambda function

5. Store SFTP credentials securely:
   Use AWS Systems Manager Parameter Store to securely store the SFTP server credentials (hostname, username, password).

To implement this solution:

1. Create the Lambda function using the provided code.
2. Set up the CloudWatch Alarms as described.
3. Create a CloudWatch Events rule to trigger the Lambda function every 5 minutes.
4. Configure the necessary IAM roles and permissions.
5. Store the SFTP credentials in Systems Manager Parameter Store.

This setup will monitor the SFTP server connection every 5 minutes and check for new files daily. It will alert you via
CloudWatch Alarms if there are connection issues or if no new files arrive for the day.

Would you like me to elaborate on any specific part of this solution?