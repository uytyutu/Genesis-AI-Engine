# -*- coding: utf-8 -*-
"""Re-validate OCR Scan/Foto → translate after 401 routing fix."""

from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from pathlib import Path

from starlette.datastructures import Headers, UploadFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.env_loader import load_local_env  # noqa: E402

load_local_env()
if not os.getenv("OFFICE_KEEP_GROQ_MODEL"):
    os.environ["GENESIS_GROQ_MODEL"] = "openai/gpt-oss-20b"

from app.integration.virtus_office.job_engine import OfficeJobEngine  # noqa: E402
from app.integration.virtus_office.ocr_engine import (  # noqa: E402
    ocr_capabilities,
    ocr_image_bytes,
    _vision_provider_candidates,
)
from app.integration.virtus_office.office_job_ssot import OFFICE_PIPELINE_LIVE  # noqa: E402
from _office_helpers import mark_office_paid  # noqa: E402

OUT = ROOT / ".office_verify" / "commercial_validation"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "ocr_fix_report.json"


def _png() -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    # Larger canvas + TrueType when available — default bitmap font is OCR-hostile.
    im = Image.new("RGB", (1200, 1600), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)
    font = None
    for path in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            font = ImageFont.truetype(path, 36)
            break
        except Exception:
            continue
    lines = [
        "RECHNUNG",
        "Nr. RE-SCAN-77",
        "Datum 10.06.2026",
        "Kunde: Virtus Core",
        "Betrag 199,00 EUR",
        "MwSt 19% 37,81 EUR",
        "Gesamt 236,81 EUR",
    ]
    y = 60
    for line in lines:
        if font:
            draw.text((48, y), line, fill=(0, 0, 0), font=font)
        else:
            draw.text((48, y), line, fill=(0, 0, 0))
        y += 64
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def main() -> int:
    png = _png()
    caps = ocr_capabilities()
    cands = [
        {"provider": c["provider"], "base": c["base"], "model": c["model"]}
        for c in _vision_provider_candidates()
    ]
    direct = ocr_image_bytes(png, content_type="image/png")
    direct_text = str(direct.get("text") or "")
    critical = {
        "invoice_number": "RE-SCAN-77" in direct_text,
        "date": "10.06.2026" in direct_text or "10.6.2026" in direct_text,
        "netto": "199,00" in direct_text or "199.00" in direct_text,
        "mwst": "37,81" in direct_text or "37.81" in direct_text,
        "brutto": "236,81" in direct_text or "236.81" in direct_text,
        "rate": "19%" in direct_text or "19 %" in direct_text,
    }
    financial_qa = direct.get("financial_qa") or {}

    eng = OfficeJobEngine(OUT / "ocr_fix_jobs")
    created = eng.create_job(service_preset="translate")
    jid, tok = created["job_id"], created["owner_token"]
    uploaded = eng.upload(
        jid,
        owner_token=tok,
        upload=UploadFile(
            file=BytesIO(png),
            filename="rechnung_scan.png",
            headers=Headers({"content-type": "image/png"}),
        ),
    )
    u = uploaded.get("understanding") or {}
    structure = u.get("structure") or {}

    result: dict = {
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "capabilities": caps,
        "vision_candidates": cands,
        "direct_ocr": {
            "ok": direct.get("ok"),
            "provider": direct.get("provider"),
            "model": direct.get("model"),
            "error": direct.get("error"),
            "detail": (direct.get("detail") or "")[:240],
            "text_preview": direct_text[:400],
            "confidence": direct.get("confidence"),
            "financial_qa": financial_qa,
            "critical_fields": critical,
        },
        "upload": {
            "status": uploaded.get("status"),
            "ocr_status": structure.get("ocr_status"),
            "text_detected": structure.get("text_detected"),
            "text_chars": u.get("text_excerpt_chars"),
            "type": u.get("document_type"),
            "language": u.get("language"),
            "ocr_needs_review": structure.get("ocr_needs_review"),
            "ocr_review_warning_de": structure.get("ocr_review_warning_de"),
        },
    }

    fields_ok = all(critical.values()) and bool(financial_qa.get("passed"))
    if structure.get("ocr_status") == "done" and structure.get("text_detected"):
        eng.select_action(
            jid,
            owner_token=tok,
            action_id="translate",
            target_language="en",
            source_language="de",
            output_format="pdf",
            confirm_settings=True,
            document_settings={
                "target_language": "en",
                "source_language": "de",
                "output_format": "pdf",
                "preserve_names": True,
                "preserve_numbers_dates": True,
            },
        )
        mark_office_paid(eng, jid, tok)
        done = eng.execute(jid, owner_token=tok)
        art = None
        quality_passed = bool((done.get("quality") or {}).get("passed"))
        if done.get("status") == "completed":
            blob, name, mime = eng.get_artifact_bytes(jid, owner_token=tok)
            path = OUT / f"ocr_fixed__{name}"
            path.write_bytes(blob)
            art = {"path": str(path), "bytes": len(blob), "name": name}
        result["execute"] = {
            "status": done.get("status"),
            "failure_reason": done.get("failure_reason"),
            "failure_detail": (done.get("failure_detail") or "")[:240],
            "quality_passed": quality_passed,
            "quality_failed": (done.get("quality") or {}).get("failed"),
            "provider": (done.get("quality") or {}).get("provider"),
            "artifact": art,
        }
        # Commercial honesty: wrong OCR must never green-pass.
        if not fields_ok:
            result["ok"] = quality_passed is False and done.get("status") != "completed"
            result["verdict"] = "HONEST_FAIL_ON_BAD_OCR" if result["ok"] else "FALSE_GREEN_FAIL"
        else:
            result["ok"] = (
                done.get("status") == "completed"
                and quality_passed
                and bool(art)
            )
            result["verdict"] = "OCR_FIELDS_AND_TRANSLATE_OK" if result["ok"] else "OCR_OK_TRANSLATE_FAIL"
    else:
        result["execute"] = None
        result["ok"] = False
        result["blocker"] = "ocr_still_failed_on_upload"
        result["verdict"] = "OCR_UPLOAD_FAIL"

    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.as_posix())
    print("ok=", result.get("ok"), "direct=", direct.get("ok"), direct.get("provider"))
    print("LIVE=", OFFICE_PIPELINE_LIVE)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
