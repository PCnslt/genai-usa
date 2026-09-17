"""DynamoDB access layer + table schema. Free-tier friendly (PAY_PER_REQUEST)."""
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
    "support": os.environ.get("TABLE_SUPPORT", "genai-conversations"),
    "meta": os.environ.get("TABLE_META", "genai-meta"),
    "leads": os.environ.get("TABLE_LEADS", "genai-leads"),
    "roster": os.environ.get("TABLE_ROSTER", "genai-roster"),
}

_ddb = boto3.resource("dynamodb")


def table(name: str):
    return _ddb.Table(_TABLES[name])


def now() -> int:
    return int(time.time())


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ---- products (catalog) ----
def list_products() -> list[dict]:
    items = table("products").scan().get("Items", [])
    items.sort(key=lambda p: p.get("product_id", ""))
    return items


def put_product(product_id: str, name: str, price_cents: int, kind: str,
                description: str = "", recurring: bool = False,
                monthly_cents: int = 0) -> None:
    item = {
        "product_id": product_id, "name": name, "price_cents": int(price_cents),
        "kind": kind, "description": description, "recurring": bool(recurring),
        "monthly_cents": int(monthly_cents or 0), "updated_at": now(),
    }
    table("products").put_item(Item=item)


def delete_product(product_id: str) -> None:
    table("products").delete_item(Key={"product_id": product_id})


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


def set_fulfillment(order_id: str, status: str) -> None:
    """Employee action: move delivery status (pending -> in_progress -> delivered)."""
    table("orders").update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET fulfillment_status = :s, updated_at = :t",
        ExpressionAttributeValues={":s": status, ":t": now()},
    )


def list_orders(customer_id: str) -> list[dict]:
    r = table("orders").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return r.get("Items", [])


def list_all_orders() -> list[dict]:
    items = table("orders").scan().get("Items", [])
    items.sort(key=lambda o: o.get("created_at", 0), reverse=True)
    return items


# ---- entitlements ----
def grant(customer_id: str, product_id: str, source_order_id: str,
          meta: Optional[dict] = None) -> None:
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


# ---- contracts (clickwrap) ----
def record_contract(customer_id: str, contract_type: str, version: str,
                    ip: str, user_agent: str) -> str:
    cid = new_id("ctr")
    table("contracts").put_item(Item={
        "contract_id": cid, "customer_id": customer_id,
        "contract_type": contract_type, "version": version,
        "accepted_at": now(), "ip": ip, "user_agent": user_agent,
    })
    return cid


def has_accepted(customer_id: str, version: str) -> bool:
    r = table("contracts").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return any(c.get("version") == version for c in r.get("Items", []))


def list_contracts(customer_id: str) -> list[dict]:
    r = table("contracts").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return r.get("Items", [])


def list_all_contracts() -> list[dict]:
    items = table("contracts").scan().get("Items", [])
    items.sort(key=lambda c: c.get("accepted_at", 0), reverse=True)
    return items


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


def list_billing(customer_id: str) -> list[dict]:
    r = table("billing").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    return r.get("Items", [])


def finance_summary() -> dict:
    items = table("billing").scan().get("Items", [])
    total = sum(int(i.get("amount_cents", 0)) for i in items)
    by_provider: dict[str, int] = {}
    for i in items:
        p = i.get("provider", "unknown")
        by_provider[p] = by_provider.get(p, 0) + int(i.get("amount_cents", 0))
    return {
        "total_charges": len(items),
        "total_revenue_cents": total,
        "by_provider_cents": by_provider,
    }


# ---- conversations (anonymized customer <-> contractor relay) ----
# One item per thread; `messages` is an append-only list. Identity is stripped
# at the API boundary so the contractor never sees the customer's real id and
# the customer never sees the contractor's real id.
def start_or_append_support(customer_id: str, subject: str, body: str,
                            customer_alias: str) -> str:
    ts = now()
    r = table("support").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        FilterExpression="#s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":c": customer_id, ":s": "open"},
    )
    items = r.get("Items", [])
    msg = {"sender": "customer", "body": body, "ts": ts}
    if items:  # append to the open thread
        cid = items[0]["conversation_id"]
        table("support").update_item(
            Key={"conversation_id": cid},
            UpdateExpression="SET messages = list_append(if_not_exists(messages, :e), :m), updated_at = :t",
            ExpressionAttributeValues={":m": [msg], ":e": [], ":t": ts},
        )
        return cid
    cid = new_id("con")
    table("support").put_item(Item={
        "conversation_id": cid,
        "customer_id": customer_id,
        "customer_alias": customer_alias,
        "subject": subject,
        "status": "open",
        "messages": [msg],
        "manager_id": "",
        "manager_name": "",
        "created_at": ts,
        "updated_at": ts,
    })
    return cid


def list_support_customer(customer_id: str) -> list[dict]:
    r = table("support").query(
        IndexName="customer-index",
        KeyConditionExpression="customer_id = :c",
        ExpressionAttributeValues={":c": customer_id},
    )
    items = r.get("Items", [])
    items.sort(key=lambda c: c.get("updated_at", 0), reverse=True)
    return items


def list_open_support() -> list[dict]:
    r = table("support").query(
        IndexName="status-index",
        KeyConditionExpression="#s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "open"},
    )
    items = r.get("Items", [])
    items.sort(key=lambda c: c.get("updated_at", 0))
    return items


def append_manager_reply(conversation_id: str, reply: str,
                         manager_id: str, manager_name: str) -> None:
    ts = now()
    msg = {"sender": "manager", "body": reply, "ts": ts}
    table("support").update_item(
        Key={"conversation_id": conversation_id},
        UpdateExpression=("SET messages = list_append(if_not_exists(messages, :e), :m), "
                          "manager_id = :mid, manager_name = :mn, updated_at = :t"),
        ExpressionAttributeValues={
            ":m": [msg], ":e": [], ":mid": manager_id,
            ":mn": manager_name, ":t": ts,
        },
    )


def resolve_support(conversation_id: str) -> None:
    table("support").update_item(
        Key={"conversation_id": conversation_id},
        UpdateExpression="SET #s = :s, resolved_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "resolved", ":t": now()},
    )


# ---- meta (runtime config, e.g. contract template override) ----
def get_meta(key: str) -> Optional[str]:
    return table("meta").get_item(Key={"key": key}).get("Item", {}).get("value")


def set_meta(key: str, value: str) -> None:
    table("meta").put_item(Item={"key": key, "value": value, "updated_at": now()})


# ---- leads (internal CRM — we dogfood our own lead-gen/CRM product) ----
def put_lead(name: str, email: str, company: str, interest: str,
             message: str, source: str) -> str:
    lead_id = new_id("lead")
    table("leads").put_item(Item={
        "lead_id": lead_id, "name": name, "email": email, "company": company,
        "interest": interest, "message": message, "source": source,
        "status": "new", "created_at": now(), "updated_at": now(),
    })
    return lead_id


def list_leads() -> list[dict]:
    items = table("leads").scan().get("Items", [])
    items.sort(key=lambda l: l.get("created_at", 0), reverse=True)
    return items


def set_lead_status(lead_id: str, status: str) -> None:
    table("leads").update_item(
        Key={"lead_id": lead_id},
        UpdateExpression="SET #s = :s, updated_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":t": now()},
    )


# ---- contractor roster (admin: track interviewing -> hired -> assigned) ----
def put_contractor(name: str, role: str, platform: str, price: str,
                   notes: str) -> str:
    cid = new_id("contractor")
    table("roster").put_item(Item={
        "contractor_id": cid, "name": name, "role": role, "platform": platform,
        "price": price, "notes": notes, "status": "interviewing",
        "created_at": now(), "updated_at": now(),
    })
    return cid


def list_contractors() -> list[dict]:
    items = table("roster").scan().get("Items", [])
    items.sort(key=lambda c: c.get("created_at", 0))
    return items


def set_contractor_status(contractor_id: str, status: str) -> None:
    table("roster").update_item(
        Key={"contractor_id": contractor_id},
        UpdateExpression="SET #s = :s, updated_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":t": now()},
    )


def delete_contractor(contractor_id: str) -> None:
    table("roster").delete_item(Key={"contractor_id": contractor_id})


# ---- chat history (optional persistence) ----
def save_chat(session_id: str, role: str, text: str) -> None:
    table("chat").put_item(Item={
        "session_id": session_id, "ts": now(), "role": role, "text": text,
    })


def get_chat(session_id: str, limit: int = 12) -> list[dict]:
    """Most recent `limit` turns for a session, oldest first."""
    r = table("chat").query(
        KeyConditionExpression="session_id = :s",
        ExpressionAttributeValues={":s": session_id},
        ScanIndexForward=False,
        Limit=limit,
    )
    items = r.get("Items", [])
    items.reverse()
    return items
