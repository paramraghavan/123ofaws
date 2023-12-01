# How to use paramter-store and npx serverless config credentials
To incorporate AWS Parameter Store and the npx serverless config credentials command in your buildspec.yml 
for a serverless application, you need to make sure your build process has the necessary permissions
and steps to access these services. Here's an  buildspec.yml sample:
```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.10
    commands:
      - echo "Installing dependencies"
      - npm install -g serverless
      - pip install awscli

  pre_build:
    commands:
      - echo "Fetching credentials from Parameter Store"
      - export AWS_ACCESS_KEY_ID=$(aws ssm get-parameter --name /serverless/aws/accessKeyId --with-decryption --query "Parameter.Value" --output text)
      - export AWS_SECRET_ACCESS_KEY=$(aws ssm get-parameter --name /serverless/aws/secretAccessKey --with-decryption --query "Parameter.Value" --output text)
      - echo "Setting up Serverless credentials"
      - npx serverless config credentials --provider aws --key $AWS_ACCESS_KEY_ID --secret $AWS_SECRET_ACCESS_KEY

  build:
    commands:
      - echo "Building the serverless application"
      - serverless deploy

artifacts:
  files:
    - .serverless/**

cache:
  paths:
    - '/root/.cache/**/*'
```

## In Details
* install: Installs Serverless Framework and AWS CLI.
  * pre_build:
  * Retrieves AWS credentials stored in AWS Systems Manager Parameter Store.
  * Uses npx serverless config credentials to set up Serverless Framework with the retrieved AWS credentials.
* build: Deploys your serverless application using the Serverless Framework.
* artifacts: Specifies the files or directories to be uploaded as build artifacts.
* cache: Caches dependencies to speed up future builds.
Important Considerations:
*   Permissions: Ensure that the AWS CodeBuild project's service role has sufficient permissions to access the AWS Systems Manager Parameter Store and any other required AWS services.
*   Security: Storing AWS credentials in Parameter Store with encryption is a secure practice. Ensure that these are encrypted and access is tightly controlled.
*   Serverless Framework Version: If your build depends on a specific version of the Serverless Framework, specify that version when installing.
*   Environment Variables: The environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set dynamically during the build process. Make sure no sensitive information is printed to logs.
*   Parameter Store Paths: Replace /serverless/aws/accessKeyId and /serverless/aws/secretAccessKey with the actual paths of your parameters in AWS Parameter Store.
*   AWS CLI Version: The version of AWS CLI installed should be compatible with your project requirements.
*   Build Specification: Adjust the build phase commands according to your deployment process. If you have a more complex deployment, additional commands might be necessary.

