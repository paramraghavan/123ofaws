#!/bin/bash
# ============================================================
# S3 UPLOAD — use when ZIP is over 50 MB
# ============================================================
set -e

LAYER_NAME="my-lambda-layer"
ZIP_FILE="my-layer-large.zip"          # your large zip here
S3_BUCKET="your-deployment-bucket"     # ← change this
S3_KEY="lambda-layers/${LAYER_NAME}.zip"
PYTHON_VERSIONS="python3.11 python3.12"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "📦 ZIP size: $(du -sh $ZIP_FILE | cut -f1)"

# Step 1 — Upload ZIP to S3
echo "☁️  Uploading ZIP to s3://$S3_BUCKET/$S3_KEY ..."
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY" \
  --region "$AWS_REGION"

echo "✅ Uploaded to S3"

# Step 2 — Publish layer referencing S3
echo "🚀 Publishing Lambda layer from S3..."

RESULT=$(aws lambda publish-layer-version \
  --layer-name "$LAYER_NAME" \
  --description "App dependencies + custom modules (large)" \
  --content "S3Bucket=$S3_BUCKET,S3Key=$S3_KEY" \
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
