pass dictionary of parameters query, index, datasetname, start data/time to Lambda handler, run_py_lambda
lambda handlers gets list of s3 urls(bucket+key-prefix+filename) and passes it to a step function
sten fucntion takes one s3 url(bucket+key-prefix+filename) list and adds it sns topic
this gets added to sqs queue
the sqs queue triggers lambda - job_trigger_lambda
the job_trigger_lambda read the s3 url and submit s EMR job using ssm command
the job_trigger_lambda reads the out from ssm command and get handle to jobId
the lambda looks for ssm command output for string "jobID"
the retuen this jobId to step function
teh step fucntion waits for this jobID to complete using a python function to check for jobs status Success or failure
once the job is complete, failed or timeout,
the steps function processes the next job
Create python and aws code for above