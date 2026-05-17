Two patterns. Each is small enough to paste at the top of any notebook, and the usage is obvious. Share both — the first
is the one modelers will use daily, the second they only need when a notebook gets slow.

**Pattern 1 — Save your work so it survives anything**

```python
# Paste at top of notebook. Change the bucket once.
import getpass

PARK = f"s3://my-bucket/emr-parking/{getpass.getuser()}"


def save(df, name):
    """Persist a DataFrame to S3 so it survives idle, restarts, weekends."""
    path = f"{PARK}/{name}"
    df.write.mode("overwrite").parquet(path)
    return spark.read.parquet(path)


def load(name):
    """Read it back tomorrow (or in another notebook)."""
    return spark.read.parquet(f"{PARK}/{name}")
```

How to use it:

```python
# Anywhere you would have written .cache(), write save(...) instead:
features = save(raw.transform(clean).transform(engineer), "features_v3")
labels = save(df.join(other, "id"), "labels_v2")

# First cells of Monday's notebook — just reload:
features = load("features_v3")
labels = load("labels_v2")
```

Tell them: **if it took more than a minute to compute, `save()` it.** That single rule covers 90% of cases.

---

**Pattern 2 — Speed up long iterative pipelines**

For notebooks doing many chained transforms or a loop with 50+ iterations, the Spark planner starts dragging because
it's tracking every step in the lineage. One-time setup, then a one-liner inside the loop:

```python
# Run once at the top of the notebook.
spark.sparkContext.setCheckpointDir("s3://my-bucket/emr-checkpoints/")

# In any long loop or chain:
for i in range(100):
    df = df.transform(some_step)
    if i % 10 == 9:
        df = df.checkpoint(eager=True)  # writes to S3, resets the lineage
```

Tell them: **only reach for this if a notebook is mysteriously slow despite small data.** Usually that means lineage
bloat, and `checkpoint()` fixes it.

---

**One-line summary for the team**

> Use `save("name")` instead of `.cache()` for anything you want to keep. Use `checkpoint()` only if your notebook gets
> slow on small data.