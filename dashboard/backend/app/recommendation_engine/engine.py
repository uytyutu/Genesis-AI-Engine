"""Match confirmed needs → official offers from any source."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from app.recommendation_engine.catalog import load_offers
from app.recommendation_engine.needs import detect_confirmed_needs

Audience = Literal["client", "owner"]


def _pick_lang(locale: str) -> str:
    lang = (locale or "en").strip().lower().split("-")[0]
    if lang in ("ru", "uk"):
        return "ru"
    if lang == "de":
        return "de"
    return "en"


def _title(offer: dict[str, Any], lang: str) -> str:
    return str(
        offer.get(f"title_{lang}")
        or offer.get("title_en")
        or offer.get("title_ru")
        or offer.get("id")
        or "Solution"
    )


def _need_label(need: dict[str, Any], lang: str) -> str:
    return str(need.get(f"label_{lang}") or need.get("label_en") or need.get("id"))


def _need_why(need: dict[str, Any], lang: str) -> str:
    return str(need.get(f"why_{lang}") or need.get("why_en") or "")


def build_recommended_solutions(
    *,
    html: str = "",
    flags: dict[str, Any] | None = None,
    fetch_ok: bool = True,
    locale: str = "en",
    memory_dir: Path | None = None,
    audience: Audience = "client",
    confirmed_needs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Recommendation appears only if need confirmed AND an enabled official offer exists.
    No commission amounts. No simulation.
    """
    lang = _pick_lang(locale)
    needs = confirmed_needs
    if needs is None:
        needs = detect_confirmed_needs(html=html, flags=flags, fetch_ok=fetch_ok)

    offers = load_offers(memory_dir)
    solutions: list[dict[str, Any]] = []
    for need in needs:
        if not need.get("confirmed"):
            continue
        need_id = str(need.get("id") or "")
        matches = [
            o
            for o in offers
            if o.get("enabled")
            and need_id in (o.get("need_ids") or [])
            and str(o.get("official_url") or "").strip().startswith("http")
        ]
        for offer in matches:
            row: dict[str, Any] = {
                "id": offer["id"],
                "need_id": need_id,
                "need_label": _need_label(need, lang),
                "title": _title(offer, lang),
                "why": _need_why(need, lang),
                "official_url": str(offer["official_url"]).strip(),
                "source_label": str(offer.get("source_label") or offer.get("source_id") or ""),
            }
            if audience == "owner":
                row["ceo_only"] = {
                    "source_id": offer.get("source_id"),
                    "offer_id": offer.get("id"),
                    "commission_policy_ru": (
                        "Комиссия — внутренний вопрос. Клиенту не показывать. "
                        "В Ledger только после CONFIRMED выплаты Digistore24/партнёра — "
                        "никогда от факта рекомендации."
                    ),
                    "reality_chain_ru": (
                        "потребность → рекомендация → официальная ссылка → "
                        "продажа → CONFIRMED комиссия → Ledger"
                    ),
                }
            solutions.append(row)

    return {
        "title_ru": "Рекомендуемые решения",
        "title_de": "Empfohlene Lösungen",
        "title_en": "Recommended solutions",
        "title": {
            "ru": "Рекомендуемые решения",
            "de": "Empfohlene Lösungen",
            "en": "Recommended solutions",
        }.get(lang, "Recommended solutions"),
        "rule_ru": (
            "Показываем только после подтверждённой потребности аудита. "
            "Официальные ссылки. Без симуляции комиссий."
        ),
        "confirmed_needs": [
            {"id": n["id"], "label": _need_label(n, lang), "why": _need_why(n, lang)}
            for n in needs
            if n.get("confirmed")
        ],
        "solutions": solutions,
        "count": len(solutions),
    }


def public_solutions_only(block: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop owner/ceo fields before client or commercial API sanitize."""
    if not isinstance(block, dict):
        return None
    solutions = []
    for s in block.get("solutions") or []:
        if not isinstance(s, dict):
            continue
        solutions.append(
            {
                "id": s.get("id"),
                "need_id": s.get("need_id"),
                "need_label": s.get("need_label"),
                "title": s.get("title"),
                "why": s.get("why"),
                "official_url": s.get("official_url"),
                "source_label": s.get("source_label"),
            }
        )
    return {
        "title": block.get("title"),
        "rule_ru": block.get("rule_ru"),
        "confirmed_needs": block.get("confirmed_needs") or [],
        "solutions": solutions,
        "count": len(solutions),
    }
