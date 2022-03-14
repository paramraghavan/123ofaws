**VPC**

It's like your own private data center. You can think of a VPC as a logically isolated piece of the AWS cloud. When an AWS account is created, you have a default VPC in each AWS Region. A default VPC is ready for you to use so that you don't have to create and configure your own VPC. You can immediately start launching Amazon EC2 instances into your default VPC. You can also use services such as Elastic Load Balancing, Amazon RDS, and Amazon EMR in your default VPC. The default VPC can be deleted and recreated from the console UI .They always have the same IP range and same '1 subnet per AZ's (Availability Zones) architecture. Default VPC with a size /16 IPv4 CIDR block (172.31.0.0/16). This provides up to 65,536 private IPv4 addresses.[more details](https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html)

*Region and VPC*

![image (2)](https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png)

Region can have one or more VPC's. Northern Virgina region is labeled **us-east-1** and it has 6 Availability Zones - us-east-1a, us-east-1b, us-east-1c, us-east-1d, us-east-1e and us-east-1f. When you create an AWS account a default VPC is created for each region, a subnet created in each Availability Zone and you can launch EC2 instance insde this subnet. AWS does allow you to delete default VPC. You can create one or more VPC's as
needed.  [Regions,AvailabilityZones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones). **"I"** above represents an EC2 instance.

Behind the scenes AWS is a massive network infrastructure. Within each availability zone and between availability zones in the same region is a private AWS network. This is highly over-provisioned, highly scalable, and very high throughput. Availability zones are connected and designed for extremely low latency, as if you were in the same data center. At the edge of the private network, AWS utilizes several different public internet providers to ensure high availability, high throughput, and low latency of all network traffic. Amazon also has their own global network backbone which provides region-to-region connection. This ensures privacy, speed, and reliability.

When you create/deploy an EC2 instance through the aws console, you can use the available default VPC and subnet. You can create and assign a security group and NACL - Network Access Control List. The subnet could be a public subnet, meaning EC2 instance can access internet, provided SG and NACL allow. SG, Security Group, are made up of set inbound and outbound rules at instance level within an AZ within a VPC. NACL, Network Access Control List, is applied at subnet level, nacl requires separate inbound and outbound rules. Security Groups are assigned to instances and applied to other instances. NACL are assigned to Subnet.

Traffic to your VPC will come from either an internet gateway or a VPN gateway then it goes to the router. The route table is the next step to determine what to do with that traffic followed by the network access control list, or NACL. Finally, after it's passed through all of these steps, the traffic will go to the security group and specifically the inbound rule of this security group. If the traffic is allowed by the inbound rule, then, and only then, will it go to the instance. 

All instances that are to be accessed via the internet you will need to create and attach an internet gateway to your VPC. This will allow communication from your VPC to the outside internet. You will also define routes to tell the router to send external traffic through the internet gateway, and how to route inbound traffic to your instances example EC2,.. via their public IP addresses. 

**VPC with public subnet**
 
 Following is an internet accessible VPC, a VPC with public subnets.
 For the internet-accessible VPC, you'll start out with a VPC that has a public subnet,
 meaning the `instances in that subnet have public IP addresses. All instances are accessed via the internet, so you'll need to create and attach an internet gateway to your VPC. 
 
 This will allow communication from your VPC to the outside internet. You will also define routes/routing tqble to tell the router to send external traffic through the internet gateway, and how to route inbound traffic to your instances via their public IP addresses. In this scenario, you would need to ensure that your security groups are set up properly so that you don't expose your instances to  risk. You can also configure allow and deny rules in a network access control list - nacl, and attach that to the subnet.

![image](https://user-images.githubusercontent.com/52529498/125168074-9dcddb00-e171-11eb-8e92-4c8f0a7ef92b.png)

***Typical N/w diagram***

 **VPC with public and private subnet, see following picture**

![image](https://user-images.githubusercontent.com/52529498/125170306-7e887b00-e17c-11eb-94ba-81134d2cee4a.png)
 
 Typically you need to define a VPC with both public and private subnets. Your public subnet instances have full access to the internet via the router and internet gateway. Instances in the private subnet, on the other hand, do not have a public IP address. They are only assigned an internal IP address based on the CIDR block of the private subnet. In order to access these instances, you will need to set up a Bastion or a jumpbox or jumphost in your public subnet. 
 Bastion host is a server that you would log into from the internet to then jump to the instances in your private subnet to be able to work on those. This instance could be you EMR master node or EB server. This is accomplished by setting up a route that allows traffic from the public subnet to enter the private subnet. You would still employ security groups and network access control lists, but now the instances in your private subnet have another layer of protection in that t**here is no direct route from the internet to access those instances because they have no public IP address**.

 If you need to access the external public internet from your private subnet to perform patches or maintenance, **you'll need to create a NAT(Network Address Translation) gateway** and attach it to your subnet. A NAT gateway allows requests to be initiated from instances in your private subnet to go out to the internet and receive a response. It does not, however, allow requests from the outside internet to be initiated and reach your instances inside of your private subnet. This is a very common architecture for applications that have multiple instances that serve different roles. For example, backend database or application servers that do not need to receive traffic from the public internet can be in your private subnet. This allows these to be managed differently and to be more secure than if they were in the public subnet. 
 
 We can also add additional access to the private subnet via a VPN connection. You would use this if you wanted to have your on-premises network have an easier way to access your private subnet without having to go through the public internet, through a Bastion host, and into your private subnet. 
 
 To create a VPN connection, you would set up a customer gateway in your on-premises network, and a VPN gateway in your VPC. These two gateways could then be connected via a VPN connection. This allows you to communicate from your on-premises network to instances in your private subnet using the internal IP address of those instances. In many cases, this is more convenient than setting up and maintaining a Bastion host and allows private subnets to essentially become an extension of your on-premises data center. 

**See Pictures Below**
- Default VPC, CIDR block assigned to default VPC is **172.31.0.0/16**
![image](https://user-images.githubusercontent.com/52529498/137606958-956256de-0ccc-410b-82d7-e3ec6ae49b3b.png)

- Default VPC goes across all the AZ's, default subnet as well created. VPC and route table id are same. There 6 different subnet id's
![image](https://user-images.githubusercontent.com/52529498/137607039-4ec285b8-0ef7-4841-8241-3c8e6f73418a.png)


# AWS Services and VPC
- By default, Lambda functions are not launched within a virtual private cloud (VPC), so they can only connect to public resources
  accessible through the internet.
- This is not how most Amazon cloud services operate. For example, EC2 instances can only be accessed within a VPC -- same 
  goes for internal application load balancers. When launching a database with Amazon Relational Database Service (RDS), it's
  considered a best practice to only allow authorized components within a VPC to connect to a specific database instance. In 
  addition, services such as ElastiCache, Elastic File System and DynamoDB Accelerator only allow access within a VPC. 
- There are a number of services that support public access, but AWS has introduced the ability to allow VPC-only access
  using private endpoints. Some examples include S3, DynamoDB, API Gateway, Elastic MapReduce, Athena, CodeBuild and 
  CodePipeline, among others. 
- If a Lambda function is required to operate within a VPC -- an increasingly common scenario -- then it needs to be 
  configured in a particular way. To do this, you need to assign a VPC to the Lambda function, then assign one 
  or more subnets, as well as the accompanying VPC security groups.
- [VPC endpoint](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/centralized-access-to-vpc-private-endpoints.html)
- [more](https://www.techtarget.com/searchcloudcomputing/answer/How-do-I-configure-AWS-Lambda-functions-in-a-VPC)




**Notes**
- https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
- https://aws.amazon.com/vpc/faqs/
- http://cidr.xyz
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones
- https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html





