#!/bin/bash
set -x
echo "Copying ${INPUT_FILE_NAME} to S3 at ${BUCKET_NAME}/${OUTPUT_KEY} ..."
aws s3 cp ./${INPUT_FILE_NAME} s3://${BUCKET_NAME}/${OUTPUT_KEY} --region ${AWS_REGION}

