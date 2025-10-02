# EMR Cluster - Recreate & Clone Guide

## Scenario 1: Recreate a Terminated EMR Cluster

### Using the Failover Manager (Automated)

**Prerequisites:**
- The cluster must have been logged before termination (exists in `logs/status.jsonl`)
- OR the cluster is still in terminated state (viewable in EMR console for ~2 months)

**Method 1: If cluster was logged before termination**

```python
from failover import AWSFailoverManager
import json

manager = AWSFailoverManager()

# Read the last known configuration from logs
with open('logs/status.jsonl', 'r') as f:
    logs = [json.loads(line) for line in f.readlines()]

# Find the terminated cluster in logs
terminated_cluster_id = 'j-XXXXXXXXXXXXX'
cluster_config = None

for log in reversed(logs):  # Start from most recent
    for cluster in log.get('emr_clusters', []):
        if cluster['cluster_id'] == terminated_cluster_id:
            cluster_config = cluster
            break
    if cluster_config:
        break

if cluster_config:
    print(f"Found cluster config: {cluster_config}")
    # Note: You'll need to manually recreate or use AWS console
    # The failover manager's recreate_emr_cluster requires the cluster to still exist
else:
    print("Cluster configuration not found in logs")
```

**Method 2: If cluster still exists in AWS (terminated state)**

```python
from failover import AWSFailoverManager

manager = AWSFailoverManager()
terminated_cluster_id = 'j-XXXXXXXXXXXXX'

# This will work if cluster is in TERMINATED/TERMINATING state
new_cluster_id = manager.recreate_emr_cluster(terminated_cluster_id)

if new_cluster_id:
    print(f"New cluster created: {new_cluster_id}")
else:
    print("Failed to recreate cluster")
```

### Manual Recreation (AWS Console)

1. **Open AWS EMR Console**
   - Go to https://console.aws.amazon.com/emr/

2. **Find Terminated Cluster**
   - Click on "Clusters" in the left sidebar
   - Change filter to "Terminated" or "All states"
   - Click on your terminated cluster ID

3. **Clone Configuration**
   - Click "Clone" button at the top
   - This creates a new cluster with the same configuration
   - Modify the name if desired
   - Review all settings

4. **Launch**
   - Click "Create cluster"
   - Note the new cluster ID

### Manual Recreation (AWS CLI)

```bash
# Get terminated cluster configuration
aws emr describe-cluster --cluster-id j-XXXXXXXXXXXXX --region us-east-1 > cluster-config.json

# Extract key configuration details and create new cluster
aws emr create-cluster \
  --name "Recreated-Cluster-Name" \
  --release-label emr-6.10.0 \
  --applications Name=Spark Name=Hadoop \
  --instance-type m5.xlarge \
  --instance-count 3 \
  --use-default-roles \
  --region us-east-1
```

---

## Scenario 2: Clone an Existing (Running) EMR Cluster

### Using the Failover Manager (Automated)

**Method 1: Clone without terminating the original**

```python
from failover import AWSFailoverManager
import boto3
import json
from datetime import datetime

manager = AWSFailoverManager()
source_cluster_id = 'j-XXXXXXXXXXXXX'
new_cluster_name = 'Cloned-Cluster-2025'

# Get the source cluster configuration
try:
    cluster_detail = manager.emr_client.describe_cluster(ClusterId=source_cluster_id)['Cluster']
    
    # Get instance groups (Master, Core, Task)
    instance_groups_response = manager.emr_client.list_instance_groups(ClusterId=source_cluster_id)
    instance_groups = instance_groups_response.get('InstanceGroups', [])
    
    # Build instance groups configuration
    new_instance_groups = []
    for ig in instance_groups:
        instance_group_config = {
            'Name': ig['Name'],
            'InstanceRole': ig['InstanceGroupType'],
            'InstanceType': ig['InstanceType'],
            'InstanceCount': ig['RequestedInstanceCount'],
            'Market': ig['Market']  # ON_DEMAND or SPOT
        }
        
        # Add spot configuration if applicable
        if ig['Market'] == 'SPOT' and 'BidPrice' in ig:
            instance_group_config['BidPrice'] = ig['BidPrice']
        
        # Add EBS configuration if present
        if 'EbsBlockDevices' in ig and ig['EbsBlockDevices']:
            ebs_config = {'EbsBlockDeviceConfigs': []}
            for ebs in ig['EbsBlockDevices']:
                volume_spec = ebs['VolumeSpecification']
                ebs_config['EbsBlockDeviceConfigs'].append({
                    'VolumeSpecification': {
                        'VolumeType': volume_spec['VolumeType'],
                        'SizeInGB': volume_spec['SizeInGB']
                    },
                    'VolumesPerInstance': 1
                })
            instance_group_config['EbsConfiguration'] = ebs_config
        
        new_instance_groups.append(instance_group_config)
    
    # Build complete cluster configuration
    new_cluster_config = {
        'Name': new_cluster_name,
        'ReleaseLabel': cluster_detail['ReleaseLabel'],
        'Instances': {
            'InstanceGroups': new_instance_groups,
            'KeepJobFlowAliveWhenNoSteps': True,
            'TerminationProtected': False,
        },
        'Applications': [{'Name': app['Name']} for app in cluster_detail.get('Applications', [])],
        'VisibleToAllUsers': cluster_detail.get('VisibleToAllUsers', True),
        'JobFlowRole': cluster_detail['Ec2InstanceAttributes']['IamInstanceProfile'].split('/')[-1],
        'ServiceRole': cluster_detail['ServiceRole']
    }
    
    # Add EC2 attributes if present
    if 'Ec2InstanceAttributes' in cluster_detail:
        ec2_attrs = cluster_detail['Ec2InstanceAttributes']
        instances_config = new_cluster_config['Instances']
        
        if 'Ec2KeyName' in ec2_attrs:
            instances_config['Ec2KeyName'] = ec2_attrs['Ec2KeyName']
        if 'Ec2SubnetId' in ec2_attrs:
            instances_config['Ec2SubnetId'] = ec2_attrs['Ec2SubnetId']
        if 'EmrManagedMasterSecurityGroup' in ec2_attrs:
            instances_config['EmrManagedMasterSecurityGroup'] = ec2_attrs['EmrManagedMasterSecurityGroup']
        if 'EmrManagedSlaveSecurityGroup' in ec2_attrs:
            instances_config['EmrManagedSlaveSecurityGroup'] = ec2_attrs['EmrManagedSlaveSecurityGroup']
    
    # Add configurations if present
    if 'Configurations' in cluster_detail:
        new_cluster_config['Configurations'] = cluster_detail['Configurations']
    
    # Add tags if present
    if 'Tags' in cluster_detail:
        new_cluster_config['Tags'] = cluster_detail['Tags']
    
    # Create the new cluster
    response = manager.emr_client.run_job_flow(**new_cluster_config)
    new_cluster_id = response['JobFlowId']
    
    print(f"✅ Successfully cloned cluster!")
    print(f"   Source: {source_cluster_id}")
    print(f"   New Cluster: {new_cluster_id}")
    print(f"   Name: {new_cluster_name}")
    
    # Log the configuration
    for ig in new_instance_groups:
        print(f"   {ig['InstanceRole']}: {ig['InstanceType']} x{ig['InstanceCount']} ({ig['Market']})")
    
except Exception as e:
    print(f"❌ Error cloning cluster: {str(e)}")
    import traceback
    traceback.print_exc()
```

**Method 2: Using the built-in recreate (terminates original)**

```python
from failover import AWSFailoverManager

manager = AWSFailoverManager()
source_cluster_id = 'j-XXXXXXXXXXXXX'

# WARNING: This will TERMINATE the original cluster
new_cluster_id = manager.recreate_emr_cluster(source_cluster_id)

print(f"Original cluster terminated: {source_cluster_id}")
print(f"New cluster created: {new_cluster_id}")
```

### Manual Cloning (AWS Console)

1. **Open AWS EMR Console**
   - Go to https://console.aws.amazon.com/emr/

2. **Select Source Cluster**
   - Click on "Clusters"
   - Find and click on the cluster you want to clone

3. **Clone**
   - Click the "Clone" button at the top right
   - This opens the "Create Cluster" page with all settings pre-filled

4. **Modify Settings**
   - **Change the cluster name** (required)
   - Optionally modify:
     - Number of instances
     - Instance types
     - Applications
     - Tags
     - Any other settings

5. **Create**
   - Click "Create cluster"
   - Both clusters will run simultaneously (original + clone)

### Manual Cloning (AWS CLI)

```bash
# Step 1: Get source cluster configuration
SOURCE_CLUSTER="j-XXXXXXXXXXXXX"
aws emr describe-cluster --cluster-id $SOURCE_CLUSTER > source-cluster.json

# Step 2: Extract and create clone with new name
aws emr create-cluster \
  --name "Cloned-Production-Cluster" \
  --release-label emr-6.10.0 \
  --applications Name=Spark Name=Hadoop Name=Hive \
  --instance-groups \
    InstanceGroupType=MASTER,InstanceType=m5.xlarge,InstanceCount=1 \
    InstanceGroupType=CORE,InstanceType=m5.2xlarge,InstanceCount=4,Market=SPOT,BidPrice=0.50 \
    InstanceGroupType=TASK,InstanceType=c5.4xlarge,InstanceCount=10,Market=SPOT,BidPrice=0.80 \
  --ec2-attributes KeyName=my-key,SubnetId=subnet-xxxxx \
  --use-default-roles \
  --region us-east-1 \
  --configurations file://cluster-configs.json
```

---

## Key Differences: Recreate vs Clone

| Operation | Original Cluster | New Cluster | Use Case |
|-----------|------------------|-------------|----------|
| **Recreate** | Terminated | Created with identical config | Recover from failure |
| **Clone** | Remains running | Created as duplicate | Testing, scaling, DR |

---

## Best Practices

### Before Recreating/Cloning

1. **Document Configuration**
   ```python
   # Save cluster details
   manager = AWSFailoverManager()
   clusters = manager.detect_emr_clusters()
   
   # Log before termination
   status = manager.log_status(
       instances=[], 
       clusters=clusters,
       rds_instances=[],
       lambda_functions=[],
       ecs_services=[],
       elasticache_clusters=[],
       auto_scaling_groups=[]
   )
   ```

2. **Backup Important Data**
   - Ensure HDFS data is backed up to S3
   - Save Hive metastore
   - Export any database content

3. **Test Clone First**
   - Clone to test environment
   - Verify all applications work
   - Test with sample data

### After Recreating/Cloning

1. **Verify Cluster Health**
   ```python
   import time
   
   # Wait for cluster to be ready
   new_cluster_id = 'j-NEWCLUSTERID'
   
   waiter = manager.emr_client.get_waiter('cluster_running')
   print("Waiting for cluster to start...")
   waiter.wait(ClusterId=new_cluster_id)
   
   # Check status
   cluster = manager.emr_client.describe_cluster(ClusterId=new_cluster_id)
   print(f"Cluster status: {cluster['Cluster']['Status']['State']}")
   ```

2. **Verify Applications**
   ```bash
   # SSH to master node
   ssh -i mykey.pem hadoop@master-public-dns
   
   # Check Spark
   spark-submit --version
   
   # Check Hadoop
   hadoop version
   
   # Check HDFS
   hdfs dfsadmin -report
   ```

3. **Update DNS/Endpoints**
   - Update application connection strings
   - Modify security group rules if needed
   - Update monitoring/alerting

---

## Automated Clone Script

Create a reusable script `clone_emr.py`:

```python
#!/usr/bin/env python3
import sys
from failover import AWSFailoverManager

def clone_emr_cluster(source_cluster_id, new_name):
    """Clone an EMR cluster with a new name"""
    manager = AWSFailoverManager()
    
    print(f"Cloning cluster: {source_cluster_id}")
    print(f"New name: {new_name}")
    
    # Get source configuration
    cluster_detail = manager.emr_client.describe_cluster(
        ClusterId=source_cluster_id
    )['Cluster']
    
    # Check if source is running
    state = cluster_detail['Status']['State']
    if state not in ['RUNNING', 'WAITING']:
        print(f"Warning: Source cluster is in state: {state}")
        return None
    
    # Use recreate logic but modify name
    # (Implementation same as Method 1 above)
    # ... 
    
    return new_cluster_id

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clone_emr.py <source-cluster-id> <new-name>")
        sys.exit(1)
    
    source = sys.argv[1]
    name = sys.argv[2]
    
    new_id = clone_emr_cluster(source, name)
    print(f"New cluster created: {new_id}")
```

**Usage:**
```bash
python clone_emr.py j-XXXXXXXXXXXXX "Production-Clone-2025"
```

---

## Troubleshooting

### Issue: "Cluster not found"
**Solution:** Cluster may have been deleted from AWS (after ~2 months). Use log files or recreate manually.

### Issue: "Insufficient capacity"
**Solution:** 
- Try different instance types
- Use different availability zones
- Reduce initial instance count

### Issue: "Invalid IAM role"
**Solution:** Ensure IAM roles still exist:
```bash
aws iam get-role --role-name EMR_EC2_DefaultRole
aws iam get-role --role-name EMR_DefaultRole
```

### Issue: "Security group not found"
**Solution:** Recreate security groups or use default EMR security groups

---

## Summary

**Quick Commands:**

```python
# Recreate terminated cluster (if still in AWS)
manager.recreate_emr_cluster('j-TERMINATED-CLUSTER')

# Clone running cluster (keeps original running)
# Use Method 1 code above with custom name

# Restart cluster (terminates and recreates)
manager.restart_emr_cluster('j-RUNNING-CLUSTER')
```

**Best Approach:**
1. For production: Always **clone first**, test, then switch
2. For development: **Recreate** is fine
3. For disaster recovery: Keep logs and use **recreate from logs**