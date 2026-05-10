# Cross-Account & Cross-Region Access - Summary

## What Was Added

Comprehensive hands-on examples for multi-account, multi-region AWS data architectures.

### Main Study Guide Additions

**Practice Area 7: Cross-Account & Cross-Region Access** includes:

#### Part 1: Cross-Account S3 Access
- **Scenario**: Dev account (111...) reads from Prod account (222...)
- **Key Components**:
  - S3 bucket policy with cross-account principal
  - KMS key policy allowing decrypt from dev account
  - AssumeRole policy with ExternalId
  - Python code using STS to assume role and access S3

#### Part 2: Cross-Region S3 Replication
- **Scenario**: Data in us-east-1 replicated to us-west-2 and eu-west-1
- **Features**:
  - S3 Replication Configuration with RTC (15-minute replication)
  - Multi-region replica buckets
  - Automatic delete marker replication
  - Cross-region failover patterns

#### Part 3: Cross-Account Cross-Region Data Access
- **Scenario**: Analytics team in us-west-2 reads replicated data from Prod in eu-west-1
- **Architecture**:
  - Primary bucket in Prod (us-east-1)
  - Replicas in multiple regions
  - Analytics account accesses cross-region data
  - Python code for Athena queries across regions

#### Part 4: Interview Q&A
- Designing safe cross-account access (dev→prod)
- Disaster recovery with multi-region replication
- "Confused Deputy" problem prevention

---

## Real-World Scenario Covered

```
Organization Structure:
├── Dev Account (111111111111)
│   └── EMR clusters, Dev pipelines
├── Prod Account (222222222222)
│   ├── S3 Data Lake (us-east-1)
│   ├── S3 Replicas (us-west-2, eu-west-1)
│   └── Production pipelines
└── Analytics Account (333333333333)
    └── Analysts using Athena, Lambda
```

---

## Key Concepts Explained

### 1. Cross-Account Access Pattern
```
Permission Flow:
Dev EMR → AssumeRole → Prod Role → S3 Bucket
         (with ExternalId)
```

### 2. Confused Deputy Prevention
- **Problem**: Attacker tricks you into assuming wrong role
- **Solution**: Require ExternalId (secret) in condition
- **Example**: 
  ```json
  "Condition": {
    "StringEquals": {
      "sts:ExternalId": "unique-secret-xyz"
    }
  }
  ```

### 3. Cross-Region Replication
- **RTC (Replication Time Control)**: Data replicated within 15 minutes
- **Consistency**: Eventual consistency, apps must handle
- **Cost**: Use Intelligent-Tiering on replicas to save money

---

## Code Patterns Included

### Terraform Patterns
- [ ] Cross-account S3 bucket policy
- [ ] KMS key policy for cross-account access
- [ ] AssumeRole IAM policy
- [ ] S3 Replication Configuration
- [ ] Replica bucket creation

### Python Patterns
- [ ] STS AssumeRole with ExternalId
- [ ] Create cross-account S3 client
- [ ] List cross-account S3 bucket
- [ ] Athena queries on cross-region data
- [ ] Credential management

### IAM Patterns
- [ ] Least privilege cross-account policy
- [ ] KMS decrypt permission across accounts
- [ ] External ID validation
- [ ] Service-to-service assume role
- [ ] Condition-based access control

---

## Interview Questions This Covers

**Scenario-Based:**
1. "Design access for dev to read prod data safely"
2. "How do you replicate data across regions for DR?"
3. "What's the confused deputy problem?"
4. "How would you organize a multi-account AWS setup?"

**Technical Deep-Dives:**
1. "Explain cross-account IAM role trust relationships"
2. "What are conditions in IAM policies?"
3. "How does S3 replication handle deletions?"
4. "Design a data architecture for 3 AWS accounts"

**Hands-On:**
1. Write Terraform for cross-account S3 access
2. Write Python to assume cross-account role
3. Configure S3 replication in terraform
4. Design Glue job that reads cross-account S3

---

## When You'd Use This Knowledge

- **Multi-account organizations** (separate dev/staging/prod)
- **Enterprise data lakes** (compliance requires data isolation)
- **Global companies** (data replication across regions)
- **Federated analytics** (teams access data across accounts)
- **Disaster recovery** (backup in different region)

---

## Your Competitive Advantage

You can now explain:
- ✅ Why multi-account architecture is better than single account
- ✅ How to secure cross-account access (least privilege)
- ✅ Compliance benefits of account separation
- ✅ Cost optimization with cross-region storage tiers
- ✅ Disaster recovery strategies

At senior level interviews, this shows you've handled:
- Large-scale, multi-team organizations
- Compliance and security requirements
- Global data distribution
- Complex permission models

---

## Files Updated

1. **AWS_Interview_Study_Guide.md**
   - Added Practice Area 7 (1500+ lines)
   - Complete architecture diagrams (text format)
   - Terraform code (production-ready)
   - Python examples (real implementations)
   - Interview Q&A with detailed answers

2. **AWS_Quick_Reference.md**
   - Cross-account S3 quick patterns
   - Cross-region replication snippets
   - IAM policy examples
   - Confused deputy prevention
   - Interview tips

---

## Next Steps

1. **Read Practice Area 7** in AWS_Interview_Study_Guide.md
2. **Try the Terraform examples** (modify account IDs and regions)
3. **Run the Python code** locally to test cross-account access
4. **Practice explaining** scenarios from "Interview Q&A" section
5. **Draw the architecture** for multi-account setup

---

## Quick Command Reference

**Deploy cross-region replication:**
```bash
terraform apply
# Enables S3 replication to 2 regions automatically
```

**Test cross-account access:**
```python
python3 -c "
import boto3
sts = boto3.client('sts')
role = sts.assume_role(
    RoleArn='arn:aws:iam::222222222222:role/prod-data-access',
    RoleSessionName='test',
    ExternalId='your-secret-id'
)
print('Success: Cross-account role assumed')
"
```

**Verify S3 replication status:**
```bash
aws s3api get-bucket-replication \
  --bucket prod-datalake-primary \
  --region us-east-1
```

---

**Created**: May 2024  
**Last Updated**: May 2024  
**Status**: Ready for Interview Use
