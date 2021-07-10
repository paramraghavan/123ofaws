You can think of a VPC as a logically isolated piece of the AWS cloud. It's like your own private data center. Whna an AWS account is creates a default VPC is created once per region.There can only be one default VPC per region, and they can be deleted and recreated from the console UI .They always have the same IP range and same '1 subnet per AZ's (Availability Zones) architecture. Northern virginia - US East (N. Virginia)us-east-1, has 6 AZ's. [Regions,AvailabilityZones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-availability-zones). **VPC** for US East (N. Virginia) is us-east-1, this has 6 Availability Zones - us-east-1a, us-east-1b, us-east-1c, us-east-1d, us-east-1e, us-east-1f.

![image (2)](https://user-images.githubusercontent.com/52529498/125163932-88e74c80-e15d-11eb-8a26-16ef92ab1356.png)

Northern Virgina region is labeled **us-east-1** and it has 6 Availability Zones from us-east-1a thru us-east-1f. When you create an AWS account a default VPC is created for each region, a subnet created in each Availability Zone and you can launch EC2 instance insde this subnet. AWS does allow you to delete default VPC. You can create one or more VPC's as
needed

Behind the scenes is a massive network infrastructure. Within each availability zone and between availability zones in the same region is a private AWS network. This is highly over-provisioned, highly scalable, and very high throughput. Availability zones are connected and designed for extremely low latency, as if you were in the same data center. At the edge of the private network, AWS utilizes several different public internet providers to ensure high availability, high throughput, and low latency of all network traffic. Amazon also has their own global network backbone which provides region-to-region connection. This ensures privacy, speed, and reliability.

When you create/deploy an EC2 instance through the aws  console, you can use the available defualt VPC and subnet. You can create and assign a secutiry group and Nacl. The subnet could be a public subnet, meaning EC2 instance can access internet. 


**Notes**
https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
https://aws.amazon.com/vpc/faqs/
http://cidr.xyz





