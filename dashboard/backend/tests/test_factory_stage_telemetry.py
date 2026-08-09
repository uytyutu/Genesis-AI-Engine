"""Factory stage telemetry + immutable Production Artifact."""

from __future__ import annotations

from pathlib import Path

from app.integration.factory_metrics import (
    BUILD_STAGE_IDS,
    StageTimer,
    normalize_stages,
    record_build,
    summary,
)
from app.factory.factory_service import FactoryService


def test_normalize_stages_aliases():
    out = normalize_stages({"zip_pack": 1.5, "compliance_check": 0.4, "total_e2e": 10.0})
    assert out["zip"] == 1.5
    assert out["gates"] == 0.4
    assert out["total"] == 10.0


def test_stage_timer_marks():
    t = StageTimer()
    t.mark("template")
    t.mark("content")
    d = t.as_dict()
    assert "template" in d and "content" in d
    assert d["total"] >= d["template"]


def test_summary_stage_table(tmp_path: Path):
    record_build(
        tmp_path,
        product_id="p1",
        stages={
            "template": 0.5,
            "content": 2.0,
            "assets": 1.0,
            "render": 3.0,
            "gates": 0.8,
            "zip": 0.6,
            "total": 7.9,
        },
        kind="build",
        cached_zip=False,
    )
    record_build(
        tmp_path,
        product_id="p1",
        stages={"zip": 0.01, "total": 0.01},
        kind="zip_cache",
        cached_zip=True,
    )
    snap = summary(tmp_path)
    assert snap["ok"] is True
    assert snap["cached_zip_hits"] == 1
    by_id = {r["id"]: r for r in snap["stage_table"]}
    assert by_id["content"]["avg_s"] == 2.0
    assert by_id["total"]["avg_s"] is not None
    assert list(BUILD_STAGE_IDS) == [
        "queue",
        "template",
        "content",
        "assets",
        "render",
        "gates",
        "zip",
    ]


def test_build_records_factory_stages(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    out = factory.build_landing(
        "Autowerkstatt Müller in Köln — Inspektion, Reifen, Bremsen für Privatkunden.",
        package_id="basic",
        contacts={"business_name": "Müller Auto", "city": "Köln", "niche": "auto"},
    )
    pid = out["product_id"]
    meta = factory._load_meta(pid)
    assert isinstance(meta.get("factory_stages"), dict)
    stages = meta["factory_stages"]
    for key in ("template", "content", "assets", "render", "gates", "total"):
        assert key in stages, key
    rows = (tmp_path / "factory_metrics.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert rows


def test_production_artifact_immutable(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    out = factory.build_landing(
        "Zahnarzt Praxis Schmidt Bonn — Prophylaxe und Implantate.",
        package_id="basic",
        contacts={"business_name": "Praxis Schmidt", "city": "Bonn", "niche": "dental"},
    )
    pid = out["product_id"]
    pre = factory.prebuild_client_delivery_zip(pid)
    assert pre["immutable"] is True
    assert pre["sha256"]
    assert (tmp_path / "sandbox" / pid / "delivery_manifest.json").is_file()
    assert (tmp_path / "sandbox" / pid / "compliance_report.json").is_file()
    meta = factory._load_meta(pid)
    assert meta.get("delivery_locked") is True
    data1, _ = factory.build_client_delivery_zip(pid)
    data2, _ = factory.build_client_delivery_zip(pid)
    assert data1 == data2
    assert len(data1) == pre["bytes"]
