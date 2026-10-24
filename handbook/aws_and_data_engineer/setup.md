# One-Time Mac Setup

Install and verify the Mac that will host Docker, LocalStack, and Jupyter. Your other computer needs only a browser.
After these steps, continue to [remote Jupyter setup](jupyter-lan-setup.md).

## Step 1: Install Docker Desktop

Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) for your chip type, open it,
and wait for the engine to be ready. Installing only `brew install docker` provides a client, not the Docker engine.

```bash
docker info
docker compose version
```

## Step 2: Install Python, lstk, And AWS CLI

With Homebrew available, run in Mac Terminal:

```bash
brew install python@3.11 localstack/tap/lstk awscli
mkdir -p ~/my-aws-project
cd ~/my-aws-project
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install boto3 pandas requests
lstk --version
aws --version
```

Use this project directory and virtual environment throughout the labs. Jupyter installation and kernel registration
are covered once in [the notebook guide](jupyter-lan-setup.md#2-install-jupyter-in-the-macs-lab-environment).

## Step 3: Start LocalStack

```bash
lstk login
lstk start --type aws
lstk setup aws
lstk status
lstk aws s3api list-buckets
```

Current AWS emulator releases need a LocalStack account and suitable license; a real AWS account is unnecessary for
these local exercises. `lstk` manages the background Docker container. `lstk aws` needs the installed AWS CLI;
`lstk setup aws` creates its local profile. See [container configuration](localstack-docker-setup.md) if you prefer
Compose, need persistence, or encounter service/license errors.

## Step 4: Test S3 With Boto3

Run this in your activated environment, or save it as `test_setup.py` and run `python test_setup.py`:

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)
bucket = "test-bucket"
if bucket not in {b["Name"] for b in s3.list_buckets()["Buckets"]}:
    s3.create_bucket(Bucket=bucket)
s3.put_object(Bucket=bucket, Key="test-file.txt", Body=b"Hello from LocalStack!")
print(s3.get_object(Bucket=bucket, Key="test-file.txt")["Body"].read().decode())
```

Expected output: `Hello from LocalStack!`. This checks S3 connectivity only, not every service.

## Step 5: Save The Local Python Environment

Create this file in `~/my-aws-project` once. Its values are dummy credentials, not a LocalStack license token:

```bash
cat > localstack.env <<'EOF'
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566
unset AWS_SESSION_TOKEN AWS_PROFILE
EOF
source localstack.env
mkdir -p notebooks data/input data/output scripts
```

Source `localstack.env` in the Mac terminal before launching Jupyter so kernels inherit the settings. A separate
`lstk aws` command does not configure an existing Python process. Keep this local-lab environment separate from real
AWS sessions. Compose's token `.env` file serves a different purpose; do not put a license token in this file.

## Step 6: Start The Remote Notebook Workflow

Follow [Jupyter on the Mac, browser on another computer](jupyter-lan-setup.md) for password setup, LAN access, notebook
cells, and daily start/stop commands. Keep `http://localhost:4566` inside notebooks because their Python runs on the Mac.
For Docker issues use [container troubleshooting](localstack-docker-setup.md#daily-workflow-and-troubleshooting);
for connection/kernel issues use [Jupyter troubleshooting](jupyter-lan-setup.md#10-troubleshooting).
