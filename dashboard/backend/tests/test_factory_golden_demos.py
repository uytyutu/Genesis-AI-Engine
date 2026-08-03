"""Regression: Golden Demo questionnaires still pass Hard Gate + niche identity."""

from __future__ import annotations

import json
from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.composers import run_composers

GOLDEN = Path(__file__).resolve().parents[1] / "app" / "factory" / "golden_demos"


def test_golden_demos_exist_and_pass_commercial_gate():
    index_path = GOLDEN / "INDEX.json"
    assert index_path.is_file(), "Run: py -3.12 scripts/generate_factory_golden_demos.py"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    niches = [n["niche"] for n in index.get("niches") or []]
    assert niches == ["dental", "beauty", "auto", "restaurant", "law"], niches

    for niche in niches:
        folder = GOLDEN / niche
        q = json.loads((folder / "questionnaire.json").read_text(encoding="utf-8"))
        html = (folder / "index.html").read_text(encoding="utf-8")
        assert (folder / "index.html").is_file()
        assert "virtus core" not in html.lower()
        assert "partner vor ort" not in html.lower()
        assert "lorem ipsum" not in html.lower()
        # ZIP optional in CI if not regenerated; require when present
        zip_path = folder / "delivery.zip"
        if zip_path.is_file():
            assert zip_path.stat().st_size > 1000

        analysis = analyze(q["description"], niche_hint=q["niche"])
        contacts = {
            "business_name": q["business_name"],
            "city": q["city"],
            "phone": q["phone"],
            "email": q["email"],
            "services_list": q["services_list"],
            "advantages": q.get("advantages") or [],
            "niche": q["niche"],
            "package_id": "basic",
            "market_code": "DE",
        }
        out, gate = run_composers(
            analysis,
            contacts=contacts,
            package_id="basic",
            html=html,
            scenario_id=q["niche"],
        )
        assert out.niche == q["niche"] or out.niche in (q["niche"], analysis.niche)
        assert gate.hard_passed, (niche, gate.failures)
        assert gate.brand_leak == "PASS"
        assert q["business_name"].split()[0].lower() in (out.headline or "").lower()
