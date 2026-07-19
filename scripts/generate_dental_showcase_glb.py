#!/usr/bin/env python3
"""Generate dental tech showcase GLB — natural tooth + implant cutaway (CC0).

Premium client path must NOT use this until quality=approved with a licensed
studio asset. This mesh is for lab (?lab3d=1) and future replacement.

Writes:
  dashboard/backend/_research_3d/showcases/dental/model.glb

Usage:
  py -3.12 scripts/generate_dental_showcase_glb.py
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dashboard" / "backend" / "_research_3d" / "showcases" / "dental"


@dataclass(frozen=True)
class PbrMaterial:
    name: str
    base_color: tuple[float, float, float, float]
    metallic: float
    roughness: float


@dataclass
class MeshPart:
    name: str
    positions: list[float]
    normals: list[float]
    indices: list[int]
    material: PbrMaterial


def _align4(n: int) -> int:
    return (4 - (n % 4)) % 4


def _norm(nx: float, ny: float, nz: float) -> tuple[float, float, float]:
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / ln, ny / ln, nz / ln


class LatheMesh:
    def __init__(self) -> None:
        self.positions: list[float] = []
        self.normals: list[float] = []
        self.indices: list[int] = []

    def _vert(self, x: float, y: float, z: float, nx: float, ny: float, nz: float) -> int:
        self.positions.extend((x, y, z))
        self.normals.extend(_norm(nx, ny, nz))
        return len(self.positions) // 3 - 1

    def lathe(self, profile: list[tuple[float, float]], *, segments: int = 72) -> None:
        if len(profile) < 2:
            return
        rings: list[list[int]] = []
        for i, (r, y) in enumerate(profile):
            if i == 0:
                dr, dy = profile[1][0] - r, profile[1][1] - y
            elif i == len(profile) - 1:
                dr, dy = r - profile[i - 1][0], y - profile[i - 1][1]
            else:
                dr = profile[i + 1][0] - profile[i - 1][0]
                dy = profile[i + 1][1] - profile[i - 1][1]
            nr, ny = -dy, dr
            ring: list[int] = []
            for s in range(segments):
                a = 2 * math.pi * s / segments
                c, si = math.cos(a), math.sin(a)
                ring.append(self._vert(c * r, y, si * r, c * nr, ny, si * nr))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for i in range(segments):
                j = (i + 1) % segments
                self.indices.extend((r0[i], r0[j], r1[j], r0[i], r1[j], r1[i]))
        top_r, top_y = profile[0]
        bot_r, bot_y = profile[-1]
        if top_r > 1e-4:
            tc = self._vert(0, top_y, 0, 0, 1, 0)
            for i in range(segments):
                j = (i + 1) % segments
                self.indices.extend((tc, rings[0][i], rings[0][j]))
        if bot_r > 1e-4:
            bc = self._vert(0, bot_y, 0, 0, -1, 0)
            for i in range(segments):
                j = (i + 1) % segments
                self.indices.extend((bc, rings[-1][j], rings[-1][i]))

    def finish(self, name: str, material: PbrMaterial) -> MeshPart:
        return MeshPart(name, self.positions, self.normals, self.indices, material)


# Materials tuned for studio look (still research — not licensed photoreal scan)
ENAMEL = PbrMaterial("NaturalEnamel", (0.96, 0.93, 0.88, 1.0), 0.0, 0.18)
DENTIN = PbrMaterial("DentinCore", (0.92, 0.82, 0.68, 1.0), 0.0, 0.42)
CERAMIC = PbrMaterial("CrownCeramic", (0.98, 0.96, 0.93, 1.0), 0.0, 0.12)
TITANIUM = PbrMaterial("DentalTitanium", (0.46, 0.48, 0.52, 1.0), 0.96, 0.26)
ABUTMENT = PbrMaterial("AbutmentPolish", (0.70, 0.72, 0.76, 1.0), 0.98, 0.12)
GINGIVA = PbrMaterial("GingivaSoft", (0.78, 0.42, 0.48, 1.0), 0.0, 0.55)


def build_enamel_crown() -> MeshPart:
    """Visible natural tooth crown — primary recognizable dental silhouette."""
    m = LatheMesh()
    m.lathe(
        [
            (0.02, 0.78),
            (0.10, 0.74),
            (0.18, 0.68),
            (0.22, 0.58),
            (0.23, 0.48),
            (0.21, 0.38),
            (0.16, 0.30),
            (0.10, 0.26),
        ],
        segments=80,
    )
    return m.finish("NaturalCrown", ENAMEL)


def build_ceramic_cap() -> MeshPart:
    """Subtle ceramic overlay on occlusal — tech without looking like a screw."""
    m = LatheMesh()
    m.lathe(
        [
            (0.01, 0.80),
            (0.08, 0.77),
            (0.14, 0.72),
            (0.16, 0.66),
            (0.12, 0.62),
        ],
        segments=64,
    )
    return m.finish("CeramicOcclusal", CERAMIC)


def build_root_shell() -> MeshPart:
    """Partial root / cutaway wall so implant reads as 'inside the tooth'."""
    m = LatheMesh()
    # Only front half via full lathe + dentin color — silhouette of root
    m.lathe(
        [
            (0.10, 0.26),
            (0.12, 0.12),
            (0.11, -0.05),
            (0.09, -0.25),
            (0.06, -0.42),
            (0.02, -0.52),
        ],
        segments=64,
    )
    return m.finish("RootDentin", DENTIN)


def build_fixture() -> MeshPart:
    m = LatheMesh()
    profile: list[tuple[float, float]] = [(0.008, -0.55)]
    y = -0.52
    while y < 0.05:
        profile.append((0.055, y))
        profile.append((0.068, y + 0.010))
        profile.append((0.048, y + 0.020))
        y += 0.030
    profile.extend([(0.06, 0.08), (0.055, 0.14), (0.04, 0.18)])
    m.lathe(profile, segments=64)
    return m.finish("TitaniumFixture", TITANIUM)


def build_abutment() -> MeshPart:
    m = LatheMesh()
    m.lathe(
        [
            (0.035, 0.16),
            (0.048, 0.22),
            (0.052, 0.28),
            (0.042, 0.32),
        ],
        segments=48,
    )
    return m.finish("Abutment", ABUTMENT)


def build_gingiva() -> MeshPart:
    m = LatheMesh()
    m.lathe(
        [
            (0.14, 0.22),
            (0.18, 0.24),
            (0.19, 0.28),
            (0.15, 0.30),
            (0.11, 0.29),
        ],
        segments=56,
    )
    return m.finish("Gingiva", GINGIVA)


def write_multi_glb(path: Path, parts: list[MeshPart]) -> int:
    bin_parts: list[bytes] = []
    accessors: list[dict] = []
    buffer_views: list[dict] = []
    materials: list[dict] = []
    primitives: list[dict] = []
    offset = 0

    for pi, part in enumerate(parts):
        pos = struct.pack("<" + "f" * len(part.positions), *part.positions)
        norm = struct.pack("<" + "f" * len(part.normals), *part.normals)
        assert max(part.indices) < 65535
        idx = struct.pack("<" + "H" * len(part.indices), *part.indices)
        if len(idx) % 4:
            idx += b"\x00" * _align4(len(idx))

        xs, ys, zs = part.positions[0::3], part.positions[1::3], part.positions[2::3]
        materials.append(
            {
                "name": part.material.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(part.material.base_color),
                    "metallicFactor": part.material.metallic,
                    "roughnessFactor": part.material.roughness,
                },
                "doubleSided": False,
            }
        )
        buffer_views.append(
            {"buffer": 0, "byteOffset": offset, "byteLength": len(pos), "target": 34962}
        )
        accessors.append(
            {
                "bufferView": len(buffer_views) - 1,
                "componentType": 5126,
                "count": len(part.positions) // 3,
                "type": "VEC3",
                "max": [max(xs), max(ys), max(zs)],
                "min": [min(xs), min(ys), min(zs)],
            }
        )
        pos_acc = len(accessors) - 1
        bin_parts.append(pos)
        offset += len(pos)

        buffer_views.append(
            {"buffer": 0, "byteOffset": offset, "byteLength": len(norm), "target": 34962}
        )
        accessors.append(
            {
                "bufferView": len(buffer_views) - 1,
                "componentType": 5126,
                "count": len(part.normals) // 3,
                "type": "VEC3",
            }
        )
        norm_acc = len(accessors) - 1
        bin_parts.append(norm)
        offset += len(norm)

        buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": offset,
                "byteLength": len(part.indices) * 2,
                "target": 34963,
            }
        )
        accessors.append(
            {
                "bufferView": len(buffer_views) - 1,
                "componentType": 5123,
                "count": len(part.indices),
                "type": "SCALAR",
            }
        )
        idx_acc = len(accessors) - 1
        bin_parts.append(idx)
        offset += len(idx)

        primitives.append(
            {
                "attributes": {"POSITION": pos_acc, "NORMAL": norm_acc},
                "indices": idx_acc,
                "material": pi,
                "mode": 4,
            }
        )

    bin_blob = b"".join(bin_parts)
    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "Virtus Core generate_dental_showcase_glb.py",
        },
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"mesh": 0, "name": "dental_tooth_implant_cutaway"}],
        "materials": materials,
        "meshes": [{"name": "DentalTechTooth", "primitives": primitives}],
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_blob)}],
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * _align4(len(json_bytes))
    chunks = bytearray()
    chunks += struct.pack("<I", len(json_bytes)) + struct.pack("<I", 0x4E4F534A) + json_bytes
    chunks += struct.pack("<I", len(bin_blob)) + struct.pack("<I", 0x004E4942) + bin_blob
    total = 12 + len(chunks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + chunks)
    return path.stat().st_size


def main() -> None:
    # Order: root behind implant, metal, gingiva, crown on top (tooth-first silhouette)
    parts = [
        build_root_shell(),
        build_fixture(),
        build_abutment(),
        build_gingiva(),
        build_enamel_crown(),
        build_ceramic_cap(),
    ]
    out = OUT_DIR / "model.glb"
    size = write_multi_glb(out, parts)
    (OUT_DIR / "LICENSE.txt").write_text(
        "CC0-1.0\n\n"
        "Original procedural dental tech showcase (tooth + implant cutaway).\n"
        "Not a licensed studio scan. Not a medical device claim.\n"
        "Premium client path uses photoreal still until quality=approved.\n",
        encoding="utf-8",
    )
    (OUT_DIR / "CREDITS.txt").write_text(
        "Dental tech showcase\n"
        "GLB: scripts/generate_dental_showcase_glb.py (lab / future)\n"
        "Premium still: showcases/dental/preview.jpg (commercial presentation)\n"
        "License mesh: CC0-1.0 · Still: Virtus-generated product visual\n",
        encoding="utf-8",
    )
    verts = sum(len(p.positions) // 3 for p in parts)
    tris = sum(len(p.indices) // 3 for p in parts)
    print(f"Wrote {out} ({size} bytes, {verts} verts, {tris} tris, {len(parts)} parts)")
    print("NOTE: Premium sold demo uses preview.jpg until quality=approved")


if __name__ == "__main__":
    main()
