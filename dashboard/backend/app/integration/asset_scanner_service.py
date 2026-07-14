"""Asset Scanner — legal public-only abandoned web asset discovery.

SECURITY LAW (binding):
- ONLY publicly reachable HTTP(S) URLs
- NO credentials, API keys, private repos, cloud buckets, or closed systems
- NO password/cookie/session harvesting
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.integration.opportunity_service import OpportunityService
from app.integration.site_analysis_service import SiteAnalysisService
from app.integration.stealth_crawl_service import stealth_status

# Taboo — reject before any network call
_FORBIDDEN_URL_PATTERNS = re.compile(
    r"(github\.com/.+/(?:blob|tree)/.+\.(?:env|pem|key|secret)|"
    r"s3\.amazonaws\.com|storage\.googleapis\.com|"
    r"\.git/|/admin/|/wp-admin/|api[_-]?key|password|private)",
    re.I,
)

_FORBIDDEN_QUERY_KEYWORDS = re.compile(
    r"(api[_-]?key|secret|password|token|credential|private[_-]?key)",
    re.I,
)

_ABANDONED_SIGNALS = (
    "under construction",
    "coming soon",
    "domain for sale",
    "diese domain",
    "parked",
    "godaddy",
    "sedo",
    "expired",
    "baustelle",
    "wartung",
)

_NICHE_CATALOG: dict[str, dict[str, Any]] = {
    "local_service": {
        "label": "Локальные услуги",
        "lead_value_eur": 25.0,
        "seed_queries": ["autowerkstatt pirna", "sanitaer dresden"],
    },
    "expired_landing": {
        "label": "Заброшенные лендинги",
        "lead_value_eur": 40.0,
        "seed_queries": ["coming soon business", "under construction website"],
    },
    "niche_blog": {
        "label": "Нишевые блоги",
        "lead_value_eur": 30.0,
        "seed_queries": ["old blog archive", "veraltete website"],
    },
}


def assert_public_scan_allowed(url: str) -> None:
    """Raise ValueError if URL violates security law."""
    raw = (url or "").strip()
    if not raw:
        raise ValueError("url_required")
    if _FORBIDDEN_URL_PATTERNS.search(raw):
        raise ValueError("forbidden_target")
    if _FORBIDDEN_QUERY_KEYWORDS.search(raw):
        raise ValueError("forbidden_target")
    if not raw.startswith(("http://", "https://")):
        raise ValueError("public_http_only")


def _estimate_traffic_band(analysis: dict) -> str:
    score = int(analysis.get("improvement_score") or 0)
    issues = int(analysis.get("issue_count") or 0)
    if score >= 55 and issues <= 2:
        return "medium"
    if score >= 35:
        return "low"
    return "trace"


def _income_rationale(analysis: dict, niche: str) -> str:
    profile = _NICHE_CATALOG.get(niche) or _NICHE_CATALOG["local_service"]
    issues = analysis.get("issues") or []
    strengths = analysis.get("strengths") or []
    traffic = _estimate_traffic_band(analysis)
    parts = [
        f"Ниша: {profile['label']}.",
        f"Сигнал трафика: {traffic}.",
    ]
    if issues:
        parts.append(f"Слабости: {'; '.join(issues[:3])}.")
    if strengths:
        parts.append(f"Плюсы: {'; '.join(strengths[:2])}.")
    parts.append(
        "Легальный путь: перехват домена/площадки после проверки WHOIS, "
        "монетизация рекламой или лид-формой — без доступа к чужим аккаунтам."
    )
    return " ".join(parts)


def _detect_abandoned(html_lower: str, analysis: dict) -> bool:
    if any(sig in html_lower for sig in _ABANDONED_SIGNALS):
        return True
    issues = analysis.get("issues") or []
    abandoned_markers = (
        "veraltet",
        "Platzhalter",
        "Baustelle",
        "Kein Seitentitel",
        "HTTP ",
    )
    return any(any(m.lower() in str(i).lower() for m in abandoned_markers) for i in issues)


def _potential_eur(analysis: dict, niche: str, abandoned: bool) -> float:
    base = float((_NICHE_CATALOG.get(niche) or _NICHE_CATALOG["local_service"])["lead_value_eur"])
    score = int(analysis.get("improvement_score") or 0)
    bonus = 0.0
    if abandoned:
        bonus += 15.0
    if score < 40:
        bonus += 10.0
    traffic = _estimate_traffic_band(analysis)
    if traffic == "medium":
        bonus += 20.0
    elif traffic == "low":
        bonus += 8.0
    return round(base + bonus, 2)


class AssetScannerService:
    def __init__(self, opportunity: OpportunityService) -> None:
        self._opportunity = opportunity
        self._analyzer = SiteAnalysisService()

    def niches(self) -> list[dict[str, Any]]:
        return [
            {"id": k, "label": v["label"], "default_value_eur": v["lead_value_eur"]}
            for k, v in _NICHE_CATALOG.items()
        ]

    def dashboard(self) -> dict[str, Any]:
        rows = self._opportunity.list_opportunities(limit=200)
        assets = [r for r in rows if r.get("source_id") == "asset_scan"]
        won = [r for r in assets if r.get("status") == "won"]
        in_work = [r for r in assets if r.get("status") in ("proposed", "contacted", "qualified")]
        pipeline = [r for r in assets if r.get("status") not in ("won", "lost")]
        my_income = sum(float(r.get("revenue_eur") or 0) for r in won)
        potential = sum(float(r.get("potential_value_eur") or 0) for r in pipeline)
        return {
            "targets_found": len(assets),
            "in_work": len(in_work),
            "monetized": len(won),
            "my_income_eur": round(my_income, 2),
            "pipeline_potential_eur": round(potential, 2),
            "security_law": (
                "Только публичные URL. Запрещены ключи, пароли, закрытые системы и приватные хранилища."
            ),
            "stealth_mode": stealth_status(),
        }

    def scan_url(self, url: str, *, niche: str = "local_service") -> dict:
        assert_public_scan_allowed(url)
        analysis = self._analyzer.analyze(url)
        if analysis.get("error"):
            err = str(analysis.get("error"))
            if err in ("robots_txt_disallowed", "forbidden_target", "write_method_forbidden", "Unauthorized Operation"):
                raise ValueError(err)
            raise ValueError("fetch_failed")

        html_note = " ".join(analysis.get("issues") or [])
        abandoned = _detect_abandoned(html_note.lower(), analysis)
        potential = _potential_eur(analysis, niche, abandoned)
        rationale = _income_rationale(analysis, niche)

        host = analysis.get("final_url") or analysis.get("url") or url
        company = analysis.get("title") or host
        if len(company) > 80:
            company = company[:77] + "…"

        row = self._opportunity.create(
            {
                "source_id": "asset_scan",
                "opportunity_type": "asset",
                "company_name": company,
                "website_url": analysis.get("final_url") or url,
                "fit_reason": rationale,
                "potential_value_eur": potential,
                "score": max(40, 100 - int(analysis.get("issue_count") or 0) * 8),
                "notes": f"Трафик: {_estimate_traffic_band(analysis)} · Заброшен: {'да' if abandoned else 'нет'}",
                "meta": {
                    "niche": niche,
                    "traffic_band": _estimate_traffic_band(analysis),
                    "abandoned": abandoned,
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )
        updated = self._opportunity.update(
            row["id"],
            {"site_analysis": analysis, "status": "new"},
        )
        return updated

    def analyze_target(self, opportunity_id: str) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        url = (row.get("website_url") or "").strip()
        if not url:
            raise ValueError("url_required")
        assert_public_scan_allowed(url)
        analysis = self._analyzer.analyze(url)
        niche = str((row.get("meta") or {}).get("niche") or "local_service")
        abandoned = _detect_abandoned(" ".join(analysis.get("issues") or []).lower(), analysis)
        rationale = _income_rationale(analysis, niche)
        potential = _potential_eur(analysis, niche, abandoned)
        return self._opportunity.update(
            opportunity_id,
            {
                "site_analysis": analysis,
                "fit_reason": rationale,
                "potential_value_eur": potential,
                "score": max(int(row.get("score") or 0), 100 - int(analysis.get("issue_count") or 0) * 8),
                "status": "reviewed",
                "notes": (
                    f"Анализ {datetime.now(timezone.utc).date()} · "
                    f"Трафик: {_estimate_traffic_band(analysis)} · "
                    f"Заброшен: {'да' if abandoned else 'нет'}"
                ),
            },
        )

    def accept_for_work(self, opportunity_id: str) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        meta = dict(row.get("meta") or {})
        meta["work_started_at"] = datetime.now(timezone.utc).isoformat()
        meta["monetization"] = "pending"
        return self._opportunity.update(
            opportunity_id,
            {
                "status": "proposed",
                "meta": meta,
                "notes": (row.get("notes") or "") + "\nПринято в работу — монетизация запущена.",
            },
        )

    def record_income(self, opportunity_id: str, revenue_eur: float) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        return self._opportunity.update(
            opportunity_id,
            {
                "status": "won",
                "revenue_eur": float(revenue_eur),
            },
        )

    def list_targets(self, *, limit: int = 50) -> list[dict]:
        return self._opportunity.list_opportunities(source_id="asset_scan", limit=limit)
