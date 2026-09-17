#!/usr/bin/env bash
set -euo pipefail
# Deploy the backend Lambda (create/update). Run infra/00 + infra/01 first.
cd "$(dirname "$0")"

R="${AWS_REGION:-us-east-2}"
FN="genai-api"

ROLE=$(aws iam get-role --role-name genai-lambda-role --query 'Role.Arn' --output text --region "$R" 2>/dev/null || true)
if [ -z "$ROLE" ]; then
  echo "creating genai-lambda-role ..."
  aws iam create-role --role-name genai-lambda-role --region "$R" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name genai-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  aws iam put-role-policy --role-name genai-lambda-role --policy-name genai-access \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["dynamodb:*","bedrock:InvokeModel","bedrock:Retrieve"],"Resource":"*"}]}'
  sleep 10
  ROLE=$(aws iam get-role --role-name genai-lambda-role --query 'Role.Arn' --output text --region "$R")
fi
echo "role: $ROLE"

rm -rf build genai-api.zip
mkdir -p build
pip install -r requirements.txt -t build --quiet 2>/dev/null || pip install -r requirements.txt -t build
cp -r src/* build/
(cd build && zip -qr ../genai-api.zip .)

if aws lambda get-function --function-name "$FN" --region "$R" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$FN" --zip-file fileb://genai-api.zip --region "$R"
else
  aws lambda create-function --function-name "$FN" --runtime python3.11 --role "$ROLE" \
    --handler handlers.lambda_handler --zip-file fileb://genai-api.zip \
    --timeout 30 --memory-size 256 --region "$R"
fi
echo "deployed: $FN"
