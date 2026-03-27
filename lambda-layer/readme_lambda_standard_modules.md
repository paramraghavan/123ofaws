# AWS Lambda: Standard Modules & Pre-installed Packages

Complete reference of what's **already included** in AWS Lambda runtimes. Don't bundle these in your layer!

---

## 📦 Python Standard Library (All Versions)

These are **always available** in Python 3.11, 3.12, etc. Do NOT include in your layer.

### Core & Utilities
```
__future__              # Future imports
__main__                # Entry point
abc                     # Abstract base classes
atexit                  # Exit handlers
ast                     # Abstract syntax trees
asyncio                 # Async/await framework
base64                  # Base64 encoding
bisect                  # Binary search
builtins                # Built-in objects
calendar                # Calendar operations
cgi                     # CGI utilities
cgitb                   # CGI traceback
chunk                   # RIFF chunk reading
cmath                   # Complex math
code                    # Code object utilities
codecs                  # Codec registry
codeop                  # Code operation utilities
collections             # Specialized containers (Counter, defaultdict, etc.)
colorsys                # Color conversions
compileall              # Compile files
concurrent.futures      # Concurrent execution (ThreadPoolExecutor, etc.)
configparser            # Config file parser
contextlib              # Context managers
contextvars             # Context variables
copy                    # Shallow & deep copy
copyreg                 # Pickle support
csv                     # CSV reading/writing
ctypes                  # C library interface
curses                  # Terminal control
dataclasses             # Data classes decorator
datetime                # Date & time
dbm                     # Database interface
decimal                 # Decimal floating point
difflib                 # Diff algorithms
dis                     # Bytecode disassembler
doctest                 # Docstring test framework
dummy_thread            # Thread interface
email                   # Email parsing
encodings               # Codecs & encodings
enum                    # Enumeration support
errno                   # Error codes
faulthandler            # Fault handler
fcntl                   # OS file controls
filecmp                 # File comparison
fileinput               # Sequential file processing
fnmatch                 # Unix filename matching
fractions               # Rational numbers
ftplib                  # FTP protocol
functools               # Function utilities (lru_cache, partial, etc.)
gc                      # Garbage collection
getopt                  # Command-line parsing (legacy)
getpass                 # Secure password input
gettext                 # Internationalization
glob                    # Pathname expansion
graphlib                # Graph operations
grp                     # Unix group database
gzip                    # Gzip compression
hashlib                 # Cryptographic hashing
heapq                   # Heap queue algorithm
hmac                    # HMAC authentication
html                    # HTML processing
http                    # HTTP protocols
idlelib                 # IDLE utilities
imaplib                 # IMAP4 protocol
imghdr                  # Image type detection
imp                     # Import utilities
importlib               # Import machinery
inspect                 # Introspection
io                      # I/O operations
ipaddress               # IP address utilities
itertools               # Iterator tools
json                    # JSON encoding/decoding ⭐ VERY COMMON
keyword                 # Keyword utilities
lib2to3                 # 2to3 library
linecache               # Line caching
locale                  # Localization
logging                 # Logging framework ⭐ VERY COMMON
lzma                    # LZMA compression
mailbox                 # Mailbox formats
mailcap                 # Mailcap file support
marshal                 # Serialization
math                    # Math functions
mimetypes               # MIME type handling
mmap                    # Memory mapping
modulefinder            # Module finder
msilib                  # Windows MSI support
msvcrt                  # Windows utilities
multiprocessing         # Process-based parallelism
netrc                   # Netrc file parsing
nis                     # Unix NIS interface
nntplib                 # NNTP protocol
numbers                 # Numeric abstract base classes
operator                # Operator utilities
optparse                # Command-line parsing (legacy)
os                      # OS utilities ⭐ VERY COMMON
ossaudiodev             # Audio device interface
parser                  # Python parse trees
pathlib                 # Object-oriented paths
pdb                     # Debugger
pickle                  # Serialization
pickletools            # Pickle tools
pipes                   # Shell pipeline interface
pkgutil                 # Package utilities
plistlib                # Plist file format
poplib                  # POP protocol
posix                   # POSIX utilities
posixpath                # POSIX path utilities
pprint                  # Pretty printing
profile                 # Profiler
pstats                  # Profile statistics
pty                     # Pseudo-terminal utilities
pwd                     # Unix password database
py_compile              # Compile Python files
pyclbr                  # Class browser
pydoc                   # Documentation
queue                   # Thread-safe queues
quopri                  # Quoted-printable codec
random                  # Random number generation
re                      # Regular expressions ⭐ VERY COMMON
readline                # Line editing
reprlib                 # Alternative repr
resource                # Resource usage
rlcompleter             # Readline completion
runpy                   # Locate & run Python modules
sched                   # Event scheduler
secrets                 # Secure random values
select                  # Waiting for I/O
selectors               # I/O multiplexing
shelve                  # Persistent object storage
shlex                   # Shell-like syntax
shutil                  # File operations ⭐ COMMON
signal                  # Asynchronous signals
site                    # Site customization
smtpd                   # SMTP server
smtplib                 # SMTP protocol
sndhdr                  # Sound file headers
socket                  # Socket interface ⭐ COMMON
socketserver            # Socket server
spwd                    # Unix shadow password
sqlite3                 # SQLite database ⭐ USEFUL
ssl                     # SSL/TLS wrapper
stat                    # Stat constants
statistics              # Statistical calculations
string                  # String operations
stringprep              # String preparation
struct                  # Binary data handling
subprocess              # Subprocess management ⭐ COMMON
sunau                   # Sun audio files
symbol                  # Python grammar symbols
symtable                # Symbol table generation
sys                     # System utilities ⭐ VERY COMMON
sysconfig               # System configuration
syslog                  # Unix syslog interface
tabnanny                # Indentation checker
tarfile                 # TAR file handling
telnetlib               # Telnet protocol
tempfile                # Temporary files & dirs
termios                 # POSIX terminal control
test                    # Regression tests
textwrap                # Text wrapping
threading               # Thread-based parallelism
time                    # Time access & conversions ⭐ VERY COMMON
timeit                  # Measure execution time
tkinter                 # Tk GUI toolkit
token                   # Token constants
tokenize                # Tokenize Python source
tomllib                 # TOML parsing
trace                   # Trace execution
traceback               # Print stack traces ⭐ USEFUL
tracemalloc             # Memory allocation tracing
trio                    # Async I/O
tty                     # Terminal utilities
turtle                  # Graphics
turtledemo              # Turtle demo
types                   # Type utilities
typing                  # Type hints ⭐ USEFUL
typing_extensions       # Type hints extensions
unicodedata             # Unicode database
unittest                # Unit testing
urllib                  # URL opening ⭐ VERY COMMON
uu                      # UUencode
uuid                    # UUID generation
venv                    # Virtual environments
warnings                # Warning control
wave                    # WAV files
weakref                 # Weak references
webbrowser              # Web browser controller
wsgiref                 # WSGI utilities
xdrlib                  # XDR encoding
xml                     # XML processing
xmlrpc                  # XML-RPC protocol
zipapp                  # Zip application support
zipfile                 # ZIP archive handling ⭐ USEFUL
zipimport                # Import from ZIP
zlib                    # Compression ⭐ USEFUL
```

---

## 🔧 AWS SDK: Pre-installed in Lambda

These are **always available** in AWS Lambda. Do NOT include in your layer.

### Boto3 & Friends

```
boto3                   # AWS SDK for Python ⭐ PRIMARY SDK
botocore                # Boto3 dependency
s3transfer              # S3 transfer utility
jmespath                # JSON query language
python-dateutil         # Date utilities
urllib3                 # HTTP client (boto3 dependency)
```

### Usage

```python
import boto3

# Always available - no installation needed
s3 = boto3.client('s3')
ec2 = boto3.resource('ec2')
lambda_client = boto3.client('lambda')
ssm = boto3.client('ssm')

# Even in isolated layers, you can do:
from botocore.exceptions import ClientError
```

### Version in Lambda

The specific versions depend on the Lambda runtime version:

**Python 3.12 (as of 2024):**
- boto3: 1.26.x - 1.28.x
- botocore: 1.29.x - 1.31.x

Check your runtime:
```bash
aws lambda get-function --function-name my-func --query 'Configuration.Runtime'
```

---

## ❌ What NOT to Bundle

### Already Available (Waste of Space)

```
boto3              # Pre-installed ❌
botocore           # Pre-installed ❌
json               # Standard library ❌
os                 # Standard library ❌
re                 # Standard library ❌
sys                # Standard library ❌
logging            # Standard library ❌
datetime           # Standard library ❌
urllib             # Standard library ❌
```

### Do NOT Bundle These (will cause errors)

```
pip                # Installation tool ❌
setuptools         # Build tool ❌
wheel              # Packaging tool ❌
virtualenv         # Virtual env ❌
```

---

## ✅ What TO Bundle

### Most Common 3rd Party Packages

```
requests            ✅ HTTP library (not in Lambda)
pandas              ✅ Data manipulation
numpy               ✅ Numerical computing
scipy               ✅ Scientific Python
scikit-learn        ✅ Machine learning
tensorflow          ✅ Deep learning (large!)
torch               ✅ PyTorch (very large!)
sqlalchemy          ✅ SQL toolkit
psycopg2            ✅ PostgreSQL driver
pymongo             ✅ MongoDB driver
redis               ✅ Redis client
elasticsearch       ✅ Elasticsearch client
python-dotenv       ✅ Environment variables
cryptography        ✅ Encryption
pydantic            ✅ Data validation
fastapi             ✅ Web framework
flask               ✅ Web framework
django              ✅ Web framework
lxml                ✅ XML processing
openpyxl            ✅ Excel files
pillow              ✅ Image processing
beautifulsoup4      ✅ HTML parsing
```

---

## 📊 Pre-installed Package Versions

### Lambda Python 3.12

```
boto3               1.28.x
botocore            1.31.x
s3transfer          0.6.x
jmespath            1.0.x
python-dateutil     2.8.x
six                 1.16.x
urllib3             1.26.x
```

### Lambda Python 3.11

```
boto3               1.26.x
botocore            1.29.x
s3transfer          0.6.x
jmespath            1.0.x
python-dateutil     2.8.x
six                 1.16.x
urllib3             1.26.x
```

### How to Check in Your Function

```python
import sys
import boto3
import json

def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'python_version': sys.version,
            'boto3_version': boto3.__version__,
            'sys_path': sys.path[:3]  # First 3 entries
        }, indent=2)
    }
```

Output:
```json
{
  "python_version": "3.12.0 (main, ...) [GCC ...]",
  "boto3_version": "1.28.85",
  "sys_path": [
    "/var/task",
    "/opt/python",
    "/var/runtime"
  ]
}
```

---

## 🗺️ Standard Library Reference by Category

### File & OS Operations
```
os                  # Directory & file operations
pathlib             # Path objects
glob                # Filename matching
shutil              # File operations
tempfile            # Temporary files
stat                # File status
fcntl               # File control
```

### Data Processing
```
json                # JSON parsing ⭐
csv                 # CSV files ⭐
pickle              # Object serialization
struct              # Binary data
base64              # Base64 encoding
```

### Networking
```
socket              # Low-level networking
http                # HTTP protocol
urllib              # URL opening ⭐
ftplib              # FTP protocol
smtplib             # SMTP protocol
poplib              # POP protocol
imaplib             # IMAP protocol
```

### Compression & Archives
```
zipfile             # ZIP files ⭐
gzip                # Gzip compression
tarfile             # TAR files
bz2                 # Bzip2 compression
lzma                # LZMA compression
```

### Cryptography
```
hashlib             # Hashing (MD5, SHA) ⭐
hmac                # HMAC authentication ⭐
secrets             # Secure random values ⭐
ssl                 # SSL/TLS
```

### Date & Time
```
datetime            # Date/time objects ⭐
time                # Time functions ⭐
calendar            # Calendar operations
timeit              # Performance timing
```

### Logging & Debugging
```
logging             # Logging ⭐
traceback           # Stack traces ⭐
pdb                 # Debugger
profile             # Profiling
```

### Text Processing
```
re                  # Regular expressions ⭐
string              # String constants ⭐
textwrap            # Text wrapping
difflib             # Diff algorithms
```

### Math & Science
```
math                # Math functions ⭐
random              # Random generation ⭐
statistics          # Statistical functions
decimal             # Decimal arithmetic
fractions           # Fractional numbers
cmath               # Complex math
```

### Concurrency
```
threading           # Thread-based parallelism
multiprocessing     # Process-based (limited in Lambda)
asyncio             # Async/await ⭐
concurrent.futures  # Executor interface
queue               # Thread-safe queues
```

### Database
```
sqlite3             # SQLite ⭐
dbm                 # Key-value store
shelve              # Object persistence
```

### Type Hints & Inspection
```
typing              # Type hints ⭐
inspect             # Introspection
types               # Type objects
```

### Utilities
```
functools           # Function utilities (lru_cache, partial) ⭐
itertools           # Iterator tools ⭐
operator            # Operator functions
collections         # Specialized containers ⭐
enum                # Enumerations ⭐
dataclasses         # Data classes ⭐
```

---

## 🔍 Examples: Do I Bundle This?

### Example 1: requests

```python
import requests  # ❌ NOT in Lambda

# Decision: Must be bundled in layer
# Add to requirements.txt:
# requests==2.31.0
```

### Example 2: json

```python
import json  # ✅ Already in Lambda (stdlib)

# Decision: Do NOT bundle
# Never add to requirements.txt
```

### Example 3: boto3

```python
import boto3  # ✅ Already in Lambda (AWS SDK)

# Decision: Do NOT bundle
# Never add to requirements.txt (even though it's safe)
```

### Example 4: pandas

```python
import pandas  # ❌ NOT in Lambda

# Decision: Must be bundled
# BUT: Watch size! pandas is ~100 MB unzipped
# Add to requirements.txt:
# pandas==2.0.3
```

### Example 5: logging

```python
import logging  # ✅ Already in Lambda (stdlib)

# Decision: Do NOT bundle
# Safe to use directly
```

---

## 💡 Pro Tips

### Tip 1: Check What's Already There

```bash
# In your Lambda function
python -c "import sys; print('\n'.join(sys.path))"
```

Output shows what's available.

### Tip 2: Don't Re-bundle boto3

```bash
# requirements.txt - BAD (wastes space)
boto3==1.28.0
botocore==1.31.0

# requirements.txt - GOOD (explicit about why)
requests==2.31.0
# boto3 is pre-installed in Lambda, don't bundle
```

### Tip 3: Use Latest Stdlib Features

```python
# Python 3.11+ supports:
match/case      # Pattern matching
|               # Union types in annotations
...             # Walrus operator :=
tomllib         # TOML parsing (no install needed)
```

### Tip 4: Document Dependencies

```python
"""
Dependencies:
- Standard Library: json, os, logging, datetime
- AWS SDK: boto3 (pre-installed)
- External: requests (in layer), python-dotenv (in layer)
"""
```

### Tip 5: Keep requirements.txt Minimal

```
# ❌ Bad (includes unnecessary packages)
requests==2.31.0
urllib3==1.26.0      # Already a dependency of requests
certifi==2023.7.22   # Already a dependency of requests
boto3==1.28.0        # Pre-installed in Lambda

# ✅ Good (only top-level packages)
requests==2.31.0
python-dotenv==1.0.0
```

---

## 📚 Reference Links

- [Python Standard Library](https://docs.python.org/3.12/library/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Lambda Runtime Environment](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [Lambda Supported Runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)

---

## 🧪 Quick Test

Copy this to your Lambda function to see what's available:

```python
import json
import sys

def handler(event, context):
    """Show what's available in this Lambda runtime."""

    try:
        import boto3
        boto3_version = boto3.__version__
    except ImportError:
        boto3_version = "Not available"

    try:
        import requests
        requests_version = requests.__version__
    except ImportError:
        requests_version = "Not available"

    return {
        'statusCode': 200,
        'body': json.dumps({
            'python_version': sys.version.split()[0],
            'boto3': boto3_version,
            'requests': requests_version,
            'sys_path': sys.path[:3],
            'stdlib_available': [
                'json', 'os', 're', 'logging', 'datetime', 'sqlite3'
            ]
        }, indent=2)
    }
```

Invoke and check what's pre-installed!

---

## Summary Table

| Module/Package | Bundled in Lambda? | Category | Notes |
|---|---|---|---|
| json | ✅ Yes | stdlib | Use directly |
| logging | ✅ Yes | stdlib | Use directly |
| os | ✅ Yes | stdlib | Use directly |
| re | ✅ Yes | stdlib | Use directly |
| boto3 | ✅ Yes | AWS SDK | Use directly |
| botocore | ✅ Yes | AWS SDK | Use directly |
| requests | ❌ No | External | Bundle in layer |
| pandas | ❌ No | External | Bundle in layer |
| numpy | ❌ No | External | Bundle in layer |
| sqlite3 | ✅ Yes | stdlib | Use directly |
| urllib | ✅ Yes | stdlib | Use directly |
| asyncio | ✅ Yes | stdlib | Use directly |

---

**Always remember:** More space in the layer = Slower cold starts. Bundle only what you need!
