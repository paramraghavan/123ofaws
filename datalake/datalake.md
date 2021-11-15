# Data Lake
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
all processing and analytics. The bonus is that we know it to be consistent and reliable. It’s trustworthy.

**To sum up what we have discussed so far** - we know that businesses need to easily access and analyze data in a variety of ways, using the tools and frameworks of their choice. 
Moving data between storage and processing is costly. Amazon S3 data lakes provide a single storage backbone for a solution meeting these requirements and tools for analyzing
the data without requiring movement.



