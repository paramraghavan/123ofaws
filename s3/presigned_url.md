# S3 Presigned URLs - Complete Tutorial

> **Grant Temporary Access to S3 Objects**: Learn to create time-limited, credential-free URLs for sharing and uploading files.

---

## Table of Contents

1. [What is a Presigned URL? (Beginner)](#what-is-a-presigned-url-beginner)
2. [The Mental Model (Sticks in Your Mind!)](#the-mental-model-sticks-in-your-mind)
3. [How Presigned URLs Work](#how-presigned-urls-work)
4. [Creating Presigned URLs](#creating-presigned-urls)
5. [Use Cases](#use-cases)
6. [Security Considerations](#security-considerations)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Patterns](#advanced-patterns)

---

## What is a Presigned URL? (Beginner)

### Simple Explanation

A **presigned URL** is a temporary link to an S3 object that allows anyone with the link to access it—**without needing AWS credentials**.

**Key points:**
- ✅ Allows public access to private S3 objects
- ✅ Time-limited (expires after set duration)
- ✅ Works with a browser (no AWS SDK needed)
- ✅ Can be for download OR upload
- ✅ No AWS credentials exposed

**Quick example:**
```
Regular S3 object: BLOCKED without AWS credentials
       ↓
Generate presigned URL
       ↓
https://my-bucket.s3.amazonaws.com/file.pdf?...&Expires=1234567890&Signature=abc123...
       ↓
Anyone can click the link and access the file
       ↓
URL expires in 1 hour, link becomes invalid
```

---

## The Mental Model (Sticks in Your Mind!)

Think of presigned URLs like **temporary guest passes**:

```
Your Company Building (S3 Bucket):
├─ Private office (Private S3 object)
└─ Anyone needs credentials to enter

Need to let a client in?
├─ Option 1: Give them your master key (BAD!)
│  └─ They have unlimited access forever
│
├─ Option 2: Issue a guest pass (GOOD!)
│  ├─ "Valid for 1 hour only"
│  ├─ "Can only access Conference Room 3"
│  ├─ "Cannot visit the vault"
│  └─ After 1 hour, pass expires automatically

Presigned URL = Guest Pass:
├─ Time-limited access (expires)
├─ Specific object access (can't access other files)
├─ No permanent credentials given
└─ Works like a magic URL anyone can use
```

**Real-world analogy:**
- **AWS credentials** = Master key to building (unlimited, permanent)
- **Presigned URL** = Guest pass (limited, temporary)

You never hand out master keys to clients. You issue guest passes instead.

---

## How Presigned URLs Work

### Step-by-Step Process

```
1. YOU create presigned URL
   ├─ You have AWS credentials (master key)
   ├─ You specify: bucket, object, expiration time
   └─ AWS signs the URL with your secret key

2. URL is created with signature
   ├─ Contains: S3 bucket, object key
   ├─ Contains: Expiration timestamp
   ├─ Contains: Cryptographic signature (proves it's real)
   └─ Looks like: https://bucket.s3.amazonaws.com/file.pdf?Expires=123&Signature=abc...

3. URL is shared
   ├─ Send to client via email, chat, web page
   └─ Client doesn't need AWS credentials

4. Client uses URL
   ├─ Clicks link or downloads
   ├─ S3 verifies signature (proves it's authentic)
   ├─ Checks expiration (not expired)
   └─ Grants access to that ONE object

5. URL expires
   └─ Client clicks link after expiration
      └─ S3 rejects: "This URL is no longer valid"
         └─ Client can no longer access the file
```

### What Makes It Secure?

```
Why can't someone just make their own presigned URL?

1. URL contains cryptographic signature
   └─ Generated using YOUR secret AWS key
   └─ Only you can generate valid signatures

2. If someone modifies the URL
   ├─ Changes expiration time
   ├─ Changes object name
   ├─ Changes bucket name
   └─ Signature becomes invalid → S3 rejects it

3. URL expires automatically
   └─ Even if URL is leaked, it stops working
   └─ Time limit = built-in security
```

---

## Creating Presigned URLs

### Method 1: For Downloading (GET)

```python
import boto3
from datetime import timedelta

s3 = boto3.client('s3')

# Generate presigned URL for downloading a file
url = s3.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'my-bucket',
        'Key': 'documents/report.pdf'
    },
    ExpiresIn=3600  # URL valid for 1 hour (3600 seconds)
)

print(url)
# Output: https://my-bucket.s3.amazonaws.com/documents/report.pdf?Expires=1234567890&Signature=...
```

**How to use:**
```bash
# Anyone can download using the URL
curl "https://my-bucket.s3.amazonaws.com/documents/report.pdf?Expires=1234567890&Signature=..." \
  -o report.pdf
```

---

### Method 2: For Uploading (PUT)

```python
import boto3

s3 = boto3.client('s3')

# Generate presigned URL for uploading a file
url = s3.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': 'my-bucket',
        'Key': 'uploads/user-file.txt'
    },
    ExpiresIn=1800  # URL valid for 30 minutes
)

print(url)
```

**How to use:**
```bash
# Anyone can upload using the URL
curl -X PUT --data-binary "@myfile.txt" \
  "https://my-bucket.s3.amazonaws.com/uploads/user-file.txt?Expires=1234567890&Signature=..."
```

---

### Method 3: For HTML Form Upload

For web applications where users upload files via form:

```python
import boto3

s3 = boto3.client('s3')

# Generate presigned POST (for HTML forms)
response = s3.generate_presigned_post(
    Bucket='my-bucket',
    Key='uploads/user-file.txt',
    ExpiresIn=3600
)

# response contains:
# {
#   'url': 'https://my-bucket.s3.amazonaws.com/',
#   'fields': {
#       'key': 'uploads/user-file.txt',
#       'policy': '...',
#       'x-amz-signature': '...',
#       'x-amz-date': '...',
#       ...
#   }
# }

print(response['url'])
print(response['fields'])
```

**Use in HTML:**
```html
<form method="POST" action="{{ url }}" enctype="multipart/form-data">
  {% for key, value in fields.items() %}
    <input type="hidden" name="{{ key }}" value="{{ value }}">
  {% endfor %}

  <input type="file" name="file">
  <button type="submit">Upload</button>
</form>
```

---

## Use Cases

### Use Case 1: Share Files with Clients

**Scenario:** Consultant generates report, needs to share with client

```python
import boto3

s3 = boto3.client('s3')

# Client needs to download report for 24 hours
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'reports', 'Key': 'q4-analysis.pdf'},
    ExpiresIn=86400  # 24 hours
)

# Send URL to client via email
email_body = f"""
Your report is ready:
{url}

This link expires in 24 hours.
"""
```

---

### Use Case 2: User Profile Pictures

**Scenario:** Users upload profile pictures to private bucket

```python
import boto3

s3 = boto3.client('s3')

def get_profile_picture_url(user_id):
    """Get temporary URL for user's profile picture"""
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'user-uploads',
            'Key': f'profiles/{user_id}/picture.jpg'
        },
        ExpiresIn=3600  # 1 hour (can be longer for static images)
    )
    return url

# In your web app:
user_picture_url = get_profile_picture_url('user-123')
# Use in HTML: <img src="{{ user_picture_url }}">
```

---

### Use Case 3: Multi-Step Data Upload

**Scenario:** Allow users to upload data to private bucket in phases

```python
import boto3
import secrets

s3 = boto3.client('s3')

def generate_upload_url(user_id, file_type):
    """Generate URL for user to upload specific file type"""

    # Include timestamp to make key unique
    timestamp = int(time.time())
    key = f'user-data/{user_id}/{file_type}-{timestamp}.json'

    url = s3.generate_presigned_post(
        Bucket='user-data',
        Key=key,
        ExpiresIn=1800,  # 30 minutes to upload
        Conditions=[
            ['content-length-range', 0, 10485760],  # Max 10MB
            ['starts-with', '$Content-Type', 'application/json']  # Only JSON
        ]
    )

    return url, key

# User gets upload URL
url_data, key = generate_upload_url('user-123', 'personal-data')
# User uploads file to URL
# File lands in S3 at exactly: user-data/user-123/personal-data-1234567890.json
```

---

## Security Considerations

### ✅ DO: Use Time Limits

```python
# ✓ GOOD: Expires in 1 hour
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'bucket', 'Key': 'file.pdf'},
    ExpiresIn=3600
)

# ✗ BAD: Expires in 7 days (too long!)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'bucket', 'Key': 'file.pdf'},
    ExpiresIn=604800  # 7 days - too permissive!
)
```

**Guidelines:**
- Public download: 1 hour
- Form upload: 15-30 minutes
- Single download: 5-15 minutes
- Maximum: 7 days (AWS limit)

---

### ✅ DO: Restrict Operations

```python
# ✓ GOOD: User can only PUT (upload), not DELETE
url = s3.generate_presigned_url(
    'put_object',  # Specific operation
    Params={'Bucket': 'bucket', 'Key': 'file.txt'},
    ExpiresIn=1800
)

# ✗ BAD: If you give get_object + put_object, user can read AND write
```

---

### ✅ DO: Validate Content

```python
# ✓ GOOD: Restrict by content type and size
response = s3.generate_presigned_post(
    Bucket='bucket',
    Key='upload/file.jpg',
    ExpiresIn=3600,
    Conditions=[
        ['content-length-range', 0, 5242880],  # Max 5MB
        ['starts-with', '$Content-Type', 'image/']  # Only images
    ]
)
```

---

### ❌ DON'T: Share Secret Key

```python
# ✗ WRONG: Never put AWS credentials in presigned URL
# The signature is based on your secret key, not the credentials themselves

# ✓ RIGHT: Presigned URL doesn't expose credentials
# Only your code (with credentials) generates the URL
# URL is shared, but credentials stay hidden
```

---

### ❌ DON'T: Log the Full URL

```python
# ✗ WRONG: URL in logs can be captured
import logging
url = s3.generate_presigned_url(...)
logging.info(f"Generated URL: {url}")  # URL in logs = vulnerable!

# ✓ RIGHT: Log only the key, not the signature
logging.info(f"Generated URL for key: documents/report.pdf")
```

---

## Best Practices

### 1. Generate URLs Server-Side Only

```python
# ✓ GOOD: Backend generates URL, sends to frontend
# Frontend code:
@app.route('/api/download-url')
def get_download_url():
    url = s3.generate_presigned_url(...)  # Server-side
    return {'url': url}

# ✗ BAD: Frontend has AWS credentials
// Frontend code:
const s3 = new AWS.S3({
    accessKeyId: AWS_KEY,  // Exposed in browser!
    secretAccessKey: AWS_SECRET
});
```

---

### 2. Use Minimal Permissions

```python
# Create IAM user with minimal permissions
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",  # Only GET
      "Resource": "arn:aws:s3:::my-bucket/public/*"  # Only specific prefix
    }
  ]
}
```

---

### 3. Monitor Usage

```python
import boto3
import logging

s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

def generate_tracked_url(bucket, key, reason='unnamed'):
    """Generate presigned URL and log it"""
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=3600
    )

    # Log for audit trail
    logging.info(f"Presigned URL generated for {key} by {reason}")

    # Send metric
    cloudwatch.put_metric_data(
        Namespace='PresignedURLs',
        MetricData=[{
            'MetricName': 'URLsGenerated',
            'Value': 1
        }]
    )

    return url
```

---

## Troubleshooting

### Problem: "Invalid signature" Error

**Cause:** URL is modified or signature is corrupted

**Solution:**
- Don't modify URL after generation
- Make sure you're copying the entire URL (including query parameters)
- Check for URL encoding issues (spaces become `%20`, etc.)

---

### Problem: "Request has expired" Error

**Cause:** URL expiration time has passed

**Solution:**
- Generate a fresh URL with new expiration time
- Use longer `ExpiresIn` if needed (max 7 days)
- Check system clock is correct

---

### Problem: Access Denied (403)

**Possible causes:**
1. Bucket is not accessible to the user who generated the URL
2. Object doesn't exist
3. Incorrect bucket or key name

**Solution:**
```python
import boto3

s3 = boto3.client('s3')

# Verify bucket exists and you have access
try:
    s3.head_bucket(Bucket='my-bucket')
    print("✓ Bucket accessible")
except Exception as e:
    print(f"✗ Bucket error: {e}")

# Verify object exists
try:
    s3.head_object(Bucket='my-bucket', Key='documents/file.pdf')
    print("✓ Object exists")
except Exception as e:
    print(f"✗ Object error: {e}")
```

---

## Advanced Patterns

### Pattern 1: Custom Response Headers

Control how browser handles the download:

```python
s3 = boto3.client('s3')

url = s3.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'my-bucket',
        'Key': 'documents/report.pdf',
        'ResponseContentDisposition': 'attachment; filename="report.pdf"',
        'ResponseContentType': 'application/pdf'
    },
    ExpiresIn=3600
)

# Browser will:
# - Download the file (not display in browser)
# - Use filename "report.pdf"
# - Treat as PDF content type
```

---

### Pattern 2: Conditional URLs

Generate different URLs based on user role:

```python
def get_download_url(user_role, file_key):
    """Generate URL with different expiration by role"""

    if user_role == 'admin':
        expires = 86400  # 24 hours
    elif user_role == 'user':
        expires = 3600   # 1 hour
    else:
        expires = 300    # 5 minutes

    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'bucket', 'Key': file_key},
        ExpiresIn=expires
    )

    return url

# Usage:
admin_url = get_download_url('admin', 'sensitive/data.pdf')
user_url = get_download_url('user', 'shared/report.pdf')
guest_url = get_download_url('guest', 'public/demo.pdf')
```

---

### Pattern 3: Rotating Upload Endpoints

Generate new upload URL for each file:

```python
import uuid
import time

def get_upload_endpoint(user_id):
    """Generate unique upload endpoint per request"""

    unique_id = str(uuid.uuid4())
    timestamp = int(time.time())

    # Create unique key
    key = f'uploads/{user_id}/{timestamp}-{unique_id}.json'

    url = s3.generate_presigned_post(
        Bucket='uploads',
        Key=key,
        ExpiresIn=1800,
        Conditions=[
            ['content-length-range', 0, 1048576]  # Max 1MB
        ]
    )

    return {
        'upload_url': url['url'],
        'form_data': url['fields'],
        'file_key': key
    }
```

---

## Common Questions

**Q: Can I revoke a presigned URL?**
A: No, not directly. The URL is valid until it expires. To effectively revoke:
- Delete the S3 object
- Delete the IAM user's credentials (if URL was generated by temporary credentials)
- Use S3 access logs to monitor usage

**Q: Can I make a presigned URL permanent?**
A: No, AWS has a 7-day maximum. For permanent access, use:
- S3 bucket policy (public or role-based)
- CloudFront distribution with signed URLs

**Q: Can presigned URLs work with server-side encryption?**
A: Yes! If the bucket uses SSE-S3 or SSE-KMS, presigned URLs work transparently.

**Q: Can I limit presigned URL to specific IP addresses?**
A: Not with presigned URLs directly. Use:
- S3 bucket policy with IP conditions
- CloudFront with IP whitelisting

---

## Summary

| Aspect | Details |
|--------|---------|
| **What** | Time-limited URL for S3 access without credentials |
| **Why** | Share files safely without exposing AWS keys |
| **How long** | 1-7 days (you choose) |
| **For download** | `generate_presigned_url('get_object', ...)` |
| **For upload** | `generate_presigned_url('put_object', ...)` or `generate_presigned_post(...)` |
| **Security** | Signature proves authenticity, expiration limits exposure |
| **Best practice** | Generate server-side, short expiration, minimal scope |

---

## Next Steps

- Use for file sharing with clients
- Add upload forms to your web app
- Integrate with CloudFront for CDN distribution
- Monitor presigned URL usage with CloudWatch

---

**Last Updated:** 2026-05-28
**Level:** Beginner to Intermediate
