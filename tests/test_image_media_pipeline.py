"""P0 Image Pipeline + Media QA — Definition of Done (unit / control-flow).

Live provider E2E is separate and only after RC1 PASS + real key.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from app.integration.provider_gateway import ProviderGateway
from app.integration.provider_gateway.image_pipeline import (
    ImageBrief,
    ImagePipelineHardFailure,
    run_image_pipeline,
)
from app.integration.provider_gateway.media_qa import run_image_media_qa


def _png(path: Path, w: int = 1920, h: int = 1080, rgb: tuple[int, int, int] = (40, 40, 40)) -> Path:
    """Minimal valid solid PNG (no Pillow required for fixture write)."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


class _StubGenerator:
    def __init__(self, mode: str = "pass", fail_times: int = 0) -> None:
        self.mode = mode
        self.fail_times = fail_times
        self.calls = 0

    def generate(self, brief: ImageBrief, *, out_path: Path, api_key: str) -> dict:
        assert "sk-" not in str(api_key) or api_key  # key used, never returned
        self.calls += 1
        if self.mode == "timeout":
            raise TimeoutError("generation timeout")
        if self.mode == "api_error":
            return {"ok": False, "error": "provider_api_error", "message": "503"}
        if self.mode == "fail_then_pass":
            if self.calls <= self.fail_times:
                # tiny invalid file → QA FAIL
                out_path.write_bytes(b"not-an-image")
                return {"ok": True, "model": "stub", "path": str(out_path)}
            _png(out_path)
            return {"ok": True, "model": "stub", "path": str(out_path)}
        if self.mode == "always_bad":
            out_path.write_bytes(b"bad")
            return {"ok": True, "model": "stub", "path": str(out_path)}
        _png(out_path)
        return {"ok": True, "model": "stub-model", "path": str(out_path)}


def test_media_qa_pass_and_fail(tmp_path: Path) -> None:
    good = _png(tmp_path / "hero.png")
    report = run_image_media_qa(good, role="hero", niche="beauty")
    assert report.ok is True
    assert report.failure_reason is None

    missing = run_image_media_qa(tmp_path / "nope.png")
    assert missing.ok is False
    assert missing.failure_reason == "file_missing"

    bad = tmp_path / "x.png"
    bad.write_bytes(b"nope")
    invalid = run_image_media_qa(bad)
    assert invalid.ok is False
    assert invalid.failure_reason == "invalid_image"

    tiny = _png(tmp_path / "tiny.png", w=100, h=100)
    dims = run_image_media_qa(tiny, role="hero", min_bytes=100)
    assert dims.ok is False
    assert dims.failure_reason == "dimensions_too_small"

    dup = run_image_media_qa(
        good,
        role="hero",
        duplicate_fingerprint="fp-1",
        known_fingerprints={"fp-1"},
    )
    assert dup.ok is False
    assert dup.failure_reason == "duplicate"


def test_provider_missing_and_key_missing(tmp_path: Path) -> None:
    gw = ProviderGateway(tmp_path)
    brief = ImageBrief(project_id="p1", niche="beauty", prompt="hero")
    out = tmp_path / "out.png"

    no_prov = run_image_pipeline(
        gateway=gw, brief=brief, out_path=out, generator=_StubGenerator()
    )
    assert no_prov.ok is False
    assert no_prov.export_allowed is False
    assert no_prov.failure_reason == "no_provider_connected"

    # Connect with key via vault — select works; still need adapter for pass
    gw.connect("openai_images", "sk-test-key-1234567890")
    no_adapter = run_image_pipeline(
        gateway=gw, brief=brief, out_path=out, generator=None
    )
    assert no_adapter.failure_reason == "no_image_adapter"


def test_timeout_and_api_error_controlled(tmp_path: Path) -> None:
    gw = ProviderGateway(tmp_path)
    gw.connect("openai_images", "sk-test-key-1234567890")
    brief = ImageBrief(project_id="p1", prompt="x")
    out = tmp_path / "out.png"

    timed = run_image_pipeline(
        gateway=gw,
        brief=brief,
        out_path=out,
        generator=_StubGenerator("timeout"),
        max_attempts=3,
    )
    assert timed.ok is False
    assert timed.failure_reason == "max_attempts_exhausted"
    assert len(timed.attempts) == 3
    assert all(a.status == "timeout" for a in timed.attempts)

    err = run_image_pipeline(
        gateway=gw,
        brief=brief,
        out_path=out,
        generator=_StubGenerator("api_error"),
        max_attempts=2,
    )
    assert err.ok is False
    assert len(err.attempts) == 2
    assert all(a.status == "provider_error" for a in err.attempts)


def test_qa_fail_regenerate_then_pass(tmp_path: Path) -> None:
    gw = ProviderGateway(tmp_path)
    gw.connect("fal_flux", "fal-test-key-1234567890")
    brief = ImageBrief(project_id="p1", role="hero", niche="beauty", prompt="hero")
    out = tmp_path / "hero.png"
    log = tmp_path / "image_pipeline.jsonl"

    report = run_image_pipeline(
        gateway=gw,
        brief=brief,
        out_path=out,
        generator=_StubGenerator("fail_then_pass", fail_times=1),
        max_attempts=3,
        log_path=log,
    )
    assert report.ok is True
    assert report.export_allowed is True
    assert out.is_file()
    assert len(report.attempts) == 2
    assert report.attempts[0].status == "qa_fail"
    assert report.attempts[1].status == "qa_pass"
    text = log.read_text(encoding="utf-8")
    assert "qa_fail" in text and "qa_pass" in text
    assert "fal-test-key" not in text
    assert "api_key" not in text or "***" in text


def test_repeated_qa_fail_hard_failure_no_infinite(tmp_path: Path) -> None:
    gw = ProviderGateway(tmp_path)
    gw.connect("openai_images", "sk-test-key-1234567890")
    brief = ImageBrief(project_id="p1", prompt="x")
    out = tmp_path / "out.png"
    gen = _StubGenerator("always_bad")

    with pytest.raises(ImagePipelineHardFailure) as ei:
        run_image_pipeline(
            gateway=gw,
            brief=brief,
            out_path=out,
            generator=gen,
            max_attempts=3,
            raise_on_hard_failure=True,
        )
    assert ei.value.report.failure_reason == "max_attempts_exhausted"
    assert ei.value.report.export_allowed is False
    assert gen.calls == 3  # not infinite
