"""WebGL failure → CSS-motion (or classic) soft fallback — research contract only."""

from __future__ import annotations

from typing import Any, Literal

DeliveryMode = Literal["webgl_3d", "css_motion", "classic"]

FALLBACK_SPEC: dict[str, Any] = {
    "version": 1,
    "preferred": "webgl_3d",
    "on_webgl_unavailable": "css_motion",
    "on_budget_fail": "css_motion",
    "on_license_fail": "classic",  # never ship unlicensed 3D; classic is safe
    "detect": [
        "WebGLRenderingContext",
        "WebGL2RenderingContext",
        "fail_if_software_renderer_optional",
    ],
    "client_copy": {
        "de": "3D-Ansicht ist auf diesem Gerät nicht verfügbar — wir zeigen die flüssige CSS-Version.",
        "en": "3D view is unavailable on this device — showing the smooth CSS version instead.",
        "ru": "3D на этом устройстве недоступен — показываем плавную CSS-версию.",
        "uk": "3D на цьому пристрої недоступний — показуємо плавну CSS-версію.",
    },
}


def resolve_delivery_mode(
    *,
    webgl_ok: bool,
    license_ok: bool,
    budget_ok: bool,
    want_3d: bool = True,
) -> DeliveryMode:
    """Deterministic mode picker for research harness / future premium contour."""
    if not want_3d:
        return "classic"
    if not license_ok:
        return "classic"
    if not budget_ok:
        return "css_motion"
    if not webgl_ok:
        return "css_motion"
    return "webgl_3d"
