Simple Python script using boto3 to read the ETag value from an S3 object:

This code:

1. Uses the `head_object` method to retrieve the object metadata without downloading the object content
2. Extracts the ETag value from the response
3. Strips the surrounding quotes that S3 includes in ETag values
4. Includes error handling for cases where the object doesn't exist or there are permission issues
5. Adds a simple check to identify if the ETag indicates a multipart upload (ETags for multipart uploads contain a
   hyphen)

### Notes about S3 ETags:

1. For simple uploads (non-multipart), the ETag is typically the MD5 hash of the object
2. For multipart uploads, the ETag is not a simple MD5 hash but follows the format `[hash]-[number of parts]`
3. If server-side encryption with customer-provided keys (SSE-C) is used, the ETag might not be the MD5 hash

You can modify the region name, bucket name, and object key in the main function to match your specific requirements.