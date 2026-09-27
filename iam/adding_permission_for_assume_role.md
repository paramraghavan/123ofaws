# Adding Permissions to an Assumed Role

To change what an assumed role can do, edit the IAM role itself. You do not change the temporary assumed-role session.

## What to Edit

Edit the target role in the account where the role exists:

```text
source identity -> sts:AssumeRole -> target IAM role -> AWS resources
```

The target IAM role has:

- trust policy: who may assume it
- permission policies: what it can do

Add resource permissions to the role's permission policies.

## Console

1. Open AWS Console.
2. Go to **IAM -> Roles**.
3. Select the target role.
4. Open **Permissions**.
5. Attach a managed policy or create an inline policy.

Example inline policy for Lambda invoke:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:your-function-name"
    }
  ]
}
```

## CLI

Run this with an identity that has IAM administration permission in the role's account:

```bash
aws iam put-role-policy \
  --role-name your-role-name \
  --policy-name AllowLambdaInvoke \
  --policy-document file://policy.json
```

`policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:your-function-name"
    }
  ]
}
```

## Check Current Role Permissions

```bash
aws iam list-role-policies --role-name your-role-name
aws iam list-attached-role-policies --role-name your-role-name
```

Check your active identity:

```bash
aws sts get-caller-identity
```

## Important Rule

An assumed-role session cannot grant itself new permissions unless it already has IAM permissions such as
`iam:PutRolePolicy` or `iam:AttachRolePolicy`. That is powerful and usually avoided for operational roles.
