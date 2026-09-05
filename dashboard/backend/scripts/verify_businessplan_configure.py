# -*- coding: utf-8 -*-
"""Hands-on verification: Businessplan → Übersetzen → Dokument anpassen → execute."""

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

from app.integration.virtus_office.document_settings import parse_special_wishes  # noqa: E402
from app.integration.virtus_office.job_engine import OfficeJobEngine  # noqa: E402
from app.integration.virtus_office import OfficeJobError  # noqa: E402
from _office_helpers import mark_office_paid  # noqa: E402

PDF = Path(r"d:\Games\Genesis-AI-Engine\docs\business\Virtus_Core_Businessplan_Oltiiev.pdf")
OUT = Path(r"d:\Games\Genesis-AI-Engine\dashboard\backend\.office_verify")
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "businessplan_configure_verify.json"


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def main() -> int:
    wish = (
        "Übersetze den vollständigen Businessplan von Deutsch nach Englisch. "
        "Die Firmennamen und Personennamen nicht verändern."
    )
    eng = OfficeJobEngine(OUT / "jobs")
    created = eng.create_job(service_preset="translate")
    jid, tok = created["job_id"], created["owner_token"]

    uploaded = eng.upload(
        jid,
        owner_token=tok,
        upload=_upload(PDF.name, PDF.read_bytes(), "application/pdf"),
    )
    u = uploaded.get("understanding") or {}
    prop = uploaded.get("proposal") or {}
    expl = prop.get("explanation") or u.get("explanation") or {}
    facts = {
        f.get("id"): f.get("value")
        for f in (expl.get("key_facts") or [])
        if isinstance(f, dict)
    }

    step1 = {
        "status": uploaded.get("status"),
        "next_step": prop.get("next_step"),
        "doc_type": u.get("document_type"),
        "doc_label": u.get("document_type_label_de"),
        "language": u.get("language"),
        "pages": u.get("page_count"),
        "document_date": facts.get("document_date"),
        "brand": facts.get("brand"),
    }

    settings_values = {
        "change_date": "04.09.2026",
        "target_language": "en",
        "source_language": "de",
        "output_format": "pdf",
        "preserve_names": True,
    }

    cfg = eng.select_action(
        jid,
        owner_token=tok,
        action_id="translate",
        target_language="en",
        source_language="de",
        output_format="pdf",
        confirm_settings=False,
        document_settings=settings_values,
        special_wishes=wish,
    )
    ds = (cfg.get("proposal") or {}).get("document_settings") or {}
    checkout_blocked = False
    checkout_err = None
    try:
        from app.integration.virtus_office.payment_bridge import lock_and_begin_checkout

        lock_and_begin_checkout(
            eng,
            jid,
            owner_token=tok,
            success_url="https://example.com/ok",
            cancel_url="https://example.com/cancel",
        )
    except OfficeJobError as exc:
        checkout_blocked = True
        checkout_err = f"{getattr(exc, 'code', '')}: {exc}"
    except Exception as exc:  # noqa: BLE001
        checkout_blocked = True
        checkout_err = str(exc)[:240]

    confirmed = eng.select_action(
        jid,
        owner_token=tok,
        action_id="translate",
        target_language="en",
        source_language="de",
        output_format="pdf",
        confirm_settings=True,
        document_settings=settings_values,
        special_wishes=wish,
    )
    cprop = confirmed.get("proposal") or {}
    cds = cprop.get("document_settings") or {}

    mark_office_paid(eng, jid, tok)
    done = eng.execute(jid, owner_token=tok)

    artifact_path = None
    out_sample = ""
    art_info = None
    if done.get("status") == "completed":
        try:
            blob, name, mime = eng.get_artifact_bytes(jid, owner_token=tok)
            artifact_path = str(OUT / name)
            Path(artifact_path).write_bytes(blob)
            art_info = {"name": name, "mime": mime, "bytes": len(blob), "magic": blob[:8].hex()}
            # Sample from result PDF text layer if present
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(blob))
                pages_txt = []
                for page in reader.pages[:3]:
                    pages_txt.append(page.extract_text() or "")
                out_sample = "\n".join(pages_txt)[:1200]
                art_info["pdf_pages"] = len(reader.pages)
            except Exception as exc:  # noqa: BLE001
                art_info["pdf_extract_error"] = str(exc)[:120]
        except Exception as exc:  # noqa: BLE001
            art_info = {"error": str(exc)[:200]}
    else:
        art_info = None

    job = eng._require_owner(jid, tok)
    q = job.get("quality") or {}
    provider = (q.get("provider") if isinstance(q, dict) else None) or (
        (job.get("artifact") or {}).get("meta") or {}
    ).get("translation_provider")

    report = {
        "pdf": str(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "step1_understanding": step1,
        "wish_parsed_ops": parse_special_wishes(wish, explanation=expl),
        "configure_without_confirm": {
            "next_step": (cfg.get("proposal") or {}).get("next_step"),
            "payment_enabled": (cfg.get("proposal") or {}).get("payment_enabled"),
            "ops": ds.get("ops"),
            "preview": ds.get("preview"),
            "confirmed": ds.get("confirmed"),
            "checkout_blocked_before_confirm": checkout_blocked,
            "checkout_error": checkout_err,
        },
        "after_confirm": {
            "next_step": cprop.get("next_step"),
            "payment_enabled": cprop.get("payment_enabled"),
            "confirmed": cds.get("confirmed"),
            "target_language": cprop.get("target_language"),
            "price_eur": cprop.get("price_eur"),
            "preview_excerpt": ((cprop.get("preview") or {}).get("excerpt") or "")[:500],
            "change_preview": (cprop.get("preview") or {}).get("change_preview"),
        },
        "execute": {
            "status": done.get("status"),
            "failure_reason": done.get("failure_reason"),
            "failure_detail": done.get("failure_detail"),
            "quality": done.get("quality"),
            "artifact_public": done.get("artifact"),
            "artifact_saved": art_info,
            "artifact_path": artifact_path,
            "translation_provider": provider,
            "output_sample": out_sample,
            "llm_key_present": bool(
                os.getenv("GENESIS_GROQ_API_KEY")
                or os.getenv("GROQ_API_KEY")
                or os.getenv("GENESIS_LLM_API_KEY")
                or os.getenv("OPENAI_API_KEY")
            ),
            "pipeline_live": done.get("pipeline_live"),
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.as_posix())
    return 0 if done.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
