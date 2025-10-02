On startup detect the instanceids, cluster ids and then run failover

# AWS Failover Manager

A comprehensive AWS infrastructure management tool that monitors EC2 instances and EMR clusters, logs their status, and performs automated failover operations with a Flask-based web dashboard.

## Features

- 🔍 **Auto-detection** of AWS resources:
  - EC2 Instances
  - EMR Clusters
  - RDS Databases
  - Lambda Functions
  - ECS Services
  - ElastiCache (Redis/Memcached)
  - Auto Scaling Groups
- 📊 **Real-time status logging** with detailed tracking
- 🔄 **Automated failover** for all supported AWS services
- 🌐 **Custom resource monitoring** for non-AWS resources (APIs, databases, services)
- 📈 **Web-based log viewer** with analytics dashboard
- 🎯 **AWS Profile support** for multi-account management
- 📝 **Comprehensive logging** (JSONL + text formats)

## Project Structure

```
aws-failover-manager/
├── failover.py           # Main failover script
├── app.py                # Flask web viewer
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html       # Web dashboard template
└── logs/                # Auto-created log directory
    ├── failover.log     # System logs
    ├── status.jsonl     # Status snapshots
    └── failover.jsonl   # Failover operation logs
```

## Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate credentials
- IAM permissions for supported services:
  
  **EC2:**
  - `ec2:DescribeInstances`
  - `ec2:StopInstances`
  - `ec2:StartInstances`
  
  **EMR:**
  - `emr:ListClusters`
  - `emr:DescribeCluster`
  - `emr:TerminateJobFlows`
  - `emr:RunJobFlow`
  - `emr:ListInstanceGroups`
  
  **RDS:**
  - `rds:DescribeDBInstances`
  - `rds:RebootDBInstance`
  
  **Lambda:**
  - `lambda:ListFunctions`
  - `lambda:GetFunctionConfiguration`
  - `lambda:UpdateFunctionConfiguration`
  
  **ECS:**
  - `ecs:ListClusters`
  - `ecs:ListServices`
  - `ecs:DescribeServices`
  - `ecs:UpdateService`
  
  **ElastiCache:**
  - `elasticache:DescribeCacheClusters`
  - `elasticache:RebootCacheCluster`
  
  **Auto Scaling:**
  - `autoscaling:DescribeAutoScalingGroups`
  - `autoscaling:StartInstanceRefresh`

## Installation

1. **Clone or create the project directory**:
```bash
mkdir aws-failover-manager
cd aws-failover-manager
```

2. **Create all required files** (using the code provided in artifacts)

3. **Create the templates directory**:
```bash
mkdir templates
```

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```

5. **Configure AWS profile** (if not using default):
```bash
aws configure --profile your-profile-name
```

6. **Update config.py** with your settings:
```python
AWS_PROFILE = 'your-profile-name'  # or 'default'
AWS_REGION = 'us-east-1'           # your AWS region
```

## Usage

### 1. Run Failover Detection

Basic detection and status logging:
```bash
python failover.py
```

This will:
- Detect all EC2 instances and EMR clusters
- Log their current status
- Generate logs in the `logs/` directory

### 2. Run Automated Failover

To enable automatic failover, edit `failover.py` and uncomment the failover section in the `main()` function:

```python
# Uncomment these lines to enable automatic failover
instance_ids = [i['instance_id'] for i in instances if i['state'] != 'running']
cluster_ids = [c['cluster_id'] for c in clusters if c['state'] != 'RUNNING']

if instance_ids or cluster_ids:
    manager.run_failover(instance_ids=instance_ids, cluster_ids=cluster_ids)
```

### 3. Start the Web Dashboard

```bash
python app.py
```

Access the dashboard at: **http://localhost:5000**

The dashboard provides:
- **AWS Resources**: Real-time view of EC2 instances and EMR clusters
- **Failover Analysis**: Success rates and statistics for failover operations
- **Non AWS Resources**: Health check summary for custom resources
- **Six Log Views**:
  - **AWS Log**: Table view of AWS resource status (EC2, EMR)
  - **AWS Log Detail**: Full JSON logs for AWS resources
  - **Non AWS Log**: Table view of custom resource checks (APIs, databases, services)
  - **Non AWS Log Detail**: Full JSON logs for custom resources
  - **Failover Logs**: Records of all failover operations
  - **System Logs**: Text format logs for debugging

### 4. Programmatic Usage

Use the failover manager in your own scripts:

```python
from failover import AWSFailoverManager

# Initialize with specific profile
manager = AWSFailoverManager(profile_name='production')

# Detect resources
instances = manager.detect_ec2_instances()
clusters = manager.detect_emr_clusters()

# Log status
status = manager.log_status(instances, clusters)

# Option 1: Restart EC2 instances only
manager.run_failover(
    instance_ids=['i-1234567890abcdef0']
)

# Option 2: Restart EMR cluster (terminates and recreates)
new_cluster_id = manager.restart_emr_cluster('j-1234567890ABC')
print(f"New cluster ID: {new_cluster_id}")

# Option 3: Recreate EMR cluster (same as restart, but explicit)
new_cluster_id = manager.recreate_emr_cluster('j-1234567890ABC')

# Option 4: Failover with restart flag
manager.run_failover(
    instance_ids=['i-1234567890abcdef0'],
    cluster_ids=['j-1234567890ABC'],
    restart_clusters=True  # Use restart method for clusters
)

# Option 5: Failover all unhealthy resources
instance_ids = [i['instance_id'] for i in instances if i['state'] != 'running']
cluster_ids = [c['cluster_id'] for c in clusters if c['state'] != 'RUNNING']
manager.run_failover(
    instance_ids=instance_ids,
    cluster_ids=cluster_ids,
    restart_clusters=True
)
```

### 5. Monitoring Custom/Non-AWS Resources

Monitor databases, APIs, web services, and custom resources:

```python
from failover import AWSFailoverManager

manager = AWSFailoverManager()
custom_resources = []

# Check HTTP/HTTPS endpoints
custom_resources.append(
    manager.check_http_endpoint('https://api.example.com/health')
)
custom_resources.append(
    manager.check_http_endpoint('https://www.example.com', expected_status=200)
)

# Check TCP ports (databases, services)
custom_resources.append(
    manager.check_tcp_port('mysql.example.com', 3306)
)
custom_resources.append(
    manager.check_tcp_port('redis.example.com', 6379)
)

# Check database connections
custom_resources.append(
    manager.check_database_connection(
        'mysql',
        host='db.example.com',
        user='monitor',
        password='your-password',
        database='production'
    )
)

custom_resources.append(
    manager.check_database_connection(
        'redis',
        host='cache.example.com',
        port=6379,
        password='redis-password'
    )
)

# Check custom resources with your own functions
def check_disk_space(path='/data', min_free_gb=100):
    import shutil
    stat = shutil.disk_usage(path)
    free_gb = stat.free / (1024**3)
    return free_gb >= min_free_gb

custom_resources.append(
    manager.check_custom_resource(
        'Disk Space',
        check_disk_space,
        path='/var/data',
        min_free_gb=50
    )
)

# Log all custom resource statuses
custom_status = manager.log_custom_status(custom_resources)
print(f"Healthy: {custom_status['summary']['healthy']}")
print(f"Unhealthy: {custom_status['summary']['unhealthy']}")
```

**Supported Resource Types:**
- HTTP/HTTPS endpoints (APIs, web applications)
- TCP ports (databases, application servers)
- Databases (MySQL, PostgreSQL, MongoDB, Redis)
- Custom resources (using your own check functions)

**See `custom_monitor_example.py` for a complete working example.**

## EMR Cluster Operations

### Restart vs Recreate

Both `restart_emr_cluster()` and `recreate_emr_cluster()` perform the same operation (terminate and recreate) since EMR clusters cannot be stopped and started like EC2 instances. The methods are provided for semantic clarity:

- **`restart_emr_cluster()`**: Use when you want to restart a cluster as part of routine maintenance
- **`recreate_emr_cluster()`**: Use when you need to rebuild a cluster after a failure

### Complete Configuration Preservation

When restarting/recreating EMR clusters, the system preserves:

- **Instance Groups**: Master, Core, and Task nodes with exact counts
- **Instance Types**: All processor and memory configurations
- **Market Types**: On-Demand and Spot instances
- **Spot Configurations**: Bid prices and timeout settings
- **Storage**: EBS volume types, sizes, and configurations
- **Networking**: VPC, subnets, and security groups
- **Scaling**: Auto-scaling policies if configured
- **Applications**: Spark, Hadoop, Hive, etc.
- **Custom Configurations**: All cluster-specific settings
- **Tags**: All resource tags for organization

Example log output:
```
INFO - Cluster config - Release: emr-6.10.0
INFO -   MASTER: m5.xlarge (1 instances, ON_DEMAND)
INFO -   CORE: r5.2xlarge (4 instances, SPOT)
INFO -   TASK: c5.4xlarge (10 instances, SPOT)
INFO - New cluster created: j-NEWCLUSTERID
```

## AWS Resource Failover Operations

### EC2 Instances
**Detection:** Automatically finds all EC2 instances or filter by tags  
**Failover:** Stop → Wait for stopped → Start → Wait for running  
**Use case:** Restart hung instances, apply updates

```python
manager.run_failover(instance_ids=['i-1234567890abcdef0'])
```

### EMR Clusters
**Detection:** Lists clusters by state (RUNNING, WAITING, etc.)  
**Failover:** Terminate → Recreate with identical configuration (master/core/task nodes, spot/on-demand, EBS, etc.)  
**Clone:** Create duplicate cluster with new name (keeps original running)  
**Use case:** Recover from cluster failures, apply configuration changes, create test environments

```python
# Recreate (terminates original)
manager.run_failover(cluster_ids=['j-XXXXXXXXXXXXX'], restart_clusters=True)

# Clone (keeps original running)
new_cluster_id = manager.clone_emr_cluster(
    source_cluster_id='j-XXXXXXXXXXXXX',
    new_cluster_name='Production-Clone-2025'
)
print(f"Clone created: {new_cluster_id}")
```

**See the EMR Clone & Recreate Guide artifact for detailed steps and examples.**

### RDS Databases
**Detection:** All RDS instances with engine, class, and Multi-AZ info  
**Failover:** Reboot (optional: force failover to standby for Multi-AZ)  
**Use case:** Apply parameter changes, test failover, recover from issues

```python
# Simple reboot
manager.run_failover(rds_instance_ids=['mydb-instance'])

# Force Multi-AZ failover
manager.run_failover(rds_instance_ids=['mydb-instance'], rds_force_failover=True)
```

### Lambda Functions
**Detection:** All Lambda functions with runtime and state  
**Failover:** Update function configuration to trigger refresh  
**Use case:** Force redeploy, clear function cache, apply environment updates

```python
manager.run_failover(lambda_function_names=['my-function-1', 'my-function-2'])
```

### ECS Services
**Detection:** Services across all clusters with task counts  
**Failover:** Force new deployment (rolling update of all tasks)  
**Use case:** Deploy new task definitions, recover unhealthy tasks

```python
manager.run_failover(ecs_services=[
    ('my-cluster', 'web-service'),
    ('prod-cluster', 'api-service')
])
```

### ElastiCache (Redis/Memcached)
**Detection:** All cache clusters with engine, node type, and status  
**Failover:** Reboot all nodes in the cluster  
**Use case:** Apply parameter changes, clear cache, recover from issues

```python
manager.run_failover(elasticache_cluster_ids=['my-redis-cluster'])
```

### Auto Scaling Groups
**Detection:** All ASGs with capacity and instance counts  
**Failover:** Start rolling instance refresh  
**Use case:** Deploy new AMI, update launch template, replace unhealthy instances

```python
manager.run_failover(asg_names=['my-asg-web-servers'])
```

### Complete Failover Example

Restart all unhealthy resources across all AWS services:

```python
from failover import AWSFailoverManager

manager = AWSFailoverManager()

# Detect all resources
instances = manager.detect_ec2_instances()
clusters = manager.detect_emr_clusters()
rds_instances = manager.detect_rds_instances()
lambda_functions = manager.detect_lambda_functions()
ecs_services = manager.detect_ecs_services()
elasticache_clusters = manager.detect_elasticache_clusters()
auto_scaling_groups = manager.detect_auto_scaling_groups()

# Perform comprehensive failover
manager.run_failover(
    # EC2: restart stopped instances
    instance_ids=[i['instance_id'] for i in instances if i['state'] != 'running'],
    
    # EMR: recreate non-running clusters
    cluster_ids=[c['cluster_id'] for c in clusters if c['state'] != 'RUNNING'],
    restart_clusters=True,
    
    # RDS: reboot unavailable databases with failover
    rds_instance_ids=[r['instance_id'] for r in rds_instances if r['status'] != 'available'],
    rds_force_failover=True,
    
    # Lambda: update inactive functions
    lambda_function_names=[l['function_name'] for l in lambda_functions if l['state'] != 'Active'],
    
    # ECS: restart services with insufficient tasks
    ecs_services=[(e['cluster_name'], e['service_name']) for e in ecs_services 
                  if e['running_count'] < e['desired_count']],
    
    # ElastiCache: reboot unavailable clusters
    elasticache_cluster_ids=[c['cluster_id'] for c in elasticache_clusters 
                            if c['status'] != 'available'],
    
    # ASG: refresh groups with capacity issues
    asg_names=[a['asg_name'] for a in auto_scaling_groups 
              if a['instance_count'] < a['desired_capacity']]
)
```

## Custom Resource Monitoring

The system supports monitoring non-AWS resources alongside AWS infrastructure:

### HTTP/HTTPS Endpoint Checks

Monitor web applications, APIs, and services:

```python
result = manager.check_http_endpoint(
    'https://api.example.com/health',
    timeout=10,
    expected_status=200
)
# Returns: status (HEALTHY/DEGRADED/TIMEOUT/UNREACHABLE), response_time_ms, status_code
```

**Use cases:**
- API health endpoints
- Web application status pages
- Internal service monitoring
- Load balancer checks

### TCP Port Checks

Verify service availability on specific ports:

```python
result = manager.check_tcp_port('db.example.com', 3306, timeout=5)
# Returns: status (OPEN/CLOSED/TIMEOUT), response_time_ms
```

**Use cases:**
- Database server availability (MySQL: 3306, PostgreSQL: 5432, MongoDB: 27017)
- Cache servers (Redis: 6379, Memcached: 11211)
- Application servers (HTTP: 8080, custom ports)
- Message queues (RabbitMQ: 5672, Kafka: 9092)

### Database Connection Checks

Test actual database connectivity and authentication:

```python
# MySQL
result = manager.check_database_connection(
    'mysql',
    host='db.example.com',
    user='monitor',
    password='password',
    database='production'
)

# PostgreSQL
result = manager.check_database_connection(
    'postgresql',
    host='postgres.example.com',
    user='monitor',
    password='password',
    database='app_db'
)

# Redis
result = manager.check_database_connection(
    'redis',
    host='cache.example.com',
    port=6379,
    password='redis-password'
)

# MongoDB
result = manager.check_database_connection(
    'mongodb',
    host='mongo.example.com',
    port=27017,
    username='monitor',
    password='password'
)
```

**Supported databases:** MySQL, PostgreSQL, MongoDB, Redis

**Note:** Requires optional database libraries (see requirements.txt)

### Custom Resource Checks

Define your own health check functions:

```python
def check_queue_size(queue_url, max_size=1000):
    """Check if message queue is within limits"""
    # Your custom logic here
    current_size = get_queue_size(queue_url)
    return current_size < max_size

result = manager.check_custom_resource(
    'Message Queue',
    check_queue_size,
    queue_url='https://sqs.example.com/queue',
    max_size=500
)
```

**Use cases:**
- Disk space monitoring
- Queue size checks
- Custom application metrics
- Third-party service status
- Log file monitoring
- Certificate expiration checks

### Logging Custom Status

Log all custom resource checks with automatic aggregation:

```python
custom_resources = [
    manager.check_http_endpoint('https://api.example.com/health'),
    manager.check_tcp_port('db.example.com', 3306),
    manager.check_database_connection('redis', host='cache.local', port=6379)
]

# Log to custom_resources.jsonl and optionally to status.jsonl
status = manager.log_custom_status(
    custom_resources,
    append_to_status=True  # Also add to main status log
)

print(f"Total: {status['summary']['total_resources']}")
print(f"Healthy: {status['summary']['healthy']}")
print(f"Unhealthy: {status['summary']['unhealthy']}")
```

### Complete Monitoring Example

See `custom_monitor_example.py` for a comprehensive example that shows:
- Checking multiple HTTP endpoints
- Monitoring database ports and connections
- Custom health check functions
- Combined AWS + custom resource monitoring
- Automated alerting for unhealthy resources

## Configuration Options

Edit `config.py` to customize:

```python
# AWS Settings
AWS_PROFILE = 'default'        # AWS profile name
AWS_REGION = 'us-east-1'       # AWS region

# Flask Settings
FLASK_HOST = '0.0.0.0'         # Host to bind (0.0.0.0 for all interfaces)
FLASK_PORT = 5000              # Port number
DEBUG = True                   # Debug mode

# Logging
LOG_DIR = 'logs'               # Log directory path
LOGS_PER_PAGE = 50             # Pagination limit
```

## Environment Variables

You can also use environment variables:

```bash
export AWS_PROFILE=production
export AWS_REGION=eu-west-1
python failover.py
```

## Log Files Explained

### 1. failover.log (Text format)
Standard Python logging output with timestamps, log levels, and messages.

### 2. status.jsonl (JSONL format)
Each line is a JSON object containing:
```json
{
  "timestamp": "2025-09-30T12:00:00",
  "ec2_instances": [...],
  "emr_clusters": [...],
  "summary": {
    "total_ec2": 5,
    "total_emr": 2,
    "ec2_running": 4,
    "emr_active": 2
  }
}
```

### 3. failover.jsonl (JSONL format)
Each line records a failover operation:
```json
{
  "timestamp": "2025-09-30T12:30:00",
  "ec2_results": {
    "i-123abc": "SUCCESS",
    "i-456def": "FAILED"
  },
  "emr_results": {
    "j-789ghi": "j-NEW123"
  }
}
```

### 4. custom_resources.jsonl (JSONL format)
Each line records custom resource checks:
```json
{
  "timestamp": "2025-09-30T12:00:00",
  "custom_resources": [
    {
      "resource_type": "HTTP_ENDPOINT",
      "url": "https://api.example.com/health",
      "status": "HEALTHY",
      "response_time_ms": 45.2
    },
    {
      "resource_type": "TCP_PORT",
      "host": "mysql.example.com",
      "port": 3306,
      "status": "OPEN",
      "response_time_ms": 12.5
    }
  ],
  "summary": {
    "total_resources": 10,
    "healthy": 9,
    "unhealthy": 1
  }
}
```

## API Endpoints

The Flask app exposes these REST endpoints:

**Dashboard & UI:**
- `GET /` - Dashboard UI

**AWS Resources:**
- `GET /api/current-status` - Get latest AWS status
- `GET /api/status-logs?limit=50` - Get AWS status logs
- `GET /api/status-table?limit=100` - Get AWS status in table format
- `GET /api/failover-logs?limit=50` - Get failover operation logs
- `GET /api/analysis/failover` - Get failover analytics

**Custom Resources:**
- `GET /api/custom-resources?limit=50` - Get custom resource logs
- `GET /api/custom-resources-table?limit=100` - Get custom resources in table format
- `GET /api/analysis/custom-resources` - Get custom resource analytics

**System Logs:**
- `GET /api/logs/text?limit=100` - Get system text logs

## Scheduling Automated Runs

### Using Cron (Linux/Mac)

```bash
# Run detection every 15 minutes
*/15 * * * * cd /path/to/aws-failover-manager && /usr/bin/python3 failover.py

# Run failover check hourly
0 * * * * cd /path/to/aws-failover-manager && /usr/bin/python3 failover.py
```

### Using Task Scheduler (Windows)

Create a scheduled task to run `python failover.py` at your desired interval.

### Using AWS Lambda

Deploy `failover.py` as a Lambda function with CloudWatch Events trigger.

## Troubleshooting

### Issue: "No credentials found"
**Solution**: Configure AWS CLI or set environment variables:
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue: "Permission denied" errors
**Solution**: Ensure your IAM role/user has required permissions listed in Prerequisites.

### Issue: "Templates not found" in Flask
**Solution**: Ensure `templates/index.html` exists in the correct directory structure.

### Issue: EMR recreation fails
**Solution**: Check that the original cluster configuration is compatible and all required IAM roles exist.

## Security Best Practices

1. **Use IAM roles** instead of access keys when possible
2. **Restrict permissions** to minimum required (principle of least privilege)
3. **Enable MFA** on AWS accounts
4. **Rotate credentials** regularly
5. **Use VPC** and security groups to restrict Flask app access
6. **Review logs** regularly for unauthorized access attempts
