Two approaches. Start with built-in if it covers you; reach for a custom helper only when it doesn't.

## Approach 1: Built-in (no helper needed)

For "assume a role from a base IAM user, with optional MFA" — the most common case — the AWS CLI handles this natively.
No script required.

`~/.aws/credentials` (base IAM user with permission to assume roles):

```ini
[base]
aws_access_key_id = AKIA....
aws_secret_access_key = wJalrXUtnFEMI/K7....
```

`~/.aws/config`:

```ini
[default]
region = us-east-1

[profile emr-prod]
region         = us-east-1
role_arn       = arn:aws:iam::111111111111:role/EMRHygieneRole
source_profile = base
mfa_serial     = arn:aws:iam::222222222222:mfa/yourusername
duration_seconds = 3600

[profile emr-dev]
region         = us-east-1
role_arn       = arn:aws:iam::333333333333:role/EMRHygieneRole
source_profile = base
```

The CLI prompts for the MFA code on first use, caches the assumed-role credentials in `~/.aws/cli/cache/`, and reuses
them until expiration. `boto3` reads the same cache, so the EMR hygiene CLI works without any extra setup:

```bash
./emr_hygiene_cli.py --profile emr-prod --vc-ids vc-abc123
```

**Use this when**: source credentials live in a standard credentials file, you only need AssumeRole (± MFA), and you're
happy with the AWS CLI's built-in cache.

---

## Approach 2: Custom credential helper

Use a helper when the built-in doesn't fit — e.g. credentials come from a secrets manager / Vault / 1Password / hardware
token, you need custom MFA flows, you want richer caching, or you want to log every credential issuance for audit.

The pattern is: `credential_process` in your AWS config points to a script. The script prints JSON on stdout in a
specific format; the SDK reads it.

`~/.aws/config`:

```ini
[default]
region = us-east-1

[profile emr-prod]
region = us-east-1
credential_process = /opt/aws-helper/aws_creds_helper.py emr-prod

[profile emr-dev]
region = us-east-1
credential_process = /opt/aws-helper/aws_creds_helper.py emr-dev
```

`~/.aws/helper-roles.json` (role configs, kept out of the main AWS config):

```json
{
  "emr-prod": {
    "role_arn": "arn:aws:iam::111111111111:role/EMRHygieneRole",
    "source_profile": "base",
    "mfa_serial": "arn:aws:iam::222222222222:mfa/yourusername",
    "duration_seconds": 3600
  },
  "emr-dev": {
    "role_arn": "arn:aws:iam::333333333333:role/EMRHygieneRole",
    "source_profile": "base",
    "duration_seconds": 3600
  }
}
```

And here's the helper itself — basic but actually functional:**How the pieces fit together**

```
~/.aws/credentials       ← base IAM user (long-lived key)
~/.aws/config            ← profile with credential_process = helper.py
~/.aws/helper-roles.json ← role configs (chmod 600)
~/.aws/helper-cache/     ← assumed-role creds, auto-managed (chmod 700)
```

**Install / first use**

```bash
# Put the helper somewhere stable and lock it down
sudo mkdir -p /opt/aws-helper
sudo cp aws_creds_helper.py /opt/aws-helper/
sudo chmod 755 /opt/aws-helper/aws_creds_helper.py

# Create the roles config
nano ~/.aws/helper-roles.json
chmod 600 ~/.aws/helper-roles.json

# Sanity check — should prompt for MFA, then print JSON to stdout
/opt/aws-helper/aws_creds_helper.py emr-prod

# Verify the SDK picks it up
aws sts get-caller-identity --profile emr-prod
```

**The output contract** (this is the part you can't change)

The helper must print exactly this JSON shape on stdout:

```json
{
  "Version": 1,
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2026-05-17T18:30:00+00:00"
}
```

Anything else on stdout breaks the SDK. That's why the helper sends MFA prompts and errors to **stderr** — stdout is
reserved.

**Where you'd extend it**

The helper is small on purpose. The three swap-in points are:

- **`get_mfa_code()`** — replace `input()` with a call to `oathtool`, a YubiKey, 1Password CLI (`op item get`), or your
  password manager's TOTP function. Lets you skip the manual prompt.
- **`assume_role()`** — replace the `boto3.Session(profile_name=...)` line with whatever fetches your source
  credentials (Vault, AWS Secrets Manager, gpg-encrypted file, hardware token).
- **`write_cache()`** — if you want centralized audit, also POST the issuance event to a logging endpoint at the same
  time as writing the file.
