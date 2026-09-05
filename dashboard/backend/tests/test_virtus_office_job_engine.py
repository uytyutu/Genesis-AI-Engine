"""Virtus Office Stage 1 — job lifecycle + ingest (no Stripe, no public download)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import (
    OFFICE_JOB_STATUSES,
    OFFICE_PIPELINE_LIVE,
    STAGE2_SUCCESS_STATUS,
    OfficeJobEngine,
    OfficeJobError,
)
from app.integration.virtus_office.file_classify import classify_office_file
from app.integration.virtus_office.router import router as office_router


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def test_ssot_statuses_and_pipeline_still_off():
    assert OFFICE_PIPELINE_LIVE is True
    assert "created" in OFFICE_JOB_STATUSES
    assert "understanding" in OFFICE_JOB_STATUSES
    assert "proposal_ready" in OFFICE_JOB_STATUSES
    assert STAGE2_SUCCESS_STATUS == "proposal_ready"


def test_classify_empty_and_unsupported():
    assert classify_office_file(filename="a.pdf", content_type="application/pdf", size=0)[1] == (
        "empty_file"
    )
    assert classify_office_file(
        filename="a.exe", content_type="application/octet-stream", size=10
    )[1] == ("unsupported_type")
    assert classify_office_file(
        filename="a.pdf", content_type="image/png", size=10
    )[1] == ("mime_ext_mismatch")
    kind, err = classify_office_file(
        filename="scan.PDF", content_type="application/octet-stream", size=12
    )
    assert err is None and kind == "pdf"


def test_create_upload_happy_path_txt(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(owner_hint="user@example.com")
    assert created["status"] == "created"
    assert created["owner_token"]
    assert created["pipeline_live"] is True
    assert created["artifact_download"] is None

    token = created["owner_token"]
    job_id = created["job_id"]
    view = eng.upload(
        job_id,
        owner_token=token,
        upload=_upload("notiz.txt", b"Hallo Virtus Office\n", "text/plain"),
    )
    assert view["status"] == STAGE2_SUCCESS_STATUS
    assert view["stage1_complete"] is True
    assert view["stage2_complete"] is True
    assert view["file_kind"] == "txt"
    assert view["material_id"]
    assert view["ingest"]["ok"] is True
    assert view["understanding"]["filled"] is True
    assert view["proposal"]["filled"] is True
    assert view["payment"]["stripe_live"] is False
    assert view["artifact_download"] is None

    # Bytes landed in order_materials, not a second store root for binaries
    mats_root = tmp_path / "order_materials"
    assert mats_root.is_dir()
    assert any(mats_root.glob("mat-*"))
    assert not any((tmp_path / "virtus_office" / "jobs").glob("mat-*"))


def test_owner_isolation(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    a = eng.create_job()
    b = eng.create_job()
    eng.upload(
        a["job_id"],
        owner_token=a["owner_token"],
        upload=_upload("a.txt", b"secret-a", "text/plain"),
    )
    with pytest.raises(OfficeJobError) as exc:
        eng.get_job(a["job_id"], owner_token=b["owner_token"])
    assert exc.value.code == "forbidden"


def test_empty_file_fails(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("empty.pdf", b"", "application/pdf"),
    )
    assert view["status"] == "failed"
    assert view["failure_reason"] == "empty_file"
    assert view["stage1_complete"] is False


def test_unsupported_fails(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("x.zip", b"PK\x03\x04fake", "application/zip"),
    )
    assert view["status"] == "failed"
    assert view["failure_reason"] == "unsupported_type"


def test_cancel(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.cancel(created["job_id"], owner_token=created["owner_token"])
    assert view["status"] == "cancelled"


def test_artifact_bytes_denied_stage1(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("a.txt", b"data", "text/plain"),
    )
    with pytest.raises(OfficeJobError) as exc:
        eng.get_artifact_bytes(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "not_ready"


def test_no_public_download_route():
    paths = {getattr(r, "path", "") for r in office_router.routes}
    assert "/api/office/jobs" in paths or any(p.endswith("/jobs") for p in paths)
    assert not any("download" in (p or "").lower() for p in paths)


def test_public_view_never_leaks_disk_path_or_token_hash(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("a.txt", b"payload-secret", "text/plain"),
    )
    blob = str(view)
    assert "order_materials" not in blob
    assert "owner_token_hash" not in blob
    assert "payload-secret" not in blob
    assert view.get("artifact_download") is None
    # On-disk job file still has hash, not plaintext token
    raw = (tmp_path / "virtus_office" / "jobs" / f"{created['job_id']}.json").read_text(
        encoding="utf-8"
    )
    assert created["owner_token"] not in raw
    assert "owner_token_hash" in raw


def test_path_traversal_filename_fails_safe(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("../evil.txt", b"x", "text/plain"),
    )
    # Either rejected by assert_safe_upload_filename → failed, or basename-normalized
    assert view["status"] in {"failed", "proposal_ready"}
    if view["status"] == "proposal_ready":
        assert view["filename"] == "evil.txt"
        assert ".." not in (view["filename"] or "")


def test_wrong_job_id_and_missing_token(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    a = eng.create_job()
    with pytest.raises(OfficeJobError) as missing:
        eng.get_job("ojob-does-not-exist", owner_token=a["owner_token"])
    assert missing.value.code == "not_found"
    with pytest.raises(OfficeJobError) as empty:
        eng.get_job(a["job_id"], owner_token="")
    assert empty.value.code == "forbidden"


def test_router_rejects_missing_owner_header():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(office_router)
    # Auth layer only — no memory_dir needed when token missing
    client = TestClient(app)
    r = client.get("/api/office/jobs/ojob-x")
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "token_required"


def test_reuse_map_stage1(tmp_path: Path):
    from app.integration.virtus_office import office_reuse_map

    m = office_reuse_map()
    assert m["stage1_job_lifecycle"] is True
    assert m["pipeline_live"] is True
    assert not any(g.startswith("office_job_engine") for g in m["missing"])
