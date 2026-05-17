#!/usr/bin/env python3
"""
EMR Studio + EMR on EKS resource hygiene — standalone CLI version.

Same logic as the Lambda, but runnable from the command line. Useful for:
  - Manual one-off cleanup
  - Running from cron on a bastion / utility host
  - CI/CD pipelines (nightly cleanup job)
  - Local debugging before deploying the Lambda

Usage examples:

  # Just show what's running — don't warn or kill anything
  ./emr_hygiene_cli.py --vc-ids vc-abc123,vc-def456 --list-only

  # Dry-run: log what WOULD be killed, but don't actually kill it
  ./emr_hygiene_cli.py --vc-ids vc-abc123 --dry-run

  # Real run with Slack notifications
  ./emr_hygiene_cli.py --vc-ids vc-abc123 \\
      --slack-webhook https://hooks.slack.com/services/... \\
      --user-email-domain example.com

  # From cron, with env vars (simpler crontab line)
  VIRTUAL_CLUSTER_IDS=vc-abc123 SLACK_WEBHOOK=https://... ./emr_hygiene_cli.py

Every CLI flag can also be set via env var (see --help). Env vars take effect
as defaults; CLI flags override them.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib import request

import boto3


# ---------- configuration ----------

def parse_args():
    p = argparse.ArgumentParser(
        description="EMR Studio + EMR on EKS resource hygiene CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--vc-ids",
        default=os.environ.get("VIRTUAL_CLUSTER_IDS"),
        help="Comma-separated EMR on EKS virtual cluster IDs "
             "(env: VIRTUAL_CLUSTER_IDS)",
    )
    p.add_argument(
        "--slack-webhook",
        default=os.environ.get("SLACK_WEBHOOK", ""),
        help="Slack webhook URL. If omitted, messages are logged to "
             "console only (env: SLACK_WEBHOOK)",
    )
    p.add_argument(
        "--warn-hours", type=int,
        default=int(os.environ.get("WARN_HOURS", "6")),
        help="Hours of runtime before warning a batch job's owner",
    )
    p.add_argument(
        "--kill-hours", type=int,
        default=int(os.environ.get("KILL_HOURS", "12")),
        help="Hours of runtime before cancelling a batch job",
    )
    p.add_argument(
        "--endpoint-warn-hours", type=int,
        default=int(os.environ.get("ENDPOINT_WARN_HOURS", "4")),
        help="Idle hours before warning an endpoint's owner",
    )
    p.add_argument(
        "--endpoint-kill-hours", type=int,
        default=int(os.environ.get("ENDPOINT_KILL_HOURS", "24")),
        help="Idle hours before deleting an endpoint",
    )
    p.add_argument(
        "--user-email-domain",
        default=os.environ.get("USER_EMAIL_DOMAIN", ""),
        help="Email domain for @-mention mailto links in Slack",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        default=os.environ.get("DRY_RUN", "false").lower() == "true",
        help="Log what would happen, but don't cancel or delete anything",
    )
    p.add_argument(
        "--list-only", action="store_true",
        help="Just list current resources and ages. No warnings, no kills.",
    )
    p.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION"),
        help="AWS region (default: from boto3 config chain)",
    )
    p.add_argument(
        "--profile",
        default=os.environ.get("AWS_PROFILE"),
        help="AWS profile to use",
    )
    p.add_argument(
        "-v", "--verbose", action="store_true",
        help="Debug-level logging",
    )

    args = p.parse_args()
    if not args.vc_ids:
        p.error("--vc-ids is required (or set VIRTUAL_CLUSTER_IDS env var)")
    return args


# ---------- main ----------

def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("emr-hygiene")

    session = boto3.Session(region_name=args.region, profile_name=args.profile)
    emr = session.client("emr-containers")
    cw = session.client("cloudwatch")

    vc_ids = [v.strip() for v in args.vc_ids.split(",") if v.strip()]
    log.info(f"checking {len(vc_ids)} virtual cluster(s): {vc_ids}")
    if args.list_only:
        log.info("LIST-ONLY MODE — no warnings or kills will be sent")
    elif args.dry_run:
        log.info("DRY-RUN MODE — nothing will actually be killed")

    stats = {
        "jobs_warned": 0, "jobs_killed": 0,
        "endpoints_warned": 0, "endpoints_killed": 0,
    }

    exit_code = 0
    for vc_id in vc_ids:
        try:
            check_job_runs(emr, vc_id, args, stats, log)
            check_managed_endpoints(emr, cw, vc_id, args, stats, log)
        except Exception as e:
            log.exception(f"failed checking vc {vc_id}: {e}")
            exit_code = 1

    log.info(
        f"done: jobs warned={stats['jobs_warned']} killed={stats['jobs_killed']}, "
        f"endpoints warned={stats['endpoints_warned']} killed={stats['endpoints_killed']}"
    )
    return exit_code


# ---------- batch job-runs ----------

def check_job_runs(emr, vc_id, args, stats, log):
    now = datetime.now(timezone.utc)
    pager = emr.get_paginator("list_job_runs")

    for page in pager.paginate(virtualClusterId=vc_id, states=["RUNNING"]):
        for job in page.get("jobRuns", []):
            age = now - job["createdAt"]
            hrs = int(age.total_seconds() // 3600)
            owner = owner_of(job)
            name = job.get("name", "<unnamed>")
            jid = job["id"]

            log.debug(f"job {jid} {name} owner={owner} age={hrs}h")

            if args.list_only:
                log.info(f"  JOB  {jid}  {name:30}  owner={owner:20}  age={hrs}h")
                continue

            if age >= timedelta(hours=args.kill_hours):
                if args.dry_run:
                    log.info(f"[DRY-RUN] would cancel job {jid} ({owner}, {hrs}h)")
                else:
                    log.warning(f"cancelling job {jid} ({owner}, {hrs}h)")
                    try:
                        emr.cancel_job_run(id=jid, virtualClusterId=vc_id)
                        post_slack(args, log,
                            f":skull: cancelled `{name}` "
                            f"({mention(owner, args)}) — was running {hrs}h.")
                    except Exception as e:
                        log.error(f"cancel_job_run failed for {jid}: {e}")
                        continue
                stats["jobs_killed"] += 1

            elif age >= timedelta(hours=args.warn_hours):
                log.info(f"warning owner of job {jid} ({owner}, {hrs}h)")
                post_slack(args, log,
                    f":warning: {mention(owner, args)} job `{name}` "
                    f"has been running *{hrs}h*. Will be killed at "
                    f"*{args.kill_hours}h*. "
                    f"Set `executionTimeoutMinutes` on submission to control this.")
                stats["jobs_warned"] += 1


# ---------- managed endpoints ----------

def check_managed_endpoints(emr, cw, vc_id, args, stats, log):
    pager = emr.get_paginator("list_managed_endpoints")

    for page in pager.paginate(virtualClusterId=vc_id, states=["ACTIVE"]):
        for ep in page.get("endpoints", []):
            ep_id = ep["id"]
            details = emr.describe_managed_endpoint(
                id=ep_id, virtualClusterId=vc_id
            ).get("endpoint", {})
            idle_h = endpoint_idle_hours(cw, vc_id, ep_id, details, args, log)
            owner = owner_of(details)
            name = details.get("name", "<unnamed>")

            log.debug(f"endpoint {ep_id} {name} owner={owner} idle={int(idle_h)}h")

            if args.list_only:
                log.info(f"  EP   {ep_id}  {name:30}  owner={owner:20}  idle={int(idle_h)}h")
                continue

            if idle_h >= args.endpoint_kill_hours:
                if args.dry_run:
                    log.info(f"[DRY-RUN] would delete endpoint {ep_id} "
                             f"({owner}, idle {int(idle_h)}h)")
                else:
                    log.warning(f"deleting endpoint {ep_id} ({owner}, idle {int(idle_h)}h)")
                    try:
                        emr.delete_managed_endpoint(id=ep_id, virtualClusterId=vc_id)
                        post_slack(args, log,
                            f":wastebasket: deleted endpoint `{name}` "
                            f"({mention(owner, args)}) — idle {int(idle_h)}h. "
                            f"Re-create from Studio when needed.")
                    except Exception as e:
                        log.error(f"delete_managed_endpoint failed for {ep_id}: {e}")
                        continue
                stats["endpoints_killed"] += 1

            elif idle_h >= args.endpoint_warn_hours:
                log.info(f"warning owner of endpoint {ep_id} ({owner}, idle {int(idle_h)}h)")
                post_slack(args, log,
                    f":zzz: {mention(owner, args)} endpoint `{name}` has been "
                    f"idle *{int(idle_h)}h*. Will be deleted at "
                    f"*{args.endpoint_kill_hours}h*. "
                    f"Detach your Studio Workspace if you're done.")
                stats["endpoints_warned"] += 1


def endpoint_idle_hours(cw, vc_id, ep_id, details, args, log):
    """
    Heuristic for endpoint idle time.

    Real signal: CPU usage on the endpoint's driver pod (requires Container
    Insights on the EKS cluster). Fallback: wall-clock age since the endpoint
    was created — coarser, but safe.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=args.endpoint_kill_hours + 2)

    try:
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
        log.debug(f"CW metric lookup failed for {ep_id}: {e}")

    created = details.get("createdAt", end)
    return (end - created).total_seconds() / 3600


# ---------- helpers ----------

def owner_of(resource):
    """
    Extract the human owner of a job-run or endpoint from tags.
    Studio auto-tags vary by configuration; we check the common ones.
    """
    tags = resource.get("tags", {}) or {}
    for key in ("submittedBy",
                "StudioUser",
                "aws:emr-studio:UserArn",
                "emr-studio:UserArn"):
        if key in tags and tags[key]:
            v = tags[key]
            return v.split("/")[-1] if "/" in v else v
    return "unknown"


def mention(owner, args):
    """Slack mention if we can build one; else plain bold name."""
    if owner == "unknown" or not args.user_email_domain:
        return f"*{owner}*"
    return f"<mailto:{owner}@{args.user_email_domain}|*{owner}*>"


def post_slack(args, log, text):
    """Post to Slack if a webhook is configured; otherwise log to console."""
    if not args.slack_webhook:
        log.info(f"[would-slack] {text}")
        return
    req = request.Request(
        args.slack_webhook,
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        request.urlopen(req, timeout=5)
    except Exception as e:
        log.error(f"slack post failed: {e}")


if __name__ == "__main__":
    sys.exit(main())
