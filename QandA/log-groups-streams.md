# Explain with example cloudwatch log group and cloudwatch log stream when/how to use each on of these

CloudWatch Log Groups and Log Streams organize AWS logging hierarchically:

Log Group are:

- Container for Log Streams
- Typically represents an application or service
- Defines retention, permissions, and metrics settings

Log Stream:

- Individual sequence of logs within a Group
- Usually represents a specific instance/container/process
- Maintains chronological order of events

Example scenario with a web application:

```
Log Group: /aws/production/web-app
└── Log Streams:
    ├── web-server-instance-1
    │   └── "GET /api/users - 200 OK"
    │   └── "Database connection successful"
    ├── web-server-instance-2
    │   └── "POST /api/orders - 201 Created"
    └── web-server-instance-3
        └── "Memory usage: 75%"
```

Usage:

- Create separate Log Groups for different applications/environments
- Create new Log Streams for each instance/container
- Use Log Groups for setting retention/permissions
- Use Log Streams to isolate and track specific instance logs

Common naming patterns:

```
/env/service/component
/aws/lambda/function-name
/aws/ecs/cluster/container-name
```

## Using an aws resource ec2 , lambda explain the above
Let me illustrate with EC2 and Lambda examples:

EC2 Example:
```
Log Group: /aws/ec2/web-application
└── Log Streams:
    ├── i-0abc123def456 (Instance 1)
    │   └── "Apache access logs: 192.168.1.1 - GET /index.html"
    │   └── "System metrics: CPU 80%"
    ├── i-0xyz789uvw123 (Instance 2)
    │   └── "Apache error logs: PHP memory limit exceeded"
    └── i-0pqr456stu789 (Instance 3)
        └── "Security logs: Failed SSH attempt"
```

Lambda Example:
```
Log Group: /aws/lambda/order-processing
└── Log Streams:
    ├── 2024/01/23/[$VERSION]abc123def456 (Invocation 1)
    │   └── "START RequestId: abc123"
    │   └── "Processing order #12345"
    │   └── "END RequestId: abc123"
    ├── 2024/01/23/[$VERSION]xyz789uvw123 (Invocation 2)
    │   └── "START RequestId: xyz789"
    │   └── "Order validation failed"
    └── 2024/01/23/[$VERSION]pqr456stu789 (Invocation 3)
        └── "REPORT RequestId: pqr456 Duration: 234ms"
```

Key differences:
- EC2: Streams typically represent individual instances
- Lambda: Streams represent function invocations, automatically created with timestamp and version

## when searching for logs in cloudwatch logs should i use log groups or log streams
You should primarily search using Log Groups first, then filter within specific Log Streams. Here's why:

1. Log Groups are high-level containers - search here to:
- Find all logs for a specific application/service
- Search across multiple instances/invocations
- Apply broader time-based filters

2. Log Streams - use these after identifying relevant Log Groups to:
- Debug specific instance/invocation issues
- Track chronological sequence of events
- Filter logs from a particular source

Example search flow:
1. Search Log Group `/aws/ec2/web-application` for "error"
2. Identify affected Stream `i-0abc123def456`
3. Filter that Stream for detailed investigation

