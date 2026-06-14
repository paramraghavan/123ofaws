Here is the combined and cleaned-up version. I kept your strong original explanation, added the clearer **GetItem vs
Query vs Scan** section, and softened “Scan = danger” into a more accurate production warning. Your attached/pasted note
was treated as the source text to revise.

# DynamoDB Quick Rundown for SQL Developers

Transitioning from the relational world of SQL to the NoSQL world of DynamoDB requires a fundamental shift in how you
think about data.

The biggest hurdle is not the syntax. It is the architecture.

In SQL, you usually model entities first, normalize them, and use joins later. In DynamoDB, you start with your
application’s **access patterns** — the exact questions your application needs to answer — and design the table around
those queries.

## 1. Core Philosophy Shift

| SQL / Relational       | DynamoDB / NoSQL            |
|------------------------|-----------------------------|
| Model entities first   | Model access patterns first |
| Normalize data         | Denormalize data            |
| Use joins at read time | Store related data together |
| Query flexibility      | Query speed at scale        |
| Schema-first design    | Key-design-first design     |

DynamoDB works best when you know queries like:

```text
Get user by user ID
Get all orders for a customer
Get orders for a customer between two dates
Get latest payments for an account
Get events by device and timestamp
```

## 2. Terminology Mapping

| SQL           | DynamoDB                 | Notes                                                                                   |
|---------------|--------------------------|-----------------------------------------------------------------------------------------|
| Table         | Table                    | Same basic idea, but DynamoDB tables are flexible/schemaless except for key attributes. |
| Row           | Item                     | One record. Maximum item size is 400 KB.                                                |
| Column        | Attribute                | Non-key attributes can vary from item to item.                                          |
| Primary Key   | Partition Key            | Used to distribute and locate data.                                                     |
| Composite Key | Partition Key + Sort Key | Groups related items together and sorts them.                                           |
| Index         | GSI / LSI                | Lets you query the same data using a different key pattern.                             |

DynamoDB’s maximum item size is **400 KB**, including attribute names and values. ([AWS Documentation][1])

## 3. Primary Keys: The Biggest Mental Hurdle

In SQL, a primary key often just uniquely identifies a row.

In DynamoDB, the primary key controls how data is stored, distributed, and retrieved.

### Partition Key Only

Example:

```text
PK = UserID
```

Good for direct key-value lookup.

Example item:

```text
UserID = U123
Name = Diya
Email = diya@example.com
```

Use this when you usually retrieve one item by one known ID.

## 4. Partition Key + Sort Key

A composite key uses:

```text
Partition Key + Sort Key
```

Example:

```text
PK = CustomerID
SK = OrderDate
```

Multiple items can share the same partition key, as long as their sort keys are different.

Example:

```text
PK=Customer#123   SK=Order#2024-01-05
PK=Customer#123   SK=Order#2024-02-10
PK=Customer#123   SK=Payment#2024-02-12
PK=Customer#456   SK=Order#2024-01-15
```

This creates an **item collection**: all related items for the same partition key.

This is how DynamoDB models one-to-many relationships without joins.

## 5. GetItem vs Query vs Scan

This is one of the most important DynamoDB concepts.

```text
GetItem = I know the full primary key.
Query   = I know the partition key and maybe a sort key condition.
Scan    = I do not know the key, so DynamoDB must search the table.
```

## 6. GetItem

Use **GetItem** when you know the complete primary key.

If the table key is:

```text
PK = CustomerID
SK = OrderID
```

Then you must provide both:

```text
CustomerID = 123
OrderID = 1005
```

SQL equivalent:

```sql
SELECT *
FROM Orders
WHERE CustomerID = 123
  AND OrderID = 1005;
```

DynamoDB operation:

```text
GetItem
PK = 123
SK = 1005
```

Result:

```text
Returns exactly one item, or no item.
```

## 7. Query: SELECT by Key Condition

Use **Query** when you know the partition key and optionally want to apply a condition on the sort key.

DynamoDB Query requires the partition key value. You can optionally narrow results using the sort key with operators
like `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, or `begins_with`. ([AWS Documentation][2])

Example table:

```text
PK = CustomerID
SK = OrderDate
```

Data:

```text
PK=123   SK=2024-01-05
PK=123   SK=2024-02-10
PK=123   SK=2024-03-15
PK=456   SK=2024-01-20
```

### Example 1: Get all orders for one customer

SQL:

```sql
SELECT *
FROM Orders
WHERE CustomerID = 123;
```

DynamoDB Query:

```text
PK = 123
```

Returns:

```text
2024-01-05
2024-02-10
2024-03-15
```

### Example 2: Get orders for one customer between two dates

SQL:

```sql
SELECT *
FROM Orders
WHERE CustomerID = 123
  AND OrderDate BETWEEN '2024-02-01' AND '2024-03-31';
```

DynamoDB Query:

```text
PK = 123
SK BETWEEN 2024-02-01 AND 2024-03-31
```

Returns:

```text
2024-02-10
2024-03-15
```

### Example 3: Query using begins_with

Suppose your sort key stores different item types:

```text
PK=CUSTOMER#123   SK=PROFILE
PK=CUSTOMER#123   SK=ORDER#1001
PK=CUSTOMER#123   SK=ORDER#1002
PK=CUSTOMER#123   SK=PAYMENT#9001
```

Query:

```text
PK = CUSTOMER#123
SK begins_with ORDER#
```

Returns only:

```text
ORDER#1001
ORDER#1002
```

This works well in single-table design because related records are stored together under the same partition key.

## 8. Scan

Use **Scan** when you do not know the key and DynamoDB must inspect the table or index.

Example:

```sql
SELECT *
FROM Orders
WHERE Status = 'Pending';
```

If `Status` is not part of the primary key or an index, DynamoDB must check every item.

Think of Scan like this:

```text
for every item in the table:
    check if Status = Pending
```

A Scan reads through the table or index first, then applies filters. It is generally less efficient than Query and can
become expensive on large tables. ([AWS Documentation][3])

Better wording than “Scan is always danger”:

```text
Scan is acceptable for small tables, admin tasks, exports, audits, or background jobs.
Avoid Scan for large tables or user-facing application queries.
```

## 9. CRUD Translation

| SQL Command                              | DynamoDB API | Key Difference                                                                 |
|------------------------------------------|--------------|--------------------------------------------------------------------------------|
| `INSERT INTO table ...`                  | `PutItem`    | Inserts item. If the same key exists, it replaces the whole item.              |
| `SELECT * WHERE full primary key = X`    | `GetItem`    | Fast lookup. Requires the full primary key.                                    |
| `SELECT * WHERE pk = X AND sk condition` | `Query`      | Efficient. Requires exact partition key and optional sort key condition.       |
| `SELECT * WHERE non_indexed_col = Z`     | `Scan`       | Reads the table/index and filters afterward. Avoid for large production paths. |
| `UPDATE table SET col = X WHERE key = Y` | `UpdateItem` | Updates specific attributes.                                                   |
| `DELETE FROM table WHERE key = Y`        | `DeleteItem` | Deletes item by primary key.                                                   |

## 10. KeyConditionExpression vs FilterExpression

SQL developers often expect every `WHERE` clause condition to reduce the read cost. In DynamoDB, that is not always
true.

DynamoDB separates conditions into two main concepts:

## KeyConditionExpression

Used with **Query**.

It applies to key attributes:

```text
Partition Key
Sort Key
```

Rules:

```text
Partition Key must use equality =
Sort Key can use =, <, <=, >, >=, BETWEEN, begins_with
```

Example:

```text
PK = Customer#123
SK BETWEEN Order#2024-01-01 AND Order#2024-12-31
```

This is efficient because DynamoDB goes directly to the matching partition and narrows results by sort key.

## FilterExpression

A **FilterExpression** is applied after DynamoDB has already read the matching data.

Example:

```text
Query:
PK = Customer#123

Filter:
Status = Pending
```

If Customer#123 has 10,000 orders and only 50 are pending, DynamoDB may still read the 10,000 matching items first and
then return only 50.

A Query filter reduces the data returned to your application, but it does not reduce the read work already done by the
Query. AWS also notes that Query can read up to 1 MB before applying a filter expression. ([AWS Documentation][4])

Use FilterExpression only when the initial Query result is already reasonably small.

## 11. Things You Cannot Do Like SQL

### No Joins

DynamoDB does not support joins.

SQL style:

```text
Customers table
Orders table
Payments table
Join them at read time
```

DynamoDB style:

```text
PK=CUSTOMER#123   SK=PROFILE
PK=CUSTOMER#123   SK=ORDER#1001
PK=CUSTOMER#123   SK=ORDER#1002
PK=CUSTOMER#123   SK=PAYMENT#9001
```

Now one Query can retrieve related customer data.

### No Cheap COUNT(*)

A live full-table count can require scanning the table, which can be expensive.

Common workaround:

```text
Maintain a separate metadata item with count values.
Increment/decrement it using UpdateItem.
```

### No GROUP BY

DynamoDB is not designed for ad hoc aggregation like SQL.

Common workarounds:

```text
Aggregate in the application
Pre-calculate totals
Use DynamoDB Streams + Lambda
Export to S3 and analyze with Athena/Glue/Spark
```

## 12. Global Secondary Indexes

A **GSI** lets you query the same table using a different partition key and sort key.

Example base table:

```text
PK = CustomerID
SK = OrderDate
```

This supports:

```text
Get orders by customer
```

But suppose you also need:

```text
Get orders by status
```

You could create a GSI:

```text
GSI_PK = Status
GSI_SK = OrderDate
```

Now you can Query:

```text
Status = Pending
OrderDate between 2024-01-01 and 2024-01-31
```

Without scanning the full table.

## 13. PartiQL Note

Amazon PartiQL lets you use SQL-like syntax against DynamoDB.

Example:

```sql
SELECT *
FROM Orders
WHERE CustomerID = '123';
```

This makes DynamoDB feel familiar, but it does not change how DynamoDB works internally.

If your PartiQL statement does not use a key or index properly, it can still result in an inefficient Scan.

## 14. Final Rule of Thumb

Before creating a DynamoDB table, write down your access patterns.

Ask:

```text
What exact data do I need to read?
What key will I know at read time?
Do I need sorting or range filtering?
Do I need another lookup pattern?
Should that lookup pattern become a GSI?
Can I retrieve the data in one Query?
```

Good DynamoDB design starts with the read patterns, not the entity model.

## 15. Interview-Ready Summary

```text
GetItem:
I know the full primary key and want one item.

Query:
I know the partition key and may use a sort key condition.
This returns one or more related items efficiently.

Scan:
I do not know the key, so DynamoDB must inspect the table or index.
Useful for small/admin/background use cases, but avoid for large user-facing queries.
```

Use this as your final concise DynamoDB note.

[1]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html?utm_source=chatgpt.com "Constraints in Amazon DynamoDB - AWS Documentation"

[2]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.html?utm_source=chatgpt.com "Querying tables in DynamoDB"

[3]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html?utm_source=chatgpt.com "Best practices for querying and scanning data in DynamoDB"

[4]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.FilterExpression.html?utm_source=chatgpt.com "Filter expressions for the Query operation in DynamoDB"

This is one of the **most important DynamoDB interview questions**.

## Short answer

> **If you know only the Sort Key but not the Partition Key, you cannot use a Query.**

You have three options:

1. **Scan the table** (slow and expensive)
2. **Create a Global Secondary Index (GSI)** with that attribute as the partition key
3. **Redesign your table** based on your access patterns

---

# Example

Suppose your table is:

| Partition Key (PK) | Sort Key (SK) | Amount |
|--------------------|---------------|--------|
| Customer123        | Order1001     | 50     |
| Customer123        | Order1002     | 75     |
| Customer456        | Order1001     | 25     |
| Customer789        | Order1003     | 60     |

Notice that **Sort Keys are only unique within a Partition Key**.

```
Customer123
    Order1001
    Order1002

Customer456
    Order1001

Customer789
    Order1003
```

The same `Order1001` exists under different customers.

---

# Case 1: You know both PK and SK

```
PK = Customer123
SK = Order1002
```

Use:

```
GetItem
```

Very fast.

---

# Case 2: You know only PK

```
PK = Customer123
```

Use:

```
Query
```

Returns

```
Order1001
Order1002
```

Still very fast.

---

# Case 3: You know only SK

Suppose you only know

```
Order1002
```

but you **don't know Customer123**.

Can DynamoDB Query?

**No.**

Why?

Because DynamoDB first hashes the **Partition Key** to determine which partition contains the data.

Without the Partition Key, it doesn't know where to look.

It would have to search every partition.

---

# What actually happens?

If you execute

```
Find SK = Order1002
```

DynamoDB effectively does:

```python
for every partition:
    for every item:
        if item.SK == "Order1002":
            return item
```

That is a **Scan**.

---

# Better solution: Create a GSI

Suppose you frequently search by `OrderID`.

Create:

```
Base Table

PK = CustomerID
SK = OrderDate
```

Create a GSI:

```
GSI PK = OrderID
```

Now you can Query:

```
OrderID = 1002
```

DynamoDB goes directly to the GSI partition.

Very fast.

---

# Real-world example

## Base table

```
PK = CUSTOMER#123
SK = ORDER#1001

PK = CUSTOMER#123
SK = ORDER#1002

PK = CUSTOMER#456
SK = ORDER#1005
```

Application asks:

```
Find OrderID = 1002
```

### Without a GSI

```
Scan entire table ❌
```

### With a GSI

```
GSI_PK = OrderID

1001
1002
1005
```

Now use

```
Query
PK = 1002
```

and DynamoDB immediately finds the record.

---

# Interview answer

If asked:

> **"Can you query using only the Sort Key?"**

A strong answer is:

> **No. A DynamoDB `Query` requires an exact Partition Key value. The Sort Key can only be used to further narrow
results within that partition. If I need to search by Sort Key alone, I would either perform a Scan (not recommended for
large tables) or create a Global Secondary Index (GSI) that uses that attribute as its Partition Key.**

## Rule to remember

```text
Know full PK (+ SK if composite)  --> GetItem

Know PK only                      --> Query

Know PK + SK condition            --> Query

Know only SK                      --> Cannot Query
                                     Use Scan or create a GSI

Know neither PK nor SK            --> Scan
```

This "know only the sort key" scenario is one of the classic reasons to add a **GSI** in DynamoDB.
