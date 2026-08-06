"""Commercial UX Gate — public copy must match Virtus Core product (not Landing-era).

Launch blocker before ads: order / site CTAs must not sell "Landing" when the
catalog is website · store · AI Assistant.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Buyer-facing order / CTA strings must not use Landing-era product naming.
_BANNED_IN_ORDER_KEYS = re.compile(
    r"Landing\s*Page|Landing\s*bestellen|Order\s*Landing|Заказать\s*Landing|"
    r"Landing\s*Information|Landing\s+Website|Landing\s+zuerst|сначала\s+Landing",
    re.IGNORECASE,
)

_ORDER_KEYS = (
    "title",
    "subtitle",
    "bulletAfterPay",
    "whyFormBody",
    "ctaSecondary",
)


def _frontend_locales_root() -> Path:
    return Path(__file__).resolve().parents[3] / "frontend" / "locales"


def _scan_locale(path: Path) -> list[str]:
    hits: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [f"unreadable:{path.name}"]
    order = data.get("order") if isinstance(data.get("order"), dict) else {}
    path_a = data.get("pathA") if isinstance(data.get("pathA"), dict) else {}
    for key in _ORDER_KEYS:
        val = str(order.get(key) or "")
        if key == "ctaSecondary":
            val = str(path_a.get("ctaSecondary") or order.get(key) or "")
        if val and _BANNED_IN_ORDER_KEYS.search(val):
            hits.append(f"{path.parent.name}/order.{key}")
    # pathA packages + CTA (showcase)
    for key in ("packagesTitle", "ctaSecondary", "foot"):
        val = str(path_a.get(key) or "")
        if val and _BANNED_IN_ORDER_KEYS.search(val):
            hits.append(f"{path.parent.name}/pathA.{key}")
    return hits


def audit_commercial_ux_gate() -> dict[str, Any]:
    """Return ok=True when public DE/EN/RU order+CTA copy is Virtus Core era."""
    root = _frontend_locales_root()
    hits: list[str] = []
    checked = 0
    for lang in ("de", "en", "ru"):
        path = root / lang / "site.json"
        if not path.is_file():
            hits.append(f"missing:{lang}/site.json")
            continue
        checked += 1
        hits.extend(_scan_locale(path))

    # Order page metadata must not say Landing
    order_layout = (
        Path(__file__).resolve().parents[3]
        / "frontend"
        / "app"
        / "order"
        / "layout.tsx"
    )
    if order_layout.is_file():
        text = order_layout.read_text(encoding="utf-8")
        if re.search(r"Landing\s*bestellen|Landing\s*Page", text, re.I):
            hits.append("order/layout.tsx")

    ok = checked >= 3 and not hits
    return {
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "checked_locales": checked,
        "violations": hits[:20],
        "detail": (
            "No Landing-era product naming in order/showcase CTAs"
            if ok
            else f"Stale Landing copy: {', '.join(hits[:8])}"
        ),
    }


def audit_commercial_ux_ready() -> dict[str, Any]:
    """Alias used by golden_website_launch."""
    return audit_commercial_ux_gate()
