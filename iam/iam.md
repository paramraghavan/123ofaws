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

IAM - has 3 parts to it 
- IDP, identity provider – create, modify or delete identities such as users and roles. IAM identities start with no permissions on an AWS Account, but can be granted permissions (almost) up to those held by the Account Root User.
- Authentciate - authenticates the identity, prove you are who you claim to be-
-IAM authorizes - Allow or deny access to resources. Policies by themselves do nothing, they simply allow or deny when attached to an identity. To access resources – allow or deny based on the policy associated with the identity.

IAM is what allows additional identities to be created within an AWS account. IAM identities start with no permissions on an AWS Account, but can be granted permissions up to that held by the Account Root User.
