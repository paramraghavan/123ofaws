import json
import os
import psycopg2
from psycopg2.extras import execute_values

# Database connection settings (from environment variables)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'loans_db'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'password')
}


def get_db_connection():
    """Create and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def parse_loan_rows(message_body):
    """
    Parse the JSON message and extract loan rows.

    Expected JSON format:
    {
        "loans": [
            {"loan_id": "L001", "customer_name": "John", "amount": 5000, "status": "approved"},
            {"loan_id": "L002", "customer_name": "Jane", "amount": 10000, "status": "pending"},
            ...
        ]
    }
    """
    data = json.loads(message_body)

    # Check if it's a list of loans
    if isinstance(data, list):
        return data

    # Check if it has a 'loans' array
    if 'loans' in data:
        return data['loans']

    return data.get('loans', [])


def insert_loans_to_db(loans):
    """Insert loan rows into PostgreSQL table."""
    if not loans:
        print("No loans to insert")
        return 0

    # SQL to insert loans (adjust columns to match your table)
    insert_sql = """
        INSERT INTO loans (loan_id, customer_name, amount, status)
        VALUES %s
        ON CONFLICT (loan_id) DO UPDATE SET
            customer_name = EXCLUDED.customer_name,
            amount = EXCLUDED.amount,
            status = EXCLUDED.status
    """

    # Convert loan dictionaries to tuples
    values = [
        (loan['loan_id'], loan['customer_name'], loan['amount'], loan['status'])
        for loan in loans
    ]

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # execute_values is efficient for bulk inserts
        execute_values(cursor, insert_sql, values)

        conn.commit()
        print(f"Successfully inserted {len(values)} loans")
        return len(values)

    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()


def lambda_handler(event, context):
    """
    Main Lambda entry point.

    AWS automatically calls this function when:
    - SQS trigger fires (messages arrive in queue)
    - Or when you test manually

    'event' contains the SQS messages
    'context' has Lambda runtime info (we don't need it here)
    """
    print(f"Received event with {len(event.get('Records', []))} messages")

    total_loans_processed = 0
    failed_messages = []

    # Process each SQS message
    for record in event.get('Records', []):
        message_id = record.get('messageId', 'unknown')

        try:
            # Get the message body (the actual JSON content)
            message_body = record['body']
            print(f"Processing message: {message_id}")

            # Parse and insert loans
            loans = parse_loan_rows(message_body)
            count = insert_loans_to_db(loans)
            total_loans_processed += count

        except Exception as e:
            print(f"Error processing message {message_id}: {e}")
            failed_messages.append(message_id)

    # Return summary
    result = {
        'statusCode': 200,
        'body': {
            'total_loans_processed': total_loans_processed,
            'messages_processed': len(event.get('Records', [])),
            'failed_messages': failed_messages
        }
    }

    print(f"Result: {result}")
    return result
