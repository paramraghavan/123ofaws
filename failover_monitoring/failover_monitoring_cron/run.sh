#!/bin/bash

# AWS Failover System - Quick Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AWS Failover Monitoring System      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

print_success "Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi

# Check if required files exist
if [ ! -f "failover_main.py" ]; then
    print_error "failover_main.py not found. Please ensure all files are in the current directory."
    exit 1
fi

# Create logs directory
mkdir -p logs
print_success "Logs directory created"

# Check if requirements are installed
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# Install requirements
if [ -f "requirements.txt" ]; then
    print_info "Installing dependencies..."
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
fi

# Create config if doesn't exist
if [ ! -f "config.json" ]; then
    print_warning "config.json not found. Creating sample configuration..."
    python3 utils.py
    print_success "Sample config.json created. Please edit with your settings."
    print_info "Edit config.json before running the system."
    exit 0
fi

# Menu
echo ""
echo -e "${GREEN}Select operation mode:${NC}"
echo "1) Monitor only"
echo "2) Failover only"
echo "3) Both (Monitor + Failover)"
echo "4) Start Web Dashboard"
echo "5) Exit"
echo ""

read -p "Enter your choice [1-5]: " choice

case $choice in
    1|2|3)
        # Check if config.json has defaults
        has_profile=$(python3 -c "import json; print(json.load(open('config.json')).get('aws_profile', ''))" 2>/dev/null)
        has_tag=$(python3 -c "import json; print(json.load(open('config.json')).get('tag_name', ''))" 2>/dev/null)

        if [ -n "$has_profile" ] && [ -n "$has_tag" ]; then
            print_info "Using defaults from config.json:"
            print_info "  Profile: $has_profile"
            print_info "  Tag Name: $has_tag"
            echo ""
            read -p "Use these defaults? (Y/n): " use_defaults

            if [[ "$use_defaults" =~ ^[Nn]$ ]]; then
                read -p "Enter AWS Profile name: " profile
                read -p "Enter Resource Tag Name: " tag_name
                extra_args="--profile $profile --tag-name $tag_name"
            else
                extra_args=""
            fi
        else
            read -p "Enter AWS Profile name: " profile
            read -p "Enter Resource Tag Name: " tag_name

            if [ -z "$profile" ] || [ -z "$tag_name" ]; then
                print_error "Profile and Tag Name are required!"
                exit 1
            fi
            extra_args="--profile $profile --tag-name $tag_name"
        fi

        mode="both"
        case $choice in
            1) mode="monitor" ;;
            2) mode="failover" ;;
            3) mode="both" ;;
        esac

        print_info "Starting failover system..."
        print_info "Mode: $mode"
        echo ""

        python3 failover_main.py \
            $extra_args \
            --mode "$mode" \
            --log-level INFO

        print_success "Operation completed!"
        echo ""
        print_info "View logs at: http://localhost:5000 (run option 4)"
        ;;

    4)
        print_info "Starting web dashboard..."
        print_info "Access the dashboard at: http://localhost:5000"
        echo ""
        python3 webapp.py
        ;;

    5)
        print_info "Exiting..."
        exit 0
        ;;

    *)
        print_error "Invalid choice!"
        exit 1
        ;;
esac

# Deactivate virtual environment
deactivate

echo ""
print_success "All done! 🎉"