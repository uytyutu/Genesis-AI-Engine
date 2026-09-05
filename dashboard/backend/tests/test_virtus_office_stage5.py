"""Virtus Office Stage 5 — Bewerbung Office."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.bewerbung_profile import (
    missing_fields_for_action,
    normalize_profile,
)
from app.integration.virtus_office.office_job_ssot import office_reuse_map

from _office_helpers import mark_office_paid


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _png() -> bytes:
    from PIL import Image

    im = Image.new("RGB", (80, 100), color=(40, 80, 120))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


COMPLETE_PROFILE = {
    "personal": {
        "full_name": "Anna Schmidt",
        "email": "anna.schmidt@example.com",
        "phone": "+49 170 1234567",
        "city": "Berlin",
    },
    "experience": [
        {
            "employer": "Muster GmbH",
            "title": "Kaufmannische Angestellte",
            "start": "03/2020",
            "end": "12/2023",
            "bullets": ["Kundenbetreuung", "Rechnungswesen"],
        }
    ],
    "education": [
        {
            "school": "Berufsschule Berlin",
            "degree": "Kaufmannische Ausbildung",
            "start": "08/2017",
            "end": "07/2020",
        }
    ],
    "languages": [{"language": "Deutsch", "level": "C1"}, {"language": "Englisch", "level": "B2"}],
    "skills": ["MS Office", "SAP"],
    "drivers_license": ["B"],
    "vacancy": {
        "title": "Office Manager",
        "company": "Nordwind AG",
        "text": "Wir suchen Verstarkung im Office.",
    },
    "motivation_notes": "Ich mochte meine Erfahrung im Office einbringen.",
}


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_ssot_stage5():
    m = office_reuse_map()
    assert m["stage5_bewerbung_office"] is True
    assert m["pipeline_live"] is True


def test_missing_fields_no_invent():
    empty = normalize_profile({})
    missing = missing_fields_for_action("lebenslauf_create", empty)
    ids = {m["id"] for m in missing}
    assert "personal.full_name" in ids
    assert "personal.contact" in ids
    assert "experience_or_education" in ids


def test_lebenslauf_create_execute(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="lebenslauf_create")
    view = eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        profile=COMPLETE_PROFILE,
        action_id="lebenslauf_create",
        output_format="pdf",
    )
    assert view["status"] == "proposal_ready"
    assert view["proposal"]["next_step"] == "awaiting_stage3"
    assert view["proposal"]["profile_ready"] is True
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", (done.get("failure_detail"), done.get("quality"))
    blob, name, mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert name.endswith(".pdf")
    assert blob.startswith(b"%PDF")
    assert "pdf" in mime


def test_incomplete_profile_blocks_execute(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="lebenslauf_create")
    view = eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        profile={"personal": {"full_name": "Nur Name"}},
        action_id="lebenslauf_create",
    )
    assert view["proposal"]["next_step"] == "complete_profile"
    assert view["proposal"]["missing_fields"]
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    with pytest.raises(OfficeJobError) as exc:
        eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "profile_incomplete"


def test_bewerbungsschreiben(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="bewerbungsschreiben")
    eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        profile=COMPLETE_PROFILE,
        action_id="bewerbungsschreiben",
        output_format="docx",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    blob, name, _mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert name.endswith(".docx")
    assert blob[:2] == b"PK"


def test_bewerbung_paket_zip(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="bewerbung_paket")
    eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        profile=COMPLETE_PROFILE,
        action_id="bewerbung_paket",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    blob, name, mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert name.endswith(".zip")
    assert "zip" in mime
    assert blob[:2] == b"PK"


def test_photo_attach_and_cv(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="lebenslauf_create")
    eng.attach_bewerbung_photo(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("foto.png", _png(), "image/png"),
    )
    eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        profile=COMPLETE_PROFILE,
        action_id="lebenslauf_create",
        output_format="pdf",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    assert done["bewerbung_profile"]["photo_material_id"]


def test_lebenslauf_improve_from_old_cv_text(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="lebenslauf_improve")
    old = (
        "Max Mustermann\n"
        "max@example.com\nBerlin\n"
        "03/2019 – 01/2024 Lagerist, Logistik AG\n"
        "Ausbildung Berufskolleg 2016 – 2019\n"
    ).encode("utf-8")
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("alter_cv.txt", old, "text/plain"),
    )
    # Fill remaining required fields if extraction incomplete
    view = eng.get_job(created["job_id"], owner_token=created["owner_token"])
    draft = dict(view.get("bewerbung_profile") or {})
    draft = {
        **COMPLETE_PROFILE,
        **draft,
        "personal": {
            **COMPLETE_PROFILE["personal"],
            **(draft.get("personal") or {}),
            "full_name": (draft.get("personal") or {}).get("full_name") or "Max Mustermann",
            "email": (draft.get("personal") or {}).get("email") or "max@example.com",
            "city": (draft.get("personal") or {}).get("city") or "Berlin",
        },
        "source_cv_text": old.decode("utf-8"),
    }
    eng.submit_bewerbung_profile(
        created["job_id"],
        owner_token=created["owner_token"],
        profile=draft,
        action_id="lebenslauf_improve",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
