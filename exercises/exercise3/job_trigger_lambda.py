import json
import boto3
import os
import logging
import re

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
ssm_client = boto3.client('ssm')


def parse_job_id(output):
    """
    Parse the EMR job ID from the SSM command output
    """
    job_id_pattern = r'jobId["\s:]+([a-zA-Z0-9-]+)'
    match = re.search(job_id_pattern, output)
    if match:
        return match.group(1)
    return None


def lambda_handler(event, context):
    """
    Lambda function that reads S3 URL from SQS and submits an EMR job using SSM
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Extract S3 URL details
        s3_url = event.get('s3_url', {})
        bucket = s3_url.get('bucket')
        key_prefix = s3_url.get('key_prefix')
        filename = s3_url.get('filename')

        # Extract other parameters
        query = event.get('query')
        index = event.get('index')
        dataset_name = event.get('datasetName')

        # Form the full S3 path
        s3_path = f"s3://{bucket}/{key_prefix}/{filename}"
        logger.info(f"Processing S3 path: {s3_path}")

        # Prepare the EMR job submission command
        # Customize this command based on your EMR job requirements
        emr_command = f"""
        aws emr add-steps \
        --cluster-id {os.environ.get('EMR_CLUSTER_ID')} \
        --steps Type=Spark,Name="Process {dataset_name}",ActionOnFailure=CONTINUE,Args=[\
        --class,org.example.DataProcessor,\
        --deploy-mode,cluster,\
        s3://{os.environ.get('CODE_BUCKET')}/spark-job.jar,\
        --input,{s3_path},\
        --query,"{query}",\
        --index,{index},\
        --dataset,{dataset_name}\
        ]
        """

        # Run the command via SSM on an instance with proper permissions
        instance_id = os.environ.get('SSM_INSTANCE_ID')
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [emr_command]
            }
        )

        command_id = response['Command']['CommandId']
        logger.info(f"SSM Command ID: {command_id}")

        # Wait for the command to complete and get the output
        waiter = ssm_client.get_waiter('command_executed')
        waiter.wait(
            CommandId=command_id,
            InstanceId=instance_id
        )

        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )

        # Check the command status
        if output['Status'] != 'Success':
            raise Exception(f"SSM command failed: {output['StatusDetails']}")

        # Extract the job ID from the output
        command_output = output['StandardOutputContent']
        job_id = parse_job_id(command_output)

        if not job_id:
            raise Exception("Could not extract job ID from command output")

        logger.info(f"Successfully submitted EMR job with ID: {job_id}")

        return {
            'statusCode': 200,
            'jobId': job_id,
            's3Path': s3_path
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }