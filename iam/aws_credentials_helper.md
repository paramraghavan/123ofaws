# AWS Credentials and `credential_process`

Use the native AWS CLI role profile when it is enough. Use `credential_process` when credentials come from a custom
office login flow, Vault, 1Password, hardware MFA, or another non-standard source.

## Native Role Profile

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

The AWS CLI uses `base`, calls STS `AssumeRole`, caches temporary credentials under `~/.aws/cli/cache`, and refreshes
when needed.

## Custom Helper Profile

`~/.aws/config`:

```ini
[profile profile-oper]
region = us-east-1
credential_process = /Users/paramraghavan/dev/123ofaws/iam/credential_helper.py profile-oper
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
chmod 600 ~/.aws/credential-helper.json
/Users/paramraghavan/dev/123ofaws/iam/credential_helper.py profile-oper
aws sts get-caller-identity --profile profile-oper
```

## Output Contract

`credential_process` must print only this JSON shape to stdout:

```json
{
  "Version": 1,
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2026-09-26T18:30:00+00:00"
}
```

Prompts, warnings, and errors must go to stderr.

## Refresh Model

- `base` is the source profile. It may be static keys, SSO, or office-managed credentials.
- `credential_helper.py` does not rotate `base`.
- The helper refreshes assumed-role STS credentials before expiration.
- `duration_seconds` controls the requested STS session length.
- AWS STS minimum is `900` seconds.
- The maximum is the target role's maximum session duration, except role chaining is limited to 1 hour.

## Quick Checks

```bash
aws configure list --profile base
aws sts get-caller-identity --profile base
aws sts get-caller-identity --profile profile-oper
```
