You can invoke another script as a subprocess from within a script running via SSM Run Command. However, there are some
important considerations:

1. The second script will run as a subprocess of the first SSM command, not as a separate SSM command
2. If you want to launch another actual SSM command (not just a subprocess), you'd need AWS credentials within the first
   script

Let me explain both approaches:

## Approach 1: Running as a subprocess

When you run a script via SSM, you can have that script launch another script using Python's subprocess module. The
second script will run as a child process of the first script.

Here's how you could modify your main.py to launch another script as a subprocess:

```python
# main.py on the edge node
import sys
import json
import subprocess
import datetime


def main():
    # Get JSON input from command line argument
    if len(sys.argv) < 2:
        print("Error: JSON input required")
        return 1

    json_input = json.loads(sys.argv[1])
    print(f"Received input: {json_input}")
    print(f"Running on host at {datetime.datetime.now()}")

    # Launch another script as a subprocess
    print("Launching child script...")

    # Option 1: Wait for completion
    result = subprocess.run(
        ["/path/to/child_script.py", json.dumps(json_input)],
        capture_output=True,
        text=True
    )

    print("Child script stdout:")
    print(result.stdout)

    if result.stderr:
        print("Child script stderr:")
        print(result.stderr)

    # Or Option 2: Launch and don't wait (background process)
    # This will continue running even if the SSM command completes
    # subprocess.Popen(["/path/to/child_script.py", json.dumps(json_input)])

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Important notes about this approach:

- The child process inherits the environment of the parent
- If the SSM command timeouts or is terminated, child processes may be terminated too
- You can use `subprocess.Popen` to launch a background process that will continue running even if the SSM command
  completes

## Approach 2: Launching a new SSM command

If you want to actually launch a new, separate SSM command from within your script, you'd need to use the AWS SDK (
boto3) within your script. This is more complex as it requires AWS credentials on the edge node:

```python
# main.py on the edge node
import sys
import json
import datetime
import boto3


def main():
    # Get JSON input from command line argument
    if len(sys.argv) < 2:
        print("Error: JSON input required")
        return 1

    json_input = json.loads(sys.argv[1])
    print(f"Received input: {json_input}")
    print(f"Running on host at {datetime.datetime.now()}")

    # Get own instance ID (if needed)
    # This requires IMDSv2 access
    import requests
    token_url = "http://169.254.169.254/latest/api/token"
    token_headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    token_response = requests.put(token_url, headers=token_headers)
    token = token_response.text

    instance_id_url = "http://169.254.169.254/latest/meta-data/instance-id"
    instance_id_headers = {"X-aws-ec2-metadata-token": token}
    instance_id_response = requests.get(instance_id_url, headers=instance_id_headers)
    instance_id = instance_id_response.text

    # Launch a new SSM command
    print(f"Launching new SSM command on instance {instance_id}")

    # Initialize boto3 client using role-based credentials
    ssm_client = boto3.client('ssm')

    child_script_content = """
import json
import datetime

print("Child SSM command executed!")
print(f"Current time: {datetime.datetime.now()}")
print(f"Received data: {json.loads('__JSON_PLACEHOLDER__')}")
"""

    # Replace placeholder with actual data
    child_script_content = child_script_content.replace("__JSON_PLACEHOLDER__", json.dumps(json_input))

    # Execute the command
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunPythonScript',
        Parameters={
            'pythonScript': [child_script_content]
        },
        Comment=f'Child SSM command launched at {datetime.datetime.now().isoformat()}'
    )

    command_id = response['Command']['CommandId']
    print(f"Launched new SSM command with ID: {command_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Important considerations for this approach:

1. The edge node must have an IAM role with permissions to execute SSM commands
2. The second SSM command runs independently - it's not tied to the first one
3. You need IMDSv2 access to get your own instance ID

## Key Differences Between the Approaches

1. **Subprocess Approach**:
    - Simpler, doesn't require special permissions
    - Child process is tied to parent (will be terminated if parent is)
    - Output is captured by parent process

2. **New SSM Command Approach**:
    - Requires IAM permissions
    - Completely independent execution
    - Shows up as a separate command in the SSM command history
    - Can target different instances

## Recommendation

For most scenarios, the first approach (subprocess) is simpler and sufficient. Use the second approach only if you need
the child process to:

- Run for longer than the SSM timeout
- Have different permissions
- Show up separately in SSM history
- Target a different instance
