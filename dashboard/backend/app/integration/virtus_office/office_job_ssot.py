"""Virtus Office Job Engine — product SSOT (honesty gate).

Commercial line separate from B2B (Receptionist / Automation / Vector).
Do not advertise automated pay→file delivery until OFFICE_PIPELINE_LIVE.

Target UX (client-facing, not chat):
  UPLOAD → UNDERSTAND → INTENT → PROPOSAL+PRICE → PAY → EXECUTE
  → QUALITY GATE → ARTIFACT → SECURE DOWNLOAD

Virtus Product Rule (binding):
  Virtus sells a reproducible deliverable the system can automatically verify —
  not an explanation, not a referral to a notary/translator/lawyer, not a
  state-issued certificate.

  No executor  → No SKU.
  No validator → No high-risk SKU (e.g. XRechnung / PDF/A).
  No PASS      → No delivery.

Sellable today (code paths only): translate, convert_docx, extract_data,
document_quality_check, Lebenslauf/Bewerbung. OCR is ingest, not a catalog SKU.
Forbidden on vitrine: Official / Legal / notarized / apostille / medical /
tax advice / legal advice theatre.

Roadmap (scaffold contracts only — SKU_ENABLED=False until executor+validator PASS):
XRechnung → ZUGFeRD → searchable PDF → fillable PDF → PDF/A-2b → Archive → PDF/UA.
Country price multipliers only after ≥2 new SELLABLE SKUs beyond baseline.
Capability truth: office_capability_audit.audit_matrix() — never invent SELLABLE.

Stage 1 (live in code, pipeline_live still False):
  UPLOAD → JOB CREATED → INGEST → UNDERSTANDING READY (stub contract)
"""

from __future__ import annotations

from typing import Any, Literal

# Owner soft-beta flip 2026-09-05 — pay→execute→deliver enabled for SELLABLE SKUs.
# Stripe live mode is env-derived (sk_live_); see office_stripe_live().
OFFICE_PIPELINE_LIVE = True


def office_stripe_live() -> bool:
    """True when checkout secret resolves to sk_live_ (real charges)."""
    try:
        from app.integration.payment_checkout_service import PaymentCheckoutService

        return bool(PaymentCheckoutService().is_live_mode())
    except Exception:  # noqa: BLE001
        return False

# Catalog honesty — must match understanding.CUSTOMER_EXECUTABLE_ACTIONS sellables.
OFFICE_SELLABLE_NOW: tuple[str, ...] = (
    "translate",
    "convert_docx",
    "extract_data",
    "document_quality_check",
    "lebenslauf_create",
    "lebenslauf_improve",
    "bewerbungsschreiben",
    "bewerbung_paket",
)

OFFICE_VITRINE_FORBIDDEN: tuple[str, ...] = (
    "official",
    "legal",
    "notary",
    "apostille",
    "beglaubigung",
    "fuehrungszeugnis",
    "medical",
    "steuerberatung",
    "rechtsberatung",
)

OFFICE_SKU_ROADMAP: tuple[str, ...] = (
    "xrechnung",
    "zugferd",
    "searchable_pdf",
    "fillable_pdf",
    "pdf_a_2b",
    "document_archive",
    "pdf_ua",
)

OfficeJobStatus = Literal[
    "created",
    "uploading",
    "ingested",
    "understanding",
    "proposal_ready",
    "awaiting_payment",
    "paid",
    "executing",
    "quality_check",
    "completed",
    "failed",
    "cancelled",
]

OFFICE_JOB_STATUSES: tuple[str, ...] = (
    "created",
    "uploading",
    "ingested",
    "understanding",
    "proposal_ready",
    "awaiting_payment",
    "paid",
    "executing",
    "quality_check",
    "completed",
    "failed",
    "cancelled",
)

# Stage 1 success after ingest (before Stage 2 fill). Stage 2 ends at proposal_ready.
STAGE1_SUCCESS_STATUS: OfficeJobStatus = "understanding"
STAGE2_SUCCESS_STATUS: OfficeJobStatus = "proposal_ready"

OFFICE_PRICE_MATRIX_EUR: dict[str, float] = {
    "simple_op": 4.90,
    "doc_quality": 7.90,
    "translate": 7.90,
    "document": 9.90,
    "cv_bewerbung": 14.90,
    "excel_calc": 14.90,
    "doc_analysis": 14.90,
    "large_pack": 24.90,
    "complex_from": 39.90,
}

# Product input formats (stricter than Path A order_materials allow-list).
OFFICE_ALLOWED_EXT: frozenset[str] = frozenset(
    {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".xlsx", ".csv", ".txt"}
)

OFFICE_EXT_TO_KIND: dict[str, str] = {
    ".pdf": "pdf",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".csv": "csv",
    ".txt": "txt",
}

OFFICE_KIND_MIMES: dict[str, frozenset[str]] = {
    "pdf": frozenset({"application/pdf"}),
    "image": frozenset({"image/jpeg", "image/jpg", "image/png"}),
    "docx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        }
    ),
    "xlsx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        }
    ),
    "csv": frozenset({"text/csv", "application/csv", "text/plain"}),
    "txt": frozenset({"text/plain"}),
}

# Generic MIME from browsers — allow when extension is trusted.
OFFICE_GENERIC_MIME: frozenset[str] = frozenset(
    {"", "application/octet-stream", "binary/octet-stream"}
)


def office_pipeline_stages() -> list[dict[str, str]]:
    return [
        {"id": "ingest", "label": "INGEST"},
        {"id": "ocr_parse", "label": "OCR / PARSER"},
        {"id": "classify", "label": "DOCUMENT CLASSIFIER"},
        {"id": "intent", "label": "INTENT ENGINE"},
        {"id": "plan", "label": "TASK PLANNER"},
        {"id": "execute", "label": "EXECUTION"},
        {"id": "generate", "label": "OUTPUT GENERATOR"},
        {"id": "quality", "label": "QUALITY GATE"},
        {"id": "second_check", "label": "SECOND CHECK"},
        {"id": "deliver", "label": "DELIVERY"},
    ]


def empty_understanding_contract() -> dict[str, Any]:
    """Stage 2 fills this — Stage 1 only installs the shape."""
    return {
        "filled": False,
        "stage": "awaiting_stage2",
        "document_type": None,
        "language": None,
        "page_count": None,
        "confidence": None,
        "suggested_intent": None,
        "suggested_output_format": None,
        "suggested_price_eur": None,
        "needs_user_choice": None,
        "choice_options": None,
        "summary_de": None,
    }


def empty_proposal_contract() -> dict[str, Any]:
    """Stage 2+ — structured proposal shown instead of chat."""
    return {
        "filled": False,
        "title_de": None,
        "detected": {
            "document_type": None,
            "language": None,
            "pages": None,
        },
        "task": None,
        "result_format": None,
        "price_eur": None,
        "includes": [],
        "low_confidence": False,
        "choice_options": [],
    }


def office_reuse_map() -> dict[str, Any]:
    """What exists in Virtus Core today vs Office gaps."""
    return {
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "stage1_job_lifecycle": True,
        "stage2_understanding_proposal": True,
        "stage3_execution_quality": True,
        "stage4_ocr_document_engine": True,
        "stage5_bewerbung_office": True,
        "reuse": [
            {
                "id": "public_vitrine",
                "path": "/site · /office",
                "status": "ship_storefront",
                "note": "Separate Office section; do not mix into B2B cards",
            },
            {
                "id": "service_order",
                "path": "/order/service/[serviceId] · sales_order_service",
                "status": "ready_shell",
                "note": "Micro-SKU checkout shell exists; do not take money until deliverable",
            },
            {
                "id": "order_materials",
                "path": "order_materials_service",
                "status": "reused_for_office_ingest",
                "note": "Office Job Engine stores bytes only via OrderMaterialsService",
            },
            {
                "id": "office_bewerbung",
                "path": "virtus_office/bewerbung_*",
                "status": "stage5+cc4",
                "note": "Lebenslauf/Anschreiben/Paket — no invented facts; checkout → QA → delivery",
            },
            {
                "id": "digital_product_delivery",
                "path": "virtus_office/digital_product_delivery · receipt_email_service",
                "status": "cc4",
                "note": "Cabinet + secure email link + receipt path; email fail ≠ drop COMPLETED",
            },
            {
                "id": "office_job_engine",
                "path": "virtus_office/job_engine",
                "status": "stage5_bewerbung",
                "note": "OCR + Bewerbung + CC-2–CC-4 delivery; OFFICE_PIPELINE_LIVE=True (owner soft-beta 2026-09-05)",
            },
            {
                "id": "office_payment_bridge",
                "path": "virtus_office/payment_bridge → sales_order + revenue_pipeline",
                "status": "cc2",
                "note": "Proposal → lock → Core Order → Checkout → webhook → PAYMENT_CONFIRMED → execute unlock",
            },
            {
                "id": "office_post_pay_cabinet",
                "path": "virtus_office/post_pay + /office/cabinet + Client Workspace bearer",
                "status": "cc3",
                "note": "Progress UI, secure artifact, Meine Aufträge/Dateien/Rechnungen/Downloads",
            },
            {
                "id": "office_ocr_engine",
                "path": "virtus_office/ocr_engine",
                "status": "stage4",
                "note": "Tesseract / Vision LLM cascade; PDF raster via pypdfium2; multi-image pages",
            },
            {
                "id": "knowledge_intake_pdf",
                "path": "knowledge_intake_pdf.extract_pdf_text_bytes",
                "status": "reused",
                "note": "PDF text layer via existing intake helper; empty layer → OCR",
            },
            {
                "id": "client_download",
                "path": "sales_order_service.build_client_download",
                "status": "website_zip_oriented",
                "note": "Secure download for website packages; Office needs job-artifact download",
            },
            {
                "id": "attachment_policy",
                "path": "attachment_policy · knowledge_intake_pdf",
                "status": "chat_intake",
                "note": "Parse kinds for Vector chat — not Office Job UX",
            },
            {
                "id": "media_qa",
                "path": "provider_gateway/media_qa",
                "status": "image_only",
                "note": "Pattern for hard QA gate; Office needs number/date/name QA",
            },
            {
                "id": "vector",
                "path": "integration/vector",
                "status": "internal_brain",
                "note": "May power Office Agent internally — client must never see chat UX",
            },
        ],
        "missing": [
            "excel_ocr_expense_pipeline (catalog Stage 6)",
            "preview_before_pay (partial artifact)",
            "micro Stripe SKUs live only after gate",
        ],
        "dod_before_ads": [
            "text_pdf",
            "scan_pdf",
            "photo_ok",
            "photo_bad",
            "multipage_pdf",
            "docx",
            "xlsx",
            "mixed",
            "de_to_ru",
            "ru_to_de",
            "tables",
            "dates",
            "currency",
            "document_numbers",
            "corrupt_empty",
            "bad_user_request",
            "cross_tenant_download_denied",
            "reupload",
            "repay",
            "cancel",
            "generation_fail_honest",
        ],
    }
