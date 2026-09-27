# Brownfield vs Edge Node AWS Access

This note compares how non-AWS servers and AWS-managed edge-style compute should get AWS credentials.

## Decision Table

| Environment | Recommended credential pattern | Why |
|-------------|--------------------------------|-----|
| Brownfield/on-prem server | Bootstrap identity -> STS `AssumeRole` | No AWS metadata service is available |
| EC2 / ECS / Lambda | Service role / task role / execution role | AWS provides and refreshes credentials automatically |
| Outposts EC2-like instance | Instance profile/service role | Same model as EC2 when supported |
| Local Zone / Wavelength workload | Service role where supported | Avoid local long-lived keys |
| Cross-account from AWS workload | Service role -> STS `AssumeRole` into target account | Source workload uses AWS-managed credentials, then assumes target role |
| Developer laptop | SSO or base profile -> role profile / `credential_process` | Human login plus short-lived role credentials |

## Brownfield Server Pattern

A brownfield server is an existing non-AWS server. It cannot automatically receive IAM role credentials from EC2
instance metadata, so it needs a bootstrap identity.

Flow:

```text
brownfield server
  -> retrieve bootstrap credentials from approved storage
  -> call sts:AssumeRole
  -> receive temporary credentials
  -> call AWS APIs
  -> refresh before Expiration
```

Use STS role credentials for AWS access rather than using the bootstrap key directly.

## Bootstrap Credential Options

| Source | Use when | Notes |
|--------|----------|-------|
| Office credential tool | Enterprise developer or server access | Best if your company already manages refresh/rotation |
| AWS Secrets Manager | Server can authenticate to read the secret | Supports audit and managed rotation patterns |
| HashiCorp Vault | Centralized secrets platform exists | Good audit and dynamic secret support |
| Encrypted local file | Isolated environment with no secrets service | Requires strong key management and manual rotation |
| Environment variables | Local development only | Avoid for production; easy to leak through process inspection/logging |

## Minimal boto3 Flow

```python
import boto3

sts = boto3.client(
    "sts",
    aws_access_key_id=bootstrap_access_key,
    aws_secret_access_key=bootstrap_secret_key,
)

response = sts.assume_role(
    RoleArn="arn:aws:iam::111111111111:role/BrownfieldAccess",
    RoleSessionName="brownfield-server",
    DurationSeconds=3600,
)

creds = response["Credentials"]

s3 = boto3.client(
    "s3",
    aws_access_key_id=creds["AccessKeyId"],
    aws_secret_access_key=creds["SecretAccessKey"],
    aws_session_token=creds["SessionToken"],
)
```

The temporary credentials include `Expiration`. Refresh before that time.

## Edge / AWS-Managed Workload Pattern

For EC2, ECS, Lambda, and similar AWS-managed compute, prefer service roles:

```text
AWS workload
  -> AWS metadata/runtime provides temporary credentials
  -> SDK discovers credentials automatically
  -> SDK refreshes credentials automatically
```

Code can usually be this small:

```python
import boto3

s3 = boto3.client("s3")
print(s3.list_buckets())
```

No static access key is needed in the application.

## Cross-Account Access

Cross-account access still uses `AssumeRole`.

Example:

```text
Account A workload/user
  -> has permission sts:AssumeRole on Account B role
  -> Account B role trust policy trusts Account A principal
  -> STS returns temporary Account B role credentials
```

Source identity policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::222222222222:role/TargetAccessRole"
    }
  ]
}
```

Target role trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/SourceWorkloadRole"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Duration and Refresh

- Request session length with `DurationSeconds`.
- Minimum is `900` seconds.
- Maximum is the role's maximum session duration, up to 12 hours for many roles.
- Role chaining is limited to 1 hour for the chained session.
- Refresh credentials before `Expiration`; a 5-minute buffer is common.

## Security Checklist

- Prefer AWS-managed service roles for AWS workloads.
- Avoid hardcoded or directly used long-lived access keys.
- Keep bootstrap identities minimal: usually only `sts:AssumeRole` on approved roles.
- Store bootstrap credentials in an approved secrets system.
- Rotate bootstrap credentials according to office policy.
- Use short STS sessions.
- Require MFA for human role assumption when appropriate.
- Enable CloudTrail and monitor `AssumeRole` calls.
- Use external IDs for third-party access.

## Troubleshooting

Check caller identity:

```bash
aws sts get-caller-identity --profile base
aws sts get-caller-identity --profile profile-oper
```

Simulate whether a source principal can call `sts:AssumeRole`:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::111111111111:user/source-user \
  --action-names sts:AssumeRole \
  --resource-arns arn:aws:iam::222222222222:role/TargetAccessRole
```

Inspect CloudTrail:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole
```

Common failures:

- source principal lacks `sts:AssumeRole`
- target role trust policy does not trust the source principal/account
- MFA or external ID is required but missing
- requested duration exceeds the role/session limit
- source bootstrap credentials are expired
