#!/usr/bin/env python3
"""Build Virtus Core Project Canon PDF from the living Markdown source.

Usage (repo root):
  py -3.12 scripts/build_project_canon_pdf.py

Outputs:
  docs/canon/Virtus_Core_Project_Canon_RC1_v1.0.pdf
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "canon" / "VIRTUS_CORE_PROJECT_CANON_RC1.md"
OUT = ROOT / "docs" / "canon" / "Virtus_Core_Project_Canon_RC1_v1.0.pdf"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_B = Path(r"C:\Windows\Fonts\arialbd.ttf")


class CanonPDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_x(self.l_margin)
        self.set_font("Canon", "B", 9)
        self.set_text_color(80, 80, 90)
        self.cell(0, 6, "Virtus Core - Project Canon (RC1)  |  v1.0", align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_draw_color(200, 200, 210)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_x(self.l_margin)
        self.set_font("Canon", size=8)
        self.set_text_color(120, 120, 130)
        self.cell(0, 8, f"{self.page_no()}", align="C")

    def write_block(self, text: str, *, size: int = 9, bold: bool = False, h: float = 5) -> None:
        self.set_x(self.l_margin)
        self.set_font("Canon", "B" if bold else "", size)
        self.multi_cell(0, h, text, new_x="LMARGIN", new_y="NEXT")


def _strip_md(line: str) -> str:
    s = line.rstrip("\n")
    s = re.sub(r"^#{1,6}\s+", "", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"^>\s?", "", s)
    # Keep PDF font-safe (Arial): arrows / status symbols → ASCII
    repl = {
        "↓": "->",
        "→": "->",
        "·": "|",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "€": "EUR",
        "✅": "[OK]",
        "🔄": "[WIP]",
        "🟡": "[HOLD]",
        "⚠": "[!]",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return s


def build() -> Path:
    if not SRC.is_file():
        raise SystemExit(f"Missing source: {SRC}")
    if not FONT.is_file():
        raise SystemExit(f"Missing font: {FONT}")

    text = SRC.read_text(encoding="utf-8")
    pdf = CanonPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(16, 16, 16)
    pdf.add_font("Canon", "", str(FONT))
    pdf.add_font("Canon", "B", str(FONT_B if FONT_B.is_file() else FONT))
    pdf.add_page()

    # Cover
    pdf.set_text_color(20, 24, 40)
    pdf.ln(36)
    pdf.write_block("Virtus Core", size=22, bold=True, h=10)
    pdf.write_block("Project Canon (RC1)", size=16, bold=True, h=8)
    pdf.ln(6)
    pdf.set_text_color(60, 60, 70)
    pdf.write_block(
        "Living technical source of truth for Owner / CTO / Investor\n"
        "Read in ~30 minutes. Update after each major stage.",
        size=11,
        h=6,
    )
    pdf.ln(10)
    pdf.write_block("Version v1.0  |  2026-07-23", size=11, bold=True, h=6)
    pdf.ln(8)
    pdf.set_text_color(100, 40, 40)
    pdf.write_block(
        "Status: RC1 TECHNICAL PASS / RELEASE HOLD\n"
        "(push only after clean tree + full pytest green + Release Approved)",
        size=10,
        h=5,
    )

    pdf.add_page()
    in_code = False
    in_table = False

    for raw in text.splitlines():
        if raw.strip() == "---":
            continue
        if raw.startswith("```"):
            in_code = not in_code
            pdf.ln(2)
            continue

        if in_code:
            pdf.set_text_color(30, 40, 55)
            line = _strip_md(raw.replace("\t", "  "))
            if len(line) > 105:
                line = line[:102] + "..."
            pdf.write_block(line or " ", size=8, h=4)
            continue

        # Tables: render as compact lines
        if raw.startswith("|") and "---" not in raw:
            in_table = True
            cells = [c.strip() for c in raw.strip("|").split("|")]
            bold = bool(cells and cells[0].lower() in {
                "module", "principle", "package", "gate", "area", "version", "ready"
            })
            pdf.set_text_color(40, 40, 50)
            row = "  |  ".join(_strip_md(c) for c in cells if c)
            pdf.write_block(row, size=8, bold=bold, h=4.2)
            continue
        if in_table and not raw.startswith("|"):
            in_table = False
            pdf.ln(2)

        if not raw.strip():
            pdf.ln(2)
            continue

        if raw.startswith("#"):
            level = len(raw) - len(raw.lstrip("#"))
            body = _strip_md(raw)
            if level == 1:
                continue  # cover already has title
            if level == 2:
                pdf.ln(4)
                pdf.set_text_color(15, 25, 50)
                pdf.write_block(body, size=13, bold=True, h=7)
                pdf.set_draw_color(180, 185, 200)
                y = pdf.get_y()
                pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
                pdf.ln(3)
            elif level == 3:
                pdf.ln(2)
                pdf.set_text_color(30, 40, 60)
                pdf.write_block(body, size=11, bold=True, h=6)
            else:
                pdf.write_block(body, size=10, bold=True, h=5)
            continue

        if raw.lstrip().startswith("- ") or raw.lstrip().startswith("* "):
            body = _strip_md(raw.lstrip()[2:])
            pdf.set_text_color(35, 35, 45)
            pdf.write_block(f"-  {body}", size=9, h=5)
            continue

        if raw.startswith(">"):
            body = _strip_md(raw)
            pdf.set_text_color(50, 60, 90)
            pdf.write_block(f'"{body}"', size=9, bold=True, h=5)
            continue

        body = _strip_md(raw)
        pdf.set_text_color(35, 35, 45)
        pdf.write_block(body, size=9, h=5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
    print(f"Size {path.stat().st_size} bytes")
    sys.exit(0)
