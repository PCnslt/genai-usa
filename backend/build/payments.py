"""
Payment provider abstraction layer.

Requirements (per owner):
1. SWAPPABLE  — active provider is chosen by env var (PROVIDER_NAME); adding
   Stripe / PayPal / bank-transfer is a new module + registry entry with zero
   changes to business logic.
2. IDEMPOTENT — every order carries an idempotency_key; every webhook event
   carries an event_id. Processing is keyed on these so a retry / re-delivery
   never double-charges or double-grants.
3. AGNOSTIC    — handlers only ever talk to PaymentProvider, never to a vendor
   SDK directly.
"""
from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class Order:
    order_id: str
    customer_id: str
    items: list                 # [{product_id, name, price_cents, qty}]
    amount_cents: int
    currency: str = "usd"
    idempotency_key: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = "pending"     # pending | paid | failed | refunded
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Checkout:
    checkout_url: str = ""
    provider_ref: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class Event:
    event_id: str
    event_type: str             # payment.succeeded | payment.failed | refund.processed
    order_id: str = ""
    customer_id: str = ""
    amount_cents: int = 0
    raw: dict = field(default_factory=dict)


class PaymentProvider(ABC):
    name = "abstract"

    @abstractmethod
    def create_checkout(self, order: Order, success_url: str, cancel_url: str) -> Checkout: ...

    @abstractmethod
    def parse_event(self, payload: Any, headers: dict) -> Event: ...

    @abstractmethod
    def verify_signature(self, payload: Any, headers: dict) -> bool: ...

    @abstractmethod
    def get_billing(self, customer_id: str) -> dict: ...

    @abstractmethod
    def refund(self, payment_id: str, amount_cents: Optional[int] = None) -> dict: ...


_REGISTRY: dict[str, type[PaymentProvider]] = {}


def register(name: str):
    def deco(cls: type[PaymentProvider]):
        cls.name = name
        _REGISTRY[name] = cls
        return cls
    return deco


def get_provider(name: Optional[str] = None) -> PaymentProvider:
    """Resolve the active provider. `name` overrides the PROVIDER_NAME env var."""
    name = name or os.environ.get("PROVIDER_NAME", "mock")
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown payment provider {name!r}; available: {sorted(_REGISTRY)}")
    return cls()


# ---------------------------------------------------------------------------
# Mock provider — works with zero configuration (used until a real account is
# wired). Emits a fake hosted checkout page and a synthetic success event.
# ---------------------------------------------------------------------------
@register("mock")
class MockProvider(PaymentProvider):
    def create_checkout(self, order: Order, success_url: str, cancel_url: str) -> Checkout:
        return Checkout(
            checkout_url=f"{success_url}?order_id={order.order_id}&mock=1",
            provider_ref=f"mock_{order.order_id}",
            raw={"provider": "mock", "idempotency_key": order.idempotency_key},
        )

    def parse_event(self, payload: Any, headers: dict) -> Event:
        return Event(
            event_id=payload.get("event_id", uuid.uuid4().hex),
            event_type=payload.get("type", "payment.succeeded"),
            order_id=payload.get("order_id", ""),
            customer_id=payload.get("customer_id", ""),
            amount_cents=int(payload.get("amount_cents", 0)),
            raw=payload,
        )

    def verify_signature(self, payload: Any, headers: dict) -> bool:
        return True  # mock accepts anything; real providers verify HMAC/signature

    def get_billing(self, customer_id: str) -> dict:
        return {"provider": "mock", "customer_id": customer_id, "invoices": []}

    def refund(self, payment_id: str, amount_cents: Optional[int] = None) -> dict:
        return {"provider": "mock", "payment_id": payment_id, "status": "refunded"}


# ---------------------------------------------------------------------------
# Stripe provider — enabled by PROVIDER_NAME=stripe + env keys. The SDK is
# imported lazily so the module still works without `stripe` installed.
# ---------------------------------------------------------------------------
@register("stripe")
class StripeProvider(PaymentProvider):
    def __init__(self):
        import stripe  # lazy: only needed when stripe is the active provider
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        self.stripe = stripe
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    def create_checkout(self, order: Order, success_url: str, cancel_url: str) -> Checkout:
        mode = "subscription" if order.metadata.get("recurring") else "payment"
        line_items = [{
            "price_data": {
                "currency": order.currency,
                "unit_amount": item["price_cents"],
                "product_data": {"name": item["name"]},
            },
            "quantity": item["qty"],
        } for item in order.items]
        session = self.stripe.checkout.Session.create(
            mode=mode,
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=order.order_id,
            idempotency_key=order.idempotency_key,   # Stripe-native idempotency
        )
        return Checkout(checkout_url=session.url, provider_ref=session.id, raw=dict(session))

    def parse_event(self, payload: Any, headers: dict) -> Event:
        # NOTE: production webhooks should reconstruct the event via
        # stripe.Webhook.construct_event(payload, sig, secret) which also
        # verifies the signature. Kept explicit here for clarity.
        etype = payload.get("type", "")
        obj = payload.get("data", {}).get("object", {})
        order_id = obj.get("client_reference_id") or obj.get("metadata", {}).get("order_id", "")
        return Event(
            event_id=payload.get("id", ""),
            event_type=etype,
            order_id=order_id,
            customer_id=obj.get("customer", "") or "",
            amount_cents=int(obj.get("amount_total", 0)),
            raw=payload,
        )

    def verify_signature(self, payload: Any, headers: dict) -> bool:
        try:
            sig = headers.get("stripe-signature", "")
            self.stripe.Webhook.construct_event(payload, sig, self.webhook_secret)
            return True
        except Exception:
            return False

    def get_billing(self, customer_id: str) -> dict:
        # Customer Portal gives the self-serve billing UI. The portal session is
        # created server-side and the URL returned to the client.
        session = self.stripe.billing_portal.Session.create(
            customer=customer_id, return_url=os.environ.get("PORTAL_RETURN_URL", ""),
        )
        return {"portal_url": session.url}

    def refund(self, payment_id: str, amount_cents: Optional[int] = None) -> dict:
        kwargs = {"payment_intent": payment_id}
        if amount_cents:
            kwargs["amount"] = amount_cents
        r = self.stripe.Refund.create(**kwargs, idempotency_key=uuid.uuid4().hex)
        return {"provider": "stripe", "payment_id": payment_id, "status": r.status}
