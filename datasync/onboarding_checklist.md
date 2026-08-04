# Onboarding Checklist for New Developers

Use this checklist when bringing a new developer onto the project. Track progress and ensure nothing is missed.

---

## Developer Information

- **Name**: ___________________________
- **Start Date**: ___________________________
- **Role**: 👨‍💻 Developer / 🏗️ DevOps / 👀 Architect / Other: _________
- **GitHub/Git User**: ___________________________

---

## Phase 1: Environment Setup (Day 1 - 2 hours)

### Local Development Environment

- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] Git installed and configured (`git config --global user.name` and `user.email`)
- [ ] Code editor/IDE installed (VSCode, PyCharm, etc.)
- [ ] AWS CLI v2 installed (`aws --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Project cloned/downloaded to local machine

### Virtual Environment

- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Installation verified (`python -c "import boto3; print('✓')"`)

### Configuration

- [ ] Copied `.env.example` to `.env`
- [ ] Filled in `.env` with actual values or AWS ARNs
- [ ] Configuration tested (`python -c "from config import get_config; get_config()"`)
- [ ] Date logic tested (`python -c "from date_logic import DateLogic; print(DateLogic.get_today())"`)

### Verification

- [ ] Unit tests pass (`pytest test_date_logic.py -v`)
- [ ] Code can be imported without errors
- [ ] Examples can be listed (`ls -la example_*.py`)

**Checkpoint**: ✅ Developer can run `python lambda_function.py daily` without errors

---

## Phase 2: Understanding the Project (Day 1-2 - 4 hours)

### Documentation Reading (Required)

- [ ] Read [getting_started.md](getting_started.md) (5 min)
- [ ] Read [README.md](README.md) (15 min)
- [ ] Skim [datasync_overview.md](datasync_overview.md) (20 min) - at least sections 1-2
- [ ] Read [developer_guide.md](developer_guide.md) - Code Structure section (10 min)
- [ ] Read [api_reference.md](api_reference.md) - Overview sections (15 min)

### Architecture Understanding

- [ ] Understand what AWS DataSync does
- [ ] Understand the NAS → DataSync → S3 flow
- [ ] Understand why this approach is recommended
- [ ] Understand the date-based filtering concept (YYYY/MMDD format)

**Task**: Draw architecture on whiteboard or paper from memory

### Code Understanding

- [ ] Can explain what `config.py` does
- [ ] Can explain what `date_logic.py` does
- [ ] Can explain what `datasync_manager.py` does
- [ ] Can explain what `lambda_function.py` does
- [ ] Can trace data flow from Lambda → S3

**Task**: Walk through code with buddy/mentor for 30 minutes

---

## Phase 3: Hands-On Practice (Day 2-3 - 4 hours)

### Testing & Running

- [ ] Run tests: `pytest test_date_logic.py -v`
- [ ] Review test output and understand test structure
- [ ] Run date logic test in Python REPL:
  ```python
  from date_logic import DateLogic
  print(DateLogic.get_today())
  print(DateLogic.get_last_n_days(7))
  ```
- [ ] Review examples: `cat example_daily_copy.py`
- [ ] Understand what each example does

### Local Testing (Without AWS)

- [ ] Test date calculation locally (`python -c "from date_logic import ..."`)
- [ ] Test configuration loading (`python -c "from config import get_config; ..."`)
- [ ] Review CloudWatch logs of existing deployments (if available)

### AWS Testing (If credentials available)

- [ ] Test AWS credentials: `aws sts get-caller-identity`
- [ ] List existing DataSync locations: `aws datasync list-locations`
- [ ] List Lambda functions: `aws lambda list-functions`
- [ ] Try running Lambda manually: `aws lambda invoke ... --payload '{"scenario":"daily"}'`

**Task**: Run through all examples and document results

---

## Phase 4: Deeper Learning (Day 3-4 - 4 hours)

### API Deep Dive

- [ ] Read [api_reference.md](api_reference.md) - Complete modules section
- [ ] Review each module's docstrings:
  ```bash
  python -c "from config import Config; help(Config.get_task_name)"
  python -c "from date_logic import DateLogic; help(DateLogic.get_date_range)"
  python -c "from datasync_manager import DataSyncOrchestrator; help(DataSyncOrchestrator.execute_copy_task)"
  ```

### AWS DataSync Understanding

- [ ] Understand DataSync concepts (agents, locations, tasks, executions)
- [ ] Know how to create locations: `aws datasync create-location-nfs`
- [ ] Know how to list tasks: `aws datasync list-tasks`
- [ ] Know how to check execution status: `aws datasync describe-task-execution`

### Deployment Understanding

- [ ] Read [deployment_guide.md](deployment_guide.md) - Understand overall flow
- [ ] Understand Lambda function requirements (timeout, memory, roles)
- [ ] Understand EventBridge trigger setup
- [ ] Understand how environment variables work in Lambda

**Task**: Document the data flow for daily execution

---

## Phase 5: Problem Solving (Day 4-5 - 3 hours)

### Troubleshooting Knowledge

- [ ] Review [troubleshooting.md](troubleshooting.md) - Read all 8 issues
- [ ] Understand common permission errors
- [ ] Understand common timeout issues
- [ ] Know where to check logs (CloudWatch)
- [ ] Know how to debug locally

### Development Skills

- [ ] Know how to add logging: `import logging; logger.info(...)`
- [ ] Know how to use Python debugger (if needed)
- [ ] Know how to read error messages
- [ ] Know how to search documentation

**Task**: Solve 3 practice problems from troubleshooting guide

---

## Phase 6: Code Review (Day 5 - 2 hours)

### Code Quality

- [ ] Review code for:
  - [ ] Clear variable names
  - [ ] Proper error handling
  - [ ] Docstrings/comments
  - [ ] No hardcoded values
  - [ ] Proper AWS SDK usage

- [ ] Understand coding standards:
  - [ ] Python style (PEP 8)
  - [ ] Naming conventions
  - [ ] Comment style
  - [ ] Test structure

### Security Review

- [ ] Understand how secrets are handled (.env file)
- [ ] Understand IAM role structure
- [ ] Understand encryption in transit
- [ ] Know what NOT to commit (credentials, .env, etc.)

**Task**: Perform code review with senior developer

---

## Phase 7: First Contribution (Days 5-6 - 4 hours)

### Easy Tasks (Pick one)

- [ ] [ Task 1 ] Add a comment to explain complex code
- [ ] [ Task 2 ] Add a new test case
- [ ] [ Task 3 ] Improve documentation or fix typos
- [ ] [ Task 4 ] Add a debug logging statement
- [ ] [ Task 5 ] Create a simple example script

### Process

- [ ] Create a branch: `git checkout -b feature/my-change`
- [ ] Make changes
- [ ] Run tests: `pytest -v`
- [ ] Format code: `black *.py`
- [ ] Commit with clear message: `git commit -m "..."`
- [ ] Push to remote: `git push`
- [ ] Create pull request
- [ ] Address code review feedback
- [ ] Merge to main

**Task**: Complete and merge first contribution

---

## Phase 8: Knowledge Transfer (Week 2 - 2 hours)

### Pair Programming

- [ ] [ ] 1 hour pair programming with experienced developer
  - Implement small feature together
  - Ask questions about design decisions

### Q&A Session

- [ ] [ ] 30 minutes team Q&A
  - Ask about project history
  - Ask about future plans
  - Clarify any confusion

### Documentation Review

- [ ] [ ] 30 minutes review documentation with mentor
  - Which docs are most useful?
  - What's missing?
  - Suggest improvements

---

## Ongoing Learning (Continuous)

### Weekly Tasks

- [ ] [ ] Attend team standup/meeting
- [ ] [ ] Review changes from other developers
- [ ] [ ] Update personal documentation/notes

### Monthly Tasks

- [ ] [ ] Review AWS DataSync documentation update (if any)
- [ ] [ ] Review project changes and PRs
- [ ] [ ] Identify potential improvements

### Resources to Bookmark

- [ ] [AWS DataSync Documentation](https://docs.aws.amazon.com/datasync/)
- [ ] [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [ ] [Python Docs](https://docs.python.org/3/)
- [ ] Project documentation (documentation_map.md)

---

## Sign-Off

### Developer Sign-Off

I confirm that I have completed the onboarding checklist and understand:
- ✅ How to set up the project locally
- ✅ How the code is organized
- ✅ How the system works architecturally
- ✅ How to run tests and examples
- ✅ How to deploy to production
- ✅ How to troubleshoot problems

**Developer Name**: _________________________ **Date**: _________

**Signature**: _____________________________

### Mentor/Lead Sign-Off

I confirm that I have reviewed this developer's progress and they are ready to:
- ✅ Work independently on the project
- ✅ Troubleshoot issues
- ✅ Make contributions
- ✅ Review others' code

**Mentor Name**: _________________________ **Date**: _________

**Signature**: _____________________________

---

## Quick Reference After Onboarding

### Daily Commands

```bash
# Activate environment
source venv/bin/activate

# Load configuration
source .env

# Run tests
pytest test_date_logic.py -v

# Test scenarios
python lambda_function.py daily
python lambda_function.py backdated 2024/0721

# View logs
aws logs tail /aws/lambda/datasync-orchestrator --follow

# Deploy Lambda
# See deployment_guide.md
```

### Important Files to Know

| File | Purpose |
|------|---------|
| config.py | Configuration |
| date_logic.py | Date utilities |
| datasync_manager.py | AWS integration |
| lambda_function.py | Lambda handler |
| .env | Your local configuration |
| .env.example | Configuration template |
| test_date_logic.py | Unit tests |
| example_*.py | Example scripts |

### Key Contacts

| Role | Name | Email |
|------|------|-------|
| Tech Lead | | |
| DevOps | | |
| AWS Architect | | |
| Project Manager | | |

### Useful Links

- [Project README](README.md)
- [Documentation Map](documentation_map.md)
- [Developer Guide](developer_guide.md)
- [API Reference](api_reference.md)
- [Troubleshooting](troubleshooting.md)
- [AWS DataSync Docs](https://docs.aws.amazon.com/datasync/)

---

## Notes

Use this space for additional notes, blockers, or observations:

```
________________________________________________________________________________________
________________________________________________________________________________________
________________________________________________________________________________________
________________________________________________________________________________________
```

---

**Congratulations on joining the team! 🎉**

If you have any questions, check [documentation_map.md](documentation_map.md) to find the right resource.

