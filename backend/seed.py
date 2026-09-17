#!/usr/bin/env python3
"""Seed the `genai-products` table from backend/src/products.py (idempotent)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import boto3
from products import CATALOG

REGION = os.environ.get("AWS_REGION", "us-east-2")
TABLE = os.environ.get("TABLE_PRODUCTS", "genai-products")

ddb = boto3.resource("dynamodb", region_name=REGION)
t = ddb.Table(TABLE)

count = 0
for p in CATALOG:
    item = {
        "product_id": p["product_id"],
        "name": p["name"],
        "price_cents": p["price_cents"],
        "kind": p["kind"],
        "description": p.get("description", ""),
        "recurring": bool(p.get("recurring")),
        "monthly_cents": int(p.get("monthly_cents", 0)),
    }
    t.put_item(Item=item)
    count += 1

print(f"seeded {count} products into {TABLE} ({REGION})")
