# IAM Role Analyzer

Use [iam_role_analyzer.py](/Users/paramraghavan/dev/123ofaws/iam/iam_role_analyzer.py) to inspect a role's attached
policies and follow explicit `sts:AssumeRole` links to other role ARNs.

Run:

```bash
python3 iam_role_analyzer.py arn:aws:iam::123456789012:role/example-role
```

What it reports:

- inline role policies
- attached managed role policies
- allowed actions found in allow statements
- allowed resources found in allow statements
- role ARNs that appear in `sts:AssumeRole` allow statements
- recursively inspected assumable roles

Important limitation: this is not a full effective-permissions engine. Real authorization can also depend on explicit
denies, permission boundaries, SCPs, session policies, resource policies, conditions, tags, and service-specific rules.
Use the analyzer for inventory and debugging, then confirm sensitive access with IAM Access Analyzer, policy simulator,
CloudTrail, and direct least-privilege review.
