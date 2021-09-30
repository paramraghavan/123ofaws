AWS FARGATE
----------------

With the execution time limits of the AWS Lambda platform, there are a lot of use cases involving long-running processes that
are hard to implement.

On the flip side, serverless computing offers benefits (like zero-administration, pay-per-execution, and auto-scaling capabilities)
that are hard to ignore. AWS recently announced AWS Fargate to bridge that gap.

>AWS Fargate is a technology that allows you to use containers as a fundamental compute primitive without having to manage the 
underlying compute instances.

Fargate technology works on Amazon ECS - Elastic Container Service & Amazon EKS - Elastic Kubernetes Service, and allows users to run containers without having to manage servers or clusters.

Amazon ECS and Amazon EKS have two modes or launch types: Fargate and EC2.

With Fargate, all you have to do is package your application in containers, specify the CPU and memory requirements, define networking
and IAM policies, and launch the application. You can define an ECS Task and call it from your Lambda function.


Project [docker-copyfile](https://github.com/paramraghavan/123ofaws/tree/main/aws-fargate/docker-copyfile), has steps to create docker image to be used by AWS ECS Fargate container.
This image runs a shell script which copies file from S3 Input bucket into to  working directory and copies the file from working directory back to S3 Output bucket.

**High level up AWS Fargate**
AWS provides a First Run Wizard that is an excellent resource to start playing with ECS using Fargate. 

![Uploading Screen Shot 2021-09-30 at 1.18.49 PM.png…]()

- Step1, we will create the container definition, most likely a custom container. Give the container a name, then image. You could ahve the image registred with ECR, Elastic Container Registry, or with docker hub using the docker hub registry URL, in the advanced container set the enviroment varaibles. Next, in the 'STORAGE AND LOGGING' add the following 'Log configuration' key/value pairs:
-- awslogs-group - /ecs/ffmpeg-thumb-task-definition
-- awslogs-region - us-east-1
-- awslogs-stream-prefix - ecs

- step2 update task defination 
-- compatibilites --> Fatrgate
-- TAsk size - appro

## References:
https://www.serverless.com/blog/serverless-application-for-long-running-process-fargate-lambda
