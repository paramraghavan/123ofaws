# AWS DataSync for NAS to S3 Migration

## What is AWS DataSync?

AWS DataSync is a data transfer service that simplifies, automates, and accelerates moving data between on-premises storage systems and AWS storage services (S3, EFS, FSx). It's designed for large-scale data transfers with minimal manual intervention.

### Key Characteristics
- **Automated transfers**: Scheduled or on-demand data movement
- **Built-in validation**: Automatic data integrity checks
- **Bandwidth throttling**: Control network impact
- **Incremental transfers**: Only copies changed files (when configured)
- **Agent-based**: Runs on edge nodes in your infrastructure
- **Multi-threading**: Optimized for performance
- **Transparent encryption**: In-transit encryption support

## Your Use Case: Brownfield NAS to S3

### Current Setup
- **Source**: NAS mounted at `/mydata/prod/icm/datain/poolData/`
- **Path structure**: `datatype/yyyy/mmdd/fileofinterest`
- **Access pattern**: Daily reads from today's date (or backdated)
- **Migration driver**: Brownfield server retirement
- **Infrastructure**: Edge nodes per environment with appropriate IAM roles

### Key Requirements
1. Copy only files from specific dates (typically today or requested dates)
2. Respect path structure: `datatype/yyyy/mmdd/`
3. Selective file copying (not full folder backups)
4. Recurring daily execution
5. Handle backdated runs on demand
6. Minimal disruption to existing jobs

---

## AWS DataSync Options for Selective File Copying

### Option 1: Full DataSync Agent → Task with Exclude Filters
**How it works**: DataSync agent on edge node copies from NAS to S3, using exclude patterns

**Pros**:
- Native DataSync validation and optimization
- Built-in bandwidth throttling
- CloudWatch integration for monitoring
- Automatic retry logic

**Cons**:
- Less granular control over date selection
- Exclude patterns are static (not dynamic based on current date)
- Requires creating multiple tasks for different date patterns
- Overkill for selective daily files

**Use case**: When you need to exclude permanent paths but still copy large portions

---

### Option 2: DataSync Agent + Custom Lambda Orchestrator (RECOMMENDED)
**How it works**:
- Lambda function determines files to copy (based on date logic)
- Lambda creates/updates DataSync task with dynamic prefix filters
- DataSync agent copies only those prefixes to S3
- Lambda monitors task completion and handles retries

**Pros**:
- Dynamic date-based filtering
- Simple logic for "today's date" or backdated scenarios
- Cost-effective (pay for actual transfers)
- Easy to modify filtering logic
- Integrates with CloudWatch and SNS
- Can implement parallel tasks for different datatypes

**Cons**:
- Requires Lambda coding
- Slightly more complex orchestration
- Need to manage task state

**Use case**: Perfect for your brownfield scenario - selective daily copies with date logic

---

### Option 3: Custom Python Script + AWS CLI + Agent
**How it works**:
- Python script runs on edge node (cron job)
- Script identifies files matching date criteria
- Uses AWS CLI to sync files to S3 using S3 sync with filters
- Does NOT use DataSync task framework

**Pros**:
- Full control over file selection
- Simple implementation
- No additional Lambda costs
- Easy debugging on edge node

**Cons**:
- Manual file validation (DataSync does this automatically)
- No bandwidth optimization
- Manual retry logic needed
- Less managed service benefits

**Use case**: Simple, lightweight solution when DataSync overhead isn't justified

---

### Option 4: DataSync Task with Source Filter Only (DatesBased)
**How it works**: DataSync native filtering on modification dates

**Pros**:
- Fully managed DataSync solution
- Native date-based filtering
- Built-in validation and optimization

**Cons**:
- Limited control over path structure
- Can't easily specify "today's date" - static date ranges only
- Reconfiguring tasks for new dates is cumbersome

---

## RECOMMENDED APPROACH: Option 2

**Why Option 2?**
1. **Best balance**: Managed DataSync + Custom logic for date selection
2. **Scalable**: Easy to add multiple datatypes/paths
3. **Maintainable**: Python/Lambda code is simple and clear
4. **Cost-efficient**: Only pays for actual data transferred
5. **Operational**: Automatic retry, validation, monitoring
6. **Future-proof**: Easy to enhance with additional filters

---

## Architecture Design

```
┌─────────────────┐
│   NAS Storage   │
│  /mydata/prod/  │
│  icm/datain/    │
│   poolData/     │
└────────┬────────┘
         │
         │ (NFS mount)
         │
┌────────▼──────────────────┐
│   Edge Node (EC2/On-Prem)  │
│   - DataSync Agent         │
│   - IAM Service Role       │
└────────┬───────────────────┘
         │
         │ (Agent registration)
         │
┌────────▼──────────────────────┐
│   AWS DataSync               │
│   - Task scheduler           │
│   - File transfer engine     │
│   - Validation               │
└────────┬──────────────────────┘
         │
         │ (Copy files)
         │
┌────────▼──────────────────┐
│   S3 Bucket               │
│   - Destination location  │
│   - Versioning enabled    │
└───────────────────────────┘

ORCHESTRATION:
┌──────────────────────────────────┐
│   Lambda Function (Daily Cron)   │
│   1. Determine date to copy      │
│   2. Build source path filters   │
│   3. Create/Update DataSync task │
│   4. Start task                  │
│   5. Monitor completion          │
│   6. Send notifications          │
└──────────────────────────────────┘
```

---

## Implementation Steps

1. **Setup DataSync Agent** on edge node
2. **Configure IAM roles** for agent and Lambda
3. **Create S3 bucket** with appropriate lifecycle policies
4. **Build Lambda orchestrator** (Python)
5. **Deploy Python handler** for date logic
6. **Set up CloudWatch** for monitoring
7. **Test** with backdated scenarios

---

## Key Implementation Details

### Path Logic for "Today"
```
Source: /mydata/prod/icm/datain/poolData/
Today (2024-08-04): datatype/2024/0804/fileofinterest
Backdated: datatype/2024/0721/fileofinterest

DataSync can copy: /mydata/prod/icm/datain/poolData/datatype/2024/0804/
To S3: s3://your-bucket/poolData/datatype/2024/0804/
```

### Dynamic Task Configuration
- Lambda calculates date format (YYYY/MMDD)
- Creates TaskDefinition with source location filter
- Handles multiple datatypes in parallel
- Monitors task and retries on failure

### Cost Optimization
- DataSync pricing: Pay per GB transferred
- No charges for task creation/scheduling
- S3: Standard storage + any lifecycle policies
- Lambda: Minimal execution cost (runs once daily)

