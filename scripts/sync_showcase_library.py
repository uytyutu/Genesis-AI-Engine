#!/usr/bin/env python3
"""Bootstrap Visual Experience Product Registry under showcases/<niche>/products/.

Usage (repo root):
  py -3.12 scripts/sync_showcase_library.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.factory.research_3d.visual_experience_registry import (  # noqa: E402
    ENGINE_LABEL,
    ensure_product_tree_example,
    list_showcase_niches,
    rebuild_library_manifest,
)

DENTAL_PRODUCTS = [
    {
        "id": "implant",
        "score": 98,
        "premium": True,
        "specializations": ["implantology", "oral_surgery", "implant"],
        "tags": ["implant", "tooth", "crown", "titanium"],
        "label_de": "Moderne Zahnmedizin — zum Anfassen",
        "label_en": "Modern dentistry — hands-on",
        "copy_model": True,
        "client_facing_3d": False,
    },
    {
        "id": "tooth",
        "score": 92,
        "premium": True,
        "specializations": ["general_dentistry", "prophylaxis", "aesthetic"],
        "tags": ["tooth", "enamel", "crown"],
        "label_de": "Zahntechnik verständlich erklärt",
        "label_en": "Dental tech made clear",
        "client_facing_3d": False,
    },
    {
        "id": "scanner",
        "score": 96,
        "premium": True,
        "specializations": ["diagnostics", "general_dentistry", "digital"],
        "tags": ["scanner", "digital", "tech"],
        "label_de": "Digitale Diagnostik",
        "label_en": "Digital diagnostics",
        "client_facing_3d": False,
    },
    {
        "id": "aligners",
        "score": 90,
        "premium": True,
        "specializations": ["orthodontics", "aligners", "ortho"],
        "tags": ["aligners", "tooth", "ortho"],
        "label_de": "Zahnstellung & moderne Systeme",
        "label_en": "Alignment & modern systems",
        "client_facing_3d": False,
    },
]

AUTO_PRODUCTS = [
    {
        "id": "engine",
        "score": 97,
        "premium": True,
        "specializations": ["engine", "motor", "powertrain"],
        "tags": ["engine", "motor", "workshop"],
        "label_de": "Antriebstechnik zum Greifen nah",
        "label_en": "Powertrain you can grasp",
        "copy_model": True,
        "client_facing_3d": False,
    },
    {
        "id": "turbo",
        "score": 94,
        "premium": True,
        "specializations": ["turbo", "tuning", "performance"],
        "tags": ["turbo", "engine"],
        "label_de": "Leistung & Aufladung",
        "label_en": "Boost & performance",
        "client_facing_3d": False,
    },
    {
        "id": "brakes",
        "score": 91,
        "premium": True,
        "specializations": ["brakes", "safety", "service"],
        "tags": ["brakes", "workshop"],
        "label_de": "Sicherheit, die man sieht",
        "label_en": "Safety you can see",
        "client_facing_3d": False,
    },
    {
        "id": "suspension",
        "score": 88,
        "premium": True,
        "specializations": ["suspension", "chassis", "service"],
        "tags": ["suspension", "workshop"],
        "label_de": "Fahrwerk & Haltung",
        "label_en": "Chassis & ride",
        "client_facing_3d": False,
    },
]

ENERGY_PRODUCTS = [
    {
        "id": "solar_panel",
        "score": 97,
        "premium": True,
        "specializations": ["solar", "pv", "energy"],
        "tags": ["solar", "panel", "energy"],
        "label_de": "Energie, die sichtbar wird",
        "label_en": "Energy made visible",
        "copy_model": True,
        "client_facing_3d": False,
    },
    {
        "id": "battery",
        "score": 93,
        "premium": True,
        "specializations": ["storage", "battery", "energy"],
        "tags": ["battery", "storage"],
        "label_de": "Speicher & Unabhängigkeit",
        "label_en": "Storage & independence",
        "client_facing_3d": False,
    },
    {
        "id": "inverter",
        "score": 90,
        "premium": True,
        "specializations": ["inverter", "solar", "installation"],
        "tags": ["inverter", "energy"],
        "label_de": "Wechselrichter & Systemtechnik",
        "label_en": "Inverter & system tech",
        "client_facing_3d": False,
    },
]

BEAUTY_PRODUCTS = [
    {
        "id": "device",
        "score": 94,
        "premium": True,
        "specializations": ["device", "treatment", "clinic"],
        "tags": ["device", "beauty"],
        "label_de": "Geräte & Methoden",
        "label_en": "Devices & methods",
        "copy_model": True,
        "client_facing_3d": False,
    },
    {
        "id": "laser",
        "score": 92,
        "premium": True,
        "specializations": ["laser", "aesthetic"],
        "tags": ["laser", "beauty"],
        "label_de": "Präzision in der Praxis",
        "label_en": "Precision in the studio",
        "client_facing_3d": False,
    },
    {
        "id": "chair",
        "score": 85,
        "premium": True,
        "specializations": ["salon", "comfort"],
        "tags": ["chair", "beauty"],
        "label_de": "Ambiente & Komfort",
        "label_en": "Ambience & comfort",
        "client_facing_3d": False,
    },
]

BOOTSTRAP = {
    "dental": DENTAL_PRODUCTS,
    "auto": AUTO_PRODUCTS,
    "energy": ENERGY_PRODUCTS,
    "beauty": BEAUTY_PRODUCTS,
}


def main() -> int:
    for niche, products in BOOTSTRAP.items():
        if niche not in list_showcase_niches():
            print(f"skip missing niche: {niche}")
            continue
        ensure_product_tree_example(niche, products)
        print(f"  products ok: {niche} → {[p['id'] for p in products]}")

    # Ensure every other niche has at least products/default
    for niche in list_showcase_niches():
        if niche in BOOTSTRAP:
            continue
        ensure_product_tree_example(
            niche,
            [
                {
                    "id": "default",
                    "score": 80,
                    "premium": True,
                    "specializations": [niche],
                    "tags": [niche, "tech"],
                    "label_de": niche,
                    "label_en": niche,
                    "copy_model": True,
                    "client_facing_3d": False,
                }
            ],
        )
        print(f"  products ok: {niche} → ['default']")

    manifest = rebuild_library_manifest()
    print(f"{ENGINE_LABEL}: niches={len(manifest.get('niches') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
