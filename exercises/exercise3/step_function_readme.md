
## Input to the State Machine

When the `run_py_lambda` invokes the Step Function, it passes this input:

```json
{
  "query": "your-query-string",
  "index": "your-index-value",
  "datasetName": "your-dataset-name",
  "startDateTime": "2025-03-30T12:00:00",
  "s3_urls": [
    {
      "bucket": "your-data-bucket",
      "key_prefix": "your-dataset-name/2025/03/30/12",
      "filename": "data1.csv"
    },
    {
      "bucket": "your-data-bucket",
      "key_prefix": "your-dataset-name/2025/03/30/12",
      "filename": "data2.csv"
    }
  ]
}
```

## Map State: ProcessS3Urls

### Input
The entire state machine input above.

### Output
The Map state outputs an array of results from processing each S3 URL.

## For Each S3 URL in the Map:

### 1. PublishToSNSTopic

#### Input
An individual S3 URL object from the array:
```json
{
  "bucket": "your-data-bucket",
  "key_prefix": "your-dataset-name/2025/03/30/12",
  "filename": "data1.csv"
}
```

#### Output
Same as input (passes through).

### 2. SubmitEMRJob

#### Input
The S3 URL object plus execution context parameters:
```json
{
  "s3_url": {
    "bucket": "your-data-bucket",
    "key_prefix": "your-dataset-name/2025/03/30/12",
    "filename": "data1.csv"
  },
  "query": "your-query-string",
  "index": "your-index-value",
  "datasetName": "your-dataset-name"
}
```

#### Output
The Lambda response is stored in `$.jobDetails`:
```json
{
  "s3_url": { ... },
  "jobDetails": {
    "Payload": {
      "statusCode": 200,
      "jobId": "s-1234ABCD5678EFGH",
      "s3Path": "s3://your-data-bucket/your-dataset-name/2025/03/30/12/data1.csv"
    }
  }
}
```

### 3. WaitForJobCompletion

#### Input
The job ID from the previous step:
```json
{
  "jobId": "s-1234ABCD5678EFGH"
}
```

#### Output
The job status check result is stored in `$.jobStatus`:
```json
{
  "s3_url": { ... },
  "jobDetails": { ... },
  "jobStatus": {
    "Payload": {
      "statusCode": 200,
      "jobId": "s-1234ABCD5678EFGH",
      "status": "RUNNING",
      "details": {
        "Id": "s-1234ABCD5678EFGH",
        "Name": "Process your-dataset-name",
        "Status": {
          "State": "RUNNING",
          "StateChangeReason": {},
          "Timeline": { ... }
        }
      }
    }
  }
}
```

### 4. CheckJobStatus (Choice)

#### Input
The entire state from the previous step.

#### Output
Routes to the appropriate next state based on job status.

### 5. WaitBeforeCheckingStatus

#### Input
The entire state (no changes).

#### Output
The entire state (no changes).

### 6. JobComplete (Choice)

#### Input
The entire state, with the latest job status.

#### Output
Routes to either JobFailed or JobSucceeded based on status.

### 7. JobFailed/JobSucceeded

#### Input
The entire state data.

#### Output
- JobFailed: Terminates with failure.
- JobSucceeded: Terminates with success.

## Final State Machine Output

If all jobs succeed, the state machine outputs an array with results for each S3 URL processed:

```json
[
  {
    "s3_url": { ... first URL ... },
    "jobDetails": { ... job details for first URL ... },
    "jobStatus": { ... final job status for first URL ... }
  },
  {
    "s3_url": { ... second URL ... },
    "jobDetails": { ... job details for second URL ... },
    "jobStatus": { ... final job status for second URL ... }
  }
]
```
