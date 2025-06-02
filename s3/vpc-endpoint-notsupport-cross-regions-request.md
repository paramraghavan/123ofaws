The VPC endpoint error occurs because your EMR cluster is using a VPC endpoint for S3, which doesn't support
cross-region requests. Here are several solutions:

## Solution 1: Use Regional Endpoints Explicitly

```bash
aws s3 sync s3://source-bucket/parquet-data/ s3://destination-bucket/parquet-data/ \
  --endpoint-url https://s3.us-east-2.amazonaws.com \
  --region us-east-2
```

## Solution 2: Configure AWS CLI with Different Profiles

```bash
# Configure separate profiles for each region
aws configure set region us-east-2 --profile source-region
aws configure set region us-east-1 --profile dest-region

# Use source profile for the sync
aws s3 sync s3://source-bucket/parquet-data/ s3://destination-bucket/parquet-data/ \
  --profile source-region
```

## Solution 3: Two-Step Process (Recommended)

```bash
# Step 1: Copy from source region to local EMR cluster
aws s3 sync s3://source-bucket/parquet-data/ /tmp/parquet-data/ \
  --endpoint-url https://s3.us-east-2.amazonaws.com \
  --region us-east-2

# Step 2: Copy from local to destination bucket
aws s3 sync /tmp/parquet-data/ s3://destination-bucket/parquet-data/
```

## Solution 4: Use Hadoop DistCp with Different Endpoints

```bash
hadoop distcp \
  -Dfs.s3a.bucket.source-bucket.endpoint=s3.us-east-2.amazonaws.com \
  -Dfs.s3a.bucket.destination-bucket.endpoint=s3.us-east-1.amazonaws.com \
  s3a://source-bucket/parquet-data/ \
  s3a://destination-bucket/parquet-data/
```

## Solution 5: Modify EMR Cluster Configuration

If you can restart your EMR cluster, configure it to not use VPC endpoints for S3:

```json
[
  {
    "Classification": "core-site",
    "Properties": {
      "fs.s3a.endpoint": "s3.amazonaws.com",
      "fs.s3a.path.style.access": "false"
    }
  }
]
```

## Solution 6: Use EMR Step with Specific Configuration

Create an EMR step with cross-region configuration:

```json
{
  "Name": "Cross-region copy",
  "ActionOnFailure": "CONTINUE",
  "HadoopJarStep": {
    "Jar": "command-runner.jar",
    "Args": [
      "hadoop",
      "distcp",
      "-Dfs.s3a.bucket.source-bucket.endpoint=s3.us-east-2.amazonaws.com",
      "s3a://source-bucket/parquet-data/",
      "s3a://destination-bucket/parquet-data/"
    ]
  }
}
```

## Quick Test

Try this first to confirm the endpoint issue:

```bash
aws s3 ls s3://source-bucket/ --endpoint-url https://s3.us-east-2.amazonaws.com --region us-east-2
```

Which solution would work best for your setup? The two-step process (Solution 3) is often the most reliable for
cross-region copies when VPC endpoints are involved.