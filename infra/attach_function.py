import sys

import boto3

cf = boto3.client("cloudfront", region_name="us-east-1")
fn_arn = sys.argv[1]
dist = "E1X5KOL649UAAN"

cfg = cf.get_distribution_config(Id=dist)
dc = cfg["DistributionConfig"]
dc["DefaultCacheBehavior"]["FunctionAssociations"] = {
    "Quantity": 1,
    "Items": [{"EventType": "viewer-request", "FunctionARN": fn_arn}],
}
cf.update_distribution(Id=dist, DistributionConfig=dc, IfMatch=cfg["ETag"])
print("distribution updated")
