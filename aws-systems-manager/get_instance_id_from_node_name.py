import boto3
import time
from botocore.exceptions import ClientError


def get_instance_id_by_name(node_name, region='us-east-1'):
    """
    Get instance ID from node name (tag Name)

    Args:
        node_name (str): Edge node name
        region (str): AWS region

    Returns:
        str: Instance ID or None if not found
    """
    ec2_client = boto3.client('ec2', region_name=region)

    try:
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [node_name]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                return instance['InstanceId']

        print(f"No running instance found with name: {node_name}")
        return None

    except ClientError as e:
        print(f"Error finding instance: {e}")
        return None




# Simple usage
if __name__ == "__main__":
    NODE_NAME = "my-edge-node"  # Replace with your edge node name
    REGION = "us-east-1"  # Replace with your region

    print(f"Running script on edge node: {NODE_NAME}")
    results = get_instance_id_by_name(NODE_NAME)

    if results:
        print(f"\n✅ Script completed: {results}")
    else:
        print("\n Error finding instance id")