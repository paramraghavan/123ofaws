"""
This is a fire and forgot ssm command that will run on aws edge node and we know the edge node name
"""

import boto3
import json
from botocore.exceptions import ClientError


def submit_python_script_via_ssm(
        instance_id,
        script_path,
        script_argument,
        region='us-east-1',
        python_executable='python3'
):
    """
    Submit a Python script to run on an AWS edge node via SSM Send Command.

    Args:
        instance_id (str): EC2 instance ID of the edge node
        script_path (str): Full path to the Python script on the edge node
        script_argument (str): Argument to pass to the Python script
        region (str): AWS region where the instance is located
        python_executable (str): Python executable to use ('python', 'python3', etc.)

    Returns:
        dict: Command execution response from SSM
    """

    # Initialize SSM client
    ssm_client = boto3.client('ssm', region_name=region)

    # Construct the command to execute
    command = f"{python_executable} {script_path} {script_argument}"

    try:
        # Send the command via SSM
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [command],
                'workingDirectory': ['/tmp'],  # Optional: set working directory
                'executionTimeout': ['3600']  # Optional: timeout in seconds (1 hour)
            },
            Comment=f'Execute Python script: {script_path}',
            TimeoutSeconds=60,  # Command dispatch timeout
            MaxConcurrency='1',
            MaxErrors='0'
        )

        command_id = response['Command']['CommandId']
        print(f"Command submitted successfully!")
        print(f"Command ID: {command_id}")
        print(f"Instance ID: {instance_id}")
        print(f"Command: {command}")

        return response

    except ClientError as e:
        print(f"Error submitting command: {e}")
        return None


def check_command_status(command_id, instance_id, region='us-east-1'):
    """
    Check the status of a previously submitted SSM command.

    Args:
        command_id (str): Command ID returned from send_command
        instance_id (str): EC2 instance ID
        region (str): AWS region

    Returns:
        dict: Command status information
    """
    ssm_client = boto3.client('ssm', region_name=region)

    try:
        response = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )

        status = response['Status']
        print(f"Command Status: {status}")

        if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
            print(f"Standard Output: {response.get('StandardOutputContent', 'No output')}")
            if response.get('StandardErrorContent'):
                print(f"Standard Error: {response['StandardErrorContent']}")

        return response

    except ClientError as e:
        print(f"Error checking command status: {e}")
        return None


def fire_and_forget_script(
        instance_id,
        script_path,
        script_argument,
        region='us-east-1',
        python_executable='python3'
):
    """
    Fire and forget version - submit script and return immediately.

    Args:
        instance_id (str): EC2 instance ID of the edge node
        script_path (str): Full path to the Python script on the edge node
        script_argument (str): Argument to pass to the Python script
        region (str): AWS region where the instance is located
        python_executable (str): Python executable to use

    Returns:
        str: Command ID if successful, None if failed
    """
    response = submit_python_script_via_ssm(
        instance_id, script_path, script_argument, region, python_executable
    )

    if response:
        command_id = response['Command']['CommandId']
        print(f"Script submitted! Command ID: {command_id}")
        print("Job is running in the background on the edge node.")
        return command_id
    else:
        print("Failed to submit script.")
        return None


# Example usage
if __name__ == "__main__":
    # Configuration
    INSTANCE_ID = "i-1234567890abcdef0"  # Replace with your edge node instance ID
    SCRIPT_PATH = "/home/ec2-user/my_script.py"  # Replace with your script path
    SCRIPT_ARG = "my_argument"  # Replace with your script argument
    REGION = "us-east-1"  # Replace with your AWS region

    # Fire and forget execution
    print("=== Fire and Forget Execution ===")
    command_id = fire_and_forget_script(
        instance_id=INSTANCE_ID,
        script_path=SCRIPT_PATH,
        script_argument=SCRIPT_ARG,
        region=REGION
    )

    # Optional: Check status later (uncomment if needed)
    # if command_id:
    #     print("\n=== Checking Status (optional) ===")
    #     import time
    #     time.sleep(10)  # Wait a bit before checking
    #     check_command_status(command_id, INSTANCE_ID, REGION)


# Alternative: Submit with multiple arguments
def submit_script_with_multiple_args(
        instance_id,
        script_path,
        script_args_list,
        region='us-east-1',
        python_executable='python3'
):
    """
    Submit script with multiple arguments.

    Args:
        script_args_list (list): List of arguments to pass to the script
    """
    # Join arguments properly (handle spaces and special characters)
    args_str = ' '.join(f'"{arg}"' for arg in script_args_list)
    command = f"{python_executable} {script_path} {args_str}"

    ssm_client = boto3.client('ssm', region_name=region)

    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [command],
                'executionTimeout': ['3600']
            },
            Comment=f'Execute Python script with multiple args: {script_path}',
        )

        return response['Command']['CommandId']

    except ClientError as e:
        print(f"Error: {e}")
        return None

# Example with multiple arguments
# command_id = submit_script_with_multiple_args(
#     "i-1234567890abcdef0",
#     "/home/ec2-user/my_script.py",
#     ["arg1", "arg2", "value with spaces"],
#     "us-east-1"
# )

