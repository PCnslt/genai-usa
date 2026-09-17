"""Single Lambda API router (HTTP API v2 payload).

Routes (map these in API Gateway):
  GET  /entitlements       -> what the customer owns
  GET  /orders             -> customer's orders
  POST /orders             -> create an order + payment checkout (idempotent)
  POST /webhooks/payments  -> provider webhook (idempotent grant)
  POST /contracts/accept   -> clickwrap acceptance (stored, timestamped)
  GET  /contracts          -> customer's signed contracts
  GET  /billing            -> billing portal URL (self-serve)
  POST /chat               -> RAG support bot
"""
from __future__ import annotations

import json
import os

import auth
import db
from payments import get_provider, Order


def _ok(body, status=200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(body),
    }


def _err(msg, status=400):
    return _ok({"error": str(msg)}, status)


def _body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except Exception:
        return {}


def _ip(event):
    return event.get("requestContext", {}).get("http", {}).get("sourceIp", "")


def _ua(event):
    return event.get("requestContext", {}).get("http", {}).get("userAgent", "")


# ---- handlers ----
def list_entitlements(event):
    return _ok(db.list_entitlements(auth.customer_id(event)))


def list_orders(event):
    return _ok(db.list_orders(auth.customer_id(event)))


def create_order(event):
    b = _body(event)
    items = b.get("items") or []
    if not items:
        return _err("items required")
    amount = sum(int(i.get("price_cents", 0)) * int(i.get("qty", 1)) for i in items)
    order = Order(
        order_id=db.new_id("ord"),
        customer_id=auth.customer_id(event),
        items=items,
        amount_cents=amount,
        metadata=b.get("metadata") or {},
    )
    provider = get_provider()
    checkout = provider.create_checkout(order, b.get("success_url", ""), b.get("cancel_url", ""))
    db.put_order({**order.to_dict(), "provider_ref": checkout.provider_ref, "created_at": db.now()})
    return _ok({"order_id": order.order_id, "checkout_url": checkout.checkout_url, "amount_cents": amount})


def payment_event(event):
    provider = get_provider()
    payload = _body(event)
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if not provider.verify_signature(event.get("body") or "{}", headers):
        return _err("bad signature", 401)
    ev = provider.parse_event(payload, headers)
    if ev.event_type == "payment.succeeded" and ev.order_id:
        order = db.get_order(ev.order_id)
        if order:
            recorded = db.record_charge(
                ev.event_id, ev.order_id, order.get("customer_id", ""),
                ev.amount_cents, provider.name,
            )
            if recorded:  # idempotent — only grant once
                db.update_order_status(ev.order_id, "paid")
                for item in order.get("items", []):
                    db.grant(order["customer_id"], item["product_id"], ev.order_id)
    return _ok({"received": True, "event": ev.event_type})


def accept_contract(event):
    b = _body(event)
    cid = db.record_contract(
        auth.customer_id(event), b.get("type", "terms"),
        b.get("version", "1.0"), _ip(event), _ua(event),
    )
    return _ok({"contract_id": cid, "accepted": True})


def list_contracts(event):
    return _ok(db.list_contracts(auth.customer_id(event)))


def billing(event):
    provider = get_provider()
    return _ok(provider.get_billing(auth.customer_id(event)))


def chat(event):
    b = _body(event)
    msg = b.get("message", "")
    if not msg:
        return _err("message required")
    ents = db.list_entitlements(auth.customer_id(event))
    ctx = "Customer owns: " + (", ".join(e["product_id"] for e in ents) or "nothing yet")
    return _ok({"answer": _answer(ctx, msg), "context": ctx})


# ---- RAG-ish answer (Bedrock if configured, else rule-based fallback) ----
def _answer(ctx, msg):
    model = os.environ.get("BEDROCK_MODEL_ID")
    if model:
        try:
            import boto3
            br = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-2"))
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": "You are the support assistant for Generative Artificial Intelligence (genai-usa.com). Be concise and helpful. Use the customer context to personalize answers.",
                "messages": [{"role": "user", "content": f"Customer context: {ctx}\n\nQuestion: {msg}"}],
            }
            r = br.invoke_model(modelId=model, body=json.dumps(body))
            return json.loads(r["body"].read())["content"][0]["text"]
        except Exception as e:
            return _fallback(msg) + f" (bedrock unavailable: {e})"
    return _fallback(msg)


def _fallback(msg):
    m = msg.lower()
    if any(k in m for k in ("price", "cost", "much", "plan")):
        return "Plans: $4,999/mo AI Concierge · $7,499/mo AI Growth Team · $14,499/mo Fractional AI Department · $19,999/mo AI Transformation Partner."
    if any(k in m for k in ("chatbot", "bot", "support")):
        return "We build support chatbots trained on your docs, live in 7–10 days. See the Services page for details."
    if any(k in m for k in ("voice", "call", "receptionist", "missed")):
        return "Our Missed-Call Recovery installs an AI voice receptionist in 48 hours — it answers, books, and confirms by SMS."
    if any(k in m for k in ("purchase", "bought", "order", "own", "product")):
        return "Check the left panel for everything you've purchased. If something's missing, email hello@genai-usa.com."
    return "I can help with our services, plans, and your purchases. Try asking about pricing, chatbots, voice agents, or what you've bought."


_ROUTES = {
    ("GET", "/entitlements"): list_entitlements,
    ("GET", "/orders"): list_orders,
    ("POST", "/orders"): create_order,
    ("POST", "/webhooks/payments"): payment_event,
    ("POST", "/contracts/accept"): accept_contract,
    ("GET", "/contracts"): list_contracts,
    ("GET", "/billing"): billing,
    ("POST", "/chat"): chat,
}


def lambda_handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method") or "GET").upper()
    path = event.get("rawPath") or event.get("requestContext", {}).get("http", {}).get("path") or "/"
    handler = _ROUTES.get((method, path))
    if not handler:
        return _err("not found", 404)
    try:
        return handler(event)
    except Exception as e:
        return _err(f"server error: {e}", 500)
