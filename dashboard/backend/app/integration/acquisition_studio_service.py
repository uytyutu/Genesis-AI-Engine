"""Mission 1.5 — Business Acquisition Studio Foundation.

Plan → Approve → Act. Prepares sales cycle; never sends without CEO approval.
"""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from app.integration.receipt_email_service import ReceiptEmailService
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.site_analysis_service import SiteAnalysisService
from app.integration.google_places_service import GooglePlacesService
from app.integration.outreach_language_service import OutreachLanguageService
from app.integration.global_exclusion import GlobalExclusionService
from app.integration.outreach_send_quota import OutreachSendQuota, outreach_daily_cap
from app.integration.pilot_service_catalog import (
    ceo_catalog_snapshot,
    suggest_services_for_signals,
    suggest_services_for_site_issues,
)


# Services Genesis can offer today (dogfood-first — public catalog only when True).
_SERVICE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "landing_basic",
        "category": "web",
        "name": "Landing Page Basic",
        "package_id": "basic",
        "price_eur": 350,
        "dogfood": True,
        "public": True,
        "note": "Fertige Seite + ZIP + Selbst-Publish-Anleitung",
    },
    {
        "id": "landing_business",
        "category": "web",
        "name": "Landing Page Business",
        "package_id": "business",
        "price_eur": 650,
        "dogfood": True,
        "public": True,
        "note": "Fertige Seite + Hilfe beim Upload (Domain/Hosting zahlt Kunde)",
    },
    {
        "id": "landing_premium",
        "category": "web",
        "name": "Landing Page Premium",
        "package_id": "premium",
        "price_eur": 1200,
        "dogfood": True,
        "public": True,
        "note": "Fertige Seite + Voll-Veröffentlichung (Setup, kein Hosting-Abo)",
    },
    {
        "id": "site_audit",
        "category": "consulting",
        "name": "Website Audit",
        "package_id": None,
        "price_eur": 79,
        "dogfood": True,
        "public": True,
        "note": "Pilot-Anfrage — Bericht + Angebot (kein Auto-Checkout)",
        "pilot_service_id": "website_audit",
    },
    {
        "id": "site_boost",
        "category": "web",
        "name": "Site Boost",
        "package_id": None,
        "price_eur": 149,
        "dogfood": True,
        "public": True,
        "note": "Pilot-Anfrage — WhatsApp/Maps/SEO am bestehenden Auftritt",
        "pilot_service_id": "site_boost",
    },
    {
        "id": "seo_audit",
        "category": "consulting",
        "name": "SEO Audit",
        "package_id": None,
        "price_eur": 99,
        "dogfood": True,
        "public": True,
        "note": "Pilot-Anfrage — technisches SEO",
        "pilot_service_id": "seo_audit",
    },
    {
        "id": "google_business_setup",
        "category": "local",
        "name": "Google Business Setup",
        "package_id": None,
        "price_eur": 129,
        "dogfood": True,
        "public": True,
        "note": "Pilot-Anfrage — Profil / Bewertungen",
        "pilot_service_id": "google_business_setup",
    },
]

_ACQUISITION_CHANNELS = [
    {"id": "weak_website", "label": "Слабый / нет сайта", "source": 1},
    {"id": "marketplace_request", "label": "Запрос на площадке", "source": 2},
    {"id": "inbound", "label": "Входящая заявка", "source": 3},
    {"id": "repeat_client", "label": "Повторный клиент", "source": 4},
    {"id": "partner", "label": "Партнёрство", "source": 5},
]

_SKIP_OUTREACH_DOMAINS = frozenset(
    {
        "wikipedia.org",
        "www.wikipedia.org",
        "python.org",
        "www.python.org",
        "mozilla.org",
        "www.mozilla.org",
        "debian.org",
        "www.debian.org",
        "nginx.com",
        "www.nginx.com",
        "cloudflare.com",
        "www.cloudflare.com",
        "f5.com",
        "www.f5.com",
        "example.com",
        "www.example.com",
        "google.com",
        "facebook.com",
        "github.com",
        "apache.org",
    }
)

# Country Desk price lanes (Mission 1): auto-draft ≤50€; above → manual_review.
# Auto-send remains gated by GENESIS_OUTREACH_ENABLED + Impressum (never by this tier alone).
AUTO_DRAFT_MAX_EUR = 50.0
# High win: queue for Approve even if price > 50€. Confirm (≥) marks approved without send unless outreach on.
HIGH_WIN_AUTO_QUEUE_PCT = 65
HIGH_WIN_AUTO_CONFIRM_PCT = 75
QUALITY_ARCHIVE_FILE = "quality_archive.jsonl"

# Structured market lessons (Evidence First) — reason code + optional CEO comment.
MARKET_REASON_LABELS_RU: dict[str, str] = {
    "subject_weak": "Тема письма",
    "offer_miss": "Оффер",
    "price": "Цена",
    "not_relevant": "Неактуально",
    "has_vendor": "Уже есть подрядчик",
    "no_budget": "Нет бюджета",
    "no_reply": "Не удалось связаться / нет ответа",
    "interested": "Заинтересовались",
    "other": "Другое",
}
MARKET_OUTCOME_EVENTS = frozenset({"replied", "qualified", "won", "lost", "no_reply"})

_SEGMENT_SIGNALS = [
    "нет сайта",
    "http://",
    "kein HTTPS",
    "nur Facebook",
    "Gelbe Seiten без сайта",
    "устаревший дизайн",
]


class AcquisitionStudioService:
    def __init__(self, opportunity_service: object, sales_service: object) -> None:
        self._opportunity = opportunity_service
        self._sales = sales_service
        mem = getattr(opportunity_service, "memory_dir", None)
        self._memory_dir = mem
        self._site = SiteAnalysisService(memory_dir=mem)
        self._email = ReceiptEmailService(memory_dir=mem)
        self._places = GooglePlacesService()
        self._outreach_lang = OutreachLanguageService()
        self._exclusion = GlobalExclusionService(opportunity_service)
        self._send_quota = OutreachSendQuota(mem)
        from app.integration.outreach_adaptive_service import OutreachAdaptiveService

        self._adaptive = OutreachAdaptiveService(mem)
        self._runner = None

    def _get_runner(self):
        if self._runner is None:
            from app.integration.outreach_runner_service import OutreachRunnerService

            self._runner = OutreachRunnerService(
                self._memory_dir,
                refresh_fn=self.refresh_country_desk_leads,
                send_next_fn=self.send_next_quality_lead,
                interval_fn=self._adaptive.effective_interval_sec,
            )
        return self._runner

    def archive_stale_pipeline_for_fresh_run(self) -> dict[str, Any]:
        """Hide old visible leads so Start shows a clean multi-market queue.

        Does not delete history — quality_archive only. Sent/won/lost stay visible
        for analytics; pending/none/manual_review/approved draft noise is parked.
        """
        archived = 0
        kept_sent = 0
        for row in self._opportunity._load_rows():
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            status = str(row.get("status") or "")
            outreach = str(row.get("outreach_status") or "")
            if status in ("won", "lost") or outreach == "sent":
                kept_sent += 1
                continue
            self._archive_quality(
                row,
                reason="fresh_multi_market_start",
                detail="Скрыто при Пуске · старый список; страны крутятся заново",
            )
            archived += 1
        return {
            "ok": True,
            "archived": archived,
            "kept_sent_or_closed": kept_sent,
            "message_ru": (
                f"Список очищен для нового пуска: скрыто {archived}, "
                f"оставлено отправленных/закрытых {kept_sent}"
            ),
        }

    def runner_start(self) -> dict[str, Any]:
        cleared = self.archive_stale_pipeline_for_fresh_run()
        status = self._get_runner().start()
        status["pipeline_cleared"] = cleared
        status["last_message_ru"] = (
            f"{status.get('last_message_ru') or 'Пуск'} · "
            f"старые лиды скрыты ({cleared.get('archived', 0)}) · "
            "hunt round-robin по всем странам до лимитов"
        )
        return status

    def runner_stop(self) -> dict[str, Any]:
        return self._get_runner().stop()

    def runner_status(self) -> dict[str, Any]:
        return self._get_runner().status()

    def runner_tick(self) -> dict[str, Any]:
        return self._get_runner().tick()

    def send_next_quality_lead(self) -> dict[str, Any]:
        """Send one quality lead if outreach enabled — any market, never force-fill."""
        from app.integration.outreach_ceo_prefs import outreach_send_allowed

        outreach_enabled = outreach_send_allowed(self._memory_dir)
        if not outreach_enabled:
            return {
                "sent": False,
                "skipped": True,
                "reason": "outreach_disabled",
                "message_ru": "Отправка выкл. (тумблер Автоотправка / GENESIS_OUTREACH_ENABLED) — только hunt/draft",
            }
        rows = self._opportunity._load_rows()
        candidates: list[tuple[int, int, dict]] = []
        for row in rows:
            status = str(row.get("outreach_status") or "")
            if status not in ("approved", "pending_approval"):
                continue
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            if not self._extract_email(row.get("contact", "")):
                continue
            if not row.get("proposed_message"):
                continue
            # Skip if another opportunity already used this email/host (sent/contacted).
            oid = str(row.get("id") or "")
            email = self._extract_email(str(row.get("contact") or "")).lower()
            host = self._normalize_host(str(row.get("website_url") or ""))
            peer_busy = False
            for other in rows:
                if str(other.get("id") or "") == oid:
                    continue
                o_status = str(other.get("status") or "")
                o_out = str(other.get("outreach_status") or "")
                if o_status not in ("contacted", "won") and o_out not in ("sent", "contacted"):
                    continue
                o_email = self._extract_email(str(other.get("contact") or "")).lower()
                o_host = self._normalize_host(str(other.get("website_url") or ""))
                if (email and o_email == email) or (host and o_host == host):
                    peer_busy = True
                    break
            if peer_busy:
                continue
            win = int(meta.get("win_probability_pct") or 0)
            score = int(row.get("score") or 0)
            if status == "pending_approval" and win < HIGH_WIN_AUTO_CONFIRM_PCT:
                continue
            tier = 2 if status == "approved" else 1
            candidates.append((tier, win * 1000 + score, row))
        if not candidates:
            return {
                "sent": False,
                "skipped": True,
                "reason": "no_quality_leads",
                "message_ru": "Нет качественных лидов к отправке — квоту не заполняем",
            }
        candidates.sort(key=lambda t: (-t[0], -t[1]))
        row = candidates[0][2]
        oid = str(row.get("id") or "")
        if str(row.get("outreach_status")) == "approved":
            row["outreach_status"] = "pending_approval"
            self._opportunity._save_rows(self._replace_row(oid, row))
        try:
            result = self.approve_outreach(oid)
        except ValueError as exc:
            return {
                "sent": False,
                "skipped": True,
                "reason": str(exc),
                "message_ru": f"Пропуск: {exc}",
                "company": row.get("company_name"),
            }
        sent = bool(
            result.get("sent")
            or result.get("outreach_status") == "sent"
            or (isinstance(result.get("send"), dict) and result["send"].get("ok"))
        )
        return {
            "sent": sent,
            "skipped": not sent,
            "company": row.get("company_name"),
            "to": self._extract_email(row.get("contact", "")),
            "result": result,
            "message_ru": (
                f"Отправлено: {row.get('company_name')}"
                if sent
                else str(
                    (result.get("send") or {}).get("reason")
                    or result.get("message")
                    or result.get("reason")
                    or "не отправлено (квота/ошибка)"
                )
            ),
        }

    def _hunt(self) -> dict[str, Any]:
        from app.integration.global_spider_service import GlobalSpiderService

        return GlobalSpiderService(self._memory_dir).hunting_target()

    def _daily_segments(self) -> list[dict[str, Any]]:
        hunt = self._hunt()
        city = hunt["target_city"]
        niches = hunt["profitable_niches"]
        return [
            {
                "id": str(niche).casefold().replace(" ", "_")[:48],
                "label": niche,
                "cities": [city],
                "signals": list(_SEGMENT_SIGNALS),
            }
            for niche in niches
        ]

    def gate_funnel(self) -> dict[str, Any]:
        from app.integration.lead_pipeline_service import gate_funnel_metrics

        return gate_funnel_metrics(self._opportunity, memory_dir=self._memory_dir)

    def markets_dashboard(self) -> dict[str, Any]:
        """CEO table: country · limit · sent · replies · orders (config-driven)."""
        from app.integration.outreach_market_config import list_markets, outreach_markets_config

        health = self._send_quota.health()
        by_sent = {
            str(r.get("code") or "").upper(): r
            for r in (health.get("markets") or [])
            if isinstance(r, dict)
        }
        rows = self._opportunity._load_rows()
        replies: dict[str, int] = {}
        orders: dict[str, int] = {}
        for row in rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            code = str(
                meta.get("market") or row.get("market") or meta.get("country_code") or ""
            ).upper()
            if not code:
                continue
            status = str(row.get("status") or "")
            outreach = str(row.get("outreach_status") or "")
            if status in ("replied", "qualified", "negotiation") or outreach == "replied":
                replies[code] = replies.get(code, 0) + 1
            # interaction log may mark reply
            for ev in row.get("interactions") or []:
                if isinstance(ev, dict) and str(ev.get("event") or "") in (
                    "replied",
                    "reply",
                    "positive_reply",
                ):
                    replies[code] = replies.get(code, 0) + 1
                    break
            if status == "won" or float(row.get("revenue_eur") or 0) > 0:
                orders[code] = orders.get(code, 0) + 1

        table = []
        for m in list_markets():
            code = str(m.get("code") or "").upper()
            snap = by_sent.get(code) or {}
            currency = str(m.get("currency") or "EUR")
            symbol = str(m.get("symbol") or "€")
            basic_label = ""
            business_label = ""
            premium_label = ""
            try:
                from app.integration.commerce_engine import resolve_final_offer
                from app.integration.market_registry import get_market as get_commerce

                cm = get_commerce(code)
                if cm and cm.currency:
                    currency = str(cm.currency)
                    symbol = str(cm.symbol or symbol)
                for pid, dest in (
                    ("basic", "basic"),
                    ("business", "business"),
                    ("premium", "premium"),
                ):
                    offer = resolve_final_offer(pid, code)
                    label = str(offer.price_label or f"{offer.amount:.0f} {offer.symbol}")
                    if pid == "basic":
                        basic_label = label
                        currency = str(offer.currency or currency)
                        symbol = str(offer.symbol or symbol)
                    elif pid == "business":
                        business_label = label
                    else:
                        premium_label = label
            except Exception:
                pass
            table.append(
                {
                    "code": code,
                    "flag": m.get("flag") or "",
                    "name_ru": m.get("name_ru") or code,
                    "enabled": bool(m.get("enabled")),
                    "phase": int(m.get("phase") or 0),
                    "daily_cap": int(
                        snap.get("daily_cap")
                        or self._adaptive.effective_daily_cap(code)
                        or m.get("daily_cap")
                        or 0
                    ),
                    "sent_today": int(snap.get("used_today") or 0),
                    "replies": int(replies.get(code, 0)),
                    "orders": int(orders.get(code, 0)),
                    "currency": currency,
                    "symbol": symbol,
                    "basic_price_label": basic_label,
                    "business_price_label": business_label,
                    "premium_price_label": premium_label,
                    "hubs": m.get("hubs") or [],
                    "timezone": m.get("timezone"),
                    "language": m.get("language"),
                    "legal_profile": m.get("legal_profile"),
                }
            )
        cfg = outreach_markets_config()
        return {
            "ok": True,
            "note_ru": cfg.get("note_ru") or "",
            "allocation_mode": cfg.get("allocation_mode") or "shared_global",
            "quality_first": bool(cfg.get("quality_first", True)),
            "force_fill_quotas": bool(cfg.get("force_fill_quotas", False)),
            "global_daily_cap": health.get("global_daily_cap"),
            "min_interval_sec": health.get("min_interval_sec"),
            "sent_today_total": health.get("sent_today_total"),
            "remaining_today_total": health.get("remaining_today_total"),
            "table": table,
            "enabled_count": sum(1 for t in table if t["enabled"]),
            "planned_count": sum(1 for t in table if not t["enabled"]),
        }

    def studio_status(self) -> dict:
        from app.integration.outreach_ceo_prefs import load_prefs, outreach_send_allowed

        rows = self._opportunity._load_rows()
        pending = sum(1 for r in rows if r.get("outreach_status") == "pending_approval")
        manual = sum(1 for r in rows if r.get("outreach_status") == "manual_review")
        sent = sum(1 for r in rows if r.get("outreach_status") == "sent")
        prefs = load_prefs(self._memory_dir)
        outreach_enabled = outreach_send_allowed(self._memory_dir)
        return {
            "version": "1.5-foundation",
            "name": "Country Desk · DE",
            "auto_search": False,
            "auto_refresh": bool(prefs.get("auto_refresh")),
            "auto_send": bool(prefs.get("auto_send")),
            "outreach_send_enabled": outreach_enabled,
            "outreach_send_note": (
                "Автоотправка: тумблер CEO или GENESIS_OUTREACH_ENABLED=true + Resend + "
                "Impressum/Abmelde. Ответственность за рассылку — у отправителя."
            ),
            "law": "Plan → Approve → Act",
            "pending_approval_count": pending,
            "manual_review_count": manual,
            "auto_draft_max_eur": AUTO_DRAFT_MAX_EUR,
            "sent_count": sent,
            "pipeline_count": sum(
                1 for r in rows if r.get("status") not in ("won", "lost")
            ),
            "channels": _ACQUISITION_CHANNELS,
            "pilot_catalog": ceo_catalog_snapshot(),
            "outreach_daily_cap": outreach_daily_cap(),
            "outreach_quota": self._send_quota.health(),
            "markets_dashboard": self.markets_dashboard(),
            "adaptive_outreach": self.adaptive_dashboard(auto_review=True),
            "outreach_runner": self.runner_status(),
        }

    def set_ceo_prefs(
        self, *, auto_refresh: bool | None = None, auto_send: bool | None = None
    ) -> dict:
        from app.integration.outreach_ceo_prefs import save_prefs

        prefs = save_prefs(
            self._memory_dir, auto_refresh=auto_refresh, auto_send=auto_send
        )
        # Never auto-start the market here — only CEO «Пуск» starts the runner.
        return {
            **prefs,
            "outreach_send_enabled": bool(prefs.get("auto_send"))
            or (
                __import__("os").getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower()
                == "true"
            ),
            "note_ru": "Рынок стартует только кнопкой Пуск. Автообновление действует после Пуска.",
        }

    def adaptive_dashboard(self, *, auto_review: bool = False) -> dict[str, Any]:
        rows = self._opportunity._load_rows()
        if auto_review and self._adaptive.review_due():
            self._adaptive.run_weekly_review(rows, force=False, apply=True)
        return self._adaptive.dashboard(rows)

    def run_adaptive_review(self, *, force: bool = True, apply: bool = True) -> dict[str, Any]:
        rows = self._opportunity._load_rows()
        return self._adaptive.run_weekly_review(rows, force=force, apply=apply)

    def catalog(self, *, public_only: bool = False) -> dict:
        items = _SERVICE_CATALOG
        if public_only:
            items = [i for i in items if i.get("public")]
        return {
            "principle": (
                f"Услуга в публичном каталоге только если {BRAND_NAME} умеет выполнять и dogfood. "
                "Checkout online: Landing /order. Übrige Pilot-Leistungen = Anfrage."
            ),
            "services": items,
            "pilot": ceo_catalog_snapshot(),
            "suggest_example": suggest_services_for_signals(
                ["no_whatsapp", "no_https", "poor_seo"]
            ),
        }

    def analyze_site(self, url: str) -> dict:
        return self._site.analyze(url)

    def daily_worklist(self) -> dict:
        hunt = self._hunt()
        return {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "mode": "config_locked",
            "note": (
                f"Локация из config: {hunt['target_city']} · радиус {hunt['search_radius']} м · "
                f"ниши: {', '.join(hunt['profitable_niches'][:5])}. "
                f"{BRAND_NAME} берёт город и ниши из global_spider_config.json."
            ),
            "target_city": hunt["target_city"],
            "search_radius": hunt["search_radius"],
            "profitable_niches": hunt["profitable_niches"],
            "target_per_day": 8,
            "target_per_day_note_ru": "Снайпер: 5–10 писем/день на старт (не массовая рассылка)",
            "outreach_daily_cap": outreach_daily_cap(),
            "outreach_quota": self._send_quota.health(),
            "segments": self._daily_segments(),
            "sources_disabled": [
                s["id"]
                for s in self._opportunity.list_sources()
                if not s.get("enabled") or not s.get("auto_search")
            ],
        }

    def generate_drafts_from_places(
        self,
        *,
        city: str,
        query: str,
        limit: int = 10,
        language: str = "de",
        throttle_ms: int = 250,
        force_skip_check: bool = False,
        market_code: str | None = None,
        search_region: str | None = None,
    ) -> dict:
        """CEO-triggered vertical slice:
        Places search → upsert opportunities (place_id) → draft outreach.

        By default drafts only leads without a website. With force_skip_check=true
        CEO can draft improvement proposals even when a website exists.
        Empty city → locked target_city from global_spider_config.json.
        """
        if not self._places.configured():
            raise ValueError("places_not_configured")
        hunt = self._hunt()
        city = (city or "").strip() or hunt["target_city"]
        query = query.strip()
        market = (market_code or "").strip().upper() or None
        region = (search_region or hunt.get("search_region") or "de").strip().lower()
        if not city or not query:
            raise ValueError("invalid_query")
        from app.integration.global_spider_service import _city_coords

        coords = _city_coords(city)
        try:
            leads = self._places.search_text(
                query=f"{query} {city}",
                language=language,
                region=region,
                limit=limit,
                throttle_ms=throttle_ms,
                lat=coords[0] if coords else None,
                lng=coords[1] if coords else None,
                radius_m=hunt["search_radius"],
            )
        except RuntimeError as exc:
            raise ValueError(str(exc).replace("places_textsearch_status:", "places_error:")) from exc

        created = 0
        drafted = 0
        skipped_has_site = 0
        skipped_already_queued = 0
        skipped_excluded = 0
        skipped_dup = 0
        duplicates = 0
        blocked = 0

        from app.integration.lead_pipeline_service import ingest_lead

        all_rows = self._opportunity.list_opportunities(limit=500)
        busy_emails, busy_hosts = self._pipeline_busy_keys(all_rows)

        for lead in leads:
            result = ingest_lead(
                self._opportunity,
                {
                    "source_id": "google_maps",
                    "opportunity_type": "lead",
                    "company_name": lead.name,
                    "contact": "",
                    "website_url": lead.website or "",
                    "fit_reason": "Google Places: нет сайта или слабый сайт",
                    "query": query,
                    "meta": {
                        "place_id": lead.place_id,
                        "address": lead.address,
                        "types": lead.types,
                        "market": market,
                        "hunt_city": city,
                        "hunt_query": query,
                    },
                },
            )
            if result.get("blocked"):
                blocked += 1
                continue
            if result.get("duplicate"):
                duplicates += 1
            elif result.get("created"):
                created += 1
            row = result.get("row")
            if not row:
                continue

            if market:
                meta = dict(row.get("meta") or {})
                if meta.get("market") != market or meta.get("hunt_city") != city:
                    meta["market"] = market
                    meta["hunt_city"] = city
                    meta["hunt_query"] = query
                    row["meta"] = meta
                    row["market"] = market
                    self._opportunity._save_rows(self._replace_row(str(row["id"]), row))

            excluded, _reason = self._exclusion.check(
                email=str(row.get("contact") or ""),
                website_url=str(row.get("website_url") or lead.website or ""),
                exclude_id=str(row.get("id") or ""),
            )
            if excluded:
                skipped_excluded += 1
                continue

            if self._is_pipeline_duplicate(
                row, busy_emails=busy_emails, busy_hosts=busy_hosts
            ):
                skipped_dup += 1
                duplicates += 1
                continue

            has_site = bool(str(row.get("website_url") or "").strip())
            if has_site and not force_skip_check:
                skipped_has_site += 1
                continue

            if row.get("outreach_status") == "pending_approval" and row.get("proposed_message"):
                skipped_already_queued += 1
                continue

            if has_site and force_skip_check:
                self._opportunity.update(
                    row["id"],
                    {"fit_reason": "CEO force: сайт есть — предложим улучшение онлайн-присутствия"},
                )

            website = str(row.get("website_url") or "").strip() or None
            try:
                self.prepare_opportunity(
                    row["id"],
                    website_url=website,
                    auto_lane=True,
                    skip_qualification=force_skip_check,
                )
                drafted += 1
                email = self._extract_email(str(row.get("contact") or "")).lower()
                if email:
                    busy_emails.add(email)
                host = self._normalize_host(str(row.get("website_url") or lead.website or ""))
                if host:
                    busy_hosts.add(host)
            except ValueError:
                continue

        return {
            "ok": True,
            "leads_found": len(leads),
            "created": created,
            "drafted": drafted,
            "duplicates": duplicates,
            "skipped_dup": skipped_dup,
            "blocked": blocked,
            "skipped_has_site": skipped_has_site,
            "skipped_already_queued": skipped_already_queued,
            "skipped_excluded": skipped_excluded,
            "force_skip_check": force_skip_check,
            "city": city,
            "market_code": market,
            "search_region": region,
            "search_radius": hunt["search_radius"],
            "results": [l.__dict__ for l in leads],
        }

    def prepare_opportunity(
        self,
        opportunity_id: str,
        *,
        website_url: str | None = None,
        skip_qualification: bool = False,
        auto_lane: bool = False,
    ) -> dict:
        from app.integration.lead_qualification_gate import (
            build_audit_report_md,
            qualify_lead,
        )
        from app.integration.opportunity_discovery_engine import evaluate_opportunity

        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")

        url = (website_url or row.get("website_url") or "").strip()
        analysis: dict | None = None
        if url:
            analysis = self._site.analyze(url)
            row["website_url"] = url
            row["site_analysis"] = analysis

        all_rows = self._opportunity.list_opportunities(limit=500)
        evaluation = evaluate_opportunity(row, all_rows=all_rows)

        if not skip_qualification:
            qual = qualify_lead(row, analysis, evaluation=evaluation)
            meta = dict(row.get("meta") or {})
            meta["qualification"] = qual
            if not qual["passed"]:
                meta["qualification_blocked_at"] = datetime.now(timezone.utc).isoformat()
                row["meta"] = meta
                row["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._log_interaction(
                    row,
                    "qualification_failed",
                    "; ".join(qual["blockers_ru"]) or "квалификация не пройдена",
                )
                self._opportunity._save_rows(self._replace_row(opportunity_id, row))
                raise ValueError("qualification_failed")

            channels = qual["channels"]
            if channels.get("primary_email") and not self._extract_email(row.get("contact", "")):
                row["contact"] = channels["primary_email"]

        package_id, price, rationale = self._recommend_pricing(row, analysis)
        from app.integration.outreach_language_service import resolve_market_from_row

        market = resolve_market_from_row(row) or "DE"
        currency = "EUR"
        symbol = "€"
        price_label = f"{price:.0f} €"
        try:
            from app.integration.commerce_engine import resolve_final_offer

            offer = resolve_final_offer(package_id, market)
            _names = {
                "basic": "Landing Basic",
                "business": "Landing Business",
                "premium": "Landing Premium",
            }
            package = {
                "id": package_id,
                "name": _names.get(package_id, str(package_id)),
                "price_eur": float(offer.amount),
                "price_label": offer.price_label,
                "currency": offer.currency,
                "symbol": offer.symbol,
                "market_code": offer.market_code,
            }
            price = float(offer.amount)
            currency = str(offer.currency or "EUR")
            symbol = str(offer.symbol or "€")
            price_label = str(offer.price_label or price_label)
        except Exception:
            packages = {
                p["id"]: p for p in self._sales.packages(market_code=market)
            }
            package = dict(packages.get(package_id, packages["basic"]))
            currency = str(package.get("currency") or "EUR")
            symbol = str(package.get("symbol") or "€")
            price_label = str(
                package.get("price_label") or f"{price:.0f} {symbol}"
            ).strip()
            package.setdefault("price_label", price_label)
            package.setdefault("currency", currency)
            package.setdefault("symbol", symbol)
            package.setdefault("market_code", market)
            if package.get("price_eur") is not None:
                price = float(package["price_eur"])

        audit_md = build_audit_report_md(
            row,
            analysis,
            service_label=str(evaluation.get("service_label_ru") or package.get("name") or "Аудит"),
            price_eur=float(price),
            price_label=price_label,
            win_pct=int(evaluation.get("win_probability_pct") or 0),
        )

        subject, body, lang = self._outreach_lang.draft_outreach(
            company=row.get("company_name", ""),
            analysis=analysis,
            package=package,
            price=price,
            fit_reason=row.get("fit_reason", ""),
            row=row,
        )

        meta = dict(row.get("meta") or {})
        meta["outreach_language"] = lang
        meta["market"] = market
        row["market"] = market
        meta["qualification"] = qualify_lead(row, analysis, evaluation=evaluation)
        meta["audit_report_md"] = audit_md
        meta["product_type"] = "site_audit_report"
        meta["recommended_currency"] = currency
        meta["recommended_symbol"] = symbol
        meta["recommended_price_label"] = price_label
        row["meta"] = meta

        now = datetime.now(timezone.utc).isoformat()
        row["recommended_package_id"] = package_id
        # Local-market amount (field name historical; not always EUR).
        row["recommended_price_eur"] = price
        row["recommended_currency"] = currency
        row["recommended_symbol"] = symbol
        row["recommended_price_label"] = price_label
        row["pricing_rationale"] = rationale
        row["potential_value_eur"] = price
        row["email_subject"] = subject
        row["proposed_message"] = body
        # Tier + high-win override:
        # - CEO prepare → always pending_approval
        # - auto + win≥65 → pending_approval (even if price > 50)
        # - auto + price>50 + win<65 → manual_review
        # - auto + price≤50 → pending_approval
        price_f = float(price or 0)
        win_pct = int(evaluation.get("win_probability_pct") or 0)
        meta["win_probability_pct"] = win_pct
        if auto_lane and win_pct >= HIGH_WIN_AUTO_QUEUE_PCT:
            row["outreach_status"] = "pending_approval"
            lane = "high_win_auto_queue"
        elif auto_lane and price_f > AUTO_DRAFT_MAX_EUR:
            row["outreach_status"] = "manual_review"
            lane = "manual_review"
        else:
            row["outreach_status"] = "pending_approval"
            lane = "auto_draft" if (auto_lane and price_f <= AUTO_DRAFT_MAX_EUR) else "ceo_prepare"
        meta["price_tier"] = lane
        meta["auto_draft_max_eur"] = AUTO_DRAFT_MAX_EUR
        meta["high_win_auto_queue_pct"] = HIGH_WIN_AUTO_QUEUE_PCT
        row["meta"] = meta
        row["status"] = "proposed"
        row["status_label"] = (
            f"Ручная проверка (цена > {AUTO_DRAFT_MAX_EUR:.0f} {symbol})"
            if row["outreach_status"] == "manual_review"
            else (
                f"Высокий win {win_pct}% · в Approve"
                if lane == "high_win_auto_queue"
                else "Предложение готово"
            )
        )
        row["score"] = self._refresh_score(row, analysis)
        row["updated_at"] = now
        self._log_interaction(
            row,
            "prepared",
            f"КП и письмо · lane={lane} · {price_label} · win={win_pct}%",
        )
        self._opportunity._save_rows(self._replace_row(opportunity_id, row))
        return row

    def _domain_blocked(self, url: str) -> bool:
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host in _SKIP_OUTREACH_DOMAINS or not host

    def _normalize_host(self, url: str) -> str:
        from urllib.parse import urlparse

        host = urlparse(str(url or "").strip()).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    _PIPELINE_BUSY = frozenset(
        {"sent", "contacted", "approved", "pending_approval"}
    )

    def _pipeline_busy_keys(self, rows: list[dict], *, exclude_id: str = "") -> tuple[set[str], set[str]]:
        """Emails and hosts already in outreach pipeline — do not re-offer."""
        emails: set[str] = set()
        hosts: set[str] = set()
        for row in rows:
            oid = str(row.get("id") or "")
            if exclude_id and oid == exclude_id:
                continue
            status = str(row.get("status") or "")
            outreach = str(row.get("outreach_status") or "")
            if status not in ("contacted", "won") and outreach not in self._PIPELINE_BUSY:
                continue
            email = self._extract_email(str(row.get("contact") or "")).lower()
            if email:
                emails.add(email)
            host = self._normalize_host(str(row.get("website_url") or ""))
            if host:
                hosts.add(host)
        return emails, hosts

    def _is_pipeline_duplicate(
        self,
        row: dict,
        *,
        busy_emails: set[str],
        busy_hosts: set[str],
    ) -> bool:
        email = self._extract_email(str(row.get("contact") or "")).lower()
        if email and email in busy_emails:
            return True
        host = self._normalize_host(str(row.get("website_url") or ""))
        if host and host in busy_hosts:
            return True
        return False

    def auto_prepare_discovery_leads(
        self,
        *,
        limit: int = 3,
        min_score: int = 50,
        min_win_pct: int = 55,
    ) -> dict[str, Any]:
        """After farm spider — draft outreach for top B2B leads (CEO still approves send)."""
        from app.integration.opportunity_discovery_engine import evaluate_opportunity

        rows = self._opportunity.list_opportunities(limit=200)
        candidates: list[tuple[int, dict]] = []
        archived = 0
        skipped_dup = 0
        busy_emails, busy_hosts = self._pipeline_busy_keys(rows)

        for row in rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            if row.get("status") in ("won", "lost", "contacted"):
                continue
            if row.get("outreach_status") in (
                "pending_approval",
                "sent",
                "approved",
                "manual_review",
            ):
                continue
            if row.get("proposed_message"):
                continue
            if self._is_pipeline_duplicate(
                row, busy_emails=busy_emails, busy_hosts=busy_hosts
            ):
                skipped_dup += 1
                continue
            url = str(row.get("website_url") or "").strip()
            if not url or self._domain_blocked(url):
                continue
            excluded, _reason = self._exclusion.check(
                email=str(row.get("contact") or ""),
                website_url=url,
                exclude_id=str(row.get("id") or ""),
            )
            if excluded:
                continue
            score = int(row.get("score") or 0)
            if score < min_score:
                self._archive_quality(
                    row,
                    reason="low_score",
                    detail=f"score {score} < {min_score}",
                )
                archived += 1
                continue
            ev = evaluate_opportunity(row, all_rows=rows)
            win_pct = int(ev.get("win_probability_pct") or 0)
            if win_pct < min_win_pct:
                self._archive_quality(
                    row,
                    reason="low_win_probability",
                    detail=f"win {win_pct}% < {min_win_pct}%",
                    win_pct=win_pct,
                )
                archived += 1
                continue
            if not ev.get("legal_gate", {}).get("legal", True):
                self._archive_quality(
                    row,
                    reason="legal_gate",
                    detail="legal_gate failed",
                    win_pct=win_pct,
                )
                archived += 1
                continue
            candidates.append((win_pct, row))

        candidates.sort(key=lambda x: (-x[0], -int(x[1].get("score") or 0)))
        prepared: list[str] = []
        manual_review: list[str] = []
        skipped_qual: list[str] = []
        errors: list[str] = []

        for _, row in candidates[: max(1, limit)]:
            try:
                updated = self.prepare_opportunity(
                    row["id"],
                    website_url=row.get("website_url"),
                    auto_lane=True,
                )
                name = str(updated.get("company_name") or row.get("company_name") or row["id"])
                if updated.get("outreach_status") == "manual_review":
                    manual_review.append(name)
                else:
                    prepared.append(name)
                email = self._extract_email(str(updated.get("contact") or "")).lower()
                if email:
                    busy_emails.add(email)
                host = self._normalize_host(str(updated.get("website_url") or ""))
                if host:
                    busy_hosts.add(host)
            except ValueError as exc:
                if str(exc) == "qualification_failed":
                    skipped_qual.append(str(row.get("company_name") or row["id"]))
                else:
                    errors.append(f"{row.get('company_name')}: {exc}"[:80])
            except Exception as exc:
                errors.append(f"{row.get('company_name')}: {exc}"[:80])

        return {
            "ok": True,
            "scanned": len(rows),
            "candidates": len(candidates),
            "prepared": len(prepared),
            "prepared_names": prepared,
            "manual_review": len(manual_review),
            "manual_review_names": manual_review,
            "archived_quality": archived,
            "skipped_qualification": len(skipped_qual),
            "skipped_names": skipped_qual,
            "skipped_dup": skipped_dup,
            "duplicates": skipped_dup,
            "errors": errors,
            "auto_draft_max_eur": AUTO_DRAFT_MAX_EUR,
            "message_ru": (
                f"Auto-draft ≤{AUTO_DRAFT_MAX_EUR:.0f}€: {len(prepared)} · "
                f"manual-review: {len(manual_review)} · архив качества: {archived}"
                + (f" · дубли: {skipped_dup}" if skipped_dup else "")
                + "."
                if (prepared or manual_review or archived or skipped_dup)
                else (
                    f"Квалификация отсеяла {len(skipped_qual)} лидов — нужен email/живой сайт."
                    if skipped_qual
                    else "Нет новых лидов для автоподготовки (или уже в очереди)."
                )
            ),
        }

    def approve_batch(self, opportunity_ids: list[str] | None = None, *, limit: int = 5) -> dict[str, Any]:
        """CEO one-click: approve top pending drafts (send if outreach enabled + email)."""
        queue = self.approval_queue(limit=limit if not opportunity_ids else 50)
        ids = opportunity_ids or [q["id"] for q in queue[:limit]]
        approved: list[str] = []
        sent: list[str] = []
        failed: list[str] = []

        for oid in ids:
            try:
                result = self.approve_outreach(oid)
                name = str(result["opportunity"].get("company_name") or oid)
                approved.append(name)
                if (result.get("send_result") or {}).get("ok"):
                    sent.append(name)
            except ValueError:
                failed.append(oid)

        return {
            "ok": True,
            "approved_count": len(approved),
            "sent_count": len(sent),
            "approved_names": approved,
            "sent_names": sent,
            "failed_ids": failed,
            "message_ru": (
                f"Одобрено {len(approved)}"
                + (f", отправлено {len(sent)}" if sent else " — скопируйте письма вручную")
            ),
        }

    def ceo_outbox_summary(self, limit: int = 5) -> dict[str, Any]:
        """Pending outreach for Business Health / morning CEO path."""
        queue = self.approval_queue(limit=limit)
        outreach_enabled = os.getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower() == "true"
        return {
            "title_ru": "CEO Outbox — Plan → Approve → Act",
            "pending_count": len(queue),
            "outreach_send_enabled": outreach_enabled,
            "pipeline_steps_ru": [
                "Spider",
                "Discovery",
                "Оценка лида",
                "Проверка сайта",
                "Поиск email",
                "Подготовка КП + аудит",
                "Approve CEO",
                "Отправка",
                "Ответ клиента",
                "Оплата",
                "Feedback",
            ],
            "week_targets_ru": {
                "week1": "20–30 лидов · 5–10 писем/день · 150–300/мес · 3–5 ответов/нед",
                "week2": "3 созвона · 2 КП · 1 оплата (снайпер, не спам)",
            },
            "money_path_ru": (
                "Реальный € = клиент платит за аудит/отчёт (50–500 €), не Toloka ledger. "
                "Ферма ищет — Genesis готовит отчёт — вы Approve — оплата на Stripe/счёт."
            ),
            "money_accounts_ru": [
                "B2B (главный): Stripe live + счёт → банк SEPA после первого клиента",
                "Scale Contributor: отдельный аккаунт исполнителя на scale.com (не API requester)",
                "Toloka Pipeline API: вы заказчик — wallet $0 нормален; performer = другой аккаунт toloka.ai",
            ],
            "law_ru": "Автоотправка только после Approve. Без email — копируйте отчёт вручную (WhatsApp/форма).",
            "items": queue,
        }

    def approval_queue(self, limit: int = 20) -> list[dict]:
        rows = self._opportunity._load_rows()
        pending = []
        for r in rows:
            if r.get("outreach_status") != "pending_approval":
                continue
            meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            pending.append(r)
        pending.sort(key=lambda r: int(r.get("score") or 0), reverse=True)
        return [self._queue_item(r) for r in pending[:limit]]

    def manual_review_queue(self, limit: int = 20) -> list[dict]:
        rows = self._opportunity._load_rows()
        pending = []
        for r in rows:
            if r.get("outreach_status") != "manual_review":
                continue
            meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            pending.append(r)
        pending.sort(key=lambda r: float(r.get("recommended_price_eur") or 0), reverse=True)
        return [self._queue_item(r) for r in pending[:limit]]

    @staticmethod
    def _resolve_queue_pricing(r: dict, meta: dict) -> dict:
        """Local-market price for owner lead lists (field name ``*_price_eur`` is historical)."""
        from app.integration.commerce_engine import resolve_final_offer
        from app.integration.market_registry import format_amount, get_market
        from app.integration.outreach_language_service import resolve_market_from_row

        market = (
            resolve_market_from_row(r)
            or meta.get("market")
            or r.get("market")
            or "DE"
        )
        package_id = (
            r.get("recommended_package_id")
            or meta.get("recommended_package_id")
            or "basic"
        )
        if package_id not in ("basic", "business", "premium"):
            package_id = "basic"

        market_profile = get_market(market)
        expected_currency = str(market_profile.currency or "EUR").upper()
        expected_symbol = str(market_profile.symbol or "€")

        currency = str(
            r.get("recommended_currency") or meta.get("recommended_currency") or ""
        ).upper()
        price_label = str(
            r.get("recommended_price_label") or meta.get("recommended_price_label") or ""
        ).strip()
        symbol = str(
            r.get("recommended_symbol") or meta.get("recommended_symbol") or ""
        )
        amount_raw = r.get("recommended_price_eur") or r.get("potential_value_eur")
        amount = float(amount_raw) if amount_raw not in (None, "") else None

        stale = (
            not price_label
            or not currency
            or currency != expected_currency
            or (
                expected_currency != "EUR"
                and "€" in price_label
                and expected_symbol not in price_label
            )
        )
        if stale:
            try:
                offer = resolve_final_offer(package_id, market)
                return {
                    "recommended_price_eur": float(offer.amount),
                    "recommended_currency": offer.currency,
                    "recommended_symbol": offer.symbol,
                    "recommended_price_label": offer.price_label,
                }
            except Exception:
                pass

        if not currency:
            currency = expected_currency
        if not symbol:
            symbol = expected_symbol
        if not price_label and amount is not None:
            price_label = format_amount(int(round(amount)), symbol)

        return {
            "recommended_price_eur": amount,
            "recommended_currency": currency,
            "recommended_symbol": symbol,
            "recommended_price_label": price_label,
        }

    @staticmethod
    def _queue_item(r: dict) -> dict:
        meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
        issues = list((r.get("site_analysis") or {}).get("issues") or [])[:5]
        pricing = AcquisitionStudioService._resolve_queue_pricing(r, meta)
        currency = pricing["recommended_currency"]
        price_label = pricing["recommended_price_label"]
        return {
            "id": r["id"],
            "company_name": r.get("company_name"),
            "contact": r.get("contact"),
            "website_url": r.get("website_url"),
            "recommended_price_eur": pricing["recommended_price_eur"],
            "recommended_currency": currency,
            "recommended_symbol": pricing["recommended_symbol"],
            "recommended_price_label": price_label,
            "recommended_package_id": r.get("recommended_package_id"),
            "email_subject": r.get("email_subject"),
            "proposed_message": r.get("proposed_message"),
            "fit_reason": r.get("fit_reason"),
            "pricing_rationale": r.get("pricing_rationale"),
            "issue_count": (r.get("site_analysis") or {}).get("issue_count", 0),
            "site_issues": issues,
            "suggested_services": suggest_services_for_site_issues(issues),
            "score": r.get("score"),
            "outreach_status": r.get("outreach_status"),
            "price_tier": meta.get("price_tier"),
            "last_market_lesson": meta.get("last_market_lesson"),
            "crm_status": r.get("status"),
            "market": meta.get("market") or r.get("market"),
            "hunt_city": meta.get("hunt_city"),
        }

    def pipeline_leads(self, *, limit: int = 50) -> list[dict]:
        """Все активные лиды Country Desk — не только Approve-очередь."""
        rows = self._opportunity.list_opportunities(limit=200)
        out: list[dict] = []
        for r in rows:
            meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            if r.get("status") in ("won", "lost"):
                continue
            item = self._queue_item(r)
            item["status"] = r.get("status")
            item["status_label"] = r.get("status_label")
            item["source_id"] = r.get("source_id")
            item["win_probability_pct"] = meta.get("win_probability_pct")
            item["niche"] = meta.get("niche")
            item["market"] = meta.get("market") or r.get("market")
            item["hunt_city"] = meta.get("hunt_city")
            item["quality_archive"] = bool(meta.get("quality_archive"))
            out.append(item)
        out.sort(
            key=lambda x: (
                0 if x.get("outreach_status") == "pending_approval" else 1,
                0 if x.get("outreach_status") == "manual_review" else 1,
                -int(x.get("win_probability_pct") or 0),
                -int(x.get("score") or 0),
            )
        )
        return out[:limit]

    def auto_confirm_high_probability(self, *, min_win_pct: int = HIGH_WIN_AUTO_CONFIRM_PCT) -> dict[str, Any]:
        """Подтвердить (без обязательной отправки) черновики с высоким win%.

        approve_outreach при выключенном GENESIS_OUTREACH_ENABLED только ставит approved —
        письмо не уходит. Это и есть «автоподтверждение» для CEO-копирования.
        """
        confirmed: list[str] = []
        queued: list[str] = []
        skipped: list[str] = []
        for row in self._opportunity.list_opportunities(limit=200):
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("quality_archive"):
                continue
            win = int(meta.get("win_probability_pct") or 0)
            if win < min_win_pct:
                continue
            name = str(row.get("company_name") or row.get("id"))
            status = str(row.get("outreach_status") or "")
            if status == "manual_review":
                try:
                    self.promote_manual_review(row["id"])
                    queued.append(name)
                    status = "pending_approval"
                except ValueError:
                    skipped.append(name)
                    continue
            if status == "pending_approval" and row.get("proposed_message"):
                try:
                    result = self.approve_outreach(row["id"])
                    confirmed.append(str(result["opportunity"].get("company_name") or name))
                except ValueError:
                    skipped.append(name)
            elif status in ("approved", "sent"):
                continue
            else:
                skipped.append(name)
        return {
            "ok": True,
            "min_win_pct": min_win_pct,
            "confirmed": len(confirmed),
            "confirmed_names": confirmed,
            "promoted_to_queue": len(queued),
            "skipped": len(skipped),
            "outreach_send_enabled": os.getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower() == "true",
            "message_ru": (
                f"Автоподтверждение win≥{min_win_pct}%: {len(confirmed)} шт. "
                + (
                    "Отправка включена."
                    if os.getenv("GENESIS_OUTREACH_ENABLED", "").strip().lower() == "true"
                    else "Письма НЕ отправлены (outreach выкл.) — скопируйте из Outbox."
                )
            ),
        }

    def refresh_country_desk_leads(
        self,
        *,
        limit: int = 8,
        query: str | None = None,
        city: str | None = None,
        auto_confirm: bool = True,
        market: str | None = None,
    ) -> dict[str, Any]:
        """Одна кнопка / тик runner: Places → ingest → prepare → high-win confirm.

        Без явного market/city — round-robin по всем enabled странам (до лимитов,
        паузы adaptive пропускаются), чтобы не долбить только DE / один IP-таргет.
        """
        from app.integration.outreach_hunt_rotation import HuntRotationCursor

        paused = (self._adaptive._load_state().get("paused_markets") or {})
        cursor = HuntRotationCursor(self._memory_dir)
        slot = cursor.next_slot(
            paused_markets=paused,
            effective_cap_fn=self._adaptive.effective_daily_cap,
            market_override=market,
            city_override=city,
            query_override=query,
        )
        if not slot:
            return {
                "ok": False,
                "message_ru": "Нет активных рынков для hunt (все на паузе или cap=0)",
                "drafts": {"created": 0, "drafted": 0},
                "pipeline": self.pipeline_leads(limit=40),
                "gate_funnel": self.gate_funnel(),
            }

        city_s = str(slot["city"])
        query_s = str(slot["query"])
        market_s = str(slot["market"])
        language = str(slot.get("language") or "en")
        region = str(slot.get("region") or market_s.lower())

        drafts = self.generate_drafts_from_places(
            city=city_s,
            query=query_s,
            limit=limit,
            language=language,
            force_skip_check=True,
            market_code=market_s,
            search_region=region,
        )
        prep = self.auto_prepare_discovery_leads(limit=limit, min_score=40, min_win_pct=40)
        confirm = (
            self.auto_confirm_high_probability(min_win_pct=HIGH_WIN_AUTO_CONFIRM_PCT)
            if auto_confirm
            else {"confirmed": 0, "message_ru": "auto_confirm выкл."}
        )
        flag = slot.get("flag") or ""
        return {
            "ok": True,
            "city": city_s,
            "query": query_s,
            "market_code": market_s,
            "slot_index": slot.get("slot_index"),
            "slots_total": slot.get("slots_total"),
            "drafts": drafts,
            "auto_prepare": prep,
            "auto_confirm": confirm,
            "pipeline": self.pipeline_leads(limit=40),
            "gate_funnel": self.gate_funnel(),
            "message_ru": (
                f"Обновлено · {flag}{market_s} · {city_s} · «{query_s}»: "
                f"Places created={drafts.get('created', 0)} drafted={drafts.get('drafted', 0)} · "
                f"prepare={prep.get('prepared', 0)}+manual={prep.get('manual_review', 0)} · "
                f"auto-confirm={confirm.get('confirmed', 0)}"
            ),
        }

    def promote_manual_review(self, opportunity_id: str) -> dict:
        """CEO: move >50€ draft from manual_review into Approve queue."""
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        if row.get("outreach_status") != "manual_review":
            raise ValueError("not_manual_review")
        if not row.get("proposed_message"):
            raise ValueError("no_draft")
        row["outreach_status"] = "pending_approval"
        row["status_label"] = "Предложение готово · после ручной проверки"
        meta = dict(row.get("meta") or {})
        meta["price_tier"] = "ceo_promoted"
        row["meta"] = meta
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._log_interaction(row, "promoted_to_approval", "CEO: manual_review → pending_approval")
        self._opportunity._save_rows(self._replace_row(opportunity_id, row))
        return row

    def _archive_quality(
        self,
        row: dict,
        *,
        reason: str,
        detail: str,
        win_pct: int | None = None,
    ) -> None:
        """Never delete weak leads — park in quality archive for later learning."""
        import json
        from pathlib import Path

        meta = dict(row.get("meta") or {})
        if meta.get("quality_archive"):
            return
        now = datetime.now(timezone.utc).isoformat()
        meta["quality_archive"] = True
        meta["quality_archive_reason"] = reason
        meta["quality_archive_detail"] = detail
        meta["quality_archived_at"] = now
        if win_pct is not None:
            meta["quality_archive_win_pct"] = int(win_pct)
        row["meta"] = meta
        row["updated_at"] = now
        self._log_interaction(row, "quality_archive", f"{reason}: {detail}"[:160])
        self._opportunity._save_rows(self._replace_row(str(row["id"]), row))

        mem = Path(getattr(self._opportunity, "memory_dir", None) or getattr(self, "_memory_dir", None) or ".")
        path = mem / QUALITY_ARCHIVE_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "id": row.get("id"),
                        "company_name": row.get("company_name"),
                        "website_url": row.get("website_url"),
                        "reason": reason,
                        "detail": detail,
                        "win_pct": win_pct,
                        "at": now,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    def approve_outreach(self, opportunity_id: str) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        if row.get("outreach_status") not in ("pending_approval", "draft"):
            raise ValueError("not_pending")

        from app.integration.outreach_ceo_prefs import outreach_send_allowed

        outreach_enabled = outreach_send_allowed(self._memory_dir)
        to_email = self._extract_email(row.get("contact", ""))
        send_result: dict | None = None

        excluded, excl_reason = self._exclusion.check(
            email=to_email,
            website_url=str(row.get("website_url") or ""),
            exclude_id=str(row.get("id") or ""),
        )
        if excluded:
            raise ValueError(f"excluded:{excl_reason}")

        if outreach_enabled and to_email:
            # Daily sniper cap before Resend call — prefer From matching lead market
            from app.integration.outreach_language_service import resolve_market_from_row

            lead_market = str(
                resolve_market_from_row(row)
                or (row.get("meta") or {}).get("market")
                or row.get("market")
                or "DE"
            ).upper()
            region_map = {
                "DE": "de",
                "AT": "de",
                "CH": "de",
                "US": "us",
                "CA": "us",
                "GB": "us",
                "UK": "us",
                "AU": "us",
                "UA": "cis",
                "RU": "cis",
                "BY": "cis",
                "KZ": "cis",
                "CIS": "cis",
            }
            want_region = region_map.get(lead_market, "de")
            picked, pick_meta = self._send_quota.pick_from_address(
                market=lead_market, region=want_region
            )
            if not picked:
                # Fallback: any region still under global/phase budget
                picked, pick_meta = self._send_quota.pick_from_address()
            if not picked:
                send_result = {
                    "ok": False,
                    "skipped": True,
                    "reason": pick_meta.get("reason") or "daily_cap",
                    "quota": pick_meta,
                }
                row["outreach_status"] = "approved"
                self._log_interaction(
                    row,
                    "approved",
                    f"Approve OK, отправка заблокирована квотой: {send_result['reason']}",
                )
            else:
                can, why = self._send_quota.can_send(picked, market=lead_market)
                if not can:
                    send_result = {
                        "ok": False,
                        "skipped": True,
                        "reason": why,
                        "quota": pick_meta,
                    }
                    row["outreach_status"] = "approved"
                    self._log_interaction(
                        row, "approved", f"Approve OK, квота: {why}"
                    )
                else:
                    send_result = self._email.send_outreach(
                        to=to_email,
                        subject=row.get("email_subject")
                        or f"{BRAND_NAME} — {row.get('company_name')}",
                        text=row.get("proposed_message") or "",
                        from_addr=picked,
                        market=str(
                            (row.get("meta") or {}).get("market")
                            or row.get("market")
                            or pick_meta.get("region")
                            or "DE"
                        ),
                        language=str(
                            (row.get("meta") or {}).get("outreach_language") or ""
                        )
                        or None,
                    )
                    if send_result.get("ok"):
                        self._send_quota.record_send(
                            picked,
                            region=pick_meta.get("region"),
                            market=lead_market,
                        )
                        row["outreach_status"] = "sent"
                        row["status"] = "contacted"
                        row["status_label"] = "Связались"
                        self._log_interaction(row, "sent", f"Отправлено на {to_email}")
                    else:
                        row["outreach_status"] = "approved"
                        reason = send_result.get("reason", "send_failed")
                        self._log_interaction(
                            row, "approved", f"Approve OK, отправка: {reason}"
                        )
        else:
            row["outreach_status"] = "approved"
            note = "CEO Approve — скопируйте письмо и отправьте вручную"
            if not to_email:
                note += " (email не найден в контакте)"
            elif not outreach_enabled:
                note += " (GENESIS_OUTREACH_ENABLED выключен)"
            self._log_interaction(row, "approved", note)

        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._opportunity._save_rows(self._replace_row(opportunity_id, row))
        return {
            "ok": True,
            "opportunity": row,
            "send_result": send_result,
            "message": (
                "Письмо отправлено."
                if send_result and send_result.get("ok")
                else "Одобрено. Скопируйте текст и отправьте вручную."
            ),
        }

    def reject_outreach(self, opportunity_id: str, *, note: str = "") -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        row["outreach_status"] = "rejected"
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._log_interaction(row, "rejected", note or "CEO отклонил черновик")
        self._opportunity._save_rows(self._replace_row(opportunity_id, row))
        return row

    def mark_sent_manual(self, opportunity_id: str, *, note: str = "") -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        row["outreach_status"] = "sent"
        row["status"] = "contacted"
        row["status_label"] = "Связались"
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._log_interaction(row, "sent_manual", note or "CEO отправил вручную")
        self._opportunity._save_rows(self._replace_row(opportunity_id, row))
        return row

    def record_interaction(
        self,
        opportunity_id: str,
        event: str,
        note: str = "",
        *,
        market_lesson: str = "",
        market_reason: str = "",
    ) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        status_map = {
            "replied": "replied",
            "qualified": "qualified",
            "won": "won",
            "lost": "lost",
            "no_reply": "contacted",
        }
        if event in status_map:
            row["status"] = status_map[event]
            from app.integration.opportunity_service import _STATUSES

            label_key = status_map[event]
            if event == "no_reply":
                row["status_label"] = "Без ответа"
            else:
                row["status_label"] = _STATUSES.get(label_key, label_key)
        if event == "lost" and note:
            row["notes"] = (row.get("notes") or "") + f"\nОтказ: {note}".strip()

        comment = (market_lesson or note or "").strip()
        reason = (market_reason or "").strip().lower()
        if event in MARKET_OUTCOME_EVENTS:
            if reason not in MARKET_REASON_LABELS_RU:
                # Legacy: free-text only → treat as other + comment required
                if comment and not reason:
                    reason = "other"
                else:
                    raise ValueError("market_reason_required")
            if reason == "other" and not comment:
                raise ValueError("market_lesson_required")

        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if event in MARKET_OUTCOME_EVENTS and reason:
            reason_label = MARKET_REASON_LABELS_RU[reason]
            lesson_text = f"{reason_label}" + (f" — {comment}" if comment else "")
            lessons = list(meta.get("market_lessons") or [])
            lessons.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "event": event,
                    "reason": reason,
                    "reason_label_ru": reason_label,
                    "comment": comment[:500],
                    "lesson": lesson_text[:500],
                    "note": (note or "")[:200],
                }
            )
            meta["market_lessons"] = lessons[-20:]
            meta["last_market_lesson"] = lesson_text[:500]
            meta["last_market_reason"] = reason
            row["meta"] = meta

        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        log_note = meta.get("last_market_lesson") if reason else note
        if comment and reason and note and note != comment:
            log_note = f"{note} | {meta.get('last_market_lesson')}"
        self._log_interaction(row, event, log_note or note)
        self._opportunity._save_rows(self._replace_row(opportunity_id, row))
        return row

    def evidence_report(self) -> dict:
        rows = self._opportunity._load_rows()
        contacted = [r for r in rows if r.get("status") in ("contacted", "replied", "qualified", "won", "lost")]
        replied = [r for r in rows if r.get("status") in ("replied", "qualified", "won")]
        won = [r for r in rows if r.get("status") == "won"]
        lost = [r for r in rows if r.get("status") == "lost"]
        sent_rows = [
            r
            for r in rows
            if r.get("outreach_status") == "sent"
            or r.get("status") in ("contacted", "replied", "qualified", "won", "lost")
        ]

        by_segment: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "replied": 0, "won": 0})
        by_price: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "replied": 0, "won": 0})

        for r in contacted:
            seg = self._infer_segment(r)
            price_band = self._price_band(float(r.get("recommended_price_eur") or r.get("potential_value_eur") or 0))
            for bucket, key in ((by_segment, seg), (by_price, price_band)):
                bucket[key]["sent"] += 1
                if r.get("status") in ("replied", "qualified", "won"):
                    bucket[key]["replied"] += 1
                if r.get("status") == "won":
                    bucket[key]["won"] += 1

        insights: list[str] = []
        if len(contacted) >= 5:
            best_seg = max(by_segment.items(), key=lambda x: x[1]["replied"], default=None)
            if best_seg and best_seg[1]["replied"] > 0:
                insights.append(
                    f"Сегмент «{best_seg[0]}» — больше всего ответов ({best_seg[1]['replied']} из {best_seg[1]['sent']})."
                )
            best_price = max(by_price.items(), key=lambda x: x[1]["replied"], default=None)
            if best_price and best_price[1]["replied"] > 0:
                insights.append(
                    f"Ценовой диапазон {best_price[0]} € — {best_price[1]['replied']} ответов."
                )
        else:
            insights.append(
                f"Нужно ≥5 контактов для Evidence. Сейчас: {len(contacted)}."
            )

        lost_reasons = Counter()
        for r in lost:
            note = (r.get("notes") or "").lower()
            if "цена" in note or "teuer" in note or "price" in note:
                lost_reasons["цена"] += 1
            elif note:
                lost_reasons["другое"] += 1
            else:
                lost_reasons["без причины"] += 1

        reason_counts: Counter[str] = Counter()
        recent_lessons: list[dict] = []
        lessons_logged = 0
        for r in rows:
            meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
            row_lessons = meta.get("market_lessons") or []
            if row_lessons:
                lessons_logged += 1
            for lesson in row_lessons:
                if not isinstance(lesson, dict):
                    continue
                reason = str(lesson.get("reason") or "")
                if reason in MARKET_REASON_LABELS_RU:
                    reason_counts[reason] += 1
                elif lesson.get("lesson"):
                    reason_counts["other"] += 1
                if lesson.get("lesson") or lesson.get("reason"):
                    recent_lessons.append(
                        {
                            "company": r.get("company_name"),
                            "event": lesson.get("event"),
                            "reason": reason or "other",
                            "reason_label_ru": lesson.get("reason_label_ru")
                            or MARKET_REASON_LABELS_RU.get(reason, "Другое"),
                            "comment": lesson.get("comment") or "",
                            "lesson": lesson.get("lesson"),
                            "at": lesson.get("at"),
                        }
                    )
        recent_lessons.sort(key=lambda x: str(x.get("at") or ""), reverse=True)
        recent_lessons = recent_lessons[:12]

        sent_count = len(sent_rows)
        pending_lessons = max(0, sent_count - lessons_logged)
        completeness_pct = (
            round(100.0 * lessons_logged / sent_count, 1) if sent_count else 100.0
        )

        reason_table = [
            {
                "reason": code,
                "label_ru": MARKET_REASON_LABELS_RU[code],
                "count": reason_counts[code],
            }
            for code in sorted(reason_counts.keys(), key=lambda c: (-reason_counts[c], c))
        ]

        if reason_counts:
            top_code, top_n = reason_counts.most_common(1)[0]
            top_label = MARKET_REASON_LABELS_RU.get(top_code, top_code)
            if top_code == "no_reply":
                insights.insert(
                    0,
                    f"Статистика: чаще всего «{top_label}» ({top_n}). "
                    "Значит, сначала улучшить тему письма и первые две строки — не цену.",
                )
            elif top_code == "price":
                insights.insert(
                    0,
                    f"Статистика: чаще всего «{top_label}» ({top_n}). "
                    "Проверьте микс Basic/Business и ясность ценности Path A.",
                )
            elif top_code == "interested":
                insights.insert(
                    0,
                    f"Статистика: «{top_label}» лидирует ({top_n}). "
                    "Сохраняйте удачные шаблоны и усиливайте follow-up.",
                )
            else:
                insights.insert(
                    0,
                    f"Статистика причин: чаще всего «{top_label}» ({top_n}).",
                )
        elif recent_lessons:
            insights.insert(
                0,
                f"Последний урок рынка: {recent_lessons[0].get('lesson')}",
            )

        if sent_count and pending_lessons > 0:
            insights.append(
                f"Learning Score: {lessons_logged}/{sent_count} уроков · "
                f"необработанных {pending_lessons} — зафиксируйте исходы, иначе Evidence дырявый."
            )

        return {
            "sample_size": len(rows),
            "contacted": len(contacted),
            "replied": len(replied),
            "won": len(won),
            "lost": len(lost),
            "reply_rate_pct": round(100 * len(replied) / len(contacted), 1) if contacted else 0,
            "by_segment": dict(by_segment),
            "by_price_band": dict(by_price),
            "lost_reasons": dict(lost_reasons),
            "reason_counts": reason_table,
            "market_reason_catalog": [
                {"id": k, "label_ru": v} for k, v in MARKET_REASON_LABELS_RU.items()
            ],
            "learning": {
                "sent": sent_count,
                "lessons_logged": lessons_logged,
                "pending_lessons": pending_lessons,
                "completeness_pct": completeness_pct,
            },
            "insights": insights,
            "recent_lessons": recent_lessons,
            "evidence_ready": len(contacted) >= 30,
            "milestone_ru": (
                "KPI: sniper-контакты Path A (лучше 8 сильных) → сигнал рынка "
                "(ответ или клик на /order). Не объём писем. Авто-ZIP = Tier 2 после первой оплаты."
            ),
            "note": (
                "Evidence First — причина + комментарий. "
                "Sniper: Approve только если Neustart уместен. "
                "Toloka/TikTok/найм — не в этом цикле."
            ),
        }

    def _recommend_pricing(
        self, row: dict, analysis: dict | None
    ) -> tuple[str, float, str]:
        packages = {p["id"]: p for p in self._sales.packages()}
        issue_count = (analysis or {}).get("issue_count", 0)
        fit = (row.get("fit_reason") or "").lower()

        if issue_count >= 5 or "нет сайта" in fit or "no website" in fit:
            pkg_id = "business"
            rationale = "Много улучшений / слабое присутствие → Business"
        elif issue_count >= 3:
            pkg_id = "basic"
            rationale = "Умеренные улучшения → Basic"
        else:
            pkg_id = "basic"
            rationale = "Базовое предложение → Basic"

        if any(w in fit for w in ("premium", "домен", "логотип", "analytics")):
            pkg_id = "premium"
            rationale = "Запрос расширенного пакета → Premium"

        package = packages.get(pkg_id, packages["basic"])
        return pkg_id, float(package["price_eur"]), rationale

    def _draft_outreach(
        self,
        *,
        company: str,
        analysis: dict | None,
        package: dict,
        price: float,
        fit_reason: str,
    ) -> tuple[str, str]:
        # Fallback DE draft — same Path A honesty as OutreachLanguageService templates.
        issues = (analysis or {}).get("issues") or []
        issues_block = (
            "\n".join(f"• {i}" for i in issues[:7])
            if issues
            else "• Online-Auftritt technisch veraltet oder schwer erreichbar"
        )
        subject = f"{company} — digitaler Neustart mit moderner Landing Page"

        from app.integration.outreach_language_service import public_order_url

        order_url = public_order_url()
        body = (
            f"Guten Tag,\n\n"
            f"wir haben uns den aktuellen Online-Auftritt von {company} angeschaut. "
            f"Statt an einem veralteten System zu „reparieren“, schlagen wir einen klaren Neustart vor: "
            f"eine moderne, schnelle Landing Page — mobil optimiert, mit klarem Kontakt-/Terminweg"
            f"{f' ({fit_reason.strip()[:80]})' if fit_reason else ''}.\n\n"
            f"Warum ein Neustart sinnvoll ist (Ist-Zustand):\n{issues_block}\n\n"
            f"Paket «{package['name']}» für {package.get('price_label') or f'{price:.0f} €'} — "
            f"fertige Landing Page in ca. 5–7 Werktagen "
            f"(HTML-Dateien, bereit für Ihren Hosting-Anbieter). "
            f"Optional: Upload auf Ihre Domain durch uns (Sorglos-Paket).\n\n"
            f"Wenn das für Sie interessant klingt — hier die Pakete und Bestellung "
            f"(ohne Verpflichtung):\n{order_url}\n\n"
            f"Beste Grüße\n"
            f"Ramish · {BRAND_NAME}\n"
        )
        return subject, body

    def _refresh_score(self, row: dict, analysis: dict | None) -> int:
        base = int(row.get("score") or 40)
        if analysis:
            base = max(base, int(analysis.get("improvement_score") or 0))
        if row.get("proposed_message"):
            base = min(100, base + 5)
        return base

    def _extract_email(self, contact: str) -> str:
        match = __import__("re").search(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", contact or ""
        )
        return match.group(0) if match else ""

    def _infer_segment(self, row: dict) -> str:
        text = f"{row.get('company_name', '')} {row.get('fit_reason', '')}".lower()
        for kw, label in (
            ("zahn", "стоматология"),
            ("dental", "стоматология"),
            ("auto", "автосервис"),
            ("werkstatt", "автосервис"),
            ("café", "кафе"),
            ("cafe", "кафе"),
            ("restaurant", "ресторан"),
            ("bau", "строительство"),
        ):
            if kw in text:
                return label
        meta = row.get("meta") or {}
        return str(meta.get("segment") or "другое")

    def _price_band(self, price: float) -> str:
        if price <= 400:
            return "350-400"
        if price <= 700:
            return "450-650"
        return "700+"

    def _log_interaction(self, row: dict, event: str, note: str) -> None:
        history = row.get("interactions")
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "note": note,
            }
        )
        row["interactions"] = history[-50:]

    def _replace_row(self, opportunity_id: str, updated: dict) -> list[dict]:
        rows = self._opportunity._load_rows()
        return [updated if r.get("id") == opportunity_id else r for r in rows]
