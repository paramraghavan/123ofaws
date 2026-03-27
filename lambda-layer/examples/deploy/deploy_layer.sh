#!/bin/bash

##############################################################################
# Deploy Lambda Layer to AWS
#
# Publishes the layer ZIP to AWS Lambda.
#
# Prerequisites:
#   - AWS CLI configured (aws configure)
#   - my-layer.zip exists (created by build_layer.sh)
#
# Usage:
#   chmod +x deploy_layer.sh
#   ./deploy_layer.sh
#
# Output:
#   Layer ARN suitable for attaching to Lambda functions
#
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAYER_ZIP="${SCRIPT_DIR}/my-layer.zip"
LAYER_NAME="my-shared-lib"
RUNTIMES="python3.11 python3.12"
REGION="${AWS_REGION:-us-east-1}"

echo -e "${BLUE}=== AWS Lambda Layer Deployer ===${NC}\n"

# Validate prerequisites
echo -e "${YELLOW}[1/3] Validating prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found${NC}"
    echo "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if [ ! -f "${LAYER_ZIP}" ]; then
    echo -e "${RED}ERROR: ${LAYER_ZIP} not found${NC}"
    echo "Run: ./build_layer.sh"
    exit 1
fi

# Test AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS CLI configured (Account: ${ACCOUNT_ID})${NC}"

# Get current account and region
echo -e "\n${YELLOW}[2/3] Publishing layer...${NC}"
echo "Layer Name: ${LAYER_NAME}"
echo "ZIP File: ${LAYER_ZIP}"
echo "File Size: $(du -sh "${LAYER_ZIP}" | cut -f1)"
echo "Runtimes: ${RUNTIMES}"
echo "Region: ${REGION}"
echo ""

# Publish the layer
echo "Publishing to AWS Lambda..."
LAYER_RESPONSE=$(aws lambda publish-layer-version \
  --layer-name "${LAYER_NAME}" \
  --zip-file "fileb://${LAYER_ZIP}" \
  --compatible-runtimes ${RUNTIMES} \
  --region "${REGION}" \
  --output json)

# Extract ARN and version
LAYER_ARN=$(echo "${LAYER_RESPONSE}" | jq -r '.LayerVersionArn')
LAYER_VERSION=$(echo "${LAYER_RESPONSE}" | jq -r '.Version')

if [ -z "${LAYER_ARN}" ] || [ "${LAYER_ARN}" == "null" ]; then
    echo -e "${RED}ERROR: Failed to publish layer${NC}"
    echo "Response: ${LAYER_RESPONSE}"
    exit 1
fi

echo -e "\n${YELLOW}[3/3] Deployment Summary${NC}"
echo -e "${GREEN}✓ Layer published successfully${NC}\n"

echo -e "Layer ARN: ${BLUE}${LAYER_ARN}${NC}"
echo -e "Version: ${LAYER_VERSION}"
echo "Region: ${REGION}"
echo ""

# Save ARN to file for easy reference
ARN_FILE="${SCRIPT_DIR}/.layer-arn"
echo "${LAYER_ARN}" > "${ARN_FILE}"
echo -e "ARN saved to: ${YELLOW}${ARN_FILE}${NC}\n"

# Next steps
echo -e "${YELLOW}Next: Attach to a Lambda function${NC}\n"
echo "Option 1 - Update existing function:"
echo "  aws lambda update-function-configuration \\"
echo "    --function-name YOUR_FUNCTION_NAME \\"
echo "    --layers \"${LAYER_ARN}\" \\"
echo "    --region ${REGION}"
echo ""

echo "Option 2 - Create function with layer:"
echo "  aws lambda create-function \\"
echo "    --function-name my-processor \\"
echo "    --runtime python3.12 \\"
echo "    --role arn:aws:iam::${ACCOUNT_ID}:role/lambda-role \\"
echo "    --handler lambda_function.handler \\"
echo "    --zip-file fileb://lambda-function.zip \\"
echo "    --layers \"${LAYER_ARN}\" \\"
echo "    --region ${REGION}"
echo ""

echo "Option 3 - Update via AWS Console:"
echo "  Lambda → Your Function → Layers → Add Layer → Specify ARN"
echo "  Paste: ${LAYER_ARN}"
echo ""
