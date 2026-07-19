#!/usr/bin/env python3
"""Generate 5 original CC0 hero examples per Factory niche + PBR materials.

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
CATALOG_OUT = ROOT / "dashboard" / "backend" / "_research_3d" / "niches" / "examples_catalog.json"


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
        x_off: float = 0.0,
        z_off: float = 0.0,
    ) -> None:
        rings: list[list[int]] = []
        for r, y in profile:
            ring: list[int] = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                x, z = math.cos(a) * r + x_off, math.sin(a) * r + z_off
                ring.append(self.vert(x, y + y_bias, z, x - x_off, 0.1, z - z_off))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for i in range(segments):
                j = (i + 1) % segments
                self.quad(r0[i], r0[j], r1[j], r1[i])
        if profile:
            top_r, top_y = profile[0]
            bot_r, bot_y = profile[-1]
            if top_r > 0.001:
                tc = self.vert(x_off, top_y + y_bias + 0.001, z_off, 0, 1, 0)
                for i in range(segments):
                    j = (i + 1) % segments
                    self.tri(tc, rings[0][i], rings[0][j])
            if bot_r > 0.001:
                bc = self.vert(x_off, bot_y + y_bias - 0.001, z_off, 0, -1, 0)
                for i in range(segments):
                    j = (i + 1) % segments
                    self.tri(bc, rings[-1][j], rings[-1][i])

    def box(
        self,
        sx: float,
        sy: float,
        sz: float,
        *,
        cx: float = 0.0,
        cy: float = 0.0,
        cz: float = 0.0,
    ) -> None:
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        faces = [
            ((-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz), (0, 0, 1)),
            ((hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz), (0, 0, -1)),
            ((hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (1, 0, 0)),
            ((-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz), (-1, 0, 0)),
            ((-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz), (0, 1, 0)),
            ((-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz), (0, -1, 0)),
        ]
        for a, b, c, d, n in faces:
            ia = self.vert(a[0] + cx, a[1] + cy, a[2] + cz, *n)
            ib = self.vert(b[0] + cx, b[1] + cy, b[2] + cz, *n)
            ic = self.vert(c[0] + cx, c[1] + cy, c[2] + cz, *n)
            id_ = self.vert(d[0] + cx, d[1] + cy, d[2] + cz, *n)
            self.quad(ia, ib, ic, id_)

    def finish(self, name: str) -> MeshData:
        return MeshData(self.positions, self.normals, self.indices, name)


# --- niche example meshes (5 each) ---


def m_dental_tooth() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.15, 0.52), (0.28, 0.32), (0.22, 0.0), (0.08, -0.35)], segments=14)
    return b.finish("Tooth")


def m_dental_mirror() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.02, 0.35), (0.02, -0.15)], segments=8)
    b.lathe([(0.16, 0.02), (0.16, -0.02)], segments=14, y_bias=0.4, x_off=0.12)
    return b.finish("DentalMirror")


def m_dental_chair() -> MeshData:
    b = MeshBuilder()
    b.box(0.5, 0.08, 0.35, cy=0.05)
    b.box(0.45, 0.35, 0.08, cy=0.28, cz=-0.12)
    b.box(0.08, 0.25, 0.08, cy=-0.15)
    return b.finish("DentalChair")


def m_dental_implant() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.06, 0.25), (0.08, 0.05), (0.05, -0.25)], segments=10)
    return b.finish("ImplantScrew")


def m_dental_floss() -> MeshData:
    b = MeshBuilder()
    b.box(0.35, 0.22, 0.12, cy=0.0)
    b.box(0.08, 0.08, 0.08, cy=0.18)
    return b.finish("FlossBox")


def m_auto_wheel() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.32, 0.12), (0.38, 0.0), (0.32, -0.12)], segments=16)
    b.lathe([(0.14, 0.06), (0.14, -0.06)], segments=12)
    return b.finish("Wheel")


def m_auto_wrench() -> MeshData:
    b = MeshBuilder()
    b.box(0.08, 0.5, 0.06, cy=0.0)
    b.box(0.22, 0.1, 0.08, cy=0.28)
    return b.finish("Wrench")


def m_auto_can() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.12, 0.28), (0.14, 0.2), (0.14, -0.2), (0.12, -0.28)], segments=12)
    return b.finish("OilCan")


def m_auto_jack() -> MeshData:
    b = MeshBuilder()
    b.box(0.35, 0.08, 0.2, cy=-0.1)
    b.box(0.08, 0.35, 0.08, cy=0.12)
    return b.finish("Jack")


def m_auto_key() -> MeshData:
    b = MeshBuilder()
    b.box(0.12, 0.35, 0.04, cy=0.05)
    b.box(0.22, 0.12, 0.04, cy=0.28)
    return b.finish("CarKey")


def m_law_scales() -> MeshData:
    b = MeshBuilder()
    b.box(0.55, 0.06, 0.08, cy=0.28)
    b.box(0.07, 0.4, 0.07, cy=0.0)

    def pan(x_off: float) -> None:
        start = len(b.positions) // 3
        b.lathe([(0.02, 0.02), (0.14, 0.0), (0.02, -0.02)], segments=10, y_bias=0.12)
        for i in range(start, len(b.positions) // 3):
            b.positions[i * 3] += x_off

    pan(-0.28)
    pan(0.28)
    return b.finish("Scales")


def m_law_gavel() -> MeshData:
    b = MeshBuilder()
    b.box(0.08, 0.45, 0.08, cy=0.0)
    b.box(0.28, 0.12, 0.12, cy=0.28)
    return b.finish("Gavel")


def m_law_book() -> MeshData:
    b = MeshBuilder()
    b.box(0.35, 0.08, 0.28, cy=0.0)
    b.box(0.33, 0.06, 0.26, cy=0.07)
    return b.finish("LawBook")


def m_law_column() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.12, 0.4), (0.1, 0.3), (0.1, -0.3), (0.14, -0.4)], segments=12)
    return b.finish("Column")


def m_law_badge() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.2, 0.04), (0.22, 0.0), (0.2, -0.04)], segments=8)
    return b.finish("Badge")


def m_beauty_bottle() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.08, 0.45), (0.14, 0.3), (0.14, -0.05), (0.1, -0.25)], segments=12)
    b.box(0.06, 0.12, 0.06, cy=0.52)
    return b.finish("Bottle")


def m_beauty_scissors() -> MeshData:
    b = MeshBuilder()
    b.box(0.06, 0.4, 0.04, cx=-0.05, cy=0.0)
    b.box(0.06, 0.4, 0.04, cx=0.05, cy=0.0)
    b.box(0.18, 0.06, 0.04, cy=0.22)
    return b.finish("Scissors")


def m_beauty_brush() -> MeshData:
    b = MeshBuilder()
    b.box(0.08, 0.35, 0.08, cy=-0.05)
    b.box(0.2, 0.12, 0.06, cy=0.25)
    return b.finish("Brush")


def m_beauty_mirror() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.02, 0.2), (0.02, -0.25)], segments=8)
    b.lathe([(0.18, 0.03), (0.18, -0.03)], segments=14, y_bias=0.28)
    return b.finish("HandMirror")


def m_beauty_cream() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.16, 0.12), (0.18, 0.05), (0.18, -0.12), (0.16, -0.18)], segments=12)
    return b.finish("CreamJar")


def m_energy_panel() -> MeshData:
    b = MeshBuilder()
    b.box(0.7, 0.04, 0.45, cy=0.1)
    b.box(0.74, 0.03, 0.49, cy=0.05)
    return b.finish("SolarPanel")


def m_energy_bulb() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.08, 0.35), (0.16, 0.2), (0.14, 0.0), (0.06, -0.15)], segments=12)
    b.box(0.08, 0.12, 0.08, cy=-0.25)
    return b.finish("Bulb")


def m_energy_battery() -> MeshData:
    b = MeshBuilder()
    b.box(0.2, 0.4, 0.2, cy=0.0)
    b.box(0.08, 0.08, 0.08, cy=0.28)
    return b.finish("Battery")


def m_energy_plug() -> MeshData:
    b = MeshBuilder()
    b.box(0.22, 0.18, 0.12, cy=0.0)
    b.box(0.04, 0.14, 0.04, cx=-0.05, cy=0.18)
    b.box(0.04, 0.14, 0.04, cx=0.05, cy=0.18)
    return b.finish("Plug")


def m_energy_inverter() -> MeshData:
    b = MeshBuilder()
    b.box(0.45, 0.28, 0.2, cy=0.0)
    b.box(0.1, 0.06, 0.06, cy=0.2)
    return b.finish("Inverter")


def m_green_leaf() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.02, 0.4), (0.22, 0.15), (0.18, -0.05), (0.02, -0.35)], segments=10)
    return b.finish("Leaf")


def m_green_pot() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.12, 0.2), (0.18, 0.05), (0.16, -0.2)], segments=12)
    b.lathe([(0.02, 0.45), (0.1, 0.3), (0.02, 0.2)], segments=8)
    return b.finish("PlantPot")


def m_green_tree() -> MeshData:
    b = MeshBuilder()
    b.box(0.08, 0.35, 0.08, cy=-0.1)
    b.lathe([(0.02, 0.35), (0.25, 0.15), (0.02, -0.05)], segments=10, y_bias=0.15)
    return b.finish("Tree")


def m_green_seed() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.06, 0.1), (0.1, 0.0), (0.06, -0.1)], segments=10)
    return b.finish("Seed")


def m_green_hose() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.08, 0.08), (0.1, 0.0), (0.08, -0.08)], segments=12)
    b.box(0.35, 0.06, 0.06, cx=0.2, cy=0.0)
    return b.finish("HoseReel")


def m_computer_laptop() -> MeshData:
    b = MeshBuilder()
    b.box(0.55, 0.35, 0.04, cy=0.2)
    b.box(0.6, 0.04, 0.35, cy=-0.05)
    return b.finish("Laptop")


def m_computer_chip() -> MeshData:
    b = MeshBuilder()
    b.box(0.3, 0.06, 0.3, cy=0.0)
    b.box(0.12, 0.04, 0.12, cy=0.06)
    return b.finish("Chip")


def m_computer_mouse() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.08, 0.08), (0.12, 0.02), (0.1, -0.08)], segments=12)
    return b.finish("Mouse")


def m_computer_hdd() -> MeshData:
    b = MeshBuilder()
    b.box(0.4, 0.12, 0.28, cy=0.0)
    return b.finish("Drive")


def m_computer_router() -> MeshData:
    b = MeshBuilder()
    b.box(0.35, 0.1, 0.22, cy=0.0)
    b.box(0.04, 0.25, 0.04, cx=-0.1, cy=0.2)
    b.box(0.04, 0.25, 0.04, cx=0.1, cy=0.2)
    return b.finish("Router")


def m_appliance_washer() -> MeshData:
    b = MeshBuilder()
    b.box(0.45, 0.6, 0.4, cy=0.05)
    b.lathe([(0.12, 0.28), (0.12, 0.18)], segments=10)
    return b.finish("Washer")


def m_appliance_fridge() -> MeshData:
    b = MeshBuilder()
    b.box(0.4, 0.7, 0.35, cy=0.0)
    b.box(0.02, 0.25, 0.02, cx=0.22, cy=0.1)
    return b.finish("Fridge")


def m_appliance_kettle() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.1, 0.25), (0.16, 0.1), (0.14, -0.15)], segments=12)
    b.box(0.12, 0.06, 0.06, cx=0.18, cy=0.05)
    return b.finish("Kettle")


def m_appliance_oven() -> MeshData:
    b = MeshBuilder()
    b.box(0.5, 0.4, 0.4, cy=0.0)
    b.box(0.35, 0.22, 0.02, cz=0.21, cy=0.0)
    return b.finish("Oven")


def m_appliance_vac() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.14, 0.2), (0.18, 0.0), (0.14, -0.15)], segments=12)
    b.box(0.08, 0.08, 0.25, cz=0.2, cy=-0.05)
    return b.finish("Vacuum")


def m_handwerk_hammer() -> MeshData:
    b = MeshBuilder()
    b.box(0.08, 0.55, 0.08, cy=0.0)
    b.box(0.32, 0.14, 0.12, cy=0.28)
    return b.finish("Hammer")


def m_handwerk_saw() -> MeshData:
    b = MeshBuilder()
    b.box(0.5, 0.08, 0.04, cy=0.05)
    b.box(0.12, 0.18, 0.06, cx=-0.28, cy=0.0)
    return b.finish("Saw")


def m_handwerk_drill() -> MeshData:
    b = MeshBuilder()
    b.box(0.28, 0.16, 0.16, cy=0.05)
    b.box(0.08, 0.2, 0.08, cy=-0.15)
    b.lathe([(0.04, 0.1), (0.04, -0.2)], segments=8, x_off=0.2)
    return b.finish("Drill")


def m_handwerk_level() -> MeshData:
    b = MeshBuilder()
    b.box(0.55, 0.08, 0.1, cy=0.0)
    b.box(0.12, 0.06, 0.06, cy=0.08)
    return b.finish("Level")


def m_handwerk_screw() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.05, 0.2), (0.06, 0.05), (0.04, -0.25)], segments=10)
    b.box(0.12, 0.04, 0.04, cy=0.24)
    return b.finish("Screw")


def m_generic_sign() -> MeshData:
    b = MeshBuilder()
    b.box(0.5, 0.35, 0.08, cy=0.15)
    b.box(0.08, 0.35, 0.08, cy=-0.15)
    return b.finish("Sign")


def m_generic_bag() -> MeshData:
    b = MeshBuilder()
    b.box(0.3, 0.28, 0.18, cy=0.0)
    b.box(0.08, 0.12, 0.04, cx=-0.08, cy=0.22)
    b.box(0.08, 0.12, 0.04, cx=0.08, cy=0.22)
    return b.finish("Bag")


def m_generic_card() -> MeshData:
    b = MeshBuilder()
    b.box(0.4, 0.25, 0.02, cy=0.0)
    return b.finish("Card")


def m_generic_pin() -> MeshData:
    b = MeshBuilder()
    b.lathe([(0.02, 0.25), (0.1, 0.05), (0.02, -0.05)], segments=10)
    return b.finish("MapPin")


def m_generic_box() -> MeshData:
    b = MeshBuilder()
    b.box(0.35, 0.25, 0.28, cy=0.0)
    return b.finish("Parcel")


MAT = {
    "ceramic": PbrMaterial("CeramicGloss", (0.96, 0.95, 0.92, 1.0), 0.05, 0.12),
    "steel": PbrMaterial("ClinicSteel", (0.75, 0.78, 0.82, 1.0), 0.75, 0.28),
    "soft": PbrMaterial("ClinicSoft", (0.85, 0.9, 0.95, 1.0), 0.05, 0.55),
    "titanium": PbrMaterial("Titanium", (0.7, 0.72, 0.74, 1.0), 0.9, 0.25),
    "plastic": PbrMaterial("ClinicPlastic", (0.4, 0.7, 0.85, 1.0), 0.1, 0.35),
    "tire": PbrMaterial("TireRubberMetal", (0.12, 0.12, 0.12, 1.0), 0.35, 0.55),
    "tool": PbrMaterial("ToolSteel", (0.55, 0.55, 0.58, 1.0), 0.7, 0.3),
    "oil": PbrMaterial("OilCan", (0.75, 0.15, 0.1, 1.0), 0.4, 0.35),
    "jack": PbrMaterial("JackRed", (0.7, 0.12, 0.1, 1.0), 0.5, 0.4),
    "key": PbrMaterial("KeyBlack", (0.15, 0.15, 0.18, 1.0), 0.3, 0.4),
    "gold": PbrMaterial("BrushedGold", (0.83, 0.69, 0.22, 1.0), 0.85, 0.28),
    "wood": PbrMaterial("Oak", (0.45, 0.3, 0.15, 1.0), 0.05, 0.55),
    "leather": PbrMaterial("Leather", (0.35, 0.2, 0.12, 1.0), 0.05, 0.6),
    "marble": PbrMaterial("Marble", (0.9, 0.9, 0.88, 1.0), 0.1, 0.35),
    "brass": PbrMaterial("Brass", (0.75, 0.6, 0.25, 1.0), 0.8, 0.3),
    "gloss": PbrMaterial("GlossBottle", (0.92, 0.45, 0.7, 1.0), 0.1, 0.18),
    "chrome": PbrMaterial("Chrome", (0.85, 0.85, 0.9, 1.0), 0.95, 0.15),
    "woodpink": PbrMaterial("BrushWood", (0.7, 0.45, 0.4, 1.0), 0.05, 0.45),
    "cream": PbrMaterial("CreamJar", (0.95, 0.9, 0.85, 1.0), 0.05, 0.3),
    "solar": PbrMaterial("SolarGlass", (0.15, 0.28, 0.45, 1.0), 0.6, 0.2, (0.05, 0.12, 0.05)),
    "glass": PbrMaterial("BulbGlass", (0.95, 0.95, 0.8, 1.0), 0.1, 0.15, (0.3, 0.25, 0.05)),
    "batt": PbrMaterial("Battery", (0.2, 0.55, 0.25, 1.0), 0.3, 0.4),
    "plug": PbrMaterial("PlugWhite", (0.9, 0.9, 0.9, 1.0), 0.05, 0.4),
    "inv": PbrMaterial("InverterGray", (0.4, 0.45, 0.5, 1.0), 0.5, 0.35),
    "leaf": PbrMaterial("LeafSatin", (0.28, 0.72, 0.35, 1.0), 0.0, 0.45),
    "pot": PbrMaterial("Terracotta", (0.7, 0.4, 0.25, 1.0), 0.05, 0.55),
    "bark": PbrMaterial("Bark", (0.35, 0.25, 0.15, 1.0), 0.05, 0.7),
    "seed": PbrMaterial("SeedBrown", (0.45, 0.35, 0.15, 1.0), 0.05, 0.5),
    "hose": PbrMaterial("HoseGreen", (0.2, 0.55, 0.25, 1.0), 0.1, 0.5),
    "device": PbrMaterial("DeviceAnodized", (0.2, 0.35, 0.55, 1.0), 0.55, 0.32),
    "chip": PbrMaterial("ChipGreen", (0.15, 0.45, 0.25, 1.0), 0.2, 0.4),
    "mouse": PbrMaterial("MouseGray", (0.35, 0.35, 0.38, 1.0), 0.15, 0.45),
    "drive": PbrMaterial("DriveSilver", (0.7, 0.72, 0.75, 1.0), 0.6, 0.35),
    "router": PbrMaterial("RouterBlack", (0.12, 0.12, 0.14, 1.0), 0.3, 0.4),
    "steel_app": PbrMaterial("ApplianceSteel", (0.72, 0.75, 0.78, 1.0), 0.7, 0.35),
    "fridge": PbrMaterial("FridgeWhite", (0.92, 0.93, 0.95, 1.0), 0.2, 0.3),
    "kettle": PbrMaterial("KettleSteel", (0.8, 0.82, 0.85, 1.0), 0.85, 0.22),
    "oven": PbrMaterial("OvenBlack", (0.15, 0.15, 0.16, 1.0), 0.4, 0.4),
    "vac": PbrMaterial("VacBlue", (0.2, 0.4, 0.75, 1.0), 0.2, 0.4),
    "hammer": PbrMaterial("ToolSteelWood", (0.55, 0.4, 0.2, 1.0), 0.4, 0.4),
    "saw": PbrMaterial("SawSteel", (0.6, 0.62, 0.65, 1.0), 0.7, 0.3),
    "drill": PbrMaterial("DrillOrange", (0.85, 0.4, 0.1, 1.0), 0.25, 0.4),
    "level": PbrMaterial("LevelYellow", (0.9, 0.75, 0.1, 1.0), 0.15, 0.4),
    "screw": PbrMaterial("ScrewSteel", (0.65, 0.65, 0.68, 1.0), 0.8, 0.28),
    "sign": PbrMaterial("StorefrontMatte", (0.35, 0.45, 0.55, 1.0), 0.15, 0.55),
    "bag": PbrMaterial("PaperBag", (0.75, 0.65, 0.45, 1.0), 0.0, 0.65),
    "card": PbrMaterial("CardWhite", (0.95, 0.95, 0.97, 1.0), 0.05, 0.45),
    "pin": PbrMaterial("PinRed", (0.85, 0.15, 0.15, 1.0), 0.2, 0.35),
    "parcel": PbrMaterial("ParcelBrown", (0.65, 0.5, 0.3, 1.0), 0.05, 0.6),
}


# niche -> list of (id, mesh_fn, material_key, title)
EXAMPLES: dict[str, list[tuple[str, Callable[[], MeshData], str, str]]] = {
    "dental": [
        ("01_tooth", m_dental_tooth, "ceramic", "Ceramic tooth"),
        ("02_mirror", m_dental_mirror, "steel", "Dental mirror"),
        ("03_chair", m_dental_chair, "soft", "Clinic chair"),
        ("04_implant", m_dental_implant, "titanium", "Implant screw"),
        ("05_floss", m_dental_floss, "plastic", "Floss pack"),
    ],
    "auto": [
        ("01_wheel", m_auto_wheel, "tire", "Workshop wheel"),
        ("02_wrench", m_auto_wrench, "tool", "Wrench"),
        ("03_oil", m_auto_can, "oil", "Oil can"),
        ("04_jack", m_auto_jack, "jack", "Car jack"),
        ("05_key", m_auto_key, "key", "Car key"),
    ],
    "law": [
        ("01_scales", m_law_scales, "gold", "Scales of justice"),
        ("02_gavel", m_law_gavel, "wood", "Gavel"),
        ("03_book", m_law_book, "leather", "Law book"),
        ("04_column", m_law_column, "marble", "Column"),
        ("05_badge", m_law_badge, "brass", "Badge"),
    ],
    "beauty": [
        ("01_bottle", m_beauty_bottle, "gloss", "Cosmetic bottle"),
        ("02_scissors", m_beauty_scissors, "chrome", "Scissors"),
        ("03_brush", m_beauty_brush, "woodpink", "Brush"),
        ("04_mirror", m_beauty_mirror, "chrome", "Hand mirror"),
        ("05_cream", m_beauty_cream, "cream", "Cream jar"),
    ],
    "energy": [
        ("01_panel", m_energy_panel, "solar", "Solar panel"),
        ("02_bulb", m_energy_bulb, "glass", "LED bulb"),
        ("03_battery", m_energy_battery, "batt", "Battery"),
        ("04_plug", m_energy_plug, "plug", "Plug"),
        ("05_inverter", m_energy_inverter, "inv", "Inverter"),
    ],
    "green": [
        ("01_leaf", m_green_leaf, "leaf", "Leaf"),
        ("02_pot", m_green_pot, "pot", "Plant pot"),
        ("03_tree", m_green_tree, "bark", "Tree"),
        ("04_seed", m_green_seed, "seed", "Seed"),
        ("05_hose", m_green_hose, "hose", "Hose reel"),
    ],
    "computer": [
        ("01_laptop", m_computer_laptop, "device", "Laptop"),
        ("02_chip", m_computer_chip, "chip", "Chip"),
        ("03_mouse", m_computer_mouse, "mouse", "Mouse"),
        ("04_drive", m_computer_hdd, "drive", "Drive"),
        ("05_router", m_computer_router, "router", "Router"),
    ],
    "appliance": [
        ("01_washer", m_appliance_washer, "steel_app", "Washer"),
        ("02_fridge", m_appliance_fridge, "fridge", "Fridge"),
        ("03_kettle", m_appliance_kettle, "kettle", "Kettle"),
        ("04_oven", m_appliance_oven, "oven", "Oven"),
        ("05_vacuum", m_appliance_vac, "vac", "Vacuum"),
    ],
    "handwerk": [
        ("01_hammer", m_handwerk_hammer, "hammer", "Hammer"),
        ("02_saw", m_handwerk_saw, "saw", "Saw"),
        ("03_drill", m_handwerk_drill, "drill", "Drill"),
        ("04_level", m_handwerk_level, "level", "Spirit level"),
        ("05_screw", m_handwerk_screw, "screw", "Screw"),
    ],
    "generic": [
        ("01_sign", m_generic_sign, "sign", "Store sign"),
        ("02_bag", m_generic_bag, "bag", "Shopping bag"),
        ("03_card", m_generic_card, "card", "Business card"),
        ("04_pin", m_generic_pin, "pin", "Map pin"),
        ("05_parcel", m_generic_box, "parcel", "Parcel"),
    ],
}


def write_glb(path: Path, mesh: MeshData, material: PbrMaterial, *, niche: str, example_id: str) -> int:
    positions, normals, indices = mesh.positions, mesh.normals, mesh.indices
    pos_bytes = struct.pack("<" + "f" * len(positions), *positions)
    norm_bytes = struct.pack("<" + "f" * len(normals), *normals)
    assert max(indices) < 65535
    idx_bytes = struct.pack("<" + "H" * len(indices), *indices)
    if len(idx_bytes) % 4:
        idx_bytes += b"\x00" * _align4(len(idx_bytes))
    bin_blob = pos_bytes + norm_bytes + idx_bytes
    pos_len, norm_len, idx_len = len(pos_bytes), len(norm_bytes), len(indices) * 2
    xs, ys, zs = positions[0::3], positions[1::3], positions[2::3]
    min_p, max_p = [min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]

    mat: dict = {
        "name": material.name,
        "pbrMetallicRoughness": {
            "baseColorFactor": list(material.base_color),
            "metallicFactor": material.metallic,
            "roughnessFactor": material.roughness,
        },
        "doubleSided": True,
    }
    if any(material.emissive):
        mat["emissiveFactor"] = list(material.emissive)

    gltf = {
        "asset": {"version": "2.0", "generator": f"Virtus research_3d {niche}/{example_id}"},
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"mesh": 0, "name": f"{niche}_{example_id}"}],
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
            {"bufferView": 1, "componentType": 5126, "count": len(normals) // 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": len(indices), "type": "SCALAR"},
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
    chunks += struct.pack("<I", len(json_bytes)) + struct.pack("<I", 0x4E4F534A) + json_bytes
    chunks += struct.pack("<I", len(bin_blob)) + struct.pack("<I", 0x004E4942) + bin_blob
    total = 12 + len(chunks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + chunks)
    return path.stat().st_size


def write_license_pack(scene_dir: Path, *, niche: str) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "LICENSE.txt").write_text(
        "CC0-1.0\n\n"
        f"Original low-poly hero examples for Virtus Core niche '{niche}'.\n"
        "Released under CC0 1.0 Universal. No third-party models downloaded.\n",
        encoding="utf-8",
    )
    lines = [
        f"Niche: {niche}",
        "Author: Virtus Core (original meshes + PBR)",
        "Source: scripts/generate_research_3d_presets.py",
        "License: CC0-1.0 Universal",
        "Examples:",
    ]
    for ex_id, _fn, mat_key, title in EXAMPLES[niche]:
        lines.append(f"  - {ex_id}.glb — {title} ({MAT[mat_key].name})")
    lines.append("Notes: Research only. Not Path A production.")
    (scene_dir / "CREDITS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_niche(niche: str) -> list[dict]:
    if niche not in EXAMPLES:
        raise SystemExit(f"unknown niche: {niche}")
    scene_dir = SCENES / niche
    write_license_pack(scene_dir, niche=niche)
    ex_dir = scene_dir / "examples"
    rows: list[dict] = []
    for i, (ex_id, mesh_fn, mat_key, title) in enumerate(EXAMPLES[niche]):
        material = MAT[mat_key]
        path = ex_dir / f"{ex_id}.glb"
        size = write_glb(path, mesh_fn(), material, niche=niche, example_id=ex_id)
        rows.append(
            {
                "niche": niche,
                "id": ex_id,
                "title": title,
                "material": material.name,
                "bytes": size,
                "path": f"scenes/{niche}/examples/{ex_id}.glb",
            }
        )
        if i == 0:
            # primary hero = first example
            size_h = write_glb(scene_dir / "hero.glb", mesh_fn(), material, niche=niche, example_id="hero")
            rows[-1]["hero_bytes"] = size_h
    return rows


def write_catalog(all_rows: list[dict]) -> None:
    by_niche: dict[str, list[dict]] = {}
    for r in all_rows:
        by_niche.setdefault(r["niche"], []).append(
            {
                "id": r["id"],
                "title": r["title"],
                "material": r["material"],
                "bytes": r["bytes"],
                "path": r["path"],
            }
        )
    payload = {
        "version": 4,
        "examples_per_niche": 5,
        "niches": by_niche,
        "runtime": "runtime/scene_engine.html",
    }
    CATALOG_OUT.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="", help="Single niche, or empty = all")
    args = parser.parse_args()
    niches = [args.niche] if args.niche else list(EXAMPLES.keys())
    all_rows: list[dict] = []
    for n in niches:
        rows = generate_niche(n)
        all_rows.extend(rows)
        for r in rows:
            print(f"{r['niche']:10s} {r['id']:14s} {r['bytes']:5d} B  {r['material']:18s}  {r['title']}")
    if not args.niche:
        write_catalog(all_rows)
        print(f"catalog -> {CATALOG_OUT}")
    print(f"done: {len(all_rows)} examples")


if __name__ == "__main__":
    main()
