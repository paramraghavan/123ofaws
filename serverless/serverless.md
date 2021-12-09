# Serverless.com, a serverless framework
Login into AWS Console, IAM. Create a aws cli user and apply [policy permissions file](sample_policy.txt) 
this aws cli user. The policy file is a very broad permission file, policies should be as narrow as possible 
and we should loosen the permissions on a as needed basis.

## [Python packaging in Lambda with Serverless plugins](https://www.serverless.com/blog/serverless-python-packaging/)

<pre>
npm install -g serverless
serverless create --template aws-python3 --name numpy-test --path numpy-test

cd numpy-test
virtualenv venv --python=python3
venv\Scripts\activate

(venv) pip install numpy
(venv) pip freeze > requirements.txt
(venv) type requirements.txt

Our last step before deploying is to add the serverless-python-requirements plugin. Create a 
package.json file for saving your node dependencies. Accept the defaults, then install the 
plugin.

(venv) npm init # creates package.json, update with app.py instead of index.js
(venv) $ npm install --save serverless-python-requirements

# lambda deployed --> pp-numpy-test-dev-numpy
(venv) $ serverless deploy # sls print, serverless deploy -v --stage dev
#serverless package -v --stage dev ****
~~~~~~~~
(venv) serverless invoke -f numpy --log

</pre>

## [serverless-lambda-dynamodb](https://www.serverless.com/blog/flask-python-rest-api-serverless-lambda-dynamodb)

<pre>
mkdir my-flask-application && cd my-flask-application
npm init -f

We're going to use the serverless-wsgi plugin for 
negotiating the API Gateway event type into the WSGI format that Flask expects. 
We'll also use the serverless-python-requirements plugin for handling our Python 
packages on deployment.

npm install --save-dev serverless-wsgi serverless-python-requirements

virtualenv venv --python=python3
venv\Scripts\activate

(venv) pip install flask
(venv) pip freeze > requirements.txt
(venv) serverless deploy -v --stage dev
# Lambda deployed and a Api Gateway Endpoint made available as a wrapper to flask endpoint.

# Adding a DynamoDB table with REST-like endpoints

Let's add a DynamoDB table as our backing store.

For this simple example, let's say we're storing Users in a database. We want to store them 
by userId, which is a unique identifier for a particular user.

First, we'll need to configure our serverless.yml to provision the table. This involves 
three parts:
1. Provisioning the table in the resources section;
2. Adding the proper IAM permissions; and
3. Passing the table name as an environment variable so our functions can use it.

</pre>

## Results of the flask application deploy

### Stack Outputs
- GetUserLambdaFunctionQualifiedArn: arn:aws:lambda:us-east-1:xxxxxxxxxxxxxx:function:pp-serverless-flask-dev-getUser:1
- CreateUserLambdaFunctionQualifiedArn: arn:aws:lambda:us-east-1:xxxxxxxxxxxxxx:function:pp-serverless-flask-dev-createUser
:1
- AppLambdaFunctionQualifiedArn: arn:aws:lambda:us-east-1:xxxxxxxxxxxxxx:function:pp-serverless-flask-dev-app:2
- ServiceEndpoint: https://server-name.execute-api.us-east-1.amazonaws.com/dev
- ServerlessDeploymentBucketName: pp-serverless-flask-dev-serverlessdeploymentbucke-xxxxxxxxxxxxxx

- https://server.execute-api.us-east-1.amazonaws.com/dev/createuser/1/param, creates user param with id 1
- https://server.execute-api.us-east-1.amazonaws.com/dev/getuser/1/120921-1, gets user param created above, pass in  id 1 and curr-data-plus-user-id 120921-1