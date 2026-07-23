"""S1.3 — Authorization Matrix (Guest / Client / Support / Owner).

Declarative expectations against *current* surfaces.
Support is not a portal Account role yet — matrix encodes that as deny-by-default
on portal commerce APIs (no silent privilege).
"""

from __future__ import annotations

from typing import Literal

ENGINE_ID = "s1_3_authz_matrix_v1"

Role = Literal["guest", "client", "support", "owner"]
Access = Literal["deny", "own_only", "read_limited", "allow"]

# Resource columns from CEO matrix (Orders · Billing · Licenses · Support · Admin)
AUTHZ_MATRIX: dict[Role, dict[str, Access]] = {
    "guest": {
        "orders": "deny",
        "billing": "deny",
        "licenses": "deny",
        "support": "deny",
        "admin": "deny",
    },
    "client": {
        "orders": "own_only",
        "billing": "own_only",
        "licenses": "own_only",
        "support": "own_only",
        "admin": "deny",
    },
    "support": {
        "orders": "read_limited",
        "billing": "read_limited",
        "licenses": "read_limited",
        "support": "allow",
        "admin": "deny",
    },
    "owner": {
        "orders": "allow",
        "billing": "allow",
        "licenses": "allow",
        "support": "allow",
        "admin": "allow",
    },
}

# Portal HTTP paths used to enforce Guest/Client today (commerce).
PORTAL_PROTECTED_PATHS: tuple[str, ...] = (
    "/portal/billing",
    "/portal/licenses",
    "/portal/my-products",
    "/portal/chatbot/conversations",
)

OWNER_ADMIN_PREFIXES: tuple[str, ...] = ("/api/owner/",)
SUPPORT_PREFIXES: tuple[str, ...] = ("/api/support",)


def matrix_cell(role: Role, resource: str) -> Access:
    return AUTHZ_MATRIX[role][resource]


def guest_must_be_denied(resource: str) -> bool:
    return matrix_cell("guest", resource) == "deny"


def client_admin_denied() -> bool:
    return matrix_cell("client", "admin") == "deny"


def support_admin_denied() -> bool:
    return matrix_cell("support", "admin") == "deny"
