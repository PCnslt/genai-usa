#!/usr/bin/env bash
set -euo pipefail
# Attach the rewrite-index CloudFront Function to the marketing distribution
# so /app/ (and other directory URLs) serve index.html.
R=us-east-1
DIST=E1X5KOL649UAAN

FN_ARN=$(aws cloudfront list-functions --region "$R" \
  --query "FunctionList.Items[?Name=='genai-rewrite-index'].FunctionMetadata.FunctionARN" --output text 2>/dev/null || true)
if [ -z "$FN_ARN" ] || [ "$FN_ARN" = "None" ]; then
  aws cloudfront create-function --name genai-rewrite-index --region "$R" \
    --function-config 'Comment=Rewrite directory URLs to index.html,Runtime=cloudfront-js-2.0' \
    --function-code fileb://"$(dirname "$0")/rewrite-index.js" >/dev/null
  FN_ARN=$(aws cloudfront list-functions --region "$R" \
    --query "FunctionList.Items[?Name=='genai-rewrite-index'].FunctionMetadata.FunctionARN" --output text)
fi
echo "function arn: $FN_ARN"

aws cloudfront get-distribution-config --id "$DIST" --region "$R" --output json > /tmp/cf-config.json
python3 - "$FN_ARN" <<'PY'
import json, sys
fn = sys.argv[1]
d = json.load(open('/tmp/cf-config.json'))
dc = d['DistributionConfig']
dc['DefaultCacheBehavior']['FunctionAssociations'] = {
    "Quantity": 1,
    "Items": [{"EventType": "viewer-request", "FunctionARN": fn}],
}
json.dump(d, open('/tmp/cf-config.json', 'w'))
PY
ETAG=$(python3 -c "import json; print(json.load(open('/tmp/cf-config.json'))['ETag'])")
python3 - <<'PY'
import json
d = json.load(open('/tmp/cf-config.json'))
json.dump(d['DistributionConfig'], open('/tmp/cf-dc.json', 'w'))
PY
aws cloudfront update-distribution --id "$DIST" --distribution-config fileb:///tmp/cf-dc.json \
  --if-match "$ETAG" --region "$R" >/dev/null
echo "distribution updated"
