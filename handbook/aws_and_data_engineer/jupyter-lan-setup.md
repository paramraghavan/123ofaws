# Jupyter On Your Mac, Browser On Another Computer

Use this workflow when Docker Desktop, LocalStack, Python, and optionally Spark run on your Mac, while you do your
work in a browser on another computer on the same trusted local network. The other computer needs only a browser.
Complete [setup.md](setup.md) Steps 1–5 on the Mac first.

## 1. Understand Where Everything Runs

```text
Other computer                         Mac
Browser                                JupyterLab server + Python kernel
    |                                      |                 |
    +-- http://MAC_IP:8888/lab ------------+                 |
                                           +-- localhost:4566 -> Docker LocalStack
                                           +-- local Spark -> Mac CPU/RAM
                                           +-- files -> ~/my-aws-project
```

| Item | Where it runs or is stored |
|---|---|
| Docker Desktop and LocalStack image/container | Mac |
| Jupyter server, notebook kernel, Boto3, and local Spark | Mac |
| Notebook files, CSV files, and scripts | Mac project folder |
| Notebook page and rendered output | Browser on the other computer |
| LocalStack URL inside notebook Python | `http://localhost:4566` |
| Jupyter URL in the other computer's browser | `http://MAC_IP:8888/lab` |

The browser does not run your Python. Even when you type code from another computer, the notebook's `localhost`,
`Path.home()`, shell commands, and filesystem paths refer to the Mac. Do not change the notebook's LocalStack endpoint
to the browser computer's IP. LocalStack port 4566 does not need to be accessible from that computer.

## 2. Install Jupyter In The Mac's Lab Environment

Run in **Terminal on the Mac**:

```bash
cd ~/my-aws-project
source venv/bin/activate
python -m pip install jupyterlab ipykernel
python -m ipykernel install --user --name aws-lab --display-name "AWS Lab (Mac)"
mkdir -p notebooks data/input data/output
jupyter kernelspec list
```

Registering the kernel makes this specific virtual environment selectable in Jupyter. If you later move or recreate
`venv`, register it again. See the [IPython kernel installation guide](https://ipython.readthedocs.io/en/stable/install/kernel_install.html).

Set a login password interactively on the Mac; do not put it in a notebook or command-line argument:

```bash
jupyter server password
```

This stores a password hash in Jupyter's configuration. Keep authentication enabled. Password setup is documented in
[Jupyter Server security](https://jupyter-server.readthedocs.io/en/stable/operators/security.html).

## 3. Find The Mac's Local Network Address

On the Mac, open **System Settings → Network → your active Wi-Fi/Ethernet connection → Details → TCP/IP** and note the
IPv4 address, for example `192.168.1.25`. The exact labels vary with macOS version.

For a quick terminal check, try:

```bash
ipconfig getifaddr en0
```

If that is empty or shows the wrong interface, use the address for the active connection in System Settings. Do not use
`127.0.0.1` or a Docker bridge address. An optional DHCP reservation in your router keeps the Mac's address stable.

## 4. Start LocalStack And Jupyter On The Mac

Use **one** LocalStack startup method from [the Docker guide](localstack-docker-setup.md). For the default lstk workflow:

```bash
cd ~/my-aws-project
source venv/bin/activate
lstk start --type aws
lstk aws s3api list-buckets

# File created in setup Step 5; inherited by new notebook kernels.
source localstack.env

jupyter lab \
  --ServerApp.ip=0.0.0.0 \
  --ServerApp.port=8888 \
  --ServerApp.port_retries=0 \
  --ServerApp.open_browser=False \
  --ServerApp.root_dir="$HOME/my-aws-project"
```

`0.0.0.0` tells Jupyter to listen on the Mac's network interfaces; it is not the address to type in your browser.
`port_retries=0` makes a port conflict visible instead of silently switching to 8889. The root directory limits the file
browser's starting area; it is not an operating-system sandbox. The logged-in notebook user can execute code as your
Mac account. See [Jupyter Server options](https://jupyter-server.readthedocs.io/en/stable/other/full-config.html).

Leave the Jupyter terminal running. If you use Compose for LocalStack, start that container with
`docker compose up -d --wait` from the Compose project directory instead of `lstk start`; keep the same notebook endpoint at port 4566.

For direct HTTP access, use a trusted home/lab network: HTTP does not encrypt your password, code, or output. Do not
forward port 8888 from your internet router. Use the SSH option below if you want an encrypted connection. Keep the Mac
awake and powered during work; closing a laptop lid can interrupt the server and jobs. See
[Apple's sleep settings](https://support.apple.com/guide/mac-help/set-sleep-and-wake-settings-mchle41a6ccd/mac).

## 5. Open Jupyter From The Other Computer

1. Connect the other computer to the same trusted LAN as the Mac (avoid guest Wi-Fi with client isolation).
2. Open `http://192.168.1.25:8888/lab`, replacing the example with the Mac's address.
3. Enter the password you set on the Mac.
4. Open `notebooks/` and create a notebook with the **AWS Lab (Mac)** kernel. Save it as `localstack_practice.ipynb`.

On the Mac, allow the lab Python/Jupyter process through the macOS firewall if prompted. If needed, review **System
Settings → Network → Firewall → Options**; allow the relevant application rather than turning the firewall off.
Closing the browser tab does not stop kernels or the server.

## 6. Run Your First Notebook Cells

**Cell 1 — verify the selected kernel and working folder:**

```python
import sys
from pathlib import Path

LAB_DIR = Path.home() / "my-aws-project"
LAB_DIR.mkdir(parents=True, exist_ok=True)
print("Python on the Mac:", sys.executable)
print("Project on the Mac:", LAB_DIR)
```

Python should come from `my-aws-project/venv/bin/python`. If it does not, use **Kernel → Change Kernel → AWS Lab (Mac)**.

**Cell 2 — set the notebook's working directory:**

```ipython
%cd ~/my-aws-project
```

This makes `data/input/...`, script imports, and pipeline output paths resolve consistently. `%cd` persists in the
kernel; `!cd ...` changes only a temporary child shell.

**Cell 3 — connect explicitly to LocalStack and create a small S3 object:**

```python
import boto3
from botocore.config import Config

local_session = boto3.Session(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)
s3 = local_session.client(
    "s3",
    endpoint_url="http://localhost:4566",
    config=Config(s3={"addressing_style": "path"}),
)

bucket = "notebook-lab"
if bucket not in {b["Name"] for b in s3.list_buckets()["Buckets"]}:
    s3.create_bucket(Bucket=bucket)
s3.put_object(Bucket=bucket, Key="hello.txt", Body=b"Hello from the Mac notebook kernel!")
print(s3.get_object(Bucket=bucket, Key="hello.txt")["Body"].read().decode())
```

Expected output: `Hello from the Mac notebook kernel!`. This tests S3 only. Other clients in the learning guide rely on
the `localstack.env` environment inherited when Jupyter starts. If you change credentials or endpoints after clients are created, restart the
kernel and rerun setup cells before importing the handler files.

**Cell 4 — run the local AWS CLI on the Mac:**

```ipython
!lstk aws s3 ls s3://notebook-lab/
```

For a Compose-managed instance use `!lstk --endpoint-url http://localhost:4566 aws s3 ls s3://notebook-lab/` instead.
These commands run on the Mac, using its installed tools. They do not install or execute anything on the browser computer.

## 7. Use The Existing Labs Entirely From Notebooks

Use [learn.md](learn.md) as the source for code. Notebook cells accept Python directly; omit the Markdown fences and
terminal heredoc wrappers such as `python3 << 'EOF'` and `EOF`.

| Guide instruction | Notebook equivalent |
|---|---|
| Run Python code | Paste it into a Python cell |
| Save a Python file | Use `%%writefile filename.py` at the start of a cell, followed by that file's code |
| Run `python filename.py` | Use `%run filename.py` |
| Run a shell command | Prefix it with `!`, or use JupyterLab's **File → New → Terminal** |
| Install a Python library | Use `%pip install package_name` in the selected kernel, then restart if needed |
| Activate a virtual environment | Select **AWS Lab (Mac)**; `!source venv/bin/activate` cannot change the running kernel |

Example file-creation cell:

```ipython
%%writefile hello_lab.py
print("This file and its output come from the Mac")
```

Then run it in a separate cell:

```ipython
%run hello_lab.py
```

For the pipeline lab, save `setup_pipeline.py`, `lambda_validator.py`, `lambda_processor.py`, and `run_pipeline.py`
using separate `%%writefile` cells with the code from `learn.md`. Create `data/input/customers.csv` with another
`%%writefile` cell using the sample CSV contents. Then run:

```ipython
%run setup_pipeline.py
%run run_pipeline.py
```

These handlers execute in the notebook on the Mac; no deployed Lambda functions are required. Keep CSV files small
for this lab. A JupyterLab terminal also runs on the Mac, but virtual-environment activation there does not change an
already running notebook kernel.

## 8. Optional: Run PySpark From The Same Remote Notebook

Install Java and Spark **on the Mac**, not on the other computer. With the lab environment activated in Mac Terminal:

```bash
brew install openjdk@17
python -m pip install "pyspark==3.5.6"
export JAVA_HOME="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
```

Set the Java environment in the terminal that starts Jupyter, and restart the Jupyter server if it was already running.
Then select **AWS Lab (Mac)** and run this before creating any Spark session:

```python
import os
import sys
from pyspark.sql import SparkSession

os.environ["PYSPARK_PYTHON"] = sys.executable
spark = (
    SparkSession.builder.appName("remote-browser-local-spark")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "2")
    .getOrCreate()
)
spark.range(5).show()
```

Spark runs with two worker threads on the Mac and shares its memory/CPU with Docker and Jupyter. Remote browser access
does not create a second compute node. For `s3a://` reads/writes, configure the matching Hadoop AWS libraries and
`spark.hadoop.fs.s3a.endpoint=http://localhost:4566` before creating the first Spark session, following the
[Mac Spark S3A setup](../../../sparksql-awsglue/help/quick101-spark/spark_quickstart/setup-mac-local-spark.md).
Call `spark.stop()` when finished. A Mac-local URL for the Spark UI will not automatically work in the other browser;
use notebook output or a separate tunnel if you need the UI, rather than exposing extra ports by default.

## 9. Daily Start And Stop

- **Mac:** start Docker Desktop, then LocalStack, activate the lab environment, source `localstack.env`, and
  launch Jupyter. Keep the Mac awake.
- **Other computer:** open the Mac's Jupyter URL, select **AWS Lab (Mac)**, and run the notebook setup cells.
- **When finished:** save the notebook, stop Spark if used, shut down unused kernels, and stop Jupyter with `Ctrl+C` in
  its Mac terminal (confirm shutdown if asked). Stop LocalStack with `lstk stop`, or `docker compose down` for Compose.

The saved `.ipynb` file survives server restarts on the Mac. In-memory variables and sessions do not. LocalStack state
has its own persistence/license settings; saving a notebook does not save simulated S3 objects.

## 10. Troubleshooting

| Symptom | What to check |
|---|---|
| Page opens on Mac, not on other computer | Use the Mac's LAN IP, confirm Jupyter listens beyond `127.0.0.1`, check firewall and Wi-Fi client isolation |
| Address suddenly stops working | Check whether DHCP changed the Mac's IP or the Mac went to sleep |
| Port 8888 is busy | Inspect `jupyter server list` locally and `lsof -nP -iTCP:8888 -sTCP:LISTEN`; stop only the server you intend to replace |
| Browser connects but kernel never starts/disconnects | Check server logs and WebSocket-blocking proxies/VPNs; select the registered kernel |
| Notebook cannot import boto3/pyspark | Check `sys.executable`; select the lab kernel and install with `%pip` |
| Notebook cannot reach LocalStack | Test `lstk status` on the Mac; keep the endpoint `http://localhost:4566` |
| `lstk` is missing inside notebook | Start Jupyter from the Mac shell whose PATH includes Homebrew and `lstk` |
| Relative input files cannot be found | Run `%cd ~/my-aws-project`; remember the files must be on the Mac |
| Spark Java gateway fails | Set Java 17 in Jupyter's launch environment and restart the server/kernel |

## Optional Encrypted Access Through SSH

To keep Jupyter off the LAN and encrypt browser traffic, enable **Remote Login** for your Mac user in macOS Sharing
settings. Start Jupyter as in Step 4 but change `--ServerApp.ip=0.0.0.0` to `--ServerApp.ip=127.0.0.1`.
On the **other computer**, keep this SSH command running, replacing the user/IP:

```bash
ssh -N -L 8889:127.0.0.1:8888 your-mac-user@192.168.1.25
```

Open `http://localhost:8889/lab` on the other computer and enter the same Jupyter password. Here the browser's localhost
is a tunnel entrance; notebook Python still runs on the Mac and uses LocalStack at `localhost:4566`. Only SSH needs to
be reachable over the LAN for this alternative. Close the SSH session when done.
