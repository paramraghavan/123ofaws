SNS vs SQS
------------
The main difference between Amazon SNS and Amazon SQS is that SNS implements a
"push" architecture—all subscribers receive the messages that are published to
a topic, while SQS implements a "pull" architecture, in which clients pull messages
from a shared queue.

When to use SNS vs. SQS?
--------------------------
While SNS and SQS are related, they serve different purposes.

SQS is a queuing system. The tasks it excels at are maintaining a queue of messages and ensuring that each message is successfully pulled from the queue exactly once. As a result, SQS requires polling for items—"pulling" data, where it’s the responsibility of the client to request the data it is ready to process.

On the other end, SNS is a publish/subscribe system. The task for which it was designed is to send all the messages it receives to each of its many subscribers. SNS follows the "push" principle, where it’s system’s responsibility to make sure all subscribers are notified of the new message. No polling on the part of subscribers is required.

In some cases you might want to use only one of these services, sometimes using SQS together with SNS can be a good option, as in the one-to-many use case.

Ref
----
https://www.serverless.com/amazon-sns
