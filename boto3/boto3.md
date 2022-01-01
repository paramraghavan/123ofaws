# boto3
## What is the use of Boto3?
  - Boto3 is the Amazon Web Services (AWS) Software Development Kit (SDK) for Python, which allows Python developers to write software that makes use of services like Amazon S3 and Amazon EC2. You can find the latest, most up to date, documentation at our doc site, including a list of services that are supported.
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


ref: 
https://www.learnaws.org/2021/02/24/boto3-resource-client/