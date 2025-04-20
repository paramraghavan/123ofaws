# Example usage of the S3DataManager

from s3_sql import S3DataManager

# Initialize the manager
manager = S3DataManager()

# Example 1: Register datasets from S3
# Register a customer dataset
manager.register_dataset(
    bucket="my-data-bucket",
    prefix="customers/2023",
    table_name="customers",
    format="parquet"
)

# Register an orders dataset
manager.register_dataset(
    bucket="my-data-bucket",
    prefix="orders/2023",
    format="csv",
    table_name="orders",
    options={"header": "true", "inferSchema": "true"}
)

# Example 2: List registered tables
tables = manager.list_tables()
print("Registered tables:")
for table_name, s3_path in tables.items():
    print(f"- {table_name}: {s3_path}")

# Example 3: Preview table data
customer_preview = manager.preview_table("customers", limit=5)
if customer_preview:
    print("\nCustomer data preview:")
    customer_preview.show()

# Example 4: Run SQL queries on the data
# Simple query
result = manager.execute_sql("SELECT COUNT(*) as customer_count FROM customers")
if result:
    print("\nCustomer count:")
    result.show()

# Join query
join_query = """
SELECT 
    c.customer_id,
    c.name,
    COUNT(o.order_id) as order_count,
    SUM(o.amount) as total_spent
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
GROUP BY 
    c.customer_id, c.name
ORDER BY 
    total_spent DESC
LIMIT 10
"""

top_customers = manager.execute_sql(join_query)
if top_customers:
    print("\nTop customers by spending:")
    top_customers.show()

# Example 5: Clean up
manager.unregister_table("customers")
manager.unregister_table("orders")