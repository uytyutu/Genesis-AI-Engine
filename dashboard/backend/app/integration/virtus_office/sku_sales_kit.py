"""Sales Kit SKU — professional business document package from customer facts only.

SKU_ENABLED / SALES_KIT_LIVE stay False until Owner E2E PASS.
Executor + validator exist for Owner testing; NOT in OFFICE_SELLABLE_NOW.

Honesty: transform and format customer data — never invent business facts.
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

from app.integration.virtus_office.artifact_writers import write_docx_bytes, write_pdf_bytes
from app.integration.virtus_office.b2b_packages import (
    B2B_DISCLAIMER_DE,
    B2B_PRICE_EUR,
    SALES_KIT_BASIC,
    SALES_KIT_BUSINESS,
    SALES_KIT_LIVE,
    SALES_KIT_PROFESSIONAL,
    SALES_KIT_SKUS,
)

SKU_ID = "sales_kit"
SKU_ENABLED = True  # Owner-approved LIVE flip
EXECUTOR_IMPLEMENTED = True
VALIDATOR_IMPLEMENTED = True

TIER_FILES: dict[str, tuple[str, ...]] = {
    SALES_KIT_BASIC: (
        "Company_Profile.pdf",
        "Company_Profile.docx",
    ),
    SALES_KIT_BUSINESS: (
        "Company_Profile.pdf",
        "Company_Profile.docx",
        "Angebot.pdf",
        "Preislist.pdf",
        "Customer_Email_Template.docx",
    ),
    SALES_KIT_PROFESSIONAL: (
        "Company_Profile.pdf",
        "Company_Profile.docx",
        "Angebot.pdf",
        "Preislist.pdf",
        "Customer_Email_Template.docx",
    ),
}

FABRICATED_MARKERS: tuple[str, ...] = (
    "beispielkunde gmbh",
    "mustermann referenz",
    "fiktive zertifizierung",
    "erfundene leistung",
    "placeholder award",
    "lorem ipsum",
    "guaranteed sales",
    "100% more customers",
    "iso 9001 zertifiziert",  # only if not in source — checked via invented fill
)

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "live": SALES_KIT_LIVE,
    "executor_required": True,
    "validator_required": True,
    "high_risk": False,
    "tiers": {
        SALES_KIT_BASIC: {"price_eur": B2B_PRICE_EUR[SALES_KIT_BASIC], "files": TIER_FILES[SALES_KIT_BASIC]},
        SALES_KIT_BUSINESS: {
            "price_eur": B2B_PRICE_EUR[SALES_KIT_BUSINESS],
            "files": TIER_FILES[SALES_KIT_BUSINESS],
        },
        SALES_KIT_PROFESSIONAL: {
            "price_eur": B2B_PRICE_EUR[SALES_KIT_PROFESSIONAL],
            "files": TIER_FILES[SALES_KIT_PROFESSIONAL],
        },
    },
    "forbidden": [
        "invented_services",
        "invented_prices",
        "invented_customers",
        "invented_certifications",
        "invented_awards",
        "empty_placeholder_files",
        "sell_while_live_false",
    ],
    "delivery": "only_if_validator_PASS_and_SALES_KIT_LIVE",
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_company_input(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize customer company materials — omit empty fields, invent nothing."""
    src = dict(raw or {})
    services_in = src.get("services") or []
    if isinstance(services_in, str):
        services_in = [s.strip() for s in services_in.split("\n") if s.strip()]
    prices_in = src.get("prices") or src.get("price_list") or []
    if isinstance(prices_in, str):
        prices_in = [s.strip() for s in prices_in.split("\n") if s.strip()]
    services: list[dict[str, str]] = []
    for row in services_in:
        if isinstance(row, dict):
            name = _txt(row.get("name") or row.get("title"))
            desc = _txt(row.get("description") or row.get("desc"))
            price = _txt(row.get("price"))
            if name or desc or price:
                services.append({"name": name, "description": desc, "price": price})
        else:
            line = _txt(row)
            if line:
                services.append({"name": line, "description": "", "price": ""})
    price_rows: list[str] = []
    for row in prices_in:
        if isinstance(row, dict):
            line = " — ".join(
                x for x in (_txt(row.get("name")), _txt(row.get("price"))) if x
            )
            if line:
                price_rows.append(line)
        else:
            line = _txt(row)
            if line:
                price_rows.append(line)
    # If services carry prices and price_rows empty, derive display lines from facts only
    if not price_rows:
        for s in services:
            if s.get("price"):
                price_rows.append(f"{s['name']} — {s['price']}" if s.get("name") else s["price"])

    contacts = dict(src.get("contacts") or {})
    return {
        "company_name": _txt(src.get("company_name") or src.get("name")),
        "tagline": _txt(src.get("tagline") or src.get("slogan")),
        "description": _txt(src.get("description") or src.get("about")),
        "services": services,
        "price_rows": price_rows,
        "contacts": {
            "email": _txt(contacts.get("email") or src.get("email")),
            "phone": _txt(contacts.get("phone") or src.get("phone")),
            "address": _txt(contacts.get("address") or src.get("address")),
            "city": _txt(contacts.get("city") or src.get("city")),
            "website": _txt(contacts.get("website") or src.get("website")),
        },
        "advantages": [
            _txt(a)
            for a in (src.get("advantages") or src.get("benefits") or [])
            if _txt(a)
        ],
        "target_customers": _txt(src.get("target_customers") or src.get("target")),
        "source_notes": _txt(src.get("source_notes") or src.get("notes")),
        "logo_present": bool(src.get("logo_bytes") or src.get("logo_material_id")),
        "extra_doc_count": int(src.get("extra_doc_count") or 0),
    }


def missing_required_fields(company: dict[str, Any], *, tier: str = SALES_KIT_BASIC) -> list[str]:
    """Return missing required field ids — do not invent fillers."""
    c = normalize_company_input(company)
    missing: list[str] = []
    if not c["company_name"]:
        missing.append("company_name")
    if not c["description"] and not c["services"]:
        missing.append("description_or_services")
    contacts = c["contacts"]
    if not any(contacts.get(k) for k in ("email", "phone", "address", "website")):
        missing.append("contacts")
    if tier in {SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL}:
        if not c["services"] and not c["price_rows"]:
            missing.append("services_or_prices")
    if tier == SALES_KIT_PROFESSIONAL and c["extra_doc_count"] < 0:
        missing.append("source_materials")
    return missing


def _contact_lines(c: dict[str, Any]) -> list[str]:
    contacts = c["contacts"]
    lines: list[str] = []
    for key in ("address", "city", "phone", "email", "website"):
        if contacts.get(key):
            lines.append(str(contacts[key]))
    return lines


def build_company_profile_paragraphs(company: dict[str, Any]) -> list[str]:
    c = normalize_company_input(company)
    paras: list[str] = []
    if c["tagline"]:
        paras.append(c["tagline"])
    if c["description"]:
        paras.append(c["description"])
    if c["services"]:
        paras.append("Leistungen")
        for s in c["services"]:
            line = s["name"] or s["description"]
            if s["description"] and s["name"]:
                line = f"{s['name']}: {s['description']}"
            if s["price"]:
                line = f"{line} ({s['price']})" if line else s["price"]
            if line:
                paras.append(f"• {line}")
    if c["advantages"]:
        paras.append("Vorteile")
        for a in c["advantages"]:
            paras.append(f"• {a}")
    if c["target_customers"]:
        paras.append(f"Zielkunden: {c['target_customers']}")
    contacts = _contact_lines(c)
    if contacts:
        paras.append("Kontakt")
        paras.extend(contacts)
    paras.append(B2B_DISCLAIMER_DE)
    return paras


def build_angebot_paragraphs(company: dict[str, Any]) -> list[str]:
    c = normalize_company_input(company)
    name = c["company_name"] or "Unser Unternehmen"
    paras = [
        f"Angebot — {name}",
        "Sehr geehrte Damen und Herren,",
        (
            f"hiermit unterbreiten wir Ihnen ein Angebot basierend auf den "
            f"von Ihnen bzw. von {name} bereitgestellten Angaben."
        ),
    ]
    if c["services"]:
        paras.append("Leistungsumfang (Ihre Angaben):")
        for s in c["services"]:
            bit = s["name"] or s["description"]
            if s["price"]:
                bit = f"{bit} — {s['price']}" if bit else s["price"]
            if bit:
                paras.append(f"• {bit}")
    elif c["description"]:
        paras.append(c["description"])
    contacts = _contact_lines(c)
    if contacts:
        paras.append("Kontakt für Rückfragen:")
        paras.extend(contacts)
    paras.append(B2B_DISCLAIMER_DE)
    return paras


def build_preislist_paragraphs(company: dict[str, Any]) -> list[str]:
    c = normalize_company_input(company)
    name = c["company_name"] or "Preisübersicht"
    paras = [f"Preisübersicht — {name}"]
    if c["price_rows"]:
        for row in c["price_rows"]:
            paras.append(f"• {row}")
    else:
        for s in c["services"]:
            if s.get("price"):
                paras.append(f"• {s['name'] or 'Leistung'} — {s['price']}")
            elif s.get("name"):
                paras.append(f"• {s['name']} — Preis auf Anfrage (nicht angegeben)")
    if len(paras) == 1:
        paras.append("Keine Preise in den Quelldaten angegeben.")
    paras.append(B2B_DISCLAIMER_DE)
    return paras


def build_email_template_paragraphs(company: dict[str, Any]) -> list[str]:
    c = normalize_company_input(company)
    name = c["company_name"] or "unser Unternehmen"
    paras = [
        f"Betreff: Informationen zu {name}",
        "",
        "Sehr geehrte Damen und Herren,",
        "",
        f"anbei erhalten Sie Informationen zu {name}.",
    ]
    if c["tagline"]:
        paras.append(c["tagline"])
    if c["description"]:
        paras.append(c["description"])
    paras.extend(
        [
            "",
            "Bei Fragen stehen wir Ihnen gerne zur Verfügung.",
            "",
            "Mit freundlichen Grüßen",
            name,
        ]
    )
    contacts = _contact_lines(c)
    paras.extend(contacts)
    paras.append("")
    paras.append(B2B_DISCLAIMER_DE)
    return paras


def resolve_tier(action_id: str | None = None, tier: str | None = None) -> str:
    raw = (action_id or tier or "").strip().lower()
    if not raw:
        return SALES_KIT_BUSINESS
    if raw in SALES_KIT_SKUS:
        return raw
    aliases = {
        "basic": SALES_KIT_BASIC,
        "business": SALES_KIT_BUSINESS,
        "professional": SALES_KIT_PROFESSIONAL,
        "pro": SALES_KIT_PROFESSIONAL,
        "sales_kit": SALES_KIT_BUSINESS,
    }
    if raw in aliases:
        return aliases[raw]
    # Unknown — return unchanged so callers can reject (do not silently map)
    return raw


def generate_sales_kit(
    *,
    company: dict[str, Any],
    tier: str = SALES_KIT_BUSINESS,
    action_id: str | None = None,
) -> dict[str, Any]:
    """Build ZIP for the purchased tier. Empty placeholders forbidden."""
    resolved = resolve_tier(action_id, tier)
    if resolved not in SALES_KIT_SKUS:
        return {
            "ok": False,
            "error": "invalid_tier",
            "detail": f"Unbekannter Sales Kit Tarif: {action_id or tier}",
            "tier": resolved,
        }
    missing = missing_required_fields(company, tier=resolved)
    if missing:
        return {
            "ok": False,
            "error": "missing_input",
            "missing": missing,
            "detail": "Erforderliche Unternehmensdaten fehlen — keine erfundenen Fakten.",
            "tier": resolved,
        }

    c = normalize_company_input(company)
    title = c["company_name"]
    files: dict[str, bytes] = {}

    profile_paras = build_company_profile_paragraphs(c)
    files["Company_Profile.pdf"] = write_pdf_bytes(title=title, paragraphs=profile_paras)
    files["Company_Profile.docx"] = write_docx_bytes(title=title, paragraphs=profile_paras)

    if resolved in {SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL}:
        angebot = build_angebot_paragraphs(c)
        files["Angebot.pdf"] = write_pdf_bytes(title=f"Angebot — {title}", paragraphs=angebot)
        preis = build_preislist_paragraphs(c)
        files["Preislist.pdf"] = write_pdf_bytes(title=f"Preisübersicht — {title}", paragraphs=preis)
        email_paras = build_email_template_paragraphs(c)
        files["Customer_Email_Template.docx"] = write_docx_bytes(
            title=f"E-Mail — {title}",
            paragraphs=email_paras,
        )

    expected = TIER_FILES[resolved]
    for name in expected:
        if name not in files or not files[name]:
            return {
                "ok": False,
                "error": "empty_output",
                "detail": f"Datei fehlt oder leer: {name}",
                "tier": resolved,
            }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in expected:
            zf.writestr(f"VIRTUS_SALES_KIT/{name}", files[name])
        # Professional: note on source processing count (facts only)
        if resolved == SALES_KIT_PROFESSIONAL:
            note = (
                f"Quellenverarbeitung: {c['extra_doc_count']} zusätzliche Dokumente angegeben.\n"
                f"{B2B_DISCLAIMER_DE}\n"
            )
            zf.writestr("VIRTUS_SALES_KIT/QA_NOTES.txt", note.encode("utf-8"))

    payload = buf.getvalue()
    qa_text = "\n".join(profile_paras)
    return {
        "ok": True,
        "tier": resolved,
        "filename": f"VIRTUS_SALES_KIT_{resolved}.zip",
        "mime": "application/zip",
        "bytes": payload,
        "files": list(expected),
        "qa_text": qa_text,
        "company_name": title,
        "price_eur": B2B_PRICE_EUR[resolved],
        "live_allowed": SALES_KIT_LIVE and SKU_ENABLED,
    }


def validate_sales_kit_artifact(
    *,
    data: bytes,
    tier: str,
    company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validator: ZIP structure, non-empty files, source facts represented, no fabricated markers."""
    resolved = resolve_tier(tier)
    expected = TIER_FILES[resolved]
    checks: list[dict[str, Any]] = []
    ok = True

    def add(name: str, passed: bool, detail: str = "") -> None:
        nonlocal ok
        if not passed:
            ok = False
        checks.append({"id": name, "pass": passed, "detail": detail})

    add("output_exists", bool(data), "ZIP bytes present")
    if not data:
        return {"ok": False, "pass": False, "tier": resolved, "checks": checks}

    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        add("zip_valid", False, str(exc)[:160])
        return {"ok": False, "pass": False, "tier": resolved, "checks": checks}

    add("zip_valid", True)
    names = zf.namelist()
    found: dict[str, bytes] = {}
    for exp in expected:
        path = f"VIRTUS_SALES_KIT/{exp}"
        alt = exp
        match = path if path in names else (alt if alt in names else None)
        if not match:
            add(f"file_{exp}", False, "missing")
            continue
        raw = zf.read(match)
        found[exp] = raw
        add(f"file_{exp}", len(raw) > 32, f"size={len(raw)}")

    # Type sniff
    for exp, raw in found.items():
        if exp.endswith(".pdf"):
            add(f"type_{exp}", raw[:4] == b"%PDF", "PDF header")
        elif exp.endswith(".docx"):
            add(f"type_{exp}", raw[:2] == b"PK", "DOCX zip")

    c = normalize_company_input(company or {})
    # Prefer DOCX XML text for source representation (PDF may subset fonts)
    docx_blob = ""
    docx_raw = found.get("Company_Profile.docx") or b""
    if docx_raw[:2] == b"PK":
        try:
            with zipfile.ZipFile(io.BytesIO(docx_raw)) as dz:
                docx_blob = dz.read("word/document.xml").decode("utf-8", errors="ignore").lower()
        except Exception:  # noqa: BLE001
            docx_blob = ""
    if c.get("company_name"):
        needle = c["company_name"].lower()
        # OOXML may escape & — compare unescaped-ish tokens
        tokens = [t for t in re.split(r"\s+", needle) if len(t) >= 3]
        represented = bool(needle) and (
            needle in docx_blob
            or all(tok in docx_blob for tok in tokens[:3])
            or needle.encode("utf-8") in docx_raw
        )
        add("source_company_represented", bool(represented), "company_name in artifacts")

    blob = docx_blob
    for raw in found.values():
        try:
            blob += raw.decode("utf-8", errors="ignore").lower()
        except Exception:  # noqa: BLE001
            blob += ""

    for marker in FABRICATED_MARKERS:
        if marker in blob:
            add("no_fabricated_placeholders", False, marker)
            break
    else:
        add("no_fabricated_placeholders", True)

    # No unexpected empty expected set
    add("tier_file_set", all(e in found for e in expected), f"expected={expected}")

    return {
        "ok": ok,
        "pass": ok,
        "tier": resolved,
        "checks": checks,
        "files_found": list(found.keys()),
        "delivery_allowed": bool(ok and SALES_KIT_LIVE and SKU_ENABLED),
    }


def can_purchase_sales_kit() -> bool:
    """Checkout gate — false while LIVE/ENABLED off."""
    return bool(SALES_KIT_LIVE and SKU_ENABLED)
