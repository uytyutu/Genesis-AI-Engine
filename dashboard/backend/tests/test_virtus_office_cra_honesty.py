"""CRA Fix Pack #1+#2 — payment required + no stub sellable actions."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.understanding import (
    CUSTOMER_EXECUTABLE_ACTIONS,
    ROADMAP_ACTIONS,
    build_understanding,
)

from _office_helpers import mark_office_paid


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_unpaid_execute_blocked(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="translate")
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload(
            "a.txt",
            b"Arbeitsvertrag Datum 01.03.2024 Gesamtbetrag 10,00 EUR\n",
            "text/plain",
        ),
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    view = eng.get_job(created["job_id"], owner_token=created["owner_token"])
    assert view["payment"]["execute_unlocked"] is False
    assert (view.get("proposal") or {}).get("preview")
    assert (view["proposal"]["preview"] or {}).get("download_allowed") is False
    with pytest.raises(OfficeJobError) as exc:
        eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "payment_required"


def test_paid_execute_allowed(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="translate")
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload(
            "a.txt",
            (
                b"Arbeitsvertrag\nArbeitgeber: Muster GmbH\n"
                b"Arbeitnehmer: Max Mustermann\nDatum: 01.03.2024\n"
                b"Gesamtbetrag 1.250,00 EUR\n"
            ),
            "text/plain",
        ),
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")


def test_choice_cards_exclude_summarize_explain(tmp_path: Path):
    u = build_understanding(
        data=b"Rechnung und Vertrag Datum 01.01.2024 GmbH Betrag 40 EUR\n",
        filename="doc.txt",
        file_kind="txt",
        content_type="text/plain",
    )
    ids = {c["id"] for c in (u.get("choice_options") or [])}
    assert "summarize" not in ids
    assert "explain" not in ids
    assert ids <= CUSTOMER_EXECUTABLE_ACTIONS
    assert ROADMAP_ACTIONS.isdisjoint(ids)


def test_select_explain_rejected(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload(
            "x.txt",
            b"Der Vertrag und die Rechnung mit Datum 01.01.2024",
            "text/plain",
        ),
    )
    with pytest.raises(OfficeJobError) as exc:
        eng.select_action(
            created["job_id"],
            owner_token=created["owner_token"],
            action_id="explain",
        )
    assert exc.value.code == "action_not_available"


def test_bewerbung_preview_no_free_artifact(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="lebenslauf_create")
    view = eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="lebenslauf_create",
        output_format="pdf",
        profile={
            "personal": {
                "full_name": "Anna Beispiel",
                "email": "anna@example.com",
                "phone": "+491234",
                "city": "Berlin",
            },
            "experience": [
                {
                    "title": "Elektrikerin",
                    "employer": "Bau GmbH",
                    "start": "01/2020",
                    "end": "12/2023",
                    "bullets": ["Installation"],
                }
            ],
            "education": [
                {"degree": "Gesellenbrief", "school": "BS Berlin", "start": "2017", "end": "2020"}
            ],
            "languages": [{"language": "Deutsch", "level": "C1"}],
            "skills": ["Elektro"],
        },
    )
    assert view["proposal"]["next_step"] == "awaiting_stage3"
    preview = (view.get("proposal") or {}).get("preview") or {}
    assert preview.get("kind") == "preview"
    assert preview.get("full_document_after_payment") is True
    assert preview.get("download_allowed") is False
    assert preview.get("excerpt")
    assert view.get("artifact_download") is None
    with pytest.raises(OfficeJobError) as exc:
        eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "payment_required"
