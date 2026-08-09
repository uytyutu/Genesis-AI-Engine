"""Image Media QA — deterministic checks before export (P0).

No export until PASS. FAIL reasons are stable string codes for logs / retry.
Does not call providers. Does not log API keys.
"""

from __future__ import annotations

import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Soft floors — tiny stubs are not accept-for-export
_MIN_BYTES = 4_000
_MIN_W = 640
_MIN_H = 360
_HERO_MIN_W = 1200
_HERO_MIN_H = 675


@dataclass(frozen=True)
class MediaQaCheck:
    id: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MediaQaReport:
    ok: bool
    path: str
    role: str = "hero"
    niche: str = ""
    checks: list[MediaQaCheck] = field(default_factory=list)
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "passed": self.ok,
            "gate": "IMAGE_MEDIA_QA",
            "path": self.path,
            "role": self.role,
            "niche": self.niche,
            "failure_reason": self.failure_reason,
            "checks": [c.as_dict() for c in self.checks],
            "action": "PASS" if self.ok else "FAIL_REGENERATE",
        }


def _probe_image_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for JPEG/PNG/WEBP without requiring Pillow."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24:
        return None

    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        try:
            w, h = struct.unpack(">II", data[16:24])
            return int(w), int(h)
        except struct.error:
            return None

    # JPEG SOF
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0xD9):
                i += 2
                continue
            if marker == 0x01 or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            try:
                seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
            except struct.error:
                return None
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                try:
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    return int(w), int(h)
                except struct.error:
                    return None
            i += 2 + seg_len
            if seg_len < 2:
                break
        return None

    # WEBP VP8X / VP8 / VP8L (minimal)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 " and len(data) >= 30:
            w = struct.unpack("<H", data[26:28])[0] & 0x3FFF
            h = struct.unpack("<H", data[28:30])[0] & 0x3FFF
            return int(w), int(h)
        if chunk == b"VP8L" and len(data) >= 25:
            bits = struct.unpack("<I", data[21:25])[0]
            w = (bits & 0x3FFF) + 1
            h = ((bits >> 14) & 0x3FFF) + 1
            return int(w), int(h)
        if chunk == b"VP8X" and len(data) >= 30:
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
            return int(w), int(h)
    return None


def _is_valid_image_header(path: Path) -> bool:
    try:
        head = path.read_bytes()[:12]
    except OSError:
        return False
    if head[:2] == b"\xff\xd8":
        return True
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if head[:4] == b"RIFF" and path.suffix.lower() in {".webp", ".WEBP"}:
        return True
    # WEBP may be .webp with RIFF; also accept if magic inside
    try:
        data = path.read_bytes()[:16]
    except OSError:
        return False
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def run_image_media_qa(
    path: Path | str,
    *,
    role: str = "hero",
    niche: str = "",
    expected_niche_token: str | None = None,
    duplicate_fingerprint: str | None = None,
    known_fingerprints: set[str] | None = None,
    min_bytes: int = _MIN_BYTES,
) -> MediaQaReport:
    """
    Deterministic Media QA for one image file.

    Checks (ordered):
      file_exists → valid_image → min_bytes → dimensions → niche → not_duplicate
    Contrast / browser-load remain soft until wired to renderer evidence.
    """
    p = Path(path)
    checks: list[MediaQaCheck] = []

    def fail(reason: str, check_id: str, detail: str) -> MediaQaReport:
        checks.append(MediaQaCheck(check_id, False, detail))
        return MediaQaReport(
            ok=False,
            path=str(p),
            role=role,
            niche=niche,
            checks=list(checks),
            failure_reason=reason,
        )

    if not p.is_file():
        return fail("file_missing", "file_exists", f"missing: {p}")
    checks.append(MediaQaCheck("file_exists", True, str(p)))

    if not _is_valid_image_header(p):
        return fail("invalid_image", "valid_image", "not jpeg/png/webp")
    checks.append(MediaQaCheck("valid_image", True, "header ok"))

    size = p.stat().st_size
    if size < min_bytes:
        return fail("too_small", "min_bytes", f"{size} < {min_bytes}")
    checks.append(MediaQaCheck("min_bytes", True, f"{size} bytes"))

    dims = _probe_image_size(p)
    if dims is None:
        return fail("dimensions_unreadable", "dimensions", "could not read width/height")
    w, h = dims
    need_w = _HERO_MIN_W if role == "hero" else _MIN_W
    need_h = _HERO_MIN_H if role == "hero" else _MIN_H
    if w < need_w or h < need_h:
        return fail(
            "dimensions_too_small",
            "dimensions",
            f"{w}x{h} < {need_w}x{need_h} for role={role}",
        )
    checks.append(MediaQaCheck("dimensions", True, f"{w}x{h}"))

    token = (expected_niche_token or niche or "").strip().lower()
    if token:
        # Soft niche marker: filename or sidecar meta string must mention niche token
        # when caller supplies expected_niche_token (deterministic, no vision model).
        hay = f"{p.name} {niche}".lower()
        if token not in hay and not p.name.lower().startswith(token[:3]):
            # Only FAIL when caller set expected_niche_token explicitly
            if expected_niche_token:
                return fail(
                    "niche_mismatch",
                    "niche",
                    f"expected niche token '{token}' not reflected in asset name",
                )
        checks.append(MediaQaCheck("niche", True, token or "n/a"))
    else:
        checks.append(MediaQaCheck("niche", True, "skipped"))

    known = known_fingerprints or set()
    fp = (duplicate_fingerprint or "").strip()
    if fp and fp in known:
        return fail("duplicate", "not_duplicate", f"fingerprint collision: {fp[:48]}")
    checks.append(MediaQaCheck("not_duplicate", True, "ok"))

    # Placeholders for future hard gates (logged as soft pass until evidence wired)
    checks.append(MediaQaCheck("text_contrast", True, "deferred"))
    checks.append(MediaQaCheck("browser_load", True, "deferred"))

    return MediaQaReport(
        ok=True,
        path=str(p),
        role=role,
        niche=niche,
        checks=checks,
        failure_reason=None,
    )
