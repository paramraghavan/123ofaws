'''
Cross account bucket access.
Ref:
 https://stackoverflow.com/questions/44171849/aws-boto3-assumerole-example-which-includes-role-usage
'''

import boto3
import os

'''
In this case cross account bucket access has been  provisioned
'''
def cross_account_bucket_access():
    sts_default_provider_chain = boto3.client('sts')
    role_to_assume_arn=os.environ['cross_bucket_access_role_arn']
    role_session_name='bucket_session'
    response = sts_default_provider_chain.assume_role(
        RoleArn=role_to_assume_arn,
        RoleSessionName=role_session_name
    )
    # From the response that contains the assumed role, get the temporary
    # credentials that can be used to make subsequent API calls
    credentials = response['Credentials']
    s3_resource=boto3.resource('s3',
                               aws_access_key_id=credentials['AccessKeyId'],
                               aws_secret_access_key=credentials['SecretAccessKey'],
                               aws_session_token=credentials['SessionToken']
                               )

    # Use the Amazon S3 resource object that is now configured with the
    # credentials to access cross account S3 buckets.
    for bucket in s3_resource.buckets.all():
        print(bucket.name)

from boto3 import Session

class Boto3STSService(object):
    def __init__(self, arn, arn_access_key, arn_secret_key, role_session_name ):
        sess = Session(aws_access_key_id=arn_access_key,
                       aws_secret_access_key=arn_secret_key)
        sts_connection = sess.client('sts')
        assume_role_object = sts_connection.assume_role(
            RoleArn=arn, RoleSessionName=role_session_name,
            DurationSeconds=30)
        self.credentials = assume_role_object['Credentials']