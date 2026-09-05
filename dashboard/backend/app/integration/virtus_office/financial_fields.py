"""Financial document field extraction + OCR honesty checks for Virtus Office.

Used for invoices / Rechnungen: critical fields must not silently green-pass
when OCR garbles numbers, dates, or VAT arithmetic.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

_AMOUNT_RE = re.compile(
    r"(?<![\d.,])(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2})(?![\d])"
)
_RATE_RE = re.compile(
    r"(?:mwst|ust|vat|umsatzsteuer|mehrwertsteuer)[^\d%]{0,20}(\d{1,2}(?:[.,]\d+)?)\s*%",
    re.I,
)
_CURRENCY_RE = re.compile(r"\b(EUR|USD|CHF|GBP|PLN|UAH)\b|(€|\$)", re.I)
_DATE_RE = re.compile(
    r"(?:datum|date|rechnungsdatum)[^\d]{0,12}(\d{1,2})[./,\s-]+(\d{1,2})[./,\s-]+(\d{2,4})",
    re.I,
)
_DATE_LOOSE_RE = re.compile(r"\b(\d{1,2})[./,\s-]+(\d{1,2})[./,\s-]+(\d{2,4})\b")
_INV_RE = re.compile(
    r"(?:rechnungsnr\.?|rechnungsnummer|invoice\s*(?:no\.?|number|#)|nr\.?|no\.?)"
    r"\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-/]{2,})",
    re.I,
)
_NETTO_LINE_RE = re.compile(
    r"(?:betrag|netto|net\s*amount|zwischensumme)[^\d]{0,20}"
    r"(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2})",
    re.I,
)
_MWST_AMT_RE = re.compile(
    r"(?:mwst|ust|vat|umsatzsteuer)[^\d%]{0,24}(?:\d{1,2}(?:[.,]\d+)?\s*%\s*)?"
    r"(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2})",
    re.I,
)
_BRUTTO_RE = re.compile(
    r"(?:gesamt(?:betrag)?|brutto|total|summe)[^\d]{0,20}"
    r"(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2})",
    re.I,
)

_WARNING_DE = (
    "Einige Finanzfelder wurden mit niedriger Sicherheit erkannt oder die "
    "MwSt-Arithmetik stimmt nicht. Bitte vor dem Fortfahren prüfen."
)
_WARNING_EN = (
    "Some financial fields were recognized with low confidence or VAT "
    "arithmetic does not add up. Please review before continuing."
)


def looks_like_financial_document(text: str) -> bool:
    low = (text or "").lower()
    strong = 0
    for token in (
        "rechnung",
        "invoice",
        "mwst",
        "umsatzsteuer",
        "vat ",
        " netto",
        "brutto",
        "iban",
        "rechnungsnr",
        "rechnungsnummer",
        "rechnungsdatum",
    ):
        if token.strip() in low:
            strong += 1
    if strong >= 2:
        return True
    if ("rechnung" in low or "invoice" in low) and bool(_AMOUNT_RE.search(text or "")):
        return True
    if ("mwst" in low or "umsatzsteuer" in low or re.search(r"\bvat\b", low)) and bool(
        _AMOUNT_RE.search(text or "")
    ):
        return True
    return False


def parse_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    s = str(raw).strip().replace(" ", "").replace("\u00a0", "")
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _norm_date(d: str, m: str, y: str) -> str | None:
    try:
        day, month, year = int(d), int(m), int(y)
    except ValueError:
        return None
    if year < 100:
        year += 2000
    if not (1 <= day <= 31 and 1 <= month <= 12 and 1990 <= year <= 2100):
        return None
    return f"{day:02d}.{month:02d}.{year:04d}"


def extract_financial_fields(text: str) -> dict[str, Any]:
    raw = text or ""
    fields: dict[str, Any] = {
        "invoice_number": None,
        "date": None,
        "netto": None,
        "mwst_rate": None,
        "mwst_amount": None,
        "brutto": None,
        "currency": None,
    }

    m = _INV_RE.search(raw)
    if m:
        fields["invoice_number"] = m.group(1).strip()

    m = _DATE_RE.search(raw) or _DATE_LOOSE_RE.search(raw)
    if m:
        fields["date"] = _norm_date(m.group(1), m.group(2), m.group(3))

    m = _NETTO_LINE_RE.search(raw)
    if m:
        fields["netto"] = parse_decimal(m.group(1))

    m = _RATE_RE.search(raw)
    if m:
        rate = parse_decimal(m.group(1))
        if rate is not None:
            fields["mwst_rate"] = rate

    m = _MWST_AMT_RE.search(raw)
    if m:
        fields["mwst_amount"] = parse_decimal(m.group(1))

    m = _BRUTTO_RE.search(raw)
    if m:
        fields["brutto"] = parse_decimal(m.group(1))

    m = _CURRENCY_RE.search(raw)
    if m:
        cur = (m.group(1) or m.group(2) or "").upper()
        if cur in {"€", ""}:
            cur = "EUR"
        if cur == "$":
            cur = "USD"
        fields["currency"] = cur

    return fields


def _money_ok(value: Decimal | None) -> bool:
    if value is None:
        return False
    return value >= 0 and value < Decimal("100000000")


def _invoice_number_anomaly(num: str | None) -> str | None:
    if not num:
        return "missing_invoice_number"
    if re.search(r"[A-Za-z]{2,}\d+$", num) and re.search(r"T\d+$", num, re.I):
        return "invoice_number_ocr_glue"
    if " " in num or "," in num:
        return "invoice_number_noise"
    return None


def _date_anomaly(date_s: str | None) -> str | None:
    if not date_s:
        return "missing_date"
    try:
        _d, _m, y = date_s.split(".")
        year = int(y)
    except Exception:
        return "invalid_date"
    if year > 2035 or year < 2000:
        return "date_year_out_of_range"
    return None


def validate_financial_fields(
    text: str,
    *,
    confidence: float | None = None,
    require_fields: bool | None = None,
) -> dict[str, Any]:
    """Return honesty verdict for financial OCR / translate input."""
    raw = text or ""
    financial = looks_like_financial_document(raw)
    fields = extract_financial_fields(raw)
    issues: list[str] = []
    field_status: dict[str, str] = {}

    if not financial:
        return {
            "is_financial": False,
            "passed": True,
            "needs_review": False,
            "fields": _fields_public(fields),
            "issues": [],
            "warning_de": None,
            "warning_en": None,
            "arithmetic_ok": None,
            "confidence": confidence,
        }

    req = True if require_fields is None else require_fields

    inv_issue = _invoice_number_anomaly(fields.get("invoice_number"))
    if inv_issue:
        issues.append(inv_issue)
        field_status["invoice_number"] = "fail"
    else:
        field_status["invoice_number"] = "ok"

    date_issue = _date_anomaly(fields.get("date"))
    if date_issue:
        issues.append(date_issue)
        field_status["date"] = "fail"
    else:
        field_status["date"] = "ok"

    for key in ("netto", "mwst_amount", "brutto"):
        val = fields.get(key)
        if val is None:
            if req:
                issues.append(f"missing_{key}")
                field_status[key] = "fail"
            else:
                field_status[key] = "missing"
        elif not _money_ok(val):
            issues.append(f"invalid_{key}")
            field_status[key] = "fail"
        else:
            if key == "brutto" and val == val.to_integral_value() and val >= 1000:
                if fields.get("netto") is not None and fields.get("mwst_amount") is not None:
                    issues.append("brutto_missing_decimals")
                    field_status[key] = "fail"
                else:
                    field_status[key] = "ok"
            else:
                field_status[key] = "ok"

    if fields.get("mwst_rate") is None:
        if req:
            issues.append("missing_mwst_rate")
            field_status["mwst_rate"] = "fail"
        else:
            field_status["mwst_rate"] = "missing"
    else:
        rate = fields["mwst_rate"]
        if rate < 0 or rate > 100:
            issues.append("invalid_mwst_rate")
            field_status["mwst_rate"] = "fail"
        else:
            field_status["mwst_rate"] = "ok"

    if fields.get("currency") is None:
        issues.append("missing_currency")
        field_status["currency"] = "fail"
    else:
        field_status["currency"] = "ok"

    arithmetic_ok: bool | None = None
    netto = fields.get("netto")
    mwst = fields.get("mwst_amount")
    brutto = fields.get("brutto")
    rate = fields.get("mwst_rate")

    if netto is not None and mwst is not None and brutto is not None:
        expected = (netto + mwst).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        got = brutto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        arithmetic_ok = abs(expected - got) <= Decimal("0.05")
        if not arithmetic_ok:
            issues.append("arithmetic_netto_mwst_ne_brutto")
            field_status["arithmetic"] = "fail"
        else:
            field_status["arithmetic"] = "ok"
        if rate is not None and netto > 0:
            expected_mwst = (netto * rate / Decimal(100)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if abs(expected_mwst - mwst.quantize(Decimal("0.01"))) > Decimal("0.05"):
                issues.append("arithmetic_mwst_rate_mismatch")
                field_status["mwst_amount"] = "fail"
                arithmetic_ok = False

    if re.search(r"(?:gesamt|brutto|total)\s*\d{4,}(?:\s*EUR)?\b", raw, re.I):
        if "brutto_missing_decimals" not in issues and "brutto_ocr_glue" not in issues:
            # only when decimal form missing
            if fields.get("brutto") is not None and "." not in str(fields["brutto"]):
                issues.append("brutto_ocr_glue")
                field_status["brutto"] = "fail"

    if confidence is not None and confidence < 0.72 and financial:
        issues.append("low_ocr_confidence")

    passed = len(issues) == 0
    needs_review = not passed
    return {
        "is_financial": True,
        "passed": passed,
        "needs_review": needs_review,
        "fields": _fields_public(fields),
        "field_status": field_status,
        "issues": issues,
        "warning_de": _WARNING_DE if needs_review else None,
        "warning_en": _WARNING_EN if needs_review else None,
        "arithmetic_ok": arithmetic_ok,
        "confidence": confidence,
    }


def _fields_public(fields: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in fields.items():
        if isinstance(v, Decimal):
            out[k] = f"{v:.2f}"
        else:
            out[k] = v
    return out


def financial_output_preserves_critical(
    input_text: str,
    output_text: str,
) -> dict[str, Any]:
    """After translate: critical numbers/dates from input must appear in output."""
    src = extract_financial_fields(input_text)
    missing: list[str] = []
    out = output_text or ""

    if src.get("invoice_number") and str(src["invoice_number"]) not in out:
        compact = str(src["invoice_number"]).replace(" ", "")
        if compact not in out.replace(" ", ""):
            missing.append("invoice_number")

    if src.get("date"):
        parts = str(src["date"]).split(".")
        if len(parts) == 3:
            d, m, y = parts
            patterns = (
                src["date"],
                f"{d}/{m}/{y}",
                f"{y}-{m}-{d}",
                f"{int(d)}.{int(m)}.{y}",
            )
            if not any(p in out for p in patterns):
                missing.append("date")

    for key in ("netto", "mwst_amount", "brutto"):
        val = src.get(key)
        if val is None:
            continue
        variants = {
            f"{val:.2f}",
            f"{val:.2f}".replace(".", ","),
            str(val),
        }
        if not any(v in out for v in variants):
            missing.append(key)

    if src.get("mwst_rate") is not None:
        rate = src["mwst_rate"]
        try:
            rate_i = int(rate)
        except Exception:
            rate_i = None
        rate_ok = (
            f"{rate}%" in out
            or f"{rate:.0f}%" in out
            or f"{str(rate).replace('.', ',')}%" in out
            or (rate_i is not None and f"{rate_i}%" in out)
            or (rate_i is not None and f"{rate_i} %" in out)
            or (
                rate_i is not None
                and bool(re.search(rf"\b{rate_i}\s*(%|percent|pct)\b", out, re.I))
            )
        )
        if not rate_ok:
            missing.append("mwst_rate")

    return {
        "passed": len(missing) == 0,
        "missing": missing,
        "source_fields": _fields_public(src),
    }
