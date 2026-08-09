#!/usr/bin/env python3
"""Seed local commercial stock photos for Premium Store (offline rebuilds).

Downloads curated Unsplash crop URLs into store_factory/stock/{category}/.
Run once with network; rebuilds then copy locally.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOCK = ROOT / "dashboard" / "backend" / "app" / "factory" / "store_factory" / "stock"

# Curated Unsplash photo IDs → commercial product / lifestyle look
PACKS: dict[str, dict[str, list[str]]] = {
    "clothing": {
        "hero": ["1523381210434-271e8be1f52b"],
        "banner": ["1441986300917-64674bd600d8"],
        "products": [
            "1521572163474-6864f9cf17ab",
            "1515886657613-9f3515b0c78f",
            "1551028719-00167b16eac5",
            "1542291026-7eec264c27ff",
            "1562157873-818bc0726f68",
            "1576566588028-4147f3842f27",
            "1434389677669-e08b4cac3107",
            "1489980557514-251d61aad3c3",
        ],
    },
    "electronics": {
        "hero": ["1519389950473-47ba0277781c"],
        "banner": ["1518770660439-4636190af475"],
        "products": [
            "1505740420928-5e560c06d30e",
            "1511707171634-5f897ff02aa9",
            "1498049794561-7780e7231661",
            "1587825140708-dfaf72ae4b04",
            "1527443224154-c4a3942d3acf",
            "1593640408182-31c70c8268f5",
            "15442476543-7a7c5850c6ab",
            "1555617981-dac3880eac6e",
        ],
    },
    "beauty": {
        "hero": ["1596462502278-27bfdd403348"],
        "banner": ["1522335789203-aabd1fc54bc9"],
        "products": [
            "1571781926291-c77df8097c2f",
            "1598440947619-2ffae4a5e6c3",
            "1512496015851-a90fb38ba796",
            "1631730486572-226b1b2e9ee4",
            "1620916569881-f0f1c4c0a0c0",
            "1612817288484-6f916006741a",
            "1583241800698-9cbe1c5c8f0c",
            "1596755094514-f87e34085b2c",
        ],
    },
    "furniture": {
        "hero": ["1586023492125-27b2c045efd7"],
        "banner": ["1555041469-a586c61ea9bc"],
        "products": [
            "1493663284031-b7e3aefcae8e",
            "1567016431669-e413954d45fd",
            "1538688522736-a6c99b0d2e0e",
            "1505693416388-ac5ce068fe85",
            "1555041469-a586c61ea9bc",
            "1618220179428-22790b461013",
            "1616486338812-3dadae4b4ace",
            "1592078615290-033ee584e267",
        ],
    },
    "accessories": {
        "hero": ["1523170335258-f5ed11844a49"],
        "banner": ["1611652022419-a9419f74343d"],
        "products": [
            "1524592094714-0f0654e20314",
            "1622434641406-a158123450f0",
            "1606760227091-3dd693630599",
            "1572635191097-a76b6065b439",
            "1617038260897-43d00f2c5f8d",
            "1548036328-c9fa89d012fa",
            "1553062407-98eeb64c6a62",
            "1611652022419-a9419f74343d",
        ],
    },
}


def _url(photo_id: str, *, w: int, h: int) -> str:
    return (
        f"https://images.unsplash.com/photo-{photo_id}"
        f"?auto=format&fit=crop&w={w}&h={h}&q=80"
    )


def _fetch(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "VirtusCore-CommercialGallery/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) < 2000:
            return False
        dest.write_bytes(data)
        print(f"OK {dest.relative_to(STOCK.parent)} ({len(data)}B)")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {dest.name}: {exc}")
        return False


def main() -> int:
    ok = 0
    fail = 0
    for cat, pack in PACKS.items():
        for photo in pack.get("hero") or []:
            if _fetch(_url(photo, w=1600, h=900), STOCK / cat / "hero.jpg"):
                ok += 1
            else:
                fail += 1
        for photo in pack.get("banner") or []:
            if _fetch(_url(photo, w=1600, h=700), STOCK / cat / "banner.jpg"):
                ok += 1
            else:
                fail += 1
        for i, photo in enumerate(pack.get("products") or [], start=1):
            if _fetch(_url(photo, w=900, h=1120), STOCK / cat / f"product_{i}.jpg"):
                ok += 1
            else:
                fail += 1
    # Alias fashion → clothing for STORE_CATEGORY clothing
    fashion = STOCK / "fashion"
    clothing = STOCK / "clothing"
    if clothing.is_dir():
        fashion.mkdir(parents=True, exist_ok=True)
        for src in clothing.glob("*.jpg"):
            dest = fashion / src.name
            if not dest.exists():
                dest.write_bytes(src.read_bytes())
    print(f"done ok={ok} fail={fail} stock={STOCK}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
