"""Commercial Acceptance Gate + UX Quality Gate (Phase D Proof).

Philosophy: product level must sell — not page count.
Empty UI blocks must not ship. Premium must earn 699 € visually (manual check listed).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.integration.demo_gallery_audit import (
    audit_demo_freshness,
    build_demo_gallery_snapshot,
)


def audit_ux_quality_html(html: str, *, label: str = "site") -> dict[str, Any]:
    """Fail on empty CTAs, empty links, empty cards, scroll-to-missing anchors.

    Any empty block = FAIL (not a warning). Client must never see placeholders.
    """
    issues: list[str] = []
    for _ in re.finditer(r"<a\b([^>]*)>(\s*)</a>", html, re.I | re.S):
        issues.append(f"{label}: empty <a> link")
    for _ in re.finditer(r"<button\b([^>]*)>(\s*)</button>", html, re.I | re.S):
        issues.append(f"{label}: empty <button>")
    empty_href = re.findall(r"<a\b[^>]*\bhref=[\"']\s*[\"'][^>]*>", html, re.I)
    if empty_href:
        issues.append(f"{label}: {len(empty_href)} empty href attribute(s)")
    ids = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", html, re.I))
    for frag in re.findall(r"\bhref=[\"']#([A-Za-z][\w\-]*)[\"']", html, re.I):
        if frag and frag not in ids and frag not in ("top",):
            issues.append(f"{label}: dead anchor #{frag}")
    # Truly empty hero: tagged hero with almost no visible text
    for m in re.finditer(
        r"<(header|section|div)\b[^>]*class=[\"'][^\"']*\bhero\b[^\"']*[\"'][^>]*>(.*?)</\1>",
        html,
        re.I | re.S,
    ):
        inner = re.sub(r"<[^>]+>", " ", m.group(2))
        inner = re.sub(r"\s+", " ", inner).strip()
        if len(inner) < 24:
            issues.append(f"{label}: empty hero container")
            break
    # Empty cards / placeholders
    for m in re.finditer(
        r"<(article|div|li)\b[^>]*class=[\"'][^\"']*\b(?:card|service-card|product-card|benefit)[^\"']*[\"'][^>]*>(.*?)</\1>",
        html,
        re.I | re.S,
    ):
        inner = re.sub(r"<[^>]+>", " ", m.group(2))
        inner = re.sub(r"\s+", " ", inner).strip()
        if len(inner) < 8:
            issues.append(f"{label}: empty card block")
            break
    # Visible copy only — ignore HTML attribute placeholder="…"
    visible = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    visible = re.sub(r"<style\b[^>]*>.*?</style>", " ", visible, flags=re.I | re.S)
    visible = re.sub(r"\splaceholder\s*=\s*(\"[^\"]*\"|'[^']*')", " ", visible, flags=re.I)
    visible = re.sub(r"<[^>]+>", " ", visible)
    visible_low = re.sub(r"\s+", " ", visible).lower()
    for ph in (
        "lorem ipsum",
        "coming soon",
        "your text here",
        "policy placeholder",
        "todo:",
        "{{",
    ):
        if ph in visible_low:
            issues.append(f"{label}: placeholder copy «{ph}»")
            break
    else:
        # Bare word "placeholder" in visible text (not input hints)
        if re.search(r"\bplaceholder\b", visible_low):
            issues.append(f"{label}: placeholder copy «placeholder»")
    ok = not issues
    return {
        "id": "ux_quality_gate",
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "issues": issues[:30],
        "ssot_ru": (
            "Любой пустой блок = FAIL сборки. "
            "Пустые кнопки, ссылки, Hero, карточки, placeholder и мёртвые якоря запрещены."
        ),
    }


def audit_ux_quality_demo_gallery(root: Path | None = None) -> dict[str, Any]:
    from app.integration.demo_gallery_audit import (
        PREMIUM_GALLERY_NICHES,
        TIER_COMPARE_NICHES,
        WEBSITE_REQUIRED,
        _previews_root,
    )

    root = root or _previews_root()
    all_issues: list[str] = []
    checked = 0
    for tier, niches in (
        ("basic", TIER_COMPARE_NICHES),
        ("business", WEBSITE_REQUIRED),
        ("premium", PREMIUM_GALLERY_NICHES),
    ):
        for niche in niches:
            path = root / "sites" / tier / niche / "index.html"
            if not path.is_file():
                continue
            checked += 1
            html = path.read_text(encoding="utf-8", errors="replace")
            r = audit_ux_quality_html(html, label=f"{tier}/{niche}")
            all_issues.extend(r.get("issues") or [])
    ok = not all_issues
    return {
        "id": "ux_quality_gate",
        "title": "UX Quality Gate",
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "mark": "🟢" if ok else "🔴",
        "checked": checked,
        "issues": all_issues[:40],
        "ssot_ru": (
            "Нет пустых кнопок/ссылок/Hero; якоря ведут на существующие секции."
        ),
    }


def build_commercial_acceptance_gate() -> dict[str, Any]:
    """CEO checklist before Production / ads. Mix of auto checks + manual Premium accept."""
    gallery = build_demo_gallery_snapshot()
    freshness = gallery.get("demo_freshness_gate") or audit_demo_freshness()
    ux = audit_ux_quality_demo_gallery()
    vqg = gallery.get("visual_quality_gate") or {}
    try:
        from app.factory.visual_intelligence.ai_design_director import (
            audit_design_director_gallery,
        )
        from app.factory.visual_intelligence.studio.ceo_blind_test import (
            run_ceo_blind_test,
        )

        director = audit_design_director_gallery()
        blind = run_ceo_blind_test()
    except Exception as exc:  # noqa: BLE001
        director = {
            "ok": False,
            "status": "FAIL",
            "error": str(exc)[:160],
            "samples": [],
        }
        blind = {
            "ok": False,
            "status": "FAIL",
            "error": str(exc)[:160],
            "rebuild_premium_luxury": True,
        }

    premium_sample = next(
        (s for s in (director.get("samples") or []) if s.get("package_id") == "premium"),
        {},
    )
    pf = (premium_sample.get("scores") or {}).get("premium_feeling")

    # Commercial Readiness on Premium dental demo (master KPI proxy for CEO)
    crs: dict[str, Any] = {"ok": False, "overall_commercial": 0, "commercial_ready": False}
    try:
        from app.factory.visual_intelligence.studio.commercial_readiness import (
            score_commercial_readiness,
        )
        from app.integration.demo_gallery_audit import _previews_root

        prem_path = _previews_root() / "sites" / "premium" / "dental" / "index.html"
        if prem_path.is_file():
            crs = score_commercial_readiness(
                prem_path.read_text(encoding="utf-8", errors="replace"),
                package_id="premium",
                niche="dental",
                market_code="DE",
                luxury_mode=True,
            )
            crs["ok"] = bool(crs.get("commercial_ready"))
    except Exception as exc:  # noqa: BLE001
        crs = {"ok": False, "error": str(exc)[:160], "commercial_ready": False}

    # CEO Visual Review — filesystem gate after every Demo Gallery rebuild
    visual: dict[str, Any] = {"ok": False, "status": "FAIL", "fail_count": 0}
    try:
        from app.integration.ceo_visual_review import run_ceo_visual_review

        visual = run_ceo_visual_review()
    except Exception as exc:  # noqa: BLE001
        visual = {
            "ok": False,
            "status": "FAIL",
            "fail_count": 1,
            "error": str(exc)[:160],
            "kpi_ru": "Показал бы я этот сайт своему первому клиенту без стыда?",
        }

    items = [
        {
            "id": "starter_modern",
            "label": "Starter · modern / adaptive / mobile",
            "ok": bool(freshness.get("ok")),
            "auto": True,
            "detail": "Demo Freshness includes basic/* with correct data-tier",
        },
        {
            "id": "business_visual",
            "label": "Business · Visual Pack / Hero / motion",
            "ok": bool(vqg.get("ok")) and bool(freshness.get("ok")),
            "auto": True,
            "detail": "VQ Gate + fresh business demos",
        },
        {
            "id": "design_director",
            "label": "5s Acceptance · Starter < Business < Premium (no price tags)",
            "ok": bool(director.get("ok")) or bool((director.get("acceptance_5s") or {}).get("pass")),
            "auto": True,
            "detail": (
                f"director={director.get('status')} 5s={ (director.get('acceptance_5s') or {}).get('pass') } "
                f"sim_BP={ (director.get('creative_score') or {}).get('business_premium_similarity_pct') } "
                f"FI_premium={ (premium_sample.get('scores') or {}).get('first_impression') } "
                f"PF={pf}"
            ),
        },
        {
            "id": "ceo_blind_test",
            "label": "CEO Blind Test · 5s without labels/prices",
            "ok": bool(blind.get("ok")) or bool(blind.get("identified_correctly")),
            "auto": True,
            "detail": (
                f"{blind.get('status')} confidence={blind.get('confidence_pct')}% "
                f"action={blind.get('action')} "
                f"rebuild_premium={blind.get('rebuild_premium_luxury')}"
            ),
        },
        {
            "id": "ceo_visual_review",
            "label": "CEO Visual Review · dental ladder + store tiers",
            "ok": bool(visual.get("ok")),
            "auto": True,
            "detail": (
                f"{visual.get('status')} fails={visual.get('fail_count')} "
                f"KPI={visual.get('kpi_ru')}"
            ),
        },
        {
            "id": "commercial_readiness",
            "label": "Commercial Readiness Score ≥ 90 → Commercial Ready",
            "ok": bool(crs.get("commercial_ready") or crs.get("ok")),
            "auto": True,
            "detail": (
                f"overall={crs.get('overall_commercial')} "
                f"scores={crs.get('scores')} status={crs.get('status') or crs.get('label')}"
            ),
        },
        {
            "id": "premium_wow",
            "label": "Premium · Luxury Mode wow (would you pay 699 €?)",
            "ok": bool(blind.get("luxury_markers_in_premium"))
            or int((premium_sample.get("scores") or {}).get("first_impression") or 0) >= 80,
            "auto": True,
            "detail": (
                f"luxury_html={blind.get('luxury_markers_in_premium')} "
                f"FI={ (premium_sample.get('scores') or {}).get('first_impression') } "
                f"— FAIL → Premium Luxury Mode rebuild"
            ),
        },
        {
            "id": "store_account",
            "label": "Store · Login / Register / Customer cabinet / Cart / Checkout",
            "ok": False,
            "auto": False,
            "detail": "Store Starter must expose customer auth — pending product proof",
        },
        {
            "id": "gallery_fresh",
            "label": "Gallery · fresh · real packages",
            "ok": gallery.get("status") in ("PASS",) and bool(freshness.get("ok")),
            "auto": True,
            "detail": f"gallery={gallery.get('status')} freshness={freshness.get('status')}",
        },
        {
            "id": "ux_empty",
            "label": "UX · no empty CTAs / dead anchors",
            "ok": bool(ux.get("ok")),
            "auto": True,
            "detail": f"checked={ux.get('checked')}",
        },
    ]
    for it in items:
        it["mark"] = "🟢" if it["ok"] else ("🟡" if not it["auto"] else "🔴")

    auto_ok = all(i["ok"] for i in items if i["auto"])
    all_ok = all(i["ok"] for i in items)
    return {
        "id": "commercial_acceptance_gate",
        "title": "Commercial Acceptance Gate",
        "ok": all_ok,
        "auto_ok": auto_ok,
        "status": "PASS" if all_ok else ("AUTO_PASS" if auto_ok else "FAIL"),
        "mark": "🟢" if all_ok else ("🟡" if auto_ok else "🔴"),
        "items": items,
        "ux_quality_gate": ux,
        "demo_freshness_gate": freshness,
        "ai_design_director": director,
        "ceo_blind_test": blind,
        "ceo_visual_review": visual,
        "commercial_readiness": crs,
        "policy_ru": (
            "Digital Creative Studio — не генератор HTML. "
            "Главный KPI: показал бы я это первому клиенту без стыда? "
            "Любое изменение Visual Studio → пересборка Demo Gallery → CEO Visual Review. "
            "Horizon — только после Factory + Store."
        ),
        "next_ru": (
            "CEO Visual Review PASS + глазами «да, без стыда» → Production. "
            "Иначе только визуальная генерация, не новые модули."
        ),
    }
