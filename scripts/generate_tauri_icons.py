"""Generate Tauri icon set from launcher genesis-icon.png."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "launcher" / "assets" / "genesis-icon.png"
OUT = ROOT / "client" / "desktop" / "src-tauri" / "icons"

SIZES = {
    "32x32.png": 32,
    "128x128.png": 128,
    "128x128@2x.png": 256,
    "icon.png": 512,
}


def main() -> None:
    if not SOURCE.is_file():
        print(f"Run launcher/assets/generate_brand_icon.py first. Missing {SOURCE}", file=sys.stderr)
        raise SystemExit(1)
    OUT.mkdir(parents=True, exist_ok=True)
    src = Image.open(SOURCE).convert("RGBA")
    for name, size in SIZES.items():
        img = src.resize((size, size), Image.Resampling.LANCZOS)
        img.save(OUT / name, format="PNG")
    # ICO for Windows bundle
    src.resize((256, 256), Image.Resampling.LANCZOS).save(
        OUT / "icon.ico",
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    # icns placeholder — copy 512 png (Tauri may regenerate on mac build)
    shutil.copy(OUT / "icon.png", OUT / "icon.icns")
    print(f"Tauri icons written to {OUT}")


if __name__ == "__main__":
    main()
