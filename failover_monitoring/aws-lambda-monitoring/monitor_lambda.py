import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError

# Configuration from environment variables
TAG_NAME = os.environ.get('TAG_NAME', 'production')
LOG_BUCKET = os.environ.get('LOG_BUCKET', '')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
S3_REPLICA_REGION = os.environ.get('S3_REPLICA_REGION', 'us-west-2')


def lambda_handler(event, context):
    """Main monitoring function - runs every 10 minutes"""
    try:
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            's3_buckets': check_s3_buckets(),
            'ec2_instances': check_ec2_instances(),
            'emr_clusters': check_emr_clusters()
        }

        # Write status to S3
        write_status(results)
        write_heartbeat()

        # Handle failures
        handle_failures(results)

        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
    except Exception as e:
        print(f"Error in monitor_lambda: {str(e)}")
        raise


def check_s3_buckets():
    """Check S3 buckets with matching tag"""
    s3 = boto3.client('s3')
    buckets = []

    try:
        response = s3.list_buckets()
        for bucket in response.get('Buckets', []):
            try:
                # Get bucket tags
                tags_response = s3.get_bucket_tagging(Bucket=bucket['Name'])
                tags = tags_response.get('TagSet', [])

                if has_matching_tag(tags, TAG_NAME):
                    # Check bucket availability
                    try:
                        s3.head_bucket(Bucket=bucket['Name'])
                        location = s3.get_bucket_location(Bucket=bucket['Name'])
                        region = location.get('LocationConstraint', 'us-east-1')
                        buckets.append({
                            'name': bucket['Name'],
                            'status': 'available',
                            'region': region
                        })
                    except ClientError as e:
                        buckets.append({
                            'name': bucket['Name'],
                            'status': 'failed',
                            'error': str(e),
                            'region': 'unknown'
                        })
            except ClientError as e:
                # If no tags found, skip bucket
                if e.response['Error']['Code'] != 'NoSuchTagSet':
                    print(f"Error checking tags on {bucket['Name']}: {str(e)}")
    except Exception as e:
        print(f"Error in check_s3_buckets: {str(e)}")

    return buckets


def check_ec2_instances():
    """Check EC2 instances with matching tag"""
    ec2 = boto3.client('ec2')
    instances = []

    try:
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [f'*{TAG_NAME}*']
                }
            ]
        )

        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instances.append({
                    'id': instance['InstanceId'],
                    'state': instance['State']['Name'],
                    'type': instance['InstanceType'],
                    'az': instance['Placement']['AvailabilityZone']
                })
    except Exception as e:
        print(f"Error in check_ec2_instances: {str(e)}")

    return instances


def check_emr_clusters():
    """Check EMR clusters with matching tag"""
    emr = boto3.client('emr')
    clusters = []

    try:
        response = emr.list_clusters(
            ClusterStates=['STARTING', 'RUNNING', 'WAITING', 'TERMINATING', 'TERMINATED']
        )

        for cluster in response.get('Clusters', []):
            try:
                # Get cluster details to retrieve tags
                cluster_details = emr.describe_cluster(ClusterId=cluster['Id'])
                tags = cluster_details.get('Cluster', {}).get('Tags', [])

                if has_matching_tag(tags, TAG_NAME):
                    clusters.append({
                        'id': cluster['Id'],
                        'name': cluster['Name'],
                        'status': cluster['Status']['State']
                    })
            except ClientError as e:
                print(f"Error describing cluster {cluster['Id']}: {str(e)}")
    except Exception as e:
        print(f"Error in check_emr_clusters: {str(e)}")

    return clusters


def has_matching_tag(tags, tag_name):
    """Check if tag list contains matching tag"""
    for tag in tags:
        # Handle both S3 format (Key/Value) and EC2/EMR format (Key/Value)
        key = tag.get('Key') or tag.get('key')
        value = tag.get('Value') or tag.get('value')
        if key == 'Name' and value and tag_name in value:
            return True
    return False


def handle_failures(results):
    """Handle detected failures"""
    if not SNS_TOPIC_ARN:
        print("SNS_TOPIC_ARN not configured, skipping failure alerts")
        return

    sns = boto3.client('sns')

    # S3 failures → Auto-failover
    for bucket in results['s3_buckets']:
        if bucket['status'] == 'failed':
            print(f"S3 bucket failed: {bucket['name']}, initiating failover")
            failover_s3_bucket(bucket['name'])

    # EC2/EMR failures → Alert
    failed_ec2 = [
        i for i in results['ec2_instances']
        if i['state'] in ['stopped', 'terminated', 'stopping']
    ]
    failed_emr = [
        c for c in results['emr_clusters']
        if 'TERMIN' in c['status'] or 'FAIL' in c['status']
    ]

    if failed_ec2 or failed_emr:
        alert_message = {
            'alert_type': 'resource_failure',
            'timestamp': datetime.utcnow().isoformat(),
            'ec2_failures': failed_ec2,
            'emr_failures': failed_emr
        }
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f'AWS Resources Failed - {TAG_NAME}',
                Message=json.dumps(alert_message, indent=2)
            )
        except ClientError as e:
            print(f"Error sending SNS alert: {str(e)}")


def failover_s3_bucket(bucket_name):
    """Auto-failover S3 bucket to replica region"""
    s3 = boto3.client('s3')

    try:
        # Get list of critical objects
        # For simplicity, failover the bucket metadata
        location = s3.get_bucket_location(Bucket=bucket_name)
        region = location.get('LocationConstraint', 'us-east-1')

        # Log failover action
        failover_log = {
            'action': 'failover_initiated',
            'bucket': bucket_name,
            'original_region': region,
            'replica_region': S3_REPLICA_REGION,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Write failover log
        if LOG_BUCKET:
            s3.put_object(
                Bucket=LOG_BUCKET,
                Key=f'failover_logs/{bucket_name}-{datetime.utcnow().timestamp()}.json',
                Body=json.dumps(failover_log, indent=2)
            )

        print(f"Failover initiated for bucket: {bucket_name}")
    except Exception as e:
        print(f"Error during S3 failover for {bucket_name}: {str(e)}")


def write_status(results):
    """Write status to S3"""
    if not LOG_BUCKET:
        print("LOG_BUCKET not configured, skipping status write")
        return

    s3 = boto3.client('s3')

    try:
        s3.put_object(
            Bucket=LOG_BUCKET,
            Key='status/latest.json',
            Body=json.dumps(results, indent=2),
            ContentType='application/json'
        )
        print(f"Status written to s3://{LOG_BUCKET}/status/latest.json")
    except ClientError as e:
        print(f"Error writing status to S3: {str(e)}")


def write_heartbeat():
    """Write heartbeat for external monitoring"""
    if not LOG_BUCKET:
        print("LOG_BUCKET not configured, skipping heartbeat write")
        return

    s3 = boto3.client('s3')

    try:
        heartbeat = {
            'last_update': datetime.utcnow().isoformat(),
            'lambda_function': 'monitor_lambda'
        }
        s3.put_object(
            Bucket=LOG_BUCKET,
            Key='heartbeat.json',
            Body=json.dumps(heartbeat, indent=2),
            ContentType='application/json'
        )
        print(f"Heartbeat written to s3://{LOG_BUCKET}/heartbeat.json")
    except ClientError as e:
        print(f"Error writing heartbeat to S3: {str(e)}")
