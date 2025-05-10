# SQS Integration with AWS Resources

## Triggers for SQS

SQS can trigger several AWS resources:

1. **AWS Lambda**: The most common integration - Lambda functions can be invoked when messages arrive in an SQS queue.
2. **AWS Step Functions**: Step Functions can be triggered by SQS via a Lambda function or Amazon EventBridge.
3. **Amazon EventBridge**: Can be configured to listen to SQS and trigger various targets.
4. **AWS Fargate / ECS**: Tasks can be triggered through EventBridge rules that listen to SQS.

## Polling Management

For Lambda integrations:

- **AWS manages polling automatically**: When you configure an SQS queue as a Lambda trigger, AWS handles the polling
  behind the scenes.
- **Poll frequency control**: You can't directly control the polling frequency, but you can adjust:
    - The batch size (how many messages are processed per Lambda invocation)
    - The maximum concurrency of your Lambda function

For other services:

- Most require implementing your own polling mechanism through Lambda or EC2 instances
- Direct control of poll frequency depends on your implementation

## Lambda as an SQS Consumer - Detailed Example

### Polling Behavior

- **Managed Polling**: AWS infrastructure automatically handles polling when you configure an SQS queue as an event
  source for Lambda
- **Polling Control**:
    - Users cannot directly control the polling frequency
    - AWS manages this based on queue activity and Lambda concurrency
    - Lambda automatically scales polling operations up or down based on message volume

### Concurrency Control

- **Configuration Location**: Set on the Lambda side in the event source mapping
- **Batch Size**:
    - Controls how many messages (1-10,000) Lambda processes in a single invocation
    - Set in Lambda console: "Configuration" → "Triggers" → Edit SQS trigger
    - Default is 10 messages per batch

- **Maximum Concurrency**:
    - Controls how many Lambda function instances can run in parallel
    - Set in Lambda console: "Configuration" → "Concurrency"
    - You can set "Reserved concurrency" (total concurrent instances)
    - For SQS specifically, you can set "Maximum concurrency" in the event source mapping
    - Default scales up to 1,000 concurrent executions across all event sources

```
# Example CloudFormation configuration
Resources:
  MyLambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      # Function properties here
      
  MySQSEventSourceMapping:
    Type: AWS::Lambda::EventSourceMapping
    Properties:
      FunctionName: !GetAtt MyLambdaFunction.Arn
      EventSourceArn: !GetAtt MySQSQueue.Arn
      BatchSize: 10
      MaximumBatchingWindowInSeconds: 30
      MaximumConcurrency: 5  # Controls parallel executions
```

### Message Lifecycle

- **Visibility Timeout**:
    - When Lambda receives messages, they become invisible in the queue
    - This is controlled by the "Visibility Timeout" setting on the SQS queue
    - Should be set longer than your Lambda function timeout

- **Message Deletion**:
    - Messages are only deleted from the queue when Lambda successfully completes processing (no exceptions)
    - Deletion happens automatically after successful execution

- **Error Handling**:
    - If Lambda throws an exception:
        1. The entire batch is returned to the queue
        2. Messages become visible again after the visibility timeout expires
        3. They can then be processed again by another Lambda invocation
        4. No automatic immediate retry - must wait for visibility timeout

- **Message Retries**:
    - Messages will be retried until:
        1. They're successfully processed, or
        2. They reach the "Maximum Receives" threshold (configured on SQS)
        3. After maximum receives, they go to Dead Letter Queue (if configured)

### Key Configuration Summary

- **On SQS**:
    - Visibility Timeout (default 30s)
    - Message Retention Period (default 4 days)
    - Maximum Receives Count
    - Dead Letter Queue settings

- **On Lambda**:
    - Batch Size
    - Maximum Batching Window
    - Maximum Concurrency
    - Function Timeout

