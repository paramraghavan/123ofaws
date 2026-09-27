# AWS IAM Notes

This folder is a practical reference for AWS IAM, STS `AssumeRole`, AWS CLI profiles, and the local
`credential_process` helper in this directory.

## Files

| File | Purpose |
|------|---------|
| [credential_helper.py](/Users/paramraghavan/dev/123ofaws/iam/credential_helper.py) | Canonical AWS `credential_process` helper. |
| [aws_creds_helper.py](/Users/paramraghavan/dev/123ofaws/iam/aws_creds_helper.py) | Backward-compatible wrapper for `credential_helper.py`. |
| [aws_credentials_helper.md](/Users/paramraghavan/dev/123ofaws/iam/aws_credentials_helper.md) | AWS CLI credential patterns and helper setup. |
| [use-role-with-aws-cli.md](/Users/paramraghavan/dev/123ofaws/iam/use-role-with-aws-cli.md) | Native AWS CLI role profile examples. |
| [role-vs-assume_role.md](/Users/paramraghavan/dev/123ofaws/iam/role-vs-assume_role.md) | Difference between IAM roles and `sts:AssumeRole`. |
| [adding_permission_for_assume_role.md](/Users/paramraghavan/dev/123ofaws/iam/adding_permission_for_assume_role.md) | How to change what an assumed role can do. |
| [cross_account_access_sts.py](/Users/paramraghavan/dev/123ofaws/iam/cross_account_access_sts.py) | Minimal boto3 AssumeRole example. |
| [iam_role_analyzer.py](/Users/paramraghavan/dev/123ofaws/iam/iam_role_analyzer.py) | Role-policy inventory/debugging script. |
| [iam-analyzer.md](/Users/paramraghavan/dev/123ofaws/iam/iam-analyzer.md) | Notes for the analyzer script. |
| [brownfield-vs-edge-node-assume-role.md](/Users/paramraghavan/dev/123ofaws/iam/brownfield-vs-edge-node-assume-role.md) | Brownfield and edge-node credential patterns. |
| [aws-cli_install.md](/Users/paramraghavan/dev/123ofaws/iam/aws-cli_install.md) | AWS CLI v2 install notes. |

## Core Model

IAM answers two questions:

- **Authentication**: who is making the request?
- **Authorization**: what is that identity allowed to do?

The main IAM building blocks:

| Concept | What it is | Credential model | Common use |
|---------|------------|------------------|------------|
| User | Long-lived IAM identity | Password/access keys | Human or legacy app identity |
| Group | Collection of users | None | Attach shared policies to users |
| Role | Assumable permission set | Temporary STS credentials | Services, cross-account access, short-lived access |
| Policy | JSON permission document | None | Allows or denies actions on resources |

Prefer roles over long-lived user permissions whenever practical. The user or workload proves identity; the role defines
the temporary permission set.

## Local Setup: `credential_process`

The local helper lets an AWS CLI profile call a script to produce temporary AWS credentials.

`~/.aws/config`:

```ini
[profile profile-oper]
region = us-east-1
credential_process = /Users/paramraghavan/dev/123ofaws/iam/credential_helper.py profile-oper
```

`credential_process` runs the command, reads JSON from stdout, and uses that JSON as credentials. The helper must print
only credential JSON to stdout. Prompts, warnings, and errors must go to stderr.

The helper flow:

```text
credential_helper.py profile-oper
  -> read profile-oper from ~/.aws/credential-helper.json
  -> load source_profile from ~/.aws/credentials or ~/.aws/config
  -> call sts:AssumeRole for role_arn
  -> print temporary credentials JSON for AWS CLI/SDKs
```

`~/.aws/credential-helper.json`:

```json
{
  "profile-oper": {
    "role_arn": "arn:aws:iam::111111111111:role/OperatorRole",
    "source_profile": "base",
    "mfa_serial": "arn:aws:iam::222222222222:mfa/your-user",
    "duration_seconds": 3600
  }
}
```

Test:

```bash
/Users/paramraghavan/dev/123ofaws/iam/credential_helper.py profile-oper
aws sts get-caller-identity --profile profile-oper
```

## What `source_profile = base` Means

`source_profile` is the starting AWS profile used to call STS before assuming the target role. In this example,
`source_profile = base` means the helper loads a profile named `base`.

Static-key `base` profile in `~/.aws/credentials`:

```ini
[base]
aws_access_key_id = <access-key-id>
aws_secret_access_key = <secret-access-key>
```

Region and output settings can live in `~/.aws/config`:

```ini
[profile base]
region = us-east-1
output = json
```

SSO-backed `base` profiles usually live mostly in `~/.aws/config`:

```ini
[profile base]
sso_start_url = https://example.awsapps.com/start
sso_region = us-east-1
sso_account_id = 222222222222
sso_role_name = DeveloperAccess
region = us-east-1
```

Useful checks:

```bash
aws configure list --profile base
aws sts get-caller-identity --profile base
aws sts get-caller-identity --profile profile-oper
```

## How `base` Is Initialized and Refreshed

| Base profile type | Initialized | Refreshed or rotated |
|-------------------|-------------|----------------------|
| Static IAM access key | `aws configure --profile base` | Manually when keys expire or security rotates them |
| AWS SSO / IAM Identity Center | SSO profile configuration | `aws sso login --profile base` when the SSO token expires |
| Office credential tool | Usually first login | Automatically or semi-automatically by the office login/refresh command |

`credential_helper.py` refreshes only the assumed-role STS credentials for `profile-oper`. It does not rotate or recreate
the underlying `base` profile. If `base` expires, refresh `base` first, then retry the role profile.

## AssumeRole Requirements

For an IAM user or source profile to assume a role, two sides must allow it.

The source identity needs permission to call `sts:AssumeRole`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::111111111111:role/OperatorRole"
    }
  ]
}
```

The target role needs a trust policy allowing the source identity:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:user/your-user"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Mental model:

```text
Source identity permission policy:
  I am allowed to call sts:AssumeRole on that role.

Target role trust policy:
  I trust that source identity/account to assume me.
```

## Temporary Credential Lifetime

`AssumeRole` returns temporary credentials with:

- `AccessKeyId`
- `SecretAccessKey`
- `SessionToken`
- `Expiration`

The requested session duration is set by `duration_seconds` in `~/.aws/credential-helper.json`.

```json
{
  "profile-oper": {
    "role_arn": "arn:aws:iam::111111111111:role/OperatorRole",
    "source_profile": "base",
    "duration_seconds": 3600
  }
}
```

Rules:

- `3600` means 1 hour.
- AWS STS requires at least `900` seconds.
- The upper bound is the target role's **Maximum session duration** setting, commonly 1 hour by default and configurable
  up to 12 hours for many roles.
- Role chaining has a stricter 1-hour maximum for the chained session.
- `credential_helper.py` refreshes cached credentials 5 minutes before `Expiration`.

## Why Use Roles Instead of Direct User Permissions?

Roles keep identity and authorization separate:

- The base user or source profile can have very small permissions.
- Operational permissions live on roles.
- Assumed-role credentials expire automatically.
- Cross-account access becomes explicit and auditable.
- Revocation is clean: remove `sts:AssumeRole` from the source identity or remove trust from the target role.
- CloudTrail shows both the source identity and the assumed-role session.

Common pattern:

```text
base profile:
  authenticate and assume approved roles

profile-oper role:
  actual permissions to operate AWS resources
```

## Role Chaining

A role can assume another role:

```text
base user/profile -> RoleA -> RoleB
```

For `RoleA` to assume `RoleB`:

`RoleA` permission policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::111111111111:role/RoleB"
    }
  ]
}
```

`RoleB` trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/RoleA"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Important: a role-chained session is limited to 1 hour maximum, even if the second role allows a longer maximum session
duration.

## Native AWS CLI Role Profiles

If the built-in AWS CLI behavior is enough, you may not need `credential_process`.

`~/.aws/credentials`:

```ini
[base]
aws_access_key_id = <access-key-id>
aws_secret_access_key = <secret-access-key>
```

`~/.aws/config`:

```ini
[profile profile-oper]
region = us-east-1
role_arn = arn:aws:iam::111111111111:role/OperatorRole
source_profile = base
mfa_serial = arn:aws:iam::222222222222:mfa/your-user
duration_seconds = 3600
```

Use it:

```bash
aws sts get-caller-identity --profile profile-oper
```

Use the custom helper when the source credentials come from a non-standard office login flow, custom MFA, Vault,
1Password, or another tool that the native AWS CLI profile cannot model cleanly.

## Policy Evaluation Short Version

AWS evaluates access roughly in this order:

1. Start with default deny.
2. Any explicit deny wins.
3. An allow in an applicable identity policy, resource policy, session policy, permission boundary, or SCP may allow the
   request only if no boundary/SCP blocks it.
4. If nothing allows the request, access is denied.

For `AssumeRole`, check both:

- source identity permission: `sts:AssumeRole` on the role ARN
- target role trust policy: principal allowed to assume the role

## Common Mistakes

Avoid:

- using the root user for daily work
- hardcoding access keys in code
- granting `Action: "*"` and `Resource: "*"` unless there is a narrow, deliberate reason
- assuming a role trust policy alone is enough
- forgetting the source identity also needs `sts:AssumeRole`
- expecting `credential_helper.py base` to print the raw `[base]` profile
- requesting a `duration_seconds` longer than the target role allows

Prefer:

- least privilege
- short STS sessions
- MFA for human access
- CloudTrail for audit
- SSO or office credential tooling over long-lived access keys
- roles for workloads and cross-account access

## Troubleshooting

Check active identity:

```bash
aws sts get-caller-identity --profile base
aws sts get-caller-identity --profile profile-oper
```

Check where a profile is resolved from:

```bash
aws configure list --profile base
aws configure list --profile profile-oper
```

Common `AssumeRole` failure causes:

- `source_profile` does not exist or is expired
- source identity lacks `sts:AssumeRole`
- target role trust policy does not trust the source identity/account
- MFA is required but not provided
- `duration_seconds` exceeds the role maximum session duration
- role chaining requested more than 1 hour

CloudTrail lookup:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole
```

## References

- AWS IAM User Guide: <https://docs.aws.amazon.com/IAM/latest/UserGuide/>
- AWS STS `AssumeRole`: <https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html>
- AWS SDK `credential_process`: <https://docs.aws.amazon.com/sdkref/latest/guide/feature-process-credentials.html>
- AWS CLI configuration: <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html>
