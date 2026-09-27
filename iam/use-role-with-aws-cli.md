# Use a Role with AWS CLI

There are two clean AWS CLI patterns:

- native role profile with `role_arn` and `source_profile`
- custom `credential_process` when a script must produce credentials

## Native Role Profile

`~/.aws/credentials`:

```ini
[base]
aws_access_key_id = <access-key-id>
aws_secret_access_key = <secret-access-key>
```

`~/.aws/config`:

```ini
[profile role-profile]
region = us-east-1
output = json
role_arn = arn:aws:iam::111111111111:role/OperatorRole
source_profile = base
duration_seconds = 3600
```

Use it:

```bash
aws sts get-caller-identity --profile role-profile
aws s3 ls --profile role-profile
```

Or set it for the current shell:

```bash
export AWS_PROFILE=role-profile
aws sts get-caller-identity
```

## Direct STS Call

You can also call STS directly:

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::111111111111:role/OperatorRole \
  --role-session-name manual-session \
  --duration-seconds 3600
```

The response contains temporary credentials. Prefer AWS CLI profiles or `credential_process` for normal use so you do
not manually export credentials.

## Custom `credential_process`

`~/.aws/config`:

```ini
[profile profile-oper]
region = us-east-1
credential_process = /Users/paramraghavan/dev/123ofaws/iam/credential_helper.py profile-oper
```

The helper reads `~/.aws/credential-helper.json`, assumes the configured role, caches temporary credentials, and prints
the JSON shape expected by AWS CLI/SDKs.

## Trusted vs Trusting Account

For cross-account access:

- **Trusting account**: owns the role and resources you want to access.
- **Trusted account**: owns the user or role that is allowed to assume the target role.

If Account `111111111111` owns the role, the role ARN uses that account ID:

```ini
role_arn = arn:aws:iam::111111111111:role/OperatorRole
```

The target role's trust policy must allow the source user, source role, or source account.
