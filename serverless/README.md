# Quick Notes
<pre>
# install aws cli
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
$ curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
$ sudo installer -pkg AWSCLIV2.pkg -target /

# brew install npm
npm install -g serverless
# create serverless.yml using tempalte  
serverless create --template aws-python3 --name aws --path aws

cd aws
# make sure you have python 3.10 installed
brew install python@3.10
virtualenv venv --python=python3.10
venv\Scripts\activate

Our last step before deploying is to add the serverless-python-requirements plugin. Create a 
package.json file for saving your node dependencies. Accept the defaults, then install the 
plugin.

(venv) npm init # creates package.json
# update serverless.yml as needed.

# lambda deploy
(venv) $ serverless deploy # sls print, serverless deploy -v --stage dev
# remove sls deployed code  
$ sls remove 
#serverless package -v --stage dev ****
</pre>

# Rest vs HTTP API endpoints
## Rest API 
<pre>

In AWS (Amazon Web Services), there are two primary types of API endpoints you can create using Amazon 
API Gateway: REST APIs and HTTP APIs. Both serve to create scalable and secure APIs for applications,
but they have different features and use cases. 
</pre>
## REST API
<pre>
Purpose:
  Best for APIs that require a range of features like API keys, request validation, request and response transformations, etc.
Features: 
  Supports a wider range of API Gateway features, including API keys, request validation, AWS IAM permissions,
  Lambda authorizers, and more.
Use Case: 
  Ideal for scenarios where you need complex API setups, legacy system support, or specific API Gateway 
  features not available in HTTP APIs.
</pre>

## HTTP API 
<pre>
Purpose:
  Best for building high-performance, cost-effective HTTP APIs.
Features: 
  Faster and cheaper than REST APIs but with limited features. Offers native support for OIDC and OAuth 2.0 authorization, and payload format versioning.
Use Case:
  Ideal for simple, straightforward HTTP APIs, where performance and cost are a priority over extensive API Gateway features.  
</pre>

# Serverless links
- [Serverless install guide](https://www.serverless.com/framework/docs/getting-started)
- [Serveless Hello World](https://www.serverless.com/framework/docs/providers/aws/examples/hello-world/python)
- [Serverless Example(s)](https://github.com/serverless/examples/)
- [Serverless Tutorial](https://www.serverless.com/examples)
- https://github.com/aws-samples/serverless-samples/
- https://github.com/aws-samples/serverless-samples/tree/main/serverless-rest-api

