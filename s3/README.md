[S3 Tutorial](https://www.simplilearn.com/tutorials/aws-tutorial/aws-s3)

## Object in S3
Amazon S3 stores data as objects within buckets. An object is composed of a file and any metadata that describes that file. To store an object in Amazon S3, you upload the file you want to store into a bucket. When you upload a file, you can set permissions on the object and add any metadata.

Buckets are logical containers for objects. You can have one or more buckets in your account and can control access for each bucket individually. You control who can create, delete, and list objects in the bucket. You can also view access logs for the bucket and its objects and choose the geographical region where Amazon S3 will store the bucket and its contents.

![image](https://user-images.githubusercontent.com/52529498/141747094-8f9babd7-b072-44f7-9636-84a5a45e3843.png)


Amazon S3 holds buckets. Each bucket contains objects. Each object is a single file with its associated metadata.

## Accessing your content
Once objects have been stored in an Amazon S3 bucket, they are given an object key. Use this, along with the bucket name, to access the object.
Below is an example of a URL for a single object in a bucket named doc, with an object key composed of the prefix 2006-03-01 and the file named AmazonS3.html.

![image](https://user-images.githubusercontent.com/52529498/141731144-466bc040-100c-419b-8dbc-ea357b2b21b2.png)

This is an example of a URL for a single object in a bucket named doc inside of a folder named 2006-03-01 with the file name AmazonS3.html.
An object key is the unique identifier for an object in a bucket. Because the combination of a bucket, key, and version ID uniquely identifies each object, you can think of Amazon S3 as a basic data map between "bucket + key + version" and the object itself. Every object in Amazon S3 can be uniquely addressed through the combination of the web service endpoint, bucket name, key, and (optionally) version.

## Advantages of using Amazon S3 as the storage platform for your data analysis solution.

### Decoupling of storage from compute and data processing
With Amazon S3, you can cost-effectively store all data types in their native formats. You can then launch as many or as few virtual servers needed using Amazon Elastic Compute Cloud (Amazon EC2) and use AWS analytics tools to process your data. You can optimize your EC2 instances to provide the correct ratios of CPU, memory, and bandwidth for best performance. Decoupling your processing and storage provides a significant number of benefits, including the ability to process and analyze the same data with a variety of tools.

### Centralized data architecture
Amazon S3 makes it easy to build a multi-tenant environment, where many users can bring their own data analytics tools to a common set of data. This improves both cost and data governance over traditional solutions, which require multiple copies of data to be distributed across multiple processing platforms. Although this may require an additional step to load your data into the right tool, using Amazon S3 as your central data store provides even more benefits over traditional storage options.

### Integration with clusterless and serverless AWS services
Combine Amazon S3 with other AWS services to query and process data. Amazon S3 also integrates with AWS Lambda serverless computing to run code without provisioning or managing servers. Amazon Athena can query Amazon S3 directly using the Structured Query Language (SQL), without the need for data to be ingested into a relational database.
With all of these capabilities, you only pay for the actual amounts of data you process or the compute time you consume.


## presigned url
**A pre-signed URL allows you to grant temporary access to users who don’t have permission to directly run AWS operations in your account.**
A pre-signed URL is signed with your credentials and can be used by any user.

All objects and buckets by default are private. The presigned URLs are useful if you want your user/customer to be able to upload a specific object to your bucket, but you don't require them to have AWS security credentials or permissions.  

The default pre-signed URL expiration time is 15 minutes

A presigned URL upload gives you access to the object identified in the URL, provided that the creator of the presigned URL has permissions to access that object. That is, if you receive a presigned URL to upload an object, you can upload the object only if the creator of the presigned URL has the necessary permissions to upload that object.

> aws s3 presign s3://<bucket-name>/object

Example:
  aws s3 presign s3://bucket/stack-templates/Managed_EC2_Batch_Environment.yaml
  output
  > https://bucket.s3.amazonaws.com/stack-templates/Managed_EC2_Batch_Environment.yaml?AWSAccessKeyId=AKIAZ77QOIYEWN5XVY56&Signature=qzY5Ly7UFT4y0o3CJ1Xgc3LD5
DM%3D&Expires=1641261208

  
 ## presigned url python code
Generate a presigned URL to upload an object by using the SDK for Python (Boto3). For example, use a Boto3 client and the generate_presigned_url function to generate a presigned URL that PUTs an object with an expiration time of 3600 seconds/1 hour.
  <pre>
  import boto3
    url = boto3.client('s3').generate_presigned_url(
    ClientMethod='put_object', 
    Params={'Bucket': 'BUCKET_NAME', 'Key': 'OBJECT_KEY'},
    ExpiresIn=3600)
  </pre>
  
 - [See here for more details](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
 
  
# S3 Strong vs Eventual Consistency  
  
Amazon S3 delivers strong read-after-write consistency automatically for all applications, without changes to performance or availability, without sacrificing regional isolation for applications, and at no additional cost. With strong consistency, S3 simplifies the migration of on-premises analytics workloads by removing the need to make changes to applications, and reduces costs by removing the need for extra infrastructure to provide strong consistency.

Any request for S3 storage is strongly consistent. After a successful write of a new object or an overwrite of an existing object, any subsequent read request immediately receives the latest version of the object. S3 also provides strong consistency for list operations, so after a write, you can immediately perform a listing of the objects in a bucket with any changes reflected.  

After a successful write of a new object, or an overwrite or delete of an existing object, any subsequent read request immediately receives the latest version of the object. S3 also provides strong consistency for list operations, so after a write, you can immediately perform a listing of the objects in a bucket with any changes reflected.

For all existing and new objects, and in all regions, all S3 GET, PUT, and LIST operations, as well as operations that change object tags, ACLs, or metadata, are now strongly consistent. What you write is what you will read, and the results of a LIST will be an accurate reflection of what’s in the bucket.
  
ref: https://aws.amazon.com/s3/consistency/  
# Notes
**Difference between s3n, s3a and s3**
Amazon S3 (Simple Storage Service) is a scalable object storage service from AWS. When working with Hadoop ecosystems (like HDFS, Spark, etc.), different schemes were developed to allow these systems to interact with Amazon S3. These schemes are denoted by their prefixes: s3, s3n, and s3a. Let's dive into the differences among these:
* s3 (Block-based FileSystem for S3):
    * The original adapter to connect Hadoop to S3.
    * It treats S3 as a block-based filesystem, which means it divides files into blocks, just like HDFS.
    * It's not considered suitable for large files because of the block-based approach. It can cause many S3 PUT requests, leading to data consistency issues and additional costs.
    * It's largely obsolete now and isn't recommended for use.
* s3n (S3 Native FileSystem):
    * A successor to the original s3 scheme.
    * It stands for "S3 Native" and treats S3 objects as native files, making it more suitable for larger files compared to the original s3 scheme.
    * s3n uses a single S3 object for files, avoiding the block-based approach.
    * Allows for horizontal scalability, but still has some limitations and inconsistencies, especially in write operations.
* s3a (S3 Advanced FileSystem):
    * The most recent and recommended way to integrate Hadoop with S3.
    * It's an extension of s3n and is built on top of the AWS Java SDK.
    * Resolves many of the issues and limitations found in s3 and s3n.
    * Supports larger files (multi-terabyte scale).
    * Provides better performance and more features, like S3 server-side encryption, S3Guard for consistency, and optimized data transfers.
    * Supports Amazon S3 Select, allowing for more efficient data retrievals.
    * It's the preferred choice when working with Hadoop ecosystems and Amazon S3.

**In summary:**
* If you're working with the Hadoop ecosystem and Amazon S3, you should choose s3a because of its performance, features, and support.
* Both s3 and s3n are older connectors and come with limitations. While they may still be in use in older systems, for new implementations, s3a is the recommended choice.

- The letter change on the URI scheme makes a big difference because it causes different software to be used to interface to S3. Somewhat like the difference between http and https - it's only a one-letter change, but it triggers a big difference in behavior.
- The difference between s3 and s3n/s3a is that s3 is a block-based overlay on top of Amazon S3, while s3n/s3a are not (they are object-based).
- The difference between s3n and s3a is that s3n supports objects up to 5GB in size, while s3a supports objects up to 5TB and has higher performance (both are because it uses multi-part upload). s3a is the successor to s3n.
- - If you're here because you want to understand which S3 file system you should use with Amazon EMR, then read [this article](https://web.archive.org/web/20170718025436/https://aws.amazon.com/premiumsupport/knowledge-center/emr-file-system-s3/) from Amazon (only available on wayback machine). The net is: use s3:// because s3:// and s3n:// are functionally interchangeable in the context of EMR, while s3a:// is not compatible with EMR.
- For additional advice, read [Work with Storage and File Systems](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-file-systems.html).
  
- [difference between s3n, s3a and s3](https://stackoverflow.com/questions/33356041/technically-what-is-the-difference-between-s3n-s3a-and-s3)
