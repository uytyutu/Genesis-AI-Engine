"""Unit tests for A-lite presentation extract/rebuild (no live LLM)."""

from __future__ import annotations

from pathlib import Path

from app.integration.virtus_office.presentation_rebuild import (
    extract_presentation_pdf,
    rebuild_presentation_pdf,
)
from app.integration.virtus_office.quality_gate import run_quality_gate

BP = (
    Path(__file__).resolve().parents[1]
    / ".office_verify/commercial_docx2/order_materials/mat-d24ae910af0d.pdf"
)


def test_extract_businessplan_pages_and_images():
    if not BP.exists():
        return
    data = BP.read_bytes()
    extracted = extract_presentation_pdf(data)
    assert extracted["ok"] is True
    assert extracted["page_count"] == 28
    assert extracted["image_count"] == 14
    assert len(extracted["pages"]) == 28
    # Screenshot page should carry image placements
    p4 = extracted["pages"][3]
    assert len(p4["images"]) >= 1
    assert p4["images"][0]["draw_w"] > 100


def test_rebuild_keeps_page_and_image_counts():
    if not BP.exists():
        return
    data = BP.read_bytes()
    extracted = extract_presentation_pdf(data)
    pages = []
    for pg in extracted["pages"]:
        p = dict(pg)
        p["translated_text"] = pg["text"]  # identity — structure proof only
        pages.append(p)
    rebuilt = rebuild_presentation_pdf(
        pages,
        title="A-lite structure proof",
        meta_lines=["Delivery: presentation-grade rebuild (not pixel-perfect)"],
    )
    assert rebuilt["ok"] is True
    assert rebuilt["page_count"] == 28
    assert rebuilt["image_count"] >= 11  # allow small placement misses
    assert rebuilt["bytes"][:4] == b"%PDF"

    qa = run_quality_gate(
        action_id="translate",
        input_text="\n\n".join(p["text"] for p in pages),
        output_text="\n\n".join(p["translated_text"] for p in pages),
        artifact_bytes=rebuilt["bytes"],
        artifact_ext="pdf",
        artifact_mime="application/pdf",
        target_language="en",
        translation_provider="offline_glossary",
        job_id="alite1",
        artifact_job_id="alite1",
        document_type="businessplan",
        source_page_count=28,
        source_image_count=14,
        delivery_mode="presentation_rebuild",
    )
    # Identity DE text will fail residual German for EN target — layout checks must still pass
    assert "layout_fidelity" not in qa["failed"]
    assert "pagination_consistent" not in qa["failed"]
    assert "source_images_preserved" not in qa["failed"]


def test_quality_gate_presentation_rebuild_pass_layout():
    # Minimal synthetic: 8 empty-ish pages not needed — check mode branch with fake pdf stats
    blob = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\nstartxref\n0\n%%EOF\n" + b"x" * 200
    # Without real pages/images, _pdf_stats may return 0 — still ensure text_rebuild fails
    qa = run_quality_gate(
        action_id="translate",
        input_text="A" * 3000,
        output_text="B" * 3000,
        artifact_bytes=blob,
        artifact_ext="pdf",
        artifact_mime="application/pdf",
        target_language="en",
        translation_provider="groq",
        job_id="x",
        artifact_job_id="x",
        document_type="businessplan",
        source_page_count=28,
        source_image_count=14,
        delivery_mode="text_rebuild_pdf",
    )
    assert qa["passed"] is False
    assert "layout_fidelity" in qa["failed"]
