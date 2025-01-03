# IAM, Identity and Access Management

AWS Identity and Access Management (IAM) enables you to manage access to AWS services and
resources securely. Using IAM, you can create and manage AWS users and groups, and
use permissions to allow and deny their access to AWS resources. IAM is a feature of your
AWS account offered at no additional charge. You will be charged only for use of other
AWS services by your users. ref https://aws.amazon.com/iam/

Think of it like - every IAM account comes with its own running copy of IAM, its own database.
IAM is a globally resilient service. Its your own dedicated instance of IAM for each account.
You AWS account trusts your instance of IAM like your root user. IAM is a global service and
there no cost for this service

![image](https://user-images.githubusercontent.com/52529498/124613465-4104b480-de41-11eb-9df6-8033cdfb3fa6.png)

IAM - has 3 parts to it:

- IDP, identity provider, create, modify or delete identities such as users and roles.
- Authentciate, authenticates the identity, prove you are who you claim to be.
- Authorize, allow or deny access to resources. Policies by themselves do nothing, they simply allow or deny when
  attached to an identity. To access resources – allow or deny based on the policy associated with the identity.

IAM allows identities to be created within an AWS account. IAM identities start with no permissions on an AWS Account,
but can be granted permissions up to that held by the Account Root User.

![image](https://user-images.githubusercontent.com/52529498/124683534-3a0a9000-de9b-11eb-868d-933a1babadf1.png)

Users and Applications cannot directly access AWS, they have to access via IAM Service.

- *Users*, Here represnets humans or applications that need to access AWS account, is an identity
- *Groups*, collections of related users example chemistry department, hr department etc.
- *Role*, used by AWS service or to grant external access to your account, is an identity
- *Policies* by themselves do nothing, they simply allow or deny when attached to an identity. To access resources –
  allow or deny based on the policy associated with the identity.
- AWS Account fully trusts the Account Root user and the IAM service
- AWS root user is the user we first create when we create an AWS account, this should never be used. You shoulc create
  separate accounts with admin permissions to create, manage identities etc.

- What is the difference between an IAM role and an IAM user?
  An IAM user has permanent long-term credentials and is used to directly interact with AWS services. An IAM role does
  not have any credentials and cannot make direct requests to AWS services. IAM roles are meant to be assumed by
  authorized entities, such as IAM users, applications, or an AWS service such as EC2.
- When should I use an IAM user, IAM group, or IAM role?
  An IAM user has permanent long-term credentials and is used to directly interact with AWS services. An IAM group is
  primarily a management convenience to manage the same set of permissions for a set of IAM users. An IAM role is an AWS
  Identity and Access Management (IAM) entity with permissions to make AWS service requests. IAM roles cannot make
  direct requests to AWS services; they are meant to be assumed by authorized entities, such as IAM users, applications,
  or AWS services such as EC2. Use IAM roles to delegate access within or between AWS accounts.
  ref: https://aws.amazon.com/iam/faqs/

## Role

In AWS, a Role is a type of identity that represents a set of permissions. However, unlike a regular user account, a
Role is meant to be assumed/taken on temporarily by:

1. AWS services - For example, an EC2 instance might need to assume a Role to access S3 buckets
2. External users/services - Like allowing users from another AWS account or third-party service to access resources in
   your account

Think of a Role like a temporary security badge that can be handed out. When someone or something assumes a Role, they
get the permissions associated with that Role for a limited time, but they don't have permanent credentials like a
regular user would.


- **Service Role**, is applicable within the same aws account. Example EC2 accessing S3 bucket, all applications running
  on EC2 will be able to access this S3 bucket
    - Login into AWS Console
    - Select IAM service
    - **Create** a policy permission file for S3 access
    - Select S3 service, choose appropriate settings
    - **Next** create a Role
    - Select type of trusted entity **"AWS Service"**
    - Select EC2
    - Attach the above S3 permission policy file you just created
    - Now on EC2 startup this service role will make sure it gets the token and key and stores it in the EC2 instance.
      So any applications running in the Ec2 instance can use these tokens to access S3


- **Delegated Role**, cross account access.
    - ![Delegated Role](https://user-images.githubusercontent.com/52529498/126061958-d728115f-b453-423c-92c7-50531db038de.png)
    - In the above figure we have 2 AWS accounts Act#1 and Act#3. Aws account#1 has UserA and account#3 has UserC.
      Acct#1 is the trusted account and Acct#3 is the trusting account. We create a permission policy for S3 on
      account#3 and trust policy for Acct#1
    - On Account #3
        - Assuming that youa re logged into the AWS console, IAM Service and you already have a S3 permission policy
          created.
        - Create Role
        - Select type of trusted entity "Another AWS account"
        - Add Account #1
        - Attach s3 readonly permission policy, name and save it
        - get the Role ARN and note it down.
    - On Account #1
        - create policy, name it Assume-S3-Read-Only
        - Choose service **STS**
        - choose assume role
        - add above noted ARN
        - ![image](https://user-images.githubusercontent.com/52529498/149468833-b62a7a64-9a2d-48f8-8645-ac32d65c41b9.png)

    - On Account #1 again
        - addabove Assume-S3-ReadOnly policy to User A
        -

- **Federated Role**, trust relationship between AWS account(trusting account) and Trusted Account - on-premise identity
  provide like Active Directory or Web Identity provider like Google, Facebook, AWS Cognito, etc...

![image](https://user-images.githubusercontent.com/52529498/124744426-bd080680-deec-11eb-87d0-b6b15dfad2aa.png)

- **Service linked Role**, this role lasts for very short time. It provides all the different permissions that that
  service will need while it's performing the job. One example is CloudFormation, it needs to do certain things, but
  only when we tell it to do the job. When you run CloudFormation, this role would basically grant access to S3, EC2, or
  maybe even the database services, and would use the service-linked role with the temporary credentials in order to
  accomplish the deployment of those instances and buckets.


- aws sts get-caller-identity

<pre>
{
    "UserId": "AIDAZ77QOIYWWERTTYYYU",
    "Account": "00000000000000",
    "Arn": "arn:aws:iam::00000000000000:user/serverless-user"
}

</pre>


### How AWS Roles works

Let me explain how AWS Roles work in practice with some common scenarios:

1. Service-to-Service Access
   For example, imagine you have an EC2 instance that needs to read from an S3 bucket:

- Instead of storing AWS credentials on the EC2 instance (which would be insecure)
- You create a Role with permissions to read from that specific S3 bucket
- You attach this Role to the EC2 instance
- The EC2 instance can now automatically get temporary credentials to access S3

2. Cross-Account Access
   Say Company A wants to let Company B access some of their AWS resources:

- Company A creates a Role with specific permissions
- Company A configures the Role to trust Company B's AWS account
- Users from Company B can then temporarily "assume" this Role to access the allowed resources
- This is much safer than creating permanent user accounts

3. Federation with External Identity Providers
   For organizations using corporate directories:

- You can create Roles that map to groups in your corporate directory
- When employees sign in through your directory (like Active Directory)
- They automatically get assigned the appropriate AWS Role based on their group membership

4. Lambda Functions
   When creating Lambda functions:

- Each function needs an "execution role"
- This Role determines what AWS services the function can interact with
- For example, a Role might allow the function to write logs to CloudWatch and access items in DynamoDB

The key advantages of using Roles are:

- No need to manage long-term credentials
- Temporary credentials that automatically rotate
- Fine-grained access control
- Clear audit trail of who assumed what Role and when

### Role in Details

Let me dive deeper into some of the more technical aspects of AWS Roles:

1. Role Session Duration

- When someone or a service assumes a Role, they get temporary credentials
- Default session duration is 1 hour
- Can be configured from 15 minutes up to 12 hours
- The credentials automatically expire after the session duration
- AWS STS (Security Token Service) handles the temporary credential creation

2. Role Trust Policy vs Permission Policy
   A Role has two key policies:

```json
// Trust Policy - Who can assume this role
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

// Permission Policy - What the role can do
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
```

3. Assuming a Role Programmatically
   Using AWS CLI:

```bash
aws sts assume-role \
    --role-arn arn:aws:iam::ACCOUNT-ID:role/ROLE-NAME \
    --role-session-name SOME-SESSION-NAME
```

Or in Python using boto3:

```python
import boto3

sts_client = boto3.client('sts')
assumed_role_object = sts_client.assume_role(
    RoleArn="arn:aws:iam::ACCOUNT-ID:role/ROLE-NAME",
    RoleSessionName="AssumeRoleSession1"
)

# Use the temporary credentials
credentials = assumed_role_object['Credentials']
```

4. Role Chaining

- Roles can be assumed by users/services that themselves have temporary credentials
- Maximum chain length is limited
- Each assumption in the chain must have permission to assume the next role
- Commonly used in complex cross-account scenarios

5. Instance Profiles
   For EC2 instances:

- An instance profile is a container for a role
- When you "attach a role" to an EC2 instance, you're actually attaching an instance profile
- The instance profile automatically handles credential rotation
- Applications on the instance can get credentials from the instance metadata service

## Advanced concepts and best practices for AWS Roles:

1. Condition Keys in Role Policies
   You can add sophisticated conditions to control when a Role can be used:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT-ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Department": "Engineering"
        },
        "IpAddress": {
          "aws:SourceIp": [
            "203.0.113.0/24"
          ]
        },
        "DateGreaterThan": {
          "aws:CurrentTime": "2024-01-01T00:00:00Z"
        }
      }
    }
  ]
}
```

2. Permission Boundaries

- A powerful feature for delegating Role management
- Sets a maximum permission ceiling
- Even if someone adds permissions to a Role, they can't exceed the boundary

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

3. Role Last Used
   AWS tracks when a Role was last used:

- Visible in IAM console
- Available through AWS API
- Helpful for identifying unused Roles
- Best practice: regularly audit and remove unused Roles

4. Service-Linked Roles
   Special type of Role that's linked to an AWS service:

- Created automatically by services
- Predefined permissions that only that service can assume
- Can't modify the permissions
- Automatically deleted when service no longer needs it
  Example services using service-linked roles:
- Amazon EMR
- AWS Organizations
- Amazon ECS

5. Role Tags
   You can attach tags to Roles for:

- Cost allocation
- Access control
- Resource organization

```bash
aws iam tag-role \
    --role-name MyRole \
    --tags '[{"Key": "Environment", "Value": "Production"}]'
```

6. Emergency Access Process
   Best practice for break-glass scenarios:

- Create emergency access Roles
- Require MFA
- Highly restricted trust policy
- Detailed CloudTrail logging
- Regular rotation of credentials

7. Role Session Policies
   When assuming a Role, you can further restrict permissions:

```python
assumed_role = sts_client.assume_role(
    RoleArn="arn:aws:iam::ACCOUNT-ID:role/MyRole",
    RoleSessionName="RestrictedSession",
    Policy='{
           "Version": "2012-10-17",
"Statement": [{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*"
}]
}'
)
```

## Policy

A policy in AWS is like a set of rules written in JSON, but by itself, it's just a document - it doesn't do anything
until it's attached to something. Think of it like a rulebook sitting on a shelf - it only becomes effective when you
give it to someone to follow.

Here's how it works:

1. Policy Structure

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

2. Attachment Process
   The policy becomes active only when attached to:

- IAM Users
- IAM Groups
- IAM Roles
- Resources (like S3 buckets, in case of resource-based policies)

3. Real-world Example:
   Let's say you have this policy that allows S3 access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::company-reports/*"
    }
  ]
}
```

Scenarios:

- If this policy exists but isn't attached to anything → No effect
- If attached to User A → User A can read from company-reports bucket
- If attached to Role B → Any entity assuming Role B can read from company-reports bucket
- If attached to Group C → All users in Group C can read from company-reports bucket

4. Policy Evaluation:
   When someone tries to access a resource:

- AWS checks the identity (who are you?)
- Looks at all policies attached to that identity
- Evaluates if the action is allowed or denied
- Grants or denies access based on the evaluation

5. Important Concepts:

- Explicit Deny always wins
- No permissions are granted by default (implicit deny)
- Multiple policies are evaluated together
- Both identity-based and resource-based policies are considered

### Deeper dive into policy evaluation and how AWS makes access decisions:

1. Policy Evaluation Logic Flow

```json
// Example of multiple policies on one identity
// Policy 1 - Attached to User
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::bucket-a/*"
}

// Policy 2 - Inherited from Group
{
  "Effect": "Allow",
  "Action": [
    "s3:DeleteObject"
  ],
  "Resource": "arn:aws:s3:::bucket-a/*"
}

// Policy 3 - Explicit Deny in another Group
{
  "Effect": "Deny",
  "Action": [
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::bucket-a/confidential/*"
}
```

2. Evaluation Order
   AWS evaluates policies in this order:
1. Explicit DENY → If found, access is denied immediately
2. Organizations SCPs (Service Control Policies) → Must allow
3. Resource-based policies → Must allow if applicable
4. IAM permissions boundaries → Must allow
5. Session policies → Must allow
6. Identity-based policies → Must allow

3. Cross-Account Access Example:

```json
// Account A - Role Trust Policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT-B-ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-exampleorgid"
        }
      }
    }
  ]
}

// Account B - User Policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::ACCOUNT-A-ID:role/CrossAccountRole"
    }
  ]
}
```

4. Permission Boundaries in Action:

```json
// Permission Boundary
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}

// User Policy (restricted by boundary)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "ec2:*",
        // This won't work due to boundary
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Real-world Policy Evaluation Example:
   Consider a user trying to upload a file to S3:

```python
# AWS Policy Evaluation Process
def evaluate_access(request):
    # 1. Check Organization SCP
    if not allowed_by_scp(request):
        return "DENY"

    # 2. Check explicit denies
    if has_explicit_deny(request):
        return "DENY"

    # 3. Check permission boundary
    if has_permission_boundary and not allowed_by_boundary(request):
        return "DENY"

    # 4. Check identity policies
    if not allowed_by_identity_policies(request):
        return "DENY"

    # 5. Check resource policies
    if requires_resource_policy and not allowed_by_resource_policy(request):
        return "DENY"

    return "ALLOW"
```

## Policy

A policy is an object in AWS that, when associated with an entity or resource example S3,lambda,ec2 etc.., defines their
permissions. AWS evaluates these policies when a principal, such as a user, makes a request. Permissions in the policies
determine whether the request to a resource is allowed or denied. Most policies are stored in AWS as JSON documents.

- Trust policy There are two parts to a trust policy
    - trusting account, is the account that has the resources that you want and is the account that's trusting you.
    - the trusted account, is account that is going to contain the users who will be accessing the resources.

- Permission policy, Permissions in the policies determine whether the request to a resource is allowed or denied. The
  following example policy
  grants the s3:GetObject permission to any public anonymous users

<pre>
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"PublicRead",
      "Effect":"Allow",
      "Principal": "*",
      "Action":["s3:GetObject","s3:GetObjectVersion"],
      "Resource":["arn:aws:s3:::my-bucket/*"]
    }
  ]
}
specifying Principal: * in your policy above, the danger here is that you’ve  authorized Any AWS Customer to access your bucket.
</pre>

- [AWS Identity and Access Management (IAM) and AWS IAM Identity Center](https://jumpcloud.com/blog/aws-iam-vs-aws-sso)
