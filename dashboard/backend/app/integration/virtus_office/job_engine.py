"""Virtus Office Job Engine — Stage 1 ingest + Stage 2 understanding → proposal.

Bytes live only in OrderMaterialsService. No public download. No Stripe LIVE.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.integration.order_materials_service import OrderMaterialsService
from app.integration.virtus_office.bewerbung_profile import (
    extract_profile_draft_from_text,
    merge_profiles,
    missing_fields_for_action,
    normalize_profile,
)
from app.integration.virtus_office.bewerbung_ssot import (
    BEWERBUNG_ACTION_IDS,
    BEWERBUNG_DISCLAIMER_DE,
    bewerbung_action_meta,
)
from app.integration.virtus_office.file_classify import classify_office_file
from app.integration.virtus_office.language_catalog import (
    is_known_language,
    list_office_languages,
)
from app.integration.virtus_office.execution import execute_office_action, EXECUTABLE_ACTION_IDS
from app.integration.virtus_office.office_job_ssot import OFFICE_PIPELINE_LIVE, office_stripe_live
from app.integration.virtus_office.post_pay import (
    cabinet_summary,
    download_formats,
    progress_steps,
)
from app.integration.virtus_office.digital_product_delivery import delivery_public_view
from app.integration.virtus_office.quality_gate import run_quality_gate
from app.integration.virtus_office.understanding import (
    ACTION_CATALOG,
    CUSTOMER_EXECUTABLE_ACTIONS,
    build_proposal_from_understanding,
    build_understanding,
    _price_for,
)


class OfficeJobError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message or code
        super().__init__(self.message)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class OfficeJobEngine:
    """Stage 1–2: create → upload/ingest → understand → proposal_ready."""

    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._root = self._memory / "virtus_office" / "jobs"
        self._root.mkdir(parents=True, exist_ok=True)
        self._index = self._root / "index.jsonl"
        self._materials = OrderMaterialsService(self._memory)

    def create_job(
        self,
        *,
        owner_hint: str | None = None,
        service_preset: str | None = None,
        customer_id: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        job_id = f"ojob-{uuid.uuid4().hex[:16]}"
        owner_token = secrets.token_urlsafe(32)
        hint = re.sub(r"[^\w\-@.]", "_", (owner_hint or "anon").strip())[:64] or "anon"
        preset = (service_preset or "").strip().lower() or None
        if preset and preset not in {a["id"] for a in ACTION_CATALOG}:
            raise OfficeJobError("invalid_preset", f"Unbekannter Service-Preset: {preset}")
        cid = (customer_id or "").strip()[:80] or None
        em = (email or "").strip().lower()[:160] or None
        now = _utc_now()
        job: dict[str, Any] = {
            "job_id": job_id,
            "owner_hint": hint,
            "owner_token_hash": _hash_token(owner_token),
            "customer_id": cid,
            "email": em,
            "service_preset": preset,
            "status": "created",
            "material_id": None,
            "page_material_ids": [],
            "filename": None,
            "content_type": None,
            "ext": None,
            "size": None,
            "file_kind": None,
            "ingest": None,
            "understanding": None,
            "proposal": None,
            "payment": {
                "status": "none",
                "paid": False,
                "stripe_live": office_stripe_live(),
                "pipeline_live": OFFICE_PIPELINE_LIVE,
            },
            "artifact": None,
            "failure_reason": None,
            "failure_detail": None,
            "created_at": now,
            "updated_at": now,
            "stage1_complete": False,
            "stage2_complete": False,
            "stage3_complete": False,
            "quality": None,
            "bewerbung_profile": None,
            "photo_material_id": None,
        }
        self._write(job)
        public = self.public_view(job)
        return {**public, "owner_token": owner_token}

    def upload(
        self,
        job_id: str,
        *,
        owner_token: str,
        upload: UploadFile,
    ) -> dict[str, Any]:
        job = self._require_owner(job_id, owner_token)
        if job["status"] in {"cancelled", "completed"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")
        if job["status"] not in {"created", "failed"}:
            if job.get("material_id"):
                raise OfficeJobError(
                    "already_ingested",
                    "Datei bereits verknüpft — neuen Job starten",
                )

        job["status"] = "uploading"
        job["failure_reason"] = None
        job["failure_detail"] = None
        job["updated_at"] = _utc_now()
        self._write(job)

        filename = Path(upload.filename or "file").name
        content_type = (upload.content_type or "application/octet-stream").split(";")[0].strip()
        try:
            data = upload.file.read()
        except Exception as exc:  # noqa: BLE001
            return self._fail(job, "read_error", str(exc)[:200])

        size = len(data)
        kind, reason = classify_office_file(
            filename=filename, content_type=content_type, size=size
        )
        if reason:
            detail = {
                "empty_file": "Datei ist leer",
                "unsupported_type": "Dateityp nicht unterstützt (PDF, JPG, PNG, DOCX, XLSX, CSV, TXT)",
                "mime_ext_mismatch": "MIME-Typ passt nicht zur Dateiendung",
            }.get(reason, reason)
            return self._fail(job, reason, detail)

        try:
            mat = self._materials.save_bytes(
                data,
                filename=filename,
                content_type=content_type,
                session_id=f"office-job:{job_id}",
                meta={
                    "office_job_id": job_id,
                    "owner_hint": job.get("owner_hint"),
                    "file_kind": kind,
                },
            )
        except ValueError as exc:
            return self._fail(job, "ingest_rejected", str(exc)[:300])
        except Exception as exc:  # noqa: BLE001
            return self._fail(job, "ingest_error", str(exc)[:300])

        job["status"] = "ingested"
        job["material_id"] = mat.get("id")
        job["page_material_ids"] = [mat.get("id")] if mat.get("id") else []
        job["filename"] = mat.get("filename") or filename
        job["content_type"] = mat.get("content_type") or content_type
        job["ext"] = Path(job["filename"] or filename).suffix.lower()
        job["size"] = mat.get("size") if mat.get("size") is not None else size
        job["file_kind"] = kind
        job["ingest"] = {
            "ok": True,
            "material_id": mat.get("id"),
            "findings": mat.get("findings") or [],
            "status_de": mat.get("status_de"),
            "_internal_ok": True,
        }
        job["stage1_complete"] = True
        job["updated_at"] = _utc_now()
        self._write(job)

        return self._run_stage2_understanding(job, data=data)

    def upload_pages(
        self,
        job_id: str,
        *,
        owner_token: str,
        uploads: list[UploadFile],
    ) -> dict[str, Any]:
        """Multi-image ingest (phone multi-shot) → one OCR document → proposal."""
        job = self._require_owner(job_id, owner_token)
        if job["status"] in {"cancelled", "completed"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")
        if job.get("material_id"):
            raise OfficeJobError(
                "already_ingested",
                "Datei bereits verknüpft — neuen Job starten",
            )
        if not uploads:
            raise OfficeJobError("empty_upload", "Keine Dateien")

        job["status"] = "uploading"
        job["failure_reason"] = None
        job["failure_detail"] = None
        job["updated_at"] = _utc_now()
        self._write(job)

        page_blobs: list[tuple[bytes, str, str]] = []  # data, filename, content_type
        for upload in uploads:
            filename = Path(upload.filename or "page.png").name
            content_type = (upload.content_type or "application/octet-stream").split(";")[0].strip()
            try:
                data = upload.file.read()
            except Exception as exc:  # noqa: BLE001
                return self._fail(job, "read_error", str(exc)[:200])
            size = len(data)
            kind, reason = classify_office_file(
                filename=filename, content_type=content_type, size=size
            )
            if reason:
                return self._fail(
                    job,
                    reason,
                    {
                        "empty_file": "Datei ist leer",
                        "unsupported_type": "Nur JPG/PNG für Mehrseiten-Upload",
                        "mime_ext_mismatch": "MIME-Typ passt nicht zur Dateiendung",
                    }.get(reason, reason),
                )
            if kind != "image":
                return self._fail(
                    job,
                    "unsupported_type",
                    "Mehrseiten-Upload akzeptiert nur JPG/PNG (PDF als eine Datei hochladen)",
                )
            page_blobs.append((data, filename, content_type))

        material_ids: list[str] = []
        try:
            for i, (data, filename, content_type) in enumerate(page_blobs):
                mat = self._materials.save_bytes(
                    data,
                    filename=filename,
                    content_type=content_type,
                    session_id=f"office-job:{job_id}",
                    meta={
                        "office_job_id": job_id,
                        "owner_hint": job.get("owner_hint"),
                        "file_kind": "image",
                        "page_index": i,
                    },
                )
                mid = mat.get("id")
                if mid:
                    material_ids.append(str(mid))
        except ValueError as exc:
            return self._fail(job, "ingest_rejected", str(exc)[:300])
        except Exception as exc:  # noqa: BLE001
            return self._fail(job, "ingest_error", str(exc)[:300])

        first_data, first_name, first_ctype = page_blobs[0]
        job["status"] = "ingested"
        job["material_id"] = material_ids[0] if material_ids else None
        job["page_material_ids"] = material_ids
        job["filename"] = first_name
        job["content_type"] = first_ctype
        job["ext"] = Path(first_name).suffix.lower()
        job["size"] = sum(len(b[0]) for b in page_blobs)
        job["file_kind"] = "image"
        job["ingest"] = {
            "ok": True,
            "material_id": job["material_id"],
            "page_count": len(page_blobs),
            "page_material_ids": material_ids,
            "findings": [],
            "status_de": f"{len(page_blobs)} Bildseite(n) aufgenommen",
            "_internal_ok": True,
        }
        job["stage1_complete"] = True
        job["updated_at"] = _utc_now()
        self._write(job)

        extras = [(b, ct) for b, _n, ct in page_blobs[1:]]
        return self._run_stage2_understanding(job, data=first_data, extra_pages=extras)

    def _run_stage2_understanding(
        self,
        job: dict[str, Any],
        *,
        data: bytes,
        extra_pages: list[tuple[bytes, str]] | None = None,
    ) -> dict[str, Any]:
        job["status"] = "understanding"
        job["updated_at"] = _utc_now()
        self._write(job)

        understanding = build_understanding(
            data=data,
            filename=str(job.get("filename") or "file"),
            file_kind=str(job.get("file_kind") or ""),
            content_type=str(job.get("content_type") or ""),
            service_preset=job.get("service_preset"),
            extra_pages=extra_pages,
        )
        # Seed Bewerbung draft from extracted text (no invent beyond heuristics)
        text_excerpt = ""
        try:
            from app.integration.virtus_office.document_parse import parse_office_file

            parsed = parse_office_file(
                data=data,
                filename=str(job.get("filename") or "file"),
                file_kind=str(job.get("file_kind") or ""),
                content_type=str(job.get("content_type") or ""),
                extra_pages=extra_pages,
            )
            text_excerpt = str(parsed.get("text") or "")
        except Exception:
            text_excerpt = ""
        if text_excerpt.strip() and (
            job.get("service_preset") in BEWERBUNG_ACTION_IDS
            or (understanding.get("document_type") in {"cv_lebenslauf", "cover_letter"})
        ):
            draft = extract_profile_draft_from_text(
                text_excerpt, filename=str(job.get("filename") or "")
            )
            job["bewerbung_profile"] = merge_profiles(job.get("bewerbung_profile") or {}, draft)

        proposal = build_proposal_from_understanding(
            understanding,
            filename=str(job.get("filename") or "file"),
        )
        if (understanding.get("intent") or {}).get("id") in BEWERBUNG_ACTION_IDS:
            proposal = self._enrich_bewerbung_proposal(job, understanding, proposal)

        job["understanding"] = understanding
        job["proposal"] = proposal
        job["status"] = "proposal_ready"
        job["stage2_complete"] = True
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def _enrich_bewerbung_proposal(
        self,
        job: dict[str, Any],
        understanding: dict[str, Any],
        proposal: dict[str, Any],
    ) -> dict[str, Any]:
        intent = dict(understanding.get("intent") or {})
        action_id = str(intent.get("id") or "")
        profile = normalize_profile(job.get("bewerbung_profile") or {})
        if job.get("photo_material_id"):
            profile["photo_material_id"] = job["photo_material_id"]
        missing = missing_fields_for_action(action_id, profile)
        proposal = dict(proposal)
        proposal["missing_fields"] = missing
        proposal["profile_ready"] = len(missing) == 0
        proposal["disclaimer_de"] = BEWERBUNG_DISCLAIMER_DE
        proposal["bewerbung_actions"] = bewerbung_action_meta()
        if missing:
            proposal["next_step"] = "complete_profile"
            proposal["stage3_ready"] = False
            proposal["continue_hint_de"] = (
                "Es fehlen Angaben — bitte Formular ausfüllen. Nichts wird erfunden."
            )
        else:
            proposal["next_step"] = "awaiting_stage3"
            proposal["stage3_ready"] = True
            from app.integration.virtus_office.customer_preview import build_customer_preview

            intent_id = str(
                ((job.get("understanding") or {}).get("intent") or {}).get("id")
                or job.get("service_preset")
                or "lebenslauf_create"
            )
            proposal["preview"] = build_customer_preview(
                action_id=intent_id,
                profile=profile,
            )
            proposal["continue_hint_de"] = (
                "Vorschau bereit — vollständiges Dokument erst nach Zahlung."
            )
        return proposal

    def submit_bewerbung_profile(
        self,
        job_id: str,
        *,
        owner_token: str,
        profile: dict[str, Any],
        action_id: str | None = None,
        output_format: str | None = None,
    ) -> dict[str, Any]:
        """Merge structured form into job profile; gate missing fields (no invent)."""
        job = self._require_owner(job_id, owner_token)
        payment = dict(job.get("payment") or {})
        if payment.get("price_lock") or payment.get("requires_payment"):
            raise OfficeJobError(
                "price_locked",
                "Preis und Parameter sind gesperrt — Änderungen abgelehnt",
            )
        if job["status"] not in {"created", "proposal_ready", "understanding", "failed"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")

        understanding = dict(job.get("understanding") or {})
        intent = dict(understanding.get("intent") or {})
        aid = (action_id or intent.get("id") or job.get("service_preset") or "").strip().lower()
        if aid not in BEWERBUNG_ACTION_IDS:
            raise OfficeJobError("invalid_action", "Bitte Bewerbung-Aktion wählen")

        meta = next((a for a in ACTION_CATALOG if a["id"] == aid), None)
        merged = merge_profiles(job.get("bewerbung_profile") or {}, profile or {})
        if job.get("photo_material_id"):
            merged["photo_material_id"] = job["photo_material_id"]
        job["bewerbung_profile"] = merged

        out_fmt = (output_format or intent.get("output_format") or (meta or {}).get("default_output") or "pdf")
        intent = {
            "id": aid,
            "source_language": "de",
            "detected_source_language": understanding.get("language") or "de",
            "target_language": "de",
            "output_format": str(out_fmt).lower(),
            "locked": bool((job.get("service_preset") or "") == aid),
            "label_de": (meta or {}).get("label_de") or aid,
            "price_eur": _price_for(aid),
        }
        understanding["intent"] = intent
        understanding["suggested_intent"] = aid
        understanding["filled"] = True
        understanding["needs_user_choice"] = False
        if not understanding.get("stage"):
            understanding["stage"] = "understood"
        understanding["summary_de"] = understanding.get("summary_de") or "Bewerbung-Profil"

        # Profile-only jobs (no upload yet)
        if job["status"] == "created" and not job.get("material_id"):
            job["stage1_complete"] = True
            job["ingest"] = {
                "ok": True,
                "material_id": None,
                "findings": [],
                "status_de": "Profil ohne Datei (Formular)",
                "_internal_ok": True,
            }
            job["filename"] = job.get("filename") or "bewerbung-profil.json"
            job["file_kind"] = job.get("file_kind") or "txt"

        proposal = build_proposal_from_understanding(
            understanding,
            filename=str(job.get("filename") or "bewerbung-profil"),
            intent_override=intent,
        )
        proposal = self._enrich_bewerbung_proposal(job, understanding, proposal)

        job["understanding"] = understanding
        job["proposal"] = proposal
        job["status"] = "proposal_ready"
        job["stage2_complete"] = True
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def attach_bewerbung_photo(
        self,
        job_id: str,
        *,
        owner_token: str,
        upload: UploadFile,
    ) -> dict[str, Any]:
        """JPG/PNG → profile.photo_material_id for CV layout."""
        job = self._require_owner(job_id, owner_token)
        if job["status"] in {"cancelled", "completed"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")
        filename = Path(upload.filename or "foto.jpg").name
        content_type = (upload.content_type or "application/octet-stream").split(";")[0].strip()
        try:
            data = upload.file.read()
        except Exception as exc:  # noqa: BLE001
            raise OfficeJobError("read_error", str(exc)[:200]) from exc
        kind, reason = classify_office_file(
            filename=filename, content_type=content_type, size=len(data)
        )
        if reason or kind != "image":
            raise OfficeJobError("unsupported_type", "Foto muss JPG oder PNG sein")
        try:
            mat = self._materials.save_bytes(
                data,
                filename=filename,
                content_type=content_type,
                session_id=f"office-job:{job_id}",
                meta={
                    "office_job_id": job_id,
                    "office_photo": True,
                    "file_kind": "image",
                },
            )
        except Exception as exc:  # noqa: BLE001
            raise OfficeJobError("ingest_error", str(exc)[:300]) from exc
        mid = mat.get("id")
        job["photo_material_id"] = mid
        profile = normalize_profile(job.get("bewerbung_profile") or {})
        profile["photo_material_id"] = mid
        job["bewerbung_profile"] = profile
        if job.get("understanding") and (job.get("understanding") or {}).get("intent"):
            proposal = dict(job.get("proposal") or {})
            proposal = self._enrich_bewerbung_proposal(
                job, dict(job.get("understanding") or {}), proposal
            )
            job["proposal"] = proposal
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def select_action(
        self,
        job_id: str,
        *,
        owner_token: str,
        action_id: str,
        target_language: str | None = None,
        source_language: str | None = None,
        output_format: str | None = None,
        document_settings: dict[str, Any] | None = None,
        special_wishes: str | None = None,
        confirm_settings: bool = True,
    ) -> dict[str, Any]:
        job = self._require_owner(job_id, owner_token)
        payment = dict(job.get("payment") or {})
        if payment.get("price_lock") or payment.get("requires_payment"):
            raise OfficeJobError(
                "price_locked",
                "Preis und Parameter sind gesperrt — Änderungen abgelehnt",
            )
        if job["status"] not in {"proposal_ready", "understanding"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")
        understanding = dict(job.get("understanding") or {})
        if not understanding.get("filled"):
            raise OfficeJobError("not_ready", "Understanding fehlt")

        action = next((a for a in ACTION_CATALOG if a["id"] == action_id), None)
        if not action:
            raise OfficeJobError("invalid_action", f"Unbekannte Aktion: {action_id}")
        if action["id"] not in CUSTOMER_EXECUTABLE_ACTIONS or not action.get(
            "customer_sellable", True
        ):
            raise OfficeJobError(
                "action_not_available",
                f"Aktion derzeit nicht verfügbar: {action_id}",
            )

        tgt = (target_language or "").strip().lower().split("-")[0] or None
        if action["needs_target_language"]:
            if not tgt or not is_known_language(tgt) or tgt in {"auto", "unknown"}:
                tgt = tgt if tgt and is_known_language(tgt) and tgt not in {"auto", "unknown"} else None
        else:
            tgt = None

        src_override = (source_language or "").strip().lower().split("-")[0] or None
        if src_override in {"", "auto", "unknown"}:
            src_override = None
        if src_override and not is_known_language(src_override):
            src_override = None

        out_fmt = (output_format or action["default_output"] or "pdf").strip().lower()
        detected_src = understanding.get("language")
        intent = {
            "id": action["id"],
            "source_language": src_override or "auto",
            "detected_source_language": detected_src,
            "source_language_override": src_override,
            "target_language": tgt,
            "output_format": out_fmt,
            "locked": bool((job.get("service_preset") or "") == action["id"]),
            "label_de": action["label_de"],
            "price_eur": _price_for(action["id"]),
        }
        understanding["intent"] = intent
        understanding["needs_user_choice"] = False
        understanding["suggested_intent"] = action["id"]
        understanding["suggested_output_format"] = out_fmt
        understanding["suggested_price_eur"] = _price_for(action["id"])

        # Dokument anpassen — build or confirm settings
        from app.integration.virtus_office.document_settings import build_document_settings

        explanation = understanding.get("explanation") if isinstance(
            understanding.get("explanation"), dict
        ) else {}
        values = dict(document_settings or {})
        if tgt:
            values.setdefault("target_language", tgt)
        if src_override:
            values.setdefault("source_language", src_override)
        if out_fmt:
            values.setdefault("output_format", out_fmt)

        settings = build_document_settings(
            action_id=action["id"],
            document_type=str(understanding.get("document_type") or ""),
            explanation=explanation,
            values=values,
            special_wishes=special_wishes,
            sections=list(explanation.get("sections") or []),
        )
        settings["confirmed"] = bool(confirm_settings)
        intent["document_settings"] = settings
        understanding["intent"] = intent

        proposal = build_proposal_from_understanding(
            understanding,
            filename=str(job.get("filename") or "file"),
            intent_override=intent,
        )
        proposal["document_settings"] = settings

        # Flow: action → configure_document → (optional confirm) → pay
        if action["needs_target_language"] and not tgt:
            proposal["next_step"] = "configure_document"
            proposal["show_choice_cards"] = False
            proposal["stage3_ready"] = False
            proposal["low_confidence"] = False
        elif action["id"] in BEWERBUNG_ACTION_IDS:
            proposal = self._enrich_bewerbung_proposal(job, understanding, proposal)
        elif not confirm_settings:
            proposal["next_step"] = "configure_document"
            proposal["show_choice_cards"] = False
            proposal["stage3_ready"] = False
            proposal["payment_enabled"] = False
        else:
            from app.integration.virtus_office.customer_preview import build_customer_preview

            structure = dict(understanding.get("structure") or {})
            proposal["preview"] = build_customer_preview(
                action_id=action["id"],
                document_hint={
                    "task_label_de": action["label_de"],
                    "language": understanding.get("language"),
                    "language_label_de": understanding.get("language_label_de"),
                    "pages": structure.get("pages") or understanding.get("page_count"),
                    "structure": [
                        understanding.get("document_type_label_de")
                        or understanding.get("document_type")
                        or "Dokument",
                    ],
                },
            )
            # Merge change preview snippets into customer preview excerpt
            change_lines = []
            for row in settings.get("preview") or []:
                if isinstance(row, dict) and row.get("before") and row.get("after"):
                    change_lines.append(f"Vorher: {row['before']}\nNachher: {row['after']}")
            if change_lines and isinstance(proposal.get("preview"), dict):
                proposal["preview"]["change_preview"] = settings.get("preview")
                proposal["preview"]["excerpt"] = (
                    (proposal["preview"].get("excerpt") or "")
                    + ("\n\n" if proposal["preview"].get("excerpt") else "")
                    + "\n\n".join(change_lines[:4])
                )
            proposal["next_step"] = "awaiting_stage3"
            proposal["stage3_ready"] = True
            proposal["payment_enabled"] = True

        job["understanding"] = understanding
        job["proposal"] = proposal
        job["status"] = "proposal_ready"
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def configure_document_settings(
        self,
        job_id: str,
        *,
        owner_token: str,
        values: dict[str, Any] | None = None,
        special_wishes: str | None = None,
        confirm: bool = False,
        action_id: str | None = None,
        target_language: str | None = None,
        source_language: str | None = None,
        output_format: str | None = None,
    ) -> dict[str, Any]:
        """Update Dokument anpassen without changing the chosen action."""
        job = self._require_owner(job_id, owner_token)
        understanding = dict(job.get("understanding") or {})
        intent = dict(understanding.get("intent") or {})
        aid = (action_id or intent.get("id") or "").strip()
        if not aid:
            raise OfficeJobError("action_required", "Bitte zuerst eine Aufgabe wählen")
        return self.select_action(
            job_id,
            owner_token=owner_token,
            action_id=aid,
            target_language=target_language or intent.get("target_language"),
            source_language=source_language
            or intent.get("source_language_override")
            or intent.get("source_language"),
            output_format=output_format or intent.get("output_format"),
            document_settings=values,
            special_wishes=special_wishes,
            confirm_settings=confirm,
        )

    def bind_customer(
        self,
        job_id: str,
        *,
        owner_token: str,
        customer_id: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        job = self._require_owner(job_id, owner_token)
        cid = (customer_id or "").strip()[:80] or None
        em = (email or "").strip().lower()[:160] or None
        if cid:
            job["customer_id"] = cid
        if em:
            job["email"] = em
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def list_for_customer(
        self,
        *,
        customer_id: str,
        email: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        cid = str(customer_id or "").strip()
        em = str(email or "").strip().lower()
        if not cid and not em:
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self._root.glob("ojob-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            job = self._load_path(path)
            if not job:
                continue
            if not self._customer_owns(job, customer_id=cid, email=em):
                continue
            view = self.public_view(job)
            rows.append(
                cabinet_summary(
                    job,
                    download_ready=bool(view.get("artifact_download")),
                )
            )
            if len(rows) >= max(1, min(100, limit)):
                break
        return rows

    def get_for_customer(
        self,
        job_id: str,
        *,
        customer_id: str,
        email: str | None = None,
    ) -> dict[str, Any]:
        job = self._load(job_id)
        if not job:
            raise OfficeJobError("not_found", "Job nicht gefunden")
        if not self._customer_owns(job, customer_id=customer_id, email=email):
            raise OfficeJobError("forbidden", "Kein Zugriff auf diesen Job")
        return self.public_view(job)

    def execute_for_customer(
        self,
        job_id: str,
        *,
        customer_id: str,
        email: str | None = None,
    ) -> dict[str, Any]:
        job = self._load(job_id)
        if not job:
            raise OfficeJobError("not_found", "Job nicht gefunden")
        if not self._customer_owns(job, customer_id=customer_id, email=email):
            raise OfficeJobError("forbidden", "Kein Zugriff auf diesen Job")
        # Re-enter owner path via temporary trust: use internal execute after ownership check
        return self._execute_job(job)

    def get_artifact_for_customer(
        self,
        job_id: str,
        *,
        customer_id: str,
        email: str | None = None,
        fmt: str | None = None,
    ) -> tuple[bytes, str, str]:
        job = self._load(job_id)
        if not job:
            raise OfficeJobError("not_found", "Job nicht gefunden")
        if not self._customer_owns(job, customer_id=customer_id, email=email):
            raise OfficeJobError("forbidden", "Kein Zugriff auf diesen Job")
        return self._artifact_bytes(job, fmt=fmt)

    def get_artifact_bytes(
        self, job_id: str, *, owner_token: str, fmt: str | None = None
    ) -> tuple[bytes, str, str]:
        job = self._require_owner(job_id, owner_token)
        return self._artifact_bytes(job, fmt=fmt)

    def get_artifact_with_delivery_token(
        self, job_id: str, *, delivery_token: str, fmt: str | None = None
    ) -> tuple[bytes, str, str]:
        from app.integration.virtus_office.digital_product_delivery import (
            verify_delivery_token,
        )

        job = self._load(job_id)
        if not job:
            raise OfficeJobError("not_found", "Job nicht gefunden")
        if not verify_delivery_token(job, delivery_token):
            raise OfficeJobError("forbidden", "Ungültiger Delivery-Token")
        return self._artifact_bytes(job, fmt=fmt)

    def _artifact_bytes(
        self, job: dict[str, Any], *, fmt: str | None = None
    ) -> tuple[bytes, str, str]:
        artifact = job.get("artifact") or {}
        if artifact.get("held_for_qa_fail"):
            raise OfficeJobError("quality_gate_failed", "Quality Gate nicht bestanden")
        if job["status"] != "completed":
            raise OfficeJobError("not_ready", "Ergebnis noch nicht bereit")
        payment = job.get("payment") or {}
        if not payment.get("paid"):
            raise OfficeJobError("payment_required", "Zahlung erforderlich")
        if not artifact.get("material_id"):
            raise OfficeJobError("no_artifact", "Kein Ergebnis vorhanden")
        ext = str(artifact.get("ext") or "").lower().lstrip(".")
        want = (fmt or "").strip().lower().lstrip(".")
        if want and want != ext:
            raise OfficeJobError(
                "format_unavailable",
                f"Format {want.upper()} für diesen Auftrag nicht verfügbar",
            )
        material_id = str(artifact.get("material_id") or "")
        # Bind artifact to this job — refuse foreign material ids
        loaded = self._materials.read_bytes(material_id) if material_id else None
        if not loaded:
            raise OfficeJobError("no_artifact", "Kein Ergebnis vorhanden")
        data, mat = loaded
        mat_meta = (mat or {}).get("meta") if isinstance(mat, dict) else {}
        if isinstance(mat_meta, dict):
            art_job = str(mat_meta.get("office_job_id") or "")
            if art_job and art_job != str(job.get("job_id")):
                raise OfficeJobError("forbidden", "Artefakt gehört zu einem anderen Auftrag")
        filename = str(artifact.get("filename") or f"{job['job_id']}.{ext or 'bin'}")
        mime = str(artifact.get("mime") or "application/octet-stream")
        return data, filename, mime

    def _customer_owns(
        self,
        job: dict[str, Any],
        *,
        customer_id: str,
        email: str | None = None,
    ) -> bool:
        cid = str(customer_id or "").strip()
        em = str(email or "").strip().lower()
        job_cid = str(job.get("customer_id") or "").strip()
        job_em = str(job.get("email") or "").strip().lower()
        if cid and job_cid and cid == job_cid:
            return True
        if em and job_em and em == job_em and not job_cid:
            return True
        return False

    def cancel(self, job_id: str, *, owner_token: str) -> dict[str, Any]:
        job = self._require_owner(job_id, owner_token)
        if job["status"] in {"completed", "cancelled"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")
        if job["status"] in {"paid", "executing", "quality_check"}:
            raise OfficeJobError("invalid_state", "Job bereits in Ausführung")
        job["status"] = "cancelled"
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def get_job(self, job_id: str, *, owner_token: str) -> dict[str, Any]:
        return self.public_view(self._require_owner(job_id, owner_token))

    def continue_stub(self, job_id: str, *, owner_token: str) -> dict[str, Any]:
        """Alias → Stage 3 execute (keeps Stage 2 API clients working)."""
        return self.execute(job_id, owner_token=owner_token)

    def execute(self, job_id: str, *, owner_token: str) -> dict[str, Any]:
        job = self._require_owner(job_id, owner_token)
        return self._execute_job(job)

    def _execute_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """proposal_ready|paid → executing → quality_check → completed|failed."""
        from app.integration.virtus_office.payment_bridge import (
            assert_price_lock_intact,
            payment_gate_blocks_execute,
        )

        job_id = str(job.get("job_id") or "")
        if job["status"] not in {"proposal_ready", "paid", "awaiting_payment"}:
            raise OfficeJobError("invalid_state", f"Job is {job['status']}")

        proposal = dict(job.get("proposal") or {})
        intent = dict((job.get("understanding") or {}).get("intent") or {})
        if proposal.get("next_step") == "select_action":
            raise OfficeJobError("action_required", "Bitte zuerst eine Aktion wählen")
        if proposal.get("next_step") == "complete_profile":
            raise OfficeJobError(
                "profile_incomplete",
                "Profil unvollständig — fehlende Felder ausfüllen (nichts wird erfunden)",
            )
        if intent.get("id") == "translate" and not intent.get("target_language"):
            raise OfficeJobError("target_language_required", "Bitte Zielsprache wählen")
        if not intent.get("id"):
            raise OfficeJobError("action_required", "Bitte zuerst eine Aktion wählen")

        # CRA honesty: after config is valid, final execution requires payment
        if payment_gate_blocks_execute(job):
            raise OfficeJobError("payment_required", "Zahlung erforderlich vor Ausführung")
        payment = dict(job.get("payment") or {})
        if payment.get("price_lock"):
            assert_price_lock_intact(job)

        executable = EXECUTABLE_ACTION_IDS
        if intent.get("id") not in executable:
            raise OfficeJobError(
                "unsupported_action",
                f"Aktion noch nicht ausgeführt: {intent.get('id')}",
            )

        is_bewerbung = intent.get("id") in BEWERBUNG_ACTION_IDS
        data = b""
        extra_pages: list[tuple[bytes, str]] = []
        photo_bytes: bytes | None = None
        profile = normalize_profile(job.get("bewerbung_profile") or {})

        if is_bewerbung:
            missing = missing_fields_for_action(str(intent["id"]), profile)
            if missing:
                return self._fail_execution(
                    job,
                    "profile_incomplete",
                    "Fehlend: " + ", ".join(m["label_de"] for m in missing),
                )
            photo_id = job.get("photo_material_id") or profile.get("photo_material_id")
            if photo_id:
                loaded_photo = self._materials.read_bytes(str(photo_id))
                if loaded_photo:
                    photo_bytes, _ = loaded_photo
                    profile["photo_material_id"] = str(photo_id)
        else:
            material_id = str(job.get("material_id") or "")
            loaded = self._materials.read_bytes(material_id) if material_id else None
            if not loaded:
                return self._fail_execution(job, "material_missing", "Quelldatei nicht gefunden")
            data, _mat = loaded
            page_ids = list(job.get("page_material_ids") or [])
            if len(page_ids) > 1:
                for mid in page_ids[1:]:
                    page_loaded = self._materials.read_bytes(str(mid))
                    if not page_loaded:
                        continue
                    page_bytes, page_mat = page_loaded
                    ct = str((page_mat or {}).get("content_type") or "image/png")
                    extra_pages.append((page_bytes, ct))

        job["status"] = "executing"
        job["failure_reason"] = None
        job["failure_detail"] = None
        job["updated_at"] = _utc_now()
        self._write(job)

        result = execute_office_action(
            action_id=str(intent["id"]),
            data=data,
            filename=str(job.get("filename") or "file"),
            file_kind=str(job.get("file_kind") or ""),
            content_type=str(job.get("content_type") or ""),
            intent=intent,
            understanding=dict(job.get("understanding") or {}),
            extra_pages=extra_pages or None,
            profile=profile if is_bewerbung else None,
            photo_bytes=photo_bytes,
        )
        if not result.get("ok"):
            return self._fail_execution(
                job,
                str(result.get("error") or "execution_failed"),
                str(result.get("detail") or "Ausführung fehlgeschlagen"),
            )

        job["status"] = "quality_check"
        job["updated_at"] = _utc_now()
        self._write(job)

        try:
            art_mat = self._materials.save_bytes(
                result["bytes"],
                filename=str(result["filename"]),
                content_type=str(result["mime"]),
                session_id=f"office-artifact:{job_id}",
                meta={
                    "office_job_id": job_id,
                    "office_artifact": True,
                    "action_id": intent.get("id"),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return self._fail_execution(job, "artifact_store_failed", str(exc)[:300])

        qa = run_quality_gate(
            action_id=str(intent["id"]),
            input_text=str(result.get("quality_input_text") or ""),
            output_text=str(result.get("quality_output_text") or ""),
            artifact_bytes=result["bytes"],
            artifact_ext=str(result["ext"]),
            artifact_mime=str(result["mime"]),
            target_language=result.get("target_language") or intent.get("target_language"),
            translation_provider=result.get("translation_provider"),
            expected_entities=list(result.get("entities") or []),
            job_id=job_id,
            artifact_job_id=job_id,
            profile_facts=result.get("profile_facts"),
            photo_placed=bool(result.get("photo_placed")),
            document_type=result.get("document_type")
            or (job.get("understanding") or {}).get("document_type"),
            source_page_count=result.get("source_page_count")
            or (job.get("understanding") or {}).get("page_count"),
            source_image_count=result.get("source_image_count"),
            delivery_mode=result.get("delivery_mode"),
            ocr_financial_qa=result.get("ocr_financial_qa"),
        )
        job["quality"] = {
            "passed": qa["passed"],
            "failed": qa["failed"],
            "checks": qa["checks"],
            "provider": result.get("translation_provider"),
        }
        if not qa["passed"]:
            job["artifact"] = {
                "material_id": art_mat.get("id"),
                "filename": result["filename"],
                "ext": result["ext"],
                "mime": result["mime"],
                "size": len(result["bytes"]),
                "held_for_qa_fail": True,
            }
            if result.get("quality_report"):
                job["quality_report"] = result["quality_report"]
            job["status"] = "failed"
            job["failure_reason"] = "quality_gate_failed"
            job["failure_detail"] = "Quality Gate FAIL: " + ", ".join(qa["failed"][:8])
            job["stage3_complete"] = False
            proposal["next_step"] = "quality_failed"
            job["proposal"] = proposal
            job["updated_at"] = _utc_now()
            self._write(job)
            return self.public_view(job)

        job["artifact"] = {
            "material_id": art_mat.get("id"),
            "filename": result["filename"],
            "ext": result["ext"],
            "mime": result["mime"],
            "size": len(result["bytes"]),
            "held_for_qa_fail": False,
        }
        if result.get("quality_report"):
            job["quality_report"] = result["quality_report"]
        job["status"] = "completed"
        job["stage3_complete"] = True
        job["failure_reason"] = None
        job["failure_detail"] = None
        proposal["next_step"] = "completed"
        proposal["stage3_ready"] = True
        proposal["continue_hint_de"] = "Ihr Dokument ist fertig."
        job["proposal"] = proposal
        job["updated_at"] = _utc_now()
        self._write(job)
        # CC-4 Digital Product Delivery (cabinet + email) — email fail ≠ incomplete
        try:
            from app.integration.virtus_office.digital_product_delivery import (
                deliver_completed_product,
            )

            deliver_completed_product(self, job)
            refreshed = self._load(job_id)
            if refreshed:
                job = refreshed
        except Exception:
            pass
        return self.public_view(job)

    def public_view(self, job: dict[str, Any]) -> dict[str, Any]:
        ingest = job.get("ingest")
        ingest_public = None
        if isinstance(ingest, dict):
            ingest_public = {
                "ok": bool(ingest.get("ok")),
                "material_id": ingest.get("material_id"),
                "page_count": ingest.get("page_count") or (1 if ingest.get("material_id") else None),
                "page_material_ids": ingest.get("page_material_ids") or job.get("page_material_ids") or [],
                "findings": ingest.get("findings") or [],
                "status_de": ingest.get("status_de"),
            }
        understanding = job.get("understanding")
        if isinstance(understanding, dict):
            understanding = {
                k: v
                for k, v in understanding.items()
                if k not in {"text", "raw_text"}
            }
        artifact = job.get("artifact")
        artifact_public = None
        download_ready = False
        if isinstance(artifact, dict) and artifact.get("material_id"):
            artifact_public = {
                "filename": artifact.get("filename"),
                "ext": artifact.get("ext"),
                "mime": artifact.get("mime"),
                "size": artifact.get("size"),
                "held_for_qa_fail": bool(artifact.get("held_for_qa_fail")),
            }
            download_ready = (
                job.get("status") == "completed"
                and not artifact.get("held_for_qa_fail")
                and bool((job.get("payment") or {}).get("paid"))
            )
        quality = job.get("quality")
        quality_public = None
        if isinstance(quality, dict):
            quality_public = {
                "passed": bool(quality.get("passed")),
                "failed": quality.get("failed") or [],
                "check_count": len(quality.get("checks") or []),
                "provider": quality.get("provider"),
            }
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "service_preset": job.get("service_preset"),
            "filename": job.get("filename"),
            "content_type": job.get("content_type"),
            "ext": job.get("ext"),
            "size": job.get("size"),
            "file_kind": job.get("file_kind"),
            "material_id": job.get("material_id"),
            "page_material_ids": list(job.get("page_material_ids") or []),
            "photo_material_id": job.get("photo_material_id"),
            "bewerbung_profile": job.get("bewerbung_profile"),
            "ingest": ingest_public,
            "understanding": understanding,
            "proposal": job.get("proposal"),
            "quality": quality_public,
            "artifact": artifact_public,
            "languages": list_office_languages(),
            "payment": {
                "status": (job.get("payment") or {}).get("status", "none"),
                "paid": bool((job.get("payment") or {}).get("paid")),
                "requires_payment": bool((job.get("payment") or {}).get("requires_payment")),
                "price_locked": bool((job.get("payment") or {}).get("price_lock")),
                "price_locked_at": (job.get("payment") or {}).get("price_locked_at"),
                "order_id": (job.get("payment") or {}).get("order_id"),
                "checkout_url": (job.get("payment") or {}).get("checkout_url"),
                "price_eur": ((job.get("payment") or {}).get("price_lock") or {}).get("price_eur"),
                "stripe_live": office_stripe_live(),
                "pipeline_live": OFFICE_PIPELINE_LIVE,
                "execute_unlocked": bool((job.get("payment") or {}).get("paid")),
            },
            "has_artifact": bool(artifact_public) and not bool((artifact or {}).get("held_for_qa_fail")),
            "artifact_download": (
                f"/api/office/jobs/{job['job_id']}/artifact" if download_ready else None
            ),
            "download_formats": download_formats(job, download_ready=download_ready),
            "progress": progress_steps(job),
            "delivery": delivery_public_view(job),
            "quality_report": job.get("quality_report") if isinstance(job.get("quality_report"), dict) else None,
            "customer_id": job.get("customer_id"),
            "email": job.get("email"),
            "failure_reason": job.get("failure_reason"),
            "failure_detail": job.get("failure_detail"),
            "stage1_complete": bool(job.get("stage1_complete")),
            "stage2_complete": bool(job.get("stage2_complete")),
            "stage3_complete": bool(job.get("stage3_complete")),
            "pipeline_live": OFFICE_PIPELINE_LIVE,
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
        }

    def _fail_execution(self, job: dict[str, Any], reason: str, detail: str) -> dict[str, Any]:
        job["status"] = "failed"
        job["failure_reason"] = reason
        job["failure_detail"] = detail
        job["stage3_complete"] = False
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def _fail(self, job: dict[str, Any], reason: str, detail: str) -> dict[str, Any]:
        job["status"] = "failed"
        job["failure_reason"] = reason
        job["failure_detail"] = detail
        job["stage1_complete"] = False
        job["stage2_complete"] = False
        job["stage3_complete"] = False
        job["updated_at"] = _utc_now()
        self._write(job)
        return self.public_view(job)

    def _require_owner(self, job_id: str, owner_token: str) -> dict[str, Any]:
        job = self._load(job_id)
        if not job:
            raise OfficeJobError("not_found", "Job nicht gefunden")
        expected = str(job.get("owner_token_hash") or "")
        got = _hash_token(owner_token or "")
        if not expected or not hmac.compare_digest(expected, got):
            raise OfficeJobError("forbidden", "Kein Zugriff auf diesen Job")
        return job

    def _path(self, job_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "", job_id)[:40]
        return self._root / f"{safe}.json"

    def _load(self, job_id: str) -> dict[str, Any] | None:
        return self._load_path(self._path(job_id))

    def _load_path(self, path: Path) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _write(self, job: dict[str, Any]) -> None:
        path = self._path(str(job["job_id"]))
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        self._upsert_index(job)

    def _upsert_index(self, job: dict[str, Any]) -> None:
        row = {
            "job_id": job.get("job_id"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
            "status": job.get("status"),
            "customer_id": job.get("customer_id"),
            "email": job.get("email"),
            "order_id": (job.get("payment") or {}).get("order_id"),
        }
        lines: list[str] = []
        if self._index.is_file():
            try:
                lines = [
                    ln
                    for ln in self._index.read_text(encoding="utf-8").splitlines()
                    if ln.strip()
                    and json.loads(ln).get("job_id") != job.get("job_id")
                ]
            except (json.JSONDecodeError, OSError):
                lines = []
        lines.append(json.dumps(row, ensure_ascii=False))
        self._index.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _append_index(self, row: dict[str, Any]) -> None:
        with self._index.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
