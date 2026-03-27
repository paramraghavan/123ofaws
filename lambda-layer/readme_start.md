# Lambda Layer: CLI to Lambda Conversion

Convert command-line Python scripts to AWS Lambda functions using Lambda layers for shared code.

---

## 🎯 Quick Navigation

| Need | Document | Time |
|------|----------|------|
| **Start here** | This file | 5 min |
| **How it works** | `readme_cli_to_lambda_guide.md` | 30 min |
| **Code examples** | `examples/readme_quickstart.md` | 1 hour |
| **Architecture** | `examples/readme_architecture.md` | 20 min |
| **Pre-installed modules** | `readme_lambda_standard_modules.md` | reference |
| **Overview** | `readme_implementation_summary.md` | 20 min |

---

## 📁 Folder Structure

```
lambda-layer/
├── examples/                    ← Working code & examples
│   ├── readme_quickstart.md     ← Start here for hands-on
│   ├── readme_architecture.md   ← Visual diagrams
│   ├── shared_lib/              ← Reusable code (goes in layer)
│   │   ├── processor.py         ← Business logic
│   │   └── logger.py            ← Logging
│   ├── cli_app.py               ← CLI entry point
│   ├── lambda_function.py       ← Lambda handler
│   ├── requirements.txt         ← Dependencies
│   ├── deploy/                  ← Deployment scripts
│   │   ├── build_layer.sh       ← Build layer ZIP
│   │   └── deploy_layer.sh      ← Deploy to AWS
│   └── tests/                   ← Test suite
│       └── test_local.py        ← All tests
│
└── Guides/
    ├── readme_cli_to_lambda_guide.md      ← Comprehensive guide
    ├── readme_lambda_standard_modules.md  ← Pre-installed packages
    └── readme_implementation_summary.md   ← Overview
```

---

## ⚡ Quick Start (5 Minutes)

### 1. Test Locally

```bash
cd examples
pip install -r requirements.txt
python tests/test_local.py
```

Expected: ✅ 5/5 tests passing

### 2. Try the CLI

```bash
python cli_app.py \
  --operation transform \
  --records '[{"Name":"Alice","Email":"alice@example.com"}]'
```

### 3. Build the Layer

```bash
./deploy/build_layer.sh
```

Creates: `my-layer.zip`

### 4. Deploy to AWS

```bash
./deploy/deploy_layer.sh
```

Shows: Layer ARN for attachment

---

## 🎯 Core Concepts

### Question 1: What goes in the Lambda layer?

✅ **YES:**
- 3rd party packages (`requests`, `pandas`, `numpy`)
- Custom reusable code (`shared_lib/`)

❌ **NO:**
- Main handler (`lambda_function.py`)
- CLI code (`cli_app.py`)
- Pre-installed modules (`boto3`, `json`, `os`, etc.)

### Question 2: How do CLI arguments become Lambda events?

```bash
# CLI
python cli_app.py --operation transform --records '[...]'

# Lambda (same business logic)
event = {"operation": "transform", "records": [...]}
```

Both call: `process_records(records, operation)`

### Question 3: What's pre-installed in Lambda?

✅ **Standard Library:** `json`, `os`, `re`, `logging`, `datetime`, `sqlite3`, `urllib`, `asyncio`

✅ **AWS SDK:** `boto3`, `botocore`, `s3transfer`

❌ **Don't bundle** these - they waste space!

### Question 4: What must I bundle?

✅ **Must bundle:** `requests`, `pandas`, `numpy`, `flask`, `django`, `sqlalchemy`, etc.

---

## 📂 What's Inside

### Code (All Tested ✅)

| File | Purpose | Size |
|------|---------|------|
| `shared_lib/processor.py` | Business logic (transform/validate/aggregate) | 250 lines |
| `shared_lib/logger.py` | Smart logging (CLI + Lambda) | 50 lines |
| `cli_app.py` | Command-line interface | 150 lines |
| `lambda_function.py` | Lambda handler | 150 lines |
| `tests/test_local.py` | Test suite (5 tests) | 200 lines |

### Deployment Tools

| Script | Purpose |
|--------|---------|
| `deploy/build_layer.sh` | Build the layer ZIP |
| `deploy/deploy_layer.sh` | Deploy to AWS Lambda |

### Documentation

| Document | Purpose | Lines |
|----------|---------|-------|
| `readme_cli_to_lambda_guide.md` | Comprehensive guide | 450+ |
| `readme_lambda_standard_modules.md` | Pre-installed packages | 350+ |
| `readme_architecture.md` | Visual diagrams | 350+ |
| `readme_quickstart.md` | Hands-on guide | 500+ |
| `readme_implementation_summary.md` | Overview | 400+ |

---

## 🚀 3 Operations Demonstrated

### 1. Transform
Converts dictionary keys to lowercase

```bash
cli_app.py --operation transform --records '[{"Name":"Alice"}]'
```

### 2. Validate
Checks for required fields (id, name, email)

```bash
cli_app.py --operation validate --records '[{"id":1,"name":"Bob"}]'
```

### 3. Aggregate
Groups records by category

```bash
cli_app.py --operation aggregate --records '[{"category":"A","id":1}]'
```

---

## 📖 Reading Guide

### Beginner (30 minutes)
1. Read this file
2. Skim `readme_cli_to_lambda_guide.md` (sections 1-3)
3. Check summary table in `readme_lambda_standard_modules.md`

### Hands-On (1-2 hours)
1. Go to `examples/`
2. Read `readme_quickstart.md`
3. Run `tests/test_local.py`
4. Try the CLI and Lambda handler

### Complete Understanding (3-4 hours)
1. Read all guides
2. Study all code files
3. Deploy to AWS using scripts
4. Modify for your use case

---

## ✨ Key Features

✅ Same code works from CLI and Lambda
✅ No code duplication
✅ Command-line args → Lambda events (automatic)
✅ Production-ready error handling
✅ CloudWatch logging
✅ Complete test suite
✅ Automated build & deploy scripts
✅ Comprehensive documentation

---

## 🔗 Next Steps

1. **Read:** `readme_cli_to_lambda_guide.md` (understand concepts)
2. **Explore:** Go to `examples/` folder
3. **Test:** Run `tests/test_local.py`
4. **Try:** Run `cli_app.py` with different operations
5. **Build:** Execute `deploy/build_layer.sh`
6. **Deploy:** Execute `deploy/deploy_layer.sh`
7. **Adapt:** Modify `shared_lib/processor.py` for your use case

---

## 📊 File Size Expectations

- `my-layer.zip`: ~2-5 MB (uncompressed)
- Deployment time: < 1 minute
- Cold start impact: ~50-100ms
- No impact on warm starts

---

## ✅ What You'll Learn

✅ How to write code that works as both CLI and Lambda
✅ What goes in a Lambda layer vs function code
✅ How command-line arguments map to Lambda events
✅ Which Python modules are pre-installed in Lambda
✅ How to build and deploy Lambda layers
✅ Best practices for Lambda development
✅ How to test Lambda code locally

---

## 🎓 Architecture at a Glance

```
CLI Command
    ↓
argparse parser
    ↓
process_records(bucket, prefix, format, dry_run)  ← Shared logic
    ↓
Output to stdout


Lambda Event
    ↓
handler(event, context)
    ↓
process_records(bucket, prefix, format, dry_run)  ← Same function!
    ↓
HTTP 200 response
```

Both use the same business logic from `shared_lib/processor.py` (in the layer).

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| ImportError: No module | Run `pip install -r requirements.txt` |
| Tests fail | Check Python version (3.11+) |
| Layer attachment fails | Copy ARN from `deploy/deploy_layer.sh` output |
| ZIP too large | Remove unused packages from `requirements.txt` |

See `examples/readme_quickstart.md` for more troubleshooting.

---

## 📞 Quick Reference

**Pre-installed in Lambda (don't bundle):**
```
json, os, sys, re, logging, datetime, sqlite3, urllib, boto3, botocore
```

**Must bundle (3rd party):**
```
requests, pandas, numpy, flask, django, sqlalchemy, pydantic
```

See `readme_lambda_standard_modules.md` for complete list.

---

## 🔄 Full Workflow

1. **Local Development:**
   - Edit `shared_lib/processor.py`
   - Test with CLI: `cli_app.py --operation ...`
   - Test with Lambda: `tests/test_local.py`

2. **Build:**
   - Run `deploy/build_layer.sh` → Creates `my-layer.zip`

3. **Deploy:**
   - Run `deploy/deploy_layer.sh` → Get Layer ARN
   - Attach ARN to Lambda function

4. **Use:**
   - Invoke function via AWS console or API
   - Same code, massively scalable

---

## 📝 File Quick Reference

| File | Lines | Purpose |
|------|-------|---------|
| `shared_lib/processor.py` | 250+ | Business logic (layer) |
| `shared_lib/logger.py` | 50+ | Logging utility (layer) |
| `cli_app.py` | 150+ | CLI entry point (NOT layer) |
| `lambda_function.py` | 150+ | Lambda handler (NOT layer) |
| `tests/test_local.py` | 200+ | Test suite |
| `deploy/build_layer.sh` | 100+ | Build tool |
| `deploy/deploy_layer.sh` | 100+ | Deploy tool |
| Guides | 2000+ | Documentation |

**Total:** ~3,500 lines of code, tests, tools, and documentation.

---

**Start with:** `examples/readme_quickstart.md` for hands-on learning!

**Or read:** `readme_cli_to_lambda_guide.md` for comprehensive concepts.
