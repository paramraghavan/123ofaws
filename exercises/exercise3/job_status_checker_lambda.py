import json
import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
emr_client = boto3.client('emr')


def lambda_handler(event, context):
    """
    Lambda function to check the status of an EMR job/step
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Extract the job ID
        job_id = event.get('jobId')

        if not job_id:
            raise ValueError("No job ID provided")

        # Get the EMR cluster ID from environment variables
        cluster_id = os.environ.get('EMR_CLUSTER_ID')

        # Check the status of the step
        response = emr_client.describe_step(
            ClusterId=cluster_id,
            StepId=job_id
        )

        step = response.get('Step', {})
        status = step.get('Status', {}).get('State', 'UNKNOWN')

        logger.info(f"Job {job_id} status: {status}")

        # Return the current status
        return {
            'statusCode': 200,
            'jobId': job_id,
            'status': status,
            'details': step
        }

    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }