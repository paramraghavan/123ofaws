# SQS Integration with AWS Resources

## Triggers for SQS

SQS is fundamentally pull-based. A Lambda can poll SQS directly, or you can configure SQS as a Lambda event source. In the event-source setup, AWS Lambda polls SQS on your behalf and invokes the function, so it behaves like a trigger even though the underlying model is still polling.

## Push vs Pull

| Mode | What happens |
| --- | --- |
| Push-like / managed trigger | Configure SQS as a Lambda event source. AWS Lambda polls SQS for you and invokes the Lambda with message batches. |
| Pull | Your Lambda, ECS task, EC2 worker, or other consumer calls `ReceiveMessage`, processes messages, and calls `DeleteMessage`. |


**Note:**
> SQS is fundamentally pull-based. A Lambda can poll SQS directly, or you can configure SQS as a Lambda event source. In the event-source setup, AWS Lambda polls SQS on your behalf and invokes the function, so it behaves like a trigger even though the underlying model is still polling.
> SQS is pull-based because Lambda polls SQS through an event source mapping. The same is true for stream/queue sources like Kinesis, DynamoDB Streams, and Kafka. But event sources like SNS, S3, EventBridge, API Gateway, and ALB are push-style integrations where the service invokes Lambda directly.

## Common Integrations

SQS commonly feeds:

1. **AWS Lambda**: Lambda event source mapping polls SQS and invokes the function.
2. **AWS Step Functions**: Usually started through Lambda or EventBridge after a message is consumed.
3. **Amazon EventBridge Pipes**: Can connect SQS to supported targets with filtering/enrichment.
4. **AWS Fargate / ECS / EC2 workers**: Workers poll SQS directly.

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
