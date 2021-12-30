# AWS Batch
AWS Batch is a fully managed service. Batch provisions, manages, and scales your infrastructure to handle your batch workloads. It's fully integrated with AWS, which means if your batch job needs to read from an S3 bucket, a raw file, and write to an S3 bucket, a processed file.  We can look at read/writes against DynamoDB or other storage tools, RDS, we can interact with Lambda, we can interact with Elasticache or Elasticsearch, so fully integrated with other AWS managed services so that you can do full end to end batch processing scenarios against an AWS landscape.

AWS batch have job queues from which jobs are pulled to be processed. So, we will write jobs into the job queues. The jobs can be free handed or can be based on a job definition, that's a template for the job that we will use run job. Job queues are read by resources that are organized in compute environments. So a compute environment reads a queue for the work to be done. And, of course, a scheduler sits down across all of it, organizes and prioritizes the jobs to be pulled from job queues, submitted to compute environments, and processe.

Jobs are submitted to a job queue where they reside until they're able to be scheduled to run in a compute environment. An AWS account can have multiple queues. For example, you might have a queue that uses EC2 on demand instances for high priority jobs, and another queue that uses EC2 Spot instances for low priority jobs. A job queue has a priority that's used by the scheduler to determine which jobs in which queue should be evaluated for execution first. 

Queues are mapped to compute environments containing EC2 instances that run containerized batch jobs. So its application virtualization, a form of Docker images that we load in a Docker container to run. So where do those container environments live? They live in compute environments, and they take two forms. So I've managed compute environments where Amazon manages the addition and removal, the scale out and scale in of your batch processing landscape, or unmanaged, where e set that up,


##AWS Batch manages the following resources:

- Job definitions
- Job queues
- Compute environments

A job definition specifies how jobs are to be run—for example, which Docker image to use for your job, how many vCPUs and how much memory is required, the IAM role to be used, and more.

Jobs are submitted to job queues where they reside until they can be scheduled to run on Amazon EC2 instances within a compute environment. An AWS account can have multiple job queues, each with varying priority. This gives you the ability to closely align the consumption of compute resources with your organizational requirements.

Compute environments provision and manage your EC2 instances and other compute resources that are used to run your AWS Batch jobs. Job queues are mapped to one more compute environments and a given environment can also be mapped to one or more job queues. This many-to-many relationship is defined by the compute environment order and job queue priority properties.

The following diagram shows a general overview of how the AWS Batch resources interact.
![image](https://user-images.githubusercontent.com/52529498/147717782-b6838f4e-ba32-4199-97de-6f62dbf2d082.png)

- [ref](https://aws.amazon.com/blogs/compute/using-aws-cloudformation-to-create-and-manage-aws-batch-resources/)

## Job Queues
-  Jobs are submitted to job queue
-  and remain in job queue until scheduled to a compute resource.
- Queues are mapped to compute enviroment  containing EC2 instances that run containerized(docker images) batch jobs.
-  queues can share the compute enviroment
-  Queue with prioty 1 will get the highest priority and lower the number lower priority.
- $awsbatch create-job-queue --job-queue-name testqueue -- priority 100 -- compute-enviroment-order ...

## Compute Environments
- Aws Managed - launch and scale resources on your behalf,  run docker images 
- Unmanaged - launch and manage you own resources, run docker images 

## Job Definations
- Identifies which docker image to use
- job properties include iam role with the job, vCpu, memory
- environment variables to be set for container
- iam role used if the application running inside tha container needs to acces s3 or dynamodb, etc..
- command the container should run when it is loaded and started.
- similar to ecs task defination
- job defination is a template for creating jobs. The jobs can be free handed as well.
- $ awsbatch register-job-defination --job-defination-name testqueue-job-dfn gatk--container--properties ...


## Jobs
- select the job defination template for creating jobs
- each job can inherit all of the jo defination execution properties or can selectively overide some properties for the job instances.
- this job intance load and fires a containerized aplication running on Amazon EC2
- example S3 bucket event triggers a lambda function, this lambda will invoke a batch submit job.
- $ awsbatch submit-job --job-name mytestjob -- job-defination testqueue-job-dfn gatk--job-queue testqueue

## The Scheduler
When there are many jobs submitted, scheduler looks at the job and their priorities and decides which to job to run first.



### References 
- https://aws.amazon.com/
- pluralsight
- https://github.com/dejonghe/aws-batch-example
- [how to enable bash shell feature on windows](https://www.laptopmag.com/articles/use-bash-shell-windows-10)
- https://aws.amazon.com/blogs/compute/orchestrating-an-application-process-with-aws-batch-using-aws-cloudformation/
