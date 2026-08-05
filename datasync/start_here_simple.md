# START HERE - Simple DataSync Solution

## Your Goal
Copy files from on-premises NFS to AWS S3

## That's It. Here's How.

---

## 3 Simple Steps

### Step 1: Install DataSync Agent on EC2 (30 min)

Get a small EC2 instance (t3.micro is fine), SSH in, and run:

```bash
cd /opt
sudo wget https://s3.amazonaws.com/aws-datasync/latest/aws-datasync-agent-linux.tar.gz
sudo tar xzf aws-datasync-agent-linux.tar.gz
cd aws-datasync-agent
sudo ./install.sh
sudo systemctl start aws-datasync-agent

# Mount your NFS
sudo mount -t nfs YOUR_NAS_IP:/vol/data /mnt/nfs
```

Done! Agent is ready.

### Step 2: Tell AWS About Your Locations (10 min)

```bash
# Tell AWS where your NFS is
aws datasync create-location-nfs \
  --subdirectory /mnt/nfs \
  --server-hostname 10.0.0.50 \
  --on-prem-config AgentArns=arn:aws:datasync:us-east-1:YOUR_ACCOUNT:agent/YOUR_AGENT_ID

# Copy the ARN from output → Save as NFS_ARN

# Tell AWS where to store files (S3)
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::my-bucket \
  --s3-config BucketAccessRoleArn=arn:aws:iam::YOUR_ACCOUNT:role/datasync-s3-role

# Copy the ARN from output → Save as S3_ARN
```

### Step 3: Copy Files (10 min)

**Quick Manual Copy:**

```python
import boto3

datasync = boto3.client('datasync')

# Edit these with your ARNs from Step 2
NFS_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/nfs/abc123'
S3_ARN = 'arn:aws:datasync:us-east-1:123456789012:location/s3/xyz789'

# Create task
task = datasync.create_task(
    SourceLocationArn=NFS_ARN,
    DestinationLocationArn=S3_ARN,
    Name='Copy-Now'
)

# Start copy
execution = datasync.start_task_execution(TaskArn=task['TaskArn'])
print("Copying... check AWS console")
```

Save this as `copy.py`, edit the ARNs, then:

```bash
pip install boto3
python copy.py
```

**Done!** Your files are being copied to S3.

---

## Want Daily Automatic Copy?

Edit `lambda_daily_copy.py`, add your ARNs, then follow DEPLOYMENT.md

That's it. Takes 10 minutes.

---

## More Info

- **Architecture diagram**: ARCHITECTURE.md
- **Complete guide**: SIMPLE_GUIDE.md
- **Deployment steps**: DEPLOYMENT.md
- **Just want details?**: README.md

---

## Quick Checklist

- [ ] EC2 instance with DataSync Agent running
- [ ] NFS mounted to /mnt/nfs on the EC2
- [ ] DataSync locations created (NFS and S3)
- [ ] ARNs saved
- [ ] Script edited with your ARNs
- [ ] Script runs successfully
- [ ] Files appear in S3

✓ Done! You have a working solution.

---

## Architecture (Simple Version)

```
NAS (Your Files)
      ↓
EC2 (DataSync Agent)
      ↓
AWS DataSync Service
      ↓
S3 Bucket (Files Stored)
```

That's literally it.

---

## Cost

- DataSync: $0.0125 per GB transferred
- S3: $0.023 per GB per month (storage)
- EC2: ~$5-10/month (small instance)

**Total for 100GB**: ~$1.25 transfer + $2.30 storage + ~$7 EC2 = ~$10/month

---

## Questions?

**"Does it copy all files?"**
Yes, by default. Only new files on subsequent runs.

**"What if the copy fails?"**
DataSync retries automatically. Safe and reliable.

**"Can I schedule it daily?"**
Yes, use Lambda + EventBridge (5 minutes to set up).

**"How do I monitor it?"**
CloudWatch logs + AWS console shows progress.

---

## Let's Go!

1. **Follow Step 1-3 above**
2. **Check S3 for your files**
3. **Done!**

Questions? Read SIMPLE_GUIDE.md or ARCHITECTURE.md

Happy copying! 🚀
