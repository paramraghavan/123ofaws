On startup detect the instanceids, cluster ids and then run failover

### Core Components:

1. **failover.py** - Main script that:
    - Detects EC2 instances and EMR clusters
    - Logs status to multiple formats (text + JSONL)
    - Performs failover operations (restart EC2, recreate EMR)
    - Uses AWS profiles for authentication

2. **app.py** - Flask web application with:
    - Real-time dashboard showing current status
    - Analytics for status trends and failover success rates
    - Three log viewers (Status, Failover, System logs)
    - REST API endpoints for programmatic access
    - Auto-refresh every 30 seconds

3. **config.py** - Centralized configuration for AWS profiles, regions, and paths

4. **templates/index.html** - Beautiful web dashboard with:
    - Modern gradient design
    - Interactive tabs for different log types
    - Real-time status cards
    - Color-coded success/failure indicators

5. **Launcher scripts** - Easy-to-use scripts for both Linux/Mac (`run.sh`) and Windows (`run.bat`)

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create templates directory and add index.html
mkdir templates

# 3. Configure your AWS profile in config.py
# AWS_PROFILE = 'your-profile-name'

# 4. Run detection
python failover.py

# 5. Start web viewer
python app.py
# Visit http://localhost:5000
```

## 🎯 Key Features

- ✅ **Auto-detects** EC2 and EMR resources on startup
- ✅ **Logs everything** in JSON and text formats
- ✅ **Web dashboard** with analytics and visualization
- ✅ **AWS profile support** for multi-account setups
- ✅ **Programmatic API** for integration
- ✅ **Failover automation** with success tracking

## 📊 Dashboard Features

The web viewer provides:

- **Current Status** card with live resource counts
- **Status Analysis** showing historical trends
- **Failover Analysis** with success rates
- **Three log tabs** for different data views
- **Auto-refresh** to stay current
