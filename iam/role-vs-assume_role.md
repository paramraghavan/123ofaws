## IAM Role vs. Assume Role in AWS

These are related but distinct concepts — one is a **resource**, the other is an **action**.
Great question — let me break that down clearly.

---

### IAM Role → It's a "Resource"

A **resource** in AWS means it's a **thing that exists** — it has an ARN, it's stored, it can be
created/updated/deleted.

```
arn:aws:iam::123456789012:role/MyRole  ← it EXISTS as an object in AWS
```

Just like an S3 bucket or an EC2 instance is a resource — an **IAM Role is a resource** sitting in AWS IAM. It does
nothing on its own. It just *exists* with policies attached to it.

---

### Assume Role → It's an "Action"

An **action** means it's something you **do** — it's an API call, a verb, an operation.

```
sts:AssumeRole  ← it's a CALL you make to AWS STS
```

It's the same concept as:

- `s3:GetObject` → an action (downloading a file)
- `ec2:StartInstances` → an action (starting a server)
- `sts:AssumeRole` → an action (borrowing a role's permissions temporarily)

---

### Simple Analogy

|                | Analogy                                                                            |
|----------------|------------------------------------------------------------------------------------|
| **IAM Role**   | A **key card** hanging on the wall (it exists, has permissions programmed into it) |
| **AssumeRole** | The act of **picking up and using** that key card                                  |

The key card does nothing until someone picks it up and swipes it. Similarly, the IAM Role does nothing until someone
calls `sts:AssumeRole` on it.

---

So in short:

- **IAM Role** = a *noun* (a thing)
- **AssumeRole** = a *verb* (an action you perform on that thing)

---

### IAM Role

An **IAM Role** is an identity (similar to a user) that defines a set of permissions. Key characteristics:

- It's a **static object** stored in AWS IAM
- Has a **trust policy** (who can use it) and a **permissions policy** (what it can do)
- Has **no long-term credentials** (no username/password or permanent access keys)
- Can be attached to AWS services (EC2, Lambda, ECS, etc.), users, or other accounts

Think of it as a **hat with permissions** sitting on a shelf — it does nothing on its own.

---

### Assume Role (`sts:AssumeRole`)

**Assuming a role** is the **act of temporarily adopting** an IAM Role's permissions. Key characteristics:

- It's an **API call** made to AWS STS (Security Token Service)
- Returns **temporary credentials** (Access Key, Secret Key, Session Token) — valid for 15 min to 12 hours
- Can be done by users, services, or other AWS accounts
- Enables **cross-account access** and **privilege escalation within policy bounds**

Think of it as **putting on the hat** — you temporarily gain those permissions.

---

### How They Work Together

```
[Entity: User / Service / Account]
        |
        |  calls sts:AssumeRole
        ▼
[IAM Role] ──── Trust Policy: "Who is allowed to assume me?"
        |
        |  returns temporary credentials
        ▼
[Caller now acts with Role's permissions]
```

---

### Quick Comparison

|                   | IAM Role                   | Assume Role                       |
|-------------------|----------------------------|-----------------------------------|
| **What it is**    | An AWS identity/resource   | An API action (`sts:AssumeRole`)  |
| **Credentials**   | None (permanent)           | Temporary (STS tokens)            |
| **Defined by**    | Permissions + Trust policy | The caller invoking STS           |
| **Used for**      | Granting permissions       | Temporarily acquiring permissions |
| **Cross-account** | Configured in trust policy | Triggered by the assuming entity  |

---

### Common Use Cases

- **EC2/Lambda** → assigned an IAM Role directly (service assumes it automatically)
- **Cross-account access** → Account A calls `AssumeRole` on a role in Account B
- **CI/CD pipelines** → GitHub Actions assumes a role to deploy to AWS
- **Temporary privilege escalation** → A restricted user assumes a more powerful role for a specific task

The key mental model: **the Role is the permission set; AssumeRole is how you claim it temporarily.**