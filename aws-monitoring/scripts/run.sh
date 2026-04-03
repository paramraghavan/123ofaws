#!/bin/bash

# AWS Monitoring System - Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AWS Monitoring System${NC}"
echo "========================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Check dependencies
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Parse arguments
CONFIG="${1:-config/config.yaml}"
PREFIXES="${2:-uat-}"
PORT="${3:-5000}"
HOST="${4:-0.0.0.0}"

# Support both --prefix and --prefixes in arguments
if [[ "$PREFIXES" == *","* ]]; then
    ARGS="--prefixes \"$PREFIXES\""
    echo "Configuration: $CONFIG"
    echo "Stack Prefixes (multiple): $PREFIXES"
else
    ARGS="--prefix \"$PREFIXES\""
    echo "Configuration: $CONFIG"
    echo "Stack Prefix: $PREFIXES"
fi

echo "Server: http://$HOST:$PORT"
echo ""

# Check config exists
if [ ! -f "$CONFIG" ]; then
    echo -e "${YELLOW}Config file not found: $CONFIG${NC}"
    echo -e "${YELLOW}Creating from example...${NC}"
    cp config/config.example.yaml "$CONFIG"
    echo -e "${GREEN}Created: $CONFIG${NC}"
    echo -e "${YELLOW}Please edit the configuration file before running again.${NC}"
    exit 0
fi

echo -e "${GREEN}Starting monitoring system...${NC}"
echo ""

# Start the application
if [[ "$PREFIXES" == *","* ]]; then
    python3 src/main.py --config "$CONFIG" --prefixes "$PREFIXES" --port "$PORT" --host "$HOST"
else
    python3 src/main.py --config "$CONFIG" --prefix "$PREFIXES" --port "$PORT" --host "$HOST"
fi
