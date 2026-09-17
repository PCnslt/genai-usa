"""Single Lambda API router (HTTP API v2 payload).

Routes are dispatched on (method, path-template); templates may contain
`{param}` segments (e.g. `/ops/orders/{id}/fulfill`). Authorization is
enforced per-handler using Cognito groups via `auth.py`.

  Customer (any authenticated user):
    GET  /products            -> catalog
    GET  /entitlements        -> what the customer owns
    GET  /orders              -> customer's orders
    POST /orders              -> create order + payment checkout (idempotent)
    GET  /billing             -> billing portal URL (self-serve)
    GET  /contracts/latest    -> active terms text + version
    GET  /contracts           -> customer's signed contracts
    POST /contracts/accept    -> clickwrap acceptance (stored, timestamped)
    POST /chat                -> RAG support bot
    GET  /support             -> customer's support thread
    POST /support             -> open a support message
    POST /webhooks/payments   -> provider webhook (idempotent grant) [no auth]

  Employee (+ admin):
    GET  /ops/orders          -> all orders
    POST /ops/orders/{id}/fulfill -> move fulfillment status
    GET  /ops/contracts       -> all accepted contracts
    GET  /ops/support         -> open support messages
    POST /ops/support/{id}/reply -> reply + resolve

  Admin only:
    POST   /ops/products             -> upsert product/pricing
    DELETE /ops/products/{id}        -> remove product
    GET    /ops/users                -> list users
    POST   /ops/users/{username}/role -> add/remove group
    GET    /ops/finance              -> revenue summary
    POST   /ops/contracts/template   -> update active terms
"""
from __future__ import annotations

import json
import os
import re
from decimal import Decimal
from typing import Optional

import auth
import db
import terms
from payments import get_provider, Order
from products import CATALOG, by_id as catalog_by_id

CONTRACT_TYPE = "terms"


def _json_default(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)


def _ok(body, status=200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key",
        },
        "body": json.dumps(body, default=_json_default),
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


# ---- role guards ----
def _require_admin(event):
    if not auth.is_admin(event):
        raise PermissionError("admins only")


def _require_employee(event):
    if not auth.is_employee(event):
        raise PermissionError("employees only")


# ---- active contract (runtime override in genai-meta) ----
def _active_terms() -> dict:
    raw = db.get_meta("contract")
    if raw:
        try:
            d = json.loads(raw)
            if d.get("version") and d.get("text"):
                return d
        except Exception:
            pass
    return {"version": terms.VERSION, "text": terms.TERMS_TEXT}


# ---- catalog ----
def list_products(event):
    products = db.list_products()
    if not products:  # table empty -> fall back to the seeded catalog in code
        products = CATALOG
    return _ok({"products": products})


def me(event):
    g = auth.claims(event).get("cognito:groups")
    return _ok({
        "sub": auth.customer_id(event),
        "email": auth.email(event),
        "roles": auth.roles(event),
        "raw_groups": g,
        "raw_groups_type": type(g).__name__,
        "is_admin": auth.is_admin(event),
        "is_employee": auth.is_employee(event),
    })


# ---- customer: orders / entitlements ----
def list_entitlements(event):
    return _ok(db.list_entitlements(auth.customer_id(event)))


def list_orders(event):
    return _ok(db.list_orders(auth.customer_id(event)))


def create_order(event):
    b = _body(event)
    items = b.get("items") or []
    if not items:
        return _err("items required")
    # gate on accepted active contract
    ver = _active_terms()["version"]
    if not db.has_accepted(auth.customer_id(event), ver):
        return _err("contract_required", 403)

    # normalize items: accept {product_id, qty} or {product_id, price_cents, qty}
    norm = []
    for it in items:
        pid = it.get("product_id")
        if not pid:
            return _err("each item needs a product_id")
        qty = int(it.get("qty", 1))
        price = it.get("price_cents")
        name = it.get("name", "")
        if price is None:
            cat = catalog_by_id().get(pid) or db.get_product(pid)
            if not cat:
                return _err(f"unknown product {pid}")
            price = int(cat.get("price_cents", 0))
            name = cat.get("name", pid)
        norm.append({"product_id": pid, "name": name, "price_cents": int(price), "qty": qty})

    amount = sum(i["price_cents"] * i["qty"] for i in norm)
    recurring = bool(b.get("recurring"))
    order = Order(
        order_id=db.new_id("ord"),
        customer_id=auth.customer_id(event),
        items=norm,
        amount_cents=amount,
        metadata={**(b.get("metadata") or {}), "recurring": recurring},
    )
    provider = get_provider()
    checkout = provider.create_checkout(
        order, b.get("success_url", ""), b.get("cancel_url", ""))
    db.put_order({**order.to_dict(), "provider_ref": checkout.provider_ref,
                  "created_at": db.now()})
    return _ok({"order_id": order.order_id,
                "checkout_url": checkout.checkout_url,
                "amount_cents": amount})


def billing(event):
    provider = get_provider()
    return _ok(provider.get_billing(auth.customer_id(event)))


# ---- contracts ----
def contracts_latest(event):
    return _ok(_active_terms())


def list_contracts(event):
    return _ok(db.list_contracts(auth.customer_id(event)))


def accept_contract(event):
    b = _body(event)
    ver = b.get("version") or _active_terms()["version"]
    cid = db.record_contract(
        auth.customer_id(event), b.get("type", CONTRACT_TYPE),
        ver, _ip(event), _ua(event),
    )
    return _ok({"contract_id": cid, "accepted": True, "version": ver})


# ---- RAG support bot ----
def chat(event):
    b = _body(event)
    msg = b.get("message", "")
    if not msg:
        return _err("message required")
    cid = auth.customer_id(event)
    ents = db.list_entitlements(cid)
    ctx = _build_context(cid, ents)
    answer = _answer(ctx, msg)
    return _ok({"answer": answer, "context_owned": [e["product_id"] for e in ents]})


def _build_context(cid: str, ents: list) -> str:
    owned = [e["product_id"] for e in ents] or []
    owned_names = [catalog_by_id().get(p, {}).get("name", p) for p in owned]
    catalog = db.list_products() or CATALOG
    lines = [f"Customer owns: {', '.join(owned_names) if owned_names else 'nothing yet'}"]
    lines.append("Available products/services (id — name — price):")
    for p in catalog:
        price = int(p.get("price_cents", 0)) / 100
        monthly = int(p.get("monthly_cents", 0)) / 100
        price_s = f"${price:,.0f}" + (f" + ${monthly:,.0f}/mo" if monthly else "")
        lines.append(f"- {p['product_id']} — {p['name']} — {price_s}")
    return "\n".join(lines)


def _answer(ctx: str, msg: str) -> str:
    model = os.environ.get("BEDROCK_MODEL_ID")
    if model:
        try:
            import boto3
            br = boto3.client("bedrock-runtime",
                              region_name=os.environ.get("AWS_REGION", "us-east-2"))
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "system": ("You are the support assistant for Generative Artificial "
                           "Intelligence (genai-usa.com). Be concise and helpful. Use the "
                           "catalog + customer context below to give accurate, personalized "
                           "answers. Never invent prices."),
                "messages": [{"role": "user",
                              "content": f"Context:\n{ctx}\n\nQuestion: {msg}"}],
            }
            r = br.invoke_model(modelId=model, body=json.dumps(body))
            return json.loads(r["body"].read())["content"][0]["text"]
        except Exception as e:
            return _fallback(ctx, msg) + f"\n\n_(bedrock unavailable: {e})_"
    return _fallback(ctx, msg)


def _fallback(ctx: str, msg: str) -> str:
    m = msg.lower()
    cat = catalog_by_id()
    # token-overlap match against product names (prefer most hits)
    best = None
    for pid, p in cat.items():
        words = [w for w in re.split(r"[^a-z0-9]+", p["name"].lower()) if len(w) >= 4]
        if not words:
            continue
        hits = sum(1 for w in words if w in m)
        if hits and (best is None or hits > best[0]):
            best = (hits, p)
    if best:
        p = best[1]
        price = int(p["price_cents"]) / 100
        monthly = int(p.get("monthly_cents", 0)) / 100
        price_s = f"${price:,.0f}" + (f" + ${monthly:,.0f}/mo" if monthly else "")
        return f"{p['name']} — {p['description']} Price: {price_s}."
    if any(k in m for k in ("price", "cost", "much", "plan", "pricing")):
        return ("Plans: $4,999/mo AI Concierge · $7,499/mo AI Growth Team · "
                "$14,499/mo Fractional AI Department · $19,999/mo AI Transformation Partner.")
    if any(k in m for k in ("chatbot", "bot", "support")):
        return "We build support chatbots trained on your docs, live in 7–10 days. See the Shop for pricing."
    if any(k in m for k in ("voice", "call", "receptionist", "missed")):
        return "Our Missed-Call Recovery installs an AI voice receptionist in 48 hours — it answers, books, and confirms by SMS."
    if any(k in m for k in ("purchase", "bought", "order", "own", "product")):
        return "Check the left panel for everything you've purchased. If something's missing, email hello@genai-usa.com."
    return "I can help with our services, plans, and your purchases. Try asking about pricing, chatbots, voice agents, or what you've bought."


# ---- support (customer) ----
def open_support(event):
    b = _body(event)
    body = (b.get("message") or "").strip()
    if not body:
        return _err("message required")
    mid = db.send_support(auth.customer_id(event), auth.email(event),
                          b.get("subject", "Support request"), body)
    return _ok({"message_id": mid, "status": "open"})


def my_support(event):
    return _ok(db.list_support_customer(auth.customer_id(event)))


# ---- ops: employee + admin ----
def ops_orders(event):
    _require_employee(event)
    return _ok(db.list_all_orders())


def ops_fulfill(event, params):
    _require_employee(event)
    status = _body(event).get("status", "in_progress")
    if status not in ("pending", "in_progress", "delivered"):
        return _err("status must be pending|in_progress|delivered")
    db.set_fulfillment(params["id"], status)
    return _ok({"order_id": params["id"], "fulfillment_status": status})


def ops_contracts(event):
    _require_employee(event)
    return _ok(db.list_all_contracts())


def ops_support(event):
    _require_employee(event)
    return _ok(db.list_open_support())


def ops_reply(event, params):
    _require_employee(event)
    reply = (_body(event).get("reply") or "").strip()
    if not reply:
        return _err("reply required")
    db.reply_support(params["id"], reply)
    return _ok({"message_id": params["id"], "status": "resolved"})


# ---- ops: admin only ----
def ops_upsert_product(event):
    _require_admin(event)
    b = _body(event)
    pid = b.get("product_id")
    if not pid:
        return _err("product_id required")
    db.put_product(pid, b.get("name", pid), b.get("price_cents", 0),
                   b.get("kind", "product"), b.get("description", ""),
                   bool(b.get("recurring")), b.get("monthly_cents", 0))
    return _ok({"product_id": pid, "saved": True})


def ops_delete_product(event, params):
    _require_admin(event)
    db.delete_product(params["id"])
    return _ok({"product_id": params["id"], "deleted": True})


def ops_users(event):
    _require_admin(event)
    import boto3
    cidp = boto3.client("cognito-idp")
    pool = os.environ.get("USER_POOL_ID")
    if not pool:
        return _err("USER_POOL_ID not configured", 500)
    users = []
    token = None
    while True:
        kwargs = {"UserPoolId": pool, "Limit": 60}
        if token:
            kwargs["PaginationToken"] = token
        r = cidp.list_users(**kwargs)
        for u in r.get("Users", []):
            attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
            users.append({
                "username": u.get("Username"),
                "email": attrs.get("email", ""),
                "status": u.get("UserStatus"),
                "created_at": u.get("UserCreateDate").isoformat() if u.get("UserCreateDate") else None,
            })
        token = r.get("PaginationToken")
        if not token:
            break
    return _ok({"users": users})


def ops_set_role(event, params):
    _require_admin(event)
    b = _body(event)
    group = b.get("group")
    action = b.get("action", "add")  # add | remove
    if group not in ("customers", "employees", "admins"):
        return _err("group must be customers|employees|admins")
    import boto3
    cidp = boto3.client("cognito-idp")
    pool = os.environ.get("USER_POOL_ID")
    kw = {"UserPoolId": pool, "Username": params["username"], "GroupName": group}
    if action == "remove":
        cidp.admin_remove_user_from_group(**kw)
    else:
        cidp.admin_add_user_to_group(**kw)
    return _ok({"username": params["username"], "group": group, "action": action})


def ops_finance(event):
    _require_admin(event)
    return _ok(db.finance_summary())


def ops_set_contract(event):
    _require_admin(event)
    b = _body(event)
    version = b.get("version")
    text = b.get("text")
    if not version or not text:
        return _err("version and text required")
    db.set_meta("contract", json.dumps({"version": version, "text": text}))
    return _ok({"version": version, "updated": True})


# ---- webhook (idempotent grant) ----
def payment_event(event):
    provider = get_provider()
    payload = _body(event)
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    raw_body = event.get("body") or "{}"
    if not provider.verify_signature(raw_body, headers):
        return _err("bad signature", 401)
    ev = provider.parse_event(payload, headers)
    if ev.event_type == "payment.succeeded" and ev.order_id:
        order = db.get_order(ev.order_id)
        if order:
            recorded = db.record_charge(
                ev.event_id, ev.order_id, order.get("customer_id", ""),
                ev.amount_cents, provider.name)
            if recorded:  # idempotent — only grant once
                db.update_order_status(ev.order_id, "paid")
                db.set_fulfillment(ev.order_id, "in_progress")
                for item in order.get("items", []):
                    db.grant(order["customer_id"], item["product_id"], ev.order_id)
    return _ok({"received": True, "event": ev.event_type})


# ---- routing ----
_ROUTES = [
    (("GET", "/products"), list_products),
    (("GET", "/me"), me),
    (("GET", "/entitlements"), list_entitlements),
    (("GET", "/orders"), list_orders),
    (("POST", "/orders"), create_order),
    (("GET", "/billing"), billing),
    (("GET", "/contracts/latest"), contracts_latest),
    (("GET", "/contracts"), list_contracts),
    (("POST", "/contracts/accept"), accept_contract),
    (("POST", "/chat"), chat),
    (("POST", "/support"), open_support),
    (("GET", "/support"), my_support),
    (("POST", "/webhooks/payments"), payment_event),

    (("GET", "/ops/orders"), ops_orders),
    (("POST", "/ops/orders/{id}/fulfill"), ops_fulfill),
    (("GET", "/ops/contracts"), ops_contracts),
    (("GET", "/ops/support"), ops_support),
    (("POST", "/ops/support/{id}/reply"), ops_reply),

    (("POST", "/ops/products"), ops_upsert_product),
    (("DELETE", "/ops/products/{id}"), ops_delete_product),
    (("GET", "/ops/users"), ops_users),
    (("POST", "/ops/users/{username}/role"), ops_set_role),
    (("GET", "/ops/finance"), ops_finance),
    (("POST", "/ops/contracts/template"), ops_set_contract),
]


def _resolve(method: str, path: str):
    segs = [s for s in path.split("/") if s]
    for (m, template), handler in _ROUTES:
        if m != method:
            continue
        tsegs = [s for s in template.split("/") if s]
        if len(tsegs) != len(segs):
            continue
        params = {}
        ok = True
        for t, s in zip(tsegs, segs):
            if t.startswith("{") and t.endswith("}"):
                params[t[1:-1]] = s
            elif t != s:
                ok = False
                break
        if ok:
            return handler, params
    return None, {}


def lambda_handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method") or "GET").upper()
    path = event.get("rawPath") or event.get("requestContext", {}).get("http", {}).get("path") or "/"
    if method == "OPTIONS":
        return _ok({"ok": True})
    handler, params = _resolve(method, path)
    if handler is None:
        return _err("not found", 404)
    try:
        if params:
            return handler(event, params)
        return handler(event)
    except PermissionError as e:
        return _err(str(e), 403)
    except Exception as e:
        return _err(f"server error: {e}", 500)
