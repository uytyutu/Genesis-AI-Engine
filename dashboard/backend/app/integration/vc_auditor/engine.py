"""Virtus Core Website Auditor engine — public URL + Virtus Core product modes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.integration.vc_auditor.branding import (
    ENGINE_ID,
    PRODUCT_ID,
    PRODUCT_NAME,
    PRODUCT_VERSION,
)
from app.integration.vc_auditor.export import export_report
from app.integration.vc_auditor.scoring import (
    build_findings,
    overall_business_score,
    score_business,
    score_legal_de,
    score_website,
)
from app.integration.vc_auditor.signals import extract_signals
from app.integration.vc_auditor.summary import build_ai_summary
from app.integration.vector.website_tips import find_product_dir


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    return u


def _compose_report(
    *,
    mode: str,
    target: str,
    signals: dict[str, Any],
    locale: str,
    virtus_mode: bool,
    product_id: str | None = None,
    order_id: str | None = None,
    fetch_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    website = score_website(signals)
    legal = score_legal_de(signals)
    business = score_business(signals)
    overall = overall_business_score(website, legal, business)
    findings = build_findings(signals, virtus_mode=virtus_mode, locale=locale)
    ai_summary = build_ai_summary(
        overall=overall,
        findings=findings,
        website=website,
        locale=locale,
    )
    report_id = f"vca_{uuid.uuid4().hex[:12]}"
    return {
        "ok": True,
        "product": PRODUCT_NAME,
        "product_id": PRODUCT_ID,
        "product_version": PRODUCT_VERSION,
        "engine_id": ENGINE_ID,
        "report_id": report_id,
        "mode": mode,
        "target": target,
        "locale": locale,
        "virtus_mode": virtus_mode,
        "product_id_ref": product_id,
        "order_id": order_id,
        "overall_business_score": overall,
        "website": website,
        "germany_legal": legal,
        "business": business,
        "findings": findings,
        "ai_summary": ai_summary,
        "signals": signals,
        "fetch": fetch_meta or {},
        "exports": ["json", "csv", "markdown", "pdf"],
        "created_at": _now(),
        "branding": {
            "name": PRODUCT_NAME,
            "apify_title": PRODUCT_NAME,
            "tagline": "What exactly should I fix to make my website better?",
        },
    }


class VirtusCoreWebsiteAuditor:
    """One engine — public scan + Virtus Core in-platform audit."""

    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._reports = self._memory / "vc_auditor" / "reports"
        self._reports.mkdir(parents=True, exist_ok=True)

    def _save(self, report: dict[str, Any]) -> None:
        rid = str(report.get("report_id") or "")
        if not rid:
            return
        path = self._reports / f"{rid}.json"
        path.write_text(
            __import__("json").dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        path = self._reports / f"{report_id}.json"
        if not path.is_file():
            return None
        try:
            import json

            raw = json.loads(path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else None
        except (OSError, ValueError):
            return None

    def analyze_url(
        self,
        url: str,
        *,
        locale: str = "de",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        target = _normalize_url(url)
        if not target:
            return {"ok": False, "error": "url_required", "product": PRODUCT_NAME}

        html = ""
        final_url = target
        status_code = 0
        err = None
        try:
            from app.integration.stealth_http import (
                UnauthorizedOperation,
                stealth_fetch_get,
            )

            resp = stealth_fetch_get(target)
            html = resp.text or ""
            final_url = str(resp.url)
            status_code = int(resp.status_code)
            if status_code >= 400:
                err = f"http_{status_code}"
        except UnauthorizedOperation:
            err = "Unauthorized Operation"
        except ValueError as exc:
            err = str(exc)
        except Exception as exc:
            err = f"fetch_failed:{type(exc).__name__}"

        if not html and not err:
            err = "empty_response"

        signals = extract_signals(html, final_url=final_url)
        if err and not html:
            # unreachable — honest low security/https unknown
            signals["https"] = target.startswith("https://")
            report = _compose_report(
                mode="public",
                target=target,
                signals=signals,
                locale=locale,
                virtus_mode=False,
                fetch_meta={
                    "ok": False,
                    "error": err,
                    "status_code": status_code,
                    "final_url": final_url,
                },
            )
            report["ai_summary"] = (
                "Die Website konnte nicht vollständig geladen werden. "
                "Prüfen Sie die URL und die Erreichbarkeit — danach erneut analysieren."
                if (locale or "").lower().startswith("de")
                else "The website could not be fully loaded. Check the URL and try again."
            )
            report["findings"] = [
                {
                    "id": "fetch_failed",
                    "category": "security",
                    "severity": "high",
                    "message": f"Fetch failed: {err}",
                    "pass": False,
                    "action": {
                        "id": "retry",
                        "kind": "noop",
                        "label": "Retry",
                        "status": "live",
                    },
                }
            ]
            report["overall_business_score"] = 15
            self._save(report)
            return report

        report = _compose_report(
            mode="public",
            target=target,
            signals=signals,
            locale=locale,
            virtus_mode=False,
            fetch_meta={
                "ok": True,
                "error": err,
                "status_code": status_code,
                "final_url": final_url,
                "bytes": len(html.encode("utf-8", errors="replace")),
            },
        )
        self._save(report)
        return report

    def analyze_virtus_product(
        self,
        *,
        product_id: str | None = None,
        order_id: str | None = None,
        product_dir: Path | None = None,
        locale: str = "de",
        niche: str | None = None,
    ) -> dict[str, Any]:
        root = product_dir or (find_product_dir(product_id or "") if product_id else None)
        if root is None:
            return {
                "ok": False,
                "error": "website_product_not_found",
                "product": PRODUCT_NAME,
            }

        index = ""
        impressum = ""
        datenschutz = ""
        try:
            index = (root / "index.html").read_text(encoding="utf-8", errors="replace")
        except OSError:
            index = ""
        try:
            impressum = (root / "impressum.html").read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            impressum = ""
        try:
            datenschutz = (root / "datenschutz.html").read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            datenschutz = ""

        # Merge legal pages into scan corpus so local files count
        corpus = "\n".join([index, impressum, datenschutz])
        signals = extract_signals(
            corpus,
            final_url=f"https://virtus.local/{root.name}/",
        )
        # Local Virtus packages are designed for HTTPS publish
        signals["https"] = True
        if impressum.strip():
            signals["impressum"] = True
        if datenschutz.strip():
            signals["datenschutz"] = True

        target = niche or root.name
        report = _compose_report(
            mode="virtus_core",
            target=str(target),
            signals=signals,
            locale=locale,
            virtus_mode=True,
            product_id=product_id or root.name,
            order_id=order_id,
            fetch_meta={
                "ok": True,
                "source": "virtus_factory_package",
                "product_dir": str(root),
            },
        )
        self._save(report)
        return report

    def export(self, report_id: str, fmt: str) -> tuple[bytes, str, str] | None:
        report = self.get_report(report_id)
        if not report:
            return None
        return export_report(report, fmt)
