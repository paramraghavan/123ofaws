# SQS to PostgreSQL Lambda (Python)

A Python Lambda function that reads loan data from an AWS SQS queue and writes it to a PostgreSQL database.


## Prerequisites

Before you begin, make sure you have:

- Python 3.11 installed on your laptop
- AWS CLI configured with your profile (`~/.aws/credentials`)
- Access to your PostgreSQL database (host, port, credentials)
- Your SQS queue URL
- AWS Console access to create Lambda functions

---

## Project Structure

```
loan-processor/
├── lambda_function.py    # Main Lambda code
├── test_local.py         # Test on your laptop
├── requirements.txt      # Python libraries needed
└── README.md             # This file
```

---

## Local Testing

### Step 1: Set Up Python Environment

Open your terminal and navigate to the project folder:

```bash
cd loan-processor
```

Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `psycopg2-binary` - PostgreSQL driver for Python
- `boto3` - AWS SDK for Python

### Step 3: Configure Test Settings

Open `test_local.py` and update these values:

```python
# Database settings
os.environ['DB_HOST'] = 'your-postgres-host.amazonaws.com'  # or 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'loans_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'your-password'

# SQS Queue (only needed for real SQS testing)
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/123456789/your-queue-name'
```

### Step 4: Run the Test

**Test with fake data first (no AWS or database needed to verify code runs):**

```bash
python test_local.py
```

By default, this runs `test_with_fake_data()` which simulates 6 loan records.

**Test with real SQS queue:**

Edit `test_local.py` and uncomment the real SQS test:

```python
if __name__ == '__main__':
    # test_with_fake_data()
    test_with_real_sqs()  # Uncomment this line
```

Then run:

```bash
python test_local.py
```

> **Note:** This uses your AWS profile from `~/.aws/credentials`. To use a specific profile, modify the boto3 client
> creation in `test_local.py`.

---

## Deployment Options

Lambda needs the `psycopg2` library to connect to PostgreSQL. Since Lambda doesn't have this pre-installed, you have two
options:

### Option A: Lambda Layer (Recommended)
> See notes [layer_notes.md](layer_notes.md)
A **Layer** is a ZIP file containing libraries that Lambda can use. This is the cleanest approach.

**Use a pre-built public layer:**
Several public psycopg2 layers are available. Search for one matching your region and Python version, or use:

```
arn:aws:lambda:us-east-1:898466741470:layer:psycopg2-py311:1
```

> **Finding layers:** Search "psycopg2 lambda layer python 3.11 [your-region]" for available ARNs.
**With this option, you only need to upload `lambda_function.py` to Lambda.**


### Option B: Deployment ZIP Package

Package your code together with all dependencies.

**On Linux:**

```bash
# Create packaging directory
mkdir package
cd package

# Install dependencies into this folder
pip install psycopg2-binary -t .

# Copy your Lambda code
cp ../lambda_function.py .

# Create ZIP file
zip -r ../lambda_deployment.zip .

# Go back to project root
cd ..
```

**On Mac or Windows:**

The psycopg2 library compiled on Mac/Windows won't work on Lambda (which runs Linux). Use this command instead:

```bash
mkdir package
cd package

# Install Linux-compatible version
pip install psycopg2-binary -t . --platform manylinux2014_x86_64 --only-binary=:all:

cp ../lambda_function.py .
zip -r ../lambda_deployment.zip .
cd ..
```

**This creates `lambda_deployment.zip` which you'll upload to AWS.**

---

## AWS Console Setup

### Step 1: Create the Lambda Function

1. Go to **AWS Console** → **Lambda** → **Create function**

2. Choose **Author from scratch**

3. Enter basic information:
    - **Function name:** `loan-processor-python`
    - **Runtime:** `Python 3.11`
    - **Architecture:** `x86_64`

4. Click **Create function**

### Step 2: Upload Your Code

**If using Option A (Layer):**

1. In the Lambda console, scroll to **Code source**
2. Delete the default code
3. Copy and paste the entire contents of `lambda_function.py`
4. Click **Deploy**

**If using Option B (ZIP):**

1. In the Lambda console, scroll to **Code source**
2. Click **Upload from** → **.zip file**
3. Upload `lambda_deployment.zip`
4. Click **Deploy**

### Step 3: Add Lambda Layer (Option A only)

1. Scroll down to **Layers** section
2. Click **Add a layer**
3. Choose **Specify an ARN**
4. Paste the psycopg2 layer ARN:
   ```
   arn:aws:lambda:us-east-1:898466741470:layer:psycopg2-py311:1
   ```
5. Click **Verify** then **Add**

### Step 4: Configure Environment Variables

1. Go to **Configuration** tab → **Environment variables**
2. Click **Edit**
3. Add the following variables:

| Key           | Value                              |
|---------------|------------------------------------|
| `DB_HOST`     | `your-postgres-host.amazonaws.com` |
| `DB_PORT`     | `5432`                             |
| `DB_NAME`     | `loans_db`                         |
| `DB_USER`     | `postgres`                         |
| `DB_PASSWORD` | `your-password`                    |

4. Click **Save**

### Step 5: Adjust Timeout and Memory

1. Go to **Configuration** tab → **General configuration**
2. Click **Edit**
3. Set these values:
    - **Memory:** `256 MB` (increase if processing large batches)
    - **Timeout:** `30 seconds` (database operations can be slow)
4. Click **Save**

### Step 6: Configure VPC (If Required)

If your PostgreSQL database is in a VPC:

1. Go to **Configuration** tab → **VPC**
2. Click **Edit**
3. Select your VPC, subnets, and security groups
4. Ensure the security group allows outbound traffic to your database port (5432)
5. Click **Save**

### Step 7: Set Up IAM Permissions

Your Lambda needs permission to read from SQS. The default execution role may need these additions:

1. Go to **Configuration** tab → **Permissions**
2. Click on the **Role name** to open IAM
3. Add this policy (or attach `AWSLambdaSQSQueueExecutionRole`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789:your-queue-name"
    }
  ]
}
```

### Step 8: Add SQS Trigger

1. Go back to your Lambda function
2. Click **Add trigger**
3. Select **SQS** from the dropdown
4. Configure the trigger:
    - **SQS queue:** Select your queue
    - **Batch size:** `10` (process up to 10 messages at once)
    - **Batch window:** `0` (or set a few seconds to batch messages)
5. Click **Add**

---

## Testing in AWS

### Create a Test Event

1. Go to your Lambda → **Test** tab
2. Click **Create new event**
3. Event name: `SampleLoanBatch`
4. Paste this test JSON:

```json
{
  "Records": [
    {
      "messageId": "test-001",
      "body": "{\"loans\": [{\"loan_id\": \"L001\", \"customer_name\": \"John Smith\", \"amount\": 5000, \"status\": \"approved\"}, {\"loan_id\": \"L002\", \"customer_name\": \"Jane Doe\", \"amount\": 10000, \"status\": \"pending\"}, {\"loan_id\": \"L003\", \"customer_name\": \"Bob Wilson\", \"amount\": 7500, \"status\": \"approved\"}, {\"loan_id\": \"L004\", \"customer_name\": \"Alice Brown\", \"amount\": 15000, \"status\": \"review\"}, {\"loan_id\": \"L005\", \"customer_name\": \"Charlie Davis\", \"amount\": 3000, \"status\": \"approved\"}, {\"loan_id\": \"L006\", \"customer_name\": \"Eva Martinez\", \"amount\": 20000, \"status\": \"pending\"}]}"
    }
  ]
}
```

5. Click **Save**
6. Click **Test**

### Check the Results

- **Execution result:** Should show `statusCode: 200`
- **Function logs:** Shows processing details
- **Database:** Verify records exist in your `loans` table

### View CloudWatch Logs

1. Go to **Monitor** tab → **View CloudWatch logs**
2. Click on the latest log stream
3. Review the log entries for any errors

---

## Database Setup

### Create the Loans Table

Run this SQL in your PostgreSQL database:

```sql
CREATE TABLE loans (
    loan_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Index for status queries
CREATE INDEX idx_loans_status ON loans(status);
```

### Expected JSON Message Format

The Lambda expects SQS messages in this format:

```json
{
  "loans": [
    {
      "loan_id": "L001",
      "customer_name": "John Smith",
      "amount": 5000,
      "status": "approved"
    },
    {
      "loan_id": "L002",
      "customer_name": "Jane Doe",
      "amount": 10000,
      "status": "pending"
    }
  ]
}
```

> **Note:** If your Java Lambda uses a different format, update the `parse_loan_rows()` function in `lambda_function.py`
> to match.

---

## Security Considerations

### 1. Store Secrets Securely

For production, don't store `DB_PASSWORD` in environment variables. Use AWS Secrets Manager instead:

```python
import boto3
import json


def get_db_password():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='loan-processor/db-credentials')
    secret = json.loads(response['SecretString'])
    return secret['password']
```

### 2. VPC Configuration

- Place Lambda in the same VPC as your database
- Use private subnets for Lambda
- Security group should only allow outbound to database port (5432)

### 3. IAM Least Privilege

Only grant the permissions your Lambda actually needs:

- `sqs:ReceiveMessage` - Read messages
- `sqs:DeleteMessage` - Remove processed messages
- `sqs:GetQueueAttributes` - Required for trigger

### 4. Enable Dead Letter Queue (DLQ)

Configure a DLQ for messages that fail processing:

1. Create a new SQS queue for failed messages
2. In your main queue settings, configure the DLQ
3. Set maximum receives to 3 (retry 3 times before moving to DLQ)

---

## Troubleshooting

### Common Issues

| Problem                                           | Solution                                                 |
|---------------------------------------------------|----------------------------------------------------------|
| `ModuleNotFoundError: No module named 'psycopg2'` | Add the psycopg2 layer or include it in your ZIP package |
| `Connection refused` to database                  | Check VPC settings, security groups, and database host   |
| `Timeout` errors                                  | Increase Lambda timeout, check database connectivity     |
| `Access Denied` to SQS                            | Update IAM role with SQS permissions                     |
| Messages not being deleted                        | Check that Lambda has `sqs:DeleteMessage` permission     |

### Checking Logs

```bash
# Using AWS CLI to tail logs
aws logs tail /aws/lambda/loan-processor-python --follow
```

### Testing Database Connection

Add this temporary test in `lambda_function.py`:

```python
def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("Database connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

---

## Adding to Your Pipeline

Once testing is complete:

1. Remove any test code
2. Update environment variables for production
3. Configure appropriate batch size for your volume
4. Set up CloudWatch alarms for errors
5. Connect to your existing SQS queue trigger

---

## Quick Reference: Java vs Python

| Aspect       | Java Lambda                     | Python Lambda                    |
|--------------|---------------------------------|----------------------------------|
| Entry point  | `handleRequest(event, context)` | `lambda_handler(event, context)` |
| Dependencies | Maven/Gradle                    | `requirements.txt` + Layer/ZIP   |
| DB Driver    | JDBC                            | psycopg2                         |
| Get records  | `event.getRecords()`            | `event.get('Records', [])`       |
| JSON parsing | Jackson/Gson                    | `json.loads()`                   |

---

## Support

If you encounter issues:

1. Check CloudWatch logs for error details
2. Test locally with `test_local.py` first
3. Verify database connectivity from within the VPC
4. Confirm IAM permissions are correct