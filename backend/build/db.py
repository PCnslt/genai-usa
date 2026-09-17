"""DynamoDB access layer + table schema. Free-tier friendly (single tables)."""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Optional

import boto3

_TABLES = {
    "products": os.environ.get("TABLE_PRODUCTS", "genai-products"),
    "orders": os.environ.get("TABLE_ORDERS", "genai-orders"),
    "entitlements": os.environ.get("TABLE_ENTITLEMENTS", "genai-entitlements"),
    "contracts": os.environ.get("TABLE_CONTRACTS", "genai-contracts"),
    "billing": os.environ.get("TABLE_BILLING", "genai-billing"),
    "chat": os.environ.get("TABLE_CHAT", "genai-chat"),
}

_ddb = boto3.resource("dynamodb")


def table(name: str):
    return _ddb.Table(_TABLES[name])


def now() -> int:
    return int(time.time())


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ---- products ----
def put_product(product_id: str, name: str, price_cents: int, kind: str, **extra) -> None:
    table("products").put_item(Item={
        "product_id": product_id, "name": name, "price_cents": price_cents,
        "kind": kind, "updated_at": now(), **extra,
    })


def get_product(product_id: str) -> Optional[dict]:
    return table("products").get_item(Key={"product_id": product_id}).get("Item")


# ---- orders ----
def put_order(order: dict) -> None:
    table("orders").put_item(Item=order)


def get_order(order_id: str) -> Optional[dict]:
    return table("orders").get_item(Key={"order_id": order_id}).get("Item")


def update_order_status(order_id: str, status: str) -> None:
    table("orders").update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET #s = :s, updated_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":t": now()},
    )


# ---- entitlements ----
def grant(customer_id: str, product_id: str, source_order_id: str, meta: Optional[dict] = None) -> None:
    table("entitlements").put_item(Item={
        "customer_id": customer_id,
        "product_id": product_id,
        "source_order_id": source_order_id,
        "granted_at": now(),
        **(meta or {}),
    })


def list_entitlements(customer_id: str) -> list[dict]:
    r = table("entitlements").query(
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return r.get("Items", [])


def list_orders(customer_id: str) -> list[dict]:
    r = table("orders").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return r.get("Items", [])


# ---- contracts ----
def record_contract(customer_id: str, contract_type: str, version: str,
                    ip: str, user_agent: str) -> str:
    cid = new_id("ctr")
    table("contracts").put_item(Item={
        "contract_id": cid, "customer_id": customer_id, "contract_type": contract_type,
        "version": version, "accepted_at": now(), "ip": ip, "user_agent": user_agent,
    })
    return cid


def list_contracts(customer_id: str) -> list[dict]:
    r = table("contracts").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return r.get("Items", [])


# ---- billing (idempotent by event id) ----
def record_charge(event_id: str, order_id: str, customer_id: str,
                  amount_cents: int, provider: str) -> bool:
    """Return True if recorded now, False if already seen (idempotent)."""
    try:
        table("billing").put_item(
            Item={
                "payment_id": event_id,
                "customer_id": customer_id,
                "order_id": order_id,
                "amount_cents": amount_cents,
                "provider": provider,
                "created_at": now(),
            },
            ConditionExpression="attribute_not_exists(payment_id)",
        )
        return True
    except _ddb.meta.client.exceptions.ConditionalCheckFailedException:
        return False
