# Architecture: CLI to Lambda

Visual guide showing how CLI and Lambda share code and dependencies.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Application                          │
│                                                                  │
│  Shared Business Logic (runs in both CLI and Lambda)             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ processor.py:                                            │  │
│  │  • process_records()                                     │  │
│  │  • _transform_records()                                  │  │
│  │  • _validate_records()                                   │  │
│  │  • _aggregate_records()                                  │  │
│  │  • parse_records_from_json()                             │  │
│  │                                                          │  │
│  │ logger.py:                                               │  │
│  │  • get_logger() - works on CLI and Lambda                │  │
│  │  • LambdaJsonFormatter - for CloudWatch                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           ▲
           ┌───────────────┴───────────────┐
           │                               │
           ▼                               ▼
    ┌─────────────┐              ┌──────────────┐
    │     CLI     │              │   Lambda     │
    ├─────────────┤              ├──────────────┤
    │cli_app.py   │              │lambda_fn.py  │
    │             │              │              │
    │Uses argparse│              │Event handler │
    │to parse:    │              │              │
    │--operation  │              │"operation"   │
    │--records    │              │"records"     │
    │--format     │              │"format"      │
    │--dry-run    │              │"dry_run"     │
    │             │              │              │
    │Calls:       │              │Calls:        │
    │process_..() │              │process_..()  │
    │             │              │              │
    │Returns JSON │              │Returns JSON  │
    │to stdout    │              │via HTTP 200  │
    └─────────────┘              └──────────────┘
```

---

## 📦 Dependency Distribution

### Local Development (Your Machine)

```
your-machine/
├── requirements.txt          ← pip packages for CLI
├── shared_lib/
│   ├── processor.py
│   ├── logger.py
│   └── __init__.py
└── cli_app.py
```

**Installation:**
```bash
pip install -r requirements.txt
```

**Includes:** `requests`, `python-dotenv`, + your custom modules

---

### Lambda Layer (AWS /opt)

```
Lambda Layer (my-layer.zip)
└── python/
    ├── requests/             ← From requirements.txt
    ├── urllib3/              ← From requests (dependency)
    ├── certifi/              ← From requests (dependency)
    ├── dotenv/               ← From requirements.txt
    └── shared_lib/           ← Your custom code
        ├── processor.py
        ├── logger.py
        └── __init__.py

Mounted at: /opt/python/
Added to: sys.path
```

---

### Lambda Function (Separate Deployment Package)

```
lambda-function.zip
└── lambda_function.py        ← ONLY your handler code

Does NOT include:
✗ shared_lib (it's in the layer)
✗ requests (it's in the layer)
✗ python-dotenv (it's in the layer)

When invoked:
- Lambda mounts layer at /opt/python
- Python adds /opt/python to sys.path
- Handler can import: from shared_lib.processor import ...
```

---

## 🔄 Execution Flow Comparison

### CLI Flow

```
User Command Line
        │
        ▼
  ┌──────────────────┐
  │   cli_app.py     │
  │  main() function │
  └────────┬─────────┘
           │
           ├─ argparse.parse_args()
           │  ├─ --operation: "transform"
           │  ├─ --records: "[...]"
           │  ├─ --format: "json"
           │  └─ --dry-run: false
           │
           ▼
  ┌──────────────────────────┐
  │ shared_lib/processor.py  │
  │ process_records(         │
  │   records=[...],         │
  │   operation="transform", │
  │   format="json",         │
  │   dry_run=false          │
  │ )                        │
  └────────┬─────────────────┘
           │
           ├─ _transform_records()
           │  └─ return result dict
           │
           ▼
  ┌──────────────────┐
  │   print JSON     │
  │   to stdout      │
  └──────────────────┘
           │
           ▼
      User's shell
      gets output
```

### Lambda Flow

```
AWS Lambda Service
        │
        ▼
  ┌──────────────────────┐
  │  Lambda Handler      │
  │  handler(event,      │
  │    context)          │
  │  in lambda_fn.py     │
  └────────┬─────────────┘
           │
           ├─ event['operation']
           ├─ event['records']
           ├─ event['format']
           └─ event['dry_run']
           │
           ▼
  ┌──────────────────────────┐
  │ shared_lib/processor.py  │
  │ process_records(         │
  │   records=event[...],    │
  │   operation=event[...],  │
  │   format=event[...],     │
  │   dry_run=event[...]     │
  │ )                        │
  └────────┬─────────────────┘
           │
           ├─ _transform_records()
           │  └─ return result dict
           │
           ▼
  ┌──────────────────────────┐
  │  return {                │
  │    'statusCode': 200,    │
  │    'body': {...}         │
  │  }                       │
  └──────────────────────────┘
           │
           ▼
    AWS Lambda → HTTP Response
           │
           ▼
   Lambda invoker gets JSON
```

---

## 📂 File Organization During Build

### Step 1: Clean Slate

```
examples/
├── requirements.txt
├── shared_lib/
├── cli_app.py
├── lambda_function.py
└── test_local.py
```

### Step 2: Build Process

```bash
./build_layer.sh
```

Creates:
```
examples/
├── build/                    ← TEMPORARY
│   └── python/
│       ├── requests/
│       ├── dotenv/
│       └── shared_lib/
│
├── my-layer.zip             ← FINAL LAYER
│
├── requirements.txt
├── shared_lib/
├── cli_app.py
├── lambda_function.py
└── test_local.py
```

### Step 3: Prepare Function Package

```bash
# For Lambda, create SEPARATE zip
zip lambda-function.zip lambda_function.py

# OR with more files:
zip -r lambda-function.zip \
  lambda_function.py \
  config.json
```

Creates:
```
lambda-function.zip
└── lambda_function.py
```

### Step 4: Deploy

**Upload to AWS:**
- `my-layer.zip` → AWS Lambda publish-layer-version
- `lambda-function.zip` → AWS Lambda create/update-function-code
- Attach layer ARN to function configuration

---

## 🔗 sys.path Resolution

When Lambda invokes your function:

```python
# sys.path includes (in order):
sys.path = [
    "/var/task",                    ← Your function code (lambda-function.zip)
    "/opt/python",                  ← Your layer (my-layer.zip → python/)
    "/var/runtime",                 ← AWS Runtime libraries
    "/opt/boto3",                   ← Pre-installed boto3
    ... standard library paths ...
]
```

So when you do:
```python
from shared_lib.processor import process_records
```

Python searches in this order:
1. `/var/task/` → Not found
2. `/opt/python/` → **FOUND!** (in the layer)
3. ✓ Import succeeds

---

## 🗺️ Import Paths

### CLI Development

```python
# Your file: cli_app.py
# In same directory: shared_lib/

from shared_lib.processor import process_records  # ✓ Works

# Or if shared_lib is in a parent directory:
import sys
sys.path.insert(0, '..')
from shared_lib.processor import process_records
```

### Lambda Execution

```python
# Your file: lambda_function.py
# In layer: /opt/python/shared_lib/

from shared_lib.processor import process_records  # ✓ Works

# Lambda automatically adds /opt/python to sys.path
```

### Layer Contents View

After unzipping `my-layer.zip`:

```
python/
├── requests/                 ← Package
│   ├── __init__.py
│   ├── api.py
│   ├── models.py
│   └── ...
├── urllib3/                  ← Package (dependency of requests)
├── certifi/                  ← Package (dependency of requests)
├── dotenv/                   ← Package
├── shared_lib/               ← YOUR package
│   ├── __init__.py
│   ├── processor.py
│   ├── logger.py
│   └── __pycache__/
└── ...
```

---

## 🔀 Multiple Layers

Lambda supports up to **5 layers per function**.

Example setup:
```
Layer 1: my-shared-lib
  └── python/
      └── shared_lib/

Layer 2: pip-packages
  └── python/
      ├── requests/
      ├── urllib3/
      └── dotenv/

Layer 3: aws-utilities (custom AWS helpers)
  └── python/
      └── aws_helpers/

Function Code:
  └── lambda_function.py
```

Merged at runtime:
```
/opt/python/
├── shared_lib/      (from Layer 1)
├── aws_helpers/     (from Layer 3)
├── requests/        (from Layer 2)
├── urllib3/         (from Layer 2)
└── dotenv/          (from Layer 2)

/var/task/
└── lambda_function.py
```

---

## 💾 Storage & Caching

### Local Development

```
Directory:    Persistent between runs
├── cli_app.py ← Editable
├── shared_lib/ ← Editable
├── build/ ← Temporary (can delete)
└── my-layer.zip ← Build output
```

### Lambda Execution

```
/tmp/               ← Ephemeral (500 MB max)
                    ← Persists across warm invocations
                    ← Cleared between cold starts

/var/task/          ← Read-only (your function code)

/opt/python/        ← Read-only (your layer)

/opt/boto3/         ← Read-only (AWS SDK)
```

Example:
```python
import os
import json

def handler(event, context):
    # Safe to write to /tmp
    with open('/tmp/cache.json', 'w') as f:
        json.dump(event, f)

    # Can't write to /var/task or /opt
    # os.makedirs('/var/task/new') ← FAILS
```

---

## 📊 Size & Performance

### Layer Size Impact

```
Layer unzipped:       ~5 MB
├── requests         2 MB
├── urllib3          1 MB
├── dotenv           0.1 MB
└── shared_lib       1.9 MB

Cold start impact:    +50-100ms
Warm start impact:    None (cached)
```

### Function Package Size

```
Function code:        ~2 KB
├── lambda_function.py 2 KB

Cold start:           ~50ms
Warm start:           ~1ms
```

---

## 🔐 Security Boundaries

```
┌─────────────────────────────────────────┐
│       AWS Lambda Sandbox                │
│                                         │
│  ┌──────────────────────────────┐      │
│  │ Your Function (lambda_fn.py) │      │
│  │ • Can import from layer       │      │
│  │ • Can import standard lib     │      │
│  │ • Can write to /tmp           │      │
│  │ • Cannot write to /opt        │      │
│  │ • Cannot write to /var/task   │      │
│  └──────────────────────────────┘      │
│                                         │
│  ┌──────────────────────────────┐      │
│  │ Layer Files (read-only)      │      │
│  │ • /opt/python/*              │      │
│  │ • /opt/boto3/*               │      │
│  └──────────────────────────────┘      │
│                                         │
│  ┌──────────────────────────────┐      │
│  │ Temp Storage (ephemeral)     │      │
│  │ • /tmp/                      │      │
│  │ • ~500 MB limit              │      │
│  │ • Cleared between invokes    │      │
│  └──────────────────────────────┘      │
└─────────────────────────────────────────┘
```

---

## 🔄 Version Management

### Layer Versions

Every publish creates an immutable version:

```
Version 1: Initial layer
  └── arn:aws:lambda:us-east-1:123456789012:layer:my-lib:1

Version 2: After rebuild (bugfix)
  └── arn:aws:lambda:us-east-1:123456789012:layer:my-lib:2

Version 3: After new package
  └── arn:aws:lambda:us-east-1:123456789012:layer:my-lib:3
```

Function can use any version:
```bash
# Use version 1
--layers arn:...:layer:my-lib:1

# Use version 2
--layers arn:...:layer:my-lib:2

# Use latest (usually not recommended)
--layers arn:...:layer:my-lib:LATEST
```

---

## 📈 Scaling Scenario

```
Single machine:
  python cli_app.py --operation transform --records "[...]"
  ↓
  Processes 1000 records in 2 seconds
  ↓
  Done


Thousands of calls:
  aws lambda invoke \
    --function-name my-processor \
    --payload "[...records...]"
  ↓
  AWS manages scaling automatically
  ↓
  Parallel execution across multiple sandboxes
  ↓
  Same code, same results, 1000x throughput
```

---

## 🎯 Key Takeaways

1. **Shared Code** → Layer (`shared_lib/`)
2. **3rd Party Packages** → Layer (`requests`, etc.)
3. **Entry Points** → Separate (`cli_app.py` vs `lambda_function.py`)
4. **Function Code** → Separate package (not in layer)
5. **Both call same business logic** → Identical results
6. **Layer is immutable** → Version 1, 2, 3, etc.
7. **Function is updatable** → New code, same layer
8. **sys.path magic** → Automatic `/opt/python` inclusion
9. **Temporary storage** → Only `/tmp` is writable
10. **Scale from 1 to millions** → Same code!

---

This architecture allows you to:
- ✅ Develop locally with full control
- ✅ Test CLI and Lambda identically
- ✅ Deploy to AWS with no code changes
- ✅ Scale from 1 to 1,000,000 requests/day
- ✅ Reuse code across projects via layer
