#!/usr/bin/env python3
"""Generate original CC0 low-poly hero GLBs for every Factory niche (research_3d).

Includes PBR materials (ceramic / gloss / metal) — no network, tiny files.
Usage (repo root):
  py -3.12 scripts/generate_research_3d_presets.py
  py -3.12 scripts/generate_research_3d_presets.py --niche dental
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "dashboard" / "backend" / "_research_3d" / "scenes"


@dataclass(frozen=True)
class PbrMaterial:
    name: str
    base_color: tuple[float, float, float, float]
    metallic: float
    roughness: float
    emissive: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class MeshData:
    positions: list[float]
    normals: list[float]
    indices: list[int]
    name: str


def _align4(n: int) -> int:
    return (4 - (n % 4)) % 4


class MeshBuilder:
    def __init__(self) -> None:
        self.positions: list[float] = []
        self.normals: list[float] = []
        self.indices: list[int] = []

    def vert(self, x: float, y: float, z: float, nx: float, ny: float, nz: float) -> int:
        self.positions.extend((x, y, z))
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        self.normals.extend((nx / ln, ny / ln, nz / ln))
        return len(self.positions) // 3 - 1

    def tri(self, a: int, b: int, c: int) -> None:
        self.indices.extend((a, b, c))

    def quad(self, a: int, b: int, c: int, d: int) -> None:
        self.tri(a, b, c)
        self.tri(a, c, d)

    def lathe(
        self,
        profile: list[tuple[float, float]],
        *,
        segments: int = 12,
        y_bias: float = 0.0,
    ) -> None:
        """profile: list of (radius, y)."""
        rings: list[list[int]] = []
        for r, y in profile:
            ring: list[int] = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                x, z = math.cos(a) * r, math.sin(a) * r
                ring.append(self.vert(x, y + y_bias, z, x, 0.1, z))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for i in range(segments):
                j = (i + 1) % segments
                self.quad(r0[i], r0[j], r1[j], r1[i])
        # caps
        if profile:
            top_r, top_y = profile[0]
            bot_r, bot_y = profile[-1]
            if top_r > 0.001:
                tc = self.vert(0, top_y + y_bias + 0.001, 0, 0, 1, 0)
                for i in range(segments):
                    j = (i + 1) % segments
                    self.tri(tc, rings[0][i], rings[0][j])
            if bot_r > 0.001:
                bc = self.vert(0, bot_y + y_bias - 0.001, 0, 0, -1, 0)
                for i in range(segments):
                    j = (i + 1) % segments
                    self.tri(bc, rings[-1][j], rings[-1][i])

    def box(self, sx: float, sy: float, sz: float, *, cy: float = 0.0) -> None:
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        faces = [
            # +Z
            ((-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz), (0, 0, 1)),
            # -Z
            ((hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz), (0, 0, -1)),
            # +X
            ((hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (1, 0, 0)),
            # -X
            ((-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz), (-1, 0, 0)),
            # +Y
            ((-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz), (0, 1, 0)),
            # -Y
            ((-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (0, -1, 0)),
        ]
        for a, b, c, d, n in faces:
            ia = self.vert(a[0], a[1] + cy, a[2], *n)
            ib = self.vert(b[0], b[1] + cy, b[2], *n)
            ic = self.vert(c[0], c[1] + cy, c[2], *n)
            id_ = self.vert(d[0], d[1] + cy, d[2], *n)
            self.quad(ia, ib, ic, id_)

    def finish(self, name: str) -> MeshData:
        return MeshData(self.positions, self.normals, self.indices, name)


def mesh_dental() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.15, 0.52), (0.28, 0.32), (0.22, 0.0), (0.08, -0.35)], segments=14)
    return b.finish("DentalTooth")


def mesh_auto() -> MeshData:
    b = MeshBuilder()
    # tire
    b.lathe([(0.32, 0.12), (0.38, 0.0), (0.32, -0.12)], segments=16)
    # hub
    b.lathe([(0.14, 0.06), (0.14, -0.06)], segments=12)
    return b.finish("AutoWheel")


def mesh_law() -> MeshData:
    b = MeshBuilder()
    b.box(0.55, 0.06, 0.08, cy=0.28)  # beam
    b.box(0.07, 0.4, 0.07, cy=0.0)  # pillar
    # pans as flat disks via short lathe, shifted in x by rewriting after
    def pan(x_off: float) -> None:
        start = len(b.positions) // 3
        b.lathe([(0.02, 0.02), (0.14, 0.0), (0.02, -0.02)], segments=10, y_bias=0.12)
        for i in range(start, len(b.positions) // 3):
            b.positions[i * 3] += x_off

    pan(-0.28)
    pan(0.28)
    return b.finish("LawScales")


def mesh_beauty() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.08, 0.45), (0.14, 0.3), (0.14, -0.05), (0.1, -0.25)], segments=12)
    b.box(0.06, 0.12, 0.06, cy=0.52)  # cap
    return b.finish("BeautyBottle")


def mesh_energy() -> MeshData:
    b = MeshBuilder()
    b.box(0.7, 0.04, 0.45, cy=0.1)
    b.box(0.74, 0.03, 0.49, cy=0.05)  # frame
    return b.finish("SolarPanel")


def mesh_green() -> MeshData:
    b = MeshBuilder()
    # leaf-like flattened lathe
    b.lathe([(0.02, 0.4), (0.22, 0.15), (0.18, -0.05), (0.02, -0.35)], segments=10)
    return b.finish("Leaf")


def mesh_computer() -> MeshData:
    b = MeshBuilder()
    b.box(0.55, 0.35, 0.04, cy=0.2)  # screen
    b.box(0.6, 0.04, 0.35, cy=-0.05)  # base/keyboard
    return b.finish("Laptop")


def mesh_appliance() -> MeshData:
    b = MeshBuilder()
    b.box(0.45, 0.6, 0.4, cy=0.05)
    b.lathe([(0.12, 0.28), (0.12, 0.18)], segments=10)  # dial
    return b.finish("Appliance")


def mesh_handwerk() -> MeshData:
    b = MeshBuilder()
    b.box(0.08, 0.55, 0.08, cy=0.0)  # handle
    b.box(0.32, 0.14, 0.12, cy=0.28)  # head
    return b.finish("Hammer")


def mesh_generic() -> MeshData:
    b = MeshBuilder()
    b.box(0.5, 0.35, 0.08, cy=0.15)
    b.box(0.08, 0.35, 0.08, cy=-0.15)  # post
    return b.finish("StoreSign")


NICHE_PRESETS: dict[str, tuple[Callable[[], MeshData], PbrMaterial, str]] = {
    "dental": (
        mesh_dental,
        PbrMaterial("CeramicGloss", (0.96, 0.95, 0.92, 1.0), 0.05, 0.12),
        "Stylized ceramic tooth — clinic hero",
    ),
    "auto": (
        mesh_auto,
        PbrMaterial("TireRubberMetal", (0.12, 0.12, 0.12, 1.0), 0.35, 0.55),
        "Stylized workshop wheel — auto hero",
    ),
    "law": (
        mesh_law,
        PbrMaterial("BrushedGold", (0.83, 0.69, 0.22, 1.0), 0.85, 0.28),
        "Stylized scales of justice — law hero",
    ),
    "beauty": (
        mesh_beauty,
        PbrMaterial("GlossBottle", (0.92, 0.45, 0.7, 1.0), 0.1, 0.18),
        "Stylized cosmetic bottle — beauty hero",
    ),
    "energy": (
        mesh_energy,
        PbrMaterial(
            "SolarGlass",
            (0.15, 0.28, 0.45, 1.0),
            0.6,
            0.2,
            emissive=(0.05, 0.12, 0.05),
        ),
        "Stylized solar panel — energy hero",
    ),
    "green": (
        mesh_green,
        PbrMaterial("LeafSatin", (0.28, 0.72, 0.35, 1.0), 0.0, 0.45),
        "Stylized leaf — garden hero",
    ),
    "computer": (
        mesh_computer,
        PbrMaterial("DeviceAnodized", (0.2, 0.35, 0.55, 1.0), 0.55, 0.32),
        "Stylized laptop — PC-service hero",
    ),
    "appliance": (
        mesh_appliance,
        PbrMaterial("ApplianceSteel", (0.72, 0.75, 0.78, 1.0), 0.7, 0.35),
        "Stylized appliance body — Hausgeraete hero",
    ),
    "handwerk": (
        mesh_handwerk,
        PbrMaterial("ToolSteelWood", (0.55, 0.4, 0.2, 1.0), 0.4, 0.4),
        "Stylized hammer — Handwerk hero",
    ),
    "generic": (
        mesh_generic,
        PbrMaterial("StorefrontMatte", (0.35, 0.45, 0.55, 1.0), 0.15, 0.55),
        "Stylized storefront sign — generic hero",
    ),
}


def write_glb(path: Path, mesh: MeshData, material: PbrMaterial, *, niche: str) -> int:
    positions, normals, indices = mesh.positions, mesh.normals, mesh.indices
    pos_bytes = struct.pack("<" + "f" * len(positions), *positions)
    norm_bytes = struct.pack("<" + "f" * len(normals), *normals)
    assert max(indices) < 65535
    idx_bytes = struct.pack("<" + "H" * len(indices), *indices)
    if len(idx_bytes) % 4:
        idx_bytes += b"\x00" * _align4(len(idx_bytes))

    bin_blob = pos_bytes + norm_bytes + idx_bytes
    pos_len = len(pos_bytes)
    norm_len = len(norm_bytes)
    idx_len = len(indices) * 2

    xs, ys, zs = positions[0::3], positions[1::3], positions[2::3]
    min_p = [min(xs), min(ys), min(zs)]
    max_p = [max(xs), max(ys), max(zs)]

    pbr: dict = {
        "baseColorFactor": list(material.base_color),
        "metallicFactor": material.metallic,
        "roughnessFactor": material.roughness,
    }
    mat: dict = {
        "name": material.name,
        "pbrMetallicRoughness": pbr,
        "doubleSided": True,
    }
    if any(material.emissive):
        mat["emissiveFactor"] = list(material.emissive)

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": f"Virtus Core research_3d preset ({niche})",
        },
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"mesh": 0, "name": f"{niche}_hero"}],
        "materials": [mat],
        "meshes": [
            {
                "name": mesh.name,
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1},
                        "indices": 2,
                        "material": 0,
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

    chunks = bytearray()
    chunks += struct.pack("<I", len(json_bytes))
    chunks += struct.pack("<I", 0x4E4F534A)
    chunks += json_bytes
    chunks += struct.pack("<I", len(bin_blob))
    chunks += struct.pack("<I", 0x004E4942)
    chunks += bin_blob

    total = 12 + len(chunks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + chunks)
    return path.stat().st_size


def write_license_pack(scene_dir: Path, *, niche: str, blurb: str, material: PbrMaterial) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "LICENSE.txt").write_text(
        "CC0-1.0\n\n"
        f"Original low-poly hero mesh for Virtus Core niche '{niche}'.\n"
        "Released into the public domain under CC0 1.0 Universal.\n"
        "No third-party model was downloaded for this file.\n",
        encoding="utf-8",
    )
    (scene_dir / "CREDITS.txt").write_text(
        f"Asset: hero.glb ({blurb})\n"
        f"Author: Virtus Core (original mesh + PBR material '{material.name}')\n"
        f"Source: scripts/generate_research_3d_presets.py\n"
        f"License: CC0-1.0 Universal\n"
        f"Material: metallic={material.metallic}, roughness={material.roughness}\n"
        f"Date: 2026-07-19\n"
        f"Notes: Research preset for niche={niche}. Not Path A production.\n",
        encoding="utf-8",
    )


def generate_niche(niche: str) -> dict:
    if niche not in NICHE_PRESETS:
        raise SystemExit(f"unknown niche: {niche}")
    mesh_fn, material, blurb = NICHE_PRESETS[niche]
    scene_dir = SCENES / niche
    size = write_glb(scene_dir / "hero.glb", mesh_fn(), material, niche=niche)
    write_license_pack(scene_dir, niche=niche, blurb=blurb, material=material)
    return {"niche": niche, "bytes": size, "material": material.name, "blurb": blurb}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="", help="Single niche id, or empty = all presets")
    args = parser.parse_args()
    niches = [args.niche] if args.niche else list(NICHE_PRESETS.keys())
    rows = [generate_niche(n) for n in niches]
    for r in rows:
        print(f"{r['niche']:12s} {r['bytes']:5d} B  {r['material']:20s}  {r['blurb']}")
    print(f"done: {len(rows)} presets -> {SCENES}")


if __name__ == "__main__":
    main()
