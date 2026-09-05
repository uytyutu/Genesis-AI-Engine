# -*- coding: utf-8 -*-
"""Commercial proof: German Businessplan → English PDF + DOCX via live translator."""

from __future__ import annotations

import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path

from starlette.datastructures import Headers, UploadFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.env_loader import load_local_env  # noqa: E402

load_local_env()
# Commercial proof: pin a reachable Groq model (fallbacks still apply).
if not os.getenv("OFFICE_KEEP_GROQ_MODEL"):
    os.environ["GENESIS_GROQ_MODEL"] = "openai/gpt-oss-20b"

from app.integration.virtus_office.job_engine import OfficeJobEngine  # noqa: E402
from app.integration.virtus_office.translator import llm_key_available  # noqa: E402
from _office_helpers import mark_office_paid  # noqa: E402

PDF = Path(r"d:\Games\Genesis-AI-Engine\docs\business\Virtus_Core_Businessplan_Oltiiev.pdf")
OUT = Path(r"d:\Games\Genesis-AI-Engine\dashboard\backend\.office_verify")
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "businessplan_commercial_translate.json"


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _run_one(eng: OfficeJobEngine, *, out_fmt: str) -> dict:
    wish = (
        "Übersetze den vollständigen Businessplan von Deutsch nach Englisch. "
        "Die Firmennamen und Personennamen nicht verändern."
    )
    created = eng.create_job(service_preset="translate")
    jid, tok = created["job_id"], created["owner_token"]
    uploaded = eng.upload(
        jid,
        owner_token=tok,
        upload=_upload(PDF.name, PDF.read_bytes(), "application/pdf"),
    )
    u = uploaded.get("understanding") or {}
    structure = u.get("structure") or {}
    settings_values = {
        "change_date": "04.09.2026",
        "target_language": "en",
        "source_language": "de",
        "output_format": out_fmt,
        "preserve_names": True,
        "preserve_numbers_dates": True,
        "scope": "full",
    }
    eng.select_action(
        jid,
        owner_token=tok,
        action_id="translate",
        target_language="en",
        source_language="de",
        output_format=out_fmt,
        confirm_settings=True,
        document_settings=settings_values,
        special_wishes=wish,
    )
    mark_office_paid(eng, jid, tok)
    done = eng.execute(jid, owner_token=tok)
    sample = ""
    art_path = None
    art_info = None
    if done.get("status") == "completed":
        blob, name, mime = eng.get_artifact_bytes(jid, owner_token=tok)
        art_path = str(OUT / f"commercial_{out_fmt}_{name}")
        Path(art_path).write_bytes(blob)
        art_info = {"name": name, "mime": mime, "bytes": len(blob)}
        job = eng._require_owner(jid, tok)
        # quality output text is not always persisted; sample from PDF if possible
        if out_fmt == "pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(blob))
                art_info["pdf_pages"] = len(reader.pages)
                sample = "\n".join((p.extract_text() or "") for p in reader.pages[:4])[:1500]
            except Exception as exc:  # noqa: BLE001
                art_info["extract_error"] = str(exc)[:120]
        q = job.get("quality") or {}
        provider = q.get("provider")
    else:
        provider = None
        q = done.get("quality")
    return {
        "format": out_fmt,
        "understanding": {
            "type": u.get("document_type"),
            "language": u.get("language"),
            "pages": u.get("page_count"),
            "pages_included": structure.get("pages_included"),
            "text_excerpt_chars": u.get("text_excerpt_chars"),
        },
        "status": done.get("status"),
        "failure_reason": done.get("failure_reason"),
        "failure_detail": done.get("failure_detail"),
        "quality": q,
        "provider": provider or (done.get("quality") or {}).get("provider"),
        "artifact": art_info,
        "artifact_path": art_path,
        "sample": sample,
        "has_new_date": "04.09.2026" in (sample or ""),
        "has_old_date": "31.07.2026" in (sample or ""),
        "has_virtus_core": "Virtus Core" in (sample or ""),
    }


def main() -> int:
    report: dict = {
        "llm_key_available": llm_key_available(),
        "pipeline_live": False,
        "runs": [],
    }
    if not llm_key_available():
        report["verdict"] = "BLOCKED — no live translator key in environment"
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(REPORT.as_posix())
        return 2

    eng = OfficeJobEngine(OUT / "commercial_jobs")
    formats = ["pdf"]
    if os.getenv("OFFICE_TRANSLATE_BOTH_FORMATS") == "1":
        formats.append("docx")
    for fmt in formats:
        report["runs"].append(_run_one(eng, out_fmt=fmt))
        time.sleep(3)

    ok = all(r.get("status") == "completed" for r in report["runs"])
    live = all(
        (r.get("provider") not in {None, "offline_glossary", "none"}) for r in report["runs"]
    )
    report["verdict"] = (
        "COMMERCIAL_PASS_CANDIDATE"
        if ok and live
        else ("FAILED" if not ok else "COMPLETED_BUT_NOT_LIVE")
    )
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.as_posix())
    print(report["verdict"])
    return 0 if ok and live else 1


if __name__ == "__main__":
    raise SystemExit(main())
