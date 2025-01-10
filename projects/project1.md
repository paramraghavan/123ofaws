How to reconstruct  data from  beginning of  time and compare with data ingested into snowflake, if there any differences, create report or some kind of output.  The data we ingest comes daily by year, month and day. The data has identified primary keys or key values.  The data is ingested from AWS S3 bucket
As we get the data we insert the data into snowflake. We could get changes for previously sent data, in that case we delete the rows based on primary key(s) for respective dataset, in snowflake and insert it again
Data stored in s3
s3://bucket-name/dataset_name/year=2024/month=12/day=1/data.parquet 
or 
s3://bucket-name/dataset_name/year=2024/month=12/day=1/data.csv
I have many datasets like these that needs to reconciled. some of these are large dataset, and some smaller ones
Design a generic code to reconstruct from s3 and compare with snowflake - using identified primary keys. you can test for one and rest should work .

Can we copy s3 data snowflake  stage, and create temp table. The temporary table schema can be assumed to be same as original snowflake table
Question :
- Should store the  data reconstructed from S3 into a single file or save into a temporary table in snowflake , etc..
* How do we handle reconstruction if the data sent today, is for the previous day as they might have missed sending the data previously or this may be an update to what was sent previously
Explain in detail