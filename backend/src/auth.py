"""Auth helpers — extract identity + role from a Cognito-issued JWT.

API Gateway (HTTP API) with a Cognito JWT authorizer passes the validated
token in `event.requestContext.authorizer.jwt.claims`. Roles come from the
`cognito:groups` claim (customers / employees / contractors / admins).

Note: the HTTP API authorizer serializes the `cognito:groups` array as a string
like "[customers admins]", so `roles()` normalizes both list and string forms.
"""
from __future__ import annotations

import re


def claims(event: dict) -> dict:
    return (event.get("requestContext", {})
                .get("authorizer", {})
                .get("jwt", {})
                .get("claims", {}))


def customer_id(event: dict) -> str:
    return claims(event).get("sub", "")


def email(event: dict) -> str:
    c = claims(event)
    return c.get("email") or c.get("cognito:username") or c.get("username") or ""


def username(event: dict) -> str:
    return claims(event).get("cognito:username", "") or claims(event).get("username", "")


def roles(event: dict) -> list[str]:
    g = claims(event).get("cognito:groups", [])
    if isinstance(g, str):
        # authorizer passes arrays as "[customers admins]" — strip + split
        g = g.strip().strip("[]")
        return [x for x in re.split(r"[,\s]+", g) if x]
    return g or []


def is_admin(event: dict) -> bool:
    return "admins" in roles(event)


def is_employee(event: dict) -> bool:
    return "employees" in roles(event) or is_admin(event)


def is_contractor(event: dict) -> bool:
    return "contractors" in roles(event)


def is_staff(event: dict) -> bool:
    """Account managers / engineers (contractors) OR internal employees/admins."""
    return is_employee(event) or is_contractor(event)


def is_customer(event: dict) -> bool:
    return "customers" in roles(event) or is_admin(event)
