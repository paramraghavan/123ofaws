# IAM Role vs `sts:AssumeRole`

An IAM role and `sts:AssumeRole` are related, but they are not the same thing.

| Item | Meaning |
|------|---------|
| IAM role | AWS identity/resource with a trust policy and permission policies |
| `sts:AssumeRole` | STS API action that returns temporary credentials for a role |

## IAM Role

An IAM role is a permission set that can be assumed by trusted principals.

It has:

- **Trust policy**: who may assume the role
- **Permission policies**: what the role can do after it is assumed
- **Maximum session duration**: upper bound for STS credentials

It does not have permanent access keys.

## `sts:AssumeRole`

`sts:AssumeRole` is the API call used to obtain temporary credentials for a role.

The response contains:

- `AccessKeyId`
- `SecretAccessKey`
- `SessionToken`
- `Expiration`

The caller uses those temporary credentials to call AWS APIs with the role's permissions.

## Required Policies

The source identity needs permission:

```json
{
  "Effect": "Allow",
  "Action": "sts:AssumeRole",
  "Resource": "arn:aws:iam::111111111111:role/OperatorRole"
}
```

The target role must trust the source identity:

```json
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::222222222222:user/your-user"
  },
  "Action": "sts:AssumeRole"
}
```

## Session Duration

- Minimum: `900` seconds.
- Maximum: target role's maximum session duration, up to 12 hours for many roles.
- Role chaining: 1 hour maximum for the chained role session.

## Common Uses

- EC2, ECS, Lambda, and other AWS services assuming service roles.
- Cross-account access.
- CI/CD deployment roles.
- Short-lived operational access for humans.
