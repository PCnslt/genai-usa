#!/usr/bin/env bash
set -euo pipefail
# Package + deploy the whole platform via CloudFormation (single source of truth).
cd "$(dirname "$0")/.."   # repo root
R="${AWS_REGION:-us-east-2}"
STACK="${STACK_NAME:-genai-platform}"
BUCKET="${CODE_BUCKET:-genai-usa.com}"

# 1) zip the Lambda code
rm -rf backend/build backend/genai-api.zip
mkdir -p backend/build
cp -r backend/src/* backend/build/
(cd backend/build && zip -qr ../genai-api.zip .)

# 2) package (uploads Lambda zip to S3, rewrites local path)
aws cloudformation package \
  --template-file infra/stack.yaml \
  --s3-bucket "$BUCKET" \
  --s3-prefix lambda \
  --output-template-file /tmp/genai-packaged.yaml

# 3) deploy (idempotent create/update, rolls back on failure)
aws cloudformation deploy \
  --template-file /tmp/genai-packaged.yaml \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region "$R"

echo "=== stack outputs ==="
aws cloudformation describe-stacks --stack-name "$STACK" --region "$R" \
  --query 'Stacks[0].Outputs' --output table

# 4) seed the product catalog (idempotent put_item)
echo "=== seeding catalog ==="
AWS_REGION="$R" python3 backend/seed.py

# 5) brand the Cognito hosted UI (logo + CSS)
echo "=== branding hosted UI ==="
AWS_REGION="$R" bash infra/hosted-ui.sh
