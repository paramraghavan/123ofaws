import json
import boto3
import os
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sfn_client = boto3.client('stepfunctions')
s3_client = boto3.client('s3')


def get_s3_urls(dataset_name, start_datetime):
    """
    Get list of S3 URLs based on dataset name and start datetime
    Returns a list of dictionaries with bucket, key_prefix, and filename
    """
    # This is a placeholder - implement your specific logic to find S3 URLs
    # based on dataset_name and start_datetime
    bucket = os.environ.get('DATA_BUCKET')
    key_prefix = f"{dataset_name}/{start_datetime.strftime('%Y/%m/%d/%H')}"

    # List objects in the bucket with the given prefix
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=key_prefix
    )

    s3_urls = []
    if 'Contents' in response:
        for obj in response['Contents']:
            s3_urls.append({
                'bucket': bucket,
                'key_prefix': os.path.dirname(obj['Key']),
                'filename': os.path.basename(obj['Key'])
            })

    return s3_urls


def run_py_lambda(event, context):
    """
    Main Lambda handler function that processes the query and starts the Step Function
    """
    try:
        # Extract parameters from the event
        query = event.get('query')
        index = event.get('index')
        dataset_name = event.get('datasetName')
        start_datetime_str = event.get('startDateTime')

        # Convert string to datetime object
        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%S')

        # Get the list of S3 URLs
        s3_urls = get_s3_urls(dataset_name, start_datetime)

        if not s3_urls:
            return {
                'statusCode': 404,
                'body': json.dumps('No files found for the given parameters')
            }

        # Start the Step Function execution with the S3 URLs
        step_function_arn = os.environ.get('STEP_FUNCTION_ARN')
        execution_input = {
            'query': query,
            'index': index,
            'datasetName': dataset_name,
            'startDateTime': start_datetime_str,
            's3_urls': s3_urls
        }

        response = sfn_client.start_execution(
            stateMachineArn=step_function_arn,
            input=json.dumps(execution_input)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Step Function execution started successfully',
                'executionArn': response['executionArn']
            })
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }