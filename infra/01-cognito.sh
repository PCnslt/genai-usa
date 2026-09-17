#!/usr/bin/env bash
set -euo pipefail
# Create the Cognito user pool + app client (hosted UI) + 3 role groups.
R="${AWS_REGION:-us-east-2}"
NAME="genai-users"
CB1="https://d2smtb2zyqn37z.cloudfront.net/app/"
CB2="https://genai-usa.com/app/"
CB3="https://localhost/app/"

POOL_ID=$(aws cognito-idp list-user-pools --max-results 60 --region "$R" \
  --query "UserPools[?Name=='$NAME'].Id" --output text 2>/dev/null || true)
if [ -z "$POOL_ID" ] || [ "$POOL_ID" = "None" ]; then
  POOL_ID=$(aws cognito-idp create-user-pool --pool-name "$NAME" --region "$R" \
    --auto-verified-attributes email \
    --username-attributes email \
    --query 'UserPool.Id' --output text)
  echo "created pool: $POOL_ID"
else
  echo "pool exists: $POOL_ID"
fi

CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id "$POOL_ID" --region "$R" \
  --query "UserPoolClients[?ClientName=='genai-portal'].ClientId" --output text 2>/dev/null || true)
if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" = "None" ]; then
  CLIENT_ID=$(aws cognito-idp create-user-pool-client --user-pool-id "$POOL_ID" --client-name genai-portal --region "$R" \
    --supported-identity-providers COGNITO \
    --callback-urls "[\"$CB1\",\"$CB2\",\"$CB3\"]" \
    --logout-urls "[\"$CB1\",\"$CB2\"]" \
    --allowed-o-auth-flows implicit \
    --allowed-o-auth-scopes openid email profile \
    --allowed-o-auth-flows-user-pool-client \
    --query 'UserPoolClient.ClientId' --output text)
fi

aws cognito-idp create-user-pool-domain --domain "genai-usa-portal" --user-pool-id "$POOL_ID" --region "$R" 2>/dev/null \
  && echo "domain created" || echo "domain exists or not ready"

for g in customers employees admins; do
  aws cognito-idp create-group --group-name "$g" --user-pool-id "$POOL_ID" --region "$R" 2>/dev/null \
    && echo "group $g created" || echo "group $g exists"
done

echo "POOL_ID=$POOL_ID"
echo "CLIENT_ID=$CLIENT_ID"
echo "DOMAIN=https://genai-usa-portal.auth.$R.amazoncognito.com"
