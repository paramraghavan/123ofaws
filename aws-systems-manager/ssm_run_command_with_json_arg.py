import boto3
import datetime
import time
from operator import itemgetter


def run_command_on_least_loaded_edge_node(region_name='us-east-1'):
    """
    Finds the least loaded edge node and runs a hello world Python script on it.

    Args:
        region_name (str): AWS region to use

    Returns:
        dict: Information about the executed command and target instance
    """
    # Initialize boto3 clients
    ec2_client = boto3.client('ec2', region_name=region_name)
    ssm_client = boto3.client('ssm', region_name=region_name)
    cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)

    print("Finding edge nodes...")

    # Find all instances with 'param-dev-node' in their name tag
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            },
            {
                'Name': 'tag:Name',
                'Values': ['*param-dev-node*']
            }
        ]
    )

    # Extract instance IDs and names
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']

            # Get the Name tag value
            instance_name = 'Unknown'
            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']
                    break

            # Add to our list
            instances.append({
                'id': instance_id,
                'name': instance_name,
            })

    if not instances:
        print("No instances found matching pattern 'param-dev-node'")
        return None

    print(f"Found {len(instances)} matching instances")

    # Get CPU utilization for each instance over the last 5 minutes
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(minutes=5)

    for instance in instances:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance['id']
                    },
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes in seconds
                Statistics=['Average']
            )

            # If datapoints exist, get the latest average CPU util
            if response['Datapoints']:
                instance['cpu_util'] = response['Datapoints'][0]['Average']
            else:
                # If no data, assume a high value to avoid selecting this instance
                instance['cpu_util'] = 100.0
        except Exception as e:
            print(f"Error getting metrics for {instance['id']}: {e}")
            instance['cpu_util'] = 100.0

    # Sort instances by CPU utilization
    instances.sort(key=itemgetter('cpu_util'))

    # Select the least loaded instance
    target_instance = instances[0]
    print(
        f"Least loaded instance: {target_instance['name']} (ID: {target_instance['id']}) with {target_instance['cpu_util']:.2f}% CPU")

    # Define the Python script to run (hello world with date/time)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hello_world_script = f"""
import datetime
print("Hello World from {target_instance['name']}!")
print("Current date and time: {current_time}")
print("This command was executed via AWS SSM Run Command")
"""

    # Execute the command on the target instance
    print(f"Executing command on {target_instance['name']}...")
    response = ssm_client.send_command(
        InstanceIds=[target_instance['id']],
        DocumentName='AWS-RunPythonScript',
        Parameters={
            'pythonScript': [hello_world_script]
        },
        Comment=f'Hello World script executed via SSM at {current_time}'
    )

    command_id = response['Command']['CommandId']
    print(f"Command ID: {command_id}")

    # Wait for command to complete and get output
    time.sleep(2)  # Brief pause to allow command to initiate

    # Loop to check command status
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        cmd_result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=target_instance['id']
        )

        status = cmd_result['Status']
        print(f"Command status: {status}")

        if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
            if status == 'Success':
                print("Command output:")
                print(cmd_result['StandardOutputContent'])

                if cmd_result['StandardErrorContent']:
                    print("Standard error:")
                    print(cmd_result['StandardErrorContent'])
            else:
                print(f"Command ended with status: {status}")
                if 'StandardErrorContent' in cmd_result and cmd_result['StandardErrorContent']:
                    print("Error details:")
                    print(cmd_result['StandardErrorContent'])
            break

        attempts += 1
        time.sleep(2)

    result = {
        'instance_id': target_instance['id'],
        'instance_name': target_instance['name'],
        'command_id': command_id,
        'cpu_utilization': target_instance['cpu_util'],
        'status': status if attempts < max_attempts else 'Unknown'
    }

    return result


if __name__ == "__main__":
    print("Starting execution...")
    result = run_command_on_least_loaded_edge_node()

    if result:
        print("\nExecution Summary:")
        print(f"Target: {result['instance_name']} ({result['instance_id']})")
        print(f"CPU Utilization: {result['cpu_utilization']:.2f}%")
        print(f"Command Status: {result['status']}")
    else:
        print("Execution failed - no matching instances found")
