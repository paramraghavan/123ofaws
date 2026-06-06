# Terraform: Infrastructure as Code Complete Guide

## Table of Contents

1. [Quick Start for Beginners](#quick-start-for-beginners)
2. [Core Concepts & Building Blocks](#core-concepts--building-blocks)
3. [Real-World Analogy](#real-world-analogy)
4. [Terraform Object Types Explained](#terraform-object-types-explained)
5. [Block Syntax & Structure](#block-syntax--structure)
6. [Build & Deploy Workflow](#build--deploy-workflow)
7. [Variables: Input, Output & Local](#variables-input-output--local)
8. [State Management](#state-management)
9. [Deleting Resources & Importing Existing Infrastructure](#deleting-resources--importing-existing-infrastructure)
10. [Common Patterns & Use Cases](#common-patterns--use-cases)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [Advanced Topics](#advanced-topics)

---

## Quick Start for Beginners

### What Is Terraform?

Think of Terraform as a **blueprint language for cloud infrastructure**. Instead of clicking buttons in AWS console, you write code that describes what infrastructure you want. Terraform then automatically builds it for you.

**Why This Matters:**
- **Reproducible**: Same code = same infrastructure every time
- **Versioned**: Track changes to infrastructure like code
- **Faster**: Deploy 50 resources in minutes, not hours
- **Safer**: Preview changes before applying them

### Minimal Example: Your First Infrastructure

```hcl
# providers.tf - Tells Terraform to use AWS
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# main.tf - The actual infrastructure
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "my-vpc"
  }
}

# outputs.tf - What you want to know after creation
output "vpc_id" {
  value = aws_vpc.main.id
}
```

**To Deploy:**
```bash
terraform init      # Download plugins
terraform plan      # See what will be created
terraform apply     # Actually create it
```

---

## Core Concepts & Building Blocks

### The 5 Core Ideas

| Concept | What It Does | Real-World Analogy |
|---------|-------------|-------------------|
| **Provider** | Connects to cloud (AWS, Azure, GCP) | Your bank (decides which services available) |
| **Resource** | Individual infrastructure piece (EC2, S3) | Individual product (savings account, credit card) |
| **Data Source** | Reads existing infrastructure info | Looking up your existing bank balance |
| **Variable** | Input parameter (region, environment) | Form input (what country? what currency?) |
| **Output** | Return value after creation | Receipt showing your new account number |

### The Terraform Workflow

```
┌─────────────────────────────────────────────────────┐
│  1. WRITE CONFIGURATION (.tf files)                 │
│     └─ Describe what infrastructure you want        │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  2. PLAN (terraform plan)                           │
│     └─ Show what WILL happen (no changes yet)       │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  3. APPLY (terraform apply)                         │
│     └─ Actually create/modify resources             │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  4. STATE FILE (.terraform/terraform.tfstate)       │
│     └─ Terraform remembers what it created          │
└─────────────────────────────────────────────────────┘
```

---

## Real-World Analogy

**Terraform is like an IKEA assembly instruction booklet:**

- **Configuration files** = The assembly instruction diagrams
- **Provider** = The specific IKEA store you're buying from
- **Resources** = Individual parts (shelf, bracket, screw)
- **Variables** = Customization (color, size)
- **State file** = Your receipt showing what you bought
- **terraform plan** = The checklist showing "we need these parts"
- **terraform apply** = Actually assembling everything
- **terraform destroy** = Returning everything and getting refund

**Key insight**: Terraform remembers what it assembled (via state file). If you manually delete a piece, Terraform will recreate it on next `apply`.

---

## Terraform Object Types Explained

### 1. Providers: The Cloud Connection

A **provider** is a plugin that lets Terraform talk to a cloud service (AWS, Azure, GCP, Kubernetes, etc.).

**What It Does:**
- Authenticates with the cloud (using credentials/API keys)
- Translates Terraform code into cloud API calls
- Defines available resources you can create

```hcl
# Using AWS provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Use version 5.x.x
    }
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "my-aws-profile"  # Uses ~/.aws/credentials
}

# Could also use multiple AWS regions
provider "aws" {
  alias  = "us-west"
  region = "us-west-2"
}
```

**Use Cases:**
- **Single region**: Most applications start here (one `provider` block)
- **Multi-region**: Need redundancy? Use multiple provider blocks with `alias`
- **Multi-cloud**: Deploy some resources to AWS, some to Azure

**Real-World Example:**
```hcl
# Production = us-east-1 (N. Virginia)
# Disaster recovery = us-west-2 (Oregon)

provider "aws" {
  alias  = "production"
  region = "us-east-1"
}

provider "aws" {
  alias  = "disaster-recovery"
  region = "us-west-2"
}

# Use different providers for different resources
resource "aws_s3_bucket" "prod_data" {
  provider = aws.production
  bucket   = "prod-data-bucket"
}

resource "aws_s3_bucket" "dr_data" {
  provider = aws.disaster-recovery
  bucket   = "dr-data-bucket"
}
```

### 2. Resources: The Building Blocks

A **resource** is a piece of infrastructure you want to create: EC2 instance, S3 bucket, RDS database, VPC, security group, etc.

**Structure:**
```hcl
resource "TYPE" "NAME" {
  # configuration
}

# TYPE = what you're creating (aws_ec2_instance, aws_s3_bucket)
# NAME = your local name (used to reference this resource)
```

**Example with Multiple Resources:**
```hcl
# 1. Create VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name        = "main-vpc"
    Environment = "production"
  }
}

# 2. Create subnet in that VPC
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id  # ← Reference the VPC!
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

# 3. Create EC2 instance in that subnet
resource "aws_instance" "web_server" {
  ami                    = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id  # ← Reference subnet!
  associate_public_ip_address = true

  tags = {
    Name = "web-server"
  }
}
```

**Reference Pattern**: `resource_type.resource_name.attribute`

```hcl
# These all refer to the web_server:
aws_instance.web_server.id          # Outputs: i-0123456789abcdef0
aws_instance.web_server.private_ip  # Outputs: 10.0.1.42
aws_instance.web_server.public_ip   # Outputs: 52.1.2.3
```

### 3. Data Sources: Read Existing Infrastructure

A **data source** reads information about existing resources without creating new ones. You use it when:
- You need to reference something that already exists
- You want to query AWS for available options

```hcl
# Get the latest Amazon Linux 2 AMI (automatically)
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Now use it in a resource
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux_2.id  # ← Use data source!
  instance_type = "t3.micro"
}
```

**Reference Pattern**: `data.TYPE.NAME.attribute`

**Real-World Scenario:**
```hcl
# Scenario: VPC already exists, you want to launch instances in it

# Read existing VPC
data "aws_vpc" "existing" {
  id = "vpc-12345678"  # VPC ID you know about
}

# Read available subnets in that VPC
data "aws_subnets" "existing" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }
}

# Launch instance in existing infrastructure
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  subnet_id     = data.aws_subnets.existing.ids[0]  # Use first subnet
}
```

---

## Block Syntax & Structure

### The Basic Template

```hcl
# Single argument (simple)
key = value

# String value
name = "my-bucket"

# Number value
port = 8080

# Boolean value
enabled = true

# List value
availability_zones = ["us-east-1a", "us-east-1b"]

# Map value (key-value pairs)
tags = {
  Name        = "my-resource"
  Environment = "production"
  Owner       = "DevOps Team"
}

# Nested block (configuration section)
lifecycle {
  create_before_destroy = true
  ignore_changes = [tags]
}
```

### Real-World Example: Complete VPC Setup

```hcl
# VPC Resource
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block      # Using a variable
  enable_dns_hostnames = var.enable_dns_hostnames

  tags = local.common_tags  # Using local values
}

# Subnet Resource
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id      # Referencing VPC
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

# Security Group Resource
resource "aws_security_group" "web" {
  name_prefix = "web-"
  vpc_id      = aws_vpc.main.id

  # Nested block for ingress rules
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = local.common_tags
}
```

### Understanding VPC CIDR vs Security Group CIDR Blocks

**Common Question:** "Why do we allow `0.0.0.0/0` (anywhere) in a security group when it's inside a VPC with a specific CIDR block like `10.0.0.0/16`?"

**Answer:** These are two **independent concepts**:

#### The Key Difference

```
VPC CIDR Block (10.0.0.0/16)
└─ WHERE instances are LOCATED
   └─ "The house's address range"
   └─ Defines IP addresses available inside the VPC

Security Group CIDR Block (0.0.0.0/0)
└─ WHERE TRAFFIC COMES FROM (for ingress)
   └─ "Who can knock on the door"
   └─ Defines who can access your instance
```

#### Real-World Analogy

Your house:
```
Your House Address: 123 Main St (10.0.0.0/16 VPC)
                    └─ You live in a specific neighborhood

Your Front Door Rules:
├─ Allow packages from ANYWHERE in the WORLD (0.0.0.0/0)
│  └─ FedEx, Amazon, UPS from any address
│
├─ Allow visitors from your neighborhood only (10.0.0.0/16)
│  └─ Friends who live nearby
│
└─ Allow guests from specific address (203.0.113.45/32)
   └─ Your boss from their office

These are INDEPENDENT!
Your house is in ONE place, but you accept from MANY places.
```

#### Complete Example: Different Rules for Different Purposes

```hcl
resource "aws_security_group" "web_server" {
  name   = "web-server-sg"
  vpc_id = aws_vpc.main.id  # VPC CIDR: 10.0.0.0/16

  # HTTP: Allow from ANYWHERE (public web server)
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ← From internet (public!)
  }

  # HTTPS: Allow from ANYWHERE (public web server)
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ← From internet (public!)
  }

  # SSH: Allow from VPC ONLY (admin access - more secure)
  ingress {
    description = "SSH from VPC only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # ← From VPC only!
  }

  # SSH: Allow from specific office IP (additional admin access)
  ingress {
    description = "SSH from office"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["203.0.113.45/32"]  # ← From specific office!
  }

  # Allow all outbound
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

#### How Traffic Flows to Your Instance

```
Internet User (203.0.113.100)
    │
    ├─ Sends HTTP request to: 52.1.2.3:80 (public IP)
    │
    ├─→ Internet Gateway (entry point to VPC)
    │
    ├─→ Routes to instance at 10.0.1.42 (inside VPC CIDR)
    │
    ├─→ Security Group checks:
    │   ├─ Is traffic on port 80? YES ✅
    │   ├─ Is it TCP? YES ✅
    │   ├─ Is source in 0.0.0.0/0? YES ✅
    │   └─ Decision: ALLOW ✅
    │
    └─→ Request reaches instance at 10.0.1.42:80 ✅

Note: The instance lives in 10.0.0.0/16 (VPC CIDR)
      But it accepts traffic from 0.0.0.0/0 (anywhere)
      These are independent decisions!
```

#### Why Use Different CIDR Blocks for Different Rules?

| Rule | Security Group CIDR | Why? |
|------|---|---|
| **HTTP (port 80)** | `0.0.0.0/0` | Public web server - needs internet access |
| **HTTPS (port 443)** | `0.0.0.0/0` | Public web server - needs internet access |
| **SSH (port 22)** | `10.0.0.0/16` | Admin access - internal only, more secure |
| **Database (port 5432)** | `10.0.1.0/24` | Only app tier subnet needs access |
| **Admin API (port 8080)** | `203.0.113.0/24` | Only office network needs access |

#### What If You Restricted HTTP to VPC Only?

```hcl
# ❌ BAD: Restricts HTTP to VPC only
ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["10.0.0.0/16"]  # ← Only VPC!
}
```

**Result:** Internet users cannot access your web server! Your website would be invisible to the internet. ❌

#### Key Takeaway

```
VPC CIDR:              "Where does my instance live?"
                       Answer: 10.0.0.0/16

Security Group CIDR:   "Who can talk to my instance?"
                       Answer: Depends on the port!
                       - HTTP: 0.0.0.0/0 (anyone)
                       - SSH: 10.0.0.0/16 (VPC only)
                       - DB: 10.0.1.0/24 (app tier only)

✅ These are INDEPENDENT decisions!
```

---

## Build & Deploy Workflow

### Step-by-Step Process

#### 1. `terraform init` - Download Providers & Initialize

```bash
terraform init
```

**What happens:**
- Downloads provider plugins (AWS, Azure, etc.) to `.terraform/`
- Creates `.terraform.lock.hcl` (locks provider versions)
- Creates `.terraform/` directory structure

**When to use:** First time, after changing providers, or in new environment

```bash
# Output looks like:
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully initialized!
```

#### 2. `terraform plan` - Preview Changes (NO changes applied yet!)

```bash
terraform plan
```

**What happens:**
- Reads all `.tf` files
- Compares desired state (your code) with current state (state file)
- Shows you exactly what will be created/changed/destroyed

**Output example:**
```
Plan: 5 to add, 2 to change, 0 to destroy.
```

**This is SAFE** - nothing is created yet!

```bash
# Save plan to file (for audit trail)
terraform plan -out=tfplan

# See more detail
terraform plan -json | jq
```

#### 3. `terraform apply` - Actually Create/Modify Resources

```bash
terraform apply
```

**What happens:**
- Asks "Do you want to perform these actions?" (type `yes` to confirm)
- Makes API calls to AWS to create/modify resources
- Updates `.terraform/terraform.tfstate` with new state

**Common pattern:**
```bash
# 1. Always plan first to see what will change
terraform plan -out=tfplan

# 2. Review the plan manually

# 3. Then apply
terraform apply tfplan  # Uses saved plan, no need to confirm again
```

#### 4. `terraform destroy` - Delete All Resources

```bash
terraform destroy
```

**What happens:**
- Deletes all resources managed by this Terraform state file
- Asks for confirmation (type `yes`)
- Updates state file

**When to use:**
- Tearing down test environment
- Cleaning up after learning/experimentation
- Development environment at end of day (to save costs)

**Warning**: This is irreversible! Make sure you mean it.

### Operating on Specific Resources Only

**Scenario: Fix just one broken resource without touching others**

```bash
# Plan only one resource
terraform plan -target=aws_instance.web_server

# Apply only one resource (careful!)
terraform apply -target=aws_instance.web_server

# Useful for:
# - Debugging one resource
# - Working around Terraform bugs
# - Rolling updates
```

**Example:**
```bash
# Your infrastructure has 50 resources
# Only the database parameter group needs updating

terraform plan -target=aws_db_parameter_group.main
terraform apply -target=aws_db_parameter_group.main
```

### Advanced: Import Existing Resources

**Scenario: Your S3 bucket already exists (created manually), need to manage it with Terraform**

```bash
# 1. Add resource definition to your .tf file
resource "aws_s3_bucket" "my_bucket" {
  bucket = "my-existing-bucket"
}

# 2. Import existing resource into Terraform state
terraform import aws_s3_bucket.my_bucket my-existing-bucket

# 3. Now Terraform knows about it and will manage it
terraform plan  # Shows any differences
```

**Real-world workflow:**
```bash
# Day 1: Create bucket manually (mistake!)
aws s3 mb s3://my-data-bucket

# Day 2: Realize need to manage with Terraform
# Add to your terraform code:
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

# Import it
terraform import aws_s3_bucket.data my-data-bucket

# Now you can manage versioning, encryption, etc.
terraform apply
```

---

## Variables: Input, Output & Local

### 1. Input Variables: The Function Parameters

Input variables are how you make Terraform code reusable. They let you change values without editing code.

```hcl
# variables.tf
variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"

  # Optional: set default
  default = "dev"
}

variable "instance_count" {
  type        = number
  description = "Number of instances to create"

  # Can add validation
  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "instance_tags" {
  type = map(string)
  description = "Tags to apply to instances"

  default = {
    Owner       = "DevOps"
    CostCenter  = "Engineering"
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "AZs to deploy to"
  default     = ["us-east-1a", "us-east-1b"]
}
```

**Using variables in code:**
```hcl
# main.tf
resource "aws_instance" "web" {
  count         = var.instance_count  # Use variable!
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = merge(
    var.instance_tags,  # Use variable!
    {
      Name        = "web-${var.environment}-${count.index}"
      Environment = var.environment  # Use variable!
    }
  )
}
```

**Setting variable values (multiple ways):**

```bash
# 1. Command line (overrides everything)
terraform apply -var="environment=prod" -var="instance_count=5"

# 2. terraform.tfvars file
# In terraform.tfvars:
environment   = "staging"
instance_count = 3

# 3. Environment variables
export TF_VAR_environment=production
export TF_VAR_instance_count=5
terraform apply

# 4. *.auto.tfvars files (auto-loaded)
# prod.auto.tfvars:
environment   = "prod"
instance_count = 20
```

**Load priority** (later = higher priority):
1. Environment variables (`TF_VAR_*`)
2. `terraform.tfvars`
3. `terraform.tfvars.json`
4. `*.auto.tfvars` (in lexical order)
5. `-var` and `-var-file` command line arguments

### 2. Output Variables: The Function Return Values

Output variables are what you want to know after Terraform creates infrastructure.

```hcl
# outputs.tf
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id

  # Optional: control visibility
  sensitive = false
}

output "instance_public_ips" {
  description = "Public IPs of all instances"
  value       = aws_instance.web[*].public_ip
  # Outputs: ["1.2.3.4", "5.6.7.8", "9.10.11.12"]
}

output "instance_ips_by_name" {
  description = "Map of instance names to IPs"
  value = {
    for instance in aws_instance.web :
    instance.tags.Name => instance.public_ip
  }
  # Outputs: {"web-0" = "1.2.3.4", "web-1" = "5.6.7.8"}
}

output "connection_string" {
  description = "Database connection string (sensitive!)"
  value       = "postgresql://${aws_db_instance.main.username}:***@${aws_db_instance.main.endpoint}"
  sensitive   = true  # Won't show in logs
}
```

**View outputs after apply:**
```bash
# Show all outputs
terraform output

# Show specific output
terraform output vpc_id

# As JSON (for scripts)
terraform output -json
```

### 3. Local Variables: Temporary Values & Reuse

Local variables are like "temporary variables" in a function - used to avoid repetition and make code cleaner.

```hcl
# locals.tf
locals {
  # Simple local values
  service_name = "web-app"
  environment  = "production"
  region       = "us-east-1"

  # Computed local value (based on other locals)
  common_prefix = "${local.service_name}-${local.environment}"

  # Common tags (to apply to ALL resources)
  common_tags = {
    Service     = local.service_name
    Environment = local.environment
    Region      = local.region
    ManagedBy   = "Terraform"
    CreatedAt   = timestamp()
  }

  # Conditional logic
  instance_type = local.environment == "prod" ? "t3.large" : "t3.micro"

  # Lists/maps
  azs = ["us-east-1a", "us-east-1b", "us-east-1c"]

  subnet_cidrs = {
    public  = "10.0.1.0/24"
    private = "10.0.2.0/24"
    db      = "10.0.3.0/24"
  }
}
```

**Using locals in code:**
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = local.common_tags  # Reuse common tags everywhere!
}

resource "aws_instance" "web" {
  count         = local.environment == "prod" ? 3 : 1
  instance_type = local.instance_type

  tags = merge(
    local.common_tags,  # Reuse!
    {
      Name = "${local.common_prefix}-${count.index}"
    }
  )
}
```

**Key Differences:**

| Type | Input Variable | Local | Output |
|------|---|---|---|
| **What** | External input (function param) | Temporary value (local var) | Return value |
| **Set by** | User (CLI, files) | Code itself | Code (after apply) |
| **Changed when** | Every apply | Code change | Every apply |
| **Use for** | Configuration | Reusable expressions | Return values |
| **Example** | `var.environment` | `local.common_tags` | `output "vpc_id"` |

---

## State Management

### ⚠️ CRITICAL: Never Commit State Files to Git!

**This is the #1 security mistake with Terraform!**

State files contain **sensitive secrets in plaintext**:
- Database passwords
- RDS master passwords
- AWS secret access keys
- Private IP addresses
- Sensitive configuration data

### Why NOT to Commit State Files

#### 1. Security Risk - Exposed Credentials

```hcl
# In your state file (visible to anyone with git access):
{
  "db_password": "MyDatabasePassword123!"
}

# Once in git history, it's permanently there!
# Even if you delete the file, git can recover it
```

**Real attack scenario:**
```
1. Developer commits state file with DB password
2. Developer leaves company
3. Attacker gains access to GitHub repo (via old device, leaked credentials)
4. Attacker finds password in git history
5. Attacker accesses production database
6. Data breach!
```

#### 2. Team Conflicts - Simultaneous Applies Break

```
Timeline:
11:00 - Alice: terraform apply -var-file=prod.tfvars
        → Creates 3 instances
        → State file updated: instances = ["i-111", "i-222", "i-333"]
        → Commits state file to git

11:05 - Bob: git pull (gets Alice's state)
        → terraform apply -var-file=prod.tfvars
        → But old state says only 2 instances existed
        → Bob's code creates 3 instances
        → Now there are 6 instances total!
        → Bob's state only knows about 3
        → Alice doesn't know about the other 3

Result: Infrastructure drift, confusion, costs!
```

#### 3. Lost Changes - Old State File Overwrites New

```
Week 1: Developer applies changes, commits state file
Week 2: Infrastructure grows (new resources added manually)
Week 3: Old developer returns, runs terraform plan on old checkout
        → Old state file loaded
        → "I'll delete these 5 new resources!"
        → Runs terraform apply
        → DISASTER!
```

### What Should You Commit vs Ignore

**✅ COMMIT to Git:**
```
terraform/
├── main.tf                 # Infrastructure code
├── variables.tf            # Variable definitions
├── outputs.tf              # Output definitions
├── .terraform.lock.hcl     # ← IMPORTANT! Version lock
├── example.tfvars          # Example variables (no real values!)
└── .gitignore              # Ignore list
```

**❌ NEVER COMMIT:**
```
terraform/
├── .terraform/             # Downloaded plugins
├── terraform.tfstate       # ← Current state (IGNORE!)
├── terraform.tfstate.d/    # ← Workspace states (IGNORE!)
├── terraform.tfstate.*.backup  # ← Backups (IGNORE!)
└── terraform.tfvars        # ← Your actual values (IGNORE!)
```

**Correct .gitignore:**
```gitignore
# Local .terraform directories (plugins)
**/.terraform/*

# .tfstate files (CRITICAL!)
*.tfstate
*.tfstate.*
terraform.tfstate*

# Lock files (IGNORE .terraform.lock.hcl should NOT be ignored!)
# .terraform.lock.hcl  ← DO COMMIT THIS

# Crash log files
crash.log
crash.*.log

# Override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Sensitive tfvars files (DO NOT COMMIT)
*.tfvars
*.tfvars.json
!example.tfvars    # Exception: example file IS committed

# IDE
.idea/
.vscode/
```

### Do We Save State File into a Repository? ❌ NEVER!

**The answer is: NO! Absolutely NOT!** State files should **NEVER** be committed to git or any repository.

#### Why NOT to Commit State Files to Git

**Reason 1: Security - Plaintext Secrets Exposed**

State files contain **passwords in plaintext**:

```json
{
  "resources": [
    {
      "type": "aws_db_instance",
      "attributes": {
        "master_password": "MyDatabasePassword123!",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "admin_password": "SuperSecretPassword"
      }
    }
  ]
}
```

**If you commit this to git:**
- ❌ Passwords visible to anyone with repo access
- ❌ Once in git history, it's PERMANENT (even if deleted)
- ❌ `git log` can recover deleted files
- ❌ Leaked on GitHub = public internet
- ❌ Attackers can access your AWS accounts/databases

**Real attack scenario:**
```
1. Developer accidentally commits state with DB password
2. Developer leaves company, GitHub repo still exists
3. Attacker gains access to old device with git credentials
4. Attacker clones repo, extracts password from history
5. Attacker connects to production database
6. DATA BREACH! 💥
```

**Reason 2: Team Conflicts - Multiple Applies Corrupt State**

```
Timeline:
11:00 - Alice: terraform apply
        └─ Creates 3 instances
        └─ State updated: instances = [i-111, i-222, i-333]
        └─ Commits state file to git

11:05 - Bob: git pull (gets Alice's state)
        └─ terraform apply
        └─ But his code says 2 instances
        └─ State conflict!
        └─ Infrastructure inconsistency

Result:
├─ State says 3 instances
├─ Code says 2 instances
└─ AWS has ??? instances (confusion!)
```

**Reason 3: Lost History - Old State Overwrites New**

```
Week 1:  Developer applies changes, commits state
Week 2:  Infrastructure grows (new resources added manually)
Week 3:  Old developer checks out old branch
         └─ Old state file loaded
         └─ "I'll delete these 5 resources that don't exist in my code!"
         └─ terraform apply
         └─ DISASTER! 🔥 Real resources deleted!
```

#### What SHOULD Be in Git vs What Shouldn't

**✅ COMMIT to Git (Infrastructure Code):**
```
terraform/
├── main.tf                 # Infrastructure definitions
├── variables.tf            # Variable declarations
├── outputs.tf              # Output definitions
├── .terraform.lock.hcl     # Version lock (IMPORTANT!)
├── example.tfvars          # Example values (no real secrets!)
└── .gitignore              # Ignore configuration
```

**❌ NEVER COMMIT (Sensitive Data + State):**
```
terraform/
├── .terraform/             # Downloaded plugins (local only)
├── terraform.tfstate       # STATE FILE (LOCAL ONLY!) ⚠️⚠️⚠️
├── terraform.tfstate.*     # Backups (LOCAL ONLY!)
├── terraform.tfstate.backup # Backups (LOCAL ONLY!)
├── terraform.tfvars        # Your actual parameter values (LOCAL ONLY!)
└── *.tfvars                # All tfvars files (LOCAL ONLY!)
```

#### Quick Reference: What Goes Where?

| File | Git | Local Disk | S3 (Remote) |
|------|---|---|---|
| `main.tf` | ✅ YES | ✅ YES | ❌ NO |
| `variables.tf` | ✅ YES | ✅ YES | ❌ NO |
| `outputs.tf` | ✅ YES | ✅ YES | ❌ NO |
| `.terraform.lock.hcl` | ✅ YES | ✅ YES | ❌ NO |
| `example.tfvars` | ✅ YES | ✅ YES | ❌ NO |
| `.gitignore` | ✅ YES | ✅ YES | ❌ NO |
| `terraform.tfstate` | ❌ NO | ⚠️ temporary | ✅ YES (remote) |
| `terraform.tfvars` | ❌ NO | ✅ YES | ❌ NO |
| `.terraform/` | ❌ NO | ✅ YES | ❌ NO |

#### Safe Git Workflow

**WRONG - Don't do this! ❌**
```bash
# BAD! This commits secrets to git!
terraform apply
git add .                    # Adds terraform.tfstate!
git commit -m "Apply changes"
git push origin main

# Result:
# - State file with passwords in GitHub
# - Visible to anyone with repo access
# - PERMANENT in git history
```

**CORRECT - Do this! ✅**
```bash
# 1. Setup remote state first (S3 backend)
# 2. Create proper .gitignore

# 3. Commit ONLY code, not state
git add main.tf variables.tf outputs.tf .terraform.lock.hcl .gitignore
git commit -m "Add infrastructure code"
git push origin main

# State lives in S3 (encrypted, versioned, backed up)
# Team members: terraform init → downloads state from S3
```

#### Then Where Does State Get Saved?

**Option 1: Local State (Development Only - Not Recommended)**
```bash
terraform apply
# State saved to: .terraform/terraform.tfstate
# Problem: Only on your laptop, not shared, can be lost
```

**Add to .gitignore immediately:**
```bash
echo '*.tfstate' >> .gitignore
echo '*.tfstate.*' >> .gitignore
echo '*.tfvars' >> .gitignore
git add .gitignore
git commit -m "Add terraform to gitignore"
```

**Option 2: Remote State in S3 (Recommended - Safe)**
```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

```bash
terraform init
# State is now in S3 (not on your laptop!)
# Encrypted at rest
# Automatic backups
# Shared across team
# NOT in git!
```

#### Real-World Checklist

Before committing to git, ask:
- [ ] `terraform.tfstate` is NOT staged? (`git status | grep tfstate`)
- [ ] `terraform.tfvars` is NOT staged? (contains your real values!)
- [ ] `.gitignore` includes `*.tfstate` and `*.tfvars`?
- [ ] Only `.tf` files and `.terraform.lock.hcl` are staged?
- [ ] `.terraform.lock.hcl` IS staged? (version lock!)

```bash
# Safe pre-commit check
git status

# Should show:
# On branch main
# Changes to be committed:
#   new file:   main.tf
#   new file:   variables.tf
#   new file:   outputs.tf
#   new file:   .terraform.lock.hcl
#   new file:   .gitignore
#
# Untracked files:
#   .terraform/              ← NOT staged
#   terraform.tfstate        ← NOT staged
#   terraform.tfvars         ← NOT staged
#
# If any .tfstate or .tfvars are staged, DO NOT COMMIT!
```

#### If You Accidentally Committed State

**EMERGENCY: You committed secrets to git! Fix immediately:**

```bash
# 1. Remove from git history (PERMANENTLY)
git rm --cached terraform.tfstate
git commit --amend -m "Remove state file"
git push origin main --force-with-lease

# 2. Rotate ALL secrets! (passwords, keys, etc.)
# State file was exposed, treat all secrets as compromised!

# 3. Scan git history to ensure removal
git log --all --full-history -- terraform.tfstate

# 4. Notify security team if on shared repo
```

---

### What Is State?

The **state file** (`.terraform/terraform.tfstate`) is Terraform's memory. It remembers:
- What resources were created
- What their IDs are
- Their current attributes

**Why it matters:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"
}

# First apply: Creates instance (ID: i-abc123)
# State file stores: i-abc123

# Second apply: Sees instance already exists
# Doesn't create duplicate, just checks for changes

# If state file lost: Terraform forgets it created the instance
# Next apply would try to create NEW instance (conflict!)
```

### Local State vs Remote State (The Decision)

#### Local State (Default - For Learning Only)

```hcl
# No backend configuration = local state
# State file at: .terraform/terraform.tfstate
```

**When to use:**
- ✅ Learning Terraform
- ✅ Solo projects
- ✅ Temporary environments

**Problems:**
- ❌ Only on your laptop
- ❌ Team can't collaborate
- ❌ No locking (simultaneous applies fail)
- ❌ No backup/versioning
- ❌ Easy to lose

#### Remote State (Recommended for Teams & Production)

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

**When to use:**
- ✅ Team collaboration
- ✅ Production environments
- ✅ Any shared infrastructure
- ✅ Need audit trail

**Benefits:**
- ✅ Stored safely in AWS S3 (encrypted)
- ✅ Versioning (recover old state)
- ✅ Locking (prevents simultaneous applies)
- ✅ Backup/disaster recovery
- ✅ Audit trail (who changed what, when)
- ✅ No state file in git!

### Setting Up Remote State (Step-by-Step)

#### Step 1: Create S3 Bucket for State

```bash
# Create bucket
aws s3 mb s3://my-terraform-state-bucket-12345

# Enable versioning (backup)
aws s3api put-bucket-versioning \
  --bucket my-terraform-state-bucket-12345 \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket my-terraform-state-bucket-12345 \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'

# Block public access (CRITICAL!)
aws s3api put-public-access-block \
  --bucket my-terraform-state-bucket-12345 \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Step 2: Create DynamoDB Table for Locking

```bash
# This prevents simultaneous applies
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

#### Step 3: Configure Backend in Terraform

```hcl
# backend.tf
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    bucket         = "my-terraform-state-bucket-12345"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

#### Step 4: Initialize Backend

```bash
# First time: Migrate from local to remote
terraform init

# Terraform asks:
# Do you want to copy existing state to the new backend?
# → Answer: yes

# Your local state is now uploaded to S3!
```

#### Step 5: Verify

```bash
# State is now in S3
ls -la | grep tfstate
# (should be empty or just backup)

# View state in S3
aws s3 ls s3://my-terraform-state-bucket-12345/

# Test locking (open two terminals, start applies in both)
terraform apply  # Terminal 1
terraform apply  # Terminal 2 - will wait for Terminal 1 to finish!
```

### The State File Format

```json
{
  "version": 4,
  "terraform_version": "1.5.0",
  "serial": 42,
  "lineage": "abc123",
  "outputs": {
    "instance_id": {
      "value": "i-0123456789abcdef0",
      "type": "string"
    }
  },
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "id": "i-0123456789abcdef0",
            "instance_type": "t3.micro",
            "private_ip": "10.0.1.42",
            "public_ip": "52.1.2.3",
            "tags": {
              "Name": "web-server"
            }
          }
        }
      ]
    }
  ]
}
```

### Common State Operations

```bash
# View current state
terraform state list                    # Show all resources
terraform state show aws_instance.web   # Show details

# Inspect remote state
terraform state pull > state.json       # Download from S3
cat state.json | jq '.resources'        # View resources only

# Move resource (rename)
terraform state mv aws_instance.web aws_instance.web_server

# Remove resource from state (don't delete in AWS!)
terraform state rm aws_instance.old     # Use when migrating

# Push state to remote (emergency recovery)
terraform state push state.json

# Lock state manually (emergency)
terraform state lock          # Lock the state
terraform state unlock        # Unlock (CAREFUL!)

# Refresh state (sync with AWS reality)
terraform refresh             # Read actual state from AWS
```

### Dealing with State Conflicts

**Scenario 1: Applied changes outside of Terraform**
```bash
# You manually changed instance type in AWS console
terraform plan

# Shows:
# Instance type differs: t3.large (in AWS) vs t3.micro (in state)

# Option 1: Update Terraform code (correct way)
# Edit main.tf: instance_type = "t3.large"
terraform plan      # Verify
terraform apply     # Apply

# Option 2: Revert AWS changes
aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type t3.micro
terraform plan      # Should show no changes now
```

**Scenario 2: State file out of sync after manual delete**
```bash
# Oops! Deleted an instance manually in AWS console
terraform plan

# Shows:
# aws_instance.web will be recreated
# (because state still thinks it exists)

# Fix: Remove from state
terraform state rm aws_instance.web   # Remove from state

# Now state matches reality
terraform plan     # Should show no changes
```

**Scenario 3: State locked (failed apply)**
```bash
# Previous apply crashed, state is locked
terraform apply
# Error: Error acquiring the lock: ... (state is locked)

# View who locked it
terraform state list

# Emergency unlock (only if absolutely sure)
terraform force-unlock LOCK_ID

# Then find out why previous apply failed
terraform plan
terraform apply
```

### Recovering from State Disasters

**Scenario: Accidentally deleted state file, need recovery**

```bash
# If using remote state (S3):
# ✅ You're safe! S3 has versioning

# Download previous version
aws s3api list-object-versions \
  --bucket my-terraform-state-bucket \
  --prefix prod/terraform.tfstate

aws s3api get-object \
  --bucket my-terraform-state-bucket \
  --key prod/terraform.tfstate \
  --version-id "abc123" \
  terraform.tfstate.backup

# Restore
terraform state push terraform.tfstate.backup

# If using local state only:
# ❌ You're in trouble (this is why remote state matters!)
# Options:
# 1. Run terraform import for each resource
# 2. Destroy and rebuild
```

### State File Troubleshooting

```bash
# State file too large? (> 50MB is a problem)
terraform state list | wc -l    # Count resources
# Solution: Split into smaller configurations or use modules

# Can't connect to remote state?
# Check credentials:
aws sts get-caller-identity

# Check S3 bucket permissions:
aws s3 ls s3://my-terraform-state-bucket

# Check DynamoDB table:
aws dynamodb describe-table --table-name terraform-locks

# Force read local state (emergency)
terraform init -reconfigure -force-copy
```

### Viewing Current State & Managing Multiple Environments

#### How to View Your Current State

```bash
# List all resources currently managed by Terraform
terraform state list
# Output:
# aws_instance.web[0]
# aws_instance.web[1]
# aws_subnet.public
# aws_vpc.main
# ... etc

# Show details of one specific resource
terraform state show aws_instance.web
# Output shows all attributes of that resource

# Show as JSON (for scripting)
terraform state show -json aws_instance.web[0] | jq

# See all outputs (final values after creation)
terraform output
# Output:
# instance_ids = [
#   "i-0123456789abcdef0",
#   "i-9876543210fedcba9",
# ]
# vpc_id = "vpc-12345678"

# Output specific value (for scripts)
terraform output -raw instance_ids[0]    # Single instance ID
terraform output -json                   # All outputs as JSON
```

#### Managing Multiple Stages (Dev/UAT/Prod)

There are 3 approaches:

##### Approach 1: Separate `.tfvars` Files (RECOMMENDED)

**Best for:** Most teams, clear & simple

```
infrastructure/
├── main.tf
├── variables.tf
├── outputs.tf
├── dev.tfvars      # Development values
├── uat.tfvars      # UAT/Staging values
└── prod.tfvars     # Production values
```

**How it works:**
```bash
# Deploy to dev (state file: dev.tfstate)
terraform apply -var-file=dev.tfvars

# Deploy to uat (state file: uat.tfstate)
terraform apply -var-file=uat.tfvars

# Deploy to prod (state file: prod.tfstate)
terraform apply -var-file=prod.tfvars
```

**Each environment has separate state file** (can see via `terraform state list`):

```bash
# Switch to dev
terraform apply -var-file=dev.tfvars
terraform state list
# Shows dev infrastructure

# Switch to prod
terraform apply -var-file=prod.tfvars
terraform state list
# Shows prod infrastructure (completely different!)
```

**variables.tf:**
```hcl
variable "environment" {
  type        = string
  description = "Environment name (dev, uat, prod)"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
}

variable "instance_count" {
  type        = number
  description = "Number of instances"
}
```

**dev.tfvars:**
```hcl
environment   = "dev"
instance_type = "t3.micro"
instance_count = 1
```

**uat.tfvars:**
```hcl
environment   = "uat"
instance_type = "t3.small"
instance_count = 2
```

**prod.tfvars:**
```hcl
environment   = "prod"
instance_type = "t3.large"
instance_count = 3
```

**main.tf:**
```hcl
resource "aws_instance" "web" {
  count         = var.instance_count
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type

  tags = {
    Name        = "web-${var.environment}-${count.index}"
    Environment = var.environment
  }
}
```

##### Approach 2: Terraform Workspaces

**Best for:** Same code, different configurations, learning

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new uat
terraform workspace new prod

# List workspaces
terraform workspace list
# * default
#   dev
#   uat
#   prod

# Switch workspace
terraform workspace select dev

# Apply (creates separate state for each workspace)
terraform apply -var-file=dev.tfvars
# State stored at: terraform.tfstate.d/dev/terraform.tfstate

# Switch to prod
terraform workspace select prod
terraform apply -var-file=prod.tfvars
# State stored at: terraform.tfstate.d/prod/terraform.tfstate

# View current state
terraform state list        # Shows dev infrastructure
terraform workspace select prod
terraform state list        # Shows prod infrastructure
```

**Pros:** Simple, same code, clear separation
**Cons:** All state files local (unless using remote backend)

##### Approach 3: Separate Directories (Complex)

**Best for:** Large organizations, strict separation

```
terraform/
├── dev/
│   ├── main.tf
│   ├── variables.tf
│   ├── backend.tf (dev bucket)
│   └── dev.tfvars
├── uat/
│   ├── main.tf
│   ├── variables.tf
│   ├── backend.tf (uat bucket)
│   └── uat.tfvars
└── prod/
    ├── main.tf
    ├── variables.tf
    ├── backend.tf (prod bucket)
    └── prod.tfvars
```

```bash
# Deploy dev
cd terraform/dev
terraform init
terraform apply -var-file=dev.tfvars

# Deploy uat
cd ../uat
terraform init
terraform apply -var-file=uat.tfvars

# Deploy prod
cd ../prod
terraform init
terraform apply -var-file=prod.tfvars
```

**Pros:** Complete isolation, different teams can manage each
**Cons:** Code duplication, harder to maintain

#### Recommended Pattern: Approach 1 + Remote State

**This is what most successful teams use:**

```
infrastructure/
├── backend.tf                           # Remote state config
│   # bucket = "terraform-state-12345"
│   # key = "${var.environment}/terraform.tfstate"
│
├── main.tf                              # Core resources
├── variables.tf                         # Variable definitions
├── outputs.tf                           # Outputs
│
├── dev.tfvars                           # Development values
├── uat.tfvars                           # UAT values
└── prod.tfvars                          # Production values
```

**backend.tf (with environment prefix):**
```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket"
    key            = "${var.environment}/terraform.tfstate"  # ← Different path per env!
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

**Workflow:**
```bash
# Deploy to dev
terraform init -upgrade          # Pull latest plugins
terraform plan -var-file=dev.tfvars -out=tfplan.dev
terraform apply tfplan.dev
# State: s3://my-terraform-state-bucket/dev/terraform.tfstate

# Deploy to uat
terraform plan -var-file=uat.tfvars -out=tfplan.uat
terraform apply tfplan.uat
# State: s3://my-terraform-state-bucket/uat/terraform.tfstate

# Deploy to prod
terraform plan -var-file=prod.tfvars -out=tfplan.prod
terraform apply tfplan.prod
# State: s3://my-terraform-state-bucket/prod/terraform.tfstate
```

**Each environment is COMPLETELY SEPARATE:**
```bash
# View dev state
terraform state list -var-file=dev.tfvars
# Shows only dev resources

# View prod state (completely different)
terraform state list -var-file=prod.tfvars
# Shows only prod resources

# They don't interfere with each other!
```

#### How to Know Which State You're Looking At

```bash
# Current environment (from tfvars file you're using)
# You control this with -var-file parameter

# Check what you're about to apply
terraform plan -var-file=prod.tfvars

# It will show:
# - Which resources exist in current state
# - What environment you're in (from output)
# - What will change

# Be EXTRA careful with prod!
# Recommended: Always review plan before apply
terraform plan -var-file=prod.tfvars -out=tfplan
cat tfplan   # Review
terraform apply tfplan
```

#### Switching Between Environments

```bash
# View dev infrastructure
terraform state list -var-file=dev.tfvars

# View prod infrastructure
terraform state list -var-file=prod.tfvars

# Make change to dev
terraform apply -var-file=dev.tfvars

# Make change to prod
terraform apply -var-file=prod.tfvars

# NO interference between environments!
```

### Does `plan` Detect If Resource Already Exists?

This is a critical question with **3 different scenarios:**

#### Scenario 1: Resource Exists + Already in State File (NORMAL)

**What happens:**
```bash
# Day 1: You create S3 bucket
terraform apply

# terraform.tfstate now contains: aws_s3_bucket.data

# Day 2: You run plan again (no code changes)
terraform plan

# Output:
# No changes. Your infrastructure matches the configuration.
```

**Why?** Terraform compares:
- Your code (what you want)
- State file (what already exists)
- AWS reality

If all match → No changes needed

```hcl
# Code
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

# State file says: aws_s3_bucket.data already exists
# AWS says: bucket "my-data-bucket" already exists
# Result: ✅ No action needed
```

#### Scenario 2: Resource Exists in AWS BUT NOT in State File (PROBLEM!)

**What happens:**
```bash
# Day 1: Someone manually creates bucket in AWS console
# "my-data-bucket" now exists in AWS
# But your state file has NO record of it

# Day 2: You write Terraform code to create it
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

terraform plan

# Output:
# Plan: 1 to add, 0 to change, 0 to destroy.
# Terraform will create aws_s3_bucket.data

# ⚠️ But when you apply...
terraform apply

# Error: BucketAlreadyExists
# The S3 bucket "my-data-bucket" already exists
```

**Why?** Terraform's plan only checks STATE, not AWS reality!

```
Terraform checks:
✅ Code says: "create bucket"
✅ State file says: "nothing about this bucket"
❌ BUT: AWS already has the bucket!
❌ Plan doesn't know about reality!
```

**Solution: Import existing resource into state**
```bash
# 1. Add resource definition to your code
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

# 2. Import it
terraform import aws_s3_bucket.data my-data-bucket

# Now state file knows about it
terraform state show aws_s3_bucket.data

# 3. Plan again
terraform plan
# Output: No changes. Your infrastructure matches the configuration.
```

#### Scenario 3: Code Tries to Create with Duplicate Name

**What happens:**
```bash
# Your code
resource "aws_s3_bucket" "bucket1" {
  bucket = "my-data-bucket"  # Name is hardcoded
}

# Day 1: Apply (creates bucket)
terraform apply
# ✅ Success

# Day 2: Someone deletes code, adds it back
resource "aws_s3_bucket" "bucket1" {
  bucket = "my-data-bucket"  # Same name!
}

# But state file was reset/lost
# State no longer knows about the bucket

terraform plan

# Output:
# Plan: 1 to add, 0 to change, 0 to destroy.
# Terraform will create aws_s3_bucket.bucket1

terraform apply
# Error: BucketAlreadyExists
# The S3 bucket "my-data-bucket" already exists
```

### Plan vs Reality: What Plan Actually Checks

```
┌──────────────────────────────────────────────┐
│ terraform plan compares:                     │
├──────────────────────────────────────────────┤
│ 1. Your Code (main.tf)                       │
│    "I want to create S3 bucket"              │
│                                              │
│ 2. State File (.tfstate)                     │
│    "I previously created vpc-123"            │
│                                              │
│ 3. Difference                                │
│    "I need to create S3 bucket"              │
│                                              │
│ ⚠️ Does NOT check AWS reality directly!      │
│    Unless you run terraform refresh first    │
└──────────────────────────────────────────────┘
```

### How to Avoid "Already Exists" Errors

#### Method 1: Always Use Unique Names (Best)
```hcl
resource "aws_s3_bucket" "data" {
  bucket = "my-data-${var.environment}-${random_suffix.main.result}"
  # Outputs: my-data-prod-abc123 (always unique)
}

resource "random_string" "main" {
  length  = 6
  special = false
}
```

#### Method 2: Use ID/Name Variables (Flexible)
```hcl
variable "bucket_name" {
  type = string
  # Different per environment
}

resource "aws_s3_bucket" "data" {
  bucket = var.bucket_name
  # dev.tfvars: bucket_name = "data-dev"
  # prod.tfvars: bucket_name = "data-prod"
}
```

#### Method 3: Check State Before Planning

```bash
# Always check if resource already exists
terraform state list | grep aws_s3_bucket

# If it exists, don't recreate it!
# If it doesn't exist but should:
terraform import aws_s3_bucket.data existing-bucket-name
```

### Real-World Workflow: Never Get "Already Exists" Error

```bash
# 1. Always plan first (dry run)
terraform plan -var-file=prod.tfvars -out=tfplan

# 2. Review the plan output
# Shows: Plan: 5 to add, 2 to change, 0 to destroy.

# 3. If it shows "to add" but you know it exists:
#    This means it's not in state file!
terraform state list | grep resource-name

# 4. If missing from state: import it
terraform import aws_s3_bucket.data my-existing-bucket

# 5. Plan again
terraform plan -var-file=prod.tfvars

# 6. Now should show: No changes needed
# Safe to apply

terraform apply
```

### Detecting Drift (AWS Resources Changed Outside Terraform)

**Problem: Someone manually changed AWS infrastructure**
```bash
# Your state says: instance_type = t3.micro
# But in AWS console: instance_type = t3.large

terraform plan

# Output:
# aws_instance.web will be updated in-place
# ~ instance_type = "t3.micro" -> "t3.large"

# ⚠️ This only works after terraform refresh!
```

**To detect changes made outside Terraform:**
```bash
# Refresh state (read actual AWS state)
terraform refresh

# Then plan to see differences
terraform plan

# Or do both in one:
terraform plan -refresh=true
```

---

## Deleting Resources & Importing Existing Infrastructure

### How to Delete AWS Resources Using Terraform

There are different ways to delete resources depending on your needs:

#### Method 1: Remove from Code & Apply (Recommended)

**Step 1: Delete the resource definition from your .tf file**

```hcl
# main.tf - BEFORE
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}

# main.tf - AFTER (remove the resource)
# (resource completely deleted)
```

**Step 2: Plan to see what will be deleted**

```bash
terraform plan

# Output shows:
# Plan: 0 to add, 0 to change, 1 to destroy
# - aws_instance.web_server
```

**Step 3: Apply the deletion**

```bash
terraform apply

# AWS EC2 instance is now DELETED
```

#### Method 2: Selective Deletion (Delete One Resource Only)

Delete a specific resource without removing others:

```bash
# See what will be deleted
terraform plan -target=aws_instance.web_server

# Actually delete it
terraform apply -target=aws_instance.web_server

# This deletes ONLY that resource, leaves others untouched
```

#### Method 3: Remove from Terraform Without Deleting from AWS

Keep the resource in AWS but stop managing it with Terraform:

```bash
# Remove from Terraform state (AWS resource stays!)
terraform state rm aws_instance.web_server

# Now Terraform forgets about it
# The EC2 instance still exists in AWS
# You can manage it manually or re-import later
```

#### Method 4: Destroy Everything

Delete ALL resources managed by this Terraform configuration:

```bash
terraform destroy

# Shows list of everything to be destroyed
# Type: yes to confirm deletion
# All resources are destroyed
```

---

### Synchronizing Existing Resources with Terraform

**The Problem:** You have infrastructure created outside Terraform (manually in AWS console, by CloudFormation, etc.), but you want to manage it with Terraform now.

**Example Scenario:**
```
Existing AWS Resources (created manually):
├─ EC2 instance (i-0123456789abcdef0)
├─ S3 bucket (my-data-bucket)
├─ RDS database (my-db)
└─ VPC (vpc-12345678)

Your Terraform Code:
├─ (nothing - no resources defined)

Problem: Terraform doesn't know about these resources!
If you write code to create them, Terraform will:
1. Try to create NEW instances (conflict!)
2. Or fail because names are taken
```

### Solution: Import Existing Resources into Terraform State

**Process Overview:**
```
Step 1: Get resource ID from AWS (CLI or console)
        ↓
Step 2: Write resource definition in Terraform code
        (Don't apply yet!)
        ↓
Step 3: Import the existing resource: terraform import <id>
        ↓
Step 4: Verify state matches: terraform plan
        ↓
Step 5: Now Terraform manages it!
```

### Complete Example: Import Existing EC2 Instance

#### Step 1: Find the EC2 Instance ID

```bash
# List EC2 instances
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Output:
# InstanceId                    | Name
# i-0123456789abcdef0          | web-server
```

#### Step 2: Define Resource in Terraform (Don't Apply!)

```hcl
# main.tf
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

⚠️ **IMPORTANT:** Don't run `terraform apply` yet! State is empty - it will try to create a NEW instance!

#### Step 3: Import the Existing Instance

```bash
terraform import aws_instance.web_server i-0123456789abcdef0

# Output:
# aws_instance.web_server: Importing from ID "i-0123456789abcdef0"...
# aws_instance.web_server: Import complete!
# Resource 'aws_instance.web_server' successfully imported 1 item(s)
```

**What happened:** Terraform state now knows "aws_instance.web_server = i-0123456789abcdef0"

#### Step 4: Verify State Matches Reality

```bash
terraform plan

# Output should show:
# No changes. Your infrastructure matches the configuration.
# ✅ Success!
```

### Real-World Workflow: Import Multiple Resources

**Scenario:** You have existing VPC with subnets and security group created manually. You want Terraform to manage them.

**Step 1: Get All Resource IDs**

```bash
# Get VPC ID
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=my-vpc" \
  --query 'Vpcs[0].VpcId' --output text
# vpc-0123456789abcdef0

# Get Subnet IDs
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-0123456789abcdef0" \
  --query 'Subnets[*].[SubnetId,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Get Security Group ID
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-0123456789abcdef0" \
  --query 'SecurityGroups[0].GroupId' --output text
```

**Step 2: Write Terraform Code**

```hcl
# main.tf
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "my-vpc" }
}

resource "aws_subnet" "subnet1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags = { Name = "subnet-1" }
}

resource "aws_subnet" "subnet2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  tags = { Name = "subnet-2" }
}

resource "aws_security_group" "main" {
  vpc_id = aws_vpc.main.id
  name   = "main-sg"
  tags = { Name = "main-sg" }
}
```

**Step 3: Import All Resources**

```bash
# Import VPC
terraform import aws_vpc.main vpc-0123456789abcdef0

# Import Subnets
terraform import aws_subnet.subnet1 subnet-abcd1234
terraform import aws_subnet.subnet2 subnet-efgh5678

# Import Security Group
terraform import aws_security_group.main sg-0123456789abcdef0
```

**Step 4: Verify**

```bash
terraform plan

# Output:
# No changes. Your infrastructure matches the configuration.
# ✅ All 4 resources successfully imported!
```

### Import Examples for Common AWS Resources

#### S3 Bucket

```bash
# Add to Terraform
resource "aws_s3_bucket" "data" {
  bucket = "my-existing-bucket"
}

# Import it
terraform import aws_s3_bucket.data my-existing-bucket
```

#### RDS Database

```bash
# Find DB instance ID
aws rds describe-db-instances \
  --query 'DBInstances[0].DBInstanceIdentifier' --output text

# Add to Terraform
resource "aws_db_instance" "main" {
  identifier = "my-database"
  engine     = "postgres"
  # ... other config
}

# Import it
terraform import aws_db_instance.main my-database
```

#### IAM Role

```bash
# Find role name
aws iam list-roles --query 'Roles[0].RoleName' --output text

# Add to Terraform
resource "aws_iam_role" "lambda_role" {
  name = "my-lambda-role"
}

# Import it
terraform import aws_iam_role.lambda_role my-lambda-role
```

#### Lambda Function

```bash
# Add to Terraform
resource "aws_lambda_function" "my_function" {
  function_name = "my-function"
  # ... other config
}

# Import it
terraform import aws_lambda_function.my_function my-function
```

### Handling Import Challenges

#### Challenge 1: Resource Requires Additional Arguments

**Problem:** Terraform imports the resource but needs information AWS doesn't return.

```bash
# Verify what AWS actually has
aws ec2 describe-security-groups --group-ids sg-123456 \
  --query 'SecurityGroups[0]' --output json

# Update Terraform code to match AWS reality
resource "aws_security_group" "main" {
  name = "actual-name-from-aws"  # ← Match AWS exactly
  # ... other fields from AWS
}

# Then re-import
terraform import aws_security_group.main sg-123456
```

#### Challenge 2: Computed Attributes

Some attributes are **computed by AWS** (you can't set them, only read):

```hcl
resource "aws_instance" "web" {
  ami           = "ami-123"
  instance_type = "t3.micro"

  # These are COMPUTED (set by AWS after creation):
  # private_ip   = "10.0.1.42"      ← Don't define these!
  # public_ip    = "52.1.2.3"       ← Terraform reads them
  # vpc_id       = "vpc-123"        ← from state file
}
```

After import, Terraform's state has these values - they just won't be in your code.

#### Challenge 3: Imported Resource Has Different Config

**Problem:** You write Terraform code, but the existing AWS resource was configured differently.

```bash
# 1. Import the resource first
terraform import aws_instance.web i-0123456789

# 2. Check what Terraform stored in state
terraform state show aws_instance.web

# 3. Update your Terraform code to match what AWS actually has
# Edit main.tf to match the state

# 4. Verify
terraform plan
# (should show "No changes")
```

### Best Practices: Avoid Import Issues

#### The Prevention Approach (Best)

**Don't create resources outside Terraform!**

```
✅ CORRECT WORKFLOW:
1. Write Terraform code FIRST
2. Run terraform apply
3. Resources created through Terraform
4. Everything in sync from the start

❌ WRONG WORKFLOW:
1. Create EC2 in console manually
2. Create S3 bucket manually
3. Months later: Write Terraform code
4. Try to import everything
5. Fix mismatches (time-consuming!)
```

#### The Remediation Approach (If Needed)

**If you inherit existing infrastructure:**

```bash
# 1. Document all existing resources
aws ec2 describe-instances --output json > instances.json
aws s3api list-buckets --output json > buckets.json

# 2. Write complete Terraform code for everything
# (copy from aws-provider docs examples)

# 3. Import each resource carefully
terraform import <type>.<name> <aws-id>

# 4. Verify with terraform plan
# (should show "No changes")

# 5. From now on: manage ONLY via Terraform
```

### Useful State Commands for Import/Delete

```bash
# List all resources in state
terraform state list

# Show details of one resource
terraform state show aws_instance.web_server

# Remove resource from Terraform (keeps it in AWS)
terraform state rm aws_instance.web_server

# View state as JSON (advanced debugging)
terraform state pull | jq '.resources'

# Verify state matches current code
terraform plan
```

### Summary: Delete vs Import

| Task | Command | Result |
|------|---------|--------|
| **Delete resource from AWS** | Remove from .tf, `terraform apply` | Resource destroyed in AWS |
| **Keep AWS resource, remove Terraform management** | `terraform state rm <resource>` | AWS resource survives, Terraform forgets |
| **Delete only one resource** | `terraform destroy -target=<resource>` | Only that resource deleted |
| **Delete everything** | `terraform destroy` | All resources destroyed |
| **Import existing resource** | `terraform import <type>.<name> <id>` | Terraform now manages it |
| **Import multiple resources** | Multiple `terraform import` commands | Terraform manages all of them |

---

## Common Patterns & Use Cases

### Pattern 1: Multi-Environment Setup (Dev/Staging/Prod)

```
infrastructure/
├── main.tf                 # Core resources (shared)
├── variables.tf            # Variable definitions
├── outputs.tf              # Output definitions
├── dev.tfvars              # Dev environment values
├── staging.tfvars          # Staging environment values
└── prod.tfvars             # Prod environment values
```

**Usage:**
```bash
# Deploy to dev
terraform apply -var-file=dev.tfvars

# Deploy to prod
terraform apply -var-file=prod.tfvars
```

**main.tf example:**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type  # Different per environment

  tags = {
    Name        = "web-${var.environment}"
    Environment = var.environment
  }
}
```

**dev.tfvars:**
```hcl
environment        = "dev"
instance_type      = "t3.micro"
instance_count     = 1
enable_monitoring  = false
```

**prod.tfvars:**
```hcl
environment        = "prod"
instance_type      = "t3.large"
instance_count     = 3
enable_monitoring  = true
```

### Pattern 2: Creating Multiple Resources (Count)

**Scenario: Create 3 web servers**

```hcl
variable "instance_count" {
  type    = number
  default = 3
}

resource "aws_instance" "web" {
  count         = var.instance_count  # Creates 3 instances
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-${count.index}"  # web-0, web-1, web-2
  }
}

output "instance_ids" {
  value = aws_instance.web[*].id  # [*] = all instances
}
```

**Reference in code:**
```hcl
aws_instance.web[0].id    # First instance
aws_instance.web[1].id    # Second instance
aws_instance.web[*].id    # All instances
```

### Pattern 3: Conditional Resources (If/Then)

**Scenario: Only create monitoring in production**

```hcl
variable "environment" {
  type = string
}

variable "enable_monitoring" {
  type    = bool
  default = false
}

# Only creates if enable_monitoring is true
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count               = var.enable_monitoring ? 1 : 0
  alarm_name          = "high-cpu"
  comparison_operator = "GreaterThanThreshold"
  threshold           = 80
}
```

**With environment:**
```hcl
locals {
  enable_monitoring = var.environment == "prod"
}

resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = local.enable_monitoring ? 1 : 0
  # ...
}
```

### Pattern 4: Loop Over Map (For Each)

**Scenario: Create subnets for each AZ**

```hcl
locals {
  subnet_configs = {
    public  = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    private = { cidr = "10.0.2.0/24", az = "us-east-1b" }
    db      = { cidr = "10.0.3.0/24", az = "us-east-1c" }
  }
}

resource "aws_subnet" "main" {
  for_each          = local.subnet_configs  # Loop over map
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = {
    Name = "subnet-${each.key}"  # subnet-public, subnet-private, subnet-db
    Type = each.key
  }
}
```

**Reference in code:**
```hcl
aws_subnet.main["public"].id     # Public subnet
aws_subnet.main["private"].id    # Private subnet
aws_subnet.main["db"].id         # DB subnet
```

### Pattern 5: Extract to Modules (Reusable)

**Scenario: VPC module used by multiple projects**

```
modules/
├── vpc/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── eks-cluster/
    ├── main.tf
    ├── variables.tf
    └── outputs.tf

main.tf  # Calls modules
```

**modules/vpc/main.tf:**
```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = {
    Name = var.vpc_name
  }
}

resource "aws_subnet" "public" {
  for_each                = var.public_subnets
  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = true
}
```

**modules/vpc/variables.tf:**
```hcl
variable "vpc_name" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "public_subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
}
```

**modules/vpc/outputs.tf:**
```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [for subnet in aws_subnet.public : subnet.id]
}
```

**main.tf (using the module):**
```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_name = "main-vpc"
  vpc_cidr = "10.0.0.0/16"

  public_subnets = {
    web-a = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    web-b = { cidr = "10.0.2.0/24", az = "us-east-1b" }
  }
}

module "eks" {
  source = "./modules/eks-cluster"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
}
```

---

## Best Practices

### 1. Code Organization

```
project/
├── backend.tf              # Remote state config
├── main.tf                 # Core infrastructure
├── variables.tf            # Variable definitions
├── locals.tf               # Local values
├── outputs.tf              # Output definitions
├── terraform.tfvars        # Default values (commit to git)
├── terraform.dev.tfvars    # Dev overrides (optional)
├── terraform.prod.tfvars   # Prod overrides (optional)
├── .gitignore              # Ignore state files!
├── .terraform/             # (ignored)
└── modules/                # Reusable modules
    ├── vpc/
    ├── eks/
    └── database/
```

**Typical .gitignore:**
```
# Local .terraform directories
**/.terraform/*

# .tfstate files
*.tfstate
*.tfstate.*

# Crash log files
crash.log

# Ignore override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Include override files as an exception
!example_override.tf

# Lock file (commit this!)
.terraform.lock.hcl

# Sensitive files
*.tfvars
!example.tfvars
```

### 2. Always Review Before Applying

```bash
# Bad: Apply without seeing what will happen
terraform apply

# Good: Always plan first
terraform plan -out=tfplan
# Review the output carefully
terraform apply tfplan
```

### 3. Use Descriptive Names & Comments

```hcl
# Good: Clear what each resource does
resource "aws_security_group" "web_server_sg" {
  name        = "web-server-${var.environment}"
  description = "Security group for web server HTTP/HTTPS access"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP from internet
  ingress {
    description = "Allow HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Bad: Unclear what this is
resource "aws_sg" "sg1" {
  # ...
}
```

### 4. Use Variables for Values That Change

```hcl
# Bad: Hardcoded values (not reusable)
resource "aws_instance" "web" {
  instance_type = "t3.micro"
  availability_zone = "us-east-1a"
}

# Good: Use variables
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}

resource "aws_instance" "web" {
  instance_type     = var.instance_type
  availability_zone = var.availability_zone
}
```

### 5. Document Your Outputs

```hcl
# Bad: No explanation
output "instance_id" {
  value = aws_instance.web.id
}

# Good: Clear description
output "instance_id" {
  description = "EC2 instance ID (use this in other scripts)"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Public IP for SSH access: ssh -i key.pem ec2-user@${this value}"
  value       = aws_instance.web.public_ip
}
```

### 6. Use Explicit Dependencies When Needed

```hcl
# Sometimes order matters
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id

  # Wait for IGW to be ready (implicit dependency)
  depends_on = [aws_internet_gateway.main]
}
```

### 7. Protect Sensitive Values

```hcl
output "database_password" {
  description = "Database password"
  value       = aws_db_instance.main.password
  sensitive   = true  # Won't show in logs!
}

variable "api_key" {
  type        = string
  description = "API key (keep secret!)"
  sensitive   = true
  # Don't provide default!
}
```

---

## Troubleshooting

### Common Error: "No AWS credentials found"

**Problem:**
```
Error: error configuring Terraform AWS Provider: no valid credential sources for Terraform AWS Provider found.
```

**Solutions:**

```bash
# 1. Using AWS profile
export AWS_PROFILE=my-profile
terraform apply

# 2. Using environment variables
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
terraform apply

# 3. Using credentials file
# ~/.aws/credentials:
[default]
aws_access_key_id = ...
aws_secret_access_key = ...

# Then in Terraform:
provider "aws" {
  region = "us-east-1"
}

# 4. Check what Terraform sees
terraform providers
```

### Common Error: "Resource already exists"

**Problem:**
```
Error: Error creating DB instance: InvalidDBInstanceIdentifier.AlreadyExists: DB instance already exists
```

**Solutions:**
```bash
# Option 1: Import existing resource
resource "aws_db_instance" "main" {
  # ...
}

terraform import aws_db_instance.main my-database

# Option 2: Use different name
resource "aws_db_instance" "main" {
  identifier = "my-database-${random_suffix.main.keepers.value}"
}

# Option 3: Manually delete and recreate
aws rds delete-db-instance --db-instance-identifier my-database --skip-final-snapshot
terraform apply
```

### Common Error: "Timeout waiting for resource"

**Problem:**
```
Error: timeout while waiting for state to become 'available'
```

**Happens with:**
- RDS instances (can take 10+ minutes)
- ECS tasks (can be slow)
- Lambda layer creation

**Solution:**
```hcl
# Increase timeout
resource "aws_db_instance" "main" {
  engine = "postgres"
  # ... other config ...

  # Default is 40 minutes, usually enough
  timeouts {
    create = "60m"
    delete = "60m"
  }
}
```

### State File Problems

```bash
# State locked? (from failed apply)
terraform force-unlock LOCK_ID

# Lost state file? (disaster)
# Option 1: Recover from backup/remote
terraform init  # Pulls from S3

# Option 2: Destroy everything and restart
terraform destroy
# Manually delete AWS resources

# State out of sync?
terraform refresh  # Read actual AWS state
terraform plan     # See what's different
```

---

## Advanced Topics

### 1. Using Terraform Modules from Registry

```hcl
# Use VPC module from Terraform Registry
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false  # High availability
  enable_vpn_gateway = true

  tags = local.common_tags
}
```

### 2. Dynamic Blocks (Advanced)

```hcl
# Instead of repeating ingress blocks:
resource "aws_security_group" "web" {
  dynamic "ingress" {
    for_each = [
      { port = 80, protocol = "tcp" },
      { port = 443, protocol = "tcp" },
      { port = 22, protocol = "tcp" }
    ]

    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}
```

### 3. Splat Syntax (Simplify Loops)

```hcl
# Get all instance IDs without explicit loop
resource "aws_instance" "web" {
  count = 3
  # ...
}

# Bad: Manual loop
output "ids" {
  value = [
    aws_instance.web[0].id,
    aws_instance.web[1].id,
    aws_instance.web[2].id,
  ]
}

# Good: Splat syntax
output "ids" {
  value = aws_instance.web[*].id
}

# Also works with attributes
output "private_ips" {
  value = aws_instance.web[*].private_ip
}

output "tags_by_name" {
  value = { for inst in aws_instance.web : inst.tags.Name => inst.id }
}
```

### 4. Workspaces (Multiple Environments)

```bash
# Create workspaces for different environments
terraform workspace new dev
terraform workspace new prod

# Switch between workspaces
terraform workspace select dev
terraform apply -var-file=dev.tfvars

terraform workspace select prod
terraform apply -var-file=prod.tfvars

# Show current workspace
terraform workspace show

# State files are separate per workspace
# dev state: terraform.tfstate.d/dev/terraform.tfstate
# prod state: terraform.tfstate.d/prod/terraform.tfstate
```

### 5. Pre/Post Hooks with Provisioners (Use Sparingly)

```hcl
# Generally avoid provisioners, but sometimes necessary
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  # Local-exec: Run command on YOUR machine
  provisioner "local-exec" {
    command = "echo 'Instance created' >> log.txt"
  }

  # Remote-exec: Run command on the instance
  provisioner "remote-exec" {
    inline = [
      "sudo yum install -y httpd",
      "sudo systemctl start httpd"
    ]

    connection {
      type        = "ssh"
      user        = "ec2-user"
      private_key = file("~/.ssh/key.pem")
      host        = self.public_ip
    }
  }
}
```

**Why avoid?** Provisioners are:
- Hard to debug
- Not idempotent (running twice != running once)
- Better done with user data or configuration management

**Better alternative: User Data**
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    environment = var.environment
  }))
}
```

---

## Quick Reference: Common Commands

```bash
# Core workflow
terraform init                 # Initialize
terraform plan                 # Preview changes
terraform apply                # Apply changes
terraform destroy              # Destroy all

# Inspection
terraform state list           # List resources
terraform state show resource  # Show resource details
terraform output               # Show outputs
terraform output -json         # Output as JSON

# Advanced
terraform import type.name id  # Import existing resource
terraform plan -target=res     # Plan specific resource
terraform apply -var key=val   # Override variable
terraform fmt                  # Format code
terraform validate             # Check syntax
terraform graph > graph.txt    # Visualize

# State management
terraform state pull           # Download state
terraform state push file      # Upload state
terraform state mv old new     # Rename resource
terraform state rm resource    # Remove from state
terraform refresh              # Sync with reality
```

---

## Resources

- **Official Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Terraform Language Docs**: https://www.terraform.io/language/
- **Getting Started with Terraform**: https://github.com/ned1313/Getting-Started-Terraform
- **Terraform Modules Registry**: https://registry.terraform.io/
- **AWS Terraform Examples**: https://registry.terraform.io/modules/terraform-aws-modules/
