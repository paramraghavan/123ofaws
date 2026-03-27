# Command Line to AWS Lambda: Complete Guide

## 🎯 Quick Answer: What Goes Where?

| Component | Location | Lambda Layer | Function Code |
|-----------|----------|--------------|---------------|
| **Main/Driver Code** | Converts CLI args to function call | ❌ No | ✅ **Yes** |
| **3rd Party Libraries** | `requests`, `pandas`, `numpy` | ✅ **Yes** | ❌ No |
| **Custom Modules** | `utils/`, `models/` | ✅ **Yes** | ❌ No (referenced from layer) |
| **Standard Library** | `os`, `json`, `re`, `sys` | ❌ No (pre-installed) | ✅ Can use |
| **AWS SDK** | `boto3`, `botocore` | ❌ No (pre-installed) | ✅ Can use |

---

## 📦 Standard Modules in AWS Lambda Runtime

### Pre-installed in ALL Lambda Python Runtimes

These are **built-in** — don't bundle them in your layer:

```
Standard Library (Python 3.11/3.12):
- json, os, sys, re, logging, datetime
- collections, itertools, functools
- pathlib, tempfile, shutil, subprocess
- urllib, http.client, socket
- argparse, configparser, csv
- base64, hashlib, hmac, uuid
- threading, queue, asyncio
- pickle, copy, pprint

AWS SDK (pre-installed):
- boto3
- botocore
- s3transfer
- urllib3
```

### Custom 3rd Party Libraries (MUST be in Layer)

```
- requests
- python-dotenv
- pandas
- numpy
- sqlalchemy
- psycopg2
- redis
- flask, django
- And any others you pip install
```

---

## 🔄 How CLI Arguments Map to Lambda Events

### CLI Approach
```bash
python script.py --bucket my-bucket --prefix logs/ --format json --dry-run
```

### Lambda Approach
The CLI args become part of the **event** JSON passed to your handler:

```python
{
    "bucket": "my-bucket",
    "prefix": "logs/",
    "format": "json",
    "dry_run": True
}
```

---

## 🏗️ Architecture Pattern

### The Core Principle

**Separate concerns:**
1. **`handler(event, context)` function** — Pure Lambda logic (always in function code)
2. **`main()` function** — Business logic (shared between CLI and Lambda)
3. **CLI entry point** — Parses args and calls `main()`
4. **Lambda handler** — Parses event and calls `main()`
5. **Utilities/Libraries** — In the Lambda layer

### Visual Flow

```
CLI Command
    ↓
argparse parser
    ↓
main(bucket, prefix, format, dry_run)
    ↓
Process & return result
    ↓
Print to stdout


Lambda Event
    ↓
handler(event, context)
    ↓
main(event['bucket'], event['prefix'], ...)
    ↓
Process & return result
    ↓
Return JSON response
```

---

## 📋 Project Structure

```
lambda-layer/
├── CLI_TO_LAMBDA_GUIDE.md          ← This file
├── requirements.txt                 ← ALL non-stdlib + non-boto3 packages
├── build/
│   └── python/                      ← Contents become the ZIP layer
│       ├── requests/
│       ├── dotenv/
│       └── shared_lib/              ← Your custom modules
│           ├── logger.py
│           ├── data_processor.py
│           └── __init__.py
├── upload_direct.sh
├── upload_via_s3.sh
│
└── EXAMPLES/
    ├── 1-cli-version/               ← CLI-only version
    │   ├── requirements.txt
    │   └── process_data.py
    │
    ├── 2-lambda-version/            ← Lambda deployment package
    │   ├── lambda_function.py        ← Handler code (NOT in layer)
    │   ├── requirements.txt          ← Same as layer requirements
    │   └── process_data/             ← Shared logic (also in layer)
    │       ├── processor.py
    │       └── __init__.py
    │
    └── 3-unified-dual-mode/         ← Single codebase for both
        ├── app.py                   ← Detects runtime (CLI vs Lambda)
        ├── main.py                  ← Entry point
        ├── requirements.txt
        └── modules/
            └── processor.py
```

---

## 🚀 Step-by-Step Implementation

### Step 1: Identify Shared Logic

Your business logic should NOT depend on how it's called:

**Bad:** (tightly coupled to CLI)
```python
import argparse
def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    result = process(args.bucket)
    print(json.dumps(result))
```

**Good:** (pure function)
```python
def process(bucket, prefix, format='json'):
    # Pure logic, no I/O assumptions
    return {"success": True, "items": [...]}
```

### Step 2: Create Layer Contents

**requirements.txt** — Only 3rd party packages:
```
requests==2.31.0
python-dotenv==1.0.0
boto3  # ← DON'T include, but safe to list
```

**python/shared_lib/processor.py** — Reusable logic:
```python
import logging

def process_s3_data(bucket, prefix, format='json'):
    """Process S3 data - works from CLI or Lambda"""
    logging.info(f"Processing s3://{bucket}/{prefix}")
    # Business logic here
    return {"bucket": bucket, "count": 42}
```

### Step 3: Create CLI Wrapper

**cli_app.py** — CLI entry point (NOT in layer):
```python
#!/usr/bin/env python3
import argparse
import json
import sys
from shared_lib.processor import process_s3_data

def main():
    parser = argparse.ArgumentParser(description="Process S3 data")
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--prefix', default='', help='S3 prefix')
    parser.add_argument('--format', choices=['json', 'csv'], default='json')
    parser.add_argument('--dry-run', action='store_true')

    args = parser.parse_args()

    result = process_s3_data(
        bucket=args.bucket,
        prefix=args.prefix,
        format=args.format
    )

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
```

Run:
```bash
python cli_app.py --bucket my-bucket --prefix logs/
```

### Step 4: Create Lambda Handler

**lambda_function.py** — Lambda entry point (NOT in layer):
```python
from shared_lib.processor import process_s3_data

def handler(event, context):
    """
    Lambda handler - receives event as dict

    Example event:
    {
        "bucket": "my-bucket",
        "prefix": "logs/",
        "format": "json"
    }
    """

    # Extract parameters from event
    bucket = event.get('bucket')
    prefix = event.get('prefix', '')
    format_type = event.get('format', 'json')

    # Validate
    if not bucket:
        return {
            'statusCode': 400,
            'body': 'Missing required parameter: bucket'
        }

    # Call shared logic
    result = process_s3_data(bucket, prefix, format_type)

    return {
        'statusCode': 200,
        'body': result
    }
```

Invoke from AWS:
```bash
# Via AWS CLI
aws lambda invoke \
  --function-name my-processor \
  --payload '{"bucket":"my-bucket","prefix":"logs/"}' \
  output.json

cat output.json
```

---

## 📦 Building & Deploying

### Build the Layer

```bash
# 1. Install packages to build/python/
mkdir -p build/python
pip install \
  --platform manylinux2014_x86_64 \
  --target "./build/python" \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --upgrade \
  -r requirements.txt

# 2. Copy your custom modules
mkdir -p build/python/shared_lib
cp -r modules/* build/python/shared_lib/

# 3. Create ZIP
cd build && zip -r "../my-layer.zip" python/ && cd ..
```

### Publish the Layer

```bash
aws lambda publish-layer-version \
  --layer-name "my-shared-lib" \
  --zip-file fileb://my-layer.zip \
  --compatible-runtimes python3.11 python3.12
```

Copy the returned **LayerVersionArn**.

### Deploy Function

```bash
# Create deployment package (includes lambda_function.py)
zip lambda-package.zip lambda_function.py

# Update function code
aws lambda update-function-code \
  --function-name my-processor \
  --zip-file fileb://lambda-package.zip

# Attach the layer
aws lambda update-function-configuration \
  --function-name my-processor \
  --layers "arn:aws:lambda:us-east-1:123456789012:layer:my-shared-lib:1"
```

---

## ✅ Testing Locally

### Option 1: Test CLI and Lambda together

```bash
# Install requirements locally
pip install -r requirements.txt

# Test CLI
python cli_app.py --bucket test-bucket

# Test Lambda handler locally
python -c "
from lambda_function import handler
event = {'bucket': 'test-bucket', 'prefix': 'logs/'}
context = None
result = handler(event, context)
print(result)
"
```

### Option 2: Use SAM (AWS Serverless Application Model)

```bash
# Install SAM CLI
pip install aws-sam-cli

# Run locally
sam local start-api
sam local invoke MyFunction --event event.json
```

---

## 🎓 Key Differences: CLI vs Lambda

| Aspect | CLI | Lambda |
|--------|-----|--------|
| **Invocation** | `python script.py --arg value` | HTTP POST / AWS CLI / SDK |
| **Arguments** | Command line flags | JSON event payload |
| **Return** | Print to stdout | Return JSON object |
| **Errors** | Exit code + stderr | HTTP status code + response body |
| **Context** | None | Lambda context object (timeouts, request ID, etc.) |
| **Execution** | Synchronous only | Sync or async (via SNS/SQS) |
| **Storage** | Local filesystem | /tmp only (ephemeral) |

---

## 💡 Best Practices

1. **Separate I/O from Logic**
   - Pure functions in shared modules
   - I/O (argparse, boto3 calls) at the boundaries

2. **Use Environment Variables for Configuration**
   ```python
   import os
   BUCKET = os.environ.get('DEFAULT_BUCKET')
   LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
   ```

3. **Handle Both Formats**
   ```python
   def get_param(event, cli_name, env_name=None, default=None):
       # If CLI: use sys.argv or argparse
       # If Lambda: use event dict
       # If env var set: use that
       return event.get(cli_name) or os.environ.get(env_name) or default
   ```

4. **Keep Layers Small**
   - Only include packages you actually use
   - Use `pip-audit` to check for vulnerabilities
   - Remove dev dependencies (`pytest`, `black`, etc.)

5. **Version Your Layers**
   ```bash
   # Publish as v1, v2, v3...
   aws lambda publish-layer-version \
     --layer-name "my-lib" \
     --zip-file fileb://my-layer.zip
   ```

---

## ❌ Common Mistakes

| ❌ Wrong | ✅ Right |
|---------|----------|
| Including boto3 in layer | Use pre-installed boto3 |
| Putting lambda_function.py in layer | Keep handler in function package |
| Complex CLI logic in handler | Move to shared module |
| Forgetting to use `--platform manylinux2014_x86_64` | Build wheels compatible with Lambda runtime |
| Hardcoding paths like `/home/user/...` | Use `/tmp` or environment variables |
| Unzipping without testing locally | Run through whole cycle locally first |

---

## 📚 Further Reading

- [AWS Lambda Layers Documentation](https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html)
- [Python Standard Library](https://docs.python.org/3.11/library/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Lambda Runtime Support Policy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

---

## 🔗 Quick Reference: File Locations

After publishing:
```
Layer in Lambda:
/opt/python/               ← Where layer is mounted
  ├── requests/
  ├── dotenv/
  └── shared_lib/

Function code (separate):
/var/task/                 ← Where your function code lives
  └── lambda_function.py   ← Your handler
```

Python automatically adds both to `sys.path`, so your handler can simply:
```python
from shared_lib.processor import process_s3_data
```
