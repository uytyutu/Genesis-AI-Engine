#!/usr/bin/env python3
"""Generate a tiny stylized tooth GLB (original Virtus Core mesh, CC0) for research dental preset.

No network. Output: dashboard/backend/_research_3d/scenes/dental/hero.glb
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dashboard" / "backend" / "_research_3d" / "scenes" / "dental"


def _tooth_mesh(segments: int = 12) -> tuple[list[float], list[float], list[int]]:
    """Low-poly tooth: crown ellipsoid + root taper. Positions + normals + indices."""
    positions: list[float] = []
    normals: list[float] = []
    indices: list[int] = []

    def add_vert(x: float, y: float, z: float, nx: float, ny: float, nz: float) -> int:
        positions.extend((x, y, z))
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        normals.extend((nx / ln, ny / ln, nz / ln))
        return len(positions) // 3 - 1

    # Crown ring (y=0.35) and top (y=0.55)
    crown_r, crown_y = 0.28, 0.32
    top_y = 0.52
    root_y, root_r = -0.35, 0.08
    mid_y, mid_r = 0.0, 0.22

    rings: list[list[int]] = []
    for y, rx, rz in (
        (top_y, crown_r * 0.55, crown_r * 0.45),
        (crown_y, crown_r, crown_r * 0.85),
        (mid_y, mid_r, mid_r * 0.9),
        (root_y, root_r, root_r),
    ):
        ring: list[int] = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            x, z = math.cos(a) * rx, math.sin(a) * rz
            # outward normal approx
            ring.append(add_vert(x, y, z, x, 0.15 if y > 0 else -0.2, z))
        rings.append(ring)

    for r0, r1 in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            a, b, c, d = r0[i], r0[j], r1[j], r1[i]
            indices.extend((a, b, c, a, c, d))

    # Cap top
    top_c = add_vert(0.0, top_y + 0.02, 0.0, 0.0, 1.0, 0.0)
    for i in range(segments):
        j = (i + 1) % segments
        indices.extend((top_c, rings[0][i], rings[0][j]))

    # Cap root
    root_c = add_vert(0.0, root_y - 0.02, 0.0, 0.0, -1.0, 0.0)
    for i in range(segments):
        j = (i + 1) % segments
        indices.extend((root_c, rings[-1][j], rings[-1][i]))

    return positions, normals, indices


def _align4(n: int) -> int:
    return (4 - (n % 4)) % 4


def write_glb(path: Path) -> int:
    positions, normals, indices = _tooth_mesh()
    pos_bytes = struct.pack("<" + "f" * len(positions), *positions)
    norm_bytes = struct.pack("<" + "f" * len(normals), *normals)
    # indices as uint16
    assert max(indices) < 65535
    idx_bytes = struct.pack("<" + "H" * len(indices), *indices)
    if len(idx_bytes) % 4:
        idx_bytes += b"\x00" * _align4(len(idx_bytes))

    bin_blob = pos_bytes + norm_bytes + idx_bytes
    pos_len = len(pos_bytes)
    norm_len = len(norm_bytes)
    idx_len = len(indices) * 2  # before pad
    idx_pad = len(idx_bytes)

    # bounds
    xs = positions[0::3]
    ys = positions[1::3]
    zs = positions[2::3]
    min_p = [min(xs), min(ys), min(zs)]
    max_p = [max(xs), max(ys), max(zs)]

    gltf = {
        "asset": {"version": "2.0", "generator": "Virtus Core research_3d dental preset"},
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"mesh": 0, "name": "DentalHeroTooth"}],
        "meshes": [
            {
                "name": "Tooth",
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1},
                        "indices": 2,
                        "mode": 4,
                    }
                ],
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(positions) // 3,
                "type": "VEC3",
                "max": max_p,
                "min": min_p,
            },
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": len(normals) // 3,
                "type": "VEC3",
            },
            {
                "bufferView": 2,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
            },
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len, "byteLength": norm_len, "target": 34962},
            {
                "buffer": 0,
                "byteOffset": pos_len + norm_len,
                "byteLength": idx_len,
                "target": 34963,
            },
        ],
        "buffers": [{"byteLength": len(bin_blob)}],
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * _align4(len(json_bytes))

    # GLB: header + JSON chunk + BIN chunk
    chunks = bytearray()
    chunks += struct.pack("<I", len(json_bytes))
    chunks += struct.pack("<I", 0x4E4F534A)  # JSON
    chunks += json_bytes
    chunks += struct.pack("<I", len(bin_blob))
    chunks += struct.pack("<I", 0x004E4942)  # BIN
    chunks += bin_blob

    total = 12 + len(chunks)
    header = struct.pack("<4sII", b"glTF", 2, total)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + chunks)
    return path.stat().st_size


def main() -> None:
    out = OUT_DIR / "hero.glb"
    size = write_glb(out)
    print(f"wrote {out} ({size} bytes)")


if __name__ == "__main__":
    main()
