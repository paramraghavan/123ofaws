#!/bin/bash
#
# LocalStack Setup Script
# This script configures your system to use LocalStack
#

set -e

echo "=========================================="
echo "  LocalStack AWS Simulator Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "  Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check docker-compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose is available${NC}"

# Setup AWS credentials
echo ""
echo "Setting up AWS credentials for LocalStack..."

mkdir -p ~/.aws

# Backup existing credentials if they exist and don't have LocalStack config
if [ -f ~/.aws/credentials ] && ! grep -q "test" ~/.aws/credentials; then
    echo -e "${YELLOW}! Backing up existing ~/.aws/credentials to ~/.aws/credentials.backup${NC}"
    cp ~/.aws/credentials ~/.aws/credentials.backup
fi

# Check if default profile exists with test credentials
if grep -q "\[default\]" ~/.aws/credentials 2>/dev/null; then
    echo -e "${YELLOW}! Default profile exists in ~/.aws/credentials${NC}"
    echo "  Make sure it has: aws_access_key_id = test"
    echo "                    aws_secret_access_key = test"
else
    cat >> ~/.aws/credentials << 'EOF'

[default]
aws_access_key_id = test
aws_secret_access_key = test
EOF
    echo -e "${GREEN}✓ Added default profile to ~/.aws/credentials${NC}"
fi

# Setup AWS config
if [ ! -f ~/.aws/config ] || ! grep -q "\[default\]" ~/.aws/config; then
    cat >> ~/.aws/config << 'EOF'

[default]
region = us-east-1
output = json
EOF
    echo -e "${GREEN}✓ Added default region to ~/.aws/config${NC}"
else
    echo -e "${GREEN}✓ AWS config already exists${NC}"
fi

# Start LocalStack
echo ""
echo "Starting LocalStack..."
docker-compose up -d

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then
        echo -e "${GREEN}✓ LocalStack is ready!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Waiting... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ LocalStack failed to start${NC}"
    echo "  Check logs with: docker-compose logs"
    exit 1
fi

# Install Python dependencies if pip is available
echo ""
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install boto3 --quiet 2>/dev/null || pip3 install boto3 --quiet 2>/dev/null || true
    echo -e "${GREEN}✓ boto3 installed${NC}"
fi

# Show health status
echo ""
echo "=========================================="
echo "  LocalStack Status"
echo "=========================================="
curl -s http://localhost:4566/_localstack/health | python3 -m json.tool 2>/dev/null || \
curl -s http://localhost:4566/_localstack/health

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "LocalStack is running at: http://localhost:4566"
echo ""
echo "Quick test commands:"
echo "  python test_localstack.py        # Run full test suite"
echo "  awslocal s3 ls                   # List S3 buckets (requires awscli-local)"
echo ""
echo "To stop LocalStack:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
