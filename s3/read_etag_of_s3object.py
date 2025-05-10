import boto3
from botocore.exceptions import ClientError


def get_s3_object_etag(bucket_name, object_key, region_name=None):
    """
    Get the ETag value of an S3 object.

    Args:
        bucket_name (str): The name of the S3 bucket
        object_key (str): The key (path) of the object in the bucket
        region_name (str, optional): AWS region name. If None, uses default region from config.

    Returns:
        str: The ETag value if successful, None otherwise
    """
    # Initialize S3 client
    if region_name:
        s3_client = boto3.client('s3', region_name=region_name)
    else:
        s3_client = boto3.client('s3')

    try:
        # Get object metadata using head_object
        response = s3_client.head_object(
            Bucket=bucket_name,
            Key=object_key
        )

        # Extract ETag from response
        if 'ETag' in response:
            # ETags are returned with quotes, so we strip them
            etag = response['ETag'].strip('"')
            return etag
        else:
            print(f"No ETag found for object {object_key} in bucket {bucket_name}")
            return None

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"Object {object_key} not found in bucket {bucket_name}")
        else:
            print(f"Error getting object metadata: {e}")
        return None


def main():
    # Example usage
    bucket_name = 'my-example-bucket'
    object_key = 'path/to/my/file.txt'

    etag = get_s3_object_etag(bucket_name, object_key)

    if etag:
        print(f"ETag for {object_key}: {etag}")

        # For multipart uploads, you can check if it's a multipart ETag
        if '-' in etag:
            print("This is a multipart upload ETag")
            parts = etag.split('-')
            print(f"Number of parts: {parts[1]}")


if __name__ == "__main__":
    main()