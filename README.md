# 123ofaws
For lot many of us in IT who have not still started  working on cloud or only getting to cloud service like AWS, Google Cloud, Azure, Oracle Cloud etc.. now, thought of putting something that helps them. Probably be useful for aws beginners and intermediates

- iam
- s3
- lambda
- api gateway
- serverless framework, see serverless.com
- vpc
- ec2
- step functions/state machine
- AWS Fargate

Usually at work we have single AWS account per emvironment(dev/test/acpt/prod) with multiple roles. These roles are assigned to active directory user ids.

Cloud Computing 

 ![image](https://user-images.githubusercontent.com/52529498/125153907-fcb93300-e124-11eb-8d50-9cfbda1cd436.png)
 
ref: https://aws.amazon.com/what-is-cloud-computing/

![image](https://user-images.githubusercontent.com/52529498/125153922-12c6f380-e125-11eb-864c-f74a574e3d9f.png)

**3 models of Cloud computing**
![image](https://user-images.githubusercontent.com/52529498/125153936-21150f80-e125-11eb-8b0c-78b8683bbc6c.png)
 
AWS Elastic Cloud  Compute Service or EC2 is IaaS(Infrastructure as a Service). This is because Amazon takes the responsibility of networking, storage, server and virtualization and the user is responsible for managing the Operating System, middleware, runtime, data and application. In PaaS aka Platform as a Service the user only needs to take care of data and application, the management of rest of the layers lies in hands of the service provider. AWS Elastic BeanStalk is PaaS

![image](https://user-images.githubusercontent.com/52529498/125153939-296d4a80-e125-11eb-9a7a-b6ab9bb4222f.png)

Ref: https://www.quora.com/Is-Amazon-EC2-IaaS-or-PaaS

**Availability Zones(AZ's)**

AWS data centers are organized into Availability Zones (AZ). Each Availability Zone comprises one or more data centers, with some Availability Zones having as many as six data centers. However, no data center can be part of two Availability Zones. Each region will have at least 2 AZ’s

Each Availability Zone is designed as an independent failure zone. This means that Availability Zones are physically separated within a typical metropolitan region and are located in lower-risk flood plains (specific flood-zone categorization varies by region). In addition to having discrete uninterruptable power supply and onsite backup generation facilities, they are each fed via different grids from independent utilities to further reduce single points of failure. Availability Zones are all redundantly connected to multiple tier-1 transit providers.

![image](https://user-images.githubusercontent.com/52529498/125154052-fbd4d100-e125-11eb-87a6-f3a5ce43a9dc.png)

**AWS Regions**

Availability Zones are further grouped into regions. Each AWS Region contains two or more Availability Zones .
When you distribute applications across multiple Availability Zones, be aware of location-dependent privacy and compliance requirements, such as the EU Data Privacy Directive. When you store data in a specific region, it is not replicated outside that region. AWS never moves your data out of the region you put it in. It is your responsibility to replicate data across regions, if your business needs require that. AWS provides information about the country, and—where applicable—the state where each region resides; you are responsible for selecting the region to store data in based on your compliance and network latency requirements.
All communications between regions are across public Internet infrastructure; therefore, use appropriate encryption methods to protect sensitive data.


![image](https://user-images.githubusercontent.com/52529498/125154117-6dad1a80-e126-11eb-9490-683be53e9fc3.png)

**For the latest update click below link**
https://aws.amazon.com/about-aws/global-infrastructure/

AWS edge locations provide local points-of-presence that commonly support AWS services like Amazon Route 53 and Amazon CloudFront. Edge locations help lower latency and improve performance for end users. For a more detailed look at AWS edge locations, see: https://aws.amazon.com/about- aws/global-infrastructure/

For customers who specifically need to replicate their data or applications over greater geographic distances, there are AWS Local Regions. An AWS Local Region is a single datacenter designed to complement an existing AWS Region. Like all AWS Regions, AWS Local Regions are completely isolated from other AWS Regions. 

**Managed vs Unmanaged Services**

![image](https://user-images.githubusercontent.com/52529498/125154267-31c68500-e127-11eb-940c-d7bcd6a1522e.png)

Unmanaged services are typically provisioned in discrete portions as specified by you. Unmanaged services require the user to manage how the service responds to changes in load, errors, and situations where resources become unavailable. For instance, if you launch a web server on an Amazon EC2 instance, that web server will not scale to handle increased traffic load or replace unhealthy instances with healthy ones unless you specify it to use a scaling solution such as Auto Scaling, because Amazon EC2 is an "unmanaged" solution.

However, if you have a static website that you're hosting in a cloud-based storage solution such as Amazon S3 without a web server, those features (scaling, fault- tolerance, and availability) would be automatically handled internally by Amazon S3, because it is a managed solution. Managed services still require the user to configure them (for example, creating an Amazon S3 bucket and setting permissions for it); however, managed services typically require far less configuration.

The benefit to using an unmanaged service, however, is that you have more fine- tuned control over how your solution handles changes in load, errors, and situations where resources become unavailable.

**Example**

![image](https://user-images.githubusercontent.com/52529498/125154352-a3063800-e127-11eb-91ff-4381b9e1c8e8.png)

To apply these categories to AWS services, you can take the examples of running a relational database (such as MySQL, Microsoft SQL Server, PostgreSQL, Oracle, or others) on AWS with either Amazon EC2 or Amazon RDS. Amazon EC2 offers compute resources in the cloud, available on a variety of operating systems. With Amazon EC2, you can host your relational database on an Amazon EC2 instance (using Amazon EBS for storage), but you will have to manage things like your database's ability to scale to keep up with load, backing up your database, as well as patching of both your database software and your instance's operating system. This means you also get more control over these aspects of your database (and others), however. You may want to do this for example you have licenses for Oracle or ss2k etc.

Amazon RDS offers a managed relational database solution on AWS. With Amazon RDS, you can host a MySQL, Microsoft SQL Server, PostgreSQL, MariaDB, Oracle, or Aurora database in an environment where important features such as scaling, patching, and backing up of your databases can be managed by AWS.

**Shared Resposibility**
ref: https://aws.amazon.com/compliance/shared-responsibility-model/

![image](https://user-images.githubusercontent.com/52529498/125154695-3b50ec80-e129-11eb-91d4-640737b03710.png)


**AWS Resposibility: Security of the Cloud**

![image](https://user-images.githubusercontent.com/52529498/125155223-553ffe80-e12c-11eb-9c74-a856d13b7ed2.png)


AWS handles the security of the cloud; specifically, the physical infrastructures that host your resources.
• Data centers: Non descript facilities, 24/7 security guards, two-factor authentication, access logging and review, video surveillance, and disk degaussing and destruction.
•Hardware infrastructure: Servers, storage devices, and other appliances that AWS services rely on.
•Software infrastructure: Host operating systems, service applications, and virtualization software.
•Network infrastructure: Routers, switches, load balancers, firewalls, cabling, etc. (including continuous network monitoring at external boundaries, secure access points, and redundant infrastructure).


**Your Resposibility: Security in the Cloud**

![image](https://user-images.githubusercontent.com/52529498/125155320-f8911380-e12c-11eb-8d67-64fc9ac356e8.png)










