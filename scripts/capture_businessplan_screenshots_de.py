#!/usr/bin/env python3
"""Capture Virtus Core screenshots in German (DE) for the business plan PDF."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "business" / "assets" / "screenshots"

PAGES = [
    ("01_home.png", "https://beta.genesis-ai-engine.com/site?market=DE"),
    ("02_order.png", "https://beta.genesis-ai-engine.com/order?package=basic&market=DE"),
    ("03_impressum.png", "https://beta.genesis-ai-engine.com/impressum"),
    ("04_datenschutz.png", "https://beta.genesis-ai-engine.com/datenschutz"),
    ("06_bot_order.png", "https://beta.genesis-ai-engine.com/order/bot?market=DE"),
    ("07_products.png", "https://beta.genesis-ai-engine.com/products?market=DE"),
]


def dismiss_cookies(page) -> None:
    for label in ("Alle akzeptieren", "Nur notwendige", "Accept all", "Necessary only"):
        try:
            btn = page.get_by_role("button", name=label)
            if btn.count() and btn.first.is_visible(timeout=800):
                btn.first.click(timeout=1500)
                page.wait_for_timeout(400)
                return
        except Exception:
            continue


def seed_de(page) -> None:
    page.evaluate(
        """() => {
          localStorage.setItem('virtus_ui_locale', 'de');
          localStorage.setItem('virtus_ui_locale_auto', '0');
          localStorage.setItem('virtus_assistant_locale', 'de');
          localStorage.setItem('virtus_market', 'DE');
          document.cookie = 'virtus_ui_locale=de; path=/; max-age=31536000';
        }"""
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(
            locale="de-DE",
            viewport={"width": 1440, "height": 900},
            extra_http_headers={"Accept-Language": "de-DE,de;q=0.9"},
        )
        context.add_cookies(
            [
                {
                    "name": "virtus_ui_locale",
                    "value": "de",
                    "domain": "beta.genesis-ai-engine.com",
                    "path": "/",
                },
                {
                    "name": "virtus_ui_locale",
                    "value": "de",
                    "domain": ".genesis-ai-engine.com",
                    "path": "/",
                },
            ]
        )
        page = context.new_page()
        page.goto(
            "https://beta.genesis-ai-engine.com/site?market=DE",
            wait_until="domcontentloaded",
        )
        seed_de(page)
        dismiss_cookies(page)
        page.reload(wait_until="networkidle")
        dismiss_cookies(page)

        for name, url in PAGES:
            page.goto(url, wait_until="networkidle", timeout=60000)
            seed_de(page)
            dismiss_cookies(page)
            page.wait_for_timeout(700)
            path = OUT / name
            page.screenshot(path=str(path), full_page=False)
            print(f"OK {name} bytes={path.stat().st_size}")

        # Vector CTA on storefront (do NOT open chat — beta may still greet in RU)
        page.goto(
            "https://beta.genesis-ai-engine.com/site?market=DE",
            wait_until="networkidle",
        )
        seed_de(page)
        dismiss_cookies(page)
        try:
            page.locator("text=Unsicher, was passt?").first.scroll_into_view_if_needed(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            try:
                page.locator("h2:has-text('Vector')").first.scroll_into_view_if_needed(timeout=3000)
                page.wait_for_timeout(500)
            except Exception as exc:
                print(f"vector scroll warn: {exc}")
        page.screenshot(path=str(OUT / "05_vector.png"), full_page=False)
        print(f"OK 05_vector.png bytes={(OUT / '05_vector.png').stat().st_size}")

        browser.close()
    print(f"OUT={OUT}")


if __name__ == "__main__":
    main()
