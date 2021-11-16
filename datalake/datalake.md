# Data Lake 
#### A data lake is a centralized repository that allows you to store structured, semistructured, and unstructured data at any scale.

Amazon S3 is an amazing object container. Like any bucket, you can put content in it in a neat and orderly fashion, or you can just dump it in. But no matter 
how the data gets there, once it’s there, you need a way to organize it in a meaningful way so you can find it when you need it.  *A data lake is an architectural
concept that helps you manage multiple data types from multiple sources, both structured and unstructured, through a single set of tools.* A data lake takes Amazon
S3 buckets and organizes them by categorizing the data inside the buckets. It doesn’t matter how the data got there or what kind it is. You can store both structured
and unstructured data effectively in an Amazon S3 data lake.

Many businesses end up grouping data together into numerous storage locations called silos. These silos are rarely managed and maintained by the same team,
which can be problematic. Inconsistencies in the way data was written, collected, aggregated, or filtered can cause problems when it is compared or combined for processing 
and analysis.
For example, one team may use the address field to store both the street number and street name, while another team might use separate fields for street number and street name.
When these datasets are combined, there is now an inconsistency in the way the address is stored, and it will make analysis very difficult.

But by using data lakes, you can break down data silos and bring data into a single, central repository that is managed by a single team. That gives you a single, consistent 
source of truth. Because data can be stored in its raw format, you don’t need to convert it, aggregate it, or filter it before you store it. Instead, you can leave that 
pre-processing to the system that processes it, rather than the system that stores it. In other words, you don’t have to transform the data to make it usable. You keep the data
in its original form, however it got there, however it was written. When you’re talking exabytes of data, you can’t afford to pre-process this data in every conceivable way it 
may need to be presented in a useful state.

**A single source of truth** - When we talk about truth in relation to data, we mean the trustworthiness of the data. Is it what it should be? Has it
been altered? Can we validate the chain of custody? When creating a single source of truth, we’re creating a dataset, in this case the data lake, which can be used for
all processing and analytics. The bonus is that we know it to be consistent and reliable. It’s trustworthy. Be careful not to let your data lake become a swamp. Enforce proper organization and structure for all data entering the lake.

**Store any type of data, regardless of structure** - Be careful to ensure that data within the data lake is relevant and does not go unused. Train users on how to access the data, and set retention policies to ensure the data stays refreshed.

**Multiple ways to analyse the data** - Be careful to learn how to use data in new ways. Don't limit analytics to typical data warehouse-style analytics. AI and machine learning offer significant insights.

**To sum up what we have discussed so far** - we know that businesses need to easily access and analyze data in a variety of ways, using the tools and frameworks of their choice. Moving data between storage and processing is costly. Amazon S3 data lakes provide a single storage backbone for a solution meeting these requirements and tools for analyzing
the data without requiring movement.

## A data lake is a centralized repository that allows you to store structured, semistructured, and unstructured data at any scale.

![image](https://user-images.githubusercontent.com/52529498/141787594-89b069b7-6a1a-466e-b1d8-36bbf8e53c9b.png)

Data lakes promise the ability to store all data for a business in a single repository. You can leverage data lakes to store large volumes of data instead of persisting that data in data warehouses. Data lakes, such as those built in Amazon S3, are generally less expensive than specialized big data storage solutions. That way, you only pay for the specialized solutions when using them for processing and analytics and not for long-term storage. Your extract, transform, and load (ETL) and analytic process can still access this data for analytics. 

## Benefits of a data lake on AWS

- Are a cost-effective data storage solution. You can durably store a nearly unlimited amount of data using Amazon S3.
- Implement industry-leading security and compliance. AWS uses stringent data security, compliance, privacy, and protection mechanisms.
- Allow you to take advantage of many different data collection and ingestion tools to ingest data into your data lake. These services include Amazon Kinesis for streaming data and AWS Snowball appliances for large volumes of on-premises data.
- Help you to categorize and manage your data simply and efficiently. Use AWS Glue to understand the data within your data lake, prepare it, and load it reliably into data stores. Once AWS Glue catalogs your data, it is immediately searchable, can be queried, and is available for ETL processing.
- Help you turn data into meaningful insights. Harness the power of purpose-built analytic services for a wide range of use cases, such as interactive analysis, data processing using Apache Spark and Apache Hadoop, data warehousing, real-time analytics, operational analytics, dashboards, and visualizations.
- Amazon EMR and data lakes, businesses have begun realizing the power of data lakes. Businesses can place data within a data lake and use their choice of open source distributed processing frameworks, such as those supported by Amazon EMR. Apache Hadoop and Spark are both supported by Amazon EMR, which has the ability to help businesses easily, quickly, and cost-effectively implement data processing solutions based on Amazon S3 data lakes.

## Data lake preparation
*Data scientists spend 60% of their time cleaning and organizing data and 19% collecting data sets.* Data preparation is a huge undertaking. There are no easy answers when it comes to cleaning, transforming, and collecting data for your data lake. However, there are services that can automate many of these time-consuming processes.

Setting up and managing data lakes today can involve a lot of manual, complicated, and time-consuming tasks. This work includes loading the data, monitoring the data flows, setting up partitions for the data, and tuning encryption. You may also need to reorganize data, deduplicate it, match linked records, and audit data over time.


## Data warehouses
A data warehouse is a central repository of structured data from many data sources. This data is transformed, aggregated, and prepared for business reporting and analysis.

![image](https://user-images.githubusercontent.com/52529498/141796149-d5e0eab5-07ac-43ea-8da8-c86bd53bc8a4.png)

A data warehouse is a central repository of information coming from one or more data sources. Data flows into a data warehouse from transactional systems, relational databases, and other sources. These data sources can include structured, semistructured, and unstructured data. These data sources are transformed into structured data before they are stored in the data warehouse.

Data is stored within the data warehouse using a schema. A schema defines how data is stored within tables, columns, and rows. The schema enforces constraints on the data to ensure integrity of the data. The transformation process often involves the steps required to make the source data conform to the schema. Following the first successful ingestion of data into the data warehouse, the process of ingesting and transforming the data can continue at a regular cadence.

Business analysts, data scientists, and decision makers access the data through business intelligence (BI) tools, SQL clients, and other analytics applications. Businesses use reports, dashboards, and analytics tools to extract insights from their data, monitor business performance, and support decision making. These reports, dashboards, and analytics tools are powered by data warehouses, which store data efficiently to minimize I/O and deliver query results at blazing speeds to hundreds and thousands of users concurrently.

## Datamarts
A subset of data from a data warehouse is called a data mart. Data marts only focus on one subject or functional area. A warehouse might contain all relevant sources for an enterprise, but a data mart might store only a single department’s sources. Because data marts are generally a copy of data already contained in a data warehouse, they are often fast and simple to implement.

![image](https://user-images.githubusercontent.com/52529498/141796384-0e76d6a8-81e2-4b62-bf78-40ceb7cf10c9.png)

## Data Lake vs Data Warehouse
<table style="width:100%;"><tbody><tr><td style="width:98.75pt;background:rgb(237, 125, 49);padding:0in 5.4pt;text-align:center;"><p><span style="font-size:20px;"><strong><span style="color:rgb(255, 255, 255);">Characteristics</span></strong></span></p></td><td style="width:2.75in;background:rgb(237, 125, 49);padding:0in 5.4pt;text-align:center;"><p><span style="color:rgb(255, 255, 255);"><strong><span style="font-size:20px;">Data warehouse</span></strong></span></p></td><td style="width:2.75in;background:rgb(237, 125, 49);padding:0in 5.4pt;text-align:center;"><p><span style="font-size:20px;"><strong><span style="color:rgb(255, 255, 255);">Data lake</span></strong></span></p></td></tr><tr><td style="width:98.75pt;background:#FBE4D5;padding:0in 5.4pt 0in 5.4pt;height:.3in;"><p><strong><span style="font-size:15px;">Data</span></strong></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Relational from transactional systems, operational databases, and line of business applications</span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;"><span style="color:rgb(49, 53, 55);">Non-relational a</span>nd relational from IoT devices, websites, mobile apps, social media, and corporate applications</span></p></td></tr><tr><td style="width:98.75pt;background:#FBE4D5;padding:0in 5.4pt 0in 5.4pt;height:.3in;"><p><span style="font-size:15px;"><strong>Schema</strong></span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Designed prior to implementation (schema-on-write)</span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Written at the time of analysis&nbsp;</span><br><span style="font-size:15px;">(schema-on-read)</span></p></td></tr><tr><td style="width:98.75pt;background:#FBE4D5;padding:0in 5.4pt 0in 5.4pt;height:.3in;"><p><span style="font-size:15px;"><strong>Price/<br>performance</strong></span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Fastest query results using higher cost storage</span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Query results getting faster using&nbsp;</span><br><span style="font-size:15px;">low-cost storage</span></p></td></tr><tr><td style="width:98.75pt;background:#FBE4D5;padding:0in 5.4pt 0in 5.4pt;height:.3in;"><p><span style="font-size:15px;"><strong>Data quality</strong></span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Highly curated data that serves as the central version of the truth</span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Any data, which may or may not be curated (e.g., raw data)</span></p></td></tr><tr><td style="width:98.75pt;background:#FBE4D5;padding:0in 5.4pt 0in 5.4pt;height:.3in;"><p><span style="font-size:15px;"><strong>Users</strong></span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Business analysts</span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Data scientists, data developers, and business analysts (using curated data)</span></p></td></tr><tr><td style="width:98.75pt;background:#FBE4D5;padding:0in 5.4pt 0in 5.4pt;height:.3in;"><p><span style="font-size:15px;"><strong>Analytics</strong></span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Batch reporting, BI, and visualizations</span></p></td><td style="width:2.75in;padding:0in 5.4pt;text-align:center;"><p><span style="font-size:15px;">Machine learning, predictive analytics, data discovery, and profiling.</span></p></td></tr></tbody></table>

## Data Processing
Data processing means the collection and manipulation of data to produce meaningful information. Data collection is divided into two parts, data collection and data processing.

![image](https://user-images.githubusercontent.com/52529498/141805926-f1767bb6-bc5a-45dc-a513-f46142b9acdd.png)

## Stream processing
means processing data in a stream—in other words, processing data that’s generated continuously, in small datasets (measured in kilobytes). You would use stream processing when you need real-time feedback or continuous insights. This kind of processing is performed on datasets like IoT sensor data, e-commerce purchases, in-game player activity, clickstreams, or information from social networks.
Many organizations use both types of processing, stream and batch, on the exact same dataset. Stream processing is used to get initial insights and real-time feedback, while batch processing is used to get deep insights from complex analytics. For example, credit card transactions. Have you ever received in text just moments after swiping your card? This is a streaming data fraud prevention alert. This is a stream process that happens in near-real time.

Now another process going on regularly using the same data would be the credit card company processing the days customer fraud prevention alert trends. Same data, two completely different business being met, two different velocities.
Stream processing also comes in two forms: real time and near-real time. Both types involve streaming data, which is, as you know, processed quickly in small batches. The difference comes in the velocity: real-time processing occurs within milliseconds, whereas near-real-time processing occurs within minutes. Processing is always performed against a storage location.

In stream processing, you use multiple services. One service to ingest the constant stream of data, one service to process and analyze the stream and another service to load the data into an analytical data store if required.

In AWS, we have a number of services for this purpose, including Amazon Kinesis Data Firehose and Amazon Kinesis Data Streams, which are used to ingest data streams and load the data stream into analytical data stores. Amazon Kinesis Data Analytics is used to process and analyze the data stream. Amazon Kinesis Data Analytics allows you to choose to query a rolling time window of data, say the last two minutes. The analysis is limited to only those records collected within that window of time. Because of this limitation, analytics on streaming data are often simple aggregates. The result of the analysis is made available to be viewed in a dashboard and/or be stored within an analytical data store. The latency in a stream processing system is seconds to milliseconds. Screaming fast! 

Imagine an advertising company that uses clickstream data from social media to identify product trends. The sheer amount of data produced per second is huge. Collection must be fast enough to gather all data without missing anything. Once collected, this data must be processed just as fast in a continuous stream, so the company can decide which trends to jump on. Rapid collection of data followed by the rapid processing of data is another common challenge. The best solution for this environment is a stream processing system.

## Scheduled or periodic batch processing
Data processing and the challenges associated with it can often be defined by the velocity at which the data must be collected and processed. Batch processing comes in two forms: scheduled and periodic.

Scheduled batch processing is a very large volume of data processed on a regular schedule—hourly, daily or weekly. It is generally the same amount of data each time, so the workloads are predictable. Periodic batch processing occurs at random times, on-demand. These workloads often run once a certain amount of data has been collected. This can make workloads unpredictable and hard to plan around.

It may seem that these processing methods would have a slow velocity. However, just because they are scheduled or periodic does not mean they can take hours to process. They may still require high-velocity processing. For example, when an airplane lands at the airport, the data from the flight computers and the IoT sensors on the engines must be collected and processed. The ground crew has just minutes to determine if the data proves that the plane is ready for another flight.

In batch processing, you use often use a single application to collect, process, and temporarily store data while it is processing. The final step in batch processing is to load the data into an analytical data store.

Amazon EMR, a managed Hadoop framework, uses common tools like Apache Spark and Hive to perform complex data processing. Part of the processing includes performing analytics on the data. In batch analytics, the entire dataset is made available for these analytic queries. This allows for highly complex analytics to be performed. Batch processing is commonly implemented in cases where deep insights and advanced analysis is required. The latency in a batch processing system is minutes to hours, depending on the complexity of the analytics being performed.

Imagine a retail chain is trying to analyze point-of-sale data from its franchise stores. The stores are located all over the world. Each location transmits batches of data to the central data center periodically throughout the day. The customer prefers to hold the analysis of the datasets until 1:15 am Eastern standard time. At that point, all datasets must be rapidly processed so that reports can be generated and delivered to branch managers across the world as soon as possible. Slower collection of data followed by a rapid processing requirement is a common challenge. The best solution for this environment is a batch processing system.

## Batch vs Stream processing
<table style="width:100%;background:white;"><tbody><tr><td style="width:15.58%;background:rgb(237, 125, 49);padding:0in 5.4pt;vertical-align:top;"><br></td><td style="width:40.02%;background:rgb(237, 125, 49);vertical-align:top;text-align:center;"><p><span style="color:rgb(255, 255, 255);"><strong>Batch data processing</strong></span></p></td><td style="width:44.4%;background:rgb(237, 125, 49);vertical-align:top;text-align:center;"><p><span style="color:rgb(255, 255, 255);"><strong>Stream data processing</strong></span></p></td></tr><tr><td style="width:15.58%;padding:0in 5.4pt;vertical-align:top;"><p><strong>Data scope</strong></p></td><td style="width:40.02%;padding:0in 5.4pt;vertical-align:top;"><p>Queries or processing over all or most of the data in the dataset</p></td><td style="width:44.4%;padding:0in 5.4pt;vertical-align:top;"><p>Queries or processing over data within a rolling time window, or on just the most recent data record</p></td></tr><tr><td style="width:15.58%;padding:0in 5.4pt;vertical-align:top;"><p><strong>Data size</strong></p></td><td style="width:40.02%;padding:0in 5.4pt;vertical-align:top;"><p>Large batches of data</p></td><td style="width:44.4%;padding:0in 5.4pt;vertical-align:top;"><p>Individual records or micro batches consisting of a few records</p></td></tr><tr><td style="width:15.58%;padding:0in 5.4pt;vertical-align:top;"><p><strong>Latency</strong></p></td><td style="width:40.02%;padding:0in 5.4pt;vertical-align:top;"><p>Minutes to hours</p></td><td style="width:44.4%;padding:0in 5.4pt;vertical-align:top;"><p>Seconds or milliseconds</p></td></tr><tr><td style="width:15.58%;padding:0in 5.4pt;vertical-align:top;"><p><strong>Analysis</strong></p></td><td style="width:40.02%;padding:0in 5.4pt;vertical-align:top;"><p>Complex analytics</p></td><td style="width:44.4%;padding:0in 5.4pt;vertical-align:top;"><p>Simple response functions, aggregates, and rolling metrics</p></td></tr></tbody></table>


Amazon EMR decouples the collection system from the processing system. This is accomplished by implementing one of two common frameworks: Hadoop or Apache Spark. Both frameworks process high-velocity data but they do it in different ways.

Hadoop running in Amazon EMR, configures a cluster of EC2 instances to serve as a single distributed storage and processing solution. This provides speed, fault tolerance, and the ability to scale the instances supporting collection separately from the instances supporting processing. Hadoop complements existing data systems by simultaneously ingesting and processing large volumes of data, structured or not, from any number of sources. This enables deeper analysis than any one system can provide. The analytical results can be delivered to any existing data store for further use.

Apache Spark is a competing framework to Hadoop. The difference is that Spark uses in-memory caching and optimized execution for faster performance. Analytics are performed by first filtering the data and then aggregating it. Apache Spark avoids writing data to storage, preferring to keep the data in memory at all times. Both Hadoop and Spark support general batch processing, streaming analytics, machine learning, graph databases, and ad hoc queries.

### Simple use case with EMR
Let’s start with a really simple architecture. In this solution, we start with the data sources. Remember, data sources can come from anywhere. The data from these sources is first added to an Amazon S3 bucket. This bucket becomes the repository for all the data that will eventually be processed.

Next, let’s use a processing service called AWS Lambda. Using AWS Lambda, we will create a program to run once every four hours to grab any new data from the Amazon S3 bucket and send it to Amazon EMR - hadoop or SPark, for processing. This program creates the batches.

Once the analytics and processing has been completed, the results are sent to a service called Amazon Redshift. Amazon Redshift is a fast, scalable data warehouse that makes it simple and cost-effective to analyze all your data across your data warehouse and data lake.

### simple use case with Glue etl
AWS Glue is a fully managed ETL service that categorizes, cleans, enriches, and moves your data reliably between various data stores. AWS Glue simplifies and automates difficult and time-consuming data discovery, conversion, mapping, and job-scheduling tasks. In other words, it simplifies data processing.

## Processing big data streams
There are many reasons to use streaming data solutions. In a batch processing system, processing is always asynchronous, and the collection system and processing system are often grouped together. With streaming solutions, the collection system (producer) and the processing system (consumer) are always separate. Streaming data uses what are called data producers. Each of these producers can write their data to the same endpoint, allowing multiple streams of data to be combined into a single stream for processing. Another huge advantage is the ability to preserve client ordering of data and the ability to perform parallel consumption of data. This allows multiple users to work simultaneously on the same data.


## Variety
relational, semi-Structured, unstrucutred, [see section](https://github.com/paramraghavan/Data-Engineering-and-Analytics-with-AWS/blob/main/data.md)

## Veracity
High-quality data is a must-have for organizations that are now relying so heavily upon the insights the data provides. When you have data that is ungoverned, coming from numerous, dissimilar systems and cannot curate the data in meaningful ways, you know you have a veracity problem.

Data veracity is the degree to which data is accurate, precise, and trusted. Data must be properly cleansed and curated, so that reports from that data are accurate. That’s the only way the business can make good decisions from their data.
- **Curation** is the action or process of selecting, organizing, and looking after the items in a collection.
- **Data integrity** is the maintenance and assurance of the accuracy and consistency of data over its entire lifecycle.
- **Data veracity** is the degree to which data is accurate, precise, and trusted.

## Value
When you have massive amounts of data used to support a few golden insights, you may be missing the real value of your data. We are going to discuss what it takes to uncover the value in all your data and bring it out in the form of reports and dashboards.

- **Information analytics** is the process of analyzing information to find the value contained within it. This term is often synonymous with data analytics. Businesses are making thousands of decisions with or without solid information to back them up. The hope, of course, is that there are solid facts that back up each decision. But the unfortunate reality is that decisions are often based upon assumptions. These assumptions may have a basis in reality, but they are still assumptions.<ul> What businesses need is a fast and efficient way to get meaningful information from all of the data they are gathering.</ul> It is a capital mistake to theorize before one has data. Insensibly, one begins to twist the facts to suit theories, instead of theories to suit facts
- **Operational analytics**, Businesses have thousands of systems, applications, and customers that are constantly generating data. This is one of the fastest growing areas of data collection. Operational analytics is a form of analytics that is used specifically to retrieve, analyze, and report on data for IT operations. This data includes system logs, security logs, complex IT infrastructure events and processes, user transactions, and even security threats.








