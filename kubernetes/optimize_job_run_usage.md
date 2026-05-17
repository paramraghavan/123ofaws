Here's the distilled version, focused on **what runs without modeller cooperation**.

## The core idea

Don't try to train modellers to remember `spark.stop()` — assume they'll forget every time. Stack three or four
automatic backstops so that "modeller closes laptop and goes on vacation" still ends in a clean shutdown within an hour.

## The automation stack (no modeller action required)

**1. Dynamic allocation with `minExecutors=0`** — within ~60 seconds of a notebook going quiet, executors drain. You're
left paying for just the driver pod (~1–4 GB). This is the single highest-leverage setting. Set it once at the
cluster/application level and every job inherits it.

**2. Jupyter kernel idle culler with `cull_connected=True`** — after 30 minutes of idle, the kernel dies, which kills
the `SparkSession`, which kills the driver. The `cull_connected=True` flag is the critical one: without it, an open
browser tab defeats everything.

**3. EMR Studio Workspace auto-stop** — the Workspace itself has an idle-stop. Set it in the Studio admin config (
typically 1–4 hours). This catches the case where the kernel culler didn't fire (e.g. it was disabled by a
user-installed extension).

**4. Hard job TTL on every submission** — for `StartJobRun`, set `executionTimeoutMinutes`. No job should be allowed to
run longer than, say, 12 hours without an explicit override. Enforce this at submission time, not by trusting the user
to set it.

**5. Pod TTL controller in EKS** — cleans up `Completed`/`Failed` pods after a few minutes so they don't accumulate. EMR
on EKS does this by default; verify it's on.

**6. Quotas per team namespace** — ResourceQuotas in Kubernetes cap the blast radius. If a modeller requests 200
executors for exploratory work, the quota refuses it. No human reviewer needed.

Layered together, the *worst* case (every layer fails until the last) is a job killed by TTL after 12 hours. Realistic
case: drained to driver-only in 60 seconds, fully dead in 30 minutes.

## The notification layer

This is the part the document doesn't cover. Two flavors worth building:

**A. Pre-emptive nudge** — a Lambda on a schedule (every hour) that lists long-running job-runs and pings the owner
*before* you kill them.

```python
# lambda: nudge-long-running-jobs
import boto3, os, json, urllib.request
from datetime import datetime, timezone, timedelta

emr = boto3.client("emr-containers")
VC_ID = os.environ["VIRTUAL_CLUSTER_ID"]
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
WARN_HOURS = 6
KILL_HOURS = 12


def handler(event, ctx):
    now = datetime.now(timezone.utc)
    for page in emr.get_paginator("list_job_runs").paginate(
            virtualClusterId=VC_ID, states=["RUNNING"]
    ):
        for job in page["jobRuns"]:
            age = now - job["createdAt"]
            owner = job.get("tags", {}).get("submittedBy", "unknown")
            if age > timedelta(hours=KILL_HOURS):
                emr.cancel_job_run(id=job["id"], virtualClusterId=VC_ID)
                post(f":skull: killed {job['name']} ({owner}) — over {KILL_HOURS}h")
            elif age > timedelta(hours=WARN_HOURS):
                post(f":warning: {owner}, your job {job['name']} has been running "
                     f"{age.seconds // 3600}h. It will be killed at {KILL_HOURS}h.")


def post(text):
    req = urllib.request.Request(
        SLACK_WEBHOOK,
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)
```

Schedule it with EventBridge: `rate(1 hour)`. The Slack webhook is simpler and cheaper than SES; if you need email
instead, swap `post()` for an `ses.send_email` call.

**B. Weekly cost report** — a digest emailed to each team lead showing their top idle/wasteful sessions. The "
leaderboard effect" mentioned in defense 6 is real; nobody wants to be top of the list two weeks running. CloudWatch
metrics + a Lambda + SES is enough — no Grafana required.

## The one thing modellers DO need to do

Tag their submissions so the notification layer knows whom to ping. Enforce this at the submission boundary:

```python
# Wrapper that every job goes through — refuses to submit without a tag.
def submit(job_spec):
    submitter = os.environ.get("USER") or os.environ.get("JUPYTERHUB_USER")
    if not submitter:
        raise RuntimeError("Cannot determine submitter — set $USER")
    job_spec.setdefault("tags", {})["submittedBy"] = submitter
    return emr.start_job_run(**job_spec)
```

For EMR Studio, the username is already in the environment — the wrapper just reads it. Now every running job has an
owner, and `cancel_job_run` calls can route blame correctly.

## Short checklist you can hand to ops

1. Cluster/application config: dynamic allocation on, `minExecutors=0`, `executorIdleTimeout=60s`,
   `shuffleTracking.enabled=true`.
2. JupyterHub/Server config: `cull_idle_timeout=1800`, `cull_connected=True`.
3. EMR Studio admin: Workspace idle-stop = 2 hours.
4. Submission wrapper: enforce `submittedBy` tag + default `executionTimeoutMinutes=720`.
5. EKS: ResourceQuotas per team namespace, TTL controller for completed pods.
6. Lambda on 1-hour schedule: warn at 6h, kill at 12h, post to Slack.
7. Lambda on weekly schedule: cost-by-owner digest to team leads.

Items 1–5 stop new waste from happening. Item 6 catches whatever leaks through. Item 7 shifts behavior over time without
anyone having to nag.

## What modellers can still do (but aren't required to)

The notebook-hygiene list (`appName`, `spark.stop()`, start small) stays in the guide as good practice, but treat it as
a bonus, not a load-bearing control. The whole point of the stack above is that you keep the lights on whether they
follow it or not.