In this project when a file is placed in s3 bucket, lambda is triggered
and the lamnda in turn invokes the container hosting the docker image, docker-copyfile

AWS Fargate Setup Notes
------------------------
- https://www.serverless.com/blog/serverless-application-for-long-running-process-fargate-lambda **
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html#create-task-execution-role  ** -- create role for Fargate Allows ECS tasks to call AWS services on your behalf
- https://aws.amazon.com/premiumsupport/knowledge-center/ecs-fargate-access-aws-services/ ** - create a role for Fargate coantiner to  read S3
- https://stackoverflow.com/questions/54237228/access-aws-s3-bucket-from-a-container-on-a-server - s3 ACCES FOR CONTAINER
- https://console.aws.amazon.com/ecs/home?region=us-east-1#/ - create ecs + fargate **
- https://github.com/rupakg/ffmpeg-video-thumb **
- https://www.serverless.com/blog/deploy-hybrid-serverless-cluster-workflows **
- https://www.serverless.com/plugins/serverless-step-functions
- https://theburningmonk.com/cloudformation-ref-and-getatt-cheatsheet/
- https://www.serverless.com/framework/docs/providers/aws/guide/installation/

ecs using fargate
-----------------
https://www.serverless.com/blog/serverless-application-for-long-running-process-fargate-lambda#setting-up-ecs-using-fargate/

AWS ECS Container setup
----------------------------
https://console.aws.amazon.com/ecs/home?region=us-east-1#/firstRun

Cron scheduler
---------------
https://www.serverless.com/examples/aws-python-scheduled-cron/

Yeoman generator template.
-------------------------
 This generator makes it much easier to create a narrow IAM policy template that will cover many Serverless use cases
 - npm install -g yo generator-serverless-policy
 - yo serverless-policy --> running this command in the serverless project folder, slsflaskapp. This created file slsflaskapp-dev-us-east-1-policy.json, used the content of above file to create poliy 
                                                             
Policy
-------
https://docs.aws.amazon.com/vpc/latest/userguide/vpc-policy-examples.html

pseudo parameters
-----------------
https://www.serverless.com/plugins/serverless-pseudo-parameters

ECR and ECS
------------

[https://faun.pub/what-is-amazon-ecs-and-ecr-how-does-they-work-with-an-example-4acbf9be8415](Amazon ECR is integrated with Amazon ECS) allowing you to easily store, run, and manage container images for applications
running on Amazon ECS. All you need to do is specify the Amazon ECR repository in your Task Definition and Amazon ECS
will retrieve the appropriate images for your applications.

Role - Unable to locate credentials inside fargate container, using Boto3
--------------------------------------------------------------------
https://stackoverflow.com/questions/65992423/unable-to-locate-credentials-inside-fargate-container-using-boto3
https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html

ecsTaskExecutionRole is not for your container to access S3. It is for ECS itself to be able to, 
e.g. pull your docker image from ECR.

For your application permissions in the container, you need a task role, not the task execution role.
It can be confusing because both are named similarly and both have same trust policy.



#Serverless
-----------------
- install npm windows --> https://nodejs.org/en/download/
- npm install -g serverless. Open up a terminal and type npm install -g serverless to install Serverless.
- npm install --> creates package.json files, if the project already exists
- serverless --version. Run to see which version of serverless you have installed.

Next setup AWS:
------------------------
- Install aws cli
- python -m pip aws
- install aws cli msi executable
 

Current credentials
-------------------
- aws configure list
- aws configure --profile slsflaskapp
- aws configure list-profiles
- https://www.serverless.com/framework/docs/providers/aws/guide/credentials/                                        

another example:
------------------
- aws configure --profile serverless
- export AWS_PROFILE=serverless
- profile: serverless -- add to serverless.yml
- https://www.serverless.com/blog/abcs-of-iam-permissions


Serverless create template
---------------------------
- [sls python example](https://www.serverless.com/framework/docs/providers/aws/examples/hello-world/python/)
- sls create --template aws-python3 --path myService
- npm install serverless-pseudo-parameters

deploy
----------
- sls deploy -v --stage dev, deploy Serverless service and all resources

remove
---------
- sls remove, Remove Serverless service and all resources


Deploy/remove Serverless app
-------------------------------
- SLS_DEBUG=1
- IS_OFFLINE=true
- sls deploy
- serverless deploy -v --stage dev
- serverless deploy -v --aws-profile slsflaskapp
- serverless remove



Onedrive and gitrepo                                                          
---------------------                                                         
- https://www.permikkelsen.dk/how-to-host-your-git-repository-on-onedrive.html  



print config - You can test your serverless config with the print command.
---------------
- sls print --stage dev , this will interpret your config object and print it to the console.
