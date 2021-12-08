# Apache Airflow

Apache Airflow is used for the scheduling and orchestration of data pipelines or workflows. 
Orchestration of data pipelines refers to the sequencing, coordination, scheduling, and 
managing complex data pipelines from diverse sources. These data pipelines deliver data sets
that are ready for consumption either by business intelligence applications and data science,
machine learning models that support big data applications.

In Airflow, these workflows are represented as Directed Acyclic Graphs (DAG). Let’s use a 
pizza-making example to understand what a workflow/DAG is.

![img.png](img.png)

Workflows usually have an end goal like creating visualizations for sales numbers of the last day.  Now, the 
DAG shows how each step is dependent on several other steps that need to be performed first. Like, to knead the
dough, you need flour, oil, yeast, and water. Similarly, for Pizza sauce, you need its ingredients. Similarly,
to create your visualization from past day’s sales, you need to move your data from relational databases to a 
data warehouse.

The analogy also shows that certain steps like kneading the dough and preparing the sauce can be performed
in parallel as they are not interdependent. Similarly, to create your visualizations it may be possible that
you need to load data from multiple sources. Here’s an example of a Dag that generates visualizations from 
previous days’ sales.

![img_1.png](img_1.png)

Efficient, cost-effective, and well-orchestrated data pipelines help data scientists develop better-tuned 
and more accurate ML models, because those models have been trained with complete data sets and not just small
samples. Airflow is natively integrated to work with big data systems such as Hive, Presto, and Spark, making 
it an ideal framework to orchestrate jobs running on any of these engines.  

Organizations are increasingly adopting Airflow to orchestrate their ETL/ELT jobs.




- [Simple Airflow video tutorial](https://www.youtube.com/watch?v=2v9AKewyUEo)
- [github link to above video](https://github.com/soumilshah1995/Learn-Apache-Airflow-in-easy-way-)


## Notes:
- docker image prune,  Cleans up dangling docker images
- docker-compose up —build, Builds airflow service
- docker-compose down, stop airflow service


### Reference
https://www.qubole.com/the-ultimate-guide-to-apache-airflow/

