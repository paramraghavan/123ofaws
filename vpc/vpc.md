**You can think of a VPC as a logically isolated piece of the AWS cloud**

It's like your own private data center. Whna an AWS account is creates a default VPC is created once per region.There can only be one default VPC per region, and they can be deleted and recreated from the console UI .They always have the same IP range and same '1 subnet per AZ's (Availability Zones) architecture. Northern virginia - US East (N. Virginia)us-east-1, has 6 AZ's. [Regions,AvailabilityZones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones). **VPC** for US East (N. Virginia) is us-east-1, this has 6 Availability Zones - us-east-1a, us-east-1b, us-east-1c, us-east-1d, us-east-1e, us-east-1f. **I** below represents an EC2  instance

![image (2)](https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png)

Northern Virgina region is labeled **us-east-1** and it has 6 Availability Zones from us-east-1a thru us-east-1f. When you create an AWS account a default VPC is created for each region, a subnet created in each Availability Zone and you can launch EC2 instance insde this subnet. AWS does allow you to delete default VPC. You can create one or more VPC's as
needed

Behind the scenes is a massive network infrastructure. Within each availability zone and between availability zones in the same region is a private AWS network. This is highly over-provisioned, highly scalable, and very high throughput. Availability zones are connected and designed for extremely low latency, as if you were in the same data center. At the edge of the private network, AWS utilizes several different public internet providers to ensure high availability, high throughput, and low latency of all network traffic. Amazon also has their own global network backbone which provides region-to-region connection. This ensures privacy, speed, and reliability.

When you create/deploy an EC2 instance through the aws  console, you can use the available defualt VPC and subnet. You can create and assign a securitry group and Nacl. The subnet could be a public subnet, meaning EC2 instance can access internet, provided SG and NACL allow. SG, Security Group, are made up of set inbount and outbound rules at instance level within an AZ within a VPC. NACL, Network Access Control List, is applied at subnet level, nacl requires separate inbound and outbound rules. Traffic to your VPC will come from either an internet gateway or a VPN gateway then it goes to the router. The route table is the next step to determine what to do with that traffic followed by the network access control list, or NACL. Finally, after it's passed through all of these steps, the traffic will go to the security group and specifically the inbound rule of this security group. If the traffic is allowed by the inbound rule, then, and only then, will it go to the instance. 

All instances that are to be accessed via the internet you will need to create and attach an internet gateway to your VPC. This will allow communication from your VPC to the outside internet. You will also define routes to tell the router to send external traffic through the internet gateway, and how to route inbound traffic to your EC2 instances via their public IP addresses. 

**VPC with public subnet**
 
 Following is an internet accessible VPC, a VPC with both public and private subnets.
 For the internet-accessible VPC, you'll start out with a VPC that has a public subnet,
 meaning the `instances in that subnet have public IP addresses. All instances are accessed via the internet, so you'll need to create and attach an internet gateway to your VPC. 
 
 This will allow communication from your VPC to the outside internet. You will also define routes to tell the router to send external traffic through the internet gateway, and how to route inbound traffic to your instances via their public IP addresses. In this scenario, you would need to ensure that your security groups were set up properly so that you don't expose your instances to unnecessary risk. You can also configure allow and deny rules in a network access control list, and attach that to the subnet.

![image](https://user-images.githubusercontent.com/52529498/125168074-9dcddb00-e171-11eb-8e92-4c8f0a7ef92b.png)

***Typical N/w diagram***

![image](https://user-images.githubusercontent.com/52529498/125170306-7e887b00-e17c-11eb-94ba-81134d2cee4a.png)

 **VPC with public and private subnet, see above diagram**
 
 Typically you need to define a VPC with both public and private subnets, and usually multiple. Your public subnet instances have full access to the internet via the router and internet gateway. Instances in the private subnet, on the other hand, do not have a public IP address. They are only assigned an internal IP address based on the CIDR block of the private subnet. In order to access these instances, you'll need to set up a Bastion or a jumpbox/jumphost in your public subnet. 
 Bastion host is a server that you would log into from the internet to then jump to the instances in your private subnet to be able to work on those. This is accomplished by setting up a route that allows traffic from the public subnet to enter the private subnet. You would still employ security groups and network access control lists, but now the instances in your private subnet have another layer of protection in that there is no direct route from the internet to access those instances because they have no public IP address.

 If you need to access the external public internet from your private subnet to perform patches or maintenance, you'll need to create a NAT(Network Address Translation) gateway and attach it to your subnet. A NAT gateway allows requests to be initiated from instances in your private subnet to go out to the internet and receive a response. It does not, however, allow requests from the outside internet to be initiated and reach your instances inside of your private subnet. This is a very common architecture for applications that have multiple instances that serve different roles. For example, backend database or application servers that do not need to receive traffic from the public internet can be in your private subnet. This allows these to be managed differently and to be more secure than if they were in the public subnet. 
 
 We can also add additional access to the private subnet via a VPN connection. You would use this if you wanted to have your on-premises network have an easier way to access your private subnet without having to go through the public internet, through a Bastion host, and into your private subnet. 
 
 To create a VPN connection, you would set up a customer gateway in your on-premises network, and a VPN gateway in your VPC. These two gateways could then be connected via a VPN connection. This allows you to communicate from your on-premises network to instances in your private subnet using the internal IP address of those instances. In many cases, this is more convenient than setting up and maintaining a Bastion host and allows private subnets to essentially become an extension of your on-premises data center. 



**Notes**
- https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
- https://aws.amazon.com/vpc/faqs/
- http://cidr.xyz





