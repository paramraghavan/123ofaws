These are both admin-level setup steps. Here's exactly what to do for each.

---

## Step 1 — Create the Storage Lens dashboard with daily export

This is done once in the AWS Console. You need S3 admin access or the permissions from the earlier checker (`s3:PutStorageLensConfiguration`).

**In the AWS Console:**

1. Go to **S3 → Storage Lens → Dashboards → Create dashboard**
2. Fill in the form:

| Field | What to set |
|---|---|
| Dashboard name | `platform-chargeback` (or any name — this becomes `lens_config_id` in CONFIG) |
| Home region | `us-east-1` (or your primary region) |
| Scope | **This account** (or org-wide if you have multi-account) |
| Metrics | Select **Advanced metrics** — you need storage class breakdown |
| Export | **Enable daily export** → see step below |

3. Under **Metrics export**, set:
   - Output format: **CSV**
   - Destination bucket: the bucket you'll read exports from (create it first if needed)
   - Destination prefix: `storage-lens/` (this becomes `lens_export_prefix` in CONFIG)
   - Encryption: SSE-S3 is fine for most setups

4. Click **Create dashboard**

AWS starts exporting within 48 hours. The first export lands the next UTC day.

---

## Step 2 — Create the export destination bucket

If you don't already have a bucket for exports, create one before step 1:

```bash
# Create the bucket
aws s3api create-bucket \
  --bucket your-lens-export-bucket \
  --region us-east-1

# Block all public access (required)
aws s3api put-public-access-block \
  --bucket your-lens-export-bucket \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,\
     BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

Then attach this bucket policy so the Storage Lens service can write to it. AWS requires this — without it the export silently fails:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowStorageLensExport",
      "Effect": "Allow",
      "Principal": {
        "Service": "storage-lens.s3.amazonaws.com"
      },
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-lens-export-bucket/storage-lens/*",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "YOUR-ACCOUNT-ID",
          "s3:x-amz-acl": "bucket-owner-full-control"
        }
      }
    }
  ]
}
```

Save that as `lens-bucket-policy.json` and apply it:

```bash
aws s3api put-bucket-policy \
  --bucket your-lens-export-bucket \
  --policy file://lens-bucket-policy.json
```

---

## Step 3 — Update CONFIG to match

Once the dashboard is created and the first export has landed, plug the values into `s3_chargeback_common.py`:

```python
CONFIG = {
    ...
    "lens_export_bucket": "your-lens-export-bucket",   # bucket name from step 2
    "lens_export_prefix": "storage-lens/",             # prefix you set in the export config
    "lens_config_id":     "platform-chargeback",       # dashboard name from step 1
    ...
}
```

---

## Step 4 — Verify the export landed

After 24–48 hours, check that files are appearing:

```bash
aws s3 ls s3://your-lens-export-bucket/storage-lens/ --recursive | head -20
```

You should see paths like:

```
storage-lens/your-account-id/platform-chargeback/V_1/reports/dt=2026-01-02/
  ├── manifest.json
  └── platform-chargeback-00001.csv
```

If the folder is empty after 48 hours, the most common cause is the bucket policy in step 2 is missing or has the wrong account ID. Re-check the `aws:SourceAccount` condition.

---

## What to ask your AWS admin

If you don't have the permissions to do this yourself, send them this:

> I need a Storage Lens dashboard set up with these settings:
> - Dashboard name: `platform-chargeback`
> - Scope: this account (account ID: `XXXX`)
> - Metrics: Advanced (storage class breakdown required)
> - Daily CSV export to bucket `your-lens-export-bucket` under prefix `storage-lens/`
> - Bucket policy granting `storage-lens.s3.amazonaws.com` `s3:PutObject` on that prefix
>
> I need read access (`s3:GetObject`, `s3:ListBucket`) on `your-lens-export-bucket`.

Once done, run the permission checker to confirm your role can read the exports:

```bash
python check_permissions.py --method lens
```