#!/usr/bin/env bash
set -euo pipefail
# Create platform DynamoDB tables (idempotent). Billing = PAY_PER_REQUEST (free-tier friendly).
R="${AWS_REGION:-us-east-2}"

mk() {
  local name="$1"; shift
  if aws dynamodb describe-table --table-name "$name" --region "$R" >/dev/null 2>&1; then
    echo "exists: $name"; return
  fi
  aws dynamodb create-table --table-name "$name" --region "$R" --billing-mode PAY_PER_REQUEST "$@" >/dev/null
  echo "created: $name"
}

# catalog
mk genai-products \
  --attribute-definitions AttributeName=product_id,AttributeType=S \
  --key-schema AttributeName=product_id,KeyType=HASH

# orders (GSI by customer)
mk genai-orders \
  --attribute-definitions AttributeName=order_id,AttributeType=S AttributeName=customer_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --global-secondary-indexes 'IndexName=customer-index,KeySchema=[{AttributeName=customer_id,KeyType=HASH}],Projection={ProjectionType=ALL}'

# entitlements: customer_id (HASH) + product_id (RANGE)
mk genai-entitlements \
  --attribute-definitions AttributeName=customer_id,AttributeType=S AttributeName=product_id,AttributeType=S \
  --key-schema AttributeName=customer_id,KeyType=HASH AttributeName=product_id,KeyType=RANGE

# contracts (GSI by customer)
mk genai-contracts \
  --attribute-definitions AttributeName=contract_id,AttributeType=S AttributeName=customer_id,AttributeType=S \
  --key-schema AttributeName=contract_id,KeyType=HASH \
  --global-secondary-indexes 'IndexName=customer-index,KeySchema=[{AttributeName=customer_id,KeyType=HASH}],Projection={ProjectionType=ALL}'

# billing (GSI by customer)
mk genai-billing \
  --attribute-definitions AttributeName=payment_id,AttributeType=S AttributeName=customer_id,AttributeType=S \
  --key-schema AttributeName=payment_id,KeyType=HASH \
  --global-secondary-indexes 'IndexName=customer-index,KeySchema=[{AttributeName=customer_id,KeyType=HASH}],Projection={ProjectionType=ALL}'

# chat: session_id (HASH) + ts (RANGE)
mk genai-chat \
  --attribute-definitions AttributeName=session_id,AttributeType=S AttributeName=ts,AttributeType=N \
  --key-schema AttributeName=session_id,KeyType=HASH AttributeName=ts,KeyType=RANGE

echo "done"
