# AWS Lambda Layer — Python 3.11 / 3.12

A lightweight Lambda layer bundling third-party pip packages and custom
Python modules into a single ZIP, ready to attach to any Lambda function.

---

## 📂 Project Structure

```
.
├── README.md
├── requirements.txt          # pip packages to bundle
├── python/
│   ├── utils/
│   │   ├── logger.py         # get_logger() helper
│   │   └── http.py           # get_json() / post_json() helpers
│   └── models/
│       └── user.py           # User dataclass
├── upload_direct.sh          # Upload ZIP < 50 MB directly to Lambda
└── upload_via_s3.sh          # Upload ZIP > 50 MB via S3
```

Inside the ZIP Lambda receives:
```
my-layer-small.zip
└── python/                   ← Lambda adds this to sys.path automatically
    ├── requests/
    ├── dotenv/
    ├── utils/
    │   ├── logger.py
    │   └── http.py
    └── models/
        └── user.py
```

---

## ⚙️ Prerequisites

- Python 3.11 or 3.12
- AWS CLI configured (`aws configure`)
- pip

---

## 🔨 Build the Layer ZIP

```bash
# 1. Install pip packages (Linux-compatible wheels, no boto3 — pre-installed in Lambda)
pip install \
  --platform manylinux2014_x86_64 \
  --target "./build/python" \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --upgrade \
  -r requirements.txt

# 2. Copy your custom modules
cp -r python/utils  ./build/python/
cp -r python/models ./build/python/

# 3. Zip
cd build && zip -r "../my-layer-small.zip" python/ && cd ..
```

> **Tip:** Use `--platform manylinux2014_x86_64` so pip downloads Linux-compatible
> wheels even if you're building on macOS or Windows.

---

## 🚀 Upload & Publish

### Option A — Direct upload (ZIP under 50 MB)

```bash
chmod +x upload_direct.sh
./upload_direct.sh
```

What it does:
```bash
aws lambda publish-layer-version \
  --layer-name "my-lambda-layer" \
  --zip-file fileb://my-layer-small.zip \
  --compatible-runtimes python3.11 python3.12
```

### Option B — Via S3 (ZIP over 50 MB)

1. Edit `upload_via_s3.sh` and set your bucket name:
   ```bash
   S3_BUCKET="your-deployment-bucket"   # ← change this
   ```

2. Run it:
   ```bash
   chmod +x upload_via_s3.sh
   ./upload_via_s3.sh
   ```

What it does:
```bash
# Step 1 — push to S3
aws s3 cp my-layer-large.zip s3://your-bucket/lambda-layers/

# Step 2 — publish referencing S3
aws lambda publish-layer-version \
  --layer-name "my-lambda-layer" \
  --content S3Bucket=your-bucket,S3Key=lambda-layers/my-layer-large.zip \
  --compatible-runtimes python3.11 python3.12
```

Both scripts print the Layer ARN on success.

---

## 🔗 Attach the Layer to a Function

```bash
aws lambda update-function-configuration \
  --function-name YOUR_FUNCTION_NAME \
  --layers arn:aws:lambda:us-east-1:123456789012:layer:my-lambda-layer:1
```

Or in the AWS Console: **Lambda → Your Function → Layers → Add a layer → Specify an ARN**.

---

## 📦 Using the Layer in Your Lambda Function

```python
# lambda_function.py  (your function code — NOT inside the layer)

from utils.logger import get_logger
from utils.http   import get_json
from models.user  import User

logger = get_logger(__name__)

def handler(event, context):
    logger.info("invoked")

    user = User(id="u1", email="alice@example.com", name="Alice", role="admin")
    data = get_json("https://jsonplaceholder.typicode.com/todos/1")

    return {
        "statusCode": 200,
        "body": {"user": user.to_dict(), "todo": data}
    }
```

---

## 📏 AWS Lambda Size Limits

| Scenario                        | Limit    |
|---------------------------------|----------|
| ZIP — direct upload             | 50 MB    |
| ZIP — via S3                    | no limit |
| Unzipped layer size             | 250 MB   |
| Function + all layers combined  | 250 MB   |
| Max layers per function         | 5        |
| Container image (escape hatch)  | 10 GB    |

---

## ❌ What NOT to Bundle

These are **already available** in the Lambda runtime — bundling them wastes space:

| Package              | Pre-installed |
|----------------------|---------------|
| `boto3` / `botocore` | ✅ Yes        |
| `json`, `os`, `re`   | ✅ stdlib     |
| `requests`, `pandas` | ❌ Bundle it  |
| Your `.py` modules   | ❌ Bundle it  |

---

## 🔄 Updating the Layer

Every publish creates a new **immutable version** (`:1`, `:2`, …).  
To update, rebuild the ZIP and re-run the upload script — then update your
function to point at the new ARN version.

---

## 🐳 When to Use a Container Instead

If your unzipped dependencies exceed **250 MB** (e.g. numpy + pandas + scipy +
scikit-learn), switch to a Lambda container image:

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ${LAMBDA_TASK_ROOT}/
CMD ["lambda_function.handler"]
```

Container images support up to **10 GB**.
