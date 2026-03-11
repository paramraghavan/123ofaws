# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**123ofaws** is a comprehensive educational AWS learning resource with examples, documentation, and tools covering AWS services. It's designed for AWS beginners and intermediates, containing a collection of independent projects and examples rather than a single monolithic application.

### Purpose
- Learning and reference material for AWS services
- Code examples for various AWS use cases
- Documentation and guides for AWS concepts

## Architecture & Project Structure

The repository is organized by AWS service and feature domain:

### Key Sections

1. **Foundation Services** (core AWS understanding required)
   - `iam/` - Identity and Access Management examples
   - `vpc/` - Virtual Private Cloud setup and configuration
   - `s3/` - Simple Storage Service operations and patterns

2. **Compute Services**
   - `aws-fargate/` - Container orchestration without infrastructure management
   - `aws-batch/` - Large-scale batch processing
   - `serverless/` - Serverless Framework examples and deployment

3. **Data & Analytics**
   - `glue/` - Data catalog and ETL examples
   - `s3-sql/` - SQL queries on S3 data
   - `datalake/` - Data lake architecture patterns
   - `iceberg/` - Iceberg table format examples

4. **Message Queue & Event Services**
   - `sns-sqs/` - SNS and SQS messaging patterns

5. **Infrastructure & Automation**
   - `cloudformation/` - Infrastructure as Code templates
   - `terraform/` - Terraform examples
   - `aws-systems-manager/` - Systems Manager automation
   - `cost/` - Cost optimization and calculation tools

6. **Development & Local Testing**
   - `simulate_aws/` - **LocalStack setup** for running AWS services locally (docker-compose)
   - `boto3/` - Boto3 SDK documentation and examples

7. **Complex Applications**
   - `failover_ver3/` - Production-like application: automated AWS resource failover/recovery system with Flask web dashboard
   - `airflow/` - Apache Airflow examples for orchestration

8. **Learning & Reference**
   - `QandA/` - Q&A and common questions about AWS
   - `exercises/` - Hands-on exercises
   - `aws-python-cheatsheet.md` - Comprehensive Python/AWS reference (includes LocalStack setup details)
   - `README.md` - Overview of cloud concepts and AWS architecture

## Technology Stack

- **Language**: Python (primary), Bash scripts
- **AWS SDK**: Boto3
- **Local Development**: LocalStack (Docker-based AWS emulation)
- **Web Framework**: Flask (used in failover_ver3)
- **Infrastructure**: CloudFormation, Terraform
- **Orchestration**: Apache Airflow, AWS Step Functions

## Common Development Tasks

### Running Python Examples
Most examples follow this pattern:
```bash
# Install dependencies
pip install -r requirements.txt

# Run example
python example_script.py
```

### Using LocalStack for Local Development
LocalStack allows running AWS services locally without AWS account charges:

```bash
# Setup LocalStack (see simulate_aws/ for full details)
cd simulate_aws
docker-compose up

# In another terminal, run tests against LocalStack
python test_localstack.py
```

The `simulate_aws/setup.sh` provides complete LocalStack configuration with multiple AWS services enabled.

### Running the Failover System (failover_ver3)
This is a more complex application with monitoring and recovery capabilities:

```bash
cd failover_ver3
pip install -r requirements.txt

# Option 1: Interactive shell
./run.sh

# Option 2: With config file
python failover_main.py --profile prod --tag-name production --mode monitor

# Option 3: View web dashboard
python webapp.py
# Navigate to http://localhost:5000
```

## Important Notes for Development

1. **Independent Projects**: Each directory is largely independent. Changes to one section rarely affect others.

2. **Boto3 Usage**: Examples use boto3 for AWS interactions. Always check which AWS service is being used (S3, EC2, RDS, etc.) when understanding code.

3. **AWS Credentials**: Examples requiring real AWS access need properly configured AWS credentials:
   - Configure via `aws configure`
   - Use AWS profiles in code (e.g., `--profile prod`)
   - LocalStack examples use fake credentials

4. **Documentation**: Each major section has README.md files. Always check section-specific docs before making changes.

5. **Configuration**: Projects like failover_ver3 use config.json for settings. Review example configs before running.

6. **Docker Requirement**: LocalStack and some examples require Docker. See `simulate_aws/README.md` for setup.

## When Modifying Code

- **Example Code**: Most code is for learning/reference. Keep examples clear and simple.
- **Documentation**: If adding examples, include docstrings and inline comments explaining the "why".
- **Dependencies**: Check `requirements.txt` files before adding new packages.
- **AWS Permissions**: Consider IAM permissions needed for examples (documented in relevant READMEs).

## Reference Files

- `aws-python-cheatsheet.md` - Complete LocalStack setup and Python/AWS patterns
- `simulate_aws/README.md` - Local AWS simulation setup details
- `failover_ver3/quick_start_guide.md` - Quick start for the failover application
- Main `README.md` - AWS concepts, cloud models, managed vs unmanaged services