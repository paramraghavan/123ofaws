# EMR Hygiene

Automated resource cleanup for **EMR Studio + EMR on EKS**. Watches running
batch jobs and idle interactive endpoints, warns owners in Slack, and kills
resources past a hard threshold so a forgotten notebook can't quietly burn
through cluster capacity over the weekend.

Ships in two deployment-ready forms with identical logic:

| File | Use for |
|---|---|
| `emr_hygiene_lambda.py` | Scheduled enforcement in AWS (EventBridge → Lambda) |
| `emr_hygiene_cli.py`    | Ad-hoc cleanup, cron on a utility host, CI/CD pipelines, local debugging |

Pick one or run both — thresholds and owner-resolution are kept identical
on purpose, so they behave the same regardless of how they're invoked.

---

## Why this exists

EMR Studio is convenient enough that modellers forget to clean up. The
common failure modes:

- A notebook is left attached over the weekend; the managed endpoint
  (Spark driver pod) stays active the whole time.
- A batch job hangs on an unproductive stage and runs for days.
- A Workspace is closed in the browser, but the backing endpoint stays up
  because nothing told it to shut down.

This tool is a backstop. It does **not** rely on modellers remembering
`spark.stop()`, closing tabs, or setting timeouts on submission. It runs
on a schedule and enforces the cleanup on its own.

---

## What it watches

| Resource | API used | Signal | Action |
|---|---|---|---|
| Batch job-runs | `emr-containers:ListJobRuns` | Wall-clock age since `createdAt` | Warn at `WARN_HOURS`, cancel at `KILL_HOURS` |
| Managed endpoints | `emr-containers:ListManagedEndpoints` | Driver pod CPU (Container Insights), fallback to age | Warn at `ENDPOINT_WARN_HOURS`, delete at `ENDPOINT_KILL_HOURS` |

Owners are identified from tags in this order:

1. `submittedBy` — custom tag set by the batch submission wrapper
2. `StudioUser` — legacy Studio tag
3. `aws:emr-studio:UserArn` / `emr-studio:UserArn` — current Studio auto-tags

If none are present, owner is `unknown` and the tool still acts — it just
can't @-mention anyone in Slack.

---

## Prerequisites

- One or more EMR on EKS virtual clusters.
- EMR Studio configured to submit on behalf of users (so resources get
  auto-tagged with the Studio user identity).
- A Slack incoming webhook for notifications.
- *Recommended*: Container Insights enabled on the EKS cluster, so endpoint
  idle detection uses real CPU rather than wall-clock age.

---

## Configuration

Same knobs, same names, regardless of how you run it.

| Setting | CLI flag | Env var | Default | Purpose |
|---|---|---|---|---|
| Virtual cluster IDs | `--vc-ids` | `VIRTUAL_CLUSTER_IDS` | — (required) | Comma-separated |
| Slack webhook | `--slack-webhook` | `SLACK_WEBHOOK` | — | Omit on CLI for console-only output |
| Job-run warn | `--warn-hours` | `WARN_HOURS` | `6` | Hours before warning a batch job's owner |
| Job-run kill | `--kill-hours` | `KILL_HOURS` | `12` | Hours before cancelling a batch job |
| Endpoint warn | `--endpoint-warn-hours` | `ENDPOINT_WARN_HOURS` | `4` | Idle hours before warning an endpoint's owner |
| Endpoint kill | `--endpoint-kill-hours` | `ENDPOINT_KILL_HOURS` | `24` | Idle hours before deleting an endpoint |
| Email domain | `--user-email-domain` | `USER_EMAIL_DOMAIN` | `""` | Enables @-mention mailto links in Slack |
| Dry run | `--dry-run` | `DRY_RUN` | `false` | Log only, no kills |
| List only | `--list-only` | — | `false` | CLI-only — print resources without warning/killing |

**Tuning guidance**

- Run with dry-run on for the first week and read the Slack channel.
  You'll quickly see whether the thresholds match how your teams actually work.
- If you have a small number of heavy nightly jobs that genuinely run 8+
  hours, raise `WARN_HOURS` and `KILL_HOURS` rather than disabling the
  tool for that cluster. Or have those specific jobs set their own
  `executionTimeoutMinutes` and exempt them via a tag-based skip (you'd
  need to add that check to `check_job_runs`).
- `ENDPOINT_KILL_HOURS=24` is deliberately lenient. Drop it to `8` once
  modellers are used to the rhythm — re-creating an endpoint from Studio
  is a one-click operation.

---

## IAM

Minimum permissions for whichever principal runs the code (Lambda
execution role, EC2 instance profile, or developer's IAM user):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "emr-containers:ListJobRuns",
        "emr-containers:ListManagedEndpoints",
        "emr-containers:DescribeManagedEndpoint",
        "emr-containers:CancelJobRun",
        "emr-containers:DeleteManagedEndpoint"
      ],
      "Resource": "arn:aws:emr-containers:*:*:/virtualclusters/*"
    },
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:GetMetricStatistics"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

The `logs:*` block is only needed for the Lambda deployment. Scope
`Resource` more tightly to your specific virtual cluster ARNs in
production.

---

## Deployment Mode A — Lambda (scheduled, hands-off)

Uses `emr_hygiene_lambda.py`. EventBridge invokes it on an hourly schedule.

### A.1 — Deploy via AWS CLI commands

```bash
zip emr_hygiene_lambda.zip emr_hygiene_lambda.py

aws lambda create-function \
  --function-name emr-hygiene \
  --runtime python3.11 \
  --role arn:aws:iam::<acct>:role/emr-hygiene-role \
  --handler emr_hygiene_lambda.handler \
  --timeout 120 \
  --zip-file fileb://emr_hygiene_lambda.zip \
  --environment "Variables={
    VIRTUAL_CLUSTER_IDS=vc-abc123,vc-def456,
    SLACK_WEBHOOK=https://hooks.slack.com/services/...,
    DRY_RUN=true,
    USER_EMAIL_DOMAIN=example.com
  }"

aws events put-rule \
  --name emr-hygiene-hourly \
  --schedule-expression "rate(1 hour)"

aws events put-targets \
  --rule emr-hygiene-hourly \
  --targets "Id"="1","Arn"="arn:aws:lambda:<region>:<acct>:function:emr-hygiene"

aws lambda add-permission \
  --function-name emr-hygiene \
  --statement-id emr-hygiene-events \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:<region>:<acct>:rule/emr-hygiene-hourly
```

### A.2 — Deploy via Terraform

```hcl
resource "aws_lambda_function" "emr_hygiene" {
  function_name = "emr-hygiene"
  runtime       = "python3.11"
  handler       = "emr_hygiene_lambda.handler"
  role          = aws_iam_role.emr_hygiene.arn
  filename      = "emr_hygiene_lambda.zip"
  timeout       = 120

  environment {
    variables = {
      VIRTUAL_CLUSTER_IDS = join(",", var.virtual_cluster_ids)
      SLACK_WEBHOOK       = var.slack_webhook
      DRY_RUN             = "true"
      USER_EMAIL_DOMAIN   = "example.com"
    }
  }
}

resource "aws_cloudwatch_event_rule" "hourly" {
  name                = "emr-hygiene-hourly"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule = aws_cloudwatch_event_rule.hourly.name
  arn  = aws_lambda_function.emr_hygiene.arn
}
```

---

## Deployment Mode B — Standalone CLI script

Uses `emr_hygiene_cli.py`. Same logic, runnable from any host with AWS
credentials and Python 3.9+ with `boto3` installed.

### B.1 — Try it locally first (recommended)

```bash
# Just inspect — no warnings, no kills
./emr_hygiene_cli.py --vc-ids vc-abc123 --list-only

# See what would be killed at default thresholds
./emr_hygiene_cli.py --vc-ids vc-abc123 --dry-run

# Real run, with Slack and @-mentions
./emr_hygiene_cli.py --vc-ids vc-abc123 \
  --slack-webhook "$SLACK_WEBHOOK" \
  --user-email-domain example.com
```

All flags accept env-var fallbacks, so this also works:

```bash
export VIRTUAL_CLUSTER_IDS=vc-abc123
export SLACK_WEBHOOK="https://hooks.slack.com/services/..."
./emr_hygiene_cli.py --dry-run
```

### B.2 — Cron on a utility host

```cron
# /etc/cron.d/emr-hygiene — runs every hour
0 * * * * ec2-user VIRTUAL_CLUSTER_IDS=vc-abc123 \
  SLACK_WEBHOOK=https://hooks.slack.com/services/... \
  USER_EMAIL_DOMAIN=example.com \
  /opt/emr-hygiene/emr_hygiene_cli.py >> /var/log/emr-hygiene.log 2>&1
```

The host needs an IAM role/profile with the permissions from the IAM
section above.

### B.3 — systemd timer

`/etc/systemd/system/emr-hygiene.service`:
```ini
[Unit]
Description=EMR Studio + EKS resource hygiene

[Service]
Type=oneshot
User=ec2-user
EnvironmentFile=/etc/emr-hygiene.env
ExecStart=/opt/emr-hygiene/emr_hygiene_cli.py
```

`/etc/systemd/system/emr-hygiene.timer`:
```ini
[Unit]
Description=Run EMR hygiene hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Then:
```bash
sudo systemctl enable --now emr-hygiene.timer
```

### B.4 — CI/CD pipeline (e.g. GitHub Actions, scheduled)

```yaml
name: emr-hygiene
on:
  schedule:
    - cron: "0 * * * *"
jobs:
  hygiene:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # for OIDC into AWS
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<acct>:role/emr-hygiene-role
          aws-region: us-east-1
      - run: pip install boto3
      - run: python emr_hygiene_cli.py
        env:
          VIRTUAL_CLUSTER_IDS: ${{ vars.VC_IDS }}
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
          USER_EMAIL_DOMAIN: example.com
```

The script exits non-zero on partial failure, so the workflow turns red
if AWS calls break — useful for catching IAM drift.

---

## Operating it

**Disabling temporarily (Lambda)**
Set the EventBridge rule to `DISABLED` rather than deleting the Lambda.

**Disabling temporarily (CLI)**
Comment out the cron/timer entry, or set `DRY_RUN=true` if you want to
keep observing without acting.

**Watching it work**

- Lambda: CloudWatch Logs group `/aws/lambda/emr-hygiene`.
- CLI: stdout/stderr, or wherever your cron entry redirects them.
- Slack: warn/kill messages flow through regardless of deployment mode.

Filter logs for `cancel_job_run failed` or `delete_managed_endpoint failed`
to catch IAM or transient API issues.

---

## Companion settings (do these too)

This tool is one of several layers. Pair it with:

| Setting | Where | Recommended value |
|---|---|---|
| Workspace idle-stop | EMR Studio admin | 2 hours |
| Spark dynamic allocation | EMR app / cluster config | `minExecutors=0`, `executorIdleTimeout=60s`, `shuffleTracking.enabled=true` |
| Jupyter kernel cull | Workspace image | `cull_idle_timeout=1800`, `cull_connected=True` |
| Default job TTL | Batch submission wrapper | `executionTimeoutMinutes=720` |
| EKS quotas | Per-team namespace | ResourceQuota capping CPU/memory |

This tool is the *last* line of defense. Each layer above it reduces the
number of resources the tool ever has to touch.

---

## Troubleshooting

**"Owner is `unknown` for every resource"**
EMR Studio isn't tagging submissions with the user identity. Check the
Studio configuration — auto-tagging is on by default in current versions
but may be off if your Studio was created from an old template. For
batch jobs, make sure the submission wrapper adds `submittedBy`.

**"Endpoint idle hours are wildly wrong"**
Container Insights is probably not enabled, so the code is falling back
to wall-clock age since the endpoint was created. Either enable Container
Insights on the EKS cluster, or adjust `ENDPOINT_KILL_HOURS` upward to
match a "session length" you're comfortable with.

**"Slack posts are missing"**
The webhook URL may be wrong or revoked. Check logs for `slack post failed`.
Slack rotates webhook URLs occasionally if abuse is detected. CLI mode
without `--slack-webhook` logs `[would-slack]` lines to stdout — useful
for confirming the *content* of messages is right before you wire up
the real webhook.

**"Lambda times out"**
Default Lambda timeout is 3s; this code needs at least 60s. Set the
function timeout to 120s. If you have many virtual clusters, consider
splitting into per-VC invocations via EventBridge with separate target
inputs.

**"CLI runs locally but cron entry fails silently"**
Cron's environment is minimal — usually missing `AWS_PROFILE`, `PATH`, or
locale settings. Use absolute paths (`/opt/emr-hygiene/emr_hygiene_cli.py`,
not `./emr_hygiene_cli.py`) and either set env vars explicitly in the
crontab line or source a file from `/etc/emr-hygiene.env`.

**"It killed something it shouldn't have"**
This is what dry-run mode is for during rollout. If it happens in
production:

1. Switch to dry-run mode immediately.
2. Look at logs — `name`, `id`, `owner`, and the age/idle figures are
   logged at the moment of action.
3. Raise the relevant threshold or add a skip-tag exemption.

---

## Limitations

- **Doesn't watch EMR on EC2 clusters.** Different API, different idle
  semantics. If you have any EC2-mode EMR clusters, write a sibling tool.
- **Coarse endpoint idle detection without Container Insights.** The
  fallback "hours since creation" assumes endpoints are recreated per
  session, which is the Studio default but not guaranteed.
- **No grace period after warn.** A job warned at exactly `WARN_HOURS`
  and a job at `KILL_HOURS - 1s` get different treatment. Run hourly and
  these edges are at most an hour wide; fine in practice.
- **No exclusion list.** If you have a known long-running job, the cleanest
  fix is to add a `skip-hygiene=true` tag check at the top of
  `check_job_runs`. Left out of the initial version to keep it small.

---

## Changes you might want to make

- **Email instead of (or as well as) Slack** — replace `post_slack()` with
  an `ses:SendEmail` call. Slack is simpler and team-visible; SES is
  better for personal accountability.
- **Per-team thresholds** — read thresholds from a tag like
  `team=ds-platform` and look up that team's policy in a DynamoDB table.
- **Daily digest** — add a second invocation on a daily schedule that
  doesn't kill anything but posts a per-owner summary of resource-hours
  used. Behaviour-change tool, not enforcement.
- **Skip during business hours** — if your problem is overnight/weekend
  drift, check the hour of day and only act outside 9–18 local time. The
  warn behaviour stays useful all day.
