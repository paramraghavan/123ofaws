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

