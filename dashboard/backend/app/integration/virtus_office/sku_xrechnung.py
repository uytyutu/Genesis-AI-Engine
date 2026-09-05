"""XRechnung SKU — Phase B executor + structural/business validator.

SKU_ENABLED stays False until:
  1) Owner Phase A GO (done separately)
  2) This module E2E PASS
  3) Optional KoSIT/official Schematron gate (recommended before SELLABLE)
  4) Explicit wire into EXECUTABLE_ACTION_IDS + OFFICE_SELLABLE_NOW

Honesty: validator is Virtus structural + EN 16931 business-term checks,
not a claim of official KoSIT certification. FAIL → no PASS → no delivery
when wired.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
SKU_ID = "xrechnung"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = True
VALIDATOR_IMPLEMENTED = True

# XRechnung 3.0 customization (compliant profile).
XRECHNUNG_CUSTOMIZATION_ID = (
    "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
)
XRECHNUNG_PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
}

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "application/xml (XRechnung UBL Invoice)",
    "validation": [
        "well_formed_xml",
        "required_bt_fields",
        "line_totals",
        "br_de_buyer_reference",
        "no_pass_no_delivery",
    ],
    "delivery": "only_if_validator_PASS",
    "forbidden": [
        "deliver_unvalidated_xml",
        "claim_official_kosit_certification",
        "claim_official_invoice_authority",
    ],
    "price_eur_hint": {"min": 14.90, "max": 29.90},
    "validator_class": "virtus_structural_en16931",
    "official_kosit_schematron": False,
}


def _money(value: Any) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_invoice_input(raw: dict[str, Any] | None = None, *, text: str = "") -> dict[str, Any]:
    """Build a normalized invoice dict from structured fields and/or plain text hints."""
    src = dict(raw or {})
    blob = text or _txt(src.get("source_text"))
    seller = dict(src.get("seller") or {})
    buyer = dict(src.get("buyer") or {})
    lines_in = list(src.get("lines") or [])

    invoice_number = _txt(src.get("invoice_number") or src.get("number"))
    issue_date = _txt(src.get("issue_date") or src.get("date"))
    currency = (_txt(src.get("currency") or "EUR") or "EUR").upper()
    buyer_ref = _txt(src.get("buyer_reference") or src.get("leitweg_id"))
    seller_name = _txt(seller.get("name") or src.get("seller_name"))
    buyer_name = _txt(buyer.get("name") or src.get("buyer_name"))
    seller_vat = _txt(seller.get("vat_id") or seller.get("vat") or src.get("seller_vat"))
    seller_email = _txt(seller.get("email") or src.get("seller_email"))
    seller_country = (_txt(seller.get("country") or "DE") or "DE").upper()
    buyer_country = (_txt(buyer.get("country") or "DE") or "DE").upper()
    seller_city = _txt(seller.get("city"))
    seller_post = _txt(seller.get("post_code") or seller.get("postal_code"))
    seller_street = _txt(seller.get("street") or seller.get("line1"))
    buyer_city = _txt(buyer.get("city"))
    buyer_post = _txt(buyer.get("post_code") or buyer.get("postal_code"))
    buyer_street = _txt(buyer.get("street") or buyer.get("line1"))
    payment_iban = _txt(src.get("iban") or (src.get("payment") or {}).get("iban"))
    payment_means = _txt(
        src.get("payment_means_code") or (src.get("payment") or {}).get("means_code") or "58"
    )

    if blob and not invoice_number:
        m = re.search(
            r"(?:Rechnung(?:s)?(?:nr|nummer)?|Invoice\s*(?:No|Number)?|Nr\.?)\s*[:#]?\s*([A-Za-z0-9\-/]+)",
            blob,
            re.I,
        )
        if m:
            invoice_number = m.group(1)
    if blob and not issue_date:
        m = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})", blob)
        if m:
            d = m.group(1)
            if "." in d:
                dd, mm, yy = d.split(".")
                issue_date = f"{yy}-{mm}-{dd}"
            else:
                issue_date = d
    if blob and not buyer_ref:
        m = re.search(r"(?:Leitweg[- ]?ID|Buyer\s*Reference)\s*[:#]?\s*([0-9\-]+)", blob, re.I)
        if m:
            buyer_ref = m.group(1)
    if blob and not seller_name:
        m = re.search(r"(?:Verk[aä]ufer|Seller|Absender)\s*[:#]?\s*(.+)", blob, re.I)
        if m:
            seller_name = m.group(1).strip()[:120]
    if blob and not buyer_name:
        m = re.search(r"(?:K[aä]ufer|Buyer|Empf[aä]nger)\s*[:#]?\s*(.+)", blob, re.I)
        if m:
            buyer_name = m.group(1).strip()[:120]

    lines: list[dict[str, Any]] = []
    for i, row in enumerate(lines_in, start=1):
        qty = _money(row.get("quantity") or 1)
        price = _money(row.get("unit_price") or row.get("price") or 0)
        vat_pct = _money(row.get("vat_percent") or row.get("vat") or 19)
        name = _txt(row.get("name") or row.get("description") or f"Position {i}")
        net = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lines.append(
            {
                "id": _txt(row.get("id") or str(i)),
                "name": name,
                "quantity": qty,
                "unit_price": price,
                "vat_percent": vat_pct,
                "net": net,
            }
        )

    if not lines and blob:
        # Single catch-all line from Gesamtbetrag / Betrag
        m = re.search(
            r"(?:Gesamtbetrag|Netto|Betrag)\s*[:#]?\s*([0-9]+[.,][0-9]{2})",
            blob,
            re.I,
        )
        if m:
            amount = _money(m.group(1).replace(",", "."))
            lines.append(
                {
                    "id": "1",
                    "name": "Rechnungsposition",
                    "quantity": Decimal("1.00"),
                    "unit_price": amount,
                    "vat_percent": Decimal("19.00"),
                    "net": amount,
                }
            )

    net_total = sum((ln["net"] for ln in lines), Decimal("0.00"))
    # Group VAT by rate
    vat_by_rate: dict[Decimal, Decimal] = {}
    for ln in lines:
        vat_by_rate[ln["vat_percent"]] = vat_by_rate.get(ln["vat_percent"], Decimal("0.00")) + ln[
            "net"
        ]
    tax_total = Decimal("0.00")
    tax_breakdown: list[dict[str, Any]] = []
    for rate, base in sorted(vat_by_rate.items(), key=lambda x: x[0]):
        tax = (base * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax_total += tax
        tax_breakdown.append({"rate": rate, "base": base, "tax": tax})
    gross = (net_total + tax_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "invoice_number": invoice_number,
        "issue_date": issue_date,
        "currency": currency,
        "invoice_type_code": _txt(src.get("invoice_type_code") or "380") or "380",
        "buyer_reference": buyer_ref,
        "seller": {
            "name": seller_name,
            "vat_id": seller_vat,
            "email": seller_email,
            "country": seller_country,
            "city": seller_city,
            "post_code": seller_post,
            "street": seller_street,
            "endpoint": _txt(seller.get("endpoint") or seller_email or seller_vat),
        },
        "buyer": {
            "name": buyer_name,
            "country": buyer_country,
            "city": buyer_city,
            "post_code": buyer_post,
            "street": buyer_street,
            "endpoint": _txt(buyer.get("endpoint") or buyer_ref),
        },
        "payment": {
            "means_code": payment_means or "58",
            "iban": payment_iban,
        },
        "lines": lines,
        "totals": {
            "net": net_total,
            "tax": tax_total,
            "gross": gross,
            "due": gross,
        },
        "tax_breakdown": tax_breakdown,
    }


def _el(tag: str, text: str | None = None, **attrs: str) -> ET.Element:
    node = ET.Element(tag, {k: v for k, v in attrs.items() if v is not None})
    if text is not None:
        node.text = text
    return node


def build_xrechnung_ubl_xml(invoice: dict[str, Any]) -> str:
    """Serialize normalized invoice to UBL 2.1 Invoice XML (XRechnung profile)."""
    for prefix, uri in NS.items():
        ET.register_namespace(prefix if prefix != "ubl" else "", uri)

    root = ET.Element(f"{{{NS['ubl']}}}Invoice")
    root.append(_el(f"{{{NS['cbc']}}}CustomizationID", XRECHNUNG_CUSTOMIZATION_ID))
    root.append(_el(f"{{{NS['cbc']}}}ProfileID", XRECHNUNG_PROFILE_ID))
    root.append(_el(f"{{{NS['cbc']}}}ID", invoice["invoice_number"]))
    root.append(_el(f"{{{NS['cbc']}}}IssueDate", invoice["issue_date"]))
    root.append(_el(f"{{{NS['cbc']}}}InvoiceTypeCode", invoice["invoice_type_code"]))
    root.append(
        _el(f"{{{NS['cbc']}}}DocumentCurrencyCode", invoice["currency"])
    )
    root.append(_el(f"{{{NS['cbc']}}}BuyerReference", invoice["buyer_reference"]))

    # Seller
    seller = invoice["seller"]
    asp = ET.SubElement(root, f"{{{NS['cac']}}}AccountingSupplierParty")
    party = ET.SubElement(asp, f"{{{NS['cac']}}}Party")
    if seller.get("endpoint"):
        party.append(
            _el(
                f"{{{NS['cbc']}}}EndpointID",
                seller["endpoint"],
                schemeID="EM" if "@" in seller["endpoint"] else "0088",
            )
        )
    pn = ET.SubElement(party, f"{{{NS['cac']}}}PartyName")
    pn.append(_el(f"{{{NS['cbc']}}}Name", seller["name"]))
    pa = ET.SubElement(party, f"{{{NS['cac']}}}PostalAddress")
    if seller.get("street"):
        pa.append(_el(f"{{{NS['cbc']}}}StreetName", seller["street"]))
    if seller.get("city"):
        pa.append(_el(f"{{{NS['cbc']}}}CityName", seller["city"]))
    if seller.get("post_code"):
        pa.append(_el(f"{{{NS['cbc']}}}PostalZone", seller["post_code"]))
    pc = ET.SubElement(pa, f"{{{NS['cac']}}}Country")
    pc.append(_el(f"{{{NS['cbc']}}}IdentificationCode", seller["country"]))
    if seller.get("vat_id"):
        pt = ET.SubElement(party, f"{{{NS['cac']}}}PartyTaxScheme")
        pt.append(_el(f"{{{NS['cbc']}}}CompanyID", seller["vat_id"]))
        ts = ET.SubElement(pt, f"{{{NS['cac']}}}TaxScheme")
        ts.append(_el(f"{{{NS['cbc']}}}ID", "VAT"))
    if seller.get("email"):
        contact = ET.SubElement(party, f"{{{NS['cac']}}}Contact")
        contact.append(_el(f"{{{NS['cbc']}}}ElectronicMail", seller["email"]))

    # Buyer
    buyer = invoice["buyer"]
    acp = ET.SubElement(root, f"{{{NS['cac']}}}AccountingCustomerParty")
    bparty = ET.SubElement(acp, f"{{{NS['cac']}}}Party")
    if buyer.get("endpoint"):
        bparty.append(
            _el(
                f"{{{NS['cbc']}}}EndpointID",
                buyer["endpoint"],
                schemeID="0204" if re.match(r"^\d{2}-\d+", buyer["endpoint"] or "") else "EM",
            )
        )
    bpn = ET.SubElement(bparty, f"{{{NS['cac']}}}PartyName")
    bpn.append(_el(f"{{{NS['cbc']}}}Name", buyer["name"]))
    bpa = ET.SubElement(bparty, f"{{{NS['cac']}}}PostalAddress")
    if buyer.get("street"):
        bpa.append(_el(f"{{{NS['cbc']}}}StreetName", buyer["street"]))
    if buyer.get("city"):
        bpa.append(_el(f"{{{NS['cbc']}}}CityName", buyer["city"]))
    if buyer.get("post_code"):
        bpa.append(_el(f"{{{NS['cbc']}}}PostalZone", buyer["post_code"]))
    bpc = ET.SubElement(bpa, f"{{{NS['cac']}}}Country")
    bpc.append(_el(f"{{{NS['cbc']}}}IdentificationCode", buyer["country"]))

    # Payment
    pay = invoice["payment"]
    pm = ET.SubElement(root, f"{{{NS['cac']}}}PaymentMeans")
    pm.append(_el(f"{{{NS['cbc']}}}PaymentMeansCode", pay["means_code"]))
    if pay.get("iban"):
        fa = ET.SubElement(pm, f"{{{NS['cac']}}}PayeeFinancialAccount")
        fa.append(_el(f"{{{NS['cbc']}}}ID", pay["iban"]))

    # Tax total
    totals = invoice["totals"]
    tt = ET.SubElement(root, f"{{{NS['cac']}}}TaxTotal")
    tt.append(
        _el(
            f"{{{NS['cbc']}}}TaxAmount",
            f"{totals['tax']:.2f}",
            currencyID=invoice["currency"],
        )
    )
    for br in invoice["tax_breakdown"]:
        tsub = ET.SubElement(tt, f"{{{NS['cac']}}}TaxSubtotal")
        tsub.append(
            _el(
                f"{{{NS['cbc']}}}TaxableAmount",
                f"{br['base']:.2f}",
                currencyID=invoice["currency"],
            )
        )
        tsub.append(
            _el(
                f"{{{NS['cbc']}}}TaxAmount",
                f"{br['tax']:.2f}",
                currencyID=invoice["currency"],
            )
        )
        cat = ET.SubElement(tsub, f"{{{NS['cac']}}}TaxCategory")
        cat.append(_el(f"{{{NS['cbc']}}}ID", "S"))
        cat.append(_el(f"{{{NS['cbc']}}}Percent", f"{br['rate']:.2f}"))
        ts = ET.SubElement(cat, f"{{{NS['cac']}}}TaxScheme")
        ts.append(_el(f"{{{NS['cbc']}}}ID", "VAT"))

    # Monetary total
    mt = ET.SubElement(root, f"{{{NS['cac']}}}LegalMonetaryTotal")
    mt.append(
        _el(
            f"{{{NS['cbc']}}}LineExtensionAmount",
            f"{totals['net']:.2f}",
            currencyID=invoice["currency"],
        )
    )
    mt.append(
        _el(
            f"{{{NS['cbc']}}}TaxExclusiveAmount",
            f"{totals['net']:.2f}",
            currencyID=invoice["currency"],
        )
    )
    mt.append(
        _el(
            f"{{{NS['cbc']}}}TaxInclusiveAmount",
            f"{totals['gross']:.2f}",
            currencyID=invoice["currency"],
        )
    )
    mt.append(
        _el(
            f"{{{NS['cbc']}}}PayableAmount",
            f"{totals['due']:.2f}",
            currencyID=invoice["currency"],
        )
    )

    for ln in invoice["lines"]:
        il = ET.SubElement(root, f"{{{NS['cac']}}}InvoiceLine")
        il.append(_el(f"{{{NS['cbc']}}}ID", ln["id"]))
        il.append(
            _el(
                f"{{{NS['cbc']}}}InvoicedQuantity",
                f"{ln['quantity']:.2f}",
                unitCode="C62",
            )
        )
        il.append(
            _el(
                f"{{{NS['cbc']}}}LineExtensionAmount",
                f"{ln['net']:.2f}",
                currencyID=invoice["currency"],
            )
        )
        item = ET.SubElement(il, f"{{{NS['cac']}}}Item")
        item.append(_el(f"{{{NS['cbc']}}}Name", ln["name"]))
        tcat = ET.SubElement(item, f"{{{NS['cac']}}}ClassifiedTaxCategory")
        tcat.append(_el(f"{{{NS['cbc']}}}ID", "S"))
        tcat.append(_el(f"{{{NS['cbc']}}}Percent", f"{ln['vat_percent']:.2f}"))
        tsch = ET.SubElement(tcat, f"{{{NS['cac']}}}TaxScheme")
        tsch.append(_el(f"{{{NS['cbc']}}}ID", "VAT"))
        price = ET.SubElement(il, f"{{{NS['cac']}}}Price")
        price.append(
            _el(
                f"{{{NS['cbc']}}}PriceAmount",
                f"{ln['unit_price']:.2f}",
                currencyID=invoice["currency"],
            )
        )

    # Pretty-ish: ElementTree tostring
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def _find_text(root: ET.Element, path: str) -> str:
    node = root.find(path, NS)
    return (node.text or "").strip() if node is not None else ""


def validate_xrechnung(
    *,
    xml_text: str | None = None,
    artifact_bytes: bytes | None = None,
    invoice: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Structural + business validation. passed=False ⇒ no delivery when wired."""
    checks: list[dict[str, Any]] = []
    problems: list[dict[str, str]] = []

    def add(code: str, ok: bool, detail: str = "") -> None:
        checks.append({"code": code, "ok": ok, "detail": detail})
        if not ok:
            problems.append({"code": code, "detail": detail})

    raw = xml_text
    if raw is None and artifact_bytes is not None:
        raw = artifact_bytes.decode("utf-8", errors="replace")
    if not raw or not str(raw).strip():
        add("xml_present", False, "empty xml")
        return {
            "ok": False,
            "passed": False,
            "checks": checks,
            "problems": problems,
            "validator_class": SKU_CONTRACT["validator_class"],
            "detail": "empty xml",
        }

    try:
        root = ET.fromstring(raw)
        add("well_formed_xml", True, "parsed")
    except ET.ParseError as exc:
        add("well_formed_xml", False, str(exc)[:160])
        return {
            "ok": False,
            "passed": False,
            "checks": checks,
            "problems": problems,
            "validator_class": SKU_CONTRACT["validator_class"],
            "detail": "xml parse error",
        }

    local = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    add("root_invoice", local == "Invoice", f"root={local}")

    customization = _find_text(root, "cbc:CustomizationID")
    add(
        "bt24_customization",
        "xrechnung" in customization.lower() or "en16931" in customization.lower(),
        customization[:120],
    )
    inv_id = _find_text(root, "cbc:ID")
    add("bt1_invoice_number", bool(inv_id), inv_id)
    issue = _find_text(root, "cbc:IssueDate")
    add("bt2_issue_date", bool(re.match(r"^\d{4}-\d{2}-\d{2}$", issue)), issue)
    currency = _find_text(root, "cbc:DocumentCurrencyCode")
    add("bt5_currency", bool(currency), currency)
    buyer_ref = _find_text(root, "cbc:BuyerReference")
    add("br_de_15_buyer_reference", bool(buyer_ref), buyer_ref)

    seller_name = _find_text(
        root, "cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name"
    )
    buyer_name = _find_text(
        root, "cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name"
    )
    add("br06_seller_name", bool(seller_name), seller_name)
    add("br07_buyer_name", bool(buyer_name), buyer_name)

    seller_country = _find_text(
        root,
        "cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
    )
    buyer_country = _find_text(
        root,
        "cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
    )
    add("br09_seller_country", bool(seller_country), seller_country)
    add("br11_buyer_country", bool(buyer_country), buyer_country)

    seller_mail = _find_text(
        root, "cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:ElectronicMail"
    )
    add("br_de_13_seller_email", bool(seller_mail), seller_mail)

    payment_code = _find_text(root, "cac:PaymentMeans/cbc:PaymentMeansCode")
    add("br_de_01_payment_means", bool(payment_code), payment_code)

    lines = root.findall("cac:InvoiceLine", NS)
    add("br15_invoice_lines", len(lines) >= 1, f"count={len(lines)}")

    payable = _find_text(root, "cac:LegalMonetaryTotal/cbc:PayableAmount")
    add("br13_payable", bool(payable), payable)

    # Cross-check totals vs lines when invoice model provided
    if invoice and invoice.get("lines"):
        model = invoice if "totals" in invoice else normalize_invoice_input(invoice)
        expected_net = _money((model.get("totals") or {}).get("net"))
        line_sum = sum(
            (
                _money(ln.get("net"))
                if ln.get("net") is not None
                else _money(ln.get("quantity") or 1) * _money(ln.get("unit_price") or ln.get("price") or 0)
            )
            for ln in model["lines"]
        )
        add(
            "line_totals_match",
            expected_net == line_sum,
            f"net={expected_net} lines={line_sum}",
        )

    # Reject obvious demo placeholders in customer-facing artifact
    banned = ("lorem ipsum", "demo only", "placeholder", "test invoice virtus fake")
    low = raw.lower()
    add(
        "no_demo_residue",
        not any(b in low for b in banned),
        "demo scan",
    )

    passed = all(c["ok"] for c in checks)
    return {
        "ok": passed,
        "passed": passed,
        "checks": checks,
        "problems": problems,
        "validator_class": SKU_CONTRACT["validator_class"],
        "official_kosit_schematron": False,
        "detail": "PASS" if passed else f"FAIL:{','.join(p['code'] for p in problems)}",
    }


def execute_xrechnung(
    *,
    invoice: dict[str, Any] | None = None,
    text: str = "",
    filename: str = "rechnung.xml",
    **_kwargs: Any,
) -> dict[str, Any]:
    """Generate XRechnung XML then validate. FAIL ⇒ ok=False (no delivery when wired)."""
    if not EXECUTOR_IMPLEMENTED:
        return {
            "ok": False,
            "error": "not_implemented",
            "detail": "XRechnung executor not implemented",
        }
    model = normalize_invoice_input(invoice, text=text)
    # Preflight required semantic fields before XML
    missing = [
        k
        for k, v in {
            "invoice_number": model["invoice_number"],
            "issue_date": model["issue_date"],
            "buyer_reference": model["buyer_reference"],
            "seller.name": model["seller"]["name"],
            "seller.email": model["seller"]["email"],
            "seller.vat_id": model["seller"]["vat_id"],
            "buyer.name": model["buyer"]["name"],
            "lines": model["lines"],
        }.items()
        if not v
    ]
    if missing:
        return {
            "ok": False,
            "error": "incomplete_invoice",
            "detail": f"Missing required fields: {', '.join(missing)}",
            "missing": missing,
            "passed": False,
        }

    xml_text = build_xrechnung_ubl_xml(model)
    validation = validate_xrechnung(xml_text=xml_text, invoice=model)
    if not validation.get("passed"):
        return {
            "ok": False,
            "error": "validation_failed",
            "detail": validation.get("detail"),
            "quality": validation,
            "passed": False,
            "bytes": None,
        }

    out_name = filename if filename.lower().endswith(".xml") else f"{filename}.xml"
    if out_name == "rechnung.xml" and model["invoice_number"]:
        safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", model["invoice_number"])[:40]
        out_name = f"xrechnung_{safe}.xml"

    return {
        "ok": True,
        "passed": True,
        "bytes": xml_text.encode("utf-8"),
        "filename": out_name,
        "ext": "xml",
        "mime": "application/xml",
        "quality": validation,
        "invoice": {
            "invoice_number": model["invoice_number"],
            "gross": str(model["totals"]["gross"]),
            "currency": model["currency"],
        },
        "sku_enabled": SKU_ENABLED,
        "note": "SKU not sellable until SKU_ENABLED + catalog wire",
    }


__all__ = [
    "SKU_ID",
    "SKU_ENABLED",
    "EXECUTOR_IMPLEMENTED",
    "VALIDATOR_IMPLEMENTED",
    "SKU_CONTRACT",
    "normalize_invoice_input",
    "build_xrechnung_ubl_xml",
    "execute_xrechnung",
    "validate_xrechnung",
]
