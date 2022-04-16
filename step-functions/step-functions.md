## Step functions
With microservices architecture in play, we use step function to orchestrate microservices as tasks with are run in sequence and eac step of the way we can take actions based on task1 succeeds or fails and go to taskn1 or taskn0. For example we can have 3 microservices -generate report, encrypt report, and email/sns the report. All these micorservices can run standalone, and we can use step functions to orchestrate - generate, encrypt and email report as a single process. The step function at each steps looks at the status of the previous step, lets say the encrypt step fails the entire step funtion fails and the report is not emailed. Lets say the encrypt failed because of lambda throtelling or some kind of network error, we can have logic to retry the encrypt step n number of times, before we deem this step and the enite process as a faield process.

**States Types**
![image](https://user-images.githubusercontent.com/52529498/163674993-2b4ed59a-23cd-4350-9c6c-aa1e356fdf41.png)

The first is a task state, and a task state determines what kind of work do you want to do, for example lambda task, which you defer to a lambda function to process, Or you can have activity tasks submit job, which defer to some EC2 instance running your application or call another step function. **AWS services** that can be invoked - AWS Batch Job, Glue, SNS, SQS.

The next is we have choice states. Choice states are like branching states where depending on the output of a previous state determines what you're going to do next. **Operators**- and, or, not. **Data types** - boolean, string, number and timestamp
![image](https://user-images.githubusercontent.com/52529498/163675315-a415cd3d-ac40-49e9-ae93-451523cadc2a.png)


Then we have parallel states, which allow you to do things at the same time and then merge back together.

Then we have wait states. Wait states are for steps that are going to take a long amount of time. So instead of you using resources to constantly poll that, you can then use the wait states to check every 30 seconds or some time interval that you set.
![image](https://user-images.githubusercontent.com/52529498/163675420-f52f8a3c-b7ab-45c2-a97f-241b5b40f446.png)

![image](https://user-images.githubusercontent.com/52529498/163675455-5d624ad8-0b0d-41f3-b138-0a79c87fdb70.png)

**Pass** doesn't perform any work. The main purpose is to pass its input to the output. They are mostly used for constructing and debugging state machines.
![image](https://user-images.githubusercontent.com/52529498/163675632-1853f5ba-b91c-4d40-ac12-fb029525d50e.png)
Here the constructed "Identity" object is passed as input to to the next step.

Success/Fail - Finally, when your application completes, we have fail and we have success states to let a simple workflow know if we completed successfully.
![image](https://user-images.githubusercontent.com/52529498/163675737-2ae56945-644f-41c5-bd83-360f5e9d6623.png)

Error States : States.All, States.Runtime, States.Timeout, States.TaskFailed, States.Permissions

Pix2

So above is an example of a simple sequential workflow in which we have a start state that sets us up into our start state, and then that starts state runs a lambda function. Once that completes, we set it over to a final state, which is also a lambda function, which,
if it completes successfully, we send it up to an end state. So how do you define these workflows? That's using the Amazon State Language.


Pix3
See above - the same in workflow seen above this image, but here we can show it with the code. And here you can see, we have the StartAt, which determines where we're going to start our state, and then we define the two states there with our StartState and FinalState that configure which lambda function it's going to run. 

<pre>
"States":{
"DailyDataLoadSelectedEntityPass":{
"Type":"Pass",
"Result":"dailyDataLoadsWorkflow",
"ResultPath":"$.dynamodbConfig.entityToUpdate",
"Next":"ExecutionChoice"
},

Lines below modify the input to step function
"Result":"dailyDataLoadsWorkflow",
"ResultPath":"$.dynamodbConfig.entityToUpdate",
</pre>
**input from :**

<pre>
..
"dynamodbConfig": {
"dailydataloads": {
        "status": "INPROGRESS",
        "statusDetails": "daily dataload can start"
} }

...
</pre>
*to:*
<pre>
...
"dynamodbConfig": {

"entityToUpdate":"dailyDataLoadsWorkflow",
"dailydataloads": {
        "status": "INPROGRESS",
        "statusDetails": "daily dataload can start"
}}
...
</pre>


https://docs.aws.amazon.com/step-functions/latest/dg/input-output-example.html


default behavior is as if you had specified "ResultPath": "$", this tells the state to replace the entire input with the result, the state input is completely replaced by the result coming from the task result.

https://docs.aws.amazon.com/step-functions/latest/dg/input-output-resultpath.html

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### InputPath, ResultPath and OutputPath Example
Any state other than a Fail state can include InputPath, ResultPath or OutputPath. These allow you to use a path to filter the JSON as it moves through your workflow.

For example, start with the AWS Lambda function and state machine described in the Creating a Step Functions State Machine That Uses Lambda tutorial. Modify the state machine so that it includes the following InputPath, ResultPath, and OutputPath.
<pre>
{
  "Comment": "A Hello World example of the Amazon States Language using an AWS Lambda function",
  "StartAt": "HelloWorld",
  "States": {
    "HelloWorld": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:HelloFunction",
"InputPath": "$.lambda",
 "ResultPath": "$.data.lambdaresult",
 "OutputPath": "$.data", 
 "End": true 
} } }
</pre>
Start an execution using the following input.
<pre>
{
  "comment": "An input comment.",
  "data": {
    "val1": 23,
    "val2": 17
  },
  "extra": "foo",
  "lambda": {
    "who": "AWS Step Functions"
  }
}
</pre>        
Assume that the comment and extra nodes can be discarded, but that we want to include the output of the Lambda function, and preserve the information in the data node.

In the updated state machine, the Task state is altered to process the input to the task.

"InputPath": "$.lambda",
This line in the state machine definition limits the task input to only the lambda node from the state input. The Lambda function receives only the JSON object {"who": "AWS Step Functions"} as input.

"ResultPath": "$.data.lambdaresult",
This ResultPath tells the state machine to insert the result of the Lambda function into a node named lambdaresult, as a child of the data node in the original state machine input. Without further processing with OutputPath, the input of the state now includes the result of the Lambda function with the original input.
<pre>
{
  "comment": "An input comment.",
  "data": {
    "val1": 23,
    "val2": 17,
    "lambdaresult": "Hello, AWS Step Functions!"
  },
  "extra": "foo",
  "lambda": {
    "who": "AWS Step Functions"
  }
}
</pre>
But, our goal was to preserve only the data node, and include the result of the Lambda function. OutputPath filters this combined JSON before passing it to the state output.

"OutputPath": "$.data",
This selects only the data node from the original input (including the lambdaresult child inserted by ResultPath) to be passed to the output. The state output is filtered to the following.
<pre>
{
  "val1": 23,
  "val2": 17,
  "lambdaresult": "Hello, AWS Step Functions!"
}
</pre>
In this Task state:
InputPath sends only the lambda node from the input to the Lambda function.
ResultPath inserts the result as a child of the data node in the original input.
OutputPath filters the state input (which now includes the result of the Lambda function) so that it passes only the data node to the state output.

ref:

https://docs.aws.amazon.com/step-functions/latest/dg/step-functions-dg.pdf#input-output-example
