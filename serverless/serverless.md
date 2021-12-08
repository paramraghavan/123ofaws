# Serverless.com, a serverless framework

## [Python packaging in Lambda with Serverless plugins](https://www.serverless.com/blog/serverless-python-packaging/)
[Serverless and Python Project](serverless/numpy-test/)
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
[Serverless and Flask Project](serverless/my-flask-application)
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
To continue
</pre>
