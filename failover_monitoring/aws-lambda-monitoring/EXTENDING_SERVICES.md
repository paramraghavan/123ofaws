# Extending to New Services - Quick Reference

Step-by-step guide for adding monitoring support for new AWS services or resources.

## Quick Checklist: Adding a New Service

```
1. ☐ Write check function in monitor_lambda.py
2. ☐ Call function in lambda_handler
3. ☐ Add table to dashboard_template.html
4. ☐ Update serverless.yml IAM permissions
5. ☐ Deploy: serverless deploy
6. ☐ Tag resources
7. ☐ Test
```

---

## Template: Adding a New AWS Service

### Step 1: Add Check Function

In `monitor_lambda.py`, copy this template:

```python
def check_new_service():
    """Check NewService resources with matching tag"""
    client = boto3.client('service-name')  # e.g., 'rds', 'dynamodb', 'sns'
    resources = []

    try:
        # List all resources
        # Example: dynamodb.list_tables(), rds.describe_db_instances()
        response = client.list_or_describe_operation()

        for resource in response.get('ResourceListKey', []):  # e.g., 'TableNames', 'DBInstances'
            try:
                # Get resource details
                details = client.describe_or_get_operation(ResourceId=resource)

                # Get tags
                tags = client.list_tags_for_resource(ResourceArn=resource_arn)

                # Check for matching tag
                if has_matching_tag(tags, TAG_NAME):
                    resources.append({
                        'id': resource['id'],
                        'status': resource['status'],
                        'region': extract_region(resource_arn),
                        'other_field': resource.get('field')
                    })

            except ClientError as e:
                resources.append({
                    'id': resource['id'],
                    'status': 'error',
                    'error': str(e)
                })

    except Exception as e:
        print(f"Error in check_new_service: {str(e)}")

    return resources
```

### Step 2: Call in lambda_handler

In `lambda_handler()`, add to results dict:

```python
results = {
    'timestamp': datetime.utcnow().isoformat(),
    's3_buckets': check_s3_buckets(),
    'ec2_instances': check_ec2_instances(),
    'emr_clusters': check_emr_clusters(),
    'new_service': check_new_service(),  # ADD THIS LINE
}
```

### Step 3: Add to Dashboard

In `dashboard_template.html`, add HTML and JavaScript:

```html
<h2>New Service Resources</h2>
<table id="new-service-table"></table>

<script>
    // ... existing code ...

    // Add this line to renderTable calls:
    renderTable('new-service-table', status.new_service || [], ['id', 'status', 'region']);
</script>
```

### Step 4: Update IAM Permissions

In `serverless.yml`, add to `iam.role.statements`:

```yaml
- Effect: Allow
  Action:
    - service:ListResources
    - service:DescribeResource
    - service:ListTagsForResource
  Resource: '*'
```

### Step 5: Deploy

```bash
serverless deploy
```

### Step 6: Tag Resources

```bash
# Example for new service
aws service-name tag-resource \
  --resource-arn arn:... \
  --tags Key=Name,Value=production
```

### Step 7: Test

```bash
# Manual test
serverless invoke -f monitor

# Check output
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/status/latest.json - | jq .new_service
```

---

## Real Examples: Adding Specific Services

### RDS (Relational Database)

```python
def check_rds_databases():
    """Check RDS instances with matching tag"""
    rds = boto3.client('rds')
    databases = []

    try:
        response = rds.describe_db_instances()

        for db in response.get('DBInstances', []):
            try:
                # Get tags
                tags_response = rds.list_tags_for_resource(
                    ResourceName=db['DBResourceIdentifier']
                )
                tags = tags_response.get('TagList', [])

                if has_matching_tag(tags, TAG_NAME):
                    databases.append({
                        'id': db['DBInstanceIdentifier'],
                        'status': db['DBInstanceStatus'],
                        'engine': db['Engine'],
                        'instance_type': db['DBInstanceClass'],
                        'region': db['AvailabilityZone'][:-1]
                    })

            except ClientError as e:
                print(f"Error getting RDS tags: {str(e)}")

    except Exception as e:
        print(f"Error in check_rds_databases: {str(e)}")

    return databases
```

**IAM Permissions:**
```yaml
- Effect: Allow
  Action:
    - rds:DescribeDBInstances
    - rds:ListTagsForResource
  Resource: '*'
```

**Dashboard:**
```html
<h2>RDS Databases</h2>
<table id="rds-table"></table>

<script>
    renderTable('rds-table', status.rds_databases || [],
                ['id', 'status', 'engine', 'instance_type']);
</script>
```

**Tag RDS:**
```bash
aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:my-db \
  --tags Key=Name,Value=production
```

---

### DynamoDB

```python
def check_dynamodb_tables():
    """Check DynamoDB tables with matching tag"""
    dynamodb = boto3.client('dynamodb')
    tables = []

    try:
        response = dynamodb.list_tables()

        for table_name in response.get('TableNames', []):
            try:
                # Get table details
                table_response = dynamodb.describe_table(TableName=table_name)
                table = table_response['Table']

                # Get tags
                tags_response = dynamodb.list_tags_of_resource(
                    ResourceArn=table['TableArn']
                )
                tags = tags_response.get('Tags', [])

                if has_matching_tag(tags, TAG_NAME):
                    tables.append({
                        'name': table_name,
                        'status': table['TableStatus'],
                        'items': table.get('ItemCount', 0),
                        'size_gb': round(table.get('TableSizeBytes', 0) / (1024**3), 2)
                    })

            except ClientError as e:
                print(f"Error checking DynamoDB table {table_name}: {str(e)}")

    except Exception as e:
        print(f"Error in check_dynamodb_tables: {str(e)}")

    return tables
```

**IAM Permissions:**
```yaml
- Effect: Allow
  Action:
    - dynamodb:ListTables
    - dynamodb:DescribeTable
    - dynamodb:ListTagsOfResource
  Resource: '*'
```

**Dashboard:**
```html
<h2>DynamoDB Tables</h2>
<table id="dynamodb-table"></table>

<script>
    renderTable('dynamodb-table', status.dynamodb_tables || [],
                ['name', 'status', 'items', 'size_gb']);
</script>
```

**Tag DynamoDB:**
```bash
aws dynamodb tag-resource \
  --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/my-table \
  --tags Key=Name,Value=production
```

---

### SNS Topics

```python
def check_sns_topics():
    """Check SNS topics with matching tag"""
    sns = boto3.client('sns')
    topics = []

    try:
        response = sns.list_topics()

        for topic in response.get('Topics', []):
            try:
                topic_arn = topic['TopicArn']

                # Get tags
                tags_response = sns.list_tags_for_resource(ResourceArn=topic_arn)
                tags = tags_response.get('Tags', [])

                if has_matching_tag(tags, TAG_NAME):
                    # Get subscription count
                    subs_response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
                    sub_count = len(subs_response.get('Subscriptions', []))

                    topics.append({
                        'name': topic_arn.split(':')[-1],
                        'arn': topic_arn,
                        'subscriptions': sub_count,
                        'status': 'active'
                    })

            except ClientError as e:
                print(f"Error checking SNS topic: {str(e)}")

    except Exception as e:
        print(f"Error in check_sns_topics: {str(e)}")

    return topics
```

**IAM Permissions:**
```yaml
- Effect: Allow
  Action:
    - sns:ListTopics
    - sns:ListTagsForResource
    - sns:ListSubscriptionsByTopic
  Resource: '*'
```

**Dashboard:**
```html
<h2>SNS Topics</h2>
<table id="sns-table"></table>

<script>
    renderTable('sns-table', status.sns_topics || [],
                ['name', 'subscriptions', 'status']);
</script>
```

**Tag SNS:**
```bash
aws sns tag-resource \
  --resource-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --tags Key=Name,Value=production
```

---

### Lambda Functions

```python
def check_lambda_functions():
    """Check Lambda functions with matching tag"""
    lambda_client = boto3.client('lambda')
    functions = []

    try:
        response = lambda_client.list_functions()

        for func in response.get('Functions', []):
            try:
                # Get tags
                func_arn = func['FunctionArn']
                tags_response = lambda_client.list_tags(Resource=func_arn)
                tags_dict = tags_response.get('Tags', {})

                # Convert dict tags to list format for has_matching_tag
                tags_list = [{'Key': k, 'Value': v} for k, v in tags_dict.items()]

                if has_matching_tag(tags_list, TAG_NAME):
                    # Get function status
                    config = lambda_client.get_function_concurrency(FunctionName=func_arn)

                    functions.append({
                        'name': func['FunctionName'],
                        'runtime': func['Runtime'],
                        'memory': func['MemorySize'],
                        'timeout': func['Timeout'],
                        'status': 'active'
                    })

            except ClientError as e:
                print(f"Error checking Lambda {func['FunctionName']}: {str(e)}")

    except Exception as e:
        print(f"Error in check_lambda_functions: {str(e)}")

    return functions
```

**IAM Permissions:**
```yaml
- Effect: Allow
  Action:
    - lambda:ListFunctions
    - lambda:ListTags
    - lambda:GetFunctionConcurrency
  Resource: '*'
```

**Dashboard:**
```html
<h2>Lambda Functions</h2>
<table id="lambda-table"></table>

<script>
    renderTable('lambda-table', status.lambda_functions || [],
                ['name', 'runtime', 'memory', 'timeout', 'status']);
</script>
```

**Tag Lambda:**
```bash
aws lambda tag-resource \
  --resource arn:aws:lambda:us-east-1:123456789012:function:my-function \
  --tags Name=production
```

---

### ECS Clusters & Services

```python
def check_ecs_services():
    """Check ECS services with matching tag"""
    ecs = boto3.client('ecs')
    services = []

    try:
        # List clusters
        clusters_response = ecs.list_clusters()
        clusters = clusters_response.get('clusterArns', [])

        for cluster_arn in clusters:
            try:
                # List services in cluster
                services_response = ecs.list_services(cluster=cluster_arn)
                service_arns = services_response.get('serviceArns', [])

                for service_arn in service_arns:
                    # Get service details
                    detail_response = ecs.describe_services(
                        cluster=cluster_arn,
                        services=[service_arn]
                    )
                    service = detail_response['services'][0]

                    # Get tags
                    tags_response = ecs.list_tags_for_resource(resourceArn=service_arn)
                    tags = tags_response.get('tags', [])

                    if has_matching_tag(tags, TAG_NAME):
                        services.append({
                            'name': service['serviceName'],
                            'cluster': cluster_arn.split('/')[-1],
                            'status': service['status'],
                            'task_count': service['runningCount']
                        })

            except ClientError as e:
                print(f"Error checking ECS cluster: {str(e)}")

    except Exception as e:
        print(f"Error in check_ecs_services: {str(e)}")

    return services
```

**IAM Permissions:**
```yaml
- Effect: Allow
  Action:
    - ecs:ListClusters
    - ecs:ListServices
    - ecs:DescribeServices
    - ecs:ListTagsForResource
  Resource: '*'
```

---

### ElastiCache (Redis/Memcached)

```python
def check_elasticache_clusters():
    """Check ElastiCache clusters with matching tag"""
    elasticache = boto3.client('elasticache')
    clusters = []

    try:
        response = elasticache.describe_cache_clusters(ShowCacheNodeInfo=True)

        for cluster in response.get('CacheClusters', []):
            try:
                # Get tags
                cluster_arn = cluster['ARN']
                tags_response = elasticache.list_tags_for_resource(ResourceName=cluster_arn)
                tags = tags_response.get('TagList', [])

                if has_matching_tag(tags, TAG_NAME):
                    clusters.append({
                        'id': cluster['CacheClusterId'],
                        'engine': cluster['Engine'],
                        'status': cluster['CacheClusterStatus'],
                        'node_type': cluster['CacheNodeType'],
                        'nodes': len(cluster.get('CacheNodes', []))
                    })

            except ClientError as e:
                print(f"Error checking ElastiCache: {str(e)}")

    except Exception as e:
        print(f"Error in check_elasticache_clusters: {str(e)}")

    return clusters
```

---

## Pattern Summary

Every service check follows this pattern:

```
┌─────────────────────────────────────────┐
│  1. Create boto3 client                 │
│  2. List/describe all resources         │
│  3. For each resource:                  │
│     - Get resource details              │
│     - Get resource tags                 │
│     - Check for matching tag            │
│     - Extract relevant fields           │
│     - Add to results list               │
│  4. Return results list                 │
└─────────────────────────────────────────┘
```

---

## Monitoring New Non-AWS Services

### Snowflake Example

```python
import snowflake.connector

def check_snowflake_warehouses():
    """Check Snowflake warehouses"""
    try:
        conn = snowflake.connector.connect(
            account=os.environ['SNOWFLAKE_ACCOUNT'],
            user=os.environ['SNOWFLAKE_USER'],
            password=os.environ['SNOWFLAKE_PASSWORD']
        )

        cursor = conn.cursor()
        cursor.execute("SHOW WAREHOUSES")
        warehouses = []

        for row in cursor.fetchall():
            warehouse = {
                'name': row[0],
                'status': row[1],
                'size': row[3]
            }
            warehouses.append(warehouse)

        conn.close()
        return warehouses

    except Exception as e:
        print(f"Error in check_snowflake_warehouses: {str(e)}")
        return []
```

**Note:** Add Snowflake client to requirements.txt:
```
snowflake-connector-python
```

---

## Testing New Service Integration

### 1. Test Locally

```bash
# Set environment
export TAG_NAME=production
export LOG_BUCKET=test-bucket

# Run function
python monitor_lambda.py

# Or test specific check
python -c "from monitor_lambda import check_new_service; print(check_new_service())"
```

### 2. Test After Deployment

```bash
# Invoke Lambda
serverless invoke -f monitor

# Check results
aws s3 cp s3://simple-aws-monitoring-logs-ACCOUNT/status/latest.json - | jq .new_service

# View dashboard
# https://...s3-website.amazonaws.com/dashboard/index.html
```

### 3. Check CloudWatch Logs

```bash
serverless logs -f monitor --tail
```

---

## Common Patterns

### Getting Resource ARN

```python
# EC2
arn = f"arn:aws:ec2:region:account:instance/{instance_id}"

# S3
arn = f"arn:aws:s3:::{bucket_name}"

# RDS
db_resource_id = f"arn:aws:rds:region:account:db:{db_name}"

# DynamoDB
arn = f"arn:aws:dynamodb:region:account:table/{table_name}"

# SNS
arn = f"arn:aws:sns:region:account:{topic_name}"

# Lambda
arn = f"arn:aws:lambda:region:account:function:{function_name}"
```

### Extracting Region from ARN

```python
def extract_region(arn):
    """Extract region from ARN"""
    # ARN format: arn:aws:service:region:account:resource
    parts = arn.split(':')
    return parts[3] if len(parts) > 3 else 'unknown'
```

### Converting Tag Formats

Different services return tags in different formats:

```python
# EC2 - returns list of dicts
tags = [{'Key': 'Name', 'Value': 'production'}]

# RDS - returns list of dicts
tags = [{'Key': 'Name', 'Value': 'production'}]

# Lambda - returns dict
tags = {'Name': 'production'}
# Convert to list:
tags_list = [{'Key': k, 'Value': v} for k, v in tags.items()]

# SNS - returns list of dicts
tags = [{'Key': 'Name', 'Value': 'production'}]
```

---

## Troubleshooting

### "Permission denied" errors

Add to `serverless.yml` IAM permissions:
```yaml
- Effect: Allow
  Action:
    - service:*  # Temporary - narrow down later
  Resource: '*'
```

Then check logs:
```bash
serverless logs -f monitor --tail
```

### Resources not showing up

1. **Check tagging:**
   ```bash
   aws service-name list-tags-for-resource --resource-arn arn:...
   ```

2. **Verify TAG_NAME matches exactly (case-sensitive)**

3. **Check Lambda permissions:**
   ```bash
   aws iam get-role-policy --role-name simple-aws-monitoring-us-east-1-lambdaRole --policy-name simple-aws-monitoring-us-east-1-policy
   ```

### Dashboard not updating

```bash
# Check status file
aws s3 cp s3://LOG_BUCKET/status/latest.json - | jq .

# Check CloudWatch logs
serverless logs -f monitor --tail

# Manually trigger
serverless invoke -f monitor --log
```

---

## See Also

- [TAGGING_STRATEGY.md](TAGGING_STRATEGY.md) - Complete tagging guide
- [README.md](README.md) - Main documentation
- [AWS Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Service Quotas](https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html)
