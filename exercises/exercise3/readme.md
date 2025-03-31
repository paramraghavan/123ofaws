
Here is the data processing pipeline using AWS services. 

## Lambda Handler (run_py_lambda)
This is the entry point Lambda function that:
- Takes a dictionary of parameters (query, index, datasetName, startDateTime)
- Gets a list of S3 URLs based on the dataset name and start date/time
- Passes these URLs to a Step Function for processing

## Step Function Definition
The Step Function:
- Uses a Map state to process each S3 URL sequentially
- For each URL, it publishes a message to an SNS topic
- Invokes a Lambda to submit an EMR job
- Waits for job completion by checking the job status
- Processes the next S3 URL after the current job completes, fails, or times out
- .asl.json for Amazon States Language (ASL) JSON definitions(.asl is optional)
- this is inlined into the cloudformation(cfm) template file.

## Job Trigger Lambda
This Lambda function:
- Is triggered when a message is received in the SQS queue
- Reads the S3 URL from the message
- Submits an EMR job using SSM Run Command
- Extracts the job ID from the SSM command output
- Returns the job ID to the Step Function

## Job Status Checker Lambda
This Lambda function:
- Takes a job ID as input
- Checks the status of the EMR job step
- Returns the job status to the Step Function

## CloudFormation Template
The CloudFormation template ties everything together and:
- Creates all necessary resources including IAM roles, Lambda functions, SNS topic, SQS queue
- Sets up the event source mapping between SQS and Lambda
- Creates the Step Functions state machine with the proper execution role
- Configures all necessary permissions

## How to Use This

1. Deploy the CloudFormation template with appropriate parameters:
   - DataBucketName: Your S3 bucket for data files
   - CodeBucketName: Your S3 bucket for code files
   - EmrClusterId: Your existing EMR cluster ID
   - SsmInstanceId: ID of an EC2 instance with permissions to submit EMR jobs

2. Upload your Lambda code to each Lambda function:
   - run_py_lambda.py
   - job_trigger_lambda.py
   - job_status_checker_lambda.py

3. Invoke the run_py_lambda function with the required parameters to start the data processing pipeline:
```json
{
  "query": "your-query",
  "index": "your-index",
  "datasetName": "your-dataset",
  "startDateTime": "2025-03-30T12:00:00"
}
```

The pipeline will then:
1. Get S3 URLs based on your dataset and date
2. Process each URL by submitting an EMR job
3. Monitor job completion and process results
4. Move on to the next URL only after the current job finishes
