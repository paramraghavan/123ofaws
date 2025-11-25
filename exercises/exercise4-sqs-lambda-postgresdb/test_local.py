"""
Run this on your laptop to test the Lambda locally.
Uses your AWS profile to read from actual SQS queue.
"""
import boto3
import os

# Import our Lambda function
from lambda_function import lambda_handler

# Set database environment variables for local testing
os.environ['DB_HOST'] = 'your-postgres-host.amazonaws.com'  # or 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'loans_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'your-password'

# Your SQS queue URL
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/123456789/your-queue-name'


def test_with_fake_data():
    """Test with sample data (no AWS needed)."""
    print("\n=== Testing with FAKE data ===\n")

    # Simulate an SQS event with 6 loan rows
    fake_event = {
        'Records': [
            {
                'messageId': 'test-message-001',
                'body': '''{
                    "loans": [
                        {"loan_id": "L001", "customer_name": "John Smith", "amount": 5000, "status": "approved"},
                        {"loan_id": "L002", "customer_name": "Jane Doe", "amount": 10000, "status": "pending"},
                        {"loan_id": "L003", "customer_name": "Bob Wilson", "amount": 7500, "status": "approved"},
                        {"loan_id": "L004", "customer_name": "Alice Brown", "amount": 15000, "status": "review"},
                        {"loan_id": "L005", "customer_name": "Charlie Davis", "amount": 3000, "status": "approved"},
                        {"loan_id": "L006", "customer_name": "Eva Martinez", "amount": 20000, "status": "pending"}
                    ]
                }'''
            }
        ]
    }

    result = lambda_handler(fake_event, None)
    print(f"Result: {result}")


def test_with_real_sqs():
    """Read from actual SQS queue using your AWS profile."""
    print("\n=== Testing with REAL SQS ===\n")

    # Uses AWS profile from ~/.aws/credentials
    # To use a specific profile: boto3.Session(profile_name='your-profile')
    sqs = boto3.client('sqs')

    # Receive messages from queue
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=10,  # Up to 10 messages at a time
        WaitTimeSeconds=5  # Wait up to 5 seconds for messages
    )

    messages = response.get('Messages', [])

    if not messages:
        print("No messages in queue")
        return

    print(f"Found {len(messages)} messages")

    # Convert to Lambda event format
    event = {
        'Records': [
            {
                'messageId': msg['MessageId'],
                'body': msg['Body'],
                'receiptHandle': msg['ReceiptHandle']
            }
            for msg in messages
        ]
    }

    # Process messages
    result = lambda_handler(event, None)
    print(f"Result: {result}")

    # Delete processed messages from queue
    for msg in messages:
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg['ReceiptHandle']
        )
    print("Messages deleted from queue")


if __name__ == '__main__':
    # Choose which test to run:
    test_with_fake_data()  # Start with this!
    # test_with_real_sqs()   # Uncomment when ready to test with real queue