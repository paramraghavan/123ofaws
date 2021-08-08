import datetime
import logging
import json
import json
import logging
import os
import time
import uuid
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REGION = os.environ['AWS_REGION']
BUCKET = os.environ['BUCKET']
FARGATE_CLUSTER = os.environ['ECS_CLUSTER_NAME']
FARGATE_TASK_DEF_NAME = os.environ['ECS_TASK_DEFINITION']
FARGATE_SUBNET_ID_1 = os.environ['ECS_TASK_VPC_SUBNET_1']
FARGATE_SUBNET_ID_2 = os.environ['ECS_TASK_VPC_SUBNET_2']
CONTAINER_NAME      = os.environ['CONTAINER_NAME']


def process(event, context):
    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info("File recently added at : " + str(current_time))
    # logger.info("Event : " + str(event))
    logger.info("s3 file  trigger event: " + json.dumps(event, indent=2))
    bucket_name = event['Records'][0]["s3"]["bucket"]["name"]
    # "key": "in/inputfile.txt"
    key = event['Records'][0]["s3"]["object"]["key"]
    # bucket_name = 'sample0012345'
    # key = 'in/inputfile.txt'
    message = f" bucket name: {bucket_name}, key: {key}"
    print(message)

    OUTPUT_KEY = f'out/outfile_{current_time}.txt'
    #in/inputfile.txt
    INPUT_FILE_NAME = key.split('/')[-1]

    print(f'output_key: {OUTPUT_KEY}, INPUT_FILE_NAME : {INPUT_FILE_NAME}')
    print(f'Invoking ECS/Task. CONTAINER_NAME: {CONTAINER_NAME}, FARGATE_TASK_DEF_NAME: {FARGATE_TASK_DEF_NAME}, FARGATE_CLUSTER: {FARGATE_CLUSTER}')
    client = boto3.client('ecs', region_name=REGION)
    response = client.run_task(
        cluster=FARGATE_CLUSTER,
        launchType='FARGATE',
        taskDefinition=FARGATE_TASK_DEF_NAME,
        count=1,
        platformVersion='LATEST',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    FARGATE_SUBNET_ID_1,
                ],
                'assignPublicIp': 'ENABLED'
            }
        },
        #S3_PATH=sample0012345 -e
        # INPUT_FILE_NAME=inputfile.txt -e OUTPUT_FILE_NAME=outfile.txt  -e AWS_REGION=us-east-
        overrides={
            'containerOverrides': [
                {
                    'name': CONTAINER_NAME,
                    'environment': [
                        {
                            'name': 'BUCKET_NAME',
                            'value': bucket_name
                        },
                        {
                            'name': 'INPUT_KEY',
                            'value': key
                        },
                        {
                            'name': 'OUTPUT_KEY',
                            'value': OUTPUT_KEY
                        },
                        {
                            'name': 'INPUT_FILE_NAME',
                            'value': INPUT_FILE_NAME
                        },
                    ],
                },
            ],
        },
    )
    print(' Invoking ECS/Task complete')
    print(f'response : {str(response)}')
    return str(response)



def remove(event, context):
    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info("File recently removed at : " + str(current_time))
    logger.info("Event : " + str(event))