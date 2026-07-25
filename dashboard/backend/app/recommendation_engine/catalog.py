"""Pluggable offer catalog — Digistore24 is one source among many."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_FILE = "recommendation_catalog.json"

# Official Digistore marketplace search URLs (not invented product IDs).
# CEO replaces with specific affiliate/promo product links in memory JSON.
_DEFAULT_OFFERS: list[dict[str, Any]] = [
    {
        "id": "digistore24_crm",
        "need_ids": ["crm"],
        "source_id": "digistore24",
        "source_label": "Digistore24",
        "enabled": True,
        "title_ru": "CRM-решение",
        "title_de": "CRM-Lösung",
        "title_en": "CRM solution",
        "official_url": "https://www.digistore24.com/en/search?q=CRM",
        "note_ru": "Официальный каталог Digistore24. Замените URL на конкретную promo-ссылку в recommendation_catalog.json.",
    },
    {
        "id": "digistore24_booking",
        "need_ids": ["online_booking"],
        "source_id": "digistore24",
        "source_label": "Digistore24",
        "enabled": True,
        "title_ru": "Онлайн-запись / booking",
        "title_de": "Online-Terminbuchung",
        "title_en": "Online booking",
        "official_url": "https://www.digistore24.com/en/search?q=booking",
        "note_ru": "Официальный каталог Digistore24. Уточните продукт под нишу клиента.",
    },
    {
        "id": "digistore24_email",
        "need_ids": ["email_marketing"],
        "source_id": "digistore24",
        "source_label": "Digistore24",
        "enabled": True,
        "title_ru": "Email-автоматизация",
        "title_de": "E-Mail-Automation",
        "title_en": "Email automation",
        "official_url": "https://www.digistore24.com/en/search?q=email+marketing",
        "note_ru": "Официальный каталог Digistore24.",
    },
    # Slots for future partners / Virtus products — disabled until real URLs exist.
    {
        "id": "virtus_core_crm",
        "need_ids": ["crm"],
        "source_id": "virtus_core",
        "source_label": "Virtus Core",
        "enabled": False,
        "title_ru": "CRM Virtus Core",
        "title_de": "Virtus Core CRM",
        "title_en": "Virtus Core CRM",
        "official_url": "",
        "note_ru": "Собственный продукт — включить, когда будет готов.",
    },
    {
        "id": "partner_a_crm",
        "need_ids": ["crm"],
        "source_id": "partner_a",
        "source_label": "Partner A",
        "enabled": False,
        "title_ru": "CRM Partner A",
        "title_de": "Partner A CRM",
        "title_en": "Partner A CRM",
        "official_url": "",
        "note_ru": "Слот партнёра — добавить официальный URL без правки аудита.",
    },
]


def load_offers(memory_dir: Path | None = None) -> list[dict[str, Any]]:
    offers = [dict(o) for o in _DEFAULT_OFFERS]
    if memory_dir is None:
        return offers
    path = memory_dir / CATALOG_FILE
    if not path.is_file():
        return offers
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return offers
    extra = raw.get("offers") if isinstance(raw, dict) else raw
    if not isinstance(extra, list):
        return offers
    by_id = {o["id"]: o for o in offers}
    for row in extra:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        oid = str(row["id"])
        if oid in by_id:
            by_id[oid] = {**by_id[oid], **row}
        else:
            by_id[oid] = dict(row)
    return list(by_id.values())


def save_default_catalog(memory_dir: Path) -> Path:
    path = memory_dir / CATALOG_FILE
    if path.is_file():
        return path
    payload = {
        "_comment": (
            "Universal Recommendation Engine catalog. "
            "Add Digistore promo URLs / Partner / Virtus offers without changing audit code. "
            "Never put commission amounts in client-facing fields."
        ),
        "offers": _DEFAULT_OFFERS,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
