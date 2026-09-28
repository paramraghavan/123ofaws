# IAM (Identity and Access Management): Comprehensive Tutoring Guide

> **Master AWS IAM**: Learn how to securely manage identities, permissions, and access control to AWS resources. This guide covers everything from basic concepts to advanced cross-account access patterns.

AWS Identity and Access Management (IAM) enables you to manage access to AWS services and resources securely. Using IAM, you can create and manage AWS users and groups, and use permissions to allow and deny their access to AWS resources. IAM is offered at no additional charge.

---

## Table of Contents

1. [What is IAM?](#what-is-iam)
2. [Core Concepts](#core-concepts)
3. [IAM Components: Users, Groups, Roles](#iam-components)
4. [Policies: The Rules](#policies-the-rules)
5. [IAM Roles in Detail](#iam-roles-in-detail)
6. [Service Roles vs Delegated Roles](#service-roles-vs-delegated-roles)
7. [Cross-Account Access](#cross-account-access)
8. [Policy Evaluation Logic](#policy-evaluation-logic)
9. [Common Mistakes & Best Practices](#common-mistakes--best-practices)
10. [Troubleshooting IAM](#troubleshooting-iam)
11. [Real-World Scenarios](#real-world-scenarios)

---

## What is IAM?

**IAM (Identity and Access Management)** is AWS's service for managing **who can do what** in your AWS account.

Think of it like a **security checkpoint**:
- **Identity**: Who are you? (Users, Roles, Applications)
- **Authentication**: Prove you are who you claim to be (credentials, tokens)
- **Authorization**: What are you allowed to do? (Policies, permissions)

### Visual Overview: IAM Architecture

![IAM Architecture Overview](https://user-images.githubusercontent.com/52529498/124613465-4104b480-de41-11eb-9df6-8033cdfb3fa6.png)

### Key Facts:

✅ **Global service** - Works across all AWS regions
✅ **Free** - No charges for using IAM itself
✅ **Always enabled** - Every AWS account has IAM
✅ **Integrated** - Used by all AWS services
✅ **Flexible** - Fine-grained control down to individual API actions

**IAM has 3 parts:**
- **IDP (Identity Provider)**: Create, modify, or delete identities such as users and roles
- **Authentication**: Proves you are who you claim to be (using credentials or tokens)
- **Authorization**: Allow or deny access to resources based on policies

### Simple Analogy:

```
Without IAM:
  AWS Account = Unlocked door
  Anyone with account password = Full access (dangerous!)

With IAM:
  AWS Account = Secure building
  Users = Employees with badge access
  Roles = Position-specific permissions
  Policies = Rules defining what each badge can do
```

---

## Core Concepts

### The IAM Trust Model

```
┌─────────────────────────────────────────────────────────┐
│ AWS Account                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  AWS Root User (Most Privileged - DON'T USE!)          │
│        ↓                                                │
│  AWS Account fully trusts:                             │
│  ├─ Root User                                          │
│  └─ IAM Service (Identity Provider)                    │
│        ↓                                                │
│  IAM Service manages:                                   │
│  ├─ Users (human/app identities)                       │
│  ├─ Roles (temporary access credentials)               │
│  ├─ Groups (collections of users)                      │
│  └─ Policies (permission rules)                        │
│        ↓                                                │
│  Everything else needs permission via IAM              │
│  (EC2, S3, Lambda, DynamoDB, etc.)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**IAM Identities Architecture:**

![IAM Identities](https://user-images.githubusercontent.com/52529498/124683534-3a0a9000-de9b-11eb-868d-933a1babadf1.png)

**Key Insight**: Users and Applications cannot directly access AWS—they have to access via IAM Service.

---

## IAM Components

### Users vs Groups vs Roles: Quick Reference

| Feature | User | Group | Role |
|---------|------|-------|------|
| **Long-term credentials?** | ✅ Yes (permanent) | N/A | ❌ No (temporary) |
| **Who uses it?** | Humans, Applications | Management only | Services, Cross-account access |
| **Direct access to AWS?** | ✅ Yes | ❌ No (contains users) | ❌ No (must be assumed) |
| **Credential type** | Access keys, password | N/A | Temporary tokens (STS) |
| **Session duration** | Indefinite | N/A | 15 min - 12 hours |
| **Use case** | Individual identity | Manage multiple users | Delegation, Services |
| **Example** | Developer Alice | Engineering team | EC2 instance access |

### When to Use Each

```
USERS - For direct, permanent access:
  ✅ Individual developers
  ✅ Operations team members
  ✅ Applications needing long-term credentials
  ❌ NOT for services (use Roles instead)
  ❌ NOT for temporary access (use Roles instead)

GROUPS - For managing multiple users:
  ✅ Organize users by department (Engineering, Finance)
  ✅ Apply same permissions to multiple users
  ✅ Simplify access management
  ❌ NOT a security boundary (just a management tool)

ROLES - For temporary, delegated access:
  ✅ EC2 instances accessing S3
  ✅ Lambda functions accessing databases
  ✅ Cross-account access
  ✅ Federated external users
  ✅ Any temporary access scenario
```

---

## Policies: The Rules

### What is a Policy?

A **policy is a JSON document** that defines permissions. By itself, it does nothing. **A policy only becomes effective when attached to an identity** (User, Group, or Role).

```
Policy = Rulebook (dormant until attached)
User/Role = Person following the rules
```

### Policy Structure

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DescriptiveStatementName",
      "Effect": "Allow",              // or "Deny"
      "Action": [
        "s3:GetObject",               // service:action format
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket/*"    // What resources
      ],
      "Condition": {                  // Optional: when does it apply?
        "StringEquals": {
          "aws:username": "alice"
        }
      }
    }
  ]
}
```

### Understanding Each Field

```yaml
Version: "2012-10-17"
  └─ Policy language version (always this one)

Statement: [...]
  └─ Array of rules (can have multiple statements)

Sid: "DescriptiveName"
  └─ Statement ID (for clarity, optional)

Effect: "Allow" or "Deny"
  └─ Allow: Grant permission
  └─ Deny: Explicitly block (takes precedence)

Action: ["service:action"]
  └─ Which API calls are allowed
  └─ Format: service:action (s3:GetObject, ec2:DescribeInstances)
  └─ Wildcards: s3:* (all S3), *:* (all actions, dangerous!)

Resource: ["arn:..."]
  └─ Which AWS resources the action applies to
  └─ ARN format: arn:partition:service:region:account-id:resource
  └─ Example: arn:aws:s3:::my-bucket/uploads/*

Condition: {...}
  └─ When does the permission apply? (optional)
  └─ StringEquals, IpAddress, DateGreaterThan, etc.
```

---

## IAM Roles in Detail

### What is a Role?

A **Role is an identity with no long-term credentials**. Instead, it has:
- **Trust policy**: Who can assume (use) this role
- **Permission policy**: What they can do when they assume it
- **Temporary credentials**: Valid for 15 minutes to 12 hours

Think of a Role like a **temporary security badge** that can be handed out. When someone or something assumes a Role, they get the permissions associated with that Role for a limited time.

---

## Service Roles vs Delegated Roles

### Service Role (Same Account)

**Use case**: AWS service needs access to other AWS resources in the same account

**Example**: EC2 instance accessing S3 bucket, all applications running on EC2 will be able to access this S3 bucket

**Setup Process**:
1. Login into AWS Console
2. Select IAM service
3. **Create** a policy permission file for S3 access
4. Select S3 service, choose appropriate settings
5. **Next** create a Role
6. Select type of trusted entity **"AWS Service"**
7. Select EC2
8. Attach the above S3 permission policy file you just created
9. Now on EC2 startup this service role will make sure it gets the token and key and stores it in the EC2 instance.

So any applications running in the Ec2 instance can use these tokens to access S3


### Delegated Role (Cross-Account)

**Use case**: User in one AWS account needs access to resources in another account

**Example**: Company A's user accessing Company B's S3 bucket

**Visual Reference:**

![Delegated Role Architecture](https://user-images.githubusercontent.com/52529498/126061958-d728115f-b453-423c-92c7-50531db038de.png)

We have 2 AWS accounts:
- **Account A** (Trusted account): Contains users
- **Account B** (Trusting account): Contains resources

**Setup Steps**:

1. **On Account B (Trusting Account)**:
   - Assuming that you  are logged into the AWS console, IAM Service and you already have a S3 permission policy created.
   - Create a role for S3 access
   - Add a trust policy allowing Account A users
   - Attach S3 permission policy
   - Note the Role ARN

2. **On Account A (Trusted Account)**:
   - Create policy for `sts:AssumeRole`
   - ![Cross-Account Assume Role Policy](https://user-images.githubusercontent.com/52529498/149468833-b62a7a64-9a2d-48f8-8645-ac32d65c41b9.png)
   - Add the Account B role ARN to the policy
   - Attach this policy to the user

---

### Other Role Types

**Federated Role**: Trust relationship between AWS account and external identity provider (Active Directory, Google, Facebook, AWS Cognito, etc.)

![Federated Role Architecture](https://user-images.githubusercontent.com/52529498/124744426-bd080680-deec-11eb-87d0-b6b15dfad2aa.png)

**Service-Linked Role**: Short-lived role that provides permissions a service needs while performing its job. Example: CloudFormation needs temporary access to S3, EC2, databases to deploy resources.

---

## Cross-Account Access

### How It Works

```
┌──────────────────────────────────────────┐     ┌──────────────────────────────────────┐
│ AWS Account A (Trusted)                  │     │ AWS Account B (Trusting)             │
│                                          │     │                                      │
│ User: alice                              │     │ Role: CrossAccountS3Access           │
│   ↓                                      │     │   ↓                                  │
│ Has permission to assume                 │────→│ Trust Policy: Allow Account A         │
│ CrossAccountS3Access role                │     │   ↓                                  │
│                                          │     │ Permission: S3 Read-Only             │
│                                          │     │                                      │
└──────────────────────────────────────────┘     └──────────────────────────────────────┘
```

---

## Policy Evaluation Logic

### The Access Decision Process

When you try to access an AWS resource:

```
User tries to do something:
  "s3:GetObject on arn:aws:s3:::my-bucket/file.txt"
           ↓
AWS checks: Is there an explicit DENY?
  ├─ YES → Access DENIED ❌
  └─ NO → Continue
           ↓
AWS checks: Is there an explicit ALLOW?
  ├─ YES → Access ALLOWED ✅
  └─ NO → Access DENIED ❌

Remember: Explicit DENY always wins!
```

### Policy Evaluation Order

AWS evaluates policies in this order. **First match wins**:

1. **Explicit DENY** (immediate block)
2. Organization SCPs (Service Control Policies)
3. Resource-based policies (like S3 bucket policies)
4. IAM permission boundaries
5. Session policies
6. Identity-based policies (User/Role policies)

---

## Common Mistakes & Best Practices

### ❌ Mistake 1: Using Root User for Daily Work

```
❌ DON'T:
aws s3 ls --region us-east-1
# Using root user credentials

✅ DO:
# Create IAM user with only needed permissions
aws iam create-user --user-name alice
# Use alice's credentials instead
```

**Why?** Root user = full account control. If compromised, entire AWS account is at risk.

### ❌ Mistake 2: Hardcoding Access Keys

```python
# ❌ DON'T: Hardcoded in code
s3 = boto3.client('s3',
    aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/...'
)

# ✅ DO: Use IAM role (auto-rotates)
s3 = boto3.client('s3')
# EC2/Lambda automatically provides credentials via role
```

### ❌ Mistake 3: Too Broad Permissions

```json
// ❌ DON'T: Allows everything on everything
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}

// ✅ DO: Least privilege - only what's needed
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::my-bucket",
    "arn:aws:s3:::my-bucket/*"
  ]
}
```

### ✅ Best Practices Checklist

```
IDENTITY MANAGEMENT:
☐ Never use Root user for daily work
☐ Enable MFA on all user accounts
☐ Rotate access keys every 90 days
☐ Use IAM roles for services (not users)
☐ Use groups to manage multiple users

PERMISSIONS:
☐ Apply least privilege principle
☐ Be specific with resources (not *)
☐ Be specific with actions (not *)
☐ Use resource tags for fine-grained control
☐ Regularly audit who has what access

CROSS-ACCOUNT:
☐ Use roles for cross-account access
☐ Specify exact accounts in trust policies
☐ Add conditions (IP restrictions, MFA)
☐ Log all cross-account access

CREDENTIALS:
☐ Store access keys securely (AWS Secrets Manager)
☐ Rotate credentials regularly
☐ Never commit credentials to Git
☐ Use temporary credentials when possible
☐ Monitor unused credentials

AUDIT & MONITORING:
☐ Enable CloudTrail logging
☐ Review IAM changes regularly
☐ Set up alerts for suspicious activity
☐ Use AWS Access Analyzer
☐ Monitor failed login attempts
```

---

## Troubleshooting IAM

### Common Error: "Access Denied"

**What it means**: You tried to do something but don't have permission

**How to troubleshoot:**

```bash
# 1. Verify your identity
aws sts get-caller-identity
# Output tells you: User ARN, Account ID

# 2. Check what policies are attached
aws iam list-user-policies --user-name alice

# 3. Simulate the action (see if it's allowed)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/alice \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::my-bucket/file.txt

# 4. Check CloudTrail logs
aws cloudtrail lookup-events \
  --event-name AssumeRole \
  --max-results 10
```

### Common Error: "User is not authorized to perform: iam:CreateUser"

**Fix**: Attach proper IAM policy with CreateUser and related permissions

### Common Error: "Role Cannot Be Assumed"

**Possible causes:**
- Trust policy doesn't allow your account
- Trust policy doesn't allow your user
- You don't have sts:AssumeRole permission
- IP restrictions block you
- Session policies are too restrictive

---

## Real-World Scenarios

### Scenario 1: Startup with Multiple Teams

```
Organization:
├─ Engineering team (developers, devops)
├─ Finance team (accountants, analysts)
└─ Operations team (SREs, on-call)

IAM Structure:

1. Create groups:
   - engineering-group
   - finance-group
   - operations-group

2. Create users and add to groups:
   - alice, bob → engineering-group
   - charlie → finance-group
   - diana → operations-group

3. Attach policies to groups:
   - engineering-group: EC2, Lambda, S3, CloudWatch
   - finance-group: Cost Explorer, Billing (read-only)
   - operations-group: All production resources (with MFA)
```

### Scenario 2: Microservices in ECS

Each microservice needs different AWS permissions - create separate roles for each service with least privilege.

### Scenario 3: Third-Party Integration

Third-party vendor needs read-only access to your S3 logs:
1. Create role with S3 read-only permissions
2. Add trust policy with vendor's AWS account
3. Share role ARN with vendor
4. Vendor assumes role to access logs

---

## Quick Reference: ARN Format

```
arn:partition:service:region:account-id:resource

Examples:
- User:     arn:aws:iam::123456789012:user/alice
- Role:     arn:aws:iam::123456789012:role/S3Access
- Group:    arn:aws:iam::123456789012:group/engineers
- S3:       arn:aws:s3:::my-bucket/path/*
- EC2:      arn:aws:ec2:us-east-1:123456789012:instance/*
- Lambda:   arn:aws:lambda:us-east-1:123456789012:function:myFunc

Note: IAM resources don't include region (use ::)
```

---

## Key Takeaways

✅ **Root user**: Never use for daily work - too powerful
✅ **Users**: For human/application identities with long-term credentials
✅ **Roles**: For temporary access - services and cross-account
✅ **Policies**: Attach to identities to grant permissions
✅ **Least Privilege**: Only grant needed permissions
✅ **MFA**: Always enable on important accounts
✅ **Audit**: Enable CloudTrail for all access logging

---

## References

- [AWS IAM Documentation](https://docs.aws.amazon.com/iam/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Policy Evaluation Logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [ARN Format and Examples](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html)

---

**Key Takeaway**: IAM is the foundation of AWS security. Master it, and you'll write secure infrastructure. Ignore it, and you're one mistake away from a breach.
