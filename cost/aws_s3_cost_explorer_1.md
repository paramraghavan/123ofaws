This guide breaks down how each method works for **Tag-based chargeback**, what you need to request, and how they handle
specific S3 cost components (PUT, GET, Storage, etc.).

---

## **1. High-Level Overview of Options**

### **A. CUR v2 + Athena (The "Gold Standard")**

* **How it works:** AWS exports a massive "line-item" file (CUR 2.0) to an S3 bucket. You use **Amazon Athena** to run
  SQL queries against this file.
* **Admin Setup:** An Admin must create the "Data Export" in the Billing console. They must also **activate Cost
  Allocation Tags** (e.g., `Project`, `Owner`) in the Billing dashboard so they appear in the report.
* **Permissions Needed:** * `s3:GetObject` on the billing bucket.
    * `athena:*` to run queries.
    * `glue:*` (if using Glue Crawlers to catalog the data).

### **B. S3 Storage Lens + Pricing API**

* **How it works:** Storage Lens provides advanced usage metrics (e.g., "This tag has 5TB of data"). You then call the *
  *AWS Pricing API** to find the current price per GB and multiply the two in a script/spreadsheet.
* **Admin Setup:** Admin must enable **Storage Lens Advanced Metrics** (paid) for the account/organization.
* **Permissions Needed:** * `s3:GetStorageLensConfiguration` and `s3:GetStorageLensDashboard`.
    * `pricing:GetProducts` (for the Pricing API).

### **C. Cost Explorer Export**

* **How it works:** A point-and-click UI where you filter by "Service: S3" and "Tag: Project." You then export the
  resulting CSV.
* **Admin Setup:** Admin must **Activate Cost Allocation Tags**.
* **Permissions Needed:** `ce:GetCostAndUsage`.

### **D. CloudWatch Metrics**

* **How it works:** CloudWatch tracks `BucketSizeBytes`. However, CloudWatch **does not natively support S3 tags.** * *
  *Limitation:** You can only calculate by **Bucket Name**, not by Tag, unless you have a 1-bucket-per-tag architecture.

---

## **2. Cost Calculation Details by Component**

When calculating for **All Buckets by Tag**, here is how costs are handled:

| Cost Component                 | CUR v2 + Athena                                                | S3 Storage Lens                                                 | Cost Explorer                                                  |
|:-------------------------------|:---------------------------------------------------------------|:----------------------------------------------------------------|:---------------------------------------------------------------|
| **Storage (Standard/Glacier)** | **Direct.** Shows exact $amount per storage class per tag.     | **Usage Only.** Shows GBs; you must multiply by Price API.      | **Direct.** Aggregate$ amount shown in UI.                     |
| **PUT/GET/LIST Requests**      | **Granular.** Lists every request type and its cost.           | **Activity Metrics.** Shows request counts, not direct $ costs. | **Bundled.** Usually grouped as "Requests" in the S3 category. |
| **Data Transfer (Out)**        | **Included.** Tracks bytes transferred out per resource.       | **Not Included.** Focuses on storage, not transit.              | **Included.** Visible under "Data Transfer" filters.           |
| **Delete Requests**            | **$0.** (Deletion is free, but check for early deletion fees). | **Visible.** Tracks delete object counts.                       | **N/A.** Usually not a line item since it's free.              |
| **Glacier Restore**            | **Detailed.** Shows retrieval fees and per-GB restore costs.   | **Partial.** Shows retrieval counts/volumes.                    | **Included.** Listed under S3 service costs.                   |

---

## **3. The "Tagging" Requirement (Crucial)**

For **any** of these to work (except CloudWatch), the Admin **must** perform a specific step:

1. **Tag the Buckets:** Ensure every bucket has a tag like `CostCenter: 123`.
2. **Activate in Billing Console:** * Navigate to **Billing and Cost Management** -> **Cost Allocation Tags**.
    * Search for your tag (e.g., `CostCenter`).
    * Click **Activate**.
    * *Note: It takes up to 24 hours for tags to start appearing in your cost data after activation.*

---

## **4. Final Recommendation**

* **If you need 100% accuracy (including transfer/API calls):** Use **CUR v2 + Athena**. It is the only way to see
  exactly what you are being billed for every single bucket tag.
* **If you need a quick summary for a meeting:** Use **Cost Explorer Export**. It's fast and requires the least
  technical setup (SQL).
* **If you need to optimize storage classes:** Use **S3 Storage Lens**. It tells you *why* a tag is expensive (e.g., "
  This tag has 2PB of non-current versions").