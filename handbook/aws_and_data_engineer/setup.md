# Setup: Local AWS Development Environment

**Time**: 30 minutes
**Goal**: Get LocalStack, Python, and boto3 working on your Mac/Windows

---

## What You're Installing

```
Your Development Environment:

┌─────────────────────────────────────────────────────────┐
│                  YOUR LAPTOP                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  Python 3.9+ │  │   Docker     │  │   Code      │  │
│  │              │  │              │  │   Editor    │  │
│  │ ├─ boto3     │  │ ┌──────────┐ │  │ (VS Code)   │  │
│  │ ├─ pandas    │  │ │LocalStack│ │  │             │  │
│  │ ├─ requests  │  │ │┌───────┐ │ │  └─────────────┘  │
│  │ └─ json      │  │ ││ S3    │ │ │                   │
│  │              │  │ ││ Lambda│ │ │                   │
│  │              │  │ ││ SQS   │ │ │                   │
│  │              │  │ │└───────┘ │ │                   │
│  │              │  │ └──────────┘ │                   │
│  └──────────────┘  └──────────────┘                   │
│                                                         │
│  Terminal (bash/zsh)                                   │
│  ├─ Run docker commands                               │
│  ├─ Run Python scripts                                │
│  └─ Use AWS CLI                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: Install Docker

### macOS

```bash
# Install Docker via Homebrew
brew install docker

# Start Docker daemon
# Either:
# Option A: Open "Docker" app from Applications
# Option B: Use Colima (lightweight alternative)
brew install colima
colima start

# Verify Docker works
docker --version
# Output: Docker version 24.0.0
```

### Windows

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and restart computer
3. Open PowerShell and verify:

```powershell
docker --version
# Output: Docker version 24.0.0
```

---

## Step 2: Install Python & boto3

### macOS

```bash
# Check Python version
python3 --version
# Need: 3.9 or higher

# Create project folder
mkdir -p ~/my-aws-project
cd ~/my-aws-project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install AWS SDK
pip install boto3

# Install useful tools
pip install pandas requests

# Verify installation
python3 << 'EOF'
import boto3
print(f"✓ boto3 version: {boto3.__version__}")
EOF
```

### Windows (PowerShell)

```powershell
# Check Python version
python --version
# Need: 3.9 or higher

# Create project folder
mkdir $env:USERPROFILE\my-aws-project
cd $env:USERPROFILE\my-aws-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install AWS SDK
pip install boto3 pandas requests

# Verify installation
python << 'EOF'
import boto3
print(f"✓ boto3 version: {boto3.__version__}")
EOF
```

---

## Step 3: Start LocalStack

### Terminal 1: Start LocalStack Container

```bash
# This downloads and starts LocalStack
docker run -it -p 4566:4566 localstack/localstack

# Wait for output:
# ✓ LocalStack is running
# ✓ Ready to handle requests on http://localhost:4566
```

**Keep this terminal running!** (Don't close it)

---

## Step 4: Test Everything Works

### Terminal 2: Create Test Script

```bash
# Open new terminal (keep Terminal 1 running)

# Navigate to project folder
cd ~/my-aws-project
source venv/bin/activate  # Activate Python environment

# Create test script
cat > test_setup.py << 'EOF'
import boto3

print("Testing LocalStack Connection...")
print("=" * 60)

# Connect to LocalStack
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

print("✓ Connected to LocalStack")

# Create a test bucket
bucket_name = "test-bucket"
s3.create_bucket(Bucket=bucket_name)
print(f"✓ Created S3 bucket: {bucket_name}")

# List buckets
response = s3.list_buckets()
buckets = [b['Name'] for b in response['Buckets']]
print(f"✓ Buckets in LocalStack: {buckets}")

# Upload a test file
s3.put_object(
    Bucket=bucket_name,
    Key="test-file.txt",
    Body=b"Hello from LocalStack!"
)
print(f"✓ Uploaded test file")

# Download the file
obj = s3.get_object(Bucket=bucket_name, Key="test-file.txt")
content = obj['Body'].read().decode()
print(f"✓ Downloaded file content: {content}")

print("=" * 60)
print("SUCCESS! LocalStack is fully working! 🎉")
EOF

# Run test
python3 test_setup.py
```

**Expected output:**
```
Testing LocalStack Connection...
============================================================
✓ Connected to LocalStack
✓ Created S3 bucket: test-bucket
✓ Buckets in LocalStack: ['test-bucket']
✓ Uploaded test file
✓ Downloaded file content: Hello from LocalStack!
============================================================
SUCCESS! LocalStack is fully working! 🎉
```

---

## Step 5: Install AWS CLI (Optional but Recommended)

```bash
# Install AWS CLI
pip install awscli-local

# Configure AWS CLI for LocalStack
aws configure --profile localstack

# When prompted:
# AWS Access Key ID: test
# AWS Secret Access Key: test
# Default region: us-east-1
# Default output format: json

# Test AWS CLI with LocalStack
awslocal --profile localstack s3 ls

# Should show: 2024-10-21 10:30:00 test-bucket
```

---

## Project Structure

```
~/my-aws-project/
├─ venv/                          ← Python virtual environment
│  └─ (auto-generated)
│
├─ test_setup.py                  ← Your test script
│
├─ data/                          ← Data files (create folder)
│  ├─ sample.csv
│  └─ input/
│
├─ scripts/                       ← Your Python scripts (create folder)
│  ├─ lambda_validator.py
│  ├─ lambda_processor.py
│  └─ setup_resources.py
│
└─ README.md                      ← Project notes
```

**Create these folders:**

```bash
mkdir -p data/input data/output
mkdir -p scripts
```

---

## Verify Everything

```
Your setup is complete when:

┌────────────────────────────────────────┐
│ ✓ Docker running (Terminal 1)          │
│   docker run... localstack/localstack  │
│                                        │
│ ✓ Python virtual environment active    │
│   source venv/bin/activate             │
│                                        │
│ ✓ boto3 installed and working          │
│   import boto3 works                   │
│                                        │
│ ✓ LocalStack test passes               │
│   S3 bucket created successfully       │
│                                        │
│ ✓ AWS CLI works (optional)             │
│   awslocal s3 ls works                 │
│                                        │
│ ═════════════════════════════════════ │
│         YOU'RE READY! 🚀               │
└────────────────────────────────────────┘
```

---

## Common Issues & Fixes

### Docker Won't Start

```
Error: Cannot connect to Docker daemon

Solution:
1. Make sure Docker Desktop is running
2. On Mac: Open Applications > Docker.app
3. On Windows: Open Docker Desktop from Start menu
4. Wait 30 seconds for Docker to start
```

### Port 4566 Already in Use

```
Error: bind: address already in use

Solution:
# Find what's using port 4566
lsof -i :4566

# Kill that process
kill -9 <PID>

# Or use a different port
docker run -it -p 4567:4566 localstack/localstack
# Then use endpoint_url="http://localhost:4567"
```

### boto3 Import Error

```
Error: ModuleNotFoundError: No module named 'boto3'

Solution:
# Make sure venv is activated
source venv/bin/activate

# Reinstall boto3
pip install boto3 --force-reinstall
```

### LocalStack Container Exits

```
Error: Container exited

Solution:
docker run -it -p 4566:4566 localstack/localstack

# Add -d to run in background
docker run -d -p 4566:4566 localstack/localstack

# View logs
docker logs <container_id>
```

---

## Daily Workflow

```
Every time you work on AWS projects:

┌──────────────────────────────────────────┐
│ Terminal 1: Start LocalStack             │
│ $ docker run -it -p 4566:4566 \          │
│   localstack/localstack                  │
│                                          │
│ [Keep this running]                      │
└──────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────┐
│ Terminal 2: Work on your code            │
│ $ cd ~/my-aws-project                    │
│ $ source venv/bin/activate               │
│ $ python3 my_script.py                   │
│                                          │
│ [Your scripts run here]                  │
└──────────────────────────────────────────┘
                    ↓
                 Done?
                    ↓
         Terminal 2: Ctrl+C (quit script)
         Terminal 1: Ctrl+C (stop LocalStack)
```

---

## You're Ready!

```
┌─────────────────────────────────────────┐
│  ✓ Docker installed and running         │
│  ✓ Python 3.9+ with boto3              │
│  ✓ LocalStack working locally            │
│  ✓ Test script passes                   │
│                                         │
│  Next: Read learn.md                    │
│  ✓ S3 fundamentals                      │
│  ✓ Lambda, SNS, SQS                     │
│  ✓ Build your first pipeline            │
└─────────────────────────────────────────┘
```

→ **Next: Open learn.md**
