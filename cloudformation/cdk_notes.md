# App, Stacks and Constructs
- Apps are the final artifact of code that define one or more Stacks.
- Stacks are equivalent to CloudFormation stacks and are made up of Constructs.
- Constructs define one or more concrete AWS resources, such as the Amazon Relational Database Service (Amazon RDS).

- ref: https://medium.com/slalom-build/the-anatomy-of-a-cdk-app-7bbf44b4ecba



# Steps
Steps to create first sample app. See also on [github](https://github.com/zzenonn/InfrastructureCdkSample)
- npm install -g npm@latest
- npm install -g cdk@1.58
- mkdir infrastructure_cdk
- cd infrastructure_cdk 
  python3 -m venv .env
- cdk init sample-app --language python
- cdk ls
- cdk synth >cfn.yaml
- rm cfn.yaml
- cdk deploy infrastructure-cdk
- cdk deploy -vv LambdaStack # cdk bootstrap aws://xxxxxxxxxxx/us-east-1"
- cdk -vv bootstrap aws://687162148361/us-east-1  
- cdk -vv --public-access-block-configuration false bootstrap aws://687162148361/us-east-1 # otherwise I get CREATE_FAILED | StagingBucket API: s3:PutPublicAccessBlock Access Denied
- add cloudformation:CreateChangeSet on resource arn:aws:cloudformation:us-east-1:687162148361:stack/CDKToolkit/*

- cdk deploy -vv LambdaStack
- ref: https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html, steps to follow
- cdk bootstrap aws://687162148361/us-east-1
- powershell "cdk bootstrap --show-template | Out-File -encoding utf8 bootstrap-template.yaml
- cdk synth LambdaStack >cfn_lambda_stack.yaml
- aws cloudformation create-stack --stack-name CDKToolkit --template-body file://cfn_lambda_stack.yaml


## AWS CDK github project
- https://github.com/aws-samples/aws-cdk-examples/tree/master/python
- https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html

The environment aws://687162148361/us-east-1 doesn't have the CDK toolkit stack
(CDKToolkit) installed. Use cdk bootstrap "aws://687162148361/us-east-1" to setup 
your environment for use with the toolkit.

Error: CDKToolkit | 7:44:45 AM | CREATE_FAILED        | AWS::S3::Bucket       | 
StagingBucket API: s3:PutPublicAccessBlock Access Denied
- cdk bootstrap

# CDK Setup
- python
- install node js, node and npm gets installed; node --version
- aws cli; aws --version
- aws cdk cli; npm install -g aws-cdk; cdk --version
- ide, vs-code has some useful plugins - Remote Containers Extension and AWS Toolkit Extension
- [visual studio code](https://code.visualstudio.com/docs/?dv=win64user)
- ref: https://github.com/devbyaccident/aws-cdk-course-materials.git

# 




