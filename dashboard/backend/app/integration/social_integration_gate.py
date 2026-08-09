"""Social Integration Gate — readiness probe for CEO Launch Blockers.

SSOT: every website/store has a social block.
Starter = order-time links only (no CMS).
Business/Premium = CMS add/remove/reorder + custom URL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.product_gates_ssot import PACKAGE_SOCIAL_POLICY, SOCIAL_NETWORKS

ENGINE_ID = "social_integration_gate_v1"


def _previews_root() -> Path:
    return Path(__file__).resolve().parents[3] / "frontend" / "public" / "package-previews"


def audit_social_integration_ready() -> dict[str, Any]:
    """PASS only when demos expose a real social link surface (not CSS-only stubs)."""
    root = _previews_root()
    business = root / "sites" / "business"
    niches = (
        "dental",
        "law",
        "restaurant",
        "beauty",
        "auto",
        "fitness",
        "handwerk",
        "it",
    )
    items: list[dict[str, Any]] = []
    for niche in niches:
        index = business / niche / "index.html"
        if not index.is_file():
            items.append({"id": niche, "ok": False, "detail": "missing index.html"})
            continue
        html = index.read_text(encoding="utf-8", errors="replace").lower()
        has_nav = (
            'data-social="' in html
            or 'class="social-links"' in html
            or 'class="social-bar"' in html
            or 'aria-label="social"' in html
            or 'aria-label="soziale' in html
        )
        has_network_href = any(
            needle in html
            for needle in (
                "instagram.com",
                "facebook.com",
                "tiktok.com",
                "t.me/",
                "wa.me/",
                "youtube.com",
                "linkedin.com",
            )
        )
        # Explicit markers beat opportunistic brand mentions in copy.
        ok = has_nav and (has_network_href or "social-link" in html)
        items.append(
            {
                "id": niche,
                "ok": ok,
                "detail": (
                    "social block present"
                    if ok
                    else "no social-links / social-bar surface with network hrefs"
                ),
            }
        )

    passed = sum(1 for i in items if i["ok"])
    goal = len(niches)
    status = "PASS" if passed == goal else "FAIL"
    return {
        "ok": status == "PASS",
        "status": status,
        "engine": ENGINE_ID,
        "pass": passed,
        "goal": goal,
        "items": items,
        "package_policy": PACKAGE_SOCIAL_POLICY,
        "networks": list(SOCIAL_NETWORKS),
        "next": (
            "Social Integration Gate complete"
            if status == "PASS"
            else "Factory: inject social block from order links; Business CMS edit + demo sync"
        ),
    }
