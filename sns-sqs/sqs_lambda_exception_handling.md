# Lambda Function with SQS Message Processing in Python

Lambda function processes SQS messages without throwing exceptions:

```python
import json
import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler that processes SQS messages.
    The message is automatically deleted from SQS only if this function
    completes without raising an exception.
    """

    # Log the received event
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # SQS messages come in a Records array
        for record in event['Records']:
            # Extract the message body
            message_body = record['body']
            message_id = record['messageId']

            logger.info(f"Processing message {message_id}: {message_body}")

            # Parse the message (assuming JSON)
            message_data = json.loads(message_body)

            # Process the message (example processing logic)
            process_message(message_data)

            # No need to explicitly delete the message
            # AWS will delete it automatically after successful execution
            logger.info(f"Successfully processed message {message_id}")

        return {
            'statusCode': 200,
            'body': json.dumps('Messages processed successfully')
        }

    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        logger.error(f"JSON parsing error: {str(e)}")
        # Important: We're catching the error and not re-throwing it
        # This means the Lambda will still "succeed" and SQS will delete the message
        return {
            'statusCode': 200,
            'body': json.dumps('Message had invalid JSON but was consumed')
        }

    except Exception as e:
        # If any other exception occurs, log it
        logger.error(f"Error processing message: {str(e)}")
        # Re-raise the exception - this will cause Lambda to fail
        # and SQS will retain the message for reprocessing
        raise


def process_message(message_data):
    """
    Process the message data - this is where your business logic goes.
    """
    # Example: Process an order
    if 'order_id' in message_data:
        logger.info(f"Processing order {message_data['order_id']}")
        # Do something with the order...

        # If you want to intentionally fail processing to retry later:
        if message_data.get('status') == 'needs_retry':
            raise Exception("Order needs to be retried later")
```

## Key Points About Message Processing

1. **Automatic Deletion**:
    - If the Lambda function completes without exceptions, AWS automatically deletes the message from SQS
    - No explicit deletion call is needed in the normal flow

2. **Exception Handling Control Flow**:
    - If you catch and handle exceptions without re-throwing them (like the JSONDecodeError example), the Lambda
      function is considered successful, and the message will be deleted
    - If you let exceptions bubble up or explicitly re-raise them, the Lambda execution is considered failed, and SQS
      will not delete the message

3. **Selective Retries**:
    - You can implement selective retry logic by catching some errors but raising others
    - This gives you fine-grained control over which conditions should cause a message to be reprocessed

4. **Dead Letter Queue Integration**:
    - After multiple processing attempts, messages will go to a Dead Letter Queue if configured

## Manually Deleting Messages

If you need more control, you can explicitly delete messages:

```python
def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    queue_url = "https://sqs.region.amazonaws.com/account-id/queue-name"

    for record in event['Records']:
        receipt_handle = record['receiptHandle']

        try:
            # Process message...
            process_message(json.loads(record['body']))

            # Explicitly delete the message after successful processing
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"Explicitly deleted message {record['messageId']}")

        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            # Message will remain in queue since we're not deleting it
            # But we're also not failing the Lambda function
```

This explicit deletion approach is useful when you have mixed success/failure in a batch of messages and want to delete
only the successfully processed ones.