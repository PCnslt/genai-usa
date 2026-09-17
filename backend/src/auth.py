"""Auth helpers — extract identity + role from a Cognito-issued JWT.

API Gateway (HTTP API) with a Cognito JWT authorizer passes the validated
token in `event.requestContext.authorizer.jwt.claims`. Roles come from the
`cognito:groups` claim (customers / employees / admins).
"""
from __future__ import annotations


def claims(event: dict) -> dict:
    return (event.get("requestContext", {})
                .get("authorizer", {})
                .get("jwt", {})
                .get("claims", {}))


def customer_id(event: dict) -> str:
    return claims(event).get("sub", "")


def roles(event: dict) -> list[str]:
    g = claims(event).get("cognito:groups", [])
    if isinstance(g, str):
        return [g]
    return g or []


def is_admin(event: dict) -> bool:
    return "admins" in roles(event)


def is_employee(event: dict) -> bool:
    return "employees" in roles(event) or is_admin(event)


def is_customer(event: dict) -> bool:
    return "customers" in roles(event) or is_admin(event)
