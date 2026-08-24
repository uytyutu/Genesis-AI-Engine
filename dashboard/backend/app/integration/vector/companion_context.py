"""B4.1 — Auth + Client Context for Vector Business Companion.

Authenticated customer_id → existing Client Context SSOT → tenant-safe payload.
No LLM, no Web Research, no ACTION, no new metric/product sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.integration.client_analytics import ClientAnalyticsService
from app.integration.vector.companion_contracts import (
    ASSISTANT_NAME,
    B4_ENGINE,
    CONTEXT_ENGINE_REQUIRED,
    CONTEXT_PATH,
    DEFAULT_GREETING_DE,
    ENTRY_SURFACE,
    ContextRef,
    assert_context_engine,
    location_from_path,
)

B4_1_SLICE = "B4.1"
COMPANION_CONTEXT_PATH = "/api/client/vector/companion-context"


class CompanionTenantDenied(PermissionError):
    """Raised when a caller tries to load another tenant's context."""


def enforce_tenant(
    *,
    auth_customer_id: str,
    requested_customer_id: str | None,
) -> None:
    """Reject spoofed customer_id. Auth subject is the only allowed tenant."""
    auth = str(auth_customer_id or "").strip()
    if not auth:
        raise HTTPException(status_code=401, detail="client_auth_required")
    req = str(requested_customer_id or "").strip()
    if req and req != auth:
        raise HTTPException(status_code=403, detail="tenant_mismatch")


class CompanionContextService:
    """Load Vector companion context for the authenticated client only."""

    def __init__(self, memory_dir: Path, *, sales: Any | None = None) -> None:
        self._memory = Path(memory_dir)
        self._sales = sales
        self._analytics = ClientAnalyticsService(self._memory, sales=sales)

    def load_for_session(
        self,
        *,
        auth_customer_id: str,
        auth_email: str | None = None,
        me: dict[str, Any] | None = None,
        period: str = "30d",
        page_path: str | None = None,
        requested_customer_id: str | None = None,
    ) -> dict[str, Any]:
        """Return tenant-bound companion context from b3_client_context_v1.

        ``requested_customer_id`` may come from a query param; if set, it must
        equal ``auth_customer_id`` or the call is forbidden (403).
        """
        enforce_tenant(
            auth_customer_id=auth_customer_id,
            requested_customer_id=requested_customer_id,
        )
        customer_id = str(auth_customer_id).strip()
        email = (auth_email or "").strip() or None
        me = me or {}

        # Always bind to auth subject — never to a client-supplied id.
        context = self._analytics.client_context(
            customer_id=customer_id,
            email=email or str(me.get("email") or "") or None,
            me=me,
            period=period,  # type: ignore[arg-type]
        )
        engine = str(context.get("engine") or "")
        assert_context_engine(engine)

        location = location_from_path(page_path)
        return {
            "ok": True,
            "engine": B4_ENGINE,
            "slice": B4_1_SLICE,
            "assistant": ASSISTANT_NAME,
            "entry_surface": ENTRY_SURFACE,
            "greeting": DEFAULT_GREETING_DE,
            "customer_id": customer_id,
            "location": location,
            "page_path": page_path,
            "context_ref": ContextRef(path=CONTEXT_PATH, engine=CONTEXT_ENGINE_REQUIRED, period=period).to_dict(),
            "context": context,
            # B4.1 foundation flags — intelligence arrives in later slices
            "modes_enabled": ["context_read"],
            "llm": False,
            "research": False,
            "action": False,
            "honesty": (
                "Tenant-bound Client Context only. "
                "No LLM / research / ACTION in B4.1. "
                f"SSOT={CONTEXT_PATH} ({CONTEXT_ENGINE_REQUIRED})."
            ),
        }
