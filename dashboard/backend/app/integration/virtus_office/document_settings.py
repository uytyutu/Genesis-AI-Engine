"""Dokument anpassen — structured document settings (not free-form ChatGPT).

Settings are contextual by action + document type.
Special wishes are parsed into concrete ops; never invent values.
Ops are marked executable_now vs instruction (honest).
"""

from __future__ import annotations

import re
from typing import Any

# Setting field definitions: id → meta
_FIELD = dict[str, Any]

TRANSLATE_FIELDS: tuple[_FIELD, ...] = (
    {"id": "source_language", "kind": "language", "group": "translate"},
    {"id": "target_language", "kind": "language", "group": "translate", "required": True},
    {"id": "output_format", "kind": "format", "group": "output", "options": ["pdf", "docx"]},
    {"id": "scope", "kind": "enum", "group": "translate", "options": ["full", "pages"]},
    {"id": "page_range", "kind": "text", "group": "translate", "when": {"scope": "pages"}},
    {"id": "translate_tables", "kind": "bool", "group": "translate", "default": True},
    {"id": "translate_headings", "kind": "bool", "group": "translate", "default": True},
    {"id": "preserve_names", "kind": "bool", "group": "preserve", "default": True},
    {"id": "preserve_numbers_dates", "kind": "bool", "group": "preserve", "default": True},
    {"id": "preserve_structure", "kind": "bool", "group": "output", "default": True},
)

BUSINESSPLAN_FIELDS: tuple[_FIELD, ...] = (
    {"id": "change_date", "kind": "replace", "group": "identity", "fact": "document_date"},
    {"id": "change_company", "kind": "replace", "group": "identity", "fact": "brand"},
    {"id": "change_location", "kind": "replace", "group": "identity", "fact": "location"},
    {"id": "change_legal_form", "kind": "replace", "group": "identity", "fact": "legal_form"},
    {"id": "keep_section", "kind": "section_multi", "group": "structure"},
    {"id": "remove_section", "kind": "section_multi", "group": "structure"},
    {"id": "translate_finance_fully", "kind": "bool", "group": "structure", "default": True},
)

INVOICE_FIELDS: tuple[_FIELD, ...] = (
    {"id": "change_invoice_date", "kind": "replace", "group": "invoice", "fact": "date"},
    {"id": "change_invoice_number", "kind": "replace", "group": "invoice", "fact": "invoice_number"},
    {"id": "recalc_vat_note", "kind": "notice", "group": "invoice"},
)

CV_FIELDS: tuple[_FIELD, ...] = (
    {"id": "target_market", "kind": "text", "group": "cv"},
    {"id": "cv_style", "kind": "enum", "group": "cv", "options": ["classic", "modern", "compact"]},
)

EXTRACT_FIELDS: tuple[_FIELD, ...] = (
    {"id": "output_format", "kind": "format", "group": "output", "options": ["xlsx", "csv"]},
    {"id": "scope", "kind": "enum", "group": "extract", "options": ["full", "pages"], "default": "full"},
    {"id": "page_range", "kind": "text", "group": "extract", "when": {"scope": "pages"}},
    {"id": "include_tables", "kind": "bool", "group": "extract", "default": True},
    {"id": "preserve_numbers_dates", "kind": "bool", "group": "preserve", "default": True},
    {"id": "preserve_names", "kind": "bool", "group": "preserve", "default": True},
)

CONVERT_FIELDS: tuple[_FIELD, ...] = (
    {"id": "output_format", "kind": "format", "group": "output", "options": ["docx", "pdf"]},
    {"id": "scope", "kind": "enum", "group": "output", "options": ["full", "pages"], "default": "full"},
    {"id": "page_range", "kind": "text", "group": "output", "when": {"scope": "pages"}},
    {"id": "preserve_structure", "kind": "bool", "group": "output", "default": True},
    {"id": "preserve_names", "kind": "bool", "group": "preserve", "default": True},
    {"id": "preserve_numbers_dates", "kind": "bool", "group": "preserve", "default": True},
)

# Minimal settings when action has no rich catalog — still a confirmable step before pay.
GENERIC_FIELDS: tuple[_FIELD, ...] = (
    {"id": "output_format", "kind": "format", "group": "output", "options": ["pdf", "docx"]},
    {"id": "preserve_structure", "kind": "bool", "group": "output", "default": True},
)

# Ops the current Stage-3 executors can apply as text transforms before/during work
EXECUTABLE_NOW = frozenset(
    {
        "set_source_language",
        "set_target_language",
        "set_output_format",
        "replace_text",
        "preserve_names",
        "preserve_numbers_dates",
        "translate_tables",
        "translate_headings",
        "preserve_structure",
        "scope_full",
        # page_range / remove_section = instruction until full layout editor exists
    }
)


def settings_catalog(
    *,
    action_id: str,
    document_type: str | None,
) -> list[dict[str, Any]]:
    """Return customer-facing field list for Dokument anpassen."""
    fields: list[dict[str, Any]] = []
    aid = (action_id or "").strip().lower()
    dtype = (document_type or "").strip().lower()

    if aid == "document_quality_check":
        # Diagnostic SKU only — no identity / section rewrite fields.
        return [
            {
                "id": "output_format",
                "kind": "format",
                "group": "output",
                "options": ["pdf", "json"],
                "default": "pdf",
            }
        ]

    if aid == "translate":
        fields.extend(dict(f) for f in TRANSLATE_FIELDS)
    elif aid == "extract_data":
        fields.extend(dict(f) for f in EXTRACT_FIELDS)
    elif aid == "convert_docx":
        fields.extend(dict(f) for f in CONVERT_FIELDS)
    elif aid in {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }:
        # Profile flow owns identity; document settings stay light.
        fields.extend(dict(f) for f in GENERIC_FIELDS)
    else:
        fields.extend(dict(f) for f in GENERIC_FIELDS)

    if dtype == "businessplan":
        fields.extend(dict(f) for f in BUSINESSPLAN_FIELDS)
    elif dtype == "invoice":
        fields.extend(dict(f) for f in INVOICE_FIELDS)
    elif dtype in {"cv_lebenslauf", "cover_letter"}:
        fields.extend(dict(f) for f in CV_FIELDS)

    # Deduplicate by id (output_format may appear twice)
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for f in fields:
        fid = str(f.get("id") or "")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        out.append(f)
    return out


def _fact_value(explanation: dict[str, Any] | None, fact_id: str) -> str | None:
    if not explanation:
        return None
    for row in explanation.get("key_facts") or []:
        if isinstance(row, dict) and row.get("id") == fact_id and row.get("value"):
            return str(row["value"]).strip()
    for row in explanation.get("findings") or []:
        if isinstance(row, dict) and row.get("id") == fact_id and row.get("value"):
            return str(row["value"]).strip()
    return None


def parse_special_wishes(
    text: str,
    *,
    explanation: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Heuristic parse of free-text wishes → concrete ops. No invention."""
    raw = (text or "").strip()
    if not raw:
        return []
    ops: list[dict[str, Any]] = []
    lower = raw.lower()

    # Date change: ... auf/to/на DD.MM.YYYY
    m = re.search(
        r"(?:datum|dokumentstand|date)[^\d]{0,40}?(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
        raw,
        re.I,
    )
    m2 = re.search(
        r"(?:auf|to|на|→|->)\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
        raw,
        re.I,
    )
    new_date = (m2.group(1) if m2 else None) or (m.group(1) if m else None)
    if new_date and re.search(r"(datum|dokumentstand|date|ändern|aender|change|измени)", lower):
        old = _fact_value(explanation, "document_date") or _fact_value(explanation, "date")
        ops.append(
            {
                "id": "replace_text",
                "label_key": "change_date",
                "from": old,
                "to": new_date,
                "executable_now": bool(old),
                "status": "ok" if old else "needs_from_value",
            }
        )

    # Keep company / brand unchanged
    if re.search(
        r"(name|firma|unternehmen|company|firmenname|название).{0,50}"
        r"(ohne|unchanged|nicht\s+veränder|nicht\s+veraender|nicht\s+ändern|nicht\s+aender|"
        r"behalten|оставь|без изменен|не менят)",
        lower,
    ) or re.search(
        r"(firmennamen|personennamen|namen|brands?).{0,40}"
        r"(nicht\s+veränder|nicht\s+veraender|nicht\s+ändern|nicht\s+aender|behalten|preserve|keep)",
        lower,
    ):
        brand = _fact_value(explanation, "brand")
        ops.append(
            {
                "id": "keep_value",
                "label_key": "keep_company",
                "value": brand,
                "executable_now": True,
                "status": "ok",
            }
        )
        ops.append(
            {
                "id": "preserve_names",
                "label_key": "preserve_names",
                "to": True,
                "executable_now": True,
                "status": "ok",
            }
        )

    # Target / source language from wish text
    lang_map = {
        "deutsch": "de",
        "german": "de",
        "englisch": "en",
        "english": "en",
        "украин": "uk",
        "ukrainisch": "uk",
        "ukrainian": "uk",
        "русск": "ru",
        "russisch": "ru",
        "russian": "ru",
        "franzo": "fr",
        "französ": "fr",
        "french": "fr",
        "polnisch": "pl",
        "polish": "pl",
    }
    tgt_m = re.search(
        r"(?:nach|to|ins|in|на|→|->)\s*"
        r"(deutsch|german|englisch|english|ukrainisch|ukrainian|russisch|russian|"
        r"französisch|franzoesisch|french|polnisch|polish)",
        lower,
    )
    src_m = re.search(
        r"(?:von|from|из|aus)\s*"
        r"(deutsch|german|englisch|english|ukrainisch|ukrainian|russisch|russian|"
        r"französisch|franzoesisch|french|polnisch|polish)",
        lower,
    )
    if tgt_m:
        code = next((v for k, v in lang_map.items() if k in tgt_m.group(1)), None)
        if code:
            ops.append(
                {
                    "id": "set_target_language",
                    "label_key": "set_target_language",
                    "to": code,
                    "executable_now": True,
                    "status": "ok",
                }
            )
    if src_m:
        code = next((v for k, v in lang_map.items() if k in src_m.group(1)), None)
        if code:
            ops.append(
                {
                    "id": "set_source_language",
                    "label_key": "set_source_language",
                    "to": code,
                    "executable_now": True,
                    "status": "ok",
                }
            )

    # Full-document translate scope
    if re.search(
        r"(vollst[aä]ndig|vollständig|complete|full|весь|полностью).{0,40}"
        r"(businessplan|dokument|document|übersetz|uebersetz|transl|перев)",
        lower,
    ) or re.search(
        r"(übersetz|uebersetz|transl|перев).{0,40}"
        r"(vollst[aä]ndig|vollständig|complete|full|весь|полностью)",
        lower,
    ):
        ops.append(
            {
                "id": "scope_full",
                "label_key": "scope_full",
                "executable_now": True,
                "status": "ok",
            }
        )

    if re.search(r"swot.{0,30}(nicht|nicht lösch|behalten|keep|сохра|не удал)", lower) or re.search(
        r"(behalten|keep|сохра).{0,20}swot", lower
    ):
        ops.append(
            {
                "id": "keep_section",
                "label_key": "keep_swot",
                "section": "swot",
                "executable_now": False,
                "status": "instruction",
            }
        )

    if re.search(r"(finanz|finance).{0,40}(vollständig|vollstaendig|fully|полностью|translate)", lower) or re.search(
        r"(übersetz|uebersetz|transl|перев).{0,40}(finanz|finance)", lower
    ):
        ops.append(
            {
                "id": "translate_section_fully",
                "label_key": "translate_finance_fully",
                "section": "finance",
                "executable_now": False,
                "status": "instruction",
            }
        )

    if not ops:
        ops.append(
            {
                "id": "free_instruction",
                "label_key": "free_instruction",
                "text": raw[:500],
                "executable_now": False,
                "status": "instruction",
            }
        )
    return ops


def build_document_settings(
    *,
    action_id: str,
    document_type: str | None,
    explanation: dict[str, Any] | None,
    values: dict[str, Any] | None,
    special_wishes: str | None,
    sections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Merge form values + special wishes into confirmed ops + preview."""
    catalog = settings_catalog(action_id=action_id, document_type=document_type)
    vals = dict(values or {})
    ops: list[dict[str, Any]] = []
    preview: list[dict[str, Any]] = []

    # Core translate / format
    if vals.get("source_language"):
        ops.append(
            {
                "id": "set_source_language",
                "to": vals["source_language"],
                "executable_now": True,
                "status": "ok",
            }
        )
    if vals.get("target_language"):
        ops.append(
            {
                "id": "set_target_language",
                "to": vals["target_language"],
                "executable_now": True,
                "status": "ok",
            }
        )
    if vals.get("output_format"):
        ops.append(
            {
                "id": "set_output_format",
                "to": vals["output_format"],
                "executable_now": True,
                "status": "ok",
            }
        )

    for bool_id in (
        "translate_tables",
        "translate_headings",
        "preserve_names",
        "preserve_numbers_dates",
        "preserve_structure",
        "translate_finance_fully",
    ):
        if bool_id in vals:
            ops.append(
                {
                    "id": bool_id,
                    "to": bool(vals[bool_id]),
                    "executable_now": bool_id in EXECUTABLE_NOW or bool_id.startswith("preserve") or bool_id.startswith("translate_"),
                    "status": "ok",
                }
            )

    if vals.get("scope") == "pages" and vals.get("page_range"):
        ops.append(
            {
                "id": "page_range",
                "to": str(vals["page_range"]),
                "executable_now": False,
                "status": "instruction",
            }
        )
    elif vals.get("scope") == "full":
        ops.append({"id": "scope_full", "executable_now": True, "status": "ok"})

    # Replace fields driven by facts
    for field in catalog:
        if field.get("kind") != "replace":
            continue
        fid = field["id"]
        new_val = vals.get(fid) or vals.get(f"{fid}_to")
        if not new_val:
            continue
        fact = str(field.get("fact") or "")
        old = _fact_value(explanation, fact)
        op = {
            "id": "replace_text",
            "label_key": fid,
            "from": old,
            "to": str(new_val).strip(),
            "executable_now": bool(old),
            "status": "ok" if old else "needs_from_value",
        }
        ops.append(op)
        if old:
            preview.append({"before": f"{fact or fid}: {old}", "after": f"{fact or fid}: {new_val}"})
        else:
            preview.append(
                {
                    "before": f"{fact or fid}: —",
                    "after": f"{fact or fid}: {new_val}",
                    "note": "from_value_not_found",
                }
            )

    # Sections
    keep = vals.get("keep_section") or []
    remove = vals.get("remove_section") or []
    if isinstance(keep, str):
        keep = [keep]
    if isinstance(remove, str):
        remove = [remove]
    for sid in keep:
        ops.append(
            {
                "id": "keep_section",
                "section": sid,
                "executable_now": False,
                "status": "instruction",
            }
        )
    for sid in remove:
        ops.append(
            {
                "id": "remove_section",
                "section": sid,
                "executable_now": False,
                "status": "instruction",
            }
        )
        preview.append({"before": f"section:{sid}", "after": "removed", "note": "instruction"})

    # Special wishes
    wish_ops = parse_special_wishes(special_wishes or "", explanation=explanation)
    for w in wish_ops:
        ops.append(w)
        if w.get("id") == "replace_text" and w.get("from") and w.get("to"):
            preview.append({"before": str(w["from"]), "after": str(w["to"])})
        elif w.get("id") == "set_target_language" and w.get("to"):
            vals.setdefault("target_language", w["to"])
            preview.append(
                {
                    "before": f"target_language: {vals.get('source_language') or 'auto'}",
                    "after": f"target_language: {w['to']}",
                }
            )
        elif w.get("id") == "set_source_language" and w.get("to"):
            vals.setdefault("source_language", w["to"])
        elif w.get("id") == "preserve_names":
            vals["preserve_names"] = True
            preview.append(
                {
                    "before": "names/brands: may translate",
                    "after": "names/brands: preserve",
                }
            )
        elif w.get("id") == "scope_full":
            vals["scope"] = "full"
            preview.append({"before": "scope: ?", "after": "scope: full document"})
        elif w.get("id") == "keep_value":
            preview.append(
                {
                    "before": f"company: {w.get('value') or '—'}",
                    "after": "company: unchanged",
                }
            )

    section_ids = [s.get("id") for s in (sections or []) if isinstance(s, dict) and s.get("id")]

    return {
        "filled": True,
        "action_id": action_id,
        "document_type": document_type,
        "catalog": catalog,
        "values": vals,
        "special_wishes": (special_wishes or "").strip() or None,
        "ops": ops,
        "preview": preview[:12],
        "available_sections": section_ids,
        "confirmed": False,
        "executable_now_count": sum(1 for o in ops if o.get("executable_now")),
        "instruction_count": sum(1 for o in ops if not o.get("executable_now")),
        "honesty": "Preview shows planned changes only. Full document after payment.",
    }


def apply_text_replacements(text: str, settings: dict[str, Any] | None) -> str:
    """Apply only executable replace_text ops with known from→to."""
    if not text or not settings:
        return text
    out = text
    for op in settings.get("ops") or []:
        if not isinstance(op, dict):
            continue
        if op.get("id") != "replace_text" or not op.get("executable_now"):
            continue
        frm = op.get("from")
        to = op.get("to")
        if frm and to and str(frm) in out:
            out = out.replace(str(frm), str(to), 1)
    return out
