# -*- coding: utf-8 -*-
"""A-lite Businessplan R&D: extract → (optional translate) → reconstruct → report.

Does not flip OFFICE_PIPELINE_LIVE. OCR / other Office surfaces untouched.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.env_loader import load_local_env  # noqa: E402

load_local_env()
if not os.getenv("OFFICE_KEEP_GROQ_MODEL"):
    os.environ["GENESIS_GROQ_MODEL"] = "openai/gpt-oss-20b"

from app.integration.virtus_office.office_job_ssot import OFFICE_PIPELINE_LIVE  # noqa: E402
from app.integration.virtus_office.presentation_rebuild import (  # noqa: E402
    extract_presentation_pdf,
    rebuild_presentation_pdf,
    translate_presentation_pages,
)
from app.integration.virtus_office.quality_gate import run_quality_gate  # noqa: E402

OUT = ROOT / ".office_verify" / "commercial_validation"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "alite_businessplan_rnd_report.json"

SRC = ROOT / ".office_verify/commercial_docx2/order_materials/mat-d24ae910af0d.pdf"
TRANSLATE = os.getenv("ALITE_TRANSLATE", "1").strip() not in {"0", "false", "no"}


def main() -> int:
    if not SRC.exists():
        REPORT.write_text(
            json.dumps({"ok": False, "error": "source_missing", "live": OFFICE_PIPELINE_LIVE}, indent=2),
            encoding="utf-8",
        )
        print(REPORT)
        return 1

    data = SRC.read_bytes()
    extracted = extract_presentation_pdf(data)
    report: dict = {
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "source": str(SRC),
        "extract": {
            "ok": extracted.get("ok"),
            "page_count": extracted.get("page_count"),
            "image_count": extracted.get("image_count"),
            "error": extracted.get("error"),
        },
        "translate_enabled": TRANSLATE,
    }
    if not extracted.get("ok"):
        report["ok"] = False
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(REPORT)
        return 1

    pages = list(extracted["pages"])
    provider = None
    if TRANSLATE:
        tr = translate_presentation_pages(
            pages,
            source_language="de",
            target_language="en",
            preserve_names=True,
            preserve_numbers_dates=True,
        )
        report["translate"] = {
            "ok": tr.get("ok"),
            "provider": tr.get("provider"),
            "error": tr.get("error"),
            "detail": (tr.get("detail") or "")[:240],
            "chars_in": tr.get("chars_in"),
            "chars_out": tr.get("chars_out"),
        }
        if not tr.get("ok"):
            report["ok"] = False
            report["verdict"] = "TRANSLATE_FAIL"
            REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(REPORT)
            print("verdict=", report["verdict"], "LIVE=", OFFICE_PIPELINE_LIVE)
            return 1
        pages = list(tr["pages"])
        provider = tr.get("provider")
        quality_in = tr.get("quality_input_text") or ""
        quality_out = tr.get("quality_output_text") or ""
    else:
        for pg in pages:
            pg["translated_text"] = pg.get("text") or ""
        quality_in = "\n\n".join(str(p.get("text") or "") for p in pages)
        quality_out = quality_in
        report["translate"] = {"ok": True, "provider": "identity", "skipped": True}

    rebuilt = rebuild_presentation_pdf(
        pages,
        title="Virtus Core Businessplan · EN · presentation rebuild",
        meta_lines=[
            "Delivery: presentation-grade rebuild (not pixel-perfect)",
            f"Provider: {provider or 'identity'}",
            f"Source pages: {extracted['page_count']} · images: {extracted['image_count']}",
        ],
    )
    art_path = OUT / "alite_businessplan_en_presentation_rebuild.pdf"
    if rebuilt.get("ok"):
        art_path.write_bytes(rebuilt["bytes"])
    report["rebuild"] = {
        "ok": rebuilt.get("ok"),
        "page_count": rebuilt.get("page_count"),
        "image_count": rebuilt.get("image_count"),
        "bytes": len(rebuilt.get("bytes") or b""),
        "path": str(art_path) if rebuilt.get("ok") else None,
        "error": rebuilt.get("error"),
    }

    qa = None
    if rebuilt.get("ok"):
        qa = run_quality_gate(
            action_id="translate",
            input_text=quality_in,
            output_text=quality_out,
            artifact_bytes=rebuilt["bytes"],
            artifact_ext="pdf",
            artifact_mime="application/pdf",
            target_language="en",
            translation_provider=provider or ("offline_glossary" if not TRANSLATE else None),
            job_id="alite-rnd",
            artifact_job_id="alite-rnd",
            document_type="businessplan",
            source_page_count=int(extracted["page_count"]),
            source_image_count=int(extracted["image_count"]),
            delivery_mode="presentation_rebuild",
        )
        report["quality"] = {
            "passed": qa.get("passed"),
            "failed": qa.get("failed"),
            "layout_related": [
                c
                for c in (qa.get("checks") or [])
                if c["id"]
                in {
                    "layout_fidelity",
                    "source_images_preserved",
                    "pagination_consistent",
                    "no_residual_source_language",
                    "live_translator_required",
                }
            ],
        }

    structure_ok = (
        rebuilt.get("ok")
        and rebuilt.get("page_count") == 28
        and int(rebuilt.get("image_count") or 0) >= 11
    )
    # R&D structure proof vs commercial PASS
    report["structure_proof"] = bool(structure_ok)
    report["commercial_candidate"] = bool(
        TRANSLATE and structure_ok and qa and qa.get("passed")
    )
    report["ok"] = bool(structure_ok)
    report["verdict"] = (
        "ALITE_STRUCTURE_AND_QA_PASS"
        if report["commercial_candidate"]
        else ("ALITE_STRUCTURE_PASS" if structure_ok else "ALITE_FAIL")
    )
    report["note"] = (
        "Presentation-grade rebuild — not pixel-perfect. "
        "Commercial PASS still requires manual visual QA."
    )

    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.as_posix())
    print("verdict=", report["verdict"], "pages=", rebuilt.get("page_count"), "images=", rebuilt.get("image_count"))
    print("LIVE=", OFFICE_PIPELINE_LIVE)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
