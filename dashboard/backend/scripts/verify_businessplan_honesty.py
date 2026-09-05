# -*- coding: utf-8 -*-
"""Re-check Businessplan translate honesty after layout fidelity gate."""

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
from app.integration.virtus_office.office_job_ssot import OFFICE_PIPELINE_LIVE  # noqa: E402
from _office_helpers import mark_office_paid  # noqa: E402

OUT = ROOT / ".office_verify" / "commercial_validation"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "businessplan_honesty_report.json"

SRC_CANDIDATES = [
    ROOT / ".office_verify/commercial_docx2/order_materials/mat-d24ae910af0d.pdf",
    ROOT / ".office_verify/commercial_docx/order_materials/mat-d24ae910af0d.pdf",
]


def main() -> int:
    src = next((p for p in SRC_CANDIDATES if p.exists()), None)
    if not src:
        REPORT.write_text(
            json.dumps({"ok": False, "error": "source_businessplan_missing", "live": OFFICE_PIPELINE_LIVE}, indent=2),
            encoding="utf-8",
        )
        print(REPORT)
        return 1

    eng = OfficeJobEngine(OUT / "bp_honesty_jobs")
    created = eng.create_job(service_preset="translate")
    jid, tok = created["job_id"], created["owner_token"]
    data = src.read_bytes()
    uploaded = eng.upload(
        jid,
        owner_token=tok,
        upload=UploadFile(
            file=BytesIO(data),
            filename="Virtus_Core_Businessplan_Oltiiev.pdf",
            headers=Headers({"content-type": "application/pdf"}),
        ),
    )
    u = uploaded.get("understanding") or {}
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
            "change_date": "04.09.2026",
            "preserve_names": True,
            "preserve_numbers_dates": True,
        },
    )
    mark_office_paid(eng, jid, tok)
    done = eng.execute(jid, owner_token=tok)
    quality = done.get("quality") or {}
    # Honest Commercial QA: text-rebuild of illustrated multi-page BP must NOT pass layout.
    honest = (
        done.get("status") != "completed"
        or quality.get("passed") is False
        or bool(quality.get("failed"))
    )
    report = {
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "source": str(src),
        "source_bytes": len(data),
        "understanding": {
            "type": u.get("document_type"),
            "pages": u.get("page_count"),
            "images": (u.get("structure") or {}).get("images"),
        },
        "status": done.get("status"),
        "failure_reason": done.get("failure_reason"),
        "failure_detail": (done.get("failure_detail") or "")[:300],
        "quality_passed": quality.get("passed"),
        "quality_failed": quality.get("failed"),
        "honest_non_layout_fail": bool(honest),
        "ok": bool(honest) and OFFICE_PIPELINE_LIVE is False,
        "verdict": "HONEST_LAYOUT_FAIL" if honest else "FALSE_LAYOUT_GREEN",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.as_posix())
    print("verdict=", report["verdict"], "LIVE=", OFFICE_PIPELINE_LIVE)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
