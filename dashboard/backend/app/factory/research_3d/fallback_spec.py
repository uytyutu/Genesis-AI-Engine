"""WebGL failure → CSS-motion / photo soft fallback — research contract only."""

from __future__ import annotations

from typing import Any, Literal

from app.factory.research_3d.quality_gate import (
    QUALITY_POLICY,
    quality_allows_client_3d,
    resolve_visual_mode,
)

DeliveryMode = Literal["webgl_3d", "css_motion", "classic", "photo"]

FALLBACK_SPEC: dict[str, Any] = {
    "version": 2,
    "preferred": "webgl_3d",
    "on_webgl_unavailable": "css_motion",
    "on_budget_fail": "css_motion",
    "on_license_fail": "classic",  # never ship unlicensed 3D; classic is safe
    "on_quality_fail": "photo_or_css_motion",
    "quality_policy": QUALITY_POLICY,
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
    "quality_copy": {
        "de": "Premium-3D nur mit geprüfter Fachmodell — sonst Foto oder CSS-Motion.",
        "en": "Premium 3D only with an approved thematic model — otherwise photo or CSS-Motion.",
    },
}


def resolve_delivery_mode(
    *,
    webgl_ok: bool,
    license_ok: bool,
    budget_ok: bool,
    want_3d: bool = True,
    quality_ok: bool | None = None,
    quality_tier: str | None = None,
    niche_id: str | None = None,
    photo_available: bool = False,
) -> DeliveryMode:
    """Deterministic mode picker for research harness / future premium contour.

    quality_ok=False forces soft fallback (legacy callers).
    Prefer quality_tier + niche_id for the full CEO quality rule.
    """
    if quality_ok is False:
        if photo_available:
            return "photo"
        return "css_motion"

    if quality_tier is not None or niche_id is not None:
        mode = resolve_visual_mode(
            niche_id=niche_id,
            quality_tier=quality_tier,
            webgl_ok=webgl_ok,
            license_ok=license_ok,
            budget_ok=budget_ok,
            want_3d=want_3d,
            photo_available=photo_available,
        )
        return mode  # type: ignore[return-value]

    if not want_3d:
        return "classic"
    if not license_ok:
        return "classic"
    if not budget_ok:
        return "css_motion"
    if not webgl_ok:
        return "css_motion"
    return "webgl_3d"


__all__ = [
    "FALLBACK_SPEC",
    "DeliveryMode",
    "resolve_delivery_mode",
    "quality_allows_client_3d",
]
