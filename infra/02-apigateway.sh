#!/usr/bin/env bash
set -euo pipefail
R="${AWS_REGION:-us-east-2}"
POOL="us-east-2_67kyg4ptP"
CLIENT="1it7qevrl4ebdev0pvbjtbm8ma"
ACCT=$(aws sts get-caller-identity --query Account --output text)

# create / find API
API_ID=$(aws apigatewayv2 get-apis --region "$R" --query "Items[?Name=='genai-api'].ApiId" --output text 2>/dev/null || true)
if [ -z "$API_ID" ] || [ "$API_ID" = "None" ]; then
  API_ID=$(aws apigatewayv2 create-api --name genai-api --protocol-type HTTP --region "$R" --query 'ApiId' --output text)
fi
echo "API_ID=$API_ID"

# JWT authorizer (Cognito)
AUTH_ID=$(aws apigatewayv2 get-authorizers --api-id "$API_ID" --region "$R" \
  --query "Items[?Name=='cognito'].AuthorizerId" --output text 2>/dev/null || true)
if [ -z "$AUTH_ID" ] || [ "$AUTH_ID" = "None" ]; then
  AUTH_ID=$(aws apigatewayv2 create-authorizer --api-id "$API_ID" --name cognito --authorizer-type JWT \
    --identity-source '$request.header.Authorization' \
    --jwt-configuration "Issuer=https://cognito-idp.$R.amazonaws.com/$POOL,Audience=$CLIENT" \
    --region "$R" --query 'AuthorizerId' --output text)
fi
echo "AUTH_ID=$AUTH_ID"

# Lambda integration
LAMBDA_ARN=$(aws lambda get-function --function-name genai-api --region "$R" --query 'Configuration.FunctionArn' --output text)
INT_ID=$(aws apigatewayv2 create-integration --api-id "$API_ID" --integration-type AWS_PROXY \
  --integration-method POST --payload-format-version 2.0 --integration-uri "$LAMBDA_ARN" \
  --region "$R" --query 'IntegrationId' --output text)
echo "INT_ID=$INT_ID"

# routes: catch-all (authenticated) + webhook (public)
aws apigatewayv2 create-route --api-id "$API_ID" --route-key 'ANY /{proxy+}' \
  --target "integrations/$INT_ID" --authorizer-id "$AUTH_ID" --authorization-type JWT --region "$R" >/dev/null 2>&1 || true
aws apigatewayv2 create-route --api-id "$API_ID" --route-key 'POST /webhooks/payments' \
  --target "integrations/$INT_ID" --authorization-type NONE --region "$R" >/dev/null 2>&1 || true

# stage (auto-deploy)
aws apigatewayv2 create-stage --api-id "$API_ID" --stage-name '$default' --auto-deploy --region "$R" >/dev/null 2>&1 || true

# allow API Gateway to invoke the Lambda
aws lambda add-permission --function-name genai-api --statement-id apigateway-invoke \
  --action lambda:InvokeFunction --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$R:$ACCT:$API_ID/*/*" --region "$R" 2>/dev/null || echo "lambda permission exists"

# CORS
aws apigatewayv2 update-api --api-id "$API_ID" --region "$R" \
  --cors-configuration '{"AllowOrigins":["*"],"AllowMethods":["*"],"AllowHeaders":["*"]}' >/dev/null

echo "API_URL=https://$API_ID.execute-api.$R.amazonaws.com"
