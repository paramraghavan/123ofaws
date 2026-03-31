## Adding Permissions to an Assumed Role

**Important clarification:** You cannot modify a role *from within* an assumed role session directly — you need to edit
the **actual IAM Role** in the account where it lives. Here's how:

---

### The Flow

```
[Your User/Identity]
        |
        | assumes
        ▼
[IAM Role] ← this is what you need to modify (in IAM, not from the session)
        |
        | grants access to
        ▼
[AWS Resources - Lambda, S3, etc.]
```

---

### Two Ways to Add Permissions to the Role

---

#### Option A — You have IAM access in the target account (Console)

1. Go to **AWS Console → IAM → Roles**
2. Search and click on the role you're assuming
3. **Permissions tab → Add permissions → Attach policies** (managed) or **Create inline policy** (custom)
4. Add the required resource permission, e.g. for Lambda:

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

---

#### Option B — Using CLI from your **original identity** (not the assumed session)

```bash
# Use your BASE credentials (not the assumed role session)
# Unset any assumed role env variables first if set
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

# Attach an inline policy to the role
aws iam put-role-policy \
  --role-name your-role-name \
  --policy-name AllowLambdaInvoke \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["lambda:InvokeFunction"],
        "Resource": "arn:aws:lambda:us-east-1:123456789012:function:your-function-name"
      }
    ]
  }'
```

---

#### Option C — From assumed role session (only if the role has `iam:PutRolePolicy`)

If the assumed role itself has IAM permissions, you can modify roles from within the session:

```bash
# While in the assumed role session
aws iam put-role-policy \
  --role-name target-role-name \
  --policy-name AddedFromSession \
  --policy-document file://policy.json
```

> ⚠️ This is rare and generally **not recommended** — granting an assumed role the ability to modify IAM is a security
> risk.

---

### How to Check What Permissions the Assumed Role Currently Has

```bash
# After assuming the role, check your effective identity
aws sts get-caller-identity

# List policies attached to the role
aws iam list-role-policies --role-name your-role-name        # inline
aws iam list-attached-role-policies --role-name your-role-name  # managed
```

---

### Common Scenarios & Fix

| Scenario               | Fix                                                               |
|------------------------|-------------------------------------------------------------------|
| **Same account**       | Log in as admin/IAM user → edit the role directly                 |
| **Cross-account role** | Go to the **target account** where the role lives → edit it there |
| **No IAM access**      | Ask your AWS admin to add the policy to the role                  |
| **Role has IAM perms** | Can modify from within session (use carefully)                    |

---

### Key Rule to Remember

> The **assumed role session** is read-only in terms of its own permissions. To change what a role can do, you must edit
> the **IAM Role definition** using an identity that has `iam:PutRolePolicy` or `iam:AttachRolePolicy` permissions.