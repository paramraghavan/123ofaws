"""
EMR Studio + EMR on EKS resource hygiene Lambda.

What it watches
  1. Batch job-runs    (emr-containers StartJobRun submissions)
  2. Managed endpoints (interactive backend for Studio Workspaces)

What it does
  - Warns the owner in Slack before killing.
  - Kills (cancel_job_run / delete_managed_endpoint) once the hard threshold passes.
  - Identifies owners from EMR Studio auto-tags and a custom 'submittedBy' tag.

Deployment
  - Runtime: python3.11
  - Trigger: EventBridge schedule, rate(1 hour)
  - IAM:    emr-containers:ListJobRuns, ListManagedEndpoints,
            CancelJobRun, DeleteManagedEndpoint, DescribeManagedEndpoint
            cloudwatch:GetMetricStatistics
            logs:* (basic Lambda execution)

Environment variables
  VIRTUAL_CLUSTER_IDS    comma-separated EMR on EKS virtual cluster IDs
  SLACK_WEBHOOK          Slack incoming webhook URL
  WARN_HOURS             job-run warn threshold (default 6)
  KILL_HOURS             job-run kill threshold (default 12)
  ENDPOINT_WARN_HOURS    endpoint idle warn threshold (default 4)
  ENDPOINT_KILL_HOURS    endpoint idle kill threshold (default 24)
  USER_EMAIL_DOMAIN      e.g. "example.com" — used to @-mention in Slack
  DRY_RUN                "true" to log only, no kills (recommended for first week)
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from urllib import request

import boto3

log = logging.getLogger()
log.setLevel(logging.INFO)

emr = boto3.client("emr-containers")
cw = boto3.client("cloudwatch")

VC_IDS             = [v.strip() for v in os.environ["VIRTUAL_CLUSTER_IDS"].split(",")]
SLACK_WEBHOOK      = os.environ["SLACK_WEBHOOK"]
WARN_HOURS         = int(os.environ.get("WARN_HOURS", "6"))
KILL_HOURS         = int(os.environ.get("KILL_HOURS", "12"))
ENDPOINT_WARN      = int(os.environ.get("ENDPOINT_WARN_HOURS", "4"))
ENDPOINT_KILL      = int(os.environ.get("ENDPOINT_KILL_HOURS", "24"))
USER_EMAIL_DOMAIN  = os.environ.get("USER_EMAIL_DOMAIN", "")
DRY_RUN            = os.environ.get("DRY_RUN", "false").lower() == "true"


# ---------- entry point ----------

def handler(event, ctx):
    for vc_id in VC_IDS:
        try:
            check_job_runs(vc_id)
            check_managed_endpoints(vc_id)
        except Exception as e:
            log.exception(f"failed checking vc {vc_id}: {e}")
    return {"ok": True}


# ---------- batch job-runs ----------

def check_job_runs(vc_id):
    """Find RUNNING job-runs older than WARN/KILL thresholds."""
    now = datetime.now(timezone.utc)
    pager = emr.get_paginator("list_job_runs")
    for page in pager.paginate(virtualClusterId=vc_id, states=["RUNNING"]):
        for job in page.get("jobRuns", []):
            age = now - job["createdAt"]
            owner = owner_of(job)
            ref = f"{job.get('name', '<unnamed>')} (`{job['id']}`)"
            hrs = int(age.total_seconds() // 3600)

            if age >= timedelta(hours=KILL_HOURS):
                kill_job(vc_id, job["id"], owner, ref, hrs)
            elif age >= timedelta(hours=WARN_HOURS):
                warn_job(owner, ref, hrs)


def warn_job(owner, ref, hrs):
    post(
        f":warning: {mention(owner)} job {ref} has been running *{hrs}h*. "
        f"It will be killed at *{KILL_HOURS}h*. "
        f"Set `executionTimeoutMinutes` on submission if you need a different cap."
    )


def kill_job(vc_id, job_id, owner, ref, hrs):
    if DRY_RUN:
        post(f":no_entry: [DRY-RUN] would cancel job {ref} ({owner}) — {hrs}h")
        return
    try:
        emr.cancel_job_run(id=job_id, virtualClusterId=vc_id)
        post(f":skull: cancelled {ref} ({mention(owner)}) — was running {hrs}h.")
    except Exception as e:
        log.error(f"cancel_job_run failed: {e}")
        post(f":bangbang: failed to cancel {ref} ({owner}): `{e}`")


# ---------- managed endpoints (interactive Studio) ----------

def check_managed_endpoints(vc_id):
    """Find ACTIVE endpoints idle longer than thresholds."""
    pager = emr.get_paginator("list_managed_endpoints")
    for page in pager.paginate(virtualClusterId=vc_id, states=["ACTIVE"]):
        for ep in page.get("endpoints", []):
            ep_id = ep["id"]
            details = emr.describe_managed_endpoint(
                id=ep_id, virtualClusterId=vc_id
            ).get("endpoint", {})
            idle_h = endpoint_idle_hours(vc_id, ep_id, details)
            owner = owner_of(details)
            ref = f"endpoint {details.get('name', '<unnamed>')} (`{ep_id}`)"

            if idle_h >= ENDPOINT_KILL:
                kill_endpoint(vc_id, ep_id, owner, ref, idle_h)
            elif idle_h >= ENDPOINT_WARN:
                warn_endpoint(owner, ref, idle_h)


def endpoint_idle_hours(vc_id, ep_id, details):
    """
    Heuristic for endpoint idle time.

    Real signal: CPU usage on the endpoint's driver pod. If your cluster
    has Container Insights enabled, query the pod_cpu_utilization metric.
    Fallback: hours since the endpoint was created (coarse — assumes
    endpoints are recreated per work session, which is the Studio default).
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=ENDPOINT_KILL + 2)

    try:
        # Container Insights metric — adjust dimensions to your setup.
        resp = cw.get_metric_statistics(
            Namespace="ContainerInsights",
            MetricName="pod_cpu_utilization",
            Dimensions=[
                {"Name": "Namespace", "Value": f"emr-{vc_id}"},
                {"Name": "PodName",   "Value": f"spark-{ep_id}-driver"},
            ],
            StartTime=start, EndTime=end, Period=300, Statistics=["Maximum"],
        )
        active = [d for d in resp.get("Datapoints", []) if d["Maximum"] > 5.0]
        if active:
            last = max(d["Timestamp"] for d in active)
            return (end - last).total_seconds() / 3600
    except Exception as e:
        log.warning(f"CW metric lookup failed for {ep_id}: {e}")

    created = details.get("createdAt", end)
    return (end - created).total_seconds() / 3600


def warn_endpoint(owner, ref, idle_h):
    post(
        f":zzz: {mention(owner)} {ref} has been idle *{int(idle_h)}h*. "
        f"It will be deleted at *{ENDPOINT_KILL}h*. "
        f"Detach your Studio Workspace if you're done."
    )


def kill_endpoint(vc_id, ep_id, owner, ref, idle_h):
    if DRY_RUN:
        post(f":no_entry: [DRY-RUN] would delete {ref} ({owner}) — idle {int(idle_h)}h")
        return
    try:
        emr.delete_managed_endpoint(id=ep_id, virtualClusterId=vc_id)
        post(
            f":wastebasket: deleted {ref} ({mention(owner)}) — idle {int(idle_h)}h. "
            f"Reconnect a Workspace in Studio to create a new endpoint."
        )
    except Exception as e:
        log.error(f"delete_managed_endpoint failed: {e}")
        post(f":bangbang: failed to delete {ref} ({owner}): `{e}`")


# ---------- helpers ----------

def owner_of(resource):
    """
    Extract the human owner of a job-run or endpoint.
    Studio auto-tags vary by configuration; we check the common ones.
    """
    tags = resource.get("tags", {}) or {}
    for key in ("submittedBy",                     # custom wrapper tag
                "StudioUser",                      # legacy
                "aws:emr-studio:UserArn",          # current Studio auto-tag
                "emr-studio:UserArn"):
        if key in tags and tags[key]:
            v = tags[key]
            # UserArn looks like arn:aws:sso::123:user/abc — take the last bit
            return v.split("/")[-1] if "/" in v else v
    return "unknown"


def mention(owner):
    """Slack @-mention if we can resolve a username, else just the name."""
    if owner == "unknown" or not USER_EMAIL_DOMAIN:
        return f"*{owner}*"
    # If your Slack workspace links emails to users, this turns into a real ping.
    return f"<mailto:{owner}@{USER_EMAIL_DOMAIN}|*{owner}*>"


def post(text):
    payload = json.dumps({"text": text}).encode()
    req = request.Request(
        SLACK_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        request.urlopen(req, timeout=5)
    except Exception as e:
        log.error(f"slack post failed: {e}")
