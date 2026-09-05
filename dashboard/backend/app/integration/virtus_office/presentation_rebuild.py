"""A-lite presentation PDF rebuild for Virtus Office Businessplan.

Presentation-grade rebuild (not pixel-perfect):
  - keep page count and page size
  - restore embedded images at extracted positions
  - replace page text with translated text in free bands

Stack: pypdf (extract) + fpdf2 (rebuild). No new heavy PDF deps.
"""

from __future__ import annotations

import io
import re
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ContentStream


def extract_presentation_pdf(data: bytes) -> dict[str, Any]:
    """Extract per-page text, size, and embedded images with cm/Do positions."""
    if not data:
        return {"ok": False, "error": "empty_pdf", "pages": [], "page_count": 0, "image_count": 0}

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        return {
            "ok": False,
            "error": "pdf_read_failed",
            "detail": str(exc)[:200],
            "pages": [],
            "page_count": 0,
            "image_count": 0,
        }

    pages_out: list[dict[str, Any]] = []
    total_images = 0

    for idx, page in enumerate(reader.pages):
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        text = (page.extract_text() or "").strip()
        spans = _extract_text_spans(page)
        images = _extract_page_images(page, page_height=height)
        total_images += len(images)
        pages_out.append(
            {
                "page_index": idx,
                "width_pt": width,
                "height_pt": height,
                "text": text,
                "spans": spans,
                "images": images,
            }
        )

    return {
        "ok": True,
        "error": None,
        "pages": pages_out,
        "page_count": len(pages_out),
        "image_count": total_images,
    }


def rebuild_presentation_pdf(
    pages: list[dict[str, Any]],
    *,
    title: str = "Translation",
    meta_lines: list[str] | None = None,
) -> dict[str, Any]:
    """Rebuild a multi-page PDF from translated page dicts + images."""
    if not pages:
        return {"ok": False, "error": "no_pages", "bytes": b"", "page_count": 0, "image_count": 0}

    try:
        from fpdf import FPDF
    except Exception as exc:
        return {"ok": False, "error": "fpdf_missing", "detail": str(exc)[:160], "bytes": b""}

    pdf = FPDF(unit="pt", format="A4")
    pdf.set_auto_page_break(auto=False, margin=36)
    font_family = _register_unicode_font(pdf)

    images_placed = 0
    for i, page in enumerate(pages):
        w = float(page.get("width_pt") or 595.28)
        h = float(page.get("height_pt") or 841.89)
        pdf.add_page(format=(w, h))

        if i == 0 and meta_lines:
            pdf.set_font(font_family, size=7)
            pdf.set_text_color(110, 110, 110)
            y = 18
            for line in meta_lines[:6]:
                pdf.set_xy(36, y)
                pdf.cell(w - 72, 9, _pdf_safe(line), new_x="LMARGIN", new_y="NEXT")
                y = pdf.get_y()
            pdf.set_text_color(0, 0, 0)

        img_boxes = list(page.get("images") or [])
        for img in img_boxes:
            if _place_image(pdf, img, page_h=h):
                images_placed += 1

        text = str(page.get("translated_text") or page.get("text") or "").strip()
        if text:
            _draw_text_avoiding_images(
                pdf,
                text=text,
                page_w=w,
                page_h=h,
                img_boxes=img_boxes,
                font_family=font_family,
                top_margin=48 if i == 0 and meta_lines else 36,
            )

    out = pdf.output()
    blob = bytes(out) if isinstance(out, (bytes, bytearray)) else str(out).encode(
        "latin-1", errors="replace"
    )
    return {
        "ok": True,
        "bytes": blob,
        "page_count": len(pages),
        "image_count": images_placed,
        "delivery_mode": "presentation_rebuild",
        "title": title,
    }


def translate_presentation_pages(
    pages: list[dict[str, Any]],
    *,
    source_language: str,
    target_language: str,
    preserve_names: bool = True,
    preserve_numbers_dates: bool = True,
    translate_fn=None,
) -> dict[str, Any]:
    """Translate each page's text via translate_fn (default: translator.translate_text)."""
    if translate_fn is None:
        from app.integration.virtus_office.translator import translate_text as translate_fn

    out_pages: list[dict[str, Any]] = []
    providers: list[str] = []
    for page in pages:
        text = str(page.get("text") or "").strip()
        if not text:
            new_page = dict(page)
            new_page["translated_text"] = ""
            out_pages.append(new_page)
            continue
        labeled = f"[Page {int(page.get('page_index', 0)) + 1}]\n{text}"
        tr = translate_fn(
            labeled,
            source_language=source_language,
            target_language=target_language,
            preserve_names=preserve_names,
            preserve_numbers_dates=preserve_numbers_dates,
        )
        if not tr.get("ok"):
            return {
                "ok": False,
                "error": tr.get("error") or "translate_failed",
                "detail": tr.get("detail") or f"page {page.get('page_index')}",
                "pages": out_pages,
                "provider": tr.get("provider"),
            }
        translated = str(tr.get("text") or "")
        translated = re.sub(r"^\[Page\s+\d+\]\s*", "", translated.strip(), flags=re.I)
        translated = _strip_llm_markdown(translated)
        new_page = dict(page)
        new_page["translated_text"] = translated
        out_pages.append(new_page)
        if tr.get("provider"):
            providers.append(str(tr["provider"]))

    provider = providers[0] if providers else None
    if providers and any(p != provider for p in providers):
        provider = "mixed"
    full_out = "\n\n".join(str(p.get("translated_text") or "") for p in out_pages)
    full_in = "\n\n".join(str(p.get("text") or "") for p in out_pages)
    return {
        "ok": True,
        "pages": out_pages,
        "provider": provider,
        "quality_input_text": full_in,
        "quality_output_text": full_out,
        "chars_in": len(full_in),
        "chars_out": len(full_out),
        "chunks": len(out_pages),
    }


def _extract_text_spans(page) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []

    def visitor(text, cm, tm, font_dict, font_size):  # noqa: ANN001
        t = (text or "").strip()
        if not t:
            return
        spans.append(
            {
                "text": text,
                "x": float(tm[4]),
                "y": float(tm[5]),
                "size": float(font_size or 10),
            }
        )

    try:
        page.extract_text(visitor_text=visitor)
    except Exception:
        return []
    return spans


def _extract_page_images(page, *, page_height: float) -> list[dict[str, Any]]:
    placements = _image_placements(page)
    images_out: list[dict[str, Any]] = []
    try:
        page_images = list(page.images)
    except Exception:
        page_images = []

    by_name: dict[str, Any] = {}
    for img in page_images:
        name = str(getattr(img, "name", "") or "").lstrip("/")
        by_name[name] = img
        stem = name.rsplit(".", 1)[0]
        by_name[stem] = img

    used: set[int] = set()
    for place in placements:
        name = place["name"]
        img = by_name.get(name) or by_name.get(f"{name}.png") or by_name.get(f"{name}.jpg")
        png = b""
        iw = ih = None
        if img is not None:
            try:
                png = bytes(img.data)
                if getattr(img, "image", None) is not None:
                    iw, ih = img.image.size
            except Exception:
                png = b""
            used.add(id(img))
        if not png:
            continue
        images_out.append(
            {
                "name": name,
                "png_bytes": png,
                "x": place["x"],
                "y": place["y"],
                "draw_w": place["w"],
                "draw_h": place["h"],
                "pixel_w": iw,
                "pixel_h": ih,
                "page_height": page_height,
            }
        )

    for img in page_images:
        if id(img) in used:
            continue
        try:
            png = bytes(img.data)
        except Exception:
            continue
        images_out.append(
            {
                "name": str(getattr(img, "name", "img")),
                "png_bytes": png,
                "x": 72.0,
                "y": 72.0,
                "draw_w": min(400.0, float(page.mediabox.width) - 144),
                "draw_h": 220.0,
                "pixel_w": None,
                "pixel_h": None,
                "page_height": page_height,
                "fallback_placement": True,
            }
        )
    return images_out


def _image_placements(page) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        contents = page.get_contents()
        if contents is None:
            return out
        cs = ContentStream(contents, page)
        last_cm: list[float] | None = None
        for operands, operator in cs.operations:
            if operator == b"cm" and operands and len(operands) >= 6:
                try:
                    last_cm = [float(operands[i]) for i in range(6)]
                except Exception:
                    last_cm = None
            elif operator == b"Do" and operands:
                name = str(operands[0]).lstrip("/")
                if last_cm and len(last_cm) == 6:
                    a, _b, _c, d, e, f = last_cm
                    out.append(
                        {
                            "name": name,
                            "w": abs(a),
                            "h": abs(d),
                            "x": e,
                            "y": f,
                        }
                    )
                last_cm = None
    except Exception:
        return out
    return out


def _strip_llm_markdown(text: str) -> str:
    t = text or ""
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"(?m)^\s*#{1,6}\s*", "", t)
    return t


def _register_unicode_font(pdf) -> str:
    candidates = (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    bold_candidates = (
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for path in candidates:
        try:
            pdf.add_font("OfficeSans", fname=path)
            for bpath in bold_candidates:
                try:
                    pdf.add_font("OfficeSans", style="B", fname=bpath)
                    break
                except Exception:
                    continue
            else:
                # Fallback: reuse regular as bold to avoid fpdf style errors
                pdf.add_font("OfficeSans", style="B", fname=path)
            return "OfficeSans"
        except Exception:
            continue
    return "Helvetica"


def _pdf_safe(text: str) -> str:
    raw = (text or "").replace("\t", " ")
    return "".join(ch if ord(ch) >= 32 or ch in "\n\r" else " " for ch in raw) or " "


def _place_image(pdf, img: dict[str, Any], *, page_h: float) -> bool:
    data = img.get("png_bytes") or b""
    if not data:
        return False
    x = float(img.get("x") or 36)
    y_pdf = float(img.get("y") or 36)
    w = float(img.get("draw_w") or 200)
    h = float(img.get("draw_h") or 120)
    y = page_h - y_pdf - h
    try:
        pdf.image(io.BytesIO(data), x=x, y=max(12.0, y), w=w, h=h)
        return True
    except Exception:
        try:
            pdf.image(io.BytesIO(data), x=x, y=max(12.0, y), w=w)
            return True
        except Exception:
            return False


def _draw_text_avoiding_images(
    pdf,
    *,
    text: str,
    page_w: float,
    page_h: float,
    img_boxes: list[dict[str, Any]],
    font_family: str,
    top_margin: float,
) -> None:
    margin_x = 36.0
    bands = _free_vertical_bands(page_h=page_h, img_boxes=img_boxes, top_margin=top_margin)

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [ln.strip() for ln in text.splitlines() if ln.strip()] or [text]

    pdf.set_font(font_family, size=10)
    pdf.set_text_color(20, 20, 20)
    para_i = 0
    for band in bands:
        y0, y1 = band
        if y1 - y0 < 28:
            continue
        # If an image sits to the right in this vertical range, shrink text width
        usable_w = _usable_text_width(page_w=page_w, margin_x=margin_x, y0=y0, y1=y1, img_boxes=img_boxes)
        pdf.set_xy(margin_x, y0)
        while para_i < len(paragraphs):
            para = paragraphs[para_i]
            if len(para) < 80 and para.isupper():
                pdf.set_font(font_family, style="B", size=12)
            elif re.match(r"^\d{1,2}\s", para):
                pdf.set_font(font_family, style="B", size=11)
            else:
                pdf.set_font(font_family, size=10)
            before = pdf.get_y()
            if before > y1 - 16:
                break
            pdf.set_x(margin_x)
            pdf.multi_cell(usable_w, 12, _pdf_safe(para))
            after = pdf.get_y()
            if after > y1 - 8:
                para_i += 1
                break
            pdf.ln(4)
            para_i += 1
            if pdf.get_y() > y1 - 16:
                break
        if para_i >= len(paragraphs):
            break


def _usable_text_width(
    *,
    page_w: float,
    margin_x: float,
    y0: float,
    y1: float,
    img_boxes: list[dict[str, Any]],
) -> float:
    """Shrink text column when an image overlaps this band horizontally on the right."""
    right_limit = page_w - margin_x
    page_h = 0.0
    for img in img_boxes:
        page_h = float(img.get("page_height") or page_h)
    if page_h <= 0:
        page_h = 841.89
    for img in img_boxes:
        y_pdf = float(img.get("y") or 0)
        h = float(img.get("draw_h") or 0)
        img_top = page_h - y_pdf - h
        img_bot = page_h - y_pdf
        # vertical overlap with band?
        if img_bot < y0 or img_top > y1:
            continue
        x = float(img.get("x") or 0)
        if x > margin_x + 80:
            right_limit = min(right_limit, x - 12)
    return max(160.0, right_limit - margin_x)


def _free_vertical_bands(
    *,
    page_h: float,
    img_boxes: list[dict[str, Any]],
    top_margin: float,
    bottom_margin: float = 36.0,
    pad: float = 8.0,
) -> list[tuple[float, float]]:
    occupied: list[tuple[float, float]] = []
    for img in img_boxes:
        y_pdf = float(img.get("y") or 0)
        h = float(img.get("draw_h") or 0)
        y_top = page_h - y_pdf - h
        y_bot = page_h - y_pdf
        occupied.append((max(0.0, y_top - pad), min(page_h, y_bot + pad)))
    occupied.sort()
    merged: list[tuple[float, float]] = []
    for a, b in occupied:
        if not merged or a > merged[-1][1]:
            merged.append((a, b))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))

    bands: list[tuple[float, float]] = []
    cursor = top_margin
    end = page_h - bottom_margin
    for a, b in merged:
        if a > cursor:
            bands.append((cursor, min(a, end)))
        cursor = max(cursor, b)
    if cursor < end:
        bands.append((cursor, end))
    return [(a, b) for a, b in bands if b - a >= 24]
