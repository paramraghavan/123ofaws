**VPC vs PrivateLink**
VPC and PrivateLink solve different problems.

```text
VPC = where your private resources live
PrivateLink = private access from your VPC to AWS service APIs
```

**VPC**
Use VPC networking when Lambda needs to reach something that actually lives inside your VPC.

Examples:

```text
Lambda -> EFS
Lambda -> RDS
Lambda -> private EC2 IP
Lambda -> internal load balancer
```

These resources have private IPs in your VPC/subnets.

For example, EFS is reached through EFS mount targets in your VPC:

```text
Lambda in private subnet
  -> EFS mount target on TCP 2049
  -> shared filesystem
```

That is VPC networking, not PrivateLink.

**PrivateLink**
Use PrivateLink when Lambda needs to call AWS service APIs privately from inside your VPC.

Examples:

```text
Lambda -> SSM API
Lambda -> EC2 API
Lambda -> SQS API
Lambda -> SNS API
Lambda -> CloudWatch Logs API
```

These APIs are not “inside your VPC.” They are regional AWS service endpoints, such as:

```text
ssm.us-east-1.amazonaws.com
ec2.us-east-1.amazonaws.com
```

By default, those are public AWS API endpoints.

PrivateLink gives your VPC a private doorway to those APIs. AWS creates interface endpoint ENIs with private IPs inside
your subnets.

```text
Lambda in private subnet
  -> VPC interface endpoint private IP
  -> AWS SSM regional service
```

With private DNS enabled, your code does not change:

```python
boto3.client("ssm").send_command(...)
boto3.client("ec2").describe_instances(...)
```

But DNS resolves the AWS service name to the private endpoint IP inside your VPC.

So the key distinction is:

```text
SSM API itself = regional AWS service, outside your VPC
SSM interface endpoint = private ENI inside your VPC

EC2 API itself = regional AWS service, outside your VPC
EC2 interface endpoint = private ENI inside your VPC
```

**For Your Architecture**
Your private design can look like this:

```text
SNS -> SQS -> Lambda in private subnet
              |
              | PrivateLink / VPC endpoint
              v
        EC2 API: describe edge nodes
              |
              | PrivateLink / VPC endpoint
              v
        SSM API: send command
              |
              v
        edge node runs job
```

If Lambda also mounts the shared filesystem:

```text
Lambda in private subnet
  -> EFS mount target using VPC networking
  -> /mnt/shared/edge-scheduler/leases
```

So both can be used together:

```text
Lambda -> EFS = VPC networking
Lambda -> EC2 DescribeInstances API = PrivateLink
Lambda -> SSM SendCommand API = PrivateLink
```

**Endpoints You May Need**
For Lambda privately calling AWS APIs:

```text
com.amazonaws.<region>.ec2
com.amazonaws.<region>.ssm
com.amazonaws.<region>.logs
```

If Lambda code directly calls SQS or SNS APIs:

```text
com.amazonaws.<region>.sqs
com.amazonaws.<region>.sns
```

For EC2 control/edge nodes using SSM without internet/NAT:

```text
com.amazonaws.<region>.ssm
com.amazonaws.<region>.ssmmessages
com.amazonaws.<region>.ec2messages
```

**Simple Rule**

```text
If the target is a private resource in your VPC, use VPC networking.

If the target is an AWS service API and you want private access, use PrivateLink / VPC endpoints.
```

In your case, SSM API and EC2 API are **not inside your VPC**. They are AWS regional services. PrivateLink lets Lambda
and EC2 nodes reach them privately from inside the VPC.