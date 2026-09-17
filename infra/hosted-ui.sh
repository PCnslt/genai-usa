#!/usr/bin/env bash
set -euo pipefail
# Brand the Cognito hosted UI (logo + CSS) to match the site theme.
# Not in the CFN template because AWS::Cognito::UserPoolUICustomizationAttachment
# only supports CSS (no logo image); this single idempotent call sets both and is
# committed + reproducible. Run from the repo root.
cd "$(dirname "$0")/.."
R="${AWS_REGION:-us-east-2}"
STACK="${STACK_NAME:-genai-platform}"

POOL=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$R" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)

aws cognito-idp set-ui-customization \
  --user-pool-id "$POOL" \
  --css "$(cat infra/hosted-ui.css)" \
  --image-file "fileb://assets/img/logo.png" \
  --region "$R"

echo "hosted UI branded (pool $POOL)"
