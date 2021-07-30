# Setup role and policies for ECS and the container

##  ecsTaskExecutionRole

This role is used by the task defination to  excute the AWS services used by the container

### Create Role ecsTaskExecutionRole
- IAM, Create role.
- Select type of trusted entity section
- Select AWS service EC2, Lambda and others choose AWS service
- Select a service,  choose AWS service, Elastic Container Service.
- Select use case, choose Elastic Container Service Task
- Attach permissions policy section, search for AmazonECSTaskExecutionRolePolicy
- For Role name, type ecsTaskExecutionRole and choose Create role.
- **Note** the arn for this role, arn:aws:iam::xxxxxxxxxxxxx:role/ecsTaskExecutionRole

### Create Policy, ecsTaskS3Access, for S3 access
<pre>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::xxxxxx0012345"
        },
        {
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::xxxxxx0012345/*"
        }
    ]
}
</pre> 

- Attach permission policy, ecsTaskS3Access, to role ecsTaskExecutionRole


![image](https://user-images.githubusercontent.com/52529498/126923912-6dd14fcf-2864-40c5-9dbc-b0ffd0d3a2c7.png)

## Trust Relationship
![image](https://user-images.githubusercontent.com/52529498/126924305-3085a6b7-9389-4a6c-9c60-6aff0618f73d.png)

### Create Policy named ecs-tasks-trust-policy
- Create Policy
- choose service STS
 - specify action, AssumeRole
 - add ARN, use the arn from ecsTaskExecutionRole above, arn:aws:iam::xxxxxxxxxxxxx:role/ecsTaskExecutionRole

<pre>
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
</pre>

References:
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html#create-task-execution-role  ** -- create role for Fargate to be use aws services
- https://aws.amazon.com/premiumsupport/knowledge-center/ecs-fargate-access-aws-services/ ** - fargate access s3 bucket
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
