# -*- coding: utf-8 -*-
"""Commercial Validation — sellable Office flows (sandbox pay → execute → artifact).

Does NOT flip OFFICE_PIPELINE_LIVE. Uses local samples + real Businessplan PDF.
"""

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
if not os.getenv("OFFICE_KEEP_GROQ_MODEL"):
    os.environ["GENESIS_GROQ_MODEL"] = "openai/gpt-oss-20b"

from app.integration.virtus_office.job_engine import OfficeJobEngine  # noqa: E402
from app.integration.virtus_office.office_job_ssot import OFFICE_PIPELINE_LIVE  # noqa: E402
from app.integration.virtus_office.translator import llm_key_available  # noqa: E402
from _office_helpers import mark_office_paid  # noqa: E402

SAMPLES = ROOT / ".office_verify" / "commercial_samples"
OUT = ROOT / ".office_verify" / "commercial_validation"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "report.json"

BIZPLAN = Path(r"d:\Games\Genesis-AI-Engine\docs\business\Virtus_Core_Businessplan_Oltiiev.pdf")

COMPLETE_PROFILE = {
    "personal": {
        "full_name": "Anna Berger",
        "email": "anna.berger@example.com",
        "phone": "+49 170 1234567",
        "city": "Dresden",
        "address": "Berliner Str. 12, 01067 Dresden",
    },
    "experience": [
        {
            "employer": "Nordlicht GmbH",
            "title": "Marketing Manager",
            "start": "01/2021",
            "end": "08/2026",
            "bullets": ["Kampagnen", "Content"],
        }
    ],
    "education": [
        {
            "school": "TU Dresden",
            "degree": "B.A. Betriebswirtschaft",
            "start": "10/2015",
            "end": "07/2018",
        }
    ],
    "languages": [{"language": "Deutsch", "level": "C2"}, {"language": "Englisch", "level": "B2"}],
    "skills": ["Marketing", "MS Office"],
    "vacancy": {
        "title": "Marketing Manager",
        "company": "Nordlicht Media",
        "text": "Wir suchen Verstärkung im Marketing.",
    },
    "motivation_notes": "Ich möchte meine Erfahrung einbringen.",
}


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _png() -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    lines = [
        "RECHNUNG",
        "Nr. RE-SCAN-77",
        "Datum 10.06.2026",
        "Kunde: Virtus Core",
        "Betrag 199,00 EUR",
        "MwSt 19% 37,81 EUR",
        "Gesamt 236,81 EUR",
    ]
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


def _run_file_job(
    eng: OfficeJobEngine,
    *,
    label: str,
    path: Path,
    content_type: str,
    action_id: str,
    target_language: str | None = None,
    source_language: str | None = None,
    output_format: str | None = None,
    require_live_translate: bool = False,
) -> dict:
    created = eng.create_job(service_preset=action_id if action_id in {"translate"} else None)
    jid, tok = created["job_id"], created["owner_token"]
    data = path.read_bytes() if path.exists() else b""
    if not data:
        return {"label": label, "ok": False, "error": "missing_file", "path": str(path)}
    uploaded = eng.upload(jid, owner_token=tok, upload=_upload(path.name, data, content_type))
    u = uploaded.get("understanding") or {}
    prop = uploaded.get("proposal") or {}
    settings = {
        "output_format": output_format or "pdf",
        "preserve_names": True,
        "preserve_numbers_dates": True,
    }
    if target_language:
        settings["target_language"] = target_language
    if source_language:
        settings["source_language"] = source_language
    if action_id == "translate":
        settings["change_date"] = "04.09.2026"
    try:
        configured = eng.select_action(
            jid,
            owner_token=tok,
            action_id=action_id,
            target_language=target_language,
            source_language=source_language,
            output_format=output_format,
            document_settings=settings,
            confirm_settings=True,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "label": label,
            "ok": False,
            "error": f"select_action:{exc}",
            "understanding": {
                "type": u.get("document_type"),
                "language": u.get("language"),
                "pages": u.get("page_count"),
            },
        }
    mark_office_paid(eng, jid, tok)
    done = eng.execute(jid, owner_token=tok)
    art = None
    sample = ""
    if done.get("status") == "completed":
        blob, name, mime = eng.get_artifact_bytes(jid, owner_token=tok)
        dest = OUT / f"{label}__{name}"
        dest.write_bytes(blob)
        art = {"path": str(dest), "bytes": len(blob), "mime": mime, "name": name}
        if name.endswith(".pdf"):
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(blob))
                sample = "\n".join((p.extract_text() or "") for p in reader.pages[:2])[:700]
                art["pdf_pages"] = len(reader.pages)
            except Exception as exc:  # noqa: BLE001
                art["pdf_error"] = str(exc)[:120]
        elif name.endswith(".docx"):
            art["magic"] = blob[:2].decode("latin1", errors="ignore")
            sample = f"docx_bytes={len(blob)}"
        elif name.endswith(".xlsx"):
            art["magic"] = blob[:2].decode("latin1", errors="ignore")
            sample = f"xlsx_bytes={len(blob)}"
    provider = ((done.get("quality") or {}) or {}).get("provider")
    ok = done.get("status") == "completed" and bool((done.get("quality") or {}).get("passed"))
    if require_live_translate and provider in {None, "offline_glossary", "none"}:
        ok = False
    return {
        "label": label,
        "ok": ok,
        "service": action_id,
        "understanding": {
            "type": u.get("document_type"),
            "type_label": u.get("document_type_label_de"),
            "language": u.get("language"),
            "pages": u.get("page_count"),
            "pages_included": (u.get("structure") or {}).get("pages_included"),
            "text_chars": u.get("text_excerpt_chars"),
            "ocr_status": (u.get("structure") or {}).get("ocr_status"),
        },
        "proposal_next": (configured.get("proposal") or {}).get("next_step"),
        "price_eur": (configured.get("proposal") or {}).get("price_eur"),
        "status": done.get("status"),
        "failure_reason": done.get("failure_reason"),
        "failure_detail": (done.get("failure_detail") or "")[:300],
        "quality_passed": (done.get("quality") or {}).get("passed"),
        "quality_failed": (done.get("quality") or {}).get("failed"),
        "provider": provider,
        "artifact": art,
        "sample": sample,
        "customer_got_file": bool(art),
    }


def _run_bewerbung(eng: OfficeJobEngine, *, action_id: str) -> dict:
    created = eng.create_job()
    jid, tok = created["job_id"], created["owner_token"]
    # Profile-only create path — upload a seed CV text for improve flows
    seed = SAMPLES / "lebenslauf_anna.txt"
    if action_id == "lebenslauf_improve" and seed.exists():
        eng.upload(
            jid,
            owner_token=tok,
            upload=_upload(seed.name, seed.read_bytes(), "text/plain"),
        )
    else:
        # create empty understanding via tiny upload for non-improve? create uses profile only
        # For create/anschreiben/paket: still need a job — upload seed as context
        eng.upload(
            jid,
            owner_token=tok,
            upload=_upload(seed.name, seed.read_bytes(), "text/plain"),
        )
    eng.submit_bewerbung_profile(
        jid,
        owner_token=tok,
        profile=COMPLETE_PROFILE,
        action_id=action_id,
        output_format="pdf",
    )
    mark_office_paid(eng, jid, tok)
    done = eng.execute(jid, owner_token=tok)
    art = None
    if done.get("status") == "completed":
        blob, name, mime = eng.get_artifact_bytes(jid, owner_token=tok)
        dest = OUT / f"bewerbung_{action_id}__{name}"
        dest.write_bytes(blob)
        art = {"path": str(dest), "bytes": len(blob), "mime": mime, "name": name}
    return {
        "label": f"bewerbung:{action_id}",
        "ok": done.get("status") == "completed" and bool((done.get("quality") or {}).get("passed")),
        "service": action_id,
        "status": done.get("status"),
        "failure_reason": done.get("failure_reason"),
        "failure_detail": (done.get("failure_detail") or "")[:300],
        "quality_passed": (done.get("quality") or {}).get("passed"),
        "quality_failed": (done.get("quality") or {}).get("failed"),
        "artifact": art,
        "customer_got_file": bool(art),
        "contains_name": False,
    }


def main() -> int:
    eng = OfficeJobEngine(OUT / "jobs")
    results: list[dict] = []

    # 1) Understanding-only checks (invoice / cv / contract)
    for name, ctype, expect_type in (
        ("rechnung_muster.txt", "text/plain", "invoice"),
        ("lebenslauf_anna.txt", "text/plain", None),
        ("vertrag_kurz.txt", "text/plain", None),
        ("kosten.csv", "text/csv", None),
    ):
        path = SAMPLES / name
        created = eng.create_job()
        view = eng.upload(
            created["job_id"],
            owner_token=created["owner_token"],
            upload=_upload(name, path.read_bytes(), ctype),
        )
        u = view.get("understanding") or {}
        results.append(
            {
                "label": f"understand:{name}",
                "ok": bool(u.get("filled")),
                "service": "understanding",
                "understanding": {
                    "type": u.get("document_type"),
                    "language": u.get("language"),
                    "pages": u.get("page_count"),
                },
                "expected_type_hint": expect_type,
                "type_match": (expect_type is None)
                or (u.get("document_type") == expect_type),
                "customer_got_file": False,
                "note": "pre-pay understanding only",
            }
        )

    # 2) Sellable executors
    results.append(
        _run_file_job(
            eng,
            label="convert_vertrag",
            path=SAMPLES / "vertrag_kurz.txt",
            content_type="text/plain",
            action_id="convert_docx",
            output_format="docx",
        )
    )
    results.append(
        _run_file_job(
            eng,
            label="extract_kosten",
            path=SAMPLES / "kosten.csv",
            content_type="text/csv",
            action_id="extract_data",
            output_format="xlsx",
        )
    )
    results.append(
        _run_file_job(
            eng,
            label="translate_rechnung_en",
            path=SAMPLES / "rechnung_muster.txt",
            content_type="text/plain",
            action_id="translate",
            target_language="en",
            source_language="de",
            output_format="pdf",
            require_live_translate=False,  # short may use offline; note honesty
        )
    )

    # OCR path (image upload)
    png = _png()
    png_path = SAMPLES / "rechnung_scan.png"
    png_path.write_bytes(png)
    results.append(
        _run_file_job(
            eng,
            label="ocr_scan_translate",
            path=png_path,
            content_type="image/png",
            action_id="translate",
            target_language="en",
            source_language="de",
            output_format="pdf",
        )
    )

    # Businessplan translate — only if live key (expensive)
    if BIZPLAN.exists() and llm_key_available() and os.getenv("OFFICE_VALIDATE_BIZPLAN", "0") == "1":
        time.sleep(2)
        results.append(
            _run_file_job(
                eng,
                label="translate_businessplan_en",
                path=BIZPLAN,
                content_type="application/pdf",
                action_id="translate",
                target_language="en",
                source_language="de",
                output_format="pdf",
                require_live_translate=True,
            )
        )

    # Bewerbung products
    for aid in ("lebenslauf_create", "lebenslauf_improve", "bewerbungsschreiben", "bewerbung_paket"):
        results.append(_run_bewerbung(eng, action_id=aid))

    sellable = [r for r in results if r.get("service") not in {"understanding"}]
    understanding = [r for r in results if r.get("service") == "understanding"]
    report = {
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "llm_key_available": llm_key_available(),
        "verdict_platform": "FUNCTIONALLY_READY_FOR_COMMERCIAL_VALIDATION",
        "understanding_pass": all(r.get("ok") for r in understanding),
        "sellable_pass_count": sum(1 for r in sellable if r.get("ok")),
        "sellable_total": len(sellable),
        "customer_got_artifact_count": sum(1 for r in sellable if r.get("customer_got_file")),
        "results": results,
        "commercial_pass": False,
        "note": (
            "Commercial PASS requires owner eye review of artifacts + LIVE decision. "
            "This report is agent validation only (sandbox payment)."
        ),
    }
    # Do not claim Commercial PASS automatically
    if (
        report["understanding_pass"]
        and report["sellable_pass_count"] == report["sellable_total"]
        and OFFICE_PIPELINE_LIVE is False
    ):
        report["validation_status"] = "ALL_SELLABLE_FLOWS_PRODUCED_ARTIFACTS"
    else:
        fails = [r["label"] for r in sellable if not r.get("ok")]
        report["validation_status"] = "GAPS_REMAIN"
        report["failed_labels"] = fails

    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.as_posix())
    print(report["validation_status"])
    print(
        f"sellable {report['sellable_pass_count']}/{report['sellable_total']} "
        f"artifacts={report['customer_got_artifact_count']} LIVE={OFFICE_PIPELINE_LIVE}"
    )
    return 0 if report["validation_status"] == "ALL_SELLABLE_FLOWS_PRODUCED_ARTIFACTS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
