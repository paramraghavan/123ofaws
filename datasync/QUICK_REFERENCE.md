# Quick Reference Card

**Print this or bookmark for quick access!**

## 🚀 Getting Started (Choose Your Path)

### ⚡ Fast Track (5 minutes)
```bash
1. Read getting_started.md
2. pip install -r requirements.txt
3. cp .env.example .env
4. python lambda_function.py daily
```

### 👨‍💻 Developer Setup (2 hours)
1. Read developer_guide.md
2. Run: python -m venv venv && source venv/bin/activate
3. Run: pip install -r requirements.txt
4. Run: pytest test_date_logic.py -v
5. Review example_*.py files

### 🏗️ AWS/DevOps (4+ hours)
1. Read datasync_overview.md
2. Follow setup_guide.md
3. Follow deployment_guide.md
4. Test with example_daily_copy.py

## 📚 Documentation Map

| Need | File |
|------|------|
| Quick overview | getting_started.md |
| Everything | README.md |
| Setup locally | developer_guide.md |
| Setup AWS | setup_guide.md |
| Deploy | deployment_guide.md |
| API docs | api_reference.md |
| Architecture | datasync_overview.md |
| Problems? | troubleshooting.md |
| Lost? | documentation_map.md |
| New team? | onboarding_checklist.md |

## ⌨️ Common Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Local Testing
python lambda_function.py daily
python lambda_function.py backdated 2024/0721
python lambda_function.py range 7
pytest test_date_logic.py -v

# AWS
aws configure
aws datasync list-locations
aws logs tail /aws/lambda/datasync-orchestrator --follow
aws lambda invoke --function-name datasync-orchestrator \
  --payload '{"scenario":"daily"}' response.json

# Configuration
cp .env.example .env
nano .env
source .env
```

## 📁 File Organization

```
Core Code:          config.py, date_logic.py, 
                    datasync_manager.py, lambda_function.py
Tests:              test_date_logic.py
Examples:           example_*.py (3 files)
Configuration:      .env.example, requirements.txt, .gitignore
Documentation:      README.md, *_guide.md, *_reference.md
                    documentation_map.md, onboarding_checklist.md
```

## 🔍 Quick Lookups

### "How do I...?"
- Set up locally? → developer_guide.md
- Deploy to Lambda? → deployment_guide.md
- Copy files? → example_daily_copy.py
- Fix an error? → troubleshooting.md
- Understand the code? → api_reference.md

### "What is...?"
- AWS DataSync? → datasync_overview.md
- This project? → README.md
- The architecture? → datasync_overview.md
- A module? → api_reference.md

### "I'm getting error..."
- ModuleNotFoundError → developer_guide.md
- AWS credentials error → developer_guide.md
- Task failed → troubleshooting.md
- Permission denied → troubleshooting.md
- Lambda timeout → troubleshooting.md

## 🎯 Role-Based Quick Start

### New Developer
1. getting_started.md (5 min)
2. developer_guide.md (30 min)
3. Run tests (5 min)
4. review_and_additions.md (10 min)

### DevOps/SRE
1. README.md (10 min)
2. setup_guide.md (20 min)
3. deployment_guide.md (20 min)
4. example_monitoring.py (10 min)

### Architect/Tech Lead
1. README.md (15 min)
2. datasync_overview.md (20 min)
3. api_reference.md (30 min)
4. review_and_additions.md (10 min)

## 🆘 Troubleshooting Quick Links

1. **Virtual env issues** → developer_guide.md#local-development-setup
2. **Import errors** → developer_guide.md#common-development-tasks
3. **AWS permission errors** → troubleshooting.md#issue-1
4. **No files copied** → troubleshooting.md#issue-2
5. **Lambda timeout** → troubleshooting.md#issue-3
6. **Date format wrong** → troubleshooting.md#issue-7

## 📞 Need Help?

1. **Quick answer?** → documentation_map.md (finding answers section)
2. **Stuck on error?** → troubleshooting.md
3. **Understanding code?** → api_reference.md
4. **Setting up?** → Use the appropriate *_guide.md
5. **Can't find doc?** → documentation_map.md

## ✅ Checklist: Ready to Deploy?

- [ ] Read: getting_started.md or developer_guide.md
- [ ] Setup: Virtual env + requirements installed
- [ ] Config: .env file with values filled in
- [ ] Test: pytest test_date_logic.py passes
- [ ] AWS: Credentials configured (aws configure)
- [ ] AWS: DataSync locations created
- [ ] Code: Reviewed lambda_function.py and config.py
- [ ] Deploy: Followed deployment_guide.md
- [ ] Monitor: Can access CloudWatch logs
- [ ] Test: Lambda invokes successfully

## 📊 Project Stats

- **Python Code**: 4 modules + 3 examples + 1 test
- **Documentation**: 12 markdown files
- **Configuration**: Templates + git config
- **Total Setup Time**: 5 min (fast track) to 4 hours (full setup)
- **Production Ready**: ✅ Yes
- **Fresh Developer Ready**: ✅ Yes

## 🎓 Learning Path

### Day 1 (3-4 hours)
- [ ] Read: getting_started.md
- [ ] Read: README.md
- [ ] Read: developer_guide.md (code structure section)
- [ ] Setup: Local environment
- [ ] Test: Run pytest
- [ ] Review: Example files

### Day 2-3 (4-6 hours)
- [ ] Read: datasync_overview.md
- [ ] Read: api_reference.md
- [ ] Run: All example scripts
- [ ] Test: With actual AWS (if available)
- [ ] Read: relevant *_guide.md files

### Week 2+
- [ ] Deploy to Lambda
- [ ] Monitor in production
- [ ] Handle real-world scenarios
- [ ] Contribute improvements

---

**For detailed documentation, see documentation_map.md**

**For onboarding structure, use onboarding_checklist.md**

**All files in: /Users/paramraghavan/dev/123ofaws/datasync/**

Happy coding! 🚀
