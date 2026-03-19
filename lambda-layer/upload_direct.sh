#!/bin/bash
# ============================================================
# DIRECT UPLOAD — use when ZIP is under 50 MB
# ============================================================
set -e

LAYER_NAME="my-lambda-layer"
ZIP_FILE="my-layer-small.zip"
PYTHON_VERSIONS="python3.11 python3.12"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "📦 ZIP size: $(du -sh $ZIP_FILE | cut -f1)"
echo "🚀 Uploading layer directly to Lambda..."

RESULT=$(aws lambda publish-layer-version \
  --layer-name "$LAYER_NAME" \
  --description "App dependencies + custom modules" \
  --zip-file "fileb://$ZIP_FILE" \
  --compatible-runtimes $PYTHON_VERSIONS \
  --region "$AWS_REGION" \
  --output json)

LAYER_ARN=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['LayerVersionArn'])")

echo ""
echo "✅ Layer published!"
echo "   ARN: $LAYER_ARN"
echo ""
echo "👉 Attach to your Lambda function:"
echo "   aws lambda update-function-configuration \\"
echo "     --function-name YOUR_FUNCTION_NAME \\"
echo "     --layers $LAYER_ARN"
