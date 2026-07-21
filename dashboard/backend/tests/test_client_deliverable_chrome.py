"""Client ZIP must not leak Virtus platform chrome (Path A deliverable)."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from app.factory.client_legal_pages import ClientLegalInfo, write_client_legal_pages
from app.factory.factory_service import FactoryService
from app.factory.landing_i18n import ui_strings
from app.factory.market_delivery import deploy_readme


_FORBIDDEN_CHROME = re.compile(
    r"Virtus(\s+Core)?|Demonstration|Tier\s*Switch|Demo-Tarif|"
    r"\bPreview\b|\bWatermark\b",
    re.IGNORECASE,
)
# Package tier names as visible calculator options (platform packages ≠ client site).
_FORBIDDEN_CALC = frozenset({"basic", "basis", "business", "premium", "преміум", "премиум"})


def test_deploy_readme_has_no_platform_brand():
    for market in ("DE", "US", "GB", "UA", "RU", "FR", "PL"):
        text = deploy_readme(market)
        assert "Virtus" not in text, market
        assert "Factory ·" not in text, market


def test_legal_pages_have_no_virtus(tmp_path: Path):
    info = ClientLegalInfo(
        business_name="Praxis Test",
        owner_name="Dr. Test",
        street="Hauptstr. 1",
        zip="50667",
        city="Koeln",
        email="a@b.de",
    )
    write_client_legal_pages(tmp_path, info, market_code="DE")
    for name in ("impressum.html", "datenschutz.html"):
        body = (tmp_path / name).read_text(encoding="utf-8")
        assert not _FORBIDDEN_CHROME.search(body), name

    write_client_legal_pages(tmp_path, info, market_code="US")
    for name in ("privacy.html", "terms.html"):
        body = (tmp_path / name).read_text(encoding="utf-8")
        assert not _FORBIDDEN_CHROME.search(body), name
        assert "Virtus" not in body


def test_calc_opts_are_not_virtus_package_names():
    for lang in ("de", "en", "cs", "uk", "ru"):
        ui = ui_strings(lang)
        for key in ("calc_opt0", "calc_opt1", "calc_opt2"):
            label = str(ui[key]).strip().casefold()
            assert label not in _FORBIDDEN_CALC, f"{lang}:{key}={ui[key]!r}"


def test_factory_zip_filename_and_contents_have_no_virtus_chrome(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate.",
        client_legal={
            "owner_name": "Dr. Anna Mueller",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "praxis@mueller-zahn.de",
            "phone": "+49 221 555",
            "legal_form": "Einzelunternehmen",
        },
    )
    pid = product["product_id"]
    data, filename = factory.build_client_delivery_zip(pid)
    assert filename.endswith(".zip")
    assert "-virtus" not in filename.casefold()
    assert "virtus" not in filename.casefold()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
        assert "README_PUBLISH.txt" in names
        assert "index.html" in names
        readme = zf.read("README_PUBLISH.txt").decode("utf-8")
        index = zf.read("index.html").decode("utf-8")
        impressum = zf.read("impressum.html").decode("utf-8")
        datenschutz = zf.read("datenschutz.html").decode("utf-8")

    for label, text in (
        ("readme", readme),
        ("index", index),
        ("impressum", impressum),
        ("datenschutz", datenschutz),
    ):
        assert not _FORBIDDEN_CHROME.search(text), label
        assert "Virtus" not in text, label
        assert "tier-switch" not in text.casefold(), label
