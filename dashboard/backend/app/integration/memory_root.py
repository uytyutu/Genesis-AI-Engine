"""Foundation F3 — memory root with optional tenant partition.

Mission 1: owner/platform uses the legacy flat ``memory/`` tree (no migration).
Future customer tenants: ``memory/tenants/{tenant_id}/``.
"""

from __future__ import annotations

from pathlib import Path

from app.integration.tenant_context import OWNER_TENANT_ID

_LEGACY_OWNER_IDS = frozenset({OWNER_TENANT_ID, "owner", "default", "_owner"})


class MemoryRoot:
    """Single entry for filesystem roots under IntegrationContext."""

    def __init__(self, base: Path, *, tenant_id: str = OWNER_TENANT_ID) -> None:
        self._base = base.expanduser()
        self._tenant_id = tenant_id.strip() or OWNER_TENANT_ID

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    @property
    def root(self) -> Path:
        if self._tenant_id in _LEGACY_OWNER_IDS:
            return self._base
        return self._base / "tenants" / self._tenant_id

    def subpath(self, *parts: str, mkdir: bool = False) -> Path:
        path = self.root.joinpath(*parts)
        if mkdir:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def for_visitor_data(self, visitor_id: str) -> Path:
        """Brain visitor files — unchanged layout under genesis_brain/users."""
        safe = (visitor_id or "anonymous").strip()[:64] or "anonymous"
        return self.subpath("genesis_brain", "users", mkdir=True) / f"{safe}.json"
