"""Pseudonym / identity layer for the anonymized customer<->contractor relay.

Goal (per owner): the Fiverr contractor must never learn the customer's real
identity, and the customer must never realize they're talking to a Fiverr
contractor. We achieve this with deterministic, stable aliases:

  - customer -> "Client #A1B2"      (seen by the contractor)
  - manager  -> "Alex" (first name) (seen by the customer, "Alex · Account Manager")

Aliases are derived from the raw Cognito `sub` so they're stable across
messages but reveal nothing about the underlying identity.
"""
from __future__ import annotations

import hashlib

# Stable first-name pool for account managers (Fiverr contractors). Each
# contractor is mapped to a name deterministically from their sub.
MANAGER_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam",
    "Drew", "Jamie", "Quinn", "Avery", "Reese",
]


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def customer_alias(customer_id: str) -> str:
    if not customer_id:
        return "Client"
    return "Client #" + _h(customer_id)[:4].upper()


def manager_name(manager_id: str) -> str:
    if not manager_id:
        return "Account Manager"
    idx = int(_h(manager_id), 16) % len(MANAGER_NAMES)
    return MANAGER_NAMES[idx]


def manager_label(manager_id: str) -> str:
    return manager_name(manager_id) + " · Account Manager"
