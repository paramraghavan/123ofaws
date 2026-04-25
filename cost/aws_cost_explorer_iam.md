Here are the exact IAM permissions for each method, broken out separately with who needs what.---

## Key differences to know

**CUR v2 + Athena** requires two separate roles — an admin to enable CUR and set up Glue, and an analyst role that is
purely read-only. The admin setup is a one-time action. Everything the analyst needs after that is non-destructive.

**S3 Storage Lens + Pricing API** is lighter. The Pricing API requires zero IAM setup for HTTP calls, and Storage Lens
read access is simpler than the full Athena stack. The tradeoff is that you're computing an estimate, not reading actual
billed amounts.

**For your view-only scenario**, ask your admin for:

| What to ask for                                              | Method it unlocks              |
|--------------------------------------------------------------|--------------------------------|
| Read access to the CUR S3 export bucket + Athena permissions | CUR v2 + Athena                |
| `s3:GetStorageLensConfiguration` + export bucket read        | Storage Lens method            |
| `s3:GetBucketTagging` + `s3:ListAllMyBuckets`                | Both methods (tag attribution) |
