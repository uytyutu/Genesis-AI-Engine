#!/usr/bin/env python3
"""Generate all Genesis brand raster assets + size audit sheet."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "brand" / "genesis-mark-master.svg"
FAVICON = ROOT / "brand" / "genesis-mark-favicon.svg"
OUT = ROOT / "brand" / "generated"
AUDIT_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)

LAUNCHER_ASSETS = ROOT / "launcher" / "assets"
TAURI_ICONS = ROOT / "client" / "desktop" / "src-tauri" / "icons"
WEB_PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "brand"
DESKTOP_PUBLIC = ROOT / "client" / "desktop" / "public"
ANDROID_BASE = OUT / "android"
IOS_BASE = OUT / "ios"
AUDIT_DIR = OUT / "audit"

PNG_TARGETS: list[tuple[Path, int]] = [
    (LAUNCHER_ASSETS / "genesis-icon.png", 512),
    (WEB_PUBLIC / "genesis-mark-512.png", 512),
    (WEB_PUBLIC / "genesis-mark-192.png", 192),
    (WEB_PUBLIC / "genesis-mark-180.png", 180),
    (WEB_PUBLIC / "apple-touch-icon.png", 180),
    (WEB_PUBLIC / "icon-192.png", 192),
    (WEB_PUBLIC / "icon-512.png", 512),
    (WEB_PUBLIC / "favicon-16.png", 16),
    (WEB_PUBLIC / "favicon-24.png", 24),
    (WEB_PUBLIC / "favicon-32.png", 32),
    (DESKTOP_PUBLIC / "icon-512.png", 512),
    (DESKTOP_PUBLIC / "icon-192.png", 192),
    (TAURI_ICONS / "icon.png", 512),
    (TAURI_ICONS / "128x128@2x.png", 256),
    (TAURI_ICONS / "128x128.png", 128),
    (TAURI_ICONS / "32x32.png", 32),
    (TAURI_ICONS / "16x16.png", 16),
    (IOS_BASE / "AppIcon-1024.png", 1024),
    (IOS_BASE / "AppIcon-180.png", 180),
]

# Windows / Store square logos (Tauri bundle extras)
TAURI_SQUARE_TARGETS: list[tuple[Path, int]] = [
    (TAURI_ICONS / "Square30x30Logo.png", 30),
    (TAURI_ICONS / "Square44x44Logo.png", 44),
    (TAURI_ICONS / "Square71x71Logo.png", 71),
    (TAURI_ICONS / "Square89x89Logo.png", 89),
    (TAURI_ICONS / "Square107x107Logo.png", 107),
    (TAURI_ICONS / "Square142x142Logo.png", 142),
    (TAURI_ICONS / "Square150x150Logo.png", 150),
    (TAURI_ICONS / "Square284x284Logo.png", 284),
    (TAURI_ICONS / "Square310x310Logo.png", 310),
    (TAURI_ICONS / "StoreLogo.png", 50),
]

ANDROID_DENSITIES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

FAVICON_THRESHOLD = 24


def _source_for_size(size: int) -> Path:
    return FAVICON if size <= FAVICON_THRESHOLD else MASTER


def _render_cairosvg(path: Path, size: int) -> bytes:
    import cairosvg

    return cairosvg.svg2png(url=str(path), output_width=size, output_height=size)


def _npx_cmd() -> list[str]:
    for name in ("npx.cmd", "npx"):
        path = shutil.which(name)
        if path:
            return [path]
    raise OSError("npx not found — install Node.js for brand asset generation on Windows")


def _render_resvg(path: Path, size: int) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        subprocess.run(
            [
                *_npx_cmd(),
                "--yes",
                "@resvg/resvg-js-cli",
                "--fit-width",
                str(size),
                "--fit-height",
                str(size),
                str(path),
                str(out),
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return out.read_bytes()
    finally:
        out.unlink(missing_ok=True)


def render_png(size: int) -> bytes:
    source = _source_for_size(size)
    try:
        return _render_cairosvg(source, size)
    except (ImportError, OSError):
        return _render_resvg(source, size)


def write_png(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_png(size))
    variant = "compact" if size <= FAVICON_THRESHOLD else "full"
    print(f"  PNG {size:4d} ({variant:7s}) -> {path.relative_to(ROOT)}")


def write_ico(path: Path, sizes: tuple[int, ...]) -> None:
    from PIL import Image

    frames = [Image.open(BytesIO(render_png(s))).convert("RGBA") for s in sizes]
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"  ICO       -> {path.relative_to(ROOT)}")


def copy_svgs() -> None:
    full = MASTER.read_text(encoding="utf-8")
    compact = FAVICON.read_text(encoding="utf-8")
    copies = [
        (WEB_PUBLIC / "genesis-mark.svg", full),
        (WEB_PUBLIC / "genesis-mark-favicon.svg", compact),
        (DESKTOP_PUBLIC / "icon.svg", full),
        (ROOT / "client" / "desktop" / "src" / "assets" / "genesis-mark.svg", full),
    ]
    for dest, content in copies:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print(f"  SVG       -> {dest.relative_to(ROOT)}")


def write_audit_sheet() -> None:
    from PIL import Image, ImageDraw, ImageFont

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    cols = 3
    rows = (len(AUDIT_SIZES) + cols - 1) // cols
    pad = 24
    label_h = 28
    max_cell = 128
    sheet_w = cols * (max_cell + pad) + pad
    sheet_h = rows * (max_cell + label_h + pad) + pad
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (18, 18, 24, 255))
    draw = ImageDraw.Draw(sheet)

    for i, size in enumerate(AUDIT_SIZES):
        col, row = i % cols, i // cols
        x0 = pad + col * (max_cell + pad)
        y0 = pad + row * (max_cell + label_h + pad)
        icon = Image.open(BytesIO(render_png(size))).convert("RGBA")
        scale = min(max_cell / size, 1.0)
        disp = max(1, int(size * scale)) if size < max_cell else max_cell
        icon = icon.resize((disp, disp), Image.Resampling.LANCZOS)
        ox = x0 + (max_cell - disp) // 2
        oy = y0 + (max_cell - disp) // 2
        sheet.paste(icon, (ox, oy), icon)
        variant = "compact" if size <= FAVICON_THRESHOLD else "full"
        draw.text((x0, y0 + max_cell + 4), f"{size}px {variant}", fill=(200, 200, 210))

    out = AUDIT_DIR / "orbit-stack-size-audit.png"
    sheet.save(out, format="PNG")
    print(f"  AUDIT     -> {out.relative_to(ROOT)}")


def main() -> int:
    if not MASTER.is_file() or not FAVICON.is_file():
        print("Missing brand SVG masters", file=sys.stderr)
        return 1

    print(f"Master: {MASTER.name} | Favicon: {FAVICON.name}")
    copy_svgs()
    for path, size in PNG_TARGETS:
        write_png(path, size)
    for path, size in TAURI_SQUARE_TARGETS:
        write_png(path, size)
    for folder, size in ANDROID_DENSITIES.items():
        write_png(ANDROID_BASE / folder / "ic_launcher.png", size)
        write_png(ANDROID_BASE / folder / "ic_launcher_round.png", size)
    write_ico(LAUNCHER_ASSETS / "genesis.ico", (256, 128, 64, 48, 32, 24, 16))
    write_ico(TAURI_ICONS / "icon.ico", (256, 128, 64, 48, 32, 24, 16))
    write_png(TAURI_ICONS / "icon.icns.png", 512)
    shutil.copy(TAURI_ICONS / "icon.icns.png", TAURI_ICONS / "icon.icns")
    write_audit_sheet()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
