# -*- coding: utf-8 -*-
"""Live-sync merchant catalog → published shop HTML.

Closes the gap where products.json updated but storefront stayed stale.
Does not invent payment/shipping integrations.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from app.integration.website_admin.cinematic_control import (
    ORIGINAL_NAME,
    ensure_control_point_original,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fmt_price(value: Any) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        n = 0.0
    if abs(n - round(n)) < 1e-9:
        return f"{int(round(n))} €"
    return f"{n:.2f} €".replace(".", ",")


def _product_card(p: dict[str, Any], idx: int) -> str:
    pid = escape(str(p.get("id") or f"p{idx}"))
    title = escape(str(p.get("title") or p.get("name") or f"Product {idx}"))
    cat = escape(str(p.get("category") or "Shop"))
    price = float(p.get("price") or 0)
    price_label = escape(_fmt_price(price))
    img = ""
    images = p.get("images") if isinstance(p.get("images"), list) else []
    if images and isinstance(images[0], dict):
        # Prefer relative storefront path if present
        img = str(images[0].get("storefront_path") or images[0].get("url") or "")
    if not img:
        img = f"assets/products/p{idx:02d}.jpg"
    img = escape(img)
    status = str(p.get("status") or "active").lower()
    hidden = ' style="display:none"' if status in {"draft", "archived", "hidden"} else ""
    return (
        f'<article class="product" id="{pid}" data-cat="{cat}"{hidden}>'
        f'<a href="#{pid}"><img src="{img}" alt="" /></a>'
        f'<p class="cat">{cat}</p>'
        f"<h3>{title}</h3>"
        f'<p class="price">{price_label}</p>'
        f'<button type="button" class="cta add" data-name="{title}" data-price="{price}">'
        f"In den Warenkorb</button></article>"
    )


def sync_catalog_to_storefront(
    product_dir: Path,
    products: list[dict[str, Any]],
) -> dict[str, Any]:
    """Rewrite #grid product cards from catalog SSOT; keep shell/theme HTML."""
    product_dir = Path(product_dir)
    html_path = product_dir / "index.html"
    if not html_path.is_file():
        raise ValueError("storefront_html_missing")

    ensure_control_point_original(product_dir)
    visible = [p for p in products if isinstance(p, dict)]
    cards = "\n".join(_product_card(p, i + 1) for i, p in enumerate(visible))
    html = html_path.read_text(encoding="utf-8", errors="replace")

    # Update catalog heading count if present
    html = re.sub(
        r"(Katalog\s*[·•]\s*)\d+(\s*Box)",
        rf"\g<1>{len(visible)}\2",
        html,
        count=1,
    )

    if 'id="grid"' in html:
        html = re.sub(
            r'(<div class="grid" id="grid">)(.*?)(</div>)',
            rf"\1{cards}\3",
            html,
            count=1,
            flags=re.S,
        )
    else:
        # Append before cart/footer as last resort
        inject = f'<div class="grid" id="grid">{cards}</div>'
        if "</main>" in html:
            html = html.replace("</main>", inject + "</main>", 1)
        else:
            html += inject

    # Also patch inline data-price by title for shells without #grid rewrite success
    for p in visible:
        title = str(p.get("title") or p.get("name") or "").strip()
        if not title:
            continue
        price = float(p.get("price") or 0)
        price_label = _fmt_price(price)
        # data-price on matching button
        html = re.sub(
            rf'(data-name="{re.escape(title)}"\s+data-price=")[^"]+(")',
            rf"\g<1>{price}\2",
            html,
        )
        # price paragraph immediately after matching h3 (best-effort)
        html = re.sub(
            rf'(<h3>\s*{re.escape(title)}\s*</h3>\s*<p class="price">)[^<]+(</p>)',
            rf"\g<1>{price_label}\2",
            html,
            count=1,
        )

    # stamp live sync
    stamp = f"<!-- virtus_live_sync {_now()} products={len(visible)} -->"
    if "virtus_live_sync" in html:
        html = re.sub(r"<!-- virtus_live_sync.*?-->", stamp, html, count=1)
    else:
        html = html.replace("</body>", f"{stamp}\n</body>", 1)

    html_path.write_text(html, encoding="utf-8")

    # Persist catalog snapshot beside storefront for restore
    snap = product_dir / "catalog_ssot.json"
    snap.write_text(
        json.dumps(
            {"updated_at": _now(), "products": visible},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "live_sync": True,
        "products": len(visible),
        "updated_at": _now(),
        "path": str(html_path),
    }


def restore_shop_original(product_dir: Path) -> dict[str, Any]:
    product_dir = Path(product_dir)
    src = product_dir / "versions" / ORIGINAL_NAME
    if not (src / "_control_point.json").is_file():
        raise ValueError("original_missing")
    for item in list(product_dir.iterdir()):
        if item.name == "versions":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except OSError:
                pass
    for item in src.iterdir():
        if item.name == "_control_point.json":
            continue
        target = product_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    return {"ok": True, "restored": ORIGINAL_NAME, "restored_at": _now()}
