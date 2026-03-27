#!/bin/bash

##############################################################################
# Build AWS Lambda Layer
#
# Creates a ZIP file containing:
# 1. Third-party packages from requirements.txt
# 2. Custom shared modules (shared_lib/)
#
# Usage:
#   chmod +x build_layer.sh
#   ./build_layer.sh
#
# Output:
#   my-layer.zip - Ready to upload to AWS Lambda
#
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
PYTHON_DIR="${BUILD_DIR}/python"
LAYER_ZIP="${SCRIPT_DIR}/my-layer.zip"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"

echo -e "${YELLOW}=== AWS Lambda Layer Builder ===${NC}\n"

# Step 1: Clean previous builds
echo -e "${YELLOW}[1/4] Cleaning previous builds...${NC}"
if [ -d "${BUILD_DIR}" ]; then
    rm -rf "${BUILD_DIR}"
    echo "Removed ${BUILD_DIR}"
fi
mkdir -p "${PYTHON_DIR}"
echo "Created ${PYTHON_DIR}"

# Step 2: Install pip packages
echo -e "\n${YELLOW}[2/4] Installing pip packages (manylinux2014_x86_64)...${NC}"

if [ ! -f "${REQUIREMENTS}" ]; then
    echo -e "${RED}ERROR: ${REQUIREMENTS} not found${NC}"
    exit 1
fi

echo "Installing from: ${REQUIREMENTS}"
pip install \
  --platform manylinux2014_x86_64 \
  --target "${PYTHON_DIR}" \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --upgrade \
  -r "${REQUIREMENTS}"

echo -e "${GREEN}✓ Packages installed${NC}"

# Step 3: Copy custom modules
echo -e "\n${YELLOW}[3/4] Copying custom modules...${NC}"

if [ -d "${SCRIPT_DIR}/shared_lib" ]; then
    cp -r "${SCRIPT_DIR}/shared_lib" "${PYTHON_DIR}/"
    echo -e "${GREEN}✓ Copied shared_lib/${NC}"
else
    echo -e "${RED}WARNING: shared_lib/ not found${NC}"
fi

# Step 4: Create ZIP archive
echo -e "\n${YELLOW}[4/4] Creating ZIP archive...${NC}"

if [ -f "${LAYER_ZIP}" ]; then
    rm "${LAYER_ZIP}"
fi

cd "${BUILD_DIR}"
zip -r "../my-layer.zip" python/ -q
cd - > /dev/null

# Print summary
echo -e "\n${GREEN}=== Build Complete ===${NC}\n"
echo -e "Layer ZIP: ${YELLOW}${LAYER_ZIP}${NC}"
echo -e "Size: $(du -sh "${LAYER_ZIP}" | cut -f1)"
echo ""
echo "Contents:"
unzip -l "${LAYER_ZIP}" | head -20
echo "  ... (and more)"
echo ""

# Next steps
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Upload to AWS Lambda:"
echo "   aws lambda publish-layer-version \\"
echo "     --layer-name my-shared-lib \\"
echo "     --zip-file fileb://my-layer.zip \\"
echo "     --compatible-runtimes python3.11 python3.12"
echo ""
echo "2. Copy the returned LayerVersionArn and attach to your function"
echo ""
