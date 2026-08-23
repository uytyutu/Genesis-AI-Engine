"""Virtus Core Website Auditor — scoring, export, virtus mode."""

from __future__ import annotations

from pathlib import Path

from app.integration.vc_auditor.branding import PRODUCT_NAME
from app.integration.vc_auditor.engine import VirtusCoreWebsiteAuditor
from app.integration.vc_auditor.export import export_csv, export_markdown, export_pdf
from app.integration.vc_auditor.scoring import score_website
from app.integration.vc_auditor.signals import extract_signals


SAMPLE_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Zahnarzt Berlin Mitte</title>
  <meta name="description" content="Ihre Zahnarztpraxis in Berlin — Termine online."/>
  <meta property="og:title" content="Zahnarzt Berlin"/>
</head>
<body>
  <h1>Willkommen</h1>
  <a class="btn" href="#contact">Jetzt Termin anfragen</a>
  <form class="contact-form"><input/><button>Senden</button></form>
  <a href="/impressum.html">Impressum</a>
  <a href="/datenschutz.html">Datenschutz</a>
  <p>Cookie Hinweis: Wir nutzen notwendige Cookies.</p>
  <img src="/hero.jpg" alt="Praxis" loading="lazy"/>
  <a href="https://instagram.com/demo">Instagram</a>
</body>
</html>
"""


def test_branding():
    assert PRODUCT_NAME == "Virtus Core Website Auditor"


def test_signals_and_scores():
    sig = extract_signals(SAMPLE_HTML, final_url="https://demo.de/")
    assert sig["title"]
    assert sig["description"]
    assert sig["viewport"]
    assert sig["impressum"]
    assert sig["forms"]
    website = score_website(sig)
    assert website["mobile"] == 100
    assert website["seo"] >= 70


def test_virtus_mode_findings_coming(tmp_path: Path):
    demo = tmp_path / "site"
    demo.mkdir()
    (demo / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    (demo / "meta.json").write_text("{}", encoding="utf-8")
    # no impressum file — signal still from link in index
    svc = VirtusCoreWebsiteAuditor(tmp_path)
    report = svc.analyze_virtus_product(
        product_dir=demo, locale="de", niche="Dental"
    )
    assert report["ok"] is True
    assert report["product"] == PRODUCT_NAME
    assert report["mode"] == "virtus_core"
    assert report["virtus_mode"] is True
    assert isinstance(report["overall_business_score"], int)
    assert "ai_summary" in report
    # missing maps → finding with coming or live action
    findings = report["findings"]
    assert isinstance(findings, list)


def test_exports(tmp_path: Path):
    demo = tmp_path / "site"
    demo.mkdir()
    (demo / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    (demo / "impressum.html").write_text("<html>Impressum</html>", encoding="utf-8")
    (demo / "datenschutz.html").write_text("<html>Datenschutz</html>", encoding="utf-8")
    (demo / "meta.json").write_text("{}", encoding="utf-8")
    report = VirtusCoreWebsiteAuditor(tmp_path).analyze_virtus_product(
        product_dir=demo, locale="de"
    )
    md = export_markdown(report)
    assert "Overall Business Score" in md
    assert PRODUCT_NAME in md
    csv = export_csv(report)
    assert "overall_business_score" in csv
    pdf = export_pdf(report)
    assert pdf.startswith(b"%PDF")


def test_public_unreachable(tmp_path: Path, monkeypatch):
    from app.integration.vc_auditor import engine as eng

    def boom(_url: str, **_kw):
        raise ValueError("robots_txt_disallowed")

    monkeypatch.setattr(
        "app.integration.stealth_http.stealth_fetch_get",
        boom,
    )
    report = VirtusCoreWebsiteAuditor(tmp_path).analyze_url(
        "https://blocked.example", locale="de"
    )
    assert report["ok"] is True
    assert report["mode"] == "public"
    assert report["fetch"]["ok"] is False
