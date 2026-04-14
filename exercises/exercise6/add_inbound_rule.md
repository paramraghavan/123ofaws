# Add inbound rule for port 4040- 4060 for emr cluster from subnet 10.28.0.0 using aws cli.

To add an inbound rule for an Amazon EMR cluster using the AWS CLI, you need to target the **Master Security Group**
associated with your cluster.

Since security group rules utilize `from-port` and `to-port` parameters, you can cover the entire 4040–4060 range in a
single command.

### Step 1: Identify your Security Group ID

If you don't already have the Security Group ID (`sg-xxxxxxxx`), you can find it by providing your EMR Cluster ID:

```bash
aws emr describe-cluster --cluster-id j-XXXXXXXXXXXXX \
--query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup' \
--output text
```

---

### Step 2: Add the Inbound Rule

Run the following command, replacing `sg-your-id-here` with the ID retrieved in Step 1.

```bash
aws ec2 authorize-security-group-ingress \
    --group-id sg-your-id-here \
    --protocol tcp \
    --port 4040-4060 \
    --cidr 10.28.0.0/16
```

> **Note on CIDR:** Ensure your subnet notation is complete (e.g., `10.28.0.0/16` or `10.28.0.0/24`). The AWS CLI
> requires the full CIDR block format.

---

### Alternative: Using JSON Syntax (for complex rules)

If you prefer the structured `ip-permissions` format (which is helpful if you want to add a description to the rule),
use this:

```bash
aws ec2 authorize-security-group-ingress \
    --group-id sg-your-id-here \
    --ip-permissions '[
        {
            "IpProtocol": "tcp",
            "FromPort": 4040,
            "ToPort": 4060,
            "IpRanges": [{"CidrIp": "10.28.0.0/16", "Description": "EMR Subnet Access"}]
        }
    ]'
```

### Verification

To confirm the rule was added successfully, you can describe the security group:

```bash
aws ec2 describe-security-groups --group-ids sg-your-id-here
```

> **Security Warning:** Opening a range of 20 ports is generally safe within a private VPC subnet, but always ensure that
only the necessary services (like Spark UI or custom applications) are listening on those ports to maintain a "least
privilege" security posture.


## Find The **Security Group ID**
The **Security Group ID** handy, you can extract it directly from the EMR cluster's metadata using
the `describe-cluster` command.

EMR clusters typically have two managed security groups: one for the **Master** node and one for the **Slave** (
Core/Task) nodes. Usually, UI ports like 4040–4060 are opened on the **Master** node.

### 1. Get the Master Security Group ID

Run this command to pull the ID specifically for the Master node:

```bash
aws emr describe-cluster --cluster-id j-XXXXXXXXXXXXX \
--query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup' \
--output text
```

### 2. Get All Security Groups (Master and Slave)

If you aren't sure which one you need, or if you want to see both, use this command:

```bash
aws emr describe-cluster --cluster-id j-XXXXXXXXXXXXX \
--query 'Cluster.Ec2InstanceAttributes.[EmrManagedMasterSecurityGroup, EmrManagedSlaveSecurityGroup]' \
--output table
```

---

### 3. The "All-in-One" Command

If you want to find the ID and add the rule in **one single step** (without copy-pasting the ID), you can use a variable
in your shell (Linux/macOS/WSL):

```bash
# Store the ID in a variable
SG_ID=$(aws emr describe-cluster --cluster-id j-XXXXXXXXXXXXX --query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup' --output text)

# Use the variable to add the rule
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 4040-4060 \
    --cidr 10.28.0.0/16
```

### Troubleshooting Tip:

If the command returns `None` or an error:

* **Check your Region:** If your cluster is in `us-west-2` but your CLI is set to `us-east-1`, it won't find the
  cluster. Add `--region us-west-2` to the command.
* **Check Permissions:** Ensure your IAM user has `elasticmapreduce:DescribeCluster` permissions.