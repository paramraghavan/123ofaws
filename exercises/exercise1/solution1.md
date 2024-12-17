This sounds like a common access control issue. Let me help you troubleshoot:

1. Most likely:
- **IP-based restrictions on the server**
- Missing or incorrect headers
- VPN/Network restrictions
- Security group/firewall rules

Try these steps:

1. Compare headers between working and non-working requests:
```python
import requests

headers = {
    'User-Agent': 'Mozilla/5.0...',  # Use the same User-Agent as your PC
    # Add any other headers from your working request
}

response = requests.get('https://abc.conenct.com', headers=headers)
```

2. Check if IP whitelisting is required:
- Find your AWS edge node's IP address
- Check if it needs to be whitelisted by the server admin
- You can get the IP using:
```python
import requests
print(requests.get('https://checkip.amazonaws.com').text.strip())
```

3. Verify AWS security group settings:
- Ensure outbound HTTPS (port 443) traffic is allowed
- Check Network ACLs if applicable

4. Try with session to maintain cookies:
```python
session = requests.Session()
response = session.get('https://abc.conenct.com', headers=headers)
```
# how to findmy edges nodes instance id
To find your AWS EC2 instance ID when you're already logged into the instance, you can use one of these methods:

1. Using EC2 metadata service:
```bash
curl http://169.254.169.254/latest/meta-data/instance-id
```

2. Using AWS CLI (if installed):
```bash
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId]' --output text
```

3. Check the system log:
```bash
cat /var/log/cloud-init-output.log | grep "instance-id"
```

4. From instance tags (if hostname is set to instance ID):
```bash
hostname
```

The first method (metadata service) is the most reliable and commonly used. 