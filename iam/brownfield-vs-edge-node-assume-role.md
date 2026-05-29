# Brownfield vs Edge Node: Assuming Roles Guide

> **AWS IAM role assumption on brownfield servers vs AWS edge nodes**: Complete guide covering practical implementation, best practices, and decision matrices for different deployment scenarios.

---

## Table of Contents

1. [Quick Decision Matrix](#quick-decision-matrix)
2. [Brownfield Servers](#brownfield-servers)
3. [AWS Edge Nodes](#aws-edge-nodes)
4. [Practical Implementations](#practical-implementations)
5. [IAM Setup Required](#iam-setup-required)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

>  **how brownfield servers access AWS credentials**, **the credential lifecycle**, and **how edge nodes differ** - with practical examples and visual flows.

---

## Quick Decision Matrix

```
┌─────────────────────────────────────────────────────────────┐
│ WHERE AM I RUNNING?          │ APPROACH                    │
├──────────────────────────────┼─────────────────────────────┤
│ Brownfield (On-Prem)         │ → STS AssumeRole            │
│ Brownfield → Different Acct  │ → STS AssumeRole            │
│                              │                             │
│ Outpost (EC2-like)           │ → Service Role (auto)       │
│ Wavelength Zone              │ → Service Role (auto)       │
│ Local Zone                   │ → Service Role (auto)       │
│                              │                             │
│ Edge → Different Account     │ → Service Role + AssumeRole │
│ Edge → Same Account          │ → Service Role (only)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Credential Flow: How Brownfield Servers Access AWS

As a tutor, let me explain the complete credential lifecycle for brownfield servers:

### The Credential Journey

```
STEP 1: BOOTSTRAP CREDENTIALS
┌──────────────────────────────────────────┐
│ Brownfield Server (On-Premises)          │
│                                          │
│ Store long-term credentials:             │
│ - AWS Access Key ID                      │
│ - AWS Secret Access Key                  │
│                                          │
│ Storage location (secure):               │
│ • Secrets Manager (preferred)            │
│ • HashiCorp Vault                        │
│ • Environment variables (dev only)       │
│ • Encrypted config files                 │
│ • Parameter Store                        │
└──────────────────────────────────────────┘
         ↓ (First-time use)

STEP 2: OBTAIN TEMPORARY CREDENTIALS
┌──────────────────────────────────────────┐
│ STS AssumeRole Call                      │
│                                          │
│ POST to AWS STS service:                 │
│ {                                        │
│   "RoleArn": "arn:aws:iam::...",        │
│   "RoleSessionName": "brownfield-1",     │
│   "DurationSeconds": 3600                │
│ }                                        │
│                                          │
│ Auth: Long-term credentials              │
└──────────────────────────────────────────┘
         ↓ (Successful)

STEP 3: RECEIVE TEMPORARY CREDENTIALS
┌──────────────────────────────────────────┐
│ STS Response (valid 1 hour)              │
│                                          │
│ {                                        │
│   "AccessKeyId": "ASIA...",              │
│   "SecretAccessKey": "...",              │
│   "SessionToken": "AQoD...",             │
│   "Expiration": "2024-01-15T11:00:00Z"   │
│ }                                        │
│                                          │
│ Cache these for: 55 minutes (safety)     │
└──────────────────────────────────────────┘
         ↓ (Use credentials)

STEP 4: ACCESS AWS SERVICES
┌──────────────────────────────────────────┐
│ Using Temporary Credentials:             │
│                                          │
│ s3.put_object(Bucket, Key, Body)         │
│ dynamodb.get_item(TableName, Key)        │
│ lambda.invoke(FunctionName, Payload)     │
│                                          │
│ AWS verifies: Access Key + Secret + Token│
│ Duration: Until 11:00 UTC                │
└──────────────────────────────────────────┘
         ↓ (55 minutes later)

STEP 5: REFRESH (Before Expiration)
┌──────────────────────────────────────────┐
│ Before credentials expire (5 min buffer) │
│                                          │
│ 1. Retrieve long-term credentials again  │
│ 2. Call STS AssumeRole again             │
│ 3. Get new temporary credentials         │
│ 4. Update session in client              │
│                                          │
│ Seamless to application                  │
└──────────────────────────────────────────┘
         ↓ (Continue operations)

STEP 6: REPEAT
│ Every 55 minutes: Refresh credentials
│ Every 90 days: Rotate long-term keys
```

### Credential Storage Options

```
OPTION 1: AWS Secrets Manager (RECOMMENDED)
┌────────────────────────────────────┐
│ Brownfield Server                  │
│                                    │
│ At runtime:                        │
│ 1. Query Secrets Manager API       │
│ 2. Provide IAM role (if on AWS)    │
│    OR access key/secret            │
│ 3. Receive encrypted credentials   │
│ 4. Use credentials to assume role  │
│                                    │
│ Pros:                              │
│ ✅ Automatic rotation support      │
│ ✅ Encryption at rest              │
│ ✅ Audit trail                     │
│ ✅ No local file storage           │
│ ✅ Access control via IAM          │
│                                    │
│ Cons:                              │
│ ❌ Requires network call           │
│ ❌ Adds latency                    │
│ ❌ External dependency             │
└────────────────────────────────────┘

OPTION 2: HashiCorp Vault
┌────────────────────────────────────┐
│ Brownfield Server                  │
│                                    │
│ At runtime:                        │
│ 1. Query Vault API                 │
│ 2. Authenticate (AppRole, JWT)     │
│ 3. Receive credentials             │
│ 4. Use to assume role              │
│                                    │
│ Pros:                              │
│ ✅ Multi-cloud support             │
│ ✅ Self-hosted option              │
│ ✅ Strong audit logging            │
│ ✅ Dynamic secrets support         │
│                                    │
│ Cons:                              │
│ ❌ Another service to manage       │
│ ❌ Operational overhead            │
│ ❌ Network dependency              │
└────────────────────────────────────┘

OPTION 3: Environment Variables (DEV ONLY)
┌────────────────────────────────────┐
│ Brownfield Server                  │
│                                    │
│ At server startup:                 │
│ export AWS_ACCESS_KEY_ID=...       │
│ export AWS_SECRET_ACCESS_KEY=...   │
│                                    │
│ At runtime:                        │
│ credentials = os.environ[...]      │
│                                    │
│ Pros:                              │
│ ✅ Simple                          │
│ ✅ No external dependency          │
│                                    │
│ Cons:                              │
│ ❌ INSECURE (visible in ps)        │
│ ❌ No encryption                   │
│ ❌ Hard to rotate                  │
│ ❌ Only for development!           │
└────────────────────────────────────┘

OPTION 4: Encrypted Configuration File
┌────────────────────────────────────┐
│ Brownfield Server                  │
│                                    │
│ File: /etc/aws/credentials.enc     │
│ Encrypted with: AES-256            │
│                                    │
│ At runtime:                        │
│ 1. Read encrypted file             │
│ 2. Decrypt with local key          │
│ 3. Extract credentials             │
│ 4. Use for assume role             │
│                                    │
│ Pros:                              │
│ ✅ Faster than network calls       │
│ ✅ Self-contained                  │
│ ✅ No dependency on Secrets Mgr    │
│                                    │
│ Cons:                              │
│ ❌ Encryption key management       │
│ ❌ No automatic rotation           │
│ ❌ Vulnerable if file accessed     │
│ ❌ Manual credential updates       │
└────────────────────────────────────┘
```

### Credential Access Diagram: Brownfield vs Edge

```
BROWNFIELD SERVER (On-Premises)
─────────────────────────────────────────────────────

┌──────────────────────────────────┐
│ Brownfield Server                │
│ (On-Premises Data Center)        │
└──────────────────────────────────┘
         ↓
    NO AUTO CREDENTIALS
    ↓ (Must retrieve manually)

┌──────────────────────────────────┐
│ Option 1: Secrets Manager        │
│ (AWS cloud)                      │
│         ↓                         │
│    Query API                     │
│         ↓                         │
│ Returns: Long-term creds         │
└──────────────────────────────────┘
OR
┌──────────────────────────────────┐
│ Option 2: Vault                  │
│ (Self-hosted)                    │
│         ↓                         │
│    Query API                     │
│         ↓                         │
│ Returns: Long-term creds         │
└──────────────────────────────────┘
OR
┌──────────────────────────────────┐
│ Option 3: Config File            │
│ (Local encrypted)                │
│         ↓                         │
│    Read & decrypt                │
│         ↓                         │
│ Returns: Long-term creds         │
└──────────────────────────────────┘
         ↓↓↓
    Use long-term credentials
         ↓
    Call STS AssumeRole
         ↓
┌──────────────────────────────────┐
│ AWS STS Service                  │
│                                  │
│ Validates:                       │
│ ✓ Access Key ID matches          │
│ ✓ Secret Key signature valid     │
│ ✓ User has sts:AssumeRole        │
│ ✓ Role allows this user          │
│         ↓                         │
│ Returns: Temporary credentials   │
│ (Access Key + Secret + Token)    │
└──────────────────────────────────┘
         ↓
    Use temporary credentials
    (Valid 1 hour)
         ↓
    Access AWS resources (S3, DDB, etc)


EDGE NODE (Outpost/Wavelength/Local Zone)
─────────────────────────────────────────────────────

┌──────────────────────────────────┐
│ Edge Node                        │
│ (Outpost/Wavelength/Local Zone)  │
│                                  │
│ AWS AUTOMATICALLY ASSIGNS:       │
│ • Service Role                   │
│ • Instance Profile               │
│ • Credential Token (in metadata) │
└──────────────────────────────────┘
         ↓
    AUTO CREDENTIALS
    ↓ (No manual retrieval needed!)

┌──────────────────────────────────┐
│ EC2 Instance Metadata Service    │
│                                  │
│ localhost:169.254.169.254/...    │
│         ↓                         │
│ Provides:                        │
│ • Role name                      │
│ • Temporary credentials          │
│ • Auto-refreshes before expiry   │
│                                  │
│ boto3 auto-uses this!            │
└──────────────────────────────────┘
         ↓
    boto3 automatically:
    1. Gets credentials from metadata
    2. Signs requests with them
    3. Refreshes before expiry
         ↓
    Use AWS resources (S3, DDB, etc)
    NO CREDENTIAL CODE NEEDED!
```

### Key Difference: Credential Retrieval

```
BROWNFIELD: Developer must handle credentials
  ❌ Get from storage
  ❌ Parse credentials
  ❌ Create STS client
  ❌ Call AssumeRole
  ❌ Handle expiration
  ❌ Refresh before expiry
  ❌ Update clients with new creds

EDGE NODE: AWS handles it automatically
  ✅ AWS assigns role at launch
  ✅ Metadata service provides creds
  ✅ boto3 discovers automatically
  ✅ Creds auto-refresh
  ✅ No code needed!
```

---

# Brownfield Servers (On-Premises/Non-AWS)

## Overview

A **brownfield server** is an existing, non-AWS server (on-premises or hosted elsewhere) that needs to access AWS resources. These servers cannot use EC2 instance profiles or IAM roles automatically.

## Option 1: STS AssumeRole (Recommended)

You **DO need to assume a role** using long-term credentials:

```python
import boto3

# 1. Use long-term credentials (stored securely)
sts = boto3.client('sts')

# 2. Assume the role
response = sts.assume_role(
    RoleArn='arn:aws:iam::ACCOUNT:role/BrownfieldServerRole',
    RoleSessionName='brownfield-server-session',
    DurationSeconds=3600
)

# 3. Use temporary credentials
creds = response['Credentials']
s3 = boto3.client(
    's3',
    aws_access_key_id=creds['AccessKeyId'],
    aws_secret_access_key=creds['SecretAccessKey'],
    aws_session_token=creds['SessionToken']
)
```

### Why Assume a Role?

| Benefit | Details |
|---------|---------|
| **Short-lived credentials** | Max 1 hour (default), auto-expire |
| **Audit trail** | All calls logged in CloudTrail |
| **Instant revocation** | Can be revoked without key rotation |
| **Least privilege** | Separate roles for different purposes |
| **Security best practice** | Industry standard for cross-service access |

## Option 2: Long-Term Credentials (Not Recommended)

Only use as a fallback for legacy systems:

```python
# ❌ Less secure - keys don't expire
import os
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)
```

**Drawbacks:**
- ❌ Keys never expire
- ❌ Difficult to rotate
- ❌ Higher compromise risk
- ❌ Audit trail less clear
- ❌ Cannot be instantly revoked

---

## How Brownfield Servers Retrieve AWS Credentials

### Real-World Example: Credential Retrieval Flow

```python
import boto3
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BrownfieldCredentialManager:
    """
    Demonstrates how a brownfield server gets AWS credentials
    """

    def __init__(self, credential_storage_type='secrets_manager'):
        """
        credential_storage_type can be:
        - 'secrets_manager': Query AWS Secrets Manager
        - 'vault': Query HashiCorp Vault
        - 'env_vars': Use environment variables (dev only)
        - 'config_file': Read encrypted config file
        """
        self.storage_type = credential_storage_type
        self._cached_creds = None
        self._cache_expiry = None

    def retrieve_bootstrap_credentials(self):
        """
        STEP 1: Get the initial long-term credentials
        These are stored securely, NOT hardcoded
        """

        if self.storage_type == 'secrets_manager':
            return self._get_from_secrets_manager()
        elif self.storage_type == 'vault':
            return self._get_from_vault()
        elif self.storage_type == 'env_vars':
            return self._get_from_env_vars()
        elif self.storage_type == 'config_file':
            return self._get_from_config_file()
        else:
            raise ValueError(f"Unknown storage type: {self.storage_type}")

    def _get_from_secrets_manager(self):
        """
        Option 1: Retrieve credentials from AWS Secrets Manager
        """
        logger.info("Retrieving credentials from Secrets Manager...")

        try:
            secrets_client = boto3.client('secretsmanager')

            # Query Secrets Manager for brownfield credentials
            response = secrets_client.get_secret_value(
                SecretId='brownfield/aws-credentials'
            )

            secret = json.loads(response['SecretString'])

            logger.info("✓ Retrieved credentials from Secrets Manager")

            return {
                'access_key': secret['access_key_id'],
                'secret_key': secret['secret_access_key'],
                'source': 'secrets_manager'
            }

        except Exception as e:
            logger.error(f"Failed to retrieve from Secrets Manager: {e}")
            raise

    def _get_from_vault(self):
        """
        Option 2: Retrieve credentials from HashiCorp Vault
        """
        logger.info("Retrieving credentials from Vault...")

        import requests

        try:
            # 1. Authenticate to Vault
            vault_url = os.getenv('VAULT_ADDR', 'http://localhost:8200')

            auth_response = requests.post(
                f'{vault_url}/v1/auth/approle/login',
                json={
                    'role_id': os.getenv('VAULT_ROLE_ID'),
                    'secret_id': os.getenv('VAULT_SECRET_ID')
                }
            )

            vault_token = auth_response.json()['auth']['client_token']

            # 2. Query Vault for AWS credentials
            secret_response = requests.get(
                f'{vault_url}/v1/secret/data/brownfield/aws-credentials',
                headers={'X-Vault-Token': vault_token}
            )

            secret_data = secret_response.json()['data']['data']

            logger.info("✓ Retrieved credentials from Vault")

            return {
                'access_key': secret_data['access_key_id'],
                'secret_key': secret_data['secret_access_key'],
                'source': 'vault'
            }

        except Exception as e:
            logger.error(f"Failed to retrieve from Vault: {e}")
            raise

    def _get_from_env_vars(self):
        """
        Option 3: Retrieve credentials from environment variables
        ⚠️ DEVELOPMENT ONLY - INSECURE FOR PRODUCTION!
        """
        logger.warning("Using credentials from environment variables (DEV ONLY!)")

        return {
            'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'source': 'env_vars'
        }

    def _get_from_config_file(self):
        """
        Option 4: Retrieve credentials from encrypted config file
        """
        logger.info("Retrieving credentials from encrypted config file...")

        try:
            from cryptography.fernet import Fernet

            # Read encrypted file
            with open('/etc/aws/credentials.enc', 'rb') as f:
                encrypted_data = f.read()

            # Decrypt with key (stored separately, e.g., in Key Management Service)
            encryption_key = os.getenv('AWS_CREDS_KEY')
            cipher = Fernet(encryption_key)
            decrypted_data = cipher.decrypt(encrypted_data)

            creds = json.loads(decrypted_data.decode())

            logger.info("✓ Retrieved credentials from config file")

            return {
                'access_key': creds['access_key'],
                'secret_key': creds['secret_key'],
                'source': 'config_file'
            }

        except Exception as e:
            logger.error(f"Failed to retrieve from config file: {e}")
            raise

    def assume_role(self, role_arn, duration_seconds=3600):
        """
        STEP 2: Use bootstrap credentials to assume a role
        This gets temporary credentials
        """
        logger.info(f"Assuming role: {role_arn}...")

        # Check cache first (don't repeat AssumeRole within 5 min)
        if self._cached_creds and self._cache_expiry > datetime.utcnow():
            logger.info("Using cached temporary credentials")
            return self._cached_creds

        try:
            # Get bootstrap credentials
            bootstrap_creds = self.retrieve_bootstrap_credentials()

            # Create STS client with bootstrap credentials
            sts = boto3.client(
                'sts',
                aws_access_key_id=bootstrap_creds['access_key'],
                aws_secret_access_key=bootstrap_creds['secret_key']
            )

            # Call AssumeRole
            response = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName='brownfield-server-session',
                DurationSeconds=duration_seconds
            )

            # Extract temporary credentials
            creds = response['Credentials']

            temp_creds = {
                'access_key': creds['AccessKeyId'],
                'secret_key': creds['SecretAccessKey'],
                'session_token': creds['SessionToken'],
                'expiration': creds['Expiration']
            }

            # Cache for 55 minutes (5 min buffer before expiry)
            self._cached_creds = temp_creds
            self._cache_expiry = creds['Expiration'] - timedelta(minutes=5)

            logger.info(f"✓ Successfully assumed role, valid until {creds['Expiration']}")

            return temp_creds

        except Exception as e:
            logger.error(f"Failed to assume role: {e}")
            raise

    def get_s3_client(self, role_arn):
        """
        STEP 3: Use temporary credentials to create AWS clients
        """
        logger.info("Creating S3 client with temporary credentials...")

        # Get temporary credentials
        temp_creds = self.assume_role(role_arn)

        # Create S3 client with temporary credentials
        s3 = boto3.client(
            's3',
            aws_access_key_id=temp_creds['access_key'],
            aws_secret_access_key=temp_creds['secret_key'],
            aws_session_token=temp_creds['session_token']
        )

        logger.info("✓ S3 client created")

        return s3

    def upload_file(self, role_arn, local_path, bucket, s3_key):
        """
        STEP 4: Use the client to perform operations
        """
        logger.info(f"Uploading {local_path} to s3://{bucket}/{s3_key}")

        try:
            s3 = self.get_s3_client(role_arn)
            s3.upload_file(local_path, bucket, s3_key)

            logger.info(f"✓ Upload successful")

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise


# EXAMPLE USAGE on Brownfield Server
if __name__ == '__main__':
    # Initialize credential manager
    # Choose one based on your setup:
    manager = BrownfieldCredentialManager(credential_storage_type='secrets_manager')
    # OR
    # manager = BrownfieldCredentialManager(credential_storage_type='vault')
    # OR
    # manager = BrownfieldCredentialManager(credential_storage_type='config_file')

    try:
        # Upload file using AWS credentials
        manager.upload_file(
            role_arn='arn:aws:iam::123456789012:role/BrownfieldServerRole',
            local_path='/var/data/export.csv',
            bucket='my-data-bucket',
            s3_key='uploads/export.csv'
        )

        print("✓ Complete credential flow successful!")

    except Exception as e:
        print(f"✗ Error: {e}")
```

### Credential Flow Summary for Brownfield

```
┌─────────────────────────────────────────────────────────────┐
│ BROWNFIELD CREDENTIAL FLOW - STEP BY STEP                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. APPLICATION STARTS                                      │
│    ↓                                                        │
│    BrownfieldCredentialManager initialized                │
│                                                             │
│ 2. RETRIEVE BOOTSTRAP CREDENTIALS (Long-term)             │
│    ↓                                                        │
│    Query secure storage:                                  │
│    • AWS Secrets Manager API (recommended)                │
│    • HashiCorp Vault API                                  │
│    • Encrypted config file (decrypt locally)              │
│    • Environment variables (dev only)                     │
│    ↓                                                        │
│    Returns: AWS Access Key ID + Secret Access Key         │
│                                                             │
│ 3. CALL STS ASSUMEROLE                                   │
│    ↓                                                        │
│    POST to AWS STS service                                │
│    Auth with: Bootstrap credentials (Access Key + Secret) │
│    Action: sts:AssumeRole on target role                  │
│    ↓                                                        │
│    AWS validates:                                         │
│    • Bootstrap credentials are valid                      │
│    • User has sts:AssumeRole permission                   │
│    • Role allows this principal in trust policy           │
│    ↓                                                        │
│    Returns: Temporary credentials (Exp: 1 hour)           │
│                                                             │
│ 4. USE TEMPORARY CREDENTIALS                              │
│    ↓                                                        │
│    Create AWS clients with:                               │
│    • AccessKeyId (starts with ASIA)                       │
│    • SecretAccessKey                                      │
│    • SessionToken (CRITICAL - includes role info)         │
│    ↓                                                        │
│    Access AWS services (S3, DDB, Lambda, etc)             │
│    ↓                                                        │
│    All API calls logged with session token                │
│                                                             │
│ 5. CREDENTIAL EXPIRATION & REFRESH                        │
│    ↓                                                        │
│    Set cache expiry: 55 minutes (5 min buffer)            │
│    ↓                                                        │
│    When near expiry:                                      │
│    1. Check cache                                         │
│    2. If expired, re-fetch bootstrap credentials          │
│    3. Call STS AssumeRole again                           │
│    4. Get new temporary credentials                       │
│    5. Update boto3 clients                                │
│    ↓                                                        │
│    Seamless to application (users don't notice)           │
│                                                             │
│ 6. AUDIT & SECURITY                                       │
│    ↓                                                        │
│    CloudTrail logs:                                       │
│    • AssumeRole calls (who, when, success/failure)        │
│    • API calls using temporary credentials               │
│    • Session token included in all logs                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# AWS Edge Nodes

## What Are AWS Edge Nodes?

AWS edge nodes include:
- **AWS Outposts** - On-premises AWS compute/storage
- **Wavelength** - AWS infrastructure at 5G edges
- **Local Zones** - AWS closer to major cities
- **Snow devices** - Portable AWS computing

## Understanding AWS Edge Node Types

### AWS Outposts vs Wavelength vs Local Zones

```
┌─────────────────────────────────────────────────────────────────┐
│ EDGE NODE TYPE    │ LOCATION        │ LATENCY    │ USE CASE     │
├─────────────────────────────────────────────────────────────────┤
│ Outposts          │ On-Premises     │ <5ms       │ Hybrid cloud │
│                   │ (Your data ctr) │            │ On-prem w/   │
│                   │                 │            │ AWS features │
│                   │                 │            │              │
│ Wavelength        │ 5G Telco edges  │ <10ms      │ Real-time    │
│                   │ (Near end users)│            │ 5G apps      │
│                   │                 │            │ Gaming       │
│                   │                 │            │ Media        │
│                   │                 │            │              │
│ Local Zones       │ Major metro     │ 1-10ms     │ Ultra-low    │
│                   │ areas           │            │ latency      │
│                   │ (Cities)        │            │ trading,     │
│                   │                 │            │ media        │
│                   │                 │            │              │
│ Standard EC2      │ AWS Regions     │ 10-50ms    │ Most apps    │
│ (Region)          │ (Geo-spread)    │            │              │
└─────────────────────────────────────────────────────────────────┘
```

### Credential Behavior: Edge vs Region

```
ALL AWS-MANAGED EDGE NODES (Outposts, Wavelength, Local Zones)
USE THE SAME CREDENTIAL SYSTEM AS EC2:

Outpost Instance:
├─ EC2-like compute
├─ Automatic instance profile attachment
├─ Metadata service at 169.254.169.254
├─ boto3 auto-discovers credentials
└─ Same as regular EC2 ✓

Wavelength Instance:
├─ EC2 in 5G network
├─ Instance profile works same way
├─ Metadata service available
├─ boto3 auto-discovers
└─ Same as regular EC2 ✓

Local Zone Instance:
├─ EC2 in metro area
├─ Instance profile available
├─ Metadata service works
├─ boto3 auto-discovers
└─ Same as regular EC2 ✓
```

### Key Insight: Edge Nodes = EC2

```
When AWS manages the edge node (Outposts/Wavelength/Local Zone):
├─ NO MANUAL CREDENTIAL MANAGEMENT NEEDED
├─ Instance profile auto-assigned
├─ Metadata service provides temporary credentials
├─ boto3 auto-detects and refreshes
└─ Works EXACTLY like regular EC2

NOT like brownfield servers!
```

## Can You Use Service Roles? ✅ YES!

**If the edge node is AWS-managed** (Outposts, Wavelength, Local Zones):

```python
# Edge node automatically has IAM role attached
# No need to assume - just use it!

import boto3

# On the edge node, boto3 auto-detects the role
s3 = boto3.client('s3')  # Uses the attached service role
ec2 = boto3.client('ec2')  # Same role

# This works because edge nodes support EC2 instance profiles
bucket_list = s3.list_buckets()
```

## Service Role vs AssumeRole on Edge

| Scenario | Use Service Role? | Use AssumeRole? | Details |
|----------|------------------|-----------------|---------|
| **Edge node (EC2-like)** | ✅ YES | ❌ Optional | Auto-assigned by AWS |
| **Outposts with instance profiles** | ✅ YES | ❌ No need | Works like EC2 |
| **Edge node → different account** | ❌ NO | ✅ YES | Must assume target role |
| **Brownfield server** | ❌ NO | ✅ YES | No auto role available |
| **Lambda on edge** | ✅ YES | ❌ No need | Auto role from definition |

---

# Practical Implementations

## Scenario 1: Brownfield Server → AWS S3

**Use case**: On-premises data center uploading files to AWS S3

```python
from boto3 import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BrownfieldAWSAccess:
    """Secure AWS access from on-premises servers"""

    def __init__(self, access_key, secret_key, role_arn, duration=3600):
        """
        Initialize brownfield AWS access.

        Args:
            access_key: Long-term AWS access key (from IAM user)
            secret_key: Long-term AWS secret key
            role_arn: ARN of role to assume
            duration: Credential duration in seconds (900-3600)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.role_arn = role_arn
        self.duration = duration
        self._credentials_cache = {}

    def get_temporary_credentials(self):
        """Get temporary credentials via AssumeRole"""
        try:
            sts = Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            ).client('sts')

            response = sts.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName='brownfield-session',
                DurationSeconds=self.duration
            )

            creds = response['Credentials']
            logger.info(f"Successfully assumed role {self.role_arn}")

            return {
                'AccessKeyId': creds['AccessKeyId'],
                'SecretAccessKey': creds['SecretAccessKey'],
                'SessionToken': creds['SessionToken'],
                'Expiration': creds['Expiration']
            }

        except Exception as e:
            logger.error(f"Failed to assume role: {e}")
            raise

    def get_s3_client(self):
        """Get S3 client with temporary credentials"""
        creds = self.get_temporary_credentials()

        return Session(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        ).client('s3')

    def upload_file(self, local_path, bucket, s3_key):
        """Upload file from brownfield server to S3"""
        s3 = self.get_s3_client()

        try:
            s3.upload_file(local_path, bucket, s3_key)
            logger.info(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

# Usage on brownfield server
if __name__ == '__main__':
    accessor = BrownfieldAWSAccess(
        access_key='AKIAIOSFODNN7EXAMPLE',
        secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        role_arn='arn:aws:iam::123456789:role/BrownfieldAccess',
        duration=3600
    )

    # Upload file
    accessor.upload_file(
        local_path='/data/customers.csv',
        bucket='my-data-bucket',
        s3_key='incoming/customers.csv'
    )
```

## Scenario 2: AWS Outpost/Edge Node with Service Role

**Use case**: Edge node automatically accessing AWS services

```python
import boto3

# Edge node already has service role attached
# No credentials needed!

# This just works:
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')

# All use the attached service role automatically
bucket_list = s3.list_buckets()

# Process data in S3
s3.upload_file(
    'local_file.parquet',
    'bucket-name',
    'data/file.parquet'
)

# Query DynamoDB
response = dynamodb.get_item(
    TableName='edge-data',
    Key={'id': {'S': 'record-1'}}
)

# Invoke Lambda on edge
result = lambda_client.invoke(
    FunctionName='edge-processor',
    InvocationType='RequestResponse',
    Payload=b'{"data": "test"}'
)

print("All operations successful - service role handles credentials!")
```

## Scenario 3: Edge Node → Different AWS Account (AssumeRole)

**Use case**: Edge node in Account A accessing resources in Account B

```python
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class EdgeNodeCrossAccount:
    """Access other AWS accounts from edge node"""

    def __init__(self, target_account, role_name, region='us-east-1'):
        """
        Initialize cross-account access from edge node.

        Args:
            target_account: Target AWS account ID
            role_name: Role name in target account
            region: AWS region
        """
        self.target_account = target_account
        self.role_name = role_name
        self.region = region
        self.target_role_arn = f'arn:aws:iam::{target_account}:role/{role_name}'
        self._credentials_cache = {}
        self._cache_expiry = None

    def assume_role_in_target_account(self):
        """Assume role using edge node's service role"""
        try:
            sts = boto3.client('sts', region_name=self.region)

            response = sts.assume_role(
                RoleArn=self.target_role_arn,
                RoleSessionName='edge-to-target-account',
                DurationSeconds=3600
            )

            creds = response['Credentials']
            logger.info(f"Successfully assumed role in account {self.target_account}")

            return {
                'access_key': creds['AccessKeyId'],
                'secret_key': creds['SecretAccessKey'],
                'token': creds['SessionToken'],
                'expiration': creds['Expiration']
            }

        except ClientError as e:
            logger.error(f"Failed to assume role: {e}")
            raise

    def get_s3_client_in_target(self):
        """Get S3 client in target account"""
        creds = self.assume_role_in_target_account()

        return boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds['token']
        )

    def get_dynamodb_client_in_target(self):
        """Get DynamoDB client in target account"""
        creds = self.assume_role_in_target_account()

        return boto3.client(
            'dynamodb',
            region_name=self.region,
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds['token']
        )

    def get_generic_client(self, service_name):
        """Get any AWS service client in target account"""
        creds = self.assume_role_in_target_account()

        return boto3.client(
            service_name,
            region_name=self.region,
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            aws_session_token=creds['token']
        )

# Usage on edge node
if __name__ == '__main__':
    cross_account = EdgeNodeCrossAccount(
        target_account='999999999999',
        role_name='EdgeNodeTargetRole',
        region='us-east-1'
    )

    # Access S3 in target account
    s3_target = cross_account.get_s3_client_in_target()
    response = s3_target.list_objects_v2(
        Bucket='target-account-bucket'
    )
    print(f"Found {len(response.get('Contents', []))} objects in target bucket")

    # Access DynamoDB in target account
    ddb_target = cross_account.get_dynamodb_client_in_target()
    response = ddb_target.list_tables()
    print(f"Tables in target account: {response['TableNames']}")

    # Access any service
    lambda_target = cross_account.get_generic_client('lambda')
    response = lambda_target.list_functions()
    print(f"Functions in target account: {len(response['Functions'])}")
```

---

# IAM Setup Required

## For Brownfield Servers

### Step 1: Create IAM User with Long-Term Credentials

```bash
# Create user
aws iam create-user --user-name brownfield-server-user

# Create access key
aws iam create-access-key --user-name brownfield-server-user
```

### Step 2: Attach AssumeRole Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::123456789:role/BrownfieldServerRole"
        }
    ]
}
```

```bash
# Attach policy
aws iam put-user-policy \
    --user-name brownfield-server-user \
    --policy-name BrownfieldAssumeRole \
    --policy-document file://policy.json
```

### Step 3: Create Role for Brownfield Server

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789:user/brownfield-server-user"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

```bash
# Create role with trust policy
aws iam create-role \
    --role-name BrownfieldServerRole \
    --assume-role-policy-document file://trust-policy.json
```

### Step 4: Attach Permissions to Role

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        }
    ]
}
```

```bash
# Attach permissions
aws iam put-role-policy \
    --role-name BrownfieldServerRole \
    --policy-name S3Access \
    --policy-document file://permissions.json
```

## For AWS Edge Nodes

### Automatic Setup

**AWS handles this automatically!** When you:

1. Create an Outpost/Wavelength/Local Zone instance
2. AWS automatically assigns a service role
3. No manual setup needed - boto3 auto-detects it

### For Cross-Account Access from Edge

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::ACCOUNT-A:role/EdgeNodeServiceRole"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

Place this trust policy on the role in Account B that the edge node should access.

---

# Best Practices

## For Brownfield Servers

| Practice | Details |
|----------|---------|
| **Store credentials securely** | Use AWS Secrets Manager or HashiCorp Vault |
| **Rotate keys regularly** | Every 90 days minimum |
| **Use shortest duration** | Set DurationSeconds to minimum needed (default 1 hour) |
| **Enable CloudTrail** | Log all AssumeRole calls for audit |
| **Least privilege** | Only grant necessary permissions in role |
| **Session naming** | Use descriptive RoleSessionName for audit trail |
| **Encrypt credentials in transit** | Use TLS/HTTPS only |

### Credential Storage Example

```python
import boto3
import json

def get_credentials_from_secrets_manager(secret_name):
    """Retrieve brownfield credentials securely"""
    secrets = boto3.client('secretsmanager')

    response = secrets.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    return secret['access_key'], secret['secret_key']

# Usage
access_key, secret_key = get_credentials_from_secrets_manager(
    'brownfield/aws-credentials'
)

accessor = BrownfieldAWSAccess(
    access_key=access_key,
    secret_key=secret_key,
    role_arn='arn:aws:iam::123456789:role/BrownfieldServerRole'
)
```

## For AWS Edge Nodes

| Practice | Details |
|----------|---------|
| **Use service roles** | Never hardcode credentials on edge nodes |
| **Verify instance profile** | Confirm service role is attached on launch |
| **Monitor AssumeRole calls** | Log cross-account access in CloudTrail |
| **Use EC2 instance tags** | Tag edge nodes for tracking and policies |
| **Implement least privilege** | Separate roles for different edge node types |
| **Test on launch** | Verify role works immediately after startup |

## For Both

| Practice | Details |
|----------|---------|
| **Enable CloudTrail** | Log all AssumeRole calls: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole` |
| **Set up alarms** | CloudWatch alarms on failed AssumeRole attempts |
| **Document role purposes** | Add descriptions to all roles |
| **Use resource tags** | Tag all roles with environment, team, purpose |
| **Regularly audit** | Review who can assume which roles quarterly |

---

# Troubleshooting

## Common Issues

### "User is not authorized to perform: sts:AssumeRole"

**Cause**: IAM user doesn't have AssumeRole permission

**Solution**:
```bash
# Check user's attached policies
aws iam list-attached-user-policies --user-name brownfield-server-user

# Attach AssumeRole policy
aws iam put-user-policy \
    --user-name brownfield-server-user \
    --policy-name AssumeRole \
    --policy-document file://assume-role-policy.json
```

### "The role does not have a trust relationship with the principal"

**Cause**: Role's trust policy doesn't include the user/role

**Solution**:
```bash
# Check current trust policy
aws iam get-role --role-name BrownfieldServerRole

# Update trust policy to include the user
# Edit trust-policy.json and update role
aws iam update-assume-role-policy-document \
    --role-name BrownfieldServerRole \
    --policy-document file://trust-policy.json
```

### "Credentials have expired"

**Cause**: Session credentials older than max duration

**Solution**:
```python
# Always request fresh credentials
credentials = accessor.get_temporary_credentials()

# Check expiration
from datetime import datetime
if credentials['Expiration'] < datetime.utcnow():
    credentials = accessor.get_temporary_credentials()  # Get new ones
```

### "AccessDenied on S3 operation"

**Cause**: Role doesn't have required S3 permissions

**Solution**:
```bash
# Check role permissions
aws iam get-role-policy --role-name BrownfieldServerRole --policy-name S3Access

# Update with required permissions
aws iam put-role-policy \
    --role-name BrownfieldServerRole \
    --policy-name S3Access \
    --policy-document file://s3-permissions.json
```

## Debugging Commands

```bash
# Test credentials
aws sts get-caller-identity \
    --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
    --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Simulate AssumeRole
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::123456789:user/brownfield-server-user \
    --action-names sts:AssumeRole \
    --resource-arns arn:aws:iam::123456789:role/BrownfieldServerRole

# Check CloudTrail for failures
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
    --max-results 10
```

---

## Complete Comparison: Brownfield vs Edge Node Credentials

### How They Get Credentials

```
BROWNFIELD SERVER (On-Premises)
────────────────────────────────────────────────────

┌────────────────────────────────────────────┐
│ Manual credential retrieval (YOU code it)  │
│                                            │
│ 1. Initialize credential manager          │
│ 2. Query storage (Secrets Manager/Vault)  │
│ 3. Retrieve long-term credentials         │
│ 4. Create STS client with them            │
│ 5. Call sts.assume_role()                 │
│ 6. Get temporary credentials              │
│ 7. Create boto3 clients                   │
│ 8. Use clients for operations             │
│ 9. Monitor expiration                     │
│ 10. Refresh before expiry                 │
│                                            │
│ Complexity: HIGH (10 steps)                │
│ Code needed: YES (credential management)  │
│ Error handling: REQUIRED (many points)     │
│ Audit trail: Manual logging                │
└────────────────────────────────────────────┘


EDGE NODE (Outpost/Wavelength/Local Zone)
────────────────────────────────────────────────────

┌────────────────────────────────────────────┐
│ Automatic credential retrieval (AWS does)  │
│                                            │
│ 1. Launch instance (specify role)          │
│ 2. AWS attaches instance profile          │
│ 3. boto3 auto-detects metadata service    │
│ 4. AWS auto-provides temporary credentials│
│ 5. boto3 auto-refreshes expiring creds    │
│                                            │
│ Complexity: LOW (AWS handles it)           │
│ Code needed: NO (boto3 is all)            │
│ Error handling: Built-in by boto3         │
│ Audit trail: Automatic CloudTrail         │
└────────────────────────────────────────────┘
```

### Security Implications

```
BROWNFIELD CHALLENGES
──────────────────

┌─ Long-term Credentials
│  ├─ Must store securely (Secrets Manager/Vault)
│  ├─ Are vulnerable if exposed
│  ├─ Hard to rotate automatically
│  └─ Greater blast radius if compromised
│
├─ Credential Storage
│  ├─ Must choose between options
│  ├─ Each has tradeoffs
│  ├─ Encryption keys must be managed
│  └─ Network dependency (if using remote storage)
│
├─ Manual Refresh Logic
│  ├─ Easy to get wrong
│  ├─ Race conditions possible
│  ├─ Expiration handling needed
│  └─ Cache invalidation complex
│
└─ Audit Trail
   ├─ Must implement logging
   ├─ Failed assumeRole attempts need handling
   └─ Multiple points of failure to log


EDGE NODE SECURITY BENEFITS
───────────────────────────

┌─ No Long-term Credentials
│  ├─ Only temporary credentials in memory
│  ├─ Auto-rotate by AWS
│  ├─ Never persisted to disk
│  └─ Minimal blast radius if compromised
│
├─ Automatic Management
│  ├─ AWS handles all credential lifecycle
│  ├─ No storage needed
│  ├─ No encryption key management
│  └─ No network dependency on credential source
│
├─ Transparent Refresh
│  ├─ boto3 handles all refresh logic
│  ├─ No race conditions
│  ├─ No cache invalidation issues
│  └─ Automatic by AWS metadata service
│
└─ Complete Audit Trail
   ├─ CloudTrail logs all calls
   ├─ Session tokens in all logs
   ├─ Automatic with no code needed
   └─ Single point of audit logging
```

### Code Complexity Comparison

```
BROWNFIELD - Full credential management code required:

```python
manager = BrownfieldCredentialManager('secrets_manager')
try:
    bootstrap_creds = manager.retrieve_bootstrap_credentials()
    creds = manager.assume_role('arn:aws:iam::...:role/...')
    if creds['expiration'] < datetime.utcnow():
        creds = manager.assume_role(...)  # refresh
    s3 = manager.get_s3_client('arn:aws:iam::...:role/...')
    s3.upload_file(...)
except Exception as e:
    logger.error(f"Credential error: {e}")
```


EDGE NODE - Simple boto3 usage:

```python
s3 = boto3.client('s3')  # That's it!
s3.upload_file(...)       # Works automatically
# boto3 handles credentials, refresh, everything!
```

─────────────────────────────────────────

Brownfield code: ~20-50 lines of credential logic
Edge node code:  0 lines of credential logic
```

---

# Summary

| Deployment Type | Role Type | How to Get | Duration | Notes |
|-----------------|-----------|-----------|----------|-------|
| **Brownfield** | User-assumed | STS AssumeRole | 1 hour max | Must store long-term credentials securely |
| **Outpost** | Service role | Auto-assigned | N/A (role-based) | No manual credential handling |
| **Wavelength** | Service role | Auto-assigned | N/A (role-based) | Works like EC2 instances |
| **Local Zone** | Service role | Auto-assigned | N/A (role-based) | Works like regular EC2 |
| **Edge→Account B** | Service role + AssumeRole | Service role + STS | 1 hour | Combine both approaches |

---

## Key Takeaways

✅ **Brownfield servers**: Always use STS AssumeRole with short duration
✅ **Edge nodes**: Use auto-assigned service roles (no credentials needed)
✅ **Cross-account**: Combine service role + AssumeRole
✅ **Security**: Store brownfield credentials in Secrets Manager
✅ **Audit**: Enable CloudTrail on all AssumeRole calls
✅ **Rotation**: Rotate brownfield credentials every 90 days

