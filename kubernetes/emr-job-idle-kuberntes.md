```text
we have huge EMR cluster running on kubernetes.Our modellers use it and they run their jupyter notebooks. It could be EMR studion, Sagemanekr studion or slef managed jupyter notebook they use to run theie spark jobs using jupyter notebook.

what happens is:
- A notebook is left attached over the weekend; the managed endpoint
  (Spark driver pod) stays active the whole time.
- A batch job hangs on an unproductive stage and runs for days.
- A Workspace is closed in the browser, but the backing endpoint stays up
  because nothing told it to shut down
so resources are wasted.

can you help me write a script to identify jobs that are running jobs, the job has completed long ago but they have forgotten to run  the spark.stop cell or something else to the effect that the job is hanging on to the resources , keeping the cluster up and pod up - not allowing it to resize/shrink
I can run this script a aws boto3 script possible run from time to time,  identify all the resourcethat are idle for more than 30  minutes and print  a list
```

It’s a notoriously common headache with EMR on EKS. Because AWS treats Managed Endpoints (your EMR Studio backends) and
Batch Jobs as standard Kubernetes resources, they will happily sit there burning money if a user closes their browser
tab without explicitly terminating the Spark session or if a batch job hangs on a dead stage.

The challenge with a purely `boto3`-based approach is that the AWS API only knows if a Managed Endpoint is `ACTIVE` or
if a Batch Job is `RUNNING`. It doesn't natively look inside the Jupyter kernel or Spark Context to see if it has been
idle for 30 minutes.

To bridge this gap, we can use a script that combines the `emr-containers` client (to find what is running) with the
`cloudwatch` client (using EKS Container Insights) to look for proxy indicators of idleness—like practically zero CPU
utilization over the last 30 minutes.

Here is a `boto3` script you can run via cron or AWS Lambda to print a list of wasteful resources.

### The Boto3 Audit Script

**Prerequisites:** You need `boto3` installed, appropriate IAM permissions to list EMR containers and read CloudWatch
metrics, and **EKS Container Insights** enabled on your cluster so CloudWatch can see the pod CPU utilization.

```python
import boto3
from datetime import datetime, timezone, timedelta


def identify_wasted_emr_resources():
    emr_client = boto3.client('emr-containers')
    cw_client = boto3.client('cloudwatch')
    now = datetime.now(timezone.utc)

    # --- Configuration Thresholds ---
    HANGING_BATCH_JOB_HOURS = 24  # Flag batch jobs running longer than a day
    ORPHAN_ENDPOINT_HOURS = 48  # Flag interactive endpoints left up over the weekend
    IDLE_MINUTES = 30  # CloudWatch lookback window for idleness
    CPU_IDLE_THRESHOLD = 5.0  # Percent CPU utilization considered "idle"

    print(f"--- Scanning EMR on EKS Cluster Resources ({now.strftime('%Y-%m-%d %H:%M')} UTC) ---\n")

    # 1. Fetch all running virtual clusters
    v_clusters = emr_client.list_virtual_clusters(states=['RUNNING']).get('virtualClusters', [])

    for vc in v_clusters:
        vc_id = vc['id']
        vc_name = vc['name']

        # Safely extract K8s details
        try:
            namespace = vc['containerProvider']['info']['eksInfo']['namespace']
            eks_cluster = vc['containerProvider']['id']
        except KeyError:
            continue  # Skip if not a standard EKS provider configuration

        print(f"\n🔍 Virtual Cluster: {vc_name} (Namespace: {namespace})")

        # ==========================================
        # 1. IDENTIFY HANGING BATCH JOBS
        # ==========================================
        jobs = emr_client.list_job_runs(virtualClusterId=vc_id, states=['RUNNING']).get('jobRuns', [])
        for job in jobs:
            runtime_hours = (now - job['createdAt']).total_seconds() / 3600
            if runtime_hours > HANGING_BATCH_JOB_HOURS:
                print(
                    f"  [⚠️ HANGING BATCH JOB] '{job['name']}' ({job['id']}) has been running for {runtime_hours:.1f} hours.")

        # ==========================================
        # 2. IDENTIFY IDLE/ORPHANED NOTEBOOK ENDPOINTS
        # ==========================================
        endpoints = emr_client.list_managed_endpoints(virtualClusterId=vc_id, states=['ACTIVE']).get('endpoints', [])

        for ep in endpoints:
            uptime_hours = (now - ep['createdAt']).total_seconds() / 3600
            ep_id = ep['id']
            ep_name = ep['name']

            # Check 1: Is this an old endpoint left on over the weekend?
            if uptime_hours > ORPHAN_ENDPOINT_HOURS:
                print(f"  [⚠️ ORPHANED ENDPOINT] '{ep_name}' ({ep_id}) ACTIVE for {uptime_hours:.1f} hours.")

            # Check 2: Has it been completely idle for the last 30 minutes?
            # We check the overall namespace CPU. If the namespace is dead quiet, the driver pod isn't doing anything.
            metrics = cw_client.get_metric_statistics(
                Namespace='ContainerInsights',
                MetricName='namespace_cpu_utilization',
                Dimensions=[
                    {'Name': 'ClusterName', 'Value': eks_cluster},
                    {'Name': 'Namespace', 'Value': namespace}
                ],
                StartTime=now - timedelta(minutes=IDLE_MINUTES),
                EndTime=now,
                Period=1800,  # 1 data point for the full 30 mins
                Statistics=['Average']
            )

            datapoints = metrics.get('Datapoints', [])
            if datapoints:
                avg_cpu = datapoints[0]['Average']
                if avg_cpu < CPU_IDLE_THRESHOLD:
                    print(
                        f"  [💤 IDLE CPU] Endpoint '{ep_name}' ({ep_id}) CPU is highly idle ({avg_cpu:.2f}%) over the last 30 mins.")


if __name__ == "__main__":
    identify_wasted_emr_resources()

```

### The "Root Cause" Fix: Native Culling

While running a script to identify these resources is a great stopgap, you can actually force the underlying Jupyter
kernels to kill themselves natively when they are created, which automatically releases the resources back to Kubernetes
so the cluster can shrink.

EMR on EKS uses Jupyter Enterprise Gateway (JEG) behind the scenes for interactive endpoints. JEG has native environment
variables designed exactly for this. When you or your automated systems create the Managed Endpoint, you can pass
configurations to enforce culling:

```json
{
  "applicationConfiguration": [
    {
      "classification": "jupyter-enterprise-gateway",
      "properties": {
        "EG_CULL_IDLE_TIMEOUT": "1800",
        "EG_CULL_CONNECTED_KERNEL_TIMEOUT": "1800"
      }
    }
  ]
}

```

Setting `EG_CULL_IDLE_TIMEOUT` to `1800` (30 minutes) tells the gateway to terminate the Spark driver pod if the Jupyter
kernel hasn't received a cell execution request in 30 minutes.

# simple audting solutions

If you just want to audit and are looking for something simpler than maintaining a custom Python script, you can
leverage the tools you likely already have running in your environment.

Since EMR on EKS is ultimately just Kubernetes under the hood, here are three simpler, low-code or no-code ways to audit
these wasted resources.

### 1. The Quickest: A `kubectl` One-Liner

Because Spark drivers are just Kubernetes pods, you don't actually need to query the AWS EMR API to find out how long
they've been running. You can just ask Kubernetes to show you the oldest running Spark drivers.

If your engineers have access to run `kubectl` commands against the cluster, this one-liner lists all Spark driver pods
across all namespaces, sorted by the oldest first:

```bash
kubectl get pods --all-namespaces -l spark-role=driver --field-selector=status.phase=Running --sort-by=.metadata.creationTimestamp

```

**Why it’s simple:** No code to write. You can instantly see if a driver has an `AGE` of 3 days. It doesn't show "
idleness" (CPU), but it immediately highlights abandoned weekend jobs.

### 2. The "No-Code" AWS Way: CloudWatch Alarms

Instead of writing a script that constantly checks CloudWatch, you can make CloudWatch do the work for you by setting up
an **Alarm**.

Since you have EKS Container Insights enabled, you already have metrics for `pod_cpu_utilization` and
`namespace_cpu_utilization`.

* **How to do it:** Go to the AWS CloudWatch Console. Create a new Alarm based on the Container Insights
  `namespace_cpu_utilization` metric (or pod-level if you put multiple jobs in one namespace).
* **The Condition:** Set it to trigger if the CPU Average is `< 5%` for `30 minutes`.
* **The Action:** Send an email via AWS SNS to your platform/data engineering team.
  **Why it’s simple:** It’s a "set it and forget it" UI configuration. You get an email alerting you to an idle
  namespace without writing or hosting a single line of code.

### 3. The Visual Tool: Kubecost (EKS standard)

If you are running a huge EMR cluster on EKS, there is a very high chance your infrastructure team is running **Kubecost
** (AWS provides a customized version of this specifically for EKS for free).

* **How to use it:** Open your Kubecost dashboard and go to the **Savings > Abandoned Workloads** or **Idle Clusters**
  report.
* **What it does:** Kubecost natively tracks pods that are requesting resources but not actually utilizing CPU/Network
  over a trailing 7-day period.
  **Why it’s simple:** It gives you a clean web dashboard that literally translates your idle Spark pods into a dollar
  amount of wasted money, which is incredibly effective for showing modelers why they need to close their notebooks.

### The Best Minimal-Effort Strategy

If you want immediate visibility today: Run the **`kubectl` one-liner** to find the jobs that have been stuck since
Friday.
If you want proactive auditing next week: Set up a single **CloudWatch Alarm** to email you when a Jupyter namespace
drops below 5% CPU for 30 minutes.

# conenct to kubecost using script to identify idle jobs

Yes, it is absolutely possible. Under the hood, the Kubecost UI is entirely powered by its own REST API. You can bypass
the dashboard and query these APIs directly using Python, a shell script, or any standard HTTP client.

This is incredibly useful for automating alerts or integrating the data into your own internal reporting tools.

Here is how you can do it using both Python and a Shell script.

### Prerequisites: Accessing the API

To run these scripts, you need to be able to reach your Kubecost service. If you are running the script from your local
machine, you usually need to port-forward the Kubecost service first:

```bash
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090

```

*(If your script runs on a pod inside the cluster, or if Kubecost is exposed via an Ingress, just
replace `http://localhost:9090` with the appropriate internal DNS or Ingress URL).*

---

### Option 1: Python Script

This Python script uses the `requests` library to fetch the abandoned workloads and prints them out nicely. It queries
the `/model/savings/abandonedWorkloads` endpoint.

```python
import requests
import json

# Replace with your Kubecost URL
KUBECOST_URL = "http://localhost:9090"


def get_abandoned_workloads():
    endpoint = f"{KUBECOST_URL}/model/savings/abandonedWorkloads"

    # Optional parameters: 
    # days = lookback window (default is usually 2 or 7)
    params = {
        "days": 7
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        # Depending on your Kubecost version, the payload might be wrapped in a "data" object
        workloads = data.get('data', data) if isinstance(data, dict) else data

        if not workloads:
            print("No abandoned workloads found.")
            return

        print(f"{'NAMESPACE':<20} | {'POD':<40} | {'MONTHLY SAVINGS'}")
        print("-" * 80)

        total_wasted = 0

        for item in workloads:
            ns = item.get('namespace', 'Unknown')
            pod = item.get('pod', 'Unknown')
            savings = item.get('monthlySavings', 0.0)
            total_wasted += savings

            print(f"{ns:<20} | {pod:<40} | ${savings:.2f}")

        print("-" * 80)
        print(f"Total potential monthly savings: ${total_wasted:.2f}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Kubecost API: {e}")


if __name__ == "__main__":
    get_abandoned_workloads()

```

### Option 2: Shell Script (Bash + jq)

If you just want a quick pipeline script, you can use `curl` and `jq` (a command-line JSON processor).

```bash
#!/bin/bash

KUBECOST_URL="http://localhost:9090"
DAYS=7

echo "Fetching abandoned workloads from Kubecost..."

# Fetch the data and parse it with jq
curl -s "${KUBECOST_URL}/model/savings/abandonedWorkloads?days=${DAYS}" | \
jq -r '
  if type == "object" and .data then .data else . end | 
  .[] | 
  "Namespace: \(.namespace) | Pod: \(.pod) | Wasting: $\(.monthlySavings)"
' | sort

```

### What about "Idle Clusters"?

If you want to look at general idleness at a broader level (like a whole namespace or cluster) rather than
specifically "abandoned network workloads", you can query the **Allocation API** (`/model/allocation`).

By hitting `/model/allocation?window=7d&aggregate=namespace`, Kubecost will return data that includes the `cpuIdle` and
`ramIdle` coefficients. If you write a script that looks for namespaces where `cpuIdle` is extremely close to `1.0` (
meaning 100% idle), you can confidently identify namespaces that are provisioned but doing absolutely no computational
work.