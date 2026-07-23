"""Lead Engine v2 — fresh lead base, Country Profiles farms, anti-spam pacing.

Before mass hunt:
- reason why site became a lead (from analysis fails)
- priority High / Medium / Low
- domain dedup across city/niche
- contact history — never pitch same business twice
- Country Profiles (enable/disable, quotas, languages) — not hardcoded lists only
- lead collection unlimited; send interval 40–60s with country rotation
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.integration.country_profiles import (
    ALL_PROFILE_CODES,
    enabled_profiles,
    get_profile,
    merge_runtime_config,
)

ENGINE_ID = "lead_engine_v2"
LEAD_ENGINE_VERSION = 2

DEFAULT_NICHES: list[str] = [
    "Zahnarzt",
    "Rechtsanwalt",
    "Handwerker",
    "Friseur",
    "Physiotherapie",
    "Steuerberater",
    "dentist",
    "lawyer",
    "plumber",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_domain(url_or_host: str) -> str:
    raw = str(url_or_host or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = (urlparse(raw).hostname or "").lower()
    except Exception:
        return ""
    return host.removeprefix("www.")


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()[:200]


def reasons_from_analysis(analysis: dict[str, Any] | None) -> list[dict[str, str]]:
    """Why this site entered the lead list — tied to real check failures."""
    if not isinstance(analysis, dict):
        return [{"code": "unknown", "label": "No analysis attached"}]
    reasons: list[dict[str, str]] = []
    for check in analysis.get("checks") or []:
        if not isinstance(check, dict):
            continue
        if check.get("status") != "fail":
            continue
        cid = str(check.get("id") or "issue")
        label = str(check.get("label") or cid)
        detail = str(check.get("detail") or "").strip()
        reasons.append(
            {
                "code": cid,
                "label": label,
                "detail": detail[:240],
            }
        )
    for problem in analysis.get("problems") or []:
        text = str(problem).strip()
        if text and not any(text.startswith(r["label"]) for r in reasons):
            reasons.append({"code": "problem", "label": text[:120], "detail": ""})
    if not reasons and analysis.get("health_score") is not None:
        hs = int(analysis.get("health_score") or 0)
        if hs < 75:
            reasons.append(
                {
                    "code": "low_health",
                    "label": f"Health score {hs}/100",
                    "detail": "Below healthy threshold",
                }
            )
    if not reasons:
        reasons.append({"code": "manual", "label": "Manual / source ingest", "detail": ""})
    return reasons[:12]


def priority_from_analysis(
    analysis: dict[str, Any] | None,
    *,
    reasons: list[dict[str, str]] | None = None,
) -> str:
    """High / Medium / Low — commercial urgency, not spam aggressiveness."""
    reasons = reasons if reasons is not None else reasons_from_analysis(analysis)
    codes = {r.get("code") for r in reasons}
    critical = {"https", "reachability", "cta", "contacts", "forms", "speed"}
    fail_n = len([r for r in reasons if r.get("code") != "manual"])
    hs = int((analysis or {}).get("health_score") or 50) if isinstance(analysis, dict) else 50
    if codes & critical or hs < 45 or fail_n >= 5:
        return "High"
    if hs < 70 or fail_n >= 2:
        return "Medium"
    return "Low"


class LeadEngineV2:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._root = memory_dir / "lead_engine_v2"
        self._root.mkdir(parents=True, exist_ok=True)
        self._leads = self._root / "leads.jsonl"
        self._dedup = self._root / "dedup_index.json"
        self._state = self._root / "state.json"
        self._farms = self._root / "country_farms.json"
        self._contacts = self._root / "contact_history.jsonl"
        self._archive = memory_dir / "lead_engine_v1_archive"

    # --- farms / country profiles -------------------------------------------------

    def farm_config(self) -> dict[str, Any]:
        raw = None
        if self._farms.is_file():
            try:
                raw = json.loads(self._farms.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                raw = None
        return merge_runtime_config(raw if isinstance(raw, dict) else None)

    def save_farm_config(self, patch: dict[str, Any]) -> dict[str, Any]:
        current = self.farm_config()
        merged = merge_runtime_config({**current, **(patch or {})})
        # Explicit enable list
        if "enabled_countries" in (patch or {}):
            merged = merge_runtime_config({**merged, "enabled_countries": patch["enabled_countries"]})
        if "profiles" in (patch or {}) and isinstance(patch["profiles"], dict):
            merged = merge_runtime_config({**merged, "profiles": {**merged["profiles"], **patch["profiles"]}})
        self._farms.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        return merged

    def set_country_enabled(self, code: str, enabled: bool) -> dict[str, Any]:
        cfg = self.farm_config()
        c = str(code or "").strip().upper()[:2]
        if c not in ALL_PROFILE_CODES:
            return {"ok": False, "error": "unknown_country", "code": c}
        enabled_set = set(cfg.get("enabled_countries") or [])
        if enabled:
            enabled_set.add(c)
        else:
            enabled_set.discard(c)
        return {
            "ok": True,
            "config": self.save_farm_config({"enabled_countries": sorted(enabled_set)}),
        }

    # --- state --------------------------------------------------------------------

    def _load_state(self) -> dict[str, Any]:
        if not self._state.is_file():
            return self._default_state()
        try:
            data = json.loads(self._state.read_text(encoding="utf-8"))
            return {**self._default_state(), **(data if isinstance(data, dict) else {})}
        except (json.JSONDecodeError, OSError):
            return self._default_state()

    def _default_state(self) -> dict[str, Any]:
        return {
            "engine": ENGINE_ID,
            "version": LEAD_ENGINE_VERSION,
            "running": False,
            "paused": False,
            "country_cursor": 0,
            "city_cursor": 0,
            "niche_cursor": 0,
            "niches": list(DEFAULT_NICHES),
            "batch_limit": 10,
            "updated_at": _now(),
            "last_reset_at": None,
            "leads_accepted": 0,
            "leads_rejected_dup": 0,
            "leads_rejected_contacted": 0,
            "rotation_country_index": 0,
        }

    def _save_state(self, state: dict[str, Any]) -> None:
        state["updated_at"] = _now()
        self._state.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_dedup(self) -> dict[str, Any]:
        if not self._dedup.is_file():
            return {"domains": {}, "emails": {}}
        try:
            data = json.loads(self._dedup.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"domains": {}, "emails": {}}
            data.setdefault("domains", {})
            data.setdefault("emails", {})
            # Drop legacy "websites" key — domain is the only site key
            return {"domains": data["domains"], "emails": data["emails"]}
        except (json.JSONDecodeError, OSError):
            return {"domains": {}, "emails": {}}

    def _save_dedup(self, idx: dict[str, Any]) -> None:
        self._dedup.write_text(
            json.dumps(
                {"domains": idx.get("domains") or {}, "emails": idx.get("emails") or {}},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # --- contact history (anti double-pitch) --------------------------------------

    def was_contacted(self, *, domain: str = "", email: str = "") -> bool:
        dom = normalize_domain(domain) if domain else ""
        em = normalize_email(email)
        if not self._contacts.is_file():
            return False
        try:
            for line in self._contacts.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if dom and normalize_domain(str(row.get("domain") or "")) == dom:
                    return True
                if em and normalize_email(str(row.get("email") or "")) == em:
                    return True
        except OSError:
            return False
        return False

    def record_contact(
        self,
        *,
        domain: str,
        email: str = "",
        channel: str = "email",
        template: str = "",
        country: str = "",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dom = normalize_domain(domain)
        if not dom:
            return {"ok": False, "error": "domain_required"}
        row = {
            "at": _now(),
            "domain": dom,
            "email": normalize_email(email),
            "channel": str(channel or "email")[:40],
            "template": str(template or "")[:80],
            "country": str(country or "").upper()[:2],
            "meta": meta or {},
        }
        with self._contacts.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        # Also mark in dedup so re-discovery cannot re-queue
        idx = self._load_dedup()
        idx["domains"][dom] = idx["domains"].get(dom) or f"contacted:{dom}"
        if row["email"]:
            idx["emails"][row["email"]] = idx["emails"].get(row["email"]) or f"contacted:{dom}"
        self._save_dedup(idx)
        return {"ok": True, "contact": row}

    # --- reset --------------------------------------------------------------------

    def reset_old_base(self, *, opportunity_service: Any | None = None) -> dict[str, Any]:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = self._archive / stamp
        dest.mkdir(parents=True, exist_ok=True)
        moved: list[str] = []
        for name in (
            "opportunities.jsonl",
            "opportunity_journal.jsonl",
            "quality_archive.jsonl",
            "lost_reasons.jsonl",
            "global_spider_seen.json",
        ):
            src = self._memory / name
            if src.is_file():
                shutil.copy2(src, dest / name)
                src.unlink(missing_ok=True)
                moved.append(name)
        for p in (self._leads, self._dedup, self._state, self._contacts):
            if p.is_file():
                shutil.copy2(p, dest / p.name)
                p.unlink(missing_ok=True)
        archived_ops = 0
        if opportunity_service is not None and hasattr(opportunity_service, "list_opportunities"):
            try:
                rows = opportunity_service.list_opportunities(limit=5000) or []
                with (dest / "opportunities_snapshot.jsonl").open("w", encoding="utf-8") as fh:
                    for row in rows:
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                        archived_ops += 1
                if hasattr(opportunity_service, "update"):
                    for row in rows:
                        oid = str(row.get("id") or "")
                        if oid:
                            try:
                                opportunity_service.update(
                                    oid,
                                    {
                                        "status": "archived_v1",
                                        "meta": {"lead_engine": "v1_retired"},
                                    },
                                )
                            except Exception:
                                pass
            except Exception:
                pass
        state = self._default_state()
        state["last_reset_at"] = _now()
        self._save_state(state)
        self._save_dedup({"domains": {}, "emails": {}})
        # Keep farm config; re-seed defaults if missing
        if not self._farms.is_file():
            self.save_farm_config({})
        return {
            "ok": True,
            "engine": ENGINE_ID,
            "archived_to": str(dest),
            "files_moved": moved,
            "opportunities_archived": archived_ops,
            "message": "Lead Engine v2: старая база архивирована, индекс и contact history очищены.",
        }

    def is_duplicate(self, *, website: str = "", email: str = "", domain: str = "") -> tuple[bool, str]:
        """Domain is global — city/niche must not recreate the same business."""
        idx = self._load_dedup()
        dom = normalize_domain(domain) or normalize_domain(website)
        em = normalize_email(email)
        if dom and self.was_contacted(domain=dom, email=em):
            return True, "contacted"
        if em and self.was_contacted(email=em):
            return True, "contacted"
        if dom and dom in idx["domains"]:
            marker = str(idx["domains"].get(dom) or "")
            if marker.startswith("contacted:"):
                return True, "contacted"
            return True, "domain"
        if em and em in idx["emails"]:
            marker = str(idx["emails"].get(em) or "")
            if marker.startswith("contacted:"):
                return True, "contacted"
            return True, "email"
        return False, ""

    def ingest_lead(
        self,
        payload: dict[str, Any],
        *,
        opportunity_service: Any | None = None,
        analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self._load_state()
        website = str(payload.get("website") or payload.get("url") or "").strip()
        email = normalize_email(str(payload.get("email") or ""))
        domain = normalize_domain(website) or normalize_domain(str(payload.get("domain") or ""))
        dup, reason = self.is_duplicate(website=website, email=email, domain=domain)
        if dup:
            key = "leads_rejected_contacted" if reason == "contacted" else "leads_rejected_dup"
            state[key] = int(state.get(key) or 0) + 1
            self._save_state(state)
            return {"ok": False, "duplicate": True, "reason": reason}

        reasons = reasons_from_analysis(analysis)
        priority = priority_from_analysis(analysis, reasons=reasons)
        country = str(payload.get("country") or "").upper()[:2]
        profile = get_profile(country, self.farm_config()) if country else None

        lead_id = f"lv2-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{domain[:20] or 'x'}"
        lead_id = re.sub(r"[^a-zA-Z0-9_-]", "", lead_id)[:64]
        row = {
            "id": lead_id,
            "engine": ENGINE_ID,
            "version": LEAD_ENGINE_VERSION,
            "created_at": _now(),
            "country": country,
            "city": str(payload.get("city") or "").strip()[:80],
            "niche": str(payload.get("niche") or "").strip()[:80],
            "company": str(payload.get("company") or payload.get("name") or "").strip()[:200],
            "website": website,
            "domain": domain,
            "email": email,
            "source": str(payload.get("source") or "lead_engine_v2").strip()[:120],
            "source_detail": str(payload.get("source_detail") or "").strip()[:500],
            "reasons": reasons,
            "priority": priority,
            "language": (profile or {}).get("language"),
            "currency": (profile or {}).get("currency"),
            "analysis": analysis,
            "recommendation": (analysis or {}).get("recommended_id")
            if isinstance(analysis, dict)
            else None,
        }
        with self._leads.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        idx = self._load_dedup()
        if domain:
            idx["domains"][domain] = lead_id
        if email:
            idx["emails"][email] = lead_id
        self._save_dedup(idx)
        state["leads_accepted"] = int(state.get("leads_accepted") or 0) + 1
        self._save_state(state)

        crm_id = None
        if opportunity_service is not None:
            try:
                from app.integration.lead_pipeline_service import ingest_lead as pipeline_ingest

                created = pipeline_ingest(
                    opportunity_service,
                    {
                        "company_name": row["company"] or domain or lead_id,
                        "source_id": "lead_engine_v2",
                        "opportunity_type": "lead",
                        "website_url": website,
                        "contact": email,
                        "city": row["city"],
                        "market_code": row["country"] or "DE",
                        "meta": {
                            "lead_engine": ENGINE_ID,
                            "lead_id": lead_id,
                            "source": row["source"],
                            "source_detail": row["source_detail"],
                            "reasons": reasons,
                            "priority": priority,
                            "analysis_case_id": (analysis or {}).get("case_id")
                            if isinstance(analysis, dict)
                            else None,
                            "health_score": (analysis or {}).get("health_score")
                            if isinstance(analysis, dict)
                            else None,
                            "recommended_id": row["recommendation"],
                        },
                    },
                )
                crm_id = (created or {}).get("id") if isinstance(created, dict) else None
            except Exception as exc:
                row["crm_error"] = str(exc)[:200]

        return {"ok": True, "lead": row, "crm_id": crm_id}

    def next_send_slot(self) -> dict[str, Any]:
        """Pick next country farm for send rotation + recommended wait seconds."""
        import random

        cfg = self.farm_config()
        farms = enabled_profiles(cfg)
        if not farms:
            return {"ok": False, "error": "no_enabled_countries"}
        state = self._load_state()
        idx = int(state.get("rotation_country_index") or 0) % len(farms)
        farm = farms[idx]
        state["rotation_country_index"] = (idx + 1) % len(farms)
        self._save_state(state)
        lo = int(cfg.get("send_interval_min_sec") or 40)
        hi = int(cfg.get("send_interval_max_sec") or 60)
        # Strict markets: prefer upper half of interval
        if farm.get("strict_anti_spam"):
            wait = random.randint(max(lo, (lo + hi) // 2), hi)
        else:
            wait = random.randint(lo, hi)
        # Per-country override if higher
        wait = max(wait, int(farm.get("send_interval_sec") or wait))
        return {
            "ok": True,
            "country": farm.get("code"),
            "farm": farm.get("name"),
            "wait_sec": wait,
            "send_quota_daily": farm.get("send_quota_daily"),
            "strict_anti_spam": bool(farm.get("strict_anti_spam")),
            "language": farm.get("language"),
            "email_template": farm.get("email_template"),
            "message": (
                f"Next farm: {farm.get('code')} · wait {wait}s · "
                "do not force-fill quotas on strict markets"
            ),
        }

    def pause(self) -> dict[str, Any]:
        state = self._load_state()
        state["paused"] = True
        state["running"] = False
        self._save_state(state)
        return {"ok": True, "paused": True, "state": state}

    def resume(self) -> dict[str, Any]:
        state = self._load_state()
        state["paused"] = False
        state["running"] = True
        self._save_state(state)
        return {"ok": True, "paused": False, "running": True, "state": state}

    def status(self) -> dict[str, Any]:
        state = self._load_state()
        cfg = self.farm_config()
        from app.integration.outreach_send_quota import OutreachSendQuota

        quota = OutreachSendQuota(self._memory).health()
        return {
            "engine": ENGINE_ID,
            "version": LEAD_ENGINE_VERSION,
            "state": state,
            "farms": enabled_profiles(cfg),
            "farm_config": {
                "enabled_countries": cfg.get("enabled_countries"),
                "lead_cap": cfg.get("lead_cap"),
                "send_interval_min_sec": cfg.get("send_interval_min_sec"),
                "send_interval_max_sec": cfg.get("send_interval_max_sec"),
                "rotate_countries": cfg.get("rotate_countries"),
            },
            "all_country_codes": list(ALL_PROFILE_CODES),
            "vector_employee_quotas": quota,
            "leads_file": str(self._leads),
            "contact_history": str(self._contacts),
            "dedup_keys": {
                "domains": len(self._load_dedup().get("domains") or {}),
                "emails": len(self._load_dedup().get("emails") or {}),
            },
        }

    def configure(self, patch: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state()
        if "batch_limit" in patch:
            state["batch_limit"] = max(1, min(50, int(patch["batch_limit"])))
        if "niches" in patch and isinstance(patch["niches"], list):
            state["niches"] = [str(x).strip() for x in patch["niches"] if str(x).strip()][:40]
        self._save_state(state)
        farm_patch = {
            k: patch[k]
            for k in (
                "enabled_countries",
                "send_interval_min_sec",
                "send_interval_max_sec",
                "rotate_countries",
                "lead_cap",
                "profiles",
            )
            if k in patch
        }
        farms = self.save_farm_config(farm_patch) if farm_patch else self.farm_config()
        return {"ok": True, "state": state, "farm_config": farms}
