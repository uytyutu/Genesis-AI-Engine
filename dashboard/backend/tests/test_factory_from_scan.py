from pathlib import Path

from app.factory.factory_service import FactoryService


def test_build_landing_from_opportunity_uses_scan_issues(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    opp = {
        "company_name": "Autowerkstatt Müller",
        "website_url": "https://mueller-auto.example",
        "meta": {"niche": "local_service"},
        "site_analysis": {
            "title": "Autowerkstatt Müller",
            "issues": ["Kein HTTPS", "Kein viewport"],
            "strengths": ["Seite erreichbar"],
        },
    }
    result = factory.build_landing_from_opportunity(opp)
    assert result["product_id"]
    assert result["business_name"]
    meta_path = tmp_path / "sandbox" / result["product_id"] / "meta.json"
    assert meta_path.is_file()
    assert "Stealth-Scan" in meta_path.read_text(encoding="utf-8") or "Autowerkstatt" in meta_path.read_text(encoding="utf-8")
