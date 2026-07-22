"""R4.1 — Login HTTP DTOs (transport only)."""

from __future__ import annotations

from pydantic import BaseModel, Field

ENGINE_ID = "login_api_contract_v1"


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Public login outcome — never includes domain failure_reason."""

    authenticated: bool
