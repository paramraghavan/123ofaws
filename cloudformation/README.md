# CloudFormation: Infrastructure as Code Complete Guide

## Table of Contents

1. [Quick Start for Beginners](#quick-start-for-beginners)
2. [What is CloudFormation & Why Use It](#what-is-cloudformation--why-use-it)
3. [Real-World Analogy](#real-world-analogy)
4. [Core Concepts Explained](#core-concepts-explained)
5. [Template Structure & Syntax](#template-structure--syntax)
6. [Build & Deploy Workflow](#build--deploy-workflow)
7. [Parameters & User Input](#parameters--user-input)
8. [Outputs & Return Values](#outputs--return-values)
9. [Common AWS Resources](#common-aws-resources)
10. [Intrinsic Functions](#intrinsic-functions)
11. [Mappings & Conditions](#mappings--conditions)
12. [Best Practices](#best-practices)
13. [Common Patterns](#common-patterns)
14. [CloudFormation vs Terraform](#cloudformation-vs-terraform)
15. [Troubleshooting](#troubleshooting)
16. [Advanced Topics](#advanced-topics)

---

## Quick Start for Beginners

### What Is CloudFormation?

CloudFormation is **AWS's native template language** for describing cloud infrastructure. Instead of clicking buttons in AWS console, you write a template (in YAML or JSON) that describes exactly what infrastructure you want. CloudFormation then automatically builds it for you.

**Why This Matters:**
- **AWS-Native**: Built by AWS, understands all AWS services
- **Repeatable**: Same template = same infrastructure every time
- **Versioned**: Track infrastructure changes like code
- **Faster**: Deploy 50 resources in minutes
- **Safer**: Preview changes before applying

### Minimal Example: Your First Stack

```yaml
# template.yaml - CloudFormation template
AWSTemplateFormatVersion: '2010-09-09'
Description: 'My first CloudFormation stack - creates a VPC'

Resources:
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: my-vpc

Outputs:
  VPCId:
    Description: The ID of the VPC
    Value: !Ref MyVPC
    Export:
      Name: MyVPC-ID
```

**To Deploy:**
```bash
# Create stack
aws cloudformation create-stack \
  --stack-name my-first-stack \
  --template-body file://template.yaml

# View stack status
aws cloudformation describe-stacks --stack-name my-first-stack

# Delete stack
aws cloudformation delete-stack --stack-name my-first-stack
```

**Output:**
```
Stack ID: arn:aws:cloudformation:us-east-1:123456789:stack/my-first-stack/abc123
Status: CREATE_IN_PROGRESS → CREATE_COMPLETE
```

---

## What is CloudFormation & Why Use It

### The Problem It Solves

**Without CloudFormation:**
```
Manual steps:
1. Log into AWS console
2. Create VPC (fill form)
3. Create subnet (fill form)
4. Create route table (fill form)
5. Create EC2 instance (fill form)
6. Create security group (fill form)
7. ... repeat 20 more times

Problems:
❌ Slow (takes hours)
❌ Error-prone (forgotten settings)
❌ No version history (can't see what changed)
❌ Team confusion (who created what?)
❌ Can't replicate (next environment different)
```

**With CloudFormation:**
```
Write template once:
- Describes all infrastructure in one file
- Version control (git)
- Deploy to dev/uat/prod with one command
- Automatic rollback if something fails
```

### CloudFormation vs AWS Console

| Aspect | Console | CloudFormation |
|--------|---------|---|
| **Speed** | Hours for 50 resources | Minutes |
| **Repeatability** | Manual each time | Same every time |
| **Team collaboration** | Hard to coordinate | Clear who changed what |
| **Disaster recovery** | Manual rebuild | Re-create stack |
| **Version control** | No history | Full git history |
| **Audit trail** | Limited | Full CloudFormation events |
| **Cost control** | Easy to over-provision | Clear resource definitions |

---

## Real-World Analogy

**CloudFormation is like a LEGO instruction manual:**

- **Template** = The instruction booklet (YAML/JSON)
- **Stack** = The assembled LEGO structure
- **Resources** = Individual LEGO pieces (bricks, connectors)
- **Parameters** = Customization options (colors, sizes)
- **Outputs** = Final dimensions/weight of built structure
- **Intrinsic functions** = Special connectors (Ref, GetAtt, Join)
- **Create stack** = Following instructions to build
- **Update stack** = Modifying existing structure
- **Delete stack** = Tearing down and starting over

**Key insight**: Change the instructions (template) → change the structure (infrastructure). Everything stays synchronized!

---

## Core Concepts Explained

### 1. Stack: The Deployed Infrastructure

A **stack** is a CloudFormation deployment - all the resources created from a single template.

```
One Stack = One Deployment

template.yaml (describes infrastructure)
         ↓
    Create Stack
         ↓
    AWS creates resources
         ↓
    Stack Status: CREATE_COMPLETE
         ↓
    All resources now managed together!
```

**Stack Properties:**
- **Name**: Unique identifier (e.g., `my-vpc-stack`)
- **Status**: CREATE_IN_PROGRESS, CREATE_COMPLETE, UPDATE_IN_PROGRESS, DELETE_IN_PROGRESS, etc.
- **Resources**: All AWS resources created by this stack
- **Outputs**: Values you want returned (IDs, IPs, URLs)
- **Parameters**: Inputs used when creating stack
- **Events**: Full history of all changes

**Multiple Stacks = Complete Isolation:**
```
Dev Stack:
  └─ dev VPC (10.0.0.0/16)
  └─ dev instances (t3.micro)
  └─ dev database (small)

Prod Stack:
  └─ prod VPC (10.1.0.0/16)
  └─ prod instances (t3.large)
  └─ prod database (large)

↑ Completely separate, no interference!
```

### 2. Template: The Infrastructure Blueprint

A **template** is a YAML or JSON file that describes your infrastructure.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'What this template does'

Parameters:
  EnvironmentName:
    Type: String
    Default: dev

Mappings:
  RegionMap:
    us-east-1:
      AMI: ami-123456

Conditions:
  IsProduction: !Equals [!Ref EnvironmentName, prod]

Resources:
  MyResource:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-bucket

Outputs:
  BucketName:
    Value: !Ref MyResource
```

**Three versions of templates:**

| Version | When to Use | Complexity |
|---------|---|---|
| **Abbreviated Syntax** | Learning | Simplest |
| **Full Syntax** | Production | More verbose |
| **YAML Macros** | Advanced | Most powerful |

### 3. Resources: AWS Services You're Creating

A **resource** is an AWS service you want to create: EC2, S3, RDS, VPC, etc.

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-data-bucket
      VersioningConfiguration:
        Status: Enabled
      Tags:
        - Key: Name
          Value: production-data

  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c55b159cbfafe1f0
      InstanceType: t3.micro
      SubnetId: !Ref MySubnet

  MySubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC
      CidrBlock: 10.0.1.0/24
```

**Key Difference from Terraform:**
- Terraform uses `resource "aws_s3_bucket" "name"`
- CloudFormation uses `Type: AWS::S3::Bucket`

Both create the same thing, different syntax!

### 4. Parameters: Making Templates Reusable

**Parameters** are inputs - values you provide when creating/updating the stack.

```yaml
Parameters:
  EnvironmentName:
    Type: String
    Description: Environment name (dev, uat, prod)
    Default: dev
    AllowedValues:
      - dev
      - uat
      - prod

  InstanceCount:
    Type: Number
    Description: Number of EC2 instances
    Default: 1
    MinValue: 1
    MaxValue: 10

  VpcCidr:
    Type: String
    Description: CIDR block for VPC
    Default: 10.0.0.0/16
    AllowedPattern: '^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$'
```

**Using parameters in resources:**
```yaml
Resources:
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr  # ← Use parameter
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-vpc'  # ← Use parameter
```

**Setting parameters when creating stack:**
```bash
# Via CLI
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=prod \
    ParameterKey=InstanceCount,ParameterValue=3

# Via JSON parameters file
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters file://parameters.json
```

---

## Template Structure & Syntax

### YAML vs JSON

**YAML (Recommended - more readable):**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: My infrastructure

Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-bucket
```

**JSON (Alternative):**
```json
{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "My infrastructure",
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket",
      "Properties": {
        "BucketName": "my-bucket"
      }
    }
  }
}
```

Both do the same thing - YAML is just easier to read.

### Complete Template Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: |
  This template creates:
  - VPC with 2 subnets
  - EC2 instance in public subnet
  - RDS database in private subnet

Metadata:
  Author: DevOps Team
  Version: '1.0'

Parameters:
  # User inputs (explained below)

Mappings:
  # Static lookup tables (explained below)

Conditions:
  # Conditional logic (explained below)

Resources:
  # AWS resources to create

Outputs:
  # Return values after creation
```

### Full Example: VPC + Subnet + Instance

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'VPC with EC2 instance'

Parameters:
  EnvironmentName:
    Type: String
    Default: dev
    AllowedValues: [dev, prod]

  InstanceType:
    Type: String
    Default: t3.micro

Resources:
  # VPC
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-vpc'

  # Subnet
  MySubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC  # Reference VPC created above
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-subnet'

  # Internet Gateway
  MyIGW:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-igw'

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref MyVPC
      InternetGatewayId: !Ref MyIGW

  # Security Group
  WebSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow HTTP and HTTPS
      VpcId: !Ref MyVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  # EC2 Instance
  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c55b159cbfafe1f0
      InstanceType: !Ref InstanceType
      SubnetId: !Ref MySubnet
      SecurityGroupIds:
        - !Ref WebSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-webserver'

Outputs:
  VPCId:
    Description: VPC ID
    Value: !Ref MyVPC
    Export:
      Name: !Sub '${EnvironmentName}-VPC-ID'

  SubnetId:
    Description: Subnet ID
    Value: !Ref MySubnet

  InstancePublicIP:
    Description: Public IP of web server
    Value: !GetAtt WebServer.PublicIp

  SecurityGroupId:
    Description: Security Group ID
    Value: !Ref WebSecurityGroup
```

---

## Build & Deploy Workflow

### Step 1: Create Stack (First Deployment)

```bash
# Create stack from template
aws cloudformation create-stack \
  --stack-name my-vpc-stack \
  --template-body file://template.yaml

# Watch stack creation
aws cloudformation describe-stacks \
  --stack-name my-vpc-stack \
  --query 'Stacks[0].StackStatus'

# Shows: CREATE_IN_PROGRESS → CREATE_COMPLETE
```

**With parameters:**
```bash
aws cloudformation create-stack \
  --stack-name prod-stack \
  --template-body file://template.yaml \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=prod \
    ParameterKey=InstanceType,ParameterValue=t3.large
```

### Step 2: Validate Template (Before Creating)

```bash
# Check if template is valid
aws cloudformation validate-template \
  --template-body file://template.yaml

# Output: Shows all parameters, resources, outputs
```

### Step 3: Create Change Set (Preview Changes)

A **change set** shows what will change before you apply it - like Terraform's `plan`.

```bash
# Create change set (don't apply yet)
aws cloudformation create-change-set \
  --stack-name my-vpc-stack \
  --change-set-name my-changes-v1 \
  --template-body file://template.yaml

# View what will change
aws cloudformation describe-change-set \
  --change-set-name my-changes-v1 \
  --stack-name my-vpc-stack

# Shows: "Add MyVPC", "Add MySubnet", etc.

# If looks good, execute it
aws cloudformation execute-change-set \
  --change-set-name my-changes-v1 \
  --stack-name my-vpc-stack

# If bad, delete it
aws cloudformation delete-change-set \
  --change-set-name my-changes-v1 \
  --stack-name my-vpc-stack
```

### Step 4: Update Stack (Modify Existing)

```bash
# Edit template.yaml
# Then update stack

aws cloudformation update-stack \
  --stack-name my-vpc-stack \
  --template-body file://template.yaml

# Watch updates
aws cloudformation describe-stacks \
  --stack-name my-vpc-stack \
  --query 'Stacks[0].StackStatus'

# Shows: UPDATE_IN_PROGRESS → UPDATE_COMPLETE
```

### Step 5: Delete Stack (Cleanup)

```bash
# Delete everything created by stack
aws cloudformation delete-stack \
  --stack-name my-vpc-stack

# Watch deletion
aws cloudformation describe-stacks \
  --stack-name my-vpc-stack \
  --query 'Stacks[0].StackStatus'

# Shows: DELETE_IN_PROGRESS → DELETE_COMPLETE
```

### Full Workflow: Safe Updates

```bash
# 1. Validate template
aws cloudformation validate-template \
  --template-body file://template.yaml

# 2. Create change set (preview)
aws cloudformation create-change-set \
  --stack-name prod-stack \
  --change-set-name v1 \
  --template-body file://template.yaml

# 3. Review what will change
aws cloudformation describe-change-set \
  --stack-name prod-stack \
  --change-set-name v1 | jq '.Changes'

# 4. If safe, execute
aws cloudformation execute-change-set \
  --stack-name prod-stack \
  --change-set-name v1

# 5. Monitor completion
watch -n 5 'aws cloudformation describe-stacks \
  --stack-name prod-stack \
  --query "Stacks[0].[StackStatus,StackStatusReason]"'
```

---

## Parameters & User Input

### Parameter Types

```yaml
Parameters:
  # String
  BucketName:
    Type: String
    Default: my-bucket
    MinLength: 3
    MaxLength: 63
    AllowedPattern: '^[a-z0-9.-]*$'
    Description: S3 bucket name

  # Number
  InstanceCount:
    Type: Number
    Default: 1
    MinValue: 1
    MaxValue: 10
    Description: Number of instances

  # AWS-Specific: Availability Zone
  AvailabilityZone:
    Type: AWS::EC2::AvailabilityZone::Name
    Description: AZ to deploy to
    # User chooses from list of available AZs!

  # AWS-Specific: VPC ID
  VPC:
    Type: AWS::EC2::VPC::Id
    Description: VPC to deploy to
    # User chooses from existing VPCs!

  # AWS-Specific: Subnet
  Subnet:
    Type: AWS::EC2::Subnet::Id
    Description: Subnet for instance
    # User chooses from existing subnets!

  # AWS-Specific: Security Group
  SecurityGroup:
    Type: AWS::EC2::SecurityGroup::Id
    Description: Security group
    # User chooses from existing security groups!

  # Comma-delimited list
  AvailabilityZones:
    Type: List<AWS::EC2::AvailabilityZone::Name>
    Description: Multiple AZs
    # User chooses multiple AZs!
```

### Constraint Examples

```yaml
Parameters:
  # Allowed values (dropdown)
  Environment:
    Type: String
    AllowedValues:
      - dev
      - uat
      - prod
    Default: dev

  # Pattern validation
  Email:
    Type: String
    AllowedPattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    Description: Valid email address

  # Numeric range
  Port:
    Type: Number
    MinValue: 1024
    MaxValue: 65535
    Default: 8080

  # String length
  Password:
    Type: String
    NoEcho: true  # Hide input
    MinLength: 8
    Description: Database password
```

### Using Parameters in Resources

```yaml
Parameters:
  InstanceType:
    Type: String
    Default: t3.micro

  Environment:
    Type: String
    Default: dev

Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType  # Use parameter
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-instance'  # Use in string
        - Key: Environment
          Value: !Ref Environment

  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'bucket-${Environment}-${AWS::AccountId}'
      # Uses: parameter + AWS pseudo parameter
```

---

## Outputs & Return Values

**Outputs** are values you want returned after the stack is created.

```yaml
Outputs:
  VPCId:
    Description: The VPC ID
    Value: !Ref MyVPC
    Export:
      Name: MyVPC-ID  # Can be imported by other stacks!

  WebServerIP:
    Description: Public IP of web server
    Value: !GetAtt WebServer.PublicIp
    Export:
      Name: WebServer-IP

  BucketName:
    Description: Name of S3 bucket
    Value: !Ref MyBucket

  ConnectionString:
    Description: Database connection string
    Value: !Sub 'postgresql://${DBInstance.Endpoint.Address}:5432/mydb'
```

**View outputs after stack creation:**
```bash
# Show all outputs
aws cloudformation describe-stacks \
  --stack-name my-vpc-stack \
  --query 'Stacks[0].Outputs'

# Output:
# [
#   {
#     "OutputKey": "VPCId",
#     "OutputValue": "vpc-12345678",
#     "ExportName": "MyVPC-ID"
#   },
#   {
#     "OutputKey": "WebServerIP",
#     "OutputValue": "52.1.2.3",
#     "ExportName": "WebServer-IP"
#   }
# ]
```

### Exporting Outputs for Other Stacks

```yaml
Outputs:
  VPCId:
    Value: !Ref MyVPC
    Export:
      Name: shared-vpc-id  # Other stacks can import this!
```

**Import in another stack:**
```yaml
Resources:
  MySubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !ImportValue shared-vpc-id  # Import from other stack!
      CidrBlock: 10.0.2.0/24
```

---

## Common AWS Resources

### S3 Bucket

```yaml
Resources:
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'my-data-bucket-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldVersions
            Status: Enabled
            NoncurrentVersionExpirationInDays: 30
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      Tags:
        - Key: Name
          Value: data-bucket
```

### EC2 Instance

```yaml
Resources:
  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c55b159cbfafe1f0
      InstanceType: t3.micro
      SubnetId: !Ref PublicSubnet
      SecurityGroupIds:
        - !Ref WebSecurityGroup
      IamInstanceProfile: !Ref InstanceProfile
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          yum update -y
          yum install -y httpd
          systemctl start httpd
          echo "Hello from ${AWS::Region}" > /var/www/html/index.html
      Tags:
        - Key: Name
          Value: web-server
```

### RDS Database

```yaml
Resources:
  MyDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: my-db
      Engine: postgres
      EngineVersion: '14.7'
      DBInstanceClass: db.t3.micro
      MasterUsername: admin
      MasterUserPassword: !Sub '{{resolve:secretsmanager:my-db-password:SecretString:password}}'
      AllocatedStorage: 20
      StorageType: gp2
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref DBSecurityGroup
      BackupRetentionPeriod: 30
      MultiAZ: false  # Set to true for prod
      StorageEncrypted: true
      Tags:
        - Key: Name
          Value: my-db
```

### VPC & Subnet

```yaml
Resources:
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: my-vpc

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: public-subnet

  PrivateSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      Tags:
        - Key: Name
          Value: private-subnet
```

### Security Group

```yaml
Resources:
  WebSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow HTTP and HTTPS
      VpcId: !Ref MyVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
          Description: HTTP
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
          Description: HTTPS
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          SourceSecurityGroupId: !Ref BastionSecurityGroup
          Description: SSH from bastion
      SecurityGroupEgress:
        - IpProtocol: -1
          CidrIp: 0.0.0.0/0
          Description: Allow all outbound
      Tags:
        - Key: Name
          Value: web-sg
```

### Lambda Function

```yaml
Resources:
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: my-function
      Runtime: python3.11
      Handler: index.handler
      Role: !GetAtt LambdaRole.Arn
      Code:
        ZipFile: |
          import json
          def handler(event, context):
              return {
                  'statusCode': 200,
                  'body': json.dumps('Hello from Lambda!')
              }
      Environment:
        Variables:
          ENVIRONMENT: !Ref EnvironmentName
          BUCKET_NAME: !Ref DataBucket

  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

---

## Intrinsic Functions

Intrinsic functions are built-in functions that work with stack data.

### Ref: Get Reference to Resource

```yaml
# Get resource ID
VPCId: !Ref MyVPC
# Returns: vpc-12345678

# Get parameter value
Environment: !Ref EnvironmentName
# Returns: prod
```

### GetAtt: Get Resource Attributes

```yaml
# Get specific attribute from resource
WebServerIP: !GetAtt WebServer.PublicIp
# Returns: 52.1.2.3

DBEndpoint: !GetAtt MyDatabase.Endpoint.Address
# Returns: my-db.c1234567890.us-east-1.rds.amazonaws.com

DBPort: !GetAtt MyDatabase.Endpoint.Port
# Returns: 5432
```

### Sub: String Substitution

```yaml
# Simple substitution
BucketName: !Sub 'my-bucket-${AWS::AccountId}'
# Returns: my-bucket-123456789012

# With parameter
InstanceName: !Sub '${Environment}-instance-${AWS::Region}'
# Returns: prod-instance-us-east-1

# With resource reference
ConnectionString: !Sub 'postgresql://${DBInstance.Endpoint.Address}:5432/mydb'
# Returns: postgresql://my-db.c123.us-east-1.rds.amazonaws.com:5432/mydb
```

### Join: Combine Strings

```yaml
# Join list into string
CIDR: !Join ['.', [10, 0, 1, 0/24]]
# Returns: 10.0.1.0/24

# Join with custom delimiter
SecurityGroups: !Join [',', [!Ref SG1, !Ref SG2, !Ref SG3]]
# Returns: sg-123,sg-456,sg-789
```

### GetAZs: Get Availability Zones

```yaml
# Get all AZs in a region
FirstAZ: !Select [0, !GetAZs '']
# Returns: us-east-1a

SecondAZ: !Select [1, !GetAZs '']
# Returns: us-east-1b

# Get AZ for a specific region
AZs: !GetAZs us-west-2
# Returns: [us-west-2a, us-west-2b, us-west-2c]
```

### AWS Pseudo Parameters

```yaml
# Use built-in AWS values
Tags:
  - Key: Account
    Value: !Ref AWS::AccountId      # 123456789012
  - Key: Region
    Value: !Ref AWS::Region         # us-east-1
  - Key: StackName
    Value: !Ref AWS::StackName      # my-stack
  - Key: StackId
    Value: !Ref AWS::StackId        # arn:aws:cloudformation:...
```

---

## Mappings & Conditions

### Mappings: Static Lookup Tables

Mappings let you create tables of values and look them up by key.

```yaml
Mappings:
  RegionAMI:
    us-east-1:
      AMI: ami-0c55b159cbfafe1f0
    us-west-2:
      AMI: ami-0d0f67b7c23e54234
    eu-west-1:
      AMI: ami-0b22e2e7ff7d47a12

  InstanceType:
    dev:
      Type: t3.micro
    uat:
      Type: t3.small
    prod:
      Type: t3.large

Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !FindInMap [RegionAMI, !Ref AWS::Region, AMI]
      # Looks up: RegionAMI[us-east-1][AMI] = ami-0c55b159cbfafe1f0

      InstanceType: !FindInMap [InstanceType, !Ref Environment, Type]
      # Looks up: InstanceType[prod][Type] = t3.large
```

### Conditions: Conditional Resource Creation

```yaml
Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, prod]

Conditions:
  IsProduction: !Equals [!Ref Environment, prod]
  IsNotProduction: !Not [!Condition IsProduction]

Resources:
  # Only created in production
  MultiAZDatabase:
    Type: AWS::RDS::DBInstance
    Condition: IsProduction  # ← Only if IsProduction is true
    Properties:
      DBInstanceClass: db.t3.large
      MultiAZ: true

  # Only created in dev
  DevDatabase:
    Type: AWS::RDS::DBInstance
    Condition: IsNotProduction  # ← Only if IsNotProduction is true
    Properties:
      DBInstanceClass: db.t3.micro
      MultiAZ: false

  # Always created
  Bucket:
    Type: AWS::S3::Bucket
    # No condition = always created
    Properties:
      BucketName: !Sub 'bucket-${Environment}'
```

**Condition Functions:**
```yaml
Conditions:
  # Equals
  IsProd: !Equals [!Ref Environment, prod]

  # Not
  IsNotProd: !Not [!Condition IsProd]

  # And
  IsHighTraffic: !And
    - !Equals [!Ref Environment, prod]
    - !Equals [!Ref TrafficLevel, high]

  # Or
  NeedsMonitoring: !Or
    - !Condition IsHighTraffic
    - !Equals [!Ref Environment, uat]

  # If
  InstanceType: !If [IsProd, t3.large, t3.micro]
```

---

## Best Practices

### 1. Use Descriptive Names & Comments

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: |
  VPC infrastructure for production environment
  Creates:
  - VPC with 2 public + 2 private subnets
  - RDS database with automatic backups
  - Auto Scaling Group for web servers

Parameters:
  EnvironmentName:
    Type: String
    Description: Environment name (dev, uat, prod)
    AllowedValues: [dev, uat, prod]
    Default: dev

  VPCCIDRBlock:
    Type: String
    Description: CIDR block for VPC (e.g., 10.0.0.0/16)
    Default: 10.0.0.0/16
    AllowedPattern: '^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$'

Resources:
  # VPC - Core network container
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VPCCIDRBlock
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${EnvironmentName}-vpc'
        - Key: Environment
          Value: !Ref EnvironmentName
```

### 2. Use Parameters for Environment-Specific Values

```yaml
Parameters:
  InstanceType:
    Type: String
    Default: t3.micro

  # Bad: Hardcoded values
  # Instance Type: t3.micro

Resources:
  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType  # ← Use parameter
```

### 3. Validate Templates Before Deploying

```bash
# Always validate first
aws cloudformation validate-template \
  --template-body file://template.yaml

# Check for syntax errors
cfn-lint template.yaml  # Requires: pip install cfn-lint
```

### 4. Use Change Sets for Production

```bash
# Never update production directly!
# Always use change sets

# 1. Create change set
aws cloudformation create-change-set \
  --stack-name prod-stack \
  --change-set-name v1 \
  --template-body file://template.yaml

# 2. Review changes
aws cloudformation describe-change-set \
  --stack-name prod-stack \
  --change-set-name v1

# 3. If safe, execute
aws cloudformation execute-change-set \
  --stack-name prod-stack \
  --change-set-name v1
```

### 5. Protect Sensitive Values

```yaml
Parameters:
  DBPassword:
    Type: String
    NoEcho: true  # Hide from console
    MinLength: 8
    Description: Database password (will be hidden)

Resources:
  MyDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      MasterUserPassword: !Ref DBPassword
```

### 6. Use Tags Consistently

```yaml
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-bucket
      Tags:
        - Key: Name
          Value: production-data
        - Key: Environment
          Value: prod
        - Key: Owner
          Value: DevOps
        - Key: CostCenter
          Value: Engineering
        - Key: ManagedBy
          Value: CloudFormation
```

### 7. Export Outputs for Cross-Stack References

```yaml
Outputs:
  VPCId:
    Description: VPC ID for other stacks to import
    Value: !Ref MyVPC
    Export:
      Name: !Sub '${EnvironmentName}-VPC-ID'
```

### 8. Use Deletion Policies for Important Resources

```yaml
Resources:
  ImportantBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain  # Don't delete on stack deletion!
    Properties:
      BucketName: important-data

  Database:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot  # Create snapshot before deletion
    Properties:
      Engine: postgres
      # ... other properties
```

---

## Common Patterns

### Pattern 1: Multi-Environment Template

```yaml
Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, uat, prod]

Mappings:
  EnvironmentConfig:
    dev:
      InstanceType: t3.micro
      DBClass: db.t3.micro
      InstanceCount: 1
      MultiAZ: false
    uat:
      InstanceType: t3.small
      DBClass: db.t3.small
      InstanceCount: 2
      MultiAZ: false
    prod:
      InstanceType: t3.large
      DBClass: db.t3.large
      InstanceCount: 3
      MultiAZ: true

Resources:
  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !FindInMap [EnvironmentConfig, !Ref Environment, InstanceType]

  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: !FindInMap [EnvironmentConfig, !Ref Environment, DBClass]
      MultiAZ: !FindInMap [EnvironmentConfig, !Ref Environment, MultiAZ]
```

### Pattern 2: Nested Stacks (Reusable Components)

Parent stack (main-stack.yaml):
```yaml
Resources:
  # Network stack
  NetworkStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/my-bucket/network.yaml
      Parameters:
        VPCCidr: 10.0.0.0/16

  # Database stack
  DatabaseStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/my-bucket/database.yaml
      Parameters:
        VPCId: !GetAtt NetworkStack.Outputs.VPCId

Outputs:
  VPCId:
    Value: !GetAtt NetworkStack.Outputs.VPCId
```

### Pattern 3: Cross-Stack References

Stack 1 - Network (network-stack.yaml):
```yaml
Resources:
  SharedVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16

Outputs:
  VPCId:
    Value: !Ref SharedVPC
    Export:
      Name: shared-vpc-id
```

Stack 2 - Application (app-stack.yaml):
```yaml
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      SubnetId: !ImportValue shared-vpc-id  # Reference from other stack
```

---

## CloudFormation vs Terraform

| Aspect | CloudFormation | Terraform |
|--------|---|---|
| **Creator** | AWS (native) | HashiCorp (multi-cloud) |
| **Cloud Support** | AWS only | AWS, Azure, GCP, etc. |
| **Language** | YAML/JSON | HCL2 |
| **Learning Curve** | Steeper (AWS-specific) | Moderate |
| **Multi-cloud** | No | Yes |
| **State Management** | Built-in | File-based |
| **Community** | Large | Larger |
| **AWS features** | Latest (native) | May lag |
| **Best for** | AWS-only shops | Multi-cloud |

**When to Use CloudFormation:**
- AWS-only infrastructure
- Need native AWS features immediately
- Team already knows AWS
- Want AWS-managed service

**When to Use Terraform:**
- Multi-cloud infrastructure
- Want more flexibility
- Prefer HCL syntax
- Need state management control

---

## Troubleshooting

### Common Error: Template is invalid

```
Template error: instance of Fn::GetAtt references undefined resource
```

**Solution:**
```bash
# Validate template
aws cloudformation validate-template \
  --template-body file://template.yaml

# Check resource names match references
# Example: !Ref MyVPC assumes resource named MyVPC exists
```

### Common Error: Resource already exists

```
Resource creation cancelled: [S3 Error: The specified bucket already exists]
```

**Solution:**
- Use unique bucket name with !Sub and AWS::AccountId
- Or delete existing resource manually
- Use DeletionPolicy: Retain to keep resources

### Common Error: Stack creation failed

```
Status: CREATE_FAILED
```

**View events to see what failed:**
```bash
aws cloudformation describe-stack-events \
  --stack-name my-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

### Common Error: Change set failed

```
Change set review status: FAILED
```

**Check what went wrong:**
```bash
aws cloudformation describe-change-set \
  --stack-name my-stack \
  --change-set-name v1 \
  --query 'StatusReason'
```

### Rollback on Failure

CloudFormation automatically rollbacks failed updates:
```bash
# If update fails, rollback to previous state
# (Automatic - you can't disable for all resources)

# Disable rollback only for specific resources:
# Use: CreationPolicy attribute
```

---

## Advanced Topics

### 1. Custom Resources (Lambda-Backed)

```yaml
Resources:
  CustomResourceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole

  CustomResourceFunction:
    Type: AWS::Lambda::Function
    Properties:
      Handler: index.handler
      Role: !GetAtt CustomResourceRole.Arn
      Runtime: python3.11
      Code:
        ZipFile: |
          import cfnresponse
          def handler(event, context):
              try:
                  # Your custom logic here
                  response_data = {'Message': 'Success'}
                  cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
              except Exception as e:
                  cfnresponse.send(event, context, cfnresponse.FAILED, {})

  MyCustomResource:
    Type: AWS::CloudFormation::CustomResource
    Properties:
      ServiceToken: !GetAtt CustomResourceFunction.Arn
      MyProperty: my-value
```

### 2. Stack Policies (Control What Can Change)

```json
{
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "Update:Delete",
      "Resource": "LogicalResourceId/ProductionDatabase"
    }
  ]
}
```

### 3. Macros (Template Transformations)

```yaml
Transform: AWS::Include
Parameters:
  S3Bucket:
    Type: String
  S3Key:
    Type: String
Resources:
  MyMacro:
    Type: AWS::CloudFormation::Macro
    Properties:
      Code:
        S3Bucket: !Ref S3Bucket
        S3Key: !Ref S3Key
```

### 4. Module/Component Reuse

Create reusable template modules and use them with nested stacks.

---

## References & Resources

- **AWS CloudFormation User Guide**: https://docs.aws.amazon.com/cloudformation/
- **CloudFormation Template Reference**: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-reference.html
- **AWS Sample Templates**: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-sample-templates.html
- **CloudFormation CLI**: https://github.com/aws-cloudformation/cloudformation-cli
- **Sceptre** (Template Manager): https://sceptre.cloudreach.com/
- **AWS CDK** (Programmatic IaC): https://docs.aws.amazon.com/cdk/latest/guide/home.html
- **cfn-lint** (Linter): https://github.com/aws-cloudformation/cfn-python-lint
- **Former2** (Generate IaC from existing resources): https://github.com/iann0036/former2
