"""Website Admin Tips — legal / SEO / performance / content from Factory meta + HTML.

Honesty: only emit Fix actions when a live capability exists; otherwise Coming R3.2.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.integration.vector.capabilities import action_for, is_live
from app.portal.website_catalog import default_factory_sandbox_dirs


def find_product_dir(product_id: str) -> Path | None:
    pid = (product_id or "").strip()
    if not pid:
        return None
    for root in default_factory_sandbox_dirs():
        cand = root / pid
        if cand.is_dir() and (cand / "meta.json").is_file():
            return cand
        # golden demos live under app/factory/golden_demos
    app_dir = Path(__file__).resolve().parents[2]
    golden = app_dir / "factory" / "golden_demos" / pid
    if golden.is_dir() and (golden / "meta.json").is_file():
        return golden
    return None


def _load_meta(product_dir: Path) -> dict[str, Any]:
    path = product_dir / "meta.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _read_html(product_dir: Path, name: str) -> str:
    path = product_dir / name
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _tip(
    *,
    id: str,
    category: str,
    severity: str,
    message: str,
    capability: str | None = None,
    fix_label: str | None = None,
    done: bool = False,
) -> dict[str, Any]:
    action = None
    if capability:
        if is_live(capability):
            action = action_for(capability, cta_override=fix_label or "Fix")
        else:
            action = action_for(capability)
            if fix_label and action.get("kind") == "coming":
                action = {
                    **action,
                    "hint_label": fix_label,
                }
    return {
        "id": id,
        "category": category,
        "severity": severity,
        "message": message,
        "done": done,
        "action": action,
    }


def scan_website_tips(
    *,
    product_id: str | None = None,
    product_dir: Path | None = None,
    niche: str | None = None,
) -> dict[str, Any]:
    """Build tip list for Website Admin / Vector website_admin surface."""
    root = product_dir or (find_product_dir(product_id or "") if product_id else None)
    if root is None:
        return {
            "ok": False,
            "error": "website_product_not_found",
            "surface": "website_admin",
            "tips": [],
            "summary": {"total": 0, "open": 0, "done": 0},
            "honesty": "Vector never offers Fix for capabilities that are not live.",
        }

    meta = _load_meta(root)
    index = _read_html(root, "index.html")
    impressum = _read_html(root, "impressum.html")
    datenschutz = _read_html(root, "datenschutz.html")
    legal = meta.get("client_legal") if isinstance(meta.get("client_legal"), dict) else {}
    qg = meta.get("quality_gate") if isinstance(meta.get("quality_gate"), dict) else {}
    niche_label = niche or str(meta.get("niche") or meta.get("business_name") or "your site")

    tips: list[dict[str, Any]] = []

    # --- Legal ---
    has_impressum = bool(impressum.strip()) or (root / "impressum.html").is_file()
    missing_imp = bool(legal.get("missing_impressum")) or not has_impressum
    if missing_imp:
        tips.append(
            _tip(
                id="legal_impressum",
                category="legal",
                severity="high",
                message="Impressum fehlt oder ist unvollständig.",
                capability="website_impressum",
                fix_label="Create Impressum",
            )
        )
    else:
        tips.append(
            _tip(
                id="legal_impressum",
                category="legal",
                severity="ok",
                message="Impressum vorhanden.",
                done=True,
            )
        )

    has_ds = bool(datenschutz.strip()) or (root / "datenschutz.html").is_file()
    if not has_ds:
        tips.append(
            _tip(
                id="legal_datenschutz",
                category="legal",
                severity="high",
                message="Datenschutz-Seite fehlt.",
                capability="website_impressum",
                fix_label="Create Datenschutz",
            )
        )
    else:
        tips.append(
            _tip(
                id="legal_datenschutz",
                category="legal",
                severity="ok",
                message="Datenschutz vorhanden.",
                done=True,
            )
        )

    cookie = bool(
        re.search(r"cookie", index, re.I)
        or re.search(r"cookie", datenschutz, re.I)
        or legal.get("uses_analytics")
    )
    if not cookie:
        tips.append(
            _tip(
                id="legal_cookie",
                category="legal",
                severity="medium",
                message="Kein Cookie-Banner / Hinweis gefunden.",
                capability="website_impressum",
                fix_label="Add cookie notice",
            )
        )
    else:
        tips.append(
            _tip(
                id="legal_cookie",
                category="legal",
                severity="ok",
                message="Cookie-/Privacy-Hinweis erkannt.",
                done=True,
            )
        )

    # --- SEO ---
    title_m = re.search(r"<title[^>]*>(.*?)</title>", index, re.I | re.S)
    title = (title_m.group(1).strip() if title_m else "")
    if not title:
        tips.append(
            _tip(
                id="seo_title",
                category="seo",
                severity="high",
                message="Meta Title fehlt.",
                capability="website_meta",
                fix_label="Generate title",
            )
        )
    else:
        tips.append(
            _tip(
                id="seo_title",
                category="seo",
                severity="ok",
                message=f"Title gesetzt ({len(title)} Zeichen).",
                done=True,
            )
        )

    desc_m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        index,
        re.I,
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
        index,
        re.I,
    )
    desc = (desc_m.group(1).strip() if desc_m else "")
    if not desc:
        tips.append(
            _tip(
                id="seo_description",
                category="seo",
                severity="high",
                message="Meta Description fehlt.",
                capability="website_meta",
                fix_label="Generate description",
            )
        )
    else:
        tips.append(
            _tip(
                id="seo_description",
                category="seo",
                severity="ok",
                message="Meta Description vorhanden.",
                done=True,
            )
        )

    if not re.search(r"<h1\b", index, re.I):
        tips.append(
            _tip(
                id="seo_h1",
                category="seo",
                severity="medium",
                message="Kein H1 auf der Startseite.",
                capability="website_meta",
                fix_label="Add H1",
            )
        )
    else:
        tips.append(
            _tip(
                id="seo_h1",
                category="seo",
                severity="ok",
                message="H1 vorhanden.",
                done=True,
            )
        )

    imgs = re.findall(r"<img\b[^>]*>", index, re.I)
    missing_alt = sum(1 for tag in imgs if not re.search(r"\balt=", tag, re.I))
    if imgs and missing_alt:
        tips.append(
            _tip(
                id="seo_alt",
                category="seo",
                severity="medium",
                message=f"{missing_alt} Bild(er) ohne Alt-Text.",
                capability="website_meta",
                fix_label="Fix image alt",
            )
        )
    elif imgs:
        tips.append(
            _tip(
                id="seo_alt",
                category="seo",
                severity="ok",
                message="Bild-Alt-Attribute gesetzt.",
                done=True,
            )
        )

    if not re.search(r"og:title|property=[\"']og:", index, re.I):
        tips.append(
            _tip(
                id="seo_og",
                category="seo",
                severity="low",
                message="Open Graph Tags fehlen.",
                capability="website_meta",
                fix_label="Add Open Graph",
            )
        )
    else:
        tips.append(
            _tip(
                id="seo_og",
                category="seo",
                severity="ok",
                message="Open Graph erkannt.",
                done=True,
            )
        )

    # --- Performance ---
    if imgs and not re.search(r"loading=[\"']lazy[\"']", index, re.I):
        tips.append(
            _tip(
                id="perf_lazy",
                category="performance",
                severity="medium",
                message="Kein lazy loading bei Bildern erkannt.",
                capability="website_meta",
                fix_label="Enable lazy loading",
            )
        )
    elif imgs:
        tips.append(
            _tip(
                id="perf_lazy",
                category="performance",
                severity="ok",
                message="Lazy loading erkannt.",
                done=True,
            )
        )

    heavy = bool(re.search(r"fonts\.googleapis|font-awesome|bootstrap\.min", index, re.I))
    if heavy:
        tips.append(
            _tip(
                id="perf_fonts",
                category="performance",
                severity="low",
                message="Externe Fonts/CSS können die Ladezeit verlangsamen.",
                capability="website_meta",
                fix_label="Optimize fonts",
            )
        )

    qg_perf = qg.get("performance") if isinstance(qg.get("performance"), dict) else {}
    if qg_perf.get("passed") is False:
        tips.append(
            _tip(
                id="perf_qg",
                category="performance",
                severity="medium",
                message="Quality Gate: Performance-Checks nicht bestanden.",
                capability="website_meta",
                fix_label="Review performance",
            )
        )

    # --- Content ---
    if not re.search(r"contact-form|<form\b", index, re.I):
        tips.append(
            _tip(
                id="content_form",
                category="content",
                severity="high",
                message="Keine Kontaktformular gefunden.",
                capability="website_maps",
                fix_label="Add contact form",
            )
        )
    else:
        tips.append(
            _tip(
                id="content_form",
                category="content",
                severity="ok",
                message="Kontaktformular vorhanden.",
                done=True,
            )
        )

    cta = bool(
        re.search(r"btn|button|cta|Jetzt|Kontakt|Anfragen|Book|Call", index, re.I)
    )
    if not cta:
        tips.append(
            _tip(
                id="content_cta",
                category="content",
                severity="medium",
                message="Schwaches oder fehlendes CTA.",
                capability="website_meta",
                fix_label="Strengthen CTA",
            )
        )
    else:
        tips.append(
            _tip(
                id="content_cta",
                category="content",
                severity="ok",
                message="CTA erkannt.",
                done=True,
            )
        )

    text_len = len(re.sub(r"<[^>]+>", " ", index))
    if text_len < 800:
        tips.append(
            _tip(
                id="content_thin",
                category="content",
                severity="medium",
                message="Wenig Text auf der Startseite — SEO und Vertrauen leiden.",
                capability="website_meta",
                fix_label="Expand content",
            )
        )

    uses_maps = bool(legal.get("uses_maps")) or bool(
        re.search(r"google\.(com|de)/maps|maps\.google|openstreetmap", index, re.I)
    )
    if not uses_maps:
        tips.append(
            _tip(
                id="content_maps",
                category="content",
                severity="low",
                message=f'Auf der Seite könnte eine Karte fehlen (nische: {niche_label}).',
                capability="website_maps",
                fix_label="Add Google Maps",
            )
        )
    else:
        tips.append(
            _tip(
                id="content_maps",
                category="content",
                severity="ok",
                message="Karten-Hinweis / Maps erkannt.",
                done=True,
            )
        )

    open_tips = [t for t in tips if not t.get("done")]
    done_tips = [t for t in tips if t.get("done")]
    score = int(round(100 * len(done_tips) / max(1, len(tips))))

    return {
        "ok": True,
        "surface": "website_admin",
        "assistant": "Vector",
        "product_id": product_id or root.name,
        "product_dir": str(root),
        "niche": niche_label,
        "score": score,
        "tips": tips,
        "open_tips": open_tips,
        "summary": {
            "total": len(tips),
            "open": len(open_tips),
            "done": len(done_tips),
            "by_category": _by_category(tips),
        },
        "honesty": "Fix only when live; otherwise Coming R3.2 — Vector never fakes edits.",
        "note": "Website Admin Tips read Factory meta/HTML. In-app Fix expands with Website Editor.",
    }


def _by_category(tips: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for t in tips:
        cat = str(t.get("category") or "other")
        bucket = out.setdefault(cat, {"open": 0, "done": 0})
        if t.get("done"):
            bucket["done"] += 1
        else:
            bucket["open"] += 1
    return out


def build_website_admin_dialog(tips_payload: dict[str, Any]) -> dict[str, Any]:
    """Vector dialog for website_admin surface from tip scan."""
    if not tips_payload.get("ok"):
        return {
            "ok": True,
            "surface": "website_admin",
            "assistant": "Vector",
            "mode": "dialog_wizard",
            "dock": "right",
            "messages": [
                {
                    "role": "assistant",
                    "text": "Ich finde noch kein Website-Produkt zum Prüfen.\n\n"
                    "Sobald Ihre Landing fertig ist, prüfe ich Impressum, SEO und Inhalt.",
                }
            ],
            "actions": [
                {
                    "id": "open_products",
                    "kind": "navigate_href",
                    "href": "/client/products",
                    "label": "Meine Produkte",
                    "status": "live",
                }
            ],
            "tips": [],
            "honesty": tips_payload.get("honesty"),
        }

    open_tips = tips_payload.get("open_tips") or []
    score = tips_payload.get("score", 0)
    messages = [
        {
            "role": "assistant",
            "text": f"Website-Check für **{tips_payload.get('niche')}**.\n\n"
            f"Score: **{score}/100** · Offene Punkte: {len(open_tips)}.",
        }
    ]
    actions: list[dict[str, Any]] = []
    for tip in open_tips[:4]:
        messages.append(
            {
                "role": "assistant",
                "text": f"[{str(tip.get('category')).upper()}] {tip.get('message')}",
            }
        )
        act = tip.get("action")
        if isinstance(act, dict):
            actions.append(act)

    if not open_tips:
        messages.append(
            {
                "role": "assistant",
                "text": "Sieht gut aus — keine kritischen Tipps offen. "
                "Ich melde mich, wenn neue Module (Editor-Fixes) live gehen.",
            }
        )

    return {
        "ok": True,
        "surface": "website_admin",
        "assistant": "Vector",
        "mode": "dialog_wizard",
        "dock": "right",
        "messages": messages,
        "actions": actions,
        "website_tips": tips_payload,
        "honesty": tips_payload.get("honesty"),
    }
