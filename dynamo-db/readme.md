# DynamoDB Complete Guide: Concept to Implementation

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Terminology Mapping](#terminology-mapping)
3. [Primary Keys](#primary-keys)
4. [Table Creation](#table-creation)
5. [Search Patterns](#search-patterns)
6. [Global Secondary Indexes](#global-secondary-indexes)
7. [Operation Comparison](#operation-comparison)

---

## Core Concepts

### Fundamental Shift from SQL to DynamoDB

| SQL / Relational | DynamoDB / NoSQL |
|---|---|
| Model entities first | Model access patterns first |
| Normalize data | Denormalize data |
| Use joins at read time | Store related data together |
| Query flexibility | Query speed at scale |
| Schema-first design | Key-design-first design |

**Golden Rule**: In DynamoDB, design your table around the questions your application needs to answer, not around the entity model.

---

## Terminology Mapping

| SQL | DynamoDB | Notes |
|---|---|---|
| Table | Table | Container for items |
| Row | Item | One record (max 400 KB) |
| Column | Attribute | Named data element |
| Primary Key | Partition Key | Used to distribute data |
| Composite Key | Partition Key + Sort Key | Groups related items |
| Index | GSI / LSI | Alternative query pattern |

**Key Size Limits**:
- Partition Key: Max 2,048 bytes
- Sort Key: Max 1,024 bytes
- Item size: Max 400 KB total

---

## Primary Keys

### Concept 1: Partition Key Only

**Design**: Single attribute that uniquely identifies each item

```
PK = UserID
```

**Use when**:
- You primarily retrieve items by a single ID
- Each item is standalone
- No range queries needed

**Example data**:
```
UserID = U001 | Name = Alice | Email = alice@example.com
UserID = U002 | Name = Bob   | Email = bob@example.com
UserID = U003 | Name = Carol | Email = carol@example.com
```

---

### Concept 2: Partition Key + Sort Key (Composite Key)

**Design**: Two attributes working together
- Partition Key: Identifies the group
- Sort Key: Orders items within the group

```
PK = CustomerID
SK = OrderDate
```

**Use when**:
- Multiple related items share same partition key
- You need range queries (date ranges, prefixes)
- You model one-to-many relationships
- Items should be grouped and sorted

**Example data** (All items with CustomerID=C123):
```
PK=C123  SK=2024-01-05  Amount=50    [Order 1]
PK=C123  SK=2024-02-10  Amount=75    [Order 2]
PK=C123  SK=2024-03-15  Amount=100   [Order 3]
PK=C456  SK=2024-01-20  Amount=25    [Order 4]
```

**Item Collection**: All items with the same Partition Key are stored together and sorted by Sort Key.

---

## Table Creation

### Method 1: AWS CLI

```bash
# Simple table - Partition Key only
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions \
    AttributeName=UserID,AttributeType=S \
  --key-schema \
    AttributeName=UserID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

```bash
# Composite table - Partition Key + Sort Key
aws dynamodb create-table \
  --table-name Orders \
  --attribute-definitions \
    AttributeName=CustomerID,AttributeType=S \
    AttributeName=OrderDate,AttributeType=S \
  --key-schema \
    AttributeName=CustomerID,KeyType=HASH \
    AttributeName=OrderDate,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Parameters explained**:
- `HASH` = Partition Key
- `RANGE` = Sort Key
- `S` = String, `N` = Number, `B` = Binary
- `PAY_PER_REQUEST` = On-demand billing (flexible)

---

### Method 2: Boto3 (Python)

```python
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Partition Key Only
table = dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {'AttributeName': 'UserID', 'KeyType': 'HASH'}  # Partition Key
    ],
    AttributeDefinitions=[
        {'AttributeName': 'UserID', 'AttributeType': 'S'}  # String
    ],
    BillingMode='PAY_PER_REQUEST'  # On-demand pricing
)

print(f"Table created: {table.table_name}")
table.wait_until_exists()
```

```python
# Partition Key + Sort Key
table = dynamodb.create_table(
    TableName='Orders',
    KeySchema=[
        {'AttributeName': 'CustomerID', 'KeyType': 'HASH'},   # Partition Key
        {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}    # Sort Key
    ],
    AttributeDefinitions=[
        {'AttributeName': 'CustomerID', 'AttributeType': 'S'},
        {'AttributeName': 'OrderDate', 'AttributeType': 'S'}
    ],
    BillingMode='PAY_PER_REQUEST'
)

print(f"Table created: {table.table_name}")
table.wait_until_exists()
```

---

### Method 3: CloudFormation (Infrastructure as Code)

```yaml
AWSTemplateFormatVersion: '2010-09-09'

Resources:
  # Simple Partition Key table
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: Users
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: UserID
          AttributeType: S
      KeySchema:
        - AttributeName: UserID
          KeyType: HASH

  # Composite Key table
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: Orders
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: CustomerID
          AttributeType: S
        - AttributeName: OrderDate
          AttributeType: S
      KeySchema:
        - AttributeName: CustomerID
          KeyType: HASH
        - AttributeName: OrderDate
          KeyType: RANGE
```

---

### Practical Example: Complete Table with Multiple Attributes

```python
# Create a realistic Orders table
table = dynamodb.create_table(
    TableName='Orders',
    KeySchema=[
        {'AttributeName': 'CustomerID', 'KeyType': 'HASH'},
        {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'CustomerID', 'AttributeType': 'S'},
        {'AttributeName': 'OrderDate', 'AttributeType': 'S'}
    ],
    BillingMode='PAY_PER_REQUEST'
)

table.wait_until_exists()

# Insert items with various attributes
table.put_item(Item={
    'CustomerID': 'C001',
    'OrderDate': '2024-01-15',
    'OrderID': 'ORD-1001',           # Non-key attribute
    'Status': 'Completed',            # Non-key attribute
    'Amount': 150.50,                 # Non-key attribute
    'Items': ['Widget-A', 'Widget-B'] # Non-key attribute (list)
})

table.put_item(Item={
    'CustomerID': 'C001',
    'OrderDate': '2024-02-20',
    'OrderID': 'ORD-1002',
    'Status': 'Pending',
    'Amount': 75.25,
    'Items': ['Widget-C']
})

table.put_item(Item={
    'CustomerID': 'C002',
    'OrderDate': '2024-01-10',
    'OrderID': 'ORD-1003',
    'Status': 'Completed',
    'Amount': 200.00,
    'Items': ['Widget-A', 'Widget-B', 'Widget-D']
})
```

---

## Search Patterns

### Pattern 1: Search by Partition Key ONLY

**Scenario**: Retrieve all orders for a specific customer

**Operation**: `Query` (fast, efficient)

```python
response = table.query(
    KeyConditionExpression='CustomerID = :cid',
    ExpressionAttributeValues={
        ':cid': 'C001'
    }
)

# Returns all items where CustomerID = C001
for item in response['Items']:
    print(f"Order: {item['OrderDate']} | Amount: {item['Amount']} | Status: {item['Status']}")

# Output:
# Order: 2024-01-15 | Amount: 150.5 | Status: Completed
# Order: 2024-02-20 | Amount: 75.25 | Status: Pending
```

**AWS CLI**:
```bash
aws dynamodb query \
  --table-name Orders \
  --key-condition-expression "CustomerID = :cid" \
  --expression-attribute-values '{":cid":{"S":"C001"}}' \
  --region us-east-1
```

**Cost**: Only reads items with matching partition key (efficient)

---

### Pattern 2: Search by Partition Key + Sort Key Condition

**Scenario**: Retrieve orders for a customer within a date range

**Operation**: `Query` with Sort Key condition (very fast)

```python
from datetime import datetime

response = table.query(
    KeyConditionExpression='CustomerID = :cid AND OrderDate BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':cid': 'C001',
        ':start': '2024-01-01',
        ':end': '2024-02-29'
    }
)

for item in response['Items']:
    print(f"{item['OrderDate']} | {item['Amount']} | {item['Status']}")

# Output (only orders in date range):
# 2024-01-15 | 150.5 | Completed
# 2024-02-20 | 75.25 | Pending
```

**Sort Key Operators Available**:
- `=` : Exact match
- `<` : Less than
- `<=` : Less than or equal
- `>` : Greater than
- `>=` : Greater than or equal
- `BETWEEN` : Range
- `begins_with` : Prefix match

**Example: Orders starting with 'ORD-1'**:
```python
response = table.query(
    KeyConditionExpression='CustomerID = :cid AND OrderID begins_with :prefix',
    ExpressionAttributeValues={
        ':cid': 'C001',
        ':prefix': 'ORD-1'
    }
)
```

**AWS CLI**:
```bash
aws dynamodb query \
  --table-name Orders \
  --key-condition-expression "CustomerID = :cid AND OrderDate BETWEEN :start AND :end" \
  --expression-attribute-values '{
    ":cid":{"S":"C001"},
    ":start":{"S":"2024-01-01"},
    ":end":{"S":"2024-02-29"}
  }' \
  --region us-east-1
```

**Cost**: Only reads items matching both conditions (very efficient)

---

### Pattern 3: Search by Both Partition Key AND Sort Key (Exact Match)

**Scenario**: Retrieve ONE specific order

**Operation**: `GetItem` (fastest, single item lookup)

```python
response = table.get_item(
    Key={
        'CustomerID': 'C001',
        'OrderDate': '2024-01-15'
    }
)

item = response['Item']
print(f"Order: {item['OrderID']}")
print(f"Amount: {item['Amount']}")
print(f"Status: {item['Status']}")

# Output:
# Order: ORD-1001
# Amount: 150.5
# Status: Completed
```

**AWS CLI**:
```bash
aws dynamodb get-item \
  --table-name Orders \
  --key '{
    "CustomerID":{"S":"C001"},
    "OrderDate":{"S":"2024-01-15"}
  }' \
  --region us-east-1
```

**Cost**: Reads only ONE item (most efficient)

---

### Pattern 4: Search by Sort Key ONLY (Without Partition Key)

**Scenario**: Find an order by its Order ID (don't know customer)

**Problem**: DynamoDB Query REQUIRES partition key

**Solution**: Use Scan (slow) OR create a Global Secondary Index

#### Option 4A: Scan (Not Recommended for Large Tables)

```python
response = table.scan(
    FilterExpression='OrderID = :oid',
    ExpressionAttributeValues={
        ':oid': 'ORD-1002'
    }
)

for item in response['Items']:
    print(f"Found: {item['CustomerID']} | {item['OrderDate']}")

# Output:
# Found: C001 | 2024-02-20
```

**⚠️ Warning**: Scan reads ENTIRE table before filtering. On large tables:
- Slow performance
- High read costs
- Not suitable for user-facing queries

**Cost**: Reads ALL items, then filters (expensive)

---

#### Option 4B: Create Global Secondary Index (Recommended)

**Index Design**: Use OrderID as partition key

```python
# Create table with GSI
table = dynamodb.create_table(
    TableName='Orders',
    KeySchema=[
        {'AttributeName': 'CustomerID', 'KeyType': 'HASH'},
        {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'CustomerID', 'AttributeType': 'S'},
        {'AttributeName': 'OrderDate', 'AttributeType': 'S'},
        {'AttributeName': 'OrderID', 'AttributeType': 'S'}  # For GSI
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'OrderID-Index',
            'KeySchema': [
                {'AttributeName': 'OrderID', 'KeyType': 'HASH'}  # GSI Partition Key
            ],
            'Projection': {'ProjectionType': 'ALL'},  # Project all attributes
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    ],
    BillingMode='PROVISIONED',
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)
```

**Query the GSI**:
```python
response = table.query(
    IndexName='OrderID-Index',
    KeyConditionExpression='OrderID = :oid',
    ExpressionAttributeValues={
        ':oid': 'ORD-1002'
    }
)

for item in response['Items']:
    print(f"Order {item['OrderID']}: Customer {item['CustomerID']} | {item['Amount']}")

# Output:
# Order ORD-1002: Customer C001 | 75.25
```

**Cost**: Only reads items with matching OrderID (efficient)

---

### Pattern 5: Search by Non-Key Attribute (Status, Amount, etc.)

**Scenario**: Find all pending orders

**Problem**: Status is NOT a key attribute

**Solution**: Scan OR create GSI

#### Option 5A: Scan (Not Recommended)

```python
response = table.scan(
    FilterExpression='#status = :status',
    ExpressionAttributeNames={
        '#status': 'Status'  # 'Status' is reserved word
    },
    ExpressionAttributeValues={
        ':status': 'Pending'
    }
)

for item in response['Items']:
    print(f"{item['CustomerID']} | {item['OrderDate']} | Pending")
```

**Cost**: Reads ALL items, filters afterward (expensive)

---

#### Option 5B: Create GSI for Status (Recommended)

```python
# Add Status GSI to table
client = boto3.client('dynamodb', region_name='us-east-1')

client.update_table(
    TableName='Orders',
    AttributeDefinitions=[
        {'AttributeName': 'Status', 'AttributeType': 'S'}
    ],
    GlobalSecondaryIndexUpdates=[
        {
            'Create': {
                'IndexName': 'Status-Index',
                'KeySchema': [
                    {'AttributeName': 'Status', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        }
    ]
)
```

**Query the GSI**:
```python
response = table.query(
    IndexName='Status-Index',
    KeyConditionExpression='#status = :status',
    ExpressionAttributeNames={
        '#status': 'Status'
    },
    ExpressionAttributeValues={
        ':status': 'Pending'
    }
)

for item in response['Items']:
    print(f"{item['CustomerID']} | {item['OrderDate']} | {item['Amount']}")

# Output:
# C001 | 2024-02-20 | 75.25
```

**Cost**: Only reads items with Pending status (efficient)

---

## Global Secondary Indexes

### What is a GSI?

A **Global Secondary Index** allows you to query the table using different partition and sort keys.

### When to Use GSI

| Scenario | Use GSI |
|----------|---------|
| Need to search by attribute other than PK | ✅ YES |
| Need to find items by date (when not PK) | ✅ YES |
| Need to filter by status/category | ✅ YES |
| Need reverse lookup (e.g., by email instead of UserID) | ✅ YES |
| Base table Query already fast | ❌ NO |

### Example: Multiple GSIs

```python
table = dynamodb.create_table(
    TableName='Orders',
    KeySchema=[
        {'AttributeName': 'CustomerID', 'KeyType': 'HASH'},
        {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'CustomerID', 'AttributeType': 'S'},
        {'AttributeName': 'OrderDate', 'AttributeType': 'S'},
        {'AttributeName': 'OrderID', 'AttributeType': 'S'},
        {'AttributeName': 'Status', 'AttributeType': 'S'},
        {'AttributeName': 'Email', 'AttributeType': 'S'}
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'OrderID-Index',
            'KeySchema': [
                {'AttributeName': 'OrderID', 'KeyType': 'HASH'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'IndexName': 'Status-OrderDate-Index',
            'KeySchema': [
                {'AttributeName': 'Status', 'KeyType': 'HASH'},
                {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'IndexName': 'Email-Index',
            'KeySchema': [
                {'AttributeName': 'Email', 'KeyType': 'HASH'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'BillingMode': 'PAY_PER_REQUEST'
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)
```

### GSI Cost Implications

| Index Type | Cost | Use Case |
|---|---|---|
| **No Index** | Low (base table only) | Simple primary key queries |
| **1 GSI** | 2x base cost | One alternative access pattern |
| **3 GSIs** | 4x base cost | Multiple access patterns (search by status, email, OrderID) |
| **Many GSIs** | Very expensive | Reconsider design or use Scan |

**Best Practice**: Create only GSIs for your actual access patterns.

---

## Operation Comparison

### GetItem vs Query vs Scan

```
GetItem
├─ Use: Know full primary key
├─ Speed: ⚡⚡⚡ Fastest
├─ Cost: Reads 1 item
└─ Example: Get customer C001's order on 2024-01-15

Query
├─ Use: Know partition key (and optionally sort key condition)
├─ Speed: ⚡⚡ Very fast
├─ Cost: Reads matching items only
└─ Example: Get all orders for customer C001 in Jan 2024

Scan
├─ Use: Don't know the key (no index available)
├─ Speed: 🐢 Slow (large tables)
├─ Cost: Reads ALL items, then filters
└─ Example: Find all orders with Status = "Pending" (no Status index)
```

### Decision Tree

```
Do you know the full primary key?
    YES  → GetItem
    NO   → Continue

Do you know the partition key?
    YES  → Query
    NO   → Continue

Is the attribute you're searching indexed (GSI)?
    YES  → Query on GSI
    NO   → Scan (expensive!)
```

---

## KeyConditionExpression vs FilterExpression

**KeyConditionExpression**: Applied to KEY attributes (reduces data READ)
- Uses: Partition Key, Sort Key
- Applied BEFORE data is fetched

**FilterExpression**: Applied AFTER data is READ (reduces data RETURNED)
- Uses: Any attribute
- Reads happen first, then filtering

### Example: Difference

```python
# KeyConditionExpression: Efficient
response = table.query(
    KeyConditionExpression='CustomerID = :cid AND OrderDate > :date',
    ExpressionAttributeValues={
        ':cid': 'C001',
        ':date': '2024-01-01'
    }
)
# DynamoDB reads only matching orders (efficient)

# FilterExpression: Less efficient
response = table.query(
    KeyConditionExpression='CustomerID = :cid',
    FilterExpression='OrderDate > :date',  # Applied AFTER reading
    ExpressionAttributeValues={
        ':cid': 'C001',
        ':date': '2024-01-01'
    }
)
# DynamoDB reads ALL orders for C001, then filters by date
# More reads, higher cost!
```

**Rule**: Use FilterExpression only when the Query result is already small.

---

## Real-World Architecture Example

### Scenario: E-commerce Order System

```python
# Table Design
dynamodb = boto3.resource('dynamodb')

table = dynamodb.create_table(
    TableName='Orders',
    KeySchema=[
        {'AttributeName': 'CustomerID', 'KeyType': 'HASH'},
        {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'CustomerID', 'AttributeType': 'S'},
        {'AttributeName': 'OrderDate', 'AttributeType': 'S'},
        {'AttributeName': 'OrderID', 'AttributeType': 'S'},
        {'AttributeName': 'Status', 'AttributeType': 'S'},
        {'AttributeName': 'Email', 'AttributeType': 'S'}
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'OrderID-Index',
            'KeySchema': [{'AttributeName': 'OrderID', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'},
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'IndexName': 'Status-OrderDate-Index',
            'KeySchema': [
                {'AttributeName': 'Status', 'KeyType': 'HASH'},
                {'AttributeName': 'OrderDate', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'IndexName': 'Email-Index',
            'KeySchema': [{'AttributeName': 'Email', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'},
            'BillingMode': 'PAY_PER_REQUEST'
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)

# Access Pattern 1: Get all orders for customer
def get_customer_orders(customer_id):
    return table.query(
        KeyConditionExpression='CustomerID = :cid',
        ExpressionAttributeValues={':cid': customer_id}
    )

# Access Pattern 2: Get specific order
def get_order(customer_id, order_date):
    return table.get_item(Key={
        'CustomerID': customer_id,
        'OrderDate': order_date
    })

# Access Pattern 3: Find order by OrderID
def find_order_by_id(order_id):
    return table.query(
        IndexName='OrderID-Index',
        KeyConditionExpression='OrderID = :oid',
        ExpressionAttributeValues={':oid': order_id}
    )

# Access Pattern 4: Get all pending orders
def get_pending_orders():
    return table.query(
        IndexName='Status-OrderDate-Index',
        KeyConditionExpression='#status = :status',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={':status': 'Pending'}
    )

# Access Pattern 5: Find customer by email
def find_customer_by_email(email):
    return table.query(
        IndexName='Email-Index',
        KeyConditionExpression='Email = :email',
        ExpressionAttributeValues={':email': email}
    )
```

---

## Summary Table

| Pattern | Operation | Speed | Cost | Key Required |
|---------|-----------|-------|------|---|
| Know full PK+SK | GetItem | ⚡⚡⚡ | 1 item read | YES |
| Know PK only | Query | ⚡⚡ | Matching items | YES |
| Know PK + SK condition | Query | ⚡⚡ | Matching items | YES |
| Know SK only | Scan or GSI | 🐢/⚡⚡ | All items / GSI match | NO |
| Know non-key attribute | Scan or GSI | 🐢/⚡⚡ | All items / GSI match | NO |

---

## Interview-Ready Answers

### "What's the difference between Query and Scan?"

> **Query** requires you to know the partition key. It goes directly to that partition and retrieves items efficiently. **Scan** doesn't require a key; it reads through the entire table or index and filters afterward. Query is fast; Scan is slow on large tables.

### "Can you query using only the Sort Key?"

> No. A **Query** always requires an exact partition key value. If you need to search by sort key alone, you either perform a **Scan** (not recommended for large tables) or create a **Global Secondary Index** that uses that attribute as its partition key.

### "When should you use a GSI?"

> Create a GSI when you have a frequent access pattern that doesn't use the table's primary key. For example, if you often search orders by Status or by Email, create GSIs for those attributes. But be careful—each GSI doubles your storage and write costs.

---

## Quick Decision Checklist

```
Before creating a table, answer these:

□ What exact data do I need to read?
□ What key will I know at read time?
□ Do I need range queries or sorting?
□ Do I need alternative lookup patterns?
□ Should each lookup pattern become a GSI?
□ Can I retrieve data in one Query?
□ What are my access patterns (top 3-5)?

Design the table around the answers, not the entity model.
```

