AWS FARGATE
----------------

With the execution time limits of the AWS Lambda platform, there are a lot of use cases involving long-running processes that
are hard to implement.

On the flip side, serverless computing offers benefits (like zero-administration, pay-per-execution, and auto-scaling capabilities)
that are hard to ignore. AWS recently announced AWS Fargate to bridge that gap.

>AWS Fargate is a technology that allows you to use containers as a fundamental compute primitive without having to manage the 
underlying compute instances.

Fargate technology works on Amazon ECS - Elastic Compute Service & Amazon EKS - Elastic Kubernetes Service, and allows users to run containers without having to manage servers or clusters.

Amazon ECS and Amazon EKS have two modes or launch types: Fargate and EC2.

With Fargate, all you have to do is package your application in containers, specify the CPU and memory requirements, define networking
and IAM policies, and launch the application. You can define an ECS Task and call it from your Lambda function.



## References:
https://www.serverless.com/blog/serverless-application-for-long-running-process-fargate-lambda
