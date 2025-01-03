I'll explain how to assume a role using AWS CLI. There are two main parts to this:

1. First, Configure the Role in your AWS CLI credentials file (`~/.aws/credentials`):

> The ACCOUNT_ID in the role_arn belongs to the Trusting Account (the account that owns the role, the one you want to
> access).

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[profile role-profile]
role_arn = arn:aws:iam::ACCOUNT-ID:role/ROLE-NAME
source_profile = default
```

2. Configure the corresponding config file (`~/.aws/config`):

```ini
[profile role-profile]
region = us-west-2
output = json
role_arn = arn:aws:iam::ACCOUNT-ID:role/ROLE-NAME
source_profile = default
```

3. To use the role, you have two options:

Option 1 - Use the `--profile` flag:

```bash
aws s3 ls --profile role-profile
```

Option 2 - Set the profile in your environment:

```bash
export AWS_PROFILE=role-profile
aws s3 ls
```

4. To assume the role temporarily using STS:

```bash
aws sts assume-role \
    --role-arn arn:aws:iam::ACCOUNT-ID:role/ROLE-NAME \
    --role-session-name my-session \
    --duration-seconds 3600
```

This will return temporary credentials that you can use by setting them as environment variables:

```bash
export AWS_ACCESS_KEY_ID=<from-sts-response>
export AWS_SECRET_ACCESS_KEY=<from-sts-response>
export AWS_SESSION_TOKEN=<from-sts-response>
```

## Trusting and Trusted Account

In this context, when setting up a role to be used from AWS CLI:

The ACCOUNT_ID in the role_arn belongs to the Trusting Account (the account that owns the role, the one you want to
access).

Here's a clear example:

- Account A (ID: 111111111111) - Trusting Account (owns the role)
- Account B (ID: 222222222222) - Trusted Account (wants to use the role)

The role_arn would use Account A's ID:

```ini
[profile cross-account]
role_arn = arn:aws:iam::111111111111:role/CrossAccountRole
source_profile = default
```

Think of it this way:

1. Account A (111111111111) creates a role and trusts Account B to use it
2. Users in Account B (222222222222) reference Account A's ID in their CLI config to say "I want to assume that role in
   Account A"
