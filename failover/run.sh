#!/bin/bash

# AWS Failover Manager Launcher Script

echo "======================================"
echo "  AWS Failover Manager Launcher"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs
mkdir -p templates

echo ""
echo "======================================"
echo "  Choose an option:"
echo "======================================"
echo "1) Run failover detection & status logging"
echo "2) Start Flask web dashboard"
echo "3) Run failover with auto-restart (EC2 & EMR)"
echo "4) Restart specific EMR cluster"
echo "5) View recent logs"
echo "6) Exit"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🔍 Running failover detection..."
        python3 failover.py
        ;;
    2)
        echo ""
        echo "🌐 Starting Flask web dashboard..."
        echo "   Access at: http://localhost:5000"
        echo "   Press Ctrl+C to stop"
        echo ""
        python3 app.py
        ;;
    3)
        echo ""
        echo "⚠️  WARNING: This will restart EC2 instances and recreate EMR clusters!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🔄 Running failover with auto-restart..."
            # This would need the failover.py main() function uncommented
            python3 failover.py
        else
            echo "❌ Failover cancelled"
        fi
        ;;
    4)
        echo ""
        echo "🔄 Restart specific EMR cluster"
        read -p "Enter cluster ID (e.g., j-XXXXXXXXXXXXX): " cluster_id
        if [ -n "$cluster_id" ]; then
            echo "⚠️  WARNING: This will terminate and recreate cluster $cluster_id"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                python3 -c "from failover import AWSFailoverManager; m = AWSFailoverManager(); m.restart_emr_cluster('$cluster_id')"
            else
                echo "❌ Restart cancelled"
            fi
        else
            echo "❌ No cluster ID provided"
        fi
        ;;
    5)
        echo ""
        echo "📋 Recent logs:"
        echo "======================================"
        if [ -f "logs/failover.log" ]; then
            tail -n 20 logs/failover.log
        else
            echo "No logs found. Run detection first."
        fi
        ;;
    6)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Deactivate virtual environment
deactivate