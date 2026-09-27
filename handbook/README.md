# AWS and Boto3 Handbook

This folder is a practical AWS/Boto3 reference for data engineering, production patterns, troubleshooting, and interview
prep. The docs are intentionally local and copy-friendly, but examples should still be reviewed before use in a real AWS
account.

## Start Here

| Goal | Read |
|------|------|
| Need a fast service or syntax reminder | [aws-quick-reference.md](/Users/paramraghavan/dev/123ofaws/handbook/aws-quick-reference.md) |
| Learn Boto3 patterns in depth | [boto3-complete-guide.md](/Users/paramraghavan/dev/123ofaws/handbook/boto3-complete-guide.md) |
| Learn AWS data engineering services | [complete-aws-data-engineering-handbook.md](/Users/paramraghavan/dev/123ofaws/handbook/complete-aws-data-engineering-handbook.md) |
| Implement production-style patterns | [production-patterns-cookbook.md](/Users/paramraghavan/dev/123ofaws/handbook/production-patterns-cookbook.md) |
| Debug an AWS/Boto3 error | [troubleshooting-guide.md](/Users/paramraghavan/dev/123ofaws/handbook/troubleshooting-guide.md) |
| Prepare for AWS + Python interviews | [notes/aws_python_boto3_interview_handbook.md](/Users/paramraghavan/dev/123ofaws/handbook/notes/aws_python_boto3_interview_handbook.md) |

## File Map

| File | Purpose |
|------|---------|
| [aws-quick-reference.md](/Users/paramraghavan/dev/123ofaws/handbook/aws-quick-reference.md) | Fast interview and service-selection reference. |
| [boto3-complete-guide.md](/Users/paramraghavan/dev/123ofaws/handbook/boto3-complete-guide.md) | Boto3 clients/resources, sessions, errors, pagination, waiters, and service examples. |
| [complete-aws-data-engineering-handbook.md](/Users/paramraghavan/dev/123ofaws/handbook/complete-aws-data-engineering-handbook.md) | Broader AWS data engineering handbook. |
| [production-patterns-cookbook.md](/Users/paramraghavan/dev/123ofaws/handbook/production-patterns-cookbook.md) | Reusable production patterns for monitoring, cost, cross-account access, CloudFormation, and SSM. |
| [troubleshooting-guide.md](/Users/paramraghavan/dev/123ofaws/handbook/troubleshooting-guide.md) | Common errors and debugging commands. |
| [notes/aws_python_boto3_interview_handbook.md](/Users/paramraghavan/dev/123ofaws/handbook/notes/aws_python_boto3_interview_handbook.md) | Interview-oriented AWS/Python/Boto3 notes. |

## Security Baseline

Use this baseline for every example in this folder:

- Prefer IAM roles, AWS SSO/IAM Identity Center, or office credential tooling over long-lived IAM user keys.
- Do not hardcode `aws_access_key_id`, `aws_secret_access_key`, passwords, tokens, or API keys in code.
- For local development, prefer named profiles:

```python
import boto3

session = boto3.Session(profile_name="dev", region_name="us-east-1")
s3 = session.client("s3")
```

- For AWS workloads, let the SDK use the attached role:

```python
import boto3

s3 = boto3.client("s3")
```

- For cross-account access, use STS `AssumeRole` and temporary credentials.
- Store configuration in SSM Parameter Store; store rotating or high-value secrets in Secrets Manager.
- Keep CloudTrail enabled and use it while debugging authorization failures.

## Credential Resolution Short Version

Boto3 and the AWS CLI can resolve credentials from several places. The most common are:

1. environment variables
2. named profiles in `~/.aws/credentials` and `~/.aws/config`
3. AWS SSO/IAM Identity Center cache
4. assume-role profiles
5. container, Lambda, ECS task, or EC2 instance role credentials

Check your active identity:

```bash
aws sts get-caller-identity --profile dev
aws configure list --profile dev
```

## Cross-Account Pattern

Two policy checks must pass:

1. The source identity must be allowed to call `sts:AssumeRole` on the target role ARN.
2. The target role trust policy must trust the source identity or account.

Temporary credentials expire. Session length is requested with `DurationSeconds`, bounded by the role's maximum session
duration. Role chaining is limited to 1 hour for the chained session.

## Local Testing

Use LocalStack or a sandbox AWS account for destructive or billing-impacting examples. Before running snippets that
create, modify, or delete resources, check:

- account and region
- active profile
- IAM permissions
- cleanup steps
- expected cost

## Maintenance Notes

When adding examples:

- Use placeholders like `<bucket-name>` and `<role-arn>`, not real-looking keys.
- Prefer profiles and roles over explicit credential parameters.
- Include pagination for list operations that can return many results.
- Include retries or explain when SDK retries are enough.
- Include cleanup for created resources.
