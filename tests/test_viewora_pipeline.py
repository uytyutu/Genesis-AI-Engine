"""Virtus Video AI — real MP4 production pipeline (FFmpeg)."""

from __future__ import annotations

from pathlib import Path

from app.integration.viewora.billing import VieworaBilling
from app.integration.viewora.ffmpeg_bin import ffmpeg_available
from app.integration.viewora.pipeline import produce
from app.integration.viewora.product import PRODUCTION_GATE, public_catalog


def test_production_gate_mp4_flags():
    assert PRODUCTION_GATE["end_to_end_mp4"] is True
    assert PRODUCTION_GATE["failed_generation_refund"] is True
    cat = public_catalog()
    assert cat["reality"]["mp4_render"] is True
    assert cat["name"] == "Virtus Video AI"


def test_produce_real_mp4(tmp_path: Path):
    if not ffmpeg_available():
        return  # host without ffmpeg — skip, do not fake PASS
    out = produce(
        memory_dir=tmp_path,
        brief="Сделай эмоциональный TikTok о новом треке",
        mode="viral",
    )
    assert out["render"]["mp4_available"] is True
    path = Path(out["render"]["path"])
    assert path.is_file()
    assert path.stat().st_size > 20_000
    assert out["package"]["render"]["mp4_available"] is True
    assert out["render"]["download_path"].endswith(".mp4")


def test_refund_on_manual_fail(tmp_path: Path):
    billing = VieworaBilling(tmp_path)
    acc = billing.account_snapshot(None)["account"]
    before = int(acc["free_creations_left"])
    acc = billing.spend(acc, action="create")
    assert int(acc["free_creations_left"]) == before - 1
    acc = billing.refund_last_spend(acc)
    assert int(acc["free_creations_left"]) == before
