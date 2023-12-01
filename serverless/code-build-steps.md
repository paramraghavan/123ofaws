# Code build steps for serverless repo/project
* Create the buildspec.yml file for the serverless project
## Step 1: Create a CodeBuild Project
*   Open the AWS CodeBuild console and choose **"Create build project."**
    * Configure the project settings:
    * Project name: Choose a name for your build project.
    * Source: Select the source provider (e.g., AWS CodeCommit, GitHub) and specify the repository that contains your code and the buildspec.yml file.
    * Environment: Choose the operating system, runtime, and image for your build environment.
    * Service role: Ensure that your CodeBuild project has a service role with necessary permissions to access your source repository, fetch from AWS Parameter Store, deploy resources, and any other required permissions.
    * Buildspec: Choose "Use a buildspec file" and ensure your source code has the buildspec.yml in its root directory.
## Step 2: Create a CodePipeline Pipeline
*   Open the AWS CodePipeline console and choose **"Create pipeline."**
    * Configure the pipeline settings:
    * Pipeline name: Give your pipeline a name.
    * Service role: Either select an existing role or allow CodePipeline to create a new role.
    * Source stage:
    * Select the same source provider as your CodeBuild project and configure it to track the branch where your code is located.
      <pre>
       Configure the Source Stage:
         Select the repository and the branch.
         For Change detection options, you usually have two main choices:
         AWS CodePipeline Polling: CodePipeline regularly checks the source 
           repository for changes.
         Webhooks (recommended for GitHub and Bitbucket): Automatically triggered 
          when a change occurs in the repository. This is more efficient and leads to faster pipeline executions.
      </pre>  
    * Build stage:
    * Add a build stage by choosing "Add build stage."
    * In the build stage settings, select "AWS CodeBuild" and choose the CodeBuild project you created earlier.
    * Deploy stage (optional):
    * If your pipeline includes deployment, add a deploy stage and choose the appropriate deployment provider (e.g., AWS CloudFormation, AWS Elastic Beanstalk).
    * Review and create:
    * Review your pipeline configuration and then choose "Create pipeline" to create it.
## Step 3: Triggering the Pipeline
* Automatic Trigger: CodePipeline can be configured to start automatically when a change is pushed to the source repository.
* Manual Trigger: You can manually start the pipeline from the AWS CodePipeline console.
## Step 4: Monitoring and Logging
* CodePipeline Console: Use this to monitor the status of your pipeline's execution.
* CloudWatch Logs: CodeBuild integrates with CloudWatch Logs, where you can view detailed logs of each build.
## Additional Notes:
* Environment Variables: You can pass environment variables to your CodeBuild project through the project settings or directly in the buildspec.yml file.
