# IAM, Identity and Access Management

AWS Identity and Access Management (IAM) enables you to manage access to AWS services and 
resources securely. Using IAM, you can create and manage AWS users and groups, and 
use permissions to allow and deny their access to AWS resources. IAM is a feature of your 
AWS account offered at no additional charge. You will be charged only for use of other 
AWS services by your users. ref https://aws.amazon.com/iam/


Every IAM account comes with its own running copy of IAM, its own database.
IAM is a globally resilient service. Its your own dedicated instance of IAM for each account.
You AWS account trusts your instance of IAM like your root user. IAM is a global service and
there no cost for this service

![image](https://user-images.githubusercontent.com/52529498/124613465-4104b480-de41-11eb-9df6-8033cdfb3fa6.png)

IAM - has 3 parts to it:
- IDP, identity provider, create, modify or delete identities such as users and roles. 
- Authentciate, authenticates the identity, prove you are who you claim to be.
- Authorize,  allow or deny access to resources. Policies by themselves do nothing, they simply allow or deny when attached to an identity. To access resources – allow or deny based on the policy associated with the identity.

IAM allows identities to be created within an AWS account. IAM identities start with no permissions on an AWS Account, but can be granted permissions up to that held by the Account Root User.

![image](https://user-images.githubusercontent.com/52529498/124683534-3a0a9000-de9b-11eb-868d-933a1babadf1.png)

Users and Applications cannot directly access AWS, they have to access via IAM Service.
- *Users*, Here represnets humans or applications that need to access AWS account, is an identity
- *Groups*, collections of related users example chemistry department, hr department etc.
- *Role*, used by AWS service or to grant external access to your account, is an identity
- *Policies* by themselves do nothing, they simply allow or deny when attached to an identity. To access resources – allow or deny based on the policy associated with the identity.
- AWS Account fully trusts the Account Root user and the IAM service
- AWS root user is the user we first create when we create an AWS account, this should never be used. You shoulc create other separate accounts  with admin permissions to create, manage identities etc.

- What is the difference between an IAM role and an IAM user?
An IAM user has permanent long-term credentials and is used to directly interact with AWS services. An IAM role does not have any credentials and cannot make direct requests to AWS services. IAM roles are meant to be assumed by authorized entities, such as IAM users, applications, or an AWS service such as EC2.
- When should I use an IAM user, IAM group, or IAM role?
An IAM user has permanent long-term credentials and is used to directly interact with AWS services. An IAM group is primarily a management convenience to manage the same set of permissions for a set of IAM users. An IAM role is an AWS Identity and Access Management (IAM) entity with permissions to make AWS service requests. IAM roles cannot make direct requests to AWS services; they are meant to be assumed by authorized entities, such as IAM users, applications, or AWS services such as EC2. Use IAM roles to delegate access within or between AWS accounts.
ref: https://aws.amazon.com/iam/faqs/

## Policy
A policy is an object in AWS that, when associated with an entity or resource example S3,lambda,ec2 etc.., defines their permissions. AWS evaluates these policies when a principal, such as a user, makes a request. Permissions in the policies determine whether the request to a resource is allowed or denied. Most policies are stored in AWS as JSON documents.
- Trust policy There are two parts to a trust policy
  - trusting account, is the account that has the resources that you want and is the account that's trusting you.
  - the trusted account, is account that is going to contain the users who will be accessing the resources. 
  
- Permission policy,  Permissions in the policies determine whether the request to a resource is allowed or denied. The following example policy 
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

## Roles
- Service Role, is applicable within the same aws account. Example EC2 accessing S3 bucket, all applications running on EC2 will be able to access this S3 bucket
  - **Create** a  policy permission file for S3  access
  - Select S3 service, choose appropriate settings
  - **Next** create a Role
  - Select type of trusted entity **"AWS Service"**
  - Select EC2
  - Attach the above S3 permission policy file you just created
  - Now on EC2 startup this service role will make sure  it gets the token and key and stores it in the EC2 instance. So any applications running in the Ec2 instance can use these tokens to access S3
- Delegated Role, cross account access.
![image](https://user-images.githubusercontent.com/52529498/124733796-87f6b680-dee2-11eb-9dc4-e0f487633e9d.png)

- Service linked Role
- 
