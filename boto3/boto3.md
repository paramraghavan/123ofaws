# boto3
## What is the use of Boto3?
  - Boto3 is the Amazon Web Services (AWS) Software Development Kit (SDK) for Python, which allows Python developers to write software that makes use of services like Amazon S3 ,EC2, etc.
  - https://aws.amazon.com/sdk-for-python/
  - [boto3 api](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html)
    
## Why is it called Boto3? 
  - Boto derives its name from the Portuguese name given to types of dolphins native to the Amazon River. ... The Boto was named after it because it swims in the Amazon, and all the good river and city names were already taken

## Boto 3: Resource vs Client
- Boto3 client are:
  - It maps 1:1 with the actual AWS service API.
  - All AWS service operations supported by clients
    
- Resources
  - Resources are higher-level abstractions of AWS services compared to clients. Resources are 
    the recommended pattern to use boto3 as you don’t have to worry about a lot of the underlying
    details when interacting with AWS services. As a result, code written with Resources tends to
    be simpler.

- Session
  - The boto3. Session class, according to the docs, “ stores configuration state and allows you to create service clients and resources.
    ”Most importantly it represents the configuration of an IAM identity (IAM user or assumed role) and AWS region, the two things you 
    need to talk to an AWS service. How long session lasts - The token (and the access and secret keys) generated using this API is valid for a 
    specific duration (minimum 900 seconds). The maximum duration of the validity of the token is 12 hours.

ref: 
https://www.learnaws.org/2021/02/24/boto3-resource-client/
