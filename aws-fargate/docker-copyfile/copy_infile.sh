#!/bin/bash
set -x
#uncomment it when running from docker command line on your pc
#export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID_VAL}
#export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY_VAL}
#echo id - $AWS_ACCESS_KEY_ID
#echo key - $AWS_SECRET_ACCESS_KEY
echo "Copying s3 files via docker image ..."
echo $AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
# Get the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# From inside the container, you can query the credential endpoint
# with the following command:
curl 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
echo "Copying  S3 at ${BUCKET_NAME}  to ${INPUT_KEY} ..."
aws s3 cp s3://${BUCKET_NAME}/${INPUT_KEY}  . --region ${AWS_REGION}

