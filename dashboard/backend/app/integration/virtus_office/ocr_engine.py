"""Virtus Office Stage 4 — OCR + layout Document Engine.

Providers (cascade, honesty over fake success):
  1. force stub — tests only (VIRTUS_OFFICE_OCR_PROVIDER=stub)
  2. tesseract — if pytesseract + binary available
  3. vision LLM — OpenAI-compatible multimodal when API key present
  4. fail — ocr_unavailable / ocr_failed (no silent empty PASS)

Returns structured layout when possible:
  pages → blocks → lines (+ bbox, confidence) · tables · language · text
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Callable

import httpx

# Optional test hook — set by tests; ignored when provider != stub and hook unset.
_TEST_OCR_HOOK: Callable[[bytes, str], dict[str, Any] | None] | None = None


def set_test_ocr_hook(hook: Callable[[bytes, str], dict[str, Any] | None] | None) -> None:
    """Inject OCR for unit tests. Production paths must leave this None."""
    global _TEST_OCR_HOOK
    _TEST_OCR_HOOK = hook


def ocr_capabilities() -> dict[str, Any]:
    return {
        "tesseract": _tesseract_available(),
        "vision_llm": bool(_vision_api_key()),
        "pdf_rasterize": _pdfium_available(),
        "provider_env": (os.getenv("VIRTUS_OFFICE_OCR_PROVIDER") or "auto").strip().lower(),
        "test_hook": _TEST_OCR_HOOK is not None,
    }


def empty_ocr_result(*, error: str, detail: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "provider": "none",
        "language": None,
        "confidence": 0.0,
        "text": "",
        "pages": [],
        "tables": [],
        "error": error,
        "detail": detail or error,
    }


def ocr_image_bytes(
    data: bytes,
    *,
    content_type: str = "image/png",
    page_index: int = 0,
    hint_lang: str | None = None,
) -> dict[str, Any]:
    """OCR one raster image (JPG/PNG)."""
    if not data:
        return empty_ocr_result(error="empty_image", detail="Leeres Bild")

    forced = (os.getenv("VIRTUS_OFFICE_OCR_PROVIDER") or "auto").strip().lower()

    if _TEST_OCR_HOOK is not None:
        hooked = _TEST_OCR_HOOK(data, content_type)
        if hooked is not None:
            return _normalize_result(hooked, default_page_index=page_index)

    if forced == "stub":
        return empty_ocr_result(
            error="ocr_stub_empty",
            detail="Stub-OCR ohne Test-Hook — kein Text.",
        )

    providers: list[str]
    if forced in {"tesseract", "vision", "vision_llm"}:
        providers = ["tesseract" if forced == "tesseract" else "vision"]
    else:
        providers = ["tesseract", "vision"]

    last = empty_ocr_result(error="ocr_unavailable", detail="Kein OCR-Provider verfügbar")
    best: dict[str, Any] | None = None
    best_score = -1

    for name in providers:
        if name == "tesseract":
            if not _tesseract_available():
                last = empty_ocr_result(
                    error="ocr_unavailable",
                    detail="Tesseract nicht installiert",
                )
                continue
            res = _ocr_tesseract(data, page_index=page_index, hint_lang=hint_lang)
        else:
            if not _vision_api_key():
                last = empty_ocr_result(
                    error="ocr_unavailable",
                    detail="Vision-LLM API-Key fehlt",
                )
                continue
            # Prefer vision when prior candidate failed financial honesty
            if best is not None and (best.get("financial_qa") or {}).get("passed") is True:
                continue
            res = _ocr_vision_llm(data, content_type=content_type, page_index=page_index)
        if not (res.get("ok") and str(res.get("text") or "").strip()):
            last = res if res.get("error") else last
            continue
        res = _attach_financial_qa(res)
        score = _ocr_candidate_score(res)
        if score > best_score:
            best = res
            best_score = score
        # Financial docs: keep searching until a financially honest candidate appears
        fq = res.get("financial_qa") or {}
        if fq.get("is_financial") and fq.get("passed"):
            return res
        if not fq.get("is_financial"):
            return res
        last = res

    if best is not None:
        return best
    return last


def ocr_pdf_bytes(
    data: bytes,
    *,
    max_pages: int = 20,
    hint_lang: str | None = None,
) -> dict[str, Any]:
    """Rasterize scanned PDF pages then OCR each page."""
    pages_img = rasterize_pdf_pages(data, max_pages=max_pages)
    if not pages_img:
        return empty_ocr_result(
            error="pdf_rasterize_failed",
            detail="PDF-Seiten konnten nicht gerastert werden (pypdfium2?).",
        )
    return ocr_image_pages(
        [(p["png_bytes"], "image/png") for p in pages_img],
        hint_lang=hint_lang,
        page_metas=pages_img,
    )


def ocr_image_pages(
    pages: list[tuple[bytes, str]],
    *,
    hint_lang: str | None = None,
    page_metas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """OCR multiple images as document pages (phone multi-shot)."""
    if not pages:
        return empty_ocr_result(error="no_pages", detail="Keine Seiten")

    out_pages: list[dict[str, Any]] = []
    texts: list[str] = []
    confs: list[float] = []
    provider = "none"
    lang: str | None = None
    errors: list[str] = []

    for i, (blob, ctype) in enumerate(pages):
        res = ocr_image_bytes(
            blob, content_type=ctype or "image/png", page_index=i, hint_lang=hint_lang
        )
        if not res.get("ok"):
            errors.append(str(res.get("error") or "ocr_failed"))
            # Keep empty page slot for honesty on mixed success
            empty_page = {
                "page_index": i,
                "width": (page_metas[i].get("width") if page_metas and i < len(page_metas) else None),
                "height": (page_metas[i].get("height") if page_metas and i < len(page_metas) else None),
                "blocks": [],
                "lines": [],
                "tables": [],
                "text": "",
                "confidence": 0.0,
                "error": res.get("error"),
            }
            out_pages.append(empty_page)
            continue
        provider = str(res.get("provider") or provider)
        if res.get("language") and not lang:
            lang = str(res.get("language"))
        page_list = list(res.get("pages") or [])
        if page_list:
            page = dict(page_list[0])
            page["page_index"] = i
            out_pages.append(page)
        else:
            out_pages.append(
                {
                    "page_index": i,
                    "width": None,
                    "height": None,
                    "blocks": [],
                    "lines": _lines_from_text(str(res.get("text") or "")),
                    "tables": list(res.get("tables") or []),
                    "text": str(res.get("text") or ""),
                    "confidence": float(res.get("confidence") or 0),
                }
            )
        t = str(res.get("text") or "").strip()
        if t:
            texts.append(t)
            confs.append(float(res.get("confidence") or 0))

    if not texts:
        return empty_ocr_result(
            error=errors[0] if errors else "ocr_failed",
            detail="OCR lieferte keinen Text auf allen Seiten",
        )

    full = "\n\n".join(texts)
    tables = _tables_from_pages(out_pages)
    return _attach_financial_qa(
        {
            "ok": True,
            "provider": provider,
            "language": lang,
            "confidence": round(sum(confs) / max(1, len(confs)), 3),
            "text": full,
            "pages": out_pages,
            "tables": tables,
            "error": None,
            "detail": None,
            "page_errors": errors or None,
        }
    )


def rasterize_pdf_pages(
    data: bytes,
    *,
    max_pages: int = 20,
    scale: float = 2.0,
) -> list[dict[str, Any]]:
    if not _pdfium_available():
        return []
    try:
        import pypdfium2 as pdfium  # type: ignore
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    try:
        doc = pdfium.PdfDocument(data)
        n = min(len(doc), max(1, max_pages))
        for i in range(n):
            page = doc[i]
            bitmap = page.render(scale=scale)
            pil = bitmap.to_pil()
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            out.append(
                {
                    "page_index": i,
                    "png_bytes": buf.getvalue(),
                    "width": pil.width,
                    "height": pil.height,
                }
            )
        return out
    except Exception:
        return []


def layout_from_plain_text(text: str, *, page_index: int = 0) -> dict[str, Any]:
    """Build a minimal layout envelope when only plain text exists (non-OCR path)."""
    lines = _lines_from_text(text)
    blocks = [
        {
            "text": text,
            "bbox": None,
            "confidence": 1.0,
            "lines": lines,
        }
    ]
    return {
        "ok": True,
        "provider": "text_layer",
        "language": None,
        "confidence": 1.0,
        "text": text,
        "pages": [
            {
                "page_index": page_index,
                "width": None,
                "height": None,
                "blocks": blocks,
                "lines": lines,
                "tables": [],
                "text": text,
                "confidence": 1.0,
            }
        ],
        "tables": [],
        "error": None,
        "detail": None,
    }


# ── providers ──────────────────────────────────────────────────────────────


def _tesseract_cmd() -> str | None:
    """Resolve tesseract binary (PATH or common Windows install)."""
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (
        os.getenv("TESSERACT_CMD", "").strip(),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _tesseract_available() -> bool:
    if not _tesseract_cmd():
        return False
    try:
        import pytesseract  # noqa: F401
    except Exception:
        return False
    return True


def _pdfium_available() -> bool:
    try:
        import pypdfium2  # noqa: F401

        return True
    except Exception:
        return False


def _vision_api_key() -> str:
    """Any configured vision-capable API key (for capability checks)."""
    for cfg in _vision_provider_candidates():
        if cfg.get("key"):
            return str(cfg["key"])
    return ""


def _vision_provider_candidates() -> list[dict[str, str]]:
    """Return coherent (key, base, model) configs — never mismatch Groq key → OpenAI URL.

    Order: explicit Office vision → OpenAI → Groq vision (Llama 4 Scout).
    """
    out: list[dict[str, str]] = []

    explicit_key = os.getenv("GENESIS_OFFICE_VISION_API_KEY", "").strip()
    if explicit_key:
        base = (
            os.getenv("GENESIS_OFFICE_VISION_BASE_URL", "").strip()
            or os.getenv("GENESIS_LLM_BASE_URL", "").strip()
            or "https://api.openai.com/v1"
        ).rstrip("/")
        model = (
            os.getenv("GENESIS_OFFICE_VISION_MODEL", "").strip()
            or os.getenv("GENESIS_LLM_VISION_MODEL", "").strip()
            or ("meta-llama/llama-4-scout-17b-16e-instruct" if "groq.com" in base else "gpt-4o-mini")
        )
        out.append(
            {
                "provider": "office_vision",
                "key": explicit_key,
                "base": base,
                "model": model,
            }
        )

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    genesis_llm = os.getenv("GENESIS_LLM_API_KEY", "").strip()
    groq_key = (
        os.getenv("GENESIS_GROQ_API_KEY", "").strip()
        or os.getenv("GROQ_API_KEY", "").strip()
    )

    # Misplaced Groq key in GENESIS_LLM_API_KEY
    if genesis_llm.startswith("gsk_") and not groq_key:
        groq_key = genesis_llm
        genesis_llm = ""

    openai_like = openai_key or (
        genesis_llm if genesis_llm and not genesis_llm.startswith("gsk_") else ""
    )
    if openai_like:
        base = (
            os.getenv("GENESIS_OFFICE_VISION_BASE_URL", "").strip()
            or os.getenv("GENESIS_LLM_BASE_URL", "").strip()
            or "https://api.openai.com/v1"
        ).rstrip("/")
        # If base is Groq but key is OpenAI-shaped, keep OpenAI host
        if "groq.com" in base and not openai_like.startswith("gsk_"):
            base = "https://api.openai.com/v1"
        model = (
            os.getenv("GENESIS_OFFICE_VISION_MODEL", "").strip()
            or os.getenv("GENESIS_LLM_VISION_MODEL", "").strip()
            or "gpt-4o-mini"
        )
        out.append(
            {
                "provider": "openai",
                "key": openai_like,
                "base": base,
                "model": model,
            }
        )

    if groq_key:
        out.append(
            {
                "provider": "groq",
                "key": groq_key,
                "base": (
                    os.getenv("GENESIS_GROQ_BASE_URL", "").strip()
                    or "https://api.groq.com/openai/v1"
                ).rstrip("/"),
                "model": (
                    os.getenv("GENESIS_OFFICE_VISION_MODEL", "").strip()
                    or os.getenv("GENESIS_GROQ_VISION_MODEL", "").strip()
                    or "meta-llama/llama-4-scout-17b-16e-instruct"
                ),
            }
        )

    # De-dupe identical (base, model, key prefix) while preserving order
    seen: set[str] = set()
    uniq: list[dict[str, str]] = []
    for cfg in out:
        sig = f"{cfg['base']}|{cfg['model']}|{cfg['key'][:12]}"
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(cfg)
    return uniq


def _ocr_tesseract(
    data: bytes,
    *,
    page_index: int,
    hint_lang: str | None,
) -> dict[str, Any]:
    try:
        import pytesseract
        from PIL import Image
    except Exception as exc:
        return empty_ocr_result(error="tesseract_import", detail=str(exc)[:160])

    cmd = _tesseract_cmd()
    if not cmd:
        return empty_ocr_result(error="ocr_unavailable", detail="Tesseract nicht installiert")
    pytesseract.pytesseract.tesseract_cmd = cmd

    try:
        base = Image.open(io.BytesIO(data))
        if base.mode not in {"RGB", "L"}:
            base = base.convert("RGB")
        lang = _tesseract_lang_pack(hint_lang)
        variants = _tesseract_image_variants(base)
        configs = ("--psm 6", "--psm 4", "--psm 11")
        best: dict[str, Any] | None = None
        best_score = -1
        for im in variants:
            w, h = im.size
            for cfg in configs:
                try:
                    try:
                        raw = pytesseract.image_to_data(
                            im, lang=lang, config=cfg, output_type=pytesseract.Output.DICT
                        )
                        used_lang = lang
                    except Exception:
                        used_lang = "eng"
                        raw = pytesseract.image_to_data(
                            im, lang="eng", config=cfg, output_type=pytesseract.Output.DICT
                        )
                    lines, blocks, text, conf = _layout_from_tesseract_data(
                        raw, page_w=w, page_h=h
                    )
                    if not text.strip():
                        text = (
                            pytesseract.image_to_string(im, lang=used_lang, config=cfg) or ""
                        ).strip()
                        lines = _lines_from_text(text)
                        blocks = (
                            [{"text": text, "bbox": None, "confidence": conf, "lines": lines}]
                            if text
                            else []
                        )
                    if not text.strip():
                        continue
                    tables = _tables_from_lines(lines)
                    page = {
                        "page_index": page_index,
                        "width": w,
                        "height": h,
                        "blocks": blocks,
                        "lines": lines,
                        "tables": tables,
                        "text": text,
                        "confidence": conf,
                    }
                    cand = {
                        "ok": True,
                        "provider": "tesseract",
                        "language": (hint_lang or used_lang or None),
                        "confidence": conf,
                        "text": text,
                        "pages": [page],
                        "tables": tables,
                        "error": None,
                        "detail": None,
                        "tesseract_config": cfg,
                    }
                    cand = _attach_financial_qa(cand)
                    score = _ocr_candidate_score(cand)
                    if score > best_score:
                        best = cand
                        best_score = score
                    if (cand.get("financial_qa") or {}).get("passed"):
                        return cand
                except Exception:
                    continue
        if best is not None:
            return best
        return empty_ocr_result(error="ocr_empty", detail="Tesseract: kein Text")
    except Exception as exc:
        return empty_ocr_result(error="tesseract_failed", detail=str(exc)[:200])


def _tesseract_image_variants(im: Any) -> list[Any]:
    """Upscale / contrast variants — default PIL bitmap fonts need scale for accuracy."""
    from PIL import Image, ImageOps, ImageFilter

    out: list[Any] = []
    rgb = im.convert("RGB") if im.mode != "RGB" else im
    out.append(rgb)
    try:
        gray = ImageOps.grayscale(rgb)
        # 3× LANCZOS helps thin default fonts and phone photos
        big = gray.resize((gray.width * 3, gray.height * 3), Image.Resampling.LANCZOS)
        out.append(ImageOps.autocontrast(big))
        out.append(ImageOps.autocontrast(big).filter(ImageFilter.SHARPEN))
        # Binary threshold often stabilizes invoice glyphs
        thr = big.point(lambda p: 255 if p > 160 else 0)
        out.append(thr)
    except Exception:
        pass
    return out


def _attach_financial_qa(res: dict[str, Any]) -> dict[str, Any]:
    from app.integration.virtus_office.financial_fields import validate_financial_fields

    text = str(res.get("text") or "")
    conf = res.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else None
    except Exception:
        conf_f = None
    qa = validate_financial_fields(text, confidence=conf_f)
    out = dict(res)
    out["financial_qa"] = qa
    if qa.get("needs_review"):
        out["needs_review"] = True
        out["review_warning_de"] = qa.get("warning_de")
        out["review_warning_en"] = qa.get("warning_en")
    return out


def _ocr_candidate_score(res: dict[str, Any]) -> float:
    text = str(res.get("text") or "")
    conf = float(res.get("confidence") or 0)
    score = min(1.0, len(text) / 80.0) + conf
    fq = res.get("financial_qa") or {}
    if fq.get("is_financial"):
        if fq.get("passed"):
            score += 5.0
        else:
            score -= 0.5 * len(list(fq.get("issues") or []))
    return score


def _tesseract_lang_pack(hint: str | None) -> str:
    # Prefer multi when installed; fall back to eng.
    env = (os.getenv("VIRTUS_OFFICE_TESSERACT_LANG") or "").strip()
    if env:
        return env
    code = (hint or "").lower().split("-")[0]
    mapping = {
        "de": "deu+eng",
        "en": "eng",
        "uk": "ukr+eng",
        "ru": "rus+eng",
        "pl": "pol+eng",
        "fr": "fra+eng",
        "es": "spa+eng",
        "tr": "tur+eng",
    }
    return mapping.get(code, "eng+deu")


def _layout_from_tesseract_data(
    raw: dict[str, Any],
    *,
    page_w: int,
    page_h: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, float]:
    n = len(raw.get("text") or [])
    lines_map: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    confs: list[float] = []
    for i in range(n):
        word = (raw["text"][i] or "").strip()
        if not word:
            continue
        try:
            conf = float(raw["conf"][i])
        except Exception:
            conf = -1.0
        if conf >= 0:
            confs.append(conf / 100.0)
        key = (int(raw["block_num"][i]), int(raw["par_num"][i]), int(raw["line_num"][i]))
        bbox = [
            int(raw["left"][i]),
            int(raw["top"][i]),
            int(raw["left"][i]) + int(raw["width"][i]),
            int(raw["top"][i]) + int(raw["height"][i]),
        ]
        lines_map.setdefault(key, []).append({"text": word, "bbox": bbox, "confidence": max(0.0, conf / 100.0)})

    lines: list[dict[str, Any]] = []
    blocks_acc: dict[int, list[dict[str, Any]]] = {}
    for (block_num, _par, _ln), words in sorted(lines_map.items()):
        line_text = " ".join(w["text"] for w in words)
        xs0 = [w["bbox"][0] for w in words]
        ys0 = [w["bbox"][1] for w in words]
        xs1 = [w["bbox"][2] for w in words]
        ys1 = [w["bbox"][3] for w in words]
        line = {
            "text": line_text,
            "bbox": [min(xs0), min(ys0), max(xs1), max(ys1)],
            "confidence": round(sum(w["confidence"] for w in words) / max(1, len(words)), 3),
            "words": words,
        }
        lines.append(line)
        blocks_acc.setdefault(block_num, []).append(line)

    blocks: list[dict[str, Any]] = []
    for _bn, blines in sorted(blocks_acc.items()):
        btext = "\n".join(l["text"] for l in blines)
        xs0 = [l["bbox"][0] for l in blines]
        ys0 = [l["bbox"][1] for l in blines]
        xs1 = [l["bbox"][2] for l in blines]
        ys1 = [l["bbox"][3] for l in blines]
        blocks.append(
            {
                "text": btext,
                "bbox": [min(xs0), min(ys0), max(xs1), max(ys1)],
                "confidence": round(sum(l["confidence"] for l in blines) / max(1, len(blines)), 3),
                "lines": blines,
            }
        )

    text = "\n".join(l["text"] for l in lines).strip()
    conf = round(sum(confs) / max(1, len(confs)), 3) if confs else 0.0
    _ = (page_w, page_h)  # reserved for normalized coords later
    return lines, blocks, text, conf


def _ocr_vision_llm(
    data: bytes,
    *,
    content_type: str,
    page_index: int,
) -> dict[str, Any]:
    candidates = _vision_provider_candidates()
    if not candidates:
        return empty_ocr_result(error="ocr_unavailable", detail="Kein Vision-Key")

    mime = content_type if content_type.startswith("image/") else "image/png"
    b64 = base64.b64encode(data).decode("ascii")
    system = (
        "You are Virtus Office OCR. Extract all readable text from the document image. "
        "Return ONLY valid JSON with keys: "
        "text (string, full reading order), language (ISO 639-1 or null), "
        "confidence (0-1), "
        "lines (array of {text, bbox:[x0,y0,x1,y1]|null}), "
        "tables (array of {rows: string[][]}). "
        "Preserve numbers, dates, currencies, names exactly. No markdown."
    )
    user_text = "OCR this document page and return the JSON schema described."
    errors: list[str] = []
    timeout = float(os.getenv("GENESIS_LLM_TIMEOUT_SEC", "90"))

    for cfg in candidates:
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(
                    f"{cfg['base']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {cfg['key']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": cfg["model"],
                        "temperature": 0.0,
                        "max_tokens": 4000,
                        "messages": [
                            {"role": "system", "content": system},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_text},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                                    },
                                ],
                            },
                        ],
                    },
                )
                if res.status_code in {401, 403}:
                    errors.append(f"{cfg['provider']}_http_{res.status_code}")
                    continue
                if res.status_code == 404:
                    errors.append(f"{cfg['provider']}_model_404:{cfg['model']}")
                    continue
                if res.status_code == 429:
                    errors.append(f"{cfg['provider']}_rate_limited")
                    continue
                res.raise_for_status()
                content = res.json()["choices"][0]["message"]["content"].strip()
                parsed = _parse_vision_json(content)
                text = str(parsed.get("text") or "").strip()
                if not text:
                    errors.append(f"{cfg['provider']}_empty")
                    continue
                lines = list(parsed.get("lines") or []) or _lines_from_text(text)
                tables = list(parsed.get("tables") or [])
                if not tables:
                    tables = _tables_from_lines(lines)
                conf = float(parsed.get("confidence") or 0.75)
                page = {
                    "page_index": page_index,
                    "width": None,
                    "height": None,
                    "blocks": [
                        {
                            "text": text,
                            "bbox": None,
                            "confidence": conf,
                            "lines": lines,
                        }
                    ],
                    "lines": lines,
                    "tables": tables,
                    "text": text,
                    "confidence": conf,
                }
                return {
                    "ok": True,
                    "provider": f"vision_llm:{cfg['provider']}",
                    "model": cfg["model"],
                    "language": parsed.get("language"),
                    "confidence": conf,
                    "text": text,
                    "pages": [page],
                    "tables": tables,
                    "error": None,
                    "detail": None,
                }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{cfg['provider']}_{type(exc).__name__}")
            continue

    return empty_ocr_result(
        error="vision_failed",
        detail="; ".join(errors[:6]) or "Vision-OCR fehlgeschlagen",
    )


def _parse_vision_json(content: str) -> dict[str, Any]:
    raw = content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # Fallback: treat whole content as text
    return {"text": content, "language": None, "confidence": 0.55, "lines": [], "tables": []}


def _normalize_result(raw: dict[str, Any], *, default_page_index: int) -> dict[str, Any]:
    text = str(raw.get("text") or "").strip()
    if not text:
        return empty_ocr_result(error=str(raw.get("error") or "ocr_empty"))
    pages = list(raw.get("pages") or [])
    if not pages:
        lines = list(raw.get("lines") or []) or _lines_from_text(text)
        pages = [
            {
                "page_index": default_page_index,
                "width": raw.get("width"),
                "height": raw.get("height"),
                "blocks": raw.get("blocks")
                or [{"text": text, "bbox": None, "confidence": float(raw.get("confidence") or 0.9), "lines": lines}],
                "lines": lines,
                "tables": list(raw.get("tables") or []),
                "text": text,
                "confidence": float(raw.get("confidence") or 0.9),
            }
        ]
    return _attach_financial_qa(
        {
            "ok": True,
            "provider": str(raw.get("provider") or "stub"),
            "language": raw.get("language"),
            "confidence": float(raw.get("confidence") or 0.9),
            "text": text,
            "pages": pages,
            "tables": list(raw.get("tables") or []) or _tables_from_pages(pages),
            "error": None,
            "detail": None,
        }
    )


def _lines_from_text(text: str) -> list[dict[str, Any]]:
    return [
        {"text": ln, "bbox": None, "confidence": None, "words": []}
        for ln in (text or "").splitlines()
        if ln.strip()
    ]


def _tables_from_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[list[str]] = []
    for ln in lines:
        t = str(ln.get("text") or "").strip()
        if not t:
            continue
        if "|" in t:
            rows.append([c.strip() for c in t.split("|") if c.strip()])
        elif "\t" in t:
            rows.append([c.strip() for c in t.split("\t")])
        elif re.search(r"\s{2,}", t):
            parts = [c.strip() for c in re.split(r"\s{2,}", t) if c.strip()]
            if len(parts) >= 2:
                rows.append(parts)
    if rows and max(len(r) for r in rows) >= 2:
        return [{"rows": rows, "source": "ocr_line_heuristic"}]
    return []


def _tables_from_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for p in pages:
        for t in p.get("tables") or []:
            tables.append(t)
        if not (p.get("tables") or []):
            tables.extend(_tables_from_lines(list(p.get("lines") or [])))
    return tables
