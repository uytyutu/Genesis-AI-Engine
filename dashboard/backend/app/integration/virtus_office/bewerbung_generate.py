"""Generate German Lebenslauf / Bewerbungsschreiben from profile facts only."""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

from app.integration.virtus_office.artifact_writers import (
    artifact_filename,
    write_docx_bytes,
    write_pdf_bytes,
)
from app.integration.virtus_office.bewerbung_profile import normalize_profile
from app.integration.virtus_office.bewerbung_ssot import BEWERBUNG_DISCLAIMER_DE

MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
}


def generate_bewerbung_artifacts(
    *,
    action_id: str,
    profile: dict[str, Any],
    photo_bytes: bytes | None = None,
    output_format: str = "pdf",
) -> dict[str, Any]:
    """Return bytes + QA mirror text. Never invent employers/degrees/skills."""
    p = normalize_profile(profile)
    action = (action_id or "").strip().lower()
    fmt = (output_format or "pdf").lower()
    if action == "bewerbung_paket":
        fmt = "zip"

    if action in {"lebenslauf_create", "lebenslauf_improve"}:
        return _lebenslauf_bundle(p, photo_bytes=photo_bytes, fmt=fmt, improve=(action == "lebenslauf_improve"))
    if action == "bewerbungsschreiben":
        return _anschreiben_bundle(p, fmt=fmt)
    if action == "bewerbung_paket":
        return _paket_bundle(p, photo_bytes=photo_bytes)
    return {
        "ok": False,
        "error": "unsupported_action",
        "detail": f"Unbekannte Bewerbung-Aktion: {action}",
    }


def build_lebenslauf_sections(profile: dict[str, Any]) -> list[tuple[str, list[str]]]:
    p = normalize_profile(profile)
    pers = p["personal"]
    sections: list[tuple[str, list[str]]] = []

    contact_lines = []
    if pers.get("full_name"):
        contact_lines.append(str(pers["full_name"]))
    bits = [pers.get("address"), pers.get("postal_code"), pers.get("city")]
    loc = " ".join(str(b) for b in bits if b).strip()
    if loc:
        contact_lines.append(loc)
    if pers.get("email"):
        contact_lines.append(str(pers["email"]))
    if pers.get("phone"):
        contact_lines.append(str(pers["phone"]))
    if pers.get("birth_date"):
        contact_lines.append(f"Geburtsdatum: {pers['birth_date']}")
    if pers.get("nationality"):
        contact_lines.append(f"Staatsangehörigkeit: {pers['nationality']}")
    sections.append(("Persönliche Daten", contact_lines))

    exp_lines: list[str] = []
    for row in p["experience"]:
        period = _period(row.get("start"), row.get("end"))
        head = " · ".join(
            x for x in (row.get("title"), row.get("employer"), row.get("city")) if x
        )
        if period:
            exp_lines.append(f"{period} — {head}" if head else period)
        elif head:
            exp_lines.append(head)
        for b in row.get("bullets") or []:
            exp_lines.append(f"• {b}")
    if exp_lines:
        sections.append(("Berufserfahrung", exp_lines))

    edu_lines: list[str] = []
    for row in p["education"]:
        period = _period(row.get("start"), row.get("end"))
        head = " · ".join(x for x in (row.get("degree"), row.get("school"), row.get("city")) if x)
        if period:
            edu_lines.append(f"{period} — {head}" if head else period)
        elif head:
            edu_lines.append(head)
    if edu_lines:
        sections.append(("Ausbildung", edu_lines))

    if p["skills"]:
        sections.append(("Kenntnisse", [", ".join(p["skills"])]))

    lang_lines = []
    for row in p["languages"]:
        if row.get("level"):
            lang_lines.append(f"{row['language']}: {row['level']}")
        elif row.get("language"):
            lang_lines.append(str(row["language"]))
    if lang_lines:
        sections.append(("Sprachen", lang_lines))

    if p["drivers_license"]:
        sections.append(("Führerschein", [", ".join(p["drivers_license"])]))

    cert_lines = []
    for row in p["certificates"]:
        bits = [row.get("name"), row.get("issuer"), row.get("year")]
        cert_lines.append(" · ".join(str(b) for b in bits if b))
    if cert_lines:
        sections.append(("Zertifikate", cert_lines))

    sections.append(("Hinweis", [BEWERBUNG_DISCLAIMER_DE]))
    return sections


def build_anschreiben_paragraphs(profile: dict[str, Any]) -> list[str]:
    p = normalize_profile(profile)
    name = p["personal"].get("full_name") or "Bewerber/in"
    vac = p["vacancy"] or {}
    title = vac.get("title") or "die ausgeschriebene Stelle"
    company = vac.get("company") or "Ihr Unternehmen"
    paras: list[str] = [
        f"Sehr geehrte Damen und Herren,",
        (
            f"hiermit bewerbe ich mich, {name}, auf die Position "
            f"„{title}“ bei {company}."
        ),
    ]
    # Only real experience — first 2 jobs as facts
    if p["experience"]:
        facts = []
        for row in p["experience"][:2]:
            bit = " als ".join(x for x in (row.get("title"),) if x)
            emp = row.get("employer")
            if emp and bit:
                facts.append(f"{bit} bei {emp}")
            elif emp:
                facts.append(f"Tätigkeit bei {emp}")
            elif bit:
                facts.append(bit)
        if facts:
            paras.append(
                "In meiner bisherigen Laufbahn habe ich unter anderem Erfahrung gesammelt: "
                + "; ".join(facts)
                + "."
            )
    if p["education"]:
        edu = p["education"][0]
        edu_bits = [edu.get("degree"), edu.get("school")]
        edu_s = " · ".join(str(x) for x in edu_bits if x)
        if edu_s:
            paras.append(f"Meine Ausbildung: {edu_s}.")
    notes = (p.get("motivation_notes") or "").strip()
    if notes:
        paras.append(notes)
    elif (vac.get("text") or "").strip():
        # Reference vacancy without inventing fit claims beyond "Bezug"
        snippet = re.sub(r"\s+", " ", str(vac["text"]))[:280]
        paras.append(f"Bezug zur Stellenanzeige: {snippet}")
    paras.append(
        "Über die Möglichkeit eines persönlichen Gesprächs freue ich mich. "
        "Unterlagen habe ich beigefügt."
    )
    paras.append("Mit freundlichen Grüßen")
    paras.append(str(name))
    paras.append(BEWERBUNG_DISCLAIMER_DE)
    return paras


def _lebenslauf_bundle(
    profile: dict[str, Any],
    *,
    photo_bytes: bytes | None,
    fmt: str,
    improve: bool,
) -> dict[str, Any]:
    sections = build_lebenslauf_sections(profile)
    title = "Lebenslauf"
    if improve:
        title = "Lebenslauf (überarbeitet)"
    name = (profile.get("personal") or {}).get("full_name") or "Lebenslauf"
    mirror = _sections_to_text(title, sections)
    paragraphs = _sections_to_paragraphs(sections)
    meta = [
        f"Kandidat/in: {name}",
        "Quelle: nur vom Nutzer bereitgestellte Angaben",
        BEWERBUNG_DISCLAIMER_DE,
    ]
    if fmt == "docx":
        blob = write_docx_bytes(title=title, paragraphs=paragraphs, headings=meta)
        ext = "docx"
    else:
        blob = write_lebenslauf_pdf(
            title=title,
            sections=sections,
            meta_lines=meta,
            photo_bytes=photo_bytes,
        )
        ext = "pdf"
    return {
        "ok": True,
        "action_id": "lebenslauf_improve" if improve else "lebenslauf_create",
        "ext": ext,
        "mime": MIME[ext],
        "filename": artifact_filename(f"Lebenslauf_{_safe(name)}", ext),
        "bytes": blob,
        "quality_input_text": mirror,
        "quality_output_text": mirror,
        "photo_placed": bool(photo_bytes) and ext == "pdf",
        "entities": _profile_entities(profile),
    }


def _anschreiben_bundle(profile: dict[str, Any], *, fmt: str) -> dict[str, Any]:
    paras = build_anschreiben_paragraphs(profile)
    title = "Bewerbungsschreiben"
    name = (profile.get("personal") or {}).get("full_name") or "Bewerbung"
    mirror = "\n\n".join([title, *paras])
    meta = [BEWERBUNG_DISCLAIMER_DE]
    if fmt == "docx":
        blob = write_docx_bytes(title=title, paragraphs=paras, headings=meta)
        ext = "docx"
    else:
        blob = write_pdf_bytes(title=title, paragraphs=paras, meta_lines=meta)
        ext = "pdf"
    return {
        "ok": True,
        "action_id": "bewerbungsschreiben",
        "ext": ext,
        "mime": MIME[ext],
        "filename": artifact_filename(f"Anschreiben_{_safe(name)}", ext),
        "bytes": blob,
        "quality_input_text": mirror,
        "quality_output_text": mirror,
        "photo_placed": False,
        "entities": _profile_entities(profile),
    }


def _paket_bundle(profile: dict[str, Any], *, photo_bytes: bytes | None) -> dict[str, Any]:
    cv_pdf = _lebenslauf_bundle(profile, photo_bytes=photo_bytes, fmt="pdf", improve=False)
    cv_docx = _lebenslauf_bundle(profile, photo_bytes=None, fmt="docx", improve=False)
    an_pdf = _anschreiben_bundle(profile, fmt="pdf")
    an_docx = _anschreiben_bundle(profile, fmt="docx")
    if not all(x.get("ok") for x in (cv_pdf, cv_docx, an_pdf, an_docx)):
        return {"ok": False, "error": "paket_failed", "detail": "Paket-Erzeugung fehlgeschlagen"}

    anlagen = (profile.get("anlagen_notes") or "").strip()
    anlagen_txt = (
        "Anlagen\n\n"
        + (anlagen if anlagen else "Lebenslauf, Bewerbungsschreiben")
        + "\n\n"
        + BEWERBUNG_DISCLAIMER_DE
    ).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(cv_pdf["filename"], cv_pdf["bytes"])
        zf.writestr(cv_docx["filename"], cv_docx["bytes"])
        zf.writestr(an_pdf["filename"], an_pdf["bytes"])
        zf.writestr(an_docx["filename"], an_docx["bytes"])
        zf.writestr("Anlagen.txt", anlagen_txt)
    name = (profile.get("personal") or {}).get("full_name") or "Bewerbung"
    mirror = "\n\n".join(
        [
            cv_pdf["quality_output_text"],
            an_pdf["quality_output_text"],
            anlagen_txt.decode("utf-8"),
        ]
    )
    return {
        "ok": True,
        "action_id": "bewerbung_paket",
        "ext": "zip",
        "mime": MIME["zip"],
        "filename": artifact_filename(f"Bewerbung_Paket_{_safe(name)}", "zip"),
        "bytes": buf.getvalue(),
        "quality_input_text": mirror,
        "quality_output_text": mirror,
        "photo_placed": bool(photo_bytes),
        "entities": _profile_entities(profile),
    }


def write_lebenslauf_pdf(
    *,
    title: str,
    sections: list[tuple[str, list[str]]],
    meta_lines: list[str] | None = None,
    photo_bytes: bytes | None = None,
) -> bytes:
    from fpdf import FPDF

    from app.integration.virtus_office.artifact_writers import _pdf_safe

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    # Photo top-right if provided
    photo_placed = False
    if photo_bytes:
        try:
            import tempfile
            from pathlib import Path as _P

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(photo_bytes)
                tmp_path = tmp.name
            try:
                pdf.image(tmp_path, x=pdf.w - pdf.r_margin - 32, y=pdf.t_margin, w=30)
                photo_placed = True
            finally:
                try:
                    _P(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception:
            photo_placed = False

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw - (34 if photo_placed else 0), 9, _pdf_safe(title))
    pdf.ln(2)
    if meta_lines:
        pdf.set_font("Helvetica", "", 8)
        for line in meta_lines:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw - (34 if photo_placed else 0), 4, _pdf_safe(line))
        pdf.ln(2)
    if photo_placed:
        pdf.set_y(max(pdf.get_y(), pdf.t_margin + 36))

    for heading, lines in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 7, _pdf_safe(heading))
        pdf.set_font("Helvetica", "", 10)
        for ln in lines:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, _pdf_safe(ln))
        pdf.ln(2)

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("latin-1", errors="replace")


def _sections_to_paragraphs(sections: list[tuple[str, list[str]]]) -> list[str]:
    out: list[str] = []
    for heading, lines in sections:
        out.append(heading)
        out.extend(lines)
        out.append("")
    return out


def _sections_to_text(title: str, sections: list[tuple[str, list[str]]]) -> str:
    parts = [title]
    for heading, lines in sections:
        parts.append(heading)
        parts.extend(lines)
        parts.append("")
    return "\n".join(parts)


def _period(start: Any, end: Any) -> str:
    s = (str(start).strip() if start else "")
    e = (str(end).strip() if end else "")
    if s and e:
        return f"{s} – {e}"
    return s or e


def _safe(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name.strip())[:40] or "Dokument"


def _profile_entities(profile: dict[str, Any]) -> list[str]:
    p = normalize_profile(profile)
    ents: list[str] = []
    for key in ("email", "phone", "full_name"):
        if p["personal"].get(key):
            ents.append(str(p["personal"][key]))
    for row in p["experience"]:
        for k in ("employer", "title", "start", "end"):
            if row.get(k):
                ents.append(str(row[k]))
    for row in p["education"]:
        for k in ("school", "degree", "start", "end"):
            if row.get(k):
                ents.append(str(row[k]))
    return list(dict.fromkeys(ents))
