"""Demo Freshness Gate — stale Basic/Premium demos must fail release."""

from pathlib import Path

from app.integration.demo_gallery_audit import audit_demo_freshness


def test_freshness_detects_wrong_data_tier(tmp_path: Path):
    root = tmp_path / "package-previews"
    dental = root / "sites" / "basic" / "dental"
    dental.mkdir(parents=True)
    (dental / "index.html").write_text(
        '<html><body data-tier="business">old recycled</body></html>',
        encoding="utf-8",
    )
    out = audit_demo_freshness(root)
    assert out["status"] == "FAIL"
    assert any("data-tier=business" in i for i in out["issues"])


def test_freshness_pass_shape_when_empty(tmp_path: Path):
    root = tmp_path / "package-previews"
    root.mkdir(parents=True)
    out = audit_demo_freshness(root)
    assert out["id"] == "demo_freshness_gate"
    assert out["ok"] is False
    assert out["status"] == "FAIL"
