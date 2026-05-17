# EMR on Kubernetes — A Practical Handbook

> A reference for modellers, platform engineers, and anyone responsible for keeping the cluster healthy and the bill
> low.

---

## Table of contents

1. [Why this changed](#1-why-this-changed)
2. [Kubernetes in ten minutes](#2-kubernetes-in-ten-minutes)
3. [EMR on EKS — the actual architecture](#3-emr-on-eks--the-actual-architecture)
4. [Translating from EMR Classic](#4-translating-from-emr-classic)
5. [Multi-tenancy — how teams share one cluster](#5-multi-tenancy--how-teams-share-one-cluster)
6. [Where Jupyter lives now](#6-where-jupyter-lives-now)
7. [Job lifecycle, application IDs, and history](#7-job-lifecycle-application-ids-and-history)
8. [Auto-scaling — what happens during and after a job](#8-auto-scaling--what-happens-during-and-after-a-job)
9. [The zombie session problem — and how to kill it](#9-the-zombie-session-problem--and-how-to-kill-it)
10. [Cost optimization playbook](#10-cost-optimization-playbook)
11. [Operator's checklist](#11-operators-checklist)
12. [Glossary](#12-glossary)
13. [Useful kubectl commands](#13-useful-kubectl-commands)

---

## 1. Why this changed

You used to run Spark on **EMR Classic** (EMR on EC2). That world looked like this:

- A long-lived cluster with a **Master node** (running YARN ResourceManager and a Jupyter service), **Core nodes** (
  HDFS + executors), and **Task nodes** (executors only).
- Jobs submitted with `spark-submit` to YARN, which decided where to run them.
- Each cluster belonged to one team or one purpose, because mixing workloads on one YARN cluster was painful.

> The YARN ResourceManager runs on the master node of a Hadoop cluster (typically a dedicated machine, sometimes called
> the "master" or "namenode host").

### A quick breakdown of the YARN daemon layout:

- ResourceManager (RM) — runs on the master node. There's one active RM per cluster.
- NodeManager (NM) — runs on every worker/slave node(Task Node). It manages containers, monitors resource usage (CPU,
  memory, disk), and reports back to the RM.
- ApplicationMaster (AM) — runs inside a container on one of the worker nodes (not on the RM). One per application/job.
  Typically there are more than 1 application manager(Core Node))

You are now running **EMR on EKS**. EKS is Amazon's managed Kubernetes service. The Spark engine itself is essentially
unchanged — your jobs still produce a DataFrame plan, still have a driver and executors, still write to S3. What changed
is **the resource manager underneath**.

| Layer            | EMR Classic                            | EMR on EKS                                                     |
|------------------|----------------------------------------|----------------------------------------------------------------|
| Cluster type     | Long-lived, single-purpose             | Shared, multi-tenant                                           |
| Resource manager | YARN                                   | Kubernetes                                                     |
| Node roles       | Master / Core / Task                   | Control plane (managed) + worker nodes                         |
| Job unit         | A YARN application                     | A set of Kubernetes pods                                       |
| Job isolation    | One cluster per team                   | One namespace per team in one cluster                          |
| Jupyter          | Hosted on the master node              | EMR Studio, managed endpoints, or self-hosted JupyterHub       |
| Auto-scaling     | EMR managed scaling on instance groups | Cluster Autoscaler or Karpenter, plus Spark dynamic allocation |
| Cost model       | You pay for the cluster while it's up  | You pay for the pods + nodes while they exist                  |

The single biggest mental shift: **there is no YARN, and there is no master node**. There is a Kubernetes control
plane (which you don't manage and can mostly ignore) and a pool of worker nodes that everyone shares.

---

## 2. Kubernetes in ten minutes

Kubernetes ("K8s") is a system for running containers reliably across many machines. Spark on Kubernetes runs the driver
and each executor as a container in its own **pod**.

### The control plane

A small set of services — `kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager` — that together accept
requests, decide where pods should run, and reconcile reality with the desired state. On EKS, AWS runs this for you. You
never SSH into it. You interact with it through the **Kubernetes API** (via `kubectl`, the AWS CLI, or job-submission
tooling).

This is the part that **replaces YARN's ResourceManager**.
> EMR Studio → EMR control plane: When the user runs a cell or submits a job, the Workspace calls the EMR service API (
> the control plane)

### Worker nodes

EC2 instances (or Fargate micro-VMs) that actually run your workloads. The control plane schedules pods onto these
nodes. Each node runs a small agent called `kubelet` that talks back to the control plane and manages local pods.

If a node dies, the control plane reschedules its pods elsewhere. If you need more capacity, an auto-scaler adds nodes.
If pods sit idle for long enough, an auto-scaler removes nodes.

### Pods

The unit of scheduling. A pod is one or more containers that share a network namespace and storage. **For Spark, each
driver is one pod and each executor is one pod.** Pods are deliberately ephemeral — they get created, they run, they
die. If your code assumes anything is on local disk between job runs, you will be unhappy.

### Namespaces

A logical partition of the cluster. Used for multi-tenancy. Pods, services, and quotas all live inside a namespace. *
*Each team in your org typically gets one or more namespaces.** A "noisy neighbor" job in namespace `team-a` can be
prevented from starving namespace `team-b` by attaching **resource quotas** to each.

### Deployments, Jobs, and the Spark Operator

Higher-level objects that describe *what should be running*, leaving the control plane to figure out how. A few you'll
encounter:

- **Deployment** — long-running services (your Jupyter pod, your monitoring tools).
- **Job** — a pod that runs to completion (a batch job).
- **`SparkApplication`** — a custom resource added by the **Spark Operator**. You submit a YAML that says "run this jar
  with these resources" and the operator creates the driver pod, watches for it, and reports status.

EMR on EKS uses its own controller (the EMR job-run controller) that does roughly the same thing as the open-source
Spark Operator, but with EMR-specific features (managed Spark runtimes, IAM integration, EMR Studio integration, billing
tags).

### Why this matters for Spark

YARN tracked containers. Kubernetes tracks pods. **The mapping is essentially one-to-one.** Where YARN would say "give
me 10 containers, 4 cores and 8 GB each", a Spark-on-K8s job says "give me 10 executor pods, each requesting 4 CPU and 8
GB". The Kubernetes scheduler then finds nodes with capacity for them.

---

## 3. EMR on EKS — the actual architecture

Walk through what happens, step by step, when a modeller submits a job.

**1. Submission.** The user (or Jupyter, or Airflow, or a CI job) makes an API call: "start this Spark application in
EMR **virtual cluster** `vc-team-a`." A virtual cluster is just an EMR-managed handle that points at a Kubernetes
namespace. So `vc-team-a` is really "namespace `team-a` in EKS cluster `analytics-prod`".

**2. Job-run controller acts.** The EMR controller running inside the EKS cluster receives the request, looks up the
right namespace, and creates a **driver pod** there. It also stamps the pod with the right IAM role (via IRSA — IAM
Roles for Service Accounts), so the driver can read its data from S3 without baked-in credentials.

**3. Driver schedules.** The Kubernetes scheduler picks a worker node with enough free CPU and memory and places the
driver pod there. If no node has room, the **cluster auto-scaler** (Karpenter or Cluster Autoscaler) requests a new EC2
instance from AWS. This usually takes 30–90 seconds.

**4. Driver requests executors.** Once the driver starts, it asks the Kubernetes API for executor pods. They get
scheduled the same way. If dynamic allocation is on, this scales up as needed.

**5. Job runs.** Driver and executors run, read from S3, do their work, write back to S3.

**6. Job ends.** The driver writes its final event log to S3 (where the Spark History Server can later replay it), then
exits. Executor pods exit too. After a short grace period, the pods are **garbage collected**. The nodes they ran on are
now under-utilized, and the auto-scaler will **consolidate** them — moving any remaining pods around and terminating
empty instances.

This is what the Kubernetes equivalents of your old EMR concepts look like:

```
EMR Classic                          EMR on EKS
------------                         ----------
Master node                    ->    AWS-managed control plane (invisible)
Core node                      ->    Worker node + executor pods
Task node                      ->    Worker node + executor pods
YARN ResourceManager           ->    kube-scheduler
YARN ApplicationMaster         ->    Spark driver pod
YARN container                 ->    Executor pod
EMR cluster                    ->    EKS cluster
EMR step                       ->    EMR job run (one SparkApplication)
HDFS                           ->    S3 (typically; HDFS is rare here)
```

### Node pools

A single EKS cluster usually has multiple **node groups** (or with Karpenter, multiple **NodePools**), each tuned for a
workload type:

- A small **on-demand** pool for drivers (drivers must not be killed mid-job by a spot interruption).
- A larger **spot** pool for executors (executors are restartable; losing one is fine).
- Optionally a **GPU** pool for ML training.
- Optionally a **memory-optimized** pool for big aggregations.

Pods request nodes from a particular pool using **node selectors** or **taints/tolerations**.

---

## 4. Translating from EMR Classic

Some things you used to do, and how they translate:

**"SSH to the master and run `spark-submit`."** You don't. There's no master to SSH into. You submit jobs via the EMR
API (`aws emr-containers start-job-run`), through EMR Studio, or through whatever scheduler you're using (Airflow with
the `EmrContainerOperator`, Argo Workflows, etc.).

**"Check the YARN UI."** The YARN UI doesn't exist. To see running jobs:

- `kubectl get pods -n <team-namespace>` — what's actually running right now.
- The **Spark UI** of a live driver, exposed via port-forward or an ingress.
- The **Spark History Server** for jobs that have finished.

**"Look at YARN logs."** Logs are written by each pod to stdout/stderr, picked up by Fluent Bit (or whatever log
forwarder is configured), and sent to **CloudWatch Logs** or **S3**.

**"Resize the cluster."** You don't resize the cluster; the cluster resizes itself in response to pending pods. What you
can change is the auto-scaler's policy (max nodes, instance types, spot fraction) and the per-namespace quotas.

**"Hit the Jupyter URL on the master."** See section 6.

---

## 5. Multi-tenancy — how teams share one cluster

You said the cluster is "one huge cluster" used by multiple teams. That's the standard pattern, and Kubernetes has the
tools to make it work — but only if they're configured. Don't assume the platform team has set all of these up; check.

### The boundary objects

**Namespaces.** Every team gets at least one. All of a team's pods, services, and config live there. RBAC controls who
can read or write each namespace.

**ResourceQuotas.** Cap total CPU, memory, GPU, and pod count per namespace. Example:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "200"
    requests.memory: 800Gi
    requests.nvidia.com/gpu: "4"
    pods: "300"
```

Once `team-a` is using 200 CPU of requests, any new pods they create stay `Pending` until something frees up. This is
what prevents one team from draining the cluster.

**LimitRanges.** Provide defaults and ceilings for individual pods, so a modeller can't ask for one pod with 96 CPUs.

**PriorityClasses.** Optional, but useful: production jobs can preempt experimental ones in a contention scenario.

**IAM Roles for Service Accounts (IRSA).** Each namespace's service account is mapped to an AWS IAM role. Pods in
`team-a` can only assume roles team A is allowed to assume, so they can only read team A's S3 prefixes.

**NetworkPolicies.** Constrain which pods can talk to which. Often used to prevent one team's pods from reaching
another's services.

### The good and the not-so-good of a single cluster

**Good.** Higher utilization (one auto-scaler pool serving everyone), one upgrade path, one observability stack, one
cost center, easier to share GPU capacity.

**Not-so-good.** Larger blast radius — a control plane issue affects everyone. A misconfigured quota lets one team
starve others. An EKS version upgrade has to be coordinated across all teams.

**The usual answer** is a single cluster per environment (`dev`, `staging`, `prod`) with strong namespace isolation,
rather than a cluster per team. If you ever need harder isolation (different compliance regimes, very different scaling
profiles), spin up a second cluster — but do this deliberately, not by default.

---

## 6. Where Jupyter lives now

This is the question that bites every team coming from EMR Classic, because Jupyter is no longer a feature of the
cluster — it's a separate component you choose and operate.

You have three common options:

**Option A: EMR Studio.** AWS-managed. Modellers log in through SSO, get a Jupyter workspace, attach it to a virtual
cluster, and submit jobs. The notebook runtime itself runs in EMR Studio's hosted environment; the Spark driver and
executors run in your EKS cluster. Lowest operational burden.

**Option B: Managed endpoints (EMR on EKS Interactive endpoints / Livy).** A long-running pod inside your EKS cluster
that exposes a Livy or Jupyter Kernel Gateway endpoint. Modellers point a Jupyter client at it. Spark sessions are
launched on demand inside the same cluster.

**Option C: Self-hosted JupyterHub.** A JupyterHub deployment running in EKS. Each user gets their own Jupyter pod.
Inside the notebook, `sparkmagic` or `pyspark` connects to Spark, which submits to EMR on EKS. Most flexibility, highest
operational burden.

The important thing to know: **the Jupyter kernel and the Spark driver are now separate pods.** When the modeller's
notebook is idle, the Jupyter pod is idle (cheap). When they execute a cell that touches Spark, the Spark driver and
executors get created in their team's namespace. When the Spark session closes, those pods exit and the resources go
back to the pool.

What that means in practice — and why it's the cause of most cost surprises — is the focus of section 9.

---

## 7. Job lifecycle, application IDs, and history

You asked: *does every job have an application ID? Can we see them on the Spark History Server?* Yes to both.

### The lifecycle of a single job

```
[Submit]                  EMR API: StartJobRun  -> assigns a job-run-id
   |
[Driver pod created]      kubectl get pods shows it as Pending then Running
   |
[Spark application starts] Spark assigns an application-id like spark-abc123…
                          This is the ID you'll see in the Spark UI and history server
   |
[Executors created]       N executor pods, each linked to the driver
   |
[Stages, tasks run]       Visible live in the Spark UI; metrics streamed to CloudWatch
   |
[Driver completes]        Writes event log to S3:  s3://.../logs/spark-events/spark-abc123…
                          Pod enters Completed state, hangs around briefly
   |
[GC]                      Pod is deleted; node may consolidate
   |
[History Server]          Reads the event log from S3 and renders it for replay
```

### Where to look during a job

- **Spark UI (live).** Each driver pod hosts a Spark UI on port 4040. You access it through `kubectl port-forward` or,
  in EMR Studio, through a built-in link. This is the equivalent of clicking "Application UI" in the YARN
  ResourceManager.
- **`kubectl get pods -n <team-ns>`.** Shows the driver and executor pods, their state, and how long they've been
  running.
- **`kubectl logs <pod>`.** stdout/stderr of a single pod.
- **CloudWatch Logs / Container Insights.** Aggregated logs and metrics.

### Where to look after a job

- **Spark History Server.** A deployment in your cluster (or hosted by EMR) that reads event logs from your S3 logs
  bucket. You'll see every job's `application-id`, its DAG, its stages, shuffle metrics, executor times. **This is how
  you debug "why did yesterday's job take 4 hours?"**
- **CloudWatch.** For pod-level metrics and OOM diagnoses.
- **The S3 event-log location itself.** Each job writes a single event log file (JSON, sometimes gigabytes). You can
  copy one down and replay it locally with `start-history-server.sh` if needed.

### IDs you'll encounter

- `job-run-id` — the EMR-on-EKS-level handle for a submission. Returned by `start-job-run`.
- `application-id` (e.g. `spark-1234…`) — the Spark-level ID. Appears in the Spark UI, History Server, and event log
  filename.
- Pod names (e.g. `spark-1234-driver`, `spark-1234-exec-1`, `spark-1234-exec-2`…) — Kubernetes-level handles.

All three are stamped onto each event so you can grep across log systems.

---

## 8. Auto-scaling — what happens during and after a job

This is the part where most teams either save real money or waste it. The flow has two independent loops.

### Loop 1: Pod-level — Spark dynamic allocation

When **`spark.dynamicAllocation.enabled=true`** is set, the driver asks for more executors when there's work queued, and
**releases idle executors** after `spark.dynamicAllocation.executorIdleTimeout` (default 60s).

This is the same dynamic allocation you'd use on YARN, but on Kubernetes you also need shuffle service support — either
the external shuffle service (rare on K8s) or, more commonly, **`spark.dynamicAllocation.shuffleTracking.enabled=true`
**, which keeps executors with shuffle data alive a bit longer.

When the **job finishes**, the driver tells all remaining executors to shut down. Those pods exit. The nodes they were
on become underutilized.

### Loop 2: Node-level — Karpenter or Cluster Autoscaler

A node-level auto-scaler watches for two situations:

- **Pending pods that can't be scheduled** → it provisions a new node sized to fit them.
- **Underutilized nodes** → it consolidates pods onto fewer nodes and terminates the empties.

**Karpenter** does this faster and more flexibly than the older Cluster Autoscaler — it picks an EC2 instance type
optimized for the pending workload (rather than scaling a fixed instance-type group), and it actively consolidates. *
*For a multi-tenant Spark cluster, Karpenter is the modern default.**

### So what happens when a Spark job finishes?

In sequence:

1. Driver writes its event log, exits, pod is marked Completed.
2. Executor pods exit and are deleted within seconds.
3. Whatever nodes were running only those executors are now empty.
4. Karpenter sees empty / under-utilized nodes and, after a short cooldown (default
   `consolidationPolicy: WhenUnderutilized`), drains and terminates them.
5. The remaining cluster footprint reflects what's actually still running.

End state: **a finished job leaves zero footprint within a few minutes.** Provided everything was configured correctly.
Which brings us to…

---

## 9. The zombie session problem — and how to kill it

This is the scenario you described: *the modeller's code ran, but they didn't call `spark.stop()`, the Spark session is
still alive, executors are sitting idle, the cluster has not scaled down.*

It happens on EKS for the same reason it happens on EMR Classic: **as long as the driver is alive, it can hold
executors.** A Jupyter kernel keeps a `SparkSession` object in memory; that session is connected to a driver; the driver
keeps executors. None of it scales down because none of it has been told to.

There is **no single fix** — you stack a few defenses.

### Defense 1: Dynamic allocation with shuffle tracking

Always enable on multi-tenant clusters. After `executorIdleTimeout`, executors release even if the driver is still
alive. Recommended baseline:

```
spark.dynamicAllocation.enabled                          true
spark.dynamicAllocation.shuffleTracking.enabled          true
spark.dynamicAllocation.executorIdleTimeout              60s
spark.dynamicAllocation.shuffleTracking.timeout          300s
spark.dynamicAllocation.minExecutors                     0
spark.dynamicAllocation.initialExecutors                 2
```

With `minExecutors=0`, an idle session can be reduced to **just the driver pod** (typically 1–4 GB of memory), which is
far cheaper than 20 idle executor pods.

#### If you want true resume-across-days semantics

That's a different design problem and Spark doesn't give it to you for free. Options:
- Materialize intermediate results to S3 as Parquet/Delta/Iceberg tables at logical checkpoints in the notebook, so
Monday's first cells just read them back.
- Use Spark's checkpoint() to a durable filesystem for long lineage chains (helps recomputation cost, not session resume).
- For ML specifically, persist fitted models/pipelines to S3 via MLflow or model.save().

> Ref: [notes-for-modellers.md](notes-for-modellers.md)

### Defense 2: Jupyter kernel idle culler

JupyterHub and modern Jupyter Server support a **kernel idle culler** that terminates any kernel idle for longer than a
threshold. When the kernel dies, the `SparkSession` is garbage-collected, the driver exits, and the rest of the cleanup
chain runs.

Recommended config (for JupyterHub):

```python
# You can add this at the top — it's not required, but it stops the linter from complaining about undefined c:
from traitlets.config import get_config  # noqa
c = get_config()  # type: ignore

c.MappingKernelManager.cull_idle_timeout = 1800  # 30 minutes
c.MappingKernelManager.cull_interval = 300  # check every 5 minutes
c.MappingKernelManager.cull_connected = True  # cull even if browser tab is open
```

The "cull connected" flag matters: without it, a modeller who leaves their browser tab open all weekend defeats the
culler.

### Defense 3: Hard job TTL

For batch jobs, set a hard time-to-live so a hung job doesn't run forever. With EMR on EKS, set
`executionTimeoutMinutes` on the job run. With raw Spark-on-K8s, use a `BackoffLimit` and an `activeDeadlineSeconds` on
the Kubernetes Job.

### Defense 4: Pod-level eviction policies

Set **PodDisruptionBudgets** carefully (they protect *important* pods from being evicted), and consider a **TTL
controller** that deletes pods that have been `Completed` for more than a few minutes. EMR on EKS does this by default,
but verify.

### Defense 5: Notebook hygiene — the human side

Tooling can't fix everything. A short internal guide for modellers helps:

- **Always create your `SparkSession` with `appName` set to something identifiable.** Future-you grepping the History
  Server will thank present-you.
- **Call `spark.stop()` at the end of a notebook** — or wrap your code in a `try/finally` that does. This isn't strictly
  required (the culler will eventually save you) but it's the polite thing to do.
- **Don't request 200 executors for exploratory work.** Start small. Let dynamic allocation grow as needed.
- **Don't leave a tab open over the weekend with a `SparkSession` you're "going to come back to".** The
  kernel-idle-culler is a backstop, not a strategy.

### Defense 6: Monitoring and a public dashboard

A Grafana dashboard showing each team's namespace usage, with a "longest-running idle session" leaderboard, changes
behavior fast. Nobody wants to be on the leaderboard.

---

## 10. Cost optimization playbook

The compounding savings, roughly in order of impact.

### 10.1 Right-size pod requests and limits

The single biggest source of waste. A pod requests resources; the cluster reserves them; if the pod doesn't actually use
them, the gap is paid for and unused.

- **Requests** = what the scheduler reserves. Set close to what you actually use.
- **Limits** = the ceiling. Set generously, but not infinitely (so a runaway pod doesn't take down a node).
- Spark drivers can usually live with **1 CPU / 4 GB**; if a job's driver is consistently OOMing, look at the driver
  workload (collecting too much, broadcasting large objects), not just the size.
- For executors, the sweet spot is usually **4–8 CPU per executor with 4–8 GB per core**. Going larger gets less
  parallelism per cost; going smaller increases shuffle overhead.

### 10.2 Use spot for executors

Executors are restartable. Spark will retry lost tasks. **Run executors on spot capacity** — typically 60–80% cheaper
than on-demand. Keep drivers on on-demand so they survive interruption.

Configure node selectors / taints so Spark drivers schedule onto the on-demand pool and executors onto spot:

```yaml
# In the SparkApplication / EMR job-run spec
driver:
  nodeSelector:
    karpenter.sh/capacity-type: on-demand
executor:
  nodeSelector:
    karpenter.sh/capacity-type: spot
```

### 10.3 Karpenter > Cluster Autoscaler

If you're still on the older Cluster Autoscaler with fixed node groups, migrate to Karpenter. Karpenter chooses instance
types per workload, scales faster, and consolidates more aggressively. The migration itself usually pays for itself
within a month.

### 10.4 Bin-pack with smaller executors

Slightly counterintuitive: **smaller, more numerous executors pack better.** A 16-CPU node holds three 5-CPU executors
with one CPU wasted, or two 7-CPU executors with two wasted. Tuning here is workload-specific; measure.

### 10.5 Per-namespace quotas + chargeback

Quota everyone. Tag pods with team/cost-center labels. Use **Kubecost** or **OpenCost** to produce a per-team monthly
cost report. Once teams see the bill that belongs to them, behavior changes.

### 10.6 S3 lifecycle policies for logs

Spark event logs and CloudWatch logs accumulate. Set a lifecycle policy: 30 days hot, 90 days infrequent access, then
expire. This is small money individually but adds up.

### 10.7 Reserved Instances or Savings Plans for the baseline

If your cluster has a stable floor of usage (say, 40 CPU on-demand always running for drivers and the control-plane
components), buy a Compute Savings Plan for it. ~30–40% off list price for predictable load. Don't over-commit; you want
headroom for spot to handle the variable layer.

### 10.8 Right-size the driver pool

Drivers are small but numerous if you have many parallel jobs. A separate small-instance pool (`m6i.large` etc.) sized
for drivers, distinct from the big executor pool, reduces fragmentation.

### 10.9 Schedule heavy batch off-peak

Spot prices drop overnight in most regions. If a job doesn't need to finish by 9am, schedule it for 2am. Trivial change,
real savings.

### 10.10 Kill the zombies (see section 9)

If a non-trivial fraction of cluster time is idle Jupyter kernels, no amount of right-sizing fixes it. The culler is
doing more work than the savings plan.

---

## 11. Operator's checklist

### Weekly

- [ ] Skim the top 10 longest-running drivers and confirm they're meant to be alive.
- [ ] Check that each namespace is inside its quota (sustained ~100% usage means under-sized; sustained <30% means
  over-sized).
- [ ] Look at the spot interruption rate. > 5% causes job retries — consider a wider mix of instance types.

### Monthly

- [ ] Review per-team chargeback. Surface the top wasters privately.
- [ ] Re-check requested vs actual CPU/memory across recent jobs. Recommend tighter requests where the gap is large.
- [ ] Validate that the kernel-idle culler is actually firing — look for the cull events in the JupyterHub logs.
- [ ] Confirm the History Server is reachable and not silently broken.

### Quarterly

- [ ] EKS version. Plan the upgrade. Co-ordinate with teams.
- [ ] Karpenter / Spark Operator versions. Update.
- [ ] Re-evaluate the on-demand baseline. Re-buy savings plans if the floor has moved.

---

## 12. Glossary

**Application ID** — Spark's per-job identifier (e.g. `spark-abc123…`). Used in the UI, History Server, and event-log
filename.

**Cluster Autoscaler** — The older AWS node auto-scaler. Scales fixed node groups. Largely superseded by Karpenter.

**Control plane** — The Kubernetes brain. On EKS, AWS runs and patches it for you. Replaces YARN ResourceManager.

**Driver pod** — The Spark driver, running as a Kubernetes pod.

**Dynamic allocation** — Spark's ability to add and remove executors during a job based on workload.

**EKS** — Amazon Elastic Kubernetes Service. Managed Kubernetes.

**EMR Studio** — AWS's hosted Jupyter/notebook environment for EMR.

**Executor pod** — A Spark executor, running as a Kubernetes pod.

**IRSA** — IAM Roles for Service Accounts. Maps Kubernetes service accounts to IAM roles so pods can use AWS APIs
without baked-in credentials.

**Karpenter** — Modern, fast node auto-scaler. Replaces fixed node groups with on-demand instance selection.

**Kubelet** — The agent on each worker node that talks to the control plane.

**Namespace** — A logical partition of a Kubernetes cluster. The standard unit of multi-tenancy.

**Node pool / NodePool** — A group of worker nodes with similar properties (instance type, on-demand vs spot, GPU vs
CPU).

**Pod** — A group of one or more containers scheduled together. For Spark, one pod = one driver or one executor.

**ResourceQuota** — A namespace-level cap on total CPU, memory, GPU, pod count.

**Spark History Server** — A web UI that replays finished Spark jobs from event logs stored in S3.

**SparkApplication** — A Kubernetes custom resource that describes a Spark job declaratively.

**Spot instance** — Discounted EC2 capacity that can be interrupted with 2 minutes' notice. Cheap; use for restartable
workloads (executors).

**Taints and tolerations** — A mechanism to keep certain pods on certain nodes (e.g. only GPU pods on GPU nodes).

**Virtual cluster** — An EMR-on-EKS handle that points at a Kubernetes namespace. Modellers see "virtual clusters"; the
platform sees namespaces.

**YARN** — Hadoop's resource manager. **Not used in EMR on EKS.**

---

## 13. Useful kubectl commands

```bash
# Who is running what right now in team-a
kubectl get pods -n team-a

# Watch a job's pods change state
kubectl get pods -n team-a -w

# Stream logs from a specific driver
kubectl logs -n team-a spark-abc123-driver -f

# Describe a stuck pod (events at the bottom are usually the answer)
kubectl describe pod -n team-a spark-abc123-driver

# Cluster-wide: which nodes are running, how full
kubectl top nodes
kubectl top pods -A --sort-by=cpu

# Find the longest-running drivers anywhere
kubectl get pods -A -l spark-role=driver \
  --sort-by=.metadata.creationTimestamp

# Forcefully end a runaway job (last resort)
kubectl delete pod -n team-a spark-abc123-driver

# Check a namespace's current resource quota usage
kubectl describe resourcequota -n team-a

# What did the scheduler do? (recent events)
kubectl get events -n team-a --sort-by=.lastTimestamp

# EMR-on-EKS: cancel a job run by ID
aws emr-containers cancel-job-run \
  --virtual-cluster-id <vc-id> \
  --id <job-run-id>
```

---

*If you take only three things from this handbook, take these:*

1. **Kubernetes replaces YARN.** No master node, no core/task nodes. Control plane (managed) + worker nodes running
   pods.
2. **One cluster, many namespaces.** Quotas, IRSA, and node selectors are how teams coexist safely.
3. **Idle sessions are the #1 waste.** Dynamic allocation + kernel-idle-culler + job TTL, layered, are the fix. Tooling
   alone does it; you don't have to chase modellers.
