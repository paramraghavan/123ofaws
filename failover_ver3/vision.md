A failover script to detect the status of all the aws resources - ec2 instances , emr clusters - including auto scaling
issues , lambdas for now.  Design such that it is extendable to the other aws resources as well.  
Use the given aws profile to access aws resources. Input to script AWS profile name, 
resource tag Name - used to select only these resources


Log the status of the resources
Ability to rerun or restart the terminated or stopped service - to restart terminated ec2 , emr's , and other resources.
When recreating the terminated EMR it should be exactly like the EMR which got terminated - including 
core and task nodes - spot, on demand instances, use the github repo to check out the bootstrap scripts . 


View status log and  analyse the log using flask html5 based viewer
A tab for summary log in a html table with
columns - Script start time, instance id, tag name, status, type/resource name
Ability to filter by any of the above columns or combination of columns

Another tab with log details

Another with failover logs and system logs


Also add log support for non-aws services - like token renewal, checking snowflake instance to log status and fail over
logs

Use python, flask html5

We run the monitor amd failover as one process  you can run monitor or failover or both one after the other
We first monitor, whatever is not terminated or stopped, we use failover to start or recreate these , or for token if
the token is invalid renew token

Create simple to tool /script. Easy to maintain and extendable as new resources need to be monitored

