"""License gate for research 3D assets — MIT runtime ≠ model license."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ALLOWED_MODEL_LICENSES = frozenset(
    {
        "CC0",
        "CC0-1.0",
        "CC-BY",
        "CC-BY-4.0",
        "CC-BY-3.0",
        "MIT",
        "PUBLIC_DOMAIN",
    }
)

BLOCKED_HINTS = (
    "personal use only",
    "non-commercial",
    "nc-sa",
    "cc-by-nc",
    "editorial",
    "sketchfab standard",
)


@dataclass(frozen=True)
class LicenseGateResult:
    ok: bool
    code: str
    detail: str = ""


def check_asset_license(
    asset_dir: Path,
    *,
    require_credits: bool = True,
) -> LicenseGateResult:
    """Pass if LICENSE (or license.txt) declares an allowed model license + optional CREDITS."""
    root = Path(asset_dir)
    if not root.is_dir():
        return LicenseGateResult(False, "no_asset_dir", str(root))

    license_path = None
    for name in ("LICENSE", "LICENSE.txt", "license.txt", "MODEL_LICENSE.txt"):
        candidate = root / name
        if candidate.is_file():
            license_path = candidate
            break
    if license_path is None:
        return LicenseGateResult(
            False,
            "missing_license",
            "Add LICENSE.txt with CC0 / CC-BY / MIT before build.",
        )

    text = license_path.read_text(encoding="utf-8", errors="replace")
    lower = text.casefold()
    for bad in BLOCKED_HINTS:
        if bad in lower:
            return LicenseGateResult(False, "blocked_license", bad)

    allowed_hit = any(token.casefold() in lower for token in ALLOWED_MODEL_LICENSES)
    # Also accept SPDX-style first line
    first = text.strip().splitlines()[0].strip().upper() if text.strip() else ""
    if first in ALLOWED_MODEL_LICENSES or allowed_hit:
        pass
    else:
        return LicenseGateResult(
            False,
            "unknown_license",
            f"First line/spdx must be one of: {', '.join(sorted(ALLOWED_MODEL_LICENSES))}",
        )

    if require_credits:
        credits = root / "CREDITS.txt"
        if not credits.is_file():
            return LicenseGateResult(
                False,
                "missing_credits",
                "CREDITS.txt required (author, source URL, license id).",
            )
        if len(credits.read_text(encoding="utf-8", errors="replace").strip()) < 8:
            return LicenseGateResult(False, "empty_credits", "CREDITS.txt too short")

    return LicenseGateResult(True, "ok", str(license_path.name))
