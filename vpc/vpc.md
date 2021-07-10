You can think of a VPC as a logically isolated piece of the AWS cloud. It's like your own private data center. Whna an AWS account is creates a default VPC is created once per region.There can only be one default VPC per region, and they can be deleted and recreated from the console UI .They always have the same IP range and same '1 subnet per AZ's (Availability Zones) architecture. Northern virginia - US East (N. Virginia)us-east-1, has 6 AZ's. [Regions,AvailabilityZones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones). **VPC** for US East (N. Virginia) is us-east-1, this has 6 Availability Zones - us-east-1a, us-east-1b, us-east-1c, us-east-1d, us-east-1e, us-east-1f. **I** below represents an EC2  instance

![image (2)](https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png)

Northern Virgina region is labeled **us-east-1** and it has 6 Availability Zones from us-east-1a thru us-east-1f. When you create an AWS account a default VPC is created for each region, a subnet created in each Availability Zone and you can launch EC2 instance insde this subnet. AWS does allow you to delete default VPC. You can create one or more VPC's as
needed

Behind the scenes is a massive network infrastructure. Within each availability zone and between availability zones in the same region is a private AWS network. This is highly over-provisioned, highly scalable, and very high throughput. Availability zones are connected and designed for extremely low latency, as if you were in the same data center. At the edge of the private network, AWS utilizes several different public internet providers to ensure high availability, high throughput, and low latency of all network traffic. Amazon also has their own global network backbone which provides region-to-region connection. This ensures privacy, speed, and reliability.

When you create/deploy an EC2 instance through the aws  console, you can use the available defualt VPC and subnet. You can create and assign a securitry group and Nacl. The subnet could be a public subnet, meaning EC2 instance can access internet, provided SG and NACL allow. SG, Security Group, are made up of set inbount and outbound rules at instance level within an AZ within a VPC. NACL, Network Access Control List, is applied at subnet level, nacl requires separate inbound and outbound rules. Traffic to your VPC will come from either an internet gateway or a VPN gateway then it goes to the router. The route table is the next step to determine what to do with that traffic followed by the network access control list, or NACL. Finally, after it's passed through all of these steps, the traffic will go to the security group and specifically the inbound rule of this security group. If the traffic is allowed by the inbound rule, then, and only then, will it go to the instance. 

All instances that are to be accessed via the internet you will need to create and attach an internet gateway to your VPC. This will allow communication from your VPC to the outside internet. You will also define routes to tell the router to send external traffic through the internet gateway, and how to route inbound traffic to your EC2 instances via their public IP addresses. 

![image](https://user-images.githubusercontent.com/52529498/125168074-9dcddb00-e171-11eb-8e92-4c8f0a7ef92b.png)


**Notes**
https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
https://aws.amazon.com/vpc/faqs/
http://cidr.xyz





