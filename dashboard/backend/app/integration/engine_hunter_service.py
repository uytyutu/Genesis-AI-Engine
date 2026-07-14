"""Engine Hunter — zero-cost Hunter-Gatherer scenarios (service-first, no asset buys)."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.acquisition_studio_service import AcquisitionStudioService
from app.factory.factory_service import FactoryService
from app.integration.opportunity_service import OpportunityService
from app.integration.public_intel_miner import PatternHit, PublicIntelMiner

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_ISSUE_LANE_MAP: dict[str, tuple[str, str, float]] = {
    "kein https": ("outreach_lead", "SSL/HTTPS fehlt", 150.0),
    "kontaktformular": ("outreach_lead", "Kein Kontaktformular", 120.0),
    "seitentitel": ("seo_revival", "SEO: fehlender Title", 80.0),
    "wenig inhalt": ("seo_revival", "Toter Content — Revival", 100.0),
    "veraltet": ("bounty_report", "Veraltete Technik", 75.0),
    "baustelle": ("bounty_report", "Site wirkt abgebrochen", 60.0),
    "langsame": ("outreach_lead", "Performance-Problem", 90.0),
    "social-meta": ("seo_revival", "Schwache Social Preview", 50.0),
}

_SERVICE_LANES = frozenset({"outreach_lead", "bounty_report", "seo_revival", "dataset_row"})


class EngineHunterService:
    """Orchestrates Bug Bounty Lite, SEO revival, outreach, dataset — €0 upfront."""

    def __init__(
        self,
        opportunity: OpportunityService,
        acquisition: AcquisitionStudioService | None,
        factory: FactoryService | None,
        intel_miner: PublicIntelMiner,
        memory_dir: Path | None = None,
    ) -> None:
        self._opportunity = opportunity
        self._acquisition = acquisition
        self._factory = factory
        self._miner = intel_miner
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _hunter_config(self) -> dict[str, Any]:
        cfg = self._miner.load_pattern_config()
        policy = cfg.get("execution_policy") if isinstance(cfg.get("execution_policy"), dict) else {}
        return {
            "hunter_mode": str(cfg.get("hunter_mode") or policy.get("hunter_mode") or "service_first"),
            "zero_cost": bool(cfg.get("zero_cost", policy.get("zero_cost", True))),
            "priority": str(cfg.get("priority") or policy.get("priority") or "outreach"),
            "auto_outreach_draft": bool(policy.get("auto_outreach_draft", True)),
        }

    def mine_analysis_signals(self, opportunity: dict[str, Any]) -> list[PatternHit]:
        """Turn site_analysis issues into hunter hits — no exploit probes."""
        analysis = opportunity.get("site_analysis")
        if not isinstance(analysis, dict):
            return []
        source_url = str(opportunity.get("website_url") or "")
        hits: list[PatternHit] = []
        for issue in analysis.get("issues") or []:
            text = str(issue).lower()
            for key, (lane, label, value) in _ISSUE_LANE_MAP.items():
                if key in text:
                    hits.append(
                        PatternHit(
                            pattern_id=f"signal_{key.replace(' ', '_')}",
                            pattern_label=label,
                            matched_value=str(issue)[:80],
                            source_url=source_url,
                            context_snippet=str(issue)[:120],
                            confidence=0.85,
                            valuation_eur=value,
                            lane=lane,
                        )
                    )
                    break
        return hits

    def _seo_content_draft(self, row: dict[str, Any]) -> dict[str, Any]:
        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        company = str(row.get("company_name") or "Business")
        issues = [str(i) for i in (analysis.get("issues") or [])[:4]]
        title = analysis.get("title") or company
        draft = {
            "headline": f"{company} — aktuelle Leistungen 2026",
            "meta_description": (
                f"{company}: professionelle Services in Ihrer Region. "
                "Kontakt, Öffnungszeiten und Angebot — jetzt aktualisiert."
            )[:160],
            "article_outline": [
                f"Problem: {issues[0]}" if issues else "Veralteter Web-Auftritt",
                "Lösung: SEO-optimierte Inhalte + klare Kontaktwege",
                "Ergebnis: mehr Anfragen ohne Werbebudget",
            ],
            "revival_offer": "0 € Vorab — Provision nur bei messbarem Anstieg der Anfragen",
        }
        if self._factory and issues:
            try:
                desc = f"Landing refresh for {company}: " + "; ".join(issues[:2])
                built = self._factory.build_landing(desc[:500])
                draft["factory_product_id"] = built.get("product_id")
                draft["preview_url"] = built.get("preview_url")
            except Exception:
                draft["factory_note"] = "Factory preview deferred"
        return draft

    def _bounty_report_draft(self, row: dict[str, Any], hits: list[PatternHit]) -> dict[str, Any]:
        bounty = [h for h in hits if h.lane == "bounty_report"]
        return {
            "report_type": "responsible_disclosure_lite",
            "subject": f"Sicherheitshinweis — {row.get('company_name', 'Website')}",
            "findings": [h.matched_value for h in bounty],
            "fix_steps": [
                "HTTPS erzwingen und HSTS aktivieren",
                "CMS/Pugins aktualisieren",
                "Öffentliche Admin-Pfade schließen",
                "Kontaktformular mit Spam-Schutz",
            ],
            "estimated_bounty_eur": sum(h.valuation_eur for h in bounty) or 75.0,
            "disclaimer": "Kein Exploit — nur öffentliche Beobachtung. CEO sendet nach Approve.",
        }

    def _append_dataset_row(self, row: dict[str, Any], hits: list[PatternHit]) -> None:
        path = self._memory / "hunter_dataset.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "at": datetime.now(timezone.utc).isoformat(),
            "company": row.get("company_name", ""),
            "url": row.get("website_url", ""),
            "niche": (row.get("meta") or {}).get("niche", ""),
            "issues": (row.get("site_analysis") or {}).get("issues", [])[:5],
            "pattern_hits": [h.pattern_id for h in hits],
            "potential_eur": row.get("potential_value_eur", 0),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def run_hunter_scenarios(
        self,
        opportunity_id: str,
        regex_hits: list[PatternHit],
    ) -> dict[str, Any]:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")

        config = self._hunter_config()
        signal_hits = self.mine_analysis_signals(row)
        all_hits = regex_hits + signal_hits
        # dedupe by pattern_id + matched_value
        seen: set[str] = set()
        merged: list[PatternHit] = []
        for h in all_hits:
            key = f"{h.pattern_id}:{h.matched_value.lower()}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(h)

        meta = dict(row.get("meta") or {})
        meta["hunter_mode"] = config["hunter_mode"]
        meta["zero_cost"] = config["zero_cost"]
        meta["monetization_priority"] = config["priority"]
        meta["hunter_scenarios"] = {
            "bounty": sum(1 for h in merged if h.lane == "bounty_report"),
            "seo_revival": sum(1 for h in merged if h.lane == "seo_revival"),
            "outreach": sum(1 for h in merged if h.lane == "outreach_lead"),
            "dataset": sum(1 for h in merged if h.lane in ("dataset_row", "data_product")),
        }
        meta["hunter_value_eur"] = round(sum(h.valuation_eur for h in merged), 2)

        service_hits = [h for h in merged if h.lane in _SERVICE_LANES]
        if service_hits and config["priority"] == "outreach":
            meta["execution_status"] = "outreach_pending_approval"
            meta.pop("pending_transactions", None)

        if any(h.lane == "seo_revival" for h in merged):
            meta["seo_content_draft"] = self._seo_content_draft(row)

        if any(h.lane == "bounty_report" for h in merged):
            meta["bounty_report_draft"] = self._bounty_report_draft(row, merged)

        if any(h.lane in ("dataset_row", "data_product") for h in merged):
            self._append_dataset_row(row, merged)

        if (
            service_hits
            and config.get("auto_outreach_draft")
            and self._acquisition
            and not row.get("proposed_message")
        ):
            try:
                row = self._acquisition.prepare_opportunity(opportunity_id)
                meta["outreach_prepared"] = True
                meta["outreach_status"] = row.get("outreach_status")
            except (ValueError, OSError):
                meta["outreach_prepared"] = False

        combined_hits = self._miner.hits_to_dicts(merged)
        meta["pattern_hits"] = combined_hits
        meta["pattern_hits_count"] = len(combined_hits)

        return self._opportunity.update(opportunity_id, {"meta": meta})

    def dataset_export_csv(self) -> str:
        path = self._memory / "hunter_dataset.jsonl"
        rows = []
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=";", lineterminator="\n")
        writer.writerow(["Datum", "Firma", "URL", "Nische", "Issues", "Patterns", "Potential_EUR"])
        for r in rows:
            writer.writerow(
                [
                    (r.get("at") or "")[:10],
                    r.get("company", ""),
                    r.get("url", ""),
                    r.get("niche", ""),
                    " | ".join(r.get("issues") or [])[:200],
                    " | ".join(r.get("pattern_hits") or []),
                    f"{float(r.get('potential_eur') or 0):.2f}".replace(".", ","),
                ]
            )
        return buf.getvalue()

    def hunter_dashboard(self) -> dict[str, Any]:
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        cfg = self._hunter_config()
        stats = {"bounty": 0, "seo_revival": 0, "outreach": 0, "dataset": 0, "outreach_ready": 0}
        value = 0.0
        for row in rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            sc = meta.get("hunter_scenarios") if isinstance(meta.get("hunter_scenarios"), dict) else {}
            for k in ("bounty", "seo_revival", "outreach", "dataset"):
                stats[k] += int(sc.get(k) or 0)
            value += float(meta.get("hunter_value_eur") or 0)
            if meta.get("outreach_prepared") or row.get("outreach_status") == "pending_approval":
                stats["outreach_ready"] += 1
        dataset_rows = 0
        ds_path = self._memory / "hunter_dataset.jsonl"
        if ds_path.is_file():
            dataset_rows = sum(1 for ln in ds_path.read_text(encoding="utf-8").splitlines() if ln.strip())
        return {
            "mode": cfg["hunter_mode"],
            "zero_cost": cfg["zero_cost"],
            "priority": cfg["priority"],
            "scenario_stats": stats,
            "hunter_value_eur": round(value, 2),
            "dataset_rows": dataset_rows,
            "note": "Hunter-Gatherer: Outreach/SEO/Bounty/Dataset — ohne Kauf von Assets.",
        }
