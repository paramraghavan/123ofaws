# Step-by-Step Guide: Calculate EMR vs EMR Serverless Job Costs in AWS Cost Explorer

## Prerequisites

1. **Access to AWS Console** with appropriate permissions
2. **Cost Explorer enabled** in your AWS account (may take 24 hours after first enabling)
3. **Job details** ready:
    - EMR Cluster: Cluster ID and job execution timeframe
    - EMR Serverless: Application ID and job run timeframe

---

## Part 1: Calculate EMR Cluster Job Cost

### Step 1: Access Cost Explorer

1. Log into AWS Console
2. Navigate to **Billing and Cost Management**
3. Click **Cost Explorer** in the left sidebar
4. Click **Launch Cost Explorer** (if first time)

### Step 2: Set Up Basic Filters

1. Click **Create report** or modify existing report
2. Set **Date range** to cover your job execution period
    - Use **Custom** date range
    - Set start date to job start date (or slightly before)
    - Set end date to job end date (or slightly after)
3. Set **Granularity** to **Daily** for detailed breakdown

### Step 3: Filter by EMR Service

1. In **Filters** section, click **Add filter**
2. Select **Service** from dropdown
3. Check **Amazon Elastic MapReduce**
4. Click **Apply**

### Step 4: Add Resource-Level Filtering

1. Click **Add filter** again
2. Select **Resource** from dropdown
3. Enter your **Cluster ID** (format: `j-XXXXXXXXXXXXX`)
4. Click **Apply**

### Step 5: Group by Relevant Dimensions

1. In **Group by** section, select:
    - **Service** (already selected)
    - **Usage Type** (to see compute vs storage costs)
    - **Resource** (to isolate your cluster)

### Step 6: Analyze Results

1. Review the **chart** for daily cost breakdown during job period
2. Check **table below** for detailed cost by usage type:
    - Look for compute instances (EC2-Instance, EMR-Instance)
    - Storage costs (EBS volumes)
    - Data transfer costs
3. **Export data** if needed (CSV/PDF options available)

---

## Part 2: Calculate EMR Serverless Job Cost

### Step 1: Access Cost Explorer (Same as Part 1)

1. Navigate to **Billing and Cost Management** → **Cost Explorer**

### Step 2: Set Up Date Range

1. Set **Date range** to your job run period
    - EMR Serverless jobs typically run for shorter periods
    - Be precise with start/end times if job was short-running
2. Set **Granularity** to **Hourly** or **Daily** depending on job duration

### Step 3: Filter by EMR Serverless Service

1. In **Filters** section, click **Add filter**
2. Select **Service** from dropdown
3. Check **EMR Serverless** (not "Amazon Elastic MapReduce")
4. Click **Apply**

### Step 4: Filter by Application ID

1. Click **Add filter**
2. Select **Resource** from dropdown
3. Enter your **Application ID** (format: `00f1r2p0123456789`)
4. Click **Apply**

### Step 5: Group by Usage Type

1. In **Group by** section, select:
    - **Service**
    - **Usage Type** (shows vCPU, memory, storage separately)
    - **Resource** (your application ID)

### Step 6: Analyze Serverless Results

1. Review costs broken down by:
    - **vCPU usage** (compute costs)
    - **Memory usage** (memory costs)
    - **Storage usage** (if applicable)
2. Note the **pay-per-use** pricing model differences

---

## Part 3: Advanced Filtering and Comparison

### For More Precise Job-Level Filtering

#### EMR Cluster Jobs:

1. **Add Tag filters** if you tagged your job steps
2. **Use Usage Type Groups** to categorize costs:
    - `EmrApplications` - Application costs
    - `EmrComputingNodes` - Node costs
    - `EmrStorage` - Storage costs

#### EMR Serverless Jobs:

1. **Filter by time range** more precisely (job runs are typically shorter)
2. **Use Resource Tags** if application is tagged
3. **Look for specific usage types**:
    - `ServerlessVCPU-Hours`
    - `ServerlessMemory-GB-Hours`
    - `ServerlessStorage-GB-Hours`

### Creating Cost Comparison Reports

#### Option 1: Side-by-Side Analysis

1. Create **two separate reports**:
    - Report 1: EMR Cluster job (specific time period)
    - Report 2: EMR Serverless job (specific time period)
2. Compare total costs and usage patterns

#### Option 2: Combined Report (if both services used)

1. Filter by **both services**: "Amazon Elastic MapReduce" AND "EMR Serverless"
2. Group by **Service** to see side-by-side comparison
3. Add **Resource** grouping to see specific clusters/applications

---

## Part 4: Key Metrics to Track

### EMR Cluster Job Costs

- **Instance costs**: EC2 compute charges
- **EBS storage**: Attached storage volumes
- **Data transfer**: Network costs
- **EMR service charges**: Platform fees
- **Duration**: Cluster uptime (even if job finished early)

### EMR Serverless Job Costs

- **vCPU-hours**: Actual compute usage
- **Memory GB-hours**: Memory consumption
- **Storage costs**: Temporary storage usage
- **Job execution time**: Pay only for actual job runtime

### Cost Comparison Factors

1. **Job duration** vs **cluster uptime**
2. **Resource utilization**:
    - EMR Cluster: May have idle time
    - EMR Serverless: Pay only for actual usage
3. **Startup costs**:
    - EMR Cluster: Cluster bootstrap time
    - EMR Serverless: Minimal cold start
4. **Minimum charges**:
    - EMR Cluster: Minimum 1-minute billing
    - EMR Serverless: Per-second billing

---

## Part 5: Export and Analysis

### Exporting Data

1. Click **Download CSV** for detailed data
2. Select **Download PDF** for executive summary
3. Use **API** for programmatic access (if needed)

### Analysis Tips

1. **Normalize by job completion time**
2. **Factor in resource utilization**
3. **Consider scaling requirements**
4. **Account for operational overhead**

### Sample Calculation Framework

```
EMR Cluster Job Cost Calculation:
- Cluster runtime: X hours
- Instance costs: $Y/hour × X hours
- Storage costs: $Z × storage GB × hours
- EMR platform fee: $W × instance hours
- Total: Instance + Storage + Platform + Data Transfer

EMR Serverless Job Cost Calculation:
- Job runtime: X hours (actual execution only)
- vCPU costs: $Y × vCPU × actual hours
- Memory costs: $Z × GB × actual hours  
- Storage costs: $W × GB × hours (if used)
- Total: vCPU + Memory + Storage
```

---

## Part 6: Troubleshooting Common Issues

### Data Not Showing

- **Wait 24 hours**: Cost data has delay
- **Check permissions**: Ensure Cost Explorer access
- **Verify date range**: Expand range if unsure of exact timing
- **Check service names**: Ensure correct service selection

### Incomplete Cost Attribution

- **Missing Resource IDs**: Some costs may not have resource tags
- **Shared resources**: EBS volumes, security groups may show separately
- **Network costs**: Data transfer might appear under different service

### Accurate Job Timing

- **Check CloudTrail**: For exact job start/stop times
- **Use EMR Console**: Job history shows precise timing
- **Monitor logs**: Application logs show actual processing time