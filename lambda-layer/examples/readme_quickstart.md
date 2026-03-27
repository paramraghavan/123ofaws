# CLI to Lambda: Complete Working Example

A production-ready example showing how to write code that works both as a **command-line tool** and as an **AWS Lambda function** using a **Lambda layer** for shared dependencies.

## 📋 Project Structure

```
examples/
├── readme_quickstart.md         ← This file
├── readme_architecture.md       ← Visual diagrams
├── requirements.txt             ← Third-party packages (for layer)
│
├── shared_lib/                  ← Reusable code (goes in layer)
│   ├── __init__.py
│   ├── processor.py             ← Business logic
│   └── logger.py                ← Logging utility
│
├── cli_app.py                   ← CLI entry point (NOT in layer)
├── lambda_function.py           ← Lambda handler (NOT in layer)
│
├── deploy/                      ← Deployment tools
│   ├── build_layer.sh           ← Build the layer ZIP
│   └── deploy_layer.sh          ← Deploy to AWS Lambda
│
└── tests/                       ← Test suite
    └── test_local.py            ← All tests
```

## 🎯 Key Concepts

### What Goes Where?

| File | Goes in Layer? | Location |
|------|---|---|
| `processor.py` | ✅ YES | `/opt/python/shared_lib/` |
| `logger.py` | ✅ YES | `/opt/python/shared_lib/` |
| `requests` (package) | ✅ YES | `/opt/python/requests/` |
| `cli_app.py` | ❌ NO | Local machine only |
| `lambda_function.py` | ❌ NO | Function deployment package |

### How Arguments Map

**CLI:**
```bash
python cli_app.py --operation transform --format json --records '[...]'
```

**Lambda Event JSON:**
```json
{
    "operation": "transform",
    "format": "json",
    "records": [...]
}
```

Both call the same `process_records()` function from `shared_lib/processor.py`.

---

## ⚡ Quick Start

### 1. Setup Local Environment

```bash
# Clone or navigate to examples directory
cd examples

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Test CLI

```bash
# Run with transform operation
python cli_app.py \
  --operation transform \
  --format json \
  --records '[{"Name":"Alice","Email":"alice@example.com"}]'
```

**Expected Output:**
```json
{
  "success": true,
  "operation": "transform",
  "count_processed": 1,
  "dry_run": false,
  "format": "json",
  "timestamp": "2024-03-27T...",
  "sample": [{"name": "Alice", "email": "alice@example.com"}]
}
```

### 3. Test Lambda Handler Locally

```bash
# Direct Python invocation
python lambda_function.py

# Or via test script
python tests/test_local.py
```

### 4. Build Layer

```bash
chmod +x deploy/build_layer.sh
./deploy/build_layer.sh
```

This creates `my-layer.zip` containing:
- `requests` package
- `python-dotenv` package
- `shared_lib/` (your custom modules)

### 5. Deploy to AWS

```bash
chmod +x deploy/deploy_layer.sh
./deploy/deploy_layer.sh
```

This publishes the layer and prints an **ARN** like:
```
arn:aws:lambda:us-east-1:123456789012:layer:my-shared-lib:1
```

### 6. Attach to Lambda Function

```bash
# Update existing function
aws lambda update-function-configuration \
  --function-name my-processor \
  --layers arn:aws:lambda:us-east-1:123456789012:layer:my-shared-lib:1
```

---

## 📖 Detailed Usage Examples

### CLI Examples

#### 1. Transform Records (Lowercase Keys)

```bash
python cli_app.py \
  --operation transform \
  --records '[
    {"Name":"Alice","Email":"alice@example.com","Category":"VIP"},
    {"Name":"Bob","Email":"bob@example.com","Category":"Regular"}
  ]'
```

#### 2. Validate Records (Check Required Fields)

```bash
python cli_app.py \
  --operation validate \
  --records '[
    {"id":1,"name":"Alice","email":"alice@example.com"},
    {"id":2,"name":"Bob"},
    {"email":"charlie@example.com"}
  ]'
```

Output will show which records are invalid (missing `id` or `email`).

#### 3. Aggregate Records by Category

```bash
python cli_app.py \
  --operation aggregate \
  --records '[
    {"id":1,"category":"A","name":"Alice"},
    {"id":2,"category":"B","name":"Bob"},
    {"id":3,"category":"A","name":"Charlie"}
  ]'
```

#### 4. Dry-run Mode

```bash
python cli_app.py \
  --operation transform \
  --dry-run \
  --records '[...]'
```

#### 5. Verbose Logging

```bash
python cli_app.py \
  --operation validate \
  --verbose \
  --records '[...]'
```

#### 6. Custom Output Format

```bash
python cli_app.py \
  --operation transform \
  --format csv \
  --records '[...]'
```

### Lambda Examples

#### 1. Basic Invocation

```bash
aws lambda invoke \
  --function-name my-processor \
  --payload '{"operation":"transform","records":[]}' \
  output.json

cat output.json
```

#### 2. With All Parameters

```bash
aws lambda invoke \
  --function-name my-processor \
  --payload '{
    "operation": "validate",
    "records": [
      {"id":1,"name":"Alice","email":"alice@example.com"},
      {"id":2,"name":"Bob"}
    ],
    "format": "json",
    "dry_run": false
  }' \
  output.json
```

#### 3. Error Handling

```bash
# Missing required field - returns 400
aws lambda invoke \
  --function-name my-processor \
  --payload '{"records":[]}' \
  output.json

cat output.json
# Response: {"statusCode": 400, "body": {"success": false, "error": "Missing required parameter: operation"}}
```

#### 4. From Python Code

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='my-processor',
    InvocationType='RequestResponse',  # Sync
    Payload=json.dumps({
        "operation": "transform",
        "records": [{"Name": "Alice"}]
    })
)

result = json.loads(response['Payload'].read())
print(result)
```

---

## 🧪 Testing

### Run All Tests

```bash
python tests/test_local.py
```

This runs:
1. CLI - Transform operation
2. CLI - Validate operation
3. CLI - Dry-run flag
4. Lambda - Transform operation
5. Lambda - Error handling

Expected output:
```
✅ PASS: CLI - Transform
✅ PASS: CLI - Validate
✅ PASS: CLI - Dry-run
✅ PASS: Lambda - Transform
✅ PASS: Lambda - Error Handling

Total: 5/5 tests passed
```

### Individual Tests

```bash
# Test shared library directly
python -c "
from shared_lib.processor import process_records
records = [{'Name': 'Alice'}]
result = process_records(records, 'transform')
print(result)
"

# Test CLI
python cli_app.py --operation transform --records '[{"id":1}]'

# Test Lambda
python -c "
from lambda_function import handler
class Context:
    invoked_function_arn = 'test'
event = {'operation': 'transform', 'records': [{'id': 1}]}
print(handler(event, Context()))
"
```

---

## 📦 Understanding the Layer

### What's Included?

After building, `my-layer.zip` contains:

```
python/
├── requests/              ← Third-party package
├── dotenv/                ← Third-party package
└── shared_lib/            ← Your custom modules
    ├── __init__.py
    ├── processor.py
    └── logger.py
```

### How Lambda Uses It?

When you attach the layer to a Lambda function, AWS:
1. Extracts it to `/opt/python/` in the Lambda sandbox
2. Adds `/opt/python/` to Python's `sys.path`
3. Your function code can import: `from shared_lib.processor import ...`

### Size Limits

```
Direct upload:     50 MB
Via S3:            No limit
Unzipped size:     250 MB
Function + layers: 250 MB total
```

This example is small (~2-5 MB unzipped), so direct upload works fine.

---

## 🔄 Development Workflow

### 1. Make Changes Locally

Edit `shared_lib/processor.py`:
```python
def _transform_records(...):
    # Your changes here
    ...
```

### 2. Test with CLI

```bash
python cli_app.py --operation transform --records '[...]'
```

### 3. Test with Lambda

```bash
python -c "from lambda_function import handler; ..."
```

### 4. Rebuild Layer

```bash
./deploy/build_layer.sh
```

### 5. Deploy to AWS

```bash
./deploy/deploy_layer.sh
```

### 6. Update Function

```bash
aws lambda update-function-configuration \
  --function-name my-processor \
  --layers arn:aws:lambda:...layer:...:2
```

---

## 🐛 Troubleshooting

### ImportError: No module named 'shared_lib'

**Cause:** Lambda layer not attached to function.

**Fix:**
```bash
aws lambda update-function-configuration \
  --function-name my-processor \
  --layers arn:aws:lambda:...
```

### ImportError: No module named 'requests'

**Cause:** `requests` package not in layer.

**Fix:** Rebuild the layer with `./deploy/build_layer.sh`

### ModuleNotFoundError on macOS/Windows

**Cause:** Building on non-Linux platform. Packages need to be Linux-compatible.

**Fix:** Use `--platform manylinux2014_x86_64` when building (already in script).

### Handler crashed during execution

**Cause:** Unhandled exception in your code.

**Fix:** Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/my-processor --follow
```

### ZIP file is too large

**Cause:** Bundled unnecessary packages (numpy, pandas, etc.).

**Fix:** Review `requirements.txt` and remove unused packages.

---

## 🚀 Production Best Practices

### 1. Use Environment Variables

```python
import os

BUCKET = os.environ.get('DEFAULT_BUCKET')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
```

Set via AWS Console or CLI:
```bash
aws lambda update-function-configuration \
  --function-name my-processor \
  --environment Variables={DEFAULT_BUCKET=my-bucket,LOG_LEVEL=DEBUG}
```

### 2. Handle Structured Logging

CloudWatch Logs can parse JSON for better searching:

```python
from shared_lib.logger import get_logger
logger = get_logger(__name__)
logger.info("Processing started", extra={"bucket": "my-bucket"})
```

### 3. Use IAM Role for AWS Access

Your Lambda execution role needs permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

### 4. Monitor and Alert

CloudWatch Alarms:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name my-processor-errors \
  --alarm-description "Alert on function errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold
```

### 5. Version Your Code

Use git tags:
```bash
git tag v1.0.0
aws lambda update-function-code \
  --function-name my-processor \
  --zip-file fileb://lambda-function.zip
```

---

## 📚 Related Files

- **CLI_TO_LAMBDA_GUIDE.md** - Comprehensive guide (in parent directory)
- **requirements.txt** - Package dependencies
- **shared_lib/processor.py** - Core business logic
- **shared_lib/logger.py** - Logging utilities
- **cli_app.py** - Command-line interface
- **lambda_function.py** - Lambda handler
- **test_local.py** - Test suite

---

## ✅ Checklist: From Local to Production

- [ ] Code works locally with CLI
- [ ] Code works locally with Lambda handler
- [ ] All tests pass (`python tests/test_local.py`)
- [ ] Layer builds successfully (`./deploy/build_layer.sh`)
- [ ] Layer deploys to AWS (`./deploy/deploy_layer.sh`)
- [ ] Function code uploaded to AWS
- [ ] Layer attached to function
- [ ] Test invocation works from AWS CLI
- [ ] CloudWatch Logs show correct output
- [ ] IAM role has necessary permissions
- [ ] Error handling tested
- [ ] Performance acceptable
- [ ] Cost within budget
- [ ] Monitoring/alerts configured

---

## 📖 Further Reading

- [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html)
- [Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/limits.html)
- [Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

## 💡 Tips & Tricks

### Test Layer Locally

```bash
# Simulate Lambda environment
export PYTHONPATH=/opt/python:$PYTHONPATH
mkdir -p /tmp/opt/python
cp -r build/python/* /tmp/opt/python/
python tests/test_local.py
```

### View Layer Contents

```bash
unzip -l my-layer.zip | head -50
```

### Check Installed Packages

```bash
pip freeze | grep -E "(requests|python-dotenv)"
```

### Remove Unused Packages

```bash
pip list --user
pip uninstall -y <package-name>
pip freeze > requirements.txt
```

### Auto-format Code

```bash
pip install black
black *.py shared_lib/*.py
```

---

## 🤝 Contributing

To extend this example:

1. Add new operations to `shared_lib/processor.py`
2. Update CLI arg parser in `cli_app.py`
3. Update Lambda handler in `lambda_function.py`
4. Add tests to `test_local.py`
5. Rebuild and deploy

---

## 📞 Support

If you encounter issues:

1. Check **Troubleshooting** section above
2. Review **CLI_TO_LAMBDA_GUIDE.md** for concepts
3. Check CloudWatch Logs: `aws logs tail /aws/lambda/my-processor`
4. Enable verbose logging: `LOG_LEVEL=DEBUG`

---

**Last Updated:** March 2024
**Python Version:** 3.11+
**AWS Lambda Runtime:** python3.11, python3.12
