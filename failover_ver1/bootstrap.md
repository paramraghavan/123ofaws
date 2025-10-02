# Add Bootstrap Actions

Bootstrap actions are **NOT automatically copied** because they're stored separately from the main cluster
configuration. This means:

- ❌ Cloned cluster starts without your custom bootstrap scripts
- ❌ Any software installations, configurations, or customizations from bootstrap actions are missing
- ✅ Everything else (instances, applications, security groups) IS copied

## ✅ Fixed Version - Now Including Bootstrap ActionsPerfect! I've **fixed the issue
** - bootstrap actions are now automatically copied. Here's what happens:

## ✅ Bootstrap Actions Now Included

### What Gets Copied:

- ✅ **Script paths** (S3 bucket locations)
- ✅ **Script arguments** (all parameters)
- ✅ **Script names**
- ✅ **Execution order** (runs in same sequence)

### Example Log Output:

```
INFO - Cloning config - Release: emr-6.10.0
INFO -   MASTER: m5.xlarge (1 instances, ON_DEMAND)
INFO -   CORE: r5.2xlarge (4 instances, SPOT)
INFO -   Bootstrap Actions: 3 found
INFO -     - Install Python Packages: s3://my-bucket/scripts/install-packages.sh
INFO -     - Configure Spark: s3://my-bucket/scripts/spark-config.sh
INFO -     - Setup Monitoring: s3://my-bucket/scripts/monitoring.sh
INFO - Cloned cluster created: j-NEWCLUSTER123
INFO -   Bootstrap Actions: 3 copied
```

## 📋 What Bootstrap Actions Typically Do

Common use cases that are now preserved:

- Install custom Python/R packages
- Configure application settings (Spark, Hadoop, Hive)
- Mount external file systems (EFS, NFS)
- Install monitoring agents (CloudWatch, DataDog)
- Set environment variables
- Download additional libraries or data

## 🔍 How to View Bootstrap Actions

### Check what will be copied:

```python
manager = AWSFailoverManager()

# List bootstrap actions from source cluster
bootstrap_actions = manager.emr_client.list_bootstrap_actions(
    ClusterId='j-XXXXXXXXXXXXX'
)

for ba in bootstrap_actions['BootstrapActions']:
    print(f"Name: {ba['Name']}")
    print(f"Script: {ba['ScriptPath']}")
    print(f"Args: {ba.get('Args', [])}")
    print("---")
```

### Verify after cloning:

```python
# Clone the cluster
new_cluster_id = manager.clone_emr_cluster(
    'j-SOURCE123',
    'Production-Clone'
)

# Check bootstrap actions on new cluster
new_bootstrap = manager.emr_client.list_bootstrap_actions(
    ClusterId=new_cluster_id
)

print(f"Copied {len(new_bootstrap['BootstrapActions'])} bootstrap actions")
```

## ⚠️ Important Notes

1. **S3 Access Required**: The cloned cluster must have access to the same S3 buckets where bootstrap scripts are stored
2. **IAM Permissions**: Ensure the EMR service role has `s3:GetObject` permissions for bootstrap script locations
3. **Script Availability**: Scripts must still exist in S3 - if deleted, bootstrap will fail
4. **Execution Time**: Bootstrap actions run during cluster startup, adding 5-15 minutes to launch time

## 🎯 What's Now Copied in Clone/Recreate

| Component             | Copied? | Notes                           |
|-----------------------|---------|---------------------------------|
| Instance types        | ✅       | Master, Core, Task              |
| Spot/On-Demand        | ✅       | Including bid prices            |
| EBS volumes           | ✅       | Type, size, count               |
| Applications          | ✅       | Spark, Hadoop, Hive, etc.       |
| Security groups       | ✅       | All SG configurations           |
| IAM roles             | ✅       | Service and instance roles      |
| Tags                  | ✅       | Plus clone metadata             |
| Configurations        | ✅       | All Hadoop/Spark configs        |
| **Bootstrap Actions** | ✅       | **Now included!**               |
| Auto Scaling          | ✅       | If configured                   |
| Steps                 | ❌       | Not copied (one-time execution) |

Bootstrap actions are now fully preserved during clone and recreate operations! 🎉