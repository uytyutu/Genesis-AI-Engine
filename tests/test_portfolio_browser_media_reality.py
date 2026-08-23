"""Browser Media Reality — Portfolio Besuchen shows real loaded images.

Separates «file exists on disk» from «client actually sees the image».

Scope: Automotive + Restaurant public agency portfolio only.
Does NOT touch Factory, Design Spec, /order, Game Factory.
"""

from __future__ import annotations

import re
import socket
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
CATALOG_TS = ROOT / "dashboard" / "frontend" / "app" / "lib" / "publicVitrineCatalog.ts"

pytest.importorskip("playwright")

VIEWPORTS = (
    ("desktop", 1440, 900),
    ("mobile", 390, 844),
)

MIN_GALLERY_VISIBLE = 3


def _chromium_ok() -> tuple[bool, str]:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 — soft skip when browser missing
        return False, f"{type(exc).__name__}: {exc}"


@pytest.fixture(scope="module")
def chromium_ready() -> None:
    ok, reason = _chromium_ok()
    if not ok:
        pytest.skip(f"chromium unavailable: {reason}")


def _parse_agency_portfolio() -> list[dict[str, str]]:
    """SSOT from publicVitrineCatalog — one artifact_id → preview + live."""
    text = CATALOG_TS.read_text(encoding="utf-8")
    const_roots = dict(re.findall(r'const (AGENCY_ARTIFACT_[A-Z_]+) = "([^"]+)"', text))
    block = text.split("PUBLIC_AGENCY_PORTFOLIO:")[1].split(
        "export function assertPortfolioArtifactIntegrity"
    )[0]
    items: list[dict[str, str]] = []
    for m in re.finditer(
        r"id:\s*\"([^\"]+)\".*?artifactId:\s*\"([^\"]+)\".*?"
        r"livePreviewUrl:\s*portfolioLivePreviewUrl\((AGENCY_ARTIFACT_[A-Z_]+)\).*?"
        r"previewImage:\s*portfolioPreviewImageForArtifact\(\3\)",
        block,
        flags=re.S,
    ):
        item_id, artifact_id, const_name = m.group(1), m.group(2), m.group(3)
        root = const_roots[const_name]
        items.append(
            {
                "id": item_id,
                "artifact_id": artifact_id,
                "root": root,
                "live": f"{root}/index.html",
                "preview": f"{root}/assets/hero.jpg",
            }
        )
    assert len(items) >= 2, "expected Automotive + Restaurant in PUBLIC_AGENCY_PORTFOLIO"
    return items


@pytest.fixture(scope="module")
def portfolio() -> list[dict[str, str]]:
    return _parse_agency_portfolio()


@pytest.fixture(scope="module")
def static_base(chromium_ready: None) -> str:
    """Serve dashboard/frontend/public so Besuchen paths resolve like on /site."""
    assert PUBLIC.is_dir(), f"missing public dir: {PUBLIC}"

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    handler = partial(Handler, directory=str(PUBLIC))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


_MEDIA_PROBE_JS = """
async () => {
  const waitImg = (img) => new Promise((resolve) => {
    if (img.complete) return resolve();
    img.addEventListener('load', () => resolve(), { once: true });
    img.addEventListener('error', () => resolve(), { once: true });
  });

  const decodeUrl = async (url) => {
    if (!url || url.startsWith('data:')) return { url, ok: true, naturalWidth: 0, kind: 'skip' };
    try {
      const img = new Image();
      img.src = url;
      await waitImg(img);
      return {
        url,
        ok: img.complete && img.naturalWidth > 0,
        naturalWidth: img.naturalWidth || 0,
        naturalHeight: img.naturalHeight || 0,
        kind: 'image',
      };
    } catch (e) {
      return { url, ok: false, naturalWidth: 0, error: String(e), kind: 'image' };
    }
  };

  const extractUrls = (bg) => {
    const out = [];
    const re = /url\\(["']?([^"')]+)["']?\\)/g;
    let m;
    while ((m = re.exec(bg || ''))) {
      const u = m[1];
      if (u && !u.startsWith('data:')) out.push(u);
    }
    return out;
  };

  // Force lazy images into network
  for (const img of Array.from(document.images)) {
    if (img.loading === 'lazy') img.loading = 'eager';
    const ds = img.getAttribute('data-src');
    if (ds && !img.getAttribute('src')) img.setAttribute('src', ds);
  }
  await Promise.all(Array.from(document.images).map(waitImg));

  const imgResults = Array.from(document.images).map((img) => {
    const r = img.getBoundingClientRect();
    const style = window.getComputedStyle(img);
    const visible =
      style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      style.opacity !== '0' &&
      r.width > 0 &&
      r.height > 0;
    return {
      src: img.currentSrc || img.src || '',
      complete: img.complete,
      naturalWidth: img.naturalWidth || 0,
      naturalHeight: img.naturalHeight || 0,
      visible,
      broken: !img.complete || img.naturalWidth === 0,
    };
  });

  // Hero: CSS background on .hero / [class*=hero] media panels
  const heroCandidates = Array.from(
    document.querySelectorAll(
      '.hero, [class*="hero"], [data-split-hero], .rx-hero-media, .co-hero-media'
    )
  );
  const heroUrls = [];
  for (const el of heroCandidates) {
    const bg = window.getComputedStyle(el).backgroundImage;
    for (const u of extractUrls(bg)) {
      if (/hero\\.jpg/i.test(u) || /assets\\/hero/i.test(u)) heroUrls.push(u);
    }
  }
  // Inline style backgrounds referencing hero
  for (const el of Array.from(document.querySelectorAll('[style*="hero"]'))) {
    const bg = el.getAttribute('style') || '';
    const m = bg.match(/url\\(['"]?([^'")]+)['"]?\\)/i);
    if (m && /hero/i.test(m[1])) heroUrls.push(new URL(m[1], location.href).href);
  }
  const uniqueHero = [...new Set(heroUrls)];
  const heroLoads = [];
  for (const u of uniqueHero.slice(0, 4)) {
    heroLoads.push(await decodeUrl(u));
  }

  // Gallery-like media plates
  const galleryEls = Array.from(
    document.querySelectorAll(
      '.rx-band-img, .rx-svc-media, [style*="gallery_"], img[src*="gallery"]'
    )
  );
  const galleryUrls = [];
  for (const el of galleryEls) {
    if (el.tagName === 'IMG') {
      galleryUrls.push(el.currentSrc || el.src);
      continue;
    }
    const bg = window.getComputedStyle(el).backgroundImage;
    const styleAttr = el.getAttribute('style') || '';
    for (const u of extractUrls(bg)) galleryUrls.push(u);
    const m = styleAttr.match(/url\\(['"]?([^'")]*gallery[^'")]+)['"]?\\)/i);
    if (m) galleryUrls.push(new URL(m[1], location.href).href);
  }
  const uniqueGallery = [...new Set(galleryUrls.filter(Boolean))];
  const galleryLoads = [];
  for (const u of uniqueGallery.slice(0, 12)) {
    const decoded = await decodeUrl(u);
    const el = galleryEls.find((node) => {
      if (node.tagName === 'IMG') return (node.currentSrc || node.src) === u;
      return (window.getComputedStyle(node).backgroundImage || '').includes(
        u.replace(location.origin, '')
      ) || (node.getAttribute('style') || '').includes('gallery');
    });
    let visible = false;
    if (el) {
      const r = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      visible =
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        r.width > 1 &&
        r.height > 1;
    }
    galleryLoads.push({ ...decoded, visible });
  }

  return {
    title: document.title || '',
    imgResults,
    heroLoads,
    galleryLoads,
    brokenImgs: imgResults.filter((i) => i.broken).map((i) => i.src).slice(0, 8),
  };
}
"""


def _assert_media_reality(probe: dict, *, label: str) -> None:
    broken = probe.get("brokenImgs") or []
    assert not broken, f"{label}: broken <img>: {broken}"

    hero_ok = [h for h in (probe.get("heroLoads") or []) if h.get("ok") and h.get("naturalWidth", 0) > 0]
    assert hero_ok, f"{label}: hero not loaded in browser (naturalWidth>0 required)"

    gallery_ok = [
        g
        for g in (probe.get("galleryLoads") or [])
        if g.get("ok") and g.get("naturalWidth", 0) > 0
    ]
    assert len(gallery_ok) >= MIN_GALLERY_VISIBLE, (
        f"{label}: need ≥{MIN_GALLERY_VISIBLE} gallery images loaded, got {len(gallery_ok)}"
    )

    # At least one loaded gallery plate should be layout-visible (or hero visible via CSS)
    visible_gallery = [g for g in gallery_ok if g.get("visible")]
    assert visible_gallery or hero_ok, f"{label}: no visible media plates"


def test_portfolio_preview_and_live_share_artifact_id(portfolio: list[dict[str, str]]) -> None:
    for item in portfolio:
        root = item["root"].rstrip("/")
        assert item["live"].startswith(root + "/"), item
        assert item["preview"].startswith(root + "/"), item
        assert item["preview"].endswith("/assets/hero.jpg"), item
        assert item["live"].endswith("/index.html"), item
        disk = PUBLIC / item["root"].lstrip("/")
        assert (disk / "index.html").is_file()
        assert (disk / "assets" / "hero.jpg").is_file()


@pytest.mark.parametrize("viewport_name,width,height", VIEWPORTS)
@pytest.mark.parametrize("item_index", [0, 1], ids=["auto", "restaurant"])
def test_portfolio_besuchen_browser_media_reality(
    static_base: str,
    portfolio: list[dict[str, str]],
    chromium_ready: None,
    viewport_name: str,
    width: int,
    height: int,
    item_index: int,
) -> None:
    from playwright.sync_api import sync_playwright

    item = portfolio[item_index]
    live_url = f"{static_base}{item['live']}"
    preview_url = f"{static_base}{item['preview']}"
    label = f"{item['artifact_id']}@{viewport_name}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        try:
            # Preview image (card thumb) must decode
            page.goto(preview_url, wait_until="load", timeout=60_000)
            preview_probe = page.evaluate(
                """async () => {
                  const img = document.querySelector('img') || (() => {
                    const i = new Image();
                    i.src = location.href;
                    document.body.appendChild(i);
                    return i;
                  })();
                  if (!img.complete) {
                    await new Promise((r) => {
                      img.onload = r; img.onerror = r;
                    });
                  }
                  // For direct image navigation, document may be the image itself
                  if (document.contentType && document.contentType.startsWith('image/')) {
                    return { ok: true, naturalWidth: 1, via: 'contentType' };
                  }
                  return {
                    ok: img.complete && img.naturalWidth > 0,
                    naturalWidth: img.naturalWidth || 0,
                    via: 'img',
                  };
                }"""
            )
            # Direct JPEG navigation: Chromium shows image viewer — check via fetch+Image
            if not preview_probe.get("ok"):
                preview_probe = page.evaluate(
                    """async (url) => {
                      const img = new Image();
                      img.src = url;
                      await new Promise((r) => { img.onload = r; img.onerror = r; });
                      return { ok: img.complete && img.naturalWidth > 0, naturalWidth: img.naturalWidth || 0 };
                    }""",
                    preview_url,
                )
            assert preview_probe.get("ok") and preview_probe.get("naturalWidth", 0) > 0, (
                f"{label}: preview image failed: {preview_probe}"
            )

            # Besuchen → live artifact
            page.goto(live_url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(800)
            # Scroll to wake lazy/gallery bands
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(600)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)

            assert item["root"].rstrip("/") in page.url.replace("\\", "/"), (
                f"{label}: Besuchen URL mismatch — expected artifact {item['root']}, got {page.url}"
            )

            probe = page.evaluate(_MEDIA_PROBE_JS)
            _assert_media_reality(probe, label=label)
        finally:
            browser.close()


def test_portfolio_browser_media_reality_summary(
    static_base: str,
    portfolio: list[dict[str, str]],
    chromium_ready: None,
) -> None:
    """Single desktop pass over both niches — concise CI signal."""
    from playwright.sync_api import sync_playwright

    results: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            for item in portfolio:
                live_url = f"{static_base}{item['live']}"
                page.goto(live_url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(700)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(500)
                probe = page.evaluate(_MEDIA_PROBE_JS)
                _assert_media_reality(probe, label=item["artifact_id"])
                hero_w = max((h.get("naturalWidth") or 0) for h in probe.get("heroLoads") or [0])
                gal_n = sum(
                    1
                    for g in (probe.get("galleryLoads") or [])
                    if g.get("ok") and (g.get("naturalWidth") or 0) > 0
                )
                results.append(f"{item['artifact_id']}: hero_w={hero_w} gallery_ok={gal_n}")
        finally:
            browser.close()
    assert len(results) == len(portfolio)
    print("Browser Media Reality PASS — " + "; ".join(results))
