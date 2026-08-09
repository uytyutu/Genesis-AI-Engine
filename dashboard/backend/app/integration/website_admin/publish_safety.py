"""Publish safety gate — block broken / empty Website publishes."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def evaluate_publish_safety(
    content: dict[str, Any],
    *,
    product_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Returns { ok, blockers: [{id, message}], warnings: [...] }.
    Hard blockers prevent publish.
    """
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    hero = content.get("hero") if isinstance(content.get("hero"), dict) else {}
    headline = str(hero.get("headline") or "").strip()
    if not headline:
        blockers.append(
            {
                "id": "empty_hero_headline",
                "message": "Hero headline is empty — fill it before publish.",
            }
        )

    services = content.get("services") if isinstance(content.get("services"), list) else []
    if not services:
        blockers.append(
            {
                "id": "no_services",
                "message": "Add at least one service before publish.",
            }
        )

    contacts = content.get("contacts") if isinstance(content.get("contacts"), dict) else {}
    phone = str(contacts.get("phone") or "").strip()
    email = str(contacts.get("email") or "").strip()
    if not phone and not email:
        blockers.append(
            {
                "id": "no_contact",
                "message": "Add phone or email before publish.",
            }
        )

    seo = content.get("seo") if isinstance(content.get("seo"), dict) else {}
    if not str(seo.get("title") or "").strip():
        warnings.append(
            {
                "id": "seo_title_missing",
                "message": "SEO title is empty.",
            }
        )

    # Broken media refs: image id without resolvable file is soft warn unless hero has broken id
    hero_img = hero.get("image")
    if isinstance(hero_img, dict) and hero_img.get("id") and not hero_img.get("path"):
        # still ok if media service can find by id — checked by caller optionally
        pass

    if product_dir is not None:
        index = product_dir / "index.html"
        if not index.is_file():
            blockers.append(
                {
                    "id": "missing_index",
                    "message": "Website HTML is missing — wait for Factory generation.",
                }
            )
        else:
            try:
                html = index.read_text(encoding="utf-8", errors="replace")
            except OSError:
                html = ""
            if "<img" in html and 'src=""' in html:
                blockers.append(
                    {
                        "id": "broken_img_src",
                        "message": "Empty image src found in HTML — fix media before publish.",
                    }
                )

    return {
        "ok": len(blockers) == 0,
        "blockers": blockers,
        "warnings": warnings,
    }
