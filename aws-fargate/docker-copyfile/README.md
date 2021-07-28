# Build and run the created image
- docker build -t docker-copy-file .
- docker run -it  docker-copy-file --> t, the docker image tag and i, for interactive session
> below execute the docker image you just created, pass in the aws credentials used serverless-admin
- docker run -e AWS_ACCESS_KEY_ID_VAL=XXXXX -e AWS_SECRET_ACCESS_KEY_VAL=XXXXXXXXX -e BUCKET_NAME=abc -e INPUT_FILE_NAME=inputfile.txt -e INPUT_KEY=in/inputfile.txt -e OUTPUT_KEY=out/outfile.txt  -e AWS_REGION=us-east-1 -it docker-copy-file

Register docker image with AWS ECR
========================================
- aws ecr create-repository --repository-name docker-copy-file
- docker tag docker-copy-file:latest #aws_account.dkr.ecr.us-east-1.amazonaws.com/docker-copy-file:latest
> login into ecr and push the docke image
- aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin #aws_account.dkr.ecr.us-east-1.amazonaws.com
- docker push #aws_account.dkr.ecr.us-east-1.amazonaws.com/docker-copy-file:latest
- https://console.aws.amazon.com/ecs/home?region=us-east-1#/firstRun, inline policy file for ecsTaskRole is in this repo.

Register docker image with ECS/fargate
--------------------------------------
- https://www.serverless.com/blog/serverless-application-for-long-running-process-fargate-lambda
- https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-set-up-credentials.html