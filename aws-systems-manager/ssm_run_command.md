# AWS Systems Manager Run Command

AWS Systems Manager (SSM) Run Command is a capability within AWS Systems Manager that lets you remotely and securely
manage the configuration of your managed instances. Run Command allows you to automate common administrative tasks and
perform one-time configuration changes at scale.

## Core Features

- **Remote Execution**: Run scripts or commands on multiple EC2 instances or on-premises servers without logging in to
  each one.
- **Security**: Execute commands without requiring direct access to instances or opening inbound ports.
- **Audit Trail**: Automatically logs all commands and their results for compliance and troubleshooting.
- **Access Control**: Integrates with IAM roles to control who can execute what commands on which resources.

## Common Use Cases

1. **Routine Administrative Tasks**
    - Applying patches and updates across fleets of servers
    - Installing or updating applications
    - Executing scripts on multiple instances simultaneously

2. **Configuration Management**
    - Changing system configurations across multiple servers
    - Standardizing settings across environments
    - Deploying configuration files

3. **Operational Maintenance**
    - Restarting services or applications
    - Performing routine cleanup tasks (log rotation, temp file removal)
    - Running system health checks

4. **Incident Response**
    - Collecting diagnostic information during outages
    - Executing emergency security patches
    - Isolating compromised instances or services

5. **Compliance Activities**
    - Running security scans
    - Collecting compliance-related data
    - Verifying system settings meet corporate standards
