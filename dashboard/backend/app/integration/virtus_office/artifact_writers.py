"""Artifact writers for Virtus Office Stage 3 — PDF (fpdf2), DOCX/XLSX (OOXML zip).

No python-docx / openpyxl dependency required.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

_UNICODE_FONT_CANDIDATES: tuple[str, ...] = (
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)


def _resolve_unicode_font() -> str | None:
    for path in _UNICODE_FONT_CANDIDATES:
        if Path(path).is_file():
            return path
    return None


def write_pdf_bytes(*, title: str, paragraphs: list[str], meta_lines: list[str] | None = None) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    font_path = _resolve_unicode_font()
    if font_path:
        pdf.add_font("OfficeSans", fname=font_path)
        body_font = "OfficeSans"
        # Keep full Unicode (Cyrillic UK/RU etc.) — Helvetica would become ????
        def safe(text: str) -> str:
            return (text or "").replace("\t", " ") or " "

    else:
        body_font = "Helvetica"

        def safe(text: str) -> str:
            return _pdf_latin1_safe(text)

    pdf.set_font(body_font, size=14)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 8, safe(title))
    pdf.ln(2)
    if meta_lines:
        pdf.set_font(body_font, size=9)
        for line in meta_lines:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, safe(line))
        pdf.ln(3)
    pdf.set_font(body_font, size=11)
    for para in paragraphs:
        text = (para or "").strip()
        if not text:
            pdf.ln(3)
            continue
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 6, safe(text))
        pdf.ln(2)
    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("latin-1", errors="replace")


def _pdf_latin1_safe(text: str) -> str:
    """Fallback when no Unicode TTF is available — non-Latin becomes '?'."""
    raw = (text or "").replace("\t", " ")
    out: list[str] = []
    for ch in raw:
        o = ord(ch)
        if ch in "\n\r":
            out.append("\n")
        elif 32 <= o <= 255:
            out.append(ch)
        else:
            out.append("?")
    return "".join(out) or " "


# Back-compat alias (Bewerbung PDF writer historically imported this name).
_pdf_safe = _pdf_latin1_safe


def write_docx_bytes(*, title: str, paragraphs: list[str], headings: list[str] | None = None) -> bytes:
    """Minimal OOXML DOCX (ZIP)."""
    body_parts: list[str] = []
    body_parts.append(_p(title, bold=True))
    for h in headings or []:
        if h.strip():
            body_parts.append(_p(h.strip(), bold=True))
    for para in paragraphs:
        body_parts.append(_p(para or ""))
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body_parts)}<w:sectPr/></w:body></w:document>"
    )
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
    return buf.getvalue()


def _p(text: str, *, bold: bool = False) -> str:
    t = escape(text or "")
    if bold:
        return f"<w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space=\"preserve\">{t}</w:t></w:r></w:p>"
    return f"<w:p><w:r><w:t xml:space=\"preserve\">{t}</w:t></w:r></w:p>"


def write_xlsx_bytes(*, sheet_name: str, headers: list[str], rows: list[list[Any]]) -> bytes:
    """Minimal SpreadsheetML XLSX (ZIP)."""
    safe_sheet = re.sub(r"[^\w\- ]", "", sheet_name or "Sheet1")[:31] or "Sheet1"
    # shared strings
    strings: list[str] = []
    index: dict[str, int] = {}

    def s_idx(val: str) -> int:
        if val not in index:
            index[val] = len(strings)
            strings.append(val)
        return index[val]

    def cell_xml(col: int, row: int, value: Any) -> str:
        ref = f"{_col(col)}{row}"
        if value is None or value == "":
            return f'<c r="{ref}"/>'
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f'<c r="{ref}"><v>{value}</v></c>'
        # dates/currency as strings for Stage 3 fidelity
        i = s_idx(str(value))
        return f'<c r="{ref}" t="s"><v>{i}</v></c>'

    all_rows = [headers] + rows
    sheet_rows = []
    for r_i, row in enumerate(all_rows, start=1):
        cells = "".join(cell_xml(c_i, r_i, val) for c_i, val in enumerate(row, start=1))
        sheet_rows.append(f'<row r="{r_i}">{cells}</row>')

    sst_items = "".join(
        f"<si><t>{escape(s)}</t></si>" for s in strings
    )
    shared = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(strings)}" uniqueCount="{len(strings)}">{sst_items}</sst>'
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{escape(safe_sheet)}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    wb_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
        zf.writestr("xl/sharedStrings.xml", shared)
    return buf.getvalue()


def write_csv_bytes(*, headers: list[str], rows: list[list[Any]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for row in rows:
        w.writerow(row)
    return buf.getvalue().encode("utf-8")


def _col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def artifact_filename(base: str, ext: str) -> str:
    stem = re.sub(r"[^\w\-]+", "_", (base or "result").rsplit(".", 1)[0])[:48] or "result"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{stem}_{ts}.{ext.lstrip('.')}"
